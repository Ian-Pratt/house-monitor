import sys, datetime
f = sys.stdin
c = 0
LT = 0
l = f.readline()
while l:
    try:
        t = l.split()[0]
        T = datetime.datetime.fromisoformat(t)
        if LT and T - LT > datetime.timedelta(seconds=10):
            print(T.isoformat(timespec='seconds'), "gap ", T-LT)
        if LT and LT.day <11 and T.day >= 11:
            print(T.date().isoformat(), int(c/1000))
            c = 0
        c = c+1
        LT = T
    except:
        print('ERROR', l)
    l = f.readline()
