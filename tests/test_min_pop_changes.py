import houseofreps as hr
import pytest

class TestMinPopChanges:

    def test_find_min_pop_shift_required_for_change_repr(self):

        true = [
            (hr.Year.YR2020, hr.St.NEW_YORK, hr.Target.ADD, hr.PopChangeMode.SHIFT_POP, 0.000084),
            (hr.Year.YR2020, hr.St.OHIO, hr.Target.ADD, hr.PopChangeMode.SHIFT_POP, 0.011054),
            (hr.Year.YR2020, hr.St.IDAHO, hr.Target.ADD, hr.PopChangeMode.SHIFT_POP, 0.027423),
            (hr.Year.YR2020, hr.St.MINNESOTA, hr.Target.LOSE, hr.PopChangeMode.SHIFT_POP, -0.000025),
            (hr.Year.YR2020, hr.St.MONTANA, hr.Target.LOSE, hr.PopChangeMode.SHIFT_POP, -0.00635),
            (hr.Year.YR2020, hr.St.RHODE_ISLAND, hr.Target.LOSE, hr.PopChangeMode.SHIFT_POP, -0.019064)
        ]

        for year,st,target,pop_change_mode,pop_shift_required in true:
            pop_shift = hr.find_min_pop_change_required_for_change_repr(year, st, target, pop_change_mode)
            assert pop_shift is not None
            assert pop_shift == pytest.approx(pop_shift_required, 1e-6)

    def test_find_min_pop_change_required_for_change_repr(self):
        # https://www2.census.gov/programs-surveys/decennial/2020/data/apportionment/apportionment-2020-tableB.pdf

        true = [
            (hr.Year.YR1960, hr.St.MASSACHUSETTS, 11436),
            (hr.Year.YR1970, hr.St.OREGON, 231),
            # (hr.Year.YR1980, hr.St.INDIANA, 7222),
            (hr.Year.YR1990, hr.St.MASSACHUSETTS, 12606),
            (hr.Year.YR2000, hr.St.UTAH, 856),
            (hr.Year.YR2010, hr.St.NORTH_CAROLINA, 15754),
            (hr.Year.YR2020, hr.St.NEW_YORK, 89)
            ]
        # NOTE: 1980 Indiana is not included because the overseas population is not included in the data

        for year, st, pop_add_true in true:
            pop_change = hr.find_min_pop_change_required_for_change_repr(year, st, hr.Target.ADD, hr.PopChangeMode.CHANGE_POP)
            assert pop_change is not None
            assert pop_change == pytest.approx(pop_add_true / 1e6, 1e-6)