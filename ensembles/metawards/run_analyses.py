#
# Ideally this is what should have been the R distribution, but it is taking far too long to convert for now
# So this is all orchestrated in Python.
#

import sys
import json as js
import numpy as np
import make_design
import subprocess


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
    titm_design: dict = {'name': "too_ill_to_move", 'samples': 3, 'spacing': "linear", 'apply': [False, False, True, False, False]}
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
    proc = subprocess.Popen(cmd, shell = True)
    proc.wait()
    print ("done")

def main():

    # Make sure we can read the disease file before running an experiment
    # TODO: Do data checks?
    disease = "ncov.json"
    try:
        with open(disease) as d_file:
            disease_data: dict = js.load(d_file)
    except IOError as error:
        print ("Cannot open the disease file")
        print("Python: " + str(error))
        sys.exit(1)
    except js.JSONDecodeError as error:
        # Errors from the json module
        print("Error handling the JSON data")
        print("Python: " + str(error))
        sys.exit(1)

    explore_beta(disease_data)

if __name__ == '__main__':
    main()