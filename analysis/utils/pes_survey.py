# PES = 2020 Post-Enumeration Survey (PES), showing population undercounts and overcounts by state and the District of Columbia.
# https://www.census.gov/library/stories/2022/05/2020-census-undercount-overcount-rates-by-state.html
# https://www2.census.gov/programs-surveys/decennial/coverage-measurement/pes/2020-source-and-accuracy-pes-estimates.pdf

import houseofreps as hr
import copy
from loguru import logger
import plotly.graph_objects as go
import os


def plot_pes_counts(show: bool):
    
    # Create house
    year = hr.Year.YR2020
    house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)

    # Assign house seats
    house.assign_house_seats_priority()
    states_actual = copy.deepcopy(house.states)

    # Undercounted populations
    state_to_undercount_perc = {
        hr.St.ARKANSAS: -5.04,
        hr.St.FLORIDA: -3.48,
        hr.St.ILLINOIS: -1.97,
        hr.St.MISSISSIPPI: -4.11,
        hr.St.TENNESSEE: -4.78,
        hr.St.TEXAS: -1.92
    }
    
    # Overcounted populations
    state_to_overcount_perc = {
        hr.St.DELAWARE: 5.45,
        hr.St.HAWAII: 6.79,
        hr.St.MASSACHUSETTS: 2.24,
        hr.St.MINNESOTA: 3.84,
        hr.St.NEW_YORK: 3.44,
        hr.St.OHIO: 1.49,
        hr.St.RHODE_ISLAND: 5.05,
        hr.St.UTAH: 2.59
        }

    # Shifts
    for state_to_perc in [state_to_undercount_perc, state_to_overcount_perc]:
        for st,perc in state_to_perc.items():
            change = perc / 100 * house.states[st].pop

            # Overrepresent => perc > 0 => subtract because actual pop is smaller
            # Underrepresent => perc < 0 => add because actual pop is larger
            house.states[st].pop -= change

    # Assign house seats
    house.assign_house_seats_priority()

    # Report changes
    st_to_old_new = {}
    for st in hr.St:
        if st == hr.St.DISTRICT_OF_COLUMBIA:
            continue
        state = house.states[st]
        state_actual = states_actual[st]
        if state.no_reps != state_actual.no_reps:
            logger.info(f"{st.name}: {state_actual.no_reps.voting} -> {state.no_reps.voting}")

            st_to_old_new[st.name] = (state_actual.no_reps.voting, state.no_reps.voting)

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

    fig.add_trace(go.Table(
        header=dict(values=["State", "Old", "New"], align='left'),
        cells=dict(
            values=[list(st_to_old_new.keys()), [x[0] for x in st_to_old_new.values()], [x[1] for x in st_to_old_new.values()]], 
            font=dict(color=[[],[],[get_text_color(x[0], x[1]) for x in st_to_old_new.values()]]),
            align='left',
            height=50
        )
        ))

    fig.update_layout(
        title='House seat changes due to Post-Enumeration Survey (PES) (%s)' % (year.value),
        height=400,
        width=1200,
        font=dict(size=18),
        )
    
    os.makedirs("plots", exist_ok=True)
    fname = 'plots/pes_survey_table_%s.jpg' % (year.value)
    fig.write_image(fname)
    logger.info(f"Saved plot to: {fname}")

    if show:
        fig.show()