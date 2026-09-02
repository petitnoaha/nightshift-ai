"""API HTTP de NightShift — consommée par le dashboard.
Écoute uniquement en 127.0.0.1 par défaut : l'exposition à Internet passe
exclusivement par Cloudflare Tunnel, jamais en ouvrant un port directement."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import get_session
from app.models import Project
from app.statistics.stats import nightshift_score, project_stats, system_stats

app = FastAPI(title="NightShift AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{settings.api_host}:{settings.api_port}"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status():
    with get_session() as session:
        projects = session.query(Project).all()
        return {
            "app": settings.app_name,
            "projects": [
                {"id": p.id, "name": p.name, "state": p.state.value, "progress_percent": p.progress_percent}
                for p in projects
            ],
        }


@app.get("/api/system")
def get_system():
    return system_stats()


@app.get("/api/projects/{project_id}/stats")
def get_project_stats(project_id: str):
    with get_session() as session:
        if session.get(Project, project_id) is None:
            raise HTTPException(status_code=404, detail="Projet inconnu")
    return project_stats(project_id)


@app.get("/api/projects/{project_id}/score")
def get_project_score(project_id: str):
    return nightshift_score(project_id)


# Le dashboard statique (HTML/JS simple) est servi directement par l'API
app.mount("/", StaticFiles(directory="dashboard", html=True), name="dashboard")
