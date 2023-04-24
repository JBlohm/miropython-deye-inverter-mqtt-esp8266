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

from umqtt.simple import MQTTClient
import machine
import ubinascii
import gc
import time

from mp_deye_config import DeyeConfig
from mp_deye_observation import Observation

class DeyeMqttClient():

    def __init__(self, config: DeyeConfig):
        self.log_level = config.log_level
        self.wdt_enable = config.wdt_enable
        
        # Call format: MQTTClient(client_id, server, port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={})        
        self.__mqtt_client = MQTTClient(ubinascii.hexlify(machine.unique_id()), config.mqtt.host, config.mqtt.port, config.mqtt.username, config.mqtt.password, keepalive=300)

        try:
            self.__mqtt_client.connect()
        except:
            if self.log_level <= 40: print("ERROR: MQTT connect error")
            time.sleep(2)
            machine.reset()
            
        self.__config = config.mqtt

    def __do_publish(self, observation: Observation):
        if self.wdt_enable: wdt = WDT()
        try:
            if observation.sensor.mqtt_topic_suffix:
                if self.wdt_enable: wdt.feed()
                mqtt_topic = f'{self.__config.topic_prefix}/{observation.sensor.mqtt_topic_suffix}'
                value = observation.value_as_str()
                if self.log_level <= 10: print(f"DEBUG: Publishing message. topic: {mqtt_topic}, value: {value}")
                info = self.__mqtt_client.publish(mqtt_topic, value)
        except:
            if self.log_level <= 40: print("ERROR: MQTT publishing error")
            time.sleep(10)
            machine.reset()           

    def publish_observation(self, observation: Observation):
        self.publish_observations([observation])

    def publish_observations(self, observations: List[Observation]):
        try:
            for observation in observations:
                if observation.sensor.mqtt_topic_suffix:
                    self.__do_publish(observation)
        except:
            if self.log_level <= 40: print("ERROR: MQTT connection error")

    def publish_os_resetcause(self):
        try:
            mqtt_topic = f'{self.__config.topic_prefix}/{"esp_os_resetcause"}'
            MyResetCause = machine.reset_cause()
            resetstr = "Unknown cause "+str(MyResetCause)
            if ( MyResetCause == machine.PWRON_RESET ): resetstr = "PWRON_RESET"
            if ( MyResetCause == machine.HARD_RESET ): resetstr = "HARD_RESET"
            if ( MyResetCause == machine.WDT_RESET ): resetstr = "WDT_RESET"
            if ( MyResetCause == machine.DEEPSLEEP_RESET ): resetstr = "DEEPSLEEP_RESET"
            if ( MyResetCause == machine.SOFT_RESET ): resetstr = "SOFT_RESET"

            self.__mqtt_client.publish(mqtt_topic, resetstr)
            if self.log_level <= 10: print("INFO: OS reset cause: ", resetstr)
        except:
            if self.log_level <= 40: print("ERROR: MQTT publishing error resetcause")
            time.sleep(10)
            machine.reset()           

    def publish_os_mem_free(self):
        try:
            mqtt_topic = f'{self.__config.topic_prefix}/{"esp_mem_free"}'
            self.__mqtt_client.publish(mqtt_topic, str(gc.mem_free()))
            if self.log_level <= 10: print("INFO: Memory free:", str(gc.mem_free()))
        except:
            if self.log_level <= 40: print("ERROR: MQTT publishing error mem_free")
            time.sleep(10)
            machine.reset()           

