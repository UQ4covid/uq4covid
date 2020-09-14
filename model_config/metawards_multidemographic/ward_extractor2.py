from metawards.extractors import extract_default
from metawards import Networks, OutputFiles, Population, Workspace
from metawards.utils import Console


# Output list
_out_channels = \
    {
        "asymp": [2, 3, 4],
        "genpop": [0, 1, 2, 3, 4, 5],
        "hospital": [2, 3, 4, 5],
        "critical": [2, 3, 4, 5]
    }

def create_tables(network: Networks):
    # return a function that creates the tables
    # for the specified number of disease classes

    def initialise(conn):
        c = conn.cursor()
        for i, subnet in enumerate(network.subnets):
            name = subnet.name
            N_INF_CLASSES = subnet.params.disease_params.N_INF_CLASSES()
            values = ",".join([f"stage_{i} int" for i in range(0, N_INF_CLASSES)])
            c.execute(f"create table {name}_totals(day int, ward int, {values})")
        conn.commit()

    return initialise


def create_tables_2(network: Networks):
    # return a function that creates the tables
    # for the specified number of disease classes
    # Primary key needs to be composite here

    def initialise(conn):
        c = conn.cursor()
        table_name: str = "results"
        values: List[str] = []
        for i, subnet in enumerate(network.subnets):
            num_classes = subnet.params.disease_params.N_INF_CLASSES()
            values += [f"{subnet.name}_{i} int" for i in range(0, num_classes)]
        c.execute(f"create table {table_name}(day int not null, ward int not null, {','.join(values)}, "
                  f"primary key (day, ward))")
        conn.commit()

    return initialise


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

    # open a database to hold the data - call the 'create_tables'
    # function on this database when it is first opened
    conn = output_dir.open_db("stages.db", initialise=create_tables(network))
    conn2 = output_dir.open_db("stages2.db", initialise=create_tables_2(network))
    conn3 = output_dir.open_db("stages3.db", initialise=create_tables_3(network))
    c = conn.cursor()
    c2 = conn2.cursor()
    c3 = conn3.cursor()

    # get each demographics data
    for i, subnet in enumerate(network.subnets):
        name = subnet.name
        ward_inf_tot = workspace.subspaces[i].ward_inf_tot
        N_INF_CLASSES = workspace.subspaces[i].n_inf_classes

        col_names = ["day", "ward"] + [f"{subnet.name}_{i}" for i in range(0, N_INF_CLASSES)]
        col2_names = ["day", "ward"] + [f"{subnet.name}_{i}" for i in _out_channels[subnet.name]]

        for k in range(1, workspace.subspaces[i].nnodes+1):
            vals = [population.day, k]
            for j in range(0, N_INF_CLASSES):
                # TODO: What is this?? Why are some classes deltas?
                if j == 1 or j == 3:
                    vals.append(ward_inf_tot[j - 1][k] + ward_inf_tot[j][k])
                else:
                    vals.append(ward_inf_tot[j][k])

            vals_str = ",".join([str(v) for v in vals])

            # Technically this is open to SQL injection, perhaps let CW know?
            c.execute(f"insert into {name}_totals VALUES ({vals_str})")

            col_str = ','.join(col_names)
            update_cols = col_names[2:]
            update_str = ','.join([f"{c} = {v}" for c, v in zip(update_cols, vals[2:])])
            qstring = f"insert into results ({col_str}) values ({vals_str}) on conflict(day, ward) do update set {update_str}"
            c2.execute(qstring)

            col2_str = ','.join(col2_names)
            #Console.print(col2_names)
            update_cols = col2_names[2:]
            #Console.print(update_cols)
            keeps = [vals[x + 2] for x in range(N_INF_CLASSES) if x in _out_channels[subnet.name]]
            keeps_str = ",".join([str(v) for v in [population.day, k] + keeps])
            #Console.print(keeps_str)
            update_str = ','.join([f"{c} = {v}" for c, v in zip(update_cols, keeps)])
            #Console.print(update_str)
            qstring = f"insert into compact ({col2_str}) values ({keeps_str}) on conflict(day, ward) do update set {update_str}"
            #Console.print(f"SQL: {qstring}")
            c3.execute(qstring)

    conn.commit()
    conn2.commit()
    conn3.commit()

def extract_db(**kwargs):
    funcs = []
    funcs.append(output_db)
    return funcs

