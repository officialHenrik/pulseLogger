#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
from datetime import datetime
import schedule
from influxdb import InfluxDBClient

from batchCollector import BatchCollector
from timer import Timer

import config

# ------------------------------------------------------
# Global
tmr = Timer()
pulseStat = BatchCollector()
points = []
pulseDiscardedCnt = 0

# Influx client
# Instantiate a connection to the InfluxDB
try:
    client = InfluxDBClient(config.DB['HOST'], 
                            config.DB['PORT'], 
                            config.DB['USER'], 
                            config.DB['PASSWORD'], 
                            config.DB['DBNAME'])
except:
    print("Influxdb connection fault")

# ------------------------------------------------------
# Callback for writing data to database
def log_to_db():
    global pulseStat, points, pulseDiscardedCnt, client, config

    current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    # Sample pulse counter
    pulseStat.sampleAndReset()
    if config.VERBOSE:
        print("(#{:d}, mean:{:.4f}s, min:{:.4f} max:{:.4f}, discarded:{})".format(pulseStat.getCnt(), 
                                                                                  pulseStat.getMean(), 
                                                                                  pulseStat.getMin(), 
                                                                                  pulseStat.getMax(), 
                                                                                  pulseDiscardedCnt))
    
    # Generate pulse batch entry
    point = {
            "measurement": 'PulseCnt',
            "time": current_time,
            "tags": {
                "location": config.PULSE['location'],
                "sensor": config.PULSE['sensor'],
                "resolution": config.PULSE['resolution'],
                "batch_length_s": config.PULSE['batch_length_s'] 
            },
            "fields": {
                "value":           pulseStat.getCnt(),
                "pulse_mean":      pulseStat.getMean(),
                "pulse_min":       pulseStat.getMin(),
                "pulse_max":       pulseStat.getMax(),
                "pulse_stdSqr":    pulseStat.getStdSqr(),
                "pulse_discarded": pulseDiscardedCnt
                    }
            }
    points.append(point)
    pulseDiscardedCnt = 0

    # Insert into db
    if(client.write_points(points)):
        # Success
        points = []
        if config.VERBOSE:
            print("Inserting into influxdb, cnt: {}".format(pulseStat.getCnt()))
    else:
       	# failure, keep the pulses and try again next time
        print("Warning: failed inserting pulses into influxd")

    if config.VERBOSE_PULSE_CNT:
        print("({})".format(pulseStat.getCnt()))
        
# ------------------------------------------------------
# Callback function to run in another thread when edges are detected
def edge_cb(channel):
    global pulseStat, tmr, pulseDiscardedCnt, config

    # Rising or falling edge?
    if GPIO.input(config.PULSE_IO_NBR):
        # Rising edge, pulse done.
        pulseLen = tmr.sampleAndReset()
        # Check pulse length
        if(pulseLen > config.PULSE['PULSE_LEN_MIN_s'] and 
           pulseLen < config.PULSE['PULSE_LEN_MAX_s']):
            # Valid pulse
            pulseStat.add(pulseLen)
            # Print pulse dot
            if config.VERBOSE_PULSE_CNT:
                print(".", end="", flush=True)
        else:
            # Pulse looks strange, discard it
            pulseDiscardedCnt += 1

        GPIO.output(config.LED_IO_NBR, GPIO.LOW) # Debug led off

    else:
        # Falling edge, start of pulse. Start timer
        tmr.reset()
        GPIO.output(config.LED_IO_NBR,GPIO.HIGH) # Debug led on


# ------------------------------------------------------
   
# Setup
GPIO.setmode(GPIO.BCM) # set up BCM GPIO numbering
GPIO.setwarnings(True)

# Setup pulse input with pull up and connect callback on all edges
GPIO.setup(config.PULSE_IO_NBR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(config.PULSE_IO_NBR, GPIO.BOTH,  callback=edge_cb, bouncetime=config.PULSE['PULSE_DEBOUNCE_ms'])

# Led output
GPIO.setup(config.LED_IO_NBR, GPIO.OUT)
GPIO.output(config.LED_IO_NBR, GPIO.HIGH)

# Schedule logging of pulse counter value
schedule.every(config.PULSE['batch_length_s']).seconds.do(log_to_db)

# ------------------------------------------------------
# Run forever
try:
    while True:
       	schedule.run_pending()
        time.sleep(1)
finally:
    GPIO.cleanup() # clean up 
