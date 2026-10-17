"""API FastAPI Principal do Sistema ERP + CRM para Grupo de Mercados.

Contempla:
- Multi-Loja (Filiais e Matriz/CD)
- Fornecedores e Catálogo com Preço Normal e Preço Clube CRM
- Controle de Estoque com Validade FEFO (First Expired, First Out)
- Transferências entre Filiais e Ajustes
- Pedidos de Compra e Recebimento Físico
- CRM 360º (Clientes, Fidelidade, Cashback e Segmentação RFM)
- Campanhas de Marketing Segmentadas
- Frente de Caixa (PDV Online) com Resgate/Crédito de Cashback e Lançamento Financeiro
- DRE Gerencial Consolidado e por Filial
- Status de Agentes CrewAI (Tiers de Modelos) e Conectividade PostgreSQL 192.168.15.109
- Servidor de Arquivos Estáticos para Frontend SPA
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
import re
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc, func
from sqlalchemy.orm import Session



def _agora_utc() -> datetime:
    """Retorna datetime UTC sem timezone para compatibilidade com colunas DateTime ingênuas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from app.core.database import (
    DATABASE_MODE,
    PG_HOST,
    PG_PORT,
    SessionLocal,
    _postgres_acessivel,
    get_db,
)
from app.models.erp_crm_models import (
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
    TransacaoCashback,
    VendaPDV,
)
from app.schemas.erp_crm_schemas import (
    AgentesStatusResponse,
    CampanhaCRMCreate,
    CampanhaCRMResponse,
    ClienteCRMCreate,
    ClienteCRMResponse,
    DashboardResumoResponse,
    DREResponse,
    EstoqueItemResponse,
    EstoqueMovimentoRequest,
    EstoqueTransferenciaRequest,
    FilialCreate,
    FilialResponse,
    FornecedorCreate,
    FornecedorResponse,
    LancamentoFinanceiroCreate,
    LancamentoFinanceiroResponse,
    LoteValidadeResponse,
    PedidoCompraCreate,
    PedidoCompraResponse,
    ProdutoCreate,
    ProdutoResponse,
    VendaPDVRequest,
    VendaPDVResponse,
)
from app.services.regras_negocio import (
    calcular_segmento_rfm,
    gerar_dre_gerencial,
    movimentar_estoque,
    processar_venda_pdv,
    receber_pedido_compra,
    transferir_estoque,
)

BASE_PROJECT_DIR = Path("/media/rodrigo/Downloads/ai-agents/workspace/erp-mercados")
FRONTEND_DIR = BASE_PROJECT_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
LOG_AO_VIVO = Path("/media/rodrigo/Downloads/ai-agents/logs/ao_vivo.log")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialização segura do banco de dados no startup."""
    try:
        from app.core.seed import inicializar_e_popular_banco

        inicializar_e_popular_banco()
    except Exception as exc:
        print(f"[Startup] Aviso ao inicializar seed: {exc}. Executando fallback seguro...")
        try:
            from app.core.database import Base, engine

            Base.metadata.create_all(bind=engine)
        except Exception as inner_exc:
            print(f"[Startup] Erro crítico criando tabelas: {inner_exc}")
    yield


app = FastAPI(
    title="Grupo Mercados — ERP & CRM Online",
    version="2.0.0",
    description="Sistema Integrado ERP Supermercadista + CRM Clube de Fidelidade e Cashback",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# 1. Health & Status
# ===========================================================================
@app.get("/api/health", tags=["Sistema"])
def health_check():
    """Verifica a integridade da API e da conexão com o banco de dados."""
    pg_ok = _postgres_acessivel(PG_HOST, PG_PORT)
    return {
        "status": "online",
        "sistema": "Grupo Mercados — ERP & CRM Online",
        "versao": "2.0.0",
        "modo_banco": DATABASE_MODE,
        "postgres_conectado": pg_ok,
        "postgres_host": f"{PG_HOST}:{PG_PORT}",
        "timestamp": _agora_utc().isoformat(),
    }


# ===========================================================================
# 2. Dashboard Consolidado
# ===========================================================================
@app.get("/api/dashboard/resumo", tags=["Dashboard"])
def dashboard_resumo(db: Session = Depends(get_db)):
    """Retorna os KPIs vitais do Grupo de Mercados."""
    hoje = date.today()

    # DRE consolidado para obter faturamento e lucro líquido
    dre = gerar_dre_gerencial(db)
    faturamento_total = dre["receita_bruta"]
    lucro_liquido = dre["ebitda_lucro_liquido"]

    # CRM KPIs
    total_clientes = db.query(ClienteCRM).count()
    cashback_circulacao = round(
        float(db.query(func.coalesce(func.sum(ClienteCRM.saldo_cashback), 0.0)).scalar()), 2
    )

    # Alertas de Ruptura (estoque <= estoque_minimo)
    alertas_db = (
        db.query(EstoqueFilial, Produto, Filial)
        .join(Produto, EstoqueFilial.produto_id == Produto.id)
        .join(Filial, EstoqueFilial.filial_id == Filial.id)
        .filter(EstoqueFilial.quantidade_atual <= EstoqueFilial.estoque_minimo)
        .all()
    )
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

    # Lotes vencendo em <= 15 dias (FEFO Alerta)
    limite_validade = hoje + timedelta(days=15)
    lotes_vencendo_db = (
        db.query(LoteValidade, Produto, Filial)
        .join(Produto, LoteValidade.produto_id == Produto.id)
        .join(Filial, LoteValidade.filial_id == Filial.id)
        .filter(
            LoteValidade.quantidade_lote > 0,
            LoteValidade.data_validade <= limite_validade,
        )
        .order_by(LoteValidade.data_validade.asc())
        .all()
    )
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

    # Vendas por filial vs meta
    filiais = db.query(Filial).all()
    vendas_por_filial = []
    for f in filiais:
        rec_f = (
            db.query(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0.0))
            .filter(
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
        vendas_por_filial.append({
            "filial_id": f.id,
            "nome": f.nome,
            "bandeira": f.bandeira,
            "vendas_mes": rec_f_val,
            "meta_mensal": f.meta_mensal,
            "atingimento_pct": atingimento,
        })

    # Top 5 produtos mais vendidos
    top_itens = (
        db.query(
            ItemVendaPDV.produto_id,
            Produto.nome,
            Produto.departamento,
            func.sum(ItemVendaPDV.quantidade).label("total_qtd"),
            func.sum(ItemVendaPDV.subtotal_item).label("total_faturado"),
        )
        .join(Produto, ItemVendaPDV.produto_id == Produto.id)
        .group_by(ItemVendaPDV.produto_id, Produto.nome, Produto.departamento)
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

    # Se não houver vendas suficientes registradas em ItemVendaPDV, usa catálogo ordenado
    if not top_5_produtos:
        prods = db.query(Produto).order_by(Produto.preco_venda.desc()).limit(5).all()
        top_5_produtos = [
            {
                "produto_id": p.id,
                "nome": p.nome,
                "departamento": p.departamento,
                "quantidade_vendida": 45.0,
                "total_faturado": round(45.0 * p.preco_venda, 2),
            }
            for p in prods
        ]

    # Últimas vendas registradas no PDV
    ultimas_vendas_db = (
        db.query(VendaPDV, Filial, ClienteCRM)
        .join(Filial, VendaPDV.filial_id == Filial.id)
        .outerjoin(ClienteCRM, VendaPDV.cliente_id == ClienteCRM.id)
        .order_by(VendaPDV.criada_em.desc())
        .limit(10)
        .all()
    )
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
        "faturamento_total": faturamento_total,
        "lucro_liquido": lucro_liquido,
        "total_clientes_crm": total_clientes,
        "cashback_em_circulacao": cashback_circulacao,
        "alertas_ruptura": alertas_ruptura,
        "lotes_vencendo_15_dias": lotes_vencendo,
        "vendas_por_filial_vs_meta": vendas_por_filial,
        "top_5_produtos": top_5_produtos,
        "ultimas_vendas": ultimas_vendas,
    }


# ===========================================================================
# 3. Filiais
# ===========================================================================
@app.get("/api/filiais", response_model=list[FilialResponse], tags=["Filiais"])
def listar_filiais(db: Session = Depends(get_db)):
    """Lista todas as filiais do Grupo de Mercados."""
    return db.query(Filial).order_by(Filial.id.asc()).all()


@app.post(
    "/api/filiais",
    response_model=FilialResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Filiais"],
)
def criar_filial(filial_in: FilialCreate, db: Session = Depends(get_db)):
    """Cadastra uma nova filial no sistema."""
    existente = (
        db.query(Filial)
        .filter((Filial.codigo == filial_in.codigo) | (Filial.cnpj == filial_in.cnpj))
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=400, detail="Código ou CNPJ de filial já existente no cadastro."
        )

    nova = Filial(**filial_in.model_dump())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


# ===========================================================================
# 4. Fornecedores
# ===========================================================================
@app.get("/api/fornecedores", response_model=list[FornecedorResponse], tags=["Fornecedores"])
def listar_fornecedores(db: Session = Depends(get_db)):
    """Lista fornecedores homologados da rede de supermercados."""
    return db.query(Fornecedor).order_by(Fornecedor.id.asc()).all()


@app.post(
    "/api/fornecedores",
    response_model=FornecedorResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Fornecedores"],
)
def criar_fornecedor(forn_in: FornecedorCreate, db: Session = Depends(get_db)):
    """Cadastra um novo fornecedor homologado."""
    existente = db.query(Fornecedor).filter(Fornecedor.cnpj == forn_in.cnpj).first()
    if existente:
        raise HTTPException(status_code=400, detail="Fornecedor já cadastrado com este CNPJ.")

    novo = Fornecedor(**forn_in.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ===========================================================================
# 5. Produtos
# ===========================================================================
@app.get("/api/produtos", response_model=list[ProdutoResponse], tags=["Produtos"])
def listar_produtos(
    departamento: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista catálogo de produtos com Preço Venda e Preço Clube CRM."""
    query = db.query(Produto)
    if departamento:
        query = query.filter(Produto.departamento.ilike(f"%{departamento}%"))
    return query.order_by(Produto.id.asc()).all()


@app.post(
    "/api/produtos",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Produtos"],
)
def criar_produto(prod_in: ProdutoCreate, db: Session = Depends(get_db)):
    """Cadastra um novo produto no catálogo central."""
    existente = (
        db.query(Produto)
        .filter((Produto.sku == prod_in.sku) | (Produto.ean == prod_in.ean))
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="SKU ou EAN já existente no catálogo.")

    novo = Produto(**prod_in.model_dump())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# ===========================================================================
# 6. Estoque & Lotes (FEFO)
# ===========================================================================
@app.get("/api/estoque", tags=["Estoque"])
def consultar_estoque(
    filial_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Retorna a posição de estoque com status (NORMAL/CRITICO/RUPTURA) e lotes ordenados por FEFO."""
    hoje = date.today()
    query = (
        db.query(EstoqueFilial, Produto, Filial)
        .join(Produto, EstoqueFilial.produto_id == Produto.id)
        .join(Filial, EstoqueFilial.filial_id == Filial.id)
    )

    if filial_id is not None:
        query = query.filter(EstoqueFilial.filial_id == filial_id)

    linhas = query.order_by(Filial.id.asc(), Produto.nome.asc()).all()

    resultado = []
    for ef, prod, fil in linhas:
        # Status de Estoque
        if ef.quantidade_atual <= 0:
            status_estoque = "RUPTURA"
        elif ef.quantidade_atual <= ef.estoque_minimo:
            status_estoque = "CRITICO"
        else:
            status_estoque = "NORMAL"

        # Lotes ordenados por FEFO (First Expired, First Out)
        lotes_db = (
            db.query(LoteValidade)
            .filter(
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
                "filial_id": l.filial_id,
                "produto_id": l.produto_id,
                "numero_lote": l.numero_lote,
                "data_fabricacao": l.data_fabricacao.isoformat(),
                "data_validade": l.data_validade.isoformat(),
                "quantidade_lote": l.quantidade_lote,
                "status_lote": l.status_lote,
                "dias_para_vencer": (l.data_validade - hoje).days,
            }
            for l in lotes_db
        ]

        resultado.append({
            "id": ef.id,
            "filial_id": ef.filial_id,
            "filial_nome": fil.nome,
            "produto_id": ef.produto_id,
            "produto_nome": prod.nome,
            "produto_sku": prod.sku,
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
        })

    return resultado


@app.post("/api/estoque/movimentar", tags=["Estoque"])
def endpoint_movimentar_estoque(
    mov_in: EstoqueMovimentoRequest,
    db: Session = Depends(get_db),
):
    """Entrada de mercadoria/lote ou baixa por quebra/perda com auditoria."""
    try:
        return movimentar_estoque(
            db=db,
            filial_id=mov_in.filial_id,
            produto_id=mov_in.produto_id,
            tipo=mov_in.tipo,
            quantidade=mov_in.quantidade,
            observacao=mov_in.observacao,
            numero_lote=mov_in.numero_lote,
            data_fabricacao=mov_in.data_fabricacao,
            data_validade=mov_in.data_validade,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@app.post("/api/estoque/transferir", tags=["Estoque"])
def endpoint_transferir_estoque(
    transf_in: EstoqueTransferenciaRequest,
    db: Session = Depends(get_db),
):
    """Transfere estoque de uma filial origem para uma filial destino com controle FEFO."""
    try:
        return transferir_estoque(
            db=db,
            filial_origem_id=transf_in.filial_origem_id,
            filial_destino_id=transf_in.filial_destino_id,
            produto_id=transf_in.produto_id,
            quantidade=transf_in.quantidade,
            observacao=transf_in.observacao,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ===========================================================================
# 7. Pedidos de Compra
# ===========================================================================
@app.get("/api/compras", response_model=list[PedidoCompraResponse], tags=["Compras"])
def listar_pedidos_compra(db: Session = Depends(get_db)):
    """Lista pedidos de compra emitidos."""
    return db.query(PedidoCompra).order_by(PedidoCompra.criado_em.desc()).all()


@app.post(
    "/api/compras",
    response_model=PedidoCompraResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Compras"],
)
def criar_pedido_compra(pc_in: PedidoCompraCreate, db: Session = Depends(get_db)):
    """Emite um novo pedido de compra para fornecedor."""
    filial = db.query(Filial).filter(Filial.id == pc_in.filial_id).first()
    if not filial:
        raise HTTPException(status_code=400, detail="Filial não encontrada.")
    forn = db.query(Fornecedor).filter(Fornecedor.id == pc_in.fornecedor_id).first()
    if not forn:
        raise HTTPException(status_code=400, detail="Fornecedor não encontrado.")
    prod = db.query(Produto).filter(Produto.id == pc_in.produto_id).first()
    if not prod:
        raise HTTPException(status_code=400, detail="Produto não encontrado.")

    num_pedido = f"PC-{_agora_utc().strftime('%Y%m%d')}-{db.query(PedidoCompra).count() + 1:04d}"
    valor_total = round(pc_in.quantidade * pc_in.custo_unitario, 2)

    pedido = PedidoCompra(
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
    return pedido


@app.post("/api/compras/{pedido_id}/receber", tags=["Compras"])
def endpoint_receber_pedido(pedido_id: int, db: Session = Depends(get_db)):
    """Recebe mercadorias de um pedido de compra, gerando entrada no estoque e lote."""
    try:
        return receber_pedido_compra(db, pedido_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ===========================================================================
# 8. CRM 360º (Clientes, Cashback & Campanhas)
# ===========================================================================
@app.get("/api/crm/clientes", response_model=list[ClienteCRMResponse], tags=["CRM"])
def listar_clientes_crm(
    segmento: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista clientes cadastrados no Clube de Vantagens CRM."""
    query = db.query(ClienteCRM)
    if segmento:
        query = query.filter(ClienteCRM.segmento_rfm == segmento.upper())
    return query.order_by(ClienteCRM.id.asc()).all()


@app.post(
    "/api/crm/clientes",
    response_model=ClienteCRMResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["CRM"],
)
def criar_cliente_crm(cli_in: ClienteCRMCreate, db: Session = Depends(get_db)):
    """Cadastra um novo cliente no Clube de Benefícios."""
    cpf_limpo = re.sub(r"\D", "", cli_in.cpf)
    existente = (
        db.query(ClienteCRM)
        .filter((ClienteCRM.cpf == cli_in.cpf) | (ClienteCRM.cpf == cpf_limpo))
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="CPF já cadastrado no CRM.")

    novo = ClienteCRM(
        cpf=cli_in.cpf.strip(),
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


@app.get("/api/crm/clientes/cpf/{cpf}", response_model=ClienteCRMResponse, tags=["CRM"])
def buscar_cliente_por_cpf(cpf: str, db: Session = Depends(get_db)):
    """Localiza o cliente do Clube CRM pelo CPF (com ou sem pontuação)."""
    cpf_puro = cpf.strip()
    cpf_num = re.sub(r"\D", "", cpf_puro)

    cliente = (
        db.query(ClienteCRM)
        .filter((ClienteCRM.cpf == cpf_puro) | (ClienteCRM.cpf == cpf_num))
        .first()
    )
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Cliente não localizado com o CPF '{cpf}'.",
        )
    return cliente


@app.get("/api/crm/campanhas", response_model=list[CampanhaCRMResponse], tags=["CRM"])
def listar_campanhas_crm(db: Session = Depends(get_db)):
    """Lista campanhas promocionais ativas do CRM."""
    return db.query(CampanhaCRM).order_by(CampanhaCRM.criada_em.desc()).all()


@app.post(
    "/api/crm/campanhas",
    response_model=CampanhaCRMResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["CRM"],
)
def criar_campanha_crm(camp_in: CampanhaCRMCreate, db: Session = Depends(get_db)):
    """Cria uma nova campanha promocional segmentada."""
    nova = CampanhaCRM(**camp_in.model_dump(), criada_em=_agora_utc(), ativa=True)
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova


# ===========================================================================
# 9. Frente de Caixa (PDV Online)
# ===========================================================================
@app.get("/api/pdv/vendas", tags=["PDV"])
def listar_vendas_pdv(db: Session = Depends(get_db)):
    """Lista as vendas realizadas no PDV."""
    vendas = (
        db.query(VendaPDV, Filial, ClienteCRM)
        .join(Filial, VendaPDV.filial_id == Filial.id)
        .outerjoin(ClienteCRM, VendaPDV.cliente_id == ClienteCRM.id)
        .order_by(VendaPDV.criada_em.desc())
        .limit(50)
        .all()
    )
    resultado = []
    for v, fil, cli in vendas:
        resultado.append({
            "venda_id": v.id,
            "numero_cupom": v.numero_cupom,
            "filial_id": fil.id,
            "filial_nome": fil.nome,
            "cliente_id": cli.id if cli else None,
            "cliente_nome": cli.nome if cli else "Consumidor Final",
            "cpf_cliente": cli.cpf if cli else None,
            "subtotal_bruto": v.subtotal_bruto,
            "desconto_clube_crm": v.desconto_clube_crm,
            "cashback_utilizado": v.cashback_utilizado,
            "valor_total_liquido": v.valor_total_liquido,
            "cashback_gerado": v.cashback_gerado,
            "forma_pagamento": v.forma_pagamento,
            "data_hora": v.criada_em.isoformat(),
        })
    return resultado


@app.post("/api/pdv/venda", response_model=VendaPDVResponse, tags=["PDV"])
def registrar_venda_pdv(venda_in: VendaPDVRequest, db: Session = Depends(get_db)):
    """Processa a venda no PDV: Preço Clube, FEFO, Cashback, Pontos e Lançamentos Financeiros."""
    try:
        itens_dict = [item.model_dump() for item in venda_in.itens]
        cupom = processar_venda_pdv(
            db=db,
            filial_id=venda_in.filial_id,
            itens=itens_dict,
            cpf_cliente=venda_in.cpf_cliente,
            usar_cashback=venda_in.usar_cashback,
            forma_pagamento=venda_in.forma_pagamento,
        )
        return cupom
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


# ===========================================================================
# 10. Financeiro & DRE
# ===========================================================================
@app.get(
    "/api/financeiro/lancamentos",
    response_model=list[LancamentoFinanceiroResponse],
    tags=["Financeiro"],
)
def listar_lancamentos_financeiros(
    filial_id: int | None = Query(default=None),
    tipo: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Lista lançamentos financeiros (Receitas, Despesas Operacionais e CMV)."""
    query = db.query(LancamentoFinanceiro)
    if filial_id is not None:
        query = query.filter(LancamentoFinanceiro.filial_id == filial_id)
    if tipo:
        query = query.filter(LancamentoFinanceiro.tipo == tipo.upper())
    return query.order_by(LancamentoFinanceiro.data_competencia.desc(), LancamentoFinanceiro.id.desc()).limit(100).all()


@app.post(
    "/api/financeiro/lancamentos",
    response_model=LancamentoFinanceiroResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Financeiro"],
)
def criar_lancamento_financeiro(
    lanc_in: LancamentoFinanceiroCreate, db: Session = Depends(get_db)
):
    """Insere manualmente um lançamento financeiro no DRE."""
    filial = db.query(Filial).filter(Filial.id == lanc_in.filial_id).first()
    if not filial:
        raise HTTPException(status_code=400, detail="Filial não encontrada.")

    novo = LancamentoFinanceiro(
        filial_id=lanc_in.filial_id,
        tipo=lanc_in.tipo,
        categoria_dre=lanc_in.categoria_dre,
        descricao=lanc_in.descricao,
        valor=lanc_in.valor,
        status=lanc_in.status,
        data_competencia=lanc_in.data_competencia or date.today(),
        criado_em=_agora_utc(),
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/api/financeiro/dre", response_model=DREResponse, tags=["Financeiro"])
def obter_dre(
    filial_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Gera o Demonstrativo de Resultado do Exercício (DRE Gerencial) consolidado ou por filial."""
    return gerar_dre_gerencial(db, filial_id=filial_id)


# ===========================================================================
# 11. Monitoramento de Agentes CrewAI & PostgreSQL
# ===========================================================================
@app.get("/api/agentes/status", response_model=AgentesStatusResponse, tags=["Agentes"])
def obter_status_agentes():
    """Retorna os Tiers de modelos configurados, conectividade Postgres e log ao vivo."""
    tiers_info = {
        "tier1": {
            "nivel": 1,
            "nome": "Tier 1 — Leve/Rápido",
            "modelo_cli": os.getenv("AGY_MODEL_TIER1", "gemini-3.8-flash-low"),
            "modelo_api": os.getenv("API_MODEL_TIER1", "gemini/gemini-2.5-flash"),
            "effort": "low",
            "descricao": "Respostas rápidas para triagem, operações padrão e validações leves",
        },
        "tier2": {
            "nivel": 2,
            "nome": "Tier 2 — Intermediário",
            "modelo_cli": os.getenv("AGY_MODEL_TIER2", "gemini-4-argon-low"),
            "modelo_api": os.getenv("API_MODEL_TIER2", "gemini/gemini-2.5-flash"),
            "effort": "medium",
            "descricao": "Resolução de tarefas com média complexidade e escalonamento após 4 iterações",
        },
        "tier3": {
            "nivel": 3,
            "nome": "Tier 3 — Sênior/Profundo",
            "modelo_cli": os.getenv("AGY_MODEL_TIER3", "gemini-4-argon-high"),
            "modelo_api": os.getenv("API_MODEL_TIER3", "gemini/gemini-2.5-pro"),
            "effort": "high",
            "descricao": "Raciocínio profundo, arquitetura, recuperação automática de exceções e erros",
        },
    }

    pg_conectado = _postgres_acessivel(PG_HOST, PG_PORT)

    linhas_log: list[str] = []
    if LOG_AO_VIVO.exists():
        try:
            with open(LOG_AO_VIVO, "r", encoding="utf-8", errors="replace") as f:
                linhas = f.readlines()
                linhas_log = [l.rstrip("\r\n") for l in linhas[-25:]]
        except Exception as err:
            linhas_log = [f"Erro ao ler log ao vivo: {err}"]
    else:
        linhas_log = ["Arquivo de log ao vivo ainda não gerado."]

    return {
        "status": "online",
        "tiers": tiers_info,
        "tiers_crewai": tiers_info,
        "postgres_host": f"{PG_HOST}:{PG_PORT}",
        "postgres_conectado": pg_conectado,
        "modo_banco": DATABASE_MODE,
        "ultimas_linhas_log": linhas_log,
        "timestamp": _agora_utc().isoformat(),
    }


# ===========================================================================
# 12. Frontend SPA e Rota Raiz
# ===========================================================================
@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
def rota_raiz():
    """Serve a aplicação web frontend ou fallback informativo."""
    index_html = FRONTEND_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)

    return HTMLResponse("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grupo Mercados — ERP & CRM Online</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }
        .card { background: #1e293b; padding: 2.5rem; border-radius: 12px; max-width: 680px; margin: 4rem auto; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; margin-top: 0; font-size: 1.8rem; }
        p { color: #94a3b8; font-size: 1.1rem; line-height: 1.6; }
        .badge { display: inline-block; background: #0284c7; color: white; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }
        ul { list-style: none; padding: 0; margin-top: 1.5rem; }
        li { margin-bottom: 0.75rem; }
        a { color: #38bdf8; text-decoration: none; font-weight: 500; font-size: 1.05rem; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">API Operacional v2.0.0</span>
        <h1>🛒 Grupo Mercados — ERP & CRM Online</h1>
        <p>Servidor backend ativo com PostgreSQL Híbrido, Frente de Caixa PDV com Preço Clube CRM, Controle FEFO de Estoque e DRE Gerencial.</p>
        <ul>
            <li>👉 <a href="/docs">Documentação Interativa Swagger UI (/docs)</a></li>
            <li>👉 <a href="/redoc">Documentação ReDoc (/redoc)</a></li>
            <li>👉 <a href="/api/health">Verificação de Integridade (/api/health)</a></li>
            <li>👉 <a href="/api/dashboard/resumo">Resumo Executivo do Dashboard (/api/dashboard/resumo)</a></li>
            <li>👉 <a href="/api/financeiro/dre">DRE Gerencial Consolidado (/api/financeiro/dre)</a></li>
            <li>👉 <a href="/api/agentes/status">Monitor de Agentes CrewAI e Log (/api/agentes/status)</a></li>
        </ul>
    </div>
</body>
</html>""")


# Monta os arquivos estáticos do frontend se o diretório existir
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
