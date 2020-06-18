# This is an extractor for multi-demographic models
# NOTE: delta writes have been removed from this edition

# This extractor gets all of the disease stages that are at least in the I class
# TODO: Is this broken with the new mapping key in the disease files??

import metawards
from metawards.utils import call_function_on_network
from metawards.utils import Console
from multiprocessing import Lock
from typing import List, Union
from sqlite3 import OperationalError, Connection, Cursor, connect
from sys import argv
from os import path
from csv import reader

_sql_file_name: str = ""
_run_index: int = -1  # Which run this currently is

# This is a bit dodgy as we use eval(), but skirts import/unresolved object errors for now
# TODO: Write mini data_src functional objects that wrap the workspace to resolve this
_output_channels_list = \
    {
        "susceptible": ["workspace.S_in_wards"],
        "exposed": ["workspace.E_in_wards"],
        "infected": ["get_comp(network, workspace, \"genpop\", 3)"],
        "deaths": ["get_comp(network, workspace, \"genpop\", 5)"],
        "recovered": ["get_comp(network, workspace, \"genpop\", 4)"]
    }


# Index a compartment
def get_comp(network, workspace, demographic, stage):
    demo_index = network.demographics.get_index(demographic)
    results = workspace.subspaces[demo_index]
    return results.ward_inf_tot[stage]


# Horrible hack to get access to input file argument not available in the extractor
# NOTE: Using metawards.app.run.parse_args() will raise an exception - no free lunch!
def get_input_file_name() -> str:
    return next((argv[i + 1] for i, x in enumerate(argv) if x == "-i" or x == "--input"), None)


# Get the design data from the input file - this is probably a member function somewhere
# This is needed because the user variables lose their dots and it is impossible to find the hypercube parameters
def get_design_data() -> (List[str], List[List[str]]):
    with open(get_input_file_name()) as in_file:
        data: List[List[str]] = list(reader(in_file))
        header = data[0]
        data.pop(0)
        return header, data


# Makes the sql database
# We can pass strings to metawards, so this can be removed at some point
# TODO: Look into removing this (make template schema and copy) - environment variables might work?
def make_sql_template(out_connection: Connection):
    header, data = get_design_data()
    design_names = [var[1:] for var in header[:-1] if var[0] == '.']
    column_indices = [i for i, s in enumerate(header[:-1]) for name in design_names if name in s]
    database: Union[Connection, None] = None

    # If the operations fail, we cannot continue, but we must close the connection (try without except)
    try:

        # Table idents: 5 is enough to stitch the entire ward output together with the hypercube designs
        # These should ensure third normal form, although I haven't checked this in detail
        design_table_name: str = "design_table"
        output_table_name: str = "output_table"
        day_table_name: str = "day_table"
        run_table_name: str = "run_table"
        results_table_name: str = "results_table"

        # The design table is a dynamic schema constructed from all the "." variables in the input table
        # We assume the first column is the key (TODO: Use a complex primary key over the row instead?)
        # First design column is an integer key, rest are hypercube points on [-1, 1]
        var_schema: List[str] = []
        check_schema: List[str] = []
        key_column: str = f"{design_names[0]}"
        var_schema.append(f"{key_column} integer not null primary key")
        for variable in design_names[1:]:
            var_schema.append(f"{variable} real not null")
            check_schema.append(f"check({variable} >= -1.0 and {variable} <= 1.0)")
        design_table_schema: str = f'create table {design_table_name} (' + ','.join(var_schema + check_schema) + ');'
        output_channel_schema: str = f"create table {output_table_name} (id integer not null primary key, name text);"
        day_table_schema: str = f"create table {day_table_name}(day integer not null primary key,date text not null);"
        run_table_schema: str = f"create table {run_table_name}(run_index integer not null primary key," \
                                f"design_index integer not null,end_day integer not null," \
                                f"mw_folder text not null," \
                                f"foreign key (design_index) references {design_table_name}({key_column}));"
        results_table_schema: str = f"create table {results_table_name}(result_id integer not null primary key," \
                                    "ward_id integer not null,output_channel integer not null,sim_out real not null," \
                                    "sim_time integer not null,run_id integer not null," \
                                    f"foreign key (output_channel) references {output_table_name}(id)," \
                                    f"foreign key (sim_time) references {day_table_name}(day)," \
                                    f"foreign key (run_id) references {run_table_name}(run_index));"

        # Create in memory first (small database, + we want to ensure it is well-formed)
        database = connect(":memory:")
        cursor: Cursor = database.cursor()

        # Flags / pragmas
        cursor.execute(f'PRAGMA encoding = "UTF-8";')
        cursor.execute(f"PRAGMA foreign_keys = ON;")

        # Create table structure
        cursor.execute(design_table_schema)
        cursor.execute(output_channel_schema)
        cursor.execute(day_table_schema)
        cursor.execute(run_table_schema)
        cursor.execute(results_table_schema)

        # Global writes

        # Write the output channels and design lists
        for i, output in enumerate(_output_channels_list.keys()):
            cursor.execute("insert into output_table(id, name) values (?, ?)", (i, output))
        for row in data:
            vals = tuple([row[c] for c in column_indices])
            cursor.execute(f"insert into design_table ({','.join(design_names)}) "
                           f"values ({','.join(['?'] * len(design_names))})", vals)
        database.commit()

        # Now save to disk
        database.backup(out_connection)

    finally:
        if database:
            database.close()
        if out_connection:
            out_connection.close()


# This sets up the database on the first run
def extractor_setup(network: metawards.Network, **kwargs):
    # Globals
    global _sql_file_name

    # Get the unique output directory for this run
    out_object: metawards.OutputFiles = kwargs["output_dir"]
    run_ident = path.basename(out_object.get_path())
    out_folder = path.abspath(path.join(out_object.get_path(), path.pardir))

    # Identify the design point
    design_index = int(network.params.user_params["design_index"])

    # Create a valid URI to use the SQLite access rights
    data_base_file_name: str = path.join(out_folder, "sql_wards.dat")
    _sql_file_name = data_base_file_name
    fixed_path = path.abspath(data_base_file_name).replace("\\", "/")
    db_uri = f"file:{fixed_path}?mode=rw"

    # Concurrency guard: multiple processes can connect, but only one should create
    # NOTE: Connections only fail if the file doesn't exist with mode "rw"
    test_connection: Union[Connection, None] = None
    create_connection: Union[Connection, None] = None

    # One at a time here
    mutex = Lock()
    with mutex:
        try:
            test_connection = connect(db_uri, uri=True)
            # TODO: What do we do if there is an old database in there?
            # FIXME: For re-running partial ensembles this needs to be handled
        except OperationalError:
            # This process is the first one in to create the database
            try:
                # Append "c" to make the connection create a blank database
                create_connection = connect(db_uri + "c", uri=True)
            except OperationalError as err:
                # An actual problem happened if we get here
                Console.print("SQL Error: " + str(err))
                raise
            make_sql_template(create_connection)
        finally:
            if test_connection:
                test_connection.close()
            if create_connection:
                create_connection.close()

        # Do first commits for setting up the run
        # TODO: Preserve connection across scope
        process_connection = connect(_sql_file_name)
        try:
            write_setup_entries(process_connection, design_index, run_ident)
        finally:
            if process_connection:
                process_connection.close()


# Setup entries which are written once per run
def write_setup_entries(database: Connection, design_index: int, run_ident: str):
    global _run_index
    c: Cursor = database.cursor()

    # Write this run
    i_str = f"insert into run_table(design_index,end_day,mw_folder) values (?,?,?)"
    vals = (design_index, -1, run_ident)
    c.execute(i_str, vals)
    _run_index = c.lastrowid
    Console.print("This is run: " + str(_run_index))
    database.commit()


#
# Grab the infected data from each ward in the network
#
def output_wards_serial(network: metawards.Network, population: metawards.Population,
                        workspace: metawards.Workspace, **kwargs):
    global _sql_file_name
    global _run_index

    # Potential problem: what if we accidentally hit a real attribute?
    if not hasattr(network.params, "_uq4covid_setup"):
        network.params._uq4covid_setup = True
        extractor_setup(network, **kwargs)

    # Prepare database entries
    database = connect(_sql_file_name)
    c: Cursor = database.cursor()

    # Write the current day, some may be longer / shorter, so ignore duplicate entries
    c.execute(f"insert or ignore into day_table(day,date) values (?,?)", (int(population.day), str(population.date)))
    database.commit()

    # Write results for infections and removed
    # NOTE: Don't re-use time_index as if there is a duplicate then the rowid will be zero
    # TODO: List comprehension is fine, but consider numpy (or equivalent) for more speed

    output_src = 0
    mode_str = "normal write"

    # The index has already been sent to the database, so reuse it here safely
    for channel_index, channel_name in enumerate(_output_channels_list.keys()):
        Console.print(f"Writing channel {channel_name} to database src = "
                      f"{_output_channels_list[channel_name][output_src]}: {mode_str}")
        data_source = eval(_output_channels_list[channel_name][output_src])
        values = [(i, channel_index, x, int(population.day), _run_index)
                  for i, x in enumerate(data_source) if i != 0]
        c.executemany(f"insert into results_table(ward_id,output_channel,sim_out,sim_time,run_id) "
                      f"values (?,?,?,?,?)", values)

    # Write last day into run table
    c.execute("update run_table set end_day = ? where run_index = ?", (int(population.day), _run_index))

    database.commit()
    database.close()


# NOTE: We test for setup by sticking a flag to the network
# TODO: Find a better solution
def extract(**kwargs) -> List[metawards.utils.MetaFunction]:
    return [output_wards_serial]


def output_wards_i(nthreads: int = 1, **kwargs):
    call_function_on_network(nthreads=nthreads, func=output_wards_ir_serial, call_on_overall=True, **kwargs)
