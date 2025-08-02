import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# 初始化 Dash 应用，使用 Bootstrap 主题
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = '实时股票蜡烛图播放器'

# 模拟实时数据生成函数
def generate_ohlc_data(existing_data, new_points=1, trend_strength=0.1):
    """
    生成模拟的OHLC数据
    参数:
        existing_data: 现有数据DataFrame
        new_points: 要生成的新数据点数
        trend_strength: 趋势强度，范围[-1, 1]
    返回:
        包含新数据的DataFrame
    """
    try:
        if existing_data.empty:
            last_close = 100
            last_date = datetime.now() - timedelta(minutes=1)
        else:
            last_close = existing_data['Close'].iloc[-1]
            last_date = existing_data['Date'].iloc[-1]
            # 检查last_date类型
            if not isinstance(last_date, datetime):
                print(f"Warning: last_date is not a datetime object: {type(last_date)}")
                last_date = datetime.now() - timedelta(minutes=1)

        new_dates = []
        for i in range(new_points):
            try:
                new_date = last_date + timedelta(minutes=i+1)
                new_dates.append(new_date)
            except TypeError as e:
                print(f"Error creating new_date: {e}")
                print(f"last_date type: {type(last_date)}, value: {last_date}")
                new_dates.append(datetime.now() + timedelta(minutes=i+1))

        # 生成带有轻微趋势的价格变动
        base_changes = np.random.uniform(-1, 1, new_points)
        trend_changes = np.cumsum([trend_strength * np.random.uniform(0.5, 1.5) for _ in range(new_points)])
        total_changes = base_changes + trend_changes

        new_closes = [last_close + change for change in total_changes]
        new_opens = [new_closes[i] - np.random.uniform(0, 0.5) if i > 0 else last_close for i in range(new_points)]
        new_highs = [max(new_opens[i], new_closes[i]) + np.random.uniform(0, 1) for i in range(new_points)]
        new_lows = [min(new_opens[i], new_closes[i]) - np.random.uniform(0, 1) for i in range(new_points)]

        new_data = pd.DataFrame({
            'Date': new_dates,
            'Open': new_opens,
            'High': new_highs,
            'Low': new_lows,
            'Close': new_closes
        })

        # 合并现有数据和新数据，并保留最近50根K线
        combined_data = pd.concat([existing_data, new_data]).iloc[-50:]
        return combined_data
    except Exception as e:
        print(f"数据生成错误: {e}")
        import traceback
        traceback.print_exc()
        return existing_data

# 创建初始数据
initial_data = pd.DataFrame({
    'Date': [datetime.now() - timedelta(minutes=50-i) for i in range(50)],
    'Open': [100 + np.random.uniform(-1, 1) for _ in range(50)],
    'High': [100 + np.random.uniform(0, 2) for _ in range(50)],
    'Low': [100 - np.random.uniform(0, 2) for _ in range(50)],
    'Close': [100 + np.random.uniform(-1, 1) for _ in range(50)]
})

# 应用布局
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1('实时股票蜡烛图播放器', className='text-center mb-4'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='candlestick-chart', config={'displayModeBar': True}), width=12)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(
                            dbc.ButtonGroup([
                                dbc.Button(
                                    html.I(className='bi bi-play-fill'),
                                    id='play-button',
                                    color='success',
                                    className='mr-2',
                                    title='播放'
                                ),
                                dbc.Button(
                                    html.I(className='bi bi-pause-fill'),
                                    id='pause-button',
                                    color='warning',
                                    className='mr-2',
                                    title='暂停'
                                ),
                                dbc.Button(
                                    html.I(className='bi bi-stop-fill'),
                                    id='stop-button',
                                    color='danger',
                                    title='停止'
                                )
                            ]),
                            width=4
                        ),
                        dbc.Col(
                            html.Div([
                                html.Label('播放速度 (秒/根K线):', className='mr-2'),
                                dcc.Slider(
                                    id='speed-slider',
                                    min=0.1,
                                    max=2.0,
                                    step=0.1,
                                    value=0.5,
                                    marks={i/10: f'{i/10}' for i in range(1, 21)}
                                )
                            ]),
                            width=4
                        ),
                        dbc.Col(
                            html.Div([
                                html.Label('趋势方向:', className='mr-2'),
                                dcc.Slider(
                                    id='trend-slider',
                                    min=-1.0,
                                    max=1.0,
                                    step=0.1,
                                    value=0.0,
                                    marks={-1: '下跌', 0: '横盘', 1: '上涨'}
                                )
                            ]),
                            width=4
                        )
                    ])
                ])
            ),
            width=12
        )
    ]),
    dcc.Interval(
        id='interval-component',
        interval=500,  # 默认500毫秒更新一次
        n_intervals=0,
        disabled=True  # 初始禁用
    ),
    dcc.Store(id='data-store', data=initial_data.to_dict('records'))
], fluid=True)

# 回调函数
@app.callback(
    [Output('candlestick-chart', 'figure'),
     Output('interval-component', 'disabled'),
     Output('interval-component', 'interval'),
     Output('data-store', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('play-button', 'n_clicks'),
     Input('pause-button', 'n_clicks'),
     Input('stop-button', 'n_clicks'),
     Input('speed-slider', 'value'),
     Input('trend-slider', 'value')],
    [State('data-store', 'data')]
)
def update_chart(n_intervals, play_clicks, pause_clicks, stop_clicks,
                speed_value, trend_value, data_store):
    """
    更新蜡烛图图表
    参数:
        n_intervals: 时间间隔计数
        play_clicks: 播放按钮点击次数
        pause_clicks: 暂停按钮点击次数
        stop_clicks: 停止按钮点击次数
        speed_value: 播放速度值
        trend_value: 趋势方向值
        data_store: 存储的数据
    返回:
        更新后的图表配置、时间间隔禁用状态、新的时间间隔、更新后的数据
    """
    # 确定哪个输入被触发
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # 初始化或获取当前数据
    if data_store is None or trigger_id == 'stop-button':
        # 初始加载或停止按钮被点击，使用初始数据
        df = initial_data
    else:
        # 从存储中获取数据
        df = pd.DataFrame(data_store)
        # 将Date列转换为datetime类型
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except Exception as e:
            print(f"Error converting Date column to datetime: {e}")
            # 如果转换失败，使用当前时间作为备选
            df['Date'] = pd.date_range(end=datetime.now(), periods=len(df), freq='T')

        # 如果是时间间隔触发，生成新数据
        if trigger_id == 'interval-component':
            df = generate_ohlc_data(df, trend_strength=trend_value)

    # 创建蜡烛图
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing_line_color='red',
        decreasing_line_color='green'
    )])

    # 更新布局
    fig.update_layout(
        title=f'股票价格 (最后价格: {df["Close"].iloc[-1]:.2f})',
        xaxis_title='时间',
        yaxis_title='价格',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600
    )

    # 设置Y轴范围，添加一些边距
    y_min = df['Low'].min() * 0.99
    y_max = df['High'].max() * 1.01
    fig.update_yaxes(range=[y_min, y_max])

    # 处理按钮点击
    if trigger_id == 'play-button':
        disabled = False
    elif trigger_id == 'pause-button':
        disabled = True
    elif trigger_id == 'stop-button':
        disabled = True
    else:
        # 如果是其他触发（如滑块），保持当前状态
        disabled = data_store is None

    # 转换速度值为毫秒（speed_value是秒/根K线）
    interval = int(speed_value * 1000)

    return fig, disabled, interval, df.to_dict('records')

# 启动应用
if __name__ == '__main__':
    app.run(debug=True, port=8051)