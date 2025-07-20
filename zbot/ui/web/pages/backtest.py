import time
from calendar import c
import dash
from dash import html, dcc, callback, Input, Output, State
import feffery_utils_components as fuc
import feffery_antd_components as fac

# 注册pages
dash.register_page(__name__, icon='antd-fund-projection-screen', name='回测')


class BacktestRunView():
    def __init__(self):
        # super().__init__()
        self.layout = html.Div(
            children=[
                fac.AntdCenter(
                    [
                        fac.AntdForm(
                            [
                                fac.AntdFormItem(
                                    [
                                        html.Div([
                                            fac.AntdSelect(
                                                options=[
                                                    {'label': '策略 1',
                                                        'value': 'run'},
                                                    {'label': '策略 2',
                                                        'value': 'analyze'}
                                                ], style={'width': '300px'}),
                                            fac.AntdButton(id="refresh-backtest-btn",
                                                           icon=fac.AntdIcon(icon='antd-reload')),
                                        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px', 'flexWrap': 'nowrap'})
                                    ],
                                    label='策略',
                                    # labelCol={'span': 4}
                                ),
                                fac.AntdFormItem(
                                    fac.AntdSelect(id='symbol'),
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
                                        ], style={'display': 'flex', 'gap': '10px'})
                                    ],
                                    label='时间范围',
                                    style={'width': '350px'}
                                ),
                                fac.AntdButton(
                                    '运行回测', id='run_backtest_btn', type='primary', block=True),
                                fac.AntdSpin(fac.AntdText(id='run_backtest_spin_output'), text='回测中',  fullscreen=True),
                            ],
                            id='run_backtest_form',
                            enableBatchControl=True,
                            values={
                                'timeframe': '15m',
                                'start_date': '2023-01-01',
                            }
                        ),
                    ]
                ),
                html.H1('回测记录'),
                fac.AntdTable(
                    id='candle_table',
                    columns=[
                        {'title': '策略', 'dataIndex': 'strategy'},
                        {'title': '详情', 'dataIndex': 'detail'},
                        {'title': '回测时间', 'dataIndex': 'backtest_time'},
                        {'title': '文件名称', 'dataIndex': 'file_name'},
                        {'title': '动作', 'dataIndex': 'action'},
                    ], data=[{
                        'strategy': '策略1',
                        'detail': '详情1',
                                  'backtest_time': '2023-01-01',
                                  'file_name': '文件1',
                                  'action': html.Div(
                                      children=[
                                          fac.AntdPopover(
                                              fac.AntdButton(disabled=False,
                                                             size='small', icon=fac.AntdIcon(
                                                                 icon='antd-arrow-right')),
                                              content='加载', id=f'load-backtest-btn{i}'
                                          ),
                                          fac.AntdPopover(
                                              fac.AntdPopconfirm(
                                                  fac.AntdButton(disabled=False,
                                                                 size='small', icon=fac.AntdIcon(icon='antd-delete')), title='确认删除'),
                                              content="删除", id=f'delete-backtest-btn{i}')
                                      ]
                                  )
                    } for i in range(3)], style={'padding': 5}
                    ),
                    
            ]
        )

    @staticmethod
    @callback(
        [
            Output(f'delete-backtest-btn1', 'disabled'),
            Output(f'load-backtest-btn1', 'disabled'),
        ],
        Input(f'delete-backtest-btn1', 'confirmCounts'),
        Input('delete-backtest-btn1', 'cancelCounts'),
        prevent_initial_call=True,
    )
    def delete_backtest(confirmCounts, cancelCounts):
        print(confirmCounts, cancelCounts)
        if confirmCounts:
            return True, True
        return False, False

    @callback(
        [
            Output('analyze-result-btn', 'disabled'),
            Output('run_backtest_spin_output', 'children'),
        ],
        Input('run_backtest_btn', 'nClicks'),
        State('run_backtest_form', 'values'),
        prevent_initial_call=True,
    )
    def run_backtest_server(n_clicks, form_values):
        if n_clicks:
            time.sleep(3)
            print(form_values)
            return False, ''
        return True, ''


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
                ),
                html.Div(id='run_back_message-div'),
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


@callback(
    Output('run-backtest-view', 'children'),
    Input('run-backtest-view-btn', 'nClicks')
)
def show_run_backtest_view(n_clicks):
    backtest_run_view = BacktestRunView()
    return backtest_run_view.layout

@callback(
    Output('run_back_message-div', 'children'),
    Input('analyze-result-btn', 'nClicks'),
    prevent_initial_call=True,
)
def show_analyze_result_view(n_clicks):
    if n_clicks:
        return ''
    return ''
