from metawards.movers import go_stage


def move_pathways(network, **kwargs):
    # extract user defined parameters
    params = network.params

    ## moves out of E class
    pE = params.user_params["pE"]
    pEA = params.user_params["pEA"]

    ## moves out of A class
    pA = params.user_params["pA"]

    ## moves out of I class
    pI = params.user_params["pI"]
    pIH = params.user_params["pIH"]
    pIR = params.user_params["pIR"]

    ## moves out of H class
    pH = params.user_params["pH"]
    pHC = params.user_params["pHC"]
    pHR = params.user_params["pHR"]

    ## moves out of C class
    pC = params.user_params["pC"]
    pCR = params.user_params["pCR"]
    func = []

    ## movers in reverse order through the stages to ensure correct mapping
    #######################################################
    #########              C1 MOVES               #########
    #######################################################

    ## move C1 critical to C2 critical
    func.append(lambda **kwargs: go_stage(go_from="critical",
                                          go_to="critical",
                                          from_stage=2,
                                          to_stage=3,
                                          fraction=1.0,
                                          **kwargs))

    #######################################################
    #########              C2 MOVES               #########
    #######################################################

    ## move C2 critical to R critical
    tpCR = pC * pCR
    func.append(lambda **kwargs: go_stage(go_from="critical",
                                          go_to="critical",
                                          from_stage=3,
                                          to_stage=4,
                                          fraction=tpCR,
                                          **kwargs))

    ## move C2 critical to D critical
    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)

    tpCD = pC * (1.0 - pCR) / (1.0 - tpCR)
    tpCD = 1.0 if tpCD > 1.0 else tpCD
    tpCD = 0.0 if tpCD < 0.0 else tpCD

    func.append(lambda **kwargs: go_stage(go_from="critical",
                                          go_to="critical",
                                          from_stage=3,
                                          to_stage=5,
                                          fraction=tpCD,
                                          **kwargs))

    #######################################################
    #########              H1 MOVES               #########
    #######################################################

    ## move H1 hospital to H2 hospital
    func.append(lambda **kwargs: go_stage(go_from="hospital",
                                          go_to="hospital",
                                          from_stage=2,
                                          to_stage=3,
                                          fraction=1.0,
                                          **kwargs))

    #######################################################
    #########              H2 MOVES               #########
    #######################################################

    ## move H2 hospital to C1 critical
    tpHC = pH * pHC
    func.append(lambda **kwargs: go_stage(go_from="hospital",
                                          go_to="critical",
                                          from_stage=3,
                                          to_stage=2,
                                          fraction=tpHC,
                                          **kwargs))

    ## move H2 hospital to R hospital
    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)

    tpHR = pH * pHR / (1.0 - tpHC)
    tpHR = 1.0 if tpHR > 1.0 else tpHR
    tpHR = 0.0 if tpHR < 0.0 else tpHR

    func.append(lambda **kwargs: go_stage(go_from="hospital",
                                          go_to="hospital",
                                          from_stage=3,
                                          to_stage=4,
                                          fraction=tpHR,
                                          **kwargs))

    ## move H2 hospital to D hospital
    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)
    tpHD = pH * (1.0 - pHC - pHR) / (1.0 - pH * (pHC + pHR))
    tpHD = 1.0 if tpHD > 1.0 else tpHD
    tpHD = 0.0 if tpHD < 0.0 else tpHD

    func.append(lambda **kwargs: go_stage(go_from="hospital",
                                          go_to="hospital",
                                          from_stage=3,
                                          to_stage=5,
                                          fraction=tpHD,
                                          **kwargs))

    #######################################################
    #########              I1 MOVES               #########
    #######################################################

    ## move I1 genpop to I2 genpop

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="genpop",
                                          from_stage=2,
                                          to_stage=3,
                                          fraction=1.0,
                                          **kwargs))

    #######################################################
    #########              I2 MOVES               #########
    #######################################################

    ## move I2 genpop to H1 hospital
    tpIH = pI * pIH

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="hospital",
                                          from_stage=3,
                                          to_stage=2,
                                          fraction=tpIH,
                                          **kwargs))

    ## move I2 genpop to R genpop

    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)

    tpIR = pI * pIR / (1.0 - tpIH)
    tpIR = 1.0 if tpIR > 1.0 else tpIR
    tpIR = 0.0 if tpIR < 0.0 else tpIR

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="genpop",
                                          from_stage=3,
                                          to_stage=4,
                                          fraction=tpIR,
                                          **kwargs))

    ## move I2 genpop to D genpop
    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)
    tpID = pI * (1 - pIH - pIR) / (1.0 - pI * (pIH + pIR))
    tpID = 1.0 if tpID > 1.0 else tpID
    tpID = 0.0 if tpID < 0.0 else tpID

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="genpop",
                                          from_stage=3,
                                          to_stage=5,
                                          fraction=tpID,
                                          **kwargs))

    #######################################################
    #########              A1 MOVES               #########
    #######################################################

    ## move A1 asymp to A2 asymp
    func.append(lambda **kwargs: go_stage(go_from="asymp",
                                          go_to="asymp",
                                          from_stage=2,
                                          to_stage=3,
                                          fraction=1.0,
                                          **kwargs))

    #######################################################
    #########              A2 MOVES                #########
    #######################################################

    ## move A2 asymp to R asymp
    tpAR = pA

    func.append(lambda **kwargs: go_stage(go_from="asymp",
                                          go_to="asymp",
                                          from_stage=3,
                                          to_stage=4,
                                          fraction=tpAR,
                                          **kwargs))

    #######################################################
    #########              E1 MOVES               #########
    #######################################################

    ## move E1 genpop to E2 genpop
    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="genpop",
                                          from_stage=0,
                                          to_stage=1,
                                          fraction=1.0,
                                          **kwargs))

    #######################################################
    #########              E2 MOVES               #########
    #######################################################

    ## move E2 genpop to A1 asymp
    tpEA = pE * pEA

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="asymp",
                                          from_stage=1,
                                          to_stage=2,
                                          fraction=tpEA,
                                          **kwargs))

    ## move E2 genpop to I1 genpop
    ## (denominator adjustment is due to operating on remainder
    ## as described in the vignette, also includes correction
    ## in case of rounding error)

    tpEI = pE * (1.0 - pEA) / (1.0 - tpEA)
    tpEI = 1.0 if tpEI > 1.0 else tpEI
    tpEI = 0.0 if tpEI < 0.0 else tpEI

    func.append(lambda **kwargs: go_stage(go_from="genpop",
                                          go_to="genpop",
                                          from_stage=1,
                                          to_stage=2,
                                          fraction=tpEI,
                                          **kwargs))

    return func


#
# This moves people between demographics
#

def move_pathways2(network, **kwargs):
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
