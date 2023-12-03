from houseofreps.state import State, St, harmonic_mean, Year, load_states_true, PopType
import logging
import numpy as np
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ElectoralFrac:
    """Electoral fraction

    Args:
        electoral_frac_vote (float): Electoral fraction by population = electoral_frac * (total US population / state population)
        electoral_frac (float): Electoral fraction = (number of electoral votes assigned to the state) / (total number of electoral votes)
    """    

    electoral_frac_vote: float
    "Electoral fraction by population = electoral_frac * (total US population / state population)"

    electoral_frac: float
    "Electoral fraction = (number of electoral votes assigned to the state) / (total number of electoral votes)"


class HouseOfReps:


    def __init__(self, year: Year, pop_type: PopType, no_voting_house_seats: int = 435, no_electoral_votes_true: int = 538):
        """House of representatives

        Args:
            year (Year): Year
            pop_type (PopType): Population type
            no_voting_house_seats (int, optional): Number of voting house seats. Defaults to 435.
            no_electoral_votes_true (int, optional): Number of electoral votes. Defaults to 538.
        """        
        self.year = year
        self.no_voting_house_seats = no_voting_house_seats
        self.no_electoral_votes_true = no_electoral_votes_true

        self.states: Dict[St,State] = { st: State.from_true(st, year, pop_type=pop_type) for st in St }
        self.electoral_fracs: Optional[Dict[St,ElectoralFrac]] = None


    def get_electoral_biggest_vote_frac(self) -> Tuple[float,St]:
        """Get the biggest vote fraction in the electoral college

        Returns:
            Tuple[float,St]: (Vote fraction, state)
        """
        assert self.electoral_fracs is not None, "First assign house seats!"
        st_all = [st for st in St]
        vote_fracs = [ self.electoral_fracs[st].electoral_frac_vote for st in st_all ]
        idx = np.argmax(vote_fracs)
        return (vote_fracs[idx], st_all[idx])


    def get_electoral_smallest_vote_frac(self) -> Tuple[float,St]:
        """Get the smallest vote fraction in the electoral college

        Returns:
            Tuple[float,St]: (Vote fraction, state)
        """
        assert self.electoral_fracs is not None, "First assign house seats!"
        st_all = [st for st in St]
        vote_fracs = [self.electoral_fracs[st].electoral_frac_vote for st in st_all]
        idx = np.argmin(vote_fracs)
        return (vote_fracs[idx], st_all[idx])


    def get_electoral_total_no_votes(self) -> float:
        """Get total no votes assigned in electoral college

        Returns:
            float: No votes
        """

        # Check no electoral college votes
        no_electoral_votes = sum([
            state.get_electoral_no_votes_assigned() for state in self.states.values()
            ])
        
        return no_electoral_votes


    def get_total_us_pop(self, sts_exclude: List[St] = []) -> float:
        """Get total us population assigned

        Args:
            sts_exclude (List[St], optional): States to exclude.  Defaults to [].

        Returns:
            float: Total assigned population
        """
        return sum(self.states[st].pop for st in St if not st in sts_exclude)


    def log_pops(self, header: str):
        """Log populations

        Args:
            header (str): Header for logging
        """
        logger.info("----------")
        logger.info(header)
        for state in self.states.values():
            logger.info("%20s : %.5f" % (state.st, state.pop))
        logger.info("----------")


    def log_reps(self):
        """Log house representatives
        """
        for state in self.states.values():
            logger.info("%20s : %d (nonvoting: %d)" % (
                state.no_reps.voting, state.no_reps.nonvoting))


    def assign_house_seats_fractional(self):
        """Assign house seats by fractional method
        """        
        pop_tot = self.get_total_us_pop()
        for state in self.states.values():
            pop_frac = state.pop / pop_tot
            state.no_reps
            state.no_reps.voting = pop_frac * self.no_voting_house_seats
            state.no_reps.nonvoting = 0
            
        self._calculate_state_electoral_vote_fracs(verbose=False)


    @dataclass
    class PriorityEntry:
        """Entry in priority assignments

        Args:
            st (St): State
            no_reps_curr (float): Number of representatives currently assigned to the state
            pop (float): Population of the state
            priority (float): Priority of the state
        """

        st: St
        "State"

        no_reps_curr: float
        "Number of representatives currently assigned to the state"

        pop: float
        "Population of the state"

        priority: float
        "Priority of the state"


    @dataclass
    class Priorities:
        """Priorities

        Args:
            priorities_top (Dict[int, HouseOfReps.PriorityEntry]): Top priorities at each seat assignment. Keys are the index of the seat assigned, starting at 51. Values are the top priority entry.
            priorities_all (Dict[int, List[HouseOfReps.PriorityEntry]]): All priorities at each seat assignment. Keys are the index of the seat assigned, starting at 51. Values are all priority entries for this assignment.
        """

        priorities_top: Dict[int, "HouseOfReps.PriorityEntry"] = field(default_factory=dict)
        "Top priorities at each seat assignment. Keys are the index of the seat assigned, starting at 51. Values are the top priority entry."

        priorities_all: Dict[int, List["HouseOfReps.PriorityEntry"]] = field(default_factory=dict)
        "All priorities at each seat assignment. Keys are the index of the seat assigned, starting at 51. Values are all priority entries for this assignment."


    def assign_house_seats_priority(self, return_priorities_top: bool = False, return_priorities_all: bool = False) -> Priorities:
        """Assign house seats using priority method

        Args:
            return_priorities_top (bool, optional): Return top priorities at each assignment. Defaults to False.
            return_priorities_all (bool, optional): Return all priorities at each assignment. Defaults to False.

        Returns:
            Priorities: Priorities at each assignment step.
        """

        no_voting_house_seats_assigned = 0

        # Assign each state mandatory 1 delegate
        for state in self.states.values():
            if state.st == St.DISTRICT_OF_COLUMBIA:
                state.no_reps.voting = 0
                state.no_reps.nonvoting = 1
            else:
                state.no_reps.voting = 1
                state.no_reps.nonvoting = 0
                no_voting_house_seats_assigned += 1

        pri_st = HouseOfReps.Priorities()

        # Assign the remaining using priorities
        st_all = [st for st in St if st != St.DISTRICT_OF_COLUMBIA]
        priorities = [(self.states[st].get_priority(), st) for st in st_all]
        priorities.sort(key = lambda x: x[0])
        while no_voting_house_seats_assigned < self.no_voting_house_seats:

            # Find the highest priority
            st_assign = priorities[-1][1]

            if return_priorities_top:
                key = no_voting_house_seats_assigned + 1
                val = HouseOfReps.PriorityEntry(
                    st=st_assign, 
                    no_reps_curr=self.states[st_assign].no_reps.voting, 
                    pop=self.states[st_assign].pop, 
                    priority=priorities[-1][0]
                    )
                pri_st.priorities_top[key] = val

            if return_priorities_all:
                key = no_voting_house_seats_assigned + 1
                vals = [
                    HouseOfReps.PriorityEntry(
                        st=st, 
                        no_reps_curr=self.states[st].no_reps.voting, 
                        pop=self.states[st].pop, 
                        priority=priority
                        ) for priority, st in priorities ]
                pri_st.priorities_all[key] = vals

            # logger.debug("Seat: %d state: %s priority: %f" % (no_voting_house_seats_assigned, st_assign, priorities[idx]))

            # c = self.states[st_assign].no_voting_reps_assigned
            # if st_assign == St.NORTH_CAROLINA or st_assign == St.UTAH:
            #    print("Assigning to state: %s - from %d to %d; nearest priorities:" % (st_assign, c, c+1))
            #    print(priorities[:3])

            # Assign
            self.states[st_assign].no_reps.voting += 1
            no_voting_house_seats_assigned += 1

            # Re-evaluate priority for this state and re-sort
            priorities[-1] = (self.states[st_assign].get_priority(), st_assign)
            priorities.sort(key = lambda x: x[0])

        self._calculate_state_electoral_vote_fracs(verbose=False)

        return pri_st


    def _calculate_state_electoral_vote_fracs(self, verbose: bool):
        """Calculate electoral college voting fractions

        Args:
            verbose (bool): True for info logs
        """

        total_us_pop = self.get_total_us_pop()
        no_electoral_votes = self.get_electoral_total_no_votes()

        # Fraction
        if verbose:
            logger.info("----- State vote fracs -----")
        self.electoral_fracs = {}
        for state in self.states.values():

            # Compute frac
            electoral_frac = state.get_electoral_no_votes_assigned() / no_electoral_votes

            # Compute frac_vote
            electoral_frac_vote = electoral_frac * (total_us_pop / state.pop)

            # Store
            self.electoral_fracs[state.st] = ElectoralFrac(
                electoral_frac_vote=electoral_frac_vote,
                electoral_frac=electoral_frac
                )
            
            if verbose:
                logger.info("State: %25s frac electoral: %.5f frac vote: %.5f" % 
                    (state.st, electoral_frac, electoral_frac_vote))
        
        if verbose:
            logger.info("----------")
