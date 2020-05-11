# This is an extractor for MetaWards that exposes the standard parameters + I for each ward
#
# NOTE: If you use the "large" extractor you get this plus the other ward data that can clutter

# If you don't have the metawards source installed, you'll need to replace call_function_on_network with something
from metawards._network import Network
from metawards._population import Population
from metawards._outputfiles import OutputFiles
from metawards._workspace import Workspace
from metawards.utils._get_functions import call_function_on_network


# This needs to be the same as "extract_" + this script file name without the py extension
def extract_only_i_per_ward(**kwargs):
    print("Sending I per ward to the output stream")
    return [output_wards_i]


#
# Grab the infected data from each ward in the network
#
def output_wards_i_serial(network: Network, population: Population, output_dir: OutputFiles,
                                   workspace: Workspace, **kwargs):
    if network.name is None:
        name = ""
    else:
        name = "_" + network.name.replace(" ", "_")

    day = str(population.day) + ","

    # NOTE: The standard extractors write .dat tables, but R doesn't load these properly (and pandas sometimes)
    # Write a CSV instead
    I_file = output_dir.open(f"wards_trajectory{name}_I.csv")
    I_file.write(day)
    I_file.write(",".join([str(x) for x in workspace.I_in_wards]))
    I_file.write("\n")


#
# Match the function signature to the extractors to allow multiple threads to call this
#
def output_wards_i(nthreads: int = 1, **kwargs):
    call_function_on_network(nthreads=1, func=output_wards_i_serial, call_on_overall=True, **kwargs)
