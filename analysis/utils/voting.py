import houseofreps as hr
from loguru import logger
from dataclasses import dataclass
from typing import List, Optional, Dict
import plotly.graph_objects as go
import os


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

    roll_max_diff: Roll
    "Roll with the maximum difference between actual and fractional votes"

    rolls_flipped_decisions: List[Roll]
    "Rolls where the majority decision was flipped"


@dataclass
class VoteData:
    votes: hr.VotesAll
    rollcalls: hr.RollCallsAll
    members: hr.Members


def analyze_voting_across_congresses(
    congress_to_data: Dict[int,VoteData],
    cv_options: hr.CalculateVotes.Options,
    show: bool = False
    ):
    logger.debug(f'Analyzing voting results...')

    # Analyze all congresses
    congresses, diffs = [], []
    for congress, data in congress_to_data.items():
        logger.info(f'Analyzing congress {congress}...')
        rollnumber_to_rollvotes = data.votes.congress_to_rollnumber_to_votes[congress]
        for rollnumber, rv in rollnumber_to_rollvotes.items():
            rc = data.rollcalls.congress_to_rollnumber_to_rollcall[congress][rollnumber]
            # Calculate vote results
            cv = hr.CalculateVotes(
                rv, data.members, rc,
                options=cv_options
                )
            vr_actual = cv.calculate_votes()
            vr_frac = cv.calculate_votes_fractional().vote_results

            # Compute diff
            diff = max([ abs(vr_actual.castcode_to_count[castcode] - vr_frac.castcode_to_count[castcode]) for castcode in vr_actual.castcode_to_count.keys() ])
            diffs.append(diff)
            congresses.append(congress)
    
    # Plot
    fig = go.Figure()
    fig.add_trace(go.Box(
        y=diffs,
        x=congresses
        ))
    fig.update_layout(
        title="Difference between actual and fractional votes across rollcalls",
        xaxis_title="Congress",
        yaxis_title="Number of votes difference",
        width=800,
        height=600
        )
    os.makedirs("plots", exist_ok=True)
    fig.write_image("plots/diffs.png")
    fig.show()
    logger.info(f'Wrote to plots/diffs.png')


def analyze_voting(
    votes: hr.VotesAll, 
    members: hr.Members, 
    rollcalls: hr.RollCallsAll,
    cv_options: hr.CalculateVotes.Options
    ) -> AnalyzeVotingResults:
    logger.debug(f'Analyzing voting results...')

    # Analyze all congresses
    rolls_flipped_decisions = []
    max_diff, roll_max_diff = 0.0, None
    no_rollnumbers_missing_members = 0
    for congress, rollnumber_to_rollvotes in votes.congress_to_rollnumber_to_votes.items():
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
                rolls_flipped_decisions.append(AnalyzeVotingResults.Roll(congress, rollnumber))
                logger.info(f'Congress {congress} rollnumber {rollnumber} has a flip')

            # Compute max diff
            max_diff_0 = max([ abs(vr_actual.castcode_to_count[castcode] - vr_frac.castcode_to_count[castcode])  for castcode in vr_actual.castcode_to_count.keys() ])
            if max_diff_0 > max_diff:
                max_diff = max_diff_0
                roll_max_diff = AnalyzeVotingResults.Roll(congress, rollnumber)

    # Report missing members
    if no_rollnumbers_missing_members > 0:
        logger.warning(f'Number of rollnumbers with missing members: {no_rollnumbers_missing_members} / {votes.no_rollcalls}')

    assert roll_max_diff is not None
    return AnalyzeVotingResults(
        roll_max_diff=roll_max_diff,
        rolls_flipped_decisions=rolls_flipped_decisions
        )


def report_voting(
    avr: AnalyzeVotingResults,
    cv_options: hr.CalculateVotes.Options,
    votes: hr.VotesAll,
    rollcalls: hr.RollCallsAll,
    members: hr.Members
    ):
    logger.info("Voting analysis results:")

    # Report max vote change
    logger.info("====================================")
    logger.info("Largest changes that would have occured by switching to fractional voting:")
    logger.info("====================================")
    report_voting_roll(votes, rollcalls, members, avr.roll_max_diff, cv_options)

    # Report flips
    if len(avr.rolls_flipped_decisions) > 0:
        logger.info("====================================")
        logger.info("Flipped decisions that would have occured by switching to fractional voting:")
        logger.info("====================================")

        for roll in avr.rolls_flipped_decisions:            
            report_voting_roll(votes, rollcalls, members, roll, cv_options)
            logger.info("============")
    else:
        logger.info("====================================")
        logger.info("No decisions would have been flipped by switching to fractional voting.")
        logger.info("====================================")


def report_voting_roll(
    votes: hr.VotesAll,
    rollcalls: hr.RollCallsAll, 
    members: hr.Members,
    roll: AnalyzeVotingResults.Roll,
    cv_options: hr.CalculateVotes.Options
    ):
    rv = votes.congress_to_rollnumber_to_votes[roll.congress][roll.rollnumber]
    rc = rollcalls.congress_to_rollnumber_to_rollcall[roll.congress][roll.rollnumber]
    cv = hr.CalculateVotes(
        rv, members, rc,
        options=cv_options 
        )
    vr_actual = cv.calculate_votes()
    vr_frac = cv.calculate_votes_fractional().vote_results
    logger.info(f"Congress {roll.congress} rollnumber {roll.rollnumber}")
    logger.info(f"Actual vote results: Yea: {vr_actual.castcode_to_count[hr.CastCode.YEA]}, Nay: {vr_actual.castcode_to_count[hr.CastCode.NAY]}")
    logger.info(f"Fractional vote results: Yea: {vr_frac.castcode_to_count[hr.CastCode.YEA]:.4f}, Nay: {vr_frac.castcode_to_count[hr.CastCode.NAY]:.4f}")
    perc_diff_yea = 100*(vr_actual.castcode_to_count[hr.CastCode.YEA] - vr_frac.castcode_to_count[hr.CastCode.YEA]) / vr_actual.castcode_to_count[hr.CastCode.YEA]
    perc_diff_nay = 100*(vr_actual.castcode_to_count[hr.CastCode.NAY] - vr_frac.castcode_to_count[hr.CastCode.NAY]) / vr_actual.castcode_to_count[hr.CastCode.NAY]
    logger.info(f"Percentage difference: Yea: {perc_diff_yea:.1f}, Nay: {perc_diff_nay:.1f}")
    logger.info(f"Actual majority decision: {vr_actual.majority_decision}")
    logger.info(f"Fractional majority decision: {vr_frac.majority_decision}")

    # Look up rollcall
    if rollcalls is not None:
        rc = rollcalls.congress_to_rollnumber_to_rollcall[roll.congress][roll.rollnumber]
        logger.info(f"Rollcall: [Yea: {rc.yea_count}] [Nay: {rc.nay_count}] [Date: {rc.date}] [Bill number: {rc.bill_number}] [Vote result: {rc.vote_result}] [Vote questions: {rc.vote_question}] [Vote desc: {rc.vote_desc}]")