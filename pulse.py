#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import datetime
import sys
import schedule
import threading

path="/var/opt/data/"

elec_pin =22
water_pin=23
led_pin = 16
GPIO.setmode(GPIO.BCM)
#GPIO.setup(led_pin, GPIO.OUT)
GPIO.setup(elec_pin, GPIO.IN)
GPIO.setup(water_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


global ecount
ecount = -1
global elast
start = elast = datetime.datetime.utcnow()
eperf = time.perf_counter_ns()

global wcount
wcount = -1 
global wlast
wlast = start

global efile
efile=None

global wfile
wfile=None


lock = threading.Lock()

def newfile ( res=0 ):
    global efile
    global ecount
    tmp = efile
    d=datetime.datetime.utcnow()
    lock.acquire()
    name = path + "elec-%s.log"%d.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='seconds')
    efile = open(name,"w+")
    ecount = res
    if tmp:
        tmp.close() 

    global wfile
    global wcount
    tmp = wfile
    name = path + "water-%s.log"%d.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='seconds')
    wfile = open(name,"w+")
    wcount = res
    if tmp:
        tmp.close()
    lock.release()

def countinc ( ignore ) :
    dd=time.perf_counter_ns()
    d=datetime.datetime.utcnow()
    lock.acquire()
    #.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='milliseconds')
    global ecount, elast, eperf
    ecount = ecount+1 
    if ecount == 0:
        elast=d
        eperf=dd
        lock.release()
        return
    #diff=(d-elast).total_seconds()
    diff=(dd-eperf)/1000000000.0
    watts=3600/diff
    print (d.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='milliseconds'),"%.3f"%diff,"%.0f"%watts, ecount, file=efile, flush=True)
    elast=d
    eperf=dd
    #print (GPIO.input(water_pin), end='')
    lock.release()

def water_edge ( ignore ) :
    d = datetime.datetime.utcnow()
    lock.acquire()
    global wcount
    global wstate
    global wlast

    if wcount == -1:
        wcount = 0
        wlast = d
        lock.release()
        return

    diff = (d-wlast).total_seconds()
    wlast = d
    time.sleep(0.02) 
    wstate=GPIO.input(water_pin)
    if wstate == 0:
        wcount = wcount + 9
        wrate = 9 * 3600.0 / diff
    else:
        wcount = wcount + 1
        wrate = 1 * 3600.0 / diff

    print (d.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='milliseconds'), "start%d %d %5.0f %3.1f %d" % (wstate, GPIO.input(water_pin), diff, wrate, wcount), file=wfile, flush=True )
    lock.release()


"""
while True:
	x=0
	xx=time.perf_counter_ns()
	while GPIO.input(elec_pin) == 1:
		x=x+1
	xxx=time.perf_counter_ns()
	countinc(elec_pin)
	y=0
	while GPIO.input(elec_pin) == 0:
		y=y+1
		pass
	print("XXXXXXX", x, (xxx-xx)/1000000, y)	
"""

newfile(-1)

GPIO.add_event_detect(elec_pin, GPIO.FALLING, callback=countinc)

wstate = GPIO.input(water_pin)
GPIO.add_event_detect(water_pin, GPIO.BOTH, callback=water_edge, bouncetime=20)
#GPIO.add_event_detect(water_pin, GPIO.RISING, callback=water_rising)

#schedule.every().minute.at(":17").do(newfile)
schedule.every().day.at("00:00").do(newfile)

while True:
    time.sleep(1)
    schedule.run_pending()



"""
while True: 
    to = (start + datetime.timedelta(minutes = i)).replace(second=0)
    time.sleep((to-start).seconds)
    newfile()
    #print("%0.3f"%(time.perf_counter_ns()/1000000000.0))
    i=i+1

actual = 0
err = 0
pulseInterval = 0.01
while True :
    
    actual = actual + 1
    GPIO.output(led_pin, 1)
    time.sleep(pulseInterval)
    #print ( actual, countx )
    if countx != actual:
        err = err + 1
        #print ( actual, countx, err )
        #countx = actual
    GPIO.output(led_pin, 0)
    time.sleep(pulseInterval)
    if actual % 1000 == 0 :
        print(actual, countx, err )
"""




