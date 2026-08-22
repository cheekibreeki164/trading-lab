import os

files = {
    "engine/options_engine.py": '''import math
import numpy as np
from scipy.stats import norm

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

def black_scholes_merton(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> dict:
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return {"premium": 0.0, "delta": 0.5, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    pdf_d1 = norm.pdf(d1)

    if option_type == "CE":
        premium = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365.0
    else:  # PE
        premium = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1.0
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365.0

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
    return round(price / step) * step

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
    atr: float, 
    capital: float, 
    max_risk_pct: float, 
    df_history = None,
    option_type: str = "CE", 
    strike_mode: str = "ATM",
    days_to_expiry: int = 15,
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
    
    return {
        "Instrument": f"{int(strike)} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "BSM Premium": bsm_premium,
        "BSM Delta": bsm_delta,
        "BSM Gamma": bsm_res["gamma"],
        "BSM Theta": bsm_res["theta"],
        "BSM Vega": bsm_res["vega"],
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
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        subplot_titles=(f'{symbol} Price & Key Moving Averages', 'RSI (14) Indicator'),
        row_width=[0.2, 0.8]
    )

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ), row=1, col=1)

    if 'EMA20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], mode='lines', name='20 EMA', line=dict(color='#00E676', width=1.5)), row=1, col=1)
    if 'SMA50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='50 SMA', line=dict(color='#FFD600', width=1.5)), row=1, col=1)

    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='#29B6F6', width=1.5)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=2, col=1)

    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=500,
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
        subplot_titles=(f'{symbol} ({instrument}) — Premium & Delta Decay Over Time', 'Daily Theta Loss (₹ / Day)'),
        row_width=[0.35, 0.65]
    )

    fig.add_trace(go.Scatter(
        x=decay_data['DTE'], 
        y=decay_data['Premium'], 
        mode='lines+markers', 
        name='Est Premium (₹)', 
        line=dict(color='#00E676', width=2.5)
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=decay_data['DTE'], 
        y=decay_data['Delta'], 
        mode='lines', 
        name='Delta (Delta)', 
        line=dict(color='#29B6F6', width=2, dash='dot')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=decay_data['DTE'], 
        y=decay_data['Theta'], 
        mode='lines+markers', 
        name='Theta (Theta / Day)', 
        fill='tozeroy',
        line=dict(color='#FF5252', width=2)
    ), row=2, col=1)

    fig.update_xaxes(title_text="Days To Expiration (DTE)", autorange="reversed", row=2, col=1)
    fig.update_yaxes(title_text="Price / Delta", row=1, col=1)
    fig.update_yaxes(title_text="Rupees / Day", row=2, col=1)

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
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

market_mode = st.sidebar.selectbox("📈 Asset Class / Mode:", ["Equity Spot (Shares)", "NSE Options Engine (BSM)"])

st.sidebar.header("🎯 Trading Strategy Profiles")
trade_style = st.sidebar.radio(
    "Select Horizon:",
    ["⚡ Intraday Breakdown", "📈 Swing Trade Setup", "🏦 Long-Term Breakout"],
    index=0
)

if "Intraday" in trade_style:
    default_period = "1mo"
    default_risk = 2.0
    default_lev = "5x (Intraday MIS Leverage)"
elif "Swing" in trade_style:
    default_period = "6mo"
    default_risk = 2.0
    default_lev = "1x (Cash Delivery)"
else:
    default_period = "2y"
    default_risk = 3.0
    default_lev = "1x (Cash Delivery)"

st.sidebar.header("🛡️ Capital & Risk Management")
capital = st.sidebar.number_input("Total Cash Balance (₹):", min_value=500.0, value=4000.0, step=500.0)
max_risk_pct_input = st.sidebar.slider("Max Balance Risk Per Trade (%):", 0.5, 5.0, default_risk, 0.5) / 100.0

if market_mode == "Equity Spot (Shares)":
    leverage_option = st.sidebar.radio("Leverage Mode:", ["1x (Cash Delivery)", "5x (Intraday MIS Leverage)"], index=1 if "5x" in default_lev else 0)
    leverage_multiplier = 5.0 if "5x" in leverage_option else 1.0
    buying_power = capital * leverage_multiplier
    selected_option_type = "CE"
    strike_type = "ATM"
    dte_input = 14
else:
    leverage_multiplier = 1.0
    buying_power = capital
    st.sidebar.header("📊 Options Strategy Specs")
    opt_selection_mode = st.sidebar.radio("Contract Selection Mode:", ["Auto-Select (Trend Based)", "Call Option (CE)", "Put Option (PE)"])
    option_strike_mode = st.sidebar.radio("Option Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)", "OTM (Out-Of-The-Money)"])
    
    if "ITM" in option_strike_mode:
        strike_type = "ITM"
    elif "OTM" in option_strike_mode:
        strike_type = "OTM"
    else:
        strike_type = "ATM"
        
    dte_input = st.sidebar.slider("Days to Expiry (DTE):", 1, 30, 14)
    selected_option_type = opt_selection_mode

max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Buying / Capital Allocated:** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Max Rupee Loss Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 30)

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title(f"⚡ Medhansh TradingLab — {market_mode}")
st.caption(f"🟢 **BSM OPTIONS ENGINE + GREEKS VISUALIZER ACTIVE** | Last Update: `{now_str}`")

@st.cache_data(ttl=20)
def run_pipeline(ticker_list, capital_input, leverage_input, risk_pct, period_lookback, mode, opt_mode, strike_mode_val, dte_val):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period=period_lookback)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition, df_ind)
            
            if mode == "Equity Spot (Shares)":
                setup = generate_trade_setup(
                    condition.get('Price', 0), 
                    condition.get('ATR', 0), 
                    total_capital=capital_input, 
                    leverage=leverage_input,
                    max_risk_pct=risk_pct
                )
            else:
                if "Call" in opt_mode:
                    opt_type = "CE"
                elif "Put" in opt_mode:
                    opt_type = "PE"
                else:
                    opt_type = "CE" if condition.get('Daily_Change', 0) >= 0 else "PE"
                    
                setup = generate_option_setup(
                    symbol=ticker,
                    spot_price=condition.get('Price', 0),
                    atr=condition.get('ATR', 0),
                    capital=capital_input,
                    max_risk_pct=risk_pct,
                    df_history=df_ind,
                    option_type=opt_type,
                    strike_mode=strike_mode_val,
                    days_to_expiry=dte_val
                )
            
            results[ticker] = {
                "Price": condition.get('Price'),
                "1D Change %": condition.get('Daily_Change', 0),
                "Score": scores['total'],
                "Status": scores['status'],
                "Pattern": scores['pattern'],
                "Preferred_Buy": condition.get('Preferred_Buy', False),
                "RSI": condition.get('RSI'),
                "RVOL": condition.get('RVOL'),
                "ATR": condition.get('ATR'),
                "Setup": setup,
                "Breakdown": scores['breakdown']
            }
            chart_dfs[ticker] = df_ind
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline(
    universe, capital, leverage_multiplier, max_risk_pct_input, default_period, market_mode, selected_option_type, strike_type, dte_input
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    if market_mode == "Equity Spot (Shares)":
        st.markdown(f"""
        <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
            <h2 style="color: #00E676; margin: 0;">🏆 TOP SPOT PICK: {winner_ticker} ({winner_setup['Leverage']} Mode)</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Pattern:</b> {winner_info['Pattern']} | <b>Score:</b> {winner_info['Score']}/50</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>Entry Price:</b> ₹{winner_setup['Entry']}</div>
                <div><b>Stop Loss ({winner_setup['SL_Pct']}% Drop):</b> <span style="color:#FF5252;">₹{winner_setup['Stop Loss']}</span></div>
                <div><b>Target Price:</b> <span style="color:#00E676;">₹{winner_setup['Target']}</span></div>
                <div><b>Shares to Buy:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Shares to Buy']} Shares</b></span></div>
                <div><b>Margin Required:</b> ₹{winner_setup['Margin Required']:,}</div>
                <div><b>Max Loss Risk:</b> ₹{winner_setup['Max Rupee Risk']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
            <h2 style="color: #00E676; margin: 0;">🎯 BSM OPTION PICK: {winner_ticker} {winner_setup['Instrument']}</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Spot Price:</b> ₹{winner_info['Price']} | <b>Vol:</b> {winner_setup['Ann. Volatility']}% | <b>Delta:</b> {winner_setup['BSM Delta']} | <b>Gamma:</b> {winner_setup['BSM Gamma']} | <b>Theta:</b> ₹{winner_setup['BSM Theta']}/day | <b>Vega:</b> ₹{winner_setup['BSM Vega']}</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>BSM Option Premium:</b> ₹{winner_setup['BSM Premium']}</div>
                <div><b>Premium Stop Loss:</b> <span style="color:#FF5252;">₹{winner_setup['Option SL']}</span></div>
                <div><b>Premium Target:</b> <span style="color:#00E676;">₹{winner_setup['Option Target']}</span></div>
                <div><b>Lots to Buy:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Lots']} Lot ({winner_setup['Total Qty']} Qty)</b></span></div>
                <div><b>Capital Allocated:</b> ₹{winner_setup['Premium Required']:,}</div>
                <div><b>Max Rupee Risk:</b> ₹{winner_setup['Max Rupee Risk']} ({winner_setup['Risk Pct']}%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Preferred Breakout Picks", "📊 Full Universe Screener"])
    
    with tab1:
        st.subheader("🔥 High-Conviction Setups")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)
        else:
            st.info("No stocks currently meet strict breakout criteria.")

    with tab2:
        st.subheader("📊 Stock Universe Screener")
        st.dataframe(sorted_df[sorted_df['Score'] >= min_score][['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)

    st.markdown("---")
    
    all_available = sorted_df.index.tolist()
    selected_stock = st.selectbox("Inspect Setup & Technical Chart for Any Stock:", all_available, index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Spot Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Algo Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Technical Indicators")
            st.write(f"**Pattern:** {stock_info['Pattern']}")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
            st.write(f"**14-Day ATR:** ₹{stock_info['ATR']}")
        with col3:
            st.markdown(f"### {'BSM Option Model Output' if market_mode != 'Equity Spot (Shares)' else 'Equity Spot Plan'}")
            setup = stock_info['Setup']
            if market_mode == "Equity Spot (Shares)":
                st.write(f"**Entry:** ₹{setup['Entry']}")
                st.write(f"**Stop Loss:** ₹{setup['Stop Loss']} (-{setup['SL_Pct']}%)")
                st.write(f"**Target:** ₹{setup['Target']}")
                st.write(f"**Position:** {setup['Shares to Buy']} Shares")
                st.write(f"**Capital Needed:** ₹{setup['Margin Required']:,}")
            else:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**BSM Est. Premium:** ₹{setup['BSM Premium']}")
                st.write(f"**Delta:** {setup['BSM Delta']}")
                st.write(f"**Gamma:** {setup['BSM Gamma']}")
                st.write(f"**Theta:** ₹{setup['BSM Theta']} / day")
                st.write(f"**Vega:** ₹{setup['BSM Vega']} per 1% vol")
                st.write(f"**Ann. Volatility:** {setup['Ann. Volatility']}%")
                st.write(f"**Option SL:** ₹{setup['Option SL']}")
                st.write(f"**Option Target:** ₹{setup['Option Target']}")
                st.write(f"**Position:** {setup['Lots']} Lot ({setup['Total Qty']} Contracts)")
                st.write(f"**Capital Needed:** ₹{setup['Premium Required']:,}")
                st.write(f"**Max Rupee Risk:** ₹{setup['Max Rupee Risk']}")
        
        st.markdown("---")
        
        if market_mode != "Equity Spot (Shares)":
            chart_tab1, chart_tab2 = st.tabs(["📉 Price Candlestick Chart", "⚡ Interactive Greeks Decay Simulator"])
            with chart_tab1:
                st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
            with chart_tab2:
                st.subheader(f"⚡ Black-Scholes Greeks Decay Profile: {selected_stock} {setup['Instrument']}")
                st.caption("Visualizing theoretical option price decay, Delta sensitivity, and non-linear Theta loss as Expiry approaches (30 DTE → 1 DTE).")
                st.plotly_chart(render_greeks_decay_chart(setup['Decay Curve'], selected_stock, setup['Instrument']), use_container_width=True)
        else:
            st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
else:
    st.error("Failed to load market data. Please refresh or check connection.")'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ FIXED: f-string syntax error resolved!")