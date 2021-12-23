#!/usr/bin/env python3

import time
import os
from datetime import datetime
import urllib.request
import logging

from configparser import RawConfigParser

from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from growatt import Growatt

setupSleep = 1

#logging.basicConfig(filename='log.log', encoding='utf-8', level=logging.INFO,format='%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
#logging.info('Waiting 60 seconds for internet connection and influxDB to establish')
time.sleep(setupSleep)

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)

localEnabled = settings.get('influx', 'enabled')
db_name = settings.get('influx', 'db_name', fallback='inverter')
measurement = settings.get('influx', 'measurement', fallback='inverter')



# Clients
#logging.info('Setup InfluxDB Client... ')
influx = InfluxDBClient(host=settings.get('influx', 'host', fallback='localhost'),
                        port=settings.getint('influx', 'port', fallback=8086),
                        username=settings.get('influx', 'username', fallback=None),
                        password=settings.get('influx', 'password', fallback=None),
                        database=db_name)
influx.create_database(db_name)



# You can generate an API token from the "API Tokens Tab" in the UI
token = settings.get('influxCloud', 'token')
org = settings.get('influxCloud', 'org')
bucket = settings.get('influxCloud', 'bucket')
cloudEnabled = settings.get('influxCloud', 'enabled')
cloudHost = settings.get('influxCloud', 'host')

cloudError = 0
setupError = 1

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
with InfluxDBClient(url=cloudHost, token=token, org=org) as influxc:
    #influxc.create_database(db_name)
    #Cloud Influx Client which differs from Local One
    write_api = influxc.write_api(write_options=SYNCHRONOUS)
port = settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
#check if connected to internet

try:
    urllib.request.urlopen('http://google.com') 
    #logging.info('Internet Connection Found...Enabling Cloud Write if Set.')
except:
    cloudEnabled = "0"
    #logging.error('Internet Connection NOT Found...Disabling Cloud Write.')
while setupError > 0:
    try:
        #logging.info('Setup Serial Connection...')
        client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
        client.connect()
        setupError = 0
        print('no error')
        if (client.is_socket_open() == False):
            print('not open')
    except:
        #logging.error('Error Connecting to Inverter.  Error Count ' + str(setupError))
        setupError = setupError + 1
        print('error in while loop')
        time.sleep(15)
        continue