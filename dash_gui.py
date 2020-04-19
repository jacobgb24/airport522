import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
import random

import utils
from radio import Radio, MockRadio
from message import Message, MessageType


plot_map = go.Figure()

app = dash.Dash('Airport 522', assets_folder='gui_assets')
app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'column', 'width': '100vw', 'height': '100vh'}, children=[
    html.Div(style={'flex': 8, 'display': 'flex'}, children=[
        html.Div(style={'flex': 1, 'padding': 8, 'display': 'flex', 'flexDirection': 'column'}, children=[
            html.H2('Current Aircraft'),
            html.Ul(id='aircraft-list', style={'flex': 1, 'borderStyle': 'solid', 'borderWidth': 2, 'margin': 0})
        ]),
        html.Div(style={'flex': 1, 'padding': 8,  'display': 'flex', 'flexDirection': 'column'}, children=[
            html.H2('Map View'),
            dcc.Graph(id='map', style={'flex': 1}, figure=plot_map)
        ])
    ]),
    html.Div(style={'flex': 2, 'padding': 8}, children=[
        html.H2('Raw Message Log'),
        dcc.Textarea(id='message-log', style={'height': '50%', 'width': '100%', 'padding': 0, 'resize': 'none'},
                     placeholder='Raw Messages appear here', readOnly=True)

    ]),
    dcc.Interval(id='interval', interval=1000, n_intervals=0)
])


@app.callback([Output('message-log', 'value'), Output('map', 'figure')],
              [Input('interval', 'n_intervals')],
              [State('message-log', 'value'), State('map', 'figure')])
def get_messages(n, old_msgs, fig):
    msgs = radio.recv()
    print(msgs)
    # put newest messages on top
    msg_log = '\n'.join([str(m) for m in reversed(msgs)]) + ('\n' if len(msgs) > 0 else '') + (old_msgs or '')
    for m in msgs:
        if m.valid:
            if m.type == MessageType.AIRBORNE_POSITION:
                update_aircraft_map(fig, m.data['lat'].value, m.data['lon'].value, m.icao)
    # print(msg_log)
    return msg_log, fig


def update_aircraft_map(fig, lat, lon, icao_id):
    lat, lon = round(lat, 4), round(lon, 4)
    for trace in fig['data']:
        if trace['name'] == icao_id:
            trace['lat'] = [lat]
            trace['lon'] = [lon]
            break
    else:
        color_str = f'rgb({random.randint(0, 255)},{random.randint(0, 255)},{random.randint(0, 255)})'
        fig['data'].append(go.Scattermapbox(lat=[lat], lon=[lon], mode='markers', hoverinfo='lat+lon+name',
                                            marker=dict(size=12, color=color_str), name=icao_id))


if __name__ == '__main__':
    utils.set_loc_ip()
    radio = Radio()
    # radio = MockRadio('data/synthetic/position.txt', 1000, False)
    plot_map.add_trace(go.Scattermapbox(lat=[utils.REF_LAT], lon=[utils.REF_LON], mode='markers',
                                        marker=dict(size=16, color='rgb(255,0,0)'), hoverinfo='lat+lon+name',
                                        name='Ref. Loc.'))
    plot_map.update_layout(mapbox=dict(style='stamen-terrain', bearing=0, zoom=8,
                                       center=dict(lat=utils.REF_LAT, lon=utils.REF_LON)),
                           legend=dict(x=0, y=1, bgcolor='rgba(224,224,224,0.85)'),
                           margin=dict(l=0, r=0, t=0, b=0, pad=0))
    # update_aircraft_map(utils.REF_LAT + .1, utils.REF_LON, 'test')
    app.run_server(debug=True)
