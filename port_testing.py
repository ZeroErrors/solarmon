import time
import os

from configparser import RawConfigParser
from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from growatt import Growatt

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)

db_name = settings.get('influx', 'db_name', fallback='inverter')
measurement = settings.get('influx', 'measurement', fallback='inverter')

port = settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
inverters = []
for section in settings.sections():
    if not section.startswith('inverters.'):
        continue

    name = section[10:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    growatt = Growatt(client, name, unit)
    growatt.print_info()
    inverters.append({
        'error_sleep': 0,
        'growatt': growatt,
        'measurement': measurement
    })

#for a in range(48):
#    print('range is ' + str(a))
#    try:
#        row = client.read_input_registers(a,150)
#row = client.read_holding_registers(15, unit=1)
#        for r in range(150):
#            if row.registers[r] > 0:
#                print(str(r) + " - " + str(row.registers[r]),sep=',' )
#    except:
#        print('no data')    

num = 109
row = client.read_input_registers(0, num)
for r in range(num):
    if row.registers[r] > 0:
        print(str(r) + " - " + str(row.registers[r]),sep=',' )