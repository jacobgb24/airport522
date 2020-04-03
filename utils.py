# constants
MSG_LEN = 112


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
