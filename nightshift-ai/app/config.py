"""
Chargement de la configuration NightShift.

- Lit config/config.yaml (valeurs par défaut, versionné dans Git)
- Fusionne avec config/config.local.yaml si présent (non versionné, tes réglages perso)
- Ne contient JAMAIS de secret : les secrets sont lus séparément par app/security/secrets.py
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

BASE_DIR = Path(os.environ.get("NIGHTSHIFT_HOME", "/opt/nightshift"))
CONFIG_DIR = BASE_DIR / "config"


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_raw() -> dict:
    default_path = CONFIG_DIR / "config.yaml"
    local_path = CONFIG_DIR / "config.local.yaml"

    if not default_path.exists():
        raise FileNotFoundError(
            f"Fichier de configuration introuvable : {default_path}. "
            "Copie config/config.yaml.example ou vérifie NIGHTSHIFT_HOME."
        )

    with open(default_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            local_data = yaml.safe_load(f) or {}
        data = _deep_merge(data, local_data)

    return data


class ProviderConfig(BaseModel):
    enabled: bool = False
    paid_enabled: bool = False
    base_url: str | None = None
    model: str = ""
    priority: int = 99


class SchedulerConfig(BaseModel):
    retry_interval_minutes: int = 60
    max_retries_before_alert: int = 5


class PerformanceConfig(BaseModel):
    max_parallel_agents: int = 1
    max_memory_usage_mb: int = 3000
    sleep_when_idle: bool = True
    idle_poll_seconds: int = 30


class SecurityConfig(BaseModel):
    linux_user: str = "nightshift"
    workspace_root: str = "/opt/nightshift/projects"
    forbidden_paths: list[str] = Field(default_factory=list)
    command_allowlist: list[str] = Field(default_factory=list)
    require_human_validation_for: list[str] = Field(default_factory=list)


class AlertsConfig(BaseModel):
    disk_percent_threshold: int = 90
    ram_percent_threshold: int = 90
    cpu_percent_threshold: int = 95
    notify_via: str = "log"


class ProjectConfig(BaseModel):
    id: str
    name: str
    workspace: str
    git_remote: str = ""
    agents: list[str] = Field(default_factory=list)


class NightShiftConfig(BaseModel):
    app_name: str = "NightShift AI"
    environment: str = "production"
    timezone: str = "Europe/Paris"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8420

    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "nightshift_db"
    db_user: str = "nightshift_user"

    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    scheduler: SchedulerConfig = SchedulerConfig()
    performance: PerformanceConfig = PerformanceConfig()
    security: SecurityConfig = SecurityConfig()
    alerts: AlertsConfig = AlertsConfig()
    projects: list[ProjectConfig] = Field(default_factory=list)

    @classmethod
    def load(cls) -> "NightShiftConfig":
        raw: dict[str, Any] = _load_raw()
        app = raw.get("app", {})
        db = raw.get("database", {})
        return cls(
            app_name=app.get("name", "NightShift AI"),
            environment=app.get("environment", "production"),
            timezone=app.get("timezone", "Europe/Paris"),
            log_level=app.get("log_level", "INFO"),
            api_host=app.get("api_host", "127.0.0.1"),
            api_port=app.get("api_port", 8420),
            db_host=db.get("host", "127.0.0.1"),
            db_port=db.get("port", 5432),
            db_name=db.get("name", "nightshift_db"),
            db_user=db.get("user", "nightshift_user"),
            providers={k: ProviderConfig(**v) for k, v in raw.get("providers", {}).items()},
            scheduler=SchedulerConfig(**raw.get("scheduler", {})),
            performance=PerformanceConfig(**raw.get("performance", {})),
            security=SecurityConfig(**raw.get("security", {})),
            alerts=AlertsConfig(**raw.get("alerts", {})),
            projects=[ProjectConfig(**p) for p in raw.get("projects", [])],
        )


# Instance globale chargée au démarrage de l'application
settings = NightShiftConfig.load()
