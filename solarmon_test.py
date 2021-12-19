
#!/usr/bin/env python3

import time
import os
from datetime import datetime

from configparser import RawConfigParser
#from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from growatt import Growatt
settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)

db_name = settings.get('influx', 'db_name', fallback='inverter')
measurement = settings.get('influx', 'measurement', fallback='inverter')

# Clients
print('Setup InfluxDB Client... ', end='')
from datetime import datetime

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# You can generate an API token from the "API Tokens Tab" in the UI
token = "-Ut_VEYEX6t70qTA1_nYR_0NdeKhpcSshEeNFIUO6in--tU4UsbzDxiayew7EFguI65OJx99dtCiiB3ZZXn9zA=="
org = "pwshaheen@gmail.com"
bucket = "SolarBucket"

with InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com", token=token, org=org) as influxc:
    #influxc.create_database(db_name)
    write_api = influxc.write_api(write_options=SYNCHRONOUS)

print('Setup Serial Connection... ', end='')
port = settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()

print('Loading inverters... ')
inverters = []
for section in settings.sections():
    if not section.startswith('inverters.'):
        continue

    name = section[10:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    growatt = Growatt(client, name, unit)
    #growatt.print_info()
    inverters.append({
        'error_sleep': 0,
        'growatt': growatt,
        'measurement': measurement
    })

while True:
    online = False
    for inverter in inverters:
        # If this inverter errored then we wait a bit before trying again
        if inverter['error_sleep'] > 0:
            inverter['error_sleep'] -= interval
            continue

        growatt = inverter['growatt']
        try:
            now = time.time()
            info = growatt.read()
            #print(info)

            if info is None:
                continue

            # Mark that at least one inverter is online so we should continue collecting data
            online = True

            points = [{
                'time': datetime.utcnow(),
                'tag': inverter['measurement'],
                'measurement':'Growatt_Inverter',
                "fields": info
            }]
            write_api.write(bucket, org, points)

        except Exception as err:
            print(growatt.name)
            print(err)
            print('there was an exception')
            inverter['error_sleep'] = error_interval
    if online:
        time.sleep(interval)
    else:
        # If all the inverters are not online because no power is being generated then we sleep for 1 min
        time.sleep(offline_interval)
