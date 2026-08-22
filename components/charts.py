import plotly.graph_objects as go
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
    return fig