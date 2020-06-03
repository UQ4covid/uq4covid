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
from uq4metawards.utils import transform_epidemiological_to_disease


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

    # Write output
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
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
