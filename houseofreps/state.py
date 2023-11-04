import numpy as np
from enum import Enum
from typing import Dict, List
import pandas as pd
import os
from dataclasses import dataclass, field
from loguru import logger
import copy


class St(Enum):
    """States including DC
    """

    CALIFORNIA = "CA"
    TEXAS = "TX"
    FLORIDA = "FL"
    NEW_YORK = "NY"
    PENNSYLVANIA = "PA"
    ILLINOIS = "IL"
    OHIO = "OH"
    GEORGIA = "GA"
    NORTH_CAROLINA = "NC"
    MICHIGAN = "MI"
    NEW_JERSEY = "NJ"
    VIRGINIA = "VA"
    WASHINGTON = "WA"
    ARIZONA = "AZ"
    MASSACHUSETTS = "MA"
    TENNESSEE = "TN"
    INDIANA = "IN"
    MISSOURI = "MO"
    MARYLAND = "MD"
    WISCONSIN = "WI"
    COLORADO = "CO"
    MINNESOTA = "MN"
    SOUTH_CAROLINA = "SC"
    ALABAMA = "AL"
    LOUISIANA = "LA"
    KENTUCKY = "KY"
    OREGON = "OR"
    OKLAHOMA = "OK"
    CONNECTICUT = "CT"
    UTAH = "UT"
    IOWA = "IA"
    NEVADA = "NV"
    ARKANSAS = "AR"
    MISSISSIPPI = "MS"
    KANSAS = "KS"
    NEW_MEXICO = "NM"
    NEBRASKA = "NE"
    WEST_VIRGINIA = "WV"
    IDAHO = "ID"
    HAWAII = "HI"
    NEW_HAMPSHIRE = "NH"
    MAINE = "ME"
    MONTANA = "MT"
    RHODE_ISLAND = "RI"
    DELAWARE = "DE"
    SOUTH_DAKOTA = "SD"
    NORTH_DAKOTA = "ND"
    ALASKA = "AK"
    DISTRICT_OF_COLUMBIA = "DC"
    VERMONT = "VT"
    WYOMING = "WY"


    @classmethod
    def all_except_dc(cls):
        """All states except DC
        """
        return [ x for x in St if x != St.DISTRICT_OF_COLUMBIA ]


    @classmethod
    def from_name(cls, name: str):
        """Construct from a name

        Args:
            name (str): Name of the state

        Returns:
            St: State
        """
        st = [x for x in St if x.name == name][0]
        return cls(st)


    @property
    def name(self) -> str:
        """Proper name of the state

        Returns:
            str: Proper name
        """
        s = str(self)[3:]
        s = s.replace("_"," ")
        s = s.lower().title()
        # Fix "of"
        if s == "District Of Columbia":
            s = "District of Columbia"
        return s
        

class Year(Enum):
    """Year
    """

    YR2020 = "2020"
    YR2010 = "2010"
    YR2000 = "2000"
    YR1990 = "1990"
    YR1980 = "1980"
    YR1970 = "1970"
    YR1960 = "1960"

    
    @classmethod
    @property
    def range_str(cls) -> str:
        year_min = min([x for x in Year], key=lambda x: int(x.value))
        year_max = max([x for x in Year], key=lambda x: int(x.value))
        return f"{year_min.value}-{year_max.value}"


def arithmetic_mean(n : float, m : float) -> float:
    """Compute arithmetic mean = (n + m) / 2

    Args:
        n (float): n
        m (float): m

    Returns:
        float: arithmetic mean
    """    
    return (n + m) / 2.0


def harmonic_mean(n : float, m : float) -> float:
    """Compute harmonic mean = 1 / (1/n + 1/m)

    Args:
        n (float): n
        m (float): m

    Returns:
        float: harmonic mean
    """    
    return 1.0 / arithmetic_mean(1.0/n, 1.0/m)


def geometric_mean(n : float, m : float) -> float:
    """Compute geometric mean = sqrt(n * m)

    Args:
        n (float): n
        m (float): m

    Returns:
        float: geometric mean
    """    
    return np.sqrt(n * m)


class PopType(Enum):
    """Population type
    """
    RESIDENT = "resident"
    OVERSEAS = "overseas"
    APPORTIONMENT = "apportionment"


class NoRepsType(Enum):
    """Type of no reps
    """
    VOTING = "voting"
    NONVOTING = "nonvoting"


@dataclass
class Pop:
    """Population

    Args:
        resident (float): Resident population, in millions
        overseas (float): Overseas population, in millions
        apportionment (float): Population used for apportionment, in millions
    """

    # Resident population, in milions
    resident: float

    # Overseas population, in millions
    overseas: float

    # Population used for apportionment, in millions
    apportionment: float


    def get_pop(self, pop_type: PopType) -> float:
        """Get population of some type

        Args:
            pop_type (PopType): Population type

        Returns:
            float: Population
        """
        if pop_type == PopType.RESIDENT:
            return self.resident
        elif pop_type == PopType.OVERSEAS:
            return self.overseas
        elif pop_type == PopType.APPORTIONMENT:
            return self.apportionment
        else:
            raise ValueError("Unknown population type: %s" % pop_type)


@dataclass
class NoReps:
    """No reps
    """
    voting: float
    nonvoting: float

    @classmethod
    def zero(cls):
        return cls(0,0)


class StateTrue:
    """True state population and number of reps
    """    

    def __init__(self, 
        st: St, 
        year_to_pop: Dict[Year,Pop], 
        year_to_no_reps: Dict[Year,NoReps]
        ):
        """A true state, from the US census data

        Args:
            st (St): State
            year_to_pop (Dict[Year,Pop]): Year to population
            year_to_no_reps (Dict[Year,NoReps]): Year to number of reps
        """        
        self.st : St = st
        self.year_to_pop: Dict[Year,Pop] = year_to_pop
        self.year_to_no_reps: Dict[Year,NoReps] = year_to_no_reps
        

    def __str__(self):
        return f'{self.st.name}'


    def __repr__(self):
        return f'State(st={self.st.name})'


def load_states_true(states: List[St] = list(St)) -> Dict[St,StateTrue]:
    """Load list of states

    Args:
        states (List[St]): List of states to load

    Returns:
        Dict[St,State]: Dictionary of states
    """

    # Load data
    dir_csv = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(dir_csv, "apportionment.csv"))

    # Load states
    ret = {}
    for st in states:
        df_state = df.loc[df['Name'] == st.name]

        pop_true = {}
        no_reps_true = {}

        for idx,row in df_state.iterrows():
            year = row["Year"]
            try:
                yr = Year(str(year))

                # Fill in
                resident = float(row["Resident Population"]) / 1e6
                overseas = float(row["Overseas population included"]) / 1e6
                apportionment = float(row["Population used for apportionment"]) / 1e6
                pop_true[yr] = Pop(resident=resident, overseas=overseas, apportionment=apportionment)
                if st == St.DISTRICT_OF_COLUMBIA:
                    no_reps_true[yr] = NoReps(voting=0,nonvoting=1)
                else:
                    no_reps_true[yr] = NoReps(voting=int(row["Number of Representatives"]),nonvoting=0)
            except:
                pass

        # Add state
        ret[st] = StateTrue(st, pop_true, no_reps_true)

    return ret


ST_TRUE = load_states_true()


@dataclass
class State:
    """State

    Args:
        st (St): State
        pop (float, optional): Population, in millions. Defaults to 0.0.
        no_reps (NoReps, optional): Number of reps. Defaults to NoReps.zero().
    """   

    # State 
    st: St
    
    # Population, in millions
    pop: float = 0.0

    # Number of reps
    no_reps: NoReps = field(default_factory=NoReps.zero)

    @classmethod
    def from_true(cls, st: St, year: Year, pop_type: PopType = PopType.APPORTIONMENT):
        """Construct from true state

        Args:
            st (St): State
            year (Year): Year
            pop_type (PopType, optional): Population to use. Defaults to PopType.APPORTIONMENT.
        """        
        return State(
            st=st,
            pop=ST_TRUE[st].year_to_pop[year].get_pop(pop_type),
            no_reps=copy.deepcopy(ST_TRUE[st].year_to_no_reps[year])
            )


    def __str__(self):
        return f'{self.st.name}'


    def __repr__(self):
        return f'State(st={self.st.name})'


    def get_electoral_no_votes_assigned_str(self) -> str:
        """Electoral college - no votes assigned as a consistently formatted string

        Returns:
            str: No votes assigned in electoral college
        """
        return "%d" % self.get_electoral_no_votes_assigned()
    

    def get_pop_assigned_str(self) -> str:
        """Nicely formatted string of assigned population

        Returns:
            str: Assigned population
        """
        if self.pop < 10:
            return "%.2f" % self.pop
        elif self.pop < 100:
            return "%.1f" % self.pop
        else:
            return "%d" % int(self.pop)


    def get_electoral_no_votes_assigned(self) -> float:
        """Electoral college - get no votes assigned

        Returns:
            int: No votes assigned
        """
        return self.no_reps.voting + self.no_reps.nonvoting + 2


    def get_priority(self) -> float:
        """Get priority of the state

        Returns:
            float: Priority
        """
        harmonic_ave = geometric_mean(self.no_reps.voting,self.no_reps.voting+1)
        multiplier = 1.0 / harmonic_ave
        return self.pop * multiplier