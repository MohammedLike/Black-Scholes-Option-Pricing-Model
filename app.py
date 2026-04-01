"""
Option Pricing Model — Streamlit Web Application

A comprehensive, interactive web app for Black-Scholes option pricing,
Greeks analysis, Monte Carlo simulation, and sensitivity studies.
"""
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys, os, io, time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.black_scholes import BlackScholesEngine
from src.monte_carlo import MonteCarloEngine
from src.implied_volatility import ImpliedVolatilitySolver
from src.sensitivity import SensitivityAnalyzer
from src.data_pipeline import MarketDataPipeline

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE CONFIG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.set_page_config(
    page_title="Option Pricing Model",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CUSTOM CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
    /* Main container */
    .main .block-container { padding-top: 1.5rem; max-width: 1400px; }

    /* KPI cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
        border: 1px solid #2d3548;
        border-radius: 12px;
        padding: 20px 24px;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(21, 101, 192, 0.15);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #8899aa;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }
    .kpi-delta {
        font-size: 0.85rem;
        margin-top: 4px;
    }
    .kpi-up { color: #4caf50; }
    .kpi-down { color: #f44336; }
    .kpi-neutral { color: #90a4ae; }

    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #e3f2fd;
        border-bottom: 3px solid #1565c0;
        padding-bottom: 8px;
        margin: 24px 0 16px 0;
    }

    /* Greek cards */
    .greek-card {
        background: linear-gradient(135deg, #1a237e 0%, #1565c0 100%);
        border-radius: 10px;
        padding: 16px 20px;
        text-align: center;
        color: white;
        margin-bottom: 8px;
    }
    .greek-symbol { font-size: 1.6rem; font-weight: 800; }
    .greek-value { font-size: 1.3rem; font-weight: 600; margin-top: 4px; }
    .greek-name { font-size: 0.75rem; color: #bbdefb; text-transform: uppercase; letter-spacing: 1px; }

    /* Status badges */
    .badge-pass {
        background: #1b5e20; color: #a5d6a7; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
    .badge-fail {
        background: #b71c1c; color: #ef9a9a; padding: 4px 12px;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] { background: #0d1117; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] .stTextInput label {
        color: #8899aa !important;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1a1f2e;
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        color: #90a4ae;
        border: 1px solid #2d3548;
    }
    .stTabs [aria-selected="true"] {
        background: #1565c0 !important;
        color: white !important;
    }

    /* Tables */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, #1565c0 0%, transparent 100%);
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def kpi_card(label, value, delta=None, delta_type="neutral"):
    delta_html = ""
    if delta:
        cls = f"kpi-{delta_type}"
        arrow = "▲" if delta_type == "up" else ("▼" if delta_type == "down" else "")
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta}</div>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """


def greek_card(symbol, name, value):
    return f"""
    <div class="greek-card">
        <div class="greek-name">{name}</div>
        <div class="greek-symbol">{symbol}</div>
        <div class="greek-value">{value}</div>
    </div>
    """


def section_header(text):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


PLOTLY_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,31,46,0.8)",
    font=dict(family="Inter, sans-serif", color="#e0e0e0"),
    margin=dict(l=60, r=30, t=50, b=50),
)

CALL_COLOR = "#2196F3"
PUT_COLOR = "#F44336"
ACCENT_COLOR = "#4CAF50"
WARN_COLOR = "#FF9800"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DATA LOADING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(ticker, period="1y"):
    pipeline = MarketDataPipeline(Path("data"))
    df = pipeline.fetch_stock_data(ticker, period)
    stats = pipeline.summary_statistics(df)
    vol = pipeline.get_annualized_vol(df)
    spot = pipeline.get_current_spot(df)
    hist_vol_df = pipeline.compute_historical_volatility(df)
    return df, stats, vol, spot, hist_vol_df


@st.cache_data(show_spinner=False)
def run_monte_carlo(S, K, T, r, sigma, q, n_sims, opt_type):
    engine = MonteCarloEngine(n_simulations=n_sims, n_steps=252, seed=42)
    result = engine.price_option(S, K, T, r, sigma, q, opt_type)
    convergence = engine.convergence_analysis(S, K, T, r, sigma, q, opt_type,
                                               sim_counts=[100, 500, 1000, 5000, 10000, 50000, n_sims])
    return result, convergence


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIDEBAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with st.sidebar:
    st.markdown("## 📈 Option Pricing Model")
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # Ticker input
    st.markdown("### 🔍 Stock Selection")
    ticker = st.text_input("Ticker Symbol", value="AAPL", help="Enter any valid stock ticker")

    # Fetch data
    fetch_btn = st.button("🚀 Fetch & Analyze", use_container_width=True, type="primary")

    if fetch_btn or "stock_data" in st.session_state:
        if fetch_btn:
            with st.spinner(f"Fetching {ticker} data..."):
                try:
                    df, stats, hist_vol, spot, hist_vol_df = fetch_stock_data(ticker.upper())
                    st.session_state["stock_data"] = df
                    st.session_state["stats"] = stats
                    st.session_state["hist_vol"] = hist_vol
                    st.session_state["spot"] = spot
                    st.session_state["hist_vol_df"] = hist_vol_df
                    st.session_state["ticker"] = ticker.upper()
                    st.success(f"Loaded {ticker.upper()}")
                except Exception as e:
                    st.error(f"Error: {e}")

        if "spot" in st.session_state:
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.markdown("### ⚙️ Option Parameters")

            spot_default = round(st.session_state["spot"], 2)
            vol_default = round(st.session_state["hist_vol"] * 100, 1)

            S = st.number_input("Spot Price ($)", value=spot_default, step=1.0, format="%.2f")
            K = st.number_input("Strike Price ($)", value=spot_default, step=1.0, format="%.2f")
            T = st.number_input("Time to Expiry (years)", value=1.0, min_value=0.01, max_value=5.0, step=0.25)
            r = st.number_input("Risk-Free Rate (%)", value=5.0, min_value=0.0, max_value=20.0, step=0.25) / 100
            sigma = st.number_input("Volatility (%)", value=vol_default, min_value=1.0, max_value=200.0, step=0.5) / 100
            q = st.number_input("Dividend Yield (%)", value=0.0, min_value=0.0, max_value=15.0, step=0.1) / 100

            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.markdown("### 🎲 Monte Carlo")
            n_sims = st.select_slider("Simulations", options=[10000, 50000, 100000, 250000, 500000], value=100000)

            # Store params
            st.session_state["params"] = dict(S=S, K=K, T=T, r=r, sigma=sigma, q=q, n_sims=n_sims)

    # Navigation
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📑 Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Dashboard", "📊 Greeks Analysis", "🎲 Monte Carlo",
         "📈 Implied Volatility", "🔥 Sensitivity Analysis",
         "💹 Stock Analysis", "📄 Report Generator"],
        label_visibility="collapsed",
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NO DATA STATE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "params" not in st.session_state:
    st.markdown("# 📈 Black-Scholes Option Pricing Model")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔬 What This Does")
        st.markdown("""
        - **Black-Scholes** analytical pricing
        - **All Greeks** (Delta, Gamma, Theta, Vega, Rho + higher-order)
        - **Monte Carlo** simulation with variance reduction
        - **Implied Volatility** extraction
        - **Sensitivity Analysis** with 3D surfaces
        - **PDF Report** generation
        """)
    with col2:
        st.markdown("### 🚀 How To Start")
        st.markdown("""
        1. Enter a **stock ticker** in the sidebar
        2. Click **Fetch & Analyze**
        3. Adjust option parameters
        4. Explore each analysis page
        5. Download your **PDF report**
        """)
    with col3:
        st.markdown("### 🏗️ Tech Stack")
        st.markdown("""
        - **Python** + NumPy + SciPy
        - **Streamlit** interactive UI
        - **Plotly** 3D visualizations
        - **yfinance** market data
        - **Monte Carlo** simulation engine
        - **Newton-Raphson** IV solver
        """)
    st.stop()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPUTE CORE RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
p = st.session_state["params"]
S, K, T, r, sigma, q = p["S"], p["K"], p["T"], p["r"], p["sigma"], p["q"]

bs_call = BlackScholesEngine.compute_all(S, K, T, r, sigma, q, "call")
bs_put = BlackScholesEngine.compute_all(S, K, T, r, sigma, q, "put")
parity = BlackScholesEngine.put_call_parity_check(S, K, T, r, sigma, q)
tkr = st.session_state.get("ticker", "STOCK")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if page == "🏠 Dashboard":
    st.markdown(f"# 🏠 {tkr} Options Dashboard")
    st.markdown("---")

    # Top KPI Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(kpi_card("Spot Price", f"${S:.2f}"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Strike", f"${K:.2f}"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Call Price", f"${bs_call.price:.2f}", f"Δ={bs_call.delta:.3f}", "up"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Put Price", f"${bs_put.price:.2f}", f"Δ={bs_put.delta:.3f}", "down"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Volatility", f"{sigma:.1%}"), unsafe_allow_html=True)
    with c6:
        parity_status = "PASS" if parity["parity_holds"] else "FAIL"
        st.markdown(kpi_card("Put-Call Parity", parity_status, f"err={parity['parity_error']:.1e}", "up" if parity["parity_holds"] else "down"), unsafe_allow_html=True)

    st.markdown("")

    # Greeks Row
    section_header("Option Greeks")
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    with g1:
        st.markdown(greek_card("Δ", "Delta", f"{bs_call.delta:.4f}"), unsafe_allow_html=True)
    with g2:
        st.markdown(greek_card("Γ", "Gamma", f"{bs_call.gamma:.6f}"), unsafe_allow_html=True)
    with g3:
        st.markdown(greek_card("Θ", "Theta/day", f"{bs_call.theta:.4f}"), unsafe_allow_html=True)
    with g4:
        st.markdown(greek_card("ν", "Vega/1%", f"{bs_call.vega:.4f}"), unsafe_allow_html=True)
    with g5:
        st.markdown(greek_card("ρ", "Rho/1%", f"{bs_call.rho:.4f}"), unsafe_allow_html=True)
    with g6:
        st.markdown(greek_card("V", "Vanna", f"{bs_call.vanna:.5f}"), unsafe_allow_html=True)

    st.markdown("")

    # Two column layout: Pricing Table + P&L Chart
    col_left, col_right = st.columns([1, 1.3])

    with col_left:
        section_header("Pricing Summary")
        pricing_df = pd.DataFrame({
            "Metric": ["Price", "Delta", "Gamma", "Theta/day", "Vega/1%", "Rho/1%",
                       "Vanna", "Volga", "Charm/day", "d1", "d2"],
            "Call": [f"${bs_call.price:.4f}", f"{bs_call.delta:.4f}", f"{bs_call.gamma:.6f}",
                     f"{bs_call.theta:.4f}", f"{bs_call.vega:.4f}", f"{bs_call.rho:.4f}",
                     f"{bs_call.vanna:.6f}", f"{bs_call.volga:.6f}", f"{bs_call.charm:.6f}",
                     f"{bs_call.d1:.6f}", f"{bs_call.d2:.6f}"],
            "Put": [f"${bs_put.price:.4f}", f"{bs_put.delta:.4f}", f"{bs_put.gamma:.6f}",
                    f"{bs_put.theta:.4f}", f"{bs_put.vega:.4f}", f"{bs_put.rho:.4f}",
                    f"{bs_put.vanna:.6f}", f"{bs_put.volga:.6f}", f"{bs_put.charm:.6f}",
                    f"{bs_put.d1:.6f}", f"{bs_put.d2:.6f}"],
        })
        st.dataframe(pricing_df, use_container_width=True, hide_index=True, height=420)

    with col_right:
        section_header("P&L at Expiry")
        spot_range = np.linspace(S * 0.5, S * 1.5, 300)
        call_payoff = np.maximum(spot_range - K, 0) - bs_call.price
        put_payoff = np.maximum(K - spot_range, 0) - bs_put.price

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_range, y=call_payoff, name="Long Call",
                                 line=dict(color=CALL_COLOR, width=2.5),
                                 fill="tozeroy", fillcolor="rgba(33,150,243,0.1)"))
        fig.add_trace(go.Scatter(x=spot_range, y=put_payoff, name="Long Put",
                                 line=dict(color=PUT_COLOR, width=2.5),
                                 fill="tozeroy", fillcolor="rgba(244,67,54,0.1)"))
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.4)
        fig.add_vline(x=K, line_dash="dash", line_color="gray", opacity=0.4,
                     annotation_text=f"K=${K:.0f}")
        fig.update_layout(**PLOTLY_LAYOUT, title="P&L at Expiry",
                         xaxis_title="Spot Price ($)", yaxis_title="P&L ($)",
                         height=420, legend=dict(x=0.02, y=0.98))
        st.plotly_chart(fig, use_container_width=True)

    # Model Parameters Info
    section_header("Model Parameters")
    pc1, pc2, pc3, pc4, pc5, pc6 = st.columns(6)
    params_display = [
        ("Spot (S)", f"${S:.2f}"), ("Strike (K)", f"${K:.2f}"),
        ("Expiry (T)", f"{T:.2f}y"), ("Rate (r)", f"{r:.2%}"),
        ("Vol (σ)", f"{sigma:.2%}"), ("Div (q)", f"{q:.2%}"),
    ]
    for col, (label, val) in zip([pc1, pc2, pc3, pc4, pc5, pc6], params_display):
        with col:
            st.markdown(kpi_card(label, val), unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: GREEKS ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📊 Greeks Analysis":
    st.markdown(f"# 📊 Greeks Analysis — {tkr}")
    st.markdown("---")

    analyzer = SensitivityAnalyzer(S, K, T, r, sigma, q)
    spot_range = np.linspace(S * 0.5, S * 1.5, 120)
    time_range = np.linspace(0.01, max(T * 1.5, 0.5), 100)

    greeks_call = analyzer.greeks_vs_spot(spot_range, "call")
    greeks_put = analyzer.greeks_vs_spot(spot_range, "put")
    greeks_time_call = analyzer.greeks_vs_time(time_range, "call")
    greeks_time_put = analyzer.greeks_vs_time(time_range, "put")

    tab1, tab2, tab3 = st.tabs(["📉 Greeks vs Spot", "⏱️ Greeks vs Time", "🏔️ 3D Surfaces"])

    with tab1:
        greeks_list = ["price", "delta", "gamma", "theta", "vega", "rho"]
        titles = ["Option Price ($)", "Delta (Δ)", "Gamma (Γ)", "Theta (Θ)/day", "Vega (ν)/1%", "Rho (ρ)/1%"]

        fig = make_subplots(rows=2, cols=3, subplot_titles=titles, vertical_spacing=0.12, horizontal_spacing=0.08)
        for idx, greek in enumerate(greeks_list):
            row, col = idx // 3 + 1, idx % 3 + 1
            fig.add_trace(go.Scatter(x=spot_range, y=greeks_call[greek], name="Call" if idx == 0 else None,
                                     line=dict(color=CALL_COLOR, width=2), showlegend=(idx == 0)), row=row, col=col)
            fig.add_trace(go.Scatter(x=spot_range, y=greeks_put[greek], name="Put" if idx == 0 else None,
                                     line=dict(color=PUT_COLOR, width=2), showlegend=(idx == 0)), row=row, col=col)
            fig.add_vline(x=K, line_dash="dash", line_color="gray", opacity=0.3, row=row, col=col)

        fig.update_layout(**PLOTLY_LAYOUT, height=700, title="All Greeks vs Spot Price",
                         legend=dict(x=0.5, y=1.08, orientation="h", xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = make_subplots(rows=2, cols=3, subplot_titles=titles, vertical_spacing=0.12, horizontal_spacing=0.08)
        for idx, greek in enumerate(greeks_list):
            row, col = idx // 3 + 1, idx % 3 + 1
            fig.add_trace(go.Scatter(x=time_range, y=greeks_time_call[greek], name="Call" if idx == 0 else None,
                                     line=dict(color=CALL_COLOR, width=2), showlegend=(idx == 0)), row=row, col=col)
            fig.add_trace(go.Scatter(x=time_range, y=greeks_time_put[greek], name="Put" if idx == 0 else None,
                                     line=dict(color=PUT_COLOR, width=2), showlegend=(idx == 0)), row=row, col=col)

        fig.update_layout(**PLOTLY_LAYOUT, height=700, title="All Greeks vs Time to Expiry",
                         legend=dict(x=0.5, y=1.08, orientation="h", xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        surf_col1, surf_col2 = st.columns(2)

        spot_3d = np.linspace(S * 0.6, S * 1.4, 50)
        vol_3d = np.linspace(0.05, 0.8, 50)
        time_3d = np.linspace(0.01, max(T * 1.5, 0.5), 50)

        with surf_col1:
            # Delta surface (spot x time)
            delta_grid = analyzer.delta_surface(spot_3d, time_3d, "call")
            fig = go.Figure(data=[go.Surface(z=delta_grid, x=time_3d, y=spot_3d,
                                             colorscale="Viridis", opacity=0.9)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Delta Surface (Call)",
                             scene=dict(xaxis_title="Time (yrs)", yaxis_title="Spot ($)", zaxis_title="Delta"),
                             height=500)
            st.plotly_chart(fig, use_container_width=True)

        with surf_col2:
            # Gamma surface (spot x vol)
            gamma_grid = analyzer.gamma_surface(spot_3d, vol_3d)
            fig = go.Figure(data=[go.Surface(z=gamma_grid, x=vol_3d, y=spot_3d,
                                             colorscale="Inferno", opacity=0.9)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Gamma Surface",
                             scene=dict(xaxis_title="Volatility", yaxis_title="Spot ($)", zaxis_title="Gamma"),
                             height=500)
            st.plotly_chart(fig, use_container_width=True)

        surf_col3, surf_col4 = st.columns(2)
        with surf_col3:
            theta_grid = analyzer.theta_surface(spot_3d, time_3d, "call")
            fig = go.Figure(data=[go.Surface(z=theta_grid, x=time_3d, y=spot_3d,
                                             colorscale="RdBu", opacity=0.9)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Theta Surface (Call)",
                             scene=dict(xaxis_title="Time (yrs)", yaxis_title="Spot ($)", zaxis_title="Theta/day"),
                             height=500)
            st.plotly_chart(fig, use_container_width=True)

        with surf_col4:
            vega_grid = analyzer.vega_surface(spot_3d, time_3d)
            fig = go.Figure(data=[go.Surface(z=vega_grid, x=time_3d, y=spot_3d,
                                             colorscale="Plasma", opacity=0.9)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Vega Surface",
                             scene=dict(xaxis_title="Time (yrs)", yaxis_title="Spot ($)", zaxis_title="Vega/1%"),
                             height=500)
            st.plotly_chart(fig, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: MONTE CARLO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🎲 Monte Carlo":
    st.markdown(f"# 🎲 Monte Carlo Simulation — {tkr}")
    st.markdown("---")

    with st.spinner("Running Monte Carlo simulation..."):
        mc_call, conv_call = run_monte_carlo(S, K, T, r, sigma, q, p["n_sims"], "call")
        mc_put, conv_put = run_monte_carlo(S, K, T, r, sigma, q, p["n_sims"], "put")

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card("MC Call Price", f"${mc_call.price:.4f}"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("BS Benchmark", f"${mc_call.bs_benchmark:.4f}"), unsafe_allow_html=True)
    with c3:
        err_type = "up" if abs(mc_call.pricing_error) < 0.1 else "down"
        st.markdown(kpi_card("Pricing Error", f"${mc_call.pricing_error:.4f}", f"SE={mc_call.std_error:.4f}", err_type), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("MC Put Price", f"${mc_put.price:.4f}"), unsafe_allow_html=True)
    with c5:
        ci = mc_call.confidence_interval_95
        st.markdown(kpi_card("95% CI", f"[{ci[0]:.2f}, {ci[1]:.2f}]"), unsafe_allow_html=True)

    st.markdown("")

    tab1, tab2, tab3 = st.tabs(["🛤️ Simulated Paths", "📊 Distributions", "📈 Convergence"])

    with tab1:
        fig = go.Figure()
        n_display = min(150, mc_call.paths.shape[0])
        t_axis = np.linspace(0, T, mc_call.paths.shape[1])

        for i in range(n_display):
            color = CALL_COLOR if mc_call.paths[i, -1] > K else PUT_COLOR
            fig.add_trace(go.Scatter(x=t_axis, y=mc_call.paths[i], mode="lines",
                                     line=dict(color=color, width=0.3), opacity=0.15,
                                     showlegend=False, hoverinfo="skip"))

        fig.add_hline(y=K, line_dash="dash", line_color="white", opacity=0.7,
                     annotation_text=f"Strike K=${K:.0f}")
        fig.add_hline(y=S, line_dash="dashdot", line_color=ACCENT_COLOR, opacity=0.7,
                     annotation_text=f"Spot S=${S:.0f}")
        fig.update_layout(**PLOTLY_LAYOUT, title=f"Monte Carlo Paths ({p['n_sims']:,} simulations, showing {n_display})",
                         xaxis_title="Time (years)", yaxis_title="Price ($)", height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=mc_call.terminal_prices, nbinsx=120, name="Terminal Prices",
                                        marker_color=CALL_COLOR, opacity=0.7))
            fig.add_vline(x=K, line_dash="dash", line_color=PUT_COLOR, line_width=2,
                         annotation_text=f"K=${K:.0f}")
            fig.add_vline(x=np.mean(mc_call.terminal_prices), line_dash="dashdot",
                         line_color=ACCENT_COLOR, line_width=2,
                         annotation_text=f"Mean=${np.mean(mc_call.terminal_prices):.1f}")
            fig.update_layout(**PLOTLY_LAYOUT, title="Terminal Price Distribution",
                             xaxis_title="Price ($)", yaxis_title="Count", height=450)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            payoffs = np.maximum(mc_call.terminal_prices - K, 0)
            payoffs_nz = payoffs[payoffs > 0]
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=payoffs_nz, nbinsx=80, name="Payoffs",
                                        marker_color=ACCENT_COLOR, opacity=0.7))
            fig.add_vline(x=bs_call.price, line_dash="dash", line_color=PUT_COLOR, line_width=2,
                         annotation_text=f"BS=${bs_call.price:.2f}")
            fig.add_vline(x=mc_call.price, line_dash="dashdot", line_color=CALL_COLOR, line_width=2,
                         annotation_text=f"MC=${mc_call.price:.2f}")
            fig.update_layout(**PLOTLY_LAYOUT, title="Call Payoff Distribution (non-zero)",
                             xaxis_title="Payoff ($)", yaxis_title="Count", height=450)
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        conv_data = conv_call["convergence_data"]
        ns = [d["n_simulations"] for d in conv_data]
        prices = [d["price"] for d in conv_data]
        errors = [d["std_error"] for d in conv_data]

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ns, y=prices, mode="lines+markers", name="MC Price",
                                     line=dict(color=CALL_COLOR, width=2), marker=dict(size=8)))
            fig.add_trace(go.Scatter(x=ns, y=[p + 1.96*e for p, e in zip(prices, errors)],
                                     mode="lines", name="95% CI Upper", line=dict(color=CALL_COLOR, width=0.5, dash="dot"),
                                     showlegend=False))
            fig.add_trace(go.Scatter(x=ns, y=[p - 1.96*e for p, e in zip(prices, errors)],
                                     mode="lines", name="95% CI Lower", line=dict(color=CALL_COLOR, width=0.5, dash="dot"),
                                     fill="tonexty", fillcolor="rgba(33,150,243,0.1)", showlegend=False))
            fig.add_hline(y=conv_call["bs_benchmark"], line_dash="dash", line_color=PUT_COLOR, line_width=2,
                         annotation_text=f"BS={conv_call['bs_benchmark']:.4f}")
            fig.update_layout(**PLOTLY_LAYOUT, title="Price Convergence",
                             xaxis_title="Simulations", yaxis_title="Price ($)",
                             xaxis_type="log", height=450)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            theoretical = [errors[0] * np.sqrt(ns[0]) / np.sqrt(n) for n in ns]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ns, y=errors, mode="lines+markers", name="Actual SE",
                                     line=dict(color=PUT_COLOR, width=2), marker=dict(size=8)))
            fig.add_trace(go.Scatter(x=ns, y=theoretical, mode="lines", name="1/sqrt(n) theoretical",
                                     line=dict(color="gray", width=1.5, dash="dash")))
            fig.update_layout(**PLOTLY_LAYOUT, title="Standard Error Convergence",
                             xaxis_title="Simulations", yaxis_title="Std Error ($)",
                             xaxis_type="log", yaxis_type="log", height=450)
            st.plotly_chart(fig, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: IMPLIED VOLATILITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📈 Implied Volatility":
    st.markdown(f"# 📈 Implied Volatility — {tkr}")
    st.markdown("---")

    # IV Recovery
    iv_result = ImpliedVolatilitySolver.solve(bs_call.price, S, K, T, r, q, "call")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("Input Vol", f"{sigma:.4%}"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Recovered IV", f"{iv_result['implied_volatility']:.4%}"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Iterations", f"{iv_result['iterations']}"), unsafe_allow_html=True)
    with c4:
        conv_text = "YES" if iv_result["converged"] else "NO"
        st.markdown(kpi_card("Converged", conv_text, f"err={iv_result['final_error']:.1e}", "up" if iv_result["converged"] else "down"), unsafe_allow_html=True)

    st.markdown("")

    tab1, tab2 = st.tabs(["😊 Volatility Smile", "🎯 Solver Convergence"])

    with tab1:
        pipeline = MarketDataPipeline()
        smile_data = pipeline.generate_synthetic_smile_data(S, K, sigma)
        smile_results = ImpliedVolatilitySolver.volatility_smile(S, T, r, q, smile_data, "call")

        col1, col2 = st.columns(2)
        with col1:
            strikes = [d["strike"] for d in smile_results]
            ivs = [d["implied_vol"] for d in smile_results]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=strikes, y=ivs, mode="lines+markers",
                                     line=dict(color=CALL_COLOR, width=2.5), marker=dict(size=7),
                                     name="Implied Vol"))
            fig.add_vline(x=K, line_dash="dash", line_color="gray", opacity=0.5,
                         annotation_text=f"ATM K=${K:.0f}")
            fig.update_layout(**PLOTLY_LAYOUT, title="Volatility Smile (IV vs Strike)",
                             xaxis_title="Strike Price ($)", yaxis_title="Implied Volatility", height=450)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            moneyness = [d["moneyness"] for d in smile_results]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=moneyness, y=ivs, mode="lines+markers",
                                     line=dict(color=PUT_COLOR, width=2.5), marker=dict(size=7),
                                     name="Implied Vol"))
            fig.add_vline(x=1.0, line_dash="dash", line_color="gray", opacity=0.5,
                         annotation_text="ATM (S/K=1)")
            fig.update_layout(**PLOTLY_LAYOUT, title="Volatility Smile (IV vs Moneyness)",
                             xaxis_title="Moneyness (S/K)", yaxis_title="Implied Volatility", height=450)
            st.plotly_chart(fig, use_container_width=True)

        # Smile data table
        section_header("Smile Data")
        smile_df = pd.DataFrame(smile_results)
        smile_df["implied_vol"] = smile_df["implied_vol"].apply(lambda x: f"{x:.4%}")
        smile_df["market_price"] = smile_df["market_price"].apply(lambda x: f"${x:.4f}")
        smile_df["strike"] = smile_df["strike"].apply(lambda x: f"${x:.2f}")
        smile_df["moneyness"] = smile_df["moneyness"].apply(lambda x: f"{x:.4f}")
        st.dataframe(smile_df, use_container_width=True, hide_index=True)

    with tab2:
        if iv_result.get("history"):
            history = iv_result["history"]
            iters = [h["iteration"] for h in history]
            sigmas = [h["sigma"] for h in history]
            diffs = [abs(h["diff"]) for h in history]

            col1, col2 = st.columns(2)
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=iters, y=sigmas, mode="lines+markers",
                                         line=dict(color=CALL_COLOR, width=2.5), marker=dict(size=8)))
                fig.update_layout(**PLOTLY_LAYOUT, title="Sigma Convergence Path",
                                 xaxis_title="Iteration", yaxis_title="Implied Volatility", height=400)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=iters, y=diffs, mode="lines+markers",
                                         line=dict(color=PUT_COLOR, width=2.5), marker=dict(size=8)))
                fig.update_layout(**PLOTLY_LAYOUT, title="Pricing Error (log scale)",
                                 xaxis_title="Iteration", yaxis_title="|BS(sigma) - Market|",
                                 yaxis_type="log", height=400)
                st.plotly_chart(fig, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: SENSITIVITY ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "🔥 Sensitivity Analysis":
    st.markdown(f"# 🔥 Sensitivity Analysis — {tkr}")
    st.markdown("---")

    analyzer = SensitivityAnalyzer(S, K, T, r, sigma, q)

    tab1, tab2, tab3 = st.tabs(["🏔️ Price Surface", "🗺️ Scenario Heatmap", "📊 Parameter Sweeps"])

    with tab1:
        spot_3d = np.linspace(S * 0.5, S * 1.5, 60)
        vol_3d = np.linspace(0.05, 0.80, 60)

        col1, col2 = st.columns(2)
        with col1:
            price_grid = analyzer.price_surface(spot_3d, vol_3d, "call")
            fig = go.Figure(data=[go.Surface(z=price_grid, x=vol_3d, y=spot_3d,
                                             colorscale="Viridis", opacity=0.92)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Call Price Surface (Spot x Volatility)",
                             scene=dict(xaxis_title="Volatility", yaxis_title="Spot ($)",
                                       zaxis_title="Price ($)"),
                             height=550)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            price_grid_put = analyzer.price_surface(spot_3d, vol_3d, "put")
            fig = go.Figure(data=[go.Surface(z=price_grid_put, x=vol_3d, y=spot_3d,
                                             colorscale="Magma", opacity=0.92)])
            fig.update_layout(**PLOTLY_LAYOUT, title="Put Price Surface (Spot x Volatility)",
                             scene=dict(xaxis_title="Volatility", yaxis_title="Spot ($)",
                                       zaxis_title="Price ($)"),
                             height=550)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        spot_scenarios = np.linspace(S * 0.7, S * 1.3, 11)
        vol_scenarios = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60])

        opt_type = st.radio("Option Type", ["call", "put"], horizontal=True)
        scenario_matrix = analyzer.scenario_matrix(spot_scenarios, vol_scenarios, opt_type)

        fig = go.Figure(data=go.Heatmap(
            z=scenario_matrix.values.astype(float),
            x=scenario_matrix.columns.tolist(),
            y=scenario_matrix.index.tolist(),
            colorscale="RdYlGn",
            texttemplate="%{z:.2f}",
            textfont=dict(size=10),
            hovertemplate="Spot: %{y}<br>Vol: %{x}<br>Price: $%{z:.2f}<extra></extra>",
        ))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"Scenario Matrix — {opt_type.title()} Prices",
                         xaxis_title="Volatility", yaxis_title="Spot Price", height=550)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(scenario_matrix, use_container_width=True)

    with tab3:
        param_choice = st.selectbox("Sweep Parameter", ["Spot Price", "Volatility", "Time to Expiry", "Risk-Free Rate"])

        if param_choice == "Spot Price":
            x_range = np.linspace(S * 0.5, S * 1.5, 150)
            x_label = "Spot Price ($)"
            call_prices = [BlackScholesEngine.price(x, K, T, r, sigma, q, "call") for x in x_range]
            put_prices = [BlackScholesEngine.price(x, K, T, r, sigma, q, "put") for x in x_range]
        elif param_choice == "Volatility":
            x_range = np.linspace(0.01, 1.0, 150)
            x_label = "Volatility"
            call_prices = [BlackScholesEngine.price(S, K, T, r, x, q, "call") for x in x_range]
            put_prices = [BlackScholesEngine.price(S, K, T, r, x, q, "put") for x in x_range]
        elif param_choice == "Time to Expiry":
            x_range = np.linspace(0.01, 3.0, 150)
            x_label = "Time to Expiry (years)"
            call_prices = [BlackScholesEngine.price(S, K, x, r, sigma, q, "call") for x in x_range]
            put_prices = [BlackScholesEngine.price(S, K, x, r, sigma, q, "put") for x in x_range]
        else:
            x_range = np.linspace(0.0, 0.15, 150)
            x_label = "Risk-Free Rate"
            call_prices = [BlackScholesEngine.price(S, K, T, x, sigma, q, "call") for x in x_range]
            put_prices = [BlackScholesEngine.price(S, K, T, x, sigma, q, "put") for x in x_range]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_range, y=call_prices, name="Call", line=dict(color=CALL_COLOR, width=2.5)))
        fig.add_trace(go.Scatter(x=x_range, y=put_prices, name="Put", line=dict(color=PUT_COLOR, width=2.5)))
        fig.update_layout(**PLOTLY_LAYOUT, title=f"Option Price vs {param_choice}",
                         xaxis_title=x_label, yaxis_title="Option Price ($)", height=450)
        st.plotly_chart(fig, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: STOCK ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "💹 Stock Analysis":
    st.markdown(f"# 💹 Stock Analysis — {tkr}")
    st.markdown("---")

    df = st.session_state["stock_data"]
    stats = st.session_state["stats"]
    hist_vol_df = st.session_state.get("hist_vol_df", None)

    # KPI Row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    ret_type = "up" if stats["period_return"] > 0 else "down"
    with c1:
        st.markdown(kpi_card("Current Price", f"${stats['current_price']:.2f}"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Period Return", f"{stats['period_return']:.2%}", None, ret_type), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Ann. Volatility", f"{stats['annualized_vol']:.2%}"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Skewness", f"{stats['skewness']:.4f}"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Kurtosis", f"{stats['kurtosis']:.2f}"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi_card("Trading Days", f"{stats['trading_days']}"), unsafe_allow_html=True)

    st.markdown("")

    tab1, tab2, tab3 = st.tabs(["📈 Price Chart", "📊 Returns Analysis", "📉 Historical Volatility"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
            name=tkr, increasing_line_color=ACCENT_COLOR, decreasing_line_color=PUT_COLOR,
        ))
        # Add moving averages
        if len(df) > 20:
            ma20 = df["Close"].rolling(20).mean()
            fig.add_trace(go.Scatter(x=df.index, y=ma20, name="MA20",
                                     line=dict(color=CALL_COLOR, width=1.2)))
        if len(df) > 50:
            ma50 = df["Close"].rolling(50).mean()
            fig.add_trace(go.Scatter(x=df.index, y=ma50, name="MA50",
                                     line=dict(color=WARN_COLOR, width=1.2)))

        fig.update_layout(**PLOTLY_LAYOUT, title=f"{tkr} Price Chart",
                         xaxis_title="Date", yaxis_title="Price ($)",
                         xaxis_rangeslider_visible=False, height=550)
        st.plotly_chart(fig, use_container_width=True)

        # Volume chart
        colors = [ACCENT_COLOR if df["Close"].iloc[i] >= df["Open"].iloc[i] else PUT_COLOR for i in range(len(df))]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=colors, opacity=0.6, name="Volume"))
        fig.update_layout(**PLOTLY_LAYOUT, title="Trading Volume", xaxis_title="Date", yaxis_title="Volume", height=250)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        log_returns = np.log(df["Close"] / df["Close"].shift(1)).dropna()

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=log_returns, nbinsx=80, name="Log Returns",
                                        marker_color=CALL_COLOR, opacity=0.7))
            fig.add_vline(x=log_returns.mean(), line_dash="dash", line_color=ACCENT_COLOR, line_width=2,
                         annotation_text=f"Mean={log_returns.mean():.5f}")
            fig.update_layout(**PLOTLY_LAYOUT, title="Log Return Distribution",
                             xaxis_title="Log Return", yaxis_title="Count", height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=log_returns.index, y=log_returns.cumsum(),
                                     mode="lines", line=dict(color=CALL_COLOR, width=1.5),
                                     name="Cumulative Return"))
            fig.update_layout(**PLOTLY_LAYOUT, title="Cumulative Log Returns",
                             xaxis_title="Date", yaxis_title="Cumulative Return", height=400)
            st.plotly_chart(fig, use_container_width=True)

        # QQ-like comparison stats
        section_header("Return Statistics")
        stats_df = pd.DataFrame({
            "Statistic": ["Daily Mean", "Daily Std Dev", "Annualized Vol", "Skewness",
                          "Excess Kurtosis", "Min Return", "Max Return", "Sharpe (approx)"],
            "Value": [f"{stats['daily_mean_return']:.6f}", f"{stats['daily_std_return']:.6f}",
                     f"{stats['annualized_vol']:.4%}", f"{stats['skewness']:.4f}",
                     f"{stats['kurtosis']:.4f}",
                     f"{log_returns.min():.4%}", f"{log_returns.max():.4%}",
                     f"{(stats['daily_mean_return'] / stats['daily_std_return'] * np.sqrt(252)):.2f}"],
        })
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    with tab3:
        if hist_vol_df is not None and len(hist_vol_df) > 0:
            fig = go.Figure()
            vol_cols = [c for c in hist_vol_df.columns if c.startswith("rv_")]
            vol_colors = [CALL_COLOR, ACCENT_COLOR, WARN_COLOR, PUT_COLOR]
            vol_names = ["21-day", "63-day", "126-day", "252-day"]
            for col, color, name in zip(vol_cols, vol_colors, vol_names):
                fig.add_trace(go.Scatter(x=hist_vol_df.index, y=hist_vol_df[col],
                                         name=name, line=dict(color=color, width=1.5)))
            fig.update_layout(**PLOTLY_LAYOUT, title="Historical Realized Volatility (Annualized)",
                             xaxis_title="Date", yaxis_title="Volatility", height=450)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Historical volatility data not available.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PAGE: REPORT GENERATOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
elif page == "📄 Report Generator":
    st.markdown(f"# 📄 Report Generator — {tkr}")
    st.markdown("---")

    st.markdown("""
    Generate a comprehensive PDF report with all analysis results for the current stock and parameters.
    The report includes:
    - **Pricing Summary** — BS call/put prices, all Greeks
    - **Model Parameters** — spot, strike, expiry, rate, vol
    - **Monte Carlo Results** — MC price, convergence, confidence interval
    - **Implied Volatility** — IV recovery, smile data
    - **Stock Statistics** — returns, volatility, skewness, kurtosis
    """)

    if st.button("📥 Generate PDF Report", type="primary", use_container_width=True):
        with st.spinner("Generating report... This may take a moment."):
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.lib.colors import HexColor, white
                from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
                from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable)

                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch,
                                        leftMargin=0.85*inch, rightMargin=0.85*inch)

                styles = getSampleStyleSheet()
                DARK_BLUE = HexColor("#1a237e")
                MED_BLUE = HexColor("#1565c0")
                LIGHT_BLUE = HexColor("#e3f2fd")
                DARK_GRAY = HexColor("#333333")
                TABLE_HEADER = HexColor("#1565c0")
                TABLE_ALT = HexColor("#f0f4ff")

                styles.add(ParagraphStyle(name='RTitle', fontName='Helvetica-Bold', fontSize=22, leading=28,
                                          alignment=TA_CENTER, textColor=DARK_BLUE, spaceAfter=12))
                styles.add(ParagraphStyle(name='RSub', fontName='Helvetica', fontSize=12, leading=16,
                                          alignment=TA_CENTER, textColor=MED_BLUE, spaceAfter=8))
                styles.add(ParagraphStyle(name='RChapter', fontName='Helvetica-Bold', fontSize=16, leading=22,
                                          textColor=DARK_BLUE, spaceBefore=16, spaceAfter=10))
                styles.add(ParagraphStyle(name='RSection', fontName='Helvetica-Bold', fontSize=12, leading=16,
                                          textColor=MED_BLUE, spaceBefore=10, spaceAfter=6))
                styles.add(ParagraphStyle(name='RBody', fontName='Helvetica', fontSize=10, leading=14,
                                          alignment=TA_JUSTIFY, textColor=DARK_GRAY, spaceAfter=6))

                story = []

                def make_tbl(data, widths=None):
                    t = Table(data, colWidths=widths, repeatRows=1)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER),
                        ('TEXTCOLOR', (0,0), (-1,0), white),
                        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0,0), (-1,-1), 9.5),
                        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#cccccc")),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [white, TABLE_ALT]),
                        ('TOPPADDING', (0,0), (-1,-1), 5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ]))
                    return t

                # Title
                story.append(Spacer(1, 0.8*inch))
                story.append(HRFlowable(width="80%", thickness=2, color=DARK_BLUE))
                story.append(Spacer(1, 14))
                story.append(Paragraph(f"{tkr} Option Pricing Report", styles['RTitle']))
                story.append(Paragraph("Black-Scholes Analysis with Monte Carlo Validation", styles['RSub']))
                story.append(Spacer(1, 8))
                story.append(HRFlowable(width="80%", thickness=1, color=MED_BLUE))
                story.append(Spacer(1, 14))
                story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['RSub']))
                story.append(PageBreak())

                # Parameters
                story.append(Paragraph("1. Model Parameters", styles['RChapter']))
                story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE))
                story.append(Spacer(1, 8))
                story.append(make_tbl([
                    ["Parameter", "Symbol", "Value"],
                    ["Spot Price", "S", f"${S:.2f}"],
                    ["Strike Price", "K", f"${K:.2f}"],
                    ["Time to Expiry", "T", f"{T:.2f} years"],
                    ["Risk-Free Rate", "r", f"{r:.2%}"],
                    ["Volatility", "sigma", f"{sigma:.2%}"],
                    ["Dividend Yield", "q", f"{q:.2%}"],
                ], widths=[2*inch, 1.2*inch, 3.2*inch]))

                # Pricing
                story.append(Spacer(1, 14))
                story.append(Paragraph("2. Black-Scholes Pricing Results", styles['RChapter']))
                story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE))
                story.append(Spacer(1, 8))
                story.append(make_tbl([
                    ["Metric", "Call", "Put"],
                    ["Price", f"${bs_call.price:.4f}", f"${bs_put.price:.4f}"],
                    ["Delta", f"{bs_call.delta:.4f}", f"{bs_put.delta:.4f}"],
                    ["Gamma", f"{bs_call.gamma:.6f}", f"{bs_put.gamma:.6f}"],
                    ["Theta/day", f"{bs_call.theta:.4f}", f"{bs_put.theta:.4f}"],
                    ["Vega/1%", f"{bs_call.vega:.4f}", f"{bs_put.vega:.4f}"],
                    ["Rho/1%", f"{bs_call.rho:.4f}", f"{bs_put.rho:.4f}"],
                    ["Vanna", f"{bs_call.vanna:.6f}", f"{bs_put.vanna:.6f}"],
                    ["Volga", f"{bs_call.volga:.6f}", f"{bs_put.volga:.6f}"],
                ], widths=[1.5*inch, 2.5*inch, 2.5*inch]))

                # Parity
                story.append(Spacer(1, 10))
                story.append(Paragraph("Put-Call Parity Verification", styles['RSection']))
                story.append(make_tbl([
                    ["C - P", "S*exp(-qT) - K*exp(-rT)", "Error", "Status"],
                    [f"${parity['C_minus_P']:.6f}", f"${parity['S_exp_minus_K_exp']:.6f}",
                     f"{parity['parity_error']:.2e}", "PASS" if parity["parity_holds"] else "FAIL"],
                ]))

                # Monte Carlo
                story.append(Spacer(1, 14))
                story.append(Paragraph("3. Monte Carlo Simulation", styles['RChapter']))
                story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE))
                story.append(Spacer(1, 8))
                mc_call, _ = run_monte_carlo(S, K, T, r, sigma, q, p["n_sims"], "call")
                story.append(make_tbl([
                    ["Metric", "Value"],
                    ["MC Call Price", f"${mc_call.price:.4f}"],
                    ["BS Benchmark", f"${mc_call.bs_benchmark:.4f}"],
                    ["Pricing Error", f"${mc_call.pricing_error:.4f}"],
                    ["Standard Error", f"${mc_call.std_error:.6f}"],
                    ["95% CI", f"[${mc_call.confidence_interval_95[0]:.4f}, ${mc_call.confidence_interval_95[1]:.4f}]"],
                    ["Simulations", f"{p['n_sims']:,}"],
                ], widths=[2.5*inch, 3.9*inch]))

                # IV
                story.append(Spacer(1, 14))
                story.append(Paragraph("4. Implied Volatility", styles['RChapter']))
                story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE))
                story.append(Spacer(1, 8))
                iv_r = ImpliedVolatilitySolver.solve(bs_call.price, S, K, T, r, q, "call")
                story.append(make_tbl([
                    ["Metric", "Value"],
                    ["Input Volatility", f"{sigma:.4%}"],
                    ["Recovered IV", f"{iv_r['implied_volatility']:.4%}"],
                    ["Converged", str(iv_r['converged'])],
                    ["Iterations", str(iv_r['iterations'])],
                ], widths=[2.5*inch, 3.9*inch]))

                # Stock stats
                story.append(Spacer(1, 14))
                story.append(Paragraph("5. Stock Statistics", styles['RChapter']))
                story.append(HRFlowable(width="100%", thickness=1.5, color=DARK_BLUE))
                story.append(Spacer(1, 8))
                stats = st.session_state["stats"]
                story.append(make_tbl([
                    ["Metric", "Value"],
                    ["Current Price", f"${stats['current_price']:.2f}"],
                    ["Period Return", f"{stats['period_return']:.2%}"],
                    ["Annualized Vol", f"{stats['annualized_vol']:.2%}"],
                    ["Skewness", f"{stats['skewness']:.4f}"],
                    ["Excess Kurtosis", f"{stats['kurtosis']:.4f}"],
                    ["Min Price", f"${stats['min_price']:.2f}"],
                    ["Max Price", f"${stats['max_price']:.2f}"],
                    ["Trading Days", f"{stats['trading_days']}"],
                ], widths=[2.5*inch, 3.9*inch]))

                doc.build(story)
                pdf_bytes = buffer.getvalue()

                st.success("Report generated successfully!")
                st.download_button(
                    "📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"{tkr}_option_pricing_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )

            except Exception as e:
                st.error(f"Error generating report: {e}")
                import traceback
                st.code(traceback.format_exc())
