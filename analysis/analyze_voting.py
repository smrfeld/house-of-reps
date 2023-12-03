import utils
import houseofreps as hr
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Analyze voting results from CSV files from https://voteview.com/')
    parser.add_argument("--members-csv", type=str, required=True, help="CSV file with members. Must have columns: icpsr, state_abbrev.")
    parser.add_argument("--votes-csv", type=str, required=True, help="CSV file with rollvotes. Must have columns: congress, rollnumber, icpsr, cast_code.")
    parser.add_argument("--rollcalls-csv", type=str, required=True, help="CSV file with rollcalls.")
    parser.add_argument("--show", action="store_true", help="Show plot")
    args = parser.parse_args()

    # Load data
    loader = hr.LoadVoteViewCsv(
        votes_csv=args.votes_csv, 
        rollcalls_csv=args.rollcalls_csv, 
        members_csv=args.members_csv
        )
    votes, rollcalls, members = loader.load_consistency()

    # Options for calculating the votes
    cv_options = hr.CalculateVotes.Options(
        use_num_votes_as_num_seats=False,
        skip_castcodes=[hr.CastCode.NOT_MEMBER, hr.CastCode.NOT_VOTING]
        )

    # Analyze
    avr = utils.analyze_voting(votes, members, rollcalls, cv_options)

    # Report
    utils.report_voting(avr)

    # Plot
    utils.plot_voting_results(avr, show=args.show)