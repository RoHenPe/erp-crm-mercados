"""Modelos de Dados do Sistema HelpDmais — Gestão Empresarial (ERP, CRM e PDV).

Estrutura de domínio:
1. Empresas e Controle de Acesso (`Tenant` / Empresa, `UsuarioSistema`, `Filial`)
2. Cadastros e Suprimentos (`Fornecedor`, `Produto`, `PedidoCompra`)
3. Operação de Estoque e Rastreabilidade (`EstoqueFilial`, `LoteValidade`, `MovimentacaoEstoque`)
4. Relacionamento com o Cliente (`ClienteCRM`, `TransacaoCashback`, `CampanhaCRM`)
5. Ponto de Venda (`SessaoCaixaPDV`, `VendaPDV`, `ItemVendaPDV`)
6. Gestão Financeira (`LancamentoFinanceiro`)
"""

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# Definição dos Cargos e Permissões de Acesso aos Aplicativos
MATRIZ_PERFIS_RBAC: dict[str, dict] = {
    "ADMINISTRADOR": {
        "codigo": "ADMINISTRADOR",
        "nome": "Administrador / Proprietário",
        "nivel_acesso": 5,
        "cor_badge": "indigo",
        "modulos_permitidos": [
            "dashboard",
            "pdv",
            "estoque",
            "compras",
            "crm",
            "financeiro",
            "configuracoes",
        ],
        "permissoes_acoes": [
            "GERENCIAR_EMPRESA",
            "GERENCIAR_USUARIOS",
            "GERENCIAR_UNIDADES",
            "VER_FINANCEIRO",
            "LANCAR_FINANCEIRO",
            "GERENCIAR_COMPRAS",
            "GERENCIAR_PRODUTOS",
            "OPERAR_PDV",
            "GERENCIAR_ESTOQUE",
            "GERENCIAR_CRM",
        ],
        "descricao": "Acesso completo a todos os aplicativos da empresa, configurações, unidades, equipe e resultados financeiros.",
    },
    "GERENTE": {
        "codigo": "GERENTE",
        "nome": "Gerente de Loja",
        "nivel_acesso": 4,
        "cor_badge": "emerald",
        "modulos_permitidos": [
            "dashboard",
            "pdv",
            "estoque",
            "compras",
            "crm",
        ],
        "permissoes_acoes": [
            "OPERAR_PDV",
            "GERENCIAR_PRODUTOS",
            "GERENCIAR_ESTOQUE",
            "GERENCIAR_COMPRAS",
            "GERENCIAR_CRM",
        ],
        "descricao": "Gestão diária da unidade: painel de vendas, frente de caixa, produtos, estoque, compras e atendimento ao cliente.",
    },
    "CAIXA": {
        "codigo": "CAIXA",
        "nome": "Operador de Caixa (PDV)",
        "nivel_acesso": 2,
        "cor_badge": "sky",
        "modulos_permitidos": [
            "pdv",
            "crm",
        ],
        "permissoes_acoes": [
            "OPERAR_PDV",
            "GERENCIAR_CRM",
        ],
        "descricao": "Operação do Ponto de Venda (abertura, registro de vendas, fechamento de caixa) e identificação/cadastro de clientes.",
    },
    "ESTOQUE_COMPRAS": {
        "codigo": "ESTOQUE_COMPRAS",
        "nome": "Estoquista & Comprador",
        "nivel_acesso": 3,
        "cor_badge": "amber",
        "modulos_permitidos": [
            "estoque",
            "compras",
        ],
        "permissoes_acoes": [
            "GERENCIAR_PRODUTOS",
            "GERENCIAR_ESTOQUE",
            "GERENCIAR_COMPRAS",
        ],
        "descricao": "Cadastro de produtos e fornecedores, pedidos de compra, recebimento de mercadorias, controle de lotes e inventário.",
    },
    "COMERCIAL_CRM": {
        "codigo": "COMERCIAL_CRM",
        "nome": "Atendimento & Marketing (CRM)",
        "nivel_acesso": 3,
        "cor_badge": "purple",
        "modulos_permitidos": [
            "dashboard",
            "crm",
        ],
        "permissoes_acoes": [
            "GERENCIAR_CRM",
        ],
        "descricao": "Gestão da carteira de clientes, programa de fidelidade, saldo de cashback e campanhas promocionais.",
    },
    "FINANCEIRO": {
        "codigo": "FINANCEIRO",
        "nome": "Analista Financeiro",
        "nivel_acesso": 4,
        "cor_badge": "rose",
        "modulos_permitidos": [
            "dashboard",
            "financeiro",
            "compras",
        ],
        "permissoes_acoes": [
            "VER_FINANCEIRO",
            "LANCAR_FINANCEIRO",
        ],
        "descricao": "Controle de contas a pagar e a receber, fluxo de caixa, despesas operacionais e demonstrativo de resultados (DRE).",
    },
}

# Aliases de compatibilidade
ALIASES_PERFIL: dict[str, str] = {
    "DIRETOR_HOLDING": "ADMINISTRADOR",
    "GERENTE_LOJA": "GERENTE",
    "OPERADOR_PDV": "CAIXA",
    "GESTOR_ESTOQUE_COMPRAS": "ESTOQUE_COMPRAS",
    "ANALISTA_CRM_MARKETING": "COMERCIAL_CRM",
    "CONTROLLER_FINANCEIRO": "FINANCEIRO",
}


def normalizar_perfil(codigo: str | None) -> str:
    if not codigo:
        return "CAIXA"
    c = codigo.strip().upper()
    c = ALIASES_PERFIL.get(c, c)
    return c if c in MATRIZ_PERFIS_RBAC else "CAIXA"


class SchemaMeta(Base):
    """Registro interno de migração de estrutura do banco de dados."""

    __tablename__ = "helpdmais_schema_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    versao_schema: Mapped[str] = mapped_column(String(40), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Tenant(Base):
    """Cadastro da Empresa (Comércio) na plataforma HelpDmais."""

    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(140), nullable=False)
    razao_social: Mapped[str] = mapped_column(String(180), nullable=False)
    cnpj_matriz: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    segmento_varejo: Mapped[str] = mapped_column(String(80), default="Supermercado & Varejo")
    cidade_uf: Mapped[str] = mapped_column(String(80), default="")
    telefone: Mapped[str] = mapped_column(String(40), default="")
    cor_tema: Mapped[str] = mapped_column(String(20), default="#714B67")
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UsuarioSistema(Base):
    """Usuário vinculado a uma Empresa e a um Cargo de acesso."""

    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int | None] = mapped_column(ForeignKey("filiais.id"), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    cargo: Mapped[str] = mapped_column(String(90), nullable=False)
    perfil_rbac: Mapped[str] = mapped_column(String(40), default="CAIXA", index=True)
    modulos_permitidos: Mapped[str] = mapped_column(
        String(255),
        default="dashboard,pdv,estoque,compras,crm,financeiro,configuracoes",
    )
    nivel_acesso: Mapped[int] = mapped_column(Integer, default=3)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    ultimo_acesso: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Filial(Base):
    """Unidade / Loja pertencente a uma Empresa."""

    __tablename__ = "filiais"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_filial_empresa_codigo"),
        UniqueConstraint("tenant_id", "cnpj", name="uq_filial_empresa_cnpj"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    codigo: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    bandeira: Mapped[str] = mapped_column(String(80), nullable=False, default="Loja")
    cnpj: Mapped[str] = mapped_column(String(30), nullable=False)
    cidade: Mapped[str] = mapped_column(String(80), nullable=False)
    gerente: Mapped[str] = mapped_column(String(100), nullable=False)
    meta_mensal: Mapped[float] = mapped_column(Float, default=100000.0)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)


class Fornecedor(Base):
    """Fornecedores cadastrados por uma Empresa."""

    __tablename__ = "fornecedores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "cnpj", name="uq_fornecedor_empresa_cnpj"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(120), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(30), nullable=False)
    categoria_principal: Mapped[str] = mapped_column(String(80), nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=3)
    telefone: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    avaliacao: Mapped[float] = mapped_column(Float, default=5.0)


class Produto(Base):
    """Catálogo de produtos da Empresa."""

    __tablename__ = "produtos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_produto_empresa_sku"),
        UniqueConstraint("tenant_id", "ean", name="uq_produto_empresa_ean"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    ean: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    departamento: Mapped[str] = mapped_column(String(80), nullable=False)
    unidade: Mapped[str] = mapped_column(String(10), default="UN")
    preco_custo: Mapped[float] = mapped_column(Float, nullable=False)
    preco_venda: Mapped[float] = mapped_column(Float, nullable=False)
    preco_clube_crm: Mapped[float] = mapped_column(Float, nullable=False)
    cashback_percentual: Mapped[float] = mapped_column(Float, default=1.0)
    estoque_minimo_padrao: Mapped[float] = mapped_column(Float, default=10.0)
    fornecedor_id: Mapped[int | None] = mapped_column(ForeignKey("fornecedores.id"), nullable=True)
    perecivel: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class EstoqueFilial(Base):
    """Saldo de estoque de um produto por unidade."""

    __tablename__ = "estoques_filial"
    __table_args__ = (
        UniqueConstraint("filial_id", "produto_id", name="uq_estoque_filial_produto"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade_atual: Mapped[float] = mapped_column(Float, default=0.0)
    estoque_minimo: Mapped[float] = mapped_column(Float, default=10.0)
    estoque_maximo: Mapped[float] = mapped_column(Float, default=500.0)
    ultima_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoteValidade(Base):
    """Controle de lotes e datas de vencimento por unidade."""

    __tablename__ = "lotes_validade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    numero_lote: Mapped[str] = mapped_column(String(60), nullable=False)
    data_fabricacao: Mapped[date] = mapped_column(Date, nullable=False)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantidade_lote: Mapped[float] = mapped_column(Float, default=0.0)
    status_lote: Mapped[str] = mapped_column(String(30), default="ATIVO")


class MovimentacaoEstoque(Base):
    """Histórico de entradas, saídas, transferências e ajustes de inventário."""

    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    observacao: Mapped[str] = mapped_column(String(255), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PedidoCompra(Base):
    """Pedidos de compra emitidos aos fornecedores."""

    __tablename__ = "pedidos_compra"
    __table_args__ = (
        UniqueConstraint("tenant_id", "numero_pedido", name="uq_pedido_empresa_numero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    numero_pedido: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    custo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="APROVADO")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClienteCRM(Base):
    """Cadastro de clientes e programa de fidelidade da Empresa."""

    __tablename__ = "clientes_crm"
    __table_args__ = (
        UniqueConstraint("tenant_id", "cpf", name="uq_cliente_empresa_cpf"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(25), index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    whatsapp: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    filial_preferida_id: Mapped[int | None] = mapped_column(ForeignKey("filiais.id"), nullable=True)
    segmento_rfm: Mapped[str] = mapped_column(String(30), default="NOVO")
    pontos_fidelidade: Mapped[int] = mapped_column(Integer, default=0)
    saldo_cashback: Mapped[float] = mapped_column(Float, default=0.0)
    total_gasto_historico: Mapped[float] = mapped_column(Float, default=0.0)
    total_compras_count: Mapped[int] = mapped_column(Integer, default=0)
    economia_acumulada_clube: Mapped[float] = mapped_column(Float, default=0.0)
    ultima_compra_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransacaoCashback(Base):
    """Histórico de créditos e resgates de cashback/pontos."""

    __tablename__ = "transacoes_cashback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes_crm.id"), nullable=False, index=True)
    venda_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    pontos: Mapped[int] = mapped_column(Integer, default=0)
    descricao: Mapped[str] = mapped_column(String(200), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampanhaCRM(Base):
    """Campanhas promocionais e ofertas para clientes."""

    __tablename__ = "campanhas_crm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(140), nullable=False)
    segmento_alvo: Mapped[str] = mapped_column(String(40), nullable=False)
    canal: Mapped[str] = mapped_column(String(40), default="WHATSAPP")
    desconto_extra_pct: Mapped[float] = mapped_column(Float, default=5.0)
    cashback_bonus_pct: Mapped[float] = mapped_column(Float, default=2.0)
    mensagem_template: Mapped[str] = mapped_column(Text, default="")
    clientes_impactados: Mapped[int] = mapped_column(Integer, default=0)
    conversao_estimada_pct: Mapped[float] = mapped_column(Float, default=15.0)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SessaoCaixaPDV(Base):
    """Controle de abertura e fechamento de caixa no Ponto de Venda."""

    __tablename__ = "sessoes_caixa_pdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    operador_nome: Mapped[str] = mapped_column(String(120), default="Operador")
    valor_abertura: Mapped[float] = mapped_column(Float, default=0.0)
    valor_fechamento: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_vendido: Mapped[float] = mapped_column(Float, default=0.0)
    qtd_vendas: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="ABERTO", index=True)
    aberta_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fechada_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class VendaPDV(Base):
    """Registro de vendas realizadas no Ponto de Venda."""

    __tablename__ = "vendas_pdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    numero_cupom: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    sessao_caixa_id: Mapped[int | None] = mapped_column(ForeignKey("sessoes_caixa_pdv.id"), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes_crm.id"), nullable=True, index=True)
    subtotal_bruto: Mapped[float] = mapped_column(Float, nullable=False)
    desconto_clube_crm: Mapped[float] = mapped_column(Float, default=0.0)
    cashback_utilizado: Mapped[float] = mapped_column(Float, default=0.0)
    valor_total_liquido: Mapped[float] = mapped_column(Float, nullable=False)
    cashback_gerado: Mapped[float] = mapped_column(Float, default=0.0)
    forma_pagamento: Mapped[str] = mapped_column(String(40), default="PIX")
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ItemVendaPDV(Base):
    """Itens de cada venda realizada no PDV."""

    __tablename__ = "itens_venda_pdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas_pdv.id"), nullable=False, index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False, index=True)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    preco_unitario_tabela: Mapped[float] = mapped_column(Float, nullable=False)
    preco_unitario_aplicado: Mapped[float] = mapped_column(Float, nullable=False)
    custo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal_item: Mapped[float] = mapped_column(Float, nullable=False)


class LancamentoFinanceiro(Base):
    """Lançamentos de receitas, custos e despesas operacionais da Empresa."""

    __tablename__ = "lancamentos_financeiros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), nullable=False, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    categoria_dre: Mapped[str] = mapped_column(String(60), nullable=False)
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="PAGO")
    data_competencia: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
