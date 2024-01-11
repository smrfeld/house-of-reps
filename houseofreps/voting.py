from .state import St, Year
from .house import HouseOfReps, PopType
from .residents_per_rep import ResidentsPerRep, calculate_residents_per_rep_for_year

from dataclasses import dataclass, field
from mashumaro import DataClassDictMixin
from typing import Dict
from enum import Enum
import pandas as pd
from typing import Optional, List, Tuple
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
    def yea_list(cls):
        return [ cls.YEA, cls.PAIRED_YEA, cls.ANNOUNCED_YEA ]

    @classmethod
    def nay_list(cls):
        return [ cls.NAY, cls.PAIRED_NAY, cls.ANNOUNCED_NAY ]


@dataclass
class Votes(DataClassDictMixin):
    """Votes for a rollcall
    """    

    congress: int
    "Congress"

    rollnumber: int
    "Roll number"

    icpsr_to_castcode: Dict[int, CastCode]
    "ICPSR to cast code"
    

@dataclass
class VotesAll(DataClassDictMixin):
    """Votes for all rollcalls
    """    

    congress_to_rollnumber_to_votes: Dict[int, Dict[int, Votes]] = field(default_factory=dict)
    "Congress to roll number to votes"

    @property
    def no_congresses(self) -> int:
        """Number of congresses
        """        
        return len(self.congress_to_rollnumber_to_votes)

    @property
    def no_rollcalls(self) -> int:
        """Number of rollcalls
        """        
        return sum([ len(rollnumber_to_rollvotes) for rollnumber_to_rollvotes in self.congress_to_rollnumber_to_votes.values() ])


@dataclass
class Members(DataClassDictMixin):
    """Members of the House of Representatives
    """    

    icpsr_to_state: Dict[int, St]
    "ICPSR to state"


@dataclass
class RollCall(DataClassDictMixin):
    """Rollcall
    """    

    congress: int
    "Congress"

    rollnumber: int
    "Roll number"
    
    date: str
    "Date"

    yea_count: int
    "Yea count"

    nay_count: int
    "Nay count"

    bill_number: str
    "Bill number"

    vote_result: str
    "Vote result"

    vote_desc: str
    "Vote description"

    vote_question: str
    "Vote question"


@dataclass
class RollCallsAll(DataClassDictMixin):
    """All rollcalls for all congresses, indexed by congress and rollnumber
    """    

    congress_to_rollnumber_to_rollcall: Dict[int, Dict[int, RollCall]] = field(default_factory=dict)
    "Congress to roll number to rollcall"

    @property
    def no_congresses(self):
        """Number of congresses
        """        
        return len(self.congress_to_rollnumber_to_rollcall)

    @property
    def no_rollcalls(self):
        """Number of rollcalls
        """        
        return sum([ len(rollnumber_to_rollcall) for rollnumber_to_rollcall in self.congress_to_rollnumber_to_rollcall.values() ])


class LoadVoteViewCsv:
    """Helper class to load voteview csv files
    """    

    
    def __init__(self, votes_csv: Optional[str] = None, rollcalls_csv: Optional[str] = None, members_csv: Optional[str] = None):
        """Constructor

        Args:
            votes_csv (Optional[str], optional): Votes CSV. Defaults to None.
            rollcalls_csv (Optional[str], optional): Rollcalls CSV. Defaults to None.
            members_csv (Optional[str], optional): Members CSV. Defaults to None.
        """        
        self.votes_csv = votes_csv
        self.rollcalls_csv = rollcalls_csv
        self.members_csv = members_csv

    
    def load_consistency(self) -> Tuple[VotesAll, RollCallsAll, Members]:
        """Load all three and ensure they are consistent. Remove votes that are inconsistent with the rollcall votes.

        Returns:
            Tuple[VotesAll, RollCallsAll, Members]: Votes, rollcalls, members
        """        
        votes = self.load_votes()
        rollcalls = self.load_rollcalls()
        members = self.load_members()

        # Check no congresses
        congresses_votes = set(votes.congress_to_rollnumber_to_votes.keys())
        congresses_rollcalls = set(rollcalls.congress_to_rollnumber_to_rollcall.keys())
        assert congresses_votes == congresses_rollcalls, f"congresses_votes != congresses_rollcalls: {congresses_votes} != {congresses_rollcalls}"

        for congress in congresses_votes:

            # Check rollnumbers
            rollnumbers_votes = set(votes.congress_to_rollnumber_to_votes[congress].keys())
            rollnumbers_rollcalls = set(rollcalls.congress_to_rollnumber_to_rollcall[congress].keys())
            assert rollnumbers_votes == rollnumbers_rollcalls, f"rollnumbers_votes != rollnumbers_rollcalls: {rollnumbers_votes} != {rollnumbers_rollcalls}"

            for rollnumber in rollnumbers_votes:
                rv = votes.congress_to_rollnumber_to_votes[congress][rollnumber]
                rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]

                # Measure castcode to votes
                castcode_to_votes = {}
                for icpsr, castcode in rv.icpsr_to_castcode.items():
                    assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
                    assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"
                    castcode_to_votes[castcode] = castcode_to_votes.get(castcode, 0) + 1
            
                # Check yays and nays consistent
                consistent_yea = rc.yea_count == castcode_to_votes.get(CastCode.YEA,0)
                consistent_nay = rc.nay_count == castcode_to_votes.get(CastCode.NAY,0)

                # Only if inconsistent, then exclude members who are not in the members csv
                if not consistent_nay or not consistent_yea:

                    # Remove rollvotes for members not in members csv
                    rv.icpsr_to_castcode = { icpsr: castcode for icpsr, castcode in rv.icpsr_to_castcode.items() if icpsr in members.icpsr_to_state }

                    # Measure castcode to votes
                    castcode_to_votes = {}
                    for icpsr, castcode in rv.icpsr_to_castcode.items():
                        assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
                        assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"
                        castcode_to_votes[castcode] = castcode_to_votes.get(castcode, 0) + 1
                
                    # Check yays and nays consistent
                    consistent_yea = rc.yea_count == castcode_to_votes.get(CastCode.YEA,0)
                    consistent_nay = rc.nay_count == castcode_to_votes.get(CastCode.NAY,0)
                    if not consistent_nay or not consistent_yea:
                        raise RuntimeError(f"Rollcall (congress={congress}, rollnumber={rollnumber}) is not consistent with votes. yea_consistent: {consistent_yea}, nay_consistent: {consistent_nay}. Yea rollcalls: {rc.yea_count} vs votes: {castcode_to_votes.get(CastCode.YEA,0)}. Nay rollcalls: {rc.nay_count} vs votes: {castcode_to_votes.get(CastCode.NAY,0)}")
        
        return votes, rollcalls, members


    def load_members(self) -> Members:
        """Load members

        Returns:
            Members: Members
        """        

        # Load csv
        assert self.members_csv is not None, "self.members_csv is None"
        df = pd.read_csv(self.members_csv)

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
 

    def load_votes(self) -> VotesAll:
        """Load votes

        Returns:
            VotesAll: Votes
        """        

        # Load csv
        assert self.votes_csv is not None, "self.votes_csv is None"
        df = pd.read_csv(self.votes_csv)

        # Get all congresses
        congresses = df.congress.unique()

        # Construct
        rva = VotesAll()
        for congress in congresses:
            rva.congress_to_rollnumber_to_votes[congress] = {}

            # Get all rollnumbers
            df_congress = df[df.congress == congress]
            rollnumbers = df_congress.rollnumber.unique()

            for rollnumber in rollnumbers:
                rva.congress_to_rollnumber_to_votes[congress][rollnumber] = self._votes_from_dataframe(df_congress, congress, rollnumber)
        return rva


    def load_rollcalls(self) -> RollCallsAll:
        """Load rollcalls

        Returns:
            RollCallsAll: Rollcalls
        """        

        # Load csv
        assert self.rollcalls_csv is not None, "self.rollcalls_csv is None"
        df = pd.read_csv(self.rollcalls_csv)

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


class Decision(Enum):
    """Decision enum
    """    
    PASS = "pass"
    "Pass"

    FAIL = "fail"
    "Fail"


@dataclass
class VoteResults(DataClassDictMixin):
    """Vote results
    """

    congress: int
    "Congress"

    rollnumber: int
    "Roll number"

    castcode_to_count: Dict[CastCode, float]
    "Castcode to count"


    @property
    def yea_count(self):
        """Count of yea votes
        """        
        return self.castcode_to_count.get(CastCode.YEA,0)


    @property
    def nay_count(self):
        """Count of nay votes
        """        
        return self.castcode_to_count.get(CastCode.NAY,0)


    @property
    def yea_count_all(self):
        """Count of all yea votes
        """        
        return sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.yea_list() ])

    
    @property
    def nay_count_all(self):
        """Count of all nay votes
        """        
        return sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.nay_list() ])


    @property
    def majority_decision(self) -> Decision:
        """Majority decision
        """        
        if self.castcode_to_count.get(CastCode.YEA,0) > self.castcode_to_count.get(CastCode.NAY,0):
            return Decision.PASS
        else:
            return Decision.FAIL


    @property
    def majority_decision_all_yea_nay(self) -> Decision:
        """Majority decision
        """        
        yea = sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.yea_list() ])
        nay = sum([ self.castcode_to_count.get(castcode,0) for castcode in CastCode.nay_list() ])
        if yea > nay:
            return Decision.PASS
        else:
            return Decision.FAIL


@dataclass
class VoteResultsFractional(DataClassDictMixin):
    """Fractional vote results
    """    

    vote_results: VoteResults
    "Vote results"

    st_to_reps_fair: Dict[St, float]
    "Fair number of representatives for each state"

    st_to_reps_actual: Dict[St, float]
    "Actual number of representatives for each state"


class CalculateVotes:
    """Helper class to calculate votes
    """    


    @dataclass
    class Options(DataClassDictMixin):
        """Options for CalculateVotes
        """        

        use_num_votes_as_num_seats: bool = False
        "Use the number of votes as the number of seats in the House of Representatives. Otherwise uses 435."

        skip_castcodes: List[CastCode] = field(default_factory=lambda: [CastCode.NOT_MEMBER, CastCode.NOT_VOTING])
        "Skip these castcodes"


    def __init__(self,
        votes: Votes, 
        members: Members,
        rollcall: RollCall,
        options: Options = Options()
        ):
        """Constructor

        Args:
            votes (Votes): Votes
            members (Members): Members
            rollcall (RollCall): Rollcall
            options (Options, optional): Options. Defaults to Options().
        """        
        self.votes = votes
        self.members = members
        self.rollcall = rollcall
        self.options = options
    

    def calculate_votes(self) -> VoteResults:
        """Vote results

        Returns:
            VoteResults: Vote results
        """        
        castcode_to_count = {}
        for icpsr, castcode in self.votes.icpsr_to_castcode.items():
            assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
            assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"
            
            # Check castcode
            if castcode in self.options.skip_castcodes:
                continue

            castcode_to_count[castcode] = castcode_to_count.get(castcode, 0) + 1

        # Check yea and nay are consistent with rollcall
        if self.rollcall.yea_count != castcode_to_count.get(CastCode.YEA,0):
            raise RuntimeError(f"Rollcall yea count {self.rollcall.yea_count} is not consistent with votes {castcode_to_count.get(CastCode.YEA,0)}")
        if self.rollcall.nay_count != castcode_to_count.get(CastCode.NAY,0):
            raise RuntimeError(f"Rollcall nay count {self.rollcall.nay_count} is not consistent with votes {castcode_to_count.get(CastCode.NAY,0)}")

        return VoteResults(
            congress=self.votes.congress,
            rollnumber=self.votes.rollnumber,
            castcode_to_count=castcode_to_count
            )
        

    def calculate_votes_fractional(self) -> VoteResultsFractional:
        """Fractional vote results

        Returns:
            VoteResultsFractional: Fractional vote results
        """        
        
        # Calculate the number of seats in the House of Representatives - either 435 or the number of votes
        if self.options.use_num_votes_as_num_seats:
            num_seats = len(self.votes.icpsr_to_castcode)
        else:
            num_seats = 435
        
        # Calculate population percentage of each state
        assert self.votes.congress in CONGRESS_TO_CENSUS_YEAR, f"congress {self.votes.congress} not found in CONGRESS_TO_CENSUS_YEAR"
        census_year = CONGRESS_TO_CENSUS_YEAR[self.votes.congress]
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
        for icpsr, castcode in self.votes.icpsr_to_castcode.items():
            assert isinstance(castcode, CastCode), f"castcode is not a CastCode: {castcode}"
            assert isinstance(icpsr, int), f"icpsr is not an int: {icpsr}"

            # Check castcode
            if castcode in self.options.skip_castcodes:
                continue

            # Get state of this member's vote
            if not icpsr in self.members.icpsr_to_state:
                # Missing member - use 1 for their rescale factor
                vote_value = 1.0
            else:
                st = self.members.icpsr_to_state[icpsr]

                # Get rescale factor for this state
                if st == St.DISTRICT_OF_COLUMBIA:
                    # Use 1 for District of Columbia
                    vote_value = 1.0
                else:
                    vote_value = st_to_rescale_factor[st]

            # Add to count = rescale_factor (not 1)
            castcode_to_count[castcode] = castcode_to_count.get(castcode, 0.0) + vote_value

        vr = VoteResults(
            congress=self.votes.congress,
            rollnumber=self.votes.rollnumber,
            castcode_to_count=castcode_to_count
            )
        return VoteResultsFractional(
            vote_results=vr,
            st_to_reps_fair=st_to_reps_fair,
            st_to_reps_actual=st_to_reps_actual
            )