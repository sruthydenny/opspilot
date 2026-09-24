from unittest.mock import patch

from backend.app.agent.runner import AgentRunner
from backend.app.agent.tools import tool_registry


def test_agent_runner():
    agent = AgentRunner(tool_registry)

    mocked_result = {
        "tool_calls": [
            {
                "tool": "get_application_health",
                "arguments": {},
            },
            {
                "tool": "get_recent_logs",
                "arguments": {
                    "lines": 2,
                },
            },
        ],
        "observations": [
            {
                "tool": "get_application_health",
                "result": {
                    "status": "healthy",
                    "service": "opspilot-api",
                },
            },
            {
                "tool": "get_recent_logs",
                "result": {
                    "service": "opspilot-api",
                    "logs": [
                        "2026-09-23 13:02:03 INFO Health check passed",
                        "2026-09-23 13:03:10 INFO Request processed successfully",
                    ],
                },
            },
        ],
        "final_answer": "The application is healthy and recent logs were reviewed.",
        "steps": 3,
    }

    with patch(
        "backend.app.agent.runner.run_agent_turn",
        return_value=mocked_result,
    ):
        result = agent.run(
            "Investigate the application."
        )

    assert result["status"] == "completed"
    assert result["steps"] == 3

    assert result["trace"][0]["type"] == "goal"

    assert result["trace"][1]["type"] == "tool_call"
    assert result["trace"][1]["tool"] == "get_application_health"

    assert result["trace"][2]["type"] == "observation"
    assert result["trace"][2]["tool"] == "get_application_health"

    assert result["trace"][3]["type"] == "tool_call"
    assert result["trace"][3]["tool"] == "get_recent_logs"

    assert result["trace"][4]["type"] == "observation"
    assert result["trace"][4]["tool"] == "get_recent_logs"

    assert result["trace"][5]["type"] == "final_answer"
    assert (
        result["trace"][5]["content"]
        == "The application is healthy and recent logs were reviewed."
    )