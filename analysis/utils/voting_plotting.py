from .voting import AnalyzeVotingResults

import houseofreps as hr
from loguru import logger
from dataclasses import dataclass
from typing import List, Optional
import plotly.graph_objects as go
import os

def plot_voting_results(
    avr: AnalyzeVotingResults,
    show: bool
    ):
    # Plot as table
    fig = go.Figure()

    # Create a function to determine the text color based on the comparison
    def get_text_color(old_value, new_value):
        if new_value > old_value:
            return 'green'
        elif new_value < old_value:
            return 'red'
        else:
            return 'black'

    # Headers
    headers = ["Congress", "Roll number", "Bill number", "Vote question", "Vote description", "Actual result", "Fractional result", "Actual Yea/Nay", "Fractional Yea/Nay"]

    # Values
    congress_rollnumber = [ (rr.roll.congress, rr.roll.rollnumber) for rr in avr.rolls_flipped_decisions ]
    congress_rollnumber.sort(key=lambda x: str(x[0]) + str(x[1]))
    values = []
    for header in headers:
        if header == "Congress":
            values.append([x[0] for x in congress_rollnumber])
        elif header == "Roll number":
            values.append([x[1] for x in congress_rollnumber])

    fig.add_trace(
        go.Table(
            header=dict(values=headers, align='left'),
            cells=dict(
                values=values, 
                # font=dict(color=[[],[],[get_text_color(x[0], x[1]) for x in st_to_old_new.values()]]),
                align='left',
                height=50
            )
        ))

    fig.update_layout(
        # title='House seat changes due to Post-Enumeration Survey (PES) (%s)' % (year.value),
        height=400,
        width=1200,
        font=dict(size=18),
        )
    
    os.makedirs("plots", exist_ok=True)
    # fname = 'plots/pes_survey_table_%s.jpg' % (year.value)
    # fig.write_image(fname)
    # logger.info(f"Saved plot to: {fname}")

    if show:
        fig.show()