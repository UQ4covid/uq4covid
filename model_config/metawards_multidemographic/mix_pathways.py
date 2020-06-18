from metawards.mixers import merge_using_matrix

def mix_pathways(network, **kwargs):
    params = network.params

    # how much FOI to GP population is affected by others
    GP_GP = 1.0 #params.user_params["GP_GP"]
    GP_A = params.user_params["GP_A"]
    GP_H = 0.0 #params.user_params["GP_H"]
    GP_C = 0.0 #params.user_params["GP_C"]

    A_GP = 0.0 # params.user_params["A_GP"]
    A_A = 0.0 # params.user_params["A_A"]
    A_H = 0.0 # params.user_params["A_H"]
    A_C = 0.0 # params.user_params["A_C"]

    H_GP = 0.0 # params.user_params["H_GP"]
    H_A = 0.0 # params.user_params["H_A"]
    H_H = 0.0 # params.user_params["H_H"]
    H_C = 0.0 # params.user_params["H_C"]

    C_GP = 0.0 # params.user_params["C_GP"]
    C_A = 0.0 # params.user_params["C_A"]
    C_H = 0.0 # params.user_params["C_H"]
    C_C = 0.0 # params.user_params["C_C"]

    matrix = [ [GP_GP, GP_A, GP_H, GP_C],
               [A_GP, A_A, A_H, A_C],
               [H_GP, H_A, H_H, H_C],
               [C_GP, C_A, C_H, C_C] ]

    network.demographics.interaction_matrix = matrix

    return [merge_using_matrix]
