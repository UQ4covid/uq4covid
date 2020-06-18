from metawards.movers import go_stage

def move_pathways(network, **kwargs):
    # extract user defined parameters
    params = network.params

    pEA = params.user_params["pEA"]
    pIH = params.user_params["pIH"]
    pIR = params.user_params["pIR"]
    pHC = params.user_params["pHC"]
    pHR = params.user_params["pHR"]
    pCR = params.user_params["pCR"]

    # move (100 * pEA)% of E2 genpop to A1 asymp
    func1 = lambda **kwargs: go_stage(go_from="genpop",
                                      go_to="asymp",
                                      from_stage=1,
                                      to_stage=2,
                                      fraction=pEA,
                                      **kwargs)

    # move A2 asymp to R genpop
    func2 = lambda **kwargs: go_stage(go_from="asymp",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=4,
                                      fraction=1.0,
                                      **kwargs)
                                      
    # move (100 * pIH)% of I2 genpop to H1 hospital
    func3 = lambda **kwargs: go_stage(go_from="genpop",
                                      go_to="hospital",
                                      from_stage=3,
                                      to_stage=2,
                                      fraction=pIH,
                                      **kwargs)
                                      
    # move (100 * (1 - pIH - pIR))% of I2 genpop to D genpop
    # (1 - pIH) adjustment is due to ordering of events (so
    # operates on remainder from move above)
    func4 = lambda **kwargs: go_stage(go_from="genpop",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=5,
                                      fraction=(1.0 - (pIR / (1.0 - pIH))),
                                      **kwargs)
                                      
    # move (100 * pHC)% of H2 hospital to C1 critical
    func5 = lambda **kwargs: go_stage(go_from="hospital",
                                      go_to="critical",
                                      from_stage=3,
                                      to_stage=2,
                                      fraction=pHC,
                                      **kwargs)
                                      
    # move (100 * pHR)% of H2 hospital to R genpop
    # (1 - pHC) adjustment is due to ordering of events (so
    # operates on remainder from move above)
    func6 = lambda **kwargs: go_stage(go_from="hospital",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=4,
                                      fraction=pHR / (1 - pHC),
                                      **kwargs)
                                      
    # move remainder of H2 hospital to D genpop
    func7 = lambda **kwargs: go_stage(go_from="hospital",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=5,
                                      fraction=1.0,
                                      **kwargs)
                                      
    # move (100 * pCR)% of C2 critical to R genpop
    func8 = lambda **kwargs: go_stage(go_from="critical",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=4,
                                      fraction=pCR,
                                      **kwargs)
                                      
    # move remainder of C2 critical to D genpop
    func9 = lambda **kwargs: go_stage(go_from="critical",
                                      go_to="genpop",
                                      from_stage=3,
                                      to_stage=5,
                                      fraction=1.0,
                                      **kwargs)

    return [func1, func2, func3, func4, func5, func6, func7, func8, func9]
