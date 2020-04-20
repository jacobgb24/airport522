import sys
import numpy as np
import time
from multiprocessing import Process, Queue
from queue import Empty
from abc import ABC, abstractmethod
# so stupid it installs here, but too lazy to fix at this point
sys.path.append('/usr/lib/python3.6/site-packages/')
import adi

from message import Message
from utils import *


def proc_loop(radio, queue: Queue):
    while True:
        msgs = radio.recv()
        for m in msgs:
            queue.put(m)


class BaseRadio(ABC):

    def __init__(self, msg_queue: Queue):
        self.queue = msg_queue
        self.radio_proc = Process(target=proc_loop, args=(self, msg_queue))
        self.radio_proc.daemon = True
        self.radio_proc.start()

    def get_all_queue(self):
        msgs = []
        try:
            while True:
                msgs.append(self.queue.get_nowait())
        except Empty:
            return msgs

    @abstractmethod
    def recv(self):
        pass


class Radio(BaseRadio):
    PREAMB_KEY = [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]  # packets always start with this code
    BUFF_SIZE = 1024 * 200

    def __init__(self, msg_queue: Queue):
        # set up SDR
        self.sdr = adi.Pluto()
        self.sdr.rx_lo = int(1090e6)  # 1090MHz
        self.sdr.sample_rate = int(2e6)  # protocol rate of 2 bits per microsecond
        self.sdr.rx_rf_bandwidth = self.sdr.sample_rate
        self.sdr.gain_control_mode = 'slow_attack'

        self.raw_buf = []
        self.noise_floor = 1e6
        super().__init__(msg_queue)

    def recv(self):
        raw = self.sdr.rx()
        self.raw_buf.extend(np.absolute(raw).tolist())

        if len(self.raw_buf) > self.BUFF_SIZE:
            return self.handle_raw()
        return []

    def handle_raw(self):
        min_amp = self._get_min_amp()
        msgs = []
        i = 0
        while i < len(self.raw_buf):
            if self.raw_buf[i] < min_amp:
                # print(f'BELOW AMP: {self.raw_buf[i]} < {min_amp}')
                i += 1
            elif self.is_preamble(self.raw_buf[i:i + len(Radio.PREAMB_KEY)]):
                # print('PREAMB' * 25)
                start = i + len(self.PREAMB_KEY)
                end = start + (MSG_LEN + 1) * 2  # multiply by 2 since one bit == two values
                msg = Message.from_raw(self.raw_buf[start:end])
                msgs.append(msg)
                i = end
            else:
                i += 1
        self.raw_buf = self.raw_buf[i:]
        return msgs

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
        return 4 * self.noise_floor  # not sure how they get this, but should be ~10dB

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


class MockRadio(BaseRadio):
    """
    'Radio' that reads messages from a file instead
    """

    def __init__(self, msg_queue, in_file, repeat=True, repeat_delay=1, init_delay=1):
        """

        :param in_file: file of messages. Lines starting with `#` are ignored. Each line should be `timestamp binary_msg`
        :param repeat: whether radio should repeat file messages in a loop
        :param repeat_delay: wait in seconds before repeat starts
        :param init_delay: how long to wait initially before messages are sent
        """
        self.msgs = []
        self.next_msg = 0
        self.should_repeat = repeat
        self.repeat_delay = repeat_delay
        self.stop_send = False
        with open(in_file, 'r') as inp:
            rel_start = None
            for m in inp.readlines():
                if not m.startswith('#'):
                    ts, m = m.strip().split(' ')
                    if rel_start is None:
                        rel_start = int(ts)
                    self.msgs.append((int(ts) - rel_start, Message(m.strip())))
        self.init_time = round(time.time()) + init_delay
        super().__init__(msg_queue)

    def recv(self):
        curr_time = round(time.time())
        if not self.stop_send and curr_time - self.init_time >= self.msgs[self.next_msg][0]:
            msg = self.msgs[self.next_msg][1]
            if self.next_msg == len(self.msgs) - 1:
                if not self.should_repeat:
                    self.stop_send = True
                else:
                    self.init_time = curr_time + self.repeat_delay
            self.next_msg = (self.next_msg + 1) % len(self.msgs)

            return [msg]
        return []
