from metawards.extractors import extract_default
from metawards import Networks, OutputFiles, Population, Workspace
from metawards.utils import Console

# Output list
_out_channels = \
    {
        "asymp": [2, 3, 4],
        "critical": [2, 3, 4, 5],
        "genpop": [0, 1, 2, 3, 4, 5],
        "hospital": [2, 3, 4, 5]
    }

_zero_crossings = {}


def create_tables_3(network: Networks):
    # return a function that creates the tables
    # for the specified number of disease classes
    # Primary key needs to be composite here

    def initialise(conn):
        c = conn.cursor()
        table_name: str = "compact"
        values: List[str] = []
        for i, subnet in enumerate(network.subnets):
            values += [f"{subnet.name}_{i} int" for i in _out_channels[subnet.name]]
        c.execute(f"create table {table_name}(day int not null, ward int not null, {','.join(values)}, "
                  f"primary key (day, ward))")
        conn.commit()

    return initialise


def output_db(population: Population, network: Networks,
              workspace: Workspace, output_dir: OutputFiles, **kwargs):
    Console.print(f"Calling output_db for a {network.__class__} object")
    conn3 = output_dir.open_db("stages3.db", initialise=create_tables_3(network))
    c3 = conn3.cursor()

    # get each demographics data
    for i, subnet in enumerate(network.subnets):
        ward_inf_tot = workspace.subspaces[i].ward_inf_tot
        N_INF_CLASSES = workspace.subspaces[i].n_inf_classes
        col2_names = ["day", "ward"] + [f"{subnet.name}_{i}" for i in _out_channels[subnet.name]]
        for k in range(1, workspace.subspaces[i].nnodes + 1):
            if k not in _zero_crossings:
                _zero_crossings[k] = False
            vals = [population.day, k]
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
            update_cols = col2_names[2:]
            keeps = [vals[x + 2] for x in range(N_INF_CLASSES) if x in _out_channels[subnet.name]]
            keeps_str = ",".join([str(v) for v in [population.day, k] + keeps])
            update_str = ','.join([f"{c} = {v}" for c, v in zip(update_cols, keeps)])
            qstring = f"insert into compact ({col2_str}) values ({keeps_str}) " \
                      f"on conflict(day, ward) do update set {update_str}"
            if _zero_crossings[k] is True:
                c3.execute(qstring)
    conn3.commit()


def extract_db(**kwargs):
    funcs = []
    funcs.append(output_db)
    return funcs
