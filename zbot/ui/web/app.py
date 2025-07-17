import dash
from dash import Dash, html, dcc, Output, Input
import feffery_antd_components as fac
import feffery_utils_components as fuc


class App(Dash):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

        self.layout = html.Div(
            [
                dcc.Location(id="url"),
                html.Div(
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
                                                        style={
                                                            'height': 54, 'width': 54}
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
                                                            'key': page['name'],
                                                            'title': page['name'],
                                                            'icon': page['icon'],
                                                            'href': page['relative_path']
                                                        }
                                                    }
                                                    for page in dash.page_registry.values()
                                                ],
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

                    ]
                ),
                html.Div(id="page-content"),
                dash.page_container
            ],
        )


if __name__ == '__main__':
    app = App(
        name=__name__,
        assets_folder='assets',  # 对应资源存放目录,可下载后解压到这里
        title='ZBot',
        update_title='Loading...',
        use_pages=True,
        pages_folder='pages',  # 对应的pages存放的目录
        suppress_callback_exceptions=True  # 异常不会触发框架级错误处理
    )
    app.run(debug=True)
