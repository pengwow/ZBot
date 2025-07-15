import dash
from dash import html
from assets.assets_file import CONTENT_STYLE

# 注册pages
dash.register_page(__name__, path='/')

layout = html.Div(
    children=[
        html.H1(children='This is our Home page'),
        html.Div(children='''This is our Home page content.'''),
    ],
    style=CONTENT_STYLE  # 指定样式
)

