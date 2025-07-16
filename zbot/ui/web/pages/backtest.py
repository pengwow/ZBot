from calendar import c
import dash
from dash import html, dcc, callback, Input, Output
import feffery_utils_components as fuc
import feffery_antd_components as fac

# 注册pages
dash.register_page(__name__, icon='antd-fund-projection-screen', name='回测')

layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                fac.AntdCenter(
                    fac.AntdSpace(
                        [
                            fac.AntdButton(
                                '运行回测', icon=fac.AntdIcon(icon='antd-desktop'), id='run-backtest-btn'),
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


# @callback(
#     [
#         Output('analyze-result-btn', 'disabled'),
#         Output('visualize-result-btn', 'disabled'),
#     ],
#     Input('run-backtest-btn', 'nClicks')
# )
# def update_btn_disabled(n_clicks):
#     if n_clicks is None:
#         return True, True
#     return False, False

@callback(
    Output('run-backtest-view', 'children'),
    Input('run-backtest-btn', 'nClicks')
)
def show_run_backtest_view(n_clicks):
    return html.Div(
        children=[
            html.H1('运行回测'),
            fac.AntdTable(id='candle_table',
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
                                              fac.AntdButton(size='small', icon=fac.AntdIcon(
                                                  icon='antd-arrow-right')),
                                              content='加载'
                                          ),
                                      fac.AntdPopover(
                                              fac.AntdPopconfirm(fac.AntdButton(
                                                  size='small', icon=fac.AntdIcon(icon='antd-delete')), title='确认删除'),
                                          content="删除")
                                  ]
                              )
                          }]*3, style={'padding': 5})
        ]
    )
