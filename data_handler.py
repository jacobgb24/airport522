import utils
from utils import *
from typing import Any, List, Union, Dict
import numpy as np


class DataPoint:
    """ Simple data class for holding information for a given value. Defines standard display method """
    def __init__(self, label: str, value: Any, unit: Union[str, None] = None):
        self.label = label
        self.value = value
        self.unit = unit
        self.value_str = str(round(value, 4) if isinstance(value, float) else value)

    def __str__(self):
        return f'{self.label}: {self.value_str}{f" ({self.unit})" if self.unit is not None else ""}'

    def __repr__(self):
        return self.__str__()


class DataHandler:
    """ Static class for handling interpretation of message payloads """
    @classmethod
    def dispatch(cls, msg) -> Dict[str, DataPoint]:
        from message import MessageType
        switch = {
            MessageType.AIRCRAFT_ID: cls.handle_identity,
            MessageType.AIRBORNE_VELOCITY: cls.handle_velocity,
            MessageType.AIRBORNE_POSITION: cls.handle_position
        }
        return switch.get(msg.type, lambda tc, data: {})(msg.typecode, msg.bin_data)

    @staticmethod
    def handle_identity(tc, data):
        print(tc)
        vals = {}
        # table to translate int to character
        char_table = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ#####_###############0123456789######"
        # table to translate tc,ec into vehicle class
        class_table = [[],  # tc = 1 is reserved
                       ["N/A", "Surface Emergency Vehicle", "Surface Service Vehicle", "Fixed Ground Obstruction"],
                       ["N/A", "Glider/Sailplane", "Lighter-Than-Air", "Parachutist/Skydiver",
                        "Ultralight/Hang-glider/Paraglider", "", "UAV", "Space Vehicle"],
                       ["N/A", "Light", "Medium 1", "Medium 2", "High Vortex Aircraft", "Heavy", "High Performance",
                        "Rotorcraft"]]
        ec = bin2int(data[:3])
        vals['type'] = DataPoint('Type', class_table[tc - 1][ec])
        craft_id = ''
        for i in range(3, len(data), 6):
            craft_id += char_table[bin2int(data[i: i + 6])]
        vals['id'] = DataPoint('ID', craft_id.rstrip('_'))

        return vals

    @staticmethod
    def handle_velocity(tc, data):
        vals = {}
        subtype = bin2int(data[:3])
        # ret['supersonic'] = subtype == 2 or subtype == 4
        vals['horz_type'] = DataPoint('Horz. Type', 'GROUND' if subtype <= 2 else 'AIR')
        ic = data[3] == 1  # ???

        if subtype <= 2:  # GROUND SPEED
            # sign and value from data
            v_we = (-1 if bin2bool(data[8]) else 1) * (bin2int(data[9:19]) - 1)
            v_sn = (-1 if bin2bool(data[19]) else 1) * (bin2int(data[20:30]) - 1)

            v = np.sqrt(np.square(v_we) + np.square(v_sn))
            h_deg = (np.rad2deg(np.arctan2(v_we, v_sn)) + 360) % 360
            vals['horz_vel'] = DataPoint('Horz. Velocity', v, 'kts')
            vals['heading'] = DataPoint('Heading', h_deg, 'deg')

        vals['vert_type'] = DataPoint('Vert. Type', 'BARO' if bin2bool(data[28]) else 'GEO')
        # sign 0=up, 1=down
        v_ud = (-1 if bin2bool(data[31]) else 1) * (bin2int(data[32:41]) - 1) * 64
        vals['vert_vel'] = DataPoint('Vert. Velocity', v_ud, 'ft/min')

        return vals

    @staticmethod
    def handle_position(tc, data):
        vals = {}

        is_odd = bin2bool(data[16])
        lat_cpr = bin2int(data[17:34]) / 131072  # the cpr is 17 bits so this is max
        lon_cpr = bin2int(data[34:51]) / 131072

        # number of zones depends on message type
        d_lat = 360/59 if is_odd else 360/60  # constants predefined
        lat_ind = np.floor(utils.REF_LAT / d_lat) + np.floor((utils.REF_LAT % d_lat) / d_lat - lat_cpr + 0.5)
        lat = d_lat * (lat_ind + lat_cpr)
        vals['lat'] = DataPoint('Latitude', lat, 'deg')

        nl = np.floor(2 * np.pi / (np.arccos(1 - ((1 - np.cos(np.pi / 30)) / np.square(np.cos(lat * np.pi / 180))))))

        d_lon = (360 / (nl - (1 if is_odd else 0))) if nl - (1 if is_odd else 0) > 0 else 360
        lon_ind = np.floor(utils.REF_LON / d_lon) + np.floor((utils.REF_LON % d_lon) / d_lon - lon_cpr + 0.5)
        lon = d_lon * (lon_ind + lon_cpr)
        vals['lon'] = DataPoint('Longitude', lon, 'deg')

        alt_mult = 25 if bin2bool(data[10]) else 100
        alt = bin2int(data[3:10] + data[11:15]) * alt_mult - 1000
        vals['alt'] = DataPoint('Altitude', alt, 'ft')

        return vals
