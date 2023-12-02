import houseofreps as hr

import os
import pytest

file_path = os.path.dirname(os.path.abspath(__file__))
TEST_VOTING_MEMBERS_CSV = os.path.join(file_path, 'test_voting_members.csv')
TEST_VOTING_VOTES_CSV = os.path.join(file_path, 'test_voting_votes.csv')
TEST_VOTING_ROLLCALLS_CSV = os.path.join(file_path, 'test_voting_rollcalls.csv')


class TestLoadVoteViewCsv:


    def test_load_members(self):
        members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)
        assert len(members.icpsr_to_state) == 538


    def test_load_votes(self):
        votes = hr.LoadVoteViewCsv().load_votes(TEST_VOTING_VOTES_CSV, congress=118, rollnumber=1)
        assert len(votes.icpsr_to_castcode) == 434
        assert votes.congress == 118
        assert votes.rollnumber == 1


    def test_load_votes_all(self):
        votes = hr.LoadVoteViewCsv().load_votes_all(TEST_VOTING_VOTES_CSV)
        assert len(votes.congress_to_rollnumber_to_rollvotes) == 1


    def test_load_rollcalls_all(self):
        rca = hr.LoadVoteViewCsv().load_rollcalls_all(TEST_VOTING_ROLLCALLS_CSV)
        assert rca.no_congresses == 1
        assert rca.no_rollcalls == 9


def test_calculate_vote_results():

    # Load data
    rollvotes = hr.LoadVoteViewCsv().load_votes(TEST_VOTING_VOTES_CSV, congress=118, rollnumber=1)
    members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)

    # Calculate vote results
    vr = hr.CalculateVotes(rollvotes, members).calculate_votes()
    assert vr.castcode_to_count[hr.CastCode.YEA] == 212
    assert vr.castcode_to_count[hr.CastCode.NAY] == 222

def test_calculate_vote_results_fractional():

    # Load data
    rollvotes = hr.LoadVoteViewCsv().load_votes(TEST_VOTING_VOTES_CSV, congress=118, rollnumber=1)
    members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)

    # Calculate vote results
    vr = hr.CalculateVotes(rollvotes, members).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.2672169188732)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.69914043681783)

    options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=True
        )
    vr = hr.CalculateVotes(rollvotes, members, options=options).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.316120218946)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.7217634529414)