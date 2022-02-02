from houseofreps import *

def test_no_reps_matches_true():
    """Assign no reps and check it matches true assignments
    """

    house = HouseOfReps()

    for year in Year:
        house.reset_pops_assigned_to_true(year, PopType.APPORTIONMENT)
        house.assign_house_seats_priority()

        # Validate
        try:
            house.validate_no_reps_matches_true(year)
        except Exception as err:
            print(err)
