import os

files = {
    "requirements.txt": """streamlit
yfinance
pandas
numpy
plotly""",

    "data/stocks.csv": """Ticker
RELIANCE.NS
TCS.NS
HDFCBANK.NS
ICICIBANK.NS
BHARTIARTL.NS
INFY.NS
ITC.NS
SBIN.NS
LTIM.NS
HINDUNILVR.NS
LT.NS
BAJFINANCE.NS
HCLTECH.NS
MARUTI.NS
SUNPHARMA.NS
KOTAKBANK.NS
TATAMOTORS.NS
AXISBANK.NS
NTPC.NS
ONGC.NS
TITAN.NS
ADANIENT.NS
POWERGRID.NS
HAL.NS
ULTRACEMCO.NS
COALINDIA.NS
BAJAJFINSV.NS
TATASTEEL.NS
M&M.NS
ADANIPORTS.NS
JSWSTEEL.NS
GRASIM.NS
HDFCLIFE.NS
TECHM.NS
BRITANNIA.NS
HINDALCO.NS
ADANIPOWER.NS
INDUSINDBK.NS
DRREDDY.NS
EICHERMOT.NS
DIVISLAB.NS
CIPLA.NS
BPCL.NS
SBILIFE.NS
TATACONSUM.NS
BAJAJ-AUTO.NS
APOLLOHOSP.NS
IOC.NS
WIPRO.NS
BEL.NS
DLF.NS
VBL.NS
SIEMENS.NS
IRFC.NS
TRENT.NS
GAIL.NS
PFC.NS
REC.NS
CHOLAFIN.NS
PIDILITIND.NS
AMBUJACEM.NS
TATAELXSI.NS
SHREECEM.NS
BANKBARODA.NS
GODREJPROP.NS
PNB.NS
INDIGO.NS
ABB.NS
HEROMOTOCO.NS
TORNTPHARM.NS
VEDL.NS
DABUR.NS
CANBK.NS
NHPC.NS
MOTHERSON.NS
SHRIRAMFIN.NS
HAVELLS.NS
ICICIPRULI.NS
NMDC.NS
BERGEPAINT.NS
POLYCAB.NS
TATACOMM.NS
MARICO.NS
ZYDUSLIFE.NS
ICICIGI.NS
SRF.NS
IOB.NS
MUTHOOTFIN.NS
UNIONBANK.NS
BOSCHLTD.NS
JINDALSTEL.NS
COLPAL.NS
TUBEINVEST.NS
TATAINVEST.NS
LODHA.NS
BHEL.NS
INDUSTOWER.NS
IDFCFIRSTB.NS
ASTRAL.NS
SOLARINDS.NS
MAXHEALTH.NS
CGPOWER.NS
GMRINFRA.NS
PAYTM.NS
IRCTC.NS
OFSS.NS
PATANJALI.NS
SJVN.NS
RECLTD.NS
YESBANK.NS
INDIANB.NS
UBL.NS
ASHOKLEY.NS
PIIND.NS
OBEROIRLTY.NS
BALKRISIND.NS
M&MFIN.NS
TIINDIA.NS
SUPREMEIND.NS
AUROPHARMA.NS
ACC.NS
POLICYBAZR.NS
FACT.NS
CUMMINSIND.NS
UPL.NS
PERSISTENT.NS
NYKAA.NS
MPHASIS.NS
LINDEINDIA.NS
AUBANK.NS
KALYANKJIL.NS
LUPIN.NS
MAHABANK.NS
SUZLON.NS
SCHAEFFLER.NS
PRESTIGE.NS
ABCAPITAL.NS
KPRMILL.NS
TATACHEM.NS
APARINDS.NS
VOLTAS.NS
GIPCL.NS
CROMPTON.NS
COFORGE.NS
GLENMARK.NS
HUDCO.NS
DELHIVERY.NS
ALOKINDS.NS
GODREJCP.NS
FEDERALBNK.NS
EXIDEIND.NS
PHOENIXLTD.NS
FORTIS.NS
MFSL.NS
SUNDARMFIN.NS
DALBHARAT.NS
JSL.NS
IRB.NS
LALPATHLAB.NS
METROPOLIS.NS
DEEPAKNTR.NS
PVRINOX.NS
KEI.NS
GUJGASLTD.NS
AARTIIND.NS
IPCALAB.NS
PETRONET.NS
PAGEIND.NS
ESCORTS.NS
SUMICHEM.NS
COROMANDEL.NS
CENTRALBK.NS
BALRAMCHIN.NS
CHAMBLFERT.NS
NATIONALUM.NS
IDBI.NS
UCOBANK.NS
RADICO.NS
STARHEALTH.NS
ENDURANCE.NS
GLAXO.NS
MANYAVAR.NS
GLS.NS
JBCHEPHARM.NS
SYNGENE.NS
AIAENG.NS
ATGL.NS
SONACOMS.NS
BIOCON.NS
BATAINDIA.NS
IEX.NS
TRIDENT.NS
LAURUSLABS.NS
CREDITACC.NS
KNRCON.NS
IIFL.NS
POONAWALLA.NS
AMBER.NS
PPLPHARMA.NS
WHIRLPOOL.NS
GRINDWELL.NS
KAYNES.NS
J&KBANK.NS
CARBORUNIV.NS
ECLERX.NS
CDSL.NS
ANGELONE.NS
BSOFT.NS
MCX.NS
CENTURYPLY.NS
RBLBANK.NS
KEC.NS
CYIENT.NS
RAINBOW.NS
GSPL.NS
RCF.NS
CERA.NS
PRAJIND.NS
HINDCOPPER.NS
RAYMOND.NS
MEDANTA.NS
SONATSOFTW.NS
AETHER.NS
ROUTE.NS
FINPIPE.NS
BLS.NS
GNFC.NS
CLEAN.NS
KPITTECH.NS
EIDPARRY.NS
NLCINDIA.NS
ERIS.NS
JWL.NS
SUVENPHAR.NS
HAPPSTMNDS.NS
SANGHVIMOV.NS
JUBLFOOD.NS
MAPMYINDIA.NS
ASAHIINDIA.NS
GRAVITA.NS
TIMKEN.NS
MAZDOCK.NS
GRANULES.NS
VIPIND.NS
GRSE.NS
CEATLTD.NS
COCHINSHIP.NS
RKFORGE.NS
HINDPETRO.NS
LEMONTREE.NS
TEJASNET.NS
REDINGTON.NS
ENGINERSIN.NS
CGCL.NS
DATAPATTNS.NS
SHOPERSTOP.NS
TRITURBINE.NS
TANLA.NS
FSL.NS
CRAFTSMAN.NS
SKFINDIA.NS
KIRLOSENG.NS
GESHIP.NS
FINEORG.NS
CUB.NS
EQUITASBNK.NS
KARURVYSYA.NS
UTIAMC.NS
NOCIL.NS
DCMSHRIRAM.NS
MAHLIFE.NS
JKCEMENT.NS
BIRLACORPN.NS
GODFRYPHLP.NS
SCHNEIDER.NS
TIIL.NS
SHARDACROP.NS
AARTIDRUGS.NS
PRINCEPIPE.NS
RAIN.NS
THYROCARE.NS
PRUDENT.NS
LUXIND.NS
BORORENEW.NS
JYOTHYLAB.NS
GREENPANEL.NS
MASTEK.NS
NILKAMAL.NS
SIS.NS
VAIBHAVGBL.NS
HFCL.NS
SUPRAJIT.NS
CANFINHOME.NS
HOMEFIRST.NS
RITES.NS
IBREALEST.NS""",

    "engine/__init__.py": "",
    "components/__init__.py": "",

    "engine/data_loader.py": '''import pandas as pd
import os

def load_stock_universe(file_path: str = "data/stocks.csv") -> list:
    if not os.path.exists(file_path):
        return ["RELIANCE.NS", "SBIN.NS", "HAL.NS", "TATAMOTORS.NS"]
    df = pd.read_csv(file_path)
    if "Ticker" in df.columns:
        return df["Ticker"].dropna().unique().tolist()
    return []''',

    "engine/market_data.py": '''import yfinance as yf
import pandas as pd

def fetch_batch_market_data(tickers: list, period: str = "6mo") -> dict:
    try:
        data = yf.download(tickers, period=period, group_by='ticker', threads=True, progress=False)
        stock_dfs = {}
        
        if len(tickers) == 1:
            ticker = tickers[0]
            df = data.dropna()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if not df.empty:
                stock_dfs[ticker] = df
        else:
            for ticker in tickers:
                try:
                    if ticker in data.columns.levels[0]:
                        df = data[ticker].dropna()
                        if not df.empty and len(df) >= 50:
                            stock_dfs[ticker] = df
                except Exception:
                    continue
                    
        return stock_dfs
    except Exception as e:
        print(f"Error fetching batch data: {e}")
        return {}''',

    "engine/indicators.py": '''import pandas as pd
import numpy as np

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Moving Averages
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # ATR (14)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # RVOL
    df['Vol_SMA20'] = df['Volume'].rolling(window=20).mean()
    df['RVOL'] = df['Volume'] / df['Vol_SMA20']
    
    # Daily Change %
    df['Daily_Change_Pct'] = df['Close'].pct_change() * 100
    
    return df''',

    "engine/analyzer.py": '''import pandas as pd

def extract_latest_condition(df: pd.DataFrame, ticker: str) -> dict:
    if df.empty or len(df) < 50:
        return {}
    
    latest = df.iloc[-1]
    
    def safe_float(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)

    close_price = safe_float(latest['Close'])
    sma20 = safe_float(latest['SMA20'])
    sma50 = safe_float(latest['SMA50'])
    rsi = safe_float(latest['RSI'])
    rvol = safe_float(latest['RVOL'])
    atr = safe_float(latest['ATR'])
    macd = safe_float(latest['MACD'])
    macd_sig = safe_float(latest['MACD_Signal'])
    daily_change = safe_float(latest['Daily_Change_Pct'])
    
    is_macd_bullish = macd > macd_sig
    is_trend_bullish = close_price > sma20 > sma50
    is_momentum_hot = 55 <= rsi <= 72
    is_volume_breakout = rvol >= 1.3
    
    is_buy_candidate = is_trend_bullish and is_momentum_hot and is_volume_breakout and is_macd_bullish

    return {
        "Ticker": ticker,
        "Price": round(close_price, 2),
        "Daily_Change": round(daily_change, 2),
        "SMA20": round(sma20, 2),
        "SMA50": round(sma50, 2),
        "RSI": round(rsi, 2),
        "ATR": round(atr, 2),
        "RVOL": round(rvol, 2),
        "MACD_Bullish": is_macd_bullish,
        "Preferred_Buy": is_buy_candidate
    }''',

    "engine/scoring.py": '''def score_market_condition(data: dict) -> dict:
    if not data or 'Price' not in data or data['Price'] is None:
        return {"total": 0, "status": "NO DATA", "breakdown": {}}
    
    scores = {}
    
    # 1. Trend Score (Max 10)
    if data['Price'] > data['SMA20'] > data['SMA50']:
        scores['Trend'] = 10
    elif data['Price'] > data['SMA20']:
        scores['Trend'] = 6
    else:
        scores['Trend'] = 2
        
    # 2. Momentum Score (Max 10)
    if 55 <= data['RSI'] <= 70:
        scores['Momentum'] = 10
    elif 45 <= data['RSI'] < 55:
        scores['Momentum'] = 7
    else:
        scores['Momentum'] = 3
        
    # 3. Volume Score (Max 10)
    if data['RVOL'] >= 1.5:
        scores['Volume'] = 10
    elif data['RVOL'] >= 1.0:
        scores['Volume'] = 6
    else:
        scores['Volume'] = 2
        
    # 4. Volatility Risk Score (Max 10)
    atr_pct = (data['ATR'] / data['Price']) * 100
    if atr_pct <= 3.0:
        scores['Risk'] = 10
    elif atr_pct <= 5.0:
        scores['Risk'] = 6
    else:
        scores['Risk'] = 3
        
    # 5. MACD Confirmation (Max 10)
    scores['MACD'] = 10 if data.get('MACD_Bullish', False) else 4
    
    total_score = sum(scores.values())
    
    if data.get('Preferred_Buy', False) or total_score >= 42:
        status = "MUST BUY 🔥"
    elif total_score >= 32:
        status = "WATCH 👁️"
    else:
        status = "WEAK ❌"
        
    return {"total": total_score, "status": status, "breakdown": scores}''',

    "engine/setup_generator.py": '''def generate_trade_setup(price: float, atr: float, risk_reward: float = 2.0) -> dict:
    if not price or not atr:
        return {"Entry": 0, "Stop Loss": 0, "Target": 0, "Risk Reward": "N/A"}
        
    stop_loss = round(price - (1.5 * atr), 2)
    risk = price - stop_loss
    target = round(price + (risk * risk_reward), 2)
    return {"Entry": price, "Stop Loss": stop_loss, "Target": target, "Risk Reward": f"{risk_reward}:1"}''',

    "components/charts.py": '''import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def render_candlestick_chart(df: pd.DataFrame, ticker: str):
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        subplot_titles=(f"{ticker} Price & Trend", "RSI (14)", "MACD Indicator"), 
        row_heights=[0.5, 0.25, 0.25]
    )
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], name="SMA 20", line=dict(color='orange', width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name="SMA 50", line=dict(color='blue', width=1.5)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, row=2, col=1, line_dash="dash", line_color="red", opacity=0.5)
    fig.add_hline(y=30, row=2, col=1, line_dash="dash", line_color="green", opacity=0.5)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name="MACD", line=dict(color='cyan', width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name="Signal", line=dict(color='magenta', width=1.5)), row=3, col=1)
    
    fig.update_layout(xaxis_rangeslider_visible=False, height=650, margin=dict(l=20, r=20, t=40, b=20), template="plotly_dark")
    return fig''',

    "app.py": '''import streamlit as st
import pandas as pd
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="👑")
st.title("👑 Medhansh TradingLab — Daily Winner Terminal")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
st.sidebar.info(f"Market Universe: **{len(universe)}** Stocks")

min_score = st.sidebar.slider("Minimum TradingLab Score:", 0, 50, 30)
scan_button = st.sidebar.button("⚡ Lock In Today's Scan", type="primary")

@st.cache_data(ttl=43200)
def run_pipeline(ticker_list):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition)
            setup = generate_trade_setup(condition.get('Price', 0), condition.get('ATR', 0))
            
            results[ticker] = {
                "Price": condition.get('Price'),
                "1D Change %": condition.get('Daily_Change', 0),
                "Score": scores['total'],
                "Status": scores['status'],
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

if scan_button or 'results' not in st.session_state:
    with st.spinner("Locking in daily market data to determine today's #1 winner..."):
        st.session_state.results, st.session_state.chart_dfs = run_pipeline(universe)

results, chart_dfs = st.session_state.results, st.session_state.chart_dfs

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    # BANNER: TOP WINNER OF THE DAY
    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🏆 OFFICIAL WINNER OF THE DAY: {winner_ticker}</h2>
        <p style="font-size: 16px; color: #CCCCCC;">Highest conviction stock selected based on maximum TradingLab Score, volume surge, and trend momentum.</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            <div><b>Current Price:</b> ₹{winner_info['Price']} ({winner_info['1D Change %']}%)</div>
            <div><b>TradingLab Score:</b> {winner_info['Score']}/50</div>
            <div><b>RVOL:</b> {winner_info['RVOL']}x</div>
            <div><b>Target:</b> ₹{winner_setup['Target']}</div>
            <div><b>Stop Loss:</b> ₹{winner_setup['Stop Loss']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Top Buy Picks", "📊 Full Market Screener"])
    
    with tab1:
        st.subheader("🔥 High-Conviction Candidates")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)
        else:
            st.info("No other stocks meet 100% of the strict breakout filters today.")

    with tab2:
        st.subheader("📊 All Stock Screener")
        st.dataframe(sorted_df[sorted_df['Score'] >= min_score][['Price', '1D Change %', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)

    st.markdown("---")
    
    all_available = sorted_df.index.tolist()
    selected_stock = st.selectbox("Inspect Chart & Plan for Any Stock:", all_available, index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Metrics")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
            st.write(f"**ATR:** ₹{stock_info['ATR']}")
        with col3:
            st.markdown("### Plan")
            setup = stock_info['Setup']
            st.write(f"**Entry:** ₹{setup['Entry']}")
            st.write(f"**Stop Loss:** ₹{setup['Stop Loss']}")
            st.write(f"**Target:** ₹{setup['Target']}")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ Fixed unsafe_allow_html argument!")
