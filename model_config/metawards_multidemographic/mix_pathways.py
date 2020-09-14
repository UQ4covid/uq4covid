from metawards.mixers import merge_using_matrix


def mix_pathways(network, **kwargs):
    params = network.params

    # how much FOI to GP population is affected by others
    GP_GP = 1.0
    GP_A = params.user_params["GP_A"]
    GP_H = params.user_params["GP_H"]
    GP_C = params.user_params["GP_C"]

    matrix = \
        [
            [GP_GP, GP_A, GP_H, GP_C],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0]
        ]

    network.demographics.interaction_matrix = matrix
    return [merge_using_matrix]
