from .state import State, St, harmonic_mean, Year, load_states, PopType
import logging
import numpy as np
from typing import Tuple

class HouseOfReps:

    def __init__(self):

        self.no_voting_house_seats = 435
        self.no_electoral_votes_true = 538

        self.states = load_states(list(St))
        
        # Logging
        handlerPrint = logging.StreamHandler()
        handlerPrint.setLevel(logging.DEBUG)
        self.log = logging.getLogger("states")
        self.log.addHandler(handlerPrint)
        self.log.setLevel(logging.INFO)

        self.err_tol = 1e-4

    def validate_total_us_pop_assigned_correct(self, year: Year, pop_type: PopType):
        assert abs(self.get_total_us_pop_assigned() - self.get_total_us_pop_true(year, pop_type)) < self.err_tol

    def validate_no_reps_matches_true(self, year: Year):
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
        no_electoral_votes = self.get_electoral_total_no_votes()
        assert no_electoral_votes == self.no_electoral_votes_true

    def get_electoral_biggest_vote_frac(self) -> Tuple[int,St]:
        st_all = [st for st in St]
        vote_fracs = [self.states[st].electoral_frac_vote for st in st_all]
        idx = np.argmax(vote_fracs)
        return (vote_fracs[idx], st_all[idx])

    def get_electoral_smallest_vote_frac(self) -> Tuple[int,St]:
        st_all = [st for st in St]
        vote_fracs = [self.states[st].electoral_frac_vote for st in st_all]
        idx = np.argmin(vote_fracs)
        return (vote_fracs[idx], st_all[idx])

    def get_electoral_total_no_votes(self) -> int:
        
        # Check no electoral college votes
        no_electoral_votes = sum([state.get_electoral_no_votes() for state in self.states.values()])
        
        self.log.debug("No electoral votes: %d" % no_electoral_votes)
        return no_electoral_votes

    def get_total_us_pop_assigned(self) -> float:
        total_us_pop = sum(self.states[state].pop_assigned for state in St)
        self.log.debug("US pop: %f" % total_us_pop)
        return total_us_pop

    def get_total_us_pop_assigned_excluding_st(self, st_exclude: St) -> float:
        total_other_pop = sum(self.states[st].pop_assigned for st in St if st != st_exclude)
        self.log.debug("US pop excluding %s: %f" % (st_exclude, total_other_pop))
        return total_other_pop

    def get_total_us_pop_true(self, year: Year, pop_type: PopType) -> float:
        total_us_pop_true = sum(self.states[state].pop_true[year].get_pop(pop_type) for state in St)
        self.log.debug("US pop true for year: %s: %f" % (year,total_us_pop_true))
        return total_us_pop_true

    def get_total_us_pop_true_excluding_st(self, year: Year, pop_type: PopType, st_exclude: St) -> float:
        total_other_pop = sum([state.pop_true[year].get_pop(pop_type) for state in self.states.values() if state.st != st_exclude])
        self.log.debug("US pop true excluding %s: %f" % (st_exclude, total_other_pop))
        return total_other_pop

    def calculate_state_electoral_vote_fracs(self, verbose: bool):
        
        total_us_pop = self.get_total_us_pop()
        no_electoral_votes = self.get_electoral_no_votes()

        # Fraction
        if verbose:
            self.log.info("----- State vote fracs -----")
        for state in self.states.values():
            state.electoral_frac = state.get_electoral_no_votes() / no_electoral_votes
            state.electoral_frac_vote = state.electoral_frac * (total_us_pop / state.pop_assigned)
            
            if verbose:
                self.log.info("State: %25s frac electoral: %.5f frac vote: %.5f" % 
                    (state.st, state.electoral_frac, state.electoral_frac_vote))
        
        if verbose:
            self.log.info("----------")

    def reset_pops_assigned_to_true(self, year: Year, pop_type: PopType):
        for state in self.states.values():
            state.pop_assigned = state.pop_true[year].get_pop(pop_type)

    def log_pops(self, header: str):
        self.log.info("----------")
        self.log.info(header)
        for state in self.states.values():
            self.log.info("%20s : %.5f" % (state.st, state.pop_assigned))
        self.log.info("----------")

    def log_house_reps(self):
        for state in self.states.values():
            self.log.info("%20s : %d (nonvoting: %d)" % (
                state.no_reps_assigned.voting, state.no_reps_assigned.nonvoting))

    def shift_pop_from_state_to_entire_us(self, st_from : St, percent_of_st_from : int, verbose: bool):
        assert (percent_of_st_from >= 0)
        assert (percent_of_st_from <= 100)

        # No people to remove
        state_from = self.states[st_from]
        no_leave = state_from.pop_assigned * percent_of_st_from / 100.0

        # Remove pop from this state
        state_from.pop_assigned -= no_leave

        # Calculate pop fracs for all the other states
        total_other_pop = self.get_total_us_pop_assigned_excluding_st(st_from)
        for st_other, state_other in self.states.items():
            if st_from == st_other:
                continue # skip

            frac = state_other.pop_assigned / total_other_pop

            # Increment pop of other states
            state_other.pop_assigned += frac * no_leave

        if verbose:
            self.log_pops("pops after: %f million people move from: %s to entire US" % (no_leave, st_from))

    def shift_pop_from_entire_us_to_state_by_global_percentage(self, st_to : St, percent_of_entire_us : int, verbose: bool):
        assert (percent_of_entire_us >= 0)
        assert (percent_of_entire_us <= 100)

        total_other_pop = self.get_total_us_pop_assigned_excluding_st(st_to)
        no_leave = total_other_pop * percent_of_entire_us / 100.0

        # Add pop to this state
        state_to = self.states[st_to]
        state_to.pop_assigned += no_leave

        # Calculate pop fracs for all the other states
        for st_other, state_other in self.states.items():
            if st_to == st_other:
                continue # skip

            frac = state_other.pop_assigned / total_other_pop

            # Increment pop of other states
            state_other.pop_assigned -= frac * no_leave

        if verbose:
            self.log_pops("pops after: %f million people move from entire US to: %s" % (no_leave, st_to))

    def shift_pop_from_entire_us_to_state_by_local_percentage(self, st_to : St, percent_of_st_to : int, verbose: bool):

        # Add pop to this state
        state_to = self.states[st_to]
        no_add = state_to.pop_assigned * percent_of_st_to / 100.0
        
        # Check enough people in USA
        total_other_pop = self.get_total_us_pop_assigned_excluding_st(st_to)
        assert no_add <= total_other_pop

        # Move people to the state
        state_to.pop_assigned += no_add

        # Remove from rest of USA
        for st_other, state_other in self.states.items():
            if st_to == st_other:
                continue # skip

            frac = state_other.pop_assigned / total_other_pop

            # Increment pop of other states
            state_other.pop_assigned -= frac * no_add

        if verbose:
            self.log_pops("pops after: %f million people move from entire US to: %s" % (no_add, st_to))

    def shift_pop_from_entire_us_to_state(self, st_to : St, pop_add_millions : float, verbose: bool):

        # Add pop to this state
        state_to = self.states[st_to]
        no_add = pop_add_millions
        
        # Check enough people in USA
        total_other_pop = self.get_total_us_pop_assigned_excluding_st(st_to)
        assert no_add <= total_other_pop

        # Check enough people in state
        if state_to.pop_assigned + no_add < 0:
            raise ValueError("Trying to remove: %f people from state: %s but this is more than the number of people in the state: %f." 
                % (no_add, st_to, state_to.pop_assigned))

        # Move people to the state
        state_to.pop_assigned += no_add

        # Remove from rest of USA
        for st_other, state_other in self.states.items():
            if st_to == st_other:
                continue # skip

            frac = state_other.pop_assigned / total_other_pop

            # Increment pop of other states
            state_other.pop_assigned -= frac * no_add

        if verbose:
            self.log_pops("pops after: %f million people move from entire US to: %s" % (no_add, st_to))

    def shift_pop_from_state_to_state(self, st_from : St, st_to : St, percent : int, verbose: bool):
        assert (percent >= 0)
        assert (percent <= 100)

        state_from = self.states[st_from]
        state_to = self.states[st_to]

        # No people to remove
        no_leave = state_from.pop_assigned * percent / 100.0

        # Remove pop from this state
        state_from.pop_assigned -= no_leave
        state_to.pop_assigned += no_leave

        if verbose:
            self.log.info("----------")
            self.log.info("pops after: %f million people move from: %s to: %s" % (no_leave, st_from, st_to))
            self.log.info("%20s : %.5f" % (state_from.st, state_from.pop_assigned))
            self.log.info("%20s : %.5f" % (state_to.st, state_to.pop_assigned))
            self.log.info("----------")

    def assign_house_seats_theory(self):

        ideal = self.get_total_us_pop_excluding_DC() / self.no_voting_house_seats
        self.log.debug("Ideal size: %f" % ideal)

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
                    self.log.error("Something went wrong!")
                    continue

                state.no_reps_assigned.voting = no_seats
                # self.log.debug("Rounded %f  UP  to %d based on harmonic mean %f" % (ideal_no, upper, harmonic_ave))

            no_voting_house_seats_assigned = sum([state.no_reps_assigned.voting for state in self.states.values()])
            # self.log.debug(no_voting_house_seats_assigned)

            if no_voting_house_seats_assigned == self.no_voting_house_seats:
                # Done!
                self.log.debug("Adjusted ideal size: %f" % ideal)
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

                self.log.debug("Try: %d assigned: %d Adjusted ideal: %f to %f" % (
                    i_try,
                    no_voting_house_seats_assigned,
                    ideal_old,
                    ideal))

                i_try += 1

    def assign_house_seats_priority(self):

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

        # Assign the remaining using priorities
        st_all = [st for st in St if st != St.DISTRICT_OF_COLUMBIA]
        priorities = [(self.states[st].get_priority(), st) for st in st_all]
        priorities.sort(key = lambda x: x[0])
        while no_voting_house_seats_assigned < self.no_voting_house_seats:

            # Find the highest priority
            st_assign = priorities[-1][1]

            # self.log.debug("Seat: %d state: %s priority: %f" % (no_voting_house_seats_assigned, st_assign, priorities[idx]))

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
