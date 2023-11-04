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
            pop_shift = hr.find_min_pop_shift_required_for_change_repr(year, st, target, pop_change_mode)
            assert pop_shift is not None
            assert pop_shift == pytest.approx(pop_shift_required, 1e-6)