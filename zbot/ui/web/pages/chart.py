import dash
from dash import html, dcc, callback, Input, Output
import plotly.graph_objects as go
import feffery_utils_components as fuc
import feffery_antd_components as fac
import pandas as pd
# 注册pages
dash.register_page(__name__, icon='antd-stock', name='图表')
df = pd.read_csv('/Users/liupeng/PycharmProjects/ZBot/zbot/ui/web/pages/charts.csv')
layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                dcc.Graph(id='candle_chart',figure=go.Figure(data=go.Ohlc(x=df['Date'],
                open=df['AAPL.Open'],
                high=df['AAPL.High'],
                low=df['AAPL.Low'],
                close=df['AAPL.Close']))),
                fac.AntdCenter(
                    "404 Not Found"
                )
            ],
            shadow='always-shadow-light',
            style={
                'borderRadius': 8,
                'background': 'white',
                'padding': 24
            }
        ),
    ],
    style={
        'minHeight': 'calc(100vh - 64px)',
        'background': '#f0f2f5',
        'padding': 20
    }
)
