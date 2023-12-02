from .state import St

from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin
from typing import Dict
from enum import Enum
import pandas as pd


class CastCode(Enum):
    """Enum for cast code"""
    NOT_MEMBER = 0
    YEA = 1
    PAIRED_YEA = 2
    ANNOUNCED_YEA = 3
    ANNOUNCED_NAY = 4
    PAIRED_NAY = 5
    NAY = 6
    PRESENT1 = 7
    PRESENT2 = 8
    NOT_VOTING = 9


@dataclass
class RollVotes(DataClassDictMixin):
    congress: int
    rollnumber: int
    icpsr_to_castcode: Dict[int, CastCode]


@dataclass
class RollVotesAll(DataClassDictMixin):
    congress_to_rollnumber_to_rollvotes: Dict[int, Dict[int, RollVotes]] = field(default_factory=dict)


@dataclass
class Members(DataClassDictMixin):
    icpsr_to_state: Dict[int, St]


class LoadVoteViewCsv:

    def load_rollvotes_all(self, fname: str) -> RollVotesAll:

        # Load csv
        df = pd.read_csv(fname)

        # Get all congresses
        congresses = df.congress.unique()

        # Construct
        rva = RollVotesAll()
        for congress in congresses:
            rva.congress_to_rollnumber_to_rollvotes[congress] = {}

            # Get all rollnumbers
            df_congress = df[df.congress == congress]
            rollnumbers = df_congress.rollnumber.unique()

            for rollnumber in rollnumbers:
                rva.congress_to_rollnumber_to_rollvotes[congress][rollnumber] = self.rollvotes_from_dataframe(df_congress, congress, rollnumber)
        return rva
    

    def load_rollvotes(self, fname: str, congress: int, rollnumber: int) -> RollVotes:
        df = pd.read_csv(fname)

        # Filter by congress and rollnumber
        df = df[(df.congress == congress) & (df.rollnumber == rollnumber)]

        return self.rollvotes_from_dataframe(df, congress, rollnumber)


    def rollvotes_from_dataframe(self, df: pd.DataFrame, congress: int, rollnumber: int) -> RollVotes:
        # Filter by congress and rollnumber
        df = df[(df.congress == congress) & (df.rollnumber == rollnumber)]

        # Convert to icpsr to castcode
        # Note: castcode is an int
        icpsr_to_castcode_int = dict(zip(df.icpsr, df.cast_code))    

        # Convert to icpsr to castcode
        icpsr_to_castcode = {
            icpsr: CastCode(castcode_int) 
            for icpsr, castcode_int in icpsr_to_castcode_int.items()
            }
        
        return RollVotes(
            congress=congress, 
            rollnumber=rollnumber, 
            icpsr_to_castcode=icpsr_to_castcode
            )


    def load_members(self, fname: str) -> Members:

        # Load csv
        df = pd.read_csv(fname)

        # Column icpsr to state_abbrev
        icpsr_to_state_str = dict(zip(df.icpsr, df.state_abbrev))

        # Convert to icpsr to St
        st_values = set([ s.value for s in St ])
        icpsr_to_state = {
            icpsr: St(state_abbrev) 
            for icpsr, state_abbrev in icpsr_to_state_str.items()
            if state_abbrev in st_values
            }

        return Members(icpsr_to_state=icpsr_to_state)