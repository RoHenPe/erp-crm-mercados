"""Regras de Negócio Operacionais e Financeiras — HelpDmais.

Todas as operações exigem e validam o vínculo com a Empresa (`tenant_id`),
garantindo que cadastros, estoques, vendas e lançamentos financeiros de uma
empresa nunca se misturem com os de outra.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import re
from typing import Any
import uuid

from sqlalchemy.orm import Session

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
    SessaoCaixaPDV,
    TransacaoCashback,
    VendaPDV,
)


def _agora_utc() -> datetime:
    """Retorna data/hora UTC sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calcular_segmento_rfm(total_gasto: float, total_compras: int) -> str:
    """Classifica o nível de fidelidade do cliente com base no histórico de compras."""
    gasto = float(total_gasto or 0.0)
    compras = int(total_compras or 0)

    if gasto >= 2500.0 or compras >= 15:
        return "DIAMANTE"
    if gasto >= 1000.0 or compras >= 8:
        return "OURO"
    if gasto >= 300.0 or compras >= 3:
        return "PRATA"
    return "NOVO"


def _limpar_cpf(cpf: str | None) -> str:
    if not cpf:
        return ""
    return re.sub(r"\D", "", cpf)


def _formatar_cpf(cpf_digitos: str) -> str:
    if len(cpf_digitos) == 11:
        return f"{cpf_digitos[:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:]}"
    return cpf_digitos


def processar_venda_pdv(
    db: Session,
    tenant_id: int,
    filial_id: int,
    itens: list[dict[str, Any]],
    cpf_cliente: str | None = None,
    usar_cashback: float = 0.0,
    forma_pagamento: str = "PIX",
    usuario_id: int | None = None,
) -> dict[str, Any]:
    """Processa uma venda no Ponto de Venda (PDV) isolada por Empresa (`tenant_id`)."""
    filial = (
        db.query(Filial)
        .filter(Filial.id == filial_id, Filial.tenant_id == tenant_id)
        .first()
    )
    if not filial:
        raise ValueError("Unidade/Loja não encontrada para esta empresa.")
    if not filial.ativa:
        raise ValueError(f"A unidade '{filial.nome}' está inativa.")

    if not itens:
        raise ValueError("A venda deve conter ao menos um item.")

    # Localiza o cliente apenas dentro da mesma Empresa (com ou sem pontuação)
    cliente: ClienteCRM | None = None
    if cpf_cliente and cpf_cliente.strip():
        cpf_puro = cpf_cliente.strip()
        cpf_num = _limpar_cpf(cpf_puro)
        cpf_fmt = _formatar_cpf(cpf_num)
        cliente = (
            db.query(ClienteCRM)
            .filter(
                ClienteCRM.tenant_id == tenant_id,
                (ClienteCRM.cpf == cpf_puro)
                | (ClienteCRM.cpf == cpf_num)
                | (ClienteCRM.cpf == cpf_fmt),
            )
            .first()
        )

    itens_calculados: list[dict[str, Any]] = []
    subtotal_bruto = 0.0
    subtotal_com_desconto = 0.0
    cashback_gerado_total = 0.0
    cmv_total = 0.0

    for item_raw in itens:
        produto_id = int(item_raw.get("produto_id", 0))
        quantidade = float(item_raw.get("quantidade", 0.0))

        if quantidade <= 0:
            raise ValueError(f"Quantidade inválida ({quantidade}) para o item.")

        produto = (
            db.query(Produto)
            .filter(Produto.id == produto_id, Produto.tenant_id == tenant_id)
            .first()
        )
        if not produto:
            raise ValueError(f"Produto ID {produto_id} não encontrado no catálogo desta empresa.")
        if not produto.ativo:
            raise ValueError(f"O produto '{produto.nome}' está inativo.")

        preco_tabela = round(float(produto.preco_venda), 2)
        preco_aplicado = (
            round(float(produto.preco_clube_crm), 2) if cliente else preco_tabela
        )

        custo_unit = round(float(produto.preco_custo), 2)
        sub_bruto_item = round(preco_tabela * quantidade, 2)
        sub_aplicado_item = round(preco_aplicado * quantidade, 2)
        desconto_item = round(max(0.0, sub_bruto_item - sub_aplicado_item), 2)

        cashback_item = 0.0
        if cliente and produto.cashback_percentual > 0:
            cashback_item = round(
                sub_aplicado_item * (produto.cashback_percentual / 100.0), 2
            )

        subtotal_bruto += sub_bruto_item
        subtotal_com_desconto += sub_aplicado_item
        cashback_gerado_total += cashback_item
        cmv_total += round(custo_unit * quantidade, 2)

        itens_calculados.append(
            {
                "produto": produto,
                "quantidade": quantidade,
                "preco_tabela": preco_tabela,
                "preco_aplicado": preco_aplicado,
                "custo_unitario": custo_unit,
                "subtotal_item": sub_aplicado_item,
                "desconto_item": desconto_item,
                "cashback_item": cashback_item,
            }
        )

    subtotal_bruto = round(subtotal_bruto, 2)
    subtotal_com_desconto = round(subtotal_com_desconto, 2)
    desconto_clube_total = round(max(0.0, subtotal_bruto - subtotal_com_desconto), 2)
    cashback_gerado_total = round(cashback_gerado_total, 2)
    cmv_total = round(cmv_total, 2)

    cashback_a_usar = 0.0
    if cliente and usar_cashback > 0:
        saldo_disponivel = max(0.0, float(cliente.saldo_cashback or 0.0))
        cashback_a_usar = min(
            round(float(usar_cashback), 2),
            round(saldo_disponivel, 2),
            round(subtotal_com_desconto, 2),
        )

    valor_total_liquido = round(max(0.0, subtotal_com_desconto - cashback_a_usar), 2)

    # Verifica se há sessão de caixa aberta para a unidade
    sessao_aberta = (
        db.query(SessaoCaixaPDV)
        .filter(
            SessaoCaixaPDV.tenant_id == tenant_id,
            SessaoCaixaPDV.filial_id == filial.id,
            SessaoCaixaPDV.status == "ABERTO",
        )
        .order_by(SessaoCaixaPDV.aberta_em.desc())
        .first()
    )

    codigo_filial = re.sub(r"[^A-Z0-9]", "", filial.codigo.upper()) or f"F{filial.id}"
    timestamp_cupom = _agora_utc().strftime("%Y%m%d%H%M%S")
    sufixo_unico = uuid.uuid4().hex[:5].upper()
    numero_cupom = f"VD-{tenant_id}-{codigo_filial}-{timestamp_cupom}-{sufixo_unico}"

    venda = VendaPDV(
        tenant_id=tenant_id,
        numero_cupom=numero_cupom,
        filial_id=filial.id,
        sessao_caixa_id=sessao_aberta.id if sessao_aberta else None,
        usuario_id=usuario_id,
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
    db.flush()

    if sessao_aberta:
        sessao_aberta.total_vendido = round(
            float(sessao_aberta.total_vendido or 0.0) + valor_total_liquido, 2
        )
        sessao_aberta.qtd_vendas = int(sessao_aberta.qtd_vendas or 0) + 1

    if cliente and cashback_a_usar > 0:
        cliente.saldo_cashback = round(float(cliente.saldo_cashback) - cashback_a_usar, 2)
        db.add(
            TransacaoCashback(
                tenant_id=tenant_id,
                cliente_id=cliente.id,
                venda_id=venda.id,
                tipo="RESGATE_PDV",
                valor=cashback_a_usar,
                pontos=0,
                descricao=f"Resgate no PDV ({numero_cupom})",
                criado_em=_agora_utc(),
            )
        )

    itens_resumo: list[dict[str, Any]] = []

    for item_calc in itens_calculados:
        prod: Produto = item_calc["produto"]
        qtd: float = item_calc["quantidade"]

        db.add(
            ItemVendaPDV(
                tenant_id=tenant_id,
                venda_id=venda.id,
                produto_id=prod.id,
                quantidade=qtd,
                preco_unitario_tabela=item_calc["preco_tabela"],
                preco_unitario_aplicado=item_calc["preco_aplicado"],
                custo_unitario=item_calc["custo_unitario"],
                subtotal_item=item_calc["subtotal_item"],
            )
        )

        estoque_filial = (
            db.query(EstoqueFilial)
            .filter(
                EstoqueFilial.tenant_id == tenant_id,
                EstoqueFilial.filial_id == filial.id,
                EstoqueFilial.produto_id == prod.id,
            )
            .first()
        )
        if not estoque_filial:
            estoque_filial = EstoqueFilial(
                tenant_id=tenant_id,
                filial_id=filial.id,
                produto_id=prod.id,
                quantidade_atual=0.0,
                estoque_minimo=float(prod.estoque_minimo_padrao or 10.0),
                estoque_maximo=500.0,
                ultima_atualizacao=_agora_utc(),
            )
            db.add(estoque_filial)

        estoque_filial.quantidade_atual = round(estoque_filial.quantidade_atual - qtd, 3)
        estoque_filial.ultima_atualizacao = _agora_utc()

        # Abate dos lotes por ordem de vencimento
        lotes = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.tenant_id == tenant_id,
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

        db.add(
            MovimentacaoEstoque(
                tenant_id=tenant_id,
                filial_id=filial.id,
                produto_id=prod.id,
                usuario_id=usuario_id,
                tipo="VENDA_PDV",
                quantidade=-qtd,
                observacao=f"Venda PDV {numero_cupom}",
                criado_em=_agora_utc(),
            )
        )

        itens_resumo.append(
            {
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
            }
        )

    pontos_ganhos = 0
    if cliente:
        pontos_ganhos = int(valor_total_liquido)
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
            db.add(
                TransacaoCashback(
                    tenant_id=tenant_id,
                    cliente_id=cliente.id,
                    venda_id=venda.id,
                    tipo="CREDITO_COMPRA",
                    valor=cashback_gerado_total,
                    pontos=pontos_ganhos,
                    descricao=f"Crédito compra PDV {numero_cupom}",
                    criado_em=_agora_utc(),
                )
            )

    hoje = date.today()
    db.add(
        LancamentoFinanceiro(
            tenant_id=tenant_id,
            filial_id=filial.id,
            tipo="RECEITA",
            categoria_dre="RECEITA_VENDAS",
            descricao=f"Venda PDV {numero_cupom} ({forma_pagamento})",
            valor=valor_total_liquido,
            status="PAGO",
            data_competencia=hoje,
            criado_em=_agora_utc(),
        )
    )
    db.add(
        LancamentoFinanceiro(
            tenant_id=tenant_id,
            filial_id=filial.id,
            tipo="CMV",
            categoria_dre="CMV_MERCADORIAS",
            descricao=f"Custo das Mercadorias Vendidas {numero_cupom}",
            valor=cmv_total,
            status="PAGO",
            data_competencia=hoje,
            criado_em=_agora_utc(),
        )
    )

    db.commit()
    db.refresh(venda)

    return {
        "venda_id": venda.id,
        "tenant_id": tenant_id,
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


def gerar_dre_gerencial(
    db: Session,
    tenant_id: int,
    filial_id: int | None = None,
) -> dict[str, Any]:
    """Gera o Demonstrativo de Resultados do Exercício (DRE) isolado por Empresa (`tenant_id`)."""
    filiais_query = db.query(Filial).filter(Filial.tenant_id == tenant_id)
    if filial_id is not None:
        filiais_query = filiais_query.filter(Filial.id == filial_id)
    filiais_db = filiais_query.order_by(Filial.id.asc()).all()

    query = db.query(LancamentoFinanceiro).filter(LancamentoFinanceiro.tenant_id == tenant_id)
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
    margem_bruta_pct = (
        round((lucro_bruto / receita_liquida * 100.0), 2) if receita_liquida > 0 else 0.0
    )
    ebitda_lucro_liquido = round(lucro_bruto - despesas_operacionais, 2)
    margem_liquida_pct = (
        round((ebitda_lucro_liquido / receita_liquida * 100.0), 2)
        if receita_liquida > 0
        else 0.0
    )

    breakdown_filiais: list[dict[str, Any]] = []
    for f in filiais_db:
        f_lancs = [l for l in lancamentos if l.filial_id == f.id]
        f_rec = sum(
            float(l.valor)
            for l in f_lancs
            if (l.tipo == "RECEITA" or l.categoria_dre == "RECEITA_VENDAS")
        )
        f_imp = sum(float(l.valor) for l in f_lancs if l.categoria_dre == "IMPOSTOS")
        f_rec_liq = round(f_rec - f_imp, 2)
        f_cmv = sum(
            float(l.valor)
            for l in f_lancs
            if (l.tipo == "CMV" or l.categoria_dre == "CMV_MERCADORIAS")
        )
        f_lucro_bruto = round(f_rec_liq - f_cmv, 2)
        f_margem_bruta = (
            round((f_lucro_bruto / f_rec_liq * 100.0), 2) if f_rec_liq > 0 else 0.0
        )

        f_desp = sum(
            float(l.valor)
            for l in f_lancs
            if (l.tipo == "DESPESA" and l.categoria_dre != "IMPOSTOS")
            or l.categoria_dre
            in ("FOLHA_PAGAMENTO", "ENERGIA_ALUGUEL", "DESPESA_OPERACIONAL")
        )
        f_lucro_liq = round(f_lucro_bruto - f_desp, 2)
        f_margem_liq = (
            round((f_lucro_liq / f_rec_liq * 100.0), 2) if f_rec_liq > 0 else 0.0
        )

        breakdown_filiais.append(
            {
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
            }
        )

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
    tenant_id: int,
    filial_origem_id: int,
    filial_destino_id: int,
    produto_id: int,
    quantidade: float,
    observacao: str = "",
    usuario_id: int | None = None,
) -> dict[str, Any]:
    """Transfere estoque entre duas unidades pertencentes à mesma Empresa (`tenant_id`)."""
    if filial_origem_id == filial_destino_id:
        raise ValueError("A unidade de origem deve ser diferente da unidade de destino.")
    if quantidade <= 0:
        raise ValueError("A quantidade a transferir deve ser maior que zero.")

    origem = (
        db.query(Filial)
        .filter(Filial.id == filial_origem_id, Filial.tenant_id == tenant_id)
        .first()
    )
    destino = (
        db.query(Filial)
        .filter(Filial.id == filial_destino_id, Filial.tenant_id == tenant_id)
        .first()
    )
    if not origem or not destino:
        raise ValueError("Unidade de origem ou destino não encontrada nesta empresa.")

    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id, Produto.tenant_id == tenant_id)
        .first()
    )
    if not produto:
        raise ValueError("Produto não encontrado no catálogo desta empresa.")

    est_origem = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.tenant_id == tenant_id,
            EstoqueFilial.filial_id == filial_origem_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est_origem or est_origem.quantidade_atual < quantidade:
        saldo_atual = est_origem.quantidade_atual if est_origem else 0.0
        raise ValueError(
            f"Saldo insuficiente na unidade {origem.nome}: disponível {saldo_atual}, solicitado {quantidade}."
        )

    est_destino = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.tenant_id == tenant_id,
            EstoqueFilial.filial_id == filial_destino_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est_destino:
        est_destino = EstoqueFilial(
            tenant_id=tenant_id,
            filial_id=filial_destino_id,
            produto_id=produto_id,
            quantidade_atual=0.0,
            estoque_minimo=est_origem.estoque_minimo,
            estoque_maximo=est_origem.estoque_maximo,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est_destino)

    est_origem.quantidade_atual = round(est_origem.quantidade_atual - quantidade, 3)
    est_origem.ultima_atualizacao = _agora_utc()
    est_destino.quantidade_atual = round(est_destino.quantidade_atual + quantidade, 3)
    est_destino.ultima_atualizacao = _agora_utc()

    lotes_origem = (
        db.query(LoteValidade)
        .filter(
            LoteValidade.tenant_id == tenant_id,
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

        lote_dest = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.tenant_id == tenant_id,
                LoteValidade.filial_id == filial_destino_id,
                LoteValidade.produto_id == produto_id,
                LoteValidade.numero_lote == lote.numero_lote,
            )
            .first()
        )
        if not lote_dest:
            db.add(
                LoteValidade(
                    tenant_id=tenant_id,
                    filial_id=filial_destino_id,
                    produto_id=produto_id,
                    numero_lote=lote.numero_lote,
                    data_fabricacao=lote.data_fabricacao,
                    data_validade=lote.data_validade,
                    quantidade_lote=abater,
                    status_lote="ATIVO",
                )
            )
        else:
            lote_dest.quantidade_lote = round(lote_dest.quantidade_lote + abater, 3)
            if lote_dest.status_lote == "ESGOTADO" and lote_dest.quantidade_lote > 0:
                lote_dest.status_lote = "ATIVO"

    obs_extra = f" - {observacao}" if observacao else ""
    db.add(
        MovimentacaoEstoque(
            tenant_id=tenant_id,
            filial_id=filial_origem_id,
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo="TRANSFERENCIA_SAIDA",
            quantidade=-quantidade,
            observacao=f"Transferência para {destino.nome}{obs_extra}",
            criado_em=_agora_utc(),
        )
    )
    db.add(
        MovimentacaoEstoque(
            tenant_id=tenant_id,
            filial_id=filial_destino_id,
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo="TRANSFERENCIA_ENTRADA",
            quantidade=quantidade,
            observacao=f"Recebido de {origem.nome}{obs_extra}",
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
    tenant_id: int,
    filial_id: int,
    produto_id: int,
    tipo: str,
    quantidade: float,
    observacao: str = "",
    numero_lote: str | None = None,
    data_fabricacao: date | None = None,
    data_validade: date | None = None,
    usuario_id: int | None = None,
) -> dict[str, Any]:
    """Registra entrada, saída por perda ou ajuste de inventário na Empresa (`tenant_id`)."""
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    filial = (
        db.query(Filial)
        .filter(Filial.id == filial_id, Filial.tenant_id == tenant_id)
        .first()
    )
    if not filial:
        raise ValueError("Unidade/Loja não encontrada nesta empresa.")

    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id, Produto.tenant_id == tenant_id)
        .first()
    )
    if not produto:
        raise ValueError("Produto não encontrado no catálogo desta empresa.")

    est = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.tenant_id == tenant_id,
            EstoqueFilial.filial_id == filial_id,
            EstoqueFilial.produto_id == produto_id,
        )
        .first()
    )
    if not est:
        est = EstoqueFilial(
            tenant_id=tenant_id,
            filial_id=filial_id,
            produto_id=produto_id,
            quantidade_atual=0.0,
            estoque_minimo=float(produto.estoque_minimo_padrao or 10.0),
            estoque_maximo=500.0,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est)

    tipo_norm = tipo.upper()
    if tipo_norm in ("ENTRADA_COMPRA", "AJUSTE_POSITIVO"):
        est.quantidade_atual = round(est.quantidade_atual + quantidade, 3)
        qtd_mov = quantidade

        if numero_lote:
            lote = (
                db.query(LoteValidade)
                .filter(
                    LoteValidade.tenant_id == tenant_id,
                    LoteValidade.filial_id == filial_id,
                    LoteValidade.produto_id == produto_id,
                    LoteValidade.numero_lote == numero_lote,
                )
                .first()
            )
            if not lote:
                db.add(
                    LoteValidade(
                        tenant_id=tenant_id,
                        filial_id=filial_id,
                        produto_id=produto_id,
                        numero_lote=numero_lote,
                        data_fabricacao=data_fabricacao or date.today(),
                        data_validade=data_validade or (date.today() + timedelta(days=90)),
                        quantidade_lote=quantidade,
                        status_lote="ATIVO",
                    )
                )
            else:
                lote.quantidade_lote = round(lote.quantidade_lote + quantidade, 3)
                lote.status_lote = "ATIVO"

    elif tipo_norm in ("QUEBRA_PERDA", "AJUSTE_INVENTARIO", "BAIXA"):
        est.quantidade_atual = round(est.quantidade_atual - quantidade, 3)
        qtd_mov = -quantidade

        lotes = (
            db.query(LoteValidade)
            .filter(
                LoteValidade.tenant_id == tenant_id,
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
            tenant_id=tenant_id,
            filial_id=filial_id,
            produto_id=produto_id,
            usuario_id=usuario_id,
            tipo=tipo_norm,
            quantidade=qtd_mov,
            observacao=observacao or f"Movimentação {tipo_norm}",
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


def receber_pedido_compra(
    db: Session,
    tenant_id: int,
    pedido_id: int,
    usuario_id: int | None = None,
) -> dict[str, Any]:
    """Processa o recebimento físico de um Pedido de Compra, gerando estoque, lote e conta a pagar."""
    pedido = (
        db.query(PedidoCompra)
        .filter(PedidoCompra.id == pedido_id, PedidoCompra.tenant_id == tenant_id)
        .first()
    )
    if not pedido:
        raise ValueError("Pedido de compra não encontrado nesta empresa.")
    if pedido.status == "RECEBIDO":
        raise ValueError(f"O pedido {pedido.numero_pedido} já foi recebido anteriormente.")

    pedido.status = "RECEBIDO"

    prod = (
        db.query(Produto)
        .filter(Produto.id == pedido.produto_id, Produto.tenant_id == tenant_id)
        .first()
    )
    filial = (
        db.query(Filial)
        .filter(Filial.id == pedido.filial_id, Filial.tenant_id == tenant_id)
        .first()
    )

    est = (
        db.query(EstoqueFilial)
        .filter(
            EstoqueFilial.tenant_id == tenant_id,
            EstoqueFilial.filial_id == pedido.filial_id,
            EstoqueFilial.produto_id == pedido.produto_id,
        )
        .first()
    )
    if not est:
        est = EstoqueFilial(
            tenant_id=tenant_id,
            filial_id=pedido.filial_id,
            produto_id=pedido.produto_id,
            quantidade_atual=0.0,
            estoque_minimo=float(prod.estoque_minimo_padrao if prod else 10.0),
            estoque_maximo=500.0,
            ultima_atualizacao=_agora_utc(),
        )
        db.add(est)

    est.quantidade_atual = round(est.quantidade_atual + pedido.quantidade, 3)
    est.ultima_atualizacao = _agora_utc()

    if prod and pedido.custo_unitario > 0:
        prod.preco_custo = round(float(pedido.custo_unitario), 2)

    validade_dias = 60 if (prod and prod.perecivel) else 180
    numero_lote = f"LT-PC{pedido.id}-{_agora_utc().strftime('%Y%m%d')}"
    db.add(
        LoteValidade(
            tenant_id=tenant_id,
            filial_id=pedido.filial_id,
            produto_id=pedido.produto_id,
            numero_lote=numero_lote,
            data_fabricacao=date.today(),
            data_validade=date.today() + timedelta(days=validade_dias),
            quantidade_lote=pedido.quantidade,
            status_lote="ATIVO",
        )
    )

    db.add(
        MovimentacaoEstoque(
            tenant_id=tenant_id,
            filial_id=pedido.filial_id,
            produto_id=pedido.produto_id,
            usuario_id=usuario_id,
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
