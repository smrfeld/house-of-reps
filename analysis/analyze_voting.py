import utils
import houseofreps as hr
import argparse
from loguru import logger


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--members-csv", type=str, required=True)
    parser.add_argument("--votes-csv", type=str, required=True)
    parser.add_argument("--year", type=str, required=True, choices=[ yr.value for yr in hr.Year ])
    args = parser.parse_args()

    # Load data
    rv_all = hr.LoadVoteViewCsv().load_rollvotes_all(args.votes_csv)
    members = hr.LoadVoteViewCsv().load_members(args.members_csv)

    # Analyze all congresses
    max_diff, congress_max, rollnumber_max = 0.0, None, None
    for congress, rollnumber_to_rollvotes in rv_all.congress_to_rollnumber_to_rollvotes.items():
        for rollnumber, rv in rollnumber_to_rollvotes.items():
            try:
                # Calculate vote results
                cv = hr.CalculateVotes(
                    rv, members, 
                    census_year=hr.Year(args.year), 
                    use_num_votes_as_num_seats=False,
                    skip_missing_icpsr_in_members=True,
                    skip_dc=True
                    )
                vr_actual = cv.calculate_votes()
                vr_frac = cv.calculate_votes_fractional().vote_results

                # Compute max diff
                max_diff_0 = max([ abs(vr_actual.castcode_to_count[castcode] - vr_frac.castcode_to_count[castcode])  for castcode in vr_actual.castcode_to_count.keys() ])
                if max_diff_0 > max_diff:
                    max_diff = max_diff_0
                    congress_max = congress
                    rollnumber_max = rollnumber

            except hr.MissingMemberError as e:
                logger.warning(f'Congress {congress} rollnumber {rollnumber} has missing member data - skipping ({str(e)})')

    assert congress_max is not None and rollnumber_max is not None
    print(f'Max diff: {max_diff}')
    print(f'Congress: {congress_max}')
    print(f'Rollnumber: {rollnumber_max}')
    rv = rv_all.congress_to_rollnumber_to_rollvotes[congress_max][rollnumber_max]
    cv = hr.CalculateVotes(
        rv, members, 
        census_year=hr.Year(args.year), 
        use_num_votes_as_num_seats=False,
        skip_missing_icpsr_in_members=True,
        skip_dc=True
        )
    vr_actual = cv.calculate_votes()
    vr_frac = cv.calculate_votes_fractional().vote_results
    print(vr_actual)
    print(vr_frac)