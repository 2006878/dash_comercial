import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =============================
# CONFIG / BRANDING
# =============================
st.set_page_config(
    page_title="Executive Performance Analyzer",
    layout="wide"
)

st.title("📊 Executive Performance Analyzer")
st.caption("Diagnóstico automático de eficiência, crescimento e risco operacional")

# =============================
# TEMPLATE
# =============================
def gerar_template(meses=6):
    base = datetime.now() - timedelta(days=30 * meses)
    datas = [base + timedelta(days=30*i) for i in range(meses)]

    np.random.seed(42)
    atendidos = np.random.randint(200, 400, meses)
    conversao = np.random.uniform(0.15, 0.35, meses)
    fechados = (atendidos * conversao).astype(int)

    ticket = np.random.normal(800, 120, meses)
    receita = (fechados * ticket).astype(int)
    despesas = (receita * np.random.uniform(0.6, 0.78, meses)).astype(int)

    return pd.DataFrame({
        "Data": pd.to_datetime(datas),
        "Clientes Atendidos": atendidos,
        "Clientes Fechados": fechados,
        "Receita": receita,
        "Despesas": despesas,
    })

def df_to_csv(df):
    return df.to_csv(index=False).encode("utf-8")

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.header("⚙️ Dados")
    uploaded = st.file_uploader(
        "Upload CSV / XLSX",
        type=["csv", "xlsx"]
    )

    st.markdown("---")
    st.subheader("📥 Template")
    meses = st.slider("Período (meses)", 3, 24, 6)

    if st.button("Baixar template"):
        df_template = gerar_template(meses)
        st.download_button(
            "Download CSV",
            df_to_csv(df_template),
            file_name="template_performance.csv",
            mime="text/csv"
        )

# =============================
# LOAD DATA
# =============================
if not uploaded:
    st.info("Faça upload de um arquivo ou utilize o template para começar.")
    st.stop()

df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)

# =============================
# VALIDATION (SILENCIOSA)
# =============================
required_cols = {
    "Data",
    "Clientes Atendidos",
    "Clientes Fechados",
    "Receita",
    "Despesas"
}

if not required_cols.issubset(df.columns):
    st.error("Arquivo fora do padrão esperado.")
    st.stop()

df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

# =============================
# FILTRO DE PERÍODO
# =============================
min_date = df["Data"].min().date()
max_date = df["Data"].max().date()

with st.sidebar:
    st.subheader("📅 Período de Análise")

    periodo = st.date_input(
        "Selecione o intervalo",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

# Proteção contra seleção inválida
if isinstance(periodo, tuple) and len(periodo) == 2:
    inicio, fim = periodo
else:
    inicio, fim = min_date, max_date

df = df[
    (df["Data"].dt.date >= inicio) &
    (df["Data"].dt.date <= fim)
]

if df.empty:
    st.warning("Nenhum dado disponível para o período selecionado.")
    st.stop()

# =============================
# METRICS
# =============================
df["Ticket Médio"] = (df["Receita"] / df["Clientes Fechados"]).round(2)
df["Lucro"] = df["Receita"] - df["Despesas"]
df["Margem %"] = (df["Lucro"] / df["Receita"] * 100).round(2)
df["Taxa Conversão %"] = (
    df["Clientes Fechados"] / df["Clientes Atendidos"] * 100
).round(2)

# =============================
# EXECUTIVE CARDS
# =============================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Receita Total", f"R$ {df['Receita'].sum():,.0f}")
col2.metric("Margem Média", f"{df['Margem %'].mean():.1f}%")
col3.metric("Conversão Média", f"{df['Taxa Conversão %'].mean():.1f}%")
col4.metric("Ticket Médio", f"R$ {df['Ticket Médio'].mean():,.0f}")

# =============================
# VISUALIZAÇÕES
# =============================
st.subheader("📈 Evolução Operacional e Financeira")

c1, c2 = st.columns(2)

with c1:
    st.line_chart(
        df.set_index("Data")[["Clientes Atendidos", "Clientes Fechados"]]
    )

with c2:
    st.line_chart(
        df.set_index("Data")[["Receita", "Lucro"]]
    )

st.line_chart(
    df.set_index("Data")[["Taxa Conversão %", "Margem %"]]
)

# =============================
# INSIGHTS (MOTOR DE DECISÃO)
# =============================
st.subheader("🧠 Insights Executivos")

crescimento = df["Receita"].pct_change().mean()
volatilidade = df["Receita"].std() / df["Receita"].mean()
margem_media = df["Margem %"].mean()

insights = []

if crescimento > 0 and volatilidade < 0.25 and margem_media > 20:
    insights.append("Crescimento consistente com boa eficiência operacional.")
elif crescimento > 0 and volatilidade >= 0.25:
    insights.append(
        "Receita em crescimento, porém com alta volatilidade. "
        "Indica risco operacional ou dependência de poucos contratos."
    )
else:
    insights.append(
        "Receita sem tendência clara de crescimento. "
        "Atenção à conversão ou ticket médio."
    )

if df["Taxa Conversão %"].mean() < 20:
    insights.append(
        "Baixa taxa de conversão: volume atendido não está se convertendo em receita."
    )

for i in insights:
    st.warning(i)

# =============================
# DADOS (COLAPSADO)
# =============================
with st.expander("📄 Ver dados carregados"):
    st.dataframe(df)

# =============================
# CTA PRODUTO
# =============================
st.markdown("---")
st.caption(
    "Este diagnóstico oferece uma visão executiva automatizada. "
    "Para análises personalizadas, relatórios recorrentes ou versão white-label, "
    "este produto pode ser customizado."
)
