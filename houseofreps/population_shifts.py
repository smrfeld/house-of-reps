from houseofreps.house import St, HouseOfReps, Year, PopType
from houseofreps.validate import validate_total_us_pop_assigned_correct
from loguru import logger


def shift_pop_from_state_to_entire_us(house: HouseOfReps, st_from : St, percent_of_st_from : float, verbose: bool):
    """Shift population from a state to the entire US. The total US population is unchanged. The percentage refers to a fraction of the state shifting from. The populaton is shifted to the rest of the US proportionally by each state's population. The idea is that every person leaving the state has a chance of moving to any other state weighted by that state's population.

    Args:
        house (HouseOfReps): House of reps
        st_from (St): State to shift from
        percent_of_st_from (float): Percentage in [0,1] to shift of the st_from population
        verbose (bool): True for verbose
    """        
    assert (percent_of_st_from >= 0)
    assert (percent_of_st_from <= 1)

    # No people to remove
    state_from = house.states[st_from]
    no_leave = state_from.pop * percent_of_st_from

    # Remove pop from this state
    state_from.pop -= no_leave

    # Calculate pop fracs for all the other states
    total_other_pop = house.get_total_us_pop(sts_exclude=[st_from])
    for st_other, state_other in house.states.items():
        if st_from == st_other:
            continue # skip

        frac = state_other.pop / total_other_pop

        # Increment pop of other states
        state_other.pop += frac * no_leave

    if verbose:
        house.log_pops("pops after: %f million people move from: %s to entire US" % (no_leave, st_from))

    # Check no people have been lost
    validate_total_us_pop_assigned_correct(house, pop_type=PopType.APPORTIONMENT)


def shift_pop_from_entire_us_to_state_by_global_percentage(house: HouseOfReps, st_to: St, percent_of_entire_us : float, verbose: bool):
    """Shift population from the entire USA by a percentage of the entire US population. The total US population is unchanged. The percentage refers to a fraction of the entire US population. The populaton is shifted to the state proportionally by each state's population.

    Args:
        house (HouseOfReps): House of reps
        st_to (St): State to shift to
        percent_of_entire_us (float): Percentage in [0,1] to shift of the entire US population
        verbose (bool): True for verbose
    """    
    assert (percent_of_entire_us >= 0)
    assert (percent_of_entire_us <= 1)

    total_other_pop = house.get_total_us_pop(sts_exclude=[st_to])
    no_leave = total_other_pop * percent_of_entire_us

    # Add pop to this state
    state_to = house.states[st_to]
    state_to.pop += no_leave

    # Calculate pop fracs for all the other states
    for st_other, state_other in house.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop / total_other_pop

        # Increment pop of other states
        state_other.pop -= frac * no_leave

    if verbose:
        house.log_pops("pops after: %f million people move from entire US to: %s" % (no_leave, st_to))

    # Check no people have been lost
    validate_total_us_pop_assigned_correct(house, pop_type=PopType.APPORTIONMENT)


def shift_pop_from_entire_us_to_state_by_local_percentage(house: HouseOfReps, st_to : St, percent_of_st_to : float, verbose: bool):
    """Shift population from the entire USA by a percentage of the state's population. The total US population is unchanged. The percentage refers to a fraction of the state shifting to. The populaton is shifted to the state proportionally by each state's population.

    Args:
        house (HouseOfReps): House of reps
        st_to (St): State to shift to
        percent_of_st_to (float): Percentage in [0,1] to shift of the st_to population
        verbose (bool): True for verbose
    """    

    # Add pop to this state
    state_to = house.states[st_to]
    no_add = state_to.pop * percent_of_st_to
    
    # Check enough people in USA
    total_other_pop = house.get_total_us_pop(sts_exclude=[st_to])
    assert no_add <= total_other_pop

    # Move people to the state
    state_to.pop += no_add

    # Remove from rest of USA
    for st_other, state_other in house.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop / total_other_pop

        # Increment pop of other states
        state_other.pop -= frac * no_add

    if verbose:
        house.log_pops("pops after: %f million people move from entire US to: %s" % (no_add, st_to))

    # Check no people have been lost
    validate_total_us_pop_assigned_correct(house, pop_type=PopType.APPORTIONMENT)


class PopShiftIsMoreThanUsPop(Exception):
    """Exception raised when trying to shift more people than are in the entire USA
    """    

    def __init__(self, st_to : St, pop_shift_millions : float, total_other_pop : float):
        self.st_to = st_to
        self.pop_shift_millions = pop_shift_millions
        self.total_other_pop = total_other_pop
    
    def __str__(self):
        return "Trying to move: %f people into state: %s from the rest of the US - but this is more than the number of people in the USA: %f." % (self.pop_shift_millions, self.st_to, self.total_other_pop)


class PopShiftMakesStatePopNegative(Exception):
    """Exception raised when trying to shift people from a state, but this makes the state population negative
    """    

    def __init__(self, st_to : St, pop_shift_millions : float, state_to_pop : float):
        self.st_to = st_to
        self.pop_shift_millions = pop_shift_millions
        self.state_to_pop = state_to_pop
    
    def __str__(self):
        return "Trying to move: %f people into state: %s from the rest of the US - but this makes the state population negative: %f." % (self.pop_shift_millions, self.st_to, self.state_to_pop)


def shift_pop_from_entire_us_to_state(house: HouseOfReps, st_to : St, pop_shift_millions : float, verbose: bool):
    """Shift population from the entire USA to a state. The total US population is unchanged. The population is shifted to the state proportionally by each state's population.

    Args:
        house (HouseOfReps): House of reps
        st_to (St): State to shift to
        pop_shift_millions (float): Population shift in millions
        verbose (bool): True for verbose

    Raises:
        PopShiftIsMoreThanUsPop: Trying to shift more people than are in the entire USA
        PopShiftMakesStatePopNegative: Trying to shift people from a state, but this makes the state population negative
    """    

    # Add pop to this state
    state_to = house.states[st_to]
    
    # Check enough people in USA
    total_other_pop = house.get_total_us_pop(sts_exclude=[st_to])
    if pop_shift_millions > total_other_pop:
        raise PopShiftIsMoreThanUsPop(st_to, pop_shift_millions, total_other_pop)

    # Check enough people in state
    if state_to.pop + pop_shift_millions < 0:
        raise PopShiftMakesStatePopNegative(st_to, pop_shift_millions, state_to.pop)

    # Move people to the state
    state_to.pop += pop_shift_millions

    # Remove from rest of USA
    for st_other, state_other in house.states.items():
        if st_to == st_other:
            continue # skip

        frac = state_other.pop / total_other_pop

        # Increment pop of other states
        state_other.pop -= frac * pop_shift_millions

    if verbose:
        house.log_pops("pops after: %f million people move from entire US to: %s" % (pop_shift_millions, st_to))

    # Check no people have been lost
    validate_total_us_pop_assigned_correct(house, pop_type=PopType.APPORTIONMENT)


def shift_pop_from_state_to_state(house: HouseOfReps, st_from : St, st_to : St, percent : float, verbose: bool):
    """Shift population from one state to another. The total US population is unchanged. The percentage refers to a fraction of the state shifting from. The populaton is shifted to the state proportionally by each state's population.

    Args:
        house (HouseOfReps): House of reps
        st_from (St): State to shift from
        st_to (St): State to shift to
        percent (float): Percentage in [0,1] to shift of the st_from population
        verbose (bool): True for verbose
    """    
    assert (percent >= 0)
    assert (percent <= 1)

    state_from = house.states[st_from]
    state_to = house.states[st_to]

    # No people to remove
    no_leave = state_from.pop * percent

    # Remove pop from this state
    state_from.pop -= no_leave
    state_to.pop += no_leave

    if verbose:
        logger.info("----------")
        logger.info("pops after: %f million people move from: %s to: %s" % (no_leave, st_from, st_to))
        logger.info("%20s : %.5f" % (state_from.st, state_from.pop))
        logger.info("%20s : %.5f" % (state_to.st, state_to.pop))
        logger.info("----------")

    # Check no people have been lost
    validate_total_us_pop_assigned_correct(house, pop_type=PopType.APPORTIONMENT)