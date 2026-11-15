"""Read high-resolution signal controller event logs.

Events use the Indiana enumerations (Sturdevant et al., 2012), the format
written by ATSPM-capable controllers.  The codes used here:

     1  phase begin green          43  phase call registered
     8  phase begin yellow         44  phase call dropped
    10  phase begin red clearance
    11  phase end red clearance
"""
import csv
from datetime import datetime

GREEN, YELLOW, RED_CLEARANCE, END, CALL_ON, CALL_OFF = 1, 8, 10, 11, 43, 44


def read(file):
    """Events from a CSV with columns timestamp,code,param.

    Returns [(seconds since the first event, code, param)] in time order.
    """
    rows = [(datetime.fromisoformat(r["timestamp"]), int(r["code"]), int(r["param"]))
            for r in csv.DictReader(file)]
    rows.sort()
    start = rows[0][0]
    return [(round((t - start).total_seconds(), 3), code, param) for t, code, param in rows]


def intervals(events):
    """Yield (phase, kind, start, duration) for every completed interval.

    kind is green, yellow or red_clearance, or wait: the time from a call
    registered while the phase is not green until the phase turns green,
    if the call stays on that long.
    """
    opened = {}       # (phase, kind) -> start time
    follows = {YELLOW: ("green", "yellow"), RED_CLEARANCE: ("yellow", "red_clearance"),
               END: ("red_clearance", None)}
    green = set()
    for t, code, phase in events:
        if code == GREEN:
            green.add(phase)
            opened[phase, "green"] = t
            if (phase, "wait") in opened:
                start = opened.pop((phase, "wait"))
                yield phase, "wait", start, round(t - start, 3)
        elif code in follows:
            ends, begins = follows[code]
            green.discard(phase)
            if (phase, ends) in opened:
                start = opened.pop((phase, ends))
                yield phase, ends, start, round(t - start, 3)
            if begins:
                opened[phase, begins] = t
        elif code == CALL_ON and phase not in green:
            opened.setdefault((phase, "wait"), t)
        elif code == CALL_OFF:
            opened.pop((phase, "wait"), None)
