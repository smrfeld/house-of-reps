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


def validate_total_us_pop_assigned_correct(house: HouseOfReps, pop_type: PopType):
    """Validate that the total pop assigned is correct

    Args:
        house (HouseOfReps): House of reps
        pop_type (PopType): Population type to check
    """
    hr_true = HouseOfReps(year=house.year, pop_type=pop_type)
    assert abs(house.get_total_us_pop() - hr_true.get_total_us_pop()) < ERR_TOL, "Total US pop assigned: %f does not match true value: %f" % (house.get_total_us_pop(), hr_true.get_total_us_pop())


def validate_no_reps_matches_true(house: HouseOfReps):
    """Validate that the number of reps matches the true

    Args:
        house (HouseOfReps): House of reps

    Raises:
        ValueError: If the no reps does not match
    """
    errs = []
    for state in house.states.values():
        try:
            validate_state_no_reps_matches_true(state, house.year)
        except Exception as err:
            errs.append(err)
    if len(errs) != 0:
        for err in errs:
            print(err)
        raise ValueError("No. representatives does not match true value for one or more states.")


def validate_electoral_total_no_votes_matches_true(house: HouseOfReps):
    """Validate the total no votes in the electoral college matches the true

    Args:
        house (HouseOfReps): House of reps
    """
    no_electoral_votes = house.get_electoral_total_no_votes()
    assert no_electoral_votes == house.no_electoral_votes_true, "Total no. electoral college votes: %d does not match true value: %d" % (no_electoral_votes, house.no_electoral_votes_true)
