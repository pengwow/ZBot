from dash import Dash, html, dcc, Output, Input
import dash
import dash_bootstrap_components as dbc
# import dash_auth
from assets.assets_file import SIDEBAR_STYLE, CONTENT_STYLE


class App(Dash):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)

        self.layout = html.Div(
            [
                dcc.Location(id="url"),
                html.Div(
                    [
                        html.H2("Sidebar", className="display-4"),
                        html.Hr(),
                        html.P("A simple sidebar layout with navigation links", className="lead"),
                        dbc.Nav([
                            dbc.NavLink(f"{page['name']} - {page['path']}", href=page["relative_path"],
                                        active="exact") for page in dash.page_registry.values()
                        ],
                            vertical=True,
                            pills=True,
                        ),
                    ],
                    style=SIDEBAR_STYLE,
                ),
                html.Div(id="page-content", style=CONTENT_STYLE),
                dash.page_container
            ],
        )

        # 添加callback
        self.callback(Output('switch', 'label'), Input('switch', 'on'))(self.func_test)

    def func_test(self, on):
        """
        测试page_file.py 内的元素能否触发回调  -> 可以触发
        :param on:
        :return:
        """
        if on:
            return '这是开关,当前开关开'
        else:
            return '这是开关,当前开关关'


if __name__ == '__main__':
    VALID_USERNAME_PASSWORD_PAIRS = {'user': 'pwd'}  # 本地账户密码储存
    app = App(
        name=__name__,
        assets_folder='assets',  # 对应资源存放目录,可下载后解压到这里
        title='app',
        update_title='Loading...',
        use_pages=True,
        pages_folder='pages',  # 对应的pages存放的目录
    )
    # auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)  # 添加用户登录
    app.run()

