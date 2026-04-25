"""
Main entrypoint for Face Attendance Service

Responsibilities:
✔ Create FastAPI app
✔ Register routes
✔ Start server
✔ Keep Cloud Run healthy
"""

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
import os

from app.routes import router
from app.auth_routes import router as auth_router
from app.config import HOST, PORT, PROJECT_ROOT
from app.storage import ensure_dirs


# =================================
# Startup / Shutdown
# =================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup tasks only

    IMPORTANT:
    Do NOT create DB tables here for Cloud Run
    because slow startup causes container failure.
    """

    # create required folders
    ensure_dirs()

    yield

    # shutdown tasks (none for now)


# =================================
# FastAPI App
# =================================

app = FastAPI(
    title="Face Attendance Service",
    version="1.0.0",
    description="Offline Face Recognition Attendance System",
    lifespan=lifespan,
)


# =================================
# CORS
# =================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # production me specific domain use karna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================
# Static Frontend
# =================================

frontend_path = os.path.join(PROJECT_ROOT, "Frontend")

if os.path.exists(frontend_path):
    app.mount(
        "/static",
        StaticFiles(directory=frontend_path),
        name="static"
    )


# =================================
# Health Check Route (VERY IMPORTANT)
# Dockerfile healthcheck uses this
# =================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "FastAPI is running"
    }


# =================================
# Root Route
# =================================

@app.get("/")
def root():
    return RedirectResponse(url="/static/login.html")


# =================================
# API Routes
# =================================

app.include_router(auth_router)
app.include_router(router)


# =================================
# Local Development / Production Run
# =================================
if __name__ == "__main__":
    HOST = os.getenv("HOST", "107.178.254.207")   # सभी interfaces पर सुनने के लिए
    PORT = int(os.getenv("PORT", 443))   # default 8080, env से override हो सकता है

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False
    )
