"""Conexão Híbrida Tripla de Banco de Dados:
1. Servidor da Rede PostgreSQL (`192.168.15.109:5432/erp_mercados_db`)
2. Vercel Cloud Serverless (`/tmp/erp_mercados.db` com auto-seed em memória/tmp)
3. Mídia Local Downloads SQLite (`/media/rodrigo/Downloads/ai-agents/workspace/erp-mercados/database/erp_mercados.db`)
"""

from __future__ import annotations

from collections.abc import Generator
import os
from pathlib import Path
import socket

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

LOCAL_DOWNLOADS_DIR = Path("/media/rodrigo/Downloads/ai-agents/workspace/erp-mercados")
if os.getenv("VERCEL") or not LOCAL_DOWNLOADS_DIR.exists():
    SQLITE_PATH = Path("/tmp/erp_mercados.db")
else:
    SQLITE_PATH = LOCAL_DOWNLOADS_DIR / "database" / "erp_mercados.db"
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

PG_HOST = os.getenv("ERP_PG_HOST", "192.168.15.109")
PG_PORT = int(os.getenv("ERP_PG_PORT", "5432"))
PG_USER = os.getenv("ERP_PG_USER", "rodrigo")
PG_PASS = os.getenv("ERP_PG_PASS", "rodrigo123")
PG_DB = os.getenv("ERP_PG_DB", "erp_mercados_db")


def _postgres_acessivel(host: str, port: int, timeout: float = 1.2) -> bool:
    if os.getenv("ERP_FORCE_SQLITE", "").lower() in ("1", "true", "yes"):
        return False
    if os.getenv("VERCEL") and host.startswith("192.168."):
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def obter_url_banco() -> tuple[str, str]:
    """Retorna (database_url, modo_banco) priorizando PostgreSQL na rede ou SQLite Cloud na Vercel."""
    url_env = os.getenv("DATABASE_URL", "").strip()
    if url_env:
        return url_env, "custom_database_url"

    if _postgres_acessivel(PG_HOST, PG_PORT):
        return (
            f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}",
            f"postgresql ({PG_HOST}:{PG_PORT}/{PG_DB})",
        )

    modo = "vercel_cloud_sqlite (/tmp/erp_mercados.db)" if os.getenv("VERCEL") else f"sqlite ({SQLITE_PATH})"
    return f"sqlite:///{SQLITE_PATH}", modo


DATABASE_URL, DATABASE_MODE = obter_url_banco()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
