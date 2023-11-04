import houseofreps as hr
import plotly.graph_objects as go
from typing import Dict, Optional
from loguru import logger
import os
from tqdm import tqdm


def plot_shift_pop(year: hr.Year, show: bool, report_all: bool = False):
    st_list = list(hr.St)
    st_list = [st for st in st_list if st != hr.St.DISTRICT_OF_COLUMBIA]

    if report_all:
        logger.info(f"--- {year.value} Adding a representative ---")
    st_to_pop_shift_for_add: Dict[hr.St,float] = {}
    for st in tqdm(st_list, disable=report_all, desc="Calculating pop shift to add rep (%s)" % year.value):

        # Three stage search: coarse to fine
        pop_shift_required = hr.find_min_pop_shift_required_for_change_repr(year, st, hr.Target.ADD, hr.PopChangeMode.SHIFT_POP)
        assert pop_shift_required is not None, "Could not find a population shift that would add a representative to %s" % st.name
        st_to_pop_shift_for_add[st] = pop_shift_required
        if report_all:
            logger.info(f"{year.value} {st.name}: {pop_shift_required:.6f} million people need to be shifted into the state to add a representative")

    if report_all:
        logger.info(f"--- {year.value} Losing a representative ---")
    st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]] = {}
    for st in tqdm(st_list, disable=report_all, desc="Calculating pop shift to lose rep (%s)" % year.value):
        pop_shift_required = hr.find_min_pop_shift_required_for_change_repr(year, st, hr.Target.LOSE, hr.PopChangeMode.SHIFT_POP)
        st_to_pop_shift_for_lose[st] = pop_shift_required
        if report_all:
            if pop_shift_required is not None:
                logger.info(f"{year.value} {st.name}: {pop_shift_required:.6f} million people need to be shifted out of the state to lose a representative")
            else:
                logger.info(f"{st.name}: Cannot lose a representative because it only has one.")

    # Smallest shifts to add
    logger.info(f"--- {year.value} Smallest shifts to add a rep ---")
    smallest = sorted(st_to_pop_shift_for_add.items(), key=lambda x: x[1])
    for st,pop_shift in smallest[:3]:
        logger.info(f"{year.value} {st.name}: {int(pop_shift*1e6)} people need to be shifted into the state to add a representative")

    logger.info(f"--- {year.value} Smallest shifts to lose a rep ---")
    smallest = sorted(st_to_pop_shift_for_lose.items(), key=lambda x: x[1] or -1e10, reverse=True)
    for st,pop_shift in smallest[:3]:
        assert pop_shift is not None
        logger.info(f"{year.value} {st.name}: {int(pop_shift*1e6)} people need to be shifted out of the state to lose a representative")

    plot_add_remove_bars(year, st_to_pop_shift_for_add, st_to_pop_shift_for_lose, show)


def plot_add_remove_bars(year: hr.Year, st_to_pop_shift_for_add: Dict[hr.St,float], st_to_pop_shift_for_lose: Dict[hr.St,Optional[float]], show: bool):
    st_list = list(st_to_pop_shift_for_add.keys())

    # Sort states for pretty plot ordering
    st_list.sort(key=lambda st: st_to_pop_shift_for_add[st])

    # Plot
    st_names = [st.name if st_to_pop_shift_for_lose[st] is not None else st.name + "*" for st in st_list]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=st_names,
            y=[st_to_pop_shift_for_add[st] for st in st_list],
            name="Add a representative",
        )
    )
    fig.add_trace(
        go.Bar(
            x=st_names,
            y=[st_to_pop_shift_for_lose[st] for st in st_list],
            name="Lose a representative<br>*Only has one representative",
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
