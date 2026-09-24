from unittest.mock import MagicMock, patch

from backend.app.agent.ai_client import (
    get_ai_client,
    run_agent_turn,
)
from backend.app.agent.tools import tool_registry


def test_ai_client_requires_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    client = get_ai_client()

    assert client is not None


def test_tool_schema_is_available():
    schemas = tool_registry.get_ai_schemas()

    assert len(schemas) >= 1
    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "get_application_health"


def test_run_agent_turn_supports_multiple_tool_calls():
    first_message = MagicMock()
    first_message.content = None

    first_tool_call = MagicMock()
    first_tool_call.id = "call-1"
    first_tool_call.function.name = "get_application_health"
    first_tool_call.function.arguments = "{}"

    first_message.tool_calls = [first_tool_call]

    second_message = MagicMock()
    second_message.content = None

    second_tool_call = MagicMock()
    second_tool_call.id = "call-2"
    second_tool_call.function.name = "get_recent_logs"
    second_tool_call.function.arguments = '{"lines": 2}'

    second_message.tool_calls = [second_tool_call]

    final_message = MagicMock()
    final_message.content = "The investigation is complete."
    final_message.tool_calls = None

    first_response = MagicMock()
    first_response.choices = [MagicMock(message=first_message)]

    second_response = MagicMock()
    second_response.choices = [MagicMock(message=second_message)]

    final_response = MagicMock()
    final_response.choices = [MagicMock(message=final_message)]

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        first_response,
        second_response,
        final_response,
    ]

    def execute_tool(tool_name, arguments):
        tool = tool_registry.get(tool_name)
        return tool.execute(**arguments)

    with patch(
        "backend.app.agent.ai_client.get_ai_client",
        return_value=mock_client,
    ):
        result = run_agent_turn(
            goal="Investigate the application.",
            tool_schemas=tool_registry.get_ai_schemas(),
            tool_executor=execute_tool,
        )

    assert result["final_answer"] == "The investigation is complete."
    assert result["steps"] == 3
    assert mock_client.chat.completions.create.call_count == 3