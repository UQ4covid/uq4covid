#
# Stitch output together as per UQ step 4
#

import argparse
import sys
import os
from typing import List
from uq4metawards.utils import load_csv
from uq4metawards.utils import print_progress_bar
from uq4metawards.utils import create_fingerprint
import pandas as pd
import numpy as np


# NOTE: If you use argv as a parameter to main, you will have problems with the package setup entry points
def main():
    argv = main_parser()

    # Read off the options from argv
    design_location = argv.design
    disease_location = argv.disease
    data_location = argv.data
    lookup_location = argv.lookup
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, disease matrix will be over-written if it exists")

    #
    # NOTE: Lockdown 1 = day 80, Lockdown 2 = day 133, 1st june = 152
    #
    # We want cumulative for each, rates for each (differences)
    #

    if argv.day < 0:
        print("Can't extract a negative day")
        sys.exit(1)

    str_prefix = f"Building day tables for day {argv.day}"
    str_suffix = f"completed"

    # Touch the file system - keep the handles as long as possible in case of threads / processes interfering
    try:
        with open(design_location) as design_file, \
                open(disease_location) as disease_file, \
                open(lookup_location) as ward_lookup_file, \
                open(out_location, mode_str) as index_file:

            # Load the required data
            # NOTE: You can use the file handles to iterate directly, but loading here does some checks
            # Plus we get early-out exceptions and header decoding
            design_array, design_header_names = load_csv(design_file)
            disease_array, disease_header_names = load_csv(disease_file)
            ward_data = pd.read_csv(ward_lookup_file, quotechar='"')
            sub_dir_list: List[str] = next(os.walk(data_location))[1]

            print("Loaded design table - fields: " + ','.join(design_header_names))
            print("Loaded disease table - fields: " + ','.join(disease_header_names))

            # Build output frame column names
            n_wards: int = ward_data.shape[0]
            col_names: List[str] = design_header_names[0:len(design_header_names) - 1]
            ward_cols: List[str] = [f"ward[{x + 1}]" for x in range(n_wards)]
            col_names += ward_cols

            # Collect the local authorities into groups (of indices)
            lads: dict = ward_data.groupby("LAD11NM").groups
            col_names_lads: List[str] = design_header_names[0:len(design_header_names) - 1]
            lads_cols: List[str] = [str(x) for x in lads]
            col_names_lads += lads_cols

            # ids = ward_data["FID"].values
            # lads = ward_data["LAD11NM"].values

            # Calculate number of size of the output frames
            n_experiments = int(sum(design_array[:, design_array.shape[1] - 1]))
            large_frame_width = len(col_names)
            small_frame_width = len(col_names_lads)

            # Day, Date, Design vars (no repeats), Wards
            # n_cols = 2 + (disease_file.shape[1] - 1) + n_wards

            # Fiddling with lists is cheaper than messing with dataframes
            all_wards_i_per_day = [[None] * large_frame_width] * n_experiments
            all_lads_i_per_day = [[None] * small_frame_width] * n_experiments
            all_wards_i_cumulative = [[None] * large_frame_width] * n_experiments
            all_lads_i_cumulative = [[None] * small_frame_width] * n_experiments

            experiment_index: int = 0
            print("Loading data from MetaWards...")
            print_progress_bar(experiment_index, n_experiments, str_prefix, str_suffix)

            # We iterate collectively over both files as the outputs requires metawards variables
            # but the stats output requires design varaiables
            for design_row, disease_row in zip(enumerate(design_array), enumerate(disease_array)):

                # Calculate how many runs match this design
                design_vars = design_row[1][0:len(design_row[1]) - 1].tolist()
                metawards_vars = disease_row[1][0:len(disease_row[1]) - 1].tolist()
                repeats: int = int(design_row[1][len(design_row[1]) - 1])

                # Check that repeats is valid
                if repeats < 1:
                    raise ValueError("Invalid number of repeats, design file might be corrupted")

                # Try to find each output folder using metawards variable fingerprint
                for r in range(repeats):
                    string: str = create_fingerprint(metawards_vars, r + 1, True)
                    if string not in sub_dir_list:
                        raise ValueError("Missing run data for: " + string)

                    wards_folder: str = os.path.join(data_location, string)
                    wards_file: str = os.path.join(wards_folder, "wards_trajectory_I.csv.bz2")

                    # Load the ward data (drop ward[0] as it is a placeholder)
                    # We need to use pandas as there is more than one datatype in the output
                    # Drop the day and date (not needed), then also ward[0] as it isn't a ward
                    mw_out = pd.read_csv(wards_file).drop(["ward[0]", "date", "day"], 1)

                    # NOTE: ANSI escape characters don't work in Windows Python implementations at the moment
                    print(f"\rLoaded: {wards_file}")

                    # Create an aggregated LAD table
                    # NOTE: This is a silly slow way of doing it, but will do for now
                    num_authorities = len(lads)
                    print_progress_bar(0, num_authorities - 1, "Aggregating local authorities", str_suffix)
                    lad_entry = np.zeros((mw_out.shape[0], num_authorities), dtype=int)
                    for i, indices in enumerate(lads.values()):
                        fids = ward_data.loc[indices, ["FID"]].values.squeeze()
                        col_strings = [f"ward[{x}]" for x in fids]
                        entry = mw_out[col_strings].values
                        lad_entry[:, i] = np.sum(entry, 1).reshape(1, -1)
                        print_progress_bar(i, num_authorities - 1, "Aggregating local authorities", str_suffix,
                                           newline_end=False)

                    # Find the limit of the disease time-span
                    max_day_available: int = mw_out.shape[0] - 1
                    if argv.day > max_day_available:

                        # If a day is missing, return zeros
                        print(f"Run: {wards_file} has no day {argv.day} - it will be substituted with zeros")
                        # NOTE: PyCharm doesn't like the type of the indexer here, but it is int?
                        all_wards_i_per_day[experiment_index] = [0] * large_frame_width
                        all_lads_i_per_day[experiment_index] = [0] * small_frame_width

                        wards_cumulative = mw_out.values.squeeze().tolist()
                        lads_cumulative = lad_entry
                        remaining = argv.day - max_day_available

                        null_row = design_vars + list([0] * (large_frame_width - len(design_vars)))
                        wards_remaining: List[List[int]] = [null_row] * remaining

                        null_row = design_vars + list([0] * (small_frame_width - len(design_vars)))
                        lads_remaining = np.broadcast_to(np.asarray(null_row), (remaining, small_frame_width))
                        cumulative_wards_row = wards_cumulative + wards_remaining
                        cumulative_lads_row = np.vstack((lads_cumulative, lads_remaining))
                    else:

                        # Instant
                        wards_row = mw_out.iloc[[argv.day]].values.squeeze().tolist()[7:]
                        data_row = design_vars + wards_row
                        all_wards_i_per_day[experiment_index] = data_row

                        # Instant LAD
                        lad_row = lad_entry[argv.day, :].tolist()
                        data_row = design_vars + lad_row
                        all_lads_i_per_day[experiment_index] = data_row

                        # Cumulative
                        cumulative_wards_row = mw_out.iloc[0:argv.day + 1].values.squeeze().tolist()
                        cumulative_lads_row = lad_entry[0:argv.day + 1, :]
                        extra_bits = np.broadcast_to(np.asarray(design_vars).reshape(1, -1),
                                                     (cumulative_lads_row.shape[0], len(design_vars)))
                        cumulative_lads_row = np.hstack((extra_bits, cumulative_lads_row))

                    # TODO: Pointless sum of inputs
                    all_wards_i_cumulative[experiment_index] = [sum(i) for i in zip(*cumulative_wards_row)]
                    all_wards_i_cumulative[experiment_index][0:7] = design_vars

                    temp = np.sum(cumulative_lads_row, 0)
                    temp[0:len(design_vars)] = design_vars
                    all_lads_i_cumulative[experiment_index] = temp

                    experiment_index += 1
                    print_progress_bar(experiment_index, n_experiments, str_prefix, str_suffix)

            print("Building output frames...")
            w_out_by_day_full = pd.DataFrame(data=all_wards_i_per_day, columns=col_names)
            w_out_by_day_full.to_csv(os.path.join(data_location, f"wards_by_day_{argv.day}.csv"), index=False)

            w_out_by_day_cumulative = pd.DataFrame(data=all_wards_i_cumulative, columns=col_names)
            w_out_by_day_cumulative.to_csv(os.path.join(data_location, f"wards_by_day_cumulative_{argv.day}.csv"),
                                           index=False)

            lad_out_by_day_full = pd.DataFrame(data=all_lads_i_per_day, columns=col_names_lads)
            lad_out_by_day_full.to_csv(os.path.join(data_location, f"lads_by_day_{argv.day}.csv"), index=False)

            lad_out_by_day_cumulative = pd.DataFrame(data=all_lads_i_cumulative, columns=col_names_lads)
            lad_out_by_day_cumulative.to_csv(os.path.join(data_location, f"lads_by_day_cumulative_{argv.day}.csv"), index=False)

            # index_header = ','.join(["key", "folder_id", "design_id", "run_id"])
            # index_matrix = np.asarray(index)
            # np.savetxt(fname=index_file, X=index_matrix, fmt="%s", delimiter=",", header=index_header, comments='')

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
    parser.add_argument('design', metavar='<input design file>', type=str, help="Input design matrix")
    parser.add_argument('disease', metavar='<input disease file>', type=str, help="Input disease matrix")
    parser.add_argument('data', metavar='<data folder>', type=str, help="MetaWards output folder")
    parser.add_argument('lookup', metavar='<ward lookup file>', type=str, help="Ward data lookup file")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output index file")
    parser.add_argument('day', metavar='<sim date>', type=int, help="Day to extract")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()
