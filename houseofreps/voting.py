from .state import St, Year
from .house import HouseOfReps, PopType
from .residents_per_rep import ResidentsPerRep, calculate_residents_per_rep_for_year

from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin
from typing import Dict
from enum import Enum
import pandas as pd
from typing import Optional


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


@dataclass
class VoteResults(DataClassDictMixin):
    congress: int
    rollnumber: int
    castcode_to_count: Dict[CastCode, float]


@dataclass
class VoteResultsFractional(DataClassDictMixin):
    vote_results: VoteResults
    st_to_reps_fair: Dict[St, float]
    st_to_reps_actual: Dict[St, float]


class MissingMemberError(Exception):
    pass


class CalculateVotes:


    def __init__(self,
        rollvotes: RollVotes, 
        members: Members, 
        census_year: Optional[Year] = None, 
        use_num_votes_as_num_seats: bool = False,
        skip_missing_icpsr_in_members: bool = False,
        skip_dc: bool = True
        ):
        self.rollvotes = rollvotes
        self.members = members
        self.census_year = census_year
        self.use_num_votes_as_num_seats = use_num_votes_as_num_seats
        self.skip_missing_icpsr_in_members = skip_missing_icpsr_in_members
        self.skip_dc = skip_dc
    

    def calculate_votes(self) -> VoteResults:
        castcode_to_count = {}
        for icpsr, castcode in self.rollvotes.icpsr_to_castcode.items():

            # Get state of this member's vote
            if not icpsr in self.members.icpsr_to_state:
                if self.skip_missing_icpsr_in_members:
                    continue
                else:
                    raise MissingMemberError(f"Member with icpsr {icpsr} not found in members.")
            st = self.members.icpsr_to_state[icpsr]

            # Check DC
            if self.skip_dc and st == St.DISTRICT_OF_COLUMBIA:
                continue    

            castcode_to_count[castcode] = castcode_to_count.get(castcode, 0) + 1

        return VoteResults(
            congress=self.rollvotes.congress,
            rollnumber=self.rollvotes.rollnumber,
            castcode_to_count=castcode_to_count
            )
        

    def calculate_votes_fractional(self) -> VoteResultsFractional:
        
        # Calculate the number of seats in the House of Representatives - either 435 or the number of votes
        if self.use_num_votes_as_num_seats:
            num_seats = len(self.rollvotes.icpsr_to_castcode)
        else:
            num_seats = 435
        
        # Calculate population percentage of each state
        assert self.census_year is not None, "census_year must be specified."
        house = HouseOfReps(
            year=self.census_year, 
            pop_type=PopType.APPORTIONMENT,
            no_voting_house_seats=num_seats
            )
        st_to_pop_perc: Dict[St, float] = {}
        for st, state in house.states.items():
            if st != St.DISTRICT_OF_COLUMBIA:
                st_to_pop_perc[st] = state.pop / house.get_total_us_pop(sts_exclude=[St.DISTRICT_OF_COLUMBIA])

        # Check sum to 1
        assert abs(sum(st_to_pop_perc.values()) - 1) < 1e-6, "Sum of state population percentages is not 1."

        # Calculate the fair number of representatives for each state
        st_to_reps_fair: Dict[St, float] = { st: pop_perc * num_seats for st, pop_perc in st_to_pop_perc.items() }

        # Calculate the actual number of representatives for each state
        house.assign_house_seats_priority()
        st_to_reps_actual: Dict[St, float] = { st: state.no_reps.voting for st, state in house.states.items() }

        # Calculate the rescaling factor for each state
        # Each vote should be rescaled by this factor
        st_to_rescale_factor: Dict[St, float] = { st: st_to_reps_fair[st] / st_to_reps_actual[st] for st in st_to_reps_fair.keys() }

        # Calculate the rescaled vote results
        castcode_to_count: Dict[CastCode, float] = {}
        for icpsr, castcode in self.rollvotes.icpsr_to_castcode.items():

            # Get state of this member's vote
            if not icpsr in self.members.icpsr_to_state:
                if self.skip_missing_icpsr_in_members:
                    continue
                else:
                    raise MissingMemberError(f"Member with icpsr {icpsr} not found in members.")
            st = self.members.icpsr_to_state[icpsr]
            
            # Check DC
            if self.skip_dc and st == St.DISTRICT_OF_COLUMBIA:
                continue    

            # Get rescale factor for this state
            rescale_factor = st_to_rescale_factor[st]

            # Add to count = rescale_factor (not 1)
            castcode_to_count[castcode] = castcode_to_count.get(castcode, 0.0) + rescale_factor

        vr = VoteResults(
            congress=self.rollvotes.congress,
            rollnumber=self.rollvotes.rollnumber,
            castcode_to_count=castcode_to_count
            )
        return VoteResultsFractional(
            vote_results=vr,
            st_to_reps_fair=st_to_reps_fair,
            st_to_reps_actual=st_to_reps_actual
            )