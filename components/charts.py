import plotly.graph_objects as go
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
    return fig