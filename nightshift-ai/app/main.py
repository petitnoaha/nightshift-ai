"""
Point d'entrée de NightShift AI.
Lancé par systemd (voir systemd/nightshift.service) sous l'utilisateur "nightshift".
"""
from __future__ import annotations

import asyncio
import logging
import logging.handlers
import os
from pathlib import Path

import uvicorn

from app.config import settings
from app.database import init_db
from app.orchestrator.orchestrator import ProjectOrchestrator

NIGHTSHIFT_HOME = Path(os.environ.get("NIGHTSHIFT_HOME", "/opt/nightshift"))
LOG_DIR = NIGHTSHIFT_HOME / "logs"


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "nightshift.log", maxBytes=10_000_000, backupCount=5
    )
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],  # StreamHandler -> journald via systemd
    )


async def run_all_projects() -> None:
    orchestrators = [ProjectOrchestrator(p) for p in settings.projects]
    await asyncio.gather(*(o.run_forever() for o in orchestrators))


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("nightshift.main")
    logger.info("Démarrage de NightShift AI (%s projet(s) configuré(s))", len(settings.projects))

    init_db()

    config = uvicorn.Config(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)

    await asyncio.gather(server.serve(), run_all_projects())


if __name__ == "__main__":
    asyncio.run(main())
