#
# Stitch output together as per UQ step 4
#

import argparse
import sys
import os
import metawards
from uq4metawards.utils import load_csv
from uq4metawards.utils import print_progress_bar
import pandas as pd
import bz2 as compression


def main():

    argv = main_parser()

    # Step 1 is to make an index file for the runs
    in_location = argv.disease
    data_location = argv.data
    lookup_location = argv.lookup
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, disease matrix will be over-written if it exists")

    #
    # NOTE: Lockdown 1 = day 80, Lockdown 2 = day 133
    #

    if argv.day < 0:
        print("Can't extract a negative day")
        sys.exit(1)

    str_prefix = f"Building day tables for day {argv.day}"
    str_suffix = f"completed"

    # Touch the file system
    try:
        with open(in_location) as disease_file, \
                open(lookup_location) as ward_lookup_file, \
                open(out_location, mode_str) as index_file:

            disease_file, disease_header_names = load_csv(disease_file)
            ward_data = pd.read_csv(ward_lookup_file, quotechar='"')
            sub_dir_list = next(os.walk(data_location))[1]

            # Build output frame column names
            n_wards = ward_data.shape[0]
            col_names = disease_header_names[0:len(disease_header_names) - 1]
            ward_cols = [f"ward[{x + 1}]" for x in range(n_wards)]
            col_names += ward_cols

            lads = ward_data.groupby("LAD11NM")
            #v = lads.groups
            #ids = ward_data["FID"].values
            #lads = ward_data["LAD11NM"].values

            # Calculate number of experiments from the disease file
            n_experiments = int(sum(disease_file[:, disease_file.shape[1] - 1]))

            # Day, Date, Design vars (no repeats), Wards
            #n_cols = 2 + (disease_file.shape[1] - 1) + n_wards

            # Fiddling with lists is cheaper than messing with dataframes
            temp_list = [None] * n_experiments

            experiment_index: int = 0
            print("Loading data from MetaWards...")
            print_progress_bar(experiment_index, n_experiments, str_prefix, str_suffix)

            for i, row in enumerate(disease_file):

                # Calculate how many runs match this design
                design_vars = row[0:len(row) - 1]
                repeats = int(row[len(row) - 1])
                if repeats < 1:
                    raise ValueError("Invalid number of repeats, design file might be corrupted")

                # Try to find each output folder
                for r in range(repeats):
                    string = metawards.VariableSet.create_fingerprint(design_vars, r + 1, True)
                    if string not in sub_dir_list:
                        raise ValueError("Missing run data for: " + string)

                    wards_folder = os.path.join(data_location, string)
                    wards_file = os.path.join(wards_folder, "wards_trajectory_I.csv.bz2")

                    # Load the ward data (drop ward[0] as it is a placeholder)
                    # We need to use pandas as there is more than one datatype in the output
                    # TODO: ALL Of this is horrible, massive time pressure - FIXME all over
                    # Check the console trace - really bad way of doing it, but whatever, time.
                    con_file = os.path.join(wards_folder, "output.txt.bz2")
                    with compression.open(con_file) as c_f:
                        if b"scale_rate" not in c_f.read():
                            print(f"Run {wards_file} is not valid")
                            temp_list[experiment_index] = [0] * 8595
                            flag = True
                        else:
                            flag = False

                    if not flag:
                        mw_out = pd.read_csv(wards_file).drop(["ward[0]", "date", "day"], 1)

                        # NOTE: ANSI escape characters don't work in Windows Python
                        # TODO: We shouldn't be using consoles on windows, use a (better) window instead.
                        print(f"\rLoaded: {wards_file}")

                        # TODO: mcar?
                        try:
                            data_row = mw_out.iloc[[argv.day]].values.squeeze().tolist()
                            temp_list[experiment_index] = data_row
                        except IndexError:
                            print(f"Run: {wards_file} has no day {argv.day} - it will be substituted with zeros")
                            temp_list[experiment_index] = [0] * 8595

                    experiment_index += 1
                    print_progress_bar(experiment_index, n_experiments, str_prefix, str_suffix)

            print("Building output frames...")
            w_out_by_day_full = pd.DataFrame(data=temp_list, columns=col_names)
            w_out_by_day_full.to_csv(os.path.join(data_location, f"wards_by_day_{argv.day}.csv"))
            print_progress_bar(experiment_index, n_experiments, str_prefix, str_suffix)

            #index_header = ','.join(["key", "folder_id", "design_id", "run_id"])
            #index_matrix = np.asarray(index)
            #np.savetxt(fname=index_file, X=index_matrix, fmt="%s", delimiter=",", header=index_header, comments='')

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
    parser.add_argument('lookup', metavar='<ward lookup file>', type=str, help="Ward data lookup file")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output index file")
    parser.add_argument('day', metavar='<sim date>', type=int, help="Day to extract")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
