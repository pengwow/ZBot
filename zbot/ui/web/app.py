import dash
from dash import Dash, html, dcc, Output, Input, callback
import feffery_antd_components as fac
import feffery_utils_components as fuc
from zbot.common.config import read_config

class App(Dash):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self.config_data = self.load_init_data()
        self.layout = html.Div(
            [
                dcc.Location(id="url"),
                dcc.Store(id='global-storage'),  # 全局存储组件
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

    def load_init_data(self):
        data = read_config()
        print(f"加载全局配置: {data}")
        return data

@callback(
    Output('global-storage', 'data'),
    Input('global-storage', 'data')
)
def load_init_data(data):
    if not data:
        data = read_config()
        print(f"加载全局配置: {data}")
    else:
        print(f"全局配置已存在: {data}")
    return data


def run_web_ui(host=None, port=None):
    app = App(
        name=__name__,
        assets_folder='assets',  # 对应资源存放目录,可下载后解压到这里
        title='ZBot',
        update_title='Loading...',
        use_pages=True,
        pages_folder='pages',  # 对应的pages存放的目录
        suppress_callback_exceptions=True  # 异常不会触发框架级错误处理
    )
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    run_web_ui('127.0.0.1', 8080)
    