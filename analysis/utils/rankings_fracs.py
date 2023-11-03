from .residents_per_rep import calculate_residents_per_rep_for_year
from .pop_rankings import get_state_population_rankings

import houseofreps as hr
import plotly.graph_objects as go
import os
import numpy as np


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
