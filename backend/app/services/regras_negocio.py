"""Regras de Negócio do ERP + CRM Supermercadista.

Módulos implementados:
1. Segmentação RFM Dinâmica (`calcular_segmento_rfm`)
2. Frente de Caixa / PDV Online com Preço Clube CRM, Resgate e Crédito de Cashback,
   Baixa de Estoque FEFO e Lançamentos Financeiros Automáticos (`processar_venda_pdv`)
3. DRE Gerencial Multi-Loja e Consolidado (`gerar_dre_gerencial`)
4. Transferências entre Filiais e Movimentações com FEFO (`transferir_estoque`, `movimentar_estoque`)
5. Recebimento de Pedidos de Compra (`receber_pedido_compra`)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from typing import Any
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session



def _agora_utc() -> datetime:
    """Retorna datetime UTC sem timezone para compatibilidade com colunas DateTime ingênuas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

from app.models.erp_crm_models import (
    ClienteCRM,
    EstoqueFilial,
    Filial,
    ItemVendaPDV,
    LancamentoFinanceiro,
    LoteValidade,
    MovimentacaoEstoque,
    PedidoCompra,
    Produto,
    TransacaoCashback,
    VendaPDV,
)


def calcular_segmento_rfm(total_gasto: float, total_compras: int) -> str:
    """Calcula a classificação RFM do cliente no Clube CRM.

    Critérios:
    - DIAMANTE: Gasto acumulado >= R$ 2500 OU compras >= 15
    - OURO:     Gasto acumulado >= R$ 1000 OU compras >= 8
    - PRATA:    Gasto acumulado >= R$ 300  OU compras >= 3
    - NOVO:     Caso contrário
    """
    gasto = float(total_gasto or 0.0)
    compras = int(total_compras or 0)

    if gasto >= 2500.0 or compras >= 15:
        return "DIAMANTE"
    elif gasto >= 1000.0 or compras >= 8:
        return "OURO"
    elif gasto >= 300.0 or compras >= 3:
        return "PRATA"
    return "NOVO"


def _limpar_cpf(cpf: str | None) -> str:
    """Remove caracteres não numéricos do CPF."""
    if not cpf:
        return ""
    return re.sub(r"\D", "", cpf)


def processar_venda_pdv(
    db: Session,
    filial_id: int,
    itens: list[dict[str, Any]],
    cpf_cliente: str | None = None,
    usar_cashback: float = 0.0,
    forma_pagamento: str = "PIX",
) -> dict[str, Any]:
    """Processa uma venda de Frente de Caixa (PDV Online) completa com:

    1. Identificação do cliente e aplicação do Preço Clube CRM (com cálculo de economia);
    2. Resgate de saldo de cashback acumulado (se solicitado);
    3. Baixa em EstoqueFilial e lotes LoteValidade ordenados por FEFO (First Expired, First Out);
    4. Registro de MovimentacaoEstoque(tipo="VENDA_PDV");
    5. Geração de novo Cashback e Pontos de Fidelidade no ClienteCRM;
    6. Atualização de total_gasto, total_compras, economia e recálculo RFM;
    7. Registro de LancamentoFinanceiro para RECEITA_VENDAS e CMV_MERCADORIAS;
    8. Retorno do cupom fiscal detalhado.
    """
    filial = db.query(Filial).filter(Filial.id == filial_id).first()
    if not filial:
        raise ValueError(f"Filial com ID {filial_id} não encontrada.")
    if not filial.ativa:
        raise ValueError(f"Filial '{filial.nome}' está inativa.")

    if not itens:
        raise ValueError("A venda deve conter ao menos um item.")

    # 1. Localização do Cliente CRM por CPF (exato ou apenas dígitos)
    cliente: ClienteCRM | None = None
    if cpf_cliente and cpf_cliente.strip():
        cpf_puro = cpf_cliente.strip()
        cpf_num = _limpar_cpf(cpf_puro)
        cliente = (
            db.query(ClienteCRM)
            .filter((ClienteCRM.cpf == cpf_puro) | (ClienteCRM.cpf == cpf_num))
            .first()
        )

    # 2. Pré-validação e cálculo dos itens da venda
    itens_calculados: list[dict[str, Any]] = []
    subtotal_bruto = 0.0
    subtotal_com_desconto = 0.0
    cashback_gerado_total = 0.0
    cmv_total = 0.0

    for item_raw in itens:
        produto_id = int(item_raw.get("produto_id", 0))
        quantidade = float(item_raw.get("quantidade", 0.0))

        if quantidade <= 0:
            raise ValueError(f"Quantidade inválida ({quantidade}) para produto_id={produto_id}.")

        produto = db.query(Produto).filter(Produto.id == produto_id).first()
        if not produto:
            raise ValueError(f"Produto ID {produto_id} não encontrado no catálogo.")
        if not produto.ativo:
            raise ValueError(f"Produto '{produto.nome}' está inativo para comercialização.")

        preco_tabela = round(float(produto.preco_venda), 2)
        # Se cliente for membro do clube CRM, ganha preço especial Clube
        if cliente:
            preco_aplicado = round(float(produto.preco_clube_crm), 2)
        else:
            preco_aplicado = preco_tabela

        custo_unit = round(float(produto.preco_custo), 2)
        sub_bruto_item = round(preco_tabela * quantidade, 2)
        sub_aplicado_item = round(preco_aplicado * quantidade, 2)
        desconto_item = round(max(0.0, sub_bruto_item - sub_aplicado_item), 2)

        # Cashback por produto percentual (somente para clientes Clube CRM)
        cashback_item = 0.0
        if cliente and produto.cashback_percentual > 0:
            cashback_item = round(sub_aplicado_item * (produto.cashback_percentual / 100.0), 2)

        subtotal_bruto += sub_bruto_item
        subtotal_com_desconto += sub_aplicado_item
        cashback_gerado_total += cashback_item
        cmv_total += round(custo_unit * quantidade, 2)

        itens_calculados.append({
            "produto": produto,
            "quantidade": quantidade,
            "preco_tabela": preco_tabela,
            "preco_aplicado": preco_aplicado,
            "custo_unitario": custo_unit,
            "subtotal_item": sub_aplicado_item,
            "desconto_item": desconto_item,
            "cashback_item": cashback_item,
        })

    subtotal_bruto = round(subtotal_bruto, 2)
    subtotal_com_desconto = round(subtotal_com_desconto, 2)
    desconto_clube_total = round(max(0.0, subtotal_bruto - subtotal_com_desconto), 2)
    cashback_gerado_total = round(cashback_gerado_total, 2)
    cmv_total = round(cmv_total, 2)

    # 3. Tratamento de Resgate de Cashback
    cashback_a_usar = 0.0
    if cliente and usar_cashback > 0:
        saldo_disponivel = max(0.0, float(cliente.saldo_cashback or 0.0))
        # O resgate não pode exceder nem o saldo disponível nem o valor da compra
        cashback_a_usar = min(
            round(float(usar_cashback), 2),
            round(saldo_disponivel, 2),
            round(subtotal_com_desconto, 2),
        )

    valor_total_liquido = round(max(0.0, subtotal_com_desconto - cashback_a_usar), 2)

    # 4. Geração do Cabeçalho da Venda PDV
    codigo_filial = filial.codigo.replace("-", "").upper()
    timestamp_cupom = _agora_utc().strftime("%Y%m%d%H%M%S")
    sufixo_unico = uuid.uuid4().hex[:5].upper()
    numero_cupom = f"CUPOM-{codigo_filial}-{timestamp_cupom}-{sufixo_unico}"

    venda = VendaPDV(
        numero_cupom=numero_cupom,
        filial_id=filial.id,
        cliente_id=cliente.id if cliente else None,
        subtotal_bruto=subtotal_bruto,
        desconto_clube_crm=desconto_clube_total,
        cashback_utilizado=cashback_a_usar,
        valor_total_liquido=valor_total_liquido,
        cashback_gerado=cashback_gerado_total,
        forma_pagamento=forma_pagamento,
        criada_em=_agora_utc(),
    )
    db.add(venda)
    db.flush()  # Garante venda.id para os itens e transações

    # 5. Se houve resgate de cashback, debita e cria TransacaoCashback(RESGATE_PDV)
    if cliente and cashback_a_usar > 0:
        cliente.saldo_cashback = round(float(cliente.saldo_cashback) - cashback_a_usar, 2)
        transacao_resgate = TransacaoCashback(
            cliente_id=cliente.id,
            venda_id=venda.id,
            tipo="RESGATE_PDV",
            valor=cashback_a_usar,
            pontos=0,
            descricao=f"Resgate de cashback no PDV (Cupom {numero_cupom})",
            criado_em=_agora_utc(),
        )
        db.add(transacao_resgate)

    # 6. Gravação dos Itens da Venda e Baixa de Estoque FEFO
    itens_resumo: list[dict[str, Any]] = []

    for item_calc in itens_calculados:
        prod: Produto = item_calc["produto"]
        qtd: float = item_calc["quantidade"]

        # 6.1 Cria ItemVendaPDV
        item_venda = ItemVendaPDV(
            venda_id=venda.id,
            produto_id=prod.id,
            quantidade=qtd,
            preco_unitario_tabela=item_calc["preco_tabela"],
            preco_unitario_aplicado=item_calc["preco_aplicado"],
            custo_unitario=item_calc["custo_unitario"],
            subtotal_item=item_calc["subtotal_item"],
        )
        db.add(item_venda)

        # 6.2 Baixa em EstoqueFilial
        estoque_filial = (
            db.query(EstoqueFilial)
            .filter(
                EstoqueFilial.filial_id == filial.id,
                EstoqueFilial.produto_id == prod.id,
            )
            .first()
        )
        if not estoque_filial:
            estoque_filial = EstoqueFilial(
                filial_id=filial.id,
                produto_id=prod.id,
                quantidade_atual=0.0,
                estoque_minimo=15.0,
                estoque_maximo=500.0,
                ultima_atualizacao=_agora_utc(),
            )
            db.add(estoque_filial)

        estoque_filial.quantidade_atual = round(estoque_filial.quantidade_atual - qtd, 3)
        estoque_filial.ultima_atualizacao = _agora_utc()

        # 6.3 Baixa FEFO nos lotes LoteValidade (ordem crescente de data_validade)
        lotes = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.filial_id == filial.id,
                LoteValidade.produto_id == prod.id,
                LoteValidade.quantidade_lote > 0,
            )
            .order_by(LoteValidade.data_validade.asc())
            .all()
        )

        qtd_restante_abater = qtd
        for lote in lotes:
            if qtd_restante_abater <= 0:
                break
            if lote.quantidade_lote <= qtd_restante_abater:
                qtd_restante_abater = round(qtd_restante_abater - lote.quantidade_lote, 3)
                lote.quantidade_lote = 0.0
                lote.status_lote = "ESGOTADO"
            else:
                lote.quantidade_lote = round(lote.quantidade_lote - qtd_restante_abater, 3)
                qtd_restante_abater = 0.0
                if lote.quantidade_lote <= 5.0 and lote.status_lote == "ATIVO":
                    lote.status_lote = "ALERTA_VENCIMENTO"

        # 6.4 Registra MovimentacaoEstoque
        mov_estoque = MovimentacaoEstoque(
            filial_id=filial.id,
            produto_id=prod.id,
            tipo="VENDA_PDV",
            quantidade=-qtd,
            observacao=f"Baixa PDV Cupom {numero_cupom}",
            criado_em=_agora_utc(),
        )
        db.add(mov_estoque)

        itens_resumo.append({
            "produto_id": prod.id,
            "nome": prod.nome,
            "sku": prod.sku,
            "quantidade": qtd,
            "unidade": prod.unidade,
            "preco_tabela": item_calc["preco_tabela"],
            "preco_aplicado": item_calc["preco_aplicado"],
            "desconto_clube": item_calc["desconto_item"],
            "subtotal": item_calc["subtotal_item"],
            "cashback_gerado": item_calc["cashback_item"],
        })

    # 7. Atualização do Cliente CRM (Crédito de Cashback, Pontos e RFM)
    pontos_ganhos = 0
    if cliente:
        pontos_ganhos = int(valor_total_liquido)  # 1 ponto por cada R$ 1 pago
        cliente.saldo_cashback = round(float(cliente.saldo_cashback) + cashback_gerado_total, 2)
        cliente.pontos_fidelidade += pontos_ganhos
        cliente.total_gasto_historico = round(
            float(cliente.total_gasto_historico or 0.0) + valor_total_liquido, 2
        )
        cliente.total_compras_count = int(cliente.total_compras_count or 0) + 1
        cliente.economia_acumulada_clube = round(
            float(cliente.economia_acumulada_clube or 0.0) + desconto_clube_total, 2
        )
        cliente.segmento_rfm = calcular_segmento_rfm(
            cliente.total_gasto_historico, cliente.total_compras_count
        )
        cliente.ultima_compra_em = _agora_utc()

        if cashback_gerado_total > 0 or pontos_ganhos > 0:
            transacao_credito = TransacaoCashback(
                cliente_id=cliente.id,
                venda_id=venda.id,
                tipo="CREDITO_COMPRA",
                valor=cashback_gerado_total,
                pontos=pontos_ganhos,
                descricao=f"Crédito cashback compra PDV {numero_cupom}",
                criado_em=_agora_utc(),
            )
            db.add(transacao_credito)

    # 8. Registro Automático de Lançamentos Financeiros (RECEITA e CMV)
    hoje = date.today()

    # 8.1 Receita Líquida da Venda
    lanc_receita = LancamentoFinanceiro(
        filial_id=filial.id,
        tipo="RECEITA",
        categoria_dre="RECEITA_VENDAS",
        descricao=f"Receita Venda PDV {numero_cupom} ({forma_pagamento})",
        valor=valor_total_liquido,
        status="PAGO",
        data_competencia=hoje,
        criado_em=_agora_utc(),
    )
    db.add(lanc_receita)

    # 8.2 Custo da Mercadoria Vendida (CMV)
    lanc_cmv = LancamentoFinanceiro(
        filial_id=filial.id,
        tipo="CMV",
        categoria_dre="CMV_MERCADORIAS",
        descricao=f"CMV Mercadorias Venda PDV {numero_cupom}",
        valor=cmv_total,
        status="PAGO",
        data_competencia=hoje,
        criado_em=_agora_utc(),
    )
    db.add(lanc_cmv)

    db.commit()
    db.refresh(venda)

    return {
        "venda_id": venda.id,
        "numero_cupom": venda.numero_cupom,
        "filial_id": filial.id,
        "filial_nome": filial.nome,
        "cliente_id": cliente.id if cliente else None,
        "cliente_nome": cliente.nome if cliente else "Consumidor Final",
        "cpf_cliente": cliente.cpf if cliente else None,
        "segmento_rfm": cliente.segmento_rfm if cliente else None,
        "subtotal_bruto": subtotal_bruto,
        "desconto_clube_crm": desconto_clube_total,
        "cashback_utilizado": cashback_a_usar,
        "valor_total_liquido": valor_total_liquido,
        "cashback_gerado": cashback_gerado_total,
        "pontos_ganhos": pontos_ganhos,
        "novo_saldo_cashback": cliente.saldo_cashback if cliente else None,
        "forma_pagamento": forma_pagamento,
        "cmv_total": cmv_total,
        "itens": itens_resumo,
        "data_hora": venda.criada_em.isoformat(),
    }


def gerar_dre_gerencial(db: Session, filial_id: int | None = None) -> dict[str, Any]:
    """Gera o Demonstrativo de Resultados do Exercício (DRE Gerencial).

    Estrutura:
    (+) Receita Bruta (RECEITA_VENDAS)
    (-) Impostos sobre Vendas (IMPOSTOS)
    (=) Receita Líquida
    (-) CMV - Custo das Mercadorias Vendidas (CMV_MERCADORIAS)
    (=) Lucro Bruto
    (%) Margem Bruta
    (-) Despesas Operacionais (FOLHA_PAGAMENTO + ENERGIA_ALUGUEL + DESPESA_OPERACIONAL)
    (=) EBITDA / Lucro Líquido
    (%) Margem Líquida
    Breakdown detalhado por filial.
    """
    query = db.query(LancamentoFinanceiro)
    if filial_id is not None:
        query = query.filter(LancamentoFinanceiro.filial_id == filial_id)

    lancamentos = query.all()

    receita_bruta = 0.0
    impostos = 0.0
    cmv = 0.0
    folha_pagamento = 0.0
    energia_aluguel = 0.0
    outras_despesas_operacionais = 0.0

    for l in lancamentos:
        val = float(l.valor or 0.0)
        tipo = (l.tipo or "").upper()
        cat = (l.categoria_dre or "").upper()

        if tipo == "RECEITA" or cat == "RECEITA_VENDAS":
            receita_bruta += val
        elif cat == "IMPOSTOS":
            impostos += val
        elif tipo == "CMV" or cat == "CMV_MERCADORIAS":
            cmv += val
        elif cat == "FOLHA_PAGAMENTO":
            folha_pagamento += val
        elif cat == "ENERGIA_ALUGUEL":
            energia_aluguel += val
        elif tipo == "DESPESA" or cat == "DESPESA_OPERACIONAL":
            outras_despesas_operacionais += val

    despesas_operacionais = folha_pagamento + energia_aluguel + outras_despesas_operacionais
    receita_liquida = round(receita_bruta - impostos, 2)
    lucro_bruto = round(receita_liquida - cmv, 2)
    margem_bruta_pct = round((lucro_bruto / receita_liquida * 100.0), 2) if receita_liquida > 0 else 0.0
    ebitda_lucro_liquido = round(lucro_bruto - despesas_operacionais, 2)
    margem_liquida_pct = (
        round((ebitda_lucro_liquido / receita_liquida * 100.0), 2) if receita_liquida > 0 else 0.0
    )

    # Breakdown por Filial
    filiais_db = db.query(Filial).all()
    if filial_id is not None:
        filiais_db = [f for f in filiais_db if f.id == filial_id]

    breakdown_filiais: list[dict[str, Any]] = []
    for f in filiais_db:
        f_lancs = [l for l in lancamentos if l.filial_id == f.id]
        f_rec = sum(float(l.valor) for l in f_lancs if (l.tipo == "RECEITA" or l.categoria_dre == "RECEITA_VENDAS"))
        f_imp = sum(float(l.valor) for l in f_lancs if l.categoria_dre == "IMPOSTOS")
        f_rec_liq = round(f_rec - f_imp, 2)
        f_cmv = sum(float(l.valor) for l in f_lancs if (l.tipo == "CMV" or l.categoria_dre == "CMV_MERCADORIAS"))
        f_lucro_bruto = round(f_rec_liq - f_cmv, 2)
        f_margem_bruta = round((f_lucro_bruto / f_rec_liq * 100.0), 2) if f_rec_liq > 0 else 0.0

        f_desp = sum(
            float(l.valor)
            for l in f_lancs
            if (l.tipo == "DESPESA" and l.categoria_dre != "IMPOSTOS")
            or l.categoria_dre in ("FOLHA_PAGAMENTO", "ENERGIA_ALUGUEL", "DESPESA_OPERACIONAL")
        )
        f_lucro_liq = round(f_lucro_bruto - f_desp, 2)
        f_margem_liq = round((f_lucro_liq / f_rec_liq * 100.0), 2) if f_rec_liq > 0 else 0.0

        breakdown_filiais.append({
            "filial_id": f.id,
            "filial_nome": f.nome,
            "receita_bruta": round(f_rec, 2),
            "impostos": round(f_imp, 2),
            "receita_liquida": f_rec_liq,
            "cmv": round(f_cmv, 2),
            "lucro_bruto": f_lucro_bruto,
            "margem_bruta_pct": f_margem_bruta,
            "despesas_operacionais": round(f_desp, 2),
            "ebitda_lucro_liquido": f_lucro_liq,
            "margem_liquida_pct": f_margem_liq,
        })

    return {
        "receita_bruta": round(receita_bruta, 2),
        "impostos": round(impostos, 2),
        "receita_liquida": receita_liquida,
        "cmv": round(cmv, 2),
        "lucro_bruto": lucro_bruto,
        "margem_bruta_pct": margem_bruta_pct,
        "despesas_operacionais": round(despesas_operacionais, 2),
        "ebitda_lucro_liquido": ebitda_lucro_liquido,
        "margem_liquida_pct": margem_liquida_pct,
        "detalhes_despesas": {
            "folha_pagamento": round(folha_pagamento, 2),
            "energia_aluguel": round(energia_aluguel, 2),
            "despesas_operacionais": round(outras_despesas_operacionais, 2),
        },
        "por_filial": breakdown_filiais,
    }


def transferir_estoque(
    db: Session,
    filial_origem_id: int,
    filial_destino_id: int,
    produto_id: int,
    quantidade: float,
    observacao: str = "",
) -> dict[str, Any]:
    """Transfere quantidade de estoque entre duas filiais com controle FEFO."""
    if filial_origem_id == filial_destino_id:
        raise ValueError("A filial de origem deve ser diferente da filial de destino.")
    if quantidade <= 0:
        raise ValueError(f"Quantidade a transferir deve ser positiva ({quantidade}).")

    origem = db.query(Filial).filter(Filial.id == filial_origem_id).first()
    destino = db.query(Filial).filter(Filial.id == filial_destino_id).first()
    if not origem or not destino:
        raise ValueError("Filial de origem ou destino não localizada.")

    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ValueError(f"Produto {produto_id} não localizado.")

    # Estoque de origem
    est_origem = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.filial_id == filial_origem_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est_origem or est_origem.quantidade_atual < quantidade:
        saldo_atual = est_origem.quantidade_atual if est_origem else 0.0
        raise ValueError(
            f"Saldo insuficiente na filial {origem.nome}: disponível {saldo_atual}, solicitado {quantidade}."
        )

    # Estoque de destino
    est_destino = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.filial_id == filial_destino_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est_destino:
        est_destino = EstoqueFilial(
            filial_id=filial_destino_id,
            produto_id=produto_id,
            quantidade_atual=0.0,
            estoque_minimo=est_origem.estoque_minimo,
            estoque_maximo=est_origem.estoque_maximo,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est_destino)

    # Atualiza posições
    est_origem.quantidade_atual = round(est_origem.quantidade_atual - quantidade, 3)
    est_origem.ultima_atualizacao = _agora_utc()
    est_destino.quantidade_atual = round(est_destino.quantidade_atual + quantidade, 3)
    est_destino.ultima_atualizacao = _agora_utc()

    # Transfere lotes FEFO
    lotes_origem = (
        db.query(LoteValidade)
        .filter(
            LoteValidade.filial_id == filial_origem_id,
            LoteValidade.produto_id == produto_id,
            LoteValidade.quantidade_lote > 0,
        )
        .order_by(LoteValidade.data_validade.asc())
        .all()
    )

    qtd_a_transferir = quantidade
    for lote in lotes_origem:
        if qtd_a_transferir <= 0:
            break
        abater = min(lote.quantidade_lote, qtd_a_transferir)
        lote.quantidade_lote = round(lote.quantidade_lote - abater, 3)
        if lote.quantidade_lote == 0:
            lote.status_lote = "ESGOTADO"
        qtd_a_transferir = round(qtd_a_transferir - abater, 3)

        # Adiciona ou atualiza lote no destino
        lote_dest = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.filial_id == filial_destino_id,
                LoteValidade.produto_id == produto_id,
                LoteValidade.numero_lote == lote.numero_lote,
            )
            .first()
        )
        if not lote_dest:
            lote_dest = LoteValidade(
                filial_id=filial_destino_id,
                produto_id=produto_id,
                numero_lote=lote.numero_lote,
                data_fabricacao=lote.data_fabricacao,
                data_validade=lote.data_validade,
                quantidade_lote=abater,
                status_lote="ATIVO",
            )
            db.add(lote_dest)
        else:
            lote_dest.quantidade_lote = round(lote_dest.quantidade_lote + abater, 3)
            if lote_dest.status_lote == "ESGOTADO" and lote_dest.quantidade_lote > 0:
                lote_dest.status_lote = "ATIVO"

    # Registra movimentações de saída e entrada
    obs_extra = f" - {observacao}" if observacao else ""
    db.add(
        MovimentacaoEstoque(
            filial_id=filial_origem_id,
            produto_id=produto_id,
            tipo="TRANSFERENCIA_SAIDA",
            quantidade=-quantidade,
            observacao=f"Transferência para {destino.nome}{obs_extra}",
            criado_em=_agora_utc(),
        )
    )
    db.add(
        MovimentacaoEstoque(
            filial_id=filial_destino_id,
            produto_id=produto_id,
            tipo="TRANSFERENCIA_ENTRADA",
            quantidade=quantidade,
            observacao=f"Transferência recebida de {origem.nome}{obs_extra}",
            criado_em=_agora_utc(),
        )
    )

    db.commit()

    return {
        "status": "sucesso",
        "produto": produto.nome,
        "quantidade_transferida": quantidade,
        "origem": origem.nome,
        "saldo_novo_origem": est_origem.quantidade_atual,
        "destino": destino.nome,
        "saldo_novo_destino": est_destino.quantidade_atual,
    }


def movimentar_estoque(
    db: Session,
    filial_id: int,
    produto_id: int,
    tipo: str,
    quantidade: float,
    observacao: str = "",
    numero_lote: str | None = None,
    data_fabricacao: date | None = None,
    data_validade: date | None = None,
) -> dict[str, Any]:
    """Movimentação de ajuste, quebra/perda ou entrada manual com lote."""
    if quantidade <= 0:
        raise ValueError("Quantidade deve ser maior que zero.")

    filial = db.query(Filial).filter(Filial.id == filial_id).first()
    if not filial:
        raise ValueError(f"Filial {filial_id} não encontrada.")

    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise ValueError(f"Produto {produto_id} não encontrado.")

    est = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.filial_id == filial_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est:
        est = EstoqueFilial(
            filial_id=filial_id,
            produto_id=produto_id,
            quantidade_atual=0.0,
            estoque_minimo=20.0,
            estoque_maximo=500.0,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est)

    tipo_norm = tipo.upper()
    if tipo_norm in ("ENTRADA_COMPRA", "AJUSTE_POSITIVO"):
        est.quantidade_atual = round(est.quantidade_atual + quantidade, 3)
        qtd_mov = quantidade

        # Se dados de lote foram informados, grava/atualiza lote
        if numero_lote:
            lote = (
                db.query(LoteValidade)
                .filter(
                    LoteValidade.filial_id == filial_id,
                    LoteValidade.produto_id == produto_id,
                    LoteValidade.numero_lote == numero_lote,
                )
                .first()
            )
            if not lote:
                lote = LoteValidade(
                    filial_id=filial_id,
                    produto_id=produto_id,
                    numero_lote=numero_lote,
                    data_fabricacao=data_fabricacao or date.today(),
                    data_validade=data_validade or (date.today() + timedelta(days=90)),
                    quantidade_lote=quantidade,
                    status_lote="ATIVO",
                )
                db.add(lote)
            else:
                lote.quantidade_lote = round(lote.quantidade_lote + quantidade, 3)
                lote.status_lote = "ATIVO"

    elif tipo_norm in ("QUEBRA_PERDA", "AJUSTE_INVENTARIO", "BAIXA"):
        est.quantidade_atual = round(est.quantidade_atual - quantidade, 3)
        qtd_mov = -quantidade

        # Baixa FEFO dos lotes
        lotes = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.filial_id == filial_id,
                LoteValidade.produto_id == produto_id,
                LoteValidade.quantidade_lote > 0,
            )
            .order_by(LoteValidade.data_validade.asc())
            .all()
        )
        qtd_rest = quantidade
        for l in lotes:
            if qtd_rest <= 0:
                break
            abater = min(l.quantidade_lote, qtd_rest)
            l.quantidade_lote = round(l.quantidade_lote - abater, 3)
            if l.quantidade_lote == 0:
                l.status_lote = "ESGOTADO"
            qtd_rest = round(qtd_rest - abater, 3)
    else:
        raise ValueError(f"Tipo de movimentação '{tipo}' não suportado.")

    est.ultima_atualizacao = _agora_utc()

    db.add(
        MovimentacaoEstoque(
            filial_id=filial_id,
            produto_id=produto_id,
            tipo=tipo_norm,
            quantidade=qtd_mov,
            observacao=observacao or f"Movimentação manual {tipo_norm}",
            criado_em=_agora_utc(),
        )
    )

    db.commit()

    return {
        "status": "sucesso",
        "filial": filial.nome,
        "produto": produto.nome,
        "tipo": tipo_norm,
        "quantidade": quantidade,
        "saldo_atual": est.quantidade_atual,
    }


def receber_pedido_compra(db: Session, pedido_id: int) -> dict[str, Any]:
    """Processa o recebimento físico de um Pedido de Compra."""
    pedido = db.query(PedidoCompra).filter(PedidoCompra.id == pedido_id).first()
    if not pedido:
        raise ValueError(f"Pedido de Compra ID {pedido_id} não encontrado.")
    if pedido.status == "RECEBIDO":
        raise ValueError(f"Pedido {pedido.numero_pedido} já foi recebido anteriormente.")

    pedido.status = "RECEBIDO"

    # Entrada em estoque
    prod = db.query(Produto).filter(Produto.id == pedido.produto_id).first()
    filial = db.query(Filial).filter(Filial.id == pedido.filial_id).first()

    est = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.filial_id == pedido.filial_id,
            EstoqueFilial.produto_id == pedido.produto_id,
        )
        .first()
    )
    if not est:
        est = EstoqueFilial(
            filial_id=pedido.filial_id,
            produto_id=pedido.produto_id,
            quantidade_atual=0.0,
            estoque_minimo=20.0,
            estoque_maximo=500.0,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est)

    est.quantidade_atual = round(est.quantidade_atual + pedido.quantidade, 3)
    est.ultima_atualizacao = _agora_utc()

    # Cria lote de validade padrão para o recebimento
    validade_dias = 60 if (prod and prod.perecivel) else 180
    numero_lote = f"LOTE-PC{pedido.id}-{_agora_utc().strftime('%Y%m%d')}"
    lote = LoteValidade(
        filial_id=pedido.filial_id,
        produto_id=pedido.produto_id,
        numero_lote=numero_lote,
        data_fabricacao=date.today(),
        data_validade=date.today() + timedelta(days=validade_dias),
        quantidade_lote=pedido.quantidade,
        status_lote="ATIVO",
    )
    db.add(lote)

    # Registra movimentação de entrada
    db.add(
        MovimentacaoEstoque(
            filial_id=pedido.filial_id,
            produto_id=pedido.produto_id,
            tipo="ENTRADA_COMPRA",
            quantidade=pedido.quantidade,
            observacao=f"Recebimento Pedido Compra {pedido.numero_pedido}",
            criado_em=_agora_utc(),
        )
    )

    db.commit()

    return {
        "status": "sucesso",
        "pedido_id": pedido.id,
        "numero_pedido": pedido.numero_pedido,
        "filial": filial.nome if filial else str(pedido.filial_id),
        "produto": prod.nome if prod else str(pedido.produto_id),
        "quantidade_recebida": pedido.quantidade,
        "novo_saldo_estoque": est.quantidade_atual,
        "lote_criado": numero_lote,
    }
