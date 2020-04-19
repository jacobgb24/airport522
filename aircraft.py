from time import time
from typing import List, Any
from message import Message
from data_handler import DataPoint

class Aircraft:

    def __init__(self, icao_id, attrs):
        self.icao = icao_id
        self.last_update = time()
        self.attrs = attrs

    def update(self, new_attrs):
        self.attrs.update(new_attrs)

    def __getitem__(self, item):
        if item not in self.attrs.keys():
            return DataPoint('Unknown', 'Unknown', '')
        return self.attrs[item]

    def __setitem__(self, key, value):
        self.attrs[key] = value
        self.last_update = time()

    def __eq__(self, other: Any):
        if isinstance(other, Aircraft):
            return other.icao == self.icao
        elif isinstance(other, str):
            return other == self.icao
        return False


class AircraftGroup:
    aircraft: List[Aircraft] = []

    @classmethod
    def update_aircraft(cls, msg: Message):
        for craft in cls.aircraft:
            if craft == msg.icao:
                craft.update(msg.data)
                return
        cls.aircraft.append(Aircraft(msg.icao, msg.data))
