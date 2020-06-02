#
# Perform step 3B of the workflow: Transform a scaled design to disease parameters
#
# 28/05/20: Changed to pass information through metawards to reduce the post-processing steps
# Also removed the need for numpy
#

import sys
import argparse
import csv
from typing import List, Any
from uq4metawards.utils import transform_epidemiological_to_disease


def main():
    argv = main_parser()

    # Query the parser - is getattr() safer?
    in_location: str = argv.input
    out_location: str = argv.output
    mode_str: str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, disease matrix will be over-written if it exists")

    # Touch the file system
    try:
        with open(in_location) as epidemiology_file_handle, \
                open(out_location, mode_str, newline='') as disease_file:

            epidemiology_file: List[List[str]] = list(csv.reader(epidemiology_file_handle))
            epidemiology_header_names: List[str] = epidemiology_file[0]
            epidemiology_file.pop(0)

            # Turn the original design variables into custom variables for metawards
            # Ignore the repeats column
            e_names: List[str] = [f".{x}" for x in epidemiology_header_names[0:-1]]

            # Additional keys
            key_names: List[str] = \
                [
                    ".design_index"
                ]

            # Disease parameters
            head_names: List[str] = key_names + e_names + \
                                    [
                                        "beta[2]",
                                        "beta[3]",
                                        "progress[1]",
                                        "progress[2]",
                                        "progress[3]",
                                        "repeats"
                                    ]

            # Only pass the first three fields to the disease builder
            # TODO: Do this by name rather than assuming order?
            disease_matrix: List[List[str]] = [[''] * len(head_names)] * len(epidemiology_file)
            for i, _ in enumerate(disease_matrix):
                row: List[Any] = epidemiology_file[i]

                # Data-type conversion
                row[:-1] = [float(x) for x in row[:-1]]
                row[-1] = int(float(row[-1]))
                new_row: List[Any] = [0] * len(head_names)

                # Create a unique design key
                write_pos: int = len(key_names)
                new_row[0:write_pos] = [i]

                # Pass scale rates and repeats through from epidemiology file
                new_row[write_pos:write_pos + len(e_names)] = row[0:-1]
                new_row[-1] = row[-1]
                write_pos += len(e_names)

                # Transform the other parameters to disease parameters
                new_row[write_pos:len(head_names) - 1] = \
                    list(transform_epidemiological_to_disease(row[0], row[1], row[2]))

                # Stringify it for csv writing
                disease_matrix[i] = [str(x) for x in new_row]

            disease_matrix.insert(0, head_names)
            writer = csv.writer(disease_file)
            writer.writerows(disease_matrix)

    except FileExistsError:
        print("Output already exists, use -f to force overwriting")
        sys.exit(1)
    except FileNotFoundError as error:
        print(str(error.filename) + " not found.")
        sys.exit(1)
    except IOError as error:
        print("File system error: " + str(error.msg) + " when operating on " + str(error.filename))
        sys.exit(1)

    print("Done! See output at " + str(out_location))
    sys.exit(0)


#
# This arg parser is wrapped in a function for testing purposes
#
def main_parser(main_args=None):
    parser = argparse.ArgumentParser("UQ3B")
    parser.add_argument('input', metavar='<input file>', type=str, help="Input epidemiology matrix")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output disease matrix")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
