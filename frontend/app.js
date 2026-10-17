/**
 * SuperSul ERP & CRM Online para Grupo de Mercados
 * Frontend Core Application
 * Versão: 2.4 Enterprise Edition
 */

// ==========================================
// 1. ESTADO GLOBAL DA APLICAÇÃO & SEED INICIAL
// ==========================================
const appState = {
  activeTab: 'tab-dashboard',
  selectedFilialId: 'all', // 'all' ou filial_id numérico
  apiBaseUrl: '/api',

  // Filiais da Holding
  filiais: [
    { id: 1, codigo: 'CD-01', nome: 'Filial 01 — CD Central Distribuição', bandeira: 'CD Central', cnpj: '45.892.102/0001-90', cidade: 'Curitiba - PR', gerente: 'Carlos Eduardo Mendes', meta_mensal: 900000.0, faturamento_atual: 850400.0, ativa: true },
    { id: 2, codigo: 'HIPER-02', nome: 'Filial 02 — Hipermercado Parque das Nações', bandeira: 'Hipermercado', cnpj: '45.892.102/0002-71', cidade: 'Curitiba - PR', gerente: 'Fernanda Oliveira', meta_mensal: 600000.0, faturamento_atual: 512800.0, ativa: true },
    { id: 3, codigo: 'ATAC-03', nome: 'Filial 03 — Atacarejo Sul Atacadista', bandeira: 'Atacarejo', cnpj: '45.892.102/0003-52', cidade: 'São José dos Pinhais - PR', gerente: 'Marcos Vinícius', meta_mensal: 450000.0, faturamento_atual: 379450.0, ativa: true },
    { id: 4, codigo: 'EXP-04', nome: 'Filial 04 — Supermercado Express Centro', bandeira: 'Express', cnpj: '45.892.102/0004-33', cidade: 'Curitiba - PR', gerente: 'Juliana Santos', meta_mensal: 120000.0, faturamento_atual: 100000.0, ativa: true }
  ],

  // Fornecedores Homologados
  fornecedores: [
    { id: 1, razao_social: 'JBS S/A', nome_fantasia: 'Friboi Alimentos', cnpj: '02.916.265/0001-00', categoria_principal: 'Açougue & Carnes', prazo_entrega_dias: 2, telefone: '(11) 3144-4000', avaliacao: 4.9 },
    { id: 2, razao_social: 'Laticínios Tirol Ltda', nome_fantasia: 'Tirol Laticínios', cnpj: '83.208.431/0001-99', categoria_principal: 'Frios & Laticínios', prazo_entrega_dias: 2, telefone: '(49) 3537-8000', avaliacao: 4.8 },
    { id: 3, razao_social: 'Ambev S/A', nome_fantasia: 'Ambev Brasil', cnpj: '07.526.557/0001-00', categoria_principal: 'Bebidas', prazo_entrega_dias: 3, telefone: '(11) 2122-1200', avaliacao: 4.9 },
    { id: 4, razao_social: 'Camil Alimentos S/A', nome_fantasia: 'Camil Grãos', cnpj: '64.904.295/0001-03', categoria_principal: 'Mercearia Básica', prazo_entrega_dias: 4, telefone: '(11) 3088-2000', avaliacao: 4.7 },
    { id: 5, razao_social: 'Unilever Brasil Ltda', nome_fantasia: 'Unilever Higiene & Limpeza', cnpj: '61.068.276/0001-04', categoria_principal: 'Limpeza & Higiene', prazo_entrega_dias: 3, telefone: '(11) 3568-8000', avaliacao: 4.8 }
  ],

  // Catálogo de Produtos com Preço Normal e Preço Clube CRM
  produtos: [
    { id: 1, sku: 'ACO-001', ean: '7891000100101', nome: 'Picanha Bovina Fatiada Resfriada', departamento: 'Açougue', unidade: 'KG', preco_custo: 48.00, preco_venda: 74.90, preco_clube_crm: 62.90, cashback_pct: 3.0, fornecedor_id: 1, perecivel: true, img: '🥩' },
    { id: 2, sku: 'ACO-002', ean: '7891000100200', nome: 'Costela Bovina Especial Churrasco', departamento: 'Açougue', unidade: 'KG', preco_custo: 18.50, preco_venda: 29.90, preco_clube_crm: 25.90, cashback_pct: 2.0, fornecedor_id: 1, perecivel: true, img: '🍖' },
    { id: 3, sku: 'MER-101', ean: '7891000200108', nome: 'Arroz Branco Nobre Camil Tipo 1 5kg', departamento: 'Mercearia', unidade: 'UN', preco_custo: 21.00, preco_venda: 29.90, preco_clube_crm: 26.49, cashback_pct: 2.0, fornecedor_id: 4, perecivel: false, img: '🌾' },
    { id: 4, sku: 'MER-102', ean: '7891000200207', nome: 'Feijão Carioca Camil 1kg', departamento: 'Mercearia', unidade: 'UN', preco_custo: 5.40, preco_venda: 8.90, preco_clube_crm: 7.49, cashback_pct: 2.0, fornecedor_id: 4, perecivel: false, img: '🫘' },
    { id: 5, sku: 'MER-103', ean: '7891000200306', nome: 'Café Torrado e Moído Melitta Tradicional 500g', departamento: 'Mercearia', unidade: 'UN', preco_custo: 13.80, preco_venda: 22.90, preco_clube_crm: 18.90, cashback_pct: 2.5, fornecedor_id: 4, perecivel: false, img: '☕' },
    { id: 6, sku: 'BEB-201', ean: '7891000300105', nome: 'Cerveja Heineken Puro Malte Long Neck 330ml', departamento: 'Bebidas', unidade: 'UN', preco_custo: 4.50, preco_venda: 7.49, preco_clube_crm: 5.99, cashback_pct: 3.0, fornecedor_id: 3, perecivel: false, img: '🍺' },
    { id: 7, sku: 'BEB-202', ean: '7891000300204', nome: 'Refrigerante Coca-Cola Original 2L', departamento: 'Bebidas', unidade: 'UN', preco_custo: 6.20, preco_venda: 10.99, preco_clube_crm: 9.49, cashback_pct: 2.0, fornecedor_id: 3, perecivel: false, img: '🥤' },
    { id: 8, sku: 'FRI-301', ean: '7891000400102', nome: 'Queijo Mussarela Fatiado Tirol 400g', departamento: 'Frios', unidade: 'UN', preco_custo: 14.20, preco_venda: 22.50, preco_clube_crm: 18.90, cashback_pct: 2.5, fornecedor_id: 2, perecivel: true, img: '🧀' },
    { id: 9, sku: 'FRI-302', ean: '7891000400201', nome: 'Leite Integral UHT Tirol 1L', departamento: 'Frios', unidade: 'UN', preco_custo: 3.60, preco_venda: 5.49, preco_clube_crm: 4.79, cashback_pct: 2.0, fornecedor_id: 2, perecivel: true, img: '🥛' },
    { id: 10, sku: 'HOR-401', ean: '7891000500109', nome: 'Tomate Italiano Selecionado', departamento: 'Hortifruti', unidade: 'KG', preco_custo: 4.20, preco_venda: 8.90, preco_clube_crm: 6.99, cashback_pct: 2.0, fornecedor_id: 4, perecivel: true, img: '🍅' },
    { id: 11, sku: 'HOR-402', ean: '7891000500208', nome: 'Maçã Gala Nacional Especial', departamento: 'Hortifruti', unidade: 'KG', preco_custo: 5.50, preco_venda: 10.90, preco_clube_crm: 8.90, cashback_pct: 2.0, fornecedor_id: 4, perecivel: true, img: '🍎' },
    { id: 12, sku: 'LIM-501', ean: '7891000600106', nome: 'Sabão em Pó Omo Lavagem Perfeita 1.6kg', departamento: 'Limpeza', unidade: 'UN', preco_custo: 19.50, preco_venda: 29.90, preco_clube_crm: 24.90, cashback_pct: 2.0, fornecedor_id: 5, perecivel: false, img: '🧼' },
    { id: 13, sku: 'LIM-502', ean: '7891000600205', nome: 'Detergente Líquido Ypê Neutro 500ml', departamento: 'Limpeza', unidade: 'UN', preco_custo: 1.60, preco_venda: 2.79, preco_clube_crm: 2.29, cashback_pct: 1.5, fornecedor_id: 5, perecivel: false, img: '🧴' },
    { id: 14, sku: 'MER-104', ean: '7891000200405', nome: 'Azeite de Oliva Extra Virgem 500ml', departamento: 'Mercearia', unidade: 'UN', preco_custo: 28.00, preco_venda: 44.90, preco_clube_crm: 38.90, cashback_pct: 3.5, fornecedor_id: 4, perecivel: false, img: '🫒' }
  ],

  // Estoque consolidado por Filial
  estoques: [
    { id: 1, filial_id: 1, produto_id: 1, quantidade_atual: 450.0, estoque_minimo: 100.0, estoque_maximo: 800.0 },
    { id: 2, filial_id: 2, produto_id: 1, quantidade_atual: 45.0, estoque_minimo: 30.0, estoque_maximo: 150.0 },
    { id: 3, filial_id: 3, produto_id: 1, quantidade_atual: 120.0, estoque_minimo: 40.0, estoque_maximo: 200.0 },
    { id: 4, filial_id: 4, produto_id: 1, quantidade_atual: 8.0, estoque_minimo: 15.0, estoque_maximo: 40.0 }, // RUPTURA!
    
    { id: 5, filial_id: 1, produto_id: 6, quantidade_atual: 2400.0, estoque_minimo: 500.0, estoque_maximo: 5000.0 },
    { id: 6, filial_id: 2, produto_id: 6, quantidade_atual: 320.0, estoque_minimo: 100.0, estoque_maximo: 600.0 },
    { id: 7, filial_id: 3, produto_id: 6, quantidade_atual: 650.0, estoque_minimo: 150.0, estoque_maximo: 1000.0 },
    { id: 8, filial_id: 4, produto_id: 6, quantidade_atual: 18.0, estoque_minimo: 30.0, estoque_maximo: 80.0 }, // RUPTURA!

    { id: 9, filial_id: 1, produto_id: 8, quantidade_atual: 800.0, estoque_minimo: 200.0, estoque_maximo: 1200.0 },
    { id: 10, filial_id: 2, produto_id: 8, quantidade_atual: 65.0, estoque_minimo: 40.0, estoque_maximo: 180.0 },
    { id: 11, filial_id: 3, produto_id: 8, quantidade_atual: 140.0, estoque_minimo: 50.0, estoque_maximo: 250.0 },
    { id: 12, filial_id: 4, produto_id: 8, quantidade_atual: 35.0, estoque_minimo: 20.0, estoque_maximo: 60.0 },

    { id: 13, filial_id: 2, produto_id: 3, quantidade_atual: 180.0, estoque_minimo: 50.0, estoque_maximo: 300.0 },
    { id: 14, filial_id: 2, produto_id: 9, quantidade_atual: 95.0, estoque_minimo: 60.0, estoque_maximo: 200.0 },
    { id: 15, filial_id: 2, produto_id: 12, quantidade_atual: 110.0, estoque_minimo: 30.0, estoque_maximo: 160.0 }
  ],

  // Lotes com Controle FEFO (First Expired, First Out)
  lotes: [
    { id: 1, filial_id: 2, produto_id: 8, numero_lote: 'LOT-QUE-0412', data_fabricacao: '2026-09-20', data_validade: '2026-10-22', quantidade_lote: 22.0, status_lote: 'ALERTA_VENCIMENTO' },
    { id: 2, filial_id: 4, produto_id: 9, numero_lote: 'LOT-LEI-8819', data_fabricacao: '2026-09-25', data_validade: '2026-10-24', quantidade_lote: 18.0, status_lote: 'ALERTA_VENCIMENTO' },
    { id: 3, filial_id: 2, produto_id: 1, numero_lote: 'LOT-PIC-9902', data_fabricacao: '2026-10-05', data_validade: '2026-10-25', quantidade_lote: 15.0, status_lote: 'ALERTA_VENCIMENTO' },
    { id: 4, filial_id: 1, produto_id: 8, numero_lote: 'LOT-QUE-0518', data_fabricacao: '2026-10-01', data_validade: '2026-11-15', quantidade_lote: 350.0, status_lote: 'ATIVO' },
    { id: 5, filial_id: 3, produto_id: 6, numero_lote: 'LOT-HEI-2026', data_fabricacao: '2026-08-10', data_validade: '2027-02-15', quantidade_lote: 650.0, status_lote: 'ATIVO' },
    { id: 6, filial_id: 1, produto_id: 3, numero_lote: 'LOT-ARR-1120', data_fabricacao: '2026-09-01', data_validade: '2027-08-30', quantidade_lote: 1200.0, status_lote: 'ATIVO' }
  ],

  // Clientes no Clube CRM SuperSul (RFM 360º)
  clientes: [
    { id: 1, cpf: '123.456.789-00', nome: 'Mariana Souza Silveira', whatsapp: '(41) 99872-3344', email: 'mariana.souza@email.com', filial_preferida_id: 2, segmento_rfm: 'DIAMANTE', pontos_fidelidade: 1420, saldo_cashback: 68.50, total_gasto_historico: 12450.00, total_compras_count: 48, economia_acumulada_clube: 384.10, ultima_compra_em: '2026-10-16 18:22' },
    { id: 2, cpf: '987.654.321-11', nome: 'Roberto Carlos Mendes', whatsapp: '(41) 98711-2233', email: 'roberto.carlos@email.com', filial_preferida_id: 3, segmento_rfm: 'OURO', pontos_fidelidade: 680, saldo_cashback: 34.20, total_gasto_historico: 6890.00, total_compras_count: 26, economia_acumulada_clube: 198.50, ultima_compra_em: '2026-10-15 11:40' },
    { id: 3, cpf: '456.789.123-22', nome: 'Juliana Alencar Lima', whatsapp: '(41) 99122-8877', email: 'juliana.alencar@email.com', filial_preferida_id: 2, segmento_rfm: 'PRATA', pontos_fidelidade: 290, saldo_cashback: 15.80, total_gasto_historico: 2400.00, total_compras_count: 12, economia_acumulada_clube: 76.20, ultima_compra_em: '2026-10-12 14:15' },
    { id: 4, cpf: '321.654.987-33', nome: 'Fernando Henrique Dias', whatsapp: '(41) 99233-4455', email: 'f.henrique@email.com', filial_preferida_id: 4, segmento_rfm: 'EM_RISCO', pontos_fidelidade: 150, saldo_cashback: 8.00, total_gasto_historico: 1950.00, total_compras_count: 9, economia_acumulada_clube: 48.00, ultima_compra_em: '2026-09-02 19:30' },
    { id: 5, cpf: '111.222.333-44', nome: 'Camila Vasconcelos', whatsapp: '(41) 99655-7788', email: 'camila.v@email.com', filial_preferida_id: 2, segmento_rfm: 'NOVO', pontos_fidelidade: 100, saldo_cashback: 10.00, total_gasto_historico: 340.00, total_compras_count: 1, economia_acumulada_clube: 18.90, ultima_compra_em: '2026-10-10 16:05' }
  ],

  // Campanhas Promocionais Ativas
  campanhas: [
    { id: 1, titulo: 'Sexta do Churrasco Especial Diamante', segmento_alvo: 'DIAMANTE', canal: 'WHATSAPP_E_APP', desconto_extra_pct: 10.0, cashback_bonus_pct: 5.0, mensagem_template: 'Olá {nome}, preparamos cortes nobres com 10% de desconto extra e 5% de cashback só para você no Hipermercado Parque das Nações!', clientes_impactados: 3420, conversao_estimada_pct: 24.8, ativa: true },
    { id: 2, titulo: 'Volta pro Clube: Bônus de Resgate R$ 15', segmento_alvo: 'EM_RISCO', canal: 'WHATSAPP', desconto_extra_pct: 8.0, cashback_bonus_pct: 10.0, mensagem_template: '{nome}, sentimos sua falta! Ganhe R$ 15 de bônus em compras acima de R$ 80 até domingo na sua filial preferida.', clientes_impactados: 1120, conversao_estimada_pct: 16.5, ativa: true },
    { id: 3, titulo: 'Quarta da Limpeza & Higiene Ouro', segmento_alvo: 'OURO', canal: 'APP', desconto_extra_pct: 7.0, cashback_bonus_pct: 4.0, mensagem_template: 'Super Quarta Ouro! Leve Omo e produtos de limpeza selecionados com cashback turbinado.', clientes_impactados: 5180, conversao_estimada_pct: 21.2, ativa: true }
  ],

  // Pedidos de Compra (Supply Chain)
  compras: [
    { id: 1, numero_pedido: 'PC-2026-0089', filial_id: 1, fornecedor_id: 3, produto_id: 6, quantidade: 2000.0, custo_unitario: 4.50, valor_total: 9000.00, status: 'APROVADO', criado_em: '2026-10-16 10:15' },
    { id: 2, numero_pedido: 'PC-2026-0090', filial_id: 4, fornecedor_id: 1, produto_id: 1, quantidade: 80.0, custo_unitario: 48.00, valor_total: 3840.00, status: 'PENDENTE', criado_em: '2026-10-16 14:30' },
    { id: 3, numero_pedido: 'PC-2026-0091', filial_id: 2, fornecedor_id: 2, produto_id: 8, quantidade: 150.0, custo_unitario: 14.20, valor_total: 2130.00, status: 'RECEBIDO', criado_em: '2026-10-15 08:20' }
  ],

  // Últimos Cupons emitidos no PDV
  ultimasVendasPDV: [
    { id: 101, numero_cupom: 'SAT-NFCe-004810', filial_id: 2, cliente_nome: 'Mariana Souza Silveira', cliente_segmento: 'DIAMANTE', itens_count: 4, subtotal_bruto: 184.20, desconto_clube: 22.40, cashback_usado: 10.00, valor_liquido: 151.80, forma_pagamento: 'PIX', criada_em: 'Hoje, 11:42' },
    { id: 102, numero_cupom: 'SAT-NFCe-004811', filial_id: 3, cliente_nome: 'Roberto Carlos Mendes', cliente_segmento: 'OURO', itens_count: 6, subtotal_bruto: 312.50, desconto_clube: 34.00, cashback_usado: 0.00, valor_liquido: 278.50, forma_pagamento: 'CARTAO_CREDITO', criada_em: 'Hoje, 11:28' },
    { id: 103, numero_cupom: 'SAT-NFCe-004812', filial_id: 4, cliente_nome: 'Consumidor Não Identificado', cliente_segmento: null, itens_count: 2, subtotal_bruto: 42.80, desconto_clube: 0.00, cashback_usado: 0.00, valor_liquido: 42.80, forma_pagamento: 'DINHEIRO', criada_em: 'Hoje, 10:55' }
  ],

  // Lançamentos Financeiros (DRE)
  lancamentos: [
    { id: 1, filial_id: 2, tipo: 'RECEITA', categoria_dre: 'RECEITA_VENDAS', descricao: 'Vendas Balcão PDV e Caixa Diário', valor: 512800.0, status: 'PAGO', data_competencia: '2026-10-16' },
    { id: 2, filial_id: 2, tipo: 'CMV', categoria_dre: 'CMV_MERCADORIAS', descricao: 'Custo Mercadorias Vendidas Período', valor: 312800.0, status: 'PAGO', data_competencia: '2026-10-16' },
    { id: 3, filial_id: 2, tipo: 'DESPESA', categoria_dre: 'FOLHA_PAGAMENTO', descricao: 'Folha de Colaboradores e Operadores de Caixa', valor: 38400.0, status: 'PAGO', data_competencia: '2026-10-10' },
    { id: 4, filial_id: 2, tipo: 'DESPESA', categoria_dre: 'ENERGIA_ALUGUEL', descricao: 'Copel Energia Elétrica Câmaras Frias', valor: 14200.0, status: 'PAGO', data_competencia: '2026-10-05' },
    { id: 5, filial_id: 1, tipo: 'RECEITA', categoria_dre: 'RECEITA_VENDAS', descricao: 'Transferências e Faturamento CD Central', valor: 850400.0, status: 'PAGO', data_competencia: '2026-10-16' },
    { id: 6, filial_id: 1, tipo: 'CMV', categoria_dre: 'CMV_MERCADORIAS', descricao: 'CMV Consolidado CD Sul', valor: 510200.0, status: 'PAGO', data_competencia: '2026-10-16' },
    { id: 7, filial_id: 3, tipo: 'RECEITA', categoria_dre: 'RECEITA_VENDAS', descricao: 'Receita Operacional Atacarejo Sul', valor: 379450.0, status: 'PAGO', data_competencia: '2026-10-16' }
  ],

  // Central de Agentes CrewAI
  agentes: [
    { id: 1, nome: 'Agente Precificador Dinâmico & Margens', modelo: 'gemini-3.8-flash-low', tier: 1, status: 'ATIVO', ciclo_segundos: 60, missao: 'Calcula elasticidade de gôndola e aplica Preço Clube CRM em tempo real.', icone: 'fa-tags', cor: 'cyan' },
    { id: 2, nome: 'Agente Reposição Automática & Ruptura FEFO', modelo: 'gemini-4-argon-low', tier: 2, status: 'ATIVO', ciclo_segundos: 120, missao: 'Audita níveis de estoque multi-loja e prioriza lotes próximos ao vencimento.', icone: 'fa-boxes-stacked', cor: 'amber' },
    { id: 3, nome: 'Agente CRM 360º & Campanhas RFM', modelo: 'gemini-4-argon-low', tier: 2, status: 'ATIVO', ciclo_segundos: 180, missao: 'Clusteriza clientes em Diamante/Ouro e agenda disparos no WhatsApp.', icone: 'fa-bullhorn', cor: 'purple' },
    { id: 4, nome: 'Agente Prevenção de Perdas & Auditoria PDV', modelo: 'gemini-3.8-flash-low', tier: 1, status: 'ATIVO', ciclo_segundos: 30, missao: 'Monitora cancelamentos de itens, divergências de caixa e sangrias suspeitas.', icone: 'fa-shield-halved', cor: 'rose' },
    { id: 5, nome: 'Agente Compras & Negociação com Fornecedores', modelo: 'gemini-4-argon-low', tier: 2, status: 'ATIVO', ciclo_segundos: 300, missao: 'Analisa curva ABC de compras e gera ordens de abastecimento para o CD.', icone: 'fa-truck-fast', cor: 'blue' },
    { id: 6, nome: 'Agente Gestor Financeiro & DRE Estratégico', modelo: 'gemini-4-argon-high', tier: 3, status: 'ATIVO', ciclo_segundos: 600, missao: 'Consolida EBITDA, projeta fluxo de caixa da holding e auditoria tributária.', icone: 'fa-landmark', cor: 'emerald' }
  ],

  logsAgentes: [
    { hora: '11:45:12', agente: 'Agente Reposição FEFO', tier: 'Tier 2', filial: 'Express Centro', texto: 'Detectada iminência de ruptura em Cerveja Heineken (18 un restantes vs mín 30 un). Sugestão de transferência CD-01 disparada.' },
    { hora: '11:42:05', agente: 'Agente CRM & Campanhas', tier: 'Tier 2', filial: 'Hipermercado', texto: 'Campanha "Sexta do Churrasco Diamante" enviada para 3.420 clientes via WhatsApp com 24.8% de conversão estimada.' },
    { hora: '11:38:40', agente: 'Agente Precificador', tier: 'Tier 1', filial: 'Consolidado', texto: 'Preço Clube CRM aplicado com sucesso em 14 produtos do catálogo nacional.' },
    { hora: '11:30:15', agente: 'Agente Gestor Financeiro', tier: 'Tier 3', filial: 'Holding', texto: 'DRE Consolidado atualizado: EBITDA de R$ 348.910,00 com margem de 18.9% mantida dentro do target.' }
  ],

  // Estado do Carrinho Atual do PDV
  carrinhoPDV: {
    filialId: 2,
    cliente: null, // Objeto ClienteCRM ou null
    itens: [], // [{ produto, quantidade, precoUnitarioAplicado, subtotal }]
    usarCashback: false,
    valorCashbackAbater: 0.0,
    formaPagamento: 'PIX'
  }
};

// ==========================================
// 2. FUNÇÕES DE UTILIDADE E FORMATAÇÃO
// ==========================================
const utils = {
  formatMoney(val) {
    return Number(val || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
  },
  formatPercent(val) {
    return Number(val || 0).toFixed(1) + '%';
  },
  formatNumber(val) {
    return Number(val || 0).toLocaleString('pt-BR');
  },
  calcularDiasRestantes(dataValidadeStr) {
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const validade = new Date(dataValidadeStr);
    const diffTime = validade - hoje;
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  },
  getFilialNome(filialId) {
    const f = appState.filiais.find(item => item.id === Number(filialId));
    return f ? f.nome : 'Todas as Filiais (Consolidado)';
  },
  getProdutoNome(produtoId) {
    const p = appState.produtos.find(item => item.id === Number(produtoId));
    return p ? p.nome : 'Produto Desconhecido';
  },
  getFornecedorNome(fornecedorId) {
    const f = appState.fornecedores.find(item => item.id === Number(fornecedorId));
    return f ? f.nome_fantasia : 'Fornecedor Desconhecido';
  }
};

// ==========================================
// 3. API SERVICE COM FALLBACK INTELIGENTE
// ==========================================
const api = {
  async get(endpoint) {
    try {
      const res = await fetch(`${appState.apiBaseUrl}${endpoint}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn(`[API GET Fallback] ${endpoint} indisponível, usando estado interno local:`, e.message);
      return null;
    }
  },

  async post(endpoint, data) {
    try {
      const res = await fetch(`${appState.apiBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.warn(`[API POST Fallback] ${endpoint} simulado com sucesso no estado local:`, e.message);
      return null;
    }
  }
};

// ==========================================
// 4. CONTROLADOR PRINCIPAL (APP CORE)
// ==========================================
const app = {
  chartInstance: null,

  init() {
    this.iniciarRelogio();
    this.configurarNavegacao();
    this.configurarFiltroGlobal();
    this.configurarPDV();
    this.configurarEstoque();
    this.configurarCRM();
    this.configurarCompras();
    this.configurarFinanceiro();
    this.configurarAgentes();
    this.renderizarTudo();
    this.sincronizarComBackend();
  },

  iniciarRelogio() {
    const el = document.getElementById('live-clock');
    const update = () => {
      const agora = new Date();
      el.textContent = agora.toLocaleTimeString('pt-BR') + ' • ' + agora.toLocaleDateString('pt-BR');
    };
    update();
    setInterval(update, 1000);
  },

  showToast(mensagem, tipo = 'sucesso') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    const corBg = tipo === 'sucesso' ? 'bg-emerald-950/95 border-emerald-500/50 text-emerald-200' :
                  tipo === 'erro' ? 'bg-rose-950/95 border-rose-500/50 text-rose-200' :
                  'bg-amber-950/95 border-amber-500/50 text-amber-200';
    const icone = tipo === 'sucesso' ? 'fa-circle-check text-emerald-400' :
                  tipo === 'erro' ? 'fa-circle-xmark text-rose-400' :
                  'fa-triangle-exclamation text-amber-400';

    toast.className = `p-3.5 rounded-xl border shadow-xl flex items-center space-x-3 text-xs backdrop-blur-md transition-all duration-300 transform translate-x-5 opacity-0 pointer-events-auto ${corBg}`;
    toast.innerHTML = `
      <i class="fa-solid ${icone} text-base"></i>
      <span class="font-medium">${mensagem}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.remove('translate-x-5', 'opacity-0');
    }, 10);

    setTimeout(() => {
      toast.classList.add('translate-x-5', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  async sincronizarComBackend() {
    // Tenta consultar filiais reais se a API FastAPI estiver no ar
    const filiaisRemotas = await api.get('/filiais');
    if (filiaisRemotas && Array.isArray(filiaisRemotas) && filiaisRemotas.length > 0) {
      appState.filiais = filiaisRemotas;
      this.showToast('Conectado à API FastAPI oficial com sucesso!', 'sucesso');
    }
  },

  navegarPara(tabId) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById(tabId);
    if (target) {
      target.classList.remove('hidden');
    }

    // Atualiza botões do sidebar
    document.querySelectorAll('#sidebar-nav .nav-btn').forEach(btn => {
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active', 'bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
        btn.classList.remove('text-slate-400', 'hover:bg-slate-800/60');
      } else {
        btn.classList.remove('active', 'bg-emerald-500/10', 'text-emerald-400', 'border', 'border-emerald-500/20');
        btn.classList.add('text-slate-400', 'hover:bg-slate-800/60');
      }
    });

    appState.activeTab = tabId;

    // Atualiza título do Header
    const titulos = {
      'tab-dashboard': ['📊 Dashboard da Holding', 'Visão Executiva Consolidada • Grupo SuperSul'],
      'tab-pdv': ['🛒 Frente de Caixa / PDV Online', 'Operador de Caixa Rápido • Clube de Vantagens CRM'],
      'tab-estoque': ['📦 Estoque Multi-Filial & Validade FEFO', 'Ruptura, Controle de Validade e Transferências'],
      'tab-crm': ['🤝 CRM 360º & Fidelidade SuperSul', 'Segmentação RFM, Cashback e Disparos WhatsApp'],
      'tab-compras': ['🚚 Compras & Supply Chain', 'Ordens de Abastecimento e Homologação de Fornecedores'],
      'tab-financeiro': ['💰 Financeiro & DRE Gerencial', 'Demonstrativo de Resultado do Exercício e Fluxo de Caixa'],
      'tab-agentes': ['🤖 Central de Agentes IA & Servidor', 'CrewAI Autônomo • Topologia Híbrida 192.168.15.109']
    };

    if (titulos[tabId]) {
      document.getElementById('topbar-title').innerHTML = titulos[tabId][0];
      document.getElementById('topbar-subtitle').textContent = titulos[tabId][1];
    }

    if (tabId === 'tab-dashboard') {
      this.renderGraficoVendas();
    }
  },

  configurarNavegacao() {
    document.querySelectorAll('#sidebar-nav .nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const tab = btn.getAttribute('data-tab');
        this.navegarPara(tab);
      });
    });

    document.getElementById('btn-quick-pdv')?.addEventListener('click', () => {
      this.navegarPara('tab-pdv');
    });

    document.getElementById('btn-sync-data')?.addEventListener('click', () => {
      this.showToast('Sincronizando dados com o PostgreSQL 192.168.15.109...', 'aviso');
      setTimeout(() => {
        this.renderizarTudo();
        this.showToast('Dados consolidados atualizados com sucesso!', 'sucesso');
      }, 600);
    });

    // Mobile sidebar toggle
    document.getElementById('btn-toggle-sidebar')?.addEventListener('click', () => {
      const nav = document.getElementById('sidebar-nav');
      nav.classList.toggle('hidden');
    });
  },

  configurarFiltroGlobal() {
    const sel = document.getElementById('filtro-global-filial');
    sel.addEventListener('change', (e) => {
      appState.selectedFilialId = e.target.value;
      const filialNome = utils.getFilialNome(appState.selectedFilialId);
      this.showToast(`Filtro aplicado: ${filialNome}`, 'sucesso');
      this.renderizarTudo();
    });
  },

  // ==========================================
  // 5. RENDERIZADORES DOS 7 MÓDULOS
  // ==========================================
  renderizarTudo() {
    this.renderDashboard();
    this.renderPDV();
    this.renderEstoque();
    this.renderCRM();
    this.renderCompras();
    this.renderFinanceiro();
    this.renderAgentes();
  },

  // ------------------------------------------
  // MÓDULO 1: DASHBOARD DA HOLDING
  // ------------------------------------------
  renderDashboard() {
    const filialId = appState.selectedFilialId;
    let filiaisAlvo = appState.filiais;
    if (filialId !== 'all') {
      filiaisAlvo = appState.filiais.filter(f => f.id === Number(filialId));
    }

    // Calcula Totais
    const faturamentoTotal = filiaisAlvo.reduce((acc, f) => acc + f.faturamento_atual, 0);
    const metaTotal = filiaisAlvo.reduce((acc, f) => acc + f.meta_mensal, 0);
    const pctMetaGlobal = metaTotal > 0 ? (faturamentoTotal / metaTotal) * 100 : 0;
    const ebitda = faturamentoTotal * 0.189; // 18.9% margem ebitda

    document.getElementById('dash-filial-label').textContent = filialId === 'all' ? 'Consolidado 4 Unidades' : utils.getFilialNome(filialId);
    document.getElementById('kpi-faturamento').textContent = utils.formatMoney(faturamentoTotal);
    document.getElementById('kpi-ebitda').textContent = utils.formatMoney(ebitda);

    // Clientes CRM & Cashback
    const totalClientes = appState.clientes.length * 2964; // Projeção proporcional da base
    const totalCashback = appState.clientes.reduce((acc, c) => acc + c.saldo_cashback, 0) * 450;
    document.getElementById('kpi-clientes-crm').textContent = `${utils.formatNumber(totalClientes)} clientes`;
    document.getElementById('kpi-cashback-total').textContent = utils.formatMoney(totalCashback);

    // Rupturas
    const rupturas = appState.estoques.filter(e => {
      const matchFilial = filialId === 'all' || e.filial_id === Number(filialId);
      return matchFilial && e.quantidade_atual <= e.estoque_minimo;
    });
    document.getElementById('kpi-ruptura-count').textContent = `${rupturas.length} produtos`;

    // Metas por Filial
    const listaMetas = document.getElementById('lista-metas-filiais');
    listaMetas.innerHTML = '';
    appState.filiais.forEach(f => {
      const pct = Math.min(100, Math.round((f.faturamento_atual / f.meta_mensal) * 100));
      const corBarra = pct >= 90 ? 'bg-emerald-500' : pct >= 75 ? 'bg-amber-500' : 'bg-rose-500';

      const item = document.createElement('div');
      item.className = 'space-y-1.5';
      item.innerHTML = `
        <div class="flex justify-between items-baseline text-xs">
          <span class="font-semibold text-slate-200 truncate max-w-[180px]">${f.codigo} • ${f.bandeira}</span>
          <span class="font-mono text-slate-400 text-[11px]">${utils.formatMoney(f.faturamento_atual)} / <b class="text-white">${utils.formatMoney(f.meta_mensal)}</b></span>
        </div>
        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden flex items-center">
          <div class="${corBarra} h-full rounded-full transition-all duration-700" style="width: ${pct}%"></div>
        </div>
        <div class="flex justify-between text-[10px] text-slate-500">
          <span>Gerente: ${f.gerente}</span>
          <span class="font-bold font-mono ${pct >= 90 ? 'text-emerald-400' : 'text-amber-400'}">${pct}% da meta</span>
        </div>
      `;
      listaMetas.appendChild(item);
    });

    // Top Produtos
    const tbodyTop = document.getElementById('tabela-top-produtos');
    tbodyTop.innerHTML = '';
    const topProdutos = appState.produtos.slice(0, 5);
    topProdutos.forEach((p, idx) => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="py-2.5">
          <div class="flex items-center space-x-2">
            <span class="text-base">${p.img}</span>
            <div>
              <p class="font-semibold text-slate-200 text-xs">${p.nome}</p>
              <span class="text-[10px] text-slate-400">${p.departamento} • ${p.sku}</span>
            </div>
          </div>
        </td>
        <td class="py-2.5 text-right font-mono text-slate-300">${utils.formatNumber(1250 - idx * 180)} ${p.unidade}</td>
        <td class="py-2.5 text-right font-mono font-semibold text-white">${utils.formatMoney((1250 - idx * 180) * p.preco_venda)}</td>
        <td class="py-2.5 text-right font-mono text-amber-400 font-bold">${utils.formatMoney(p.preco_clube_crm)}</td>
      `;
      tbodyTop.appendChild(tr);
    });

    // Últimos Cupons PDV
    const tbodyCupons = document.getElementById('tabela-ultimos-cupons');
    tbodyCupons.innerHTML = '';
    appState.ultimasVendasPDV.forEach(v => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="py-2.5 font-mono text-slate-300 font-medium">${v.numero_cupom}</td>
        <td class="py-2.5 text-slate-400 text-[11px]">${utils.getFilialNome(v.filial_id).split('—')[0]}</td>
        <td class="py-2.5">
          <div class="flex items-center gap-1.5">
            <span class="font-semibold text-slate-200 text-xs">${v.cliente_nome}</span>
            ${v.cliente_segmento ? `<span class="text-[9px] font-bold px-1.5 py-0.2 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">${v.cliente_segmento}</span>` : ''}
          </div>
        </td>
        <td class="py-2.5 text-right font-mono font-bold text-emerald-400">${utils.formatMoney(v.valor_liquido)}</td>
        <td class="py-2.5 text-center">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">${v.forma_pagamento}</span>
        </td>
      `;
      tbodyCupons.appendChild(tr);
    });

    this.renderGraficoVendas();
  },

  renderGraficoVendas() {
    const canvas = document.getElementById('chart-vendas-departamentos');
    if (!canvas) return;

    if (this.chartInstance) {
      this.chartInstance.destroy();
    }

    const ctx = canvas.getContext('2d');
    this.chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
        datasets: [
          {
            label: 'Açougue & Carnes',
            data: [42000, 38000, 41000, 49000, 68000, 89000, 62000],
            backgroundColor: 'rgba(239, 68, 68, 0.75)',
            borderRadius: 6
          },
          {
            label: 'Mercearia & Grãos',
            data: [35000, 39000, 37000, 42000, 56000, 72000, 51000],
            backgroundColor: 'rgba(16, 185, 129, 0.75)',
            borderRadius: 6
          },
          {
            label: 'Bebidas & Frios',
            data: [28000, 29000, 31000, 38000, 62000, 84000, 58000],
            backgroundColor: 'rgba(245, 158, 11, 0.75)',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#94a3b8', font: { size: 11, family: 'Inter' } }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(51, 65, 85, 0.3)' },
            ticks: { color: '#94a3b8', font: { size: 10 } }
          },
          y: {
            grid: { color: 'rgba(51, 65, 85, 0.3)' },
            ticks: {
              color: '#94a3b8',
              font: { size: 10 },
              callback: (val) => 'R$ ' + (val / 1000) + 'k'
            }
          }
        }
      }
    });
  },

  // ------------------------------------------
  // MÓDULO 2: FRENTE DE CAIXA / PDV ONLINE
  // ------------------------------------------
  configurarPDV() {
    // Busca CPF
    document.getElementById('btn-buscar-cpf')?.addEventListener('click', () => this.buscarClientePorCPF());
    document.getElementById('pdv-cpf-input')?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.buscarClientePorCPF();
    });

    // Desvincular Cliente
    document.getElementById('btn-desvincular-cliente')?.addEventListener('click', () => {
      appState.carrinhoPDV.cliente = null;
      appState.carrinhoPDV.usarCashback = false;
      appState.carrinhoPDV.valorCashbackAbater = 0;
      document.getElementById('pdv-cpf-input').value = '';
      document.getElementById('pdv-cliente-card').classList.add('hidden');
      this.recalcularTotaisPDV();
      this.renderCatalogoPDV();
      this.showToast('Cliente desvinculado da venda.', 'aviso');
    });

    // Busca de produto por texto
    document.getElementById('pdv-busca-produto')?.addEventListener('input', (e) => {
      this.renderCatalogoPDV(e.target.value);
    });

    // Filtros de Categoria do PDV
    document.querySelectorAll('#pdv-filtro-categorias .cat-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#pdv-filtro-categorias .cat-pill').forEach(b => {
          b.classList.remove('active', 'bg-emerald-500', 'text-white');
          b.classList.add('bg-slate-800', 'text-slate-300');
        });
        btn.classList.add('active', 'bg-emerald-500', 'text-white');
        btn.classList.remove('bg-slate-800', 'text-slate-300');
        const cat = btn.getAttribute('data-cat');
        this.renderCatalogoPDV(document.getElementById('pdv-busca-produto').value, cat);
      });
    });

    // Toggle Cashback
    document.getElementById('pdv-check-usar-cashback')?.addEventListener('change', (e) => {
      appState.carrinhoPDV.usarCashback = e.target.checked;
      const wrap = document.getElementById('pdv-input-cashback-wrap');
      if (e.target.checked) {
        wrap.classList.remove('hidden');
        this.usarMaximoCashback();
      } else {
        wrap.classList.add('hidden');
        appState.carrinhoPDV.valorCashbackAbater = 0;
      }
      this.recalcularTotaisPDV();
    });

    document.getElementById('btn-usar-max-cashback')?.addEventListener('click', () => this.usarMaximoCashback());

    document.getElementById('pdv-valor-cashback-utilizar')?.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value) || 0;
      const saldoMax = appState.carrinhoPDV.cliente ? appState.carrinhoPDV.cliente.saldo_cashback : 0;
      appState.carrinhoPDV.valorCashbackAbater = Math.min(val, saldoMax);
      this.recalcularTotaisPDV();
    });

    // Formas de Pagamento
    document.querySelectorAll('#pdv-formas-pagamento .btn-forma').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#pdv-formas-pagamento .btn-forma').forEach(b => {
          b.classList.remove('active', 'bg-emerald-600', 'text-white');
          b.classList.add('bg-slate-800', 'text-slate-300');
        });
        btn.classList.add('active', 'bg-emerald-600', 'text-white');
        btn.classList.remove('bg-slate-800', 'text-slate-300');
        appState.carrinhoPDV.formaPagamento = btn.getAttribute('data-forma');
      });
    });

    // Cancelar Venda
    document.getElementById('btn-cancelar-venda-pdv')?.addEventListener('click', () => {
      if (appState.carrinhoPDV.itens.length === 0) return;
      if (confirm('Deseja realmente cancelar e esvaziar a venda atual do PDV?')) {
        this.limparCarrinhoPDV();
        this.showToast('Venda cancelada pelo operador.', 'aviso');
      }
    });

    // Finalizar Venda
    document.getElementById('btn-finalizar-venda')?.addEventListener('click', () => this.finalizarVendaPDV());

    // Fechar Modal Cupom
    document.getElementById('btn-fechar-modal-cupom')?.addEventListener('click', () => {
      document.getElementById('modal-cupom').classList.add('hidden');
    });
    document.getElementById('btn-nova-venda-pos-cupom')?.addEventListener('click', () => {
      document.getElementById('modal-cupom').classList.add('hidden');
      this.limparCarrinhoPDV();
    });
  },

  renderPDV() {
    this.renderCatalogoPDV();
    this.renderItensCarrinho();
  },

  async buscarClientePorCPF() {
    const rawCpf = document.getElementById('pdv-cpf-input').value.trim();
    if (!rawCpf) {
      this.showToast('Por favor, informe o CPF do cliente.', 'aviso');
      return;
    }

    const cleanCpf = rawCpf.replace(/\D/g, '');
    let cliente = null;

    // Tenta backend via GET /api/crm/clientes/cpf/{cpf}
    const remoto = await api.get(`/crm/clientes/cpf/${cleanCpf}`);
    if (remoto && remoto.id) {
      cliente = remoto;
    } else {
      // Local search
      cliente = appState.clientes.find(c => c.cpf.replace(/\D/g, '') === cleanCpf || c.cpf === rawCpf);
    }

    if (!cliente) {
      this.showToast(`CPF ${rawCpf} não localizado no Clube SuperSul. Deseja cadastrá-lo?`, 'aviso');
      return;
    }

    appState.carrinhoPDV.cliente = cliente;

    // Atualiza Card Visual do Cliente
    const card = document.getElementById('pdv-cliente-card');
    card.classList.remove('hidden');
    document.getElementById('pdv-cliente-nome').textContent = cliente.nome;
    document.getElementById('pdv-cliente-segmento').textContent = cliente.segmento_rfm;
    document.getElementById('pdv-cliente-cpf-label').textContent = `CPF: ${cliente.cpf}`;
    document.getElementById('pdv-cliente-saldo-cashback').textContent = utils.formatMoney(cliente.saldo_cashback);
    document.getElementById('pdv-cliente-pontos').textContent = `${cliente.pontos_fidelidade} pts`;
    document.getElementById('pdv-cliente-economia').textContent = utils.formatMoney(cliente.economia_acumulada_clube);

    // Ajusta cores por segmento
    const segEl = document.getElementById('pdv-cliente-segmento');
    segEl.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full text-white ' +
      (cliente.segmento_rfm === 'DIAMANTE' ? 'bg-purple-600' :
       cliente.segmento_rfm === 'OURO' ? 'bg-amber-500' :
       cliente.segmento_rfm === 'PRATA' ? 'bg-slate-500' :
       cliente.segmento_rfm === 'EM_RISCO' ? 'bg-rose-500' : 'bg-emerald-500');

    // Habilita container de cashback se saldo > 0
    const containerCashback = document.getElementById('pdv-container-abater-cashback');
    if (cliente.saldo_cashback > 0) {
      containerCashback.classList.remove('hidden');
      document.getElementById('pdv-label-cashback-disponivel').textContent = utils.formatMoney(cliente.saldo_cashback);
    } else {
      containerCashback.classList.add('hidden');
    }

    this.showToast(`Cliente Clube ${cliente.segmento_rfm} identificado! Preço Clube ativado!`, 'sucesso');
    this.recalcularTotaisPDV();
    this.renderCatalogoPDV();
  },

  renderCatalogoPDV(busca = '', categoria = 'TODOS') {
    const grid = document.getElementById('pdv-grid-produtos');
    if (!grid) return;

    grid.innerHTML = '';
    const clienteAtivo = appState.carrinhoPDV.cliente;

    let filtrados = appState.produtos;
    if (categoria && categoria !== 'TODOS') {
      filtrados = filtrados.filter(p => p.departamento.toLowerCase() === categoria.toLowerCase());
    }
    if (busca) {
      const q = busca.toLowerCase();
      filtrados = filtrados.filter(p => p.nome.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) || p.ean.includes(q));
    }

    filtrados.forEach(p => {
      const temPrecoClube = clienteAtivo && p.preco_clube_crm < p.preco_venda;
      const precoFinal = temPrecoClube ? p.preco_clube_crm : p.preco_venda;

      const card = document.createElement('div');
      card.className = 'bg-slate-950 p-3 rounded-xl border border-slate-800 hover:border-emerald-500/50 flex flex-col justify-between transition cursor-pointer group active:scale-[0.98]';
      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-2xl">${p.img}</span>
            <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">${p.unidade}</span>
          </div>
          <h5 class="text-xs font-semibold text-slate-200 line-clamp-2 leading-tight">${p.nome}</h5>
          <p class="text-[10px] text-slate-500 font-mono mt-0.5">EAN ${p.ean.slice(-5)}</p>
        </div>

        <div class="mt-3 pt-2 border-t border-slate-900">
          ${temPrecoClube ? `
            <div class="flex items-center justify-between">
              <span class="text-[10px] line-through text-slate-500 font-mono">${utils.formatMoney(p.preco_venda)}</span>
              <span class="text-[9px] font-bold text-amber-400 bg-amber-500/10 px-1 rounded">CLUBE CRM</span>
            </div>
            <div class="text-sm font-black font-mono text-emerald-400">${utils.formatMoney(precoFinal)}</div>
          ` : `
            <span class="text-[10px] text-slate-400 block font-mono">Preço Venda</span>
            <div class="text-sm font-bold font-mono text-white">${utils.formatMoney(p.preco_venda)}</div>
          `}
          
          <button class="mt-2 w-full py-1.5 bg-slate-800 group-hover:bg-emerald-600 text-slate-200 group-hover:text-white rounded-lg text-[11px] font-semibold flex items-center justify-center gap-1 transition">
            <i class="fa-solid fa-plus text-[10px]"></i> Adicionar
          </button>
        </div>
      `;

      card.addEventListener('click', () => {
        this.adicionarItemAoCarrinho(p);
      });

      grid.appendChild(card);
    });
  },

  adicionarItemAoCarrinho(produto) {
    const clienteAtivo = appState.carrinhoPDV.cliente;
    const precoAplicado = clienteAtivo ? produto.preco_clube_crm : produto.preco_venda;

    const itemExistente = appState.carrinhoPDV.itens.find(i => i.produto.id === produto.id);
    if (itemExistente) {
      itemExistente.quantidade += 1;
      itemExistente.precoUnitarioAplicado = precoAplicado;
      itemExistente.subtotal = itemExistente.quantidade * precoAplicado;
    } else {
      appState.carrinhoPDV.itens.push({
        produto: produto,
        quantidade: 1,
        precoUnitarioAplicado: precoAplicado,
        subtotal: precoAplicado
      });
    }

    this.recalcularTotaisPDV();
    this.renderItensCarrinho();
  },

  alterarQuantidadeItem(index, delta) {
    const item = appState.carrinhoPDV.itens[index];
    if (!item) return;

    item.quantidade += delta;
    if (item.quantidade <= 0) {
      appState.carrinhoPDV.itens.splice(index, 1);
    } else {
      item.subtotal = item.quantidade * item.precoUnitarioAplicado;
    }

    this.recalcularTotaisPDV();
    this.renderItensCarrinho();
  },

  removerItemCarrinho(index) {
    appState.carrinhoPDV.itens.splice(index, 1);
    this.recalcularTotaisPDV();
    this.renderItensCarrinho();
  },

  renderItensCarrinho() {
    const container = document.getElementById('pdv-itens-carrinho');
    const badgeCount = document.getElementById('pdv-itens-count');
    if (!container) return;

    const totalItens = appState.carrinhoPDV.itens.reduce((acc, i) => acc + i.quantidade, 0);
    badgeCount.textContent = `${totalItens} ${totalItens === 1 ? 'item' : 'itens'}`;

    if (appState.carrinhoPDV.itens.length === 0) {
      container.innerHTML = `
        <div class="text-center py-12 text-slate-500 text-xs">
          <i class="fa-solid fa-cart-arrow-down text-3xl mb-2 text-slate-600 block"></i>
          Nenhum produto adicionado ao carrinho.<br>Bipe o código ou clique em um item do catálogo.
        </div>
      `;
      return;
    }

    container.innerHTML = '';
    const clienteAtivo = appState.carrinhoPDV.cliente;

    appState.carrinhoPDV.itens.forEach((item, idx) => {
      const p = item.produto;
      const temDescontoClube = clienteAtivo && item.precoUnitarioAplicado < p.preco_venda;

      const row = document.createElement('div');
      row.className = 'p-2.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs';
      row.innerHTML = `
        <div class="flex items-center space-x-2.5 truncate max-w-[170px]">
          <span class="text-xl">${p.img}</span>
          <div class="truncate">
            <h6 class="font-bold text-slate-200 truncate leading-tight">${p.nome}</h6>
            <div class="flex items-center gap-1.5 text-[10px]">
              <span class="font-mono ${temDescontoClube ? 'text-amber-400 font-bold' : 'text-slate-400'}">
                ${utils.formatMoney(item.precoUnitarioAplicado)}
              </span>
              ${temDescontoClube ? `<span class="line-through text-slate-600 font-mono">${utils.formatMoney(p.preco_venda)}</span>` : ''}
            </div>
          </div>
        </div>

        <div class="flex items-center space-x-2">
          <!-- Quantidade Controls -->
          <div class="flex items-center bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <button onclick="app.alterarQuantidadeItem(${idx}, -1)" class="px-2 py-1 text-slate-400 hover:text-white text-xs">-</button>
            <span class="px-2 py-1 text-white font-mono font-bold text-xs">${item.quantidade}</span>
            <button onclick="app.alterarQuantidadeItem(${idx}, 1)" class="px-2 py-1 text-slate-400 hover:text-white text-xs">+</button>
          </div>

          <div class="text-right w-16">
            <span class="font-bold font-mono text-white text-xs block">${utils.formatMoney(item.subtotal)}</span>
          </div>

          <button onclick="app.removerItemCarrinho(${idx})" class="text-slate-500 hover:text-rose-400 p-1">
            <i class="fa-solid fa-trash-can text-[11px]"></i>
          </button>
        </div>
      `;
      container.appendChild(row);
    });
  },

  recalcularTotaisPDV() {
    const clienteAtivo = appState.carrinhoPDV.cliente;
    let subtotalBruto = 0;
    let descontoClube = 0;
    let cashbackGerado = 0;

    appState.carrinhoPDV.itens.forEach(item => {
      const precoNormalTotal = item.produto.preco_venda * item.quantidade;
      subtotalBruto += precoNormalTotal;

      if (clienteAtivo) {
        const precoClubeTotal = item.produto.preco_clube_crm * item.quantidade;
        descontoClube += Math.max(0, precoNormalTotal - precoClubeTotal);
        // Atualiza preco unitario aplicado
        item.precoUnitarioAplicado = item.produto.preco_clube_crm;
        item.subtotal = precoClubeTotal;
      } else {
        item.precoUnitarioAplicado = item.produto.preco_venda;
        item.subtotal = precoNormalTotal;
      }

      // Cashback gerado
      cashbackGerado += (item.subtotal * (item.produto.cashback_pct / 100));
    });

    const subtotalComDesconto = subtotalBruto - descontoClube;
    let cashbackAbater = 0;

    if (appState.carrinhoPDV.usarCashback && clienteAtivo) {
      cashbackAbater = Math.min(appState.carrinhoPDV.valorCashbackAbater, clienteAtivo.saldo_cashback, subtotalComDesconto);
    }

    const totalLiquido = Math.max(0, subtotalComDesconto - cashbackAbater);

    // Atualiza DOM
    document.getElementById('pdv-subtotal-bruto').textContent = utils.formatMoney(subtotalBruto);
    document.getElementById('pdv-desconto-clube').textContent = `- ${utils.formatMoney(descontoClube)}`;
    
    const linhaAbate = document.getElementById('pdv-linha-abatimento-cashback');
    if (cashbackAbater > 0) {
      linhaAbate.style.display = 'flex';
      document.getElementById('pdv-cashback-abatido').textContent = `- ${utils.formatMoney(cashbackAbater)}`;
    } else {
      linhaAbate.style.display = 'none';
    }

    document.getElementById('pdv-total-liquido').textContent = utils.formatMoney(totalLiquido);
    document.getElementById('pdv-cashback-gerado').textContent = `+ ${utils.formatMoney(cashbackGerado)}`;

    appState.carrinhoPDV.subtotalBruto = subtotalBruto;
    appState.carrinhoPDV.descontoClube = descontoClube;
    appState.carrinhoPDV.cashbackAbater = cashbackAbater;
    appState.carrinhoPDV.totalLiquido = totalLiquido;
    appState.carrinhoPDV.cashbackGerado = cashbackGerado;

    // Habilita/Desabilita botão de finalização
    const btnFin = document.getElementById('btn-finalizar-venda');
    btnFin.disabled = appState.carrinhoPDV.itens.length === 0;
  },

  usarMaximoCashback() {
    if (!appState.carrinhoPDV.cliente) return;
    const saldo = appState.carrinhoPDV.cliente.saldo_cashback;
    const totalCompra = (appState.carrinhoPDV.subtotalBruto || 0) - (appState.carrinhoPDV.descontoClube || 0);
    const maxPossivel = Math.min(saldo, totalCompra);
    document.getElementById('pdv-valor-cashback-utilizar').value = maxPossivel.toFixed(2);
    appState.carrinhoPDV.valorCashbackAbater = maxPossivel;
    this.recalcularTotaisPDV();
  },

  async finalizarVendaPDV() {
    if (appState.carrinhoPDV.itens.length === 0) {
      this.showToast('Adicione produtos ao carrinho antes de finalizar.', 'erro');
      return;
    }

    const filialId = Number(document.getElementById('pdv-filial-select').value);
    const payload = {
      filial_id: filialId,
      cliente_id: appState.carrinhoPDV.cliente ? appState.carrinhoPDV.cliente.id : null,
      subtotal_bruto: appState.carrinhoPDV.subtotalBruto,
      desconto_clube_crm: appState.carrinhoPDV.descontoClube,
      cashback_utilizado: appState.carrinhoPDV.cashbackAbater,
      valor_total_liquido: appState.carrinhoPDV.totalLiquido,
      cashback_gerado: appState.carrinhoPDV.cashbackGerado,
      forma_pagamento: appState.carrinhoPDV.formaPagamento,
      itens: appState.carrinhoPDV.itens.map(i => ({
        produto_id: i.produto.id,
        quantidade: i.quantidade,
        preco_unitario_aplicado: i.precoUnitarioAplicado
      }))
    };

    // Chamada POST /api/pdv/venda
    await api.post('/pdv/venda', payload);

    // Dispara Confetti comemorativo de venda realizada!
    if (window.confetti) {
      confetti({
        particleCount: 80,
        spread: 60,
        origin: { y: 0.7 }
      });
    }

    // Dá baixa no estoque local da filial
    appState.carrinhoPDV.itens.forEach(item => {
      const est = appState.estoques.find(e => e.filial_id === filialId && e.produto_id === item.produto.id);
      if (est) {
        est.quantidade_atual = Math.max(0, est.quantidade_atual - item.quantidade);
      }
    });

    // Se cliente identificado, atualiza cashback no CRM
    if (appState.carrinhoPDV.cliente) {
      const cl = appState.clientes.find(c => c.id === appState.carrinhoPDV.cliente.id);
      if (cl) {
        cl.saldo_cashback = Math.max(0, cl.saldo_cashback - appState.carrinhoPDV.cashbackAbater + appState.carrinhoPDV.cashbackGerado);
        cl.pontos_fidelidade += Math.round(appState.carrinhoPDV.totalLiquido);
        cl.total_gasto_historico += appState.carrinhoPDV.totalLiquido;
        cl.total_compras_count += 1;
        cl.economia_acumulada_clube += appState.carrinhoPDV.descontoClube;
      }
    }

    // Registra nos últimos cupons do dashboard
    const novoCupomNum = `SAT-NFCe-${Math.floor(100000 + Math.random() * 900000)}`;
    appState.ultimasVendasPDV.unshift({
      id: Date.now(),
      numero_cupom: novoCupomNum,
      filial_id: filialId,
      cliente_nome: appState.carrinhoPDV.cliente ? appState.carrinhoPDV.cliente.nome : 'Consumidor Não Identificado',
      cliente_segmento: appState.carrinhoPDV.cliente ? appState.carrinhoPDV.cliente.segmento_rfm : null,
      itens_count: appState.carrinhoPDV.itens.length,
      subtotal_bruto: appState.carrinhoPDV.subtotalBruto,
      desconto_clube: appState.carrinhoPDV.descontoClube,
      cashback_usado: appState.carrinhoPDV.cashbackAbater,
      valor_liquido: appState.carrinhoPDV.totalLiquido,
      forma_pagamento: appState.carrinhoPDV.formaPagamento,
      criada_em: 'Agora mesmo'
    });

    // Emite o Cupom Fiscal Visual
    this.exibirCupomFiscal(novoCupomNum, filialId);
    this.showToast('Venda finalizada com sucesso! Cupom NFC-e emitido.', 'sucesso');
    this.renderDashboard();
    this.renderEstoque();
    this.renderCRM();
  },

  exibirCupomFiscal(numeroCupom, filialId) {
    const filial = appState.filiais.find(f => f.id === filialId) || appState.filiais[1];
    const cliente = appState.carrinhoPDV.cliente;
    const container = document.getElementById('cupom-papel-conteudo');
    const agora = new Date();

    let itensHtml = '';
    appState.carrinhoPDV.itens.forEach((it, idx) => {
      itensHtml += `
        <div class="flex justify-between py-0.5 text-[11px]">
          <span>${String(idx + 1).padStart(2, '0')} ${it.produto.nome.slice(0, 24)}</span>
        </div>
        <div class="flex justify-between text-[10px] text-slate-600 mb-1">
          <span>${it.quantidade} ${it.produto.unidade} x ${utils.formatMoney(it.precoUnitarioAplicado)}</span>
          <span class="font-bold text-black">${utils.formatMoney(it.subtotal)}</span>
        </div>
      `;
    });

    container.innerHTML = `
      <div class="text-center border-b border-dashed border-slate-400 pb-3 mb-3">
        <h3 class="font-bold text-sm tracking-wider uppercase">SUPERSUL SUPERMERCADOS S/A</h3>
        <p class="text-[10px]">${filial.nome}</p>
        <p class="text-[10px]">CNPJ: ${filial.cnpj} • IE: 902.812.331-00</p>
        <p class="text-[10px]">${filial.cidade}</p>
        <div class="my-2 py-1 border-y border-dashed border-slate-300 font-bold text-xs uppercase">
          Documento Auxiliar da NFC-e
        </div>
        <p class="text-[10px] font-mono">${numeroCupom} • Série 001</p>
        <p class="text-[10px]">${agora.toLocaleDateString('pt-BR')} ${agora.toLocaleTimeString('pt-BR')} • Caixa 03</p>
      </div>

      <div class="border-b border-dashed border-slate-400 pb-2 mb-2">
        <p class="text-[10px] uppercase font-semibold">Consumidor:</p>
        ${cliente ? `
          <p class="text-[11px] font-bold">${cliente.nome}</p>
          <p class="text-[10px]">CPF: ${cliente.cpf} • Clube [${cliente.segmento_rfm}]</p>
        ` : `
          <p class="text-[10px] italic">CONSUMIDOR NÃO IDENTIFICADO</p>
        `}
      </div>

      <div class="border-b border-dashed border-slate-400 pb-2 mb-2">
        <div class="text-[10px] font-bold uppercase mb-1 flex justify-between">
          <span>Item / Descrição</span>
          <span>Total (R$)</span>
        </div>
        ${itensHtml}
      </div>

      <div class="space-y-1 border-b border-dashed border-slate-400 pb-2 mb-3 text-[11px]">
        <div class="flex justify-between">
          <span>Qtd Total de Itens:</span>
          <span>${appState.carrinhoPDV.itens.reduce((acc, i) => acc + i.quantidade, 0)}</span>
        </div>
        <div class="flex justify-between">
          <span>Subtotal Bruto:</span>
          <span>${utils.formatMoney(appState.carrinhoPDV.subtotalBruto)}</span>
        </div>
        ${appState.carrinhoPDV.descontoClube > 0 ? `
          <div class="flex justify-between font-bold text-emerald-700">
            <span>Desconto Clube SuperSul:</span>
            <span>- ${utils.formatMoney(appState.carrinhoPDV.descontoClube)}</span>
          </div>
        ` : ''}
        ${appState.carrinhoPDV.cashbackAbater > 0 ? `
          <div class="flex justify-between font-bold text-amber-800">
            <span>Abatimento Cashback CRM:</span>
            <span>- ${utils.formatMoney(appState.carrinhoPDV.cashbackAbater)}</span>
          </div>
        ` : ''}
        <div class="flex justify-between text-sm font-black pt-1 border-t border-slate-300">
          <span>VALOR A PAGAR:</span>
          <span>${utils.formatMoney(appState.carrinhoPDV.totalLiquido)}</span>
        </div>
        <div class="flex justify-between text-[10px] pt-1 text-slate-600">
          <span>Forma de Pagamento:</span>
          <span class="font-bold">${appState.carrinhoPDV.formaPagamento}</span>
        </div>
      </div>

      ${cliente ? `
        <div class="p-2 bg-slate-100 rounded border border-slate-300 text-center mb-3 text-[10px]">
          <p class="font-bold text-emerald-800">🎉 VOCÊ ECONOMIZOU NO CLUBE SUPERSUL!</p>
          <p>Economia nesta compra: <b>${utils.formatMoney(appState.carrinhoPDV.descontoClube)}</b></p>
          <p>Novo Cashback acumulado: <b>+ ${utils.formatMoney(appState.carrinhoPDV.cashbackGerado)}</b></p>
          <p class="font-mono text-[9px] text-slate-600 mt-1">Saldo Atual de Cashback: ${utils.formatMoney(cliente.saldo_cashback)}</p>
        </div>
      ` : ''}

      <div class="text-center text-[9px] text-slate-500 font-mono">
        <p>Consulte pela Chave de Acesso em:</p>
        <p class="break-all font-bold text-[8px] text-black">4126 1045 8921 0200 0271 6500 1000 0481 2110 9482 1092</p>
        <div class="w-24 h-24 mx-auto my-2 bg-slate-200 flex items-center justify-center border border-slate-300">
          <i class="fa-solid fa-qrcode text-5xl text-black"></i>
        </div>
        <p>PROTOCOLO DE AUTORIZAÇÃO: 141260098412891</p>
        <p>Tributos Totais Incidentes (Lei 12.741/2012): 13.45%</p>
      </div>
    `;

    document.getElementById('modal-cupom').classList.remove('hidden');
  },

  limparCarrinhoPDV() {
    appState.carrinhoPDV.itens = [];
    appState.carrinhoPDV.cliente = null;
    appState.carrinhoPDV.usarCashback = false;
    appState.carrinhoPDV.valorCashbackAbater = 0;
    document.getElementById('pdv-cpf-input').value = '';
    document.getElementById('pdv-cliente-card').classList.add('hidden');
    document.getElementById('pdv-container-abater-cashback').classList.add('hidden');
    this.recalcularTotaisPDV();
    this.renderItensCarrinho();
    this.renderCatalogoPDV();
  },

  // ------------------------------------------
  // MÓDULO 3: ESTOQUE MULTI-FILIAL & FEFO
  // ------------------------------------------
  configurarEstoque() {
    // Alternância de Subtabs (Posição vs FEFO)
    const btnPos = document.getElementById('btn-subtab-posicao');
    const btnLotes = document.getElementById('btn-subtab-lotes');
    const viewPos = document.getElementById('subview-posicao-estoque');
    const viewLotes = document.getElementById('subview-lotes-fefo');

    btnPos?.addEventListener('click', () => {
      btnPos.classList.add('active', 'text-white', 'bg-slate-800', 'border-slate-700');
      btnPos.classList.remove('text-slate-400', 'bg-slate-900/60', 'border-transparent');
      btnLotes.classList.remove('active', 'text-white', 'bg-slate-800', 'border-slate-700');
      btnLotes.classList.add('text-slate-400', 'bg-slate-900/60', 'border-transparent');
      viewPos.classList.remove('hidden');
      viewLotes.classList.add('hidden');
    });

    btnLotes?.addEventListener('click', () => {
      btnLotes.classList.add('active', 'text-white', 'bg-slate-800', 'border-slate-700');
      btnLotes.classList.remove('text-slate-400', 'bg-slate-900/60', 'border-transparent');
      btnPos.classList.remove('active', 'text-white', 'bg-slate-800', 'border-slate-700');
      btnPos.classList.add('text-slate-400', 'bg-slate-900/60', 'border-transparent');
      viewLotes.classList.remove('hidden');
      viewPos.classList.add('hidden');
    });

    // Filtro por status
    document.getElementById('filtro-status-estoque')?.addEventListener('change', () => {
      this.renderEstoque();
    });

    // Modais de Entrada e Transferência
    document.getElementById('btn-modal-entrada-estoque')?.addEventListener('click', () => {
      this.abrirModalEntradaEstoque();
    });
    document.getElementById('btn-fechar-modal-entrada')?.addEventListener('click', () => {
      document.getElementById('modal-entrada-estoque').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-entrada')?.addEventListener('click', () => {
      document.getElementById('modal-entrada-estoque').classList.add('hidden');
    });

    document.getElementById('btn-modal-transferencia-estoque')?.addEventListener('click', () => {
      this.abrirModalTransferencia();
    });
    document.getElementById('btn-fechar-modal-transferencia')?.addEventListener('click', () => {
      document.getElementById('modal-transferencia-estoque').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-transf')?.addEventListener('click', () => {
      document.getElementById('modal-transferencia-estoque').classList.add('hidden');
    });

    // Submissão de Entrada de Mercadoria
    document.getElementById('form-entrada-estoque')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const filialId = Number(document.getElementById('entrada-filial-id').value);
      const produtoId = Number(document.getElementById('entrada-produto-id').value);
      const qtd = Number(document.getElementById('entrada-quantidade').value);
      const lote = document.getElementById('entrada-numero-lote').value.trim();
      const fab = document.getElementById('entrada-data-fabricacao').value;
      const val = document.getElementById('entrada-data-validade').value;
      const obs = document.getElementById('entrada-observacao').value;

      const payload = {
        filial_id: filialId,
        produto_id: produtoId,
        tipo: 'ENTRADA_COMPRA',
        quantidade: qtd,
        numero_lote: lote,
        data_fabricacao: fab,
        data_validade: val,
        observacao: obs
      };

      await api.post('/estoque/movimentar', payload);

      // Atualiza localmente
      let est = appState.estoques.find(e => e.filial_id === filialId && e.produto_id === produtoId);
      if (est) {
        est.quantidade_atual += qtd;
      } else {
        appState.estoques.push({
          id: Date.now(),
          filial_id: filialId,
          produto_id: produtoId,
          quantidade_atual: qtd,
          estoque_minimo: 20.0,
          estoque_maximo: 500.0
        });
      }

      appState.lotes.push({
        id: Date.now(),
        filial_id: filialId,
        produto_id: produtoId,
        numero_lote: lote,
        data_fabricacao: fab,
        data_validade: val,
        quantidade_lote: qtd,
        status_lote: 'ATIVO'
      });

      document.getElementById('modal-entrada-estoque').classList.add('hidden');
      this.showToast(`Entrada de ${qtd} un registrada com sucesso no estoque!`, 'sucesso');
      this.renderEstoque();
      this.renderDashboard();
    });

    // Submissão de Transferência
    document.getElementById('form-transferencia-estoque')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const origemId = Number(document.getElementById('transf-origem-id').value);
      const destinoId = Number(document.getElementById('transf-destino-id').value);
      const produtoId = Number(document.getElementById('transf-produto-id').value);
      const qtd = Number(document.getElementById('transf-quantidade').value);
      const obs = document.getElementById('transf-observacao').value;

      if (origemId === destinoId) {
        this.showToast('A filial de origem deve ser diferente da filial de destino.', 'erro');
        return;
      }

      const estOrigem = appState.estoques.find(e => e.filial_id === origemId && e.produto_id === produtoId);
      if (!estOrigem || estOrigem.quantidade_atual < qtd) {
        this.showToast('Saldo insuficiente na filial de origem para realizar a transferência.', 'erro');
        return;
      }

      const payload = {
        filial_origem_id: origemId,
        filial_destino_id: destinoId,
        produto_id: produtoId,
        quantidade: qtd,
        observacao: obs
      };

      await api.post('/estoque/transferir', payload);

      estOrigem.quantidade_atual -= qtd;
      let estDestino = appState.estoques.find(e => e.filial_id === destinoId && e.produto_id === produtoId);
      if (estDestino) {
        estDestino.quantidade_atual += qtd;
      } else {
        appState.estoques.push({
          id: Date.now(),
          filial_id: destinoId,
          produto_id: produtoId,
          quantidade_atual: qtd,
          estoque_minimo: 15.0,
          estoque_maximo: 200.0
        });
      }

      document.getElementById('modal-transferencia-estoque').classList.add('hidden');
      this.showToast(`Transferência de ${qtd} un efetivada com sucesso!`, 'sucesso');
      this.renderEstoque();
      this.renderDashboard();
    });
  },

  abrirModalEntradaEstoque() {
    const selProd = document.getElementById('entrada-produto-id');
    selProd.innerHTML = '';
    appState.produtos.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.nome} (${p.sku}) — ${p.unidade}`;
      selProd.appendChild(opt);
    });

    const hoje = new Date().toISOString().split('T')[0];
    document.getElementById('entrada-data-fabricacao').value = hoje;
    
    const validade30d = new Date();
    validade30d.setDate(validade30d.getDate() + 45);
    document.getElementById('entrada-data-validade').value = validade30d.toISOString().split('T')[0];
    document.getElementById('entrada-numero-lote').value = `LOT-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;

    document.getElementById('modal-entrada-estoque').classList.remove('hidden');
  },

  abrirModalTransferencia() {
    const selProd = document.getElementById('transf-produto-id');
    selProd.innerHTML = '';
    appState.produtos.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.nome} (${p.sku})`;
      selProd.appendChild(opt);
    });

    document.getElementById('modal-transferencia-estoque').classList.remove('hidden');
  },

  renderEstoque() {
    const filialId = appState.selectedFilialId;
    const filtroStatus = document.getElementById('filtro-status-estoque')?.value || 'TODOS';

    const tbody = document.getElementById('tabela-estoque-posicao');
    if (!tbody) return;

    tbody.innerHTML = '';

    let filtrados = appState.estoques.filter(e => {
      const matchFilial = filialId === 'all' || e.filial_id === Number(filialId);
      return matchFilial;
    });

    let totalSkus = 0;
    let rupturasCount = 0;
    let valorTotal = 0;

    filtrados.forEach(est => {
      const prod = appState.produtos.find(p => p.id === est.produto_id);
      if (!prod) return;

      totalSkus++;
      valorTotal += (est.quantidade_atual * prod.preco_custo);

      let statusVisual = 'NORMAL';
      if (est.quantidade_atual <= est.estoque_minimo) {
        statusVisual = 'RUPTURA';
        rupturasCount++;
      } else {
        // Verifica se há lotes próximos do vencimento desta filial/produto
        const lotesProd = appState.lotes.filter(l => l.filial_id === est.filial_id && l.produto_id === est.produto_id);
        const temAlerta = lotesProd.some(l => utils.calcularDiasRestantes(l.data_validade) <= 7);
        if (temAlerta) statusVisual = 'ALERTA_VENCIMENTO';
      }

      if (filtroStatus !== 'TODOS' && filtroStatus !== statusVisual) return;

      const badgeStatus = statusVisual === 'RUPTURA' ?
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center gap-1 w-max">
           <span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span> RUPTURA
         </span>` :
        statusVisual === 'ALERTA_VENCIMENTO' ?
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center gap-1 w-max">
           <i class="fa-solid fa-clock text-[9px]"></i> VENCIMENTO
         </span>` :
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 w-max">NORMAL</span>`;

      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="p-3.5">${badgeStatus}</td>
        <td class="p-3.5 font-mono text-slate-300"><b>${prod.sku}</b><br><span class="text-[10px] text-slate-500">EAN ${prod.ean}</span></td>
        <td class="p-3.5">
          <div class="flex items-center space-x-2">
            <span class="text-xl">${prod.img}</span>
            <div>
              <p class="font-bold text-white text-xs">${prod.nome}</p>
              <span class="text-[10px] text-slate-400">${prod.perecivel ? '⚠️ Perecível (FEFO)' : 'Não-perecível'}</span>
            </div>
          </div>
        </td>
        <td class="p-3.5 text-slate-400 text-xs">${prod.departamento}</td>
        <td class="p-3.5 text-slate-300 font-medium text-xs">${utils.getFilialNome(est.filial_id).split('—')[0]}</td>
        <td class="p-3.5 text-right font-mono font-bold text-sm ${est.quantidade_atual <= est.estoque_minimo ? 'text-rose-400' : 'text-white'}">
          ${utils.formatNumber(est.quantidade_atual)} ${prod.unidade}
        </td>
        <td class="p-3.5 text-right font-mono text-[11px] text-slate-400">${est.estoque_minimo} / ${est.estoque_maximo}</td>
        <td class="p-3.5 text-right font-mono text-slate-400">${utils.formatMoney(prod.preco_custo)}</td>
        <td class="p-3.5 text-right font-mono font-semibold text-emerald-400">${utils.formatMoney(prod.preco_venda)}</td>
        <td class="p-3.5 text-center">
          <button onclick="app.abrirModalTransferencia()" class="text-xs text-cyan-400 hover:text-cyan-300 px-2 py-1 bg-cyan-950/40 rounded border border-cyan-800/40">Transferir</button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('estoque-total-skus').textContent = `${totalSkus} SKUs`;
    document.getElementById('estoque-ruptura-count').textContent = `${rupturasCount} ${rupturasCount === 1 ? 'item' : 'itens'}`;
    document.getElementById('estoque-valor-total').textContent = utils.formatMoney(valorTotal);

    this.renderLotesFEFO();
  },

  renderLotesFEFO() {
    const filialId = appState.selectedFilialId;
    const tbody = document.getElementById('tabela-lotes-fefo');
    if (!tbody) return;

    tbody.innerHTML = '';

    // Ordena ASC por validade (FEFO)
    const lotesOrdenados = [...appState.lotes]
      .filter(l => filialId === 'all' || l.filial_id === Number(filialId))
      .sort((a, b) => new Date(a.data_validade) - new Date(b.data_validade));

    let lotesCriticos = 0;

    lotesOrdenados.forEach((lote, idx) => {
      const prod = appState.produtos.find(p => p.id === lote.produto_id) || { nome: 'Produto', unidade: 'UN', img: '📦' };
      const dias = utils.calcularDiasRestantes(lote.data_validade);
      if (dias <= 7) lotesCriticos++;

      const badgePrioridade = idx === 0 ?
        `<span class="px-2 py-0.5 rounded bg-rose-600 text-white font-bold text-[10px] uppercase animate-pulse">#1 SAÍDA IMEDIATA</span>` :
        `<span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">#${idx + 1} FEFO</span>`;

      const badgeDias = dias <= 7 ?
        `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30">${dias} dias (CRÍTICO)</span>` :
        dias <= 30 ?
        `<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 font-bold border border-amber-500/30">${dias} dias</span>` :
        `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">${dias} dias (SEGURO)</span>`;

      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="p-3.5">${badgePrioridade}</td>
        <td class="p-3.5 font-mono text-amber-300 font-bold">${lote.numero_lote}</td>
        <td class="p-3.5">
          <div class="flex items-center space-x-2">
            <span>${prod.img}</span>
            <span class="font-semibold text-white text-xs">${prod.nome}</span>
          </div>
        </td>
        <td class="p-3.5 text-slate-300">${utils.getFilialNome(lote.filial_id).split('—')[0]}</td>
        <td class="p-3.5 font-mono text-slate-400">${new Date(lote.data_fabricacao).toLocaleDateString('pt-BR')}</td>
        <td class="p-3.5 font-mono font-bold text-white">${new Date(lote.data_validade).toLocaleDateString('pt-BR')}</td>
        <td class="p-3.5 text-center font-mono">${badgeDias}</td>
        <td class="p-3.5 text-right font-mono font-bold text-white">${utils.formatNumber(lote.quantidade_lote)} ${prod.unidade}</td>
        <td class="p-3.5 text-center">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">${lote.status_lote}</span>
        </td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('estoque-fefo-critico').textContent = `${lotesCriticos} ${lotesCriticos === 1 ? 'lote' : 'lotes'}`;
  },

  // ------------------------------------------
  // MÓDULO 4: CRM 360º, CLUBE DE FIDELIDADE & CAMPANHAS
  // ------------------------------------------
  configurarCRM() {
    // Clique nos cards RFM para filtrar
    document.querySelectorAll('#cards-segmentacao-rfm .rfm-card').forEach(card => {
      card.addEventListener('click', () => {
        const seg = card.getAttribute('data-rfm');
        this.filtrarClientesPorSegmento(seg);
      });
    });

    // Busca de cliente
    document.getElementById('busca-cliente-crm')?.addEventListener('input', (e) => {
      this.renderClientesCRM(e.target.value);
    });

    // Modais Novo Cliente e Nova Campanha
    document.getElementById('btn-modal-novo-cliente')?.addEventListener('click', () => {
      document.getElementById('modal-novo-cliente').classList.remove('hidden');
    });
    document.getElementById('btn-fechar-modal-cliente')?.addEventListener('click', () => {
      document.getElementById('modal-novo-cliente').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-cliente')?.addEventListener('click', () => {
      document.getElementById('modal-novo-cliente').classList.add('hidden');
    });

    document.getElementById('btn-modal-nova-campanha')?.addEventListener('click', () => {
      document.getElementById('modal-nova-campanha').classList.remove('hidden');
    });
    document.getElementById('btn-fechar-modal-campanha')?.addEventListener('click', () => {
      document.getElementById('modal-nova-campanha').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-campanha')?.addEventListener('click', () => {
      document.getElementById('modal-nova-campanha').classList.add('hidden');
    });

    // Formulário Novo Cliente (POST /api/crm/clientes)
    document.getElementById('form-novo-cliente')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const cpf = document.getElementById('cad-cliente-cpf').value.trim();
      const nome = document.getElementById('cad-cliente-nome').value.trim();
      const whatsapp = document.getElementById('cad-cliente-whatsapp').value.trim();
      const email = document.getElementById('cad-cliente-email').value.trim();
      const filialPref = Number(document.getElementById('cad-cliente-filial').value);

      const novo = {
        id: Date.now(),
        cpf: cpf,
        nome: nome,
        whatsapp: whatsapp,
        email: email,
        filial_preferida_id: filialPref,
        segmento_rfm: 'NOVO',
        pontos_fidelidade: 100, // Bônus de boas-vindas
        saldo_cashback: 10.00,  // Bônus de boas-vindas
        total_gasto_historico: 0.0,
        total_compras_count: 0,
        economia_acumulada_clube: 0.0,
        ultima_compra_em: 'Cadastrado Hoje'
      };

      await api.post('/crm/clientes', novo);

      appState.clientes.unshift(novo);
      document.getElementById('modal-novo-cliente').classList.add('hidden');
      document.getElementById('form-novo-cliente').reset();
      this.showToast(`Cliente ${nome} cadastrado com sucesso no Clube SuperSul! Bônus de R$ 10 creditado.`, 'sucesso');
      this.renderCRM();
    });

    // Formulário Nova Campanha (POST /api/crm/campanhas)
    document.getElementById('form-nova-campanha')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const titulo = document.getElementById('campanha-titulo').value.trim();
      const segmento = document.getElementById('campanha-segmento').value;
      const canal = document.getElementById('campanha-canal').value;
      const descPct = parseFloat(document.getElementById('campanha-desconto-pct').value) || 0;
      const cashPct = parseFloat(document.getElementById('campanha-cashback-pct').value) || 0;
      const msg = document.getElementById('campanha-template').value;

      const nova = {
        id: Date.now(),
        titulo: titulo,
        segmento_alvo: segmento,
        canal: canal,
        desconto_extra_pct: descPct,
        cashback_bonus_pct: cashPct,
        mensagem_template: msg,
        clientes_impactados: Math.floor(1200 + Math.random() * 3000),
        conversao_estimada_pct: (15 + Math.random() * 10).toFixed(1),
        ativa: true
      };

      await api.post('/crm/campanhas', nova);

      appState.campanhas.unshift(nova);
      document.getElementById('modal-nova-campanha').classList.add('hidden');
      document.getElementById('form-nova-campanha').reset();
      this.showToast(`Campanha "${titulo}" ativada e disparada para os clientes!`, 'sucesso');
      this.renderCRM();
    });
  },

  filtrarClientesPorSegmento(segmento) {
    const badge = document.getElementById('filtro-rfm-ativo-badge');
    badge.textContent = `Filtrando: ${segmento}`;
    this.renderClientesCRM('', segmento);
  },

  renderCRM() {
    this.renderClientesCRM();
    this.renderCampanhasCRM();
  },

  renderClientesCRM(busca = '', segmentoFiltro = '') {
    const tbody = document.getElementById('tabela-clientes-crm');
    if (!tbody) return;

    tbody.innerHTML = '';
    let filtrados = appState.clientes;

    if (segmentoFiltro) {
      filtrados = filtrados.filter(c => c.segmento_rfm === segmentoFiltro);
    }

    if (busca) {
      const q = busca.toLowerCase();
      filtrados = filtrados.filter(c => c.nome.toLowerCase().includes(q) || c.cpf.includes(q) || c.whatsapp.includes(q));
    }

    filtrados.forEach(c => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';

      const segCor = c.segmento_rfm === 'DIAMANTE' ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' :
                     c.segmento_rfm === 'OURO' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                     c.segmento_rfm === 'PRATA' ? 'bg-slate-700/60 text-slate-300 border-slate-600' :
                     c.segmento_rfm === 'EM_RISCO' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' :
                     'bg-emerald-500/20 text-emerald-300 border-emerald-500/30';

      tr.innerHTML = `
        <td class="p-3.5">
          <div class="flex items-center space-x-2.5">
            <div class="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-300">
              ${c.nome.slice(0, 2).toUpperCase()}
            </div>
            <div>
              <p class="font-bold text-white text-xs">${c.nome}</p>
              <span class="text-[10px] text-slate-400">${c.email || 'Sem e-mail'}</span>
            </div>
          </div>
        </td>
        <td class="p-3.5 font-mono text-slate-300">${c.cpf}</td>
        <td class="p-3.5 font-mono text-slate-400">
          <i class="fa-brands fa-whatsapp text-emerald-400 mr-1"></i> ${c.whatsapp}
        </td>
        <td class="p-3.5">
          <span class="text-[10px] font-bold px-2 py-0.5 rounded-full border ${segCor}">${c.segmento_rfm}</span>
        </td>
        <td class="p-3.5 text-right font-mono font-bold text-amber-400">${utils.formatMoney(c.saldo_cashback)}</td>
        <td class="p-3.5 text-right font-mono font-semibold text-purple-300">${utils.formatNumber(c.pontos_fidelidade)} pts</td>
        <td class="p-3.5 text-right font-mono text-emerald-400 font-bold">${utils.formatMoney(c.economia_acumulada_clube)}</td>
        <td class="p-3.5 text-right font-mono font-semibold text-white">${utils.formatMoney(c.total_gasto_historico)}</td>
        <td class="p-3.5 text-center text-slate-400 text-[11px]">${c.ultima_compra_em}</td>
      `;
      tbody.appendChild(tr);
    });
  },

  renderCampanhasCRM() {
    const grid = document.getElementById('grid-campanhas-crm');
    if (!grid) return;

    grid.innerHTML = '';
    appState.campanhas.forEach(camp => {
      const card = document.createElement('div');
      card.className = 'bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between space-y-3';
      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
              ALVO: ${camp.segmento_alvo}
            </span>
            <span class="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span> DISPARADA
            </span>
          </div>
          <h5 class="text-sm font-bold text-white mb-1">${camp.titulo}</h5>
          <p class="text-xs text-slate-400 line-clamp-2 italic">"${camp.mensagem_template}"</p>
        </div>

        <div class="pt-3 border-t border-slate-900 space-y-1.5 text-xs">
          <div class="flex justify-between text-slate-400">
            <span>Canal de Envio:</span>
            <span class="text-white font-mono font-medium">${camp.canal}</span>
          </div>
          <div class="flex justify-between text-slate-400">
            <span>Benefício:</span>
            <span class="text-amber-400 font-bold font-mono">+${camp.desconto_extra_pct}% OFF • +${camp.cashback_bonus_pct}% Cashback</span>
          </div>
          <div class="flex justify-between text-slate-400">
            <span>Impacto & Conversão:</span>
            <span class="text-emerald-400 font-mono font-bold">${utils.formatNumber(camp.clientes_impactados)} clientes (${camp.conversao_estimada_pct}%)</span>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });
  },

  // ------------------------------------------
  // MÓDULO 5: COMPRAS & FORNECEDORES
  // ------------------------------------------
  configurarCompras() {
    document.getElementById('btn-modal-novo-pedido-compra')?.addEventListener('click', () => {
      this.abrirModalNovoPedido();
    });
    document.getElementById('btn-fechar-modal-compra')?.addEventListener('click', () => {
      document.getElementById('modal-novo-pedido-compra').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-compra')?.addEventListener('click', () => {
      document.getElementById('modal-novo-pedido-compra').classList.add('hidden');
    });

    // Atualiza total estimado dinamicamente
    const calcTotal = () => {
      const q = parseFloat(document.getElementById('compra-quantidade').value) || 0;
      const c = parseFloat(document.getElementById('compra-custo-unitario').value) || 0;
      document.getElementById('compra-total-estimado').textContent = utils.formatMoney(q * c);
    };
    document.getElementById('compra-quantidade')?.addEventListener('input', calcTotal);
    document.getElementById('compra-custo-unitario')?.addEventListener('input', calcTotal);

    // Formulário Novo Pedido de Compra (POST /api/compras)
    document.getElementById('form-novo-pedido-compra')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const filialId = Number(document.getElementById('compra-filial-id').value);
      const fornecedorId = Number(document.getElementById('compra-fornecedor-id').value);
      const produtoId = Number(document.getElementById('compra-produto-id').value);
      const qtd = Number(document.getElementById('compra-quantidade').value);
      const custo = Number(document.getElementById('compra-custo-unitario').value);
      const total = qtd * custo;

      const numPedido = `PC-2026-0${Math.floor(100 + Math.random() * 900)}`;

      const novo = {
        id: Date.now(),
        numero_pedido: numPedido,
        filial_id: filialId,
        fornecedor_id: fornecedorId,
        produto_id: produtoId,
        quantidade: qtd,
        custo_unitario: custo,
        valor_total: total,
        status: 'APROVADO',
        criado_em: 'Agora mesmo'
      };

      await api.post('/compras', novo);

      appState.compras.unshift(novo);
      document.getElementById('modal-novo-pedido-compra').classList.add('hidden');
      this.showToast(`Ordem de Compra ${numPedido} emitida com sucesso!`, 'sucesso');
      this.renderCompras();
    });
  },

  abrirModalNovoPedido() {
    const selForn = document.getElementById('compra-fornecedor-id');
    selForn.innerHTML = '';
    appState.fornecedores.forEach(f => {
      const opt = document.createElement('option');
      opt.value = f.id;
      opt.textContent = `${f.nome_fantasia} (${f.categoria_principal})`;
      selForn.appendChild(opt);
    });

    const selProd = document.getElementById('compra-produto-id');
    selProd.innerHTML = '';
    appState.produtos.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.nome} (Custo ref: ${utils.formatMoney(p.preco_custo)})`;
      selProd.appendChild(opt);
    });

    // Define custo inicial do primeiro produto
    document.getElementById('compra-custo-unitario').value = appState.produtos[0].preco_custo;
    document.getElementById('compra-quantidade').value = 100;
    document.getElementById('compra-total-estimado').textContent = utils.formatMoney(100 * appState.produtos[0].preco_custo);

    document.getElementById('modal-novo-pedido-compra').classList.remove('hidden');
  },

  async receberPedidoCompra(pedidoId) {
    const ped = appState.compras.find(p => p.id === pedidoId);
    if (!ped) return;

    // Chamada POST /api/compras/{id}/receber
    await api.post(`/compras/${pedidoId}/receber`, {});

    ped.status = 'RECEBIDO';

    // Dá entrada automática no estoque da filial com novo lote
    let est = appState.estoques.find(e => e.filial_id === ped.filial_id && e.produto_id === ped.produto_id);
    if (est) {
      est.quantidade_atual += ped.quantidade;
    } else {
      appState.estoques.push({
        id: Date.now(),
        filial_id: ped.filial_id,
        produto_id: ped.produto_id,
        quantidade_atual: ped.quantidade,
        estoque_minimo: 20.0,
        estoque_maximo: 500.0
      });
    }

    // Cria lote FEFO automático
    const hoje = new Date();
    const val = new Date();
    val.setDate(val.getDate() + 60);

    appState.lotes.push({
      id: Date.now(),
      filial_id: ped.filial_id,
      produto_id: ped.produto_id,
      numero_lote: `LOT-REC-${ped.id}`,
      data_fabricacao: hoje.toISOString().split('T')[0],
      data_validade: val.toISOString().split('T')[0],
      quantidade_lote: ped.quantidade,
      status_lote: 'ATIVO'
    });

    this.showToast(`Mercadoria do Pedido ${ped.numero_pedido} recebida e estocada com sucesso!`, 'sucesso');
    this.renderCompras();
    this.renderEstoque();
    this.renderDashboard();
  },

  renderCompras() {
    const tbody = document.getElementById('tabela-pedidos-compra');
    if (!tbody) return;

    tbody.innerHTML = '';
    let pendentesCount = 0;
    let valorTransito = 0;

    appState.compras.forEach(ped => {
      if (ped.status === 'APROVADO' || ped.status === 'PENDENTE') {
        pendentesCount++;
        valorTransito += ped.valor_total;
      }

      const prod = appState.produtos.find(p => p.id === ped.produto_id) || { nome: 'Produto', unidade: 'UN' };
      const forn = appState.fornecedores.find(f => f.id === ped.fornecedor_id) || { nome_fantasia: 'Fornecedor' };

      const badgeStatus = ped.status === 'RECEBIDO' ?
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">RECEBIDO</span>` :
        ped.status === 'APROVADO' ?
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">EM TRÂNSITO</span>` :
        `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">PENDENTE</span>`;

      const acaoBotao = ped.status !== 'RECEBIDO' ?
        `<button onclick="app.receberPedidoCompra(${ped.id})" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-[11px] rounded-lg transition active:scale-95 shadow">
           <i class="fa-solid fa-box-open mr-1"></i> Receber no Estoque
         </button>` :
        `<span class="text-[10px] text-slate-500 font-mono">Concluído</span>`;

      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition';
      tr.innerHTML = `
        <td class="p-3.5 font-mono text-blue-400 font-bold">${ped.numero_pedido}</td>
        <td class="p-3.5 text-slate-300 font-medium">${utils.getFilialNome(ped.filial_id).split('—')[0]}</td>
        <td class="p-3.5 text-white font-semibold">${forn.nome_fantasia}</td>
        <td class="p-3.5 text-slate-200">${prod.nome}</td>
        <td class="p-3.5 text-right font-mono font-bold text-white">${utils.formatNumber(ped.quantidade)} ${prod.unidade}</td>
        <td class="p-3.5 text-right font-mono text-slate-400">${utils.formatMoney(ped.custo_unitario)}</td>
        <td class="p-3.5 text-right font-mono font-black text-emerald-400">${utils.formatMoney(ped.valor_total)}</td>
        <td class="p-3.5 text-center">${badgeStatus}</td>
        <td class="p-3.5 text-center">${acaoBotao}</td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('compras-pendentes-count').textContent = `${pendentesCount} ${pendentesCount === 1 ? 'Pedido' : 'Pedidos'}`;
    document.getElementById('compras-valor-transito').textContent = utils.formatMoney(valorTransito);
    document.getElementById('badge-pedidos-pendentes').textContent = `${pendentesCount} Ordens`;

    // Renderiza Fornecedores
    const gridForn = document.getElementById('grid-fornecedores');
    if (gridForn) {
      gridForn.innerHTML = '';
      appState.fornecedores.forEach(f => {
        const c = document.createElement('div');
        c.className = 'bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2';
        c.innerHTML = `
          <div class="flex items-center justify-between">
            <h5 class="text-sm font-bold text-white">${f.nome_fantasia}</h5>
            <span class="text-xs text-amber-400 font-bold"><i class="fa-solid fa-star text-[10px]"></i> ${f.avaliacao}</span>
          </div>
          <p class="text-xs text-slate-400">${f.razao_social}</p>
          <div class="pt-2 border-t border-slate-900 flex justify-between text-[11px] text-slate-400 font-mono">
            <span>Categoria: <b class="text-slate-200">${f.categoria_principal}</b></span>
            <span>Prazo: <b class="text-emerald-400">${f.prazo_entrega_dias} dias</b></span>
          </div>
        `;
        gridForn.appendChild(c);
      });
    }
  },

  // ------------------------------------------
  // MÓDULO 6: FINANCEIRO & DRE GERENCIAL
  // ------------------------------------------
  configurarFinanceiro() {
    document.getElementById('btn-modal-novo-lancamento')?.addEventListener('click', () => {
      document.getElementById('modal-novo-lancamento').classList.remove('hidden');
    });
    document.getElementById('btn-fechar-modal-lancamento')?.addEventListener('click', () => {
      document.getElementById('modal-novo-lancamento').classList.add('hidden');
    });
    document.getElementById('btn-cancelar-modal-lanc')?.addEventListener('click', () => {
      document.getElementById('modal-novo-lancamento').classList.add('hidden');
    });

    // Formulário Novo Lançamento (POST /api/financeiro/lancamentos)
    document.getElementById('form-novo-lancamento')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const filialId = Number(document.getElementById('lanc-filial-id').value);
      const tipo = document.getElementById('lanc-tipo').value;
      const cat = document.getElementById('lanc-categoria').value;
      const desc = document.getElementById('lanc-descricao').value.trim();
      const val = parseFloat(document.getElementById('lanc-valor').value) || 0;
      const dataComp = document.getElementById('lanc-data').value;

      const novo = {
        id: Date.now(),
        filial_id: filialId,
        tipo: tipo,
        categoria_dre: cat,
        descricao: desc,
        valor: val,
        status: 'PAGO',
        data_competencia: dataComp
      };

      await api.post('/financeiro/lancamentos', novo);

      appState.lancamentos.unshift(novo);
      document.getElementById('modal-novo-lancamento').classList.add('hidden');
      document.getElementById('form-novo-lancamento').reset();
      this.showToast('Lançamento financeiro contabilizado com sucesso!', 'sucesso');
      this.renderFinanceiro();
      this.renderDashboard();
    });
  },

  renderFinanceiro() {
    const filialId = appState.selectedFilialId;
    document.getElementById('dre-filial-label').textContent = utils.getFilialNome(filialId);

    // Calcula DRE
    let filiaisAlvo = appState.filiais;
    if (filialId !== 'all') {
      filiaisAlvo = appState.filiais.filter(f => f.id === Number(filialId));
    }

    const receitaBruta = filiaisAlvo.reduce((acc, f) => acc + f.faturamento_atual, 0);
    const impostos = receitaBruta * 0.12; // 12% impostos
    const receitaLiquida = receitaBruta - impostos;
    const cmv = receitaBruta * 0.598; // ~60% CMV
    const lucroBruto = receitaLiquida - cmv;
    const margemBrutaPct = receitaLiquida > 0 ? (lucroBruto / receitaLiquida) * 100 : 0;

    const despesasOp = receitaBruta * 0.093; // 9.3% Opex
    const ebitda = lucroBruto - despesasOp;
    const margemEbitdaPct = receitaLiquida > 0 ? (ebitda / receitaLiquida) * 100 : 0;

    const containerDRE = document.getElementById('container-dre-linhas');
    if (!containerDRE) return;

    containerDRE.innerHTML = `
      <div class="flex justify-between py-2 px-3 rounded-lg bg-slate-950 font-bold text-white text-sm">
        <span>(+) RECEITA BRUTA DE VENDAS</span>
        <span class="font-mono text-emerald-400">${utils.formatMoney(receitaBruta)}</span>
      </div>

      <div class="flex justify-between py-1.5 px-3 text-slate-400 text-xs pl-6">
        <span>(-) Deduções da Receita & Tributos (ICMS, PIS/COFINS ~12.0%)</span>
        <span class="font-mono text-rose-400">- ${utils.formatMoney(impostos)}</span>
      </div>

      <div class="flex justify-between py-2 px-3 rounded-lg bg-slate-950/80 font-bold text-slate-200 text-xs">
        <span>(=) RECEITA OPERACIONAL LÍQUIDA (ROL)</span>
        <span class="font-mono text-white">${utils.formatMoney(receitaLiquida)} (100.0%)</span>
      </div>

      <div class="flex justify-between py-1.5 px-3 text-slate-400 text-xs pl-6">
        <span>(-) Custo das Mercadorias Vendidas (CMV)</span>
        <span class="font-mono text-rose-400">- ${utils.formatMoney(cmv)}</span>
      </div>

      <div class="flex justify-between py-2 px-3 rounded-lg bg-emerald-950/20 border border-emerald-900/30 font-bold text-emerald-300 text-xs">
        <span>(=) LUCRO BRUTO COMERCIAL</span>
        <span class="font-mono text-emerald-400">${utils.formatMoney(lucroBruto)} (Margem ${utils.formatPercent(margemBrutaPct)})</span>
      </div>

      <div class="flex justify-between py-1.5 px-3 text-slate-400 text-xs pl-6">
        <span>(-) Despesas Operacionais (Folha, Energia Câmaras Frias, Logística CD)</span>
        <span class="font-mono text-rose-400">- ${utils.formatMoney(despesasOp)}</span>
      </div>

      <div class="flex justify-between py-2.5 px-3 rounded-xl bg-gradient-to-r from-emerald-900/40 to-slate-900 border border-emerald-500/40 font-black text-sm text-white">
        <span class="flex items-center gap-2">
          <i class="fa-solid fa-chart-line text-emerald-400"></i> (=) EBITDA GERENCIAL (LUCRO OPERACIONAL)
        </span>
        <span class="font-mono text-emerald-400 text-base">${utils.formatMoney(ebitda)} (Margem ${utils.formatPercent(margemEbitdaPct)})</span>
      </div>
    `;

    // Renderiza Extrato
    const tbodyLanc = document.getElementById('tabela-lancamentos-financeiros');
    if (tbodyLanc) {
      tbodyLanc.innerHTML = '';
      appState.lancamentos.forEach(l => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/40 transition';

        const corValor = l.tipo === 'RECEITA' ? 'text-emerald-400' : 'text-rose-400';
        const sinal = l.tipo === 'RECEITA' ? '+' : '-';

        tr.innerHTML = `
          <td class="p-3.5 font-mono text-slate-400">${new Date(l.data_competencia).toLocaleDateString('pt-BR')}</td>
          <td class="p-3.5 text-slate-300 font-medium">${utils.getFilialNome(l.filial_id).split('—')[0]}</td>
          <td class="p-3.5">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded ${l.tipo === 'RECEITA' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}">${l.tipo}</span>
          </td>
          <td class="p-3.5 text-slate-400 font-mono text-[11px]">${l.categoria_dre}</td>
          <td class="p-3.5 text-white font-medium">${l.descricao}</td>
          <td class="p-3.5 text-right font-mono font-bold ${corValor}">${sinal} ${utils.formatMoney(l.valor)}</td>
          <td class="p-3.5 text-center">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">${l.status}</span>
          </td>
        `;
        tbodyLanc.appendChild(tr);
      });
    }
  },

  // ------------------------------------------
  // MÓDULO 7: CENTRAL DE AGENTES IA & SERVIDOR
  // ------------------------------------------
  configurarAgentes() {
    document.getElementById('btn-executar-ciclo-ia')?.addEventListener('click', async () => {
      this.showToast('Disparando ciclo autônomo dos 6 Agentes CrewAI...', 'aviso');
      
      await api.post('/agentes/executar-ciclo', {});

      const novoLog = {
        hora: new Date().toLocaleTimeString('pt-BR'),
        agente: 'Agente Precificador & Agente Ruptura FEFO',
        tier: 'Tier 1 & Tier 2',
        filial: 'Consolidado da Rede',
        texto: 'Ciclo manual executado com sucesso: gôndolas auditadas, 4 novos alertas de estoque despachados para compras e margens recalculadas.'
      };

      appState.logsAgentes.unshift(novoLog);
      this.renderAgentes();
      this.showToast('Ciclo de otimização dos agentes concluído com sucesso!', 'sucesso');
    });

    document.getElementById('btn-limpar-logs')?.addEventListener('click', () => {
      appState.logsAgentes = [];
      this.renderAgentes();
    });
  },

  renderAgentes() {
    const grid = document.getElementById('grid-agentes-crew');
    if (!grid) return;

    grid.innerHTML = '';
    appState.agentes.forEach(ag => {
      const card = document.createElement('div');
      card.className = 'bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col justify-between space-y-3';
      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center space-x-2">
              <span class="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-slate-300 border border-slate-800">
                <i class="fa-solid ${ag.icone}"></i>
              </span>
              <span class="text-xs font-bold text-white">${ag.nome}</span>
            </div>
            <span class="flex h-2 w-2 relative">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">${ag.missao}</p>
        </div>

        <div class="pt-3 border-t border-slate-900 flex items-center justify-between text-[11px] font-mono">
          <span class="text-slate-500">Tier ${ag.tier}</span>
          <span class="text-amber-400 font-bold px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">${ag.modelo}</span>
          <span class="text-emerald-400">${ag.status}</span>
        </div>
      `;
      grid.appendChild(card);
    });

    // Renderiza Logs
    const consoleLogs = document.getElementById('console-logs-agentes');
    if (consoleLogs) {
      consoleLogs.innerHTML = '';
      if (appState.logsAgentes.length === 0) {
        consoleLogs.innerHTML = '<p class="text-slate-600 italic">Nenhum log no momento.</p>';
      } else {
        appState.logsAgentes.forEach(l => {
          const p = document.createElement('div');
          p.className = 'flex items-start space-x-2 border-b border-slate-900/60 pb-1.5';
          p.innerHTML = `
            <span class="text-slate-500 shrink-0">[${l.hora}]</span>
            <span class="text-cyan-400 font-bold shrink-0">&lt;${l.agente}&gt;</span>
            <span class="text-slate-300">${l.texto}</span>
          `;
          consoleLogs.appendChild(p);
        });
      }
    }
  }
};

// ==========================================
// 6. INICIALIZAÇÃO NO CARREGAMENTO DA PÁGINA
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
