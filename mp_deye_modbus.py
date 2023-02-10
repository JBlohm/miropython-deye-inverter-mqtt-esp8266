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

#import logging
import ubinascii

from mp_deye_connector import DeyeConnector
from mp_deye_config import DeyeConfig

def crc16(data: bytearray, poly: hex = 0xA001) -> str:
    '''
        CRC-16 MODBUS HASHING ALGORITHM
        All the credits to [kalebu](https://github.com/kalebu)
        
        MIT License

        Copyright (c) 2021 Jordan Kalebu

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
    '''
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc >> 1) ^ poly
                   if (crc & 0x0001)
                   else crc >> 1)

    hv = hex(crc).upper()[2:]
    blueprint = '0000'
    return (blueprint if len(hv) == 0 else blueprint[:-len(hv)] + hv)

class DeyeModbus:
    """ Simplified Modbus over TCP implementation that works with Deye Solar inverter.
        Supports only Modbus read-holding-registers function (0x03)
        Inspired by https://github.com/jlopez77/DeyeInverter
    """

    def __init__(self, config: DeyeConfig, connector: DeyeConnector):
        self.log_level = config.log_level
        self.config = config.logger
        self.connector = connector

    def read_registers(self, first_reg: int, last_reg: int) -> dict[int, int]:
        modbus_frame = self.__build_modbus_read_holding_registers_request_frame(first_reg, last_reg)
        req_frame = self.__build_request_frame(modbus_frame)
        resp_frame = self.connector.send_request(req_frame)
        modbus_resp_frame = self.__extract_modbus_response_frame(resp_frame)
        return self.__parse_modbus_read_holding_registers_response(modbus_resp_frame, first_reg, last_reg)

    def write_register(self, reg_address: int, reg_value: int) -> bool:
        modbus_frame = self.__build_modbus_write_holding_register_request_frame(reg_address, reg_value)
        req_frame = self.__build_request_frame(modbus_frame)
        resp_frame = self.connector.send_request(req_frame)
        modbus_resp_frame = self.__extract_modbus_response_frame(resp_frame)
        return self.__parse_modbus_write_holding_register_response(modbus_resp_frame, reg_address, reg_value)

    def __build_request_frame(self, modbus_frame) -> bytearray:
        start = bytearray(ubinascii.unhexlify('A5'))  # start
        length = (15 + len(modbus_frame) + 2).to_bytes(2, 'little')  # datalength
        controlcode = bytearray(ubinascii.unhexlify('1045'))  # controlCode
        inverter_sn_prefix = bytearray(ubinascii.unhexlify('0000'))  # serial
        datafield = bytearray(ubinascii.unhexlify('020000000000000000000000000000'))
        modbus_crc = bytearray(ubinascii.unhexlify(crc16(modbus_frame)))
        modbus_crc = bytearray(bytes(reversed(modbus_crc)))
        checksum = bytearray(ubinascii.unhexlify('00'))  # checksum placeholder for outer frame
        end_code = bytearray(ubinascii.unhexlify('15'))
        inverter_sn = bytearray(ubinascii.unhexlify('{:10x}'.format(self.config.serial_number).strip()))
        inverter_sn = bytearray(bytes(reversed(inverter_sn)))
        frame = start + length + controlcode + inverter_sn_prefix + inverter_sn + datafield \
            + modbus_frame + modbus_crc + checksum + end_code

        checksum = 0
        for i in range(1, len(frame) - 2, 1):
            checksum += frame[i] & 255
        frame[len(frame) - 2] = int((checksum & 255))

        return frame

    def __extract_modbus_response_frame(self, frame: bytearray) -> bytearray:
        # 29 - outer frame, 2 - modbus addr and command, 2 - modbus crc
        if not frame:
            if self.log_level <= 40: print(f"ERROR: No response frame")
            return None
        elif len(frame) == 29:
            self.__parse_response_error_code(frame)
            return None
        elif len(frame) < (29 + 4):
            if self.log_level <= 40: print(f"ERROR: Response frame is too short")
            return None
        elif frame[0] != 0xa5:
            if self.log_level <= 40: print(f"ERROR: Response frame has invalid starting byte")
            return None
        elif frame[-1] != 0x15:
            if self.log_level <= 40: print(f"ERROR: Response frame has invalid ending byte")
            return None

        return frame[25:-2]

    def __build_modbus_read_holding_registers_request_frame(self, first_reg, last_reg):
        reg_count = last_reg - first_reg + 1
        return bytearray(ubinascii.unhexlify('0103{:04x}{:04x}'.format(first_reg, reg_count)))

    def __parse_modbus_read_holding_registers_response(self, frame: bytearray, first_reg: int, last_reg: int) -> dict:
        reg_count = last_reg - first_reg + 1
        registers = {}
        expected_frame_data_len = 2 + 1 + reg_count * 2
        if not frame or len(frame) < expected_frame_data_len + 2: # 2 bytes for crc
            if self.log_level <= 40: print(f"ERROR: Modbus frame is too short or empty")
            return registers
        actual_crc = int.from_bytes(frame[expected_frame_data_len:expected_frame_data_len+2], 'little')
        expected_crc = int.from_bytes(ubinascii.unhexlify(crc16(frame[0:expected_frame_data_len])), 'big')
        if actual_crc != expected_crc:
            if self.log_level <= 40: print("ERROR: Modbus frame crc is not valid. Expected {:04x}, got {:04x}".format(
                expected_crc, actual_crc))
            return registers
        a = 0
        while a < reg_count:
            p1 = 3 + (a*2)
            p2 = p1 + 2
            registers[a + first_reg] = frame[p1:p2]
            a += 1
        return registers

    def __build_modbus_write_holding_register_request_frame(self, reg_address, reg_value):
        return bytearray(ubinascii.unhexlify('0110{:04x}000102{:04x}'.format(reg_address, reg_value)))

    def __parse_modbus_write_holding_register_response(self, frame, reg_address, reg_value):
        expected_frame_data_len = 6
        expected_frame_len = 6 + 2 # 2 bytes for crc
        if not frame:
            if self.log_level <= 40: print(f"ERROR: Modbus response frame is empty")
            return False
        elif len(frame) != expected_frame_len: 
            if self.log_level <= 40: print(f"ERROR: Wrong response frame length. Expected at least {expected_frame_len} bytes, got {len(frame)}")
            return False
        actual_crc = int.from_bytes(frame[expected_frame_data_len:expected_frame_data_len+2], 'little')
        expected_crc = int.from_bytes(ubinascii.unhexlify(crc16(frame[0:expected_frame_data_len])), 'big')
        if actual_crc != expected_crc:
            if self.log_level <= 40: print("ERROR: Modbus frame crc is not valid. Expected {:04x}, got {:04x}".format(
                expected_crc, actual_crc))
            return False
        returned_address = int.from_bytes(frame[2:4], 'big')
        returned_count = int.from_bytes(frame[4:6], 'big')
        if returned_address != reg_address or returned_count != 1:
            if self.log_level <= 40: print(f"ERROR: Returned address does not match sent value.")
            return False
        return True

    def __parse_response_error_code(self, frame):
        error_frame = frame[25:-2]
        error_code = error_frame[0]
        if error_code == 0x05:
            if self.log_level <= 40: print(f"ERROR: Modbus device address does not match.")
        elif error_code == 0x06:
            if self.log_level <= 40: print(f"ERROR: Logger Serial Number does not match. Check your configuration file.")
        else:
            if self.log_level <= 40: print("ERROR: Unknown response error code. Error frame: %s", error_frame.hex())

