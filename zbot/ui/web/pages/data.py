import dash
from dash import html, dcc, callback, Input, Output
import feffery_utils_components as fuc
import feffery_antd_components as fac

# 注册pages
dash.register_page(__name__, icon='antd-save', name='数据')

# 内容区
layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                fac.AntdForm(
                    [
                        fac.AntdFormItem(
                            fac.AntdSelect(), label=f'交易商', hasFeedback=True, id='exchange_form'
                        ),
                        fac.AntdFormItem(
                            fac.AntdSelect(), label=f'交易模式', hasFeedback=True, id='trade_mode_form'
                        ),
                        fac.AntdFormItem(
                            fac.AntdSelect(), label=f'交易对', hasFeedback=True, id='symbol_form'
                        ),
                        fac.AntdFormItem(
                            fac.AntdSelect(), label=f'时间周期', hasFeedback=True, id='timeframe_form'
                        ),
                        fac.AntdFormItem(
                            fac.AntdDatePicker(style={'display': 'block'}), label=f'开始时间', hasFeedback=True, id='start_time_form'
                        ),
                        fac.AntdFormItem(
                            fac.AntdDatePicker(style={'display': 'block'}), label=f'结束时间', hasFeedback=True, id='end_time_form'
                        ),
                        fac.AntdButton(
                            '获取数据', type='primary', block=True, id='get_data_button', autoSpin=True)
                    ],
                    id='data_form',
                    enableBatchControl=True,
                    layout='vertical',
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


# @callback(
#     [Output("get_data_progress", "hidden"),
#      Output("candle_table", "loading"),
#      Output('progress', 'children')],
#     Input("get_data_button", "nClicks"),
#     prevent_initial_call=True  # 防止初始加载触发
# )
# def data_download(n_clicks):
#     print(n_clicks)
#     dddd = fac.AntdProgress(id='get_data_progress')
#     return True, False, dddd
