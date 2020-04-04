import requests

# constants
MSG_LEN = 112
REF_LAT = None
REF_LON = None


# data format conversion
def bin2hex(b: str) -> str:
    return hex(int(b, 2))[2:]


def bin2int(b: str) -> int:
    return int(b, 2)


def int2bin(i: int) -> str:
    return format(i, 'b')


def bin2bool(b: str) -> bool:
    return all([b_ == "1" for b_ in b])


# unit conversion
def knot2mph(knots) -> float:
    return knots * 1.150779


# other
def set_loc_ip():
    """
    Set globals RED_LAT, REF_LON using a free IP lookup API
    In general, an IP should give back a result within 180M
    """
    global REF_LAT, REF_LON
    url = "http://ip-api.com/json/?fields=lat,lon"
    j = requests.get(url).json()
    REF_LAT, REF_LON = j['lat'], j['lon']
