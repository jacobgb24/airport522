import sys
import numpy as np
# so stupid it installs here, but too lazy to fix at this point
sys.path.append('/usr/lib/python3.6/site-packages/')
import adi

from message import Message
from utils import *


class Radio:
    PREAMB_KEY = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]  # packets always start with this code
    BUFF_SIZE = 1024 * 200

    def __init__(self):
        # set up SDR
        self.sdr = adi.Pluto()
        self.sdr.rx_lo = int(1090e6)  # 1090MHz
        self.sdr.sample_rate = int(2e6)  # protocol rate of 2 bits per microsecond
        self.sdr.rx_rf_bandwidth = self.sdr.sample_rate
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
        min_amp = self._get_min_amp()

        i = 0
        while i < len(self.raw_buf):
            if self.raw_buf[i] < min_amp:
                # print(f'BELOW AMP: {self.raw_buf[i]} < {min_amp}')
                i += 1
                continue
            if self.is_preamble(self.raw_buf[i:i + len(Radio.PREAMB_KEY)]):
                # print('PREAMB' * 25)
                start = i + len(self.PREAMB_KEY)
                end = start + (MSG_LEN + 1) * 2  # multiply by 2 since one bit == two values
                msg = Message(self.raw_buf[start:end])
                if msg.valid:
                    print('\n' + str(msg))

                i = end
            else:
                i += 1
        self.raw_buf = self.raw_buf[i:]

    def _get_min_amp(self):
        """Calculate noise floor. This code almost entirely from pyModeS"""
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
    def is_preamble(data) -> bool:
        """Returns true if the given data is a valid preamble to a message"""
        if len(data) < 16:
            return False
        # set cut-off for 0/1 between minimum and maximum values in data
        thresh = min(data) + ((max(data) - min(data)) / 2)
        normed = [1 if b >= thresh else 0 for b in data]
        # print(f'NORMED PREAMB: {normed}')
        for i, b in enumerate(Radio.PREAMB_KEY):
            if normed[i] != b:
                return False
        return True

