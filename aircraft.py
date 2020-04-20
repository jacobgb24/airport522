from time import time
from typing import List, Any
from message import Message
from data_handler import DataPoint
from csv import reader

class Aircraft:

    def __init__(self, icao_id, attrs):
        self.icao = icao_id
        self.last_update = time()
        self.attrs = attrs
        self.model, self.operator = AircraftICAODB.get_info(icao_id)

    def update(self, new_attrs):
        self.last_update = time()
        self.attrs.update(new_attrs)

    def __getitem__(self, item):
        if item not in self.attrs.keys():
            return DataPoint('Unknown', 'Unknown', '')
        return self.attrs[item]

    def __eq__(self, other: Any):
        if isinstance(other, Aircraft):
            return other.icao == self.icao
        elif isinstance(other, str):
            return other == self.icao
        return False

    def __lt__(self, other):
        return self.last_update > other.last_update


class AircraftGroup:
    aircraft: List[Aircraft] = []

    @classmethod
    def update_aircraft(cls, msg: Message):
        for craft in cls.aircraft:
            if craft == msg.icao:
                craft.update(msg.data)
                break
        else:
            cls.aircraft.insert(0, Aircraft(msg.icao, msg.data))


class AircraftICAODB:
    mapping = {}
    # file from - https://junzis.com/adb/data
    _file = 'aircraft_db.csv'

    @classmethod
    def get_info(cls, icao_id):
        """ Returns the model and operator of an aircraft with the given ICAO ID """
        if len(cls.mapping) == 0:
            cls._generate_mapping()
        return cls.mapping.get(icao_id.lower(), ('Unknown', 'Unknown'))

    @classmethod
    def _generate_mapping(cls):
        with open(cls._file, newline='') as csv:
            data = list(reader(csv))
            for line in data[1:]:
                model = line[3] if len(line[3]) > 0 else 'Unknown'
                operator = line[4] if len(line[4]) > 0 else 'Unknown'
                cls.mapping[line[0]] = (model, operator)
