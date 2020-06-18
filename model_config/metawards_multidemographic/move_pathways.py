from metawards.movers import go_stage


#
# This moves people between demographics
#

def move_pathways(network, **kwargs):
    # extract user defined parameters
    params = network.params

    # Design Constants
    pEA = params.user_params["pEA"]
    pIH = params.user_params["pIH"]
    pHC = params.user_params["pHC"]
    pHR = params.user_params["pHR"]
    pCR = params.user_params["pCR"]
    pIR = params.user_params["pIR"]

    # Derived parameters

    # Proportion from infectious to death
    # (1 - pIH) adjustment is due to ordering of events (so operates on remainder from move above)
    pID = (1.0 - (pIR / (1.0 - pIH)))

    # Proportion from hospital to recovery
    # (1 - pHC) adjustment is due to ordering of events (so operates on remainder from move above)
    pHR2 = pHR / (1 - pHC)

    moves = \
        [
            ["genpop", "asymp", 1, 2, pEA],         # move E2 genpop to A1 asymp
            ["asymp", "genpop", 3, 4, 1.0],         # move A2 asymp to R genpop
            ["genpop", "hospital", 3, 2, pIH],      # move I2 genpop to H1 hospital
            ["genpop", "genpop", 3, 5, pID],        # move I2 genpop to D genpop
            ["hospital", "critical", 3, 2, pHC],    # move H2 hospital to C1 critical
            ["hospital", "genpop", 3, 4, pHR2],     # move H2 hospital to R genpop
            ["hospital", "genpop", 3, 5, 1.0],      # move remainder of H2 hospital to D genpop
            ["critical", "genpop", 3, 4, pCR],      # move C2 critical to R genpop
            ["critical", "genpop", 3, 5, 1.0]       # move remainder of C2 critical to D genpop
        ]

    return [lambda **kwargs: go_stage(go_from=m[0], go_to=m[1], from_stage=m[2], to_stage=m[3],
                                      fraction=m[4], **kwargs) for m in moves]
