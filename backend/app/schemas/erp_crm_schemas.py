"""Schemas Pydantic para validação e serialização da API ERP + CRM."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Filiais
# ---------------------------------------------------------------------------
class FilialBase(BaseModel):
    codigo: str = Field(..., max_length=20, examples=["CD-01", "LOJA-01"])
    nome: str = Field(..., max_length=120, examples=["Hipermercado Matriz Central"])
    bandeira: str = Field(..., max_length=80, examples=["Hiper", "Atacarejo", "Express", "CD"])
    cnpj: str = Field(..., max_length=25, examples=["12.345.678/0001-90"])
    cidade: str = Field(..., max_length=80, examples=["São Paulo - SP"])
    gerente: str = Field(..., max_length=100, examples=["Carlos Silva"])
    meta_mensal: float = Field(default=500000.0, ge=0.0)
    ativa: bool = True


class FilialCreate(FilialBase):
    pass


class FilialResponse(FilialBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Fornecedores
# ---------------------------------------------------------------------------
class FornecedorBase(BaseModel):
    razao_social: str = Field(..., max_length=150)
    nome_fantasia: str = Field(..., max_length=120)
    cnpj: str = Field(..., max_length=25)
    categoria_principal: str = Field(..., max_length=80)
    prazo_entrega_dias: int = Field(default=3, ge=1)
    telefone: str = Field(default="", max_length=40)
    avaliacao: float = Field(default=4.8, ge=0.0, le=5.0)


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorResponse(FornecedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Produtos
# ---------------------------------------------------------------------------
class ProdutoBase(BaseModel):
    sku: str = Field(..., max_length=30)
    ean: str = Field(..., max_length=20)
    nome: str = Field(..., max_length=160)
    departamento: str = Field(..., max_length=80)
    unidade: str = Field(default="UN", max_length=10)
    preco_custo: float = Field(..., gt=0.0)
    preco_venda: float = Field(..., gt=0.0)
    preco_clube_crm: float = Field(..., gt=0.0)
    cashback_percentual: float = Field(default=2.0, ge=0.0, le=100.0)
    fornecedor_id: int | None = None
    perecivel: bool = False
    ativo: bool = True


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoResponse(ProdutoBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Lotes & Estoque
# ---------------------------------------------------------------------------
class LoteValidadeResponse(BaseModel):
    id: int
    filial_id: int
    produto_id: int
    numero_lote: str
    data_fabricacao: date
    data_validade: date
    quantidade_lote: float
    status_lote: str
    dias_para_vencer: int | None = None

    model_config = ConfigDict(from_attributes=True)


class EstoqueItemResponse(BaseModel):
    id: int
    filial_id: int
    filial_nome: str | None = None
    produto_id: int
    produto_nome: str | None = None
    produto_sku: str | None = None
    departamento: str | None = None
    unidade: str | None = "UN"
    preco_custo: float | None = 0.0
    preco_venda: float | None = 0.0
    quantidade_atual: float
    estoque_minimo: float
    estoque_maximo: float
    status: Literal["NORMAL", "CRITICO", "RUPTURA"]
    lotes_validade: list[LoteValidadeResponse] = []
    ultima_atualizacao: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EstoqueMovimentoRequest(BaseModel):
    filial_id: int
    produto_id: int
    tipo: Literal["ENTRADA_COMPRA", "QUEBRA_PERDA", "AJUSTE_INVENTARIO"]
    quantidade: float = Field(..., gt=0.0)
    observacao: str = Field(default="", max_length=255)
    numero_lote: str | None = None
    data_fabricacao: date | None = None
    data_validade: date | None = None


class EstoqueTransferenciaRequest(BaseModel):
    filial_origem_id: int
    filial_destino_id: int
    produto_id: int
    quantidade: float = Field(..., gt=0.0)
    observacao: str = Field(default="", max_length=255)


# ---------------------------------------------------------------------------
# Pedidos de Compra
# ---------------------------------------------------------------------------
class PedidoCompraCreate(BaseModel):
    filial_id: int
    fornecedor_id: int
    produto_id: int
    quantidade: float = Field(..., gt=0.0)
    custo_unitario: float = Field(..., gt=0.0)


class PedidoCompraResponse(BaseModel):
    id: int
    numero_pedido: str
    filial_id: int
    fornecedor_id: int
    produto_id: int
    quantidade: float
    custo_unitario: float
    valor_total: float
    status: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CRM: Clientes & Campanhas
# ---------------------------------------------------------------------------
class ClienteCRMCreate(BaseModel):
    cpf: str = Field(..., max_length=20)
    nome: str = Field(..., max_length=140)
    whatsapp: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=120)
    filial_preferida_id: int | None = None


class TransacaoCashbackResponse(BaseModel):
    id: int
    cliente_id: int
    venda_id: int | None = None
    tipo: str
    valor: float
    pontos: int
    descricao: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteCRMResponse(BaseModel):
    id: int
    cpf: str
    nome: str
    whatsapp: str
    email: str
    filial_preferida_id: int | None = None
    segmento_rfm: str
    pontos_fidelidade: int
    saldo_cashback: float
    total_gasto_historico: float
    total_compras_count: int
    economia_acumulada_clube: float
    ultima_compra_em: datetime | None = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class CampanhaCRMCreate(BaseModel):
    titulo: str = Field(..., max_length=140)
    segmento_alvo: str = Field(default="TODOS", max_length=40)
    canal: str = Field(default="WHATSAPP_E_APP", max_length=40)
    desconto_extra_pct: float = Field(default=5.0, ge=0.0)
    cashback_bonus_pct: float = Field(default=3.0, ge=0.0)
    mensagem_template: str = Field(default="")
    clientes_impactados: int = Field(default=0, ge=0)
    conversao_estimada_pct: float = Field(default=18.5, ge=0.0)


class CampanhaCRMResponse(CampanhaCRMCreate):
    id: int
    ativa: bool
    criada_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# PDV: Vendas & Itens
# ---------------------------------------------------------------------------
class ItemVendaRequest(BaseModel):
    produto_id: int
    quantidade: float = Field(..., gt=0.0)


class VendaPDVRequest(BaseModel):
    filial_id: int
    itens: list[ItemVendaRequest]
    cpf_cliente: str | None = None
    usar_cashback: float = Field(default=0.0, ge=0.0)
    forma_pagamento: Literal["PIX", "CARTAO_CREDITO", "CARTAO_DEBITO", "DINHEIRO", "ALIMENTACAO"] = "PIX"


class ItemVendaDetalhe(BaseModel):
    produto_id: int
    nome: str
    sku: str
    quantidade: float
    unidade: str
    preco_tabela: float
    preco_aplicado: float
    desconto_clube: float
    subtotal: float
    cashback_gerado: float


class VendaPDVResponse(BaseModel):
    venda_id: int
    numero_cupom: str
    filial_id: int
    filial_nome: str
    cliente_id: int | None = None
    cliente_nome: str
    cpf_cliente: str | None = None
    segmento_rfm: str | None = None
    subtotal_bruto: float
    desconto_clube_crm: float
    cashback_utilizado: float
    valor_total_liquido: float
    cashback_gerado: float
    pontos_ganhos: int
    novo_saldo_cashback: float | None = None
    forma_pagamento: str
    cmv_total: float
    itens: list[ItemVendaDetalhe] = []
    data_hora: str


# ---------------------------------------------------------------------------
# Financeiro & DRE
# ---------------------------------------------------------------------------
class LancamentoFinanceiroCreate(BaseModel):
    filial_id: int
    tipo: Literal["RECEITA", "DESPESA", "CMV"]
    categoria_dre: Literal[
        "RECEITA_VENDAS",
        "CMV_MERCADORIAS",
        "DESPESA_OPERACIONAL",
        "FOLHA_PAGAMENTO",
        "ENERGIA_ALUGUEL",
        "IMPOSTOS",
    ]
    descricao: str = Field(..., max_length=200)
    valor: float = Field(..., gt=0.0)
    status: Literal["PAGO", "PENDENTE"] = "PAGO"
    data_competencia: date | None = None


class LancamentoFinanceiroResponse(BaseModel):
    id: int
    filial_id: int
    tipo: str
    categoria_dre: str
    descricao: str
    valor: float
    status: str
    data_competencia: date
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class DREBreakdownFilial(BaseModel):
    filial_id: int
    filial_nome: str
    receita_bruta: float
    impostos: float
    receita_liquida: float
    cmv: float
    lucro_bruto: float
    margem_bruta_pct: float
    despesas_operacionais: float
    ebitda_lucro_liquido: float
    margem_liquida_pct: float


class DREResponse(BaseModel):
    receita_bruta: float
    impostos: float
    receita_liquida: float
    cmv: float
    lucro_bruto: float
    margem_bruta_pct: float
    despesas_operacionais: float
    ebitda_lucro_liquido: float
    margem_liquida_pct: float
    detalhes_despesas: dict[str, float]
    por_filial: list[DREBreakdownFilial] = []


# ---------------------------------------------------------------------------
# Dashboard & Agentes Status
# ---------------------------------------------------------------------------
class FilialMetaResumo(BaseModel):
    filial_id: int
    nome: str
    bandeira: str
    vendas_mes: float
    meta_mensal: float
    atingimento_pct: float


class TopProdutoVendido(BaseModel):
    produto_id: int
    nome: str
    departamento: str
    quantidade_vendida: float
    total_faturado: float


class DashboardResumoResponse(BaseModel):
    faturamento_total: float
    lucro_liquido: float
    total_clientes_crm: int
    cashback_em_circulacao: float
    alertas_ruptura: list[dict[str, Any]]
    lotes_vencendo_15_dias: list[dict[str, Any]]
    vendas_por_filial_vs_meta: list[FilialMetaResumo]
    top_5_produtos: list[TopProdutoVendido]
    ultimas_vendas: list[dict[str, Any]]


class AgentesStatusResponse(BaseModel):
    status: str
    tiers: dict[str, Any] = {}
    tiers_crewai: dict[str, Any] = {}
    postgres_host: str
    postgres_conectado: bool
    modo_banco: str
    ultimas_linhas_log: list[str]
    timestamp: str

