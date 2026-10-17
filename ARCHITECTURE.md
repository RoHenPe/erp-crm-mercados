# 🛒 Arquitetura Master — ERP & CRM Online para Grupo de Mercados

## 1. Visão Geral e Topologia Híbrida (Local + Servidor de Rede)
- **Workspace Local (Mídia Downloads):** `/media/rodrigo/Downloads/ai-agents/workspace/erp-mercados` (Atalho: `/media/rodrigo/Downloads/erp-mercados`)
- **Servidor de Rede Dedicado (`rohenper`):** `rodrigo@192.168.15.109:/home/rodrigo/erp-mercados` (VPN: `100.119.122.10`)
  - **Hardware:** 16 GB RAM, 308 GB livres em SSD
  - **Banco de Dados Oficial:** PostgreSQL (`srv_postgres_db` na porta `5432`)
  - **Business Intelligence Integrado:** Metabase (`http://192.168.15.109:3003`)

---

## 2. Módulos do Sistema (ERP + CRM Supermercadista)

### A. Núcleo Multi-Loja (Holding / Grupo de Mercados)
- `grupos_economicos` e `filiais` (CNPJ, Inscrição Estadual, endereço, depósito central CD vs loja física)
- `usuarios` e `perfis_acesso` (Diretoria, Gerente de Loja, Comprador, Financeiro, Operador de Caixa, Analista de Marketing/CRM)

### B. ERP — Catálogo, Estoque, Lotes e Compras
- `departamentos`, `categorias`, `marcas` e `fornecedores`
- `produtos` (Código interno, EAN/GTIN-13, NCM, CEST, unidade `UN`/`KG`, preço de custo, margem, preço de venda, preço clube CRM)
- `estoque_filial` e `lotes_validade` (Controle FEFO — *First Expired, First Out*, alerta de produtos próximos ao vencimento e ponto de reposição)
- `pedidos_compra` e `movimentacoes_estoque` (Entrada por XML/NF-e, transferência entre filiais/CD, quebra/perda, baixa de venda PDV)

### C. ERP — Frente de Caixa (PDV Online) & Financeiro
- `caixas_sessoes` (Abertura, sangria, suprimento, fechamento cego)
- `vendas` e `itens_venda` (Identificação do cliente por CPF/telefone para o CRM, múltiplos meios de pagamento: PIX, Cartão, Dinheiro, Saldo Cashback)
- `contas_pagar`, `contas_receber` e `fluxo_caixa` (DRE por filial e consolidado do Grupo de Mercados)

### D. CRM — Clube de Fidelidade, Cashback & Inteligência de Varejo
- `clientes_crm` (Cadastro 360º, CPF, WhatsApp, loja preferida, ticket médio, frequência, classificação RFM: *Campeão*, *Leal*, *Em Risco*, *Inativo*)
- `carteira_fidelidade` e `transacoes_cashback` (Acúmulo automático de pontos/cashback por compra e resgate direto no PDV)
- `campanhas_promocionais` e `ofertas_clube` (Descontos exclusivos "Preço Clube" por categoria/produto e disparos segmentados)

---

## 3. Estrutura de Pastas do Projeto
```text
erp-mercados/
├── ARCHITECTURE.md          # Documento mestre de arquitetura
├── backend/                 # API FastAPI / Python + SQLAlchemy / PostgreSQL
│   ├── app/
│   │   ├── core/            # Configurações, conexão DB, autenticação JWT
│   │   ├── models/          # Tabelas ERP (Lojas, Estoque, PDV, Financeiro) e CRM
│   │   ├── schemas/         # Validação Pydantic
│   │   ├── routers/         # Endpoints REST (/lojas, /estoque, /pdv, /financeiro, /crm)
│   │   └── services/        # Regras de negócio (FEFO, Curva ABC, Motor Cashback/RFM)
│   └── tests/               # Suíte automatizada de testes (pytest)
├── frontend/                # Aplicação Web Online (Dashboard Grupo, PDV, Estoque, CRM)
├── database/                # Migrations SQL, seeds de produtos/mercados e views Metabase
└── deploy/                  # docker-compose.yml e scripts de deploy para 192.168.15.109
```
