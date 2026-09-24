import os
from pathlib import Path
from typing import Any, Callable


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
        return [tool.to_ai_schema() for tool in self._tools.values()]


LOG_FILE = Path(__file__).parent.parent / "logs" / "application.log"


def is_incident_active() -> bool:
    return os.getenv("INCIDENT_MODE", "false").lower() == "true"


def get_application_health() -> dict[str, Any]:
    if is_incident_active():
        return {
            "status": "unhealthy",
            "service": "opspilot-api",
            "error_rate": "high",
            "message": "Application health check is failing.",
        }

    return {
        "status": "healthy",
        "service": "opspilot-api",
    }


def get_recent_logs(lines: int = 20) -> dict[str, Any]:
    if is_incident_active():
        incident_logs = [
            "2026-09-23 16:10:01 ERROR Database connection refused",
            "2026-09-23 16:10:02 ERROR Request failed with status 500",
            "2026-09-23 16:10:03 ERROR Database connection timeout",
            "2026-09-23 16:10:04 ERROR Health check failed",
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

    with LOG_FILE.open("r", encoding="utf-8") as file:
        recent_logs = file.readlines()[-lines:]

    return {
        "service": "opspilot-api",
        "logs": [line.strip() for line in recent_logs],
    }


def get_deployment_status() -> dict[str, Any]:
    if is_incident_active():
        return {
            "service": "opspilot-api",
            "version": "1.0.1",
            "status": "failed",
            "environment": "development",
            "deployed_at": "2026-09-23T16:10:00",
            "message": "Latest deployment is unhealthy.",
        }

    return {
        "service": "opspilot-api",
        "version": "1.0.0",
        "status": "healthy",
        "environment": "development",
        "deployed_at": "2026-09-23T13:10:00",
    }


def rollback_deployment() -> dict[str, Any]:
    """
    Simulate a rollback to the previous stable version.

    For the demo, the rollback disables INCIDENT_MODE for the
    running process so subsequent health checks report recovery.
    """
    os.environ["INCIDENT_MODE"] = "false"

    return {
        "action": "rollback_deployment",
        "status": "completed",
        "service": "opspilot-api",
        "from_version": "1.0.1",
        "to_version": "1.0.0",
        "message": (
            "Deployment successfully rolled back to the previous "
            "stable version."
        ),
    }


tool_registry = ToolRegistry()


tool_registry.register(
    Tool(
        name="get_application_health",
        description="Check the current health status of the OpsPilot application.",
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
        description="Retrieve recent application logs for incident investigation.",
        function=get_recent_logs,
        parameters={
            "type": "object",
            "properties": {
                "lines": {
                    "type": "integer",
                    "description": "Number of recent log lines to retrieve.",
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
        description="Check the currently deployed application version and deployment status.",
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
            "Roll back the current failed deployment to the previous stable "
            "application version. This action requires human approval."
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