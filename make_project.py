import os

files = {
    "requirements.txt": '''streamlit
pandas
numpy
yfinance
plotly
''',

    "engine/__init__.py": "",
    "components/__init__.py": "",

    "engine/data_loader.py": '''def load_stock_universe():
    return [
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "TATAMOTORS.NS",
        "INFY.NS",
        "HAL.NS",
        "TATAINVEST.NS"
    ]
''',

    "engine/market_data.py": '''import yfinance as yf
import pandas as pd

def fetch_batch_market_data(tickers: list, period: str = "3mo") -> dict:
    data_dict = {}
    if not tickers:
        return data_dict

    try:
        df_batch = yf.download(tickers, period=period, group_by='ticker', progress=False, auto_adjust=True)
        
        for t in tickers:
            try:
                if len(tickers) == 1:
                    df = df_batch.copy()
                else:
                    df = df_batch[t].copy() if t in df_batch else None

                if df is not None and not df.empty and 'Close' in df.columns:
                    df = df.dropna(subset=['Close'])
                    if len(df) >= 5:
                        data_dict[t] = df
            except Exception:
                continue
    except Exception:
        pass

    return data_dict
''',

    "engine/options_engine.py": '''import math
import numpy as np

LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "RELIANCE.NS": 250,
    "TCS.NS": 175,
    "HDFCBANK.NS": 550,
    "ICICIBANK.NS": 700,
    "SBIN.NS": 750,
    "BHARTIARTL.NS": 475,
    "TATAMOTORS.NS": 1425,
    "INFY.NS": 400,
    "HAL.NS": 300,
    "TATAINVEST.NS": 100,
}

DEFAULT_LOT_SIZE = 250

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def black_scholes_merton(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> dict:
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return {"premium": 0.5, "delta": 0.5, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    pdf_d1 = norm_pdf(d1)

    if option_type == "CE":
        premium = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        delta = norm_cdf(d1)
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365.0
    else:  # PE
        premium = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
        delta = norm_cdf(d1) - 1.0
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365.0

    gamma = pdf_d1 / (S * sigma * math.sqrt(T))
    vega = (S * pdf_d1 * math.sqrt(T)) / 100.0

    return {
        "premium": max(round(premium, 2), 0.5),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),
        "vega": round(vega, 2)
    }

def compute_greeks_decay_curve(S: float, K: float, sigma: float, option_type: str = "CE", r: float = 0.07, max_dte: int = 30) -> dict:
    dtes = list(range(max_dte, 0, -1))
    premiums, deltas, thetas = [], [], []

    for dte in dtes:
        T = dte / 365.0
        res = black_scholes_merton(S=S, K=K, T=T, r=r, sigma=sigma, option_type=option_type)
        premiums.append(res["premium"])
        deltas.append(abs(res["delta"]))
        thetas.append(res["theta"])

    return {
        "DTE": dtes,
        "Premium": premiums,
        "Delta": deltas,
        "Theta": thetas
    }

def round_to_strike(price: float, step: float = 50.0) -> float:
    return max(round(price / step) * step, step)

def compute_historical_volatility(df, window: int = 30) -> float:
    if df is None or len(df) < 5:
        return 0.25
    
    log_returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
    daily_std = log_returns.tail(window).std()
    
    if np.isnan(daily_std) or daily_std <= 0:
        return 0.25
        
    annualized_vol = daily_std * np.sqrt(252)
    return float(annualized_vol)

def generate_option_setup(
    symbol: str, 
    spot_price: float, 
    capital: float, 
    max_risk_pct: float, 
    df_history = None,
    option_type: str = "CE", 
    strike_mode: str = "ATM",
    days_to_expiry: int = 14,
    risk_free_rate: float = 0.07
) -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    if spot_price < 500:
        step = 10.0
    elif spot_price < 1500:
        step = 20.0
    elif spot_price < 5000:
        step = 50.0
    else:
        step = 100.0

    atm_strike = round_to_strike(spot_price, step)
    
    if strike_mode == "ITM":
        strike = atm_strike - step if option_type == "CE" else atm_strike + step
    elif strike_mode == "OTM":
        strike = atm_strike + step if option_type == "CE" else atm_strike - step
    else:
        strike = atm_strike

    sigma = compute_historical_volatility(df_history)
    T = max(days_to_expiry, 1) / 365.0
    
    bsm_res = black_scholes_merton(S=spot_price, K=strike, T=T, r=risk_free_rate, sigma=sigma, option_type=option_type)
    bsm_premium = bsm_res["premium"]
    bsm_delta = abs(bsm_res["delta"])
    
    cost_per_lot = bsm_premium * lot_size
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    if lots_to_buy < 1:
        lots_to_buy = 1
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * bsm_premium, 2)
    
    target_account_loss = capital * max_risk_pct
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    
    option_sl_price = max(round(bsm_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(bsm_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)

    decay_curve = compute_greeks_decay_curve(S=spot_price, K=strike, sigma=sigma, option_type=option_type, r=risk_free_rate)
    
    # Measure directional price drift over 5 trading periods
    if df_history is not None and len(df_history) >= 5:
        p_now = float(df_history['Close'].iloc[-1])
        p_past = float(df_history['Close'].iloc[-5])
        drift_pct = (p_now - p_past) / p_past
    else:
        drift_pct = 0.0

    # Direction-Aware Scoring:
    # CALL options reward positive price trend
    # PUT options reward negative price trend
    directional_score = drift_pct * 300.0 if option_type == "CE" else (-drift_pct) * 300.0
    vol_score = (sigma * 100.0) * 0.4
    delta_score = bsm_delta * 30.0

    raw_score = 50.0 + directional_score + vol_score + delta_score
    bsm_score = max(min(int(round(raw_score)), 99), 1)

    return {
        "Instrument": f"{int(strike)} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "BSM Premium": bsm_premium,
        "BSM Delta": bsm_delta,
        "BSM Gamma": bsm_res["gamma"],
        "BSM Theta": bsm_res["theta"],
        "BSM Vega": bsm_res["vega"],
        "BSM Score": bsm_score,
        "Drift %": round(drift_pct * 100, 2),
        "Ann. Volatility": round(sigma * 100, 2),
        "Lot Size": lot_size,
        "Lots": lots_to_buy,
        "Total Qty": total_quantity,
        "Premium Required": total_premium_required,
        "Option SL": option_sl_price,
        "Option Target": option_target_price,
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct,
        "Decay Curve": decay_curve
    }''',

    "components/charts.py": '''import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_candlestick_chart(df, symbol: str):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))

    fig.update_layout(
        template='plotly_dark',
        title=f"{symbol} Price Action",
        xaxis_rangeslider_visible=False,
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='#131722',
        plot_bgcolor='#1E222D'
    )
    return fig

def render_greeks_decay_chart(decay_data: dict, symbol: str, instrument: str):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=(f'{symbol} ({instrument}) — BSM Premium Decay', 'Theta Loss Profile (₹ / Day)'),
        row_width=[0.35, 0.65]
    )

    fig.add_trace(go.Scatter(
        x=decay_data['DTE'], 
        y=decay_data['Premium'], 
        mode='lines+markers', 
        name='Premium (₹)', 
        line=dict(color='#00E676', width=2.5)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=decay_data['DTE'], 
        y=decay_data['Theta'], 
        mode='lines+markers', 
        name='Theta (₹/Day)', 
        fill='tozeroy',
        line=dict(color='#FF5252', width=2)
    ), row=2, col=1)

    fig.update_xaxes(title_text="Days To Expiration (DTE)", autorange="reversed", row=2, col=1)
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Loss (₹ / Day)", row=2, col=1)

    fig.update_layout(
        template='plotly_dark',
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='#131722',
        plot_bgcolor='#1E222D',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig''',

    "app.py": '''import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh BSM Trading Lab", layout="wide", page_icon="⚡")

st.sidebar.header("🎯 Option Contract Config")
opt_type_input = st.sidebar.radio("Option Strategy:", ["Call Option (CE)", "Put Option (PE)"])
selected_option_type = "CE" if "Call" in opt_type_input else "PE"

moneyness_input = st.sidebar.radio("Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)", "OTM (Out-Of-The-Money)"])
if "ITM" in moneyness_input:
    strike_type = "ITM"
elif "OTM" in moneyness_input:
    strike_type = "OTM"
else:
    strike_type = "ATM"

dte_input = st.sidebar.slider("Days to Expiry (DTE):", 1, 30, 14)

st.sidebar.header("🛡️ Account Capital & Risk")
capital = st.sidebar.number_input("Capital (₹):", min_value=1000.0, value=50000.0, step=5000.0)
max_risk_pct_input = st.sidebar.slider("Max Account Risk per Trade (%):", 0.5, 5.0, 2.0, 0.5) / 100.0

universe = load_stock_universe()
now_str = datetime.datetime.now().strftime("%H:%M:%S IST")

st.title("⚡ Medhansh BSM Options & Spot Engine")
st.caption(f"🟢 **PURE BSM MODEL ACTIVE** | Direction: **{selected_option_type}** | Updated: `{now_str}`")

@st.cache_data(ttl=30)
def run_pipeline(ticker_list, cap, risk_pct, opt_type, strike_mode, dte_val):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period="3mo")

    for ticker, df in batch_dfs.items():
        try:
            if df is None or len(df) < 5:
                continue
            
            spot_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else spot_price
            day_change = round(((spot_price - prev_close) / prev_close) * 100, 2)

            setup = generate_option_setup(
                symbol=ticker,
                spot_price=spot_price,
                capital=cap,
                max_risk_pct=risk_pct,
                df_history=df,
                option_type=opt_type,
                strike_mode=strike_mode,
                days_to_expiry=dte_val
            )

            results[ticker] = {
                "Spot Price": spot_price,
                "1D Change %": day_change,
                "5D Trend Drift %": setup["Drift %"],
                "BSM Quant Score": setup["BSM Score"],
                "Instrument": setup["Instrument"],
                "BSM Premium": setup["BSM Premium"],
                "Delta": setup["BSM Delta"],
                "Gamma": setup["BSM Gamma"],
                "Theta": setup["BSM Theta"],
                "Vega": setup["BSM Vega"],
                "Volatility %": setup["Ann. Volatility"],
                "Lots": setup["Lots"],
                "Total Qty": setup["Total Qty"],
                "Capital Required": setup["Premium Required"],
                "Option SL": setup["Option SL"],
                "Option Target": setup["Option Target"],
                "Max Rupee Risk": setup["Max Rupee Risk"],
                "Setup": setup
            }
            chart_dfs[ticker] = df
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline(
    universe, capital, max_risk_pct_input, selected_option_type, strike_type, dte_input
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')
    sorted_df = df_all.sort_values(by=['BSM Quant Score', '5D Trend Drift %'], ascending=[False, False if selected_option_type == "CE" else True])

    top_stock = sorted_df.index[0]
    top_setup = sorted_df.iloc[0]['Setup']

    color = "#00E676" if selected_option_type == "CE" else "#FF5252"

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 18px; border-radius: 8px; border: 2px solid {color}; margin-bottom: 20px;">
        <h2 style="color: {color}; margin: 0;">🏆 TOP BSM {selected_option_type} OPPORTUNITY: {top_stock} — {top_setup['Instrument']}</h2>
        <p style="font-size: 14px; color: #BBB;">Spot: <b>₹{top_setup['Strike']}</b> | Drift: <b>{top_setup['Drift %']}%</b> | Volatility: <b>{top_setup['Ann. Volatility']}%</b> | Quant Score: <b>{top_setup['BSM Score']}/100</b></p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 15px;">
            <div><b>Theoretical Premium:</b> ₹{top_setup['BSM Premium']}</div>
            <div><b>Stop Loss:</b> <span style="color:#FF5252;">₹{top_setup['Option SL']}</span></div>
            <div><b>Target:</b> <span style="color:#00E676;">₹{top_setup['Option Target']}</span></div>
            <div><b>Sizing:</b> <span style="color:{color}; font-weight:bold;">{top_setup['Lots']} Lot ({top_setup['Total Qty']} Qty)</span></div>
            <div><b>Margin Required:</b> ₹{top_setup['Premium Required']:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_equity, tab_options, tab_detail = st.tabs([
        "📈 Equity Spot Rankings", 
        "🎯 Options Engine", 
        "⚡ Contract Deep-Dive"
    ])

    with tab_equity:
        st.subheader(f"📈 Equity Spot Rankings ({selected_option_type} Direction-Aware)")
        st.dataframe(
            sorted_df[['Spot Price', '1D Change %', '5D Trend Drift %', 'Volatility %', 'BSM Quant Score', 'Capital Required', 'Max Rupee Risk']], 
            use_container_width=True
        )

    with tab_options:
        st.subheader(f"🎯 BSM Options Valuation ({selected_option_type})")
        st.dataframe(
            sorted_df[['Instrument', 'Spot Price', 'BSM Premium', 'Delta', 'Gamma', 'Theta', 'Vega', 'Volatility %', 'Lots', 'Total Qty', 'Capital Required', 'Option SL', 'Option Target']], 
            use_container_width=True
        )

    with tab_detail:
        st.subheader("⚡ Contract Deep-Dive & Greeks Visualizer")
        selected_stock = st.selectbox("Choose Instrument:", sorted_df.index.tolist(), index=0)

        if selected_stock:
            info = results[selected_stock]
            setup = info['Setup']
            df_chart = chart_dfs[selected_stock]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Spot Price", f"₹{info['Spot Price']}", f"{info['1D Change %']}%")
                st.metric("BSM Quant Score", f"{info['BSM Quant Score']} / 100")
            with c2:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**BSM Premium:** ₹{setup['BSM Premium']}")
                st.write(f"**Stop Loss:** ₹{setup['Option SL']}")
                st.write(f"**Target:** ₹{setup['Option Target']}")
            with c3:
                st.write(f"**Delta (Δ):** {setup['BSM Delta']}")
                st.write(f"**Gamma (γ):** {setup['BSM Gamma']}")
                st.write(f"**Theta (θ):** ₹{setup['BSM Theta']} / day")
                st.write(f"**Vega (ν):** ₹{setup['BSM Vega']} / % vol")

            st.markdown("---")
            ct1, ct2 = st.tabs(["📉 Price Candlesticks", "⚡ Greeks & Premium Decay"])
            with ct1:
                st.plotly_chart(render_candlestick_chart(df_chart, selected_stock), use_container_width=True)
            with ct2:
                st.plotly_chart(render_greeks_decay_chart(setup['Decay Curve'], selected_stock, setup['Instrument']), use_container_width=True)
else:
    st.error("Market data could not be fetched. Please refresh.")'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ APP REBUILT SUCCESSFULLY!")