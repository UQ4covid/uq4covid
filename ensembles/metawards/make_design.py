#
# This converts a job JSON into a design matrix
#

import sys
import argparse
import json as js
import numpy as np
from typing import List
import pyDOE2


# Handy short-hand for checking that a list of dictionaries have a minimum set of common keys
def check_common_keys_in_dictionaries(required_keys: List[str], data: List[dict]) -> bool:
    if not required_keys or not data:
        return False
    return all([key in item for item in data] for key in required_keys)


# Check the job file is valid
#
# The top-level keys must contain 'disease', 'stages', 'parameter_list' and 'design'
#   - 'stages' must have a value > 0
# The 'apply' key is optional and reduces the matrix to apply over a smaller set of stages
#
def check_job_file(job: dict) -> bool:
    # Check top-level keys
    required_keys: List[str] = ['disease', 'stages', 'parameter_list', 'design', 'method']
    if not check_common_keys_in_dictionaries(required_keys, [job]):
        return False
    num_stages: int = job['stages']
    if num_stages < 1:
        return False

    valid_methods = ["full_factorial", "latin_hypercube"]
    if not job['method'] in valid_methods:
        return False

    # Check there are parameter definitions and that all parameters have the required definition
    required_parameter_keys: List[str] = ['name', 'min', 'max']
    if not check_common_keys_in_dictionaries(required_parameter_keys, list(job['parameter_list'])):
        return False

    # Check the design settings are valid for each parameter in the design list
    required_design_keys: List[str] = ['name', 'samples', 'spacing']
    if not check_common_keys_in_dictionaries(required_design_keys, list(job['design'])):
        return False

    # Check valid entries
    for entry in job['design']:
        if entry['samples'] < 2:
            return False
        if 'apply' in entry:
            if len(entry['apply']) != num_stages:
                return False

    return True


# Linearly space points in a range
def linear_space(min: float, max: float, samples: int) -> np.ndarray:
    return np.linspace(min, max, samples)


# Divide a space into regions and return mid-points
# This re-uses the linear space method, but doesn't need to (trivial calculation)
def midpoint_space(min: float, max: float, samples: int) -> np.ndarray:
    points: np.ndarray = linear_space(min, max, samples + 1)
    return np.asarray([0.5 * (points[i - 1] + points[i]) for i in range(1, samples + 1)])


# Extract the variables to be adjusted
def extract_columns(data: dict) -> (int, List[str]):
    num_stages: int = int(data['stages'])
    methods: dict = {"linear": linear_space, "midpoint": midpoint_space}
    column_names: List[str] = []
    column_states: List[List[float]] = []
    for entry in data['design']:
        if 'apply' not in entry:
            mask: List[bool] = [True] * num_stages
        else:
            mask: List[bool] = entry['apply']
        variables: List[str] = [entry['name'] + "[" + str(stage) + "]" for stage in range(num_stages) if mask[stage]]
        column_names.extend(variables)
        parameter: dict = next(item for item in data['parameter_list'] if item["name"] == entry['name'])
        states = [methods[entry["spacing"]](parameter['min'], parameter['max'], entry['samples'])] * sum(mask)
        column_states.extend(states)
    return column_states, column_names


def full_header(job: dict) -> str:
    parameter_names: List[str] = [param['name'] for param in job['parameter_list']]
    num_stages: int = job['stages']
    return ','.join([name + "[" + str(stage) + "]" for name in parameter_names for stage in range(num_stages)])


#
# Full factorial design matrices
#
def factorial_design(data: dict) -> (np.ndarray, str):
    states, idents = extract_columns(data)
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
    states, idents = extract_columns(data)
    min_values = [min(entry) for entry in states]
    max_values = [max(entry) for entry in states]
    num_variables = len(idents)
    if num_samples is None:
        num_samples = num_variables
    design = pyDOE2.lhs(n=num_variables, samples=num_samples)

    # Transform the designs back to original ranges
    for i, row in enumerate(design):
        design[i] = [((max_values[i] - min_values[i]) * item) + min_values[i] for i, item in enumerate(row)]

    return design, ','.join(idents)


# Wrapper to call from import or command line
# This is what can be called from inside scripts
def process(data: dict) -> (np.ndarray, str):
    design_methods = {"full_factorial": factorial_design, "latin_hypercube": latin_design}
    return design_methods[data['method']](data)


# Entry point
def main(argv):
    # Query the parser - is getattr() safer?
    in_location = argv.input
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        print("force option passed, design matrix will be over-written if it exists")
        mode_str = "w"

    # Try to 'touch' the file system for both input and output to short-circuit any obvious problems
    # As the file-system could change between calls, we retain the file handle as long as possible
    # There are also numerous verdicts on whether open() is safe in a 'with' statement due to __exit__
    # having odd behaviour

    try:
        with open(in_location) as in_file, open(out_location, mode_str) as out_file:

            # Try to load the JSON data
            data: dict = js.load(in_file)
            if not data:
                print("Invalid job file")
                sys.exit(1)

            # Build the matrix
            design, header = process(data)
            np.savetxt(fname=out_file, X=design, fmt="%f", delimiter=",", header=header, comments='')

    # Catch a few exceptions, but let others pass through
    except OSError as error:
        # Can be thrown by the open(), read() and write() calls
        msg = "Unexpected error"
        if error.filename == in_location:
            msg = "Could not open the input file"
        if error.filename == out_location:
            msg = "Could not open the output file"
        print(msg + " " + error.filename)
        print("Python: " + str(error))
        sys.exit(1)
    except js.JSONDecodeError as error:
        # Errors from the json module
        print("Error handling the JSON data")
        print("Python: " + str(error))
        sys.exit(1)

    # Normal completion
    print("Design matrix created")
    sys.exit(0)


#
# This arg parser is wrapped in a function for testing purposes
#
def main_parser(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='<input file>', type=str, help="Input job file")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output design file")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(args)


#
# If this script is called from the command line instead of importing, the entry point will be here
#
if __name__ == "__main__":
    args = main_parser()
    main(args)
