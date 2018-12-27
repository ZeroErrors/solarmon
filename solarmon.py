#!/usr/bin/env python3

import time
import os

from configparser import RawConfigParser
from influxdb import InfluxDBClient

from growatt import Growatt

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

db_name = settings.get('influx', 'db_name', fallback='inverter')
measurement = settings.get('influx', 'measurement', fallback='inverter')

# Clients
print('Setup InfluxDB Client... ', end='')
influx = InfluxDBClient(host=settings.get('influx', 'host', fallback='localhost'),
                        port=settings.getint('influx', 'port', fallback=8086),
                        username=settings.get('influx', 'username', fallback=None),
                        password=settings.get('influx', 'password', fallback=None),
                        database=db_name)
influx.create_database(db_name)
print('Done!')

print('Setup Serial Connection... ', end='')
growatt = Growatt(port=settings.get('inverter', 'port', fallback='/dev/ttyUSB0'))
print('Dome!')

while True:
    try:
        now = time.time()
        info = growatt.read()

        # If the inverter is not on because no power is being generated then we sleep for 1 min
        if info is None:
            time.sleep(settings.getint('query', 'offline_interval', fallback=60))
            continue

        points = [{
            'time': int(now),
            'measurement': measurement,
            "fields": info
        }]

        print(points)

        if not influx.write_points(points, time_precision='s'):
            print("Failed to write to DB!")

        time.sleep(settings.getint('query', 'interval', fallback=1))
    except Exception as err:
        print(err)
        time.sleep(settings.getint('query', 'error_interval', fallback=60))
