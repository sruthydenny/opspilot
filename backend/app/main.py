from fastapi import FastAPI

app = FastAPI(
    title="OpsPilot API",
    description="Agentic AI platform for intelligent DevOps operations.",
    version="0.1.0",
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "opspilot-api",
        "version": "0.1.0",
    }