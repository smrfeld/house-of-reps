from .helpers import COL_OVER, COL_UNDER, COL_OVER_RGB, COL_UNDER_RGB
from .pop_rankings import get_state_population_rankings

import houseofreps as hr
import plotly.graph_objects as go
import os
import numpy as np
from loguru import logger


def plot_rankings_fracs_for_year(year: hr.Year, show: bool):
    rpr = hr.calculate_residents_per_rep_for_year(year)
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
            marker=dict(color=[COL_OVER if yi < 1 else COL_UNDER for yi in y], size=10),
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
            marker_color=COL_OVER,
            mode='markers',
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            name="Underrepresented",
            marker_color=COL_UNDER,
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
    logger.info(f"Saved plot to: plots/state_pop_rankings_frac_{year.value}.jpg")

    if show:
        fig.show()


def plot_rankings_fracs_ave(show: bool):
    fig = go.Figure()

    x = None
    ymean: np.ndarray = np.array([], dtype=float)
    for year in hr.Year:
        rpr = hr.calculate_residents_per_rep_for_year(year)
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
    logger.info(f"Saved plot to: plots/state_pop_rankings_frac_ave.jpg")

    if show:
        fig.show()


def plot_rankings_fracs_heat(show: bool):
    fig = go.Figure()

    y = None
    years = sorted(list(hr.Year), key=lambda year: year.value)
    year_to_ranking_delaware = {}
    for iyear,year in enumerate(years):
        rpr = hr.calculate_residents_per_rep_for_year(year)
        rankings = get_state_population_rankings(year)

        y,z = [],[]
        for i,(pop,st) in enumerate(reversed(rankings)):
            y.append(i)
            frac = rpr.residents_per_rep[st]/rpr.fair
            if frac > 1:
                z.append(0)
            else:
                z.append(1)

            if st == hr.St.DELAWARE:
                year_to_ranking_delaware[year] = i

        custom_colorscale = [
            [0, 'rgba(%d, %d, %d, 0.35)' % COL_UNDER_RGB],
            [1, 'rgba(%d, %d, %d, 0.35)' % COL_OVER_RGB]
        ]

        # Heat map
        fig.add_trace(
            go.Heatmap(
                x=[iyear]*len(y),
                y=y,
                z=z,
                # colorscale='Bluered',
                colorscale=custom_colorscale,
                showscale=False,
                )
            )

    # Line plot for delaware
    fig.add_trace(
        go.Scatter(
            x=list(range(len(list(years)))),
            y=[year_to_ranking_delaware[year] for year in years],
            mode='lines+markers',
            marker=dict(color="black", size=12),
            line=dict(color="black", width=3),
            name="Delaware"
            )
        )

    # Set x ticks to the years
    fig.update_xaxes(tickvals=list(range(len(list(years)))), ticktext=[year.value for year in years])
    fig.update_yaxes(tickvals=[6,43], ticktext=["Lowest population", "Highest population"])
    fig.update_yaxes(tickangle=-90)

    # Add empty traces for the legend
    for name,col in [("Overrepresented", COL_OVER), ("Underrepresented", COL_UNDER)]:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                name=name,
                marker_color=col,
                mode='markers',
                marker=dict(size=12),
            )
        )

    fig.update_layout(
        title='The population ranking trap',
        yaxis_title="State ranked by population",
        xaxis_title="Year",
        height=900,
        width=1000,
        font=dict(size=18),
        showlegend=True,
        )    

    os.makedirs("plots", exist_ok=True)
    fig.write_image(f'plots/state_pop_rankings_frac_heat.jpg')
    logger.info(f"Saved plot to: plots/state_pop_rankings_frac_heat.jpg")

    if show:
        fig.show()
