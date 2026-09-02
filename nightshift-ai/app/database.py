"""Connexion à PostgreSQL via SQLAlchemy."""
from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings
from app.security.secrets import get_secret


class Base(DeclarativeBase):
    pass


def _build_url() -> str:
    password = get_secret("db_password") or ""
    return (
        f"postgresql+psycopg2://{settings.db_user}:{password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


engine = create_engine(_build_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Crée les tables si elles n'existent pas encore (appelé au premier démarrage)."""
    import app.models  # noqa: F401 (enregistre les modèles auprès de Base)
    Base.metadata.create_all(bind=engine)
