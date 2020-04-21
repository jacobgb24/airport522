import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import utils
import logging
from typing import Union, List

from radio import BaseRadio
from message import Message, MessageType
from aircraft import Aircraft

# suppress logging of POST requests
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class GUIData:
    aircraft: List[Aircraft] = []
    msg_log: List[str] = []
    radio: Union[None, BaseRadio] = None

    @classmethod
    def add_message(cls, msg: Message):
        cls.msg_log.insert(0, str(msg))
        cls._update_aircraft(msg)

        if len(cls.msg_log) > 1000:
            cls.msg_log = cls.msg_log[100:]

    @classmethod
    def _update_aircraft(cls, msg: Message):
        for craft in cls.aircraft:
            if craft == msg.icao:
                craft.update(msg.data)
                break
        else:
            cls.aircraft.insert(0, Aircraft(msg.icao, msg.data))

        if len(cls.aircraft) > 100:
            cls.aircraft = cls.aircraft[25:]

    @classmethod
    def get_msg_log(cls) -> str:
        return '\n'.join(cls.msg_log)


plot_map = go.Figure()

app = dash.Dash('Airport 522', assets_folder='gui_assets')
app.title = 'Airport 522'
app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'column', 'width': '100vw', 'height': '100vh'}, children=[
    html.Div(style={'flex': 8, 'display': 'flex'}, children=[
        html.Div(style={'flex': 1, 'padding': 8, 'display': 'flex', 'flexDirection': 'column'}, children=[
            html.H2('Aircraft'),
            html.Ul(id='aircraft-list', style={'flex': 1, 'borderStyle': 'solid', 'borderWidth': 2, 'margin': 0,
                                               'list-style-type': 'none', 'padding': 0}, children=[])
        ]),
        html.Div(style={'flex': 1, 'padding': 8,  'display': 'flex', 'flexDirection': 'column'}, children=[
            html.H2('Map View'),
            dcc.Graph(id='map', style={'flex': 1}, figure=plot_map)
        ])
    ]),
    html.Div(style={'flex': 2, 'padding': 8}, children=[
        html.H2('Raw Message Log'),
        dcc.Textarea(id='message-log', style={'height': '70%', 'width': '100%', 'padding': 0, 'resize': 'none'},
                     placeholder='Raw Messages appear here', readOnly=True)

    ]),
    dcc.Interval(id='interval', interval=1000, n_intervals=0)
])


@app.callback([Output('message-log', 'value'), Output('map', 'figure'), Output('aircraft-list', 'children')],
              [Input('interval', 'n_intervals')],
              [State('message-log', 'value'), State('map', 'figure'), State('aircraft-list', 'children')])
def get_messages(n, old_msgs, fig, craft_list):
    msgs = GUIData.radio.get_all_queue()
    valid = [m for m in msgs if m is not None and m.valid]
    if len(valid) == 0 and not (len(craft_list) < len(GUIData.aircraft)):
        # print('No msgs')
        return old_msgs, fig, craft_list
    print(valid)

    # add messages/aircraft to global data
    for m in reversed(valid):
        GUIData.add_message(m)

    # set locations on map for all known aircraft
    for craft in GUIData.aircraft:
        if craft['lat'].value_str != 'Unknown':
            update_aircraft_map(fig, craft['lat'].value, craft['lon'].value, craft.icao)

    return GUIData.get_msg_log(), fig, build_aircraft_ul()


def build_aircraft_ul():
    children = []
    for craft in GUIData.aircraft:
        li = html.Li(id=f'li-{craft.icao}', style={'display': 'flex', 'padding': 8, 'border-bottom': '2px solid gray'}, children=[
            html.Div(style={'flex': 3}, children=[
                html.P(style={'margin': 0}, children=[
                    html.H3(f'{craft.model}', title="Model", style={'display': 'inline', 'margin': 0}),
                    html.P(f'  |  {craft.operator}', title='Operator', style={'display': 'inline'}),
                ]),
                html.P(style={'margin': 0, 'marginLeft': 8}, children=[
                    html.B(f'ID: {craft["id"].value}', title='Flight ID', style={'display': 'inline', 'margin': 0}),
                    html.P(f'  ({craft.icao})', title='ICAO ID', style={'display': 'inline'}),
                    html.P(f'Horz. Vel.: {craft["horz_vel"].value_str} {craft["horz_vel"].unit}',
                           title='Horizontal Velocity', style={'margin': 0}),
                    html.P(f'Vert. Vel.: {craft["vert_vel"].value_str} {craft["vert_vel"].unit}',
                           title='Vertical Velocity', style={'margin': 0}),
                    html.P(f'Heading: {craft["heading"].value_str} {craft["heading"].unit}',
                           title='Heading', style={'margin': 0})

                ])
            ]),
            html.P(style={'flex': '0 1 auto', 'borderBottom': f'6px solid #{craft.icao}', 'height': 'auto',
                          'textAlign': 'right'}, children=[
                html.P(f'Lat: {craft["lat"].value_str} {craft["lat"].unit}', style={'margin': 0}),
                html.P(f'Lon: {craft["lon"].value_str} {craft["lon"].unit}', style={'margin': 0}),
                html.P(f'Alt: {craft["alt"].value} {craft["alt"].unit}', style={'margin': 0})
            ])
        ])
        children.append(li)
    return children


def update_aircraft_map(fig, lat, lon, icao_id):
    lat, lon = round(lat, 4), round(lon, 4)
    for trace in fig['data']:
        if trace['name'] == icao_id:
            trace['lat'] = [lat]
            trace['lon'] = [lon]
            break
    else:
        fig['data'].append(go.Scattermapbox(lat=[lat], lon=[lon], mode='markers', hoverinfo='lat+lon+name',
                                            marker=dict(size=12, color=f'#{icao_id}'), name=icao_id))


def run_gui(radio, debug):
    GUIData.radio = radio

    plot_map.add_trace(go.Scattermapbox(lat=[utils.REF_LAT], lon=[utils.REF_LON], mode='markers',
                                        marker=dict(size=16, color='rgb(255,0,0)'), hoverinfo='lat+lon+name',
                                        name='Ref. Loc.'))
    plot_map.update_layout(mapbox=dict(style='stamen-terrain', bearing=0, zoom=8,
                                       center=dict(lat=utils.REF_LAT, lon=utils.REF_LON)),
                           legend=dict(x=0, y=1, bgcolor='rgba(224,224,224,0.85)'),
                           margin=dict(l=0, r=0, t=0, b=0, pad=0))
    app.run_server(debug=debug)
