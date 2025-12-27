import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

# =====================================================
# CONFIGURAÇÃO
# =====================================================
st.set_page_config(page_title="Análise Financeira Estratégica", layout="wide")

st.title("📊 Análise Financeira Estratégica")
st.caption("Diagnóstico financeiro orientado à decisão executiva")

# =====================================================
# FUNÇÕES
# =====================================================
def plot_line_zero(df, x, y, title, y_label):
    fig = px.line(df, x=x, y=y, markers=True)
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title=title,
        title_x=0.5,
        height=280,
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis_title=None,
        yaxis_title=y_label
    )
    return fig


def calcular_score(resultado_medio, margem, cv):
    score = 100
    if resultado_medio < 0:
        score -= 40
    if margem < 10:
        score -= 20
    if cv > 1:
        score -= 20
    return max(score, 0)


def classificar(score):
    if score >= 80:
        return "Excelente"
    if score >= 60:
        return "Saudável"
    if score >= 40:
        return "Atenção"
    return "Crítico"

# =====================================================
# INPUT
# =====================================================
st.subheader("📋 Dados Financeiros")

with st.expander("📄 Tabela interativa (adicione quantos meses quiser)", expanded=True):
    base_df = pd.DataFrame({
        "Data": pd.date_range("2025-01-01", periods=12, freq="MS"),
        "Receita": [None]*12,
        "Despesa": [None]*12,
        "Retirada": [None]*12,
    })

    df_input = st.data_editor(
        base_df,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "Data": st.column_config.DateColumn("Mês", format="MM/YYYY"),
            "Receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
            "Despesa": st.column_config.NumberColumn("Despesa", format="R$ %.2f"),
            "Retirada": st.column_config.NumberColumn("Retirada", format="R$ %.2f"),
        }
    )

df = df_input.dropna().copy()
if df.empty:
    st.info("Preencha ao menos um mês completo.")
    st.stop()

df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

# =====================================================
# CÁLCULOS
# =====================================================
df["Resultado"] = df["Receita"] - df["Despesa"] - df["Retirada"]
df["Margem_%"] = (df["Resultado"] / df["Receita"]) * 100

media = df["Resultado"].mean()
vol = df["Resultado"].std()
cv = vol / abs(media) if media != 0 else np.inf

df["Media_hist"] = df["Resultado"].expanding().mean().shift(1)
df["Crescimento_%"] = (df["Resultado"] - df["Media_hist"]) / df["Media_hist"].abs() * 100

# =====================================================
# SCORE
# =====================================================
score = calcular_score(media, df["Margem_%"].mean(), cv)
status = classificar(score)

# =====================================================
# KPIs
# =====================================================
st.subheader("🎯 Visão Executiva")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Resultado Médio", f"R$ {media:,.2f}")
c2.metric("Margem Média", f"{df['Margem_%'].mean():.1f}%")
c3.metric("Volatilidade (CV)", f"{cv:.2f}")
c4.metric("Score Financeiro", f"{score} / 100")

st.progress(score / 100)

st.markdown(f"**Status Geral:** `{status}`")

# =====================================================
# DIAGNÓSTICO
# =====================================================
st.subheader("🧠 Diagnóstico Automático")

diagnosticos = []

if media < 0:
    diagnosticos.append("O negócio opera com prejuízo médio, indicando inviabilidade financeira atual.")
elif df["Margem_%"].mean() < 10:
    diagnosticos.append("O negócio é viável, porém opera com margens muito apertadas.")
else:
    diagnosticos.append("O negócio é financeiramente viável e lucrativo.")

if cv > 1:
    diagnosticos.append("Alta instabilidade nos resultados indica dependência de picos ou contratos pontuais.")

if df["Crescimento_%"].mean() > 0 and cv > 1:
    diagnosticos.append("O crescimento recente não é estrutural e carece de previsibilidade.")

for d in diagnosticos:
    st.markdown(f"- {d}")

# =====================================================
# RECOMENDAÇÕES
# =====================================================
st.subheader("🚀 Recomendações Acionáveis")

recs = []

if df["Margem_%"].mean() < 10:
    recs.append("Reavaliar precificação e estrutura de custos imediatamente.")

if cv > 1:
    recs.append("Buscar contratos recorrentes para reduzir volatilidade.")

if score >= 80:
    recs.append("Avaliar expansão controlada ou reinvestimento estratégico.")

for r in recs:
    st.markdown(f"- {r}")

# =====================================================
# GRÁFICOS – EVIDÊNCIAS VISUAIS (COMPACTOS)
# =====================================================
st.subheader("📈 Evidências Visuais")

g1, g2 = st.columns(2)

with g1:
    st.plotly_chart(
        plot_line_zero(
            df,
            "Data",
            "Resultado",
            "Resultado Líquido",
            "R$"
        ),
        width='stretch'
    )

with g2:
    fig_margem = px.line(
        df,
        x="Data",
        y="Margem_%",
        markers=True,
        title="Margem Líquida (%)"
    )
    fig_margem.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_margem.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis_title=None,
        yaxis_title="%"
    )
    st.plotly_chart(fig_margem, width='stretch')

g3, g4 = st.columns(2)

with g3:
    st.plotly_chart(
        plot_line_zero(
            df,
            "Data",
            "Crescimento_%",
            "Crescimento vs Média Histórica",
            "%"
        ),
        width='stretch'
    )

with g4:
    df["Custo_Total"] = df["Despesa"] + df["Retirada"]

    fig_fluxo = px.line(
        df,
        x="Data",
        y=["Receita", "Custo_Total"],
        markers=True,
        title="Receita vs Custos"
    )
    fig_fluxo.update_layout(
        height=280,
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis_title=None,
        yaxis_title="R$"
    )
    st.plotly_chart(fig_fluxo, width='stretch')

# =====================================================
# TABELA FINAL
# =====================================================
with st.expander("📄 Tabela Analítica Final"):
    st.dataframe(df, width='stretch')
