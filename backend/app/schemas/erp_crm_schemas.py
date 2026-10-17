"""Schemas de Entrada e Saída da API HelpDmais."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 0. Cadastro de Empresa, Autenticação e Equipe
# ---------------------------------------------------------------------------
class RegistroComercioRequest(BaseModel):
    nome_fantasia: str = Field(..., min_length=2, max_length=140)
    razao_social: str = Field(..., min_length=2, max_length=180)
    cnpj_matriz: str = Field(..., min_length=11, max_length=30)
    segmento_varejo: str = Field(default="Supermercado & Varejo", max_length=80)
    cidade_uf: str = Field(..., min_length=2, max_length=80)
    telefone: str = Field(default="", max_length=40)
    cor_tema: str = Field(default="#714B67", max_length=20)
    # Dados da Unidade Matriz inicial
    nome_filial_matriz: str = Field(default="Matriz Principal", max_length=120)
    codigo_filial_matriz: str = Field(default="MATRIZ-01", max_length=30)
    bandeira_matriz: str = Field(default="Matriz", max_length=80)
    meta_mensal_matriz: float = Field(default=150000.0, ge=0.0)
    # Dados do Administrador
    admin_nome: str = Field(..., min_length=2, max_length=120)
    admin_email: str = Field(..., min_length=5, max_length=140)
    admin_senha: str = Field(..., min_length=6, max_length=80)
    admin_cargo: str = Field(default="Proprietário / Administrador", max_length=90)


class TenantBase(BaseModel):
    slug: str = Field(..., max_length=80)
    nome_fantasia: str = Field(..., max_length=140)
    razao_social: str = Field(..., max_length=180)
    cnpj_matriz: str = Field(..., max_length=30)
    segmento_varejo: str = Field(default="Supermercado & Varejo", max_length=80)
    cidade_uf: str = Field(default="", max_length=80)
    telefone: str = Field(default="", max_length=40)
    cor_tema: str = Field(default="#714B67", max_length=20)
    ativo: bool = True


class TenantResponse(TenantBase):
    id: int
    total_filiais: int = 0
    total_usuarios: int = 0
    total_produtos: int = 0
    total_clientes_crm: int = 0
    criado_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PerfilRBACInfo(BaseModel):
    codigo: str
    nome: str
    nivel_acesso: int
    cor_badge: str
    modulos_permitidos: list[str]
    permissoes_acoes: list[str]
    descricao: str


class UsuarioCreate(BaseModel):
    filial_id: int | None = None
    nome: str = Field(..., min_length=2, max_length=120)
    email: str = Field(..., min_length=5, max_length=140)
    senha: str = Field(..., min_length=6, max_length=80)
    cargo: str = Field(..., min_length=2, max_length=90)
    perfil_rbac: str = Field(default="CAIXA", max_length=40)
    ativo: bool = True


class UsuarioUpdateStatus(BaseModel):
    perfil_rbac: str | None = None
    filial_id: int | None = None
    cargo: str | None = None
    ativo: bool | None = None
    nova_senha: str | None = None


class UsuarioResponse(BaseModel):
    id: int
    tenant_id: int
    tenant_nome: str | None = None
    filial_id: int | None = None
    filial_nome: str | None = None
    nome: str
    email: str
    cargo: str
    perfil_rbac: str
    modulos_permitidos: list[str] = []
    permissoes_acoes: list[str] = []
    nivel_acesso: int = 3
    ativo: bool = True
    ultimo_acesso: datetime | None = None
    criado_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=140)
    senha: str = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# 1. Unidades / Filiais
# ---------------------------------------------------------------------------
class FilialCreate(BaseModel):
    codigo: str = Field(..., max_length=30)
    nome: str = Field(..., max_length=120)
    bandeira: str = Field(default="Loja", max_length=80)
    cnpj: str = Field(..., max_length=30)
    cidade: str = Field(..., max_length=80)
    gerente: str = Field(..., max_length=100)
    meta_mensal: float = Field(default=100000.0, ge=0.0)
    ativa: bool = True


class FilialResponse(FilialCreate):
    id: int
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    autenticado: bool
    token_sessao: str
    usuario: UsuarioResponse
    tenant: TenantResponse
    filiais: list[FilialResponse] = []
    perfil_detalhes: PerfilRBACInfo
    mensagem: str


# ---------------------------------------------------------------------------
# 2. Fornecedores
# ---------------------------------------------------------------------------
class FornecedorCreate(BaseModel):
    razao_social: str = Field(..., max_length=150)
    nome_fantasia: str = Field(..., max_length=120)
    cnpj: str = Field(..., max_length=30)
    categoria_principal: str = Field(..., max_length=80)
    prazo_entrega_dias: int = Field(default=3, ge=1)
    telefone: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=120)
    avaliacao: float = Field(default=5.0, ge=0.0, le=5.0)


class FornecedorResponse(FornecedorCreate):
    id: int
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 3. Produtos
# ---------------------------------------------------------------------------
class ProdutoCreate(BaseModel):
    sku: str = Field(..., max_length=40)
    ean: str = Field(..., max_length=30)
    nome: str = Field(..., max_length=160)
    departamento: str = Field(..., max_length=80)
    unidade: str = Field(default="UN", max_length=10)
    preco_custo: float = Field(..., gt=0.0)
    preco_venda: float = Field(..., gt=0.0)
    preco_clube_crm: float | None = Field(default=None, gt=0.0)
    cashback_percentual: float = Field(default=1.0, ge=0.0, le=100.0)
    estoque_minimo_padrao: float = Field(default=10.0, ge=0.0)
    fornecedor_id: int | None = None
    perecivel: bool = False
    ativo: bool = True
    estoque_inicial: float = Field(default=0.0, ge=0.0)
    filial_inicial_id: int | None = None
    numero_lote_inicial: str | None = None
    data_validade_inicial: date | None = None


class ProdutoResponse(BaseModel):
    id: int
    tenant_id: int
    sku: str
    ean: str
    nome: str
    departamento: str
    unidade: str
    preco_custo: float
    preco_venda: float
    preco_clube_crm: float
    cashback_percentual: float
    estoque_minimo_padrao: float = 10.0
    fornecedor_id: int | None = None
    perecivel: bool
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 4. Estoque & Lotes
# ---------------------------------------------------------------------------
class LoteValidadeResponse(BaseModel):
    id: int
    tenant_id: int
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
    tenant_id: int
    filial_id: int
    filial_nome: str | None = None
    produto_id: int
    produto_nome: str | None = None
    produto_sku: str | None = None
    produto_ean: str | None = None
    departamento: str | None = None
    unidade: str | None = "UN"
    preco_custo: float | None = 0.0
    preco_venda: float | None = 0.0
    preco_clube_crm: float | None = 0.0
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
    tipo: Literal["ENTRADA_COMPRA", "AJUSTE_POSITIVO", "QUEBRA_PERDA", "AJUSTE_INVENTARIO", "BAIXA"]
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
# 5. Pedidos de Compra
# ---------------------------------------------------------------------------
class PedidoCompraCreate(BaseModel):
    filial_id: int
    fornecedor_id: int
    produto_id: int
    quantidade: float = Field(..., gt=0.0)
    custo_unitario: float = Field(..., gt=0.0)


class PedidoCompraResponse(BaseModel):
    id: int
    tenant_id: int
    numero_pedido: str
    filial_id: int
    filial_nome: str | None = None
    fornecedor_id: int
    fornecedor_nome: str | None = None
    produto_id: int
    produto_nome: str | None = None
    quantidade: float
    custo_unitario: float
    valor_total: float
    status: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 6. Clientes & Campanhas (CRM)
# ---------------------------------------------------------------------------
class ClienteCRMCreate(BaseModel):
    cpf: str = Field(..., max_length=25)
    nome: str = Field(..., max_length=140)
    whatsapp: str = Field(default="", max_length=30)
    email: str = Field(default="", max_length=120)
    filial_preferida_id: int | None = None


class TransacaoCashbackResponse(BaseModel):
    id: int
    tenant_id: int
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
    tenant_id: int
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
    canal: str = Field(default="WHATSAPP", max_length=40)
    desconto_extra_pct: float = Field(default=5.0, ge=0.0)
    cashback_bonus_pct: float = Field(default=2.0, ge=0.0)
    mensagem_template: str = Field(default="")


class CampanhaCRMResponse(CampanhaCRMCreate):
    id: int
    tenant_id: int
    clientes_impactados: int
    conversao_estimada_pct: float
    ativa: bool
    criada_em: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# 7. Ponto de Venda (PDV)
# ---------------------------------------------------------------------------
class SessaoCaixaAbrirRequest(BaseModel):
    filial_id: int
    valor_abertura: float = Field(default=0.0, ge=0.0)


class SessaoCaixaFecharRequest(BaseModel):
    valor_fechamento: float = Field(..., ge=0.0)


class SessaoCaixaResponse(BaseModel):
    id: int
    tenant_id: int
    filial_id: int
    filial_nome: str | None = None
    usuario_id: int | None = None
    operador_nome: str
    valor_abertura: float
    valor_fechamento: float | None = None
    total_vendido: float
    qtd_vendas: int
    status: str
    aberta_em: datetime
    fechada_em: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


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
    tenant_id: int
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
# 8. Financeiro & Demonstrativo de Resultados (DRE)
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
    tenant_id: int
    filial_id: int
    filial_nome: str | None = None
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
# 9. Resumo de Indicadores (Painel)
# ---------------------------------------------------------------------------
class FilialMetaResumo(BaseModel):
    filial_id: int
    tenant_id: int
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
    software_nome: str = "HelpDmais"
    tenant_ativo_id: int
    tenant_ativo_nome: str
    faturamento_total: float
    lucro_liquido: float
    total_produtos: int = 0
    total_fornecedores: int = 0
    total_clientes_crm: int
    cashback_em_circulacao: float
    alertas_ruptura: list[dict[str, Any]]
    lotes_vencendo_15_dias: list[dict[str, Any]]
    vendas_por_filial_vs_meta: list[FilialMetaResumo]
    top_5_produtos: list[TopProdutoVendido]
    ultimas_vendas: list[dict[str, Any]]
