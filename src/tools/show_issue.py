from rich.console import Console
from rich.markdown import Markdown

from src.utils.git import GitConfig
from src.utils.services import GitServiceType, GitLabService

DEBUG = False


def show_issue(args) -> int:
    git_service_type = args.type
    is_raw_text = args.raw
    issue_reference = args.issue_reference

    if git_service_type == GitServiceType.GITHUB.value:
        print("Not yet implemented. Use other available git services.")
        return 0

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
        raw_labels += f"**[{label}]** "

    # Print raw markdown
    if is_raw_text:
        print(f"# {gitlab_project.issue.title}", end="")
        print("\n")
        print(gitlab_project.issue.description, end="\n")
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
