import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

# 确保安装了必要的依赖
# pip install dash dash-bootstrap-components pandas

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True)
server = app.server

# 导航菜单组件
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("数据下载", href="/download")),
        dbc.NavItem(dbc.NavLink("策略回测", href="/backtest")),
        dbc.NavItem(dbc.NavLink("配置管理", href="/config")),
    ],
    brand="加密货币交易平台",
    brand_href="/",
    color="primary",
    dark=True,
)

# 数据下载页面布局
download_layout = dbc.Container([
    html.H2("数据下载", className="mt-4 mb-5"),
    dbc.Row([
        dbc.Col([
            dbc.Label("选择交易所"),
            dcc.Dropdown(
                id='exchange-select',
                options=[
                    {'label': 'Binance', 'value': 'binance'},
                    {'label': 'Huobi', 'value': 'huobi'},
                    {'label': 'OKX', 'value': 'okx'}
                ],
                value='binance',
                clearable=False,
                className="mb-4"
            ),
        ], width=4),
        dbc.Col([
            dbc.Label("选择交易对"),
            dcc.Dropdown(
                id='symbol-select',
                options=[
                    {'label': 'BTC/USDT', 'value': 'BTC/USDT'},
                    {'label': 'ETH/USDT', 'value': 'ETH/USDT'},
                    {'label': 'SOL/USDT', 'value': 'SOL/USDT'},
                    {'label': 'ADA/USDT', 'value': 'ADA/USDT'}
                ],
                value='BTC/USDT',
                clearable=False,
                className="mb-4"
            ),
        ], width=4),
        dbc.Col([
            dbc.Label("时间周期"),
            dcc.Dropdown(
                id='timeframe-select',
                options=[
                    {'label': '1分钟', 'value': '1m'},
                    {'label': '5分钟', 'value': '5m'},
                    {'label': '15分钟', 'value': '15m'},
                    {'label': '1小时', 'value': '1h'},
                    {'label': '1天', 'value': '1d'}
                ],
                value='15m',
                clearable=False,
                className="mb-4"
            ),
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label("开始日期"),
            dcc.DatePickerSingle(
                id='start-date',
                date=(datetime.now() - timedelta(days=30)).date(),
                className="mb-4"
            ),
        ], width=4),
        dbc.Col([
            dbc.Label("结束日期"),
            dcc.DatePickerSingle(
                id='end-date',
                date=datetime.now().date(),
                className="mb-4"
            ),
        ], width=4),
        dbc.Col([
            dbc.Label("数据格式"),
            dcc.Dropdown(
                id='format-select',
                options=[
                    {'label': 'CSV', 'value': 'csv'},
                    {'label': 'Excel', 'value': 'excel'},
                    {'label': 'JSON', 'value': 'json'}
                ],
                value='csv',
                clearable=False,
                className="mb-4"
            ),
        ], width=4)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "下载数据",
                id="download-button",
                color="primary",
                size="lg",
                className="mt-2"
            ),
            dcc.Download(id="download-data")
        ], width=12, className="text-center")
    ]),
    dbc.Row([
        dbc.Col([
            html.Div(id="download-status", className="mt-4 text-center")
        ], width=12)
    ])
], fluid=True)

# 策略回测页面布局
backtest_layout = dbc.Container([
    html.H2("策略回测", className="mt-4 mb-5"),
    html.P("策略回测功能正在开发中...", className="text-center text-muted")
], fluid=True)

# 配置管理页面布局
config_layout = dbc.Container([
    html.H2("配置管理", className="mt-4 mb-5"),
    html.P("配置管理功能正在开发中...", className="text-center text-muted")
], fluid=True)

# 应用总体布局
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])

# 页面路由回调
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/download':
        return download_layout
    elif pathname == '/backtest':
        return backtest_layout
    elif pathname == '/config':
        return config_layout
    else:
        return download_layout  # 默认显示数据下载页面

# 数据下载回调
@app.callback(
    [Output("download-data", "data"),
     Output("download-status", "children")],
    Input("download-button", "n_clicks"),
    [State("exchange-select", "value"),
     State("symbol-select", "value"),
     State("timeframe-select", "value"),
     State("start-date", "date"),
     State("end-date", "date"),
     State("format-select", "value")],
    prevent_initial_call=True
)
def download_data(n_clicks, exchange, symbol, timeframe, start_date, end_date, data_format):
    """
    处理数据下载请求
    在实际应用中，这里会调用数据服务获取真实数据
    当前示例返回模拟数据
    """
    # 模拟数据生成
    dates = pd.date_range(start=start_date, end=end_date, freq=timeframe.replace('m', 'T').replace('h', 'H').replace('d', 'D'))
    df = pd.DataFrame({
        'timestamp': dates,
        'open': [30000 + i * 100 for i in range(len(dates))],
        'high': [30100 + i * 100 for i in range(len(dates))],
        'low': [29900 + i * 100 for i in range(len(dates))],
        'close': [30050 + i * 100 for i in range(len(dates))],
        'volume': [100 + i * 5 for i in range(len(dates))]
    })

    # 根据选择的格式准备下载数据
    filename = f"{exchange}_{symbol}_{timeframe}_{start_date}_{end_date}"
    status_message = f"✅ 数据下载成功: {filename}.{data_format}"

    if data_format == 'csv':
        return dcc.send_data_frame(df.to_csv, f"{filename}.csv", index=False), status_message
    elif data_format == 'excel':
        return dcc.send_data_frame(df.to_excel, f"{filename}.xlsx", index=False), status_message
    elif data_format == 'json':
        return dcc.send_data_frame(df.to_json, f"{filename}.json", orient='records'), status_message

if __name__ == '__main__':
    print("启动Dash应用...")
    print("访问地址: http://localhost:8050")
    app.run(debug=True, port=8050)