#
# Stitch output together as per UQ step 4
#

import argparse
import sys
import os
import metawards
import numpy as np
from uq4metawards.utils import load_csv


def main():

    argv = main_parser()

    # Step 1 is to make an index file for the runs
    in_location = argv.disease
    data_location = argv.data
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, disease matrix will be over-written if it exists")

    if argv.day < 0:
        print("Can't extract a negative day")
        sys.exit(1)

    # Touch the file system
    try:
        with open(in_location) as disease_file, \
                open(out_location, mode_str) as index_file:

            disease_file, disease_header_names = load_csv(disease_file)
            sub_dir_list = next(os.walk(data_location))[1]

            num_experiments = 0
            index = []
            for i, row in enumerate(disease_file):
                # To have having to input the design file pick up repeats from regex
                design_vars = row
                string = metawards.VariableSet.create_fingerprint(design_vars)

                # Find how many folders match this partial name
                # TODO: Dir checks for data location
                matches = [s for s in sub_dir_list if string in s]
                run_id = 0
                for m in matches:
                    index.append((str("run_index_" + str(num_experiments)), m, str(i), str(run_id)))

                    disease_str = ','.join(str(x) for x in design_vars)

                    num_experiments += 1
                    run_id += 1

            index_header = ','.join(["key", "folder_id", "design_id", "run_id"])
            index_matrix = np.asarray(index)
            np.savetxt(fname=index_file, X=index_matrix, fmt="%s", delimiter=",", header=index_header, comments='')

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
    parser = argparse.ArgumentParser("UQ4")
    parser.add_argument('disease', metavar='<input file>', type=str, help="Input disease matrix")
    parser.add_argument('data', metavar='<data folder>', type=str, help="MetaWards output folder")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output index file")
    parser.add_argument('day', metavar='<sim date>', type=int, help="Day to extract")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
