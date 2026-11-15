#!/usr/bin/env python3
"""List the signal intervals found in a controller event log.

Reads an event CSV (timestamp,code,param) on stdin and prints one
tab-separated row per interval:  phase, interval, start_s, duration_s.
Intervals are green, yellow, red_clearance and wait (see atspm.py).
"""
import sys

import atspm


def main():
    print("phase", "interval", "start_s", "duration_s", sep="\t")
    for row in atspm.intervals(atspm.read(sys.stdin)):
        print(*row, sep="\t")


if __name__ == "__main__":
    main()
