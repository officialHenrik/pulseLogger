#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import schedule
from influxdb import InfluxDBClient

# ------------------------------------------------------
# Influx cfg
USER = 'root'
PASSWORD = 'root'
DBNAME = 'test'
HOST = 'localhost'
PORT =  8086

# defines
VERBOSE = True
PULSE_IO_NBR = 20
LED_IO_NBR = 21
PULSE_DEBOUNCE_ms = 5
DB_LOG_INTERVAL_minutes = 1

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
PulseCnt = 0
tmr = Timer()

# ------------------------------------------------------
# Callback for writing data to database
def log_to_db():
    global PulseCnt

    # Sample pulse counter
    cnt = PulseCnt
    PulseCnt = 0
    print("({})".format(cnt))

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
             "value": cnt
                }
            }
    points.append(point)
    client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)

    if(client.write_points(points)):
        if VERBOSE:
            print("Inserting into influxdb, cnt: {}".format(cnt))
    else:
       	# failure, add the point to the counter again
        PulseCnt = PulseCnt + cnt
        print("Warning: failed inserting {} pulses into influxdb".format(cnt))

# ------------------------------------------------------
# Callback function to run in another thread when edges are detected
def edge_cb(channel):
    global PulseCnt, tmr

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
            print("\n{},  tp {}".format(PulseCnt, timeSinceLast))

    if PulseDetected:
        if VERBOSE:
            print("{}, len {}".format(PulseCnt, pulseLen))

        PulseCnt = PulseCnt+1
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
