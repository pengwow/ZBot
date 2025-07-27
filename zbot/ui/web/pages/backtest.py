import time
from calendar import c
import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import feffery_utils_components as fuc
import feffery_antd_components as fac
from zbot.services.backtest import get_strategy_class_names, Backtest
from zbot.models.backtest import BacktestRecord


# 注册pages
dash.register_page(__name__, icon='antd-fund-projection-screen', name='回测')


class BacktestRunView():
    def __init__(self):
        # super().__init__()
        self.symbols = ctx.global_vars['symbols']
        self.strategy_options = self.get_strategy()
        self.backtest_results = self.get_backtest_results()
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
                                                id="backtest_strategy",
                                                options=self.strategy_options, style={'width': '300px'}),
                                            fac.AntdButton(id="refresh-backtest-btn",
                                                           icon=fac.AntdIcon(icon='antd-reload')),
                                        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'gap': '10px', 'flexWrap': 'nowrap'})
                                    ],
                                    label='策略',
                                    # labelCol={'span': 4}
                                ),
                                fac.AntdFormItem(
                                    fac.AntdSelect(
                                        id='symbol', options=self.symbols),
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
                fac.AntdTable(
                    id='candle_table',
                    columns=[
                        {'title': 'ID', 'dataIndex': 'id'},
                        {'title': '策略', 'dataIndex': 'strategy_name'},
                        {'title': '回测时间', 'dataIndex': 'created_at'},
                        {'title': '最大回撤', 'dataIndex': 'max_drawdown'},
                        {'title': '总收益率', 'dataIndex': 'total_return'},
                        {'title': '动作', 'dataIndex': 'action', 'renderOptions': {'renderType': 'button'}},
                    ], data=[{
                        'id': record['id'],
                        'strategy_name': record['strategy_name'],
                        'created_at': record['created_at'],
                        'max_drawdown': record['max_drawdown'],
                        'total_return': record['total_return'],
                        'action': [
                            {'content': '加载', 'type': 'link', 'custom': {"load": f"{record['id']}"}},
                            {'content': '删除', 'type': 'dashed', 'custom': {"deleted": f"{record['id']}"}},
                        ]
                        # html.Div(
                        #               children=[
                        #                   fac.AntdPopover(
                        #                       fac.AntdButton(disabled=False,
                        #                                      size='small', icon=fac.AntdIcon(
                        #                                          icon='antd-arrow-right')),
                        #                       content='加载', id=f'load-backtest-btn{record['id']}'
                        #                   ),
                        #                   fac.AntdPopover(
                        #                       fac.AntdPopconfirm(
                        #                           fac.AntdButton(disabled=False,
                        #                                          size='small', icon=fac.AntdIcon(icon='antd-delete')), title='确认删除'),
                        #                       content="删除", id=f'delete-backtest-btn{record['id']}')
                        #               ]
                        #           )
                    } for record in self.backtest_results], style={'padding': 5}
                ),

            ]
        )

    # 获取回测记录
    @staticmethod
    def get_backtest_results():
        backtest_records = BacktestRecord.select().order_by(BacktestRecord.created_at.desc())
        backtest_records = [record.to_dict() for record in backtest_records]
        print(backtest_records)
        
        return backtest_records

    # 删除回测记录
    @staticmethod
    @callback(
        Input(f'candle_table', 'nClicksButton'),
        [
            State(f'candle_table', 'recentlyButtonClickedRow'),
            State(f'candle_table', 'clickedCustom'),
        ],
        prevent_initial_call=True,
    )
    def action_backtest(nClicksButton, recentlyButtonClickedRow, clickedCustom):
        # print(recentlyButtonClickedRow, clickedCustom)
        if nClicksButton:
            if clickedCustom.get('load'):
                print(f"加载回测记录: {clickedCustom['load']}")
                backtest_record = BacktestRecord.get(BacktestRecord.id == clickedCustom['load'])
                print(backtest_record)
            if clickedCustom.get('deleted'):
                print(f"删除回测记录: {clickedCustom['deleted']}")
                BacktestRecord.delete().where(BacktestRecord.id == clickedCustom['deleted']).execute()
            return True, True
        return False, False

    @staticmethod
    def get_strategy():
        class_names = get_strategy_class_names()
        return [{'label': f"{item['name']} ({item['filename']})", 'value': item['name']} for item in class_names]

    @callback(
        Output('backtest_strategy', 'options'),
        Input('refresh-backtest-btn', 'nClicks'),
        prevent_initial_call=True,
    )
    def refresh_backtest_btn(self, n_clicks):
        return self.get_strategy()

    @staticmethod
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
    def run_backtest_server(n_clicks, form_values):
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
            return True, ''
        return False, ''


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
        print('分析结果')
        return ''
    return ''
