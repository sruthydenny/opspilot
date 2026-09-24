# OpsPilot

Agentic AI platform for DevOps incident investigation and controlled remediation.

## Overview

OpsPilot uses an AI agent to investigate software incidents, analyze operational evidence, propose remediation, execute approved actions, and verify recovery.

The agent interacts with DevOps operations through a controlled tool registry. Risky actions require human approval.

## Core Workflow

```text
Incident
   ↓
AI Investigation
   ↓
Evidence Analysis
   ↓
Remediation Proposal
   ↓
Human Approval
   ↓
Rollback
   ↓
Recovery Verification
```

## Main Features

- Agentic AI with LLM tool calling
- Application health inspection
- Recent log inspection
- Deployment status inspection
- Human approval for risky actions
- Deployment rollback
- Recovery verification
- Agent execution trace
- DevOps improvement recommendations

## Tech Stack

- Python 3.12
- FastAPI
- OpenRouter
- Next.js
- React
- TypeScript
- Tailwind CSS
- PostgreSQL
- Redis
- Docker
- Docker Compose
- GitHub Actions
- Pytest

## Architecture

```text
Next.js Dashboard
       ↓
FastAPI Backend
       ↓
AI Agent
       ↓
Tool Registry
   ┌───┴──────────────┐
   ↓                  ↓
Read-only tools    Approved actions
Health             Rollback
Logs
Deployment Status
```

## DevOps Practices

- Continuous integration
- Automated testing
- Dependency security checks
- Containerization
- Docker Compose
- Controlled operational actions
- Human approval
- Recovery verification

## Goal

OpsPilot demonstrates how Agentic AI can participate in a controlled DevOps workflow:

```text
Observe → Investigate → Reason → Propose → Approve → Execute → Verify
```

For installation and local setup, see [Getting Started](GETTING_STARTED.md).