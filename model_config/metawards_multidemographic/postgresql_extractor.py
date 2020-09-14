from metawards.extractors import extract_default
from metawards import Networks, OutputFiles, Population, Workspace
from metawards.utils import Console
import psycopg2 as psg
from os import path

#
# Send all results to a PostgreSQL server
# This will make a giant results table which is keyed by design ID and run ID in order to paste them together

database_name = "myrun"
table_name = "post_results_2"

# Output list
_out_channels = \
    {
        "asymp": [2, 3, 4],
        "critical": [2, 3, 4, 5],
        "genpop": [0, 1, 2, 3, 4, 5],
        "hospital": [2, 3, 4, 5]
    }

_zero_crossings = {}


def initialise(conn, network):
    c = conn.cursor()
    values: List[str] = []
    for i, subnet in enumerate(network.subnets):
        values += [f"{subnet.name}_{i} int" for i in _out_channels[subnet.name]]
    qstring = f"CREATE TABLE IF NOT EXISTS {table_name}(design INT NOT NULL, repeat INT NOT NULL, " \
              f"day INT NOT NULL, ward INT NOT NULL, {','.join(values)}, " \
              f"PRIMARY KEY (design, repeat, day, ward));"
    Console.print(f"POSTGRESQL Exec: \n{qstring}")
    c.execute(qstring)
    conn.commit()


def output_db(population: Population, network: Networks,
              workspace: Workspace, output_dir: OutputFiles, **kwargs):

    Console.print(f"Calling output_db for a {network.__class__} object")
    postgres_connection = psg.connect(host="localhost", user="uqwrite", password="uq4covid", database=database_name)

    # Make sure init is only called once, it actually doesn't matter, but saves time
    if not hasattr(network, "init_guard"):
        initialise(postgres_connection, network)
        setattr(network, "init_guard", False)

    cur = postgres_connection.cursor()
    run_ident = path.basename(output_dir.get_path())
    repeat_ident = int(run_ident[-3:])
    design_index = int(network.params.user_params["design_index"])

    # get each demographics data
    for i, subnet in enumerate(network.subnets):
        ward_inf_tot = workspace.subspaces[i].ward_inf_tot
        N_INF_CLASSES = workspace.subspaces[i].n_inf_classes
        col2_names = ["design", "repeat", "day", "ward"] + \
                     [f"{subnet.name}_{i}" for i in _out_channels[subnet.name]]
        for k in range(1, workspace.subspaces[i].nnodes + 1):
            if k not in _zero_crossings:
                _zero_crossings[k] = False
            vals = [design_index, repeat_ident, population.day, k]
            for j in range(0, N_INF_CLASSES):

                # Try to fudge a marker for first infections
                if ward_inf_tot[0][k] != 0 and _zero_crossings[k] is False:
                    _zero_crossings[k] = True
                    Console.print(f"Got first infection in ward {k}")

                # TODO: What is this?? Why are some classes deltas?
                if j == 1 or j == 3:
                    vals.append(ward_inf_tot[j - 1][k] + ward_inf_tot[j][k])
                else:
                    vals.append(ward_inf_tot[j][k])
            col2_str = ','.join(col2_names)
            update_cols = col2_names[4:]
            keeps = [vals[x + 4] for x in range(N_INF_CLASSES) if x in _out_channels[subnet.name]]
            keeps_str = ",".join([str(v) for v in [design_index, repeat_ident, population.day, k] + keeps])
            update_str = ','.join([f"{c} = {v}" for c, v in zip(update_cols, keeps)])
            qstring = f"INSERT INTO {table_name} ({col2_str}) VALUES ({keeps_str}) " \
                      f"ON CONFLICT (design, repeat, day, ward) DO UPDATE SET {update_str};"
            if _zero_crossings[k] is True:
                cur.execute(qstring)
    postgres_connection.commit()
    postgres_connection.close()


def extract_db(**kwargs):
    funcs = []
    funcs.append(output_db)
    return funcs
