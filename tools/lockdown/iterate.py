# Moved imports to local space

def get_lockdown_state(population):
    if not hasattr(population, "lockdown_state"):
        population.lockdown_state = -1
        population.is_locked_down = False

    if population.total > 5000:
        if population.lockdown_state == -1:
            print(f"Lockdown started on {population.date}")
            population.lockdown_state = 0
            population.is_locked_down = True

        elif population.lockdown_state > 0:
            print(f"Restarting lockdown on {population.date}")
            population.lockdown_state = 0
            population.is_locked_down = True

    elif population.total > 3000:
        if population.lockdown_state == 2:
            print(f"Re-entering relaxed (yellow) on {population.date}")
            population.lockdown_state = 1

    elif population.total < 2000:
        if population.lockdown_state == 0:
            print(f"Entering relaxed (yellow) on {population.date}")
            population.lockdown_state = 1

    elif population.total < 1000:
        if population.lockdown_state == 1:
            print(f"Entering relaxed (green) on {population.date}")
            population.lockdown_state = 2

    return population.lockdown_state

def advance_lockdown(network, population, **kwargs):
    from metawards.iterators import advance_infprob
    from metawards.iterators import advance_play
    from metawards.iterators import advance_fixed

    params = network.params
    state = get_lockdown_state(population)
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
    state = get_lockdown_state(population)

    if population.is_locked_down:
        print("Locked down")
        return [advance_lockdown]
    else:
        print("Normal working week day")
        return iterate_working_week(network=network,
                                    population=population,
                                    **kwargs)