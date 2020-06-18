from metawards.mixers import merge_using_matrix


def mix_pathways(network, **kwargs):
    params = network.params.user_params

    # how much FOI to GP population is affected by others
    GP_GP = params["GP_GP"]
    GP_A = params["GP_A"]
    GP_H = params["GP_H"]
    GP_C = params["GP_C"]

    A_GP = params["A_GP"]
    A_A = params["A_A"]
    A_H = params["A_H"]
    A_C = params["A_C"]

    H_GP = params["H_GP"]
    H_A = params["H_A"]
    H_H = params["H_H"]
    H_C = params["H_C"]

    C_GP = params["C_GP"]
    C_A = params["C_A"]
    C_H = params["C_H"]
    C_C = params["C_C"]

    matrix = \
        [
            [GP_GP, GP_A, GP_H, GP_C],
            [A_GP, A_A, A_H, A_C],
            [H_GP, H_A, H_H, H_C],
            [C_GP, C_A, C_H, C_C]
        ]

    network.demographics.interaction_matrix = matrix
    return [merge_using_matrix]
