

def bits2hex(b: str) -> str:
    return hex(int(b, 2))[2:]


def bits2int(b: str) -> int:
    return int(b, 2)


def int2bits(i: int) -> str:
    return format(i, 'b')
