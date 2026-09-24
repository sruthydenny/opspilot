# OpsPilot — Getting Started

This guide explains how to run OpsPilot locally and demonstrate the main Agentic DevOps workflow.

## Requirements

Make sure you have:

- Python 3.12+
- Node.js 24+
- npm
- Git
- Docker Desktop

Docker Desktop should be running before starting the project.

## 1. Clone the Repository

```powershell
git clone https://github.com/sruthydenny/opspilot.git
cd opspilot
```

## 2. Set Up the Backend

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

## 3. Configure Environment Variables

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your AI API key.

Example:

```env
OPENROUTER_API_KEY=your_api_key_here
AI_MODEL=openrouter/free

POSTGRES_USER=opspilot
POSTGRES_PASSWORD=opspilot_dev_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=opspilot
```

Do not commit `.env` to GitHub.

## 4. Start the Backend Services

From the project root:

```powershell
docker compose up -d --build
```

Check the services:

```powershell
docker compose ps
```

The project uses Docker services for the API, PostgreSQL, and Redis.

## 5. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the application:

```text
http://localhost:3000
```

## 6. Run the Demo

### Create an account

Register a user and log in to the dashboard.

### Create a project

Create a project and provide information such as:

- Project name
- GitHub repository
- Application URL
- Health endpoint
- Environment

### Simulate an incident

Select the project and click:

**Simulate Incident**

The project enters a deterministic failed state with an unhealthy application and failed deployment.

### Investigate with OpsPilot

Click:

**Ask OpsPilot**

The agent will investigate:

```text
Application Health
      ↓
Recent Logs
      ↓
Deployment Status
      ↓
Recent GitHub Commits
      ↓
GitHub Actions
      ↓
AI Analysis
```

The investigation trace shows the tools used and the observations returned by each tool.

### Approve the remediation

When the agent requests a rollback, open **Human Approvals**.

The rollback must be explicitly approved before it can execute.

### Verify recovery

After approval, the deployment is rolled back and the project returns to a healthy state.

The complete demonstration is:

```text
Detect
  ↓
Investigate
  ↓
Reason
  ↓
Recommend
  ↓
Human Approval
  ↓
Rollback
  ↓
Verify Recovery
```

## 7. Run Tests

From the project root:

```powershell
python -m pytest backend/tests -q
```

Run integration tests:

```powershell
python -m pytest backend/integration_tests -q
```

Run frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

## 8. Useful Docker Commands

Rebuild the API after backend changes:

```powershell
docker compose up -d --build api
```

View API logs:

```powershell
docker compose logs -f api
```

Check services:

```powershell
docker compose ps
```

Stop services:

```powershell
docker compose down
```

## Notes

OpsPilot is an educational/MVP implementation.

The incident and deployment environment used in the demonstration is simulated. GitHub integration currently provides read-only repository and CI information, while operational actions such as rollback are protected by human approval.