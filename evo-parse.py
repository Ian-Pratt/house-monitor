import json
import sys

# sudo nohup stdbuf -oL rtl_433/build/src/rtl_433 -f 868M -R 185 -M level -F json -d0 | stdbuf -oL tee evo6.log | python3 -u ./evo-parse.py &> evo-parse6.log


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
    'Thm:107090': 'Living',  # also get cmd 2389 from this amd garden
    'Thm:246835': 'Study', 
    'Thm:180099': 'Kitchen', 
    'Thm:258025': 'Garden',
    'Thm:144228': 'Hall',
    'Thm:259179': 'Playroom', 
    'Thm:259157': 'Dining', 
    'Thm:180126': 'WC1_Cloak', 
    'Thm:180151': 'WC2_Lobby',
    'Thm:180155': 'Utility',  
    'Thm:246845': 'Master_Bed',
    'Thm:258478': 'Master_Ens', 
    'Thm:241764': 'Master_Wrd', 
    'Thm:246888': 'Leon_Bed', 
    'Thm:180166': 'Spa_Bathroom', 
    'Thm:180132': 'Bedroom3', 
    'Thm:259066': 'Bedroom3_Ens', 
    'Thm:245874': 'Elodie_Bed', 
    'Thm:180098': 'Studio', 
    'Thm:180131': 'Art_Room', 
    'Thm:180165': 'Landing', 
    'Thm:144239': 'Back_Stairs', 
    'Thm:259184': 'Bedroom6', 
    'Thm:259183': 'Bedroom7', 
    'Thm:144222': '2F_Landing'
}

"""
{ # 2F Rad manifold
    'Bedroom6'   : 1,
    'Bedroom7'   : 2,
    'Floor2_Lnd' : 3
}

"""

temps = {}
setpoints = {}
setpoints_rad = {}
for i in rooms:
    temps[rooms[i]] = -1.0
    setpoints[rooms[i]] = -1.0

for line in sys.stdin:
    if line[0] != '{':
        continue
    dict = json.loads(line)
    #print ( dict )
    time = dict['time']
    cmd = dict['Command']

    #if cmd == "1060": # due to bug no ids
    #    continue

    ids = dict['ids']
    (id0,id1) = ids.split()

    if cmd == "30c9":
        if id0[0:4]=='CTL:':
            #print(dict)
            ctl = controllers[id0]
            for i in range(0,16):
                if ('temp (zone %d)' % i) in dict:
                    temp = dict['temp (zone %d)' % i]
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
            temp = dict["temp (zone 1)"]
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
        print( time, "CMD", ids, cmd, dict['Payload'])
        continue

    print(time, "STATUS")
    for r in temps:
        print("%15s %.1f %.1f" % (r, temps[r], setpoints[r]),end='' )
        if r in setpoints_rad:
            print(" %.1f" % (setpoints_rad[r]),end='')
        print()
    
    #for m in sorted(demand):
    #    print(m,demand[m],"  ",end='')
    for k,v in manifolds.items():
        #print(v,demand[k],rdemand[k],"  ",end='')
        print(f'{v:>15} {demand[k]} {(rdemand[k]/2):1.0f}%')
    print()

print(rooms)





 
