#
# Ideally this is what should have been the R distribution, but it is taking far too long to convert for now
# So this is all orchestrated in Python.
#

import sys
import os
import argparse
import numpy as np
import make_design
import subprocess
import dataclasses
from typing import List
from metawards._disease import Disease
from jobfile import JobFile
import utils

# Yes, monolithic is 'bad' (SIC), but it works for now
class Design:
    def __init__(self):
        self.num_stages = 0
        self.stage_vars: dict = {}
        self.design_method = ""

    # Choose which stages to apply the design rule to (this uses 1 based indexing for stages)
    def set_apply_mask(self, name, mask):
        stages = set(sorted(mask))
        limits = range(1, self.num_stages + 1)
        if any([i not in limits for i in stages]):
            raise ValueError("applying design to invalid stages! Stages = [1, " + str(self.num_stages) + "]")
        apply_mask = [n in stages for n in limits]
        if all(apply_mask):
            return
        self.stage_vars[name] = {**self.stage_vars[name], **{"apply": apply_mask}}

    # Sets the spacing rule
    def set_parameter_spacing_rule(self, name, samples, mode):
        allowable_modes = ["linear", "midpoint"]
        if mode not in allowable_modes:
            raise ValueError("mode: " + str(mode) + " must be one of " + str(allowable_modes))
        self.stage_vars[name] = {**self.stage_vars[name], **{"samples": samples, "spacing": mode}}

    def set_parameter_limits(self, name, min_value, max_value):
        self.stage_vars[name] = {**self.stage_vars[name], **{"min": min_value, "max": max_value}}

    # Extract parameters from the disease model that can be modified by stage
    # TODO: What about bad loads? (Shouldn't modify until verified)
    def load(self, data: Disease):
        self.num_stages = len(data)
        d_data: dict = dataclasses.asdict(data)
        self.stage_vars: dict = {}
        for key in list(d_data.keys()):
            if key.startswith('_'):
                del d_data[key]  # Remove the other fields
                continue
            try:
                iter(d_data[key])
                self.stage_vars[key] = {"default": d_data[key]}
            except TypeError:
                pass
        # Allow chaining / anonymous loads
        return self


    def export_json(self, file_name):
        required_design_keys = ["min", "max", "samples", "spacing"]
        optional_design_keys = ["apply"]

        # Select out the adjustable parameters and then clean any tags that are not required for design
        export_vars = {k: v for k, v in self.stage_vars.items() if utils.contains_required_keys(v, required_design_keys)}
        clean = {k: utils.select_dictionary_keys(v, required_design_keys + optional_design_keys)
                 for k, v in export_vars.items()}
        utils.export_dictionary_to_json(clean, file_name)


# R0 hardcoded
# Infectous period has a beta
# 3 parameters, beta is +-inf
# R0 < 1, should die, R0 > 1 should grow

# This is a quick hack to build a job description JSON file to repeat part 2 of tutorial 2 on the MetaWards documentation
def metawards_tutorial_2_2(disease: dict) -> dict:
    num_stages = len(disease['progress'])
    job: dict = {'disease': "ncov", 'stages': num_stages}

    # Define the two parameters
    parameter_list = []
    beta_def: dict = {'name': "beta", 'min': 0.3, 'max': 0.5}
    titm_def: dict = {'name': "too_ill_to_move", 'min': 0.0, 'max': 0.5}
    parameter_list.append(beta_def)
    parameter_list.append(titm_def)

    # Define the design - mask out for stage 2 only
    beta_design: dict = {'name': "beta", 'samples': 3, 'spacing': "linear", 'apply': [False, False, True, False, False]}
    titm_design: dict = {'name': "too_ill_to_move", 'samples': 3, 'spacing': "linear",
                         'apply': [False, False, True, False, False]}
    design_list = [beta_design, titm_design]
    job['parameter_list'] = parameter_list
    job['design'] = design_list
    job['method'] = "full_factorial"
    return job


# The example analysis in the repo: permute all the different ways of setting beta in {0, 0.87} across stages
#
# Emulates the command:
# metawards -d ncov -o .\output --force-overwrite-output --input beta_table.csv -a ExtraSeedsLondon.dat --repeats 5
#
# With automatic creation of the job file
#
def explore_beta(disease: dict):
    # Create the job description JSON
    num_stages = len(disease['progress'])
    job: dict = {'disease': "ncov", 'stages': num_stages}
    parameter_list = []
    beta_def: dict = {'name': "beta", 'min': 0.0, 'max': 0.87}
    parameter_list.append(beta_def)
    beta_design: dict = {'name': "beta", 'samples': 2, 'spacing': "linear"}
    design_list = [beta_design]
    job['parameter_list'] = parameter_list
    job['design'] = design_list
    job['method'] = "full_factorial"

    # Create the design matrix (this one line does the make_design code in Python)
    design, header = make_design.process(job)

    # Save the design file
    design_file_name = "beta_table.csv"
    try:
        with open(design_file_name, "w") as out_file:
            np.savetxt(fname=out_file, X=design, fmt="%f", delimiter=",", header=header, comments='')
    except IOError as error:
        print("Could not open the output file " + error.filename)
        print("Python: " + str(error))
        sys.exit(1)

    # build the run string
    cmd: str = "metawards -d " + job['disease'] + " --input " + design_file_name
    cmd += " -a ExtraSeedsLondon.dat --repeats 5"
    cmd += " -o .\\output2 --force-overwrite-output"

    # Call MetaWards
    # NOTE: You can also call MetaWards in a Python script by faking sys.argv and calling __init__.cli()
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    print("done")


def main(argv):

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