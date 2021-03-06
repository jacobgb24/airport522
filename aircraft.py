from time import time
from typing import Tuple, Any, Dict
from data_handler import DataPoint
from csv import reader


class Aircraft:

    def __init__(self, icao_id: str, attrs: Dict[str, DataPoint]):
        self.icao = icao_id
        self.last_update = round(time())
        self.attrs = attrs
        self.model, self.operator = AircraftICAODB.get_info(icao_id)

    def update(self, new_attrs):
        """ Update aircraft's info with new_attrs from a message """
        self.last_update = round(time())
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


class AircraftICAODB:
    """ Static class for getting data from CSV file """
    mapping = {}
    # file from - https://junzis.com/adb/data
    # it's outdated, but the best free source I could find
    # file not in repo as it's not mine
    _file = 'aircraft_db.csv'

    @classmethod
    def get_info(cls, icao_id: str) -> Tuple[str, str]:
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
