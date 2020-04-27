#!/bin/sh

logger house_monitor

cd /var/opt/data

nohup /usr/bin/python3 /home/ian/pulse.py || logger pulse fail &

logger next

nohup /home/ian/go/src/github.com/nDenerserve/SmartPi/bin/smartpireadout > 3phase-`date --iso-8601=seconds`.log || logger smart fail &



