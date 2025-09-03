import sys

from src.tools.show_issue import show_issue


def print_help() -> None:
    print("Usefull tools to use with your git project", end="")
    print("\n")
    print("USAGE:")
    print("  git-tools [--help|-h|TOOLS]")
    print("  git-tools <tool> [--help|-h]", end="")
    print("\n")
    print("TOOLS:")
    print("  show-issue\t Show git issue description in your terminal")


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit(0)

    if len(sys.argv) >= 2 and sys.argv[1] == "show-issue":
        exit_code = show_issue(argv=sys.argv[1:])
        sys.exit(exit_code)

    sys.exit(0)
