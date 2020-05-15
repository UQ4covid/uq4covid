# Moved imports to local space


def get_lockdown_state(network, population):
    from datetime import datetime

    date = population.date
    params = network.params.user_params

    y1 = int(params["lockdown_date_1_year"])
    m1 = int(params["lockdown_date_1_month"])
    d1 = int(params["lockdown_date_1_day"])

    y2 = int(params["lockdown_date_2_year"])
    m2 = int(params["lockdown_date_2_month"])
    d2 = int(params["lockdown_date_2_day"])

    # Lock down dates
    lock_1 = datetime(y1, m1, d1).date()
    lock_2 = datetime(y2, m2, d2).date()
    
    state = 0
    if date >= lock_1:
        state += 1
    if date >= lock_2:
        state += 1

    return state

def advance_lockdown(network, population, **kwargs):
    from metawards.iterators import advance_infprob
    from metawards.iterators import advance_play
    from metawards.iterators import advance_fixed

    params = network.params
    state = get_lockdown_state(network, population)
    scale_rate = params.user_params["scale_rate"][state]
    can_work = params.user_params["can_work"][state]
    print(f"Lockdown {state}: scale_rate = {scale_rate}, can_work = {can_work}")

    advance_infprob(scale_rate=scale_rate,
                    network=network, population=population,
                    **kwargs)
    advance_play(network=network, population=population,
                **kwargs)

    if can_work:
        advance_fixed(network=network, population=population,
                    **kwargs)

def iterate_custom(network, population, **kwargs):
    from metawards.iterators import iterate_working_week

    params = network.params
	
    state = get_lockdown_state(network, population)
    print("Simulation date " + str(population.date) + " lockdown state " + str(state))

    if state > 0:
        print("Locked down: stage " + str(state))
        return [advance_lockdown]
    else:
        print("Normal working week day")
        return iterate_working_week(network=network,
                                    population=population,
                                    **kwargs)