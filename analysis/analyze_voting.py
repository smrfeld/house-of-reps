import utils
import houseofreps as hr
import argparse
from loguru import logger
from dataclasses import dataclass
from typing import List


@dataclass
class AnalyzeVotingResults:

    @dataclass
    class Roll:
        congress: int
        rollnumber: int

    roll_max_diff: Roll
    rolls_flipped_decisions: List[Roll]


def analyze_voting(
    year: hr.Year, 
    rv_all: hr.RollVotesAll, 
    members: hr.Members, 
    cv_options: hr.CalculateVotes.Options
    ) -> AnalyzeVotingResults:

    # Analyze all congresses
    rolls_flipped_decisions = []
    max_diff, roll_max_diff = 0.0, None
    no_rollnumbers_missing_members = 0
    for congress, rollnumber_to_rollvotes in rv_all.congress_to_rollnumber_to_rollvotes.items():
        for rollnumber, rv in rollnumber_to_rollvotes.items():
            try:
                # Calculate vote results
                cv = hr.CalculateVotes(
                    rv, members, 
                    census_year=year, 
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
        logger.warning(f'Number of rollnumbers with missing members: {no_rollnumbers_missing_members} / {rv_all.no_rollvotes}')

    assert roll_max_diff is not None
    return AnalyzeVotingResults(
        roll_max_diff=roll_max_diff,
        rolls_flipped_decisions=rolls_flipped_decisions
        )

def report_voting(
    avr: AnalyzeVotingResults,
    cv_options: hr.CalculateVotes.Options
    ):

    # Report max vote change
    logger.info("====================================")
    logger.info(f'Max diff: Congress/rollnumber: {avr.roll_max_diff}')
    rv = rv_all.congress_to_rollnumber_to_rollvotes[avr.roll_max_diff.congress][avr.roll_max_diff.rollnumber]
    cv = hr.CalculateVotes(
        rv, members, 
        census_year=year,
        options=cv_options 
        )
    vr_actual = cv.calculate_votes()
    vr_frac = cv.calculate_votes_fractional().vote_results
    logger.info(f"Actual vote results: {vr_actual}")
    logger.info(f"Fractional vote results: {vr_frac}")

    # Report flips
    for roll in avr.rolls_flipped_decisions:
        logger.info("====================================")
        rv = rv_all.congress_to_rollnumber_to_rollvotes[roll.congress][roll.rollnumber]
        cv = hr.CalculateVotes(
            rv, members, 
            census_year=year,
            options=cv_options 
            )
        vr_actual = cv.calculate_votes()
        vr_frac = cv.calculate_votes_fractional().vote_results
        logger.info(f"Flip decision: Congress {roll.congress} rollnumber {roll.rollnumber}")
        logger.info(f"Actual vote results: {vr_actual}")
        logger.info(f"Fractional vote results: {vr_frac}")
        logger.info(f"Actual majority decision: {vr_actual.majority_decision}")
        logger.info(f"Fractional majority decision: {vr_frac.majority_decision}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--members-csv", type=str, required=True)
    parser.add_argument("--votes-csv", type=str, required=True)
    parser.add_argument("--year", type=str, required=True, choices=[ yr.value for yr in hr.Year ])
    args = parser.parse_args()

    # Load data
    rv_all = hr.LoadVoteViewCsv().load_rollvotes_all(args.votes_csv)
    members = hr.LoadVoteViewCsv().load_members(args.members_csv)
    year = hr.Year(args.year)

    # Options
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_missing_icpsr_in_members=True,
        skip_dc=True,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    # Analyze
    avr = analyze_voting(year, rv_all, members, cv_options)
    report_voting(avr, cv_options)