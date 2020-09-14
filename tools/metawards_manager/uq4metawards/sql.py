#
# SQL routines
#

from typing import List
import sqlite3 as sql


# The design table lists all the variables in the design header apart from the first and last
# It is a dynamic schema constructed from all the "." variables in the input table
def make_design_table_schema(primary_key: str, design_vars: List[str], design_table_name: str) -> str:

    # Create the primary key
    key_column: str = f"{primary_key}"
    var_schema: List[str] = [f"{key_column} integer not null primary key"]

    # Add hypercube variables with input range checks
    var_schema += [f"{var} real not null" for var in design_vars]
    check_schema: List[str] = [f"check({var} >= -1.0 and {var} <= 1.0)" for var in design_vars]

    # Construct the table format schema string
    table_entries = f','.join(var_schema + check_schema)
    return f'create table {design_table_name} ( {table_entries} );'
