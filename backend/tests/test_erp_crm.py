"""Suíte Automatizada de Testes Fim-a-Fim (QA) — ERP & CRM Grupo de Mercados."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def test_fluxo_completo_erp_crm() -> None:
    with TestClient(app) as client:
        # 1. Healthcheck & Status do Banco
        r_health = client.get("/api/health")
        assert r_health.status_code == 200
        dados_health = r_health.json()
        assert dados_health["status"] == "online"

        # 2. Filiais da Rede
        r_filiais = client.get("/api/filiais")
        assert r_filiais.status_code == 200
        filiais = r_filiais.json()
        assert len(filiais) >= 4

        # 3. Catálogo de Produtos (EAN, Preço Venda vs Preço Clube CRM)
        r_prod = client.get("/api/produtos")
        assert r_prod.status_code == 200
        produtos = r_prod.json()
        assert len(produtos) >= 10
        primeiro_prod = produtos[0]
        assert primeiro_prod["preco_clube_crm"] < primeiro_prod["preco_venda"]

        # 4. Estoque Multi-Filial e Lotes FEFO
        r_est = client.get("/api/estoque")
        assert r_est.status_code == 200
        estoque = r_est.json()
        assert len(estoque) > 0

        # 5. CRM 360º e Busca por CPF
        r_cli = client.get("/api/crm/clientes")
        assert r_cli.status_code == 200
        clientes = r_cli.json()
        assert len(clientes) >= 5
        cpf_teste = clientes[0]["cpf"]

        r_cpf = client.get(f"/api/crm/clientes/cpf/{cpf_teste}")
        assert r_cpf.status_code == 200
        assert r_cpf.json()["cpf"] == cpf_teste

        # 6. Realizar Venda Real no PDV com CPF do Clube CRM e Geração de Cashback
        filial_venda_id = filiais[1]["id"]
        payload_venda = {
            "filial_id": filial_venda_id,
            "cpf_cliente": cpf_teste,
            "usar_cashback": 0.0,
            "forma_pagamento": "PIX",
            "itens": [
                {"produto_id": primeiro_prod["id"], "quantidade": 2.0},
            ],
        }
        r_venda = client.post("/api/pdv/venda", json=payload_venda)
        assert r_venda.status_code in (200, 201), r_venda.text
        cupom = r_venda.json()
        assert cupom["desconto_clube_crm"] > 0
        assert cupom["cashback_gerado"] > 0

        # 7. Financeiro & DRE Consolidado
        r_dre = client.get("/api/financeiro/dre")
        assert r_dre.status_code == 200
        dre = r_dre.json()
        assert "receita_bruta" in dre
        assert "ebitda_lucro_liquido" in dre

        # 8. Dashboard Executivo e Central de Agentes IA
        r_dash = client.get("/api/dashboard/resumo")
        assert r_dash.status_code == 200
        assert "faturamento_total" in r_dash.json()

        r_ag = client.get("/api/agentes/status")
        assert r_ag.status_code == 200
        assert "tiers" in r_ag.json()

        # 9. Frontend Web Online na raiz /
        r_ui = client.get("/")
        assert r_ui.status_code == 200
        assert "text/html" in r_ui.headers.get("content-type", "")
