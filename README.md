Solarmon
----
A simple Python Script for reading Growatt PV Inverter Modbus RS485 RTU Protocol and storing into InfluxDB

Protocol Documentation: http://www.growatt.pl/dokumenty/Inne/Growatt%20PV%20Inverter%20Modbus%20RS485%20RTU%20Protocol%20V3.04.pdf


How to use
----
- Some hardware running a Linux based OS with Python 3 (eg. Raspberry Pi)
- Connect your Linux based OS to the RS485 port on the inverter via a RS485 to USB cable
- [Install InfluxDB](https://www.influxdata.com/)
- Copy `solarmon.cfg.example` to `solarmon.cfg` and modify the config values to your setup as needed
- Run `pip install -r requirements.txt`
- Run `python solarmon.py` in a screen (or you could setup a service if that is your preference)
- [Install Grafana](https://grafana.com/)
- Go to http://localhost:3000/dashboard/import or equivalent for where you installed Grafana and import `grafana/dashboard.json`

![Inverter Grafana Dashboard](grafana/dashboard.png)
