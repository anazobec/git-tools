import requests

from typing import Any
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


from src.utils.git import GitProjectInfo
from src.utils.errors import (
    unauthorized_service_access,
    service_rate_limit_reached,
    general_service_error,
    project_with_namespace_not_found,
)


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


class GitService(ABC):
    def __init__(self, type: GitServiceType = GitServiceType.GITLAB):
        self.type = type

    @staticmethod
    def _handle_request_errors(git_project_info: GitProjectInfo, service_type: str, response_status_code: int) -> int:
        if response_status_code == 429:
            return service_rate_limit_reached(service_type=service_type)

        if response_status_code == 401:
            return unauthorized_service_access(service_type=service_type)

        if response_status_code == 404:
            return project_with_namespace_not_found(
                service_type=service_type,
                namespace=git_project_info.namespace,
            )

        if response_status_code != 200:
            return general_service_error(service_type=service_type)

        return 0

    @classmethod
    @abstractmethod
    def fetch_project_id(
        cls,
        git_project_info: GitProjectInfo,
    ) -> tuple[int | None, int]:
        pass

    @classmethod
    @abstractmethod
    def fetch_project_issue_by_reference(
        cls,
        git_project_info: GitProjectInfo,
        project_id: int,
        issue_reference: int,
    ) -> tuple[GitLabProject | None, int]:
        pass


class GitLabService(GitService):
    @classmethod
    def fetch_project_id(
        cls,
        git_project_info: GitProjectInfo,
    ) -> tuple[int | None, int]:
        namespace_search = git_project_info.namespace.replace("/", "%2F")
        url = f"{git_project_info.api_base}/api/v4/projects/{namespace_search}"
        response = requests.get(
            url=url,
            headers={
                "Content-Type": "application/json",
                "PRIVATE-TOKEN": git_project_info.api_token,
            },
        )
        exit_code = cls._handle_request_errors(
            git_project_info=git_project_info, service_type="GitLab", response_status_code=response.status_code
        )
        if exit_code > 0:
            return None, exit_code

        response_json = response.json()
        project_id = response_json["id"]

        return project_id, 0

    @classmethod
    def fetch_project_issue_by_reference(
        cls,
        git_project_info: GitProjectInfo,
        project_id: int,
        issue_reference: int,
    ) -> tuple[GitLabProject | None, int]:
        url = f"{git_project_info.api_base}/api/v4/projects/{project_id}/issues/{issue_reference}"
        response = requests.get(
            url=url,
            headers={
                "Content-Type": "application/json",
                "PRIVATE-TOKEN": git_project_info.api_token,
            },
        )
        exit_code = cls._handle_request_errors(
            git_project_info=git_project_info, service_type="GitLab", response_status_code=response.status_code
        )
        if exit_code > 0:
            return None, exit_code

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
