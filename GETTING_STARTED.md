# Getting Started

## Prerequisites

Install:

- Python 3.12+
- Node.js 24+
- Docker Desktop
- Git

## 1. Clone the Repository

```powershell
git clone https://github.com/sruthydenny/opspilot.git
cd opspilot
```

## 2. Create the Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install Backend Dependencies

```powershell
pip install -r backend/requirements.txt
```

## 4. Configure Environment Variables

Create `.env` from `.env.example`.

Example:

```env
OPENROUTER_API_KEY=your_api_key_here
AI_MODEL=openrouter/free
```

Do not commit `.env` or API keys.

## 5. Start Backend Services

From the project root:

```powershell
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

## 6. Start the Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The dashboard will be available at:

```text
http://localhost:3000
```

## 7. Run Tests

Backend:

```powershell
python -m pytest backend/tests -q
```

Frontend lint:

```powershell
cd frontend
npm run lint
```

Frontend build:

```powershell
npm run build
```

Docker build:

```powershell
cd ..
docker build -f backend/Dockerfile -t opspilot-api:ci .
```

## 8. Demo Flow

1. Open the OpsPilot dashboard.
2. Run an incident investigation.
3. Review the agent investigation trace.
4. Create or load the rollback approval.
5. Approve the rollback.
6. Verify application recovery.
7. Review the DevOps improvement recommendations.