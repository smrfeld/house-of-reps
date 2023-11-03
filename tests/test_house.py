import houseofreps as hr
import pytest

@pytest.fixture
def house():
    return hr.HouseOfReps(
        year=hr.Year.YR2010,
        pop_type=hr.PopType.APPORTIONMENT
        )

class TestHouseOfReps:


    def test_get_electoral_biggest_vote_frac(self, house: hr.HouseOfReps):
        # Fails
        with pytest.raises(Exception):
            house.get_electoral_biggest_vote_frac()

        # Assign house seats
        house.assign_house_seats_priority()

        vote_frac, st = house.get_electoral_biggest_vote_frac()
        print(vote_frac, st)
        assert vote_frac == pytest.approx(3.039638725554007, 1e-6)
        assert st == hr.St.WYOMING


    def test_get_electoral_smallest_vote_frac(self, house: hr.HouseOfReps):
        # Fails
        with pytest.raises(Exception):
            house.get_electoral_smallest_vote_frac()

        # Assign house seats
        house.assign_house_seats_priority()

        vote_frac, st = house.get_electoral_smallest_vote_frac()
        assert vote_frac == pytest.approx(0.8480932623886999, 1e-6)
        assert st == hr.St.CALIFORNIA


    def test_get_electoral_total_no_votes(self, house: hr.HouseOfReps):
        no_votes = house.get_electoral_total_no_votes()
        assert no_votes == 538


    def test_get_total_us_pop(self, house: hr.HouseOfReps):
        total_pop = house.get_total_us_pop()
        assert total_pop == pytest.approx(309.78518600000007, 1e-6)


    def test_assign_house_seats_fractional(self, house: hr.HouseOfReps):
        # Assign house seats
        house.assign_house_seats_fractional()

        true_vals = {
            hr.St.CALIFORNIA: hr.NoReps(voting=52.43557777808005, nonvoting=0),
            hr.St.TEXAS: hr.NoReps(voting=35.481883339637804, nonvoting=0),
            hr.St.FLORIDA: hr.NoReps(voting=26.540443593064516, nonvoting=0),
            hr.St.NEW_YORK: hr.NoReps(voting=27.27102297590175, nonvoting=0),
            hr.St.PENNSYLVANIA: hr.NoReps(voting=17.882338876591724, nonvoting=0)
            }
        for st, no_reps in true_vals.items():
            assert house.states[st].no_reps == no_reps


    def test_assign_house_seats_priority(self):

        for year in hr.Year:
            house = hr.HouseOfReps(
                year=year,
                pop_type=hr.PopType.APPORTIONMENT
                )

            # Assign house seats
            house.assign_house_seats_priority()
            
            hr.validate_no_reps_matches_true(house, year)