import utils
import houseofreps as hr
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("command", type=str, choices=["rpr", "rpr-frac", "pop-rankings", "rankings-fracs", "shift-pop", "all"], help="Command to run. 'all' runs all commands. 'rpr' plots residents per rep. 'rpr-frac' plots residents per rep as a fraction. 'pop-rankings' plots state population rankings. 'rankings-fracs' plots state population rankings as a fraction. 'shift-pop' plots population shifts.")
    parser.add_argument("--show", action="store_true", help="Show plots.")
    parser.add_argument("--verbose", action="store_true", help="Verbose mode.")
    args = parser.parse_args()

    if args.command in ["all","rpr"]:
        for year in hr.Year:
            utils.plot_residents_per_rep(year, args.show)

    if args.command in ["all","rpr-frac"]:
        utils.plot_residents_per_rep_frac(args.show)
    
    if args.command in ["all","pop-rankings"]:
        for year in hr.Year:
            utils.plot_state_pop_rankings(year, args.show)

    if args.command in ["all","rankings-fracs"]:
        for year in hr.Year:
            utils.plot_rankings_fracs_for_year(year, args.show)
        utils.plot_rankings_fracs_ave(args.show)
        utils.plot_rankings_fracs_heat(args.show)

    if args.command in ["all","shift-pop"]:
        for year in hr.Year:
            utils.plot_shift_pop(year, args.show, report_all=args.verbose)