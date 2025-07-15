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
                    "404 Not Found"
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



