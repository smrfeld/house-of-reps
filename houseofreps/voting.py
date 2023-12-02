from .state import St, Year
from .house import HouseOfReps, PopType
from .residents_per_rep import ResidentsPerRep, calculate_residents_per_rep_for_year

from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin
from typing import Dict
from enum import Enum
import pandas as pd
from typing import Optional, List
from loguru import logger


# Map from census year to congress
CENSUS_YEAR_TO_CONGRESS = {
    Year.YR2020: list(range(117,118+1)),
    Year.YR2010: list(range(112,116+1)),
    Year.YR2000: list(range(107,111+1)),
    Year.YR1990: list(range(102,106+1)),
    Year.YR1980: list(range(97,101+1)),
    Year.YR1970: list(range(92,96+1)),
    Year.YR1960: list(range(87,91+1))
    }

# Map from congress to census year
CONGRESS_TO_CENSUS_YEAR = { 
    congress: census_year 
    for census_year, congresses in CENSUS_YEAR_TO_CONGRESS.items() 
    for congress in congresses 
    }


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

    @classmethod
    def yeas(cls):
        return [ cls.YEA, cls.PAIRED_YEA, cls.ANNOUNCED_YEA ]

    @classmethod
    def nays(cls):
        return [ cls.NAY, cls.PAIRED_NAY, cls.ANNOUNCED_NAY ]


@dataclass
class Votes(DataClassDictMixin):
    congress: int
    rollnumber: int
    icpsr_to_castcode: Dict[int, CastCode]
    

@dataclass
class VotesAll(DataClassDictMixin):
    congress_to_rollnumber_to_rollvotes: Dict[int, Dict[int, Votes]] = field(default_factory=dict)

    @property
    def no_congresses(self):
        return len(self.congress_to_rollnumber_to_rollvotes)

    @property
    def no_rollvotes(self):
        return sum([ len(rollnumber_to_rollvotes) for rollnumber_to_rollvotes in self.congress_to_rollnumber_to_rollvotes.values() ])


@dataclass
class Members(DataClassDictMixin):
    icpsr_to_state: Dict[int, St]


@dataclass
class RollCall(DataClassDictMixin):

    congress: int
    rollnumber: int
    date: str
    yea_count: int
    nay_count: int
    bill_number: str
    vote_result: str
    vote_desc: str
    vote_question: str


@dataclass
class RollCallsAll(DataClassDictMixin):
    congress_to_rollnumber_to_rollcall: Dict[int, Dict[int, RollCall]] = field(default_factory=dict)

    @property
    def no_congresses(self):
        return len(self.congress_to_rollnumber_to_rollcall)

    @property
    def no_rollcalls(self):
        return sum([ len(rollnumber_to_rollcall) for rollnumber_to_rollcall in self.congress_to_rollnumber_to_rollcall.values() ])


class LoadVoteViewCsv:

    def load_rollcalls_all(self, fname: str) -> RollCallsAll:

        # Load csv
        df = pd.read_csv(fname)

        # Get all congresses
        congresses = df.congress.unique()

        # Construct
        rca = RollCallsAll()
        for congress in congresses:
            rca.congress_to_rollnumber_to_rollcall[congress] = {}

            # Get all rollnumbers
            df_congress = df[df.congress == congress]
            rollnumbers = df_congress.rollnumber.unique()

            for rollnumber in rollnumbers:
                rca.congress_to_rollnumber_to_rollcall[congress][rollnumber] = self._rollcall_from_dataframe(df_congress, congress, rollnumber)

        return rca

    def _rollcall_from_dataframe(self, df: pd.DataFrame, congress: int, rollnumber: int) -> RollCall:
        # Filter by congress and rollnumber
        df = df[(df.congress == congress) & (df.rollnumber == rollnumber)]

        # Check that there is only one row
        assert len(df) == 1, f"Found {len(df)} rows for congress {congress} rollnumber {rollnumber}"

        # Get date
        date = df.date.iloc[0]

        # Get yea count
        yea_count = df.yea_count.iloc[0]

        # Get nay count
        nay_count = df.nay_count.iloc[0]

        # Get bill number
        bill_number = df.bill_number.iloc[0]

        # Get vote result
        vote_result = df.vote_result.iloc[0]

        # Get vote desc
        vote_desc = df.vote_desc.iloc[0]

        # Get vote question
        vote_question = df.vote_question.iloc[0]

        return RollCall(
            congress=congress,
            rollnumber=rollnumber,
            date=date,
            yea_count=yea_count,
            nay_count=nay_count,
            bill_number=bill_number,
            vote_result=vote_result,
            vote_desc=vote_desc,
            vote_question=vote_question
            )

    def load_votes_all(self, fname: str) -> VotesAll:

        # Load csv
        df = pd.read_csv(fname)

        # Get all congresses
        congresses = df.congress.unique()

        # Construct
        rva = VotesAll()
        for congress in congresses:
            rva.congress_to_rollnumber_to_rollvotes[congress] = {}

            # Get all rollnumbers
            df_congress = df[df.congress == congress]
            rollnumbers = df_congress.rollnumber.unique()

            for rollnumber in rollnumbers:
                rva.congress_to_rollnumber_to_rollvotes[congress][rollnumber] = self._votes_from_dataframe(df_congress, congress, rollnumber)
        return rva
    

    def load_votes(self, fname: str, congress: int, rollnumber: int) -> Votes:
        df = pd.read_csv(fname)

        # Filter by congress and rollnumber
        df = df[(df.congress == congress) & (df.rollnumber == rollnumber)]

        return self._votes_from_dataframe(df, congress, rollnumber)


    def _votes_from_dataframe(self, df: pd.DataFrame, congress: int, rollnumber: int) -> Votes:
        # Filter by congress and rollnumber
        df = df[(df.congress == congress) & (df.rollnumber == rollnumber)]

        # Convert to icpsr to castcode
        # Note: castcode is an int
        icpsr_to_castcode_int = dict(zip(df.icpsr, df.cast_code))    

        # Convert to icpsr to castcode
        icpsr_to_castcode = {
            int(icpsr): CastCode(castcode_int) 
            for icpsr, castcode_int in icpsr_to_castcode_int.items()
            }
        
        return Votes(
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
            int(icpsr): St(state_abbrev) 
            for icpsr, state_abbrev in icpsr_to_state_str.items()
            if state_abbrev in st_values
            }

        return Members(icpsr_to_state=icpsr_to_state)


class Decision(Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class VoteResults(DataClassDictMixin):
    congress: int
    rollnumber: int
    castcode_to_count: Dict[CastCode, float]


    @property
    def majority_decision(self) -> Decision:
        yea = sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.yeas() ])
        nay = sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.nays() ])
        if yea > nay:
            return Decision.PASS
        else:
            return Decision.FAIL


@dataclass
class VoteResultsFractional(DataClassDictMixin):
    vote_results: VoteResults
    st_to_reps_fair: Dict[St, float]
    st_to_reps_actual: Dict[St, float]


class MissingMemberError(Exception):
    pass


class CalculateVotes:


    @dataclass
    class Options(DataClassDictMixin):
        use_num_votes_as_num_seats: bool = False
        skip_missing_icpsr_in_members: bool = False
        warn_missing_icpsr_in_members: bool = False
        skip_dc: bool = True
        skip_castcodes: List[CastCode] = field(default_factory=lambda: [CastCode.NOT_MEMBER, CastCode.NOT_VOTING])


    def __init__(self,
        rollvotes: Votes, 
        members: Members, 
        options: Options = Options()
        ):
        self.rollvotes = rollvotes
        self.members = members
        self.options = options
    

    def calculate_votes(self) -> VoteResults:
        castcode_to_count = {}
        for icpsr, castcode in self.rollvotes.icpsr_to_castcode.items():
            assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
            assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"
            
            # Check castcode
            if castcode in self.options.skip_castcodes:
                continue

            # Get state of this member's vote
            if not icpsr in self.members.icpsr_to_state:
                if self.options.skip_missing_icpsr_in_members:
                    if self.options.warn_missing_icpsr_in_members:
                        logger.warning(f"Member with icpsr {icpsr} not found in members. Skipping counting vote.")
                    continue
                else:
                    raise MissingMemberError(f"Member with icpsr {icpsr} not found in members.")
            st = self.members.icpsr_to_state[icpsr]

            # Check DC
            if self.options.skip_dc and st == St.DISTRICT_OF_COLUMBIA:
                continue    

            castcode_to_count[castcode] = castcode_to_count.get(castcode, 0) + 1

        return VoteResults(
            congress=self.rollvotes.congress,
            rollnumber=self.rollvotes.rollnumber,
            castcode_to_count=castcode_to_count
            )
        

    def calculate_votes_fractional(self) -> VoteResultsFractional:
        
        # Calculate the number of seats in the House of Representatives - either 435 or the number of votes
        if self.options.use_num_votes_as_num_seats:
            num_seats = len(self.rollvotes.icpsr_to_castcode)
        else:
            num_seats = 435
        
        # Calculate population percentage of each state
        assert self.rollvotes.congress in CONGRESS_TO_CENSUS_YEAR, f"congress {self.rollvotes.congress} not found in CONGRESS_TO_CENSUS_YEAR"
        census_year = CONGRESS_TO_CENSUS_YEAR[self.rollvotes.congress]
        house = HouseOfReps(
            year=census_year, 
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
            assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
            assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"

            # Check castcode
            if castcode in self.options.skip_castcodes:
                continue

            # Get state of this member's vote
            if not icpsr in self.members.icpsr_to_state:
                if self.options.skip_missing_icpsr_in_members:
                    if self.options.warn_missing_icpsr_in_members:
                        logger.warning(f"Member with icpsr {icpsr} not found in members. Skipping counting vote.")
                    continue
                else:
                    raise MissingMemberError(f"Member with icpsr {icpsr} not found in members.")
            st = self.members.icpsr_to_state[icpsr]
            
            # Check DC
            if self.options.skip_dc and st == St.DISTRICT_OF_COLUMBIA:
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