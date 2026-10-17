"""Modelos ORM Canônicos do ERP & CRM para Grupo de Mercados.

Abrange:
1. Multi-Loja / Holding (`Filial`)
2. Fornecedores e Catálogo de Produtos com Preço Clube CRM (`Fornecedor`, `Produto`)
3. Estoque por Filial, Lotes com Validade FEFO e Movimentações (`EstoqueFilial`, `LoteValidade`, `MovimentacaoEstoque`)
4. Pedidos de Compra (`PedidoCompra`)
5. CRM 360º: Clientes, Fidelidade, Cashback, Segmentação RFM e Campanhas (`ClienteCRM`, `TransacaoCashback`, `CampanhaCRM`)
6. Frente de Caixa / PDV Online (`VendaPDV`, `ItemVendaPDV`)
7. Financeiro e DRE Multi-Loja (`LancamentoFinanceiro`)
"""

from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Filial(Base):
    """Unidade do Grupo de Mercados (Matriz/CD, Hipermercado, Atacarejo, Express)."""

    __tablename__ = "filiais"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    bandeira: Mapped[str] = mapped_column(String(80), nullable=False)  # Ex: Hiper, Atacarejo, Express, CD
    cnpj: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    cidade: Mapped[str] = mapped_column(String(80), nullable=False)
    gerente: Mapped[str] = mapped_column(String(100), nullable=False)
    meta_mensal: Mapped[float] = mapped_column(Float, default=500000.0)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)


class Fornecedor(Base):
    """Fornecedores homologados do grupo supermercadista."""

    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[str] = mapped_column(String(120), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(25), unique=True, nullable=False)
    categoria_principal: Mapped[str] = mapped_column(String(80), nullable=False)
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, default=3)
    telefone: Mapped[str] = mapped_column(String(40), default="")
    avaliacao: Mapped[float] = mapped_column(Float, default=4.8)


class Produto(Base):
    """Catálogo centralizado de produtos com Preço Normal e Preço Clube CRM."""

    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    ean: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(160), nullable=False)
    departamento: Mapped[str] = mapped_column(String(80), nullable=False)  # Mercearia, Açougue, Hortifruti, Bebidas, Frios, Limpeza
    unidade: Mapped[str] = mapped_column(String(10), default="UN")  # UN, KG, CX, LT
    preco_custo: Mapped[float] = mapped_column(Float, nullable=False)
    preco_venda: Mapped[float] = mapped_column(Float, nullable=False)
    preco_clube_crm: Mapped[float] = mapped_column(Float, nullable=False)
    cashback_percentual: Mapped[float] = mapped_column(Float, default=2.0)
    fornecedor_id: Mapped[int | None] = mapped_column(ForeignKey("fornecedores.id"), nullable=True)
    perecivel: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)


class EstoqueFilial(Base):
    """Posição consolidada de estoque de um produto em uma filial específica."""

    __tablename__ = "estoques_filial"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade_atual: Mapped[float] = mapped_column(Float, default=0.0)
    estoque_minimo: Mapped[float] = mapped_column(Float, default=20.0)
    estoque_maximo: Mapped[float] = mapped_column(Float, default=500.0)
    ultima_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LoteValidade(Base):
    """Controle de lotes e validade (FEFO - First Expired, First Out) por filial."""

    __tablename__ = "lotes_validade"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    numero_lote: Mapped[str] = mapped_column(String(50), nullable=False)
    data_fabricacao: Mapped[date] = mapped_column(Date, nullable=False)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantidade_lote: Mapped[float] = mapped_column(Float, default=0.0)
    status_lote: Mapped[str] = mapped_column(String(30), default="ATIVO")  # ATIVO, ALERTA_VENCIMENTO, ESGOTADO, VENCIDO


class MovimentacaoEstoque(Base):
    """Histórico auditável de entradas, baixas de PDV, transferências e quebras."""

    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)  # ENTRADA_COMPRA, VENDA_PDV, TRANSFERENCIA_SAIDA, TRANSFERENCIA_ENTRADA, QUEBRA_PERDA
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    observacao: Mapped[str] = mapped_column(String(255), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PedidoCompra(Base):
    """Pedidos de abastecimento emitidos aos fornecedores para uma filial ou CD."""

    __tablename__ = "pedidos_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_pedido: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    custo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="APROVADO")  # PENDENTE, APROVADO, RECEBIDO, CANCELADO
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClienteCRM(Base):
    """Cadastro 360º do Clube de Fidelidade & CRM do Grupo de Mercados."""

    __tablename__ = "clientes_crm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cpf: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(140), nullable=False)
    whatsapp: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    filial_preferida_id: Mapped[int | None] = mapped_column(ForeignKey("filiais.id"), nullable=True)
    segmento_rfm: Mapped[str] = mapped_column(String(30), default="NOVO")  # DIAMANTE, OURO, PRATA, EM_RISCO, NOVO
    pontos_fidelidade: Mapped[int] = mapped_column(Integer, default=0)
    saldo_cashback: Mapped[float] = mapped_column(Float, default=0.0)
    total_gasto_historico: Mapped[float] = mapped_column(Float, default=0.0)
    total_compras_count: Mapped[int] = mapped_column(Integer, default=0)
    economia_acumulada_clube: Mapped[float] = mapped_column(Float, default=0.0)
    ultima_compra_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TransacaoCashback(Base):
    """Extrato de créditos e resgates de cashback/pontos do cliente no CRM."""

    __tablename__ = "transacoes_cashback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes_crm.id"), index=True)
    venda_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # CREDITO_COMPRA, RESGATE_PDV, BONUS_CAMPANHA
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    pontos: Mapped[int] = mapped_column(Integer, default=0)
    descricao: Mapped[str] = mapped_column(String(200), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CampanhaCRM(Base):
    """Campanhas de marketing e ofertas segmentadas do Clube de Mercados."""

    __tablename__ = "campanhas_crm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(140), nullable=False)
    segmento_alvo: Mapped[str] = mapped_column(String(40), nullable=False)  # TODOS, DIAMANTE, OURO, EM_RISCO, HORTIFRUTI, CHURRASCO
    canal: Mapped[str] = mapped_column(String(40), default="WHATSAPP_E_APP")
    desconto_extra_pct: Mapped[float] = mapped_column(Float, default=5.0)
    cashback_bonus_pct: Mapped[float] = mapped_column(Float, default=3.0)
    mensagem_template: Mapped[str] = mapped_column(Text, default="")
    clientes_impactados: Mapped[int] = mapped_column(Integer, default=0)
    conversao_estimada_pct: Mapped[float] = mapped_column(Float, default=18.5)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VendaPDV(Base):
    """Cabeçalho de venda realizada no Frente de Caixa (PDV Online)."""

    __tablename__ = "vendas_pdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    numero_cupom: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes_crm.id"), nullable=True, index=True)
    subtotal_bruto: Mapped[float] = mapped_column(Float, nullable=False)
    desconto_clube_crm: Mapped[float] = mapped_column(Float, default=0.0)
    cashback_utilizado: Mapped[float] = mapped_column(Float, default=0.0)
    valor_total_liquido: Mapped[float] = mapped_column(Float, nullable=False)
    cashback_gerado: Mapped[float] = mapped_column(Float, default=0.0)
    forma_pagamento: Mapped[str] = mapped_column(String(40), default="PIX")  # PIX, CARTAO_CREDITO, CARTAO_DEBITO, DINHEIRO, ALIMENTACAO
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class ItemVendaPDV(Base):
    """Itens individuais do cupom de venda do PDV."""

    __tablename__ = "itens_venda_pdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas_pdv.id"), index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), index=True)
    quantidade: Mapped[float] = mapped_column(Float, nullable=False)
    preco_unitario_tabela: Mapped[float] = mapped_column(Float, nullable=False)
    preco_unitario_aplicado: Mapped[float] = mapped_column(Float, nullable=False)
    custo_unitario: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal_item: Mapped[float] = mapped_column(Float, nullable=False)


class LancamentoFinanceiro(Base):
    """Contas a Pagar, Contas a Receber e base para o DRE Multi-Loja."""

    __tablename__ = "lancamentos_financeiros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filial_id: Mapped[int] = mapped_column(ForeignKey("filiais.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # RECEITA, DESPESA, CMV
    categoria_dre: Mapped[str] = mapped_column(String(60), nullable=False)  # RECEITA_VENDAS, CMV_MERCADORIAS, DESPESA_OPERACIONAL, FOLHA_PAGAMENTO, ENERGIA_ALUGUEL, IMPOSTOS
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(25), default="PAGO")  # PAGO, PENDENTE
    data_competencia: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
