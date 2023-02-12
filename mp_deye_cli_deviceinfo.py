# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import network
import esp

import sys

from mp_deye_config import DeyeConfig
from mp_deye_connector import DeyeConnector
from mp_deye_modbus import DeyeModbus


class DeyeCliDeviceInfo():

    def __init__(self, config: DeyeConfig):
        connector = DeyeConnector(config)
        self.__modbus = DeyeModbus(config, connector)
        self.log_level = config.log_level

    def read_info(self):
        ser_no=''
        micro=False
        for reg_address in [0,2,3,4,5,6,7,16,17,18,20,40]:
            registers = self.__modbus.read_registers(reg_address, reg_address)
            if registers is None:
                if self.log_level <= 40: print(f"ERROR: no registers read")
                sys.exit(1)
            if reg_address not in registers:
                if self.log_level <= 40: print(f"ERROR: register {reg_address} not read")
                sys.exit(1)
            reg_bytes = registers[reg_address]
            reg_value_int = int.from_bytes(reg_bytes, 'big')
            low_byte = reg_bytes[1]
            high_byte = reg_bytes[0]
            if self.log_level <= 10: print(f'DEBUG: reg_address: {reg_address} Result -> int: {reg_value_int}, lo_byte: {low_byte}, hi_byte: {high_byte}')
            if (reg_address == 0):
                if (low_byte == 2): print("Stringing Inverter")
                elif (low_byte == 3): print("Single-phase energy storage machine")
                elif (low_byte == 4):
                    print("Micro Inverter")
                    micro=True
                elif (low_byte == 5): print("Three-phase Energy Storage Machine")
            elif (reg_address == 2):
                print(f"Communication protocol version {low_byte}.{high_byte}")
            elif ((reg_address == 3) | (reg_address == 4) | (reg_address == 5) | (reg_address == 6) | (reg_address == 7)):
                ser_no = ser_no + chr(low_byte)+ chr(high_byte)
                if (reg_address == 7): print(f"Serial number {ser_no}")
            elif ((reg_address == 16) | (reg_address == 17)):
                if (reg_address == 16): rated_power = reg_value_int
                if (reg_address == 17): print(f"Rated power {(reg_value_int*65535+rated_power)/10} W")
            elif (reg_address == 20):
                if (reg_value_int==0): print(f"Remote lock OFF")
                elif (reg_value_int==2): print(f"Remote lock ON")
                elif (reg_value_int==2): print(f"Remote lock unknown")
            elif (reg_address == 40):
                if (micro == True): print(f"Active power regulation {reg_value_int} Percent")
                else: print(f"Active power regulation {reg_value_int/10} Percent")



def main():
    
    # Disable AP_IF (which is active per default)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    config = DeyeConfig.from_env()
    
    # Activate WLAN Connection
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(config.wifi_ssid, config.wifi_pwd)

    while station.isconnected() == False:
      pass
    
    print(f"WLAN Connection successful")
    cli = DeyeCliDeviceInfo(config)
    cli.read_info()

    station.disconnect()


if __name__ == "__main__":
    main()
