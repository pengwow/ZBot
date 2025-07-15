import dash
from dash import html
import feffery_antd_components as fac
import feffery_utils_components as fuc

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        fuc.FefferyDiv(
            [
                # 利用fac中的网格系统进行页首元素的排布
                fac.AntdRow(
                    [
                        # logo+标题
                        fac.AntdCol(
                            fac.AntdSpace(
                                [
                                    fac.AntdImage(
                                        src=dash.get_asset_url(
                                            'logo.png'
                                        ),
                                        preview=False,
                                        style={'height': 54, 'width': 54}
                                    ),
                                    fac.AntdText(
                                        'ZBot',
                                        strong=True,
                                        style={
                                            'fontSize': 32
                                        }
                                    )
                                ]
                            ),
                            flex='none',
                            style={
                                'height': 'auto'
                            }
                        ),

                        # 菜单栏
                        fac.AntdCol(
                            fac.AntdMenu(
                                menuItems=[
                                    {
                                        'component': 'Item',
                                        'props': {
                                            'key': f'图表',
                                            'title': f'图表',
                                            'icon': 'antd-stock'
                                        }
                                    },
                                    {
                                        'component': 'Item',
                                        'props': {
                                            'key': f'回测',
                                            'title': f'回测',
                                            'icon': 'antd-fund-projection-screen'
                                        }
                                    },
                                    {
                                        'component': 'Item',
                                        'props': {
                                            'key': f'数据',
                                            'title': f'数据',
                                            'icon': 'antd-save'
                                        }
                                    },
                                    {
                                        'component': 'Item',
                                        'props': {
                                            'key': f'配置',
                                            'title': f'配置',
                                            'icon': 'antd-setting'
                                        }
                                    }

                                ],
                                defaultSelectedKey='数据',
                                mode='horizontal',
                                style={
                                    'maxWidth': 600,
                                    'borderBottom': 'none'
                                }
                            ),
                            flex='none',
                            style={
                                'height': 'auto'
                            }
                        )
                    ],
                    align='middle',
                    justify='space-between',
                    wrap=False,  # 阻止自动换行
                    style={
                        'height': '100%'
                    }
                )
            ],
            style={
                'height': 64,
                'padding': '0 25px',
                'background': 'white',
                'borderBottom': '1px solid #f0f0f0'
            }
        ),
        # 内容区
        html.Div(

            fuc.FefferyDiv(
                [
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(
                                fac.AntdSelect(), label=f'交易商', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdSelect(), label=f'交易模式', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdSelect(), label=f'交易对', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdSelect(), label=f'时间周期', hasFeedback=True
                            ),
                            fac.AntdFormItem(
                                fac.AntdDatePicker(style={'display': 'block'}), label=f'开始时间', hasFeedback=True, 
                            ),
                            fac.AntdFormItem(
                                fac.AntdDatePicker(style={'display': 'block'}), label=f'结束时间', hasFeedback=True,
                            ),
                            fac.AntdButton('获取数据', type='primary', block=True)
                        ],
                        id='batch-validate-status-form-demo',
                        enableBatchControl=True,
                        layout='vertical',
                    )
                ],
                shadow='always-shadow-light',
                style={
                    'borderRadius': 8,
                    'background': 'white',
                    'padding': 24
                }
            ),
            style={
                'minHeight': 'calc(100vh - 64px)',
                'background': '#f0f2f5',
                'padding': 20
            }
        )
    ]
)

if __name__ == '__main__':
    app.run(debug=False)
