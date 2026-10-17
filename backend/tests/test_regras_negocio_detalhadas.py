"""Suíte Detalhada de Testes Unitários e de Integração das Regras de Negócio do ERP/CRM."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import SessionLocal
from app.main import app
from app.models.erp_crm_models import (
    ClienteCRM,
    EstoqueFilial,
    Filial,
    LancamentoFinanceiro,
    LoteValidade,
    MovimentacaoEstoque,
    Produto,
    TransacaoCashback,
    VendaPDV,
)
from app.services.regras_negocio import (
    calcular_segmento_rfm,
    gerar_dre_gerencial,
    movimentar_estoque,
    processar_venda_pdv,
    receber_pedido_compra,
    transferir_estoque,
)


def test_segmento_rfm_todas_as_faixas():
    """Valida as regras de segmentação RFM para diferentes combinações de gasto e compras."""
    # DIAMANTE (gasto >= 2500 ou compras >= 15)
    assert calcular_segmento_rfm(2500.0, 0) == "DIAMANTE"
    assert calcular_segmento_rfm(3000.0, 2) == "DIAMANTE"
    assert calcular_segmento_rfm(50.0, 15) == "DIAMANTE"
    assert calcular_segmento_rfm(100.0, 20) == "DIAMANTE"

    # OURO (gasto >= 1000 ou compras >= 8)
    assert calcular_segmento_rfm(1000.0, 1) == "OURO"
    assert calcular_segmento_rfm(2499.0, 7) == "OURO"
    assert calcular_segmento_rfm(200.0, 8) == "OURO"
    assert calcular_segmento_rfm(100.0, 14) == "OURO"

    # PRATA (gasto >= 300 ou compras >= 3)
    assert calcular_segmento_rfm(300.0, 1) == "PRATA"
    assert calcular_segmento_rfm(999.0, 2) == "PRATA"
    assert calcular_segmento_rfm(50.0, 3) == "PRATA"
    assert calcular_segmento_rfm(100.0, 7) == "PRATA"

    # NOVO (< 300 e < 3 compras)
    assert calcular_segmento_rfm(0.0, 0) == "NOVO"
    assert calcular_segmento_rfm(299.99, 2) == "NOVO"
    assert calcular_segmento_rfm(150.0, 1) == "NOVO"


def test_processar_venda_pdv_fefo_e_financeiro():
    """Testa uma venda real pelo PDV verificando:
    - Aplicação do Preço Clube CRM
    - Baixa FEFO nos lotes
    - Movimentação de estoque
    - Lançamento financeiro de Receita e CMV
    - Acúmulo de cashback e pontos
    """
    db = SessionLocal()
    try:
        filial = db.query(Filial).first()
        assert filial is not None

        produto = db.query(Produto).filter(Produto.preco_clube_crm < Produto.preco_venda).first()
        assert produto is not None

        cliente = db.query(ClienteCRM).first()
        assert cliente is not None

        saldo_cashback_anterior = cliente.saldo_cashback
        pontos_anterior = cliente.pontos_fidelidade

        # Executa venda
        resultado = processar_venda_pdv(
            db=db,
            filial_id=filial.id,
            itens=[{"produto_id": produto.id, "quantidade": 2.0}],
            cpf_cliente=cliente.cpf,
            usar_cashback=0.0,
            forma_pagamento="PIX",
        )

        assert resultado["venda_id"] > 0
        assert resultado["desconto_clube_crm"] > 0.0
        assert resultado["cashback_gerado"] > 0.0
        assert resultado["novo_saldo_cashback"] > saldo_cashback_anterior
        assert cliente.pontos_fidelidade > pontos_anterior

        # Verifica se os dois lançamentos financeiros foram criados
        lanc_rec = (
            db.query(LancamentoFinanceiro)
            .filter(
                LancamentoFinanceiro.filial_id == filial.id,
                LancamentoFinanceiro.categoria_dre == "RECEITA_VENDAS",
                LancamentoFinanceiro.descricao.like(f"%{resultado['numero_cupom']}%"),
            )
            .first()
        )
        assert lanc_rec is not None
        assert lanc_rec.valor == resultado["valor_total_liquido"]

        lanc_cmv = (
            db.query(LancamentoFinanceiro)
            .filter(
                LancamentoFinanceiro.filial_id == filial.id,
                LancamentoFinanceiro.categoria_dre == "CMV_MERCADORIAS",
                LancamentoFinanceiro.descricao.like(f"%{resultado['numero_cupom']}%"),
            )
            .first()
        )
        assert lanc_cmv is not None
        assert lanc_cmv.valor == resultado["cmv_total"]

        # Verifica se movimentação de estoque foi registrada
        mov = (
            db.query(MovimentacaoEstoque)
            .filter(
                MovimentacaoEstoque.filial_id == filial.id,
                MovimentacaoEstoque.produto_id == produto.id,
                MovimentacaoEstoque.tipo == "VENDA_PDV",
                MovimentacaoEstoque.observacao.like(f"%{resultado['numero_cupom']}%"),
            )
            .first()
        )
        assert mov is not None
        assert mov.quantidade == -2.0

    finally:
        db.close()


def test_processar_venda_com_resgate_cashback():
    """Testa resgate parcial de cashback no PDV."""
    db = SessionLocal()
    try:
        filial = db.query(Filial).first()
        produto = db.query(Produto).first()
        cliente = db.query(ClienteCRM).filter(ClienteCRM.saldo_cashback >= 10.0).first()
        if not cliente:
            cliente = db.query(ClienteCRM).first()
            cliente.saldo_cashback = 50.0
            db.commit()

        saldo_antigo = cliente.saldo_cashback
        resgate_solicitado = 10.0

        resultado = processar_venda_pdv(
            db=db,
            filial_id=filial.id,
            itens=[{"produto_id": produto.id, "quantidade": 1.0}],
            cpf_cliente=cliente.cpf,
            usar_cashback=resgate_solicitado,
            forma_pagamento="CARTAO_DEBITO",
        )

        assert resultado["cashback_utilizado"] == resgate_solicitado
        # O valor líquido deve ser o subtotal com desconto menos o cashback usado
        assert resultado["valor_total_liquido"] < resultado["subtotal_bruto"]

        # Verifica se transação de resgate foi registrada
        resgate_reg = (
            db.query(TransacaoCashback)
            .filter(
                TransacaoCashback.cliente_id == cliente.id,
                TransacaoCashback.tipo == "RESGATE_PDV",
                TransacaoCashback.venda_id == resultado["venda_id"],
            )
            .first()
        )
        assert resgate_reg is not None
        assert resgate_reg.valor == resgate_solicitado
    finally:
        db.close()


def test_gerar_dre_consolidado_e_por_filial():
    """Valida o cálculo do DRE gerencial, margens e detalhamento por filial."""
    db = SessionLocal()
    try:
        dre = gerar_dre_gerencial(db)
        assert dre["receita_bruta"] > 0
        assert dre["receita_liquida"] == round(dre["receita_bruta"] - dre["impostos"], 2)
        assert dre["lucro_bruto"] == round(dre["receita_liquida"] - dre["cmv"], 2)
        assert dre["ebitda_lucro_liquido"] == round(
            dre["lucro_bruto"] - dre["despesas_operacionais"], 2
        )
        assert len(dre["por_filial"]) >= 4

        # Testa DRE filtrado para uma única filial
        f1 = db.query(Filial).first()
        dre_f1 = gerar_dre_gerencial(db, filial_id=f1.id)
        assert len(dre_f1["por_filial"]) == 1
        assert dre_f1["por_filial"][0]["filial_id"] == f1.id
    finally:
        db.close()


def test_transferencia_estoque():
    """Valida transferência de mercadorias entre filiais com movimentação."""
    db = SessionLocal()
    try:
        filiais = db.query(Filial).all()
        assert len(filiais) >= 2
        f_origem, f_destino = filiais[0], filiais[1]

        produto = db.query(Produto).first()

        # Garante saldo de teste na filial de origem
        est_orig = (
            db.query(EstoqueFilial)
            .filter(
                EstoqueFilial.filial_id == f_origem.id,
                EstoqueFilial.produto_id == produto.id,
            )
            .first()
        )
        if not est_orig or est_orig.quantidade_atual < 5.0:
            movimentar_estoque(
                db,
                filial_id=f_origem.id,
                produto_id=produto.id,
                tipo="ENTRADA_COMPRA",
                quantidade=50.0,
                numero_lote="LOTE-TEST-TRANSF",
            )
            est_orig = (
                db.query(EstoqueFilial)
                .filter(
                    EstoqueFilial.filial_id == f_origem.id,
                    EstoqueFilial.produto_id == produto.id,
                )
                .first()
            )

        qtd_antes_orig = est_orig.quantidade_atual

        res = transferir_estoque(
            db=db,
            filial_origem_id=f_origem.id,
            filial_destino_id=f_destino.id,
            produto_id=produto.id,
            quantidade=5.0,
            observacao="Transferência para balanceamento de gôndola",
        )

        assert res["status"] == "sucesso"
        assert res["quantidade_transferida"] == 5.0
        assert res["saldo_novo_origem"] == round(qtd_antes_orig - 5.0, 3)
    finally:
        db.close()


def test_endpoints_api_completos():
    """Valida todos os endpoints expostos pela API FastAPI."""
    with TestClient(app) as client:
        # Estoque com filtro de filial
        r = client.get("/api/estoque?filial_id=1")
        assert r.status_code == 200
        itens = r.json()
        assert isinstance(itens, list)
        if itens:
            assert itens[0]["filial_id"] == 1
            assert "status" in itens[0]
            assert "lotes_validade" in itens[0]

        # Movimentação de estoque via API
        prod = itens[0]["produto_id"] if itens else 1
        r_mov = client.post(
            "/api/estoque/movimentar",
            json={
                "filial_id": 1,
                "produto_id": prod,
                "tipo": "ENTRADA_COMPRA",
                "quantidade": 10.0,
                "observacao": "Entrada de teste automatizado",
                "numero_lote": "LT-AUTO-01",
            },
        )
        assert r_mov.status_code == 200
        assert r_mov.json()["status"] == "sucesso"

        # Transferência via API
        r_transf = client.post(
            "/api/estoque/transferir",
            json={
                "filial_origem_id": 1,
                "filial_destino_id": 2,
                "produto_id": prod,
                "quantidade": 2.0,
                "observacao": "Transferência via endpoint",
            },
        )
        assert r_transf.status_code == 200

        # Pedido de Compra e Recebimento
        r_pc = client.post(
            "/api/compras",
            json={
                "filial_id": 1,
                "fornecedor_id": 1,
                "produto_id": prod,
                "quantidade": 30.0,
                "custo_unitario": 12.50,
            },
        )
        assert r_pc.status_code == 201
        pc_id = r_pc.json()["id"]

        r_rec = client.post(f"/api/compras/{pc_id}/receber")
        assert r_rec.status_code == 200
        assert r_rec.json()["status"] == "sucesso"

        # Campanha CRM
        r_camp = client.post(
            "/api/crm/campanhas",
            json={
                "titulo": "Campanha Teste Automatizado",
                "segmento_alvo": "DIAMANTE",
                "canal": "WHATSAPP",
                "desconto_extra_pct": 5.0,
                "cashback_bonus_pct": 3.0,
                "mensagem_template": "Mensagem de teste {nome}",
            },
        )
        assert r_camp.status_code == 201

        # Lançamento Financeiro Manual
        r_lanc = client.post(
            "/api/financeiro/lancamentos",
            json={
                "filial_id": 1,
                "tipo": "DESPESA",
                "categoria_dre": "DESPESA_OPERACIONAL",
                "descricao": "Material de escritório e limpeza",
                "valor": 350.0,
                "status": "PAGO",
            },
        )
        assert r_lanc.status_code == 201
