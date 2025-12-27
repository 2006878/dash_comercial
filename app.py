import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(page_title="Análise Financeira Estratégica", layout="wide")

# =====================================================
# WHITE-LABEL
# =====================================================
st.sidebar.header("🧩 White-label")

logo_cliente = st.sidebar.file_uploader(
    "Logo do Cliente", type=["png", "jpg", "jpeg"]
)

cor_primaria = st.sidebar.color_picker("Cor primária", "#1f77b4")
cor_secundaria = st.sidebar.color_picker("Cor secundária", "#ff7f0e")

# =====================================================
# HEADER
# =====================================================
col_logo, col_title = st.columns([1, 5])

with col_logo:
    if logo_cliente:
        st.image(logo_cliente, width=210)

with col_title:
    st.title("📊 Análise Financeira Estratégica")
    st.caption("Diagnóstico financeiro e operacional orientado à decisão executiva.")

# =====================================================
# FUNÇÕES
# =====================================================
def plot_line_zero(df, x, y, title, y_label, color):
    fig = px.line(
        df,
        x=x,
        y=y,
        markers=True,
        color_discrete_sequence=[color],
        title=title
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_layout(
        height=260,
        margin=dict(l=30, r=30, t=40, b=30),
        xaxis_title=None,
        yaxis_title=y_label,
        title_x=0.5
    )
    return fig


def calcular_score(resultado, margem, cv):
    if resultado > 0 and margem >= 20 and cv < 0.5:
        return "A"
    if resultado > 0 and margem >= 10 and cv < 1:
        return "B"
    if resultado > 0:
        return "C"
    return "D"


def classificar_negocio(resultado, crescimento, cv):
    if resultado > 0 and crescimento > 0 and cv < 1:
        return "Em crescimento Saudável"
    if resultado > 0 and crescimento > 0 and cv >= 1:
        return "Em crescimento Instável"
    return "Em risco"


def gerar_narrativa(resultado, margem, cv, crescimento, delta):
    narrativa = []

    if resultado > 0:
        narrativa.append("O negócio apresenta resultado líquido médio positivo, indicando viabilidade financeira.")
    else:
        narrativa.append("O negócio opera com resultado líquido médio negativo, indicando fragilidade financeira.")

    if margem >= 20:
        narrativa.append("As margens são elevadas, refletindo alta eficiência operacional.")
    elif margem >= 10:
        narrativa.append("As margens são moderadas, com espaço para otimização.")
    else:
        narrativa.append("As margens são baixas, pressionando a rentabilidade.")

    if cv > 1:
        narrativa.append("Existe alta volatilidade nos resultados, reduzindo previsibilidade de caixa.")
    else:
        narrativa.append("Os resultados são relativamente estáveis ao longo do tempo.")

    if crescimento > 0:
        narrativa.append("O desempenho recente supera a média histórica, indicando tendência positiva.")
    else:
        narrativa.append("O desempenho recente está abaixo da média histórica, indicando desaceleração.")

    if delta <= -30:
        narrativa.append(
            "O último mês apresentou desempenho significativamente inferior ao melhor período histórico, "
            "indicando possível sazonalidade negativa ou ruptura pontual."
        )

    return narrativa


# =====================================================
# INPUT — TABELA FLEXÍVEL
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
        use_container_width=True,
        column_config={
            "Data": st.column_config.DateColumn("Mês", format="MM/YYYY"),
            "Receita": st.column_config.NumberColumn("Receita", format="R$ %.2f"),
            "Despesa": st.column_config.NumberColumn("Despesa", format="R$ %.2f"),
            "Retirada": st.column_config.NumberColumn("Retirada", format="R$ %.2f"),
        }
    )

# =====================================================
# VALIDAÇÃO
# =====================================================
df = df_input.dropna().copy()

if df.empty:
    st.info("Preencha ao menos um mês completo.")
    st.stop()

df["Data"] = pd.to_datetime(df["Data"])
df = df.sort_values("Data")

# =====================================================
# CÁLCULOS
# =====================================================
df["Resultado_liquido"] = df["Receita"] - df["Despesa"] - df["Retirada"]
df["Margem_liquida_%"] = (df["Resultado_liquido"] / df["Receita"]) * 100
df["Eficiencia_custo_%"] = ((df["Despesa"] + df["Retirada"]) / df["Receita"]) * 100

df["Media_historica"] = df["Resultado_liquido"].expanding().mean().shift(1)
df["Crescimento_vs_media_%"] = (
    (df["Resultado_liquido"] - df["Media_historica"]) /
    df["Media_historica"].abs()
) * 100

# =====================================================
# MÉTRICAS GLOBAIS
# =====================================================
resultado_medio = df["Resultado_liquido"].mean()
margem_media = df["Margem_liquida_%"].mean()
crescimento_medio = df["Crescimento_vs_media_%"].mean()
volatilidade = df["Resultado_liquido"].std(ddof=1)
coef_var = (
    volatilidade / abs(resultado_medio)
    if abs(resultado_medio) > 1e-6
    else np.inf
)

score = calcular_score(resultado_medio, margem_media, coef_var)
classificacao = classificar_negocio(resultado_medio, crescimento_medio, coef_var)

melhor_mes = df.loc[df["Resultado_liquido"].idxmax()]
ultimo_mes = df.iloc[-1]
delta_melhor = (
    (ultimo_mes["Resultado_liquido"] - melhor_mes["Resultado_liquido"]) /
    abs(melhor_mes["Resultado_liquido"])
) * 100

# =====================================================
# KPIs — SCORE VISUAL
# =====================================================
st.subheader("📌 Diagnóstico Executivo")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Resultado Médio", f"R$ {resultado_medio:,.2f}")
c2.metric("Margem Média", f"{margem_media:.1f}%")
c3.metric("Score Financeiro", score)
c4.metric("Classificação", classificacao)

# =====================================================
# GRÁFICOS (MESMA PROPORÇÃO)
# =====================================================
g1, g2, g3 = st.columns(3)

with g1:
    st.plotly_chart(
        plot_line_zero(df, "Data", "Resultado_liquido", "Resultado Líquido", "R$", cor_primaria),
        use_container_width=True
    )

with g2:
    fig = px.line(
        df,
        x="Data",
        y=["Margem_liquida_%", "Eficiencia_custo_%"],
        markers=True,
        color_discrete_sequence=[cor_primaria, cor_secundaria]
    )
    fig.update_layout(height=260, margin=dict(l=30, r=30, t=40, b=30), title="Margem & Eficiência")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

with g3:
    st.plotly_chart(
        plot_line_zero(df, "Data", "Crescimento_vs_media_%", "Crescimento vs Média", "%", cor_secundaria),
        use_container_width=True
    )

# =====================================================
# NARRATIVA EXECUTIVA AUTOMÁTICA
# =====================================================
st.subheader("🧠 Insights Executivos")

narrativa = gerar_narrativa(
    resultado_medio,
    margem_media,
    coef_var,
    crescimento_medio,
    delta_melhor
)

for n in narrativa:
    st.markdown(f"- {n}")

# =====================================================
# RECOMENDAÇÕES ACIONÁVEIS
# =====================================================
st.subheader("🎯 Recomendações Estratégicas")

if classificacao == "Em crescimento Estável":
    st.success("Invista em escala, previsibilidade comercial e retenção de clientes.")
elif classificacao == "Em crescimento Instável":
    st.info("Priorize redução de volatilidade e ganho de eficiência operacional.")
else:
    st.error("Recomenda-se revisão imediata do modelo de custos e estratégia comercial.")

# =====================================================
# TABELA FINAL
# =====================================================
with st.expander("📄 Tabela Analítica Final"):
    st.dataframe(df, use_container_width=True)
