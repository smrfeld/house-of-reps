import houseofreps as hr
import numpy as np
import random

class TestPopShifts:

    def test_shift_pop_from_entire_us_to_state(self):
        for year in hr.Year:
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            for st in random.choices(list(hr.St), k=5):
                pop_shift = np.random.uniform(0, 0.1)
                hr.shift_pop_from_entire_us_to_state(house, st_to=st, pop_shift_millions=pop_shift, verbose=True)
                hr.validate_total_us_pop_assigned_correct(house, pop_type=hr.PopType.APPORTIONMENT)

    def test_shift_pop_from_entire_us_to_state_by_local_percentage(self):
        for year in hr.Year:
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            for st in random.choices(list(hr.St), k=5):
                percent_of_st_to = np.random.uniform(0, 0.1)
                hr.shift_pop_from_entire_us_to_state_by_local_percentage(house, st_to=st, percent_of_st_to=percent_of_st_to, verbose=True)
                hr.validate_total_us_pop_assigned_correct(house, pop_type=hr.PopType.APPORTIONMENT)

    def test_shift_pop_from_entire_us_to_state_by_global_percentage(self):
        for year in hr.Year:
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            for st in random.choices(list(hr.St), k=5):
                percent_of_us = np.random.uniform(0, 0.1)
                hr.shift_pop_from_entire_us_to_state_by_global_percentage(house, st_to=st, percent_of_entire_us=percent_of_us, verbose=True)
                hr.validate_total_us_pop_assigned_correct(house, pop_type=hr.PopType.APPORTIONMENT)

    def test_shift_pop_from_state_to_entire_us(self):
        for year in hr.Year:
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            for st in random.choices(list(hr.St), k=5):
                percent_of_st_from = np.random.uniform(0, 0.1)
                hr.shift_pop_from_state_to_entire_us(house, st_from=st, percent_of_st_from=percent_of_st_from, verbose=True)
                hr.validate_total_us_pop_assigned_correct(house, pop_type=hr.PopType.APPORTIONMENT)

    def test_shift_pop_from_state_to_state(self):
        for year in hr.Year:
            house = hr.HouseOfReps(year=year, pop_type=hr.PopType.APPORTIONMENT)
            for st in random.choices(list(hr.St), k=5):
                for st_other in random.choices(list(hr.St), k=5):
                    percent_of_st_from = np.random.uniform(0, 0.1)
                    hr.shift_pop_from_state_to_state(house, st_from=st, st_to=st_other, percent=percent_of_st_from, verbose=True)
                    hr.validate_total_us_pop_assigned_correct(house, pop_type=hr.PopType.APPORTIONMENT)
