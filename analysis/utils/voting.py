import houseofreps as hr
from loguru import logger
from dataclasses import dataclass
from typing import List, Optional
from tqdm import tqdm


@dataclass
class AnalyzeVotingResults:
    """Results from analyzing voting results.
    """    

    @dataclass
    class Roll:
        congress: int
        "Congress number"

        rollnumber: int
        "Roll number"

    @dataclass
    class RollResults:
        roll: "AnalyzeVotingResults.Roll"
        "Roll"

        vr_actual: hr.VoteResults
        "Actual vote results"

        vr_frac: hr.VoteResults
        "Fractional vote results"

        rollcall: hr.RollCall
        "Rollcall"

    roll_max_diff: RollResults
    "Roll with the maximum difference between actual and fractional votes"

    rolls_flipped_decisions: List[RollResults]
    "Rolls where the majority decision was flipped"


def analyze_voting(
    votes: hr.VotesAll, 
    members: hr.Members, 
    rollcalls: hr.RollCallsAll,
    cv_options: hr.CalculateVotes.Options
    ) -> AnalyzeVotingResults:

    assert votes.no_rollcalls > 0, "No rollcalls for voting analysis"

    # Analyze all congresses
    rolls_flipped_decisions = []
    max_diff, roll_max_diff = 0.0, None
    for congress, rollnumber_to_rollvotes in tqdm(votes.congress_to_rollnumber_to_votes.items(), desc="Analyzing congresses"):
        for rollnumber, rv in rollnumber_to_rollvotes.items():
            rc = rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]

            # Calculate vote results
            cv = hr.CalculateVotes(
                rv, members, rc,
                options=cv_options
                )
            vr_actual = cv.calculate_votes()
            vr_frac = cv.calculate_votes_fractional().vote_results

            if vr_actual.majority_decision != vr_frac.majority_decision:
                roll_result = AnalyzeVotingResults.RollResults(
                    roll=AnalyzeVotingResults.Roll(congress, rollnumber),
                    vr_actual=vr_actual,
                    vr_frac=vr_frac,
                    rollcall=rc
                    )
                rolls_flipped_decisions.append(roll_result)
                logger.info(f'Congress {congress} rollnumber {rollnumber} has a flipped decision: {vr_actual.majority_decision} -> {vr_frac.majority_decision}')

            # Compute max diff
            max_diff_0 = max([ abs(vr_actual.castcode_to_count[castcode] - vr_frac.castcode_to_count[castcode])  for castcode in vr_actual.castcode_to_count.keys() ])
            if max_diff_0 > max_diff:
                max_diff = max_diff_0
                roll_max_diff = AnalyzeVotingResults.RollResults(
                    roll=AnalyzeVotingResults.Roll(congress, rollnumber),
                    vr_actual=vr_actual,
                    vr_frac=vr_frac,
                    rollcall=rc
                    )

    assert roll_max_diff is not None
    return AnalyzeVotingResults(
        roll_max_diff=roll_max_diff,
        rolls_flipped_decisions=rolls_flipped_decisions
        )


def report_voting(
    avr: AnalyzeVotingResults
    ):

    # Report max vote change
    logger.info("====================================")
    logger.info("[Max diff]")
    report_voting_roll(avr.roll_max_diff)

    # Report flips
    for roll in avr.rolls_flipped_decisions:
        logger.info("====================================")
        logger.info("[Flip decision]")
        report_voting_roll(roll)


def report_voting_roll(
    rr: AnalyzeVotingResults.RollResults,
    ):
    vr_actual = rr.vr_actual
    vr_frac = rr.vr_frac
    logger.info(f"Congress {rr.roll.congress} rollnumber {rr.roll.rollnumber}")
    logger.info(f"Actual vote results: Yea: {vr_actual.castcode_to_count[hr.CastCode.YEA]}, Nay: {vr_actual.castcode_to_count[hr.CastCode.NAY]}")
    logger.info(f"Fractional vote results: Yea: {vr_frac.castcode_to_count[hr.CastCode.YEA]:.4f}, Nay: {vr_frac.castcode_to_count[hr.CastCode.NAY]:.4f}")
    logger.info(f"Actual majority decision: {vr_actual.majority_decision}")
    logger.info(f"Fractional majority decision: {vr_frac.majority_decision}")

    # Look up rollcall
    rc = rr.rollcall
    logger.info(f"Rollcall: [Yea: {rc.yea_count}] [Nay: {rc.nay_count}] [Date: {rc.date}] [Bill number: {rc.bill_number}] [Vote result: {rc.vote_result}] [Vote questions: {rc.vote_question}] [Vote desc: {rc.vote_desc}]")