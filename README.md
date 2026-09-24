# OpsPilot

OpsPilot is an **Agentic AI DevOps platform** designed to help investigate software incidents, analyze DevOps signals, and safely perform operational actions with human approval.

The project explores how AI agents can move beyond chat and actively participate in software delivery and production workflows.

## Core Workflow

```text
Incident
   ↓
AI Investigation
   ↓
Health + Logs + Deployment
   ↓
GitHub + CI/CD
   ↓
Root-Cause Analysis
   ↓
Remediation Recommendation
   ↓
Human Approval
   ↓
Rollback / Recovery
   ↓
Verification
```

## Features

- Multi-user authentication
- Multiple projects per user
- Project-specific DevOps investigation
- AI agent with tool calling
- Application health and log inspection
- Deployment status analysis
- GitHub commit inspection
- GitHub Actions / CI status inspection
- Human approval for operational actions
- Simulated incidents and deployment failures
- Rollback and recovery workflow
- DevOps improvement recommendations
- Dockerized development environment
- Automated CI checks

## Example Incident

OpsPilot can simulate a production incident such as:

```text
Application: Unhealthy
Deployment: 1.0.1 Failed
Previous Version: 1.0.0

Logs:
ERROR Database connection refused
ERROR Request failed with status 500
ERROR Database connection timeout
ERROR Health check failed
```

The agent investigates the available evidence, identifies a likely cause, and requests a rollback. The rollback requires human approval before execution.

## Architecture

```text
Next.js Frontend
       ↓
FastAPI Backend
       ↓
Agent Runner
       ↓
LLM + Tool Calling
       ↓
Tool Registry
   ↙    ↓     ↘
Health  GitHub  Deployment
Logs    CI/CD   Actions
       ↓
Human Approval
       ↓
Recovery
```

## Tech Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Cache / Services:** Redis
- **AI:** LLM API with tool calling
- **DevOps:** Docker, Docker Compose, GitHub Actions

## DevOps Practices

OpsPilot demonstrates:

- Continuous integration
- Automated testing
- Containerization
- CI/CD monitoring
- Incident investigation
- Health and log monitoring
- Rollback and recovery
- Human-in-the-loop operations
- Post-incident improvement

## Goal

The main goal is to demonstrate an Agentic AI workflow for DevOps:

**Observe → Investigate → Reason → Recommend → Approve → Act → Verify → Improve**

## Getting Started

See [GETTING_STARTED.md](GETTING_STARTED.md) for installation and the project demonstration.