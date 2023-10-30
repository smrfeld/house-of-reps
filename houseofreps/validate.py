from houseofreps.state import State, Year, ST_TRUE, PopType
from houseofreps.house import HouseOfReps


ERR_TOL = 1e-6


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


def validate_total_us_pop_assigned_correct(hr: HouseOfReps, year: Year, pop_type: PopType):
    """Validate that the total pop assigned is correct

    Args:
        year (Year): Year to check against
        pop_type (PopType): Population type to check
    """
    hr_true = HouseOfReps(year=year, pop_type=pop_type)
    assert abs(hr.get_total_us_pop() - hr_true.get_total_us_pop()) < ERR_TOL


def validate_no_reps_matches_true(hr: HouseOfReps, year: Year):
    """Validate that the number of reps matches the true

    Args:
        year (Year): Year to check

    Raises:
        ValueError: If the no reps does not match
    """
    errs = []
    for state in hr.states.values():
        try:
            validate_state_no_reps_matches_true(state, year)
        except Exception as err:
            errs.append(err)
    if len(errs) != 0:
        for err in errs:
            print(err)
        raise ValueError("No. representatives does not match true value for one or more states.")


def validate_electoral_total_no_votes_matches_true(hr: HouseOfReps):
    """Validate the total no votes in the electoral college matches the true
    """
    no_electoral_votes = hr.get_electoral_total_no_votes()
    assert no_electoral_votes == hr.no_electoral_votes_true