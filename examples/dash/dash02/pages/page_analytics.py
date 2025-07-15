import dash
from dash import html, dcc, callback, Input, Output
# from dash_daq import BooleanSwitch
from assets.assets_file import CONTENT_STYLE

# 注册pages
dash.register_page(__name__)

layout = html.Div(
    children=[
        html.H1(children='This is our Analytics page'),
        html.Div([
            "Select a city: ",
            dcc.RadioItems(['New York City', 'Montreal', 'San Francisco'],
                           'Montreal',
                           id='analytics-input')
        ]),
        html.Br(),
        html.Div(id='analytics-output'),
        html.Br(),
        # html.Div(BooleanSwitch(id='switch', on=False, label="开关", labelPosition="top",style={"float": "left"}))
    ],
    style=CONTENT_STYLE
)


# page_file.py 内写的callback也可以正常使用
@callback(
    Output('analytics-output', 'children'),
    Input('analytics-input', 'value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'

