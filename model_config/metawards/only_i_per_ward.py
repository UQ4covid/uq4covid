# This is an extractor for MetaWards that exposes the standard parameters + I for each ward
#
# NOTE: If you use the "large" extractor you get this plus the other ward data that can clutter
#


from metawards.utils import call_function_on_network
import metawards
from typing import List


# This needs to be the same as "extract_" + this script file name without the py extension
def extract_only_i_per_ward(**kwargs):
    print("Sending I per ward to the output stream")
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
    infect_file = output_dir.open(f"wards_trajectory{name}_I.csv")

    if population.day == 0:
        # Print header
        ident: List[str] = ["day"]
        ident += ["beta[" + str(x) + "]" for x, _ in enumerate(d_vars.beta)]
        ident += ["progress[" + str(x) + "]" for x, _ in enumerate(d_vars.progress)]
        ident += ["too_ill_to_move[" + str(x) + "]" for x, _ in enumerate(d_vars.too_ill_to_move)]
        ident += ["contrib_foi[" + str(x) + "]" for x, _ in enumerate(d_vars.contrib_foi)]
        ident += ["start_symptom"]
        ident += ["ward[" + str(i) + "]" for i, _ in enumerate(workspace.I_in_wards)]
        header = ','.join(ident)
        infect_file.write(header)
        infect_file.write("\n")

    day = str(population.day) + ","
    in_params = d_vars.beta + d_vars.progress + d_vars.too_ill_to_move + d_vars.contrib_foi + [d_vars.start_symptom]

    # NOTE: The standard extractors write .dat tables, but R doesn't load these properly (and pandas sometimes)
    # Write a CSV instead
    infect_file.write(day)
    infect_file.write(",".join(str(x) for x in in_params))
    infect_file.write(",")
    infect_file.write(",".join([str(x) for x in workspace.I_in_wards]))
    infect_file.write("\n")


#
# Match the function signature to the extractors to allow multiple threads to call this
#
def output_wards_i(nthreads: int = 1, **kwargs):
    call_function_on_network(nthreads=1, func=output_wards_i_serial, call_on_overall=True, **kwargs)
