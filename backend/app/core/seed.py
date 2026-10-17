"""Inicialização da estrutura de tabelas do banco de dados — HelpDmais."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import inspect

from app.core.database import Base, SessionLocal, engine
from app.models.erp_crm_models import SchemaMeta

VERSAO_SCHEMA = "3.1.0"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def inicializar_e_popular_banco() -> None:
    """Garante que todas as tabelas da versão atual existam no banco de dados."""
    insp = inspect(engine)
    tabelas_existentes = set(insp.get_table_names())

    recriar = False
    if "helpdmais_schema_meta" not in tabelas_existentes or "empresas" not in tabelas_existentes:
        recriar = True
    else:
        db = SessionLocal()
        try:
            meta = (
                db.query(SchemaMeta)
                .filter(SchemaMeta.versao_schema == VERSAO_SCHEMA)
                .first()
            )
            if not meta:
                recriar = True
        except Exception:
            recriar = True
        finally:
            db.close()

    if recriar:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            db.add(
                SchemaMeta(
                    versao_schema=VERSAO_SCHEMA,
                    atualizado_em=_agora_utc(),
                )
            )
            db.commit()
        finally:
            db.close()
    else:
        Base.metadata.create_all(bind=engine)
