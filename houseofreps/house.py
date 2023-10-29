from houseofreps.state import State, St, harmonic_mean, Year, load_states, PopType
import logging
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
from loguru import logger


@dataclass
class PriorityEntry:
    """Entry in priority assignments
    """
    st: St
    no_reps_curr: int
    pop: float
    priority: float


@dataclass
class Priorities:
    """Priorities
    """

    # Key = seat assigned
    # Values = (State, no reps current, population, priority)
    priorities_top: Dict[int,PriorityEntry]
    priorities_all: Dict[int,List[PriorityEntry]]

    def __init__(self):
        self.priorities_top = {}
        self.priorities_all = {}


class HouseOfReps:


    def __init__(self):
        """House of representatives
        """
        self.no_voting_house_seats = 435
        self.no_electoral_votes_true = 538

        self.states = load_states(list(St))

        self.err_tol = 1e-4


    def validate_total_us_pop_assigned_correct(self, year: Year, pop_type: PopType):
        """Validate that the total pop assigned is correct

        Args:
            year (Year): Year to check against
            pop_type (PopType): Population type to check
        """
        assert abs(self.get_total_us_pop_assigned() - self.get_total_us_pop_true(year, pop_type)) < self.err_tol


    def validate_no_reps_matches_true(self, year: Year):
        """Validate that the number of reps matches the true

        Args:
            year (Year): Year to check

        Raises:
            ValueError: If the no reps does not match
        """
        errs = []
        for state in self.states.values():
            try:
                state.validate_no_reps_matches_true(year)
            except Exception as err:
                errs.append(err)
        if len(errs) != 0:
            for err in errs:
                print(err)
            raise ValueError("No. representatives does not match true value for one or more states.")


    def validate_electoral_total_no_votes_matches_true(self):
        """Validate the total no votes in the electoral college matches the true
        """
        no_electoral_votes = self.get_electoral_total_no_votes()
        assert no_electoral_votes == self.no_electoral_votes_true


    def get_electoral_biggest_vote_frac(self) -> Tuple[float,St]:
        """Get the biggest vote fraction in the electoral college

        Returns:
            Tuple[float,St]: (Vote fraction, state)
        """
        st_all = [st for st in St]
        vote_fracs = [self.states[st].electoral_frac_vote for st in st_all]
        idx = np.argmax(vote_fracs)
        return (vote_fracs[idx], st_all[idx])


    def get_electoral_smallest_vote_frac(self) -> Tuple[float,St]:
        """Get the smallest vote fraction in the electoral college

        Returns:
            Tuple[float,St]: (Vote fraction, state)
        """
        st_all = [st for st in St]
        vote_fracs = [self.states[st].electoral_frac_vote for st in st_all]
        idx = np.argmin(vote_fracs)
        return (vote_fracs[idx], st_all[idx])


    def get_electoral_total_no_votes(self) -> int:
        """Get total no votes assigned in electoral college

        Returns:
            int: No votes
        """

        # Check no electoral college votes
        no_electoral_votes = sum([state.get_electoral_no_votes() for state in self.states.values()])
        
        logger.debug("No electoral votes: %d" % no_electoral_votes)
        return no_electoral_votes


    def get_total_us_pop_assigned(self, sts_exclude: List[St] = []) -> float:
        """Get total us population assigned

        Args:
            sts_exclude (List[St], optional): States to exclude.  Defaults to [].

        Returns:
            float: Total assigned population
        """
        total_us_pop = sum(self.states[st].pop_assigned for st in St if not st in sts_exclude)
        if len(sts_exclude) == 0:
            logger.debug("US pop: %f" % total_us_pop)
        else:
            logger.debug("US pop excluding ", sts_exclude, ": %f" % total_us_pop)
        return total_us_pop


    def get_total_us_pop_true(self, year: Year, pop_type: PopType, sts_exclude: List[St] = []) -> float:
        """Get total us population true

        Args:
            year (Year): Year to retrieve pop at
            pop_type (PopType): Population type
            sts_exclude (List[St], optional): List of states to exclude. Defaults to [].

        Returns:
            float: Total assigned population
        """
        total_us_pop_true = sum(self.states[st].pop_true[year].get_pop(pop_type) for st in St if not st in sts_exclude)
        if len(sts_exclude) == 0:
            logger.debug("US pop true for year: %s: %f" % (year,total_us_pop_true))
        else:
            logger.debug("US pop true excluding ", sts_exclude, ": %f" % total_us_pop_true)
        return total_us_pop_true


    def calculate_state_electoral_vote_fracs(self, verbose: bool):
        """Calculate electoral college voting fractions

        Args:
            verbose (bool): True for info logs
        """

        total_us_pop = self.get_total_us_pop()
        no_electoral_votes = self.get_electoral_no_votes()

        # Fraction
        if verbose:
            logger.info("----- State vote fracs -----")
        for state in self.states.values():
            state.electoral_frac = state.get_electoral_no_votes() / no_electoral_votes
            state.electoral_frac_vote = state.electoral_frac * (total_us_pop / state.pop_assigned)
            
            if verbose:
                logger.info("State: %25s frac electoral: %.5f frac vote: %.5f" % 
                    (state.st, state.electoral_frac, state.electoral_frac_vote))
        
        if verbose:
            logger.info("----------")


    def reset_pops_assigned_to_true(self, year: Year, pop_type: PopType):
        """Reset populations to the true values

        Args:
            year (Year): Year to assign
            pop_type (PopType): Population type to assign
        """
        for state in self.states.values():
            state.pop_assigned = state.pop_true[year].get_pop(pop_type)


    def log_pops(self, header: str):
        """Log populations

        Args:
            header (str): Header for logging
        """
        logger.info("----------")
        logger.info(header)
        for state in self.states.values():
            logger.info("%20s : %.5f" % (state.st, state.pop_assigned))
        logger.info("----------")


    def log_house_reps(self):
        """Log house representatives
        """
        for state in self.states.values():
            logger.info("%20s : %d (nonvoting: %d)" % (
                state.no_reps_assigned.voting, state.no_reps_assigned.nonvoting))


    def assign_house_seats_theory(self):
        """Assign house seats by an alternative method.
        """

        ideal = self.get_total_us_pop_assigned(sts_exclude=[St.DISTRICT_OF_COLUMBIA]) / self.no_voting_house_seats
        logger.debug("Ideal size: %f" % ideal)

        i_try = 0
        no_tries_max = 100

        no_voting_house_seats_assigned = 0
        while (no_voting_house_seats_assigned != self.no_voting_house_seats) and (i_try < no_tries_max):

            for state in self.states.values():

                if state.st == St.DISTRICT_OF_COLUMBIA:
                    state.no_reps_assigned.nonvoting = 1
                    state.no_reps_assigned.voting = 0
                    continue

                # All other states only have voting reps
                state.no_reps_assigned.nonvoting = 0

                # Ideal
                no_reps_ideal = state.pop_assigned / ideal

                # Minimum of 1
                if no_reps_ideal < 1:
                    state.no_reps_assigned.voting = 1
                    continue

                lower = int(no_reps_ideal)
                upper = lower + 1
                harmonic_ave = harmonic_mean(lower, upper)

                if no_reps_ideal < harmonic_ave:
                    no_seats = lower
                elif no_reps_ideal > harmonic_ave:
                    no_seats = upper
                else:
                    logger.error("Something went wrong!")
                    continue

                state.no_reps_assigned.voting = no_seats
                # logger.debug("Rounded %f  UP  to %d based on harmonic mean %f" % (ideal_no, upper, harmonic_ave))

            no_voting_house_seats_assigned = sum([state.no_reps_assigned.voting for state in self.states.values()])
            # logger.debug(no_voting_house_seats_assigned)

            if no_voting_house_seats_assigned == self.no_voting_house_seats:
                # Done!
                logger.debug("Adjusted ideal size: %f" % ideal)
                return

            else:
                # Adjust the ideal fraction!
                ideal_old = ideal

                if no_voting_house_seats_assigned > self.no_voting_house_seats:
                    # Tune up
                    ideal *= 1.0001
                elif no_voting_house_seats_assigned < self.no_voting_house_seats:
                    # Tune down
                    ideal *= 0.9999

                logger.debug("Try: %d assigned: %d Adjusted ideal: %f to %f" % (
                    i_try,
                    no_voting_house_seats_assigned,
                    ideal_old,
                    ideal))

                i_try += 1


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
                state.no_reps_assigned.voting = 0
                state.no_reps_assigned.nonvoting = 1
            else:
                state.no_reps_assigned.voting = 1
                state.no_reps_assigned.nonvoting = 0
                no_voting_house_seats_assigned += 1

        pri_st = Priorities()

        # Assign the remaining using priorities
        st_all = [st for st in St if st != St.DISTRICT_OF_COLUMBIA]
        priorities = [(self.states[st].get_priority(), st) for st in st_all]
        priorities.sort(key = lambda x: x[0])
        while no_voting_house_seats_assigned < self.no_voting_house_seats:

            # Find the highest priority
            st_assign = priorities[-1][1]

            if return_priorities_top:
                key = no_voting_house_seats_assigned + 1
                val = PriorityEntry(
                    st=st_assign, 
                    no_reps_curr=self.states[st_assign].no_reps_assigned.voting, 
                    pop=self.states[st_assign].pop_assigned, 
                    priority=priorities[-1][0]
                    )
                pri_st.priorities_top[key] = val

            if return_priorities_all:
                key = no_voting_house_seats_assigned + 1
                vals = [
                    PriorityEntry(
                        st=st, 
                        no_reps_curr=self.states[st].no_reps_assigned.voting, 
                        pop=self.states[st].pop_assigned, 
                        priority=priority
                        ) for priority, st in priorities ]
                pri_st.priorities_all[key] = vals

            # logger.debug("Seat: %d state: %s priority: %f" % (no_voting_house_seats_assigned, st_assign, priorities[idx]))

            # c = self.states[st_assign].no_voting_reps_assigned
            # if st_assign == St.NORTH_CAROLINA or st_assign == St.UTAH:
            #    print("Assigning to state: %s - from %d to %d; nearest priorities:" % (st_assign, c, c+1))
            #    print(priorities[:3])

            # Assign
            self.states[st_assign].no_reps_assigned.voting += 1
            no_voting_house_seats_assigned += 1

            # Re-evaluate priority for this state and re-sort
            priorities[-1] = (self.states[st_assign].get_priority(), st_assign)
            priorities.sort(key = lambda x: x[0])

        return pri_st