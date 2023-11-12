# This script demonstrates some example usage for the package.

import houseofreps as hr

print("--------------------")
print("Basics")
print("--------------------")

# Create the house of reps of a year, filling it with the apportionment population
house = hr.HouseOfReps(
    year=hr.Year.YR2020, 
    pop_type=hr.PopType.APPORTIONMENT
    )
print("Created house of reps")

# Calculate the total US population
pop = house.get_total_us_pop()
print(f"\tTotal US population in 2020: {pop:.2f} million")

# Get the population of a state
pop_state = house.states[hr.St.CALIFORNIA].pop
print(f"\tPopulation of California in 2020: {pop_state:.2f} million")

# Assign the house seats
priorities = house.assign_house_seats_priority(return_priorities_top=True, return_priorities_all=False)
print(f"\tAssigned house seats. Priority assignment of 435th seat assigned: {priorities.priorities_top[435]}")

# Get the number of reps assigned to a state
no_voting = house.states[hr.St.CALIFORNIA].no_reps.voting
print(f"\tNumber of voting reps assigned to California in 2020: {no_voting}")
no_nonvoting = house.states[hr.St.DISTRICT_OF_COLUMBIA].no_reps.nonvoting
print(f"\tNumber of nonvoting reps assigned to DC in 2020: {no_nonvoting}")

print("--------------------")
print("Population changes")
print("--------------------")

# Shift some populations around, and recalculate
print("Changing California population to 1 million")
house.states[hr.St.CALIFORNIA].pop = 1
priorities = house.assign_house_seats_priority(return_priorities_top=True, return_priorities_all=False)
print("\tChanged California population to 1 million")

# Population of US after shift
pop = house.get_total_us_pop()
print(f"\tTotal US population in 2020 after change: {pop:.2f} million")

# Get the number of reps assigned to a state after shift
no_voting = house.states[hr.St.CALIFORNIA].no_reps.voting
print(f"\tNumber of voting reps assigned to California in 2020 after change: {no_voting}")

# Reset to the true values
house = hr.HouseOfReps(
    year=hr.Year.YR2020, 
    pop_type=hr.PopType.APPORTIONMENT
    )
print("Reset to true values")

print("--------------------")
print("True data")
print("--------------------")

# Load the true data
st_to_true_data = hr.load_states_true()
print("Loaded true data")
print(f"\tTrue data for population of California: {st_to_true_data[hr.St.CALIFORNIA].year_to_pop}")
print(f"\tTrue data for no. reps of California: {st_to_true_data[hr.St.CALIFORNIA].year_to_no_reps}")

print("--------------------")
print("Minimum population changes")
print("--------------------")

# Find the minimum population *shift* (one state to the others) required to add a representative to a state
min_change = hr.find_min_pop_change_required_for_change_repr(
    year=hr.Year.YR2020,
    st=hr.St.NEW_YORK,
    target=hr.Target.ADD,
    pop_change_mode=hr.PopChangeMode.SHIFT_POP
    )
min_change = int(min_change*1e6) if min_change is not None else None
print(f"\tMinimum population change required to add a representative to New York in 2020: {min_change:d} people (*not* million)")

min_change = hr.find_min_pop_change_required_for_change_repr(
    year=hr.Year.YR2020,
    st=hr.St.CALIFORNIA,
    target=hr.Target.LOSE,
    pop_change_mode=hr.PopChangeMode.SHIFT_POP
    )
min_change = int(min_change*1e6) if min_change is not None else None
print(f"\tMinimum population change required to remove a representative from California in 2020: {min_change:d} people (*not* million)")