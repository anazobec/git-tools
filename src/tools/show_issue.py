import configparser
import os
import requests

from typing import Any
from dataclasses import dataclass
from enum import Enum

from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

DEBUG = False


@dataclass
class GitProjectInfo:
    path: Path
    namespace: str  # path_with_namespace
    server_base: str
    api_token: str
    api_base: str
    url_to_repo: str


@dataclass
class GitLabProjectIssue:
    reference: int
    description: str
    title: str
    labels: list[str]


@dataclass
class GitLabProject:
    id: int
    issue: GitLabProjectIssue


class GitServiceType(Enum):
    GITLAB = "gitlab"
    GITHUB = "github"

    @classmethod
    def has_value(cls, value) -> bool:
        return value in cls._value2member_map_

    @classmethod
    def list_values(cls) -> list[Any]:
        return list(cls._value2member_map_.keys())


def generate_git_user_tokens_config(git_user_config_path):
    # TODO
    pass


def _find_git_project_root(cwd: Path) -> Path | None:
    if ".git" in os.listdir(cwd.absolute()):
        return cwd

    return _find_git_project_root(cwd=cwd.parent)


def _get_project_namespace(git_dir_path: Path) -> tuple[str, str, str, str]:
    git_config_path = git_dir_path / "config"

    git_config = configparser.ConfigParser()
    git_config.read(git_config_path)

    remote_url = git_config['remote "origin"']["url"]
    remote_url_parts = remote_url.split("/")
    project_namespace = "/".join(remote_url_parts[3:]).strip(".git")

    server_parts = remote_url_parts[2].replace("git@", "")
    server_base = server_parts.split(":")[0]
    api_base_url = f"https://{server_base}"

    return project_namespace, server_base, api_base_url, remote_url


def _get_git_api_token(git_user_config_path: Path, git_server_base: str) -> str:
    git_user_config = configparser.ConfigParser()
    try:
        git_user_config.read(git_user_config_path)
        return git_user_config[f"{git_server_base}"]["api_token"].strip('"')
    except KeyError:
        print(
            f'Error: Couldn\'t find an auth token. Config must have a section [{git_server_base}] with provided "token" propperty.'
        )
    except Exception:
        print(
            'Error: Something went wrong when looking for your git token. This script looks for your config in "$HOME/.config/git/.tokens"'
        )
    return "not-found"


def get_git_project_info() -> tuple[GitProjectInfo | None, int]:
    try:
        git_project_root = _find_git_project_root(cwd=Path.cwd())
        if git_project_root is None:
            print("Error: Couldn't find your git project root")
            return None, 1

        git_dir_path = git_project_root / ".git"
        project_namespace, git_server_base, api_base_url, url_to_repo = _get_project_namespace(
            git_dir_path=git_dir_path
        )

        git_api_token = _get_git_api_token(
            git_user_config_path=Path.home() / ".config" / "git" / ".tokens",
            git_server_base=git_server_base,
        )

        return GitProjectInfo(
            path=git_project_root,
            namespace=project_namespace,
            server_base=git_server_base,
            api_token=git_api_token,
            api_base=api_base_url,
            url_to_repo=url_to_repo,
        ), 0
    except RecursionError:
        print("Error: Folder not part of the git repo.")
        return None, 1


def get_gitlab_project_id(git_project_info: GitProjectInfo) -> tuple[int | None, int]:
    namespace_search = git_project_info.namespace.replace("/", "%2F")
    url = f"{git_project_info.api_base}/api/v4/projects/{namespace_search}"
    response = requests.get(
        url=url,
        headers={
            "Content-Type": "application/json",
            "PRIVATE-TOKEN": git_project_info.api_token,
        },
    )
    if response.status_code == 429:
        print("GitLab error: Rate limit reached, please wait before trying again.")
        return None, 2

    if response.status_code != 200:
        print(response)
        print("Error: Unable to fetch GitLab project's ID.")
        return None, 1

    response_json = response.json()
    project_id = response_json["id"]

    return project_id, 0


def get_gitlab_project_issue_by_reference(
    git_project_info: GitProjectInfo, project_id: int, issue_reference: int
) -> tuple[GitLabProject | None, int]:
    url = f"{git_project_info.api_base}/api/v4/projects/{project_id}/issues/{issue_reference}"
    response = requests.get(
        url=url,
        headers={
            "Content-Type": "application/json",
            "PRIVATE-TOKEN": git_project_info.api_token,
        },
    )
    if response.status_code == 429:
        print("GitLab error: Rate limit reached, please wait before trying again.")
        return None, 2

    if response.status_code != 200:
        print("Error: Unable to fetch the GitLab project issue by its reference")
        return None, 1

    response_json = response.json()
    return GitLabProject(
        id=project_id,
        issue=GitLabProjectIssue(
            reference=issue_reference,
            description=response_json["description"],
            title=response_json["title"],
            labels=response_json["labels"],
        ),
    ), 0


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

    git_project_info, exit_code = get_git_project_info()
    if exit_code != 0:
        return exit_code
    if git_project_info is None:
        print("Error: Couldn't get project info")
        return 1

    gitlab_project_id, exit_code = get_gitlab_project_id(git_project_info=git_project_info)
    if exit_code != 0:
        return exit_code
    if gitlab_project_id is None:
        print("Error: Couldn't get GitLab project ID")
        return 1

    gitlab_project, exit_code = get_gitlab_project_issue_by_reference(
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

    if is_raw_text:
        print(gitlab_project.issue.title, end="")
        print("\n")
        print(gitlab_project.issue.description, end="")
        print("\n")
        print("=========")
        print("\n")
        print(raw_labels)
        return 0

    no_wrap = True
    force_terminal = True

    console = Console(force_terminal=force_terminal)
    markdown_title = Markdown(f"# {gitlab_project.issue.title}")
    markdown_description = Markdown(gitlab_project.issue.description)
    console.print(markdown_title, no_wrap=no_wrap)
    console.print(markdown_description, no_wrap=no_wrap)
    console.print(Markdown("---"), no_wrap=no_wrap)

    markdown_labels = Markdown(raw_labels)
    console.print(markdown_labels, no_wrap=no_wrap)

    return 0
