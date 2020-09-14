from metawards.extractors import extract_default
from metawards import Networks, OutputFiles, Population, Workspace
from metawards.utils import Console

def create_tables(network: Networks):
    # return a function that creates the tables
    # for the specified number of disease classes

    def initialise(conn):
        # create tables for the values for each demographic... - put all your initialisation code here
        c = conn.cursor()

        for i, subnet in enumerate(network.subnets):
            name = subnet.name
            N_INF_CLASSES = subnet.params.disease_params.N_INF_CLASSES()

            values = ",".join([f"stage_{i} int" for i in range(0, N_INF_CLASSES)])
            c.execute(f"create table {name}_totals(day int, ward int, {values})")

        conn.commit()

    return initialise


def output_db(population: Population, network: Networks,
              workspace: Workspace, output_dir: OutputFiles, **kwargs):

    Console.print(f"Calling output_db for a {network.__class__} object")

    # open a database to hold the data - call the 'create_tables'
    # function on this database when it is first opened
    conn = output_dir.open_db("stages.db",
                              initialise=create_tables(network))

    c = conn.cursor()

    # get each demographics data
    for i, subnet in enumerate(network.subnets):
        name = subnet.name

        ward_inf_tot = workspace.subspaces[i].ward_inf_tot

        N_INF_CLASSES = workspace.subspaces[i].n_inf_classes

        for k in range(1, workspace.subspaces[i].nnodes+1):
            vals = [population.day, k]
            for j in range(0, N_INF_CLASSES):
                if j == 1 or j == 3:
                    vals.append(ward_inf_tot[j - 1][k] + ward_inf_tot[j][k])
                else:
                    vals.append(ward_inf_tot[j][k])

            vals_str = ",".join([str(v) for v in vals])

            c.execute(f"insert into {name}_totals VALUES ({vals_str})")

    conn.commit()


def extract_db(**kwargs):
    funcs = []
    funcs.append(output_db)
    return funcs

