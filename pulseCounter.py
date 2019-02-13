#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import schedule
from influxdb import InfluxDBClient

from batchCollector import BatchCollector
from timer import Timer

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
PULSE_LEN_MIN_s = 0.015
PULSE_LEN_MAX_s = 0.15

# Global
tmr = Timer()
pulseStat = BatchCollector()
points = []
# ------------------------------------------------------
# Callback for writing data to database
def log_to_db():
    global pulseStat, points

    # Sample pulse counter
    pulseStat.sampleAndReset()
    cnt = pulseStat.getCnt()
    print("(#{:d}, mean:{:.4f}s, min:{:.4f} max:{:.4f})".format(cnt, pulseStat.getMean(), pulseStat.getMin(), pulseStat.getMax()))

    # Insert into db
    point = {
        "measurement": 'PulseCnt',
        "tags": {
            "location": "home",
            "sensor": "p.1",
            "resolution": "10000",
            "batch_length_s": "60" 
        },
        "fields": {
             "value": cnt,
             "pulse_mean":   pulseStat.getMean(),
             "pulse_min":    pulseStat.getMin(),
             "pulse_max":    pulseStat.getMax(),
             "pulse_stdSqr": pulseStat.getStdSqr()
                }
            }
    points.append(point)
    client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)

    if(client.write_points(points)):
        points = []
        if VERBOSE:
            print("Inserting into influxdb, cnt: {}".format(cnt))
    else:
       	# failure, keep the pulses and try again next time
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
        if(pulseLen > PULSE_LEN_MIN_s and pulseLen < PULSE_LEN_MAX_s):
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
GPIO.setmode(GPIO.BCM) # set up BCM GPIO numbering
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
try:
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    GPIO.cleanup() # clean up 
