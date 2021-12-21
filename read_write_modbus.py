import time
from datetime import datetime
import os
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from configparser import RawConfigParser
from growatt import Growatt

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')


port = settings.get('solarmon', 'port', fallback='/dev/ttyUSB0')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
method = input('Enter read or write: ')
if method == "read":
    start = int(input('enter starting register to read from: '))
    numreg = input('enter number of registers to read [0-100]: ')
    row = client.read_input_registers(int(start), int(numreg))
    for r in range(int(numreg)):
        if row.registers[r] > 0:
            print(str(r) + " - " + str(row.registers[r]),sep=',' )
if method == "write":
    start = int(input("enter register you want to modify: "))
    rr = client.read_holding_registers(start,1,unit=1)
    print("current value for register " + str(start) + " is " + str(rr.registers[0]))
    writeval = input("What do you want to change it to? ")
    client.write_register(start,int(writeval))
    print('done')
    client.close()
    
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

#num = 109
#row = client.read_input_registers(0, num)
#for r in range(num):
#    if row.registers[r] > 0:
#        print(str(r) + " - " + str(row.registers[r]),sep=',' )


