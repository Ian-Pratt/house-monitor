#!/usr/bin/python3

import socket
import random
import http.client
import datetime
#import ephem
import time
import pdpyras
import schedule

alarm_delay = 10

UDP_IP = "0.0.0.0"
BRIDGE_IP = '192.168.1.34'
PORT = 9761
URL = 'http://' + BRIDGE_IP +'/rako.xml'

routing_key = 'R03DGSERQAG8S08Y18MMNQ8WSP33ND5H'

path = "/var/opt/data/"

global xrooms

def get_room_names():
    import xmltodict
    import urllib.request

    xml = ""
    weburl=urllib.request.urlopen(URL)
    if(weburl.getcode() == 200):
        xml=weburl.read()

    dict=xmltodict.parse(xml)

    xrooms={}
    lstRoom_num = []
    for room in dict['rako']['rooms']['Room'] :
        if room['@id'] == '0':
            continue
        room_name = room["Title"].replace(" ", "_")

        #print(room)

        print(room['@id'],room_name)

        lstRoom_num.append(int(room['@id']))

        xrooms[int(room['@id'])]=room_name
    return xrooms

global log_file 
log_file = 0

def new_file():
    global log_file
    tmp = log_file
    d=datetime.datetime.utcnow()
    name = path + "rako-%s.log"%d.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='seconds')
    log_file = open(name,"w+")
    if tmp:
        tmp.close()     

def listening():
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    soc.bind((UDP_IP, PORT))
    soc.settimeout(1.0)

    #obs = ephem.Observer()
    #obs.lat = "52.2053"
    #obs.long="0.1218"
    #obs.date= ('2022/1/1 18:00')
    #print( obs.previous_rising(ephem.Sun()).datetime(), obs.next_setting(ephem.Sun()).datetime() 
               
    global log_file 
        
    holdoff=0
    event_key = ''
    log_session = pdpyras.ChangeEventsAPISession(routing_key)
    event_session = pdpyras.EventsAPISession(routing_key)
    resp = ''
        
        
    while True:    
        try:
            data, addr = soc.recvfrom(1024)
        except socket.timeout:
            if holdoff and t > holdoff:
                print(T,"send_pagerduty_trigger")
                event_key = event_session.trigger("Alarm is Sounding!", 'Elmhurst')
                holdoff = 0
            schedule.run_pending()
            continue

        try: 
            #print("recieved message:", addr, len(data), data.hex())
            if addr[0] != BRIDGE_IP:
                continue
            t=datetime.datetime.utcnow()
            T=t.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='seconds')

            if len(data) >=9 and data[0] == 0x53: # status report
                room = data[2] * 256 + data[3]
                channel = data[4]
                command= data[5]
                val = data[7]
                if command == 0x31: # set scene
                    crc = 0
                    for b in data[2:]:
                        crc += b
                    if crc == 256:
                        try:
                            roomname = xrooms[room]
                        except:
                            roomname = "__"
                        entry = "%s set_scene room=%d %s channel=%d command=%d value=%d" % (T, room, roomname,channel,command,val )
                        print(entry)
                        log_file.write( entry + "\n")

                        if room == 52:  # alarm is room 52
                            if val == 4:   # scene 4 is Alarm is Set
                                print(T, "alarm_set")
                                log_file.write( "%s alarm_set\n" % T ) 
                                resp = log_session.submit("Alarm set", 'Elmhurst')

                            elif val == 0:    # Alarm is unset
                                if event_key:
                                    event_session.resolve(event_key)
                                    print(T, "resolve", event_key)
                                    log_file.write( "%s alarm_resolve\n" % T )
                                    event_key = ''
                                    
                                print(T, "alarm_unset")
                                log_file.write( "%s alarm_unset\n" % T )
                                resp = log_session.submit("Alarm unset", 'Elmhurst')
                                holdoff = 0

                            elif val == 1:    # Alarm sounding
                                print(T, "alarm_sounding")
                                log_file.write( "%s alarm_sounding\n" % T )
                                holdoff = t + datetime.timedelta(seconds=alarm_delay)
                            else:
                                print(T,"alarm_unknown")
                                log_file.write( "%s alarm_unknown\n" % T )

                    else:
                        print(T,"CRC_fail", data)
                else:
                    print(T,"not_set_scene", command, len(data), data.hex())

            else:
                print(T,"not_status_update", len(data), data.hex())
    
        except Exception as e:  
            print(e) 
            
        # bottom of main while loop

new_file()
schedule.every().day.at("00:00").do(new_file)
#schedule.every().minute.at(':00').do(new_file)
        
while True:                
    try:
        xrooms=get_room_names()
        listening()  # just restart the listening loop if there are random failures
    except Exception as e:
        print(e)
        t=datetime.datetime.utcnow()
        T=t.replace(tzinfo=datetime.timezone.utc).astimezone().isoformat(timespec='seconds')
        print(T,"exception_restart")
        time.sleep(10)

def set_scene( room, channel, scene):

    data = bytearray.fromhex('000000000000000000')

    data[0] = 0x52
    data[1] = 7
    data[2] = room >> 8
    data[3] = room & 0xff
    data[4] = channel
    data[5] = 0x31
    data[6] = 0x1
    data[7] = scene

    sum = 0
    for x in data[1:]:
        sum += x

    data[8] = 0x100 - (sum & 0xff)

    print(data)
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    soc.connect((BRIDGE_IP, PORT))
    soc.send(data)
    soc.close()


#set_scene( 23, 0, 1)

