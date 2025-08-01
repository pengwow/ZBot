import json
import time
from calendar import c
import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import feffery_utils_components as fuc
import feffery_antd_components as fac
from zbot.services.backtest import get_strategy_class_names, Backtest
from zbot.models.backtest import BacktestRecord
from zbot.ui.web.utils.feedback import MessageManager

# 注册pages
dash.register_page(__name__, icon='antd-fund-projection-screen', name='回测')


strategy_params = []
strategy_metrics = []
strategy_trades = []


# 获取回测记录
def get_backtest_results():
    backtest_records = BacktestRecord.select().order_by(
        BacktestRecord.created_at.desc())
    backtest_records = [record.to_dict() for record in backtest_records]
    print(backtest_records)

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
                            ], data=strategy_trades
                        , style={'width': '1000px'})], direction='vertical'),
                ], direction='vertical'),
            ]),
        ]
    )


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
    print(f"回测页面获取data: {data}")
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
        print(form_values)
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
        print(stats)
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
        if clickedCustom.get('deleted'):
            print(f"删除回测记录: {clickedCustom['deleted']}")
            BacktestRecord.delete().where(BacktestRecord.id ==
                                          clickedCustom['deleted']).execute()
            message = f'删除成功'
        MessageManager.success(content=message)
    table_data = refresh_table_data()
    return table_data, disabled


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
