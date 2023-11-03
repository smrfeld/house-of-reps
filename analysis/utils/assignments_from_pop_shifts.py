import houseofreps as hr
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from loguru import logger
import copy
import os


@dataclass
class ShiftedAssignments(DataClassDictMixin):
    year: hr.Year
    pop_shift_between_state_and_entire_us: float
    st_shift_to_from: hr.St
    states_after_shift: Dict[hr.St,hr.State]


def calculate_assignments_with_pop_shift(year: hr.Year, pop_shift: float, st_shift_to: hr.St) -> Optional[ShiftedAssignments]:
    house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
    try:
        hr.shift_pop_from_entire_us_to_state(
            hr=house,
            st_to=st_shift_to, 
            pop_shift_millions=pop_shift, 
            verbose=False
            )
    except hr.PopShiftIsMoreThanUsPop as e:
        logger.warning(str(e))
        return None
    except hr.PopShiftMakesStatePopNegative as e:
        logger.warning(str(e))
        return None

    # Assign house seats
    house.assign_house_seats_priority()

    # logger.debug(f"Number of reps in state {st_shift_to} is: {house.states[st_shift_to].no_reps.voting} after shifting {pop_shift_millions_from_entire_us_to_state} MM people to the state from the rest of the USA (pop is now: {house.states[st_shift_to].pop}).")

    return ShiftedAssignments(
        year=year,
        pop_shift_between_state_and_entire_us=pop_shift,
        st_shift_to_from=st_shift_to,
        states_after_shift=copy.deepcopy(house.states)
        )    

from enum import Enum
class Target(Enum):
    ADD = 1
    LOSE = 2


def find_min_pop_shift_required_for_change_repr(
    year: hr.Year, 
    st: hr.St, 
    search_resolution_millions: float, 
    target: Target,
    pop_shift_millions_start: float,
    pop_shift_millions_end: float
    ) -> Optional[float]:
    assert st is not hr.St.DISTRICT_OF_COLUMBIA, "Cannot add/lose a representative to DC"

    # Calculate initial number of reps
    house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
    house.assign_house_seats_priority()
    no_reps_initial = house.states[st].no_reps.voting

    if target == Target.LOSE and no_reps_initial == 1:
        logger.warning(f"Cannot lose a representative from {st} - true assignment has 1, which is the minimum.")
        return None

    pop_shift = pop_shift_millions_start
    if pop_shift > 0:
        pop_shift -= search_resolution_millions

    while (target == Target.ADD and pop_shift <= pop_shift_millions_end) or (target == Target.LOSE and pop_shift >= pop_shift_millions_end):
        pop_shift += search_resolution_millions

        shift = calculate_assignments_with_pop_shift(year, pop_shift, st)
        if shift is None:
            raise ValueError("Population of state would be negative. Cannot add/lose a representative.")
        
        no_reps = shift.states_after_shift[st].no_reps.voting
        if target == Target.ADD and no_reps == no_reps_initial + 1:
            return pop_shift
        elif target == Target.LOSE and no_reps == no_reps_initial - 1:
            return pop_shift
        elif no_reps == no_reps_initial:
            pass
        else:
            raise ValueError("Unexpected number of reps: %d after shifting population" % no_reps)

    raise RuntimeError(f"Could not find a population shift that would add/lose a representative to {st} - tried up to {pop_shift} million people")


def find_min_pop_shift_required_for_change_repr_hierarchical(
    year: hr.Year, 
    st: hr.St, 
    target: Target
    ) -> Optional[float]:

    search_resolution_1 = 0.01
    search_resolution_2 = 0.0001
    search_resolution_3 = 0.000001
    if target == Target.LOSE:
        search_resolution_1 = -search_resolution_1
        search_resolution_2 = -search_resolution_2
        search_resolution_3 = -search_resolution_3

    pop_shift_required = find_min_pop_shift_required_for_change_repr(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_1,
        pop_shift_millions_start=0, 
        pop_shift_millions_end=1.0 if target == Target.ADD else -1.0,
        target=target
        )
    if pop_shift_required is None:
        return None
    pop_shift_required = find_min_pop_shift_required_for_change_repr(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_2, 
        target=target,
        pop_shift_millions_start=pop_shift_required-search_resolution_1, 
        pop_shift_millions_end=pop_shift_required
        )
    if pop_shift_required is None:
        return None
    pop_shift_required = find_min_pop_shift_required_for_change_repr(
        year=year, 
        st=st, 
        search_resolution_millions=search_resolution_3, 
        target=target,
        pop_shift_millions_start=pop_shift_required-search_resolution_2, 
        pop_shift_millions_end=pop_shift_required
        )
    return pop_shift_required


def plot_shift_pop(year: hr.Year, show: bool):
    st_list = list(hr.St)
    st_list = [st for st in st_list if st != hr.St.DISTRICT_OF_COLUMBIA]

    logger.info("--- Adding a representative ---")
    st_to_pop_shift_for_add: Dict[hr.St,float] = {}
    for st in st_list:

        # Three stage search: coarse to fine
        pop_shift_required = find_min_pop_shift_required_for_change_repr_hierarchical(year, st, Target.ADD)
        assert pop_shift_required is not None, "Could not find a population shift that would add a representative to %s" % st.name
        st_to_pop_shift_for_add[st] = pop_shift_required
        logger.info("%s: %f million people need to be shifted into the state to add a representative" % (st.name, pop_shift_required))

    logger.info("--- Losing a representative ---")
    st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]] = {}
    for st in st_list:
        pop_shift_required = find_min_pop_shift_required_for_change_repr_hierarchical(year, st, Target.LOSE)
        st_to_pop_shift_for_lose[st] = pop_shift_required
        if pop_shift_required is not None:
            logger.info("%s: %f million people need to be shifted out of the state to lose a representative" % (st.name, pop_shift_required))
        else:
            logger.info("%s: Cannot lose a representative because it only has one." % st.name)

    plot_add_remove_bars(year, st_to_pop_shift_for_add, st_to_pop_shift_for_lose, show)


def plot_add_remove_scatter(year: hr.Year, st_to_pop_shift_for_add: Dict[hr.St,float], st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]], show: bool):
    st_list = list(st_to_pop_shift_for_add.keys())

    # Sort states for pretty plot ordering
    st_list.sort(key=lambda st: st_to_pop_shift_for_add[st])

    # Plot
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[st.name for st in st_list],
            y=[st_to_pop_shift_for_add[st] for st in st_list],
            name="Add a representative",
            mode='markers',
            marker_color="blue",
            marker=dict(size=10),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[st.name for st in st_list],
            y=[st_to_pop_shift_for_lose[st] for st in st_list],
            name="Lose a representative",
            mode='markers',
            marker_color="red",
            marker=dict(size=10),
        )
    )

    # Horizontal line at 0
    fig.add_trace(
        go.Scatter(
            x=[st.name for st in st_list],
            y=[0 for st in st_list],
            mode='lines',
            showlegend=False,
            line=dict(color="black", dash="dash")
        )
    )

    fig.update_layout(
        title='Population shift required to add or lose a representative (%s)' % year.value,
        xaxis_title="State",
        yaxis_title="Population shift required (millions)",
        height=600,
        width=800,
        font=dict(size=20),
        yaxis_range=[-0.8,0.8],
        )

    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/pop_shift_add_remove_scatter_%s.jpg' % year.value)
    logger.info(f"Saved plot to: plots/pop_shift_add_remove_scatter_{year.value}.jpg")

    if show:
        fig.show()


def plot_add_remove_bars(year: hr.Year, st_to_pop_shift_for_add: Dict[hr.St,float], st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]], show: bool):
    st_list = list(st_to_pop_shift_for_add.keys())

    # Sort states for pretty plot ordering
    st_list.sort(key=lambda st: st_to_pop_shift_for_add[st])

    # Plot
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[st.name for st in st_list],
            y=[st_to_pop_shift_for_add[st] for st in st_list],
            name="Add a representative",
        )
    )
    fig.add_trace(
        go.Bar(
            x=[st.name for st in st_list],
            y=[st_to_pop_shift_for_lose[st] for st in st_list],
            name="Lose a representative",
        )
    )

    # Overlap the bars
    fig.update_layout(barmode="overlay")

    fig.update_layout(
        title='Population shift required to add or lose a representative (%s)' % year.value,
        xaxis_title="State",
        yaxis_title="Population shift required (millions)",
        height=600,
        width=1600,
        font=dict(size=18),
        yaxis_range=[-0.8,0.8],
        )

    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/pop_shift_add_remove_%s.jpg' % year.value)
    logger.info(f"Saved plot to: plots/pop_shift_add_remove_{year.value}.jpg")

    if show:
        fig.show()
