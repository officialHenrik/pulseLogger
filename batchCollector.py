#!/usr/bin/env python3

# ----------------------------------------------------
class Data:
    def __init__(self):
        self.reset()

    def reset(self):
        self.n = 0
        self.sum = 0.0
        self.sumSqr = 0.0
        self.stdSqr = 0.0
        self.min = 99999999.0
        self.max = 0.0

# ----------------------------------------------------
class BatchCollector:

    def __init__(self):
        self.batch = Data()
        self.result = Data()

    def reset(self):
        self.batch.reset()

    def add(self, x):
        # Add new sample to batch
        self.batch.sum    = self.batch.sum + x
        self.batch.sumSqr = self.batch.sumSqr + x*x
        self.batch.n     += 1

        # Track max/min
        if x > self.batch.max:
            self.batch.max = x
        if x < self.batch.min:
            self.batch.min = x

    def sampleAndReset(self):
        # sample data
        self.result.n      = self.batch.n
        self.result.sum    = self.batch.sum
        self.result.sumSqr = self.batch.sumSqr
        self.result.max    = self.batch.max
        self.result.min    = self.batch.min
        # reset batch
        self.batch.reset()
        # calc mean
        self.result.mean   = self.result.sum   /self.result.n
        # calc standard deviation, skip sqrt
        self.result.stdSqr = self.result.sumSqr/self.result.n - self.result.mean*self.result.mean

    # Getters
    def getCntNow(self):
        return self.batch.n

    def getCnt(self):
        return self.result.n

    def getMean(self):
        return self.result.mean

    def getMin(self):
        return self.result.min

    def getMax(self):
        return self.result.max

    def getStdSqr(self):
        return self.result.stdSqr
