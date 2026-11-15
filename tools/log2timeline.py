#!/usr/bin/env python3
"""Sample a controller event log into a signal timeline.

Reads an event CSV (timestamp,code,param) on stdin and prints one CSV row
per time step with columns step, call_pN, g_pN, y_pN for every phase N in
the log -- the same layout simulate.py writes, so plot_timeline.py can draw
it.  A signal is sampled at the start of each step.
"""
import argparse
import sys

import atspm


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--step", type=float, default=1.0, help="seconds per row (default 1)")
    ap.add_argument("--start", type=float, default=0.0, help="first second to print")
    ap.add_argument("--end", type=float, help="last second to print (default: end of log)")
    args = ap.parse_args()
    events = atspm.read(sys.stdin)
    phases = sorted({p for _, code, p in events if code == atspm.GREEN})
    state = {f"{kind}_p{p}": 0 for p in phases for kind in ("call", "g", "y")}
    effect = {atspm.GREEN: {"g": 1}, atspm.YELLOW: {"g": 0, "y": 1},
              atspm.RED_CLEARANCE: {"y": 0}, atspm.CALL_ON: {"call": 1}, atspm.CALL_OFF: {"call": 0}}
    end = events[-1][0] if args.end is None else args.end
    print("step", *state, sep=",")
    k, step = 0, 0
    while step * args.step <= end:
        while k < len(events) and events[k][0] <= step * args.step:
            _, code, p = events[k]
            if p in phases:
                for kind, value in effect.get(code, {}).items():
                    state[f"{kind}_p{p}"] = value
            k += 1
        if step * args.step >= args.start:
            print(step, *state.values(), sep=",")
        step += 1


if __name__ == "__main__":
    main()
