import requests

# constants
MSG_LEN = 112
# these values should be set before messages are decoded. Set with ``set_loc_ip()``
REF_LAT = None
REF_LON = None


# data format conversion
def bin2hex(b: str) -> str:
    """ converts binary string to hex string """
    return hex(int(b, 2))[2:]


def bin2int(b: str) -> int:
    """ converts binary string to int """
    return int(b, 2)


def int2bin(i: int) -> str:
    """ converts int to binary string """
    return format(i, 'b')


def bin2bool(b: str) -> bool:
    """ converts binary string to bool (each bit is ANDed) """
    return all([b_ == "1" for b_ in b])


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
