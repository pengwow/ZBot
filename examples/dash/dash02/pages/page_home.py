import dash
from dash.dependencies import Input, Output, State
from dash import dcc,html
import random

app = dash.Dash(__name__)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

app.layout = html.Div([
    html.Div([

        dcc.Graph(
            id='graph-extendable',
            figure={'layout': {'title': 'Random title',
                               'barmode': 'overlay'},
                    'data': [{'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []},
                             {'x': [], 'y': []}, ]
                    }
        ),
    ]),

    dcc.Interval(
        id='interval-graph-update',
        interval=1000,
        n_intervals=0),
])


@app.callback(Output('graph-extendable', 'extendData'),
              [Input('interval-graph-update', 'n_intervals')]
              )
def create_then_extend_single_trace(n_intervals):

    return (dict(x=[
        [n_intervals],
        [n_intervals]
    ],

        y=[
        [n_intervals],
        [n_intervals**2]
    ]
    ),

        [0, 4]

    )


if __name__ == '__main__':
    app.run(debug=True)