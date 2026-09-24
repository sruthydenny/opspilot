import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_ai_model() -> str:
    return os.getenv("AI_MODEL", "openrouter/free")

def get_ai_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not configured."
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


def choose_tool(
    goal: str,
    tool_schemas: list[dict],
) -> str:
    client = get_ai_client()

    response = client.chat.completions.create(
        model=get_ai_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI DevOps agent. "
                    "Use the available tools to accomplish the user's goal."
                ),
            },
            {
                "role": "user",
                "content": goal,
            },
        ],
        tools=tool_schemas,
        tool_choice="required",
    )

    message = response.choices[0].message

    if not message.tool_calls:
        print("\n--- AI RESPONSE DEBUG ---")
        print("Content:", message.content)
        print("Tool calls:", message.tool_calls)
        print("Finish reason:", response.choices[0].finish_reason)
        print("-------------------------\n")

        raise RuntimeError("AI did not request a tool.")

    return message.tool_calls[0].function.name


def run_agent_turn(
    goal: str,
    tool_schemas: list[dict],
    tool_executor,
) -> dict:
    MAX_STEPS = 5

    client = get_ai_client()

    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI DevOps agent. "
                "Use available tools to investigate the user's goal. "
                "When you have enough information, provide a concise final answer."
            ),
        },
        {
            "role": "user",
            "content": goal,
        },
    ]

    tool_calls = []
    observations = []

    for step in range(MAX_STEPS):
        response = client.chat.completions.create(
            model=get_ai_model(),
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return {
                "tool_calls": tool_calls,
                "observations": observations,
                "final_answer": message.content,
                "steps": step + 1,
            }

        tool_call = message.tool_calls[0]

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        parsed_arguments = json.loads(arguments)

        observation = tool_executor(
            tool_name,
            parsed_arguments,
        )

        tool_calls.append(
            {
                "tool": tool_name,
                "arguments": parsed_arguments,
            }
        )

        observations.append(
            {
                "tool": tool_name,
                "result": observation,
            }
        )

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": arguments,
                        },
                    }
                ],
            }
        )

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(observation),
            }
        )

    return {
        "tool_calls": tool_calls,
        "observations": observations,
        "final_answer": (
            "The investigation reached the maximum number of "
            "agent steps without producing a final answer."
        ),
        "steps": MAX_STEPS,
    }