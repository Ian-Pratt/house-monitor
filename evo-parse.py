import json
import sys

# sudo nohup stdbuf -oL rtl_433/build/src/rtl_433 -f 868M -R 185 -M level -F json -d0 | stdbuf -oL tee evo6.log | python3 -u ./evo-parse.py &> evo-parse6.log

csv = 1

if csv:
    f = open("foo.csv","w")

controllers = {
    'CTL:024309' : 0,  # ground floor
    'CTL:024310' : 1   # first floor
}

manifolds = { # number ofter {} is the zone listed in 3150 heat demand commands
    'UFH:010822' : 'F0_STR_UFH', # { Living, Dining, Garden, Kitchen, Utility } 0
    'UFH:009719' : 'F0_STR_RAD', # { Hall, Study, Dining } 6 
    'UFH:009749' : 'F0_WC1_UFH', # { Hall, Study, Playroom, WC1 } 5
    'UFH:009725' : 'F0_WC1_RAD', # { WC1_Cloak, WC2_Lobby, Playroom, Utility } 14
    'UFH:009723' : 'F1_BD3_RA1', # RM4 tested BED3. { believed to be in no order BED3, BED3_ENS, Landing, Elodie } 12
    'UFH:010819' : 'F1_BD3_RA2', # RM5 { believed to be in no order Studio, Art_Room } 4
    'UFH:010829' : 'F1_MBW_RAD', # tested BED1-Wardrobe. { believed to be in no order: MB1, MB1_Wrd, MB1_ENS, Bed2, Spa} 0
    'UFH:009722' : 'F2_CBD_RAD', # { Bedroom6, Bedroom7, 2F_Landing } 10
} 


demand = { k : -1 for k in manifolds }
rdemand = { k : -1 for k in manifolds }

controller_mappings = {
    0 : { # ground floor controller
        0 : 'Living_UFH',
        1 : 'Dining_UFH',
        2 : 'Dining_Rad',
        3 : 'Garden_UFH',
        4 : 'Kitchen_UFH',
        5 : 'Hall_UFH',
        6 : 'Hall_Rad',
        7 : 'Study_UFH',
        8 : 'Study_Rad',
        9 : 'Playroom_UFH',
        10: 'Playroom_Rad',
        11: 'Utility_UFH',
        12: 'Utility_Rad',
        13: 'WC1_Cloak_UFH',
        14: 'WC1_Cloak_Rad',
        15: 'WC2_Lobby'
    },
    1 : { # first floor controller
        0 : 'Master_Bed',
        1 : 'Master_Ens',
        2 : 'Master_Wrd',
        3 : 'Spa_Bathroom',
        4 : 'Studio',
        5 : 'Leon_Bed',
        6 : 'Bedroom3',
        7 : 'Bedroom3_Ens',
        8 : 'Elodie_Bed',
        9 : 'Art_Room',
        10: 'Bedroom6',
        11: 'Bedroom7',
        12: 'Landing',
        13: 'Back_Stairs',
        14: '2F_Landing'
        # Master_Ens_EUF
        # Spa Bathroom EUF
        # Bedroom3 Ens EUF
        # 1F Bathroom2 EUF
        # 2F Bathroom EUF
    }
}

rooms = {
    'Thm:107090': 'Living',       # 0da252  Also cmd 2389
    'Thm:246835': 'Study',        # 0fc433
    'Thm:180099': 'Kitchen',      # 0ebf83
    'Thm:258025': 'Garden',       # 0fefe9  Also cmd 2389
    'Thm:144228': 'Hall',         # 0e3364
    'Thm:259179': 'Playroom',     # 0ff46b
    'Thm:259157': 'Dining',       # 0ff455
    'Thm:180126': 'WC1_Cloak',    # 0ebf9e
    'Thm:180151': 'WC2_Lobby',    # 0ebfb7
    'Thm:180155': 'Utility',      # 0ebfbb
    'Thm:246845': 'Master_Bed',   # 0fc43d
    'Thm:258478': 'Master_Ens',   # 0ff1ae
    'Thm:241764': 'Master_Wrd',   # 0fb064
    'Thm:246888': 'Leon_Bed',     # 0fc468
    'Thm:180166': 'Spa_Bathroom', # 0ebfc6
    'Thm:180132': 'Bedroom3',     # 0ebfa4
    'Thm:259066': 'Bedroom3_Ens', # 0ff3fa
    'Thm:245874': 'Elodie_Bed',   # 0fc072
    'Thm:180098': 'Studio',       # 0ebf82
    'Thm:180131': 'Art_Room',     # 0ebfa3
    'Thm:180165': 'Landing',      # 0ebfc5
    'Thm:144239': 'Back_Stairs',  # 0e336f
    'Thm:259184': 'Bedroom6',     # 0ff470
    'Thm:259183': 'Bedroom7',     # 0ff46f
    'Thm:144222': '2F_Landing'    # 0e335e
}


"""
{ # 2F Rad manifold
    'Bedroom6'   : 1,
    'Bedroom7'   : 2,
    'Floor2_Lnd' : 3
}

"""

devid_map = {
        1:"CTL",  # Controller
        2:"UFH",  # Underfloor heating (HCC80, HCE80)
        3:"Thm",  # HCW82
        4:"TRV",  # Thermostatic radiator valve (HR80, HR91, HR92)
        7:"DHW",  # DHW sensor (CS92)
        10:"OTB", # OpenTherm bridge (R8810)
        12:"THm", # Thermostat with setpoint schedule control (DTS92E, CME921)
        13:"BDR", # Wireless relay box (BDR91) (HC60NG too?)
        17:"-17", # Dunno - Outside weather sensor?
        18:"HGI", # Honeywell Gateway Interface (HGI80, HGS80)
        22:"THM", # Thermostat with setpoint schedule control (DTS92E)
        30:"GWY", # Gateway (e.g. RFG100?)
        32:"VNT", # (HCE80) Ventilation (Nuaire VMS-23HB33, VMN-23LMH23)
        34:"STA", # Thermostat (T87RF)
        63:"NUL"  # No device
}

def hex_to_id (i):
    if not ":" in i:
        j = int(i,16)
        d = j >> 18
        m = j & 0x3ffff
        if d in devid_map:
            D = devid_map[d]
        else:
            D = " {:>2}".format(d)
            D = D.replace(" ","-")
        return "%3s:%06d" % (D,m)
    return i               

def id_to_hex (h):
    (t,a) = h.split(':')
    for T in devid_map:
        if devid_map[T] == t:
            break
    return '{:06x}'.format(T<<18 | int(a)) 
    


for id in rooms:
    print ("    '{}': '{}', \t # {}".format( id, rooms[id], id_to_hex(id) ))
 

colour = 1
CEND    = '\33[0m' if colour else ""
CBOLD   = '\33[1m' if colour else ""
CRED    = '\33[91m' if colour else ""
CGREEN  = '\33[92m' if colour else ""

temps = {}
setpoints = {}
setpoints_rad = { "Dining" : -1.0, "Study" : -1.0, "Hall" : -1.0, "Playroom" : -1.0, "Utility" : -1.0, "WC1_Cloak" : -1.0 }  # initialization hack
for i in rooms:
    temps[rooms[i]] = -1.0
    setpoints[rooms[i]] = -1.0


# {"time" : "2023-12-29 21:17:57", "model" : "AmbientWeather-WH31E", "id" : 118, "channel" : 1, "battery_ok" : 1, "temperature_C" : 19.100, "humidity" : 64, "data" : "0800000000", "mic" : "CRC", "mod" : "FSK", "freq1" : 868.254, "freq2" : 868.380, "rssi" : -3.131, "snr" : 29.471, "noise" : -32.602}

otemps = { "Outside" : -99, "Humidor" : -99, "Cellar" : -99 }
ohumidity = { "Outside" : -99, "Humidor" : -99, "Cellar" : -99 } 
obat = { "Outside" : "", "Humidor" : "", "Cellar" : "" } 

orooms = { 1 : "Outside", 2 : "Unknown2", 3 : "Unknown3", 4 : "Unknown4", 5 : "Unknown5", 6 : "Unknown6", 7 : "Cellar", 8 : "Humidor", }

if csv:
    print("time, ", end='', file=f)
    for r in temps:
        print("%s_t, %s_s, " % (r, r), end='', file=f)
        if r in setpoints_rad:
            print("%s_r, " % (r), end='', file=f)
    for r in otemps:
        print("%s_t, %s_h, %s_b, " % (r, r, r), end='', file=f)

    for k,v in manifolds.items():
        print("%s_d, %s_p, " % (v, v), end='', file=f)
    print('', file=f)

for line in sys.stdin:
    if line[0] != '{':
        continue
    dict = json.loads(line)
    #print ( dict )
    time = dict['time']

    model = dict['model']

    if model == "AmbientWeather-WH31E":
        otemps[orooms[dict['channel']]] = dict['temperature_C']
        ohumidity[orooms[dict['channel']]] = dict['humidity']
        obat[orooms[dict['channel']]] = "!" if dict['battery_ok'] == 0 else ""

    elif model == "Honeywell-CM921": 
        cmd = dict['Command']
        sum = int(dict['csum'],16)


        if cmd == "1100" or cmd == "1030": # very rare commands that we don't understand and only have one id
            continue

        ids = dict['ids']
        (id0,id1) = ids.split()
        id0 = hex_to_id(id0)
        id1 = hex_to_id(id1)
        ids = id0+" "+id1

        if sum != 0: # skip packets with the weird sum=1 or otherwise not 0
            print( time, "CMD", sum, ids, cmd, dict['Payload'])
            continue

        if cmd == "30c9":
            if id0[0:4]=='CTL:':
                #print(dict)
                ctl = controllers[id0]
                for i in range(0,16):
                    if ('temperature (zone %d)' % i) in dict:
                        temp = dict['temperature (zone %d)' % i]
                        circ = controller_mappings[ctl][i]
                        room = circ.removesuffix('_Rad')
                        room = room.removesuffix('_UFH')
                        room = room.removesuffix('_EUF')
                        #print(room, circ, ctl, i)
                        #print("%15s %15s %.1f %.1f" % (circ, room, temp, temps[room]) )
                        if temps[room] != temp:
                            print("%15s %.1f %.1f UPDATE" % (room, temp, temps[room]) )
                        temps[room] = temp   # update in case controller has seen a report we haven't

            elif id0[0:4]=='Thm:':
                temp = dict["temperature (zone 1)"]
                room = rooms[id0]
                #print('%15s %.1f' % (room, temp))

                temps[room] = temp

                #if id0 in rooms:
                #    print(rooms[id0])

        elif cmd == "2309":
            ctl = controllers[id0]
            circ_setpoints = {}
            for i in range(0,16):
                if ('setpoint (zone %d)' % i) in dict:
                    sp = dict['setpoint (zone %d)' % i]
                    circ = controller_mappings[ctl][i]
                    circ_setpoints[circ] = sp

            r_setpoints = {}
            for c in circ_setpoints: # code assumes same controller
                room = c.removesuffix('_Rad')
                room = room.removesuffix('_UFH')
                room = room.removesuffix('_EUF')
                if (not room in r_setpoints) or (circ_setpoints[c] > r_setpoints[room]):
                    r_setpoints[room] = circ_setpoints[c]
                if c[-4:] == "_Rad":
                    setpoints_rad[c[:-4]] = circ_setpoints[c]

            for r in r_setpoints:
                setpoints[r] = r_setpoints[r]
                #print("SETPOINT",r, setpoints[r])

        elif cmd == "0008":
            dom = dict['domain_id']
            if dom == 252: # boiler demand
                d = int(dict['demand'])
                demand[id0] = d
            else:
                print("WEIRD",dom)
        elif cmd == "3150":
            rdemand[id0] = dict['heat_demand']
        else:
            print( time, "CMD", sum, ids, cmd, dict['Payload'])
            continue
    else:
        print("MODEL NOT KNOWN")

    if csv:
        print(f'{time}, ', end='', file=f)
        for r in temps:
            print(f'{temps[r]:.1f}, {setpoints[r]:.1f}, ', end='', file=f)
            if r in setpoints_rad:
                print(f'{setpoints_rad[r]:.1f}, ', end='', file=f)
        for r in otemps:
            print(f'{otemps[r]:.1f}, {ohumidity[r]:02d}, {obat[r]}, ', end='', file=f) 
        for k,v in manifolds.items():
            print(f'{demand[k]}, {(rdemand[k]/2):1.0f}, ',end='', file=f)
        print('', file=f)

    if 1: 
        print(time, "STATUS")
        for r in temps:
            print("%15s %s%.1f%s %.1f" % (r, CRED if temps[r] < setpoints[r] else "", temps[r], CEND, setpoints[r]),end='' )
            if r in setpoints_rad:
                print(" %.1f" % (setpoints_rad[r]),end='')
            print()

        for r in otemps:
            print("%15s %.1f %02d%% %s" % (r,otemps[r],ohumidity[r],obat[r]) )
    
        #for m in sorted(demand):
        #    print(m,demand[m],"  ",end='')
        for k,v in manifolds.items():
            #print(v,demand[k],rdemand[k],"  ",end='')
            print(f'{v:>15} {demand[k]} {(rdemand[k]/2):1.0f}%')
        print()

#print(rooms)





 
