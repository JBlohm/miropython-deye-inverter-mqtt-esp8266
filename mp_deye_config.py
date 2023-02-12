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

import os

DEYE_LOGGER_IP_ADDRESS='192.168.2.156'
DEYE_LOGGER_PORT=8899
DEYE_LOGGER_SERIAL_NUMBER=4175806782

MQTT_HOST='your-mqtt-server'
MQTT_PORT=1883
MQTT_USERNAME='user'
MQTT_PASSWORD='password'
MQTT_TOPIC_PREFIX='deye'

WIFI_SSID = 'your-ssid'
WIFI_PASSWORD = 'your-password'

WDT_ENABLE=False

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

LOG_LEVEL=INFO
DEYE_DATA_READ_INTERVAL=60 # Do not exceed approx. 500sec, (300 = 5 Minutes is safe) else adapt MQTT keepalive im mp_deye_mqtt.py
DEYE_METRIC_GROUPS={'micro'}

class DeyeMqttConfig():
    def __init__(self, host: str, port: int, username: str, password: str, topic_prefix: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix

    @staticmethod
    def from_env():
        return DeyeMqttConfig(
            host=MQTT_HOST,
            port=int(MQTT_PORT),
            username=MQTT_USERNAME,
            password=MQTT_PASSWORD,
            topic_prefix=MQTT_TOPIC_PREFIX
        )


class DeyeLoggerConfig():
    """
    Logger is a device that connects the Solar Inverter with the internet.

    Logger is identified by a unique serial number. It is required when communicating
    with the device.
    """

    def __init__(self, serial_number: int, ip_address: str, port: int):
        self.serial_number = serial_number
        self.ip_address = ip_address
        self.port = port

    @staticmethod
    def from_env():
        return DeyeLoggerConfig(
            serial_number=int(DEYE_LOGGER_SERIAL_NUMBER),
            ip_address=DEYE_LOGGER_IP_ADDRESS,
            port=int(DEYE_LOGGER_PORT),
        )


class DeyeConfig():
    def __init__(self, logger_config: DeyeLoggerConfig, mqtt: DeyeMqttConfig,
                 log_level=INFO,
                 wifi_ssid='',
                 wifi_pwd='',
                 wdt_enable=False,
                 data_read_inverval=60,
                 metric_groups=[]):
        self.logger = logger_config
        self.mqtt = mqtt
        self.log_level = log_level
        self.wifi_ssid=WIFI_SSID
        self.wifi_pwd=WIFI_PASSWORD
        self.wdt_enable=WDT_ENABLE
        self.data_read_inverval = data_read_inverval
        self.metric_groups = metric_groups

    @staticmethod
    def from_env():
        return DeyeConfig(DeyeLoggerConfig.from_env(), DeyeMqttConfig.from_env(),
                          log_level=LOG_LEVEL,
                          data_read_inverval=int(DEYE_DATA_READ_INTERVAL),
                          metric_groups=DEYE_METRIC_GROUPS
                          )
