# -*- coding: utf-8 -*-
"""
Dashboard – Renato Oliveira Móveis Planejados
Sem tela de login. Abre direto no painel principal.
Tema: Laranja / Preto / Branco.
"""

import glob
import os

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Configuração geral
# ---------------------------------------------------------------------------
ARQUIVO_PADRAO = "Agenda de Entregas Renato Oliveira Móveis Planejados.xlsx"
LOGO = "logo.png"


def encontrar_planilha() -> str:
    """Localiza a planilha mesmo que o nome varie um pouco (acentos/espaços)."""
    if os.path.exists(ARQUIVO_PADRAO):
        return ARQUIVO_PADRAO
    candidatos = [f for f in glob.glob("*.xlsx") if "agenda" in f.lower()]
    if candidatos:
        return candidatos[0]
    return ARQUIVO_PADRAO


ARQUIVO = encontrar_planilha()

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
        .stButton>button {{
            background: {LARANJA}; color: {BRANCO}; border: 0;
            border-radius: 10px; font-weight: 700; padding: 8px 18px;
        }}
        .stButton>button:hover {{ background: #ff8533; color: {BRANCO}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def moeda(valor: float) -> str:
    """Formata número no padrão R$ brasileiro."""
    try:
        return ("R$ {:,.2f}".format(float(valor))
                .replace(",", "X").replace(".", ",").replace("X", "."))
    except (ValueError, TypeError):
        return "R$ 0,00"


def carregar_dados() -> pd.DataFrame:
    df = pd.read_excel(ARQUIVO)
    # Tipagem segura
    df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors="coerce")
    for c in (COL_TOTAL, COL_ENTRADA, COL_POS):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def esta_concluida(serie: pd.Series) -> pd.Series:
    s = serie.astype(str).str.strip().str.lower()
    return s.isin(["sim", "s", "true", "1"])


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

if not os.path.exists(LOGO):
    st.info("💡 Coloque um arquivo **logo.png** nesta pasta para exibir a logomarca no topo.")

st.divider()

# ---------------------------------------------------------------------------
# Carrega dados
# ---------------------------------------------------------------------------
if not os.path.exists(ARQUIVO):
    st.error(f"Arquivo não encontrado: {ARQUIVO}")
    st.stop()

df = carregar_dados()

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
# Tabela interativa + edição / inclusão de linhas
# ---------------------------------------------------------------------------
st.subheader("📝 Tabela de Clientes (editar / adicionar)")
st.caption("Edite as células direto na tabela, use a última linha vazia para adicionar "
           "um novo cliente e clique em **Salvar alterações**.")

editado = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
    column_config={
        COL_TOTAL:   st.column_config.NumberColumn("Valor Total do Serviço", format="R$ %.2f"),
        COL_ENTRADA: st.column_config.NumberColumn("Valor da Entrada", format="R$ %.2f"),
        COL_POS:     st.column_config.NumberColumn(
            "Valor Pós Obra Concluída", format="R$ %.2f",
            help="Calculado automaticamente (Total − Entrada) ao salvar.", disabled=True),
        COL_DATA:    st.column_config.DateColumn("Data Final para Entrega", format="DD/MM/YYYY"),
        COL_CONCLUIDA: st.column_config.SelectboxColumn(
            "Obra foi Concluída", options=["Sim", "Não"]),
        COL_PAGOU:   st.column_config.SelectboxColumn("Pagou Entrada", options=["Sim", "Não"]),
        COL_PARCELOU: st.column_config.SelectboxColumn("Parcelou Restante?", options=["Sim", "Não"]),
    },
)

if st.button("💾 Salvar alterações"):
    salvar = editado.copy()
    # Recalcula o saldo pós-obra para manter consistência
    salvar[COL_POS] = (pd.to_numeric(salvar[COL_TOTAL], errors="coerce").fillna(0)
                       - pd.to_numeric(salvar[COL_ENTRADA], errors="coerce").fillna(0))
    salvar[COL_DATA] = pd.to_datetime(salvar[COL_DATA], errors="coerce")
    salvar.to_excel(ARQUIVO, index=False)
    st.success("✅ Dados salvos na planilha com sucesso!")
    st.rerun()
