import datetime
from pymodbus.exceptions import ModbusIOException

def read_single(row, index, unit=10):
    return float(row.registers[index]) / unit

def read_double(row, index, unit=10):
    return float((row.registers[index] << 16) + row.registers[index + 1]) / unit

def merge(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class Growatt_SPH_TL3:
    def __init__(self, client, name, unit):
        self.client = client
        self.name = name
        self.unit = unit

        self.read_info()

    def read_info(self):
        row = self.client.read_holding_registers(88, unit=self.unit)
        if type(row) is ModbusIOException:
            raise row

        self.modbusVersion = row.registers[0]

    def print_info(self):
        print('Growatt:')
        print('\tName: ' + str(self.name))
        print('\tUnit: ' + str(self.unit))
        print('\tModbus Version: ' + str(self.modbusVersion))

    def read(self):
        row = self.client.read_input_registers(0, 100, unit=self.unit)
        if type(row) is ModbusIOException:
            return None

        # https://github.com/evcc-io/evcc/files/10957121/New-Modbus.RS485.RTU.Protocal.Latest.Ver.pdf

        # Codes for hybrid TL3 BH-UP with battery
        StateCodes = {
            0: 'Waiting',
            1: 'Selftest',
            2: 'Reserved',
            3: 'Fault',
            4: 'Flash',
            5: 'PV_BAT_ONline_Normal',
            6: 'BAT_ONline_Normal',
            7: 'PV_OFFline_Normal',
            8: 'BAT_OFFline_Normal'
        }

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
            'Pac': read_double(row, 35),            # 0.1W,     Pac H,              Output power (high)
                                                    # 0.1W,     Pac L,              Output power (low)
            'Fac': read_single(row, 37, 100),       # 0.01Hz,   Fac,                Grid frequency
            'Vac1': read_single(row, 38),           # 0.1V,     Vac1,               Three/single phase grid voltage
            'Iac1': read_single(row, 39),           # 0.1A,     Iac1,               Three/single phase grid output current
            'Pac1': read_double(row, 40),           # 0.1VA,    Pac1 H,             Three/single phase grid output watt (high)
                                                    # 0.1VA,    Pac1 L,             Three/single phase grid output watt (low)
            'Vac2': read_single(row, 42),           # 0.1V,     Vac2,               Three phase grid voltage
            'Iac2': read_single(row, 43),           # 0.1A,     Iac2,               Three phase grid output current
            'Pac2': read_double(row, 44),           # 0.1VA,    Pac2 H,             Three phase grid output power (high)
                                                    # 0.1VA,    Pac2 L,             Three phase grid output power (low)
            'Vac3': read_single(row, 46),           # 0.1V,     Vac3,               Three phase grid voltage
            'Iac3': read_single(row, 47),           # 0.1A,     Iac3,               Three phase grid output current
            'Pac3': read_double(row, 48),           # 0.1VA,    Pac3 H,             Three phase grid output power (high)
                                                    # 0.1VA,    Pac3 L,             Three phase grid output power (low)
            'EnergyToday': read_double(row, 53),    # 0.1kWh,   Energy today H,     Today generate energy (high)
                                                    # 0.1kWh,   Energy today L,     Today generate energy today (low)
            'EnergyTotal': read_double(row, 55),    # 0.1kWh,   Energy total H,     Total generate energy (high)
                                                    # 0.1kWh,   Energy total L,     Total generate energy (low)
            'TimeTotal': read_double(row, 57, 2),   # 0.5S,     Time total H,       Work time total (high)
                                                    # 0.5S,     Time total L,       Work time total (low)
            'Temp': read_single(row, 93)            # 0.1C,     Temperature,        Inverter temperature
        }

        row = self.client.read_input_registers(105, 1, unit=self.unit)
        info = merge(info, {
            'FaultCode': row.registers[0],          #           Fault code,         Inverter fault bit
        })

        row = self.client.read_input_registers(98, 2, unit=self.unit)
        info = merge(info, {
            'PBusV': read_single(row, 0),           # 0.1V,     P Bus Voltage,      P Bus inside Voltage
            'NBusV': read_single(row, 1),           # 0.1V,     N Bus Voltage,      N Bus inside Voltage
        })

        row = self.client.read_input_registers(59, 8, unit=self.unit)
        info = merge(info, {
            'Epv1_today': read_double(row, 0),      # 0.1kWh,   Epv1_today H,       PV Energy today
                                                    # 0.1kWh,   Epv1_today L,       PV Energy today
            'Epv1_total': read_double(row, 2),      # 0.1kWh,   Epv1_total H,       PV Energy total
                                                    # 0.1kWh,   Epv1_total L,       PV Energy total
            'Epv2_today': read_double(row, 4),      # 0.1kWh,   Epv2_today H,       PV Energy today
                                                    # 0.1kWh,   Epv2_today L,       PV Energy today
            'Epv2_total': read_double(row, 6),      # 0.1kWh,   Epv2_total H,       PV Energy total
                                                    # 0.1kWh,   Epv2_total L,       PV Energy total
        })

        row = self.client.read_input_registers(91, 16, unit=self.unit)
        info = merge(info, {
            'Epv_total': read_double(row, 0),       # 0.1kWh,   Epv_total H,        PV Energy total
                                                    # 0.1kWh,   Epv_total L,        PV Energy total
        })

        row = self.client.read_input_registers(1009, 6, unit=self.unit)
        info = merge(info, {
            'Pdischarge1': read_double(row, 0),       # 0.1W,   Pdischarge1 H,       Discharge power
                                                        # 0.1W,   Pdischarge1 L,       Discharge power
            'Pcharge1': read_double(row, 2),          # 0.1W,   Pcharge1 H,          Charge power
                                                        # 0.1W,   Pcharge1 L,          Charge power
            'Vbat': read_single(row, 4),              # 0.1V,   Vbat                 Battery voltage
            'SOC': row.registers[5],                  # 1%,     SOC                  State of charge Capacity
        })

        row = self.client.read_input_registers(1044, 20, unit=self.unit)
        info = merge(info, {
            'Etouser_today': read_double(row, 0),       # 0.1W,   Etouser_today H,          Energy to user today
                                                            # 0.1W,   Etouser_today L,          Energy to user today
            'Etouser_total': read_double(row, 2),       # 0.1W,   Etouser_total H,          Energy to user total
                                                            # 0.1W,   Etouser_total L,          Energy to user total
            'Etogrid_today': read_double(row, 4),       # 0.1W,   Etogrid_today H,          Energy to grid today
                                                            # 0.1W,   Etogrid_today L,          Energy to grid today
            'Etogrid_total': read_double(row, 6),       # 0.1W,   Etogrid_total H,          Energy to grid total
                                                            # 0.1W,   Etogrid_total L,          Energy to grid total
            'Edischarge1_today': read_double(row, 8),   # 0.1W,   Edischarge1_today H,      Discharge energy1 today
                                                            # 0.1W,   Edischarge1_today L,      Discharge energy1 today
            'Edischarge1_total': read_double(row, 10),  # 0.1W,   Edischarge1_total H,      Total discharge energy1
                                                            # 0.1W,   Edischarge1_total L,      Total discharge energy1
            'Echarge1_today': read_double(row, 12),     # 0.1W,   Echarge1_today H,         Charge1 energy today
                                                            # 0.1W,   Echarge1_today L,         Charge1 energy today
            'Echarge1_total': read_double(row, 14),     # 0.1W,   Echarge1_total H,         Charge1 energy total
                                                            # 0.1W,   Echarge1_total L,         Charge1 energy total
        })

        # row = self.client.read_input_registers(64, 2, unit=self.unit)
        # info = merge_dicts(info, {
        #    'WarningCode': row.registers[0],        #           WarningCode,        Warning Code
        #    'WarningValue': row.registers[1],       #           WarningValue,       Warning Value
        # })
        #
        # info = merge_dicts(info, self.read_fault_table('GridFault', 90, 5))

        return info
