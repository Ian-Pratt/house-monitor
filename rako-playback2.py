
#!/usr/bin/env python3
import argparse, os, re, sys, socket, time as time_mod
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import Optional

FNAME_PREFIX = "rako-"
FNAME_SUFFIX = ".log"
BRIDGE_IP = "192.168.1.34"
PORT = 9761

def set_scene(e):
    room = e['room']
    channel = e['channel']
    scene = e['scene']    
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


@dataclass
class Event:
    tod: time
    command: int
    room: int
    room_name: str
    channel: int
    scene: int
    rawline: str
    file: str
    lineno: int

def parse_iso_from_filename(name: str) -> Optional[datetime]:
    if not (name.startswith(FNAME_PREFIX) and name.endswith(FNAME_SUFFIX)):
        return None
    iso = name[len(FNAME_PREFIX):-len(FNAME_SUFFIX)]
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00'))
    except ValueError:
        return None

def group_files_by_month(base_dir: str):
    by_month = {}
    for fn in os.listdir(base_dir):
        if not (fn.startswith(FNAME_PREFIX) and fn.endswith(FNAME_SUFFIX)):
            continue
        dt = parse_iso_from_filename(fn)
        if dt is None: 
            continue
        by_month.setdefault(dt.month, []).append((dt, fn))
    for m in list(by_month.keys()):
        by_month[m].sort(key=lambda t: t[0])
    return by_month

def circular_distance(a: int, b: int) -> int:
    """Circular distance on 1..12 months."""
    # Map to 0..11 for simplicity
    a0, b0 = (a-1) % 12, (b-1) % 12
    diff = abs(a0 - b0)
    return min(diff, 12 - diff)

def forward_steps(from_m: int, to_m: int) -> int:
    """Steps moving forward (increasing months, wrapping) from from_m to to_m."""
    return (to_m - from_m) % 12

def pick_month(by_month, now: datetime):
    if not by_month:
        return None
    cur = now.month
    months = sorted(by_month.keys())
    best = None
    best_key = None
    for m in months:
        dist = circular_distance(m, cur)
        fwd = forward_steps(cur, m)
        # Prefer minimal circular distance, then fewer forward steps (i.e., prefer future),
        # then higher month number just for determinism.
        key = (dist, fwd, -m)
        if best_key is None or key < best_key:
            best_key = key
            best = m
    return best

def parse_events_from_files(base_dir: str, files_sorted):
    events = []
    action_re = re.compile(r'^set[_\-]scene$')
    for _, fn in files_sorted:
        count = 0
        fpath = os.path.join(base_dir, fn)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
            for lineno, line in enumerate(fh, start=1):
                #print(line)
                line = line.strip()
                if not line: continue
                parts = line.split()
                if len(parts) < 4: continue
                if not action_re.fullmatch(parts[1]): continue
                if not re.fullmatch(r'[RS][\+-]\d+', parts[2]): continue
                if parts[3] != 'I': continue
                room_name = parts[6]
                kv = {}
                for p in parts:
                    if '=' in p:
                        k, v = p.split('=', 1)
                        kv[k] = v
                try:
                    if int(kv.get('command', -1)) != 49: continue
                    room = int(kv['room'], 10)
                    channel = int(kv['channel'], 10)
                    scene = int(kv['scene'], 10)
                except Exception:
                    continue
                ts = parts[0]
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                except ValueError:
                    dt = datetime.strptime(ts[:19], '%Y-%m-%dT%H:%M:%S')
                count = count + 1
                events.append(dict(
                    tod=dt.time().replace(microsecond=0),
                    command=49, room=room, room_name=room_name, channel=channel, scene=scene,
                    rawline=line, file=fpath, lineno=lineno
                ))
                #print("+++")
        print(f"{fn} read {count} events")
    #events.sort(key=lambda e: (e["tod"].hour, e["tod"].minute, e["tod"].second))

    #print(events)

    return events

def build_schedule(events, now: datetime):
    today = now.date()
    schedule = []
    for e in events:
        target_date = today if e["tod"] >= now.time() else (today + timedelta(days=1))
        dt = datetime.combine(target_date, e["tod"])
        schedule.append((dt, e))
    #schedule.sort(key=lambda t: t[0])
    return schedule

def main():
    ap = argparse.ArgumentParser(description="Rako Scene Scheduler (file-based month selection, circular distance)")
    ap.add_argument("base_dir", nargs="?", default=os.getcwd(), help="Directory containing rako-<ISO>.log files (default: CWD)")
    ap.add_argument("--warp", help="Pretend 'now' is this ISO datetime (e.g., 2025-10-18T21:30:00)")
    ap.add_argument("--simulate", type=int, metavar="N", help="Don't sleep; just print the next N scheduled firings and exit")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.warp:
        try:
            now = datetime.fromisoformat(args.warp.replace('Z', '+00:00'))
        except ValueError:
            print(f"--warp must be ISO datetime like 2025-10-18T21:30:00 ; got {args.warp}", file=sys.stderr); sys.exit(2)
    else:
        now = datetime.now()

    base_dir = os.path.abspath(args.base_dir)
    if not os.path.isdir(base_dir):
        print(f"Base directory not found: {base_dir}", file=sys.stderr); sys.exit(1)

    if args.simulate:
        N = args.simulate if args.simulate > 0 else len(schedule)

    count = 1
    while not args.simulate or count < N :
        by_month = group_files_by_month(base_dir)
        m = pick_month(by_month, now)
        if m is None:
            print(f"No matching rako-*.log files found in {base_dir}", file=sys.stderr); sys.exit(1)

        files_sorted = by_month[m]
        print(f"Selected month {m} (current month {now.month})")
        #for _, fn in files_sorted:
        #    print(f"  - {fn}")

        events = parse_events_from_files(base_dir, files_sorted)
        if not events:
            print("No qualifying events found in selected files.", file=sys.stderr)
            break

        schedule = build_schedule(events, now)
      
        for dt, e in schedule:
            if args.simulate:
                print(f"SIMU {count:4}-> will fire at {dt.isoformat()} : cmd={e['command']} room={e['room']:2} name={e['room_name']:14} channel={e['channel']} scene={e['scene']} f={os.path.basename(e['file'])}:{e['lineno']}")
            else:
                print(f"WAIT {dt.isoformat()} : cmd={e['command']} room={e['room']:2} name={e['room_name']:14} channel={e['channel']} scene={e['scene']} f={os.path.basename(e['file'])}:{e['lineno']}")

                now = datetime.now()
                while now < dt:
                    #print(min(10, (dt - now).total_seconds()))
                    time_mod.sleep(min(10, (dt - now).total_seconds()))
                    print(".",end="")
                    now = datetime.now()
                
                print(f"\nSEND {dt.isoformat()} : cmd={e['command']} room={e['room']:2} name={e['room_name']:14} channel={e['channel']} scene={e['scene']} f={os.path.basename(e['file'])}:{e['lineno']}")

                set_scene(e)

            count = count + 1
            if args.simulate and count > N:
                break


if __name__ == "__main__":
    main()
