from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.agent.runner import AgentRunner
from backend.app.agent.tools import (
    build_project_tool_registry,
    tool_registry,
)
from backend.app.auth import (
    create_session,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.app.database import engine, get_db, init_db
from backend.app.models import Approval, Project, User


app = FastAPI(
    title="OpsPilot API",
    description="Agentic AI platform for intelligent DevOps operations.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    goal: str


class ApprovalRequest(BaseModel):
    tool: str
    arguments: dict[str, Any] = {}


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ProjectCreateRequest(BaseModel):
    name: str
    repository_url: HttpUrl | None = None
    application_url: HttpUrl | None = None
    health_endpoint: HttpUrl | None = None
    environment: str = "development"


@app.on_event("startup")
def startup() -> None:
    init_db()


def get_user_project(
    project_id: int,
    user: User,
    db: Session,
) -> Project:
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.owner_id == user.id,
        )
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found.",
        )

    return project


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "opspilot-api",
        "version": "0.3.0",
    }


@app.get("/api/database/health")
async def database_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "postgresql",
    }


@app.post("/api/auth/register")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        )

    user = User(
        email=email,
        password_hash=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_session(db, user.id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "token": token,
    }


@app.post("/api/auth/login")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    email = request.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_session(db, user.id)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
        },
        "token": token,
    }


@app.get("/api/auth/me")
async def get_me(
    user: User = Depends(get_current_user),
):
    return {
        "id": user.id,
        "email": user.email,
    }


@app.post("/api/projects")
async def create_project(
    request: ProjectCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        owner_id=user.id,
        name=request.name.strip(),
        repository_url=(
            str(request.repository_url)
            if request.repository_url
            else None
        ),
        application_url=(
            str(request.application_url)
            if request.application_url
            else None
        ),
        health_endpoint=(
            str(request.health_endpoint)
            if request.health_endpoint
            else None
        ),
        environment=request.environment.strip(),
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "repository_url": project.repository_url,
        "application_url": project.application_url,
        "health_endpoint": project.health_endpoint,
        "environment": project.environment,
        "deployment_status": project.deployment_status,
    }


@app.get("/api/projects")
async def list_projects(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = (
        db.query(Project)
        .filter(Project.owner_id == user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return {
        "projects": [
            {
                "id": project.id,
                "name": project.name,
                "repository_url": project.repository_url,
                "application_url": project.application_url,
                "health_endpoint": project.health_endpoint,
                "environment": project.environment,
                "deployment_status": project.deployment_status,
                "current_version": project.current_version,
            }
            for project in projects
        ]
    }


@app.get("/api/projects/{project_id}")
async def get_project(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        user,
        db,
    )

    return {
        "id": project.id,
        "name": project.name,
        "repository_url": project.repository_url,
        "application_url": project.application_url,
        "health_endpoint": project.health_endpoint,
        "environment": project.environment,
        "incident_mode": project.incident_mode,
        "current_version": project.current_version,
        "previous_version": project.previous_version,
        "deployment_status": project.deployment_status,
    }


@app.post("/api/projects/{project_id}/simulate-incident")
async def simulate_incident(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        user,
        db,
    )

    # Deterministic demo incident:
    # stable version 1.0.0 -> failed deployment 1.0.1
    project.previous_version = "1.0.0"
    project.current_version = "1.0.1"
    project.incident_mode = True
    project.deployment_status = "failed"

    db.commit()
    db.refresh(project)

    return {
        "project_id": project.id,
        "status": "incident_simulated",
        "version": project.current_version,
        "previous_version": project.previous_version,
        "deployment_status": project.deployment_status,
    }


@app.post("/api/projects/{project_id}/agent/run")
async def run_project_agent(
    project_id: int,
    request: AgentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        user,
        db,
    )

    project_tools = build_project_tool_registry(
        project,
        db,
    )

    project_agent = AgentRunner(project_tools)

    return project_agent.run(
        request.goal
    )


@app.get("/api/projects/{project_id}/approvals")
async def list_project_approvals(
    project_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_user_project(
        project_id,
        user,
        db,
    )

    approvals = (
        db.query(Approval)
        .filter(
            Approval.project_id == project_id,
            Approval.user_id == user.id,
        )
        .order_by(Approval.created_at.desc())
        .all()
    )

    return {
        "approvals": [
            {
                "id": approval.id,
                "status": approval.status,
                "tool": approval.tool,
                "arguments": approval.arguments,
                "result": approval.result,
            }
            for approval in approvals
        ]
    }


@app.post("/api/projects/{project_id}/approvals")
async def create_project_approval(
    project_id: int,
    request: ApprovalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        user,
        db,
    )

    project_tools = build_project_tool_registry(
        project,
        db,
    )

    tool = project_tools.get(request.tool)

    if not tool.requires_approval:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tool '{request.tool}' does not "
                "require approval."
            ),
        )

    approval = Approval(
        user_id=user.id,
        project_id=project.id,
        tool=request.tool,
        arguments=request.arguments,
        status="pending",
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return {
        "id": approval.id,
        "status": approval.status,
        "tool": approval.tool,
        "arguments": approval.arguments,
    }


@app.post("/api/projects/{project_id}/approvals/{approval_id}/approve")
async def approve_project_request(
    project_id: int,
    approval_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_user_project(
        project_id,
        user,
        db,
    )

    approval = (
        db.query(Approval)
        .filter(
            Approval.id == approval_id,
            Approval.project_id == project.id,
            Approval.user_id == user.id,
        )
        .first()
    )

    if not approval:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found.",
        )

    if approval.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=(
                "Approval request has already "
                "been processed."
            ),
        )

    project_tools = build_project_tool_registry(
        project,
        db,
    )

    tool = project_tools.get(approval.tool)

    result = tool.execute(
        **approval.arguments
    )

    approval.status = "approved"
    approval.result = result

    db.commit()

    return {
        "id": approval.id,
        "status": approval.status,
        "tool": approval.tool,
        "arguments": approval.arguments,
        "result": approval.result,
    }


# Legacy demo endpoint kept for backward compatibility.
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


@app.post("/api/agent/run")
async def run_legacy_agent(
    request: AgentRequest,
):
    agent = AgentRunner(tool_registry)
    return agent.run(request.goal)