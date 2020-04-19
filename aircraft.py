from time import time
from typing import List, Dict, Union, Any
from message import Message

class Aircraft:

    def __init__(self, icao_id, attrs):
        self.id = icao_id
        self.last_update = time()
        self.attrs = attrs

    def update(self, new_attrs):
        self.attrs.update(new_attrs)

    def __getitem__(self, item):
        return self.attrs[item]

    def __setitem__(self, key, value):
        self.attrs[key] = value
        self.last_update = time()

    def __eq__(self, other: Any):
        if isinstance(other, Aircraft):
            return other.id == self.id
        elif isinstance(other, str):
            return other == self.id
        return False

