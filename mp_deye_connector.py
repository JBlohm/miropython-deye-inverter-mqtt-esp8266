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

import socket
import logging
import ubinascii

from mp_deye_config import DeyeConfig


class DeyeConnector:

    def __init__(self, config: DeyeConfig):
        self.__log = logging.getLogger(DeyeConnector.__name__)
        self.config = config.logger

    def send_request(self, req_frame):
        for res in socket.getaddrinfo(self.config.ip_address, self.config.port, socket.AF_INET, socket.SOCK_STREAM):
            family, socktype, proto, canonname, sockadress = res
            try:
                client_socket = socket.socket(family, socktype, proto)
                client_socket.settimeout(10)
                client_socket.connect(sockadress)
            except: #socket.error as msg:
                self.__log.warn("Could not open socket on IP %s", self.config.ip_address)
                return

            self.__log.warn("Request frame: %s", ubinascii.hexlify(req_frame))
            client_socket.sendall(req_frame)

            attempts = 10 # was 5
            while (attempts > 0):
                attempts = attempts - 1
                try:
                    data = client_socket.recv(1024)
                    try:
                        data
                    except:
                        self.__log.warn("No data received")
                    self.__log.warn("Response frame: %s", ubinascii.hexlify(data))
                    return data
                except:
                    self.__log.warn("Connection timeout/error (send_request)")

        return bytearray()
