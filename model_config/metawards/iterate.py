#
# Lock-down iterator that simulates various control measures for Covid-19
#

from datetime import datetime
from metawards.utils import Console


# Determine the lock-down status based on the population and current network
# TODO: Now MetaWards accepts dates, so we might be able to simplify this
def get_lock_down_vars(network, population):

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
    rate = 1.0
    if date >= lock_1:
        state += 1
        rate = params["lock_1_restrict"]
    if date >= lock_2:
        state += 1
        rate = (1.0 - ((1.0 - params["lock_1_restrict"]) * params["lock_2_release"]))

    can_work = params["can_work"][state]
    return state, rate, can_work


#
# Advance in a lock-down state
#
def advance_lock_down(network, population, **kwargs):

    from metawards.iterators import advance_infprob
    from metawards.iterators import advance_play
    from metawards.iterators import advance_fixed

    state, rate, can_work = get_lock_down_vars(network, population)

    advance_infprob(scale_rate=rate, network=network, population=population, **kwargs)
    advance_play(network=network, population=population, **kwargs)
    if can_work:
        advance_fixed(network=network, population=population, **kwargs)


#
# Iterate as normal, unless it is past a lock-down date
#
def iterate_custom(network, population, **kwargs):
    
    from metawards.iterators import iterate_working_week

    state, rate, can_work = get_lock_down_vars(network, population)
    Console.print(f"state {state}: scale_rate = {rate}, can_work = {can_work}")    
    
    if state > 0:
        return [advance_lock_down]
    else:    
        return iterate_working_week(network=network, population=population, **kwargs)