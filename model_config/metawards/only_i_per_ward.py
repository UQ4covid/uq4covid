# This is an extractor for MetaWards that exposes the standard parameters + I for each ward
#
# NOTE: If you use the "large" extractor you get this plus the other ward data that can clutter
#


import metawards
from typing import List


# This needs to be the same as "extract_" + this script file name without the py extension
def extract_only_i_per_ward(**kwargs):
    from metawards.utils import Console
    Console.print("Sending I per ward to the output stream")
    return [output_wards_i]


#
# Grab the infected data from each ward in the network
#
def output_wards_i_serial(network: metawards.Network, population: metawards.Population,
                          output_dir: metawards.OutputFiles, workspace: metawards.Workspace, **kwargs):

    if network.name is None:
        name = ""
    else:
        name = "_" + network.name.replace(" ", "_")

    d_vars = network.params.disease_params
    u_vars = network.params.user_params
    infect_file = output_dir.open(f"wards_trajectory{name}_I.csv")

    # Just print the design parameters: 
    head_str = "beta[2],beta[3],progress[1],progress[2],progress[3],.scale_rate[1],.scale_rate[2]"

    design_out = [d_vars.beta[2], d_vars.beta[3], d_vars.progress[1], d_vars.progress[2], d_vars.progress[3]]
    design_out += [u_vars["lock_1_restrict"], u_vars["lock_2_release"]]

    if population.day == 0:
        # Print header
        ident: List[str] = ["day", "date"]
        ident += [head_str]
        ident += ["ward[" + str(i) + "]" for i, _ in enumerate(workspace.I_in_wards)]
        header = ','.join(ident)
        infect_file.write(header)
        infect_file.write("\n")

    day = str(population.day) + ","
    date = str(population.date) + ","

    # NOTE: The standard extractors write .dat tables, but R doesn't load these properly (and pandas sometimes)
    # Write a CSV instead
    infect_file.write(day)
    infect_file.write(date)
    infect_file.write(",".join(str(x) for x in design_out))
    infect_file.write(",")
    infect_file.write(",".join([str(x) for x in workspace.I_in_wards]))
    infect_file.write("\n")


#
# Match the function signature to the extractors to allow multiple threads to call this
#
def output_wards_i(nthreads: int = 1, **kwargs):
    from metawards.utils import call_function_on_network
    call_function_on_network(nthreads=1, func=output_wards_i_serial, call_on_overall=True, **kwargs)
