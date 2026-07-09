# -*- coding: utf-8 -*-
"""
Dashboard – Renato Oliveira Móveis Planejados
Lê os dados ao vivo de uma Planilha Google (somente leitura).
A edição é feita direto na Planilha Google. Sem tela de login.
Tema: Laranja / Preto / Branco.
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Fonte de dados – Planilha Google
# ---------------------------------------------------------------------------
SHEET_ID  = "1NGap2QQUv5MbvqQrD5AlFR8nWsmxHnZ_DYHgdFQ8mV0"
CSV_URL   = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
EDIT_URL  = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

LOGO = "logo.png"

# Nomes das colunas exatamente como estão na planilha
COL_CLIENTE   = "Cliente"
COL_NUM       = "Número do Serviço"
COL_TOTAL     = "Valor Total do Serviço"
COL_PAGOU     = "Pagou Entrada"
COL_ENTRADA   = "Valor da Entrada"
COL_CONCLUIDA = "Obra foi Concluída"
COL_POS       = "Valor Pós Obra Concluída"
COL_PARCELOU  = "Parcelou Restante?"
COL_PARCELAS  = "Parcelou em quantas vezes"
COL_DATA      = "Data Final para Entrega"

# Paleta do tema
LARANJA = "#FF6B00"
PRETO   = "#0F0F0F"
CINZA   = "#1C1C1C"
BRANCO  = "#FFFFFF"

st.set_page_config(
    page_title="Renato Oliveira • Móveis Planejados",
    page_icon=LOGO if os.path.exists(LOGO) else "🪚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# PWA – manifest, ícone e cor de tema, para instalar como app no celular
# ---------------------------------------------------------------------------
st.iframe(
    """
    <script>
    (function () {
        const doc = window.parent.document;
        const head = doc.querySelector('head');
        function addTag(tag, attrs) {
            const selector = tag + Object.entries(attrs)
                .map(([k, v]) => `[${k}="${v}"]`).join('');
            if (head.querySelector(selector)) return;
            const el = doc.createElement(tag);
            Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
            head.appendChild(el);
        }
        addTag('link', {rel: 'manifest', href: 'app/static/manifest.json'});
        addTag('link', {rel: 'apple-touch-icon', href: 'app/static/icon-192.png'});
        addTag('meta', {name: 'theme-color', content: '#0F0F0F'});
        addTag('meta', {name: 'apple-mobile-web-app-capable', content: 'yes'});
        addTag('meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent'});
        addTag('meta', {name: 'apple-mobile-web-app-title', content: 'Renato Oliveira'});
    })();
    </script>
    """,
    height=1,
)

# ---------------------------------------------------------------------------
# Estilo (CSS) – fundo escuro, destaques em laranja
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {PRETO}; color: {BRANCO}; }}
        h1, h2, h3, h4 {{ color: {BRANCO}; }}
        .kpi-card {{
            background: {CINZA};
            border-radius: 16px;
            padding: 22px 18px;
            border-left: 6px solid {LARANJA};
            box-shadow: 0 4px 14px rgba(0,0,0,.45);
        }}
        .kpi-titulo {{ font-size: 0.95rem; color: #BBBBBB; margin-bottom: 6px; }}
        .kpi-valor  {{ font-size: 1.7rem; font-weight: 800; color: {LARANJA}; }}
        .montagem-card {{
            background: {CINZA};
            border: 1px solid #333;
            border-left: 6px solid {LARANJA};
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 10px;
        }}
        .stButton>button, .stLinkButton>a {{
            background: {LARANJA}; color: {BRANCO}; border: 0;
            border-radius: 10px; font-weight: 700; padding: 8px 18px;
        }}
        .stButton>button:hover, .stLinkButton>a:hover {{ background: #ff8533; color: {BRANCO}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def moeda(valor: float) -> str:
    """Formata número no padrão R$ brasileiro. Oculta se o usuário não pediu para exibir."""
    if not st.session_state.get("valores_visiveis", False):
        return "R$ ••••••"
    try:
        return ("R$ {:,.2f}".format(float(valor))
                .replace(",", "X").replace(".", ",").replace("X", "."))
    except (ValueError, TypeError):
        return "R$ 0,00"


def texto_para_numero(serie: pd.Series) -> pd.Series:
    """Converte texto monetário ('R$ 31.200,00', 'R$ -') em número."""
    s = (serie.astype(str)
         .str.replace("R$", "", regex=False)
         .str.replace(" ", "", regex=False)
         .str.replace(".", "", regex=False)      # separador de milhar
         .str.replace(",", ".", regex=False))    # vírgula decimal -> ponto
    return pd.to_numeric(s, errors="coerce").fillna(0)


@st.cache_data(ttl=60)  # recarrega da planilha no máximo a cada 60s
def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]
    # Converte colunas de valores
    for c in (COL_TOTAL, COL_ENTRADA, COL_POS):
        if c in df.columns:
            df[c] = texto_para_numero(df[c])
    # Converte datas
    if COL_DATA in df.columns:
        df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors="coerce")
    return df


def esta_concluida(serie: pd.Series) -> pd.Series:
    s = serie.astype(str).str.strip().str.lower()
    return s.isin(["sim", "s", "true", "1"])


# ---------------------------------------------------------------------------
# Estado do "olho" – valores sempre começam ocultos ao abrir o app
# ---------------------------------------------------------------------------
if "valores_visiveis" not in st.session_state:
    st.session_state.valores_visiveis = False

# ---------------------------------------------------------------------------
# Cabeçalho + Logo
# ---------------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    if os.path.exists(LOGO):
        st.image(LOGO, use_container_width=True)
    else:
        st.markdown(f"<h2 style='color:{LARANJA};margin:0'>RO</h2>", unsafe_allow_html=True)
with col_titulo:
    st.markdown(
        f"<h1 style='margin-bottom:0'>Renato Oliveira "
        f"<span style='color:{LARANJA}'>Móveis Planejados</span></h1>"
        "<p style='color:#999;margin-top:4px'>Painel financeiro e cronograma de entregas</p>",
        unsafe_allow_html=True,
    )

st.divider()

# ---------------------------------------------------------------------------
# Carrega dados (com botão de atualizar)
# ---------------------------------------------------------------------------
top1, top2, top3 = st.columns([3, 1, 1])
with top2:
    rotulo_olho = "🙈 Ocultar valores" if st.session_state.valores_visiveis else "👁️ Mostrar valores"
    if st.button(rotulo_olho, use_container_width=True):
        st.session_state.valores_visiveis = not st.session_state.valores_visiveis
        st.rerun()
with top3:
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

try:
    df = carregar_dados()
except Exception as e:
    st.error("Não consegui ler a Planilha Google. Verifique se o link continua "
             "compartilhado como 'Qualquer pessoa com o link'.")
    st.caption(f"Detalhe técnico: {e}")
    st.stop()

if df.empty:
    st.warning("A planilha está vazia.")
    st.stop()

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_faturado = df[COL_TOTAL].sum()
total_entradas = df[COL_ENTRADA].sum()
saldo_pos      = df[COL_POS].sum()
concluidas     = int(esta_concluida(df[COL_CONCLUIDA]).sum())
pendentes      = int(len(df) - concluidas)


def kpi(col, titulo, valor):
    col.markdown(
        f"<div class='kpi-card'><div class='kpi-titulo'>{titulo}</div>"
        f"<div class='kpi-valor'>{valor}</div></div>",
        unsafe_allow_html=True,
    )


k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Total Faturado", moeda(total_faturado))
kpi(k2, "Total Recebido em Entradas", moeda(total_entradas))
kpi(k3, "Saldo Pós-Obra a Receber", moeda(saldo_pos))
kpi(k4, "Obras Concluídas vs. Pendentes", f"{concluidas} ✓  /  {pendentes} ⏳")

st.write("")

# ---------------------------------------------------------------------------
# Cronograma de entregas
# ---------------------------------------------------------------------------
st.subheader("📅 Cronograma de Entregas")

dfc = df.dropna(subset=[COL_DATA]).copy()
if dfc.empty:
    st.warning("Nenhuma data de entrega válida encontrada.")
else:
    hoje = pd.Timestamp.now().normalize()
    dfc["_ini"] = dfc[COL_DATA].apply(lambda d: min(hoje, d))
    dfc["_fim"] = dfc[COL_DATA].apply(lambda d: max(hoje, d))
    dfc["Status"] = dfc[COL_CONCLUIDA].apply(
        lambda v: "Concluída" if str(v).strip().lower() in ("sim", "s") else "Pendente"
    )
    dfc = dfc.sort_values(COL_DATA)

    fig = px.timeline(
        dfc,
        x_start="_ini",
        x_end="_fim",
        y=COL_CLIENTE,
        color="Status",
        color_discrete_map={"Pendente": LARANJA, "Concluída": "#5A5A5A"},
        hover_data={COL_DATA: "|%d/%m/%Y", "_ini": False, "_fim": False},
    )
    fig.update_yaxes(autorange="reversed", title="")
    fig.update_xaxes(title="")
    fig.add_vline(x=hoje, line_width=2, line_dash="dash", line_color=BRANCO)
    fig.update_layout(
        paper_bgcolor=PRETO,
        plot_bgcolor=CINZA,
        font_color=BRANCO,
        legend_title_text="",
        height=80 + 55 * len(dfc),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Lista de Montagem (obras pendentes)
# ---------------------------------------------------------------------------
st.subheader("🛠️ Lista de Montagem — Obras Pendentes")

pend = df[~esta_concluida(df[COL_CONCLUIDA])].copy()
if pend.empty:
    st.success("🎉 Todas as obras estão concluídas!")
else:
    cols = st.columns(min(3, len(pend)))
    for i, (_, linha) in enumerate(pend.iterrows()):
        data_txt = (linha[COL_DATA].strftime("%d/%m/%Y")
                    if pd.notna(linha[COL_DATA]) else "Sem data")
        with cols[i % len(cols)]:
            st.markdown(
                f"""
                <div class='montagem-card'>
                    <div style='font-size:1.15rem;font-weight:800;color:{LARANJA}'>
                        {linha[COL_CLIENTE]}</div>
                    <div style='color:#ccc;margin-top:4px'>📅 Entrega: <b>{data_txt}</b></div>
                    <div style='color:#ccc'>💰 A receber: <b>{moeda(linha[COL_POS])}</b></div>
                    <div style='color:#888;font-size:.85rem'>Serviço nº {linha[COL_NUM]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# ---------------------------------------------------------------------------
# Tabela (visualização) + botão para editar na Planilha Google
# ---------------------------------------------------------------------------
cab1, cab2 = st.columns([3, 1])
with cab1:
    st.subheader("📋 Dados dos Clientes")
with cab2:
    st.link_button("✏️ Editar na Planilha Google", EDIT_URL)

st.caption("Para adicionar ou alterar clientes, clique em **Editar na Planilha Google**. "
           "Depois volte aqui e clique em **🔄 Atualizar dados**.")

colunas_valor = (COL_TOTAL, COL_ENTRADA, COL_POS)
df_exibicao = df.copy()

col_config = {
    COL_DATA: st.column_config.DateColumn("Data Final para Entrega", format="DD/MM/YYYY"),
}
if st.session_state.valores_visiveis:
    col_config.update({
        COL_TOTAL:   st.column_config.NumberColumn("Valor Total do Serviço", format="R$ %.2f"),
        COL_ENTRADA: st.column_config.NumberColumn("Valor da Entrada", format="R$ %.2f"),
        COL_POS:     st.column_config.NumberColumn("Valor Pós Obra Concluída", format="R$ %.2f"),
    })
else:
    for c in colunas_valor:
        df_exibicao[c] = "R$ ••••••"
    col_config.update({
        COL_TOTAL:   st.column_config.TextColumn("Valor Total do Serviço"),
        COL_ENTRADA: st.column_config.TextColumn("Valor da Entrada"),
        COL_POS:     st.column_config.TextColumn("Valor Pós Obra Concluída"),
    })

st.dataframe(
    df_exibicao,
    use_container_width=True,
    hide_index=True,
    column_config=col_config,
)
