from houseofreps.house import St, HouseOfReps
from loguru import logger


def shift_pop_from_state_to_entire_us(hr: HouseOfReps, st_from : St, percent_of_st_from : float, verbose: bool):
    """Shift population from state to the entire US evenly

    Args:
        st_from (St): State to shift from
        percent_of_st_from (float): Percent in [0,1] to shift
        verbose (bool): True for verbose
    """
    assert (percent_of_st_from >= 0)
    assert (percent_of_st_from <= 1)

    # No people to remove
    state_from = hr.states[st_from]
    no_leave = state_from.pop_assigned * percent_of_st_from

    # Remove pop from this state
    state_from.pop_assigned -= no_leave

    # Calculate pop fracs for all the other states
    total_other_pop = hr.get_total_us_pop_assigned(sts_exclude=[st_from])
    for st_other, state_other in hr.states.items():
        if st_from == st_other:
            continue # skip

        frac = state_other.pop_assigned / total_other_pop

        # Increment pop of other states
        state_other.pop_assigned += frac * no_leave

    if verbose:
        hr.log_pops("pops after: %f million people move from: %s to entire US" % (no_leave, st_from))


def shift_pop_from_entire_us_to_state_by_global_percentage(hr: HouseOfReps, st_to: St, percent_of_entire_us : float, verbose: bool):
    """Shift population from the entire US to a state evenly, where the percentage refers to a fraction of the total USA

    Args:
        st_to (St): State to shift to
        percent_of_entire_us (int): Percentage in [0,1] to shift of the entire US pop
        verbose (bool): True for verbose
    """
    assert (percent_of_entire_us >= 0)
    assert (percent_of_entire_us <= 1)

    total_other_pop = hr.get_total_us_pop_assigned(sts_exclude=[st_to])
    no_leave = total_other_pop * percent_of_entire_us

    # Add pop to this state
    state_to = hr.states[st_to]
    state_to.pop_assigned += no_leave

    # Calculate pop fracs for all the other states
    for st_other, state_other in hr.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop_assigned / total_other_pop

        # Increment pop of other states
        state_other.pop_assigned -= frac * no_leave

    if verbose:
        hr.log_pops("pops after: %f million people move from entire US to: %s" % (no_leave, st_to))


def shift_pop_from_entire_us_to_state_by_local_percentage(hr: HouseOfReps, st_to : St, percent_of_st_to : float, verbose: bool):
    """Shift population from the entire USA by a percentage of the state shifting to

    Args:
        st_to (St): State to shift to
        percent_of_st_to (float): Percentage in [0,1] to shift of the st_to population
        verbose (bool): True for verbose
    """

    # Add pop to this state
    state_to = hr.states[st_to]
    no_add = state_to.pop_assigned * percent_of_st_to
    
    # Check enough people in USA
    total_other_pop = hr.get_total_us_pop_assigned(sts_exclude=[st_to])
    assert no_add <= total_other_pop

    # Move people to the state
    state_to.pop_assigned += no_add

    # Remove from rest of USA
    for st_other, state_other in hr.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop_assigned / total_other_pop

        # Increment pop of other states
        state_other.pop_assigned -= frac * no_add

    if verbose:
        hr.log_pops("pops after: %f million people move from entire US to: %s" % (no_add, st_to))


def shift_pop_from_entire_us_to_state(hr: HouseOfReps, st_to : St, pop_shift_millions : float, verbose: bool):
    """Shift population from entire USA to a state

    Args:
        st_to (St): State to shift to
        pop_shift_millions (float): Population in millions to shift from entire USA
        verbose (bool): True for verbose

    Raises:
        ValueError: If the population to shift is larger than the state's population
    """

    # Add pop to this state
    state_to = hr.states[st_to]
    
    # Check enough people in USA
    total_other_pop = hr.get_total_us_pop_assigned(sts_exclude=[st_to])
    assert pop_shift_millions <= total_other_pop

    # Check enough people in state
    if state_to.pop_assigned + pop_shift_millions < 0:
        raise ValueError("Trying to remove: %f people from state: %s but this is more than the number of people in the state: %f." 
            % (pop_shift_millions, st_to, state_to.pop_assigned))

    # Move people to the state
    state_to.pop_assigned += pop_shift_millions

    # Remove from rest of USA
    for st_other, state_other in hr.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop_assigned / total_other_pop

        # Increment pop of other states
        state_other.pop_assigned -= frac * pop_shift_millions

    if verbose:
        hr.log_pops("pops after: %f million people move from entire US to: %s" % (pop_shift_millions, st_to))


def shift_pop_from_state_to_state(hr: HouseOfReps, st_from : St, st_to : St, percent : float, verbose: bool):
    """Shift population from one state to another

    Args:
        st_from (St): State to shift from
        st_to (St): State to shift to
        percent (float): Percent in [0,1] to shift
        verbose (bool): True for verbose
    """
    assert (percent >= 0)
    assert (percent <= 1)

    state_from = hr.states[st_from]
    state_to = hr.states[st_to]

    # No people to remove
    no_leave = state_from.pop_assigned * percent

    # Remove pop from this state
    state_from.pop_assigned -= no_leave
    state_to.pop_assigned += no_leave

    if verbose:
        logger.info("----------")
        logger.info("pops after: %f million people move from: %s to: %s" % (no_leave, st_from, st_to))
        logger.info("%20s : %.5f" % (state_from.st, state_from.pop_assigned))
        logger.info("%20s : %.5f" % (state_to.st, state_to.pop_assigned))
        logger.info("----------")
