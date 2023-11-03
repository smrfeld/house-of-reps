import utils

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






if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=["rpr", "rpr-frac", "pop-rankings", "rankings-fracs", "shift-pop"])
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    if args.command == "rpr":

        for year in hr.Year:
            utils.plot_residents_per_rep(year, args.show)

    elif args.command == "rpr-frac":
        utils.plot_residents_per_rep_frac(args.show)
    
    elif args.command == "pop-rankings":
        for year in hr.Year:
            utils.plot_state_pop_rankings(year, args.show)

    elif args.command == "rankings-fracs":
        for year in hr.Year:
            utils.plot_rankings_fracs_for_year(year, args.show)
        utils.plot_rankings_fracs_ave(args.show)

    elif args.command == "shift-pop":
        for year in hr.Year:
            utils.plot_shift_pop(year, args.show)

    else:
        raise ValueError(f"Unknown command: {args.command}")
    