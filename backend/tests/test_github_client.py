import pytest

from backend.app.agent.github_client import (
    parse_github_repository_url,
)


def test_parse_github_repository_url():
    owner, repository = parse_github_repository_url(
        "https://github.com/example/project"
    )

    assert owner == "example"
    assert repository == "project"


def test_parse_github_repository_url_with_git_suffix():
    owner, repository = parse_github_repository_url(
        "https://github.com/example/project.git"
    )

    assert owner == "example"
    assert repository == "project"


def test_parse_github_repository_url_rejects_non_github():
    with pytest.raises(ValueError):
        parse_github_repository_url(
            "https://gitlab.com/example/project"
        )