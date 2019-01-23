#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import schedule
from influxdb import InfluxDBClient
import math

# ------------------------------------------------------
# Influx cfg
USER = 'root'
PASSWORD = 'root'
DBNAME = 'test'
HOST = 'localhost'
PORT =  8086

# defines
VERBOSE = False
PULSE_IO_NBR = 20
LED_IO_NBR = 21
PULSE_DEBOUNCE_ms = 5
DB_LOG_INTERVAL_minutes = 1

# ----------------------------------------------------
class PulseStat:
    def __init__(self):
        self.sum = 0.0
        self.sumSqr = 0.0
        self.n = 0
        self.last_std = 0.0
        self.last_mean = 0.0
        self.last_min = 0.0
        self.last_max = 0.0
        self.last_n = 0.0
        self.min = 10000.0
        self.max = 0.0
    def add(self, sample):
        self.sum = self.sum + sample
        self.sumSqr = self.sumSqr + sample*sample
        self.n = self.n + 1
        if sample > self.max:
            self.max = sample
        if sample < self.min:
            self.min = sample
    def sampleAndReset(self):
        n = self.n
        sum = self.sum
        self.n = 0
        self.sum = 0.0
        self.last_n = n
        self.last_mean = sum/n
        self.last_std = math.sqrt(self.sumSqr/n - self.last_mean*self.last_mean) 
        self.last_max = self.max
        self.last_min = self.min
        self.sumSqr = 0.0
        self.min = 10000.0
        self.max = 0.0
    def getCntNow(self):
        return self.n
    def getMean(self):
        return self.last_mean
    def getCnt(self):
        return self.last_n
    def getMin(self):
        return self.last_min
    def getMax(self):
        return self.last_max
    def getStd(self):
        return self.last_std

# -----------------------------------------------------
class Timer:
    def __init__(self):
        self.start = time.time()

    def sampleAndReset(self):
        now = time.time()
        diff = now - self.start
        self.start = now
        return diff

# Global parameters
tmr = Timer()
pulseStat = PulseStat()

# ------------------------------------------------------
# Callback for writing data to database
def log_to_db():
    global pulseStat

    # Sample pulse counter
    pulseStat.sampleAndReset()
    cnt = pulseStat.getCnt()
    print("(#{:d}, {:.4f}s, min:{:.4f} max:{:.4f} std:{:.8f})".format(cnt, pulseStat.getMean(), pulseStat.getMin(), pulseStat.getMax(), pulseStat.getStd()))

    # Insert into db
    points = []
    point = {
        "measurement": 'PulseCnt',
        "tags": {
            "location": "home",
            "sensor": "p.1",
            "resolution": "10000"
        },
        "fields": {
             "value": cnt,
             "pulse_mean": pulseStat.getMean(),
             "pulse_min": pulseStat.getMin(),
             "pulse_max": pulseStat.getMax(),
             "pulse_std": pulseStat.getStd()
                }
            }
    points.append(point)
    client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)

    if(client.write_points(points)):
        if VERBOSE:
            print("Inserting into influxdb, cnt: {}".format(cnt))
    else:
       	# failure, add the point to the counter again
        # PulseCnt = PulseCnt + cnt
        print("Warning: failed inserting {} pulses into influxdb".format(cnt))

# ------------------------------------------------------
# Callback function to run in another thread when edges are detected
def edge_cb(channel):
    global pulseStat, tmr

    pulseLen = 0
    timeSinceLast = 0
    PulseDetected = False

    if GPIO.input(PULSE_IO_NBR):
        pulseLen = tmr.sampleAndReset()
        if(pulseLen > 0.015 and pulseLen < 0.15):
            PulseDetected = True
    else:
        timeSinceLast = tmr.sampleAndReset()
        if VERBOSE:
            print("\n{},  tp {}".format(pulseStat.getCntNow(), timeSinceLast))

    if PulseDetected:
        if VERBOSE:
            print("{}, len {}".format(pulseStat.getCntNow(), pulseLen))

        pulseStat.add(pulseLen)
        print(".", end="", flush=True)

        # New pulse detected, toggle the led
        if GPIO.input(LED_IO_NBR):
            GPIO.output(LED_IO_NBR, GPIO.LOW)
        else:
            GPIO.output(LED_IO_NBR,GPIO.HIGH)
    else:
        if pulseLen > 0:
            print("Pulse discarded, len {}".format(pulseLen))

# ------------------------------------------------------
# Setup
GPIO.setmode(GPIO.BCM)      # set up BCM GPIO numbering
GPIO.setwarnings(True)

# Setup pulse input with pull up and connect callback on rising in edges
GPIO.setup(PULSE_IO_NBR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(PULSE_IO_NBR, GPIO.BOTH,  callback=edge_cb, bouncetime=PULSE_DEBOUNCE_ms)

# Led output
GPIO.setup(LED_IO_NBR,GPIO.OUT)

# Schedule logging of pulse counter value
schedule.every(DB_LOG_INTERVAL_minutes).minutes.do(log_to_db)

# ------------------------------------------------------
# Run forever
print("   _                __                  ")
print("  |_)    |  _  _   /   _    __ _|_ _ __ ")
print("  |  |_| | _> (/_  \__(_)|_|| | |_(/_|  ")
print("----------------------------------------")


try:
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    GPIO.cleanup() # clean up 
