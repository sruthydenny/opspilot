from urllib.parse import urlparse

import httpx


GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION = "2026-03-10"


def parse_github_repository_url(
    repository_url: str,
) -> tuple[str, str]:
    parsed = urlparse(repository_url)

    if parsed.netloc.lower() != "github.com":
        raise ValueError(
            "Repository URL must point to github.com."
        )

    parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if len(parts) != 2:
        raise ValueError(
            "Repository URL must look like "
            "https://github.com/owner/repository."
        )

    owner = parts[0]
    repository = parts[1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    return owner, repository


def github_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def get_recent_commits(
    repository_url: str,
    limit: int = 5,
) -> dict:
    owner, repository = parse_github_repository_url(
        repository_url
    )

    response = httpx.get(
        f"{GITHUB_API_URL}/repos/{owner}/{repository}/commits",
        headers=github_headers(),
        params={
            "per_page": min(limit, 10),
        },
        timeout=10.0,
    )

    if response.status_code == 404:
        return {
            "status": "not_found",
            "repository": f"{owner}/{repository}",
            "message": (
                "GitHub repository was not found or "
                "is not publicly accessible."
            ),
        }

    response.raise_for_status()

    commits = response.json()

    return {
        "status": "success",
        "repository": f"{owner}/{repository}",
        "commits": [
            {
                "sha": commit["sha"],
                "message": commit["commit"]["message"],
                "author": (
                    commit.get("author", {})
                    or {}
                ).get("login"),
                "date": (
                    commit["commit"]
                    .get("author", {})
                    .get("date")
                ),
                "url": commit["html_url"],
            }
            for commit in commits
        ],
    }


def get_ci_status(
    repository_url: str,
    limit: int = 5,
) -> dict:
    owner, repository = parse_github_repository_url(
        repository_url
    )

    response = httpx.get(
        f"{GITHUB_API_URL}/repos/{owner}/{repository}/actions/runs",
        headers=github_headers(),
        params={
            "per_page": min(limit, 10),
        },
        timeout=10.0,
    )

    if response.status_code == 404:
        return {
            "status": "not_found",
            "repository": f"{owner}/{repository}",
            "message": (
                "GitHub Actions information was not found "
                "or is not publicly accessible."
            ),
        }

    response.raise_for_status()

    data = response.json()
    runs = data.get("workflow_runs", [])

    return {
        "status": "success",
        "repository": f"{owner}/{repository}",
        "workflow_runs": [
            {
                "name": run["name"],
                "status": run["status"],
                "conclusion": run["conclusion"],
                "branch": run["head_branch"],
                "commit_sha": run["head_sha"],
                "created_at": run["created_at"],
                "url": run["html_url"],
            }
            for run in runs
        ],
    }