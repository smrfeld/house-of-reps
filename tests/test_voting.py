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
        assert len(members.icpsr_to_state) == 538


    def test_load_consistency(self):
        votes, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()
        print(votes.no_rollvotes)


def test_calculate_vote_results():

    # Load data
    votes, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()
    votes0 = votes.congress_to_rollnumber_to_rollvotes[118][1]

    # Calculate vote results
    vr = hr.CalculateVotes(votes0, members).calculate_votes()
    assert vr.castcode_to_count[hr.CastCode.YEA] == 212
    assert vr.castcode_to_count[hr.CastCode.NAY] == 222


def test_calcualte_vote_results_consistent():

    # Load data
    votes, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()

    # Calculate vote results for each vote
    options = hr.CalculateVotes.Options(
        skip_missing_icpsr_in_members=True,
        skip_castcodes=[]
        )
    for congress, rollnumber_to_rollvotes in votes.congress_to_rollnumber_to_rollvotes.items():
        for rollnumber, rollvotes in rollnumber_to_rollvotes.items():
            vr = hr.CalculateVotes(rollvotes, members, options=options).calculate_votes()
            rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
            logger.debug(f"Rollvotes: {rollvotes} Voting: {vr}, Roll-call: {rc}")
            assert rc.yea_count == vr.yea_count_all, f"Voting: {vr}, Roll-call: {rc}"
            assert rc.nay_count == vr.nay_count_all, f"Voting: {vr}, Roll-call: {rc}"


def test_calculate_vote_results_fractional():

    # Load data
    votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=H117_VOTES_CSV, rollcalls_csv=H117_ROLLCALLS_CSV, members_csv=H117_MEMBERS_CSV).load_consistency()
    votes = votes_all.congress_to_rollnumber_to_rollvotes[118][1]

    # Calculate vote results
    vr = hr.CalculateVotes(votes, members).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.2672169188732)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.69914043681783)

    options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=True
        )
    vr = hr.CalculateVotes(votes, members, options=options).calculate_votes_fractional().vote_results
    assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(211.316120218946)
    assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(222.7217634529414)