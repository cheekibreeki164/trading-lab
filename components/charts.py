import plotly.graph_objects as go
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
    return fig