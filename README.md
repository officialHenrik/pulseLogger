# Energy logger
                         
A Raspberry pi reads power consumption from an electricity energy meter via the S0 led pulse output, and stores it in an influx database.

Sensor: Osram, SFH 3310 phototransistor

## Autostart

/lib/systemd/system/PulseCounter.service 

     [Unit]
     Description=My pulse counter Service
     After=multi-user.target

     [Service]
     Type=idle
     WorkingDirectory=/home/pi/projects/git/pulseLogger/
     ExecStart=/usr/bin/python3 /home/pi/projects/git/pulseLogger/pulseCounter.py
     User=pi
     Restart=always
     RestartSec=10

     [Install]
     WantedBy=multi-user.target
