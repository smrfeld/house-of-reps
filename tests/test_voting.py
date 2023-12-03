import houseofreps as hr

import os
import pytest
from loguru import logger


file_path = os.path.dirname(os.path.abspath(__file__))

H117_MEMBERS_CSV = os.path.join(file_path, 'H117_members.csv')
H117_VOTES_CSV = os.path.join(file_path, 'H117_votes.csv')
H117_ROLLCALLS_CSV = os.path.join(file_path, 'H117_rollcalls.csv')


class TestLoadVoteViewCsv:


    def test_load_members(self):
        members = hr.LoadVoteViewCsv(members_csv=H117_MEMBERS_CSV).load_members()
        assert len(members.icpsr_to_state) == 450


    def test_load_consistency(self):
        votes, rollcalls, members = hr.LoadVoteViewCsv(
            votes_csv=H117_VOTES_CSV, 
            rollcalls_csv=H117_ROLLCALLS_CSV, 
            members_csv=H117_MEMBERS_CSV
            ).load_consistency()
        assert votes.no_rollcalls == 996
        assert rollcalls.no_rollcalls == 996
        assert len(members.icpsr_to_state) == 450


def test_calculate_vote_results():

    # Load data
    votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()
    votes = votes_all.congress_to_rollnumber_to_votes[117][1]
    rc = rollcalls.congress_to_rollnumber_to_rollcall[117][1]

    # Calculate vote results
    vr = hr.CalculateVotes(votes, members, rc).calculate_votes()
    assert vr.castcode_to_count[hr.CastCode.YEA] == 216
    assert vr.castcode_to_count[hr.CastCode.NAY] == 211


def test_calcualte_vote_results_consistent():

    # Load data
    votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()

    # Calculate vote results for each vote
    options = hr.CalculateVotes.Options(
        skip_castcodes=[]
        )
    for congress, rollnumber_to_rollvotes in votes_all.congress_to_rollnumber_to_votes.items():
        for rollnumber, votes in rollnumber_to_rollvotes.items():
            rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
            vr = hr.CalculateVotes(votes, members, rc, options=options).calculate_votes()
            rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
            assert rc.yea_count == vr.yea_count_all, f"Voting: {vr}, Roll-call: {rc}"
            assert rc.nay_count == vr.nay_count_all, f"Voting: {vr}, Roll-call: {rc}"


def test_calculate_vote_results_fractional():

    # Load data
    votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()
    votes = votes_all.congress_to_rollnumber_to_votes[117][1]
    rc = rollcalls.congress_to_rollnumber_to_rollcall[117][1]

    # Calculate vote results
    vr = hr.CalculateVotes(votes, members, rc).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(215.76760646980654)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(211.74396112191627)

    options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=True
        )
    vr = hr.CalculateVotes(votes, members, rc, options=options).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(215.30891482085957)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(212.01347793114823)