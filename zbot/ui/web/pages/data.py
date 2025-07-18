import dash
from dash import html, dcc, callback, Input, Output, State
import feffery_utils_components as fuc
import feffery_antd_components as fac

# 注册pages
dash.register_page(__name__, icon='antd-save', name='数据')

TIMEFRAME_FORM = [
    '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d'
]


class DownloadData(object):
    def __init__(self) -> None:
        pass

    def get_data_progress():
        return html.Div(
            children=[
                fac.AntdSpace(
                    []
                )
            ]
        )


# 内容区
layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdSelect(id='trade_mode_form'), label=f'交易模式', hasFeedback=True
                        ),
                        fac.AntdFormItem(
                            fac.AntdSelect(id='symbol_form',options=['BTC/USDT'], value='BTC/USDT'), label=f'交易对', hasFeedback=True
                        ),
                        fac.AntdFormItem(
                            fac.AntdSelect(id='timeframe_form', options=[i for i in TIMEFRAME_FORM]), label=f'时间周期', hasFeedback=True
                        ),
                        fac.AntdFormItem(
                            fac.AntdDatePicker(style={'display': 'block'}, id='start_time_form'), label=f'开始时间', hasFeedback=True
                        ),
                        fac.AntdFormItem(
                            fac.AntdDatePicker(style={'display': 'block'}, id='end_time_form'), label=f'结束时间', hasFeedback=True
                        ),
                        fac.AntdButton(
                            '获取数据', type='primary', block=True, id='get_data_button', autoSpin=True)
                    ],
                    id='data_form',
                    enableBatchControl=True,
                    layout='vertical',
                    values={
                        'trade_mode_form': 'spot',
                        'symbol_form': 'BTC/USDT',
                        'timeframe_form': '15m',
                        'start_time_form': '2023-01-01',
                        'end_time_form': '2023-01-02',
                    }
                ),
                fuc.FefferyDiv(children=[], id='progress'),

                fac.AntdDivider('现有数据'),
                fac.AntdTable(id='candle_table',
                              columns=[
                                  {'title': '货币对', 'dataIndex': 'symbol'},
                                  {'title': '时间周期', 'dataIndex': 'timeframe'},
                                  {'title': '开始时间', 'dataIndex': 'open_time'},
                                  {'title': '结束时间', 'dataIndex': 'close_time'},
                                  {'title': '完整度', 'dataIndex': 'complete'},
                              ], data=[], style={'padding': 5})
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
    # [Output("get_data_progress", "hidden"),
    #  Output("candle_table", "loading"),
    #  Output('progress', 'children')],
    Input("get_data_button", "nClicks"),
    State('data_form', 'values'),
    # State('trade_mode_form', 'value'),
    # State('symbol_form', 'value'),
    # State('timeframe_form', 'value'),
    # State('start_time_form', 'value'),
    # State('end_time_form', 'value'),
    prevent_initial_call=True  # 防止初始加载触发
)
def data_download(n_clicks, values):
# def data_download(n_clicks, exchange, trade_mode, symbol, timeframe, start_time, end_time):
    print(n_clicks)
    # dddd = fac.AntdProgress(id='get_data_progress')
    print('1111111')
    print(values)
    # print(exchange)
    # download_data = DownloadData()
    # return True, False, download_data.get_data_progress()
