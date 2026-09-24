from typing import Any
from uuid import uuid4

from backend.app.agent.ai_client import run_agent_turn
from backend.app.agent.tools import ToolRegistry


class AgentRunner:
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        approved: bool = False,
    ) -> Any:
        tool = self.tool_registry.get(tool_name)

        if tool.requires_approval and not approved:
            return {
                "status": "approval_required",
                "tool": tool_name,
                "arguments": arguments,
                "approval_id": str(uuid4()),
                "message": (
                    f"Human approval is required before executing "
                    f"'{tool_name}'."
                ),
            }

        return tool.execute(**arguments)

    def run(self, goal: str) -> dict[str, Any]:
        result = run_agent_turn(
            goal=goal,
            tool_schemas=self.tool_registry.get_ai_schemas(),
            tool_executor=self.execute_tool,
        )

        trace = [
            {
                "step": 1,
                "type": "goal",
                "content": goal,
            }
        ]

        step_number = 2
        approval_required = None

        for tool_call, observation in zip(
            result["tool_calls"],
            result["observations"],
        ):
            trace.append(
                {
                    "step": step_number,
                    "type": "tool_call",
                    "tool": tool_call["tool"],
                    "arguments": tool_call["arguments"],
                }
            )

            step_number += 1

            trace.append(
                {
                    "step": step_number,
                    "type": "observation",
                    "tool": observation["tool"],
                    "result": observation["result"],
                }
            )

            if observation["result"].get("status") == "approval_required":
                approval_required = observation["result"]

            step_number += 1

        trace.append(
            {
                "step": step_number,
                "type": "final_answer",
                "content": result["final_answer"],
            }
        )

        response = {
            "goal": goal,
            "status": "completed",
            "trace": trace,
            "steps": result["steps"],
        }

        if approval_required:
            response["approval_required"] = approval_required

        return response