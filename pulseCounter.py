#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
from datetime import datetime
import schedule
from influxdb import InfluxDBClient

# ------------------------------------------------------
# Influx cfg
USER = 'root'
PASSWORD = 'root'
DBNAME = 'test'
HOST = 'localhost'
PORT =  8086

# Global parameters
PulseCnt = 0

# defines
PULSE_IO_NBR = 20
LED_IO_NBR = 21
PULSE_DEBOUNCE_ms = 4
DB_LOG_INTERVAL_minutes = 1

# ------------------------------------------------------
# Callback for writing data to database
def log_to_db():
    global PulseCnt

    # Sample pulse counter
    cnt = PulseCnt
    PulseCnt = 0

    # Insert into db
    points = []
    point = {
        "measurement": 'PulseCnt',
        "fields": {
             "value": cnt
                }
            }
    points.append(point)
    client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)

    if(client.write_points(points)):
        print("Inserting into influxdb, cnt: {}".format(cnt))
    else:
       	# failure, add the point to the counter again
        PulseCnt = PulseCnt + cnt
        print("Warning: failed inserting {} pulses into influxdb".format(cnt))

# ------------------------------------------------------
# Callback function to run in another thread when edges are detected
def rising_edge_cb(channel):
    global PulseCnt
    global LED_IO_NBR

    PulseCnt = PulseCnt+1
    #print(PulseCnt)

    # New pulse detected, toggle the led
    if GPIO.input(LED_IO_NBR):
        GPIO.output(LED_IO_NBR, GPIO.LOW)
    else:
        GPIO.output(LED_IO_NBR,GPIO.HIGH)

# ------------------------------------------------------
# Setup
GPIO.setmode(GPIO.BCM)      # set up BCM GPIO numbering
GPIO.setwarnings(True)

# Setup pulse input with pull up and connect callback on rising in edges
GPIO.setup(PULSE_IO_NBR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(PULSE_IO_NBR, GPIO.RISING,  callback=rising_edge_cb, bouncetime=PULSE_DEBOUNCE_ms)

# Led output
GPIO.setup(LED_IO_NBR,GPIO.OUT)

# Schedule logging of pulse counter value
schedule.every(DB_LOG_INTERVAL_minutes).minutes.do(log_to_db)

# ------------------------------------------------------
# Run forever
print("Pulse counter enabled")
try:
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    GPIO.cleanup() # clean up 
