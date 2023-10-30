from houseofreps.state import State, Year, ST_TRUE, PopType


def validate_state_no_reps_matches_true(state: State, year: Year):
    """Validate that the number of reps assigned matches the true value

    Args:
        state (State): State to check (must be in ST_TRUE)
        year (Year): Year to check against

    Raises:
        ValueError: In case the reps does not match
    """
    state_true = ST_TRUE[state.st]

    # Validate that they match the expected
    if state.no_reps.voting != state_true.year_to_no_reps[year].voting:
        raise ValueError("State: %s no. voting reps assigned: %d does not match the true no. reps: %d in year: %s" % 
            (state.st, state.no_reps.voting, state_true.year_to_no_reps[year].voting, year))
    if state.no_reps.nonvoting != state_true.year_to_no_reps[year].nonvoting:
        raise ValueError("State: %s no. nonvoting reps assigned: %d does not match the true no. reps: %d in year: %s" % 
            (state.st, state.no_reps.nonvoting, state_true.year_to_no_reps[year].nonvoting, year))


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
