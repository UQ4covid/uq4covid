from metawards.movers import go_stage


#
# This moves people between demographics
#

def move_pathways(network, **kwargs):
    # extract user defined parameters
    params = network.params

    pEA = params.user_params["pEA"]
    pIH = params.user_params["pIH"]
    pID = params.user_params["pID"]
    pHC = params.user_params["pHC"]
    pHR = params.user_params["pHR"]
    pCR = params.user_params["pCR"]
    pHD = params.user_params["pHD"]
    pCD = params.user_params["pCD"]

    moves = \
    [
        [ "genpop", "hospital", 3, 2, pIH ],
        [ "genpop", "morgue", 3, 4, pID ],
        [ "hospital", "genpop", 3, 4, pHR ],
        [ "hospital", "morgue", 3, 4, pHD ],
        [ "hospital", "critical", 3, 2, pHC ],
        [ "critical", "genpop", 3, 4, pCR ],
        [ "critical", "morgue", 3, 4, pCD ],
        [ "asymp", "genpop", 3, 4, 1.0 ],
        [ "genpop", "asymp", 1, 2, pEA ]
    ]

    funcs = []
    for m in moves:
        funcs.append(lambda  **kwargs: go_stage(go_from=m[0], go_to=m[1], from_stage=m[2], to_stage=m[3],
                                                fraction=m[4], **kwargs))

    return funcs
