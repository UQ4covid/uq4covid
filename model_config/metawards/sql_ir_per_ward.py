# This is a new extractor prototype that uses sqlite to reduce the output size


from metawards.utils import call_function_on_network
from metawards.utils import Console
import metawards
import multiprocessing
from typing import List, Union
import sqlite3 as sql
import sys
import os
import csv

_created_file_flag = False                                      # This process created the database
_output_channels = {"infected": -1, "removed": -1}              # Output channels for the database
_sql_file_name = ""
_run_ident = ""
_run_index: int = -1                                             # Which run this currently is


# Horrible hacks to get access to things not available in the extractor
# NOTE: Using metawards.app.run.parse_args() will raise an exception - no free lunch!

def get_input_file_name() -> str:
    return next((sys.argv[i + 1] for i, x in enumerate(sys.argv) if x == "-i" or x == "--input"), None)


# Find the variable headers from the input file (without repeats) - this is probably a member function somewhere
# This is needed because the user variables lose their dots and it is impossible to find the hypercube parameters
def get_input_header_names() -> List[str]:
    with open(get_input_file_name()) as in_file:
        header: List[List[str]] = list(csv.reader(in_file))
        return header[0]


# Makes the sql database
# This is here because there is no clean way to pass the required info to the extractor without more hassle
# TODO: Look into removing this (make template schema and copy) - environment variables might work?
def make_sql_template(design_names: List[str], out_connection: sql.Connection):

    database: Union[sql.Connection, None] = None

    # If the operations fail, we cannot continue, but we must close the connection (try without except)
    try:

        # Table idents
        design_table_name: str = "design_table"
        output_table_name: str = "output_table"
        day_table_name: str = "day_table"
        run_table_name: str = "run_table"
        results_table_name: str = "results_table"

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
        database = sql.connect(":memory:")
        cursor: sql.Cursor = database.cursor()

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
        # Write the output channels (don't use executemany as we need the ids)
        for output in _output_channels:
            cursor.execute("insert into output_table(name) values (?)", (output,))
            _output_channels[output] = cursor.lastrowid

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
    global _created_file_flag
    global _sql_file_name
    global _run_ident

    # Get the unique output directory for this run
    out_object: metawards.OutputFiles = kwargs["output_dir"]
    run_ident = os.path.basename(out_object.get_path())
    out_folder = os.path.abspath(os.path.join(out_object.get_path(), os.path.pardir))

    # Identify the design point
    design_index = int(network.params.user_params["design_index"])

    # Create a valid URI to use the SQLite access rights
    data_base_file_name: str = os.path.join(out_folder, "sql_wards.dat")
    _sql_file_name = data_base_file_name
    fixed_path = os.path.abspath(data_base_file_name).replace("\\", "/")
    db_uri = f"file:{fixed_path}?mode=rw"

    # Concurrency guard: multiple processes can connect, but only one should create
    # NOTE: Connections only fail if the file doesn't exist with mode "rw"
    test_connection: Union[sql.Connection, None] = None
    create_connection: Union[sql.Connection, None] = None

    # One at a time here
    mutex = multiprocessing.Lock()
    with mutex:
        try:
            test_connection = sql.connect(db_uri, uri=True)
            # TODO: What do we do if there is an old database in there?
            # FIXME: For re-running partial ensembles this needs to be handled
        except sql.OperationalError:
            # This process is the first one in to create the database
            try:
                # Append "c" to make the connection create a blank database
                create_connection = sql.connect(db_uri + "c", uri=True)
                _created_file_flag = True
            except sql.OperationalError as err:
                # An actual problem happened if we get here
                Console.print("SQL Error: " + str(err))
                raise
            # Drop repeats
            u_vars = get_input_header_names()[:-1]
            design_vars = [var[1:] for var in u_vars if var[0] == '.']
            make_sql_template(design_vars, create_connection)
        finally:
            if test_connection:
                test_connection.close()
            if create_connection:
                create_connection.close()

    # Do first commits for setting up the run
    write_setup_entries(network, design_index, run_ident, **kwargs)


# Setup entries which are written once per run
def write_setup_entries(network: metawards.Network, design_index: int, run_ident: str, **kwargs):
    global _sql_file_name
    global _run_index

    database: Union[sql.Connection, None] = None
    try:
        database = sql.connect(_sql_file_name)

        # Prepare database entries
        c: sql.Cursor = database.cursor()

        # Write the hypercube point, ignoring repeats
        # Repeat runs can create duplicate keys, ideally this would be done before entering here
        # So we use 'insert or ignore' instead of 'insert'
        hypercube_keys = [var[1:] for var in get_input_header_names()[:-1] if var[0] == '.']
        hypercube_values = tuple([network.params.user_params[x] for x in hypercube_keys])
        i_str = f"insert or ignore into design_table({','.join(hypercube_keys)}) values ({','.join(['?'] * len(hypercube_keys))})"
        c.execute(i_str, hypercube_values)
        database.commit()

        # Write this run
        i_str = f"insert into run_table(design_index,end_day,mw_folder) values (?,?,?)"
        vals = (design_index, -1, run_ident)
        c.execute(i_str, vals)
        _run_index = c.lastrowid
        Console.print("This is run: " + str(_run_index))
        database.commit()

    finally:
        database.close()


#
# Grab the infected data from each ward in the network
#
def output_wards_ir_serial(network: metawards.Network, population: metawards.Population,
                           workspace: metawards.Workspace, **kwargs):

    global _sql_file_name
    global _run_index

    # Potential problem: what if we accidentally hit a real attribute?
    if not hasattr(network.params, "_uq4covid_setup"):
        network.params._uq4covid_setup = True
        Console.print("First output")
        extractor_setup(network, **kwargs)

    # Prepare database entries
    database = sql.connect(_sql_file_name)
    c: sql.Cursor = database.cursor()

    # Write the current day
    c.execute(f"insert into day_table(day,date) values (?,?)", (int(population.day), str(population.date)))
    time_index = c.lastrowid
    database.commit()

    # Write results for infections and removed
    v = []
    for i, x in enumerate(workspace.I_in_wards):
        if i == 0:
            continue
        v.append((i, _output_channels["infected"], x, time_index, _run_index))
    for i, x in enumerate(workspace.R_in_wards):
        if i == 0:
            continue
        v.append((i, _output_channels["removed"], x, time_index, _run_index))

    c.executemany(f"insert into results_table(ward_id,output_channel,sim_out,sim_time,run_id) values (?,?,?,?,?)", v)
    database.commit()
    database.close()


#
# Match the function signature to the extractors to allow multiple threads to call this
#
def output_wards_i(nthreads: int = 1, **kwargs):
    call_function_on_network(nthreads=nthreads, func=output_wards_ir_serial, call_on_overall=True, **kwargs)


# NOTE: We test for setup by sticking a flag to the network
# TODO: Find a better solution
def extract(network: metawards.Network, **kwargs) -> List[metawards.utils.MetaFunction]:
    Console.print(f"Sending I and R per ward to the output stream")
    return [output_wards_i]
