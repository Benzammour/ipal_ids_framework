from curses.ascii import NUL
import json
from turtle import st
import numpy as np

import ipal_iids.settings as settings
from ids.ids import MetaIDS


N = 10
Q = 1


#not finished but a start. Calculates q_min and q_max for one process value
class Task_3_1(MetaIDS):
    _name = "Task_3_1"
    _description = "Minumum and maximum change over a given window"
    _requires = ["train.state", "live.state"]


    def train(self, ipal=None, state=None):
        # Map each process to its maximum and minimum change:
        # We make sure both dicts have the same keys.
        max_change = {}
        min_change = {}

        # Calc Min Max in n Steps
        with self._open_file(state) as f:
            window_buf = []

            for i,line in enumerate(f.readlines()):
                cur_state = json.loads(line)
                window_buf.append(cur_state)

                # DEBUG: Assert all process values are present in all states:
                for process in cur_state["state"]:
                    assert process in window_buf[0]["state"]
                # DEBUG: Assert: one line for every second:
                if len(window_buf) > 1:
                    assert window_buf[-2]["timestamp"] + 1 == cur_state["timestamp"], str(cur_state["timestamp"]) + ", " + str(window_buf[-2]["timestamp"])

                for process in window_buf[0]["state"]:
                    diff = cur_state["state"][process] - window_buf[0]["state"][process]
                    if process in max_change:
                        if max_change[process] < diff:
                            max_change[process] = diff
                        if min_change[process] > diff:
                            min_change[process] = diff
                    else:
                        max_change[process] = diff
                        min_change[process] = diff

                # Remove the oldest entry:
                if len(window_buf) > N:
                    window_buf.pop(0)

        self.q_max_map = {}
        self.q_min_map = {}
        # Calculate q_min q_max
        for process in max_change:
            max_diff = max_change[process] - min_change[process]
            self.q_max_map[process] = max_change[process] + Q * max_diff
            self.q_min_map[process] = min_change[process] - Q * max_diff

        self.window_buf = []


    def new_state_msg(self, msg):
        self.window_buf.append(msg)

        # Remove old entries:
        while len(self.window_buf) > 1 and self.window_buf[1]["timestamp"] + N <= msg["timestamp"]:
            self.window_buf.pop(0)

        for process in self.window_buf[0]["state"]:
            # DEBUG
            assert process in msg["state"]

            diff = msg["state"][process] - self.window_buf[0]["state"][process]
            if diff < self.q_min_map[process]:
                return True, self.q_min_map[process]
            elif diff > self.q_max_map[process]:
                return True, self.q_max_map[process]

        return False, 0
