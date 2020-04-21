import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import utils
import logging
from typing import Union, List
import time

from radio import BaseRadio
from message import Message
from aircraft import Aircraft

# suppress logging of POST requests
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


class GUIData:
    """ Class for holding global data for display on GUI. This helps with loading data after refresh """
    aircraft: List[Aircraft] = []
    msg_log: List[str] = []
    radio: Union[None, BaseRadio] = None

    @classmethod
    def add_message(cls, msg: Message) -> None:
        """ add message to data. Updates msg_log and relevant aircraft """
        cls.msg_log.insert(0, str(msg))
        cls._update_aircraft(msg)

        if len(cls.msg_log) > 1000:
            cls.msg_log = cls.msg_log[100:]

    @classmethod
    def _update_aircraft(cls, msg: Message) -> None:
        for craft in cls.aircraft:
            if craft == msg.icao:
                craft.update(msg.data)
                break
        else:
            cls.aircraft.insert(0, Aircraft(msg.icao, msg.data))

        if len(cls.aircraft) > 100:
            cls.aircraft = cls.aircraft[25:]

    @classmethod
    def remove_old(cls) -> List[str]:
        """ Removes any aircraft that haven't recently changed. Returns list of removed ICAOs"""
        to_remove = []
        for craft in cls.aircraft:
            if round(time.time()) - craft.last_update > 180:
                to_remove.append(craft)
        for craft in to_remove:
            cls.aircraft.remove(craft)

        return [c.icao for c in to_remove]

    @classmethod
    def get_msg_log(cls) -> str:
        return '\n'.join(cls.msg_log)


plot_map = go.Figure()

app = dash.Dash('Airport 522', assets_folder='gui_assets')
app.title = 'Airport 522'
app.layout = html.Div(style={'display': 'flex', 'flexDirection': 'column', 'width': '100vw', 'height': '100vh'},
                      children=[
                          html.Div(style={'flex': 8, 'display': 'flex'}, children=[
                              html.Div(style={'flex': 1, 'padding': 8, 'display': 'flex', 'flexDirection': 'column'},
                                       children=[
                                           html.H2('Aircraft'),
                                           html.Ul(id='aircraft-list',
                                                   style={'flex': 1, 'borderStyle': 'solid', 'borderWidth': 2,
                                                          'margin': 0,
                                                          'list-style-type': 'none', 'padding': 0}, children=[])
                                       ]),
                              html.Div(style={'flex': 1, 'padding': 8, 'display': 'flex', 'flexDirection': 'column'},
                                       children=[
                                           html.H2('Map View'),
                                           dcc.Graph(id='map', style={'flex': 1}, figure=plot_map)
                                       ])
                          ]),
                          html.Div(style={'flex': 2, 'padding': 8}, children=[
                              html.H2('Raw Message Log'),
                              dcc.Textarea(id='message-log',
                                           style={'height': '70%', 'width': '100%', 'padding': 0, 'resize': 'none'},
                                           placeholder='Raw Messages appear here', readOnly=True)

                          ]),
                          dcc.Interval(id='interval', interval=1000, n_intervals=0)
                      ])


@app.callback([Output('message-log', 'value'), Output('map', 'figure'), Output('aircraft-list', 'children')],
              [Input('interval', 'n_intervals')],
              [State('message-log', 'value'), State('map', 'figure'), State('aircraft-list', 'children')])
def get_messages(n, old_msgs, fig, craft_list):
    """
    Main callback function for dash
    :param n: unused, but needed since we trigger function via interval
    :param old_msgs: string value inside raw message log. Used for no-op calls to keep log the same
    :param fig: the map. Can update data dictionary directly
    :param craft_list: the children of the aircraft list. Used to determine if refresh occured
    :return: message log, map figure, aircraft list (list of <li> elements)
    """
    msgs = GUIData.radio.get_all_queue()
    valid = [m for m in msgs if m is not None and m.valid]

    # refresh data to remove old aircraft and delete them from map
    for r in GUIData.remove_old():
        remove_aircraft_map(fig, r)

    if len(valid) == 0 and not (len(craft_list) < len(GUIData.aircraft)):
        # print('No msgs')
        return old_msgs, fig, build_aircraft_ul()
    print(f"[{' '.join([m.icao for m in valid])}]")

    # add messages/aircraft to global data
    for m in reversed(valid):
        GUIData.add_message(m)

    # set locations on map for all known aircraft
    for craft in GUIData.aircraft:
        if craft['lat'].value_str != 'Unknown':
            update_aircraft_map(fig, craft['lat'].value, craft['lon'].value, craft.icao)

    return GUIData.get_msg_log(), fig, build_aircraft_ul()


def build_aircraft_ul() -> List[html.Li]:
    """
    Builds the aircraft list for the GUI
    :return: a list of <li> elements
    """
    children = []
    for craft in GUIData.aircraft:
        li = html.Li(id=f'li-{craft.icao}', style={'display': 'flex', 'padding': 8, 'border-bottom': '2px solid gray'},
                     children=[
                         html.Div(style={'flex': 3}, children=[
                             html.P(style={'margin': 0}, children=[
                                 html.H3(f'{craft.model}', title="Model", style={'display': 'inline', 'margin': 0}),
                                 html.H4(f'  |  {craft.operator}', title='Operator', style={'display': 'inline'}),
                                 html.I(f'  (Updated: {round(time.time()) - craft.last_update}s ago)',
                                        style={'display': 'inline'})

                             ]),
                             html.P(style={'margin': 0, 'marginLeft': 12}, children=[
                                 html.P(f'ID: {craft["id"].value}', title='Flight ID',
                                        style={'display': 'inline', 'margin': 0}),
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


def update_aircraft_map(fig: go.Figure, lat: float, lon: float, icao_id: str) -> None:
    """ Updates position of an aircraft on the map (or adds it if new) """
    lat, lon = round(lat, 4), round(lon, 4)
    for trace in fig['data']:
        if trace['name'] == icao_id:
            trace['lat'] = [lat]
            trace['lon'] = [lon]
            break
    else:
        fig['data'].append(go.Scattermapbox(lat=[lat], lon=[lon], mode='markers', hoverinfo='lat+lon+name',
                                            marker=dict(size=12, color=f'#{icao_id}'), name=icao_id))


def remove_aircraft_map(fig: go.Figure, icao_id: str) -> None:
    """ Removes given aircraft from the map """
    fig['data'] = [t for t in fig['data'] if t['name'] != icao_id]


def run_gui(radio: BaseRadio, debug: bool):
    """ Runs the GUI """
    GUIData.radio = radio

    plot_map.add_trace(go.Scattermapbox(lat=[utils.REF_LAT], lon=[utils.REF_LON], mode='markers',
                                        marker=dict(size=16, color='rgb(255,0,0)'), hoverinfo='lat+lon+name',
                                        name='Ref. Loc.'))
    plot_map.update_layout(mapbox=dict(style='stamen-terrain', bearing=0, zoom=8,
                                       center=dict(lat=utils.REF_LAT, lon=utils.REF_LON)),
                           legend=dict(x=0, y=1, bgcolor='rgba(224,224,224,0.85)'),
                           margin=dict(l=0, r=0, t=0, b=0, pad=0))
    app.run_server(debug=debug)
