import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
import tempfile
import re

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Análise Financeira Estratégica", layout="wide")
st.title("📊 Análise Financeira Estratégica – Visão Líquida")
st.caption("Diagnóstico financeiro e operacional orientado à decisão executiva.")

# =====================================================
# SESSÃO (persistência por usuário)
# =====================================================
if "historico" not in st.session_state:
    st.session_state.historico = []

# =====================================================
# FUNÇÕES UTILITÁRIAS
# =====================================================
def plot_line_zero(df, x, y, title, y_label):
    fig = px.line(df, x=x, y=y, markers=True, title=title)
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(xaxis_title="Período", yaxis_title=y_label)
    return fig


def sanitize(text):
    """Remove caracteres incompatíveis com latin-1 (FPDF)"""
    return re.sub(r"[^\x00-\xFF]", "", text)


def calcular_score(resultado_medio, margem, cv):
    if resultado_medio > 0 and margem >= 20 and cv < 0.5:
        return "A"
    if resultado_medio > 0 and margem >= 10 and cv < 1:
        return "B"
    if resultado_medio > 0:
        return "C"
    return "D"


def classificar_negocio(resultado_medio, crescimento, cv):
    if resultado_medio > 0 and crescimento > 0 and cv < 1:
        return "Em crescimento"
    if resultado_medio > 0 and cv <= 1:
        return "Estável"
    return "Em risco"


# =====================================================
# INPUT – TABELA INTERATIVA
# =====================================================
st.subheader("📋 Dados Financeiros")

with st.expander("📄 Tabela Interativa de Entrada", expanded=True):
    base_df = pd.DataFrame({
        "Data": pd.date_range("2024-01-01", periods=6, freq="MS"),
        "Receita": [None]*6,
        "Despesa": [None]*6,
        "Retirada": [None]*6,
        "Clientes_Atendidos": [None]*6,
        "Clientes_Fechados": [None]*6,
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
            "Clientes_Atendidos": st.column_config.NumberColumn("Atendidos"),
            "Clientes_Fechados": st.column_config.NumberColumn("Fechados"),
        }
    )

# =====================================================
# VALIDAÇÃO
# =====================================================
df = df_input.dropna(subset=["Data", "Receita", "Despesa", "Retirada"]).copy()
if df.empty:
    st.info("Preencha ao menos um mês completo.")
    st.stop()

df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

# =====================================================
# CÁLCULOS FINANCEIROS
# =====================================================
df["Resultado_liquido"] = df["Receita"] - df["Despesa"] - df["Retirada"]
df["Margem_liquida_%"] = (df["Resultado_liquido"] / df["Receita"]) * 100
df["Eficiencia_custo_%"] = ((df["Despesa"] + df["Retirada"]) / df["Receita"]) * 100

df["Media_resultado_historica"] = df["Resultado_liquido"].expanding().mean().shift(1)
df["Crescimento_vs_media_%"] = (
    (df["Resultado_liquido"] - df["Media_resultado_historica"])
    / df["Media_resultado_historica"].abs()
) * 100

# =====================================================
# MÉTRICAS GLOBAIS
# =====================================================
resultado_medio = df["Resultado_liquido"].mean()
volatilidade = df["Resultado_liquido"].std()
coef_var = volatilidade / abs(resultado_medio) if resultado_medio != 0 else np.inf
margem_media = df["Margem_liquida_%"].mean()
crescimento_medio = df["Crescimento_vs_media_%"].mean()

score = calcular_score(resultado_medio, margem_media, coef_var)
classificacao = classificar_negocio(resultado_medio, crescimento_medio, coef_var)

# =====================================================
# SAZONALIDADE
# =====================================================
df["Mes"] = df["Data"].dt.month
sazonal = df.groupby("Mes")["Resultado_liquido"].mean()
mes_pico = sazonal.idxmax()
mes_fraco = sazonal.idxmin()

# =====================================================
# COMPARATIVO ÚLTIMO VS MELHOR MÊS
# =====================================================
melhor_mes = df.loc[df["Resultado_liquido"].idxmax()]
ultimo_mes = df.iloc[-1]

delta_melhor = (
    (ultimo_mes["Resultado_liquido"] - melhor_mes["Resultado_liquido"])
    / abs(melhor_mes["Resultado_liquido"])
) * 100

# =====================================================
# KPIs
# =====================================================
st.subheader("📌 Indicadores Executivos")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Resultado Total", f"R$ {df['Resultado_liquido'].sum():,.2f}")
c2.metric("📆 Média Mensal", f"R$ {resultado_medio:,.2f}")
c3.metric("📈 Margem Média", f"{margem_media:.1f}%")
c4.metric("📊 Score Financeiro", score)
c5.metric("🧭 Classificação", classificacao)

# =====================================================
# GRÁFICOS
# =====================================================
st.subheader("📈 Resultado Líquido Mensal")
st.plotly_chart(plot_line_zero(df, "Data", "Resultado_liquido", "Resultado Líquido", "R$"), True)

st.subheader("📊 Margem e Eficiência")
fig = px.line(df, x="Data", y=["Margem_liquida_%", "Eficiencia_custo_%"], markers=True)
fig.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(fig, True)

st.subheader("📉 Crescimento vs Média Histórica")
st.plotly_chart(plot_line_zero(df, "Data", "Crescimento_vs_media_%", "Crescimento", "%"), True)

# =====================================================
# INSIGHTS ESTRATÉGICOS (CONSISTENTES)
# =====================================================
st.subheader("🧠 Insights Estratégicos")

eh_lucrativo = resultado_medio > 0
margem_alta = margem_media >= 20
cresce = crescimento_medio > 0
volatil_alta = coef_var > 1
queda_recente_forte = delta_melhor <= -30

insights_ui = []
insights_pdf = []

# Diagnóstico principal (único)
if eh_lucrativo and margem_alta and volatil_alta:
    txt = (
        "O negócio é financeiramente viável e eficiente, porém apresenta instabilidade relevante. "
        "A lucratividade parece concentrada em poucos períodos ou contratos."
    )
    insights_ui.append("🟡 " + txt)
    insights_pdf.append(txt)

elif eh_lucrativo and margem_alta:
    txt = "O negócio apresenta boa saúde financeira, com lucratividade consistente e eficiência operacional."
    insights_ui.append("🟢 " + txt)
    insights_pdf.append(txt)

elif eh_lucrativo:
    txt = "O negócio é viável, porém com margens limitadas, exigindo maior controle de custos."
    insights_ui.append("🟠 " + txt)
    insights_pdf.append(txt)

else:
    txt = "O negócio apresenta prejuízo médio, indicando inviabilidade financeira no formato atual."
    insights_ui.append("🔴 " + txt)
    insights_pdf.append(txt)

# Crescimento
if cresce:
    if volatil_alta:
        txt = (
            "Apesar do crescimento recente, o avanço ocorre de forma irregular, "
            "indicando crescimento não estrutural."
        )
    else:
        txt = "O resultado cresce de forma consistente acima da média histórica."
else:
    txt = "O resultado recente está abaixo da média histórica, indicando desaceleração."

insights_ui.append("📈 " + txt if cresce else "📉 " + txt)
insights_pdf.append(txt)

# Queda recente
if queda_recente_forte:
    txt = (
        "O último mês apresentou desempenho muito inferior ao melhor período histórico, "
        "o que pode indicar sazonalidade negativa ou ruptura operacional."
    )
    insights_ui.append("⚠️ " + txt)
    insights_pdf.append(txt)

# Sazonalidade
txt = (
    f"Foi identificada sazonalidade: melhor desempenho médio no mês {mes_pico} "
    f"e pior no mês {mes_fraco}."
)
insights_ui.append("📆 " + txt)
insights_pdf.append(txt)

# Render UI
for i in insights_ui:
    st.markdown(f"- {i}")

# =====================================================
# RECOMENDAÇÕES ESTRATÉGICAS
# =====================================================
st.subheader("🎯 Recomendações Estratégicas")

if classificacao == "Em crescimento":
    st.success("Foque em escalabilidade, previsibilidade comercial e retenção.")
elif classificacao == "Estável":
    st.info("Priorize eficiência operacional e redução de volatilidade.")
else:
    st.error("Recomenda-se revisão urgente de custos e modelo comercial.")

# =====================================================
# RELATÓRIO PDF EXECUTIVO (CLEAN)
# =====================================================
st.subheader("📄 Relatório Executivo")

if st.button("📥 Gerar Relatório PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    pdf.cell(0, 8, "Relatório Executivo de Análise Financeira", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, "Insights Estratégicos", ln=True)

    pdf.set_font("Arial", size=10)
    for i in insights_pdf:
        pdf.multi_cell(0, 6, f"- {sanitize(i)}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        st.download_button(
            "⬇️ Baixar PDF",
            open(tmp.name, "rb"),
            file_name="relatorio_financeiro_estrategico.pdf"
        )

# =====================================================
# TABELA FINAL
# =====================================================
with st.expander("📄 Tabela Analítica Final"):
    st.dataframe(df, width='stretch')
