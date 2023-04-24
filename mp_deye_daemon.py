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

import sys
import time
import network
import gc
import machine
from machine import WDT

from mp_deye_config import DeyeConfig
from mp_deye_connector import DeyeConnector
from mp_deye_modbus import DeyeModbus
from mp_deye_sensors import sensor_list
from mp_deye_mqtt import DeyeMqttClient
from mp_deye_observation import Observation


class DeyeDaemon():
    
    def __init__(self, config: DeyeConfig):
        self.__config = config
        self.log_level = config.log_level
        self.wdt_enable = config.wdt_enable
        self.mqtt_client = DeyeMqttClient(config)
        connector = DeyeConnector(config)
        self.modbus = DeyeModbus(config, connector)
        self.sensors = [s for s in sensor_list if s.in_any_group(self.__config.metric_groups)]

    def do_task(self):
        if self.log_level <= 20: print("INFO: Reading start")
        if self.wdt_enable: wdt = WDT()
        if self.wdt_enable: wdt.feed()
        try:
            
            regs = self.modbus.read_registers(0x3c, 0x3f)
            if self.wdt_enable: wdt.feed()
            gc.collect()
            regs.update(self.modbus.read_registers(0x40, 0x4f))
            if self.wdt_enable: wdt.feed()
            gc.collect()
            regs.update(self.modbus.read_registers(0x50, 0x5f))
            if self.wdt_enable: wdt.feed()
            gc.collect()
            regs.update(self.modbus.read_registers(0x6d, 0x74))
            if self.wdt_enable: wdt.feed()
            gc.collect()

            timestamp = time.localtime()
            observations = []
            for sensor in self.sensors:
                value = sensor.read_value(regs)
                if value is not None:
                    observation = Observation(sensor, timestamp, value)
                    observations.append(observation)
                    if self.log_level <= 10: print(f"DEBUG: Observation {observation.sensor.name}: {observation.value_as_str()}")

            self.mqtt_client.publish_observations(observations)
            self.mqtt_client.publish_os_mem_free()
            self.mqtt_client.publish_os_resetcause()
            if self.wdt_enable: wdt.feed()
            gc.collect()
            if self.log_level <= 20: print("INFO: Reading completed")

        except:
            if self.log_level <= 30: print("WARN: Cannot read from Inverter (do_task)")
            

def os_mem_free():
    m_free = gc.mem_free()
    m_alloc = gc.mem_alloc()
    m_total = m_free + m_alloc
    m_pct = '{0:.2f}%'.format(m_free/m_total*100)
    return ('Total:{0} Free:{1} ({2})'.format(m_total,m_free,m_pct))
  
def restart_and_reconnect():
    print('Fatal Error: Restart and reconnect')
    time.sleep(10)
    machine.reset()
  
def main():

    # Disable AP_IF (which is active per default)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    config = DeyeConfig.from_env()
    
    if config.wdt_enable: wdt = WDT()

    # Activate WLAN Connection
    if config.log_level <= 20: print("INFO: Connecting to Wifi")
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(config.wifi_ssid, config.wifi_pwd)

    while station.isconnected() == False:
        if config.log_level <= 20: print(".", end=" ")
        if config.wdt_enable: wdt.feed()
        time.sleep(1)
        pass
    
    if config.log_level <= 20: print("INFO: Wifi Connection successful")
    
    daemon = DeyeDaemon(config)

    while station.isconnected() == True:
        if config.wdt_enable: wdt.feed()
        daemon.do_task()
        gc.collect()
        if config.log_level <= 20: print("INFO: main() Loop memory:", os_mem_free())
        count = config.data_read_inverval
        while (count):
            if config.wdt_enable: wdt.feed()
            count -= 1
            time.sleep(1)


    station.disconnect()
    restart_and_reconnect()  # If connection gets lost

if __name__ == "__main__":
    main()
    
