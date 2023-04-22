# Deye solar inverter MQTT bridge on ESP8266 D1-mini platform (with Micropython)

Reads Deye solar inverter metrics using Modbus over TCP and publishes them over MQTT.
This is the code version was ported by Joern Blohm for use with: MicroPython v1.19.1 on 2022-06-17; ESP module with ESP8266

Original code by Krzysztof Białek https://github.com/kbialek/deye-inverter-mqtt

Original code tested with:
* [Deye SUN-4K-G05](https://www.deyeinverter.com/product/three-phase-string-inverter/sun4-5-6-7-8-10kg03.html) and Logger S/N 23xxxxxxxx
* [Deye SUN1300G3](https://www.deyeinverter.com/product/microinverter-1/sun13002000g3eu230.html) and Logger S/N 41xxxxxxxx
* [Deye SUN600G3](https://www.deyeinverter.com/product/microinverter-1/sun600-800-1000g3eu230-single-phase-4-mppt-microinverter-rapid-shutdown.html) and Logger S/N 41xxxxxxxx

This Code tested with Deye SUN600G3-EU-230 Microinverter (Firmware: MW3_16U_5406_1.53)
and MQTT service (FHEM w. builtin MQTT Server)

## Supported metrics
The meaning of certain registers depends on the inverter type. 
For example, **string** inverters use registers 0x46 - 0x4e to report AC phase voltage/current.
On the other hand, **micro** inverters use this same registers to report pv1-pv4 cumulative energy.
Generally there are three types of inverters documented in the specification: **string**, **micro** and **hybrid**.
In the table below you can see, that the metrics are assigned to specific groups.
Empty value indicates a general purpose metric, that is available in all type of inverters.
You should specify the set of groups that is appropriate for your inverter in `DEYE_METRIC_GROUPS` environment variable,
otherwise only general purpose metrics will be reported over mqtt. Typically you should set it to either **string** or **micro**. 
Additional groups may be added in the future.

|Metric|Modbus address|MQTT topic suffix|Unit|Groups|
|---|:-:|---|:-:|---|
|Production today|0x3c|`day_energy`|kWh||
|Uptime|0x3e|`uptime`|minutes||
|Total Production (Active)|0x3F - 0x40|`total_energy`|kWh||
|Daily Production 1|0x41|`dc/pv1_day_energy`|kWh|micro|
|Daily Production 2|0x42|`dc/pv2_day_energy`|kWh|micro|
|Daily Production 3|0x43|`dc/pv3_day_energy`|kWh|micro|
|Daily Production 4|0x44|`dc/pv4_day_energy`|kWh|micro|
|Total Production 1|0x45 - 0x46|`dc/pv1_total_energy`|kWh|micro|
|Total Production 2|0x47 - 0x48|`dc/pv2_total_energy`|kWh|micro|
|Total Production 3|0x4a - 0x4b|`dc/pv3_total_energy`|kWh|micro|
|Total Production 4|0x4d - 0x4e|`dc/pv4_total_energy`|kWh|micro|
|AC Phase 1 voltage|0x49|`ac/l1_voltage`|V|string, micro|
|AC Phase 2 voltage|0x4a|`ac/l2_voltage`|V|string|
|AC Phase 3 voltage|0x4b|`ac/l3_voltage`|V|string|
|AC Phase 1 current|0x4c|`ac/l1_current`|A|string, micro|
|AC Phase 2 current|0x4d|`ac/l2_current`|A|string|
|AC Phase 3 current|0x4e|`ac/l3_current`|A|string|
|AC Phase 1 power|computed|`ac/l1_power`|W|string, micro|
|AC Phase 2 power|computed|`ac/l2_power`|W|string|
|AC Phase 3 power|computed|`ac/l3_power`|W|string|
|AC Frequency|0x4f|`ac_freq`|Hz||
|Operating power|0x50|`operating_power`|W|string, micro|
|DC total power|0x52|`dc_total_power`|W|string|
|DC total power|computed|`dc_total_power`|W|micro|
|AC apparent power|0x54|`ac_apparent_power`|W|string|
|AC active power|0x56 - 0x57|`ac_active_power`|W|string, micro|
|AC reactive power|0x58|`ac_reactive_power`|W|string|
|Radiator temperature|0x5a|`radiator_temp`|C|string, micro|
|IGBT temperature|0x5b|`igbt_temp`|C|string|
|DC PV1 voltage|0x6d|`dc/pv1_voltage`|V||
|DC PV1 current|0x6e|`dc/pv1_current`|A||
|DC PV1 power|computed|`dc/pv1_power`|W||
|DC PV2 voltage|0x6f|`dc/pv2_voltage`|V||
|DC PV2 current|0x70|`dc/pv2_current`|A||
|DC PV2 power|computed|`dc/pv2_power`|W||
|DC PV3 voltage|0x71|`dc/pv3_voltage`|V||
|DC PV3 current|0x72|`dc/pv3_current`|A||
|DC PV3 power|computed|`dc/pv3_power`|W||
|DC PV4 voltage|0x73|`dc/pv4_voltage`|V||
|DC PV4 current|0x74|`dc/pv4_current`|A||
|DC PV4 power|computed|`dc/pv4_power`|W||

## Installation
1. Adapt mp_deye_config.py to your needs
2. Copy all files except main.py to ESP8266 chip filesystem
3. Run mp_deye_daemon.py or mp_deye_cli.py in Thonny. Play with mp_deye_cli_deviceinfo.py. If that works, goto next step.
4. Copy the main.py file to the ESP8266 chip filesystem
5. Reboot ESP8266

## Configuration
All configuration options are controlled through environment variables.
WLAN is controlled directly within mp_deye_daemon.py and mp_deye_cli.py

* `LOG_LEVEL` - application log level, can be any of `DEBUG`, `INFO`, `WARN`, `ERROR`, `NOTSET`
* `DEYE_DATA_READ_INTERVAL` - interval between subsequent data reads, in seconds, defaults to 60
* `DEYE_METRIC_GROUPS` - a comma delimited set of:
    * `string` - set when connecting to a string inverter
    * `micro` - set when connecting to a micro inverter
* `DEYE_LOGGER_SERIAL_NUMBER` - inverter data logger serial number
* `DEYE_LOGGER_IP_ADDRESS` - inverter data logger IP address
* `DEYE_LOGGER_PORT` - inverter data logger communication port, typically 8899
* `MQTT_HOST`
* `MQTT_PORT`
* `MQTT_USERNAME`
* `MQTT_PASSWORD`
* `MQTT_TOPIC_PREFIX` - mqtt topic prefix used for all inverter metrics
* `WIFI_SSID`
* `WIFI_PASSWORD`
* `WDT_ENABLE` - False (default) 
    * `Enabeling` (True) might cause problems when answering times of the inverter are >=3 sec.

## Reading and writing raw register values
The tool allows reading and writing raw register values directly in the terminal.

**USE AT YOUR OWN RISK!** Be sure to know what you are doing. Writing invalid values may damage the inverter.
By using this tool you accept this risk and you take full responsiblity for the consequences.

* To read register value execute:
    ```
    edit mp_deye_cli.py as required. use 'r' in     args=['r', '86'] # Output active power 0x56=86(dec): unit: 0.1W
    Run in Thonny.
    ```
    where `<reg_address>` is register address (decimal)

* To write register value execute:
    ```
    edit mp_deye_cli.py as required. use 'w' in     args=['w', '<reg_addres>', '<reg_value>']
    Think before you act. Do not brick your inverter.
    Run in Thonny.
    ```
    where `<reg_address>` is register address (decimal), and <reg_value> is a value to set (decimal)

  

