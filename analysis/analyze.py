import houseofreps as hr
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
import os
import numpy as np
import argparse
from loguru import logger
import copy


@dataclass
class ResidentsPerRep(DataClassDictMixin):
    year: hr.Year
    fair: float
    residents_per_rep: Dict[hr.St, float]


def calculate_residents_per_rep_for_year(year: hr.Year) -> ResidentsPerRep:
    residents_per_rep = {}

    house = hr.HouseOfReps(
        year=year, 
        pop_type=hr.PopType.APPORTIONMENT
        )

    for st, state in house.states.items():
        if st != hr.St.DISTRICT_OF_COLUMBIA:
            residents_per_rep[st] = 1e6 * hr.ST_TRUE[st].year_to_pop[year].apportionment / state.no_reps.voting

    fair = 1e6 * house.get_total_us_pop(sts_exclude=[hr.St.DISTRICT_OF_COLUMBIA]) / 435.0
    return ResidentsPerRep(year=year, fair=fair, residents_per_rep=residents_per_rep)


def plot_residents_per_rep(rpr: ResidentsPerRep, show: bool):
    vals = sorted(rpr.residents_per_rep.items(), key=lambda x: x[1])

    xticks = [x[0].name for x in vals]
    x = list(range(len(rpr.residents_per_rep)))
    y = [x[1] for x in vals]

    fig = go.Figure()

    # Create a horizontal dashed line for 'fair'
    fig.add_shape(
        type="line",
        x0=0,
        x1=len(x),
        y0=rpr.fair,
        y1=rpr.fair,
        line=dict(color="black", dash="dash"),
        )

    def st_to_col(st_name: str):
        if st_name == hr.St.DELAWARE.name:
            return "blue"
        elif st_name == hr.St.WYOMING.name:
            return "red"
        else:
            return "lightgray"

    # Create a bar chart
    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            text=["{:d}k".format(int(yi/1000.0)) for yi in y],
            marker_color=[st_to_col(st) for st in xticks],
        )
    )

    # Make sure both bar plots can be shown
    fig.update_layout(barmode="overlay")

    # Update the x-axis tick labels and rotation
    fig.update_xaxes(tickvals=x, ticktext=xticks, tickangle=90)

    # Update the layout of the plot
    fig.update_layout(
        title=f'Number of state residents per representative ({rpr.year.value})',
        xaxis_title="State",
        yaxis_title="Number of Residents per Representative",
        height=600,
        width=1200,
        margin=dict(b=200),  # Adjust bottom margin to accommodate x-axis labels
        yaxis_range=[0,1150000]
    )

    # Save the plot as an HTML file
    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/no_residents_per_rep_{rpr.year.value}.jpg')

    if show:
        fig.show()

    return fig
    
def plot_residents_per_rep_frac(rprs: List[ResidentsPerRep], show: bool):
    mean_dat, std_dat, labels = [], [], []
    st_list = list(hr.St)
    for st in st_list:
        if st == hr.St.DISTRICT_OF_COLUMBIA:
            continue
        fracs = [ rpr.residents_per_rep[st] / rpr.fair for rpr in rprs ]
        mean = np.mean(fracs, dtype=float)
        std = np.std(fracs, dtype=float)
        mean_dat.append(mean)
        std_dat.append(std)
        if abs(1-mean) > 0.05 or std > 0.07:
            labels.append(st.value)
        else:
            labels.append("")

    def st_to_pos(st_value: str):
        if st_value == hr.St.NEW_MEXICO.value:
            return "top center"
        elif st_value == hr.St.NEBRASKA.value:
            return "middle left"
        else:
            return "bottom center"
    
    def st_to_col(st_value: str):
        if st_value == hr.St.DELAWARE.value:
            return "blue"
        elif st_value == hr.St.WYOMING.value:
            return "red"
        else:
            return "gray"

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=mean_dat,
            y=std_dat,
            mode='markers+text',
            showlegend=False,
            text=labels,
            textposition=[st_to_pos(st) for st in labels],
            marker_color=[st_to_col(st) for st in labels],
        )
    )
    fig.update_layout(
        title='Representation fraction<br>Num. state residents per rep. / fair representation',
        xaxis_title="Mean",
        yaxis_title="Std. dev.",
        height=600,
        width=800,
        font=dict(size=18),
    )
    fig.update_xaxes(range=[0.75,1.25])
    fig.update_yaxes(range=[0,0.23])
    fig.add_trace(
        go.Scatter(
            x=[1,1],
            y=[0,0.23],
            mode='lines',
            text=['Equal representation'],
            line=dict(color="black", dash="dash"),
            showlegend=False,
        )
    )

    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/no_residents_per_rep_frac.jpg')

    if show:
        fig.show()

    return fig


def get_state_population_rankings(year: hr.Year) -> List[Tuple[float, hr.St]]:
    rankings = []
    house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
    for st,state in house.states.items():
        if st == hr.St.DISTRICT_OF_COLUMBIA:
            continue
        rankings.append((state.pop,st))

    rankings.sort(key = lambda x: -x[0])
    return rankings


def plot_state_pop_rankings(year: hr.Year, show: bool):
    rankings = get_state_population_rankings(year)
    rpr = calculate_residents_per_rep_for_year(year)

    st_best_name = {}
    st_worst_name = {}
    st_best_name[year] = []
    st_worst_name[year] = []
    for st,count in rpr.residents_per_rep.items():
        frac = count / rpr.fair
        if frac < 1:
            st_best_name[year].append(st.name)
        else:
            st_worst_name[year].append(st.name)

    fig = go.Figure()

    xticks = [p[1].name for p in rankings]
    x = np.arange(0,len(xticks))
    y = [1e6*p[0] for p in rankings]
    marker_color = ["blue" if xticks[i] in st_best_name[year] else "red" for i in range(len(xticks))]

    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            marker_color=marker_color,
            showlegend=False,
        )
    )

    # Update the x-axis tick labels and rotation
    fig.update_xaxes(tickvals=x, ticktext=xticks, tickangle=90)

    # Empty traces for the legend
    fig.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            name="Overrepresented",
            marker_color="blue",
        )
    )
    fig.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            name="Underrepresented",
            marker_color="red",
        )
    )

    fig.update_layout(
        title='State population rankings (%s)' % year.value,
        xaxis_title="State",
        yaxis_title="Population",
        height=600,
        width=1400,
        font=dict(size=18),
    )

    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/state_pop_rankings_%s.jpg' % year.value)

    if show:
        fig.show()


def plot_rankings_fracs_for_year(year: hr.Year, show: bool):
    rpr = calculate_residents_per_rep_for_year(year)
    rankings = get_state_population_rankings(year)

    x,y,xticks = [],[],[]
    for i,(pop,st) in enumerate(rankings):
        x.append(i)
        y.append(rpr.residents_per_rep[st]/rpr.fair)
        xticks.append(st.name)

    fig = go.Figure()    
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode='markers+lines',
            showlegend=False,
            marker=dict(color=["blue" if yi < 1 else "red" for yi in y], size=10),
            line=dict(color="black", dash="dash")
            )
        )
    
    # Update the x-axis tick labels and rotation
    fig.update_xaxes(tickvals=x, ticktext=xticks, tickangle=90)

    # Horizontal line for fair
    fig.add_trace(
        go.Scatter(
            x=[0,len(x)],
            y=[1,1],
            mode='lines',
            showlegend=False,
            line=dict(color="black", dash="dash")
            )
        )

    # Empty traces for the legend
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            name="Overrepresented",
            marker_color="blue",
            mode='markers',
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            name="Underrepresented",
            marker_color="red",
            mode='markers',
        )
    )

    fig.update_layout(
        title='State population rankings (%s)' % year.value,
        xaxis_title="State ranked by population (highest to lowest)",
        yaxis_title="Representation fraction (fair = 1)",
        height=600,
        width=1400,
        font=dict(size=18),
        yaxis_range=[0.5,1.5],
        )
    
    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/state_pop_rankings_frac_%s.jpg' % year.value)

    if show:
        fig.show()


def plot_rankings_fracs_ave(show: bool):
    fig = go.Figure()

    x = None
    ymean: np.ndarray = np.array([], dtype=float)
    for year in hr.Year:
        rpr = calculate_residents_per_rep_for_year(year)
        rankings = get_state_population_rankings(year)

        x,y = [],[]
        for i,(pop,st) in enumerate(rankings):
            x.append(i)
            y.append(rpr.residents_per_rep[st]/rpr.fair)
        if len(ymean) == 0:
            ymean = np.array(y)
        else:
            ymean += np.array(y)

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode='lines',
                showlegend=False,
                line=dict(color="lightgray")
                )
            )
    
    # Plot mean
    assert x is not None
    ymean /= int(len(list(hr.Year)))
    fig.add_trace(
        go.Scatter(
            x=x,
            y=ymean,
            mode='lines',
            showlegend=False,
            line=dict(color="blue")
            )
        )
        
    # Horizontal line for fair
    fig.add_trace(
        go.Scatter(
            x=[0,len(x)],
            y=[1,1],
            mode='lines',
            showlegend=False,
            line=dict(color="black", dash="dash")
            )
        )

    fig.update_layout(
        title='The population ranking trap',
        xaxis_title="State ranked by population (highest to lowest)",
        yaxis_title="Representation fraction (fair = 1)",
        height=600,
        width=1400,
        font=dict(size=18),
        yaxis_range=[0.5,1.5],
        )
        
    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/state_pop_rankings_frac_ave.jpg')

    if show:
        fig.show()


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


def plot_add_remove(st_to_pop_shift_for_add: Dict[hr.St,float], st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]], show: bool):
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
        title='Population shift required to add or lose a representative',
        xaxis_title="State",
        yaxis_title="Population shift required (millions)",
        height=600,
        width=800,
        font=dict(size=20),
        )

    if show:
        fig.show()


def plot_add_remove_bars(st_to_pop_shift_for_add: Dict[hr.St,float], st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]], show: bool):
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
        title='Population shift required to add or lose a representative',
        xaxis_title="State",
        yaxis_title="Population shift required (millions)",
        height=600,
        width=1600,
        font=dict(size=18),
        )

    if show:
        fig.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=["rpr", "rpr-frac", "pop-rankings", "rankings-fracs", "add-rep"])
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    if args.command == "rpr":

        for year in hr.Year:
            rpr = calculate_residents_per_rep_for_year(year)
            plot_residents_per_rep(rpr, args.show)

    elif args.command == "rpr-frac":
        rprs = []
        for year in hr.Year:
            rpr = calculate_residents_per_rep_for_year(year)
            rprs.append(rpr)

        plot_residents_per_rep_frac(rprs, args.show)
    
    elif args.command == "pop-rankings":
        for year in hr.Year:
            plot_state_pop_rankings(year, args.show)

    elif args.command == "rankings-fracs":
        for year in hr.Year:
            plot_rankings_fracs_for_year(year, args.show)
        plot_rankings_fracs_ave(args.show)

    elif args.command == "add-rep":

        st_list = list(hr.St)
        st_list = [st for st in st_list if st != hr.St.DISTRICT_OF_COLUMBIA]
        # st_list = st_list[:5]

        logger.info("--- Adding a representative ---")
        st_to_pop_shift_for_add: Dict[hr.St,float] = {}
        for st in st_list:

            # Three stage search: coarse to fine
            pop_shift_required = find_min_pop_shift_required_for_change_repr_hierarchical(hr.Year.YR2020, st, Target.ADD)
            assert pop_shift_required is not None, "Could not find a population shift that would add a representative to %s" % st.name
            st_to_pop_shift_for_add[st] = pop_shift_required
            logger.info("%s: %f million people need to be shifted into the state to add a representative" % (st.name, pop_shift_required))

        logger.info("--- Losing a representative ---")
        st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]] = {}
        for st in st_list:
            pop_shift_required = find_min_pop_shift_required_for_change_repr_hierarchical(hr.Year.YR2020, st, Target.LOSE)
            st_to_pop_shift_for_lose[st] = pop_shift_required
            if pop_shift_required is not None:
                logger.info("%s: %f million people need to be shifted out of the state to lose a representative" % (st.name, pop_shift_required))
            else:
                logger.info("%s: Cannot lose a representative because it only has one." % st.name)

        plot_add_remove_bars(st_to_pop_shift_for_add, st_to_pop_shift_for_lose, args.show)

    else:
        raise ValueError(f"Unknown command: {args.command}")
    