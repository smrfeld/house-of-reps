from .state import St, Year, ST_TRUE
from .house import HouseOfReps, PopType

from dataclasses import dataclass
from mashumaro import DataClassDictMixin
from typing import Dict


@dataclass
class ResidentsPerRep(DataClassDictMixin):
    year: Year
    "Year"

    fair: float
    "Fair residents per representative"

    residents_per_rep: Dict[St, float]
    "Residents per representative for each state"


def calculate_residents_per_rep_for_year(year: Year) -> ResidentsPerRep:
    """Calculate the number of residents per representative for each state.

    Args:
        year (Year): Year to calculate for

    Returns:
        ResidentsPerRep: Residents per representative for each state
    """    
    residents_per_rep = {}

    house = HouseOfReps(
        year=year, 
        pop_type=PopType.APPORTIONMENT
        )

    for st, state in house.states.items():
        if st != St.DISTRICT_OF_COLUMBIA:
            residents_per_rep[st] = 1e6 * ST_TRUE[st].year_to_pop[year].apportionment / state.no_reps.voting

    fair = 1e6 * house.get_total_us_pop(sts_exclude=[St.DISTRICT_OF_COLUMBIA]) / 435.0
    return ResidentsPerRep(year=year, fair=fair, residents_per_rep=residents_per_rep)

