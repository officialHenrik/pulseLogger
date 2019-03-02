
# Influx cfg
DB = {
    'USER': 'root',
    'PASSWORD': 'root',
    'DBNAME': 'test',
    'HOST': 'localhost',
    'PORT':  8086
}

# defines home
#PULSE = {
#    'PULSE_DEBOUNCE_ms': 5,
#    'PULSE_LEN_MIN_s': 0.015,
#    'PULSE_LEN_MAX_s': 0.15,
#    
#    "location": "home",
#    "sensor": "p.1",
#    "resolution": "10000",
#   "batch_length_s": 60 
#}

# defines tg
PULSE = {
    'PULSE_DEBOUNCE_ms': 1,
    'PULSE_LEN_MIN_s': 0.002,
    'PULSE_LEN_MAX_s': 0.034,
    
    "location": "tg",
    "sensor": "p.2",
    "resolution": "1000",
    "batch_length_s": 60
}

VERBOSE = True
PULSE_IO_NBR =  20
LED_IO_NBR = 21
