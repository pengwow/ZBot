import json
import time
import pandas as pd
from calendar import c
from click.utils import R
import numpy as np
from datetime import datetime, timedelta
import dash
from dash import html, dcc, callback, Input, Output, State, ctx, callback_context
import feffery_utils_components as fuc
import feffery_antd_components as fac
from zbot.services.backtest import get_strategy_class_names, Backtest
from zbot.models.backtest import BacktestRecord
from zbot.ui.web.utils.feedback import MessageManager
from zbot.ui.web.utils.candlestick_chart import create_candlestick_chart
# 注册pages
dash.register_page(__name__, icon='antd-fund-projection-screen', name='回测')


strategy_params = []
strategy_metrics = []
strategy_trades = []
strategy_strategy = []

# 获取回测记录
def get_backtest_results():
    backtest_records = BacktestRecord.select().order_by(
        BacktestRecord.created_at.desc())
    backtest_records = [record.to_dict() for record in backtest_records]
    # print(backtest_records)

    return backtest_records


# 刷新表格控件数据
def refresh_table_data():
    backtest_results = get_backtest_results()
    backtest_tab_data = [{
        'id': record['id'],
        'strategy_name': record['strategy_name'],
        'created_at': record['created_at'],
        'max_drawdown': record['max_drawdown'],
        'total_return': record['total_return'],
        'action': [
            {'content': '加载', 'type': 'primary',
                'custom': {"load": f"{record['id']}"}},
            {'content': '删除', 'type': 'primary', 'danger': True,
             'popConfirmProps': {
                        'title': '是否删除该回测记录？',
                        'okText': '确认',
                        'cancelText': '取消',
             },
                'custom': {"deleted": f"{record['id']}"}},
        ]
    } for record in backtest_results]
    return backtest_tab_data


def get_strategy():
    class_names = get_strategy_class_names()
    return [{'label': f"{item['name']} ({item['filename']})", 'value': item['name']} for item in class_names]


layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                fac.AntdCenter(
                    fac.AntdSpace(
                        [
                            fac.AntdButton(
                                '运行回测', icon=fac.AntdIcon(icon='antd-desktop'), id='run-backtest-view-btn'),
                            fac.AntdButton(
                                '结果分析', icon=fac.AntdIcon(icon='antd-file-search'), disabled=True, id='analyze-result-btn'),
                            fac.AntdButton(
                                '可视化结果', icon=fac.AntdIcon(icon='antd-dot-chart'), disabled=True, id='visualize-result-btn'),
                        ]
                    )
                ),
                fac.AntdDivider(),
                html.Div(
                    children=[],
                    id='run-backtest-view'
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

#


def render_content_backtest():
    symbols = ctx.global_vars['symbols']
    strategy_options = get_strategy()
    backtest_results = refresh_table_data()
    return html.Div(
        children=[
            fac.AntdCenter(
                [
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(
                                [
                                    html.Div([
                                        fac.AntdSelect(
                                            id="backtest_strategy",
                                            options=strategy_options, style={'width': '300px'}),
                                        fac.AntdButton(id="refresh-backtest-btn",
                                                       icon=fac.AntdIcon(icon='antd-reload')),
                                    ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px', 'flexWrap': 'nowrap'})
                                ],
                                label='策略',
                                # labelCol={'span': 4}
                            ),
                            fac.AntdFormItem(
                                fac.AntdSelect(
                                    id='symbol', options=symbols),
                                label='货币对'
                            ),
                            fac.AntdFormItem(
                                [
                                    fac.AntdSelect(
                                        options=["1m", "5m", "15m",
                                                 "30m", "60m", "1h", "1d"],
                                        style={'width': '150px'},
                                        id='timeframe'
                                    ),
                                ],
                                label='时间框架'
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(id='initial_cash'),
                                label='初始资金'
                            ),
                            fac.AntdFormItem(
                                [
                                    html.Div([
                                        fac.AntdDatePicker(id='start_date', placeholder='请选择开始时间', style={
                                            'width': '150px'}),
                                        fac.AntdDatePicker(id='end_date', placeholder='请选择结束时间', style={
                                            'width': '150px'}),
                                    ], style={'display': 'flex', 'gap': '15px'})
                                ],
                                label='时间范围',
                                style={'width': '350px'}
                            ),
                            fac.AntdButton(
                                '运行回测', id='run_backtest_btn', type='primary', block=True),
                            fac.AntdSpin(fac.AntdText(
                                id='run_backtest_spin_output'), text='回测中',  fullscreen=True),
                        ],
                        id='run_backtest_form',
                        enableBatchControl=True,
                        values={
                            'timeframe': '15m',
                            'start_date': '',
                        }
                    ),
                ]
            ),
            html.H1('回测记录'),
            html.Div(
                children=[
                    fac.AntdTable(
                        id='candle_table',
                        columns=[
                            {'title': 'ID', 'dataIndex': 'id'},
                            {'title': '策略', 'dataIndex': 'strategy_name'},
                            {'title': '回测时间', 'dataIndex': 'created_at'},
                            {'title': '最大回撤', 'dataIndex': 'max_drawdown'},
                            {'title': '总收益率', 'dataIndex': 'total_return'},
                            {'title': '动作', 'dataIndex': 'action',
                             'renderOptions': {'renderType': 'button'}},
                        ], data=backtest_results, style={'padding': 5}
                    ),
                ], id='candle_table_div'
            ),
        ]
    )


def render_content_analyze(strategy_params: list, strategy_metrics: list, strategy_trades: list):
    return html.Div(
        children=[
            fac.AntdCenter([
                fac.AntdSpace([
                    fac.AntdSpace([
                        fac.AntdSpace([
                            html.H2('策略参数'),
                            fac.AntdTable(
                                id='strategy_params_table',
                                columns=[
                                    {'title': '参数', 'dataIndex': 'param',
                                        'align': 'left'},
                                    {'title': '值', 'dataIndex': 'value',
                                        'align': 'left'},
                                ],
                                data=strategy_params,
                                style={'width': '500px'},
                                pagination=False
                            ),
                        ], direction='vertical'),
                        fac.AntdSpace([
                            html.H2('策略指标'),
                            fac.AntdTable(
                                id='strategy_metrics_table',
                                columns=[
                                    {'title': '指标', 'dataIndex': 'metric',
                                     'align': 'left'},
                                    {'title': '值', 'dataIndex': 'value',
                                        'align': 'left'},
                                ],
                                data=strategy_metrics,
                                style={'width': '500px'},
                                pagination=False
                            ),
                        ], direction='vertical'),
                    ], align='start'),
                    fac.AntdSpace([
                        html.H2('交易记录'),
                        fac.AntdTable(
                            id='trade_table',
                            columns=[
                                {'title': '入场时间', 'dataIndex': 'EntryTime'},
                                {'title': '出场时间', 'dataIndex': 'ExitTime'},
                                {'title': '持续时间', 'dataIndex': 'Duration'},
                                {'title': '交易方向', 'dataIndex': 'Direction'},
                                {'title': '开仓价格', 'dataIndex': 'EntryPrice'},
                                {'title': '平仓价格', 'dataIndex': 'ExitPrice'},
                                {'title': '止损', 'dataIndex': 'SL'},
                                {'title': '止盈', 'dataIndex': 'TP'},
                                {'title': '仓位大小', 'dataIndex': 'Size'},
                                {'title': '盈亏', 'dataIndex': 'PnL'},
                                {'title': '收益率', 'dataIndex': 'ReturnPct'},
                                {'title': '标签', 'dataIndex': 'Tag'},
                            ], data=strategy_trades, style={'width': '1000px'})], direction='vertical'),
                ], direction='vertical'),
            ]),
        ]
    )


def render_content_visualize(strategy_trades: list, strategy_strategy: list):
    # df = pd.DataFrame(strategy_trades)
    # 初始化数据，将strategy_trades中的数据转换为candlestick_chart需要的格式
    chart_data = []
    for data in strategy_strategy:
        # 添加错误处理，确保键存在
        try:
            chart_data.append({
                'Date': data.get('Date', '') if data.get('Date', '') else data.get('close_time', ''),
                'Open': data.get('Open', 0) if 'Open' in data else data.get('open', 0),
                'Close': data.get('Close', 0) if 'Close' in data else data.get('close', 0),
                'High': data.get('High', 0) if 'High' in data else data.get('high', 0),
                'Low': data.get('Low', 0) if 'Low' in data else data.get('low', 0),
                'Volume': data.get('Volume', 0) if 'Volume' in data else data.get('volume', 0),
            })
        except Exception as e:
            print(f"Error processing data item: {e}")
            print(f"Problematic data: {data}")
            # 添加默认值以继续执行
            chart_data.append({
                'Date': '',
                'Open': 0,
                'Close': 0,
                'High': 0,
                'Low': 0,
                'Volume': 0
            })
    return html.Div([
        fac.AntdCenter([
            fac.AntdSpace([
                fac.AntdButton('播放', id='play-button', icon=fac.AntdIcon(mode='iconfont',
                                                                      scriptUrl='assets/font/iconfont.js', icon='icon-a-mti-bofangshi')),
                fac.AntdButton('暂停', id='pause-button', icon=fac.AntdIcon(mode='iconfont',
                                                                       scriptUrl='assets/font/iconfont.js', icon='icon-a-mti-zanting2shi')),
                fac.AntdButton('停止', id='stop-button', icon=fac.AntdIcon(mode='iconfont',
                                                                      scriptUrl='assets/font/iconfont.js', icon='icon-a-mti-tingzhi2shi')),
                fac.AntdButton('重置', id='reset-button', icon=fac.AntdIcon(mode='iconfont',
                                                                       scriptUrl='assets/font/iconfont.js', icon='icon-mti-zhongzhi')),
            ]),
        ]),

        dcc.Graph(id='candlestick-chart', config={'displayModeBar': True}),
        dcc.Interval(
            id='interval-component',
            interval=500,  # 默认500毫秒更新一次
            n_intervals=0,
            disabled=True  # 初始禁用
        ),
        dcc.Store(id='data-store', data=chart_data)
    ])


@callback(
    Output('backtest_strategy', 'options'),
    Input('refresh-backtest-btn', 'nClicks'),
    prevent_initial_call=True,
)
def refresh_backtest_btn(n_clicks):
    return get_strategy()


@callback(
    Output('backtest_strategy', 'value'),
    Input('global-storage', 'data'),
    prevent_initial_call=True,
)
def load_config(data):
    # print(f"回测页面获取data: {data}")
    if data:
        return data[0]['value']
    return ''


@callback(
    [
        Output('analyze-result-btn', 'disabled'),
        Output('run_backtest_spin_output', 'children'),
    ],
    Input('run_backtest_btn', 'nClicks'),
    State('run_backtest_form', 'values'),
    prevent_initial_call=True,
)
def run_backtest_server(n_clicks, form_values: dict):
    if n_clicks:
        # print(form_values)
        if not form_values.get('backtest_strategy'):
            return False, '请选择策略'
        if not form_values.get('symbol'):
            return False, '请选择货币对'
        if not form_values.get('timeframe'):
            return False, '请选择时间框架'
        if not form_values.get('initial_cash'):
            return False, '请输入初始资金'
        if not form_values.get('start_date'):
            return False, '请选择开始时间'
        if not form_values.get('end_date'):
            return False, '请选择结束时间'
        bt = Backtest(strategy=form_values['backtest_strategy'],
                      symbol=form_values['symbol'],
                      interval=form_values['timeframe'],
                      cash=float(form_values['initial_cash']),
                      commission=0.01,
                      start=form_values['start_date'],
                      end=form_values['end_date'])
        stats = bt.run()
        # print(stats)
        return False, ''
    return True, ''

# 生成指标结构
def gen_metric_table(data):
    metric = data.get('cn')
    value = data.get('value')
    desc = data.get('desc')
    return fac.AntdSpace([
        fac.AntdText(metric),
        fac.AntdTooltip(
            [
                fac.AntdIcon(icon='antd-exclamation-circle-two-tone'),
            ], title=f'{desc}'
        ) if desc else fac.Fragment()
    ]), value

# 加载,删除回测记录


@callback(
    Output('candle_table', 'data'),
    Output('analyze-result-btn', 'disabled', allow_duplicate=True),
    Output('visualize-result-btn', 'disabled', allow_duplicate=True),
    # Output('strategy_params_table', 'data'),
    # Output('strategy_metrics_table', 'data'),
    Input(f'candle_table', 'nClicksButton'),
    [
        State(f'candle_table', 'clickedCustom'),
    ],
    prevent_initial_call=True,
)
def action_backtest(nClicksButton, clickedCustom):
    message = ''
    disabled = True
    global strategy_params
    global strategy_metrics
    global strategy_trades
    global strategy_strategy
    strategy_metrics = []
    strategy_params = []
    strategy_metrics = []
    strategy_strategy = []
    if nClicksButton:
        if clickedCustom.get('load'):
            print(f"加载回测记录: {clickedCustom['load']}")
            backtest_record = BacktestRecord.get(
                BacktestRecord.id == clickedCustom['load'])
            print(backtest_record)
            message = f'加载回测记录: {backtest_record.strategy_name}'
            disabled = False
            backtest_results = json.loads(backtest_record.results)
            for i in backtest_results:
                metric, value = gen_metric_table(i)
                strategy_metrics.append({'metric': metric, 'value': value})
            print(strategy_metrics)
            backtest_params = json.loads(backtest_record.parameters)
            for i in backtest_params.items():
                strategy_params.append({'param': i[0], 'value': i[1]})
            strategy_trades = json.loads(backtest_record.trades)
            strategy_strategy = json.loads(backtest_record.strategy)
        if clickedCustom.get('deleted'):
            print(f"删除回测记录: {clickedCustom['deleted']}")
            BacktestRecord.delete().where(BacktestRecord.id ==
                                          clickedCustom['deleted']).execute()
            message = f'删除成功'
        MessageManager.success(content=message)
    table_data = refresh_table_data()
    return table_data, disabled, disabled


# @callback(
#     Output('tooltip-metric', 'title'),
#     Input('tooltip-metric', 'color'),
#     )
# def tooltip_metric_callback(color):
#     print(color)
#     return fac.AntdParagraph(['当前color: ',fac.AntdText(color, copyable=True)])


@callback(
    Output('run-backtest-view', 'children'),
    Input('run-backtest-view-btn', 'nClicks')
)
def show_run_backtest_view(n_clicks):
    return render_content_backtest()


@callback(
    Output('run-backtest-view', 'children', allow_duplicate=True),
    Input('analyze-result-btn', 'nClicks'),
    prevent_initial_call=True,
)
def show_analyze_result_view(n_clicks):
    global strategy_params
    global strategy_metrics
    global strategy_trades
    return render_content_analyze(strategy_params, strategy_metrics, strategy_trades)


@callback(
    Output('run-backtest-view', 'children', allow_duplicate=True),
    Input('visualize-result-btn', 'nClicks'),
    prevent_initial_call=True,
)
def show_visualize_result_view(n_clicks):
    global strategy_trades
    global strategy_params
    global strategy_metrics
    global strategy_strategy
    if n_clicks:
        return render_content_visualize(strategy_trades, strategy_strategy)
    return render_content_analyze(strategy_params, strategy_metrics, strategy_trades)


@callback(
    Output('candle_graph', 'figure'),
    Input('play-btn', 'nClicks'),
    State('candle_graph', 'figure'),
    prevent_initial_call=True,
)
def play_button_callback(n_clicks, figure):
    # 播放按钮回调逻辑
    # 这里可以实现图表的动画播放功能
    print('播放按钮被点击')
    # 示例: 更新图表以开始动画
    figure['layout']['animation'] = {'duration': 1000, 'easing': 'linear'}
    return figure


@callback(
    Output('candle_graph', 'figure', allow_duplicate=True),
    Input('pause-btn', 'nClicks'),
    State('candle_graph', 'figure'),
    prevent_initial_call=True,
)
def pause_button_callback(n_clicks, figure):
    # 暂停按钮回调逻辑
    # 这里可以实现图表动画的暂停功能
    print('暂停按钮被点击')
    # 示例: 暂停图表动画
    if 'animation' in figure['layout']:
        figure['layout'].pop('animation')
    return figure


@callback(
    Output('candle_graph', 'figure', allow_duplicate=True),
    Input('stop-btn', 'nClicks'),
    State('candle_graph', 'figure'),
    prevent_initial_call=True,
)
def stop_button_callback(n_clicks, figure):
    # 停止按钮回调逻辑
    # 这里可以实现图表动画的停止功能
    print('停止按钮被点击')
    # 示例: 停止图表动画并重置到初始状态
    if 'animation' in figure['layout']:
        figure['layout'].pop('animation')
    # 可以在这里重置图表数据或视图
    return figure


@callback(
    Output('candle_graph', 'figure', allow_duplicate=True),
    Input('reset-btn', 'nClicks'),
    prevent_initial_call=True,
)
def reset_button_callback(n_clicks):
    # 重置按钮回调逻辑
    # 这里可以实现图表的重置功能
    print('重置按钮被点击')
    # 示例: 重置图表到初始状态
    return {
        'data': [],
        'layout': {
            'title': 'Candle Graph',
            'xaxis': {'title': 'Time'},
            'yaxis': {'title': 'Price'},
        }
    }

def generate_ohlc_data(existing_data, new_points=1, trend_strength=0.1):
    """
    从strategy_strategy获取真实的OHLC数据
    参数:
        existing_data: 现有数据DataFrame
        new_points: 要获取的新数据点数
        trend_strength: 趋势强度参数(此实现中未使用)
    返回:
        包含新数据的DataFrame
    """
    try:
        global strategy_strategy
        
        if not strategy_strategy:
            print("Warning: strategy_strategy is empty")
            return existing_data
        
        # 如果existing_data为空，则从strategy_strategy的开始获取数据
        if existing_data.empty:
            start_idx = 0
        else:
            # 尝试找到现有数据最后一条记录对应的索引
            last_date = existing_data['Date'].iloc[-1]
            # 查找strategy_strategy中对应的位置
            start_idx = 0
            for i, data in enumerate(strategy_strategy):
                try:
                    if pd.to_datetime(data.get('close_time', '')) > last_date:
                        start_idx = i
                        break
                except Exception as e:
                    print(f"Error processing date for index {i}: {e}")
                    continue
        
        # 获取新数据点
        end_idx = start_idx + new_points
        new_data_list = strategy_strategy[start_idx:end_idx]
        
        # 转换为DataFrame，添加错误处理
        dates = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for data in new_data_list:
            try:
                _date = data.get('Date', '') if data.get('Date', '') else data.get('close_time', '')
                dates.append(pd.to_datetime(_date))
                opens.append(data.get('Open', 0) if 'Open' in data else data.get('open', 0))
                highs.append(data.get('High', 0) if 'High' in data else data.get('high', 0))
                lows.append(data.get('Low', 0) if 'Low' in data else data.get('low', 0))
                closes.append(data.get('Close', 0) if 'Close' in data else data.get('close', 0))
                volumes.append(data.get('Volume', 0) if 'Volume' in data else data.get('volume', 0))
            except Exception as e:
                print(f"Error processing data item: {e}")
                print(f"Problematic data: {data}")
                # 添加默认值以继续执行
                dates.append(pd.to_datetime(''))
                opens.append(0)
                highs.append(0)
                lows.append(0)
                closes.append(0)
                volumes.append(0)
        
        new_data = pd.DataFrame({
            'Date': dates,
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        })
        
        # 合并现有数据和新数据，并保留最近50根K线
        combined_data = pd.concat([existing_data, new_data]).iloc[-50:]
        return combined_data
    
    except Exception as e:
        print(f"数据获取错误: {e}")
        import traceback
        traceback.print_exc()
        return existing_data

@callback(
    [Output('candlestick-chart', 'figure'),
     Output('interval-component', 'disabled'),
     Output('interval-component', 'interval'),
     Output('data-store', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('play-button', 'nClicks'),
     Input('pause-button', 'nClicks'),
     Input('stop-button', 'nClicks'),
    #  Input('speed-slider', 'value')
     ],
    [State('data-store', 'data')]
)
def update_chart(n_intervals, play_clicks, pause_clicks, stop_clicks,data_store):
    """
    更新蜡烛图图表
    参数:
        n_intervals: 时间间隔计数
        play_clicks: 播放按钮点击次数
        pause_clicks: 暂停按钮点击次数
        stop_clicks: 停止按钮点击次数
        speed_value: 播放速度值
        data_store: 存储的数据
    返回:
        更新后的图表配置、时间间隔禁用状态、新的时间间隔、更新后的数据
    """
    # 确定哪个输入被触发
    _ctx = callback_context
    trigger_id = _ctx.triggered[0]['prop_id'].split('.')[0] if _ctx.triggered else None

    # 初始化或获取当前数据
    if data_store is None or trigger_id == 'stop-button':
        # 初始加载或停止按钮被点击，使用初始数据
        global strategy_strategy
        if strategy_strategy:
            # 从strategy_strategy获取初始数据
            initial_data = pd.DataFrame({
                'Date': [pd.to_datetime(item['close_time']) for item in strategy_strategy[:50]],
                'Open': [item['Open'] for item in strategy_strategy[:50]],
                'High': [item['High'] for item in strategy_strategy[:50]],
                'Low': [item['Low'] for item in strategy_strategy[:50]],
                'Close': [item['Close'] for item in strategy_strategy[:50]],
                'Volume': [item['Volume'] for item in strategy_strategy[:50]]
            })
        else:
            # 如果strategy_strategy为空，创建空DataFrame
            initial_data = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df = initial_data
    else:
        # 从存储中获取数据
        df = pd.DataFrame(data_store)
        # 将Date列转换为datetime类型
        try:
            if df.get('Date', ''):
                df['Date'] = pd.to_datetime(df['Date'])
            else:
                df['Date'] = pd.to_datetime(df['close_time'])
        except Exception as e:
            print(f"Error converting Date column to datetime: {e}")
            # 如果转换失败，使用当前时间作为备选
            df['Date'] = pd.date_range(
                end=datetime.now(), periods=len(df), freq='T')

        # 如果是时间间隔触发，获取新数据
        if trigger_id == 'interval-component':
            df = generate_ohlc_data(df, new_points=1)

    # 确保最多显示50条数据，适用于所有情况
    df = df.tail(50)
    fig = create_candlestick_chart(df)

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
    interval = int(0.2 * 1000)

    return fig, disabled, interval, df.to_dict('records')


