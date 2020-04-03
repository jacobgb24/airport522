from utils import *
from enum import Enum
import numpy as np

class MessageType(Enum):
    AIRCRAFT_ID = range(1, 5)
    SURFACE_POSITION = range(5, 9)
    AIRBORNE_POSITION = list(range(9, 19)) + list(range(20, 23))
    AIRBORNE_VELOCITY = range(19, 20)
    # below are v1+ only.
    AIRCRAFT_STATUS = range(28, 29)
    TARGET_STATE_STATUS = range(29, 30)
    OPERATION_STATUS = range(31, 32)
    UNKNOWN = range(0, 32)


    @classmethod
    def from_tc(cls, tc):
        for e in cls:
            if tc in e.value:
                return e
        return cls.UNKNOWN


class Message:
    CHECK_GEN = '1111111111111010000001001'  # used as key in crc

    def __init__(self, bin_msg):
        self.bin_msg = bin_msg
        self.valid = self._is_valid()
        if self.valid:
            # these are all straight from headers
            self.df = bin2int(self.bin_msg[:5])
            self.icao = bin2hex(self.bin_msg[8:32])
            self.capability = bin2int(self.bin_msg[5:8])
            self.typecode = bin2int(self.bin_msg[32:37])
            self.raw_data = self.bin_msg[37:88]
            # these require some extra work
            self.type = MessageType.from_tc(self.typecode)
            self.data = self._interpret_data()

    @classmethod
    def from_raw(cls, raw):
        """Create a Message from raw signal (uses ``raw2bin()``"""
        return cls(cls.raw2bin(raw))

    @staticmethod
    def raw2bin(raw):
        if len(raw) == 0:
            return ''
        thresh = max(raw) * .2  # want data at least this strong
        msg = ''
        for i in range(0, len(raw), 2):
            if i + 1 >= len(raw):
                break
            # print(f"THRESH: {thresh} compared to 1={raw[i]}, 2={raw[i+1]}")
            if raw[i] < thresh and raw[i + 1] < thresh:
                break
            if raw[i] >= raw[i + 1]:
                msg += '1'
            else:
                msg += '0'
        return msg

    def _is_valid(self) -> bool:
        if len(self.bin_msg) != MSG_LEN:
            # print(f'bad len: {len(self.bin_msg)}')
            return False

        # CRC check based on: https://en.wikipedia.org/wiki/Cyclic_redundancy_check#Computation
        msg_cpy = list(self.bin_msg)
        while '1' in msg_cpy[:88]:
            cur_shift = msg_cpy.index('1')
            for i in range(len(Message.CHECK_GEN)):
                msg_cpy[cur_shift + i] = str(int(Message.CHECK_GEN[i] != msg_cpy[cur_shift + i]))
        if '1' in msg_cpy[88:]:
            print('bad CS')
            return False

        return True

    def _interpret_data(self):
        if self.type == MessageType.AIRCRAFT_ID:
            return handle_identity(self.typecode, self.raw_data)
        if self.type == MessageType.AIRBORNE_VELOCITY:
            return handle_velocity(self.typecode, self.raw_data)
        # priority: TC 19,11,29,31 (maybe)

    def __str__(self):
        if self.valid:
            return ('#' * MSG_LEN) + f'\n{self.bin_msg}\n{self.icao}: DF={self.df}, CA={self.capability}, TC={self.typecode}, ' \
                               f'TYPE={self.type.name}\n\tDATA={self.data}'
        else:
            return f'Invalid ({self.bin_msg})'


def handle_identity(tc, data):
    ret = {}
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
    ret['type'] = class_table[tc - 1][ec]
    craft_id = ''
    for i in range(3, len(data), 6):
        craft_id += char_table[bin2int(data[i:i+6])]
    ret['id'] = craft_id
    return ret


def handle_velocity(tc, data):
    ret = {}
    subtype = bin2int(data[:3])
    # ret['supersonic'] = subtype == 2 or subtype == 4
    ret['horz_type'] = 'GROUND' if subtype <= 2 else 'AIR'
    ic = data[3] == 1  # ???

    if subtype <= 2:  # GROUND SPEED
        # sign and value from data
        v_we = (-1 if bin2bool(data[8]) else 1) * (bin2int(data[9:19]) - 1)
        v_sn = (-1 if bin2bool(data[19]) else 1) * (bin2int(data[20:30]) - 1)

        v = np.sqrt(np.square(v_we) + np.square(v_sn))
        h_deg = (np.rad2deg(np.arctan2(v_we, v_sn)) + 360) % 360
        ret['horz_vel (kt)'] = round(v, 3)
        ret['heading (deg)'] = round(h_deg, 3)

    ret['vert_type'] = 'BARO' if bin2bool(data[28]) else 'GEO'
    # sign 0=up, 1=down
    v_ud = (-1 if bin2bool(data[31]) == "1" else 1) * (bin2int(data[32:41]) - 1) * 64

    ret['vert_vel (ft/min)'] = v_ud
    
    return ret



