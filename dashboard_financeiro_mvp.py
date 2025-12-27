import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# ========== CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Dashboard Financeiro MVP | Análise de Negócio",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== TEMA E CORES ==========
COLORS = {
    "bg_main": "#0F172A",
    "bg_card": "#111827",
    "bg_hover": "#1F2937",
    "border": "#1F2937",
    "primary": "#3B82F6",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text_primary": "#F9FAFB",
    "text_secondary": "#D1D5DB",
    "text_muted": "#9CA3AF",
}

st.markdown(f"""
<style>
    * {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}

    .main {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['text_primary']};
    }}

    [data-testid="stSidebar"] {{
        background-color: {COLORS['bg_card']};
    }}

    [data-testid="stMetric"] {{
        background-color: {COLORS['bg_card']};
        padding: 16px;
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
    }}

    .metric-card {{
        background: linear-gradient(135deg, {COLORS['bg_card']} 0%, {COLORS['bg_hover']} 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid {COLORS['border']};
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        transition: all 0.3s ease;
    }}

    .metric-card:hover {{
        border-color: {COLORS['primary']};
        box-shadow: 0 12px 32px rgba(59, 130, 246, 0.15);
        transform: translateY(-2px);
    }}

    .metric-label {{
        font-size: 0.75rem;
        font-weight: 600;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 8px;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        line-height: 1.2;
    }}

    .metric-change {{
        font-size: 0.85rem;
        margin-top: 8px;
    }}

    .metric-change.positive {{
        color: {COLORS['success']};
    }}

    .metric-change.negative {{
        color: {COLORS['danger']};
    }}

    .metric-change.neutral {{
        color: {COLORS['text_muted']};
    }}

    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin: 20px 0 12px 0;
        border-bottom: 2px solid {COLORS['primary']};
        padding-bottom: 8px;
    }}

    .section-subtitle {{
        font-size: 0.85rem;
        color: {COLORS['text_muted']};
        margin: 0 0 16px 0;
    }}

    .insight-box {{
        background-color: {COLORS['bg_card']};
        border-left: 4px solid {COLORS['primary']};
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }}

    .insight-good {{
        border-left-color: {COLORS['success']};
    }}

    .insight-warning {{
        border-left-color: {COLORS['warning']};
    }}

    .dataframe {{
        font-size: 0.9rem;
    }}

    .header-title {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, #2563EB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
</style>
""", unsafe_allow_html=True)

# ========== GERAÇÃO DE DADOS REALISTAS ==========
def gerar_dados_vendas(meses_back=6):
    """Gera dados simulados realistas de vendas com padrões de negócio."""
    data_inicio = datetime.now() - timedelta(days=30 * meses_back)
    datas = [data_inicio + timedelta(days=30*i) for i in range(meses_back)]
    meses = [d.strftime("%b") for d in datas]

    np.random.seed(42)

    # Padrão de crescimento com sazonalidade
    base_leads = 400
    trend = np.linspace(0, 200, meses_back)
    sazonalidade = 50 * np.sin(np.arange(meses_back) * np.pi / 3)
    leads = (base_leads + trend + sazonalidade + np.random.normal(0, 40, meses_back)).astype(int)
    leads = np.maximum(leads, 150)

    # Taxa de conversão melhora com otimizações
    conv_base = 0.12
    conv_improvement = np.linspace(0, 0.06, meses_back)
    conversao = (conv_base + conv_improvement + np.random.normal(0, 0.02, meses_back))
    conversao = np.clip(conversao, 0.08, 0.25)

    clientes = (leads * conversao).astype(int)

    # Ticket médio com variação realista
    ticket_base = 650
    ticket_trend = np.linspace(0, 150, meses_back)
    ticket = ticket_base + ticket_trend + np.random.normal(0, 50, meses_back)
    ticket = np.maximum(ticket, 400)

    receita = (clientes * ticket).astype(int)

    # Padrão de retenção melhorando
    perc_recorrentes = np.linspace(0.20, 0.42, meses_back)
    clientes_recorrentes = (clientes * perc_recorrentes).astype(int)
    clientes_novos = clientes - clientes_recorrentes

    # Taxa de churn reduzindo
    churn_rate = np.linspace(0.15, 0.08, meses_back)

    df = pd.DataFrame({
        "Mês": meses,
        "Data": datas,
        "Leads": leads,
        "Clientes": clientes,
        "Clientes Novos": clientes_novos,
        "Clientes Recorrentes": clientes_recorrentes,
        "Receita": receita.astype(int),
        "Ticket Médio": (receita / clientes).astype(int),
        "Conversão (%)": (conversao * 100).round(2),
        "Churn (%)": (churn_rate * 100).round(2),
    })

    return df

# ========== CÁLCULO DE MÉTRICAS ==========
def calcular_metricas(df):
    """Calcula KPIs principais e variações."""
    ultima_linha = len(df) - 1
    penultima_linha = ultima_linha - 1

    receita_total = df["Receita"].sum()
    clientes_total = df["Clientes"].sum()
    ticket_medio = df["Ticket Médio"].mean()
    conversao_media = df["Conversão (%)"].mean()

    # Variações
    rec_var = ((df.iloc[ultima_linha]["Receita"] - df.iloc[penultima_linha]["Receita"]) 
               / df.iloc[penultima_linha]["Receita"]) * 100
    cli_var = ((df.iloc[ultima_linha]["Clientes"] - df.iloc[penultima_linha]["Clientes"]) 
               / df.iloc[penultima_linha]["Clientes"]) * 100
    conv_var = df.iloc[ultima_linha]["Conversão (%)"] - df.iloc[penultima_linha]["Conversão (%)"]
    churn_var = df.iloc[ultima_linha]["Churn (%)"] - df.iloc[penultima_linha]["Churn (%)"]

    retenção_media = 100 - df["Churn (%)"].mean()

    return {
        "receita_total": receita_total,
        "clientes_total": clientes_total,
        "ticket_medio": ticket_medio,
        "conversao_media": conversao_media,
        "rec_var": rec_var,
        "cli_var": cli_var,
        "conv_var": conv_var,
        "churn_var": churn_var,
        "retenção_media": retenção_media,
    }

# ========== GRÁFICOS AVANÇADOS ==========
def criar_grafico_receita_clientes(df):
    """Gráfico dual-axis: Receita e Clientes ao longo do tempo."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Mês"],
        y=df["Receita"],
        name="Receita",
        yaxis="y1",
        mode="lines+markers",
        line=dict(color="#3B82F6", width=3),
        marker=dict(size=8, symbol="circle"),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.15)",
    ))

    fig.add_trace(go.Bar(
        x=df["Mês"],
        y=df["Clientes"],
        name="Clientes",
        yaxis="y2",
        marker=dict(color="rgba(16, 185, 129, 0.6)", line=dict(color="#10B981", width=2)),
        opacity=0.6,
    ))

    fig.update_layout(
        title="Receita & Clientes - Evolução Temporal",
        xaxis=dict(title="Mês", showgrid=True, gridwidth=1, gridcolor="rgba(31, 41, 55, 0.5)"),
        yaxis=dict(title="Receita (R$)", titlefont=dict(color="#3B82F6"), tickfont=dict(color="#3B82F6")),
        yaxis2=dict(
            title="Clientes",
            titlefont=dict(color="#10B981"),
            tickfont=dict(color="#10B981"),
            overlaying="y",
            side="right",
        ),
        hovermode="x unified",
        plot_bgcolor="#111827",
        paper_bgcolor="#0F172A",
        font=dict(color="#F9FAFB"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(17, 24, 39, 0.8)", bordercolor="#1F2937", borderwidth=1),
        margin=dict(l=70, r=70, t=80, b=70),
        height=400,
    )

    return fig

def criar_grafico_novos_recorrentes(df):
    """Área stacked: Novos vs Recorrentes."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Mês"],
        y=df["Clientes Novos"],
        name="Clientes Novos",
        mode="lines",
        line=dict(width=0.5, color="#3B82F6"),
        fillcolor="rgba(59, 130, 246, 0.4)",
        stackgroup="one",
    ))

    fig.add_trace(go.Scatter(
        x=df["Mês"],
        y=df["Clientes Recorrentes"],
        name="Clientes Recorrentes",
        mode="lines",
        line=dict(width=0.5, color="#10B981"),
        fillcolor="rgba(16, 185, 129, 0.4)",
        stackgroup="one",
    ))

    fig.update_layout(
        title="Composição de Clientes - Novos vs Recorrentes",
        xaxis=dict(title="Mês", showgrid=True, gridwidth=1, gridcolor="rgba(31, 41, 55, 0.5)"),
        yaxis=dict(title="Número de Clientes", showgrid=True, gridwidth=1, gridcolor="rgba(31, 41, 55, 0.5)"),
        hovermode="x unified",
        plot_bgcolor="#111827",
        paper_bgcolor="#0F172A",
        font=dict(color="#F9FAFB"),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(17, 24, 39, 0.8)", bordercolor="#1F2937", borderwidth=1),
        margin=dict(l=70, r=70, t=80, b=70),
        height=350,
    )

    return fig

def criar_grafico_conversao_churn(df):
    """Gráficos de Conversão e Churn em gauge ou linha."""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "scatter"}, {"type": "scatter"}]],
        subplot_titles=("Taxa de Conversão", "Taxa de Churn (Retenção)"),
    )

    fig.add_trace(
        go.Scatter(
            x=df["Mês"],
            y=df["Conversão (%)"],
            name="Conversão (%)",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=3),
            marker=dict(size=8),
        ),
        row=1, col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df["Mês"],
            y=100 - df["Churn (%)"],
            name="Retenção (%)",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
            marker=dict(size=8),
        ),
        row=1, col=2,
    )

    fig.update_xaxes(title_text="Mês", row=1, col=1, showgrid=True, gridcolor="rgba(31, 41, 55, 0.5)")
    fig.update_xaxes(title_text="Mês", row=1, col=2, showgrid=True, gridcolor="rgba(31, 41, 55, 0.5)")
    fig.update_yaxes(title_text="(%)", row=1, col=1, showgrid=True, gridcolor="rgba(31, 41, 55, 0.5)")
    fig.update_yaxes(title_text="(%)", row=1, col=2, showgrid=True, gridcolor="rgba(31, 41, 55, 0.5)")

    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#0F172A",
        font=dict(color="#F9FAFB"),
        hovermode="x unified",
        height=350,
        showlegend=False,
        margin=dict(l=50, r=50, t=80, b=50),
    )

    return fig

from plotly.subplots import make_subplots

def criar_grafico_ticket_medio(df):
    """Evolução do Ticket Médio."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["Mês"],
        y=df["Ticket Médio"],
        name="Ticket Médio",
        marker=dict(
            color=df["Ticket Médio"],
            colorscale="Viridis",
            showscale=False,
            line=dict(color="#3B82F6", width=2),
        ),
        text=[f"R$ {v:,.0f}" for v in df["Ticket Médio"]],
        textposition="outside",
    ))

    fig.update_layout(
        title="Evolução do Ticket Médio",
        xaxis=dict(title="Mês", showgrid=False),
        yaxis=dict(title="Ticket Médio (R$)", showgrid=True, gridwidth=1, gridcolor="rgba(31, 41, 55, 0.5)"),
        hovermode="x",
        plot_bgcolor="#111827",
        paper_bgcolor="#0F172A",
        font=dict(color="#F9FAFB"),
        margin=dict(l=70, r=70, t=80, b=70),
        height=320,
        showlegend=False,
    )

    return fig

# ========== INSIGHTS AUTOMÁTICOS ==========
def gerar_insights(df, metricas):
    """Gera insights baseados em análise dos dados."""
    insights = []

    # Insight 1: Crescimento
    if metricas["rec_var"] > 5:
        insights.append({
            "tipo": "good",
            "titulo": "📈 Crescimento de Receita",
            "texto": f"Receita cresceu {metricas['rec_var']:.1f}% no último mês - tendência positiva mantida."
        })
    elif metricas["rec_var"] < -5:
        insights.append({
            "tipo": "warning",
            "titulo": "⚠️ Queda de Receita",
            "texto": f"Receita caiu {abs(metricas['rec_var']):.1f}% - analise causas e adapte estratégia."
        })

    # Insight 2: Conversão
    if metricas["conversao_media"] > 0.18:
        insights.append({
            "tipo": "good",
            "titulo": "✅ Conversão Forte",
            "texto": f"Taxa de conversão média de {metricas['conversao_media']:.2f}% indica funil bem otimizado."
        })
    else:
        insights.append({
            "tipo": "warning",
            "titulo": "🔍 Oportunidade de Conversão",
            "texto": f"Taxa de conversão {metricas['conversao_media']:.2f}% - teste otimizações na jornada."
        })

    # Insight 3: Retenção
    if metricas["retenção_media"] > 90:
        insights.append({
            "tipo": "good",
            "titulo": "🎯 Retenção Excelente",
            "texto": f"Retenção média de {metricas['retenção_media']:.1f}% mostra satisfação dos clientes."
        })
    elif metricas["retenção_media"] < 85:
        insights.append({
            "tipo": "warning",
            "titulo": "⚠️ Churn Elevado",
            "texto": f"Retenção em {metricas['retenção_media']:.1f}% - priorize estratégias de permanência."
        })

    # Insight 4: Ticket
    ticket_trend = df.iloc[-1]["Ticket Médio"] - df.iloc[0]["Ticket Médio"]
    if ticket_trend > 50:
        insights.append({
            "tipo": "good",
            "titulo": "💰 Ticket Crescente",
            "texto": f"Ticket médio subiu R$ {ticket_trend:.0f} - estratégia de upsell funcionando."
        })

    return insights

# ========== INTERFACE PRINCIPAL ==========
st.markdown("""
<div style="text-align: center; margin: 30px 0 20px 0;">
    <h1 class="header-title">Dashboard Financeiro MVP</h1>
    <p style="color: #9CA3AF; font-size: 0.95rem; margin-top: 8px;">
        📊 Análise Executiva de Negócio | Decisões Orientadas a Dados
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Sidebar - Controles
with st.sidebar:
    st.markdown("### ⚙️ Configurações")
    periodo = st.slider("Período de análise (meses)", 3, 12, 6)

    st.markdown("---")
    st.markdown("### 📌 Sobre este Dashboard")
    st.markdown("""
    Este dashboard simula resultados reais de uma empresa em validação.

    **Propósito:**
    - Entender o padrão de dados necessários
    - Replicar em qualquer negócio
    - Tomar decisões baseadas em dados reais

    **KPIs Essenciais:**
    - Receita & Crescimento
    - Conversão & Eficiência
    - Retenção & Churn
    - Ticket Médio & AOV
    """)

# Carregar dados
df = gerar_dados_vendas(periodo)
metricas = calcular_metricas(df)

# KPIs Principais
st.markdown("<h2 class='section-title'>📊 KPIs Principais</h2>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">💰 Receita Total</div>
        <div class="metric-value">R$ {metricas['receita_total']:,.0f}</div>
        <div class="metric-change {'positive' if metricas['rec_var'] >= 0 else 'negative'}">
            {'📈' if metricas['rec_var'] >= 0 else '📉'} {abs(metricas['rec_var']):.1f}% vs mês anterior
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">👥 Total de Clientes</div>
        <div class="metric-value">{metricas['clientes_total']}</div>
        <div class="metric-change {'positive' if metricas['cli_var'] >= 0 else 'negative'}">
            {'📈' if metricas['cli_var'] >= 0 else '📉'} {abs(metricas['cli_var']):.1f}% vs mês anterior
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🎯 Ticket Médio</div>
        <div class="metric-value">R$ {metricas['ticket_medio']:,.0f}</div>
        <div class="metric-change neutral">
            Receita ÷ Clientes
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📈 Conversão Média</div>
        <div class="metric-value">{metricas['conversao_media']:.2f}%</div>
        <div class="metric-change neutral">
            Clientes ÷ Leads
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Gráficos em Grid
st.markdown("<h2 class='section-title'>📈 Análise Temporal</h2>", unsafe_allow_html=True)

col_esq, col_dir = st.columns([1.5, 1])

with col_esq:
    st.plotly_chart(criar_grafico_receita_clientes(df), use_container_width=True)

with col_dir:
    st.plotly_chart(criar_grafico_ticket_medio(df), use_container_width=True)

# Segunda linha de gráficos
col_novo, col_conv = st.columns([1, 1])

with col_novo:
    st.plotly_chart(criar_grafico_novos_recorrentes(df), use_container_width=True)

with col_conv:
    st.plotly_chart(criar_grafico_conversao_churn(df), use_container_width=True)

st.markdown("---")

# Insights Automáticos
st.markdown("<h2 class='section-title'>💡 Insights & Recomendações</h2>", unsafe_allow_html=True)

insights = gerar_insights(df, metricas)
for insight in insights:
    classe = f"insight-box insight-{insight['tipo']}"
    st.markdown(f"""
    <div class="{classe}">
        <strong>{insight['titulo']}</strong><br>
        {insight['texto']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Tabela Detalhada
st.markdown("<h2 class='section-title'>📋 Dados Detalhados</h2>", unsafe_allow_html=True)
st.markdown("<p class='section-subtitle'>Visualize todas as métricas por período.</p>", unsafe_allow_html=True)

df_display = df[["Mês", "Leads", "Clientes", "Clientes Novos", "Clientes Recorrentes", "Receita", "Ticket Médio", "Conversão (%)", "Churn (%)"]].copy()
df_display["Receita"] = df_display["Receita"].apply(lambda x: f"R$ {x:,.0f}")
df_display["Ticket Médio"] = df_display["Ticket Médio"].apply(lambda x: f"R$ {x:,.0f}")
df_display["Conversão (%)"] = df_display["Conversão (%)"].apply(lambda x: f"{x:.2f}%")
df_display["Churn (%)"] = df_display["Churn (%)"].apply(lambda x: f"{x:.2f}%")

st.dataframe(df_display, use_container_width=True, hide_index=True)

st.markdown("---")

# Footer
st.markdown("""
<div style="text-align: center; padding: 20px; color: #9CA3AF; font-size: 0.85rem;">
    <p>🎓 <strong>Dashboard de Educação</strong> - Desenvolvido para ensinar dados em negócio</p>
    <p>Use como referência para replicar em seu próprio projeto ou empresa</p>
</div>
""", unsafe_allow_html=True)
