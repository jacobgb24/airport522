from data_handler import DataHandler, DataPoint
from utils import *
from enum import Enum


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
            self.icao = bin2hex(self.bin_msg[8:32]).upper()
            self.capability = bin2int(self.bin_msg[5:8])
            self.typecode = bin2int(self.bin_msg[32:37])
            self.bin_data = self.bin_msg[37:88]
            # these require some extra work
            self.type = MessageType.from_tc(self.typecode)
            self.data = DataHandler.dispatch(self)

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
            return False

        return True

    def __str__(self):
        if self.valid:
            return ('#' * MSG_LEN) + f'\n{self.bin_msg}\n{self.icao}: DF={self.df}, CA={self.capability}, TC={self.typecode}, ' \
                               f'TYPE={self.type.name}\n\tDATA={list(self.data.values())}'
        else:
            return f'Invalid ({self.bin_msg})'





