#!/bin/bash

logger house_monitor

cd /var/opt/data

/usr/bin/python3 /home/ian/pulse.py &>> pulse.out || logger pulse fail &

logger next

/home/ian/go/src/github.com/nDenerserve/SmartPi/bin/smartpireadout &>> smartpi.out || logger smart fail &

logger discord

/usr/bin/python3 /home/ian/discord/send.py &>> discord.out || logger discord fail &




