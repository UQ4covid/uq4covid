#
# Small converter that takes the 2011 census ward data and puts it into a database for queries
# NOTE: This is on hold and currently not working, do not use
#

raise NotImplementedError("DO NOT USE")

import sys
import argparse
import pandas as pd
import sqlite3 as sql
from typing import Set, Iterable, Tuple


# This originally returned the missing column idents, but done externally now
def check_dataframe_has_column_names(data: pd.DataFrame, required_columns: Set[str]) -> bool:
    return required_columns.issubset(data.columns)


def create_database(name: str, field_desc: Iterable[Tuple[str, str]], data: pd.DataFrame):
    db = None

    # Table creation string
    str_exec = "CREATE TABLE IF NOT EXISTS wlookup ( table_key integer PRIMARY KEY,"
    str_columns = ','.join(f"{x[0]} {x[1]}" for x in field_desc)
    str_exec += str_columns + " );"

    # Find the unique LAD11NM, use these as a LAD table
    lads = data["LAD11NM"].unique()
    one_to_one = [True, True]
    for local_authority in lads:
        wales_matches = data[data["LAD11NM"] == local_authority]["LAD11NMW"].unique()
        code_matches = data[data["LAD11NM"] == local_authority]["LAD11CD"].unique()
        n_wales_matches = len(wales_matches)
        n_code_matches = len(code_matches)
        if n_wales_matches > 1:
            one_to_one[0] = False
        if n_code_matches > 1:
            one_to_one[1] = False
    print(one_to_one)

    # LAD Table:
    # Key | LA Name | LA Name for wales | Code
    lad_table = "CREATE TABLE IF NOT EXISTS la_table " \
                "( " \
                "table_key integer NOT NULL," \
                "la_name text NOT NULL," \
                "la_name_wales text," \
                "code text NOT NULL," \
                "PRIMARY KEY(table_key) " \
                "); "

    try:
        db = sql.connect(name)
        cur = db.cursor()
        cur.execute(str_exec)
        cur.execute(lad_table)

        # TODO: Make this go away if the table exists
        for local_authority in lads:
            row = data[data["LAD11NM"] == local_authority]
            code = row["LAD11CD"].unique()
            name = row["LAD11NM"].unique()
            wales = row["LAD11NMW"].unique()
            e_string = "INSERT INTO la_table(la_name, la_name_wales, code) VALUES(?,?,?)"
            cur.execute(e_string, (name, wales, code))

        for index, row in data.iterrows():
            # NOTE: Pandas irritatingly scrambles column order
            vals = row.values
            q_string = ','.join(['?'] * len(vals))
            n_string = ','.join(f"{x[0]}" for x in field_desc)
            e_string = f"INSERT INTO wlookup({n_string}) VALUES ({q_string})"
            cur.execute(e_string, vals)

    except sql.Error as err:
        print("Problem opening connection")
        print(err)
    finally:
        if db:
            db.close()


def main():
    argv = main_parser()

    in_location = getattr(argv, "input")
    out_location = getattr(argv, "output")

    # Read the Dataframe from the disk
    try:
        with open(in_location, encoding="utf-8-sig") as ward_file:
            ward_data = pd.read_csv(ward_file, encoding="utf-8-sig")
    except FileNotFoundError:
        print("Couldn't find file: " + str(in_location))
    except IOError:
        print("Unable to open the ward lookup")
        sys.exit(1)

    # Check we have the right columns, then slice out
    required_columns: Set[str] = {"WD11CD", "WD11NM", "WD11NMW", "LAD11CD", "LAD11NM", "LAD11NMW", "FID"}
    if not check_dataframe_has_column_names(ward_data, required_columns):
        print("Invalid ward data format. Missing columns: " + str(required_columns.difference(ward_data.columns)))
        sys.exit(1)
    ward_data_reduced = ward_data[list(required_columns)]

    column_types = ["text", "text", "text", "text", "text", "text", "integer"]
    column_names = ["ward_code", "ward_name", "ward_name_wales", "local_authority_code", "local_authority_name",
                    "local_authority_name_wales", "feature_id"]

    create_database(out_location, zip(column_names, column_types), ward_data_reduced)


def main_parser(main_args=None):
    parser = argparse.ArgumentParser("w2sql")
    parser.add_argument('input', metavar='<input file>', type=str, help="Input ward lookup csv")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output database")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
