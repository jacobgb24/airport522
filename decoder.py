from utils import *

def get_df(msg: str) -> int:
    return int(msg[:5], 2)

def get_icao(msg: str) -> str:
    return bits2hex(msg[8:32])