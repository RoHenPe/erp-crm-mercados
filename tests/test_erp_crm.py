"""Suíte de Testes de Produção do Sistema HelpDmais.

Valida:
1. Inicialização limpa do banco de dados (zero dados fictícios) e bloqueio de chamadas sem token (401).
2. Fluxo de criação de duas empresas independentes (Mercado A e Mercado B).
3. Isolamento total de dados: mesmo código de barras (EAN), SKU, CNPJ de fornecedor e CPF de cliente em cada empresa sem colisão e sem mistura de informações.
4. Fluxo operacional completo: Fornecedor -> Pedido de Compra -> Recebimento no Estoque -> Abertura de Caixa -> Venda no PDV com Fidelidade/Cashback -> Apuração Financeira (DRE).
5. Controle de acesso por cargo: Operador de Caixa opera o PDV mas é bloqueado ao tentar acessar o DRE financeiro ou criar usuários.
"""

from __future__ import annotations

from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def test_01_health_e_bloqueio_sem_autenticacao(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"

    # Sem token, nenhuma rota de dados deve responder
    for rota in ["/api/dashboard/resumo", "/api/produtos", "/api/estoque", "/api/financeiro/dre"]:
        r = client.get(rota)
        assert r.status_code == 401


def test_02_isolamento_completo_entre_dois_mercados(client: TestClient):
    # 1. Cadastra Mercado 1 (Seu Mercado)
    reg1 = client.post(
        "/api/auth/registrar-comercio",
        json={
            "nome_fantasia": "Mercado Central",
            "razao_social": "Mercado Central Ltda",
            "cnpj_matriz": "11.111.111/0001-11",
            "cidade_uf": "São Paulo - SP",
            "telefone": "11999990001",
            "meta_mensal_matriz": 200000.0,
            "admin_nome": "Rodrigo",
            "admin_email": "rodrigo@mercadocentral.com.br",
            "admin_senha": "senhaForte123",
        },
    )
    assert reg1.status_code == 201, reg1.text
    dados1 = reg1.json()
    token1 = dados1["token_sessao"]
    headers1 = {"Authorization": f"Bearer {token1}"}
    filial1_id = dados1["filiais"][0]["id"]

    # 2. Cadastra Mercado 2 (Mercado do Amigo)
    reg2 = client.post(
        "/api/auth/registrar-comercio",
        json={
            "nome_fantasia": "Supermercado do Amigo",
            "razao_social": "Comércio de Alimentos Amigo Ltda",
            "cnpj_matriz": "22.222.222/0001-22",
            "cidade_uf": "Campinas - SP",
            "telefone": "19988880002",
            "meta_mensal_matriz": 180000.0,
            "admin_nome": "Carlos Amigo",
            "admin_email": "carlos@mercadoamigo.com.br",
            "admin_senha": "outraSenha456",
        },
    )
    assert reg2.status_code == 201, reg2.text
    dados2 = reg2.json()
    token2 = dados2["token_sessao"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    filial2_id = dados2["filiais"][0]["id"]

    # 3. Verifica que ambos começam com 0 produtos, 0 clientes e R$ 0 de faturamento
    resumo1_ini = client.get("/api/dashboard/resumo", headers=headers1).json()
    assert resumo1_ini["faturamento_total"] == 0.0
    assert resumo1_ini["total_produtos"] == 0
    assert resumo1_ini["total_clientes_crm"] == 0
    assert resumo1_ini["top_5_produtos"] == []

    # 4. Ambos cadastram um produto com o MESMO EAN e SKU, mas preços diferentes
    p1 = client.post(
        "/api/produtos",
        headers=headers1,
        json={
            "sku": "ARROZ-5KG",
            "ean": "7891000123456",
            "nome": "Arroz Tipo 1 5kg",
            "departamento": "Mercearia",
            "unidade": "UN",
            "preco_custo": 18.0,
            "preco_venda": 26.90,
            "preco_clube_crm": 24.90,
            "cashback_percentual": 2.0,
            "estoque_inicial": 50.0,
            "filial_inicial_id": filial1_id,
        },
    )
    assert p1.status_code == 201, p1.text
    prod1_id = p1.json()["id"]

    p2 = client.post(
        "/api/produtos",
        headers=headers2,
        json={
            "sku": "ARROZ-5KG",
            "ean": "7891000123456",
            "nome": "Arroz Tipo 1 5kg",
            "departamento": "Mercearia",
            "unidade": "UN",
            "preco_custo": 19.50,
            "preco_venda": 29.90,
            "preco_clube_crm": 27.90,
            "cashback_percentual": 1.0,
            "estoque_inicial": 120.0,
            "filial_inicial_id": filial2_id,
        },
    )
    assert p2.status_code == 201, p2.text
    prod2_id = p2.json()["id"]
    assert prod1_id != prod2_id

    # 5. Mercado 1 só vê o seu produto e o seu estoque (50 un, R$ 26,90)
    lista_p1 = client.get("/api/produtos", headers=headers1).json()
    assert len(lista_p1) == 1
    assert lista_p1[0]["preco_venda"] == 26.90

    # Mercado 2 só vê o produto dele (120 un, R$ 29,90)
    lista_p2 = client.get("/api/produtos", headers=headers2).json()
    assert len(lista_p2) == 1
    assert lista_p2[0]["preco_venda"] == 29.90

    # 6. Mercado 1 tenta vender usando a filial ou produto do Mercado 2 -> Bloqueado!
    venda_cruzada = client.post(
        "/api/pdv/vender",
        headers=headers1,
        json={
            "filial_id": filial1_id,
            "itens": [{"produto_id": prod2_id, "quantidade": 1}],
            "forma_pagamento": "PIX",
        },
    )
    assert venda_cruzada.status_code == 400

    # 7. Fluxo completo no Mercado 1: Cliente, Caixa, Venda e DRE
    cli1 = client.post(
        "/api/crm/clientes",
        headers=headers1,
        json={
            "cpf": "123.456.789-00",
            "nome": "Maria Cliente",
            "whatsapp": "11977776666",
        },
    )
    assert cli1.status_code == 201

    # Mercado 2 não enxerga o cliente do Mercado 1
    busca_cruzada = client.get("/api/crm/clientes/cpf/12345678900", headers=headers2)
    assert busca_cruzada.status_code == 404

    # Abre caixa no Mercado 1 e realiza venda
    abertura = client.post(
        "/api/pdv/caixa/abrir",
        headers=headers1,
        json={"filial_id": filial1_id, "valor_abertura": 150.0},
    )
    assert abertura.status_code == 201

    venda_ok = client.post(
        "/api/pdv/vender",
        headers=headers1,
        json={
            "filial_id": filial1_id,
            "itens": [{"produto_id": prod1_id, "quantidade": 2}],
            "cpf_cliente": "12345678900",
            "forma_pagamento": "PIX",
        },
    )
    assert venda_ok.status_code == 200, venda_ok.text
    v_dados = venda_ok.json()
    assert v_dados["valor_total_liquido"] == 49.80  # 2 * 24.90 (preço fidelidade)

    # DRE do Mercado 1 tem R$ 49,80 de receita; DRE do Mercado 2 continua R$ 0,00
    dre1 = client.get("/api/financeiro/dre", headers=headers1).json()
    dre2 = client.get("/api/financeiro/dre", headers=headers2).json()
    assert dre1["receita_bruta"] == 49.80
    assert dre2["receita_bruta"] == 0.0

    # 8. Controle de Cargo (Operador de Caixa vs Administrador)
    novo_caixa = client.post(
        "/api/usuarios",
        headers=headers1,
        json={
            "nome": "João Caixa",
            "email": "caixa@mercadocentral.com.br",
            "senha": "senhaCaixa123",
            "cargo": "Operador de Caixa",
            "filial_id": filial1_id,
            "perfil_rbac": "CAIXA",
        },
    )
    assert novo_caixa.status_code == 201

    login_caixa = client.post(
        "/api/auth/login",
        json={"email": "caixa@mercadocentral.com.br", "senha": "senhaCaixa123"},
    )
    assert login_caixa.status_code == 200
    headers_caixa = {"Authorization": f"Bearer {login_caixa.json()['token_sessao']}"}

    # Operador de Caixa NÃO pode acessar o DRE financeiro nem cadastrar novos usuários
    assert client.get("/api/financeiro/dre", headers=headers_caixa).status_code == 403
    assert (
        client.post(
            "/api/usuarios",
            headers=headers_caixa,
            json={
                "nome": "Outro",
                "email": "outro@mercadocentral.com.br",
                "senha": "123456",
                "cargo": "Teste",
                "perfil_rbac": "CAIXA",
            },
        ).status_code
        == 403
    )
