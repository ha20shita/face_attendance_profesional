"""
Main entrypoint for Face Attendance Service

Responsibilities:
✔ Create FastAPI app
✔ Register routes
✔ Initialize database tables automatically
✔ Start server
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

# ✅ Database
from app.db import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Startup: ensure folders + create tables
    ensure_dirs()
    Base.metadata.create_all(bind=engine)
    yield
    # ✅ Shutdown: nothing needed for now


app = FastAPI(
    title="Face Attendance Service",
    version="1.0.0",
    description="Offline Face Recognition Attendance System",
    lifespan=lifespan,
)

# ✅ CORS (client app / browser integration safe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later production me specific domains rakhna
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Static files (Frontend)
frontend_path = os.path.join(PROJECT_ROOT, "Frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ✅ Root redirect to login page
@app.get("/")
def root():
    return RedirectResponse(url="/static/login.html")

# ✅ Routes
app.include_router(auth_router)
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,  # client delivery: stable
    )
