from .helpers import COL_OVER, COL_UNDER

import houseofreps as hr
import plotly.graph_objects as go
from typing import List, Dict
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
import os
import numpy as np
from loguru import logger


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


def plot_residents_per_rep(year: hr.Year, show: bool):
    rpr = calculate_residents_per_rep_for_year(year)

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
            return COL_UNDER
        elif st_name == hr.St.WYOMING.name:
            return COL_OVER
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
    logger.info(f"Saved plot to: plots/no_residents_per_rep_{rpr.year.value}.jpg")

    if show:
        fig.show()

    return fig
    
def plot_residents_per_rep_frac(show: bool):
    rprs = []
    for year in hr.Year:
        rpr = calculate_residents_per_rep_for_year(year)
        rprs.append(rpr)

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
            return COL_UNDER
        elif st_value == hr.St.WYOMING.value:
            return COL_OVER
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
        xaxis_title="Mean fraction (%s)" % hr.Year.range_str,
        yaxis_title="Std. dev. of fraction (%s)" % hr.Year.range_str,
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
    logger.info(f"Saved plot to: plots/no_residents_per_rep_frac.jpg")

    if show:
        fig.show()

    return fig

