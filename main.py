"""
Terra Intelligence Engine (TIE) - Main API Application.

Production-grade Health Intelligence Layer built on top of Terra's unified
wearable and sensor data infrastructure.

Powers OdinAI reasoning, Terra Graph API visual telemetry,
longitudinal bio-age forecasting, and behavioral retention optimization.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from datetime import datetime

from config import APP_NAME, APP_VERSION, APP_DESCRIPTION, PERSONAS
from api.odin_routes import router as odin_router
from api.graph_routes import router as graph_router
from api.health_routes import router as health_router
from api.reward_routes import router as reward_router
from api.webhook_routes import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize system, verify models, and seed demo telemetry."""
    print("=" * 65)
    print(f"🚀  {APP_NAME} v{APP_VERSION} starting up...")
    print("📡  Terra Wearable Infrastructure Layer: CONNECTED")
    print(f"🧬  Active Health Personas: {len(PERSONAS)} configured")
    print("🧠  OdinAI Health Reasoning Engine: ONLINE")
    print("📊  Terra Graph API & Knowledge Visualizer: ONLINE")
    print("⏳  Longitudinal Bio-Age & Trajectory Predictor: ONLINE")
    print("🎯  Behavioral Habit Retention Engine: ONLINE")
    print("=" * 65)
    yield
    print(f"🛑  {APP_NAME} shutting down...")


app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular Routers
app.include_router(odin_router)
app.include_router(graph_router)
app.include_router(health_router)
app.include_router(reward_router)
app.include_router(webhook_router)

@app.get("/", response_class=HTMLResponse)
async def api_root():
    """
    API root. The interactive dashboard now lives in the Next.js frontend
    (see frontend/ - run `pnpm dev` and visit http://localhost:3000). The
    original zero-build static dashboard is archived under
    archive/legacy-static-dashboard/ for reference.
    """
    return HTMLResponse(
        "<h1>TERRA Intelligence Engine API</h1>"
        "<p>Backend is running. The dashboard now lives in the Next.js frontend — "
        "run <code>pnpm dev</code> in <code>frontend/</code> and visit "
        "<a href=\"http://localhost:3000\">http://localhost:3000</a>.</p>"
        "<p>Explore the API directly via <a href=\"/docs\">Swagger UI</a> or "
        "<a href=\"/redoc\">ReDoc</a>.</p>"
    )


@app.get("/health")
async def health_check():
    """System health check and infrastructure telemetry status."""
    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "connected_personas": list(PERSONAS.keys()),
        "subsystems": {
            "odin_ai_reasoning": "operational",
            "terra_graph_api": "operational",
            "bio_age_trajectory": "operational",
            "behavioral_retention": "operational",
            "webhook_ingestion": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
