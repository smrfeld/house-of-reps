import utils
import houseofreps as hr
import argparse
import os
from typing import Optional
from loguru import logger


def download_data(congress: Optional[str]):
    """Download data from https://voteview.com/ and save to CSV files.
    
    Args:
        congress (Optional[str]): Congress number, or 'all'.
    """
    import wget
    from loguru import logger

    if congress is None:
        congress = "all"

    urls = [
        f"https://voteview.com/static/data/out/rollcalls/H{congress}_rollcalls.csv",
        f"https://voteview.com/static/data/out/votes/H{congress}_votes.csv",
        f"https://voteview.com/static/data/out/members/H{congress}_members.csv"
        ]
    for url in urls:
        bname = url.split('/')[-1]
        if not os.path.exists(bname):
            logger.info(f"Downloading {url}")
            wget.download(url)
        else:
            logger.info(f"Skipping downloading file {bname} - already exists.")


def make_loader(congress: Optional[str]) -> hr.LoadVoteViewCsv:
    """Make a loader for loading data from CSV files.

    Args:
        congress (Optional[str]): Congress number, or 'all'.

    Returns:
        hr.LoadVoteViewCsv: Loader for loading data from CSV files.
    """
    if congress is None:
        congress = "all"
    
    votes_csv = f"H{congress}_votes.csv"
    rollcalls_csv = f"H{congress}_rollcalls.csv"
    members_csv = f"H{congress}_members.csv"
    assert os.path.exists(votes_csv), f"File {votes_csv} does not exist - try running with --command download first."
    assert os.path.exists(rollcalls_csv), f"File {rollcalls_csv} does not exist - try running with --command download first."
    assert os.path.exists(members_csv), f"File {members_csv} does not exist - try running with --command download first."

    return hr.LoadVoteViewCsv(
        votes_csv=votes_csv, 
        rollcalls_csv=rollcalls_csv, 
        members_csv=members_csv
        )


def analyze(congress: Optional[str]):
    """Analyze voting results.

    Args:
        congress (Optional[str]): Congress number, or 'all'.
    """

    # Load data
    loader = make_loader(congress)
    votes, rollcalls, members = loader.load_consistency()

    # Options for calculating the votes
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    # Analyze
    avr = utils.analyze_voting(votes, members, rollcalls, cv_options)
    utils.report_voting(avr, cv_options, votes, rollcalls, members)


def analyze_voting_across_congresses(show: bool = False):
    """Analyze voting results across congresses.

    Args:
        show (bool, optional): Show plots. Defaults to False.
    """

    # Options for calculating the votes
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    congress_to_data = {}
    for congress_int in range(90,118+1):
        if congress_int in [103,110,111]:
            logger.warning(f'Skipping congress {congress_int} - no data available.')
            continue
        logger.info(f'Loading data for congress {congress_int}...')

        congress = "%03d" % congress_int
        download_data(congress)
        loader = make_loader(congress)
        votes, rollcalls, members = loader.load_consistency()

        data = utils.VoteData(
            votes=votes,
            rollcalls=rollcalls,
            members=members
            )
        congress_to_data[congress_int] = data
    utils.analyze_voting_across_congresses(
        congress_to_data=congress_to_data,
        cv_options=cv_options,
        show=show
        )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Analyze voting results from CSV files from https://voteview.com/')
    parser.add_argument("--command", type=str, choices=['download', 'analyze', 'analyze-batch'], required=False, help="Command to run.", default="all")
    parser.add_argument("--congress", type=str, required=False, nargs="+", help="Year of congress, or 'all', or several years.", default="117")
    parser.add_argument("--show", action="store_true", help="Show plots.")
    args = parser.parse_args()

    if args.command == 'analyze-batch':
        analyze_voting_across_congresses(args.show)
    else:
            
        for congress in args.congress:
            if args.command in ['download']:
                download_data(congress)

            if args.command in ['analyze']:
                analyze(congress)