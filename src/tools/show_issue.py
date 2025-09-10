from rich.console import Console
from rich.markdown import Markdown

from src.utils.git import GitConfig
from src.utils.services import GitServiceType, GitLabService

DEBUG = False


def print_help(available_git_services: str, default_git_service_type: str):
    print("Show Git issue description in your terminal", end="")
    print("\n")
    print("USAGE:")
    print("  git-tools show-issue [--help|-h|--type|-t] <issue_number> [--raw|-r]", end="")
    print("\n")
    print("OPTIONS:")
    print("  --help, -h\t Show this help.")
    print("  --raw,  -r\t Print issue description without markdown rendering.")
    print(
        f"  --type, -t\t Choose git service type. Available types are: {available_git_services}; Default is: {default_git_service_type}"
    )


def show_issue(argv: list) -> int:
    git_service_type = "gitlab"
    available_git_services = ", ".join(GitServiceType.list_values())

    if len(argv) == 1:
        print("Error: Invalid use of the tool. Use options --help or -h to see usage")
        return 1

    if len(argv) >= 2 and argv[1] in ("--help", "-h"):
        print_help(available_git_services=available_git_services, default_git_service_type=git_service_type)
        return 0

    if len(argv) == 4 and argv[1] in ("--type", "-t"):
        git_service_type = argv[2]
        if not GitServiceType.has_value(git_service_type):
            print(f"Error: Git service {git_service_type} not supported.")
            print(f"Supported types are: {available_git_services}")
            return 1
        if git_service_type == GitServiceType.GITHUB.value:
            print("Not yet implemented. Use other available git services.")
            return 0
        issue_reference = int(argv[3])

    if len(argv) >= 2:
        try:
            issue_reference = int(argv[1])
        except ValueError as ve:
            print(f"Error: Issue reference must be a number: {ve}")
            return 1

    is_raw_text = "--raw" in argv or "-r" in argv

    git_project_info, exit_code = GitConfig.get_git_project_info()
    if exit_code != 0:
        return exit_code
    if git_project_info is None:
        print("Error: Couldn't get project info")
        return 1

    gitlab_project_id, exit_code = GitLabService.fetch_project_id(git_project_info=git_project_info)
    if exit_code != 0:
        return exit_code
    if gitlab_project_id is None:
        print("Error: Couldn't get GitLab project ID")
        return 1

    gitlab_project, exit_code = GitLabService.fetch_project_issue_by_reference(
        git_project_info=git_project_info,
        project_id=gitlab_project_id,
        issue_reference=issue_reference,
    )
    if exit_code != 0:
        return exit_code
    if gitlab_project is None:
        print("Error: Couldn't get your GitLab project")
        return 1

    raw_labels = "Labels: "
    for label in gitlab_project.issue.labels:
        raw_labels += f"**_{label}_** "

    # Print raw markdown
    if is_raw_text:
        print(f"# {gitlab_project.issue.title}", end="")
        print("\n")
        print(gitlab_project.issue.description, end="")
        print("---")
        print(raw_labels)
        return 0

    # Print rendered markdown
    force_terminal = True
    crop = False

    console = Console(force_terminal=force_terminal)
    markdown_title = Markdown(f"# {gitlab_project.issue.title}")
    markdown_description = Markdown(gitlab_project.issue.description)
    markdown_labels = Markdown(raw_labels)

    console.print(markdown_title, crop=crop)
    console.print(markdown_description, crop=crop)
    console.print(Markdown("---"), crop=crop)
    console.print(markdown_labels, crop=crop)

    return 0
