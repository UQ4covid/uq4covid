#
# This converts a job JSON into a design matrix
# It can be run in a script or from the command line itself
#

import sys
import os
import argparse
import numpy as np
from typing import List
import pyDOE2
import utils
from jobfile import JobFile


# Linearly space points in a range
def linear_space(min_value: float, max_value: float, samples: int) -> np.ndarray:
    return np.linspace(min_value, max_value, samples)


# Divide a space into regions and return mid-points
# This re-uses the linear space method, but doesn't need to (trivial calculation)
def midpoint_space(min_value: float, max_value: float, samples: int) -> np.ndarray:
    points: np.ndarray = linear_space(min_value, max_value, samples + 1)
    return np.asarray([0.5 * (points[i - 1] + points[i]) for i in range(1, samples + 1)])


# Takes the input from a job description and enumerates the factors based on spacing rules
def extract_factors_from_analysis(data: dict) -> (int, List[str]):
    minimums, maximums, names = extract_variables_from_analysis(data)
    column_states: List[List[float]] = []
    methods: dict = {"linear": linear_space, "midpoint": midpoint_space}
    for entry in data["parameter_list"]:
        states = [methods[entry["spacing"]](entry['min'], entry['max'], entry['samples'])]
        column_states.extend(states)
    return column_states, names


# Takes the input from a job and extracts the bare variables
# TODO: Are iterations guaranteed to be in the same order? Might have to have a better solution
def extract_variables_from_analysis(data: dict) -> (int, List[str]):
    column_names: List[str] = [entry["name"] for entry in data["parameter_list"]]
    column_mins: List[float] = [entry["min"] for entry in data["parameter_list"]]
    column_maxs: List[float] = [entry["max"] for entry in data["parameter_list"]]
    return column_mins, column_maxs, column_names


#
# Full factorial design matrices
#
def factorial_design(data: dict) -> (np.ndarray, str):
    states, idents = extract_factors_from_analysis(data)
    state_counts = [len(states[i]) for i, _ in enumerate(states)]
    design = pyDOE2.fullfact(state_counts)
    # Transform the designs back to real numbers
    for i, row in enumerate(design):
        design[i] = [states[index][int(item)] for index, item in enumerate(row)]
    return design, ','.join(idents)


#
# Latin hypercubes (really simple usage for now)
#
# TODO: Extend this for more types from pyDOE2 and/or allow passing control arguments in
# TODO: Look into adding a fixed seed input
#
def latin_design(data: dict, num_samples=None) -> (np.ndarray, str):
    min_values, max_values, idents = extract_variables_from_analysis(data)
    num_variables = len(idents)
    if num_samples is None:
        num_samples = data["method"]["args"]["samples"]
    design = pyDOE2.lhs(n=num_variables, samples=num_samples)
    # Transform the designs back to original ranges
    for i, row in enumerate(design):
        design[i] = [((max_values[i] - min_values[i]) * item) + min_values[i] for i, item in enumerate(row)]
    return design, ','.join(idents)


# TODO: Put these external somewhere?
__design_function_mapping: List[dict] = \
    [
        {
            "name": "full_factorial",
            "func": factorial_design
        },
        {
            "name": "latin_hypercube",
            "func": latin_design
        }
    ]


# Wrapper to call from import or command line
# This is what can be called from inside scripts
def process(data: dict) -> (np.ndarray, str):
    algorithm = next((item for item in __design_function_mapping if item["name"] == data["method"]["algorithm"]), None)
    if algorithm is None:
        raise ValueError("Invalid design method")
    return algorithm["func"](data)


def main(argv):
    # Query the parser - is getattr() safer?
    in_location = argv.input
    out_location = argv.output
    if argv.force:
        print("force option passed, design matrix will be over-written if it exists")
    if argv.epidemiology:
        print("Epidemiology option passed, intermediate matrix will be output")
    export_epidemiological_matrix = argv.epidemiology

    # Load the job file
    analysis = JobFile().load_from_disk(in_location)
    # Get the disease file using the environment variable METAWARDSDATA if possible
    disease_data = utils.load_disease_model(analysis.get_disease_name(), "METAWARDSDATA")

    # Check that the design output is adjusting things that can be adjusted
    adjustable = utils.list_adjustable_parameters(disease_data)
    transform = analysis.list_transform_parameters()
    if not all([variable in adjustable for variable in transform]):
        print("The disease cannot be modified with the current design")
        sys.exit(1)

    # make sure the output folder exists
    if not os.path.exists(out_location):
        os.makedirs(out_location)

    design, header = process(analysis.description)

    # Save the epidemiology matrix only if doesn't exist or -f was passed
    if export_epidemiological_matrix:
        in_base = os.path.basename(in_location)
        in_name, in_ext = os.path.splitext(in_base)
        e_name = os.path.join(out_location, in_name) + "_epidemiology.csv"
        if os.path.isfile(e_name) and not argv.force:
            print("Epidemiology matrix already exists, please run with -f to overwrite files")
        else:
            np.savetxt(fname=e_name, X=design, fmt="%f", delimiter=",", header=header, comments='')

    # Transform the design into disease parameters
    num_outs = analysis.get_num_stream_outputs()
    disease_matrix = np.zeros((design.shape[0], num_outs))
    for i, row in enumerate(design):
        disease_matrix[i] = utils.transform_epidemiological_to_disease(row[0], row[1], row[2])

    # Use the stream outputs to get the right variable idents
    var_names: List[str] = analysis.get_transform_variables()
    disease_header: str = ','.join(var_names)

    # Save the output only if it doesn't exist or -f was passed
    out_name = os.path.join(out_location, analysis.description["output_file"])
    if os.path.isfile(out_name) and not argv.force:
        print("Output already exists, please run with -f to overwrite files")
        sys.exit(1)
    else:
        np.savetxt(fname=out_name, X=disease_matrix, fmt="%f", delimiter=",", header=disease_header, comments='')
        sys.exit(0)


#
# This arg parser is wrapped in a function for testing purposes
#
def main_parser(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='<input file>', type=str, help="Input job file")
    parser.add_argument('output', metavar='<output folder>', type=str, help="Output design folder")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    parser.add_argument('-e', '--epidemiology', action='store_true', help="Output epidemiology matrix")
    return parser.parse_args(args)


#
# If this script is called from the command line instead of importing, the entry point will be here
#
if __name__ == "__main__":
    args = main_parser()
    main(args)
