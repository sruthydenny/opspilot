from backend.app.agent.tools import tool_registry


def test_tool_registry_contains_expected_tools():
    tools = tool_registry.list_tools()

    assert "get_application_health" in tools
    assert "get_recent_logs" in tools
    assert "get_deployment_status" in tools
    assert "rollback_deployment" in tools


def test_tool_ai_schema():
    schemas = tool_registry.get_ai_schemas()

    assert len(schemas) == 4

    assert schemas[0]["type"] == "function"
    assert schemas[0]["function"]["name"] == "get_application_health"

    assert schemas[1]["type"] == "function"
    assert schemas[1]["function"]["name"] == "get_recent_logs"

    assert schemas[2]["type"] == "function"
    assert schemas[2]["function"]["name"] == "get_deployment_status"

    assert schemas[3]["type"] == "function"
    assert schemas[3]["function"]["name"] == "rollback_deployment"


def test_rollback_tool_requires_approval():
    rollback_tool = tool_registry.get("rollback_deployment")

    assert rollback_tool.requires_approval is True