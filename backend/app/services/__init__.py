"""Módulo de Serviços e Regras de Negócio do ERP/CRM."""

from app.services.regras_negocio import (
    calcular_segmento_rfm,
    gerar_dre_gerencial,
    movimentar_estoque,
    processar_venda_pdv,
    receber_pedido_compra,
    transferir_estoque,
)

__all__ = [
    "calcular_segmento_rfm",
    "gerar_dre_gerencial",
    "movimentar_estoque",
    "processar_venda_pdv",
    "receber_pedido_compra",
    "transferir_estoque",
]
