import houseofreps as hr

import os

file_path = os.path.dirname(os.path.abspath(__file__))
TEST_VOTING_MEMBERS_CSV = os.path.join(file_path, 'test_voting_members.csv')
TEST_VOTING_ROLLVOTES_CSV = os.path.join(file_path, 'test_voting_rollvotes.csv')

class TestLoadVoteViewCsv:

    def test_voting_members(self):
        members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)
        assert len(members.icpsr_to_state) == 12, "Number of members: %d does not match expected: %d" % (len(members.icpsr_to_state), 12)

    def test_voting_rollvotes(self):
        votes = hr.LoadVoteViewCsv().load_rollvotes(TEST_VOTING_ROLLVOTES_CSV, congress=118, rollnumber=1)
        assert len(votes.icpsr_to_castcode) == 434, "Number of votes: %d does not match expected: %d" % (len(votes.icpsr_to_castcode), 434)

    def test_rollvotes_all(self):
        votes = hr.LoadVoteViewCsv().load_rollvotes_all(TEST_VOTING_ROLLVOTES_CSV)
        assert len(votes.congress_to_rollnumber_to_rollvotes) == 1, "Number of congresses: %d does not match expected: %d" % (len(votes.congress_to_rollnumber_to_rollvotes), 1)