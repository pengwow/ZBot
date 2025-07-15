from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
from zbot.exchange.exchange import ExchangeFactory
from zbot.utils.dateutils import timestamp_to_datetime, format_datetime

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Apple stock candlestick chart'),
    dcc.Checklist(
        id='toggle-rangeslider',
        options=[{'label': 'Include Rangeslider',
                  'value': 'slider'}],
        value=['slider']
    ),
    dcc.Graph(id="graph"),
])


@app.callback(
    Output("graph", "figure"),
    Input("toggle-rangeslider", "value"))
def display_candlestick(value):
    exchange = ExchangeFactory.create_exchange('binance')
    df = exchange.load_data('BTC/USDT', '15m', "2025-01-01", "2025-05-03")
    # df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv') # replace with your own data source
    df['open_time'] = df['open_time'].apply(lambda x: timestamp_to_datetime(x))
    fig = go.Figure(data=[go.Candlestick(x=df['open_time'],
                open=df['open'], high=df['high'],
                low=df['low'], close=df['close'])
])



    fig.update_layout(
        xaxis_rangeslider_visible='slider' in value
    )

    return fig


app.run(debug=True)
