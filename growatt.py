import datetime
from pymodbus.exceptions import ModbusIOException

# Codes
StateCodes = {
    0: 'Waiting',
    1: 'Normal',
    3: 'Fault'
}

ErrorCodes = {
    0: 'None',
    24: 'Auto Test Failed',
    25: 'No AC Connection',
    26: 'PV Isolation Low',
    27: 'Residual Current High',
    28: 'DC Current High',
    29: 'PV Voltage High',
    30: 'AC Voltage Outrange',
    31: 'AC Freq Outrange',
    32: 'Module Hot'
}

for i in range(1, 24):
    ErrorCodes[i] = "Error Code: %s" % str(99 + i)

DeratingMode = {
    0: 'No Deratring',
    1: 'PV',
    2: '',
    3: 'Vac',
    4: 'Fac',
    5: 'Tboost',
    6: 'Tinv',
    7: 'Control',
    8: '*LoadSpeed',
    9: '*OverBackByTime',
}

def read_single(row, index, unit=10):
    return float(row.registers[index]) / unit

def read_double(row, index, unit=10):
    return float((row.registers[index] << 16) + row.registers[index + 1]) / unit

def merge(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class Growatt:
    def __init__(self, client, name, unit):
        self.client = client
        self.name = name
        self.unit = unit

        self.read_info()

    def read_info(self):
        row = self.client.read_holding_registers(73, unit=self.unit)
        if type(row) is ModbusIOException:
            raise row

        self.modbusVersion = row.registers[0]

    def print_info(self):
        print('Growatt:')
        print('\tName: ' + str(self.name))
        print('\tUnit: ' + str(self.unit))
        print('\tModbus Version: ' + str(self.modbusVersion))

    def read(self):
        row = self.client.read_input_registers(0, 33, unit=self.unit)
        if type(row) is ModbusIOException:
            return None

        # http://www.growatt.pl/dokumenty/Inne/Growatt%20PV%20Inverter%20Modbus%20RS485%20RTU%20Protocol%20V3.04.pdf
        #                                           # Unit,     Variable Name,      Description
        info = {                                    # ==================================================================
            'StatusCode': row.registers[0],         # N/A,      Inverter Status,    Inverter run state
            'Status': StateCodes[row.registers[0]],
            'Ppv': read_double(row, 1),             # 0.1W,     Ppv H,              Input power (high)
                                                    # 0.1W,     Ppv L,              Input power (low)
            'Vpv1': read_single(row, 3),            # 0.1V,     Vpv1,               PV1 voltage
            'PV1Curr': read_single(row, 4),         # 0.1A,     PV1Curr,            PV1 input current
            'PV1Watt': read_double(row, 5),         # 0.1W,     PV1Watt H,          PV1 input watt (high)
                                                    # 0.1W,     PV1Watt L,          PV1 input watt (low)
            'Vpv2': read_single(row, 7),            # 0.1V,     Vpv2,               PV2 voltage
            'PV2Curr': read_single(row, 8),         # 0.1A,     PV2Curr,            PV2 input current
            'PV2Watt': read_double(row, 9),         # 0.1W,     PV2Watt H,          PV2 input watt (high)
                                                    # 0.1W,     PV2Watt L,          PV2 input watt (low)
            'Pac': read_double(row, 11),            # 0.1W,     Pac H,              Output power (high)
                                                    # 0.1W,     Pac L,              Output power (low)
            'Fac': read_single(row, 13, 100),       # 0.01Hz,   Fac,                Grid frequency
            'Vac1': read_single(row, 14),           # 0.1V,     Vac1,               Three/single phase grid voltage
            'Iac1': read_single(row, 15),           # 0.1A,     Iac1,               Three/single phase grid output current
            'Pac1': read_double(row, 16),           # 0.1VA,    Pac1 H,             Three/single phase grid output watt (high)
                                                    # 0.1VA,    Pac1 L,             Three/single phase grid output watt (low)
            'Vac2': read_single(row, 18),           # 0.1V,     Vac2,               Three phase grid voltage
            'Iac2': read_single(row, 19),           # 0.1A,     Iac2,               Three phase grid output current
            'Pac2': read_double(row, 20),           # 0.1VA,    Pac2 H,             Three phase grid output power (high)
                                                    # 0.1VA,    Pac2 L,             Three phase grid output power (low)
            'Vac3': read_single(row, 22),           # 0.1V,     Vac3,               Three phase grid voltage
            'Iac3': read_single(row, 23),           # 0.1A,     Iac3,               Three phase grid output current
            'Pac3': read_double(row, 24),           # 0.1VA,    Pac3 H,             Three phase grid output power (high)
                                                    # 0.1VA,    Pac3 L,             Three phase grid output power (low)
            'EnergyToday': read_double(row, 26),    # 0.1kWh,   Energy today H,     Today generate energy (high)
                                                    # 0.1kWh,   Energy today L,     Today generate energy today (low)
            'EnergyTotal': read_double(row, 28),    # 0.1kWh,   Energy total H,     Total generate energy (high)
                                                    # 0.1kWh,   Energy total L,     Total generate energy (low)
            'TimeTotal': read_double(row, 30, 2),   # 0.5S,     Time total H,       Work time total (high)
                                                    # 0.5S,     Time total L,       Work time total (low)
            'Temp': read_single(row, 32)            # 0.1C,     Temperature,        Inverter temperature
        }

        row = self.client.read_input_registers(33, 8, unit=self.unit)
        info = merge(info, {
            'ISOFault': read_single(row, 0),        # 0.1V,     ISO fault Value,    ISO Fault value
            'GFCIFault': read_single(row, 1, 1),    # 1mA,      GFCI fault Value,   GFCI fault Value
            'DCIFault': read_single(row, 2, 100),   # 0.01A,    DCI fault Value,    DCI fault Value
            'VpvFault': read_single(row, 3),        # 0.1V,     Vpv fault Value,    PV voltage fault value
            'VavFault': read_single(row, 4),        # 0.1V,     Vac fault Value,    AC voltage fault value
            'FacFault': read_single(row, 5, 100),   # 0.01 Hz,  Fac fault Value,    AC frequency fault value
            'TempFault': read_single(row, 6),       # 0.1C,     Temp fault Value,   Temperature fault value
            'FaultCode': row.registers[7],          #           Fault code,         Inverter fault bit
            'Fault': ErrorCodes[row.registers[7]]
        })

        # row = self.client.read_input_registers(41, 1, unit=self.unit)
        # info = merge_dicts(info, {
        #    'IPMTemp': read_single(row, 0),         # 0.1C,     IPM Temperature,    The inside IPM in inverter Temperature
        # })

        row = self.client.read_input_registers(42, 2, unit=self.unit)
        info = merge(info, {
            'PBusV': read_single(row, 0),           # 0.1V,     P Bus Voltage,      P Bus inside Voltage
            'NBusV': read_single(row, 1),           # 0.1V,     N Bus Voltage,      N Bus inside Voltage
        })

        # row = self.client.read_input_registers(44, 3, unit=self.unit)
        # info = merge_dicts(info, {
        #                                            #           Check Step,         Product check step
        #                                            #           IPF,                Inverter output PF now
        #                                            #           ResetCHK,           Reset check data
        # })
        #
        # row = self.client.read_input_registers(47, 1, unit=self.unit)
        # info = merge_dicts(info, {
        #    'DeratingMode': row.registers[6],       #           DeratingMode,       DeratingMode
        #    'Derating': DeratingMode[row.registers[6]]
        # })

        row = self.client.read_input_registers(48, 16, unit=self.unit)
        info = merge(info, {
            'Epv1_today': read_double(row, 0),      # 0.1kWh,   Epv1_today H,       PV Energy today
                                                    # 0.1kWh,   Epv1_today L,       PV Energy today
            'Epv1_total': read_double(row, 2),      # 0.1kWh,   Epv1_total H,       PV Energy total
                                                    # 0.1kWh,   Epv1_total L,       PV Energy total
            'Epv2_today': read_double(row, 4),      # 0.1kWh,   Epv2_today H,       PV Energy today
                                                    # 0.1kWh,   Epv2_today L,       PV Energy today
            'Epv2_total': read_double(row, 6),      # 0.1kWh,   Epv2_total H,       PV Energy total
                                                    # 0.1kWh,   Epv2_total L,       PV Energy total
            'Epv_total': read_double(row, 8),       # 0.1kWh,   Epv_total H,        PV Energy total
                                                    # 0.1kWh,   Epv_total L,        PV Energy total
            'Rac': read_double(row, 10),            # 0.1Var,   Rac H,              AC Reactive power
                                                    # 0.1Var,   Rac L,              AC Reactive power
            'E_rac_today': read_double(row, 12),    # 0.1kVarh, E_rac_today H,      AC Reactive energy
                                                    # 0.1kVarh, E_rac_today L,      AC Reactive energy
            'E_rac_total': read_double(row, 14),    # 0.1kVarh, E_rac_total H,      AC Reactive energy
                                                    # 0.1kVarh, E_rac_total L,      AC Reactive energy
        })

        # row = self.client.read_input_registers(64, 2, unit=self.unit)
        # info = merge_dicts(info, {
        #    'WarningCode': row.registers[0],        #           WarningCode,        Warning Code
        #    'WarningValue': row.registers[1],       #           WarningValue,       Warning Value
        # })
        #
        # info = merge_dicts(info, self.read_fault_table('GridFault', 90, 5))

        return info

    # def read_fault_table(self, name, base_index, count):
    #     fault_table = {}
    #     for i in range(0, count):
    #         fault_table[name + '_' + str(i)] = self.read_fault_record(base_index + i * 5)
    #     return fault_table
    #
    # def read_fault_record(self, index):
    #     row = self.client.read_input_registers(index, 5, unit=self.unit)
    #     # TODO: Figure out how to read the date for these records?
    #     print(row.registers[0],
    #             ErrorCodes[row.registers[0]],
    #             '\n',
    #             row.registers[1],
    #             row.registers[2],
    #             row.registers[3],
    #             '\n',
    #             2000 + (row.registers[1] >> 8),
    #             row.registers[1] & 0xFF,
    #             row.registers[2] >> 8,
    #             row.registers[2] & 0xFF,
    #             row.registers[3] >> 8,
    #             row.registers[3] & 0xFF,
    #             row.registers[4],
    #             '\n',
    #             2000 + (row.registers[1] >> 4),
    #             row.registers[1] & 0xF,
    #             row.registers[2] >> 4,
    #             row.registers[2] & 0xF,
    #             row.registers[3] >> 4,
    #             row.registers[3] & 0xF,
    #             row.registers[4]
    #           )
    #     return {
    #         'FaultCode': row.registers[0],
    #         'Fault': ErrorCodes[row.registers[0]],
    #         #'Time': int(datetime.datetime(
    #         #    2000 + (row.registers[1] >> 8),
    #         #    row.registers[1] & 0xFF,
    #         #    row.registers[2] >> 8,
    #         #    row.registers[2] & 0xFF,
    #         #    row.registers[3] >> 8,
    #         #    row.registers[3] & 0xFF
    #         #).timestamp()),
    #         'Value': row.registers[4]
    #     }
