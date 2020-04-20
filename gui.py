import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State

import utils
from radio import Radio, MockRadio
from message import Message, MessageType
from aircraft import Aircraft, AircraftGroup

# suppress logging of POST requests
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

radio = None
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
        dcc.Textarea(id='message-log', style={'height': '50%', 'width': '100%', 'padding': 0, 'resize': 'none'},
                     placeholder='Raw Messages appear here', readOnly=True)

    ]),
    dcc.Interval(id='interval', interval=100, n_intervals=0)
])


@app.callback([Output('message-log', 'value'), Output('map', 'figure'), Output('aircraft-list', 'children')],
              [Input('interval', 'n_intervals')],
              [State('message-log', 'value'), State('map', 'figure'), State('aircraft-list', 'children')])
def get_messages(n, old_msgs, fig, craft_list):
    msgs = radio.recv()
    if not any([msg is not None and msg.valid for msg in msgs]):
        # print('No msgs')
        return old_msgs, fig, craft_list
    print(msgs)

    # put newest messages on top
    msg_log = '\n'.join([str(m) for m in reversed(msgs)]) + ('\n' if len(msgs) > 0 else '') + (old_msgs or '')
    for m in msgs:
        if m.valid:
            AircraftGroup.update_aircraft(m)
            if m.type == MessageType.AIRBORNE_POSITION:
                update_aircraft_map(fig, m.data['lat'].value, m.data['lon'].value, m.icao)
    # print(msg_log)
    return msg_log, fig, build_aircraft_list()


def build_aircraft_list():
    children = []
    for craft in AircraftGroup.aircraft:
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


def run_gui(loc_radio, debug):
    global radio
    radio = loc_radio

    plot_map.add_trace(go.Scattermapbox(lat=[utils.REF_LAT], lon=[utils.REF_LON], mode='markers',
                                        marker=dict(size=16, color='rgb(255,0,0)'), hoverinfo='lat+lon+name',
                                        name='Ref. Loc.'))
    plot_map.update_layout(mapbox=dict(style='stamen-terrain', bearing=0, zoom=8,
                                       center=dict(lat=utils.REF_LAT, lon=utils.REF_LON)),
                           legend=dict(x=0, y=1, bgcolor='rgba(224,224,224,0.85)'),
                           margin=dict(l=0, r=0, t=0, b=0, pad=0))
    app.run_server(debug=debug)
