#!/bin/bash

logger house_monitor

source /home/ian/house-monitor/config

cd /var/opt/data

/usr/bin/python3 /home/ian/house-monitor/pulse.py &>> pulse.out || logger pulse fail &

logger next

/home/ian/go/src/github.com/nDenerserve/SmartPi/bin/smartpireadout &>> smartpi.out || logger smart fail &


logger rako_holiday
PYTHONUNBUFFERED=1 /usr/bin/python3 /home/ian/house-monitor/rako_holiday.py &>> rako_holiday.out || logger rako fail &


#logger discord
#/usr/bin/python3 /home/ian/discord/send.py >> discord.out 2>> discord.err || logger discord fail &


logger attention_button_server
PYTHONUNBUFFERED=1 /usr/bin/python3 /home/ian/house-monitor/attention_button_server.py &>> attention_button.out || logger attention_button_server fail &



