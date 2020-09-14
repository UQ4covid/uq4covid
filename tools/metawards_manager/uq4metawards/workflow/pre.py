#
# pre.py: Performs the pre-processing needed to run metawards from a design
#
# This is essentially a roll-up of uq3a and uq3b with minimal dependencies
#

import sys
import os
import argparse
import csv
from typing import List
from uq4metawards.utils import transform_epidemiological_to_disease, select_dictionary_keys
from uq4metawards.sql import make_design_table_schema
from configparser import ConfigParser
from sqlite3 import connect, Cursor, Connection
import psycopg2 as psg
from psycopg2 import sql


def make_memory_database(design_names, design_data, out_connection: Connection):
    # Table idents: 5 is enough to stitch the entire ward output together with the hypercube designs
    # These should ensure third normal form, although I haven't checked this in detail
    design_table_name: str = "design_table"
    output_table_name: str = "output_table"
    day_table_name: str = "day_table"
    run_table_name: str = "run_table"

    key_column = design_names[0]

    design_table_schema = make_design_table_schema(key_column, design_names[1:], design_table_name)
    output_channel_schema: str = f"create table {output_table_name} (id integer not null primary key, name text);"
    day_table_schema: str = f"create table {day_table_name}(day integer not null primary key,date text not null);"
    run_table_schema: str = f"create table {run_table_name}(run_index integer not null primary key," \
                            f"design_index integer not null,end_day integer not null," \
                            f"mw_folder text not null," \
                            f"foreign key (design_index) references {design_table_name}({key_column}));"

    try:

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

        # Global writes

        # Write the design table
        for i, row in enumerate(design_data):
            vals = tuple([i] + row[:-1])
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


# The design table lists all the variables in the design header apart from the first and last
# It is a dynamic schema constructed from all the "." variables in the input table
# NOTE: SQLite and PostgreSQL have *different* SQL formats, such a pain in the arse!
def make_design_table_schema(primary_key: str, design_vars: List[str], design_table_name: str) -> str:

    # Create the primary key
    # An automatically incrementing scheme is fine here as nothing is sensitive
    key_column: str = f"{primary_key}"
    var_schema: List[str] = [f"{key_column} INTEGER NOT NULL PRIMARY KEY"]

    # Add hypercube variables with input range checks
    var_schema += [f"{var} REAL NOT NULL" for var in design_vars]
    check_schema: List[str] = [f"CHECK({var} >= -1.0 and {var} <= 1.0)" for var in design_vars]

    # Construct the table format schema string
    table_entries = f','.join(var_schema + check_schema)
    return f'create table {design_table_name} ( {table_entries} );'


def main():
    args = main_parser()

    design_location: str = args.design
    scales_location: str = args.scales
    disease_location: str = args.disease

    # Grab data from disk
    try:
        with open(design_location) as design_file, \
                open(scales_location) as scales_file:

            design_data: List[List[str]] = list(csv.reader(design_file))
            scales_data: List[List[str]] = list(csv.reader(scales_file))

            design_names: List[str] = design_data[0]
            design_data.pop(0)
            scales_names: List[str] = scales_data[0]
            scales_data.pop(0)

    except IOError as error:
        print("File system error: " + str(error.msg) + " when operating on " + str(error.filename))
        sys.exit(1)

    # Check that the designs are the right size to scale and all scale vars have been defined
    n_design_columns = len(design_names)
    n_scale_columns = len(scales_names)
    n_design_points = len(design_data)

    # We need at least 2 columns for a valid design
    if n_design_columns < 2:
        print("Design has no input parameters!")
        sys.exit(1)
    # Check the size of the inputs (+/- 1 accounts for repeat column)
    if n_scale_columns < (n_design_columns - 1):
        print("Variable limits file does not have enough entries")
        sys.exit(1)
    if n_design_columns < (n_scale_columns + 1):
        print("Design potentially incomplete")
        sys.exit(1)

    # Check that all the scales are defined
    if not all([x in scales_names for x in design_names[:-1]]):
        print("scale limits file does not define the design completely")
        sys.exit(1)

    # Just in case the columns are in a different order...
    col_indices = [next(index for index, item in enumerate(scales_names) if item == x) for x in design_names[:-1]]
    minimums = [float(x) for x in scales_data[0]]
    maximums = [float(x) for x in scales_data[1]]

    # Additional keys for the database components
    key_names: List[str] = \
        [
            ".design_index"
        ]

    # Epidemiological parameteres
    epidemiology_headers: List[str] = key_names + design_names

    # Disease parameters
    user_var_names: List[str] = [f".{x}" for x in design_names[:-1]]
    disease_headers: List[str] = key_names + user_var_names + \
                                 [
                                     "beta[2]",
                                     "beta[3]",
                                     "progress[1]",
                                     "progress[2]",
                                     "progress[3]",
                                     "repeats"
                                 ]

    n_epidemiology_columns = len(epidemiology_headers)
    n_disease_columns = len(disease_headers)
    epidemiology_table = [[''] * n_epidemiology_columns] * n_design_points
    disease_table = [[''] * n_disease_columns] * n_design_points

    # Iterate down the design table and rescale as needed
    for i, row in enumerate(design_data):
        hypercube = [float(x) for x in row[:-1]]
        hyper_01 = [(x / 2.0) + 0.5 for x in hypercube]
        hyper_scale = [(x * (maximums[col_indices[i]] - minimums[col_indices[i]])) + minimums[col_indices[i]]
                       for i, x in enumerate(hyper_01)]
        metawards_params = list(transform_epidemiological_to_disease(hyper_scale[col_indices[0]],
                                                                     hyper_scale[col_indices[1]],
                                                                     hyper_scale[col_indices[2]]))

        disease_row = [''] * n_disease_columns
        epidemiology_row = [''] * n_epidemiology_columns

        # Design keys
        epidemiology_row[0:len(key_names)] = [str(i)]
        disease_row[0:len(key_names)] = [str(i)]

        # Hypercubes
        epidemiology_row[len(key_names):len(key_names) + len(hyper_scale)] = [str(x) for x in hyper_scale]
        disease_row[len(key_names):len(key_names) + len(hypercube)] = [str(x) for x in hypercube]

        # Metawards parameters
        epidemiology_row[len(key_names) + len(hyper_scale):] = str(row[-1])
        disease_row[len(key_names) + len(hyper_scale):] = [str(x) for x in metawards_params] + [str(row[-1])]

        epidemiology_table[i] = epidemiology_row
        disease_table[i] = disease_row

    epidemiology_table.insert(0, epidemiology_headers)
    disease_table.insert(0, disease_headers)

    # Write output disease table
    str_mode = 'x'
    if args.force:
        str_mode = "w"

    try:
        with open(disease_location, str_mode, newline='') as disease_file:
            writer = csv.writer(disease_file)
            writer.writerows(disease_table)
    except FileExistsError:
        print("Disease table already exists, use -f to force overwriting")
        sys.exit(1)
    except IOError as error:
        print("File system error: " + str(error.msg) + " when operating on " + str(error.filename))
        sys.exit(1)


    # Write epidemiology table
    if args.epidemiology:
        in_name, in_ext = os.path.splitext(disease_location)
        e_name = in_name + "_epidemiology.csv"
        try:
            with open(e_name, str_mode, newline='') as e_file:
                writer = csv.writer(e_file)
                writer.writerows(epidemiology_table)
        except FileExistsError:
            print("Epidemiology table already exists, use -f to force overwriting")
            sys.exit(1)
        except IOError as error:
            print("File system error: " + str(error.msg) + " when operating on " + str(error.filename))
            sys.exit(1)

    # Write database
    if args.remote:

        p = ConfigParser()
        p.read(args.remote)

        params: dict = {}
        if p.has_section("postgresql"):
            items = p.items("postgresql")
            params = {v[0]: v[1] for v in items}

        # Add a timestamp
        from datetime import datetime
        extra: str =  datetime.now().strftime('%Y%m%d%H%M%S')
        params["database"] = params["ident"] + f"_{extra}"

        # Connect to the "master" database, then create one for this run
        # NOTE: No finally block -> leave the connection alone
        connection_params: dict = select_dictionary_keys(params, ["host", "user", "password"])
        connection_params["database"] = "postgres"
        try:
            maintenance_connection = psg.connect(**connection_params)

            # A strange quirk of psycopg2 is that 'create database' will fail every time unless autocommit is on
            maintenance_connection.autocommit = True
            cur = maintenance_connection.cursor()
            cur.execute(f"CREATE DATABASE {params['database']}")
            maintenance_connection.autocommit = False
        except psg.Error as err:
            if maintenance_connection is not None:
                maintenance_connection.close()
            print("Problem with creating the remote database, consider a local solution instead?")
            sys.exit(1)

        # Connect to the new database and attempt to create the design table
        # Any exceptions before the commit() will cause a rollback
        # NOTE: Don't get lazy and use "with" / context managers here, we NEED to see the right exceptions
        connection_params: dict = select_dictionary_keys(params, ["host", "user", "password", "database"])
        new_database = None
        try:

            # Get a connection
            new_database = psg.connect(**connection_params)
            cur = new_database.cursor()

            # Make design table
            qstring = make_design_table_schema("design_index", design_names[:-1], "design")
            cur.execute(qstring)

            # Send design data
            for i, row in enumerate(design_data):
                data = [float(x) for x in row[:-1]]
                qstring = f"INSERT INTO design ({','.join(['design_index'] + design_names[:-1])}) " \
                          f"VALUES ({','.join(['%s']*(len(design_names[:-1])+1))})"
                cur.execute(qstring, tuple([i] + data))

            # Make index table of design index and repeat count

            # Finally commit
            new_database.commit()
        except psg.Error as err:
            # if we get here we need to drop the new database
            if new_database is not None:
                new_database.close()

            # If this fails the there is nothing we can do
            maintenance_connection.autocommit = True
            cur = maintenance_connection.cursor()
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {};").format(sql.Identifier(params["database"])))
            maintenance_connection.autocommit = False
            sys.exit(1)
        finally:
            if new_database is not None:
                new_database.close()
            if maintenance_connection is not None:
                maintenance_connection.close()


        # Make database
        make_memory_database([key_names[0][1:]] + design_names, design_data, None)

        # Create a valid URI to use the SQLite access rights
        data_base_file_name: str = os.path.join(os.path.dirname(disease_location), "sql_wards.dat")
        _sql_file_name = data_base_file_name
        fixed_path = os.path.abspath(data_base_file_name).replace("\\", "/")
        db_uri = f"file:{fixed_path}?mode=rw"


    print("Done! See output in " + str(disease_location))
    sys.exit(0)


#
# This arg parser is wrapped in a function for testing purposes
#
def main_parser(main_args=None):
    parser = argparse.ArgumentParser("pre")
    parser.add_argument('design', metavar='<design file>', type=str, help="Input design hypercube")
    parser.add_argument('scales', metavar='<scale file>', type=str, help="Variable limits")
    parser.add_argument('disease', metavar='<disease file>', type=str, help="Output disease file for metawards")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    parser.add_argument('-e', '--epidemiology', action='store_true', help="Output epidemiology matrix")
    parser.add_argument('-r', '--remote', nargs=1, type=str, help="Remote database configuration file")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
