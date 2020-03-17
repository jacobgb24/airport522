import sys
from bitstring import BitArray
import numpy as np
# so stupid it installs here, but too lazy to fix at this point
sys.path.append('/usr/lib/python3.6/site-packages/')
import adi



class Radio():
    FREQ = int(1090e6)
    BANDWIDTH = 1000
    RATE = int(2e6)  # protocol rate of 2 bits per microsecond
    AMP_DIFF = 0.8  # signal amplitude threshold difference between 0 and 1 bit
    PREAMB_KEY = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]  # packets always start with this code
    MSG_LEN = 112  # bits
    BUFF_SIZE = 1024 * 200

    def __init__(self):
        self.sdr = adi.Pluto()
        self.sdr.rx_lo = Radio.FREQ
        self.sdr.sample_rate = Radio.RATE
        self.sdr.rx_rf_bandwidth = Radio.RATE
        self.sdr.tx_cyclic_buffer = True
        self.sdr.gain_control_mode = 'slow_attack'
        self.raw_buf = []
        self.noise_floor = 1e6

    def recv(self):
        raw = self.sdr.rx()
        self.raw_buf.extend(np.absolute(raw).tolist())

        if len(self.raw_buf) > self.BUFF_SIZE:
            self.handle_raw()

    def handle_raw(self):
        min_amp = self.get_min_amp()

        i = 0
        while i < len(self.raw_buf):
            if self.raw_buf[i] < min_amp:
                # print(f'BELOW AMP: {self.raw_buf[i]} < {min_amp}')
                i += 1
                continue
            if self.is_preamb(self.raw_buf[i:i+len(Radio.PREAMB_KEY)]):
                # print('PREAMB' * 25)
                start = i + len(self.PREAMB_KEY)
                end = start + (self.MSG_LEN + 1) * 2  # multiply by 2 since one bit == two values
                msg = self.raw_to_bits(self.raw_buf[start:end])
                # print(f'MSG: {msg}')
                i = end
                if len(msg) >= 50:
                    print(msg)
                    df = int(msg[:5], 2)
                    print(f'DF: {df}')
                    if df == 17 or df == 18:
                        icao = msg[8:32]
                        print(hex(int(icao, 2)))
                    # exit()

            else:
                i += 1
        self.raw_buf = self.raw_buf[i:]

    @staticmethod
    def raw_to_bits(data):
        thresh = max(data) * .2
        msg = ''
        for i in range(0, len(data), 2):
            if data[i] < thresh and data[i+1] < thresh:
                break
            if data[i] >= data[i+1]:
                msg += '1'
            else:
                msg += '0'
        return msg

    def get_min_amp(self):
        """Calculate noise floor"""
        window = 200  # microseconds
        total_len = len(self.raw_buf)
        means = (
            np.array(self.raw_buf[: total_len // window * window])
            .reshape(-1, window)
            .mean(axis=1)
        )
        self.noise_floor = min(min(means), self.noise_floor)
        return 3.162 * self.noise_floor  # not sure how they get this, but should be ~10dB

    @staticmethod
    def is_preamb(data) -> bool:
        if len(data) < 16:
            return False
        thresh = max(data) * .8
        normed = [1 if b >= thresh else 0 for b in data]
        # print(f'NORMED PREAMB: {normed}')
        for i, b in enumerate(Radio.PREAMB_KEY):
            if normed[i] != b:
                return False
        return True




test = Radio()
while True:
    test.recv()

