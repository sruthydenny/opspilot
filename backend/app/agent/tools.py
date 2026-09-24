import os
from pathlib import Path
from typing import Any, Callable

from sqlalchemy.orm import Session

from backend.app.agent.github_client import (
    get_ci_status,
    get_recent_commits,
)


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
        parameters: dict[str, Any] | None = None,
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters or {}
        self.requires_approval = requires_approval

    def execute(self, **kwargs: Any) -> Any:
        return self.function(**kwargs)

    def to_ai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        return self._tools[name]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def get_ai_schemas(self) -> list[dict[str, Any]]:
        return [
            tool.to_ai_schema()
            for tool in self._tools.values()
        ]


LOG_FILE = (
    Path(__file__).parent.parent
    / "logs"
    / "application.log"
)


def is_incident_active() -> bool:
    return (
        os.getenv(
            "INCIDENT_MODE",
            "false",
        ).lower()
        == "true"
    )


def get_application_health() -> dict[str, Any]:
    if is_incident_active():
        return {
            "status": "unhealthy",
            "service": "opspilot-api",
            "error_rate": "high",
            "message": (
                "Application health check is failing."
            ),
        }

    return {
        "status": "healthy",
        "service": "opspilot-api",
    }


def get_recent_logs(
    lines: int = 20,
) -> dict[str, Any]:
    if is_incident_active():
        incident_logs = [
            "ERROR Database connection refused",
            "ERROR Request failed with status 500",
            "ERROR Database connection timeout",
            "ERROR Health check failed",
        ]

        return {
            "service": "opspilot-api",
            "logs": incident_logs[-lines:],
        }

    if not LOG_FILE.exists():
        return {
            "service": "opspilot-api",
            "logs": [],
            "message": "Log file not found.",
        }

    with LOG_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        recent_logs = file.readlines()[-lines:]

    return {
        "service": "opspilot-api",
        "logs": [
            line.strip()
            for line in recent_logs
        ],
    }


def get_deployment_status() -> dict[str, Any]:
    if is_incident_active():
        return {
            "service": "opspilot-api",
            "version": "1.0.1",
            "status": "failed",
            "environment": "development",
            "message": (
                "Latest deployment is unhealthy."
            ),
        }

    return {
        "service": "opspilot-api",
        "version": "1.0.0",
        "status": "healthy",
        "environment": "development",
    }


def rollback_deployment() -> dict[str, Any]:
    os.environ["INCIDENT_MODE"] = "false"

    return {
        "action": "rollback_deployment",
        "status": "completed",
        "service": "opspilot-api",
        "from_version": "1.0.1",
        "to_version": "1.0.0",
        "message": (
            "Deployment successfully rolled back "
            "to the previous stable version."
        ),
    }


def build_project_tool_registry(
    project,
    db: Session,
) -> ToolRegistry:
    registry = ToolRegistry()

    def project_health() -> dict[str, Any]:
        if project.incident_mode:
            return {
                "status": "unhealthy",
                "project_id": project.id,
                "project": project.name,
                "environment": project.environment,
                "error_rate": "high",
                "message": (
                    "Application health check is failing."
                ),
            }

        return {
            "status": "healthy",
            "project_id": project.id,
            "project": project.name,
            "environment": project.environment,
        }

    def project_logs(
        lines: int = 20,
    ) -> dict[str, Any]:
        if project.incident_mode:
            logs = [
                "ERROR Database connection refused",
                "ERROR Request failed with status 500",
                "ERROR Database connection timeout",
                "ERROR Health check failed",
            ]

            return {
                "project_id": project.id,
                "project": project.name,
                "logs": logs[-lines:],
            }

        return {
            "project_id": project.id,
            "project": project.name,
            "logs": [
                "INFO Application started successfully",
                "INFO Health check passed",
            ],
        }

    def project_deployment() -> dict[str, Any]:
        return {
            "project_id": project.id,
            "project": project.name,
            "version": project.current_version,
            "previous_version": project.previous_version,
            "status": project.deployment_status,
            "environment": project.environment,
        }

    def project_commits(
        limit: int = 5,
    ) -> dict[str, Any]:
        if not project.repository_url:
            return {
                "status": "not_configured",
                "project_id": project.id,
                "project": project.name,
                "message": (
                    "No GitHub repository is configured "
                    "for this project."
                ),
            }

        try:
            result = get_recent_commits(
                project.repository_url,
                limit=limit,
            )

            return {
                "project_id": project.id,
                "project": project.name,
                **result,
            }

        except Exception as exc:
            return {
                "status": "error",
                "project_id": project.id,
                "project": project.name,
                "message": (
                    f"Unable to read GitHub commits: {exc}"
                ),
            }

    def project_ci_status(
        limit: int = 5,
    ) -> dict[str, Any]:
        if not project.repository_url:
            return {
                "status": "not_configured",
                "project_id": project.id,
                "project": project.name,
                "message": (
                    "No GitHub repository is configured "
                    "for this project."
                ),
            }

        try:
            result = get_ci_status(
                project.repository_url,
                limit=limit,
            )

            return {
                "project_id": project.id,
                "project": project.name,
                **result,
            }

        except Exception as exc:
            return {
                "status": "error",
                "project_id": project.id,
                "project": project.name,
                "message": (
                    f"Unable to read GitHub Actions: {exc}"
                ),
            }

    def project_rollback() -> dict[str, Any]:
        if not project.previous_version:
            return {
                "action": "rollback_deployment",
                "status": "failed",
                "message": (
                    "No previous deployment is available."
                ),
            }

        from_version = project.current_version
        target_version = project.previous_version

        project.current_version = target_version
        project.previous_version = from_version
        project.incident_mode = False
        project.deployment_status = "healthy"

        db.commit()
        db.refresh(project)

        return {
            "action": "rollback_deployment",
            "status": "completed",
            "project_id": project.id,
            "project": project.name,
            "from_version": from_version,
            "to_version": target_version,
            "message": (
                "Project deployment successfully rolled back."
            ),
        }

    registry.register(
        Tool(
            name="get_application_health",
            description=(
                "Check the health of the selected project."
            ),
            function=project_health,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )
    )

    registry.register(
        Tool(
            name="get_recent_logs",
            description=(
                "Retrieve recent logs for the selected project."
            ),
            function=project_logs,
            parameters={
                "type": "object",
                "properties": {
                    "lines": {
                        "type": "integer",
                        "description": (
                            "Number of recent log lines."
                        ),
                        "default": 20,
                    }
                },
                "required": [],
            },
        )
    )

    registry.register(
        Tool(
            name="get_deployment_status",
            description=(
                "Check the deployment status of the "
                "selected project."
            ),
            function=project_deployment,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
        )
    )

    registry.register(
        Tool(
            name="get_recent_commits",
            description=(
                "Read recent commits from the selected "
                "project's public GitHub repository. "
                "Use this to investigate recent code changes."
            ),
            function=project_commits,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Number of recent commits to inspect."
                        ),
                        "default": 5,
                    }
                },
                "required": [],
            },
        )
    )

    registry.register(
        Tool(
            name="get_ci_status",
            description=(
                "Read recent GitHub Actions workflow runs "
                "for the selected project. Use this to "
                "investigate CI failures or deployment checks."
            ),
            function=project_ci_status,
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Number of recent workflow runs "
                            "to inspect."
                        ),
                        "default": 5,
                    }
                },
                "required": [],
            },
        )
    )

    registry.register(
        Tool(
            name="rollback_deployment",
            description=(
                "Roll back the selected project's current "
                "deployment to its previous version. "
                "This action requires human approval."
            ),
            function=project_rollback,
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            requires_approval=True,
        )
    )

    return registry


tool_registry = ToolRegistry()

tool_registry.register(
    Tool(
        name="get_application_health",
        description=(
            "Check the current health status "
            "of the OpsPilot application."
        ),
        function=get_application_health,
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
)

tool_registry.register(
    Tool(
        name="get_recent_logs",
        description=(
            "Retrieve recent application logs "
            "for incident investigation."
        ),
        function=get_recent_logs,
        parameters={
            "type": "object",
            "properties": {
                "lines": {
                    "type": "integer",
                    "description": (
                        "Number of recent log lines."
                    ),
                    "default": 20,
                }
            },
            "required": [],
        },
    )
)

tool_registry.register(
    Tool(
        name="get_deployment_status",
        description=(
            "Check the currently deployed application "
            "version and deployment status."
        ),
        function=get_deployment_status,
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    )
)

tool_registry.register(
    Tool(
        name="rollback_deployment",
        description=(
            "Roll back the current failed deployment "
            "to the previous stable version. "
            "This action requires human approval."
        ),
        function=rollback_deployment,
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        requires_approval=True,
    )
)