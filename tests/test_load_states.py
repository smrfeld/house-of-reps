from houseofreps import *

# Load all states
states = load_states(list(St))

for state in states.values():
    assert len(state.pop_true) > 0
    assert len(state.no_reps_true) > 0