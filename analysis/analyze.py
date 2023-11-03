import utils
import houseofreps as hr
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=["rpr", "rpr-frac", "pop-rankings", "rankings-fracs", "shift-pop"])
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.command == "rpr":

        for year in hr.Year:
            utils.plot_residents_per_rep(year, args.show)

    elif args.command == "rpr-frac":
        utils.plot_residents_per_rep_frac(args.show)
    
    elif args.command == "pop-rankings":
        for year in hr.Year:
            utils.plot_state_pop_rankings(year, args.show)

    elif args.command == "rankings-fracs":
        #for year in hr.Year:
        #    utils.plot_rankings_fracs_for_year(year, args.show)
        #utils.plot_rankings_fracs_ave(args.show)
        utils.plot_rankings_fracs_heat(args.show)

    elif args.command == "shift-pop":
        for year in hr.Year:
            utils.plot_shift_pop(year, args.show, report_all=args.verbose)

    else:
        raise ValueError(f"Unknown command: {args.command}")
    