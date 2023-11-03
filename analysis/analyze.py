import houseofreps as hr
import plotly.graph_objects as go
from typing import List, Dict, Tuple
from dataclasses import dataclass
from mashumaro import DataClassDictMixin
import os

@dataclass
class ResidentsPerRep(DataClassDictMixin):
    year: hr.Year
    fair: float
    residents_per_rep: Dict[str, float]


def calculate_residents_per_rep_for_year(year: hr.Year) -> ResidentsPerRep:
    residents_per_rep = {}

    house = hr.HouseOfReps(
        year=year, 
        pop_type=hr.PopType.APPORTIONMENT
        )

    for st, state in house.states.items():
        if st != hr.St.DISTRICT_OF_COLUMBIA:
            residents_per_rep[st.name] = 1e6 * hr.ST_TRUE[st].year_to_pop[year].apportionment / state.no_reps.voting

    fair = 1e6 * house.get_total_us_pop(sts_exclude=[hr.St.DISTRICT_OF_COLUMBIA]) / 435.0
    return ResidentsPerRep(year=year, fair=fair, residents_per_rep=residents_per_rep)


def plot_residents_per_rep(rpr: ResidentsPerRep):
    vals = sorted(rpr.residents_per_rep.items(), key=lambda x: x[1])

    xticks = [x[0] for x in vals]
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

    # Create a bar chart
    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            text=["{:d}k".format(int(yi/1000.0)) for yi in y],
            marker_color=["lightgray" if st != hr.St.DELAWARE.name else "blue" for st in xticks],
        )
    )

    # Make sure both bar plots can be shown
    fig.update_layout(barmode="overlay")

    # Update the x-axis tick labels and rotation
    fig.update_xaxes(tickvals=x, ticktext=xticks, tickangle=90)

    # Update the layout of the plot
    fig.update_layout(
        title=f'Number of state residents per representative - {rpr.year.value}',
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

    return fig
    

if __name__ == "__main__":
    for year in hr.Year:
        rpr = calculate_residents_per_rep_for_year(year)
        plot_residents_per_rep(rpr)