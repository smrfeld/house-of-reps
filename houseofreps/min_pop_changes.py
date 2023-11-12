from houseofreps.state import State, Year, PopType, St
from houseofreps.house import HouseOfReps
from houseofreps.population_shifts import shift_pop_from_entire_us_to_state, PopShiftIsMoreThanUsPop, PopShiftMakesStatePopNegative


from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from typing import Optional, Dict, List
from loguru import logger
import copy
from enum import Enum


@dataclass
class AssignmentsAfterChange(DataClassDictMixin):
    """Assignments after a change in population for one of the states

    Args:
        year (Year): Year
        pop_change_millions (float): Population change in the state. Can be positive or negative. Measured in millions of people.
        st_change (St): State whose population was changed
        states (Dict[St,State]): States after the change
    """    

    year: Year
    "Year"

    pop_change_millions: float
    "Population change in the state. Can be positive or negative. Measured in millions of people."

    st_change: St
    "State whose population was changed"

    states: Dict[St,State]
    "States after the change"


def calculate_assignments_with_pop_shift(year: Year, pop_shift_millions: float, st_shift_to_from: St) -> Optional[AssignmentsAfterChange]:
    """Calculate assignments after shifting population. The total US population is unchanged.

    Args:
        year (Year): Year
        pop_shift_millions (float): Population shift in millions
        st_shift_to_from (St): State to shift to/from

    Returns:
        Optional[AssignmentsAfterChange]: Assignments after change, if possible
    """    

    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    try:
        shift_pop_from_entire_us_to_state(
            house=house,
            st_to=st_shift_to_from, 
            pop_shift_millions=pop_shift_millions, 
            verbose=False
            )
    except PopShiftIsMoreThanUsPop as e:
        logger.warning(str(e))
        return None
    except PopShiftMakesStatePopNegative as e:
        logger.warning(str(e))
        return None

    # Assign house seats
    house.assign_house_seats_priority()

    return AssignmentsAfterChange(
        year=year,
        pop_change_millions=pop_shift_millions,
        st_change=st_shift_to_from,
        states=copy.deepcopy(house.states)
        )    


def calculate_assignments_with_pop_change(year: Year, pop_change_millions: float, st_change: St) -> Optional[AssignmentsAfterChange]:
    """Calculate assignments after changing population. Note: this is not the same as shifting population. This method increases or decreases the population of a state by a given amount, and hence the total US population is changed.

    Args:
        year (Year): Year
        pop_change_millions (float): Population change in millions
        st_change (St): State to change

    Returns:
        Optional[AssignmentsAfterChange]: Assignments after change, if possible
    """    
    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    house.states[st_change].pop += pop_change_millions

    # Assign house seats
    house.assign_house_seats_priority()

    return AssignmentsAfterChange(
        year=year,
        pop_change_millions=pop_change_millions,
        st_change=st_change,
        states=copy.deepcopy(house.states)
        )    


class Target(Enum):
    """Target to calculate the minimum population change required to add/lose a representative to a state
    """    

    ADD = "add"
    "Add a representative to a state"

    LOSE = "lose"
    "Lose a representative from a state"


class PopChangeMode(Enum):
    """Pop change mode for changing population of a state
    """    

    CHANGE_POP = "change_pop"
    "Change the population of the state. The total US population is changed."

    SHIFT_POP = "shift_pop"
    "Shift the population into/out of the state. The total US population is unchanged."


def find_min_pop_change_required_for_change_repr(
    year: Year, 
    st: St, 
    target: Target,
    pop_change_mode: PopChangeMode
    ) -> Optional[float]:
    """Find the minimum population change required to add/lose a representative to a state. The total US population is unchanged.

    Args:
        year (Year): Year
        st (St): State
        target (Target): Target
        pop_change_mode (PopChangeMode): Pop change mode

    Returns:
        Optional[float]: Population change required in millions, if possible
    """    
    search_resolution_1 = 10000
    search_resolution_2 = 100
    search_resolution_3 = 1
    if target == Target.LOSE:
        search_resolution_1 = -search_resolution_1
        search_resolution_2 = -search_resolution_2
        search_resolution_3 = -search_resolution_3

    pop_change_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution=search_resolution_1,
        pop_change_start=0, 
        pop_change_end=1000000 if target == Target.ADD else -1000000,
        target=target,
        pop_change_mode=pop_change_mode
        )
    if pop_change_required is None:
        return None
    pop_change_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution=search_resolution_2, 
        target=target,
        pop_change_start=pop_change_required-search_resolution_1, 
        pop_change_end=pop_change_required,
        pop_change_mode=pop_change_mode
        )
    if pop_change_required is None:
        return None
    pop_change_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution=search_resolution_3, 
        target=target,
        pop_change_start=pop_change_required-search_resolution_2, 
        pop_change_end=pop_change_required,
        pop_change_mode=pop_change_mode
        )
    if pop_change_required is None:
        return None
    return pop_change_required / 1e6


def _find_min_pop_change_required_for_change_grid_search(
    year: Year, 
    st: St, 
    search_resolution: int, 
    target: Target,
    pop_change_start: int,
    pop_change_end: int,
    pop_change_mode: PopChangeMode
    ) -> Optional[int]:
    """Find the minimum population change required to add/lose a representative to a state. The total US population is unchanged.

    Args:
        year (Year): Year
        st (St): State
        search_resolution (int): Search resolution, in raw population
        target (Target): Target
        pop_change_start (int): Population change start, in raw population
        pop_change_end (int): Population change end, in raw population
        pop_change_mode (PopChangeMode): Pop change mode

    Returns:
        Optional[int]: Population change required in millions, if possible
    """    

    assert st is not St.DISTRICT_OF_COLUMBIA, "Cannot add/lose a representative to DC"

    # Calculate initial number of reps
    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    house.assign_house_seats_priority()
    no_reps_initial = house.states[st].no_reps.voting

    if target == Target.LOSE and no_reps_initial == 1:
        # logger.warning(f"Cannot lose a representative from {st} - true assignment has 1, which is the minimum.")
        return None

    pop_change = pop_change_start
    if pop_change > 0:
        pop_change -= search_resolution

    while (target == Target.ADD and pop_change <= pop_change_end) or (target == Target.LOSE and pop_change >= pop_change_end):
        pop_change += search_resolution

        if pop_change_mode == PopChangeMode.CHANGE_POP:
            assignments = calculate_assignments_with_pop_change(year, pop_change/1e6, st)
        elif pop_change_mode == PopChangeMode.SHIFT_POP:
            assignments = calculate_assignments_with_pop_shift(year, pop_change/1e6, st)
        else:
            raise NotImplementedError(f"Unexpected pop_change_mode: {pop_change_mode}")
        if assignments is None:
            raise ValueError("Population of state would be negative. Cannot add/lose a representative.")
        
        no_reps = assignments.states[st].no_reps.voting
        if target == Target.ADD and no_reps == no_reps_initial + 1:
            return pop_change
        elif target == Target.LOSE and no_reps == no_reps_initial - 1:
            return pop_change
        elif no_reps == no_reps_initial:
            pass
        else:
            raise ValueError("Unexpected number of reps: %d after changing population" % no_reps)

    raise RuntimeError(f"Could not find a population change that would add/lose a representative to {st} - tried up to {pop_change} million people")