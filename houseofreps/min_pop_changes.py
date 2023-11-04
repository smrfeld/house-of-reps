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
    year: Year
    pop_change: float
    st_change: St
    states: Dict[St,State]


def calculate_assignments_with_pop_shift(year: Year, pop_shift: float, st_shift_to_from: St) -> Optional[AssignmentsAfterChange]:
    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    try:
        shift_pop_from_entire_us_to_state(
            house=house,
            st_to=st_shift_to_from, 
            pop_shift_millions=pop_shift, 
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
        pop_change=pop_shift,
        st_change=st_shift_to_from,
        states=copy.deepcopy(house.states)
        )    


def calculate_assignments_with_pop_change(year: Year, pop_change: float, st_change: St) -> Optional[AssignmentsAfterChange]:
    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    house.states[st_change].pop += pop_change

    # Assign house seats
    house.assign_house_seats_priority()

    return AssignmentsAfterChange(
        year=year,
        pop_change=pop_change,
        st_change=st_change,
        states=copy.deepcopy(house.states)
        )    



class Target(Enum):
    ADD = "add"
    LOSE = "lose"


class PopChangeMode(Enum):
    CHANGE_POP = "change_pop"
    SHIFT_POP = "shift_pop"


def find_min_pop_shift_required_for_change_repr(
    year: Year, 
    st: St, 
    target: Target,
    pop_change_mode: PopChangeMode
    ) -> Optional[float]:

    search_resolution_1 = 0.01
    search_resolution_2 = 0.0001
    search_resolution_3 = 0.000001
    if target == Target.LOSE:
        search_resolution_1 = -search_resolution_1
        search_resolution_2 = -search_resolution_2
        search_resolution_3 = -search_resolution_3

    pop_shift_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_1,
        pop_change_millions_start=0, 
        pop_change_millions_end=1.0 if target == Target.ADD else -1.0,
        target=target,
        pop_change_mode=pop_change_mode
        )
    if pop_shift_required is None:
        return None
    pop_shift_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_2, 
        target=target,
        pop_change_millions_start=pop_shift_required-search_resolution_1, 
        pop_change_millions_end=pop_shift_required,
        pop_change_mode=pop_change_mode
        )
    if pop_shift_required is None:
        return None
    pop_shift_required = _find_min_pop_change_required_for_change_grid_search(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_3, 
        target=target,
        pop_change_millions_start=pop_shift_required-search_resolution_2, 
        pop_change_millions_end=pop_shift_required,
        pop_change_mode=pop_change_mode
        )
    return pop_shift_required


def _find_min_pop_change_required_for_change_grid_search(
    year: Year, 
    st: St, 
    search_resolution_millions: float, 
    target: Target,
    pop_change_millions_start: float,
    pop_change_millions_end: float,
    pop_change_mode: PopChangeMode
    ) -> Optional[float]:
    assert st is not St.DISTRICT_OF_COLUMBIA, "Cannot add/lose a representative to DC"

    # Calculate initial number of reps
    house = HouseOfReps(year=year, pop_type=PopType.APPORTIONMENT)
    house.assign_house_seats_priority()
    no_reps_initial = house.states[st].no_reps.voting

    if target == Target.LOSE and no_reps_initial == 1:
        # logger.warning(f"Cannot lose a representative from {st} - true assignment has 1, which is the minimum.")
        return None

    pop_change = pop_change_millions_start
    if pop_change > 0:
        pop_change -= search_resolution_millions

    while (target == Target.ADD and pop_change <= pop_change_millions_end) or (target == Target.LOSE and pop_change >= pop_change_millions_end):
        pop_change += search_resolution_millions

        if pop_change_mode == PopChangeMode.CHANGE_POP:
            assignments = calculate_assignments_with_pop_change(year, pop_change, st)
        elif pop_change_mode == PopChangeMode.SHIFT_POP:
            assignments = calculate_assignments_with_pop_shift(year, pop_change, st)
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