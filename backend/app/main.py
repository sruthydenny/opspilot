from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from backend.app.agent.runner import AgentRunner
from backend.app.agent.tools import tool_registry
from backend.app.database import engine


app = FastAPI(
    title="OpsPilot API",
    description="Agentic AI platform for intelligent DevOps operations.",
    version="0.1.0",
)


# Allow the Next.js frontend to communicate with the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = AgentRunner(tool_registry)

approval_requests: dict[str, dict[str, Any]] = {}


class AgentRequest(BaseModel):
    goal: str


class ApprovalRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = {}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "opspilot-api",
        "version": "0.1.0",
    }


@app.get("/api/database/health")
async def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "postgresql",
    }


@app.get("/api/agent/tools")
async def list_agent_tools():
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_approval": tool.requires_approval,
            }
            for tool in tool_registry._tools.values()
        ]
    }


@app.post("/api/agent/tools/{tool_name}/execute")
async def execute_agent_tool(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
):
    arguments = arguments or {}

    tool = tool_registry.get(tool_name)

    if tool.requires_approval:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Tool '{tool_name}' requires human approval "
                "before execution."
            ),
        )

    return tool.execute(**arguments)


@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    return agent.run(request.goal)


@app.post("/api/approvals")
async def create_approval(request: ApprovalRequest):
    tool = tool_registry.get(request.tool)

    if not tool.requires_approval:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{request.tool}' does not require approval.",
        )

    approval_id = str(len(approval_requests) + 1)

    approval = {
        "id": approval_id,
        "status": "pending",
        "tool": request.tool,
        "arguments": request.arguments,
    }

    approval_requests[approval_id] = approval

    return approval


@app.get("/api/approvals")
async def list_approvals():
    return {
        "approvals": list(approval_requests.values())
    }


@app.post("/api/approvals/{approval_id}/approve")
async def approve_request(approval_id: str):
    approval = approval_requests.get(approval_id)

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    if approval["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Approval request has already been processed.",
        )

    tool = tool_registry.get(approval["tool"])

    result = tool.execute(**approval["arguments"])

    approval["status"] = "approved"
    approval["result"] = result

    return approval