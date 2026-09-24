from backend.app.agent.ai_client import choose_tool
from backend.app.agent.tools import tool_registry


def test_openrouter_can_choose_health_tool():
    tool_name = choose_tool(
        "Check whether the application is healthy.",
        tool_registry.get_ai_schemas(),
    )

    print(f"\nOpenRouter selected tool: {tool_name}")

    assert tool_name == "get_application_health"

def test_openrouter_can_choose_logs_tool():
    tool_name = choose_tool(
        "Show me the recent application logs.",
        tool_registry.get_ai_schemas(),
    )

    print(f"\nOpenRouter selected tool: {tool_name}")

    assert tool_name == "get_recent_logs"