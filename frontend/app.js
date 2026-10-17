/**
 * HelpDmais — Gestão Empresarial (ERP, CRM & PDV)
 * Aplicação Web de Produção (Multi-Empresa com Isolamento por Sessão e Controle de Cargos)
 */

const STORAGE_TOKEN_KEY = "helpdmais_session_token_v3";

const CATALOGO_APLICATIVOS = [
  {
    id: "dashboard",
    nome: "Painel Geral",
    descricao: "Indicadores de vendas, metas, estoque e resultados",
    icone: "fa-chart-pie",
    corBg: "from-indigo-600 to-indigo-800",
  },
  {
    id: "pdv",
    nome: "Ponto de Venda (PDV)",
    descricao: "Frente de caixa, código de barras e emissão de cupom",
    icone: "fa-cash-register",
    corBg: "from-teal-600 to-emerald-700",
  },
  {
    id: "estoque",
    nome: "Produtos & Estoque",
    descricao: "Catálogo de itens, controle de lotes, validade e transferências",
    icone: "fa-boxes-stacked",
    corBg: "from-amber-500 to-orange-600",
  },
  {
    id: "compras",
    nome: "Compras & Fornecedores",
    descricao: "Fornecedores, pedidos de compra e entrada de mercadorias",
    icone: "fa-truck-ramp-box",
    corBg: "from-sky-600 to-blue-700",
  },
  {
    id: "crm",
    nome: "Clientes & Fidelidade",
    descricao: "Cadastro de clientes, níveis de fidelidade, cashback e campanhas",
    icone: "fa-users",
    corBg: "from-purple-600 to-fuchsia-700",
  },
  {
    id: "financeiro",
    nome: "Financeiro & DRE",
    descricao: "Contas a pagar/receber, despesas e demonstrativo de resultados",
    icone: "fa-scale-balanced",
    corBg: "from-rose-600 to-pink-700",
  },
  {
    id: "configuracoes",
    nome: "Empresa & Equipe",
    descricao: "Unidades/lojas e cadastro de funcionários por cargo",
    icone: "fa-sliders",
    corBg: "from-slate-700 to-slate-900",
  },
];

const ESTADO = {
  token: localStorage.getItem(STORAGE_TOKEN_KEY) || null,
  usuario: null,
  tenant: null,
  perfil: null,
  filiais: [],
  filialAtivaId: "all",
  appAtual: "apps",
  perfisDisponiveis: [],
  produtos: [],
  estoque: [],
  fornecedores: [],
  compras: [],
  clientes: [],
  campanhas: [],
  sessaoCaixaPDV: null,
  carrinhoPDV: [],
  clientePDV: null,
};

// ============================================================================
// Utilitários de Formatação e Notificações
// ============================================================================
function moeda(valor) {
  const num = Number(valor || 0);
  return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function numero(valor, casas = 0) {
  const num = Number(valor || 0);
  return num.toLocaleString("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  });
}

function dataHoraBR(isoStr) {
  if (!isoStr) return "-";
  const d = new Date(isoStr.endsWith("Z") ? isoStr : isoStr + "Z");
  if (isNaN(d.getTime())) return isoStr;
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function dataBR(isoDate) {
  if (!isoDate) return "-";
  const partes = String(isoDate).split("T")[0].split("-");
  if (partes.length === 3) return `${partes[2]}/${partes[1]}/${partes[0]}`;
  return isoDate;
}

function notificar(mensagem, tipo = "sucesso") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const cores = {
    sucesso: "bg-emerald-600 text-white border-emerald-700",
    erro: "bg-rose-600 text-white border-rose-700",
    aviso: "bg-amber-500 text-white border-amber-600",
    info: "bg-slate-800 text-white border-slate-900",
  };
  const icones = {
    sucesso: "fa-circle-check",
    erro: "fa-circle-exclamation",
    aviso: "fa-triangle-exclamation",
    info: "fa-circle-info",
  };

  const el = document.createElement("div");
  el.className = `pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold transition-all duration-300 ${cores[tipo] || cores.info}`;
  el.innerHTML = `
    <i class="fa-solid ${icones[tipo] || icones.info} text-base"></i>
    <span class="flex-1">${mensagem}</span>
  `;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 300);
  }, 4000);
}

// ============================================================================
// Cliente HTTP Autenticado
// ============================================================================
async function apiFetch(url, options = {}) {
  const headers = Object.assign(
    { "Content-Type": "application/json" },
    options.headers || {}
  );
  if (ESTADO.token) {
    headers["Authorization"] = `Bearer ${ESTADO.token}`;
  }
  const resp = await fetch(url, { ...options, headers });
  let dados = null;
  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    dados = await resp.json();
  } else {
    const txt = await resp.text();
    dados = { detail: txt };
  }

  if (!resp.ok) {
    if (resp.status === 401 && ESTADO.token && !url.includes("/api/auth/login")) {
      encerrarSessao(false);
    }
    const msg =
      (dados && (dados.detail || dados.mensagem)) ||
      `Erro na requisição (${resp.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return dados;
}

// ============================================================================
// Controle de Autenticação e Cadastro de Empresa
// ============================================================================
function alternarAbaAuth(aba) {
  const formLogin = document.getElementById("form-login");
  const formReg = document.getElementById("form-registro-empresa");
  const btnLogin = document.getElementById("tab-btn-login");
  const btnReg = document.getElementById("tab-btn-registro");

  if (aba === "registro") {
    formLogin.classList.add("hidden");
    formReg.classList.remove("hidden");
    btnReg.className =
      "flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition bg-white text-slate-900 shadow-sm";
    btnLogin.className =
      "flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition text-slate-600 hover:text-slate-900";
  } else {
    formReg.classList.add("hidden");
    formLogin.classList.remove("hidden");
    btnLogin.className =
      "flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition bg-white text-slate-900 shadow-sm";
    btnReg.className =
      "flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition text-slate-600 hover:text-slate-900";
  }
}

function aplicarSessaoAutenticada(respostaLogin) {
  ESTADO.token = respostaLogin.token_sessao;
  localStorage.setItem(STORAGE_TOKEN_KEY, ESTADO.token);
  ESTADO.usuario = respostaLogin.usuario;
  ESTADO.tenant = respostaLogin.tenant;
  ESTADO.perfil = respostaLogin.perfil_detalhes;
  ESTADO.filiais = respostaLogin.filiais || [];

  if (ESTADO.usuario.filial_id) {
    ESTADO.filialAtivaId = String(ESTADO.usuario.filial_id);
  } else {
    ESTADO.filialAtivaId = "all";
  }

  document.getElementById("auth-screen").classList.add("hidden");
  document.getElementById("app-shell").classList.remove("hidden");

  atualizarBarraSuperior();
  renderizarGradeAplicativos();
  abrirGradeAplicativos();
}

function encerrarSessao(exibirMensagem = true) {
  ESTADO.token = null;
  ESTADO.usuario = null;
  ESTADO.tenant = null;
  ESTADO.perfil = null;
  ESTADO.filiais = [];
  ESTADO.produtos = [];
  ESTADO.estoque = [];
  ESTADO.fornecedores = [];
  ESTADO.compras = [];
  ESTADO.clientes = [];
  ESTADO.campanhas = [];
  ESTADO.carrinhoPDV = [];
  ESTADO.clientePDV = null;
  localStorage.removeItem(STORAGE_TOKEN_KEY);

  document.getElementById("app-shell").classList.add("hidden");
  document.getElementById("auth-screen").classList.remove("hidden");
  if (exibirMensagem) {
    notificar("Sessão encerrada com segurança.", "info");
  }
}

function atualizarBarraSuperior() {
  if (!ESTADO.usuario || !ESTADO.tenant) return;

  document.getElementById("top-empresa-nome").textContent =
    ESTADO.tenant.nome_fantasia;
  document.getElementById("top-user-nome").textContent = ESTADO.usuario.nome;
  document.getElementById("top-user-cargo").textContent =
    (ESTADO.perfil && ESTADO.perfil.nome) || ESTADO.usuario.cargo;

  const iniciais = ESTADO.usuario.nome
    .split(" ")
    .map((n) => n[0])
    .join("")
    .substring(0, 2)
    .toUpperCase();
  document.getElementById("top-user-avatar").textContent = iniciais || "U";

  // Preenche o seletor de unidade ativa apenas com as unidades da empresa logada
  const selectFilial = document.getElementById("select-filial-ativa");
  const opcoes = [`<option value="all" class="text-slate-900">Todas as Unidades (${ESTADO.filiais.length})</option>`];
  ESTADO.filiais.forEach((f) => {
    opcoes.push(
      `<option value="${f.id}" class="text-slate-900">${f.codigo} — ${f.nome}</option>`
    );
  });
  selectFilial.innerHTML = opcoes.join("");
  selectFilial.value = ESTADO.filialAtivaId;

  // Atalhos rápidos na barra superior
  const navTop = document.getElementById("top-module-shortcuts");
  const modulosPermitidos = ESTADO.usuario.modulos_permitidos || [];
  navTop.innerHTML = CATALOGO_APLICATIVOS.filter((app) =>
    modulosPermitidos.includes(app.id)
  )
    .map(
      (app) => `
      <button type="button" onclick="abrirAplicativo('${app.id}')" class="px-2.5 py-1.5 rounded-lg text-xs font-medium text-purple-100 hover:bg-white/15 transition flex items-center gap-1.5">
        <i class="fa-solid ${app.icone} text-[11px]"></i>
        <span>${app.nome}</span>
      </button>
    `
    )
    .join("");
}

function aoTrocarFilialAtiva() {
  const val = document.getElementById("select-filial-ativa").value;
  ESTADO.filialAtivaId = val;
  if (ESTADO.appAtual !== "apps") {
    abrirAplicativo(ESTADO.appAtual);
  }
}

function obterQueryFilial() {
  if (ESTADO.filialAtivaId && ESTADO.filialAtivaId !== "all") {
    return `?filial_id=${encodeURIComponent(ESTADO.filialAtivaId)}`;
  }
  return "";
}

// ============================================================================
// Navegação entre Grade de Aplicativos e Módulos
// ============================================================================
function renderizarGradeAplicativos() {
  if (!ESTADO.usuario || !ESTADO.tenant) return;

  document.getElementById("home-greeting-role").textContent =
    `${ESTADO.tenant.nome_fantasia} • ${(ESTADO.perfil && ESTADO.perfil.nome) || ESTADO.usuario.cargo}`;
  document.getElementById("home-greeting-title").textContent =
    `Olá, ${ESTADO.usuario.nome}`;
  document.getElementById("home-greeting-subtitle").textContent =
    (ESTADO.perfil && ESTADO.perfil.descricao) ||
    "Selecione um aplicativo abaixo para iniciar suas atividades.";

  const modulosPermitidos = ESTADO.usuario.modulos_permitidos || [];
  const appsVisiveis = CATALOGO_APLICATIVOS.filter((app) =>
    modulosPermitidos.includes(app.id)
  );

  const grid = document.getElementById("apps-grid-container");
  grid.innerHTML = appsVisiveis
    .map(
      (app) => `
      <button type="button" onclick="abrirAplicativo('${app.id}')" class="group bg-white hover:bg-slate-50 p-5 rounded-2xl border border-slate-200 hover:border-[#714B67]/40 shadow-xs hover:shadow-md transition text-left flex flex-col justify-between">
        <div>
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br ${app.corBg} text-white flex items-center justify-center text-xl shadow-md mb-4 group-hover:scale-105 transition">
            <i class="fa-solid ${app.icone}"></i>
          </div>
          <h3 class="text-sm font-bold text-slate-900 group-hover:text-[#714B67] transition">${app.nome}</h3>
          <p class="text-xs text-slate-500 mt-1 leading-relaxed">${app.descricao}</p>
        </div>
        <div class="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-semibold text-[#714B67]">
          <span>Acessar módulo</span>
          <i class="fa-solid fa-arrow-right group-hover:translate-x-1 transition"></i>
        </div>
      </button>
    `
    )
    .join("");
}

function ocultarTodasAsViews() {
  const views = [
    "view-apps",
    "view-dashboard",
    "view-pdv",
    "view-estoque",
    "view-compras",
    "view-crm",
    "view-financeiro",
    "view-configuracoes",
  ];
  views.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.add("hidden");
  });
}

function abrirGradeAplicativos() {
  ESTADO.appAtual = "apps";
  ocultarTodasAsViews();
  document.getElementById("top-current-app-name").textContent = "Aplicativos";
  document.getElementById("view-apps").classList.remove("hidden");
  renderizarGradeAplicativos();
}

async function abrirAplicativo(appId) {
  const modulosPermitidos = (ESTADO.usuario && ESTADO.usuario.modulos_permitidos) || [];
  if (!modulosPermitidos.includes(appId)) {
    notificar("Seu perfil de usuário não possui acesso a este aplicativo.", "aviso");
    return;
  }

  ESTADO.appAtual = appId;
  ocultarTodasAsViews();

  const appInfo = CATALOGO_APLICATIVOS.find((a) => a.id === appId);
  document.getElementById("top-current-app-name").textContent = appInfo
    ? appInfo.nome
    : "Módulo";

  const viewEl = document.getElementById(`view-${appId}`);
  if (viewEl) viewEl.classList.remove("hidden");

  try {
    if (appId === "dashboard") await carregarDashboard();
    if (appId === "pdv") await inicializarModuloPDV();
    if (appId === "estoque") await carregarModuloEstoque();
    if (appId === "compras") await carregarModuloCompras();
    if (appId === "crm") await carregarModuloCRM();
    if (appId === "financeiro") await carregarModuloFinanceiro();
    if (appId === "configuracoes") await carregarModuloConfiguracoes();
  } catch (err) {
    notificar(err.message, "erro");
  }
}

async function atualizarDadosGlobais() {
  try {
    const me = await apiFetch("/api/auth/me");
    aplicarSessaoAutenticada(me);
    notificar("Dados sincronizados com sucesso.");
  } catch (err) {
    notificar(err.message, "erro");
  }
}

// ============================================================================
// APLICATIVO 1: Painel Geral (Dashboard)
// ============================================================================
async function carregarDashboard() {
  const resumo = await apiFetch(`/api/dashboard/resumo${obterQueryFilial()}`);

  document.getElementById("kpi-faturamento").textContent = moeda(
    resumo.faturamento_total
  );
  document.getElementById("kpi-lucro").textContent = moeda(resumo.lucro_liquido);
  document.getElementById("kpi-produtos").textContent = numero(
    resumo.total_produtos
  );
  document.getElementById("kpi-clientes").textContent = numero(
    resumo.total_clientes_crm
  );
  document.getElementById("kpi-cashback").textContent = moeda(
    resumo.cashback_em_circulacao
  );

  // Vendas por Unidade vs Meta
  const boxMetas = document.getElementById("dash-filiais-metas");
  const metas = resumo.vendas_por_filial_vs_meta || [];
  if (!metas.length) {
    boxMetas.innerHTML = `<p class="text-xs text-slate-400">Nenhuma unidade cadastrada.</p>`;
  } else {
    boxMetas.innerHTML = metas
      .map((f) => {
        const pct = Math.min(100, Math.max(0, Number(f.atingimento_pct || 0)));
        return `
        <div class="p-3 rounded-xl bg-slate-50 border border-slate-200">
          <div class="flex justify-between text-xs mb-1">
            <span class="font-bold text-slate-800">${f.nome} <span class="text-slate-400 font-normal">(${f.bandeira})</span></span>
            <span class="font-mono font-bold text-[#714B67]">${moeda(f.vendas_mes)} / ${moeda(f.meta_mensal)} (${numero(f.atingimento_pct, 1)}%)</span>
          </div>
          <div class="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
            <div class="h-full bg-[#017E84]" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
      })
      .join("");
  }

  // Top Produtos Vendidos
  const boxTop = document.getElementById("dash-top-produtos");
  const topProds = resumo.top_5_produtos || [];
  if (!topProds.length) {
    boxTop.innerHTML = `
      <div class="p-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
        Nenhuma venda registrada ainda. Cadastre seus produtos em <strong>Produtos & Estoque</strong> e realize vendas no <strong>PDV</strong>.
      </div>`;
  } else {
    boxTop.innerHTML = topProds
      .map(
        (p, idx) => `
      <div class="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
        <div class="flex items-center gap-2.5">
          <span class="w-6 h-6 rounded-full bg-[#714B67]/10 text-[#714B67] font-bold flex items-center justify-center">${idx + 1}</span>
          <div>
            <p class="font-bold text-slate-800">${p.nome}</p>
            <p class="text-[11px] text-slate-500">${p.departamento} • ${numero(p.quantidade_vendida)} un. vendidas</p>
          </div>
        </div>
        <span class="font-mono font-bold text-emerald-700">${moeda(p.total_faturado)}</span>
      </div>
    `
      )
      .join("");
  }

  // Alertas de Ruptura / Estoque Mínimo
  const alertas = resumo.alertas_ruptura || [];
  document.getElementById("dash-count-ruptura").textContent = alertas.length;
  const boxRuptura = document.getElementById("dash-alertas-ruptura");
  if (!alertas.length) {
    boxRuptura.innerHTML = `<p class="text-xs text-slate-400 py-4 text-center">Nenhum item abaixo do estoque mínimo.</p>`;
  } else {
    boxRuptura.innerHTML = alertas
      .map(
        (a) => `
      <div class="flex items-center justify-between p-2.5 rounded-lg bg-rose-50/70 border border-rose-200 text-xs">
        <div>
          <span class="font-bold text-slate-800">${a.produto_nome}</span>
          <span class="block text-[11px] text-slate-500">${a.filial_nome} • SKU: ${a.sku}</span>
        </div>
        <div class="text-right">
          <span class="px-2 py-0.5 rounded bg-rose-600 text-white text-[10px] font-bold">${a.status}</span>
          <span class="block font-mono text-[11px] text-rose-800 mt-0.5">Saldo: ${a.quantidade_atual} (Mín: ${a.estoque_minimo})</span>
        </div>
      </div>
    `
      )
      .join("");
  }

  // Lotes Vencendo
  const lotes = resumo.lotes_vencendo_15_dias || [];
  document.getElementById("dash-count-lotes").textContent = lotes.length;
  const boxLotes = document.getElementById("dash-lotes-vencendo");
  if (!lotes.length) {
    boxLotes.innerHTML = `<p class="text-xs text-slate-400 py-4 text-center">Nenhum lote com vencimento nos próximos 15 dias.</p>`;
  } else {
    boxLotes.innerHTML = lotes
      .map(
        (l) => `
      <div class="flex items-center justify-between p-2.5 rounded-lg bg-amber-50/70 border border-amber-200 text-xs">
        <div>
          <span class="font-bold text-slate-800">${l.produto_nome}</span>
          <span class="block text-[11px] text-slate-500">${l.filial_nome} • Lote: ${l.numero_lote}</span>
        </div>
        <div class="text-right font-mono">
          <span class="font-bold text-amber-800">Vence em ${l.dias_para_vencer} dia(s)</span>
          <span class="block text-[11px] text-slate-600">${dataBR(l.data_validade)} • Qtd: ${l.quantidade_lote}</span>
        </div>
      </div>
    `
      )
      .join("");
  }

  // Últimas Vendas
  const tbodyVendas = document.getElementById("dash-ultimas-vendas");
  const vendas = resumo.ultimas_vendas || [];
  if (!vendas.length) {
    tbodyVendas.innerHTML = `<tr><td colspan="7" class="py-6 text-center text-slate-400">Nenhuma venda realizada até o momento.</td></tr>`;
  } else {
    tbodyVendas.innerHTML = vendas
      .map(
        (v) => `
      <tr class="hover:bg-slate-50">
        <td class="py-2.5 px-4 font-mono font-semibold text-slate-800">${v.numero_cupom}</td>
        <td class="py-2.5 px-4">${v.filial_nome}</td>
        <td class="py-2.5 px-4">${v.cliente_nome}</td>
        <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold">${v.forma_pagamento}</span></td>
        <td class="py-2.5 px-4 text-right font-mono text-emerald-600">- ${moeda((v.desconto_clube_crm || 0) + (v.cashback_utilizado || 0))}</td>
        <td class="py-2.5 px-4 text-right font-mono font-bold text-slate-900">${moeda(v.valor_total_liquido)}</td>
        <td class="py-2.5 px-4 text-right text-slate-500">${dataHoraBR(v.criada_em)}</td>
      </tr>
    `
      )
      .join("");
  }
}

// ============================================================================
// APLICATIVO 2: Ponto de Venda (PDV)
// ============================================================================
async function inicializarModuloPDV() {
  const selectFilial = document.getElementById("pdv-select-filial");
  selectFilial.innerHTML = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");

  if (ESTADO.filialAtivaId !== "all") {
    selectFilial.value = ESTADO.filialAtivaId;
  }

  ESTADO.produtos = await apiFetch("/api/produtos");
  await carregarSessaoCaixaPDV();
  filtrarCatalogoPDV();
  renderizarCarrinhoPDV();
}

async function carregarSessaoCaixaPDV() {
  const filialId = document.getElementById("pdv-select-filial").value;
  if (!filialId) return;

  const sessao = await apiFetch(`/api/pdv/sessao-atual?filial_id=${filialId}`);
  ESTADO.sessaoCaixaPDV = sessao;

  const txt = document.getElementById("pdv-status-sessao-texto");
  const btnAbrir = document.getElementById("btn-abrir-caixa");
  const btnFechar = document.getElementById("btn-fechar-caixa");

  if (sessao && sessao.status === "ABERTO") {
    txt.innerHTML = `<span class="text-emerald-600 font-bold">● CAIXA ABERTO</span> • Operador: <strong>${sessao.operador_nome}</strong> • Abertura: ${moeda(sessao.valor_abertura)} • Vendido na sessão: <strong>${moeda(sessao.total_vendido)}</strong> (${sessao.qtd_vendas} vendas)`;
    btnAbrir.classList.add("hidden");
    btnFechar.classList.remove("hidden");
  } else {
    txt.innerHTML = `<span class="text-amber-600 font-bold">● CAIXA FECHADO</span> • Abra o caixa para registrar o fundo de troco da unidade.`;
    btnAbrir.classList.remove("hidden");
    btnFechar.classList.add("hidden");
  }
}

function abrirModalCaixa(acao) {
  const filialId = Number(document.getElementById("pdv-select-filial").value);
  if (acao === "abrir") {
    abrirModal(
      "Abertura de Caixa (Ponto de Venda)",
      `
      <form onsubmit="submeterAbrirCaixa(event, ${filialId})" class="space-y-4 text-xs">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Fundo de Troco / Valor Inicial em Caixa (R$)</label>
          <input type="number" step="0.01" min="0" id="modal-caixa-abertura" value="200.00" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono text-sm">
        </div>
        <button type="submit" class="w-full py-2.5 rounded-lg bg-emerald-600 text-white font-bold">Confirmar Abertura de Caixa</button>
      </form>
      `
    );
  } else if (ESTADO.sessaoCaixaPDV) {
    const esperado =
      Number(ESTADO.sessaoCaixaPDV.valor_abertura || 0) +
      Number(ESTADO.sessaoCaixaPDV.total_vendido || 0);
    abrirModal(
      "Fechamento de Caixa",
      `
      <form onsubmit="submeterFecharCaixa(event, ${ESTADO.sessaoCaixaPDV.id})" class="space-y-4 text-xs">
        <div class="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
          <div class="flex justify-between"><span>Fundo de Abertura:</span><strong class="font-mono">${moeda(ESTADO.sessaoCaixaPDV.valor_abertura)}</strong></div>
          <div class="flex justify-between"><span>Total Vendido na Sessão (${ESTADO.sessaoCaixaPDV.qtd_vendas} vendas):</span><strong class="font-mono text-emerald-700">${moeda(ESTADO.sessaoCaixaPDV.total_vendido)}</strong></div>
          <div class="flex justify-between pt-1 border-t border-slate-200"><span>Saldo Total Esperado:</span><strong class="font-mono">${moeda(esperado)}</strong></div>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Valor Conferido no Fechamento (R$)</label>
          <input type="number" step="0.01" min="0" id="modal-caixa-fechamento" value="${esperado.toFixed(2)}" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono text-sm">
        </div>
        <button type="submit" class="w-full py-2.5 rounded-lg bg-rose-600 text-white font-bold">Encerrar Caixa</button>
      </form>
      `
    );
  }
}

async function submeterAbrirCaixa(e, filialId) {
  e.preventDefault();
  const valor = Number(document.getElementById("modal-caixa-abertura").value || 0);
  await apiFetch("/api/pdv/caixa/abrir", {
    method: "POST",
    body: JSON.stringify({ filial_id: filialId, valor_abertura: valor }),
  });
  fecharModal();
  notificar("Caixa aberto com sucesso.");
  await carregarSessaoCaixaPDV();
}

async function submeterFecharCaixa(e, sessaoId) {
  e.preventDefault();
  const valor = Number(document.getElementById("modal-caixa-fechamento").value || 0);
  await apiFetch(`/api/pdv/caixa/${sessaoId}/fechar`, {
    method: "POST",
    body: JSON.stringify({ valor_fechamento: valor }),
  });
  fecharModal();
  notificar("Caixa encerrado com sucesso.");
  await carregarSessaoCaixaPDV();
}

function filtrarCatalogoPDV() {
  const termo = (document.getElementById("pdv-busca-produto").value || "")
    .trim()
    .toLowerCase();
  const grid = document.getElementById("pdv-grid-produtos");

  const lista = ESTADO.produtos.filter(
    (p) =>
      p.ativo &&
      (!termo ||
        p.nome.toLowerCase().includes(termo) ||
        p.sku.toLowerCase().includes(termo) ||
        p.ean.toLowerCase().includes(termo) ||
        p.departamento.toLowerCase().includes(termo))
  );

  if (!lista.length) {
    grid.innerHTML = `
      <div class="col-span-full py-12 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
        Nenhum produto encontrado no catálogo da empresa.
        <button type="button" onclick="abrirAplicativo('estoque')" class="block mx-auto mt-2 text-[#714B67] font-bold hover:underline">
          + Ir para Produtos & Estoque para cadastrar itens
        </button>
      </div>`;
    return;
  }

  grid.innerHTML = lista
    .map(
      (p) => `
    <button type="button" onclick="adicionarAoCarrinhoPDV(${p.id})" class="p-3 rounded-xl border border-slate-200 hover:border-[#017E84] bg-slate-50/60 hover:bg-white text-left transition flex flex-col justify-between group">
      <div>
        <div class="flex items-center justify-between text-[10px] font-mono text-slate-400 mb-1">
          <span>${p.sku}</span>
          <span>EAN: ${p.ean}</span>
        </div>
        <p class="text-xs font-bold text-slate-900 group-hover:text-[#017E84] line-clamp-2">${p.nome}</p>
        <span class="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-slate-200/70 text-slate-600">${p.departamento}</span>
      </div>
      <div class="mt-3 pt-2 border-t border-slate-200/80 flex items-baseline justify-between">
        <div>
          <span class="text-xs font-extrabold font-mono text-slate-900">${moeda(p.preco_venda)}</span>
          ${
            p.preco_clube_crm < p.preco_venda
              ? `<span class="block text-[10px] font-mono text-purple-700 font-semibold">Fidelidade: ${moeda(p.preco_clube_crm)}</span>`
              : ""
          }
        </div>
        <span class="w-6 h-6 rounded-lg bg-[#017E84]/10 text-[#017E84] flex items-center justify-center text-xs font-bold">+</span>
      </div>
    </button>
  `
    )
    .join("");
}

function aoPressionarEnterBuscaPDV(e) {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const termo = (e.target.value || "").trim().toLowerCase();
  if (!termo) return;
  const exato = ESTADO.produtos.find(
    (p) =>
      p.ativo &&
      (p.ean.toLowerCase() === termo || p.sku.toLowerCase() === termo)
  );
  if (exato) {
    adicionarAoCarrinhoPDV(exato.id);
    e.target.value = "";
    filtrarCatalogoPDV();
  }
}

function adicionarAoCarrinhoPDV(produtoId) {
  const prod = ESTADO.produtos.find((p) => p.id === produtoId);
  if (!prod) return;

  const itemExistente = ESTADO.carrinhoPDV.find(
    (i) => i.produto.id === produtoId
  );
  if (itemExistente) {
    itemExistente.quantidade += 1;
  } else {
    ESTADO.carrinhoPDV.push({ produto: prod, quantidade: 1 });
  }
  renderizarCarrinhoPDV();
}

function alterarQuantidadeCarrinho(produtoId, delta) {
  const idx = ESTADO.carrinhoPDV.findIndex((i) => i.produto.id === produtoId);
  if (idx === -1) return;
  ESTADO.carrinhoPDV[idx].quantidade += delta;
  if (ESTADO.carrinhoPDV[idx].quantidade <= 0) {
    ESTADO.carrinhoPDV.splice(idx, 1);
  }
  renderizarCarrinhoPDV();
}

async function identificarClientePDV() {
  const cpf = (document.getElementById("pdv-cpf-cliente").value || "").trim();
  if (!cpf) {
    notificar("Digite o CPF do cliente para localizar.", "aviso");
    return;
  }
  try {
    const res = await apiFetch(
      `/api/crm/clientes/cpf/${encodeURIComponent(cpf)}`
    );
    ESTADO.clientePDV = res.cliente;
    document.getElementById("pdv-info-cliente").classList.remove("hidden");
    document.getElementById("pdv-cliente-nome").textContent =
      ESTADO.clientePDV.nome;
    document.getElementById("pdv-cliente-nivel").textContent =
      ESTADO.clientePDV.segmento_rfm;
    document.getElementById("pdv-cliente-saldo").textContent = moeda(
      ESTADO.clientePDV.saldo_cashback
    );
    notificar(`Cliente ${ESTADO.clientePDV.nome} identificado no PDV.`);
    renderizarCarrinhoPDV();
  } catch (err) {
    notificar(err.message, "erro");
  }
}

function limparClientePDV() {
  ESTADO.clientePDV = null;
  document.getElementById("pdv-cpf-cliente").value = "";
  document.getElementById("pdv-usar-cashback").value = "0";
  document.getElementById("pdv-info-cliente").classList.add("hidden");
  renderizarCarrinhoPDV();
}

function renderizarCarrinhoPDV() {
  const tbody = document.getElementById("pdv-carrinho-tbody");
  if (!ESTADO.carrinhoPDV.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-slate-400">Carrinho vazio. Selecione ou bipe produtos ao lado.</td></tr>`;
    document.getElementById("pdv-resumo-bruto").textContent = "R$ 0,00";
    document.getElementById("pdv-resumo-desconto").textContent = "- R$ 0,00";
    document.getElementById("pdv-resumo-liquido").textContent = "R$ 0,00";
    return;
  }

  let bruto = 0;
  let comDesconto = 0;

  tbody.innerHTML = ESTADO.carrinhoPDV
    .map(({ produto, quantidade }) => {
      const unitNormal = Number(produto.preco_venda);
      const unitAplicado = ESTADO.clientePDV
        ? Number(produto.preco_clube_crm)
        : unitNormal;
      const subItem = unitAplicado * quantidade;
      bruto += unitNormal * quantidade;
      comDesconto += subItem;

      return `
      <tr>
        <td class="py-2 px-3">
          <p class="font-bold text-slate-800">${produto.nome}</p>
          <span class="text-[10px] font-mono text-slate-400">${produto.sku}</span>
        </td>
        <td class="py-2 px-2 text-center">
          <div class="inline-flex items-center border border-slate-300 rounded-lg overflow-hidden">
            <button type="button" onclick="alterarQuantidadeCarrinho(${produto.id}, -1)" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 font-bold">-</button>
            <span class="px-2 font-mono font-bold">${quantidade}</span>
            <button type="button" onclick="alterarQuantidadeCarrinho(${produto.id}, 1)" class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 font-bold">+</button>
          </div>
        </td>
        <td class="py-2 px-2 text-right font-mono">${moeda(unitAplicado)}</td>
        <td class="py-2 px-3 text-right font-mono font-bold">${moeda(subItem)}</td>
        <td class="py-2 px-2 text-right">
          <button type="button" onclick="alterarQuantidadeCarrinho(${produto.id}, -9999)" class="text-rose-500 hover:text-rose-700">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </td>
      </tr>
    `;
    })
    .join("");

  const usarCashbackInput = Number(
    document.getElementById("pdv-usar-cashback").value || 0
  );
  const saldoDisp = ESTADO.clientePDV
    ? Number(ESTADO.clientePDV.saldo_cashback || 0)
    : 0;
  const cashbackAplicado = Math.min(usarCashbackInput, saldoDisp, comDesconto);
  const descontoTotal = bruto - comDesconto + cashbackAplicado;
  const liquido = Math.max(0, comDesconto - cashbackAplicado);

  document.getElementById("pdv-resumo-bruto").textContent = moeda(bruto);
  document.getElementById("pdv-resumo-desconto").textContent =
    `- ${moeda(descontoTotal)}`;
  document.getElementById("pdv-resumo-liquido").textContent = moeda(liquido);
}

async function finalizarVendaPDV() {
  if (!ESTADO.carrinhoPDV.length) {
    notificar("Adicione ao menos um item ao carrinho para vender.", "aviso");
    return;
  }
  const filialId = Number(document.getElementById("pdv-select-filial").value);
  if (!filialId) {
    notificar("Selecione a unidade do PDV.", "aviso");
    return;
  }

  const payload = {
    filial_id: filialId,
    itens: ESTADO.carrinhoPDV.map((i) => ({
      produto_id: i.produto.id,
      quantidade: i.quantidade,
    })),
    cpf_cliente: ESTADO.clientePDV
      ? ESTADO.clientePDV.cpf
      : document.getElementById("pdv-cpf-cliente").value.trim() || null,
    usar_cashback: Number(
      document.getElementById("pdv-usar-cashback").value || 0
    ),
    forma_pagamento: document.getElementById("pdv-forma-pagamento").value,
  };

  try {
    const cupom = await apiFetch("/api/pdv/vender", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    ESTADO.carrinhoPDV = [];
    limparClientePDV();
    renderizarCarrinhoPDV();
    await carregarSessaoCaixaPDV();
    exibirCupomFiscal(cupom);
    notificar(`Venda ${cupom.numero_cupom} concluída com sucesso!`);
  } catch (err) {
    notificar(err.message, "erro");
  }
}

function exibirCupomFiscal(cupom) {
  const modal = document.getElementById("modal-cupom");
  const box = document.getElementById("cupom-conteudo");

  const itensHtml = (cupom.itens || [])
    .map(
      (i) => `
    <div class="flex justify-between py-0.5">
      <span class="truncate max-w-[180px]">${i.quantidade}x ${i.nome}</span>
      <span>${moeda(i.subtotal)}</span>
    </div>
  `
    )
    .join("");

  box.innerHTML = `
    <div class="text-center border-b border-dashed border-slate-400 pb-2">
      <p class="font-bold text-sm uppercase">${ESTADO.tenant ? ESTADO.tenant.nome_fantasia : "HelpDmais"}</p>
      <p class="text-[11px]">${cupom.filial_nome}</p>
      <p class="text-[10px] text-slate-500">${cupom.numero_cupom}</p>
      <p class="text-[10px] text-slate-500">${dataHoraBR(cupom.data_hora)}</p>
    </div>
    <div class="border-b border-dashed border-slate-400 py-2 space-y-0.5">
      ${itensHtml}
    </div>
    <div class="space-y-1 pt-1">
      <div class="flex justify-between"><span>SUBTOTAL BRUTO:</span><span>${moeda(cupom.subtotal_bruto)}</span></div>
      <div class="flex justify-between"><span>DESCONTO FIDELIDADE:</span><span>- ${moeda(cupom.desconto_clube_crm)}</span></div>
      <div class="flex justify-between"><span>CASHBACK USADO:</span><span>- ${moeda(cupom.cashback_utilizado)}</span></div>
      <div class="flex justify-between font-bold text-sm pt-1 border-t border-dashed border-slate-400">
        <span>TOTAL PAGO (${cupom.forma_pagamento}):</span>
        <span>${moeda(cupom.valor_total_liquido)}</span>
      </div>
    </div>
    <div class="pt-2 border-t border-dashed border-slate-400 text-[10px] text-center">
      <p>Cliente: ${cupom.cliente_nome}</p>
      ${cupom.cashback_gerado > 0 ? `<p class="font-bold">Cashback creditado nesta compra: ${moeda(cupom.cashback_gerado)}</p>` : ""}
    </div>
  `;
  modal.classList.remove("hidden");
}

// ============================================================================
// APLICATIVO 3: Produtos & Estoque
// ============================================================================
async function carregarModuloEstoque() {
  const [produtos, estoque, fornecedores] = await Promise.all([
    apiFetch("/api/produtos"),
    apiFetch(`/api/estoque${obterQueryFilial()}`),
    apiFetch("/api/fornecedores"),
  ]);
  ESTADO.produtos = produtos;
  ESTADO.estoque = estoque;
  ESTADO.fornecedores = fornecedores;
  renderizarTabelaEstoque();
}

function renderizarTabelaEstoque() {
  const tbody = document.getElementById("estoque-tbody");
  const busca = (document.getElementById("estoque-filtro-busca").value || "")
    .trim()
    .toLowerCase();

  const filtrados = ESTADO.estoque.filter(
    (e) =>
      !busca ||
      (e.produto_nome && e.produto_nome.toLowerCase().includes(busca)) ||
      (e.produto_sku && e.produto_sku.toLowerCase().includes(busca)) ||
      (e.produto_ean && e.produto_ean.toLowerCase().includes(busca)) ||
      (e.departamento && e.departamento.toLowerCase().includes(busca))
  );

  if (!filtrados.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="py-10 text-center text-slate-400">
          Nenhum produto cadastrado nesta empresa ainda. Clique em <strong>+ Novo Produto</strong> acima para cadastrar.
        </td>
      </tr>`;
    return;
  }

  const badgeStatus = {
    NORMAL: "bg-emerald-100 text-emerald-800",
    CRITICO: "bg-amber-100 text-amber-800",
    RUPTURA: "bg-rose-100 text-rose-800",
  };

  tbody.innerHTML = filtrados
    .map((item) => {
      const lotesHtml = (item.lotes_validade || []).length
        ? item.lotes_validade
            .map(
              (l) =>
                `<span class="inline-block mr-1 mb-1 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 font-mono text-[10px]">${l.numero_lote}: ${l.quantidade_lote} un (Venc: ${dataBR(l.data_validade)})</span>`
            )
            .join("")
        : `<span class="text-slate-400 text-[11px]">Sem lotes ativos</span>`;

      return `
      <tr class="hover:bg-slate-50">
        <td class="py-3 px-4 font-mono">
          <span class="font-bold text-slate-800">${item.produto_sku}</span>
          <span class="block text-[10px] text-slate-400">${item.produto_ean || ""}</span>
        </td>
        <td class="py-3 px-4">
          <p class="font-bold text-slate-900">${item.produto_nome}</p>
          <span class="text-[11px] text-slate-500">${item.departamento} (${item.unidade})</span>
        </td>
        <td class="py-3 px-4">${item.filial_nome}</td>
        <td class="py-3 px-4 text-right font-mono">${moeda(item.preco_custo)}</td>
        <td class="py-3 px-4 text-right font-mono">
          <span class="font-bold text-slate-900">${moeda(item.preco_venda)}</span>
          <span class="block text-[10px] text-purple-700">Clube: ${moeda(item.preco_clube_crm)}</span>
        </td>
        <td class="py-3 px-4 text-right font-mono font-bold text-sm">${item.quantidade_atual}</td>
        <td class="py-3 px-4 text-center">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeStatus[item.status] || ""}">${item.status}</span>
        </td>
        <td class="py-3 px-4">${lotesHtml}</td>
      </tr>
    `;
    })
    .join("");
}

function abrirModalNovoProduto() {
  const opcoesForn = [
    `<option value="">Sem fornecedor vinculado</option>`,
    ...ESTADO.fornecedores.map(
      (f) => `<option value="${f.id}">${f.nome_fantasia} (${f.cnpj})</option>`
    ),
  ].join("");

  const opcoesFiliais = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");

  abrirModal(
    "Cadastrar Novo Produto no Catálogo",
    `
    <form onsubmit="submeterNovoProduto(event)" class="space-y-3 text-xs">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Código Interno (SKU) *</label>
          <input type="text" id="prod-sku" required placeholder="Ex: ARROZ-5KG" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono uppercase">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Código de Barras (EAN-13) *</label>
          <input type="text" id="prod-ean" required placeholder="7890000000001" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Descrição do Produto *</label>
        <input type="text" id="prod-nome" required placeholder="Ex: Arroz Tipo 1 Pacote 5kg" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-3 gap-3">
        <div class="col-span-2">
          <label class="block font-semibold text-slate-700 mb-1">Departamento / Categoria *</label>
          <input type="text" id="prod-depto" required placeholder="Ex: Mercearia, Bebidas, Açougue, Hortifruti" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Unidade</label>
          <select id="prod-un" class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">
            <option value="UN">UN</option>
            <option value="KG">KG</option>
            <option value="CX">CX</option>
            <option value="FD">FD</option>
            <option value="LT">LT</option>
          </select>
        </div>
      </div>
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Preço de Custo (R$) *</label>
          <input type="number" step="0.01" min="0.01" id="prod-custo" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Preço de Venda (R$) *</label>
          <input type="number" step="0.01" min="0.01" id="prod-venda" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Preço Fidelidade (R$)</label>
          <input type="number" step="0.01" min="0.01" id="prod-clube" placeholder="Opcional" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Fornecedor Principal</label>
          <select id="prod-forn" class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesForn}</select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Estoque Mínimo de Alerta</label>
          <input type="number" step="1" min="0" id="prod-est-min" value="10" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
        <p class="font-bold text-slate-700">Saldo Inicial de Estoque (Opcional)</p>
        <div class="grid grid-cols-3 gap-2">
          <div>
            <label class="block text-[11px] text-slate-600 mb-1">Unidade</label>
            <select id="prod-filial-ini" class="w-full px-2 py-1.5 rounded border border-slate-300 bg-white">${opcoesFiliais}</select>
          </div>
          <div>
            <label class="block text-[11px] text-slate-600 mb-1">Qtd Inicial</label>
            <input type="number" step="0.01" min="0" id="prod-qtd-ini" value="0" class="w-full px-2 py-1.5 rounded border border-slate-300 font-mono">
          </div>
          <div>
            <label class="block text-[11px] text-slate-600 mb-1">Validade Lote</label>
            <input type="date" id="prod-val-ini" class="w-full px-2 py-1.5 rounded border border-slate-300">
          </div>
        </div>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Salvar Produto</button>
    </form>
    `
  );
}

async function submeterNovoProduto(e) {
  e.preventDefault();
  const venda = Number(document.getElementById("prod-venda").value);
  const clubeVal = document.getElementById("prod-clube").value;
  const fornVal = document.getElementById("prod-forn").value;
  const valIni = document.getElementById("prod-val-ini").value;

  const payload = {
    sku: document.getElementById("prod-sku").value.trim(),
    ean: document.getElementById("prod-ean").value.trim(),
    nome: document.getElementById("prod-nome").value.trim(),
    departamento: document.getElementById("prod-depto").value.trim(),
    unidade: document.getElementById("prod-un").value,
    preco_custo: Number(document.getElementById("prod-custo").value),
    preco_venda: venda,
    preco_clube_crm: clubeVal ? Number(clubeVal) : venda,
    cashback_percentual: 1.0,
    estoque_minimo_padrao: Number(
      document.getElementById("prod-est-min").value || 10
    ),
    fornecedor_id: fornVal ? Number(fornVal) : null,
    perecivel: Boolean(valIni),
    ativo: true,
    filial_inicial_id: Number(document.getElementById("prod-filial-ini").value),
    estoque_inicial: Number(document.getElementById("prod-qtd-ini").value || 0),
    data_validade_inicial: valIni || null,
  };

  await apiFetch("/api/produtos", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  fecharModal();
  notificar("Produto cadastrado com sucesso.");
  await carregarModuloEstoque();
}

function abrirModalMovimentarEstoque() {
  if (!ESTADO.produtos.length) {
    notificar("Cadastre ao menos um produto antes de movimentar o estoque.", "aviso");
    return;
  }
  const opcoesFiliais = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");
  const opcoesProds = ESTADO.produtos
    .map((p) => `<option value="${p.id}">${p.sku} — ${p.nome}</option>`)
    .join("");

  abrirModal(
    "Entrada de Mercadoria / Ajuste de Inventário",
    `
    <form onsubmit="submeterMovimentoEstoque(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Unidade / Loja *</label>
        <select id="mov-filial" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Produto *</label>
        <select id="mov-produto" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesProds}</select>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Tipo de Operação *</label>
          <select id="mov-tipo" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">
            <option value="ENTRADA_COMPRA">Entrada de Mercadoria (+)</option>
            <option value="AJUSTE_POSITIVO">Ajuste Positivo de Inventário (+)</option>
            <option value="QUEBRA_PERDA">Baixa por Perda / Avaria (-)</option>
            <option value="AJUSTE_INVENTARIO">Ajuste Negativo de Inventário (-)</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Quantidade *</label>
          <input type="number" step="0.01" min="0.01" id="mov-qtd" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Número do Lote</label>
          <input type="text" id="mov-lote" placeholder="Ex: LOTE-2026-01" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Data de Validade</label>
          <input type="date" id="mov-validade" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Observação / Nota Fiscal</label>
        <input type="text" id="mov-obs" placeholder="Ex: NF 12450" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#017E84] text-white font-bold">Confirmar Movimentação</button>
    </form>
    `
  );
}

async function submeterMovimentoEstoque(e) {
  e.preventDefault();
  const payload = {
    filial_id: Number(document.getElementById("mov-filial").value),
    produto_id: Number(document.getElementById("mov-produto").value),
    tipo: document.getElementById("mov-tipo").value,
    quantidade: Number(document.getElementById("mov-qtd").value),
    numero_lote: document.getElementById("mov-lote").value.trim() || null,
    data_validade: document.getElementById("mov-validade").value || null,
    observacao: document.getElementById("mov-obs").value.trim(),
  };
  await apiFetch("/api/estoque/movimentar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  fecharModal();
  notificar("Estoque atualizado com sucesso.");
  await carregarModuloEstoque();
}

function abrirModalTransferirEstoque() {
  if (ESTADO.filiais.length < 2) {
    notificar(
      "Cadastre ao menos 2 unidades em Empresa & Equipe para transferir estoque entre lojas.",
      "aviso"
    );
    return;
  }
  const opcoesFiliais = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");
  const opcoesProds = ESTADO.produtos
    .map((p) => `<option value="${p.id}">${p.sku} — ${p.nome}</option>`)
    .join("");

  abrirModal(
    "Transferência de Estoque entre Unidades",
    `
    <form onsubmit="submeterTransferenciaEstoque(event)" class="space-y-3 text-xs">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Unidade de Origem *</label>
          <select id="transf-origem" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Unidade de Destino *</label>
          <select id="transf-destino" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Produto *</label>
        <select id="transf-produto" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesProds}</select>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Quantidade a Transferir *</label>
        <input type="number" step="0.01" min="0.01" id="transf-qtd" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Observação</label>
        <input type="text" id="transf-obs" placeholder="Motivo da transferência" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Transferir Mercadoria</button>
    </form>
    `
  );
}

async function submeterTransferenciaEstoque(e) {
  e.preventDefault();
  const payload = {
    filial_origem_id: Number(document.getElementById("transf-origem").value),
    filial_destino_id: Number(document.getElementById("transf-destino").value),
    produto_id: Number(document.getElementById("transf-produto").value),
    quantidade: Number(document.getElementById("transf-qtd").value),
    observacao: document.getElementById("transf-obs").value.trim(),
  };
  await apiFetch("/api/estoque/transferir", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  fecharModal();
  notificar("Transferência entre unidades concluída.");
  await carregarModuloEstoque();
}

// ============================================================================
// APLICATIVO 4: Compras & Fornecedores
// ============================================================================
async function carregarModuloCompras() {
  const [fornecedores, compras, produtos] = await Promise.all([
    apiFetch("/api/fornecedores"),
    apiFetch("/api/compras"),
    apiFetch("/api/produtos"),
  ]);
  ESTADO.fornecedores = fornecedores;
  ESTADO.compras = compras;
  ESTADO.produtos = produtos;

  const boxForn = document.getElementById("fornecedores-lista");
  if (!fornecedores.length) {
    boxForn.innerHTML = `<p class="text-xs text-slate-400 py-6 text-center">Nenhum fornecedor cadastrado. Clique em <strong>Novo Fornecedor</strong>.</p>`;
  } else {
    boxForn.innerHTML = fornecedores
      .map(
        (f) => `
      <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <div class="flex justify-between font-bold text-slate-900">
          <span>${f.nome_fantasia}</span>
          <span class="font-mono text-[11px] text-slate-500">${f.cnpj}</span>
        </div>
        <p class="text-[11px] text-slate-500 mt-0.5">${f.razao_social}</p>
        <div class="flex justify-between mt-2 pt-2 border-t border-slate-200/80 text-[11px] text-slate-600">
          <span>${f.categoria_principal}</span>
          <span>Prazo: ${f.prazo_entrega_dias} dia(s)</span>
        </div>
      </div>
    `
      )
      .join("");
  }

  const tbody = document.getElementById("compras-tbody");
  if (!compras.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="py-10 text-center text-slate-400">Nenhum pedido de compra emitido.</td></tr>`;
  } else {
    tbody.innerHTML = compras
      .map(
        (c) => `
      <tr class="hover:bg-slate-50">
        <td class="py-3 px-4 font-mono font-bold">${c.numero_pedido}</td>
        <td class="py-3 px-4">${c.filial_nome || c.filial_id}</td>
        <td class="py-3 px-4">
          <p class="font-bold text-slate-900">${c.produto_nome || c.produto_id}</p>
          <span class="text-[11px] text-slate-500">${c.fornecedor_nome || ""}</span>
        </td>
        <td class="py-3 px-4 text-right font-mono">${c.quantidade}</td>
        <td class="py-3 px-4 text-right font-mono font-bold">${moeda(c.valor_total)}</td>
        <td class="py-3 px-4 text-center">
          <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${c.status === "RECEBIDO" ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}">${c.status}</span>
        </td>
        <td class="py-3 px-4 text-right">
          ${
            c.status !== "RECEBIDO"
              ? `<button type="button" onclick="confirmarRecebimentoCompra(${c.id})" class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-semibold">Receber no Estoque</button>`
              : `<span class="text-slate-400 text-[11px]">Integrado</span>`
          }
        </td>
      </tr>
    `
      )
      .join("");
  }
}

function abrirModalNovoFornecedor() {
  abrirModal(
    "Cadastrar Fornecedor",
    `
    <form onsubmit="submeterNovoFornecedor(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Nome Fantasia *</label>
        <input type="text" id="forn-fantasia" required placeholder="Ex: Distribuidora Sul Alimentos" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Razão Social *</label>
        <input type="text" id="forn-razao" required placeholder="Ex: Sul Alimentos Atacadista Ltda" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">CNPJ *</label>
          <input type="text" id="forn-cnpj" required placeholder="00.000.000/0001-00" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Categoria Principal *</label>
          <input type="text" id="forn-cat" required placeholder="Ex: Bebidas, Secos, Laticínios" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Telefone</label>
          <input type="text" id="forn-tel" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Prazo de Entrega (Dias)</label>
          <input type="number" min="1" id="forn-prazo" value="3" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Salvar Fornecedor</button>
    </form>
    `
  );
}

async function submeterNovoFornecedor(e) {
  e.preventDefault();
  await apiFetch("/api/fornecedores", {
    method: "POST",
    body: JSON.stringify({
      nome_fantasia: document.getElementById("forn-fantasia").value.trim(),
      razao_social: document.getElementById("forn-razao").value.trim(),
      cnpj: document.getElementById("forn-cnpj").value.trim(),
      categoria_principal: document.getElementById("forn-cat").value.trim(),
      telefone: document.getElementById("forn-tel").value.trim(),
      prazo_entrega_dias: Number(document.getElementById("forn-prazo").value || 3),
    }),
  });
  fecharModal();
  notificar("Fornecedor cadastrado com sucesso.");
  await carregarModuloCompras();
}

function abrirModalNovoPedidoCompra() {
  if (!ESTADO.fornecedores.length || !ESTADO.produtos.length) {
    notificar(
      "Cadastre ao menos um fornecedor e um produto antes de emitir pedidos de compra.",
      "aviso"
    );
    return;
  }
  const opcoesFiliais = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");
  const opcoesForn = ESTADO.fornecedores
    .map((f) => `<option value="${f.id}">${f.nome_fantasia}</option>`)
    .join("");
  const opcoesProd = ESTADO.produtos
    .map(
      (p) =>
        `<option value="${p.id}" data-custo="${p.preco_custo}">${p.sku} — ${p.nome}</option>`
    )
    .join("");

  abrirModal(
    "Emitir Pedido de Compra",
    `
    <form onsubmit="submeterNovoPedidoCompra(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Unidade Recebedora *</label>
        <select id="pc-filial" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Fornecedor *</label>
        <select id="pc-forn" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesForn}</select>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Produto *</label>
        <select id="pc-prod" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesProd}</select>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Quantidade *</label>
          <input type="number" step="0.01" min="0.01" id="pc-qtd" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Custo Unitário (R$) *</label>
          <input type="number" step="0.01" min="0.01" id="pc-custo" value="${ESTADO.produtos[0].preco_custo}" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Emitir Pedido de Compra</button>
    </form>
    `
  );
}

async function submeterNovoPedidoCompra(e) {
  e.preventDefault();
  await apiFetch("/api/compras", {
    method: "POST",
    body: JSON.stringify({
      filial_id: Number(document.getElementById("pc-filial").value),
      fornecedor_id: Number(document.getElementById("pc-forn").value),
      produto_id: Number(document.getElementById("pc-prod").value),
      quantidade: Number(document.getElementById("pc-qtd").value),
      custo_unitario: Number(document.getElementById("pc-custo").value),
    }),
  });
  fecharModal();
  notificar("Pedido de compra emitido.");
  await carregarModuloCompras();
}

async function confirmarRecebimentoCompra(pedidoId) {
  try {
    const res = await apiFetch(`/api/compras/${pedidoId}/receber`, {
      method: "POST",
    });
    notificar(
      `Mercadoria recebida! Novo saldo de ${res.produto}: ${res.novo_saldo_estoque} (${res.lote_criado}).`
    );
    await carregarModuloCompras();
  } catch (err) {
    notificar(err.message, "erro");
  }
}

// ============================================================================
// APLICATIVO 5: Clientes & CRM
// ============================================================================
async function carregarModuloCRM() {
  const [clientes, campanhas] = await Promise.all([
    apiFetch("/api/crm/clientes"),
    apiFetch("/api/crm/campanhas"),
  ]);
  ESTADO.clientes = clientes;
  ESTADO.campanhas = campanhas;

  // Kanban de Fidelidade
  const colunas = [
    { codigo: "NOVO", titulo: "Novos Clientes", cor: "border-slate-300 bg-slate-50" },
    { codigo: "PRATA", titulo: "Nível Prata", cor: "border-sky-300 bg-sky-50/40" },
    { codigo: "OURO", titulo: "Nível Ouro", cor: "border-amber-300 bg-amber-50/40" },
    { codigo: "DIAMANTE", titulo: "Nível Diamante", cor: "border-purple-300 bg-purple-50/40" },
  ];

  document.getElementById("crm-kanban-board").innerHTML = colunas
    .map((col) => {
      const lista = clientes.filter((c) => c.segmento_rfm === col.codigo);
      return `
      <div class="rounded-xl border ${col.cor} p-3.5">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-extrabold uppercase text-slate-700">${col.titulo}</span>
          <span class="px-2 py-0.5 rounded-full bg-white border border-slate-200 text-xs font-bold">${lista.length}</span>
        </div>
        <div class="space-y-2 max-h-56 overflow-y-auto">
          ${
            lista.length
              ? lista
                  .map(
                    (c) => `
              <div class="p-2.5 rounded-lg bg-white border border-slate-200 shadow-2xs text-xs">
                <p class="font-bold text-slate-900">${c.nome}</p>
                <p class="text-[10px] font-mono text-slate-500">CPF: ${c.cpf}</p>
                <div class="flex justify-between mt-1.5 pt-1.5 border-t border-slate-100 font-mono text-[11px]">
                  <span>Gasto: ${moeda(c.total_gasto_historico)}</span>
                  <span class="text-emerald-700 font-bold">CB: ${moeda(c.saldo_cashback)}</span>
                </div>
              </div>
            `
                  )
                  .join("")
              : `<p class="text-[11px] text-slate-400 text-center py-4">Sem clientes neste nível</p>`
          }
        </div>
      </div>
    `;
    })
    .join("");

  const tbody = document.getElementById("crm-clientes-tbody");
  if (!clientes.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="py-10 text-center text-slate-400">Nenhum cliente cadastrado na empresa.</td></tr>`;
  } else {
    tbody.innerHTML = clientes
      .map(
        (c) => `
      <tr class="hover:bg-slate-50">
        <td class="py-3 px-4">
          <p class="font-bold text-slate-900">${c.nome}</p>
          <span class="font-mono text-[11px] text-slate-500">${c.cpf}</span>
        </td>
        <td class="py-3 px-4 text-slate-600">${c.whatsapp || "-"}<span class="block text-[11px] text-slate-400">${c.email || ""}</span></td>
        <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-purple-100 text-purple-800 text-[10px] font-bold">${c.segmento_rfm}</span></td>
        <td class="py-3 px-4 text-right font-mono">${c.total_compras_count}</td>
        <td class="py-3 px-4 text-right font-mono font-bold">${moeda(c.total_gasto_historico)}</td>
        <td class="py-3 px-4 text-right font-mono font-bold text-emerald-700">${moeda(c.saldo_cashback)}</td>
      </tr>
    `
      )
      .join("");
  }

  const boxCamp = document.getElementById("crm-campanhas-lista");
  if (!campanhas.length) {
    boxCamp.innerHTML = `<p class="text-xs text-slate-400 py-6 text-center">Nenhuma campanha criada.</p>`;
  } else {
    boxCamp.innerHTML = campanhas
      .map(
        (cp) => `
      <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <div class="flex justify-between items-start">
          <span class="font-bold text-slate-900">${cp.titulo}</span>
          <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">${cp.segmento_alvo}</span>
        </div>
        <p class="text-[11px] text-slate-600 mt-1">${cp.mensagem_template || "Oferta ativa para clientes qualificados."}</p>
        <div class="flex justify-between mt-2 pt-2 border-t border-slate-200 text-[11px] text-slate-500">
          <span>Desconto: ${cp.desconto_extra_pct}% | Cashback: +${cp.cashback_bonus_pct}%</span>
          <span>Alcance: ${cp.clientes_impactados} cliente(s)</span>
        </div>
      </div>
    `
      )
      .join("");
  }
}

function abrirModalNovoCliente() {
  abrirModal(
    "Cadastrar Cliente no Programa de Fidelidade",
    `
    <form onsubmit="submeterNovoCliente(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Nome Completo *</label>
        <input type="text" id="cli-nome" required class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">CPF *</label>
          <input type="text" id="cli-cpf" required placeholder="000.000.000-00" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">WhatsApp / Telefone</label>
          <input type="text" id="cli-whats" placeholder="(11) 99999-9999" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">E-mail</label>
        <input type="email" id="cli-email" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Cadastrar Cliente</button>
    </form>
    `
  );
}

async function submeterNovoCliente(e) {
  e.preventDefault();
  await apiFetch("/api/crm/clientes", {
    method: "POST",
    body: JSON.stringify({
      nome: document.getElementById("cli-nome").value.trim(),
      cpf: document.getElementById("cli-cpf").value.trim(),
      whatsapp: document.getElementById("cli-whats").value.trim(),
      email: document.getElementById("cli-email").value.trim(),
    }),
  });
  fecharModal();
  notificar("Cliente cadastrado com sucesso.");
  await carregarModuloCRM();
}

function abrirModalNovaCampanha() {
  abrirModal(
    "Criar Campanha Promocional",
    `
    <form onsubmit="submeterNovaCampanha(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Título da Campanha *</label>
        <input type="text" id="camp-titulo" required placeholder="Ex: Quarta do Hortifruti" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Público-Alvo</label>
          <select id="camp-alvo" class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">
            <option value="TODOS">Todos os Clientes</option>
            <option value="DIAMANTE">Nível Diamante</option>
            <option value="OURO">Nível Ouro</option>
            <option value="PRATA">Nível Prata</option>
            <option value="NOVO">Novos Clientes</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Desconto (%)</label>
          <input type="number" step="0.5" min="0" id="camp-desc" value="5" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Cashback Extra (%)</label>
          <input type="number" step="0.5" min="0" id="camp-cb" value="2" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Mensagem da Oferta</label>
        <textarea id="camp-msg" rows="3" class="w-full px-3 py-2 rounded-lg border border-slate-300"></textarea>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#017E84] text-white font-bold">Publicar Campanha</button>
    </form>
    `
  );
}

async function submeterNovaCampanha(e) {
  e.preventDefault();
  await apiFetch("/api/crm/campanhas", {
    method: "POST",
    body: JSON.stringify({
      titulo: document.getElementById("camp-titulo").value.trim(),
      segmento_alvo: document.getElementById("camp-alvo").value,
      canal: "WHATSAPP",
      desconto_extra_pct: Number(document.getElementById("camp-desc").value || 0),
      cashback_bonus_pct: Number(document.getElementById("camp-cb").value || 0),
      mensagem_template: document.getElementById("camp-msg").value.trim(),
    }),
  });
  fecharModal();
  notificar("Campanha criada com sucesso.");
  await carregarModuloCRM();
}

// ============================================================================
// APLICATIVO 6: Financeiro & DRE
// ============================================================================
async function carregarModuloFinanceiro() {
  const qFilial = obterQueryFilial();
  const [dre, lancamentos] = await Promise.all([
    apiFetch(`/api/financeiro/dre${qFilial}`),
    apiFetch(`/api/financeiro/lancamentos${qFilial}`),
  ]);

  document.getElementById("fin-dre-container").innerHTML = `
    <div class="flex justify-between p-2.5 rounded-lg bg-slate-50">
      <span>(+) Receita Bruta de Vendas</span>
      <strong class="font-mono text-slate-900">${moeda(dre.receita_bruta)}</strong>
    </div>
    <div class="flex justify-between p-2.5 rounded-lg text-rose-700">
      <span>(-) Impostos sobre Vendas</span>
      <span class="font-mono">- ${moeda(dre.impostos)}</span>
    </div>
    <div class="flex justify-between p-2.5 rounded-lg bg-slate-100 font-bold">
      <span>(=) ReceitaOperacional Líquida</span>
      <span class="font-mono">${moeda(dre.receita_liquida)}</span>
    </div>
    <div class="flex justify-between p-2.5 rounded-lg text-rose-700">
      <span>(-) Custo das Mercadorias Vendidas (CMV)</span>
      <span class="font-mono">- ${moeda(dre.cmv)}</span>
    </div>
    <div class="flex justify-between p-2.5 rounded-lg bg-indigo-50 font-bold text-indigo-900">
      <span>(=) Lucro Bruto (${numero(dre.margem_bruta_pct, 1)}%)</span>
      <span class="font-mono">${moeda(dre.lucro_bruto)}</span>
    </div>
    <div class="flex justify-between p-2.5 rounded-lg text-rose-700">
      <span>(-) Despesas Operacionais (Folha, Energia, Aluguel)</span>
      <span class="font-mono">- ${moeda(dre.despesas_operacionais)}</span>
    </div>
    <div class="flex justify-between p-3.5 rounded-xl bg-slate-900 text-white font-extrabold text-sm">
      <span>(=) RESULTADO LÍQUIDO / EBITDA (${numero(dre.margem_liquida_pct, 1)}%)</span>
      <span class="font-mono text-emerald-400">${moeda(dre.ebitda_lucro_liquido)}</span>
    </div>
  `;

  const tbody = document.getElementById("fin-lancamentos-tbody");
  if (!lancamentos.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="py-10 text-center text-slate-400">Nenhum lançamento financeiro registrado.</td></tr>`;
  } else {
    tbody.innerHTML = lancamentos
      .map(
        (l) => `
      <tr class="hover:bg-slate-50">
        <td class="py-2.5 px-4 font-mono">${dataBR(l.data_competencia)}</td>
        <td class="py-2.5 px-4">${l.filial_nome || l.filial_id}</td>
        <td class="py-2.5 px-4">
          <p class="font-bold text-slate-800">${l.descricao}</p>
          <span class="text-[10px] font-mono text-slate-400">${l.categoria_dre}</span>
        </td>
        <td class="py-2.5 px-4 text-center">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold ${l.tipo === "RECEITA" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}">${l.tipo}</span>
        </td>
        <td class="py-2.5 px-4 text-right font-mono font-bold ${l.tipo === "RECEITA" ? "text-emerald-700" : "text-rose-700"}">${moeda(l.valor)}</td>
      </tr>
    `
      )
      .join("");
  }
}

function abrirModalNovoLancamento() {
  const opcoesFiliais = ESTADO.filiais
    .map((f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`)
    .join("");

  abrirModal(
    "Novo Lançamento Financeiro",
    `
    <form onsubmit="submeterNovoLancamento(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Unidade *</label>
        <select id="fin-filial" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Tipo *</label>
          <select id="fin-tipo" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">
            <option value="DESPESA">Despesa (-)</option>
            <option value="RECEITA">Receita (+)</option>
            <option value="CMV">Custo de Mercadoria (-)</option>
          </select>
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Classificação DRE *</label>
          <select id="fin-cat" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">
            <option value="DESPESA_OPERACIONAL">Despesa Operacional Geral</option>
            <option value="FOLHA_PAGAMENTO">Folha de Pagamento / Encargos</option>
            <option value="ENERGIA_ALUGUEL">Energia, Água e Aluguel</option>
            <option value="IMPOSTOS">Impostos e Tributos</option>
            <option value="CMV_MERCADORIAS">Custo de Mercadorias (CMV)</option>
            <option value="RECEITA_VENDAS">Receita de Vendas</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Descrição *</label>
        <input type="text" id="fin-desc" required placeholder="Ex: Conta de Energia Elétrica Mês Atual" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Valor (R$) *</label>
          <input type="number" step="0.01" min="0.01" id="fin-valor" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Data de Competência</label>
          <input type="date" id="fin-data" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Registrar Lançamento</button>
    </form>
    `
  );
}

async function submeterNovoLancamento(e) {
  e.preventDefault();
  await apiFetch("/api/financeiro/lancamentos", {
    method: "POST",
    body: JSON.stringify({
      filial_id: Number(document.getElementById("fin-filial").value),
      tipo: document.getElementById("fin-tipo").value,
      categoria_dre: document.getElementById("fin-cat").value,
      descricao: document.getElementById("fin-desc").value.trim(),
      valor: Number(document.getElementById("fin-valor").value),
      status: "PAGO",
      data_competencia: document.getElementById("fin-data").value || null,
    }),
  });
  fecharModal();
  notificar("Lançamento financeiro registrado.");
  await carregarModuloFinanceiro();
}

// ============================================================================
// APLICATIVO 7: Configurações, Unidades & Equipe
// ============================================================================
async function carregarModuloConfiguracoes() {
  const [empresa, filiais, usuarios, perfis] = await Promise.all([
    apiFetch("/api/empresa"),
    apiFetch("/api/filiais"),
    apiFetch("/api/usuarios"),
    apiFetch("/api/perfis-acesso"),
  ]);
  ESTADO.tenant = empresa;
  ESTADO.filiais = filiais;
  ESTADO.perfisDisponiveis = perfis;
  atualizarBarraSuperior();

  document.getElementById("cfg-dados-empresa").innerHTML = `
    <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
      <div class="flex justify-between"><span class="text-slate-500">Nome Fantasia:</span><strong class="text-slate-900">${empresa.nome_fantasia}</strong></div>
      <div class="flex justify-between"><span class="text-slate-500">Razão Social:</span><strong>${empresa.razao_social}</strong></div>
      <div class="flex justify-between"><span class="text-slate-500">CNPJ Matriz:</span><strong class="font-mono">${empresa.cnpj_matriz}</strong></div>
      <div class="flex justify-between"><span class="text-slate-500">Cidade / UF:</span><strong>${empresa.cidade_uf || "-"}</strong></div>
      <div class="flex justify-between"><span class="text-slate-500">Unidades Ativas:</span><strong>${empresa.total_filiais}</strong></div>
      <div class="flex justify-between"><span class="text-slate-500">Usuários na Equipe:</span><strong>${empresa.total_usuarios}</strong></div>
    </div>
  `;

  document.getElementById("cfg-lista-filiais").innerHTML = filiais
    .map(
      (f) => `
    <div class="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
      <div>
        <span class="font-bold text-slate-900">${f.codigo} — ${f.nome}</span>
        <span class="block text-[11px] text-slate-500">CNPJ: ${f.cnpj} • ${f.cidade} • Gerente: ${f.gerente}</span>
      </div>
      <span class="font-mono font-bold text-[#017E84]">Meta: ${moeda(f.meta_mensal)}</span>
    </div>
  `
    )
    .join("");

  document.getElementById("cfg-usuarios-tbody").innerHTML = usuarios
    .map(
      (u) => `
    <tr class="hover:bg-slate-50">
      <td class="py-3 px-4">
        <p class="font-bold text-slate-900">${u.nome}</p>
        <span class="font-mono text-[11px] text-slate-500">${u.email}</span>
      </td>
      <td class="py-3 px-4">${u.cargo}</td>
      <td class="py-3 px-4"><span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold">${u.perfil_rbac}</span></td>
      <td class="py-3 px-4">${u.filial_nome || "Todas as Unidades"}</td>
      <td class="py-3 px-4 text-[11px] text-slate-600">${(u.modulos_permitidos || []).join(", ")}</td>
    </tr>
  `
    )
    .join("");
}

function abrirModalNovaFilial() {
  abrirModal(
    "Cadastrar Nova Unidade / Filial da Empresa",
    `
    <form onsubmit="submeterNovaFilial(event)" class="space-y-3 text-xs">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Código da Unidade *</label>
          <input type="text" id="fil-codigo" required placeholder="Ex: LOJA-02" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono uppercase">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Tipo / Bandeira *</label>
          <input type="text" id="fil-bandeira" value="Supermercado" required class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Nome da Unidade *</label>
        <input type="text" id="fil-nome" required placeholder="Ex: Filial Centro" class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">CNPJ da Unidade *</label>
          <input type="text" id="fil-cnpj" required placeholder="00.000.000/0002-00" class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Cidade / UF *</label>
          <input type="text" id="fil-cidade" required class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Gerente Responsável *</label>
          <input type="text" id="fil-gerente" required class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Meta Mensal (R$) *</label>
          <input type="number" step="0.01" min="0" id="fil-meta" value="100000" required class="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono">
        </div>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Salvar Unidade</button>
    </form>
    `
  );
}

async function submeterNovaFilial(e) {
  e.preventDefault();
  await apiFetch("/api/filiais", {
    method: "POST",
    body: JSON.stringify({
      codigo: document.getElementById("fil-codigo").value.trim(),
      bandeira: document.getElementById("fil-bandeira").value.trim(),
      nome: document.getElementById("fil-nome").value.trim(),
      cnpj: document.getElementById("fil-cnpj").value.trim(),
      cidade: document.getElementById("fil-cidade").value.trim(),
      gerente: document.getElementById("fil-gerente").value.trim(),
      meta_mensal: Number(document.getElementById("fil-meta").value || 0),
      ativa: true,
    }),
  });
  fecharModal();
  notificar("Nova unidade cadastrada com sucesso.");
  await carregarModuloConfiguracoes();
}

function abrirModalNovoUsuario() {
  const opcoesPerfis = ESTADO.perfisDisponiveis
    .map(
      (p) =>
        `<option value="${p.codigo}">${p.nome} (${p.modulos_permitidos.join(", ")})</option>`
    )
    .join("");

  const opcoesFiliais = [
    `<option value="">Todas as Unidades da Empresa</option>`,
    ...ESTADO.filiais.map(
      (f) => `<option value="${f.id}">${f.codigo} — ${f.nome}</option>`
    ),
  ].join("");

  abrirModal(
    "Cadastrar Funcionário / Usuário da Empresa",
    `
    <form onsubmit="submeterNovoUsuario(event)" class="space-y-3 text-xs">
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Nome Completo do Funcionário *</label>
        <input type="text" id="usr-nome" required class="w-full px-3 py-2 rounded-lg border border-slate-300">
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">E-mail de Login *</label>
          <input type="email" id="usr-email" required placeholder="funcionario@empresa.com.br" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Senha de Acesso (mín. 6) *</label>
          <input type="password" id="usr-senha" required minlength="6" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Cargo / Função *</label>
          <input type="text" id="usr-cargo" required placeholder="Ex: Operador de Caixa" class="w-full px-3 py-2 rounded-lg border border-slate-300">
        </div>
        <div>
          <label class="block font-semibold text-slate-700 mb-1">Unidade Vinculada</label>
          <select id="usr-filial" class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesFiliais}</select>
        </div>
      </div>
      <div>
        <label class="block font-semibold text-slate-700 mb-1">Perfil de Permissões *</label>
        <select id="usr-perfil" required class="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white">${opcoesPerfis}</select>
      </div>
      <button type="submit" class="w-full py-2.5 rounded-lg bg-[#714B67] text-white font-bold">Criar Acesso do Funcionário</button>
    </form>
    `
  );
}

async function submeterNovoUsuario(e) {
  e.preventDefault();
  const filVal = document.getElementById("usr-filial").value;
  await apiFetch("/api/usuarios", {
    method: "POST",
    body: JSON.stringify({
      nome: document.getElementById("usr-nome").value.trim(),
      email: document.getElementById("usr-email").value.trim(),
      senha: document.getElementById("usr-senha").value,
      cargo: document.getElementById("usr-cargo").value.trim(),
      filial_id: filVal ? Number(filVal) : null,
      perfil_rbac: document.getElementById("usr-perfil").value,
      ativo: true,
    }),
  });
  fecharModal();
  notificar("Funcionário cadastrado com sucesso.");
  await carregarModuloConfiguracoes();
}

// ============================================================================
// Modal Genérico
// ============================================================================
function abrirModal(titulo, htmlCorpo) {
  document.getElementById("modal-titulo").textContent = titulo;
  document.getElementById("modal-corpo").innerHTML = htmlCorpo;
  document.getElementById("modal-overlay").classList.remove("hidden");
}

function fecharModal() {
  document.getElementById("modal-overlay").classList.add("hidden");
  document.getElementById("modal-corpo").innerHTML = "";
}

// ============================================================================
// Inicialização da Aplicação
// ============================================================================
document.addEventListener("DOMContentLoaded", async () => {
  // Listener de Login
  document
    .getElementById("form-login")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-submit-login");
      btn.disabled = true;
      try {
        const res = await apiFetch("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({
            email: document.getElementById("login-email").value.trim(),
            senha: document.getElementById("login-senha").value,
          }),
        });
        notificar(res.mensagem || "Login realizado com sucesso.");
        aplicarSessaoAutenticada(res);
      } catch (err) {
        notificar(err.message, "erro");
      } finally {
        btn.disabled = false;
      }
    });

  // Listener de Registro de Nova Empresa
  document
    .getElementById("form-registro-empresa")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btn-submit-registro");
      btn.disabled = true;
      try {
        const payload = {
          nome_fantasia: document
            .getElementById("reg-nome-fantasia")
            .value.trim(),
          razao_social: document
            .getElementById("reg-razao-social")
            .value.trim(),
          cnpj_matriz: document.getElementById("reg-cnpj").value.trim(),
          cidade_uf: document.getElementById("reg-cidade").value.trim(),
          telefone: document.getElementById("reg-telefone").value.trim(),
          meta_mensal_matriz: Number(
            document.getElementById("reg-meta").value || 150000
          ),
          admin_nome: document.getElementById("reg-admin-nome").value.trim(),
          admin_email: document.getElementById("reg-admin-email").value.trim(),
          admin_senha: document.getElementById("reg-admin-senha").value,
        };
        const res = await apiFetch("/api/auth/registrar-comercio", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        notificar(res.mensagem || "Conta da empresa criada com sucesso!");
        aplicarSessaoAutenticada(res);
      } catch (err) {
        notificar(err.message, "erro");
      } finally {
        btn.disabled = false;
      }
    });

  // Se houver token salvo, valida sessão automaticamente
  if (ESTADO.token) {
    try {
      const res = await apiFetch("/api/auth/me");
      aplicarSessaoAutenticada(res);
    } catch (_) {
      encerrarSessao(false);
    }
  }
});
