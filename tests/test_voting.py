import houseofreps as hr

import os
import pytest

file_path = os.path.dirname(os.path.abspath(__file__))
TEST_VOTING_MEMBERS_CSV = os.path.join(file_path, 'test_voting_members.csv')
TEST_VOTING_ROLLVOTES_CSV = os.path.join(file_path, 'test_voting_rollvotes.csv')

class TestLoadVoteViewCsv:

    def test_voting_members(self):
        members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)
        assert len(members.icpsr_to_state) == 538

    def test_voting_rollvotes(self):
        votes = hr.LoadVoteViewCsv().load_rollvotes(TEST_VOTING_ROLLVOTES_CSV, congress=118, rollnumber=1)
        assert len(votes.icpsr_to_castcode) == 434
        assert votes.congress == 118
        assert votes.rollnumber == 1

    def test_rollvotes_all(self):
        votes = hr.LoadVoteViewCsv().load_rollvotes_all(TEST_VOTING_ROLLVOTES_CSV)
        assert len(votes.congress_to_rollnumber_to_rollvotes) == 1

def test_calculate_vote_results():

    # Load data
    rollvotes = hr.LoadVoteViewCsv().load_rollvotes(TEST_VOTING_ROLLVOTES_CSV, congress=118, rollnumber=1)

    # Calculate vote results
    vr = hr.calculate_votes(rollvotes)
    assert vr.castcode_to_count[hr.CastCode.YEA] == 212
    assert vr.castcode_to_count[hr.CastCode.NAY] == 222

def test_calculate_vote_results_fractional():

    # Load data
    rollvotes = hr.LoadVoteViewCsv().load_rollvotes(TEST_VOTING_ROLLVOTES_CSV, congress=118, rollnumber=1)
    members = hr.LoadVoteViewCsv().load_members(TEST_VOTING_MEMBERS_CSV)

    # Calculate vote results
    vr = hr.calculate_votes_fractional(rollvotes, members, census_year=hr.Year.YR2020).vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.2672169188732)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.69914043681783)

    vr = hr.calculate_votes_fractional(rollvotes, members, census_year=hr.Year.YR2020, use_num_votes_as_num_seats=True).vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.316120218946)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.7217634529414)