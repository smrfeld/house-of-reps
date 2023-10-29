import houseofreps as hr
import math
import pytest


def test_load_states():
    """Test we can load all the states
    """

    # Load all states
    states = hr.load_states(list(hr.St))

    for state in states.values():
        assert len(state.pop_true) > 0
        assert len(state.no_reps_true) > 0


def test_st_all_except_dc():
    st_list = hr.St.all_except_dc()
    assert len(st_list) == 50
    assert not hr.St.DISTRICT_OF_COLUMBIA in st_list


def test_st_from_name():
    assert hr.St.from_name("Alabama") == hr.St.ALABAMA
    assert hr.St.from_name("District of Columbia") == hr.St.DISTRICT_OF_COLUMBIA
    assert hr.St.from_name("West Virginia") == hr.St.WEST_VIRGINIA


def test_st_name():
    assert hr.St.ALABAMA.name == "Alabama"
    assert hr.St.DISTRICT_OF_COLUMBIA.name == "District of Columbia"
    assert hr.St.WEST_VIRGINIA.name == "West Virginia"


TOL = 1e-6


def test_arithmetic_mean():
    assert hr.arithmetic_mean(1, 2) == pytest.approx(1.5, TOL)


def test_harmonic_mean():
    assert hr.harmonic_mean(1, 2) == pytest.approx(1.3333333333333333, TOL)


def test_geometric_mean():
    assert hr.geometric_mean(1, 2) == pytest.approx(math.sqrt(1.0 * 2.0), TOL)


