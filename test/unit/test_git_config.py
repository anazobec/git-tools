import pytest
from pytest_mock import MockerFixture
from pathlib import Path
from src.utils.git import GitConfig


def mock_git_config(
    mocker: MockerFixture | None,
    remote_url: str,
) -> dict[str, dict[str, str]] | None:
    config = {
        'remote "origin"': {
            "url": remote_url,
        },
    }
    if mocker is not None:
        mocker.patch("configparser.ConfigParser.read", return_value=[])
        mocker.patch("configparser.ConfigParser.__getitem__", side_effect=config.__getitem__)

        return None

    return config


def mock_gitlab_api_token(
    mocker: MockerFixture | None,
    server_base: str,
    api_token: str,
) -> dict[str, dict[str, str]] | None:
    config = {
        server_base: {
            "api_token": api_token,
        },
    }

    if mocker is not None:
        mocker.patch("configparser.ConfigParser.read", return_value=[])
        mocker.patch("configparser.ConfigParser.__getitem__", side_effect=config.__getitem__)

        return None

    return config


def mock_gitlab_config(
    mocker: MockerFixture,
    remote_url: str,
    server_base: str,
    api_token: str,
) -> None:
    git_config = mock_git_config(mocker=None, remote_url=remote_url)
    gitlab_api_token_config = mock_gitlab_api_token(mocker=None, server_base=server_base, api_token=api_token)
    assert git_config is not None
    assert gitlab_api_token_config is not None

    config = {}
    config.update(git_config)
    config.update(gitlab_api_token_config)

    mocker.patch("configparser.ConfigParser.read", return_value=[])
    mocker.patch("configparser.ConfigParser.__getitem__", side_effect=config.__getitem__)


class TestGitConfig:
    @pytest.mark.parametrize(
        "remote_url",
        [
            ("ssh://git@abc.gitlab.com:1234/some/namespace/path.git"),
            ("http://git@abc.gitlab.com:1234/some/namespace/path.git"),
            ("https://git@abc.gitlab.com:1234/some/namespace/path.git"),
        ],
    )
    def test_get_project_namespace_with_net_url_with_port(self, mocker: MockerFixture, remote_url: str) -> None:
        mock_git_config(mocker=mocker, remote_url=remote_url)

        project_namespace, server_base, api_base_url, remote_url = GitConfig.get_project_namespace(
            git_dir_path=Path("test-dir"),
        )

        assert project_namespace == "some/namespace/path"
        assert server_base == "abc.gitlab.com"
        assert api_base_url == f"https://{server_base}"
        assert remote_url == remote_url

    @pytest.mark.parametrize(
        "remote_url",
        [
            ("ssh://git@abc.gitlab.com/some/namespace/path.git"),
            ("http://git@abc.gitlab.com/some/namespace/path.git"),
            ("https://git@abc.gitlab.com/some/namespace/path.git"),
        ],
    )
    def test_get_project_namespace_with_net_url_without_port(self, mocker: MockerFixture, remote_url: str) -> None:
        mock_git_config(mocker=mocker, remote_url=remote_url)

        project_namespace, server_base, api_base_url, remote_url = GitConfig.get_project_namespace(
            git_dir_path=Path("test-dir"),
        )

        assert project_namespace == "some/namespace/path"
        assert server_base == "abc.gitlab.com"
        assert api_base_url == f"https://{server_base}"
        assert remote_url == remote_url

    def test_get_project_namespace_with_at_url_with_port(self, mocker: MockerFixture) -> None:
        remote_url = "git@abc.gitlab.com:1234/some/namespace/path.git"
        mock_git_config(mocker=mocker, remote_url=remote_url)

        project_namespace, server_base, api_base_url, remote_url = GitConfig.get_project_namespace(
            git_dir_path=Path("test-dir"),
        )

        assert project_namespace == "some/namespace/path"
        assert server_base == "abc.gitlab.com"
        assert api_base_url == f"https://{server_base}"
        assert remote_url == remote_url

    def test_get_project_namespace_with_at_url_without_port(self, mocker: MockerFixture) -> None:
        remote_url = "git@abc.gitlab.com:some/namespace/path.git"
        mock_git_config(mocker=mocker, remote_url=remote_url)

        project_namespace, server_base, api_base_url, remote_url = GitConfig.get_project_namespace(
            git_dir_path=Path("test-dir"),
        )

        assert project_namespace == "some/namespace/path"
        assert server_base == "abc.gitlab.com"
        assert api_base_url == f"https://{server_base}"
        assert remote_url == remote_url

    def test_get_git_api_token_pass(self, mocker: MockerFixture) -> None:
        server_base = "abc.gitlab.com"
        api_token = "some-very-legit-api-token"
        mock_gitlab_api_token(mocker=mocker, server_base=server_base, api_token=api_token)

        git_api_token = GitConfig.get_git_api_token(git_user_config_path=Path("test-path"), git_server_base=server_base)

        assert git_api_token == api_token

    def test_get_git_api_token(self, mocker: MockerFixture) -> None:
        server_base = "abc.gitlab.com"
        api_token = "some-very-legit-api-token"
        mock_gitlab_api_token(mocker=mocker, server_base=server_base, api_token=api_token)

        git_api_token = GitConfig.get_git_api_token(
            git_user_config_path=Path("test-path"),
            git_server_base=server_base,
        )

        assert git_api_token == api_token

    def test_get_git_project_info(self, mocker: MockerFixture) -> None:
        git_project_root = Path("test-root")
        mocker.patch("src.utils.git.GitConfig.find_git_project_root", return_value=git_project_root)

        server_base = "abc.gitlab.com"
        namespace = "some/namespace/path"
        remote_url = f"git@{server_base}:1234/{namespace}.git"
        api_token = "some-very-legit-api-token"

        mock_gitlab_config(
            mocker=mocker,
            remote_url=remote_url,
            server_base=server_base,
            api_token=api_token,
        )

        git_project_info, exit_code = GitConfig.get_git_project_info()

        assert git_project_info is not None
        assert git_project_info.path == git_project_root
        assert git_project_info.namespace == namespace
        assert git_project_info.server_base == server_base
        assert git_project_info.api_token == api_token
        assert git_project_info.url_to_repo == remote_url
        assert exit_code == 0
