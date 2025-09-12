import sys
import argparse

from src.tools.show_issue import show_issue
from src.utils.services import GitServiceType


if __name__ == "__main__":
    available_git_services = ", ".join(GitServiceType.list_values())
    parser = argparse.ArgumentParser(
        prog="git-tools",
        usage="%(prog)s [--help|options]",
        description="Useful tools to use with your git project",
    )

    subparsers = parser.add_subparsers(help="--help", required=True)

    parser_show_issue = subparsers.add_parser(
        "show-issue",
        help="Show git issue description in your terminal",
        description="Show git issue description in your terminal",
    )
    parser_show_issue.add_argument(
        "-t",
        "--type",
        type=str,
        default="gitlab",
        choices=GitServiceType.list_values(),
        help=f"Git service type. Available types are {available_git_services} (default: gitlab)",
        required=False,
    )
    parser_show_issue.add_argument(
        "-r",
        "--raw",
        action="store_true",
        help="Print issue description in raw (non-rendered) markdown if set",
        required=False,
    )
    parser_show_issue.add_argument(
        "issue_reference",
        type=int,
        help="Reference number of the issue to get description of",
    )
    parser_show_issue.set_defaults(func=show_issue)

    args = parser.parse_args()
    args.func(args)

    # if len(sys.argv) == 1 or sys.argv[1] in ("--help", "-h"):
    #     print_help()
    #     sys.exit(0)
    #
    # if len(sys.argv) >= 2 and sys.argv[1] == "show-issue":
    #     exit_code = show_issue(argv=sys.argv[1:])
    #     sys.exit(exit_code)

    sys.exit(0)
