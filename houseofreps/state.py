import numpy as np

from enum import Enum
from typing import Dict, List

import pandas as pd
import os
from dataclasses import dataclass

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
    def allExceptDC(cls):
        """All states except DC
        """
        return [ x for x in St if x != St.DISTRICT_OF_COLUMBIA ]

    @classmethod
    def fromName(cls, name: str):
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

def arithmetic_mean(n : float, m : float) -> float:
    return (n + m) / 2.0

def harmonic_mean(n : float, m : float) -> float:
    return 1.0 / arithmetic_mean(1.0/n, 1.0/m)

def geometric_mean(n : float, m : float) -> float:
    return np.sqrt(n * m)

class PopType(Enum):
    """Population type
    """
    RESIDENT = 0
    OVERSEAS = 1
    APPORTIONMENT = 2

class NoRepsType(Enum):
    """Type of no reps
    """
    VOTING = 0
    NONVOTING = 1

@dataclass
class Pop:
    """Population
    """

    resident: float
    overseas: float
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
        else:
            return self.apportionment

@dataclass
class NoReps:
    """No reps
    """
    voting: float
    nonvoting: float

class State:
    
    def __init__(self, 
        st: St, 
        pop_true: Dict[Year,Pop], 
        no_reps_true: Dict[Year,NoReps]
        ):
        """State class

        Args:
            st (St): State
            pop_true (Dict[Year,Pop]): True population at each year
            no_reps_true (Dict[Year,NoReps]): True number of reps at each year
        """
        self.st : St = st

        self.pop_true : Dict[Year,Pop] = pop_true
        self.no_reps_true : Dict[Year,NoReps] = no_reps_true
        
        self.pop_assigned : float = self.pop_true[Year.YR2010].apportionment
        self.no_reps_assigned : NoReps = NoReps(voting=0,nonvoting=0)

        self.electoral_frac_vote : float = 0.0
        self.electoral_frac : float = 0.0

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
    
    def get_electoral_frac_vote_str(self) -> str:
        """Electoral college - vote fraction as a consistently formatted string

        Returns:
            str: Vote fraction
        """
        return "%.2f" % self.electoral_frac_vote

    def get_pop_assigned_str(self) -> str:
        """Nicely formatted string of assigned population

        Returns:
            str: Assigned population
        """
        if self.pop_assigned < 10:
            return "%.2f" % self.pop_assigned
        elif self.pop_assigned < 100:
            return "%.1f" % self.pop_assigned
        else:
            return "%d" % int(self.pop_assigned)

    def get_electoral_no_votes_assigned(self) -> int:
        """Electoral college - get no votes assigned

        Returns:
            int: No votes assigned
        """
        return self.no_reps_assigned.voting + self.no_reps_assigned.nonvoting + 2

    def get_priority(self) -> float:
        """Get priority of the state

        Returns:
            float: Priority
        """
        harmonic_ave = geometric_mean(self.no_reps_assigned.voting,self.no_reps_assigned.voting+1)
        multiplier = 1.0 / harmonic_ave
        return self.pop_assigned * multiplier

    def validate_no_reps_matches_true(self, year: Year):
        """Validate that the number of reps assigned matches the true value

        Args:
            year (Year): Year to check against

        Raises:
            ValueError: In case the reps does not match
        """

        # Validate that they match the expected
        if self.no_reps_assigned.voting != self.no_reps_true[year].voting:
            raise ValueError("State: %s no. voting reps assigned: %d does not match the true no. reps: %d in year: %s" % 
                (self.st, self.no_reps_assigned.voting, self.no_reps_true[year].voting, year))
        if self.no_reps_assigned.nonvoting != self.no_reps_true[year].nonvoting:
            raise ValueError("State: %s no. nonvoting reps assigned: %d does not match the true no. reps: %d in year: %s" % 
                (self.st, self.no_reps_assigned.nonvoting, self.no_reps_true[year].nonvoting, year))

def load_states(states: List[St]) -> Dict[St,State]:
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
            year = row[3]
            try:
                yr = Year(str(year))

                # Fill in
                resident = float(row[4]) / 1e6
                overseas = float(row[5]) / 1e6
                apportionment = float(row[6]) / 1e6
                pop_true[yr] = Pop(resident=resident, overseas=overseas, apportionment=apportionment)
                if st == St.DISTRICT_OF_COLUMBIA:
                    no_reps_true[yr] = NoReps(voting=0,nonvoting=1)
                else:
                    no_reps_true[yr] = NoReps(voting=int(row[10]),nonvoting=0)
            except:
                pass

        # Add state
        ret[st] = State(st, pop_true, no_reps_true)

    return ret