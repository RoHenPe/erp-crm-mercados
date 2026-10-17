"""Inicializador e Carga Inicial de Dados (Seed) para o ERP + CRM Grupo de Mercados."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from app.core.database import Base, SessionLocal, engine
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
from app.services.regras_negocio import calcular_segmento_rfm

logger = logging.getLogger(__name__)


def inicializar_e_popular_banco() -> None:
    """Cria as tabelas caso não existam e insere dados iniciais no banco caso esteja vazio."""
    logger.info("Criando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Verifica se já existem filiais cadastradas
        filial_existente = db.query(Filial).first()
        if filial_existente:
            logger.info("Banco de dados já contém registros. Seed ignorado.")
            return

        logger.info("Iniciando seed de dados supermercadistas completos...")

        # 1. Filiais (Multi-Loja)
        f1 = Filial(
            codigo="LOJA-01",
            nome="Hipermercado Central Matriz",
            bandeira="Hiper",
            cnpj="12.345.678/0001-90",
            cidade="São Paulo - SP",
            gerente="Carlos Eduardo Silva",
            meta_mensal=750000.0,
            ativa=True,
        )
        f2 = Filial(
            codigo="LOJA-02",
            nome="Atacarejo Econômico Sul",
            bandeira="Atacarejo",
            cnpj="12.345.678/0002-71",
            cidade="Campinas - SP",
            gerente="Mariana Albuquerque",
            meta_mensal=900000.0,
            ativa=True,
        )
        f3 = Filial(
            codigo="LOJA-03",
            nome="Express Bairro Jardins",
            bandeira="Express",
            cnpj="12.345.678/0003-52",
            cidade="São Paulo - SP",
            gerente="Roberto Santos",
            meta_mensal=280000.0,
            ativa=True,
        )
        f4 = Filial(
            codigo="CD-01",
            nome="Centro de Distribuição Logístico Cajamar",
            bandeira="CD",
            cnpj="12.345.678/0004-33",
            cidade="Cajamar - SP",
            gerente="Fernando Guimarães",
            meta_mensal=0.0,
            ativa=True,
        )
        db.add_all([f1, f2, f3, f4])
        db.flush()

        # 2. Fornecedores
        forn_ambev = Fornecedor(
            razao_social="Ambev Brasil Bebidas S/A",
            nome_fantasia="Ambev",
            cnpj="02.808.708/0001-07",
            categoria_principal="Bebidas",
            prazo_entrega_dias=2,
            telefone="(11) 3741-2000",
            avaliacao=4.9,
        )
        forn_jbs = Fornecedor(
            razao_social="JBS S/A Carnes e Frios",
            nome_fantasia="Friboi / Seara",
            cnpj="02.916.265/0001-00",
            categoria_principal="Açougue e Frios",
            prazo_entrega_dias=1,
            telefone="(11) 3144-4000",
            avaliacao=4.7,
        )
        forn_nestle = Fornecedor(
            razao_social="Nestlé Brasil Alimentos Ltda",
            nome_fantasia="Nestlé",
            cnpj="60.409.075/0001-52",
            categoria_principal="Mercearia e Laticínios",
            prazo_entrega_dias=3,
            telefone="(11) 5188-9000",
            avaliacao=4.9,
        )
        forn_unilever = Fornecedor(
            razao_social="Unilever Brasil Higiene e Limpeza",
            nome_fantasia="Unilever",
            cnpj="61.068.276/0001-04",
            categoria_principal="Limpeza e Higiene",
            prazo_entrega_dias=3,
            telefone="(11) 5645-3000",
            avaliacao=4.8,
        )
        forn_horti = Fornecedor(
            razao_social="Cooperativa Agrícola Holambra Hortifruti",
            nome_fantasia="Coop Holambra",
            cnpj="45.123.987/0001-11",
            categoria_principal="Hortifruti",
            prazo_entrega_dias=1,
            telefone="(19) 3802-1200",
            avaliacao=4.8,
        )
        db.add_all([forn_ambev, forn_jbs, forn_nestle, forn_unilever, forn_horti])
        db.flush()

        # 3. Produtos (com Preço Venda, Preço Clube CRM e Cashback %)
        produtos = [
            Produto(
                sku="PROD-001",
                ean="7891000100011",
                nome="Arroz Nobre Tipo 1 5kg",
                departamento="Mercearia",
                unidade="UN",
                preco_custo=19.50,
                preco_venda=27.90,
                preco_clube_crm=24.90,
                cashback_percentual=3.0,
                fornecedor_id=forn_nestle.id,
                perecivel=False,
                ativo=True,
            ),
            Produto(
                sku="PROD-002",
                ean="7891000100028",
                nome="Feijão Carioca Especial 1kg",
                departamento="Mercearia",
                unidade="UN",
                preco_custo=5.20,
                preco_venda=8.49,
                preco_clube_crm=7.29,
                cashback_percentual=2.5,
                fornecedor_id=forn_nestle.id,
                perecivel=False,
                ativo=True,
            ),
            Produto(
                sku="PROD-003",
                ean="7891000100035",
                nome="Picanha Bovina Grill Resfriada kg",
                departamento="Açougue",
                unidade="KG",
                preco_custo=48.00,
                preco_venda=74.90,
                preco_clube_crm=64.90,
                cashback_percentual=5.0,
                fornecedor_id=forn_jbs.id,
                perecivel=True,
                ativo=True,
            ),
            Produto(
                sku="PROD-004",
                ean="7891000100042",
                nome="Cerveja Puro Malte Premium Lata 350ml",
                departamento="Bebidas",
                unidade="UN",
                preco_custo=3.10,
                preco_venda=4.99,
                preco_clube_crm=4.19,
                cashback_percentual=4.0,
                fornecedor_id=forn_ambev.id,
                perecivel=False,
                ativo=True,
            ),
            Produto(
                sku="PROD-005",
                ean="7891000100059",
                nome="Leite Integral Longa Vida 1L",
                departamento="Laticínios",
                unidade="UN",
                preco_custo=3.40,
                preco_venda=5.19,
                preco_clube_crm=4.49,
                cashback_percentual=2.0,
                fornecedor_id=forn_nestle.id,
                perecivel=True,
                ativo=True,
            ),
            Produto(
                sku="PROD-006",
                ean="7891000100066",
                nome="Sabão Líquido Concentrado Lavagem Perfeita 3L",
                departamento="Limpeza",
                unidade="UN",
                preco_custo=28.00,
                preco_venda=43.90,
                preco_clube_crm=38.90,
                cashback_percentual=3.5,
                fornecedor_id=forn_unilever.id,
                perecivel=False,
                ativo=True,
            ),
            Produto(
                sku="PROD-007",
                ean="7891000100073",
                nome="Café Tradicional Torrado e Moído 500g",
                departamento="Mercearia",
                unidade="UN",
                preco_custo=12.80,
                preco_venda=18.90,
                preco_clube_crm=16.49,
                cashback_percentual=3.0,
                fornecedor_id=forn_nestle.id,
                perecivel=False,
                ativo=True,
            ),
            Produto(
                sku="PROD-008",
                ean="7891000100080",
                nome="Banana Prata Selecionada kg",
                departamento="Hortifruti",
                unidade="KG",
                preco_custo=3.50,
                preco_venda=6.99,
                preco_clube_crm=5.49,
                cashback_percentual=2.0,
                fornecedor_id=forn_horti.id,
                perecivel=True,
                ativo=True,
            ),
            Produto(
                sku="PROD-009",
                ean="7891000100097",
                nome="Queijo Mussarela Fatiado 500g",
                departamento="Frios",
                unidade="UN",
                preco_custo=16.50,
                preco_venda=26.90,
                preco_clube_crm=22.90,
                cashback_percentual=4.0,
                fornecedor_id=forn_jbs.id,
                perecivel=True,
                ativo=True,
            ),
            Produto(
                sku="PROD-010",
                ean="7891000100103",
                nome="Refrigerante Cola Pet 2L",
                departamento="Bebidas",
                unidade="UN",
                preco_custo=5.50,
                preco_venda=9.99,
                preco_clube_crm=8.49,
                cashback_percentual=2.0,
                fornecedor_id=forn_ambev.id,
                perecivel=False,
                ativo=True,
            ),
        ]
        db.add_all(produtos)
        db.flush()

        # 4. Estoques por Filial e Lotes com Validade FEFO
        hoje = date.today()
        for f in [f1, f2, f3, f4]:
            for p in produtos:
                # Quantidades padrão por filial
                multiplicador = 1.0 if f.bandeira == "Hiper" else (1.5 if f.bandeira == "Atacarejo" else (0.5 if f.bandeira == "Express" else 3.0))
                qtd_base = 80.0 * multiplicador

                # Produto em situação crítica proposital para demonstração de alertas
                if p.sku == "PROD-003" and f.id == f3.id:
                    qtd_base = 8.0  # Abaixo do mínimo de 15 -> CRITICO
                elif p.sku == "PROD-005" and f.id == f1.id:
                    qtd_base = 0.0  # RUPTURA

                estoque = EstoqueFilial(
                    filial_id=f.id,
                    produto_id=p.id,
                    quantidade_atual=qtd_base,
                    estoque_minimo=15.0 if f.bandeira != "CD" else 50.0,
                    estoque_maximo=300.0 * multiplicador,
                    ultima_atualizacao=datetime.utcnow(),
                )
                db.add(estoque)

                # Lotes de Validade
                if qtd_base > 0:
                    # Lote 1: lote mais novo
                    lote1 = LoteValidade(
                        filial_id=f.id,
                        produto_id=p.id,
                        numero_lote=f"LT-{p.sku}-A{f.id}",
                        data_fabricacao=hoje - timedelta(days=20),
                        data_validade=hoje + timedelta(days=90),
                        quantidade_lote=round(qtd_base * 0.7, 1),
                        status_lote="ATIVO",
                    )
                    db.add(lote1)

                    # Lote 2: lote com vencimento próximo (<= 15 dias) para produtos perecíveis
                    dias_venc = 7 if (p.perecivel and f.id in (f1.id, f2.id)) else 45
                    status_l = "ALERTA_VENCIMENTO" if dias_venc <= 15 else "ATIVO"
                    lote2 = LoteValidade(
                        filial_id=f.id,
                        produto_id=p.id,
                        numero_lote=f"LT-{p.sku}-B{f.id}",
                        data_fabricacao=hoje - timedelta(days=40),
                        data_validade=hoje + timedelta(days=dias_venc),
                        quantidade_lote=round(qtd_base * 0.3, 1),
                        status_lote=status_l,
                    )
                    db.add(lote2)

        # 5. Clientes CRM & Segmentação RFM
        clientes = [
            ClienteCRM(
                cpf="111.222.333-44",
                nome="Ana Paula Guimarães",
                whatsapp="(11) 98765-4321",
                email="ana.guimaraes@email.com",
                filial_preferida_id=f1.id,
                segmento_rfm=calcular_segmento_rfm(2850.0, 18),
                pontos_fidelidade=2850,
                saldo_cashback=45.80,
                total_gasto_historico=2850.0,
                total_compras_count=18,
                economia_acumulada_clube=340.50,
                ultima_compra_em=datetime.utcnow() - timedelta(days=1),
            ),
            ClienteCRM(
                cpf="222.333.444-55",
                nome="Marcos Vinicius de Souza",
                whatsapp="(19) 99123-4567",
                email="marcos.souza@email.com",
                filial_preferida_id=f2.id,
                segmento_rfm=calcular_segmento_rfm(1420.0, 9),
                pontos_fidelidade=1420,
                saldo_cashback=28.40,
                total_gasto_historico=1420.0,
                total_compras_count=9,
                economia_acumulada_clube=165.00,
                ultima_compra_em=datetime.utcnow() - timedelta(days=3),
            ),
            ClienteCRM(
                cpf="333.444.555-66",
                nome="Juliana Mendes de Freitas",
                whatsapp="(11) 97654-3210",
                email="juliana.mendes@email.com",
                filial_preferida_id=f3.id,
                segmento_rfm=calcular_segmento_rfm(450.0, 4),
                pontos_fidelidade=450,
                saldo_cashback=12.20,
                total_gasto_historico=450.0,
                total_compras_count=4,
                economia_acumulada_clube=52.00,
                ultima_compra_em=datetime.utcnow() - timedelta(days=6),
            ),
            ClienteCRM(
                cpf="444.555.666-77",
                nome="Lucas Carvalho Pereira",
                whatsapp="(11) 96543-2109",
                email="lucas.carvalho@email.com",
                filial_preferida_id=f1.id,
                segmento_rfm=calcular_segmento_rfm(120.0, 1),
                pontos_fidelidade=120,
                saldo_cashback=3.50,
                total_gasto_historico=120.0,
                total_compras_count=1,
                economia_acumulada_clube=14.00,
                ultima_compra_em=datetime.utcnow() - timedelta(days=15),
            ),
        ]
        db.add_all(clientes)
        db.flush()

        # 6. Campanhas CRM
        campanhas = [
            CampanhaCRM(
                titulo="Festival de Carnes & Cervejas Especiais",
                segmento_alvo="DIAMANTE",
                canal="WHATSAPP_E_APP",
                desconto_extra_pct=7.0,
                cashback_bonus_pct=5.0,
                mensagem_template="Olá {nome}! Exclusivo para Clientes Diamante: 7% OFF na Picanha Grill e 5% de cashback extra!",
                clientes_impactados=184,
                conversao_estimada_pct=26.4,
                ativa=True,
            ),
            CampanhaCRM(
                titulo="Quarta do Hortifruti & Saúde",
                segmento_alvo="TODOS",
                canal="WHATSAPP_E_APP",
                desconto_extra_pct=10.0,
                cashback_bonus_pct=3.0,
                mensagem_template="Quarta é dia da Feira Fresca no Grupo Mercados! Frutas e verduras selecionadas com Preço Clube!",
                clientes_impactados=1250,
                conversao_estimada_pct=19.8,
                ativa=True,
            ),
            CampanhaCRM(
                titulo="Resgate seu Cashback em Dobro",
                segmento_alvo="OURO",
                canal="WHATSAPP_E_APP",
                desconto_extra_pct=5.0,
                cashback_bonus_pct=4.0,
                mensagem_template="Você possui saldo de cashback disponível! Utilize neste final de semana no Hipermercado.",
                clientes_impactados=420,
                conversao_estimada_pct=22.1,
                ativa=True,
            ),
        ]
        db.add_all(campanhas)

        # 7. Pedidos de Compra Iniciais
        ped1 = PedidoCompra(
            numero_pedido="PC-2026-001",
            filial_id=f1.id,
            fornecedor_id=forn_ambev.id,
            produto_id=produtos[3].id,  # Cerveja
            quantidade=500.0,
            custo_unitario=3.10,
            valor_total=1550.0,
            status="RECEBIDO",
            criado_em=datetime.utcnow() - timedelta(days=5),
        )
        ped2 = PedidoCompra(
            numero_pedido="PC-2026-002",
            filial_id=f2.id,
            fornecedor_id=forn_jbs.id,
            produto_id=produtos[2].id,  # Picanha
            quantidade=200.0,
            custo_unitario=48.00,
            valor_total=9600.0,
            status="APROVADO",
            criado_em=datetime.utcnow() - timedelta(days=1),
        )
        db.add_all([ped1, ped2])

        # 8. Lançamentos Financeiros (DRE Inicial)
        db.add_all([
            # Receitas de Vendas
            LancamentoFinanceiro(
                filial_id=f1.id,
                tipo="RECEITA",
                categoria_dre="RECEITA_VENDAS",
                descricao="Faturamento Vendas PDV Balcão - Loja 01",
                valor=420500.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f2.id,
                tipo="RECEITA",
                categoria_dre="RECEITA_VENDAS",
                descricao="Faturamento Vendas PDV Balcão - Atacarejo Sul",
                valor=535200.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f3.id,
                tipo="RECEITA",
                categoria_dre="RECEITA_VENDAS",
                descricao="Faturamento Vendas PDV Balcão - Express Jardins",
                valor=178900.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            # Impostos
            LancamentoFinanceiro(
                filial_id=f1.id,
                tipo="DESPESA",
                categoria_dre="IMPOSTOS",
                descricao="ICMS / PIS / COFINS Vendas Loja 01",
                valor=38200.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f2.id,
                tipo="DESPESA",
                categoria_dre="IMPOSTOS",
                descricao="ICMS / PIS / COFINS Vendas Loja 02",
                valor=46800.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f3.id,
                tipo="DESPESA",
                categoria_dre="IMPOSTOS",
                descricao="ICMS / PIS / COFINS Vendas Loja 03",
                valor=15200.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            # CMV
            LancamentoFinanceiro(
                filial_id=f1.id,
                tipo="CMV",
                categoria_dre="CMV_MERCADORIAS",
                descricao="CMV de Mercadorias Vendidas Loja 01",
                valor=285000.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f2.id,
                tipo="CMV",
                categoria_dre="CMV_MERCADORIAS",
                descricao="CMV de Mercadorias Vendidas Loja 02",
                valor=375000.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f3.id,
                tipo="CMV",
                categoria_dre="CMV_MERCADORIAS",
                descricao="CMV de Mercadorias Vendidas Loja 03",
                valor=119000.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            # Despesas Operacionais (Folha, Energia/Aluguel e Operacionais)
            LancamentoFinanceiro(
                filial_id=f1.id,
                tipo="DESPESA",
                categoria_dre="FOLHA_PAGAMENTO",
                descricao="Folha de Pagamento Funcionários Loja 01",
                valor=42000.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f1.id,
                tipo="DESPESA",
                categoria_dre="ENERGIA_ALUGUEL",
                descricao="Aluguel de Imóvel e Conta de Luz Loja 01",
                valor=21500.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f2.id,
                tipo="DESPESA",
                categoria_dre="FOLHA_PAGAMENTO",
                descricao="Folha de Pagamento Funcionários Loja 02",
                valor=48000.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f2.id,
                tipo="DESPESA",
                categoria_dre="ENERGIA_ALUGUEL",
                descricao="Energia Elétrica de Câmaras Frias Loja 02",
                valor=27300.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f3.id,
                tipo="DESPESA",
                categoria_dre="FOLHA_PAGAMENTO",
                descricao="Folha de Pagamento Loja 03",
                valor=16500.0,
                status="PAGO",
                data_competencia=hoje,
            ),
            LancamentoFinanceiro(
                filial_id=f3.id,
                tipo="DESPESA",
                categoria_dre="ENERGIA_ALUGUEL",
                descricao="Aluguel e Condomínio Jardins",
                valor=14200.0,
                status="PAGO",
                data_competencia=hoje,
            ),
        ])

        db.commit()
        logger.info("Seed concluído com sucesso!")
    except Exception as exc:
        db.rollback()
        logger.exception("Erro ao executar seed de dados: %s", exc)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    inicializar_e_popular_banco()
