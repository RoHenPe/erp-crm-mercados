"""Autenticação, Hash de Senhas e Controle de Sessão por Empresa — HelpDmais."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.erp_crm_models import (
    MATRIZ_PERFIS_RBAC,
    Tenant,
    UsuarioSistema,
    normalizar_perfil,
)

SECRET_KEY = os.getenv("HELPDMAIS_SECRET_KEY", "helpdmais-auth-secret-key-2026-v3")
TOKEN_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 dias


def gerar_hash_senha(senha: str) -> str:
    """Gera hash PBKDF2-HMAC-SHA256 com salt aleatório."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"pbkdf2_sha256$100000${salt}${dk.hex()}"


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Valida uma senha plana contra o hash PBKDF2 armazenado."""
    if not senha_hash or not senha_plana:
        return False
    if not senha_hash.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(senha_plana, senha_hash)
    try:
        _, iter_str, salt, hash_hex = senha_hash.split("$", 3)
        iterations = int(iter_str)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            senha_plana.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def criar_token_sessao(usuario_id: int, tenant_id: int, perfil_rbac: str, email: str) -> str:
    """Gera o token de sessão assinado com o identificador do usuário e da empresa."""
    perfil_norm = normalizar_perfil(perfil_rbac)
    payload = {
        "uid": int(usuario_id),
        "tid": int(tenant_id),
        "role": perfil_norm,
        "email": str(email),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(payload_bytes).decode("ascii").rstrip("=")
    assinatura = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"hdm.{b64_payload}.{assinatura}"


def decodificar_token_sessao(token: str) -> dict[str, Any] | None:
    """Valida a assinatura e a validade temporal do token de sessão."""
    if not token:
        return None
    limpo = token.strip()
    if limpo.lower().startswith("bearer "):
        limpo = limpo[7:].strip()
    partes = limpo.split(".")
    if len(partes) != 3 or partes[0] != "hdm":
        return None
    _, b64_payload, assinatura_recebida = partes
    assinatura_esperada = hmac.new(
        SECRET_KEY.encode("utf-8"),
        b64_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(assinatura_recebida, assinatura_esperada):
        return None
    try:
        padding = "=" * (-len(b64_payload) % 4)
        raw = base64.urlsafe_b64decode((b64_payload + padding).encode("ascii"))
        dados = json.loads(raw.decode("utf-8"))
        if int(dados.get("exp", 0)) < int(time.time()):
            return None
        return dados
    except Exception:
        return None


@dataclass
class ContextoComercio:
    """Contexto da empresa e do usuário autenticados na requisição."""

    tenant_id: int
    tenant: Tenant
    usuario: UsuarioSistema
    perfil_rbac: str
    modulos_permitidos: list[str]
    permissoes_acoes: list[str]


def resolver_contexto_comercio(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_tenant_token: str | None = Header(default=None),
    tenant_id_query: int | None = Query(default=None, alias="tenant_id"),
) -> ContextoComercio:
    """Valida o token de sessão e carrega os dados da empresa autenticada."""
    token_bruto = authorization or x_tenant_token
    if not token_bruto:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão não autenticada. Entre com seu e-mail e senha.",
        )

    payload = decodificar_token_sessao(token_bruto)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão expirada ou inválida. Faça login novamente.",
        )

    tid = int(payload["tid"])
    uid = int(payload["uid"])

    if tenant_id_query is not None and int(tenant_id_query) != tid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não permitido aos dados de outra empresa.",
        )

    tenant = db.query(Tenant).filter(Tenant.id == tid, Tenant.ativo.is_(True)).first()
    usuario = (
        db.query(UsuarioSistema)
        .filter(
            UsuarioSistema.id == uid,
            UsuarioSistema.tenant_id == tid,
            UsuarioSistema.ativo.is_(True),
        )
        .first()
    )
    if not tenant or not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta ou usuário não encontrado ou inativo.",
        )

    perfil_norm = normalizar_perfil(usuario.perfil_rbac)
    info_rbac = MATRIZ_PERFIS_RBAC.get(perfil_norm, MATRIZ_PERFIS_RBAC["CAIXA"])
    return ContextoComercio(
        tenant_id=tenant.id,
        tenant=tenant,
        usuario=usuario,
        perfil_rbac=perfil_norm,
        modulos_permitidos=list(info_rbac["modulos_permitidos"]),
        permissoes_acoes=list(info_rbac["permissoes_acoes"]),
    )


def exigir_permissao_modulo(contexto: ContextoComercio, modulo: str) -> None:
    """Verifica se o cargo do usuário possui acesso ao módulo."""
    if modulo not in contexto.modulos_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Seu cargo ({contexto.perfil_rbac}) não possui permissão para acessar este módulo.",
        )


def exigir_permissao_acao(contexto: ContextoComercio, acao: str) -> None:
    """Verifica se o cargo do usuário possui permissão para executar a ação."""
    if acao not in contexto.permissoes_acoes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu perfil de usuário não possui permissão para realizar esta operação.",
        )
