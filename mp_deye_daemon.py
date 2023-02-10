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
        self.mqtt_client = DeyeMqttClient(config)
        connector = DeyeConnector(config)
        self.modbus = DeyeModbus(config, connector)
        self.sensors = [s for s in sensor_list if s.in_any_group(self.__config.metric_groups)]

    def do_task(self):
        if self.log_level <= 20: print(f"INFO: Reading start")
        try:
            
            regs = self.modbus.read_registers(0x3c, 0x4f)
            gc.collect()
            regs.update(self.modbus.read_registers(0x50, 0x5f))
            gc.collect()
            regs.update(self.modbus.read_registers(0x6d, 0x74))
            gc.collect()

            timestamp = time.localtime()
            observations = []
            for sensor in self.sensors:
                value = sensor.read_value(regs)
                if value is not None:
                    observation = Observation(sensor, timestamp, value)
                    observations.append(observation)
                    if self.log_level <= 10: print(f"DEBUG: {observation.sensor.name}: {observation.value_as_str()}")

            self.mqtt_client.publish_observations(observations)
            gc.collect()
            if self.log_level <= 20: print(f"INFO: Reading completed")

        except:
            if self.log_level <= 30: print(f"WARN: Cannot read from Inverter (do_task)")
            

def main():

    # Disable AP_IF (which is active per default)
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    config = DeyeConfig.from_env()
    daemon = DeyeDaemon(config)
    
    # Activate WLAN Connection
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(config.wifi_ssid, config.wifi_pwd)

    while station.isconnected() == False:
      pass
    
    if config.log_level <= 20: print(f"INFO: WLAN Connection successful")
    
    while True:
        daemon.do_task()
        gc.collect()
        time.sleep(config.data_read_inverval)


if __name__ == "__main__":
    main()
    
