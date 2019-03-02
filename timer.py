#!/usr/bin/env python3

import time

# -----------------------------------------------------
class Timer:
    def __init__(self):
        self.start = time.time()

    def sampleAndReset(self):
        now = time.time()
        diff = now - self.start
        self.start = now
        return diff

    def reset(self):
        self.start = time.time()