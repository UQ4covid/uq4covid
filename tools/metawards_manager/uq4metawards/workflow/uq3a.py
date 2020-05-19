#
# Performs step 3A of the workflow
#
# Converts the input design to ranges specified by the limits file
#


import sys
import argparse
import numpy as np
import uq4metawards.utils


# Rescale a design matrix from [-1, 1] to a set of ranges defined for each column
def scale_lh_to_design(matrix: np.ndarray, scales: np.ndarray) -> np.ndarray:
    lh_limit = np.broadcast_to(np.asarray([[-1.0], [1.0]]), (2, matrix.shape[1]))
    if not uq4metawards.utils.validate_matrix_range(matrix, lh_limit):
        raise ValueError("Matrix is not clamped between [-1, 1]")
    return uq4metawards.utils.scale_matrix_columns(np.add(np.divide(matrix, 2.0), 0.5), scales[0, :], scales[1, :])


def main():

    argv = main_parser()

    # Query the parser - is getattr() safer?
    in_location = argv.input
    var_location = argv.scales
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, epidemiology matrix will be over-written if it exists")

    # Touch the file system
    try:
        with open(in_location) as design_file, \
             open(var_location) as var_file, \
             open(out_location, mode_str) as epidemiology_file:

            # Open the source files
            design, header = uq4metawards.utils.load_csv(design_file)
            scales, var_names = uq4metawards.utils.load_csv(var_file)

            # We need at least 2 columns for a valid design
            if design.shape[1] < 2:
                print("Design has no input parameters!")
                sys.exit(1)
            # Check the size of the inputs (+/- 1 accounts for repeat column)
            if scales.shape[1] < (design.shape[1] - 1):
                print("Variable limits file does not have enough entries")
                sys.exit(1)
            if design.shape[1] < (scales.shape[1] + 1):
                print("Design potentially incomplete")
                sys.exit(1)

            # Split off the repeats column
            data = design[:, :-1]
            repeats = design[:, -1]

            e_matrix = scale_lh_to_design(data, scales)
            v_names = ','.join(var_names + ["repeats"])
            final = np.c_[e_matrix, repeats]
            np.savetxt(fname=epidemiology_file, X=final, fmt="%f", delimiter=",", header=v_names, comments='')

    except FileExistsError:
        print("Output already exists, use -f to force overwriting")
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
    parser = argparse.ArgumentParser("UQ3A")
    parser.add_argument('input', metavar='<input file>', type=str, help="Input design matrix")
    parser.add_argument('scales', metavar='<scale file>', type=str, help="Variable limits")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output epidemiology matrix")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
