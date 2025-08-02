import dash
from dash.dependencies import Input, Output, State
from dash import dcc,html
import random
import feffery_antd_components as fac

app = dash.Dash(__name__)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

from feffery_antd_charts.demo_data import stock_data

import feffery_antd_charts as fact

test_data = copy.copy(stock_data)

app.layout = html.Div([
    html.Div([
        fac.AntdCenter([
        fac.AntdButton('刷新', id='refresh-button'),
        fac.AntdIcon(mode='iconfont', scriptUrl='./.js', icon='icon-mti-huifang'),
        ]),

        dcc.Graph(
            id='graph-extendable',
            figure={'layout': {'title': 'Random title',
                               'barmode': 'overlay'},
                    'data': [{'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []}, ]
                    }
        ),
        fact.AntdStock(
    data=test_data,
    xField='trade_date',
    yField=['open', 'close', 'high', 'low'],
    meta={
        'vol': {
            'alias': '成交量',
        },
        'open': {
            'alias': '开盘价',
        },
        'close': {
            'alias': '收盘价',
        },
        'high': {
            'alias': '最高价',
        },
        'low': {
            'alias': '最低价',
        },
    },
    tooltip={
        'fields': ['open', 'close', 'high', 'low', 'vol'],
    },
)
    ]),

    dcc.Interval(
        id='interval-graph-update',
        interval=1000,
        n_intervals=0),
])


@app.callback(
    Output('graph-extendable', 'extendData'),
              [Input('interval-graph-update', 'n_intervals')]
              )
def create_then_extend_single_trace(n_intervals):

    return (dict(x=[
        [n_intervals],
        [n_intervals]
    ],

        y=[
        [n_intervals],
        [n_intervals**2]
    ]
    ),

        [0, 4]

    )


if __name__ == '__main__':
    app.run(debug=True)