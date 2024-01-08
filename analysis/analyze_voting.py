import utils
import houseofreps as hr
import argparse
import os
from typing import Optional


def download_data(year: Optional[str]):
    import wget
    from loguru import logger

    if year is None:
        year = "all"

    urls = [
        f"https://voteview.com/static/data/out/rollcalls/H{year}_rollcalls.csv",
        f"https://voteview.com/static/data/out/votes/H{year}_votes.csv",
        f"https://voteview.com/static/data/out/members/H{year}_members.csv"
        ]
    for url in urls:
        bname = url.split('/')[-1]
        if not os.path.exists(bname):
            logger.info(f"Downloading {url}")
            wget.download(url)
        else:
            logger.info(f"Skipping downloading file {bname} - already exists.")


def analyze(year: Optional[str]):
    if year is None:
        year = "all"
    
    votes_csv = f"H{year}_votes.csv"
    rollcalls_csv = f"H{year}_rollcalls.csv"
    members_csv = f"H{year}_members.csv"
    assert os.path.exists(votes_csv), f"File {votes_csv} does not exist - try running with --command download first."
    assert os.path.exists(rollcalls_csv), f"File {rollcalls_csv} does not exist - try running with --command download first."
    assert os.path.exists(members_csv), f"File {members_csv} does not exist - try running with --command download first."

    # Load data
    loader = hr.LoadVoteViewCsv(
        votes_csv=votes_csv, 
        rollcalls_csv=rollcalls_csv, 
        members_csv=members_csv
        )
    votes, rollcalls, members = loader.load_consistency()

    # Options for calculating the votes
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    # Analyze
    avr = utils.analyze_voting(votes, members, rollcalls, cv_options)
    utils.report_voting(avr, cv_options, votes, rollcalls, members)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Analyze voting results from CSV files from https://voteview.com/')
    parser.add_argument("--command", type=str, choices=['download', 'analyze', 'all'], required=False, help="Command to run.", default="all")
    parser.add_argument("--year", type=str, required=False, help="Year of congress, or 'all'.", default="117")
    args = parser.parse_args()

    if args.command in ['all', 'download']:
        download_data(args.year)
    
    if args.command in ['all', 'analyze']:
        analyze(args.year)