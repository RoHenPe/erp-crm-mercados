"""API Principal do Sistema HelpDmais — Gestão Empresarial (ERP, CRM e PDV)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ContextoComercio,
    criar_token_sessao,
    exigir_permissao_acao,
    exigir_permissao_modulo,
    gerar_hash_senha,
    resolver_contexto_comercio,
    verificar_senha,
)
from app.models.erp_crm_models import (
    MATRIZ_PERFIS_RBAC,
    CampanhaCRM,
    ClienteCRM,
    EstoqueFilial,
    Filial,
    Fornecedor,
    ItemVendaPDV,
    LancamentoFinanceiro,
    LoteValidade,
    MovimentacaoEstoque,
    PedidoCompra,
    Produto,
    SessaoCaixaPDV,
    Tenant,
    TransacaoCashback,
    UsuarioSistema,
    VendaPDV,
    normalizar_perfil,
)
from app.schemas.erp_crm_schemas import (
    CampanhaCRMCreate,
    CampanhaCRMResponse,
    ClienteCRMCreate,
    ClienteCRMResponse,
    DREResponse,
    EstoqueMovimentoRequest,
    EstoqueTransferenciaRequest,
    FilialCreate,
    FilialResponse,
    FornecedorCreate,
    FornecedorResponse,
    LancamentoFinanceiroCreate,
    LancamentoFinanceiroResponse,
    LoginRequest,
    LoginResponse,
    PedidoCompraCreate,
    PedidoCompraResponse,
    PerfilRBACInfo,
    ProdutoCreate,
    ProdutoResponse,
    RegistroComercioRequest,
    SessaoCaixaAbrirRequest,
    SessaoCaixaFecharRequest,
    SessaoCaixaResponse,
    TenantResponse,
    UsuarioCreate,
    UsuarioResponse,
    UsuarioUpdateStatus,
    VendaPDVRequest,
    VendaPDVResponse,
)
from app.services.regras_negocio import (
    gerar_dre_gerencial,
    movimentar_estoque,
    processar_venda_pdv,
    receber_pedido_compra,
    transferir_estoque,
)

BASE_PROJECT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_PROJECT_DIR / "frontend"


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _garantir_banco_inicializado() -> None:
    try:
        from app.core.seed import inicializar_e_popular_banco

        inicializar_e_popular_banco()
    except Exception as exc:
        print(f"[Startup] Aviso ao inicializar estrutura do banco: {exc}")
        from app.core.database import Base, engine

        Base.metadata.create_all(bind=engine)


_garantir_banco_inicializado()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _garantir_banco_inicializado()
    yield


app = FastAPI(
    title="HelpDmais — Gestão Empresarial (ERP, CRM & PDV)",
    version="3.1.0",
    description="Plataforma Integrada de Gestão de Varejo, Estoque, Compras, PDV, CRM e Financeiro",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _gerar_slug(texto: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", texto.strip().lower()).strip("-")
    return base or "empresa"


def _serializar_tenant(db: Session, tenant: Tenant) -> TenantResponse:
    total_filiais = db.query(Filial).filter(Filial.tenant_id == tenant.id).count()
    total_usuarios = (
        db.query(UsuarioSistema).filter(UsuarioSistema.tenant_id == tenant.id).count()
    )
    total_produtos = db.query(Produto).filter(Produto.tenant_id == tenant.id).count()
    total_clientes = (
        db.query(ClienteCRM).filter(ClienteCRM.tenant_id == tenant.id).count()
    )
    return TenantResponse(
        id=tenant.id,
        slug=tenant.slug,
        nome_fantasia=tenant.nome_fantasia,
        razao_social=tenant.razao_social,
        cnpj_matriz=tenant.cnpj_matriz,
        segmento_varejo=tenant.segmento_varejo,
        cidade_uf=tenant.cidade_uf,
        telefone=tenant.telefone,
        cor_tema=tenant.cor_tema,
        ativo=tenant.ativo,
        total_filiais=total_filiais,
        total_usuarios=total_usuarios,
        total_produtos=total_produtos,
        total_clientes_crm=total_clientes,
        criado_em=tenant.criado_em,
    )


def _serializar_usuario(
    db: Session, usuario: UsuarioSistema, tenant: Tenant | None = None
) -> UsuarioResponse:
    if not tenant:
        tenant = db.query(Tenant).filter(Tenant.id == usuario.tenant_id).first()
    filial = None
    if usuario.filial_id:
        filial = (
            db.query(Filial)
            .filter(Filial.id == usuario.filial_id, Filial.tenant_id == usuario.tenant_id)
            .first()
        )
    perfil_norm = normalizar_perfil(usuario.perfil_rbac)
    info_rbac = MATRIZ_PERFIS_RBAC.get(perfil_norm, MATRIZ_PERFIS_RBAC["CAIXA"])
    return UsuarioResponse(
        id=usuario.id,
        tenant_id=usuario.tenant_id,
        tenant_nome=tenant.nome_fantasia if tenant else None,
        filial_id=usuario.filial_id,
        filial_nome=filial.nome if filial else "Todas as Unidades",
        nome=usuario.nome,
        email=usuario.email,
        cargo=usuario.cargo,
        perfil_rbac=perfil_norm,
        modulos_permitidos=list(info_rbac["modulos_permitidos"]),
        permissoes_acoes=list(info_rbac["permissoes_acoes"]),
        nivel_acesso=int(info_rbac["nivel_acesso"]),
        ativo=usuario.ativo,
        ultimo_acesso=usuario.ultimo_acesso,
        criado_em=usuario.criado_em,
    )


# ===========================================================================
# 1. Status do Serviço & Perfis de Acesso
# ===========================================================================
@app.get("/api/health", tags=["Sistema"])
def health_check():
    """Retorna o status operacional da aplicação."""
    return {
        "status": "online",
        "sistema": "HelpDmais",
        "versao": "3.1.0",
        "timestamp": _agora_utc().isoformat(),
    }


@app.get("/api/perfis-acesso", response_model=list[PerfilRBACInfo], tags=["Autenticação & Equipe"])
def listar_perfis_acesso():
    """Lista os cargos e permissões disponíveis para cadastro de usuários."""
    return [PerfilRBACInfo(**dados) for dados in MATRIZ_PERFIS_RBAC.values()]


# ===========================================================================
# 2. Registro de Empresa (Onboarding), Login & Sessão
# ===========================================================================
@app.post(
    "/api/auth/registrar-comercio",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Autenticação & Equipe"],
)
def registrar_comercio(req: RegistroComercioRequest, db: Session = Depends(get_db)):
    """Cadastra uma nova Empresa, sua Unidade Matriz e seu usuário Administrador."""
    email_norm = req.admin_email.strip().lower()
    cnpj_limpo = req.cnpj_matriz.strip()

    if db.query(UsuarioSistema).filter(func.lower(UsuarioSistema.email) == email_norm).first():
        raise HTTPException(
            status_code=400,
            detail="Este e-mail já está em uso por outra conta.",
        )

    if db.query(Tenant).filter(Tenant.cnpj_matriz == cnpj_limpo).first():
        raise HTTPException(
            status_code=400,
            detail="Já existe uma empresa cadastrada com este CNPJ.",
        )

    slug_base = _gerar_slug(req.nome_fantasia)
    slug_final = slug_base
    contador = 2
    while db.query(Tenant).filter(Tenant.slug == slug_final).first():
        slug_final = f"{slug_base}-{contador}"
        contador += 1

    novo_tenant = Tenant(
        slug=slug_final,
        nome_fantasia=req.nome_fantasia.strip(),
        razao_social=req.razao_social.strip(),
        cnpj_matriz=cnpj_limpo,
        segmento_varejo=req.segmento_varejo.strip() or "Supermercado & Varejo",
        cidade_uf=req.cidade_uf.strip(),
        telefone=req.telefone.strip(),
        cor_tema=req.cor_tema.strip() or "#714B67",
        ativo=True,
        criado_em=_agora_utc(),
    )
    db.add(novo_tenant)
    db.flush()

    filial_matriz = Filial(
        tenant_id=novo_tenant.id,
        codigo=req.codigo_filial_matriz.strip().upper() or "MATRIZ-01",
        nome=req.nome_filial_matriz.strip() or "Matriz Principal",
        bandeira=req.bandeira_matriz.strip() or "Matriz",
        cnpj=cnpj_limpo,
        cidade=req.cidade_uf.strip(),
        gerente=req.admin_nome.strip(),
        meta_mensal=float(req.meta_mensal_matriz or 150000.0),
        ativa=True,
    )
    db.add(filial_matriz)
    db.flush()

    info_admin = MATRIZ_PERFIS_RBAC["ADMINISTRADOR"]
    usuario_admin = UsuarioSistema(
        tenant_id=novo_tenant.id,
        filial_id=None,
        nome=req.admin_nome.strip(),
        email=email_norm,
        cargo=req.admin_cargo.strip() or "Proprietário / Administrador",
        perfil_rbac="ADMINISTRADOR",
        modulos_permitidos=",".join(info_admin["modulos_permitidos"]),
        nivel_acesso=info_admin["nivel_acesso"],
        senha_hash=gerar_hash_senha(req.admin_senha),
        ativo=True,
        ultimo_acesso=_agora_utc(),
        criado_em=_agora_utc(),
    )
    db.add(usuario_admin)
    db.commit()
    db.refresh(novo_tenant)
    db.refresh(filial_matriz)
    db.refresh(usuario_admin)

    token = criar_token_sessao(
        usuario_id=usuario_admin.id,
        tenant_id=novo_tenant.id,
        perfil_rbac="ADMINISTRADOR",
        email=usuario_admin.email,
    )

    return LoginResponse(
        autenticado=True,
        token_sessao=token,
        usuario=_serializar_usuario(db, usuario_admin, novo_tenant),
        tenant=_serializar_tenant(db, novo_tenant),
        filiais=[FilialResponse.model_validate(filial_matriz)],
        perfil_detalhes=PerfilRBACInfo(**info_admin),
        mensagem=f"Empresa '{novo_tenant.nome_fantasia}' criada com sucesso.",
    )


@app.post("/api/auth/login", response_model=LoginResponse, tags=["Autenticação & Equipe"])
def login_usuario(req: LoginRequest, db: Session = Depends(get_db)):
    """Autentica um usuário pelo e-mail e senha e retorna o contexto isolado da sua Empresa."""
    email_norm = req.email.strip().lower()
    usuario = (
        db.query(UsuarioSistema)
        .filter(func.lower(UsuarioSistema.email) == email_norm)
        .first()
    )
    if not usuario or not verificar_senha(req.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este usuário está desativado. Contate o administrador da empresa.",
        )

    tenant = (
        db.query(Tenant)
        .filter(Tenant.id == usuario.tenant_id, Tenant.ativo.is_(True))
        .first()
    )
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A conta da empresa associada a este usuário está inativa.",
        )

    usuario.ultimo_acesso = _agora_utc()
    db.commit()
    db.refresh(usuario)

    perfil_norm = normalizar_perfil(usuario.perfil_rbac)
    info_rbac = MATRIZ_PERFIS_RBAC.get(perfil_norm, MATRIZ_PERFIS_RBAC["CAIXA"])
    token = criar_token_sessao(
        usuario_id=usuario.id,
        tenant_id=tenant.id,
        perfil_rbac=perfil_norm,
        email=usuario.email,
    )

    filiais_db = (
        db.query(Filial)
        .filter(Filial.tenant_id == tenant.id)
        .order_by(Filial.id.asc())
        .all()
    )

    return LoginResponse(
        autenticado=True,
        token_sessao=token,
        usuario=_serializar_usuario(db, usuario, tenant),
        tenant=_serializar_tenant(db, tenant),
        filiais=[FilialResponse.model_validate(f) for f in filiais_db],
        perfil_detalhes=PerfilRBACInfo(**info_rbac),
        mensagem=f"Bem-vindo(a), {usuario.nome}!",
    )


@app.get("/api/auth/me", response_model=LoginResponse, tags=["Autenticação & Equipe"])
def obter_sessao_atual(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna os dados atualizados do usuário e da empresa autenticada."""
    info_rbac = MATRIZ_PERFIS_RBAC.get(
        contexto.perfil_rbac, MATRIZ_PERFIS_RBAC["CAIXA"]
    )
    filiais_db = (
        db.query(Filial)
        .filter(Filial.tenant_id == contexto.tenant_id)
        .order_by(Filial.id.asc())
        .all()
    )
    token_renovado = criar_token_sessao(
        usuario_id=contexto.usuario.id,
        tenant_id=contexto.tenant_id,
        perfil_rbac=contexto.perfil_rbac,
        email=contexto.usuario.email,
    )
    return LoginResponse(
        autenticado=True,
        token_sessao=token_renovado,
        usuario=_serializar_usuario(db, contexto.usuario, contexto.tenant),
        tenant=_serializar_tenant(db, contexto.tenant),
        filiais=[FilialResponse.model_validate(f) for f in filiais_db],
        perfil_detalhes=PerfilRBACInfo(**info_rbac),
        mensagem="Sessão ativa.",
    )


# ===========================================================================
# 3. Gestão da Empresa e Equipe (Usuários e Cargos)
# ===========================================================================
@app.get("/api/empresa", response_model=TenantResponse, tags=["Empresa & Equipe"])
def obter_dados_empresa(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna os dados cadastrais da empresa autenticada."""
    return _serializar_tenant(db, contexto.tenant)


@app.get("/api/usuarios", response_model=list[UsuarioResponse], tags=["Empresa & Equipe"])
def listar_usuarios_empresa(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista exclusivamente os usuários da empresa autenticada."""
    usuarios = (
        db.query(UsuarioSistema)
        .filter(UsuarioSistema.tenant_id == contexto.tenant_id)
        .order_by(UsuarioSistema.id.asc())
        .all()
    )
    return [_serializar_usuario(db, u, contexto.tenant) for u in usuarios]


@app.post(
    "/api/usuarios",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Empresa & Equipe"],
)
def criar_usuario_empresa(
    user_in: UsuarioCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cadastra um novo funcionário na empresa autenticada com cargo e permissões específicas."""
    exigir_permissao_acao(contexto, "GERENCIAR_USUARIOS")

    email_norm = user_in.email.strip().lower()
    if db.query(UsuarioSistema).filter(func.lower(UsuarioSistema.email) == email_norm).first():
        raise HTTPException(
            status_code=400, detail="Já existe um usuário cadastrado com este e-mail."
        )

    if user_in.filial_id is not None:
        filial = (
            db.query(Filial)
            .filter(
                Filial.id == user_in.filial_id,
                Filial.tenant_id == contexto.tenant_id,
            )
            .first()
        )
        if not filial:
            raise HTTPException(
                status_code=400, detail="Unidade selecionada não pertence a esta empresa."
            )

    perfil_norm = normalizar_perfil(user_in.perfil_rbac)
    info_rbac = MATRIZ_PERFIS_RBAC[perfil_norm]

    novo_usuario = UsuarioSistema(
        tenant_id=contexto.tenant_id,
        filial_id=user_in.filial_id,
        nome=user_in.nome.strip(),
        email=email_norm,
        cargo=user_in.cargo.strip(),
        perfil_rbac=perfil_norm,
        modulos_permitidos=",".join(info_rbac["modulos_permitidos"]),
        nivel_acesso=info_rbac["nivel_acesso"],
        senha_hash=gerar_hash_senha(user_in.senha),
        ativo=user_in.ativo,
        criado_em=_agora_utc(),
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return _serializar_usuario(db, novo_usuario, contexto.tenant)


@app.patch(
    "/api/usuarios/{usuario_id}",
    response_model=UsuarioResponse,
    tags=["Empresa & Equipe"],
)
def atualizar_usuario_empresa(
    usuario_id: int,
    upd: UsuarioUpdateStatus,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Atualiza cargo, unidade, status ou senha de um funcionário da mesma empresa."""
    exigir_permissao_acao(contexto, "GERENCIAR_USUARIOS")

    usuario = (
        db.query(UsuarioSistema)
        .filter(
            UsuarioSistema.id == usuario_id,
            UsuarioSistema.tenant_id == contexto.tenant_id,
        )
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado nesta empresa.")

    if upd.perfil_rbac is not None:
        perfil_norm = normalizar_perfil(upd.perfil_rbac)
        info_rbac = MATRIZ_PERFIS_RBAC[perfil_norm]
        usuario.perfil_rbac = perfil_norm
        usuario.modulos_permitidos = ",".join(info_rbac["modulos_permitidos"])
        usuario.nivel_acesso = info_rbac["nivel_acesso"]

    if upd.cargo is not None:
        usuario.cargo = upd.cargo.strip()
    if upd.filial_id is not None:
        if upd.filial_id == 0:
            usuario.filial_id = None
        else:
            f = (
                db.query(Filial)
                .filter(
                    Filial.id == upd.filial_id,
                    Filial.tenant_id == contexto.tenant_id,
                )
                .first()
            )
            if not f:
                raise HTTPException(status_code=400, detail="Unidade inválida.")
            usuario.filial_id = f.id
    if upd.ativo is not None:
        usuario.ativo = upd.ativo
    if upd.nova_senha and len(upd.nova_senha.strip()) >= 6:
        usuario.senha_hash = gerar_hash_senha(upd.nova_senha.strip())

    db.commit()
    db.refresh(usuario)
    return _serializar_usuario(db, usuario, contexto.tenant)


# ===========================================================================
# 4. Painel de Indicadores (Dashboard)
# ===========================================================================
@app.get("/api/dashboard/resumo", tags=["Painel"])
def dashboard_resumo(
    filial_id: int | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna os indicadores reais da Empresa autenticada."""
    hoje = date.today()
    tid = contexto.tenant_id

    dre = gerar_dre_gerencial(db, tenant_id=tid, filial_id=filial_id)
    faturamento_total = dre["receita_bruta"]
    lucro_liquido = dre["ebitda_lucro_liquido"]

    total_produtos = db.query(Produto).filter(Produto.tenant_id == tid).count()
    total_fornecedores = db.query(Fornecedor).filter(Fornecedor.tenant_id == tid).count()
    total_clientes = db.query(ClienteCRM).filter(ClienteCRM.tenant_id == tid).count()
    cashback_circulacao = round(
        float(
            db.query(func.coalesce(func.sum(ClienteCRM.saldo_cashback), 0.0))
            .filter(ClienteCRM.tenant_id == tid)
            .scalar()
        ),
        2,
    )

    alertas_q = (
        db.query(EstoqueFilial, Produto, Filial)
        .join(Produto, EstoqueFilial.produto_id == Produto.id)
        .join(Filial, EstoqueFilial.filial_id == Filial.id)
        .filter(
            EstoqueFilial.tenant_id == tid,
            EstoqueFilial.quantidade_atual <= EstoqueFilial.estoque_minimo,
        )
    )
    if filial_id is not None:
        alertas_q = alertas_q.filter(EstoqueFilial.filial_id == filial_id)
    alertas_db = alertas_q.all()

    alertas_ruptura = [
        {
            "filial_id": ef.filial_id,
            "filial_nome": filial.nome,
            "produto_id": ef.produto_id,
            "produto_nome": prod.nome,
            "sku": prod.sku,
            "departamento": prod.departamento,
            "quantidade_atual": ef.quantidade_atual,
            "estoque_minimo": ef.estoque_minimo,
            "status": "RUPTURA" if ef.quantidade_atual <= 0 else "CRITICO",
        }
        for ef, prod, filial in alertas_db
    ]

    limite_validade = hoje + timedelta(days=15)
    lotes_q = (
        db.query(LoteValidade, Produto, Filial)
        .join(Produto, LoteValidade.produto_id == Produto.id)
        .join(Filial, LoteValidade.filial_id == Filial.id)
        .filter(
            LoteValidade.tenant_id == tid,
            LoteValidade.quantidade_lote > 0,
            LoteValidade.data_validade <= limite_validade,
        )
    )
    if filial_id is not None:
        lotes_q = lotes_q.filter(LoteValidade.filial_id == filial_id)
    lotes_vencendo_db = lotes_q.order_by(LoteValidade.data_validade.asc()).all()

    lotes_vencendo = [
        {
            "lote_id": lote.id,
            "numero_lote": lote.numero_lote,
            "filial_id": filial.id,
            "filial_nome": filial.nome,
            "produto_id": prod.id,
            "produto_nome": prod.nome,
            "departamento": prod.departamento,
            "quantidade_lote": lote.quantidade_lote,
            "data_validade": lote.data_validade.isoformat(),
            "dias_para_vencer": (lote.data_validade - hoje).days,
            "status_lote": lote.status_lote,
        }
        for lote, prod, filial in lotes_vencendo_db
    ]

    filiais = (
        db.query(Filial)
        .filter(Filial.tenant_id == tid)
        .order_by(Filial.id.asc())
        .all()
    )
    vendas_por_filial = []
    for f in filiais:
        rec_f = (
            db.query(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0.0))
            .filter(
                LancamentoFinanceiro.tenant_id == tid,
                LancamentoFinanceiro.filial_id == f.id,
                (LancamentoFinanceiro.tipo == "RECEITA")
                | (LancamentoFinanceiro.categoria_dre == "RECEITA_VENDAS"),
            )
            .scalar()
        )
        rec_f_val = round(float(rec_f), 2)
        atingimento = (
            round((rec_f_val / f.meta_mensal * 100.0), 2) if f.meta_mensal > 0 else 0.0
        )
        vendas_por_filial.append(
            {
                "filial_id": f.id,
                "tenant_id": tid,
                "nome": f.nome,
                "bandeira": f.bandeira,
                "vendas_mes": rec_f_val,
                "meta_mensal": f.meta_mensal,
                "atingimento_pct": atingimento,
            }
        )

    top_q = (
        db.query(
            ItemVendaPDV.produto_id,
            Produto.nome,
            Produto.departamento,
            func.sum(ItemVendaPDV.quantidade).label("total_qtd"),
            func.sum(ItemVendaPDV.subtotal_item).label("total_faturado"),
        )
        .join(Produto, ItemVendaPDV.produto_id == Produto.id)
        .join(VendaPDV, ItemVendaPDV.venda_id == VendaPDV.id)
        .filter(ItemVendaPDV.tenant_id == tid)
    )
    if filial_id is not None:
        top_q = top_q.filter(VendaPDV.filial_id == filial_id)
    top_itens = (
        top_q.group_by(ItemVendaPDV.produto_id, Produto.nome, Produto.departamento)
        .order_by(desc("total_qtd"))
        .limit(5)
        .all()
    )
    top_5_produtos = [
        {
            "produto_id": row[0],
            "nome": row[1],
            "departamento": row[2],
            "quantidade_vendida": round(float(row[3]), 2),
            "total_faturado": round(float(row[4]), 2),
        }
        for row in top_itens
    ]

    ultimas_q = (
        db.query(VendaPDV, Filial, ClienteCRM)
        .join(Filial, VendaPDV.filial_id == Filial.id)
        .outerjoin(ClienteCRM, VendaPDV.cliente_id == ClienteCRM.id)
        .filter(VendaPDV.tenant_id == tid)
    )
    if filial_id is not None:
        ultimas_q = ultimas_q.filter(VendaPDV.filial_id == filial_id)
    ultimas_vendas_db = ultimas_q.order_by(VendaPDV.criada_em.desc()).limit(10).all()

    ultimas_vendas = [
        {
            "venda_id": v.id,
            "numero_cupom": v.numero_cupom,
            "filial_nome": fil.nome,
            "cliente_nome": cli.nome if cli else "Consumidor Final",
            "subtotal_bruto": v.subtotal_bruto,
            "desconto_clube_crm": v.desconto_clube_crm,
            "cashback_utilizado": v.cashback_utilizado,
            "valor_total_liquido": v.valor_total_liquido,
            "cashback_gerado": v.cashback_gerado,
            "forma_pagamento": v.forma_pagamento,
            "criada_em": v.criada_em.isoformat(),
        }
        for v, fil, cli in ultimas_vendas_db
    ]

    return {
        "software_nome": "HelpDmais",
        "tenant_ativo_id": tid,
        "tenant_ativo_nome": contexto.tenant.nome_fantasia,
        "faturamento_total": faturamento_total,
        "lucro_liquido": lucro_liquido,
        "total_produtos": total_produtos,
        "total_fornecedores": total_fornecedores,
        "total_clientes_crm": total_clientes,
        "cashback_em_circulacao": cashback_circulacao,
        "alertas_ruptura": alertas_ruptura,
        "lotes_vencendo_15_dias": lotes_vencendo,
        "vendas_por_filial_vs_meta": vendas_por_filial,
        "top_5_produtos": top_5_produtos,
        "ultimas_vendas": ultimas_vendas,
    }


# ===========================================================================
# 5. Unidades / Filiais
# ===========================================================================
@app.get("/api/filiais", response_model=list[FilialResponse], tags=["Unidades"])
def listar_filiais(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista todas as unidades pertencentes à empresa autenticada."""
    return (
        db.query(Filial)
        .filter(Filial.tenant_id == contexto.tenant_id)
        .order_by(Filial.id.asc())
        .all()
    )


@app.post(
    "/api/filiais",
    response_model=FilialResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Unidades"],
)
def criar_filial(
    filial_in: FilialCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cadastra uma nova unidade/loja na empresa autenticada."""
    exigir_permissao_acao(contexto, "GERENCIAR_UNIDADES")
    tid = contexto.tenant_id

    existente = (
        db.query(Filial)
        .filter(
            Filial.tenant_id == tid,
            (Filial.codigo == filial_in.codigo.strip().upper())
            | (Filial.cnpj == filial_in.cnpj.strip()),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Já existe uma unidade com este código ou CNPJ na sua empresa.",
        )

    nova = Filial(
        tenant_id=tid,
        codigo=filial_in.codigo.strip().upper(),
        nome=filial_in.nome.strip(),
        bandeira=filial_in.bandeira.strip() or "Loja",
        cnpj=filial_in.cnpj.strip(),
        cidade=filial_in.cidade.strip(),
        gerente=filial_in.gerente.strip(),
        meta_mensal=filial_in.meta_mensal,
        ativa=filial_in.ativa,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


# ===========================================================================
# 6. Fornecedores
# ===========================================================================
@app.get("/api/fornecedores", response_model=list[FornecedorResponse], tags=["Compras & Fornecedores"])
def listar_fornecedores(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista os fornecedores cadastrados pela empresa autenticada."""
    return (
        db.query(Fornecedor)
        .filter(Fornecedor.tenant_id == contexto.tenant_id)
        .order_by(Fornecedor.id.asc())
        .all()
    )


@app.post(
    "/api/fornecedores",
    response_model=FornecedorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Compras & Fornecedores"],
)
def criar_fornecedor(
    forn_in: FornecedorCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cadastra um novo fornecedor na empresa autenticada."""
    exigir_permissao_acao(contexto, "GERENCIAR_PRODUTOS")
    tid = contexto.tenant_id

    existente = (
        db.query(Fornecedor)
        .filter(
            Fornecedor.tenant_id == tid,
            Fornecedor.cnpj == forn_in.cnpj.strip(),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400, detail="Fornecedor já cadastrado com este CNPJ na sua empresa."
        )

    novo = Fornecedor(
        tenant_id=tid,
        razao_social=forn_in.razao_social.strip(),
        nome_fantasia=forn_in.nome_fantasia.strip(),
        cnpj=forn_in.cnpj.strip(),
        categoria_principal=forn_in.categoria_principal.strip(),
        prazo_entrega_dias=forn_in.prazo_entrega_dias,
        telefone=forn_in.telefone.strip(),
        email=forn_in.email.strip(),
        avaliacao=forn_in.avaliacao,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ===========================================================================
# 7. Produtos & Catálogo
# ===========================================================================
@app.get("/api/produtos", response_model=list[ProdutoResponse], tags=["Estoque & Produtos"])
def listar_produtos(
    departamento: str | None = Query(default=None),
    busca: str | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista o catálogo de produtos exclusivo da empresa autenticada."""
    query = db.query(Produto).filter(Produto.tenant_id == contexto.tenant_id)
    if departamento:
        query = query.filter(Produto.departamento.ilike(f"%{departamento}%"))
    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            (Produto.nome.ilike(termo))
            | (Produto.sku.ilike(termo))
            | (Produto.ean.ilike(termo))
        )
    return query.order_by(Produto.nome.asc()).all()


@app.post(
    "/api/produtos",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Estoque & Produtos"],
)
def criar_produto(
    prod_in: ProdutoCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cadastra um novo produto no catálogo da empresa e opcionalmente registra seu estoque inicial."""
    exigir_permissao_acao(contexto, "GERENCIAR_PRODUTOS")
    tid = contexto.tenant_id

    sku_norm = prod_in.sku.strip().upper()
    ean_norm = prod_in.ean.strip()

    existente = (
        db.query(Produto)
        .filter(
            Produto.tenant_id == tid,
            (Produto.sku == sku_norm) | (Produto.ean == ean_norm),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400,
            detail="Já existe um produto com este código SKU ou código de barras (EAN) na sua empresa.",
        )

    if prod_in.fornecedor_id is not None:
        forn = (
            db.query(Fornecedor)
            .filter(
                Fornecedor.id == prod_in.fornecedor_id,
                Fornecedor.tenant_id == tid,
            )
            .first()
        )
        if not forn:
            raise HTTPException(
                status_code=400, detail="Fornecedor selecionado não pertence à sua empresa."
            )

    preco_clube = (
        prod_in.preco_clube_crm
        if prod_in.preco_clube_crm is not None
        else prod_in.preco_venda
    )

    novo = Produto(
        tenant_id=tid,
        sku=sku_norm,
        ean=ean_norm,
        nome=prod_in.nome.strip(),
        departamento=prod_in.departamento.strip(),
        unidade=prod_in.unidade.strip().upper() or "UN",
        preco_custo=round(float(prod_in.preco_custo), 2),
        preco_venda=round(float(prod_in.preco_venda), 2),
        preco_clube_crm=round(float(preco_clube), 2),
        cashback_percentual=round(float(prod_in.cashback_percentual), 2),
        estoque_minimo_padrao=round(float(prod_in.estoque_minimo_padrao), 2),
        fornecedor_id=prod_in.fornecedor_id,
        perecivel=prod_in.perecivel,
        ativo=prod_in.ativo,
    )
    db.add(novo)
    db.flush()

    # Inicializa posição de estoque para as unidades da empresa
    filiais_empresa = db.query(Filial).filter(Filial.tenant_id == tid).all()
    filial_alvo_id = prod_in.filial_inicial_id or (
        filiais_empresa[0].id if filiais_empresa else None
    )

    for fil in filiais_empresa:
        qtd_ini = (
            round(float(prod_in.estoque_inicial), 3)
            if (fil.id == filial_alvo_id and prod_in.estoque_inicial > 0)
            else 0.0
        )
        db.add(
            EstoqueFilial(
                tenant_id=tid,
                filial_id=fil.id,
                produto_id=novo.id,
                quantidade_atual=qtd_ini,
                estoque_minimo=novo.estoque_minimo_padrao,
                estoque_maximo=max(500.0, qtd_ini * 2),
                ultima_atualizacao=_agora_utc(),
            )
        )
        if qtd_ini > 0:
            lote_num = (
                prod_in.numero_lote_inicial.strip()
                if prod_in.numero_lote_inicial
                else f"INI-{novo.sku}-{date.today().strftime('%Y%m%d')}"
            )
            validade = prod_in.data_validade_inicial or (
                date.today() + timedelta(days=60 if novo.perecivel else 365)
            )
            db.add(
                LoteValidade(
                    tenant_id=tid,
                    filial_id=fil.id,
                    produto_id=novo.id,
                    numero_lote=lote_num,
                    data_fabricacao=date.today(),
                    data_validade=validade,
                    quantidade_lote=qtd_ini,
                    status_lote="ATIVO",
                )
            )
            db.add(
                MovimentacaoEstoque(
                    tenant_id=tid,
                    filial_id=fil.id,
                    produto_id=novo.id,
                    usuario_id=contexto.usuario.id,
                    tipo="ENTRADA_INICIAL",
                    quantidade=qtd_ini,
                    observacao="Saldo inicial no cadastro do produto",
                    criado_em=_agora_utc(),
                )
            )

    db.commit()
    db.refresh(novo)
    return novo


# ===========================================================================
# 8. Estoque, Lotes e Transferências
# ===========================================================================
@app.get("/api/estoque", tags=["Estoque & Produtos"])
def consultar_estoque(
    filial_id: int | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna a posição de estoque e lotes das unidades da empresa autenticada."""
    hoje = date.today()
    tid = contexto.tenant_id

    query = (
        db.query(EstoqueFilial, Produto, Filial)
        .join(Produto, EstoqueFilial.produto_id == Produto.id)
        .join(Filial, EstoqueFilial.filial_id == Filial.id)
        .filter(EstoqueFilial.tenant_id == tid)
    )
    if filial_id is not None:
        query = query.filter(EstoqueFilial.filial_id == filial_id)

    linhas = query.order_by(Filial.id.asc(), Produto.nome.asc()).all()

    resultado = []
    for ef, prod, fil in linhas:
        if ef.quantidade_atual <= 0:
            status_estoque = "RUPTURA"
        elif ef.quantidade_atual <= ef.estoque_minimo:
            status_estoque = "CRITICO"
        else:
            status_estoque = "NORMAL"

        lotes_db = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.tenant_id == tid,
                LoteValidade.filial_id == ef.filial_id,
                LoteValidade.produto_id == ef.produto_id,
                LoteValidade.quantidade_lote > 0,
            )
            .order_by(LoteValidade.data_validade.asc())
            .all()
        )

        lotes = [
            {
                "id": l.id,
                "tenant_id": tid,
                "filial_id": l.filial_id,
                "produto_id": l.produto_id,
                "numero_lote": l.numero_lote,
                "data_fabricacao": l.data_fabricacao.isoformat(),
                "data_validade": l.data_validade.isoformat(),
                "quantidade_lote": l.quantidade_lote,
                "status_lote": l.status_lote,
                "dias_para_vencer": (lote.data_validade - hoje).days
                if (lote := l)
                else 0,
            }
            for l in lotes_db
        ]

        resultado.append(
            {
                "id": ef.id,
                "tenant_id": tid,
                "filial_id": ef.filial_id,
                "filial_nome": fil.nome,
                "produto_id": ef.produto_id,
                "produto_nome": prod.nome,
                "produto_sku": prod.sku,
                "produto_ean": prod.ean,
                "departamento": prod.departamento,
                "unidade": prod.unidade,
                "preco_custo": prod.preco_custo,
                "preco_venda": prod.preco_venda,
                "preco_clube_crm": prod.preco_clube_crm,
                "quantidade_atual": ef.quantidade_atual,
                "estoque_minimo": ef.estoque_minimo,
                "estoque_maximo": ef.estoque_maximo,
                "status": status_estoque,
                "lotes_validade": lotes,
                "ultima_atualizacao": (
                    ef.ultima_atualizacao.isoformat() if ef.ultima_atualizacao else None
                ),
            }
        )

    return resultado


@app.post("/api/estoque/movimentar", tags=["Estoque & Produtos"])
def endpoint_movimentar_estoque(
    mov_in: EstoqueMovimentoRequest,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Registra entrada de mercadoria, ajuste ou baixa por perda."""
    exigir_permissao_acao(contexto, "GERENCIAR_ESTOQUE")
    try:
        return movimentar_estoque(
            db=db,
            tenant_id=contexto.tenant_id,
            filial_id=mov_in.filial_id,
            produto_id=mov_in.produto_id,
            tipo=mov_in.tipo,
            quantidade=mov_in.quantidade,
            observacao=mov_in.observacao,
            numero_lote=mov_in.numero_lote,
            data_fabricacao=mov_in.data_fabricacao,
            data_validade=mov_in.data_validade,
            usuario_id=contexto.usuario.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/api/estoque/transferir", tags=["Estoque & Produtos"])
def endpoint_transferir_estoque(
    transf_in: EstoqueTransferenciaRequest,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Transfere mercadorias entre duas unidades da mesma empresa."""
    exigir_permissao_acao(contexto, "GERENCIAR_ESTOQUE")
    try:
        return transferir_estoque(
            db=db,
            tenant_id=contexto.tenant_id,
            filial_origem_id=transf_in.filial_origem_id,
            filial_destino_id=transf_in.filial_destino_id,
            produto_id=transf_in.produto_id,
            quantidade=transf_in.quantidade,
            observacao=transf_in.observacao,
            usuario_id=contexto.usuario.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ===========================================================================
# 9. Pedidos de Compra
# ===========================================================================
@app.get("/api/compras", response_model=list[PedidoCompraResponse], tags=["Compras & Fornecedores"])
def listar_pedidos_compra(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista os pedidos de compra da empresa autenticada."""
    tid = contexto.tenant_id
    pedidos = (
        db.query(PedidoCompra, Filial, Fornecedor, Produto)
        .join(Filial, PedidoCompra.filial_id == Filial.id)
        .join(Fornecedor, PedidoCompra.fornecedor_id == Fornecedor.id)
        .join(Produto, PedidoCompra.produto_id == Produto.id)
        .filter(PedidoCompra.tenant_id == tid)
        .order_by(PedidoCompra.criado_em.desc())
        .all()
    )
    return [
        PedidoCompraResponse(
            id=p.id,
            tenant_id=p.tenant_id,
            numero_pedido=p.numero_pedido,
            filial_id=p.filial_id,
            filial_nome=fil.nome,
            fornecedor_id=p.fornecedor_id,
            fornecedor_nome=forn.nome_fantasia,
            produto_id=p.produto_id,
            produto_nome=prod.nome,
            quantidade=p.quantidade,
            custo_unitario=p.custo_unitario,
            valor_total=p.valor_total,
            status=p.status,
            criado_em=p.criado_em,
        )
        for p, fil, forn, prod in pedidos
    ]


@app.post(
    "/api/compras",
    response_model=PedidoCompraResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Compras & Fornecedores"],
)
def criar_pedido_compra(
    pc_in: PedidoCompraCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Emite um novo pedido de compra para fornecedor da empresa."""
    exigir_permissao_acao(contexto, "GERENCIAR_COMPRAS")
    tid = contexto.tenant_id

    filial = (
        db.query(Filial)
        .filter(Filial.id == pc_in.filial_id, Filial.tenant_id == tid)
        .first()
    )
    if not filial:
        raise HTTPException(status_code=400, detail="Unidade não encontrada nesta empresa.")
    forn = (
        db.query(Fornecedor)
        .filter(Fornecedor.id == pc_in.fornecedor_id, Fornecedor.tenant_id == tid)
        .first()
    )
    if not forn:
        raise HTTPException(status_code=400, detail="Fornecedor não encontrado nesta empresa.")
    prod = (
        db.query(Produto)
        .filter(Produto.id == pc_in.produto_id, Produto.tenant_id == tid)
        .first()
    )
    if not prod:
        raise HTTPException(status_code=400, detail="Produto não encontrado nesta empresa.")

    seq = db.query(PedidoCompra).filter(PedidoCompra.tenant_id == tid).count() + 1
    num_pedido = f"OC-{_agora_utc().strftime('%Y%m%d')}-{seq:04d}"
    valor_total = round(pc_in.quantidade * pc_in.custo_unitario, 2)

    pedido = PedidoCompra(
        tenant_id=tid,
        numero_pedido=num_pedido,
        filial_id=pc_in.filial_id,
        fornecedor_id=pc_in.fornecedor_id,
        produto_id=pc_in.produto_id,
        quantidade=pc_in.quantidade,
        custo_unitario=pc_in.custo_unitario,
        valor_total=valor_total,
        status="APROVADO",
        criado_em=_agora_utc(),
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    return PedidoCompraResponse(
        id=pedido.id,
        tenant_id=tid,
        numero_pedido=pedido.numero_pedido,
        filial_id=pedido.filial_id,
        filial_nome=filial.nome,
        fornecedor_id=pedido.fornecedor_id,
        fornecedor_nome=forn.nome_fantasia,
        produto_id=pedido.produto_id,
        produto_nome=prod.nome,
        quantidade=pedido.quantidade,
        custo_unitario=pedido.custo_unitario,
        valor_total=pedido.valor_total,
        status=pedido.status,
        criado_em=pedido.criado_em,
    )


@app.post("/api/compras/{pedido_id}/receber", tags=["Compras & Fornecedores"])
def endpoint_receber_pedido(
    pedido_id: int,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Confirma o recebimento físico do pedido de compra e dá entrada no estoque."""
    exigir_permissao_acao(contexto, "GERENCIAR_COMPRAS")
    try:
        return receber_pedido_compra(
            db=db,
            tenant_id=contexto.tenant_id,
            pedido_id=pedido_id,
            usuario_id=contexto.usuario.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ===========================================================================
# 10. Clientes & Fidelidade (CRM)
# ===========================================================================
@app.get("/api/crm/clientes", response_model=list[ClienteCRMResponse], tags=["Vendas & CRM"])
def listar_clientes_crm(
    segmento: str | None = Query(default=None),
    busca: str | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista a carteira de clientes exclusiva da empresa autenticada."""
    query = db.query(ClienteCRM).filter(ClienteCRM.tenant_id == contexto.tenant_id)
    if segmento:
        query = query.filter(ClienteCRM.segmento_rfm == segmento.upper())
    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            (ClienteCRM.nome.ilike(termo)) | (ClienteCRM.cpf.ilike(termo))
        )
    return query.order_by(ClienteCRM.nome.asc()).all()


@app.post(
    "/api/crm/clientes",
    response_model=ClienteCRMResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Vendas & CRM"],
)
def criar_cliente_crm(
    cli_in: ClienteCRMCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cadastra um novo cliente na carteira da empresa."""
    exigir_permissao_acao(contexto, "GERENCIAR_CRM")
    tid = contexto.tenant_id

    cpf_limpo = re.sub(r"\D", "", cli_in.cpf)
    if not cpf_limpo:
        raise HTTPException(status_code=400, detail="Informe um CPF válido.")
    cpf_fmt = (
        f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        if len(cpf_limpo) == 11
        else cpf_limpo
    )

    existente = (
        db.query(ClienteCRM)
        .filter(
            ClienteCRM.tenant_id == tid,
            (ClienteCRM.cpf == cli_in.cpf.strip())
            | (ClienteCRM.cpf == cpf_limpo)
            | (ClienteCRM.cpf == cpf_fmt),
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400, detail="Este CPF já está cadastrado na sua empresa."
        )

    if cli_in.filial_preferida_id is not None:
        f = (
            db.query(Filial)
            .filter(
                Filial.id == cli_in.filial_preferida_id,
                Filial.tenant_id == tid,
            )
            .first()
        )
        if not f:
            raise HTTPException(
                status_code=400, detail="Unidade preferida não pertence à sua empresa."
            )

    novo = ClienteCRM(
        tenant_id=tid,
        cpf=cpf_fmt,
        nome=cli_in.nome.strip(),
        whatsapp=cli_in.whatsapp.strip(),
        email=cli_in.email.strip(),
        filial_preferida_id=cli_in.filial_preferida_id,
        segmento_rfm="NOVO",
        pontos_fidelidade=0,
        saldo_cashback=0.0,
        total_gasto_historico=0.0,
        total_compras_count=0,
        economia_acumulada_clube=0.0,
        criado_em=_agora_utc(),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/api/crm/clientes/cpf/{cpf}", tags=["Vendas & CRM"])
def buscar_cliente_por_cpf(
    cpf: str,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Localiza um cliente pelo CPF dentro da empresa autenticada e retorna seu histórico."""
    tid = contexto.tenant_id
    cpf_limpo = re.sub(r"\D", "", cpf)
    cpf_fmt = (
        f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        if len(cpf_limpo) == 11
        else cpf_limpo
    )
    cliente = (
        db.query(ClienteCRM)
        .filter(
            ClienteCRM.tenant_id == tid,
            (ClienteCRM.cpf == cpf)
            | (ClienteCRM.cpf == cpf_limpo)
            | (ClienteCRM.cpf == cpf_fmt),
        )
        .first()
    )
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado no cadastro desta empresa.",
        )

    transacoes = (
        db.query(TransacaoCashback)
        .filter(
            TransacaoCashback.tenant_id == tid,
            TransacaoCashback.cliente_id == cliente.id,
        )
        .order_by(TransacaoCashback.criado_em.desc())
        .limit(20)
        .all()
    )

    return {
        "cliente": {
            "id": cliente.id,
            "tenant_id": tid,
            "cpf": cliente.cpf,
            "nome": cliente.nome,
            "whatsapp": cliente.whatsapp,
            "email": cliente.email,
            "filial_preferida_id": cliente.filial_preferida_id,
            "segmento_rfm": cliente.segmento_rfm,
            "pontos_fidelidade": cliente.pontos_fidelidade,
            "saldo_cashback": cliente.saldo_cashback,
            "total_gasto_historico": cliente.total_gasto_historico,
            "total_compras_count": cliente.total_compras_count,
            "economia_acumulada_clube": cliente.economia_acumulada_clube,
            "ultima_compra_em": (
                cliente.ultima_compra_em.isoformat() if cliente.ultima_compra_em else None
            ),
        },
        "historico_cashback": [
            {
                "id": t.id,
                "tipo": t.tipo,
                "valor": t.valor,
                "pontos": t.pontos,
                "descricao": t.descricao,
                "criado_em": t.criado_em.isoformat(),
            }
            for t in transacoes
        ],
    }


@app.get("/api/crm/campanhas", response_model=list[CampanhaCRMResponse], tags=["Vendas & CRM"])
def listar_campanhas_crm(
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista as campanhas promocionais da empresa autenticada."""
    return (
        db.query(CampanhaCRM)
        .filter(CampanhaCRM.tenant_id == contexto.tenant_id)
        .order_by(CampanhaCRM.criada_em.desc())
        .all()
    )


@app.post(
    "/api/crm/campanhas",
    response_model=CampanhaCRMResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Vendas & CRM"],
)
def criar_campanha_crm(
    camp_in: CampanhaCRMCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Cria uma nova campanha segmentada para os clientes da empresa."""
    exigir_permissao_acao(contexto, "GERENCIAR_CRM")
    tid = contexto.tenant_id
    alvo = camp_in.segmento_alvo.upper()

    if alvo == "TODOS":
        impactados = db.query(ClienteCRM).filter(ClienteCRM.tenant_id == tid).count()
    else:
        impactados = (
            db.query(ClienteCRM)
            .filter(
                ClienteCRM.tenant_id == tid,
                ClienteCRM.segmento_rfm == alvo,
            )
            .count()
        )

    nova = CampanhaCRM(
        tenant_id=tid,
        titulo=camp_in.titulo.strip(),
        segmento_alvo=alvo,
        canal=camp_in.canal.strip(),
        desconto_extra_pct=camp_in.desconto_extra_pct,
        cashback_bonus_pct=camp_in.cashback_bonus_pct,
        mensagem_template=camp_in.mensagem_template.strip(),
        clientes_impactados=impactados,
        conversao_estimada_pct=15.0,
        ativa=True,
        criada_em=_agora_utc(),
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


# ===========================================================================
# 11. Ponto de Venda (PDV) & Controle de Caixa
# ===========================================================================
@app.get("/api/pdv/sessao-atual", response_model=SessaoCaixaResponse | None, tags=["Ponto de Venda"])
def obter_sessao_caixa_atual(
    filial_id: int | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna a sessão de caixa aberta da unidade, se houver."""
    q = db.query(SessaoCaixaPDV, Filial).join(
        Filial, SessaoCaixaPDV.filial_id == Filial.id
    ).filter(
        SessaoCaixaPDV.tenant_id == contexto.tenant_id,
        SessaoCaixaPDV.status == "ABERTO",
    )
    if filial_id is not None:
        q = q.filter(SessaoCaixaPDV.filial_id == filial_id)
    row = q.order_by(SessaoCaixaPDV.aberta_em.desc()).first()
    if not row:
        return None
    sessao, fil = row
    return SessaoCaixaResponse(
        id=sessao.id,
        tenant_id=sessao.tenant_id,
        filial_id=sessao.filial_id,
        filial_nome=fil.nome,
        usuario_id=sessao.usuario_id,
        operador_nome=sessao.operador_nome,
        valor_abertura=sessao.valor_abertura,
        valor_fechamento=sessao.valor_fechamento,
        total_vendido=sessao.total_vendido,
        qtd_vendas=sessao.qtd_vendas,
        status=sessao.status,
        aberta_em=sessao.aberta_em,
        fechada_em=sessao.fechada_em,
    )


@app.post(
    "/api/pdv/caixa/abrir",
    response_model=SessaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Ponto de Venda"],
)
def abrir_sessao_caixa(
    req: SessaoCaixaAbrirRequest,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Abre o caixa de uma unidade para operação do Ponto de Venda."""
    exigir_permissao_acao(contexto, "OPERAR_PDV")
    tid = contexto.tenant_id

    filial = (
        db.query(Filial)
        .filter(Filial.id == req.filial_id, Filial.tenant_id == tid)
        .first()
    )
    if not filial:
        raise HTTPException(status_code=400, detail="Unidade não encontrada nesta empresa.")

    ja_aberta = (
        db.query(SessaoCaixaPDV)
        .filter(
            SessaoCaixaPDV.tenant_id == tid,
            SessaoCaixaPDV.filial_id == filial.id,
            SessaoCaixaPDV.status == "ABERTO",
        )
        .first()
    )
    if ja_aberta:
        return SessaoCaixaResponse(
            id=ja_aberta.id,
            tenant_id=tid,
            filial_id=filial.id,
            filial_nome=filial.nome,
            usuario_id=ja_aberta.usuario_id,
            operador_nome=ja_aberta.operador_nome,
            valor_abertura=ja_aberta.valor_abertura,
            valor_fechamento=ja_aberta.valor_fechamento,
            total_vendido=ja_aberta.total_vendido,
            qtd_vendas=ja_aberta.qtd_vendas,
            status=ja_aberta.status,
            aberta_em=ja_aberta.aberta_em,
            fechada_em=ja_aberta.fechada_em,
        )

    nova = SessaoCaixaPDV(
        tenant_id=tid,
        filial_id=filial.id,
        usuario_id=contexto.usuario.id,
        operador_nome=contexto.usuario.nome,
        valor_abertura=round(float(req.valor_abertura), 2),
        total_vendido=0.0,
        qtd_vendas=0,
        status="ABERTO",
        aberta_em=_agora_utc(),
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)

    return SessaoCaixaResponse(
        id=nova.id,
        tenant_id=tid,
        filial_id=filial.id,
        filial_nome=filial.nome,
        usuario_id=nova.usuario_id,
        operador_nome=nova.operador_nome,
        valor_abertura=nova.valor_abertura,
        valor_fechamento=nova.valor_fechamento,
        total_vendido=nova.total_vendido,
        qtd_vendas=nova.qtd_vendas,
        status=nova.status,
        aberta_em=nova.aberta_em,
        fechada_em=nova.fechada_em,
    )


@app.post(
    "/api/pdv/caixa/{sessao_id}/fechar",
    response_model=SessaoCaixaResponse,
    tags=["Ponto de Venda"],
)
def fechar_sessao_caixa(
    sessao_id: int,
    req: SessaoCaixaFecharRequest,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Encerra a sessão de caixa informando o saldo conferido no fechamento."""
    exigir_permissao_acao(contexto, "OPERAR_PDV")
    tid = contexto.tenant_id

    sessao = (
        db.query(SessaoCaixaPDV)
        .filter(SessaoCaixaPDV.id == sessao_id, SessaoCaixaPDV.tenant_id == tid)
        .first()
    )
    if not sessao:
        raise HTTPException(status_code=404, detail="Sessão de caixa não encontrada.")

    filial = db.query(Filial).filter(Filial.id == sessao.filial_id).first()
    sessao.valor_fechamento = round(float(req.valor_fechamento), 2)
    sessao.status = "FECHADO"
    sessao.fechada_em = _agora_utc()
    db.commit()
    db.refresh(sessao)

    return SessaoCaixaResponse(
        id=sessao.id,
        tenant_id=tid,
        filial_id=sessao.filial_id,
        filial_nome=filial.nome if filial else "",
        usuario_id=sessao.usuario_id,
        operador_nome=sessao.operador_nome,
        valor_abertura=sessao.valor_abertura,
        valor_fechamento=sessao.valor_fechamento,
        total_vendido=sessao.total_vendido,
        qtd_vendas=sessao.qtd_vendas,
        status=sessao.status,
        aberta_em=sessao.aberta_em,
        fechada_em=sessao.fechada_em,
    )


@app.post("/api/pdv/vender", response_model=VendaPDVResponse, tags=["Ponto de Venda"])
def endpoint_vender_pdv(
    venda_in: VendaPDVRequest,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Registra uma venda no Ponto de Venda da empresa autenticada."""
    exigir_permissao_acao(contexto, "OPERAR_PDV")
    try:
        itens_dict = [
            {"produto_id": i.produto_id, "quantidade": i.quantidade}
            for i in venda_in.itens
        ]
        return processar_venda_pdv(
            db=db,
            tenant_id=contexto.tenant_id,
            filial_id=venda_in.filial_id,
            itens=itens_dict,
            cpf_cliente=venda_in.cpf_cliente,
            usar_cashback=venda_in.usar_cashback,
            forma_pagamento=venda_in.forma_pagamento,
            usuario_id=contexto.usuario.id,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.get("/api/pdv/vendas", tags=["Ponto de Venda"])
def listar_vendas_pdv(
    filial_id: int | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista o histórico de vendas da empresa autenticada."""
    tid = contexto.tenant_id
    query = (
        db.query(VendaPDV, Filial, ClienteCRM)
        .join(Filial, VendaPDV.filial_id == Filial.id)
        .outerjoin(ClienteCRM, VendaPDV.cliente_id == ClienteCRM.id)
        .filter(VendaPDV.tenant_id == tid)
    )
    if filial_id is not None:
        query = query.filter(VendaPDV.filial_id == filial_id)

    vendas = query.order_by(VendaPDV.criada_em.desc()).limit(50).all()
    return [
        {
            "id": v.id,
            "tenant_id": tid,
            "numero_cupom": v.numero_cupom,
            "filial_id": v.filial_id,
            "filial_nome": fil.nome,
            "cliente_id": v.cliente_id,
            "cliente_nome": cli.nome if cli else "Consumidor Final",
            "subtotal_bruto": v.subtotal_bruto,
            "desconto_clube_crm": v.desconto_clube_crm,
            "cashback_utilizado": v.cashback_utilizado,
            "valor_total_liquido": v.valor_total_liquido,
            "cashback_gerado": v.cashback_gerado,
            "forma_pagamento": v.forma_pagamento,
            "criada_em": v.criada_em.isoformat(),
        }
        for v, fil, cli in vendas
    ]


# ===========================================================================
# 12. Financeiro & Demonstrativo de Resultados (DRE)
# ===========================================================================
@app.get(
    "/api/financeiro/lancamentos",
    response_model=list[LancamentoFinanceiroResponse],
    tags=["Financeiro"],
)
def listar_lancamentos_financeiros(
    filial_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Lista os lançamentos financeiros exclusivos da empresa autenticada."""
    exigir_permissao_modulo(contexto, "financeiro")
    tid = contexto.tenant_id

    query = (
        db.query(LancamentoFinanceiro, Filial)
        .join(Filial, LancamentoFinanceiro.filial_id == Filial.id)
        .filter(LancamentoFinanceiro.tenant_id == tid)
    )
    if filial_id is not None:
        query = query.filter(LancamentoFinanceiro.filial_id == filial_id)
    if tipo:
        query = query.filter(LancamentoFinanceiro.tipo == tipo.upper())

    rows = (
        query.order_by(
            LancamentoFinanceiro.data_competencia.desc(),
            LancamentoFinanceiro.id.desc(),
        )
        .limit(100)
        .all()
    )
    return [
        LancamentoFinanceiroResponse(
            id=l.id,
            tenant_id=l.tenant_id,
            filial_id=l.filial_id,
            filial_nome=fil.nome,
            tipo=l.tipo,
            categoria_dre=l.categoria_dre,
            descricao=l.descricao,
            valor=l.valor,
            status=l.status,
            data_competencia=l.data_competencia,
            criado_em=l.criado_em,
        )
        for l, fil in rows
    ]


@app.post(
    "/api/financeiro/lancamentos",
    response_model=LancamentoFinanceiroResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Financeiro"],
)
def criar_lancamento_financeiro(
    lanc_in: LancamentoFinanceiroCreate,
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Registra uma receita ou despesa financeira na empresa autenticada."""
    exigir_permissao_acao(contexto, "LANCAR_FINANCEIRO")
    tid = contexto.tenant_id

    filial = (
        db.query(Filial)
        .filter(Filial.id == lanc_in.filial_id, Filial.tenant_id == tid)
        .first()
    )
    if not filial:
        raise HTTPException(status_code=400, detail="Unidade não encontrada nesta empresa.")

    novo = LancamentoFinanceiro(
        tenant_id=tid,
        filial_id=lanc_in.filial_id,
        tipo=lanc_in.tipo.upper(),
        categoria_dre=lanc_in.categoria_dre.upper(),
        descricao=lanc_in.descricao.strip(),
        valor=round(float(lanc_in.valor), 2),
        status=lanc_in.status.upper(),
        data_competencia=lanc_in.data_competencia or date.today(),
        criado_em=_agora_utc(),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)

    return LancamentoFinanceiroResponse(
        id=novo.id,
        tenant_id=tid,
        filial_id=novo.filial_id,
        filial_nome=filial.nome,
        tipo=novo.tipo,
        categoria_dre=novo.categoria_dre,
        descricao=novo.descricao,
        valor=novo.valor,
        status=novo.status,
        data_competencia=novo.data_competencia,
        criado_em=novo.criado_em,
    )


@app.get("/api/financeiro/dre", response_model=DREResponse, tags=["Financeiro"])
def obter_dre_gerencial(
    filial_id: int | None = Query(default=None),
    contexto: ContextoComercio = Depends(resolver_contexto_comercio),
    db: Session = Depends(get_db),
):
    """Retorna o Demonstrativo de Resultados do Exercício (DRE) da empresa autenticada."""
    exigir_permissao_modulo(contexto, "financeiro")
    return gerar_dre_gerencial(db, tenant_id=contexto.tenant_id, filial_id=filial_id)


# ===========================================================================
# 13. Frontend Web (SPA)
# ===========================================================================
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/app.js", include_in_schema=False)
def serve_app_js():
    js_file = FRONTEND_DIR / "app.js"
    if js_file.exists():
        return FileResponse(str(js_file), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="app.js não encontrado")


@app.get("/", include_in_schema=False)
def serve_frontend():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse(
        content="<h1>HelpDmais</h1><p>Acesse <a href='/docs'>/docs</a></p>",
        status_code=200,
    )
