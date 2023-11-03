from .residents_per_rep import calculate_residents_per_rep_for_year

import houseofreps as hr
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Optional
import os
import numpy as np


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
