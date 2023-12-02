import houseofreps as hr

import os

file_path = os.path.dirname(os.path.abspath(__file__))
TEST_VOTING_MEMBERS_CSV = os.path.join(file_path, 'test_voting_members.csv')

def test_voting_members():
    members = hr.load_members_from_csv(TEST_VOTING_MEMBERS_CSV)
    assert len(members.icpsr_to_state) == 12, "Number of members: %d does not match expected: %d" % (len(members.icpsr_to_state), 12)
