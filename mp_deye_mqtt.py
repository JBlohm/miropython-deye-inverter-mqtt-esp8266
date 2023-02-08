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

import logging

from umqtt.simple import MQTTClient
import machine
import ubinascii

from mp_deye_config import DeyeConfig
from mp_deye_observation import Observation

class DeyeMqttClient():

    def __init__(self, config: DeyeConfig):
        self.__log = logging.getLogger(DeyeMqttClient.__name__)
        # umqtt.simple.MQTTClient(client_id, server, port=0, user=None, password=None, keepalive=0, ssl=False, ssl_params={})
        self.__mqtt_client = MQTTClient(ubinascii.hexlify(machine.unique_id()), config.mqtt.host, config.mqtt.port, config.mqtt.username, config.mqtt.password, keepalive=120)
        self.__mqtt_client.connect()
        self.__config = config.mqtt

    def __do_publish(self, observation: Observation):
        try:
            if observation.sensor.mqtt_topic_suffix:
                mqtt_topic = f'{self.__config.topic_prefix}/{observation.sensor.mqtt_topic_suffix}'
                value = observation.value_as_str()
                self.__log.debug("Publishing message. topic: '%s', value: '%s'", mqtt_topic, value)
                info = self.__mqtt_client.publish(mqtt_topic, value)
        except:
            self.__log.error("MQTT publishing error (__do_publish)")

    def publish_observation(self, observation: Observation):
        self.publish_observations([observation])

    def publish_observations(self, observations: List[Observation]):
        try:
            for observation in observations:
                if observation.sensor.mqtt_topic_suffix:
                    self.__do_publish(observation)
        except:
            self.__log.error("MQTT connection error")