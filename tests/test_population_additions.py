# This test reproduces the data here:
# https://www2.census.gov/programs-surveys/decennial/2020/data/apportionment/apportionment-2020-tableB.pdf
# Additional pop needed for next seat
# Massachusetts - 1960 - 11,436
# Oregon - 1970 - 231
# Indiana - 1980 - 7222
# Massachusetts - 1990 - 12606
# Utah - 200 - 856
# North Carolina - 2010 - 15754
# New York - 2020 - 89

# Note: The additional population numbers are increasing the total US population, not shifting people state-to-state

import houseofreps as hr

class TestPopAddition:

    def test_addition(self):
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
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            
            # Assign house seats
            house.assign_house_seats_priority()
            no_reps = house.states[st].no_reps.voting

            # Add less than required population
            print(f"Pop 1: {house.states[st].pop}")
            house.states[st].pop += (pop_add_true - 1) / (1e6)
            print(f"Pop 2: {house.states[st].pop}")

            # Check no reps did NOT change
            house.assign_house_seats_priority()
            assert house.states[st].no_reps.voting == no_reps

            # Add required population
            house.states[st].pop += (1) / (1e6)
            print(f"Pop 3: {house.states[st].pop}")

            # Check no reps DID change
            house.assign_house_seats_priority()
            assert house.states[st].no_reps.voting == no_reps + 1