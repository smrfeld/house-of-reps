import houseofreps as hr
import argparse
from loguru import logger
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AnalyzeVotingResults:

    @dataclass
    class Roll:
        congress: int
        rollnumber: int

    roll_max_diff: Roll
    rolls_flipped_decisions: List[Roll]


def analyze_voting(
    votes: hr.VotesAll, 
    members: hr.Members, 
    rollcalls: hr.RollCallsAll,
    cv_options: hr.CalculateVotes.Options
    ) -> AnalyzeVotingResults:

    # Analyze all congresses
    rolls_flipped_decisions = []
    max_diff, roll_max_diff = 0.0, None
    no_rollnumbers_missing_members = 0
    for congress, rollnumber_to_rollvotes in votes.congress_to_rollnumber_to_rollvotes.items():
        for rollnumber, rv in rollnumber_to_rollvotes.items():
            try:
                # Calculate vote results
                cv = hr.CalculateVotes(
                    rv, members, rollcalls,
                    options=cv_options
                    )
                vr_actual = cv.calculate_votes()
                vr_frac = cv.calculate_votes_fractional().vote_results

                if vr_actual.majority_decision != vr_frac.majority_decision:
                    rolls_flipped_decisions.append(AnalyzeVotingResults.Roll(congress, rollnumber))
                    logger.info(f'Congress {congress} rollnumber {rollnumber} has a flip')

                # Compute max diff
                max_diff_0 = max([ abs(vr_actual.castcode_to_count[castcode] - vr_frac.castcode_to_count[castcode])  for castcode in vr_actual.castcode_to_count.keys() ])
                if max_diff_0 > max_diff:
                    max_diff = max_diff_0
                    roll_max_diff = AnalyzeVotingResults.Roll(congress, rollnumber)

            except hr.MissingMemberError as e:
                logger.warning(f'Congress {congress} rollnumber {rollnumber} has missing member data - skipping ({str(e)})')
                no_rollnumbers_missing_members += 1

    # Report missing members
    if no_rollnumbers_missing_members > 0:
        logger.warning(f'Number of rollnumbers with missing members: {no_rollnumbers_missing_members} / {votes.no_rollvotes}')

    assert roll_max_diff is not None
    return AnalyzeVotingResults(
        roll_max_diff=roll_max_diff,
        rolls_flipped_decisions=rolls_flipped_decisions
        )

def report_voting(
    avr: AnalyzeVotingResults,
    cv_options: hr.CalculateVotes.Options,
    votes: hr.VotesAll,
    rollcalls: hr.RollCallsAll
    ):

    # Report max vote change
    logger.info("====================================")
    logger.info(f'[Max diff]: Congress/rollnumber: {avr.roll_max_diff}')
    rv = votes.congress_to_rollnumber_to_rollvotes[avr.roll_max_diff.congress][avr.roll_max_diff.rollnumber]
    cv = hr.CalculateVotes(
        rv, members, rollcalls,
        options=cv_options 
        )
    vr_actual = cv.calculate_votes()
    vr_frac = cv.calculate_votes_fractional().vote_results
    logger.info(f"Actual vote results: {vr_actual}")
    logger.info(f"Fractional vote results: {vr_frac}")

    # Report flips
    for roll in avr.rolls_flipped_decisions:
        logger.info("====================================")
        rv = votes.congress_to_rollnumber_to_rollvotes[roll.congress][roll.rollnumber]
        cv = hr.CalculateVotes(
            rv, members, rollcalls,
            options=cv_options 
            )
        vr_actual = cv.calculate_votes()
        vr_frac = cv.calculate_votes_fractional().vote_results
        logger.info(f"[Flip decision]: Congress {roll.congress} rollnumber {roll.rollnumber}")
        logger.info(f"Actual vote results: {vr_actual}")
        logger.info(f"Fractional vote results: {vr_frac}")
        logger.info(f"Actual majority decision: {vr_actual.majority_decision}")
        logger.info(f"Fractional majority decision: {vr_frac.majority_decision}")

        # Look up rollcall
        if rollcalls is not None:
            rc = rollcalls.congress_to_rollnumber_to_rollcall[roll.congress][roll.rollnumber]
            logger.info(f"Rollcall: {rc}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Analyze voting results from CSV files from https://voteview.com/')
    parser.add_argument("--members-csv", type=str, required=True, help="CSV file with members. Must have columns: icpsr, state_abbrev.")
    parser.add_argument("--votes-csv", type=str, required=True, help="CSV file with rollvotes. Must have columns: congress, rollnumber, icpsr, cast_code.")
    parser.add_argument("--rollcalls-csv", type=str, required=True, help="CSV file with rollcalls.")
    args = parser.parse_args()

    # Load data
    loader = hr.LoadVoteViewCsv(
        votes_csv=args.votes_csv, 
        rollcalls_csv=args.rollcalls_csv, 
        members_csv=args.members_csv
        )
    votes, rollcalls, members = loader.load_consistency()

    # Options
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    # Analyze
    avr = analyze_voting(votes, members, rollcalls, cv_options)
    report_voting(avr, cv_options, votes, rollcalls)