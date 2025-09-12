import configparser
import os
import re

from dataclasses import dataclass

from pathlib import Path


@dataclass
class GitProjectInfo:
    path: Path
    namespace: str  # path_with_namespace
    server_base: str
    api_token: str
    api_base: str
    url_to_repo: str


class GitConfig:
    @classmethod
    def find_git_project_root(cls, cwd: Path) -> Path | None:
        if ".git" in os.listdir(cwd.absolute()):
            return cwd

        return cls.find_git_project_root(cwd=cwd.parent)

    @classmethod
    def get_project_namespace(cls, git_dir_path: Path) -> tuple[str, str, str, str]:
        # Get git config
        git_config_path = git_dir_path / "config"

        git_config = configparser.ConfigParser()
        git_config.read(git_config_path)

        # Parse data from config
        remote_url = git_config['remote "origin"']["url"]
        is_net_url = (
            remote_url.startswith("ssh://") or remote_url.startswith("http://") or remote_url.startswith("https://")
        )
        if is_net_url:
            remote_url_parts = remote_url.split("/")

            project_namespace = "/".join(remote_url_parts[3:]).replace(".git", "")
            server_parts = remote_url_parts[2].replace("git@", "")
            server_base = server_parts.split(":")[0]  # port is not needed
            api_base_url = f"https://{server_base}"

            return project_namespace, server_base, api_base_url, remote_url

        # git@<service>.com:[<port>/<namespace_path>.git|<namespace_path>.git]
        remote_url_parts = remote_url.split(":")
        match = re.search(r"^[0-9]+/", remote_url_parts[1]) if len(remote_url_parts) > 1 else None
        has_port = match is not None
        has_separator = len(remote_url_parts) > 1

        if has_separator:
            # [git@gitlab.com, 1234/something/something.git]
            if has_port:
                assert match is not None
                match_start, match_end = match.span()
                matched_string = remote_url_parts[1][match_start:match_end]
                remote_url_parts[1] = remote_url_parts[1].replace(matched_string, "")
            project_namespace = remote_url_parts[1].replace(".git", "")
        else:
            remote_url_parts = remote_url.split("/")
            project_namespace = "/".join(remote_url_parts[1:]).replace(".git", "")

        server_parts = remote_url_parts[0].replace("git@", "")
        server_base = server_parts.split(":")[0]  # port is not needed, this works even without port
        api_base_url = f"https://{server_base}"

        return project_namespace, server_base, api_base_url, remote_url

    @classmethod
    def get_git_api_token(cls, git_user_config_path: Path, git_server_base: str) -> str:
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

    @classmethod
    def get_git_project_info(cls) -> tuple[GitProjectInfo | None, int]:
        try:
            git_project_root = cls.find_git_project_root(cwd=Path.cwd())
            if git_project_root is None:
                print("Error: Couldn't find your git project root")
                return None, 1

            git_dir_path = git_project_root / ".git"
            project_namespace, git_server_base, api_base_url, url_to_repo = cls.get_project_namespace(
                git_dir_path=git_dir_path
            )

            git_api_token = cls.get_git_api_token(
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
            print("Error: Folder not part of the git repo. You must be within the git project folder.")
            return None, 1
