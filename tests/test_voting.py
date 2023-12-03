import houseofreps as hr

import os
import pytest
from loguru import logger


file_path = os.path.dirname(os.path.abspath(__file__))

H116_MEMBERS_CSV = os.path.join(file_path, 'H116_members.csv')
H116_VOTES_CSV = os.path.join(file_path, 'H116_votes.csv')
H116_ROLLCALLS_CSV = os.path.join(file_path, 'H116_rollcalls.csv')


H117_MEMBERS_CSV = os.path.join(file_path, 'H117_members.csv')
H117_VOTES_CSV = os.path.join(file_path, 'H117_votes.csv')
H117_ROLLCALLS_CSV = os.path.join(file_path, 'H117_rollcalls.csv')


class TestLoadVoteViewCsv:


    def test_load_members(self):
        members = hr.LoadVoteViewCsv(members_csv=H117_MEMBERS_CSV).load_members()
        assert len(members.icpsr_to_state) == 450

        members = hr.LoadVoteViewCsv(members_csv=H116_MEMBERS_CSV).load_members()
        assert len(members.icpsr_to_state) == 446


    def test_load_consistency(self):
        votes, rollcalls, members = hr.LoadVoteViewCsv(
            votes_csv=H117_VOTES_CSV, 
            rollcalls_csv=H117_ROLLCALLS_CSV, 
            members_csv=H117_MEMBERS_CSV
            ).load_consistency()
        assert votes.no_rollcalls == 996
        assert rollcalls.no_rollcalls == 996
        assert len(members.icpsr_to_state) == 450

        votes, rollcalls, members = hr.LoadVoteViewCsv(
            votes_csv=H116_VOTES_CSV, 
            rollcalls_csv=H116_ROLLCALLS_CSV, 
            members_csv=H116_MEMBERS_CSV
            ).load_consistency()
        assert votes.no_rollcalls == 952
        assert rollcalls.no_rollcalls == 952
        assert len(members.icpsr_to_state) == 446


def test_calculate_vote_results():

    for votes_csv, rollcalls_csv, members_csv, congress, yea, nay in [
        (H117_VOTES_CSV, H117_ROLLCALLS_CSV, H117_MEMBERS_CSV, 117, 216, 211),
        (H116_VOTES_CSV, H116_ROLLCALLS_CSV, H116_MEMBERS_CSV, 116, 220, 210)
        ]:
        # Load data
        votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=votes_csv, rollcalls_csv=rollcalls_csv, members_csv=members_csv).load_consistency()
        votes = votes_all.congress_to_rollnumber_to_votes[congress][1]
        rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][1]

        # Calculate vote results
        vr = hr.CalculateVotes(votes, members, rc).calculate_votes()
        assert vr.castcode_to_count[hr.CastCode.YEA] == yea
        assert vr.castcode_to_count[hr.CastCode.NAY] == nay


def test_calcualte_vote_results_consistent():

    for votes_csv, rollcalls_csv, members_csv in [
        (H117_VOTES_CSV, H117_ROLLCALLS_CSV, H117_MEMBERS_CSV),
        (H116_VOTES_CSV, H116_ROLLCALLS_CSV, H116_MEMBERS_CSV)
        ]:

        # Load data
        votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=votes_csv, rollcalls_csv=rollcalls_csv, members_csv=members_csv).load_consistency()

        # Calculate vote results for each vote
        options = hr.CalculateVotes.Options(
            skip_castcodes=[]
            )
        for congress, rollnumber_to_rollvotes in votes_all.congress_to_rollnumber_to_votes.items():
            for rollnumber, votes in rollnumber_to_rollvotes.items():
                rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
                vr = hr.CalculateVotes(votes, members, rc, options=options).calculate_votes()
                rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
                assert rc.yea_count == vr.yea_count, f"Voting: {vr}, Roll-call: {rc}"
                assert rc.nay_count == vr.nay_count, f"Voting: {vr}, Roll-call: {rc}"


def test_calculate_vote_results_fractional():

    for votes_csv, rollcalls_csv, members_csv, congress, yea1, nay1, yea2, nay2 in [
        (H117_VOTES_CSV, H117_ROLLCALLS_CSV, H117_MEMBERS_CSV, 117, 215.76760646980654, 211.74396112191627, 215.30891482085957, 212.01347793114823),
        (H116_VOTES_CSV, H116_ROLLCALLS_CSV, H116_MEMBERS_CSV, 116, 219.6140676795838, 210.2900659224949, 219.77532216780347, 210.2063091319445)
        ]:

        # Load data
        votes_all, rollcalls, members = hr.LoadVoteViewCsv(votes_csv=votes_csv, rollcalls_csv=rollcalls_csv, members_csv=members_csv).load_consistency()
        votes = votes_all.congress_to_rollnumber_to_votes[congress][1]
        rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][1]

        # Calculate vote results
        vr = hr.CalculateVotes(votes, members, rc).calculate_votes_fractional().vote_results
        assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(yea1)
        assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(nay1)

        options = hr.CalculateVotes.Options(
            use_num_votes_as_num_seats=True
            )
        vr = hr.CalculateVotes(votes, members, rc, options=options).calculate_votes_fractional().vote_results
        assert vr.castcode_to_count[hr.CastCode.YEA] == pytest.approx(yea2)
        assert vr.castcode_to_count[hr.CastCode.NAY] == pytest.approx(nay2)