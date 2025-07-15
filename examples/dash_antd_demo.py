
import dash
from dash import html
import feffery_antd_components as fac
from dash.dependencies import Input, Output

# 实例化Dash应用对象
app = dash.Dash(__name__)

# 添加初始化页面内容
app.layout = html.Div(
    
fac.AntdLayout(
    [
        fac.AntdSider(
            [
                fac.AntdMenu(
                    menuItems=[
                        {
                            'component': 'Item',
                            'props': {
                                'key': f'图标{icon}',
                                'title': f'图标{icon}',
                                'icon': icon,
                            },
                        }
                        for icon in [
                            'antd-home',
                            'antd-cloud-upload',
                            'antd-bar-chart',
                            'antd-pie-chart',
                        ]
                    ],
                    mode='inline',
                    style={'height': '100%', 'overflow': 'hidden auto'},
                )
            ],
            collapsible=True,
            collapsedWidth=60,
            style={'backgroundColor': 'rgb(240, 242, 245)'},
        ),
        fac.AntdContent(
            fac.AntdCenter(
                fac.AntdTitle('内容区示例', level=2, style={'margin': '0'}),
                style={
                    'height': '100%',
                },
            ),
            style={'backgroundColor': 'white'},
        ),
    ],
    style={'height': '100vh'},
)
)


# 定义回调函数串起相关交互逻辑
@app.callback(
    Output("output-container", "children"),
    [Input("target-value", "value"), Input("actual-value", "value")],
)
def handle_progress_render(target_value, actual_value):
    # 判断传入的目标值和实际值是否有效
    if target_value and actual_value:
        return fac.AntdProgress(
            percent=round(100 * actual_value / target_value, 2), type="dashboard"
        )

    return fac.AntdResult(subTitle="请输入有效的目标值和实际值", status="warning")


if __name__ == "__main__":
    app.run(debug=False)