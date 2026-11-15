#!/usr/bin/env python3
"""Intervals computed for every phase of every intersection, at 1 s steps.

Prints TSV: intersection, phase, speed_mph, width_ft, min_green_s, yellow_s,
red_s (as computed) and yellow, red (rounded up to whole steps).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import timing  # noqa: E402


def main():
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "intersections")
    print("intersection", "phase", "speed_mph", "width_ft", "min_green_s", "yellow_s", "red_s",
          "yellow", "red", sep="\t")
    for path in sorted(glob.glob(os.path.join(root, "*.json"))):
        intersection = json.load(open(path))
        computed = timing.timing(intersection, 1.0)["phases"]
        for name, p in intersection["phases"].items():
            t = computed[name]
            print(os.path.basename(path)[:-5], name, p["speed_mph"], p["width_ft"],
                  p["min_green_s"], t["yellow_s"], t["red_s"], t["yellow"], t["red"], sep="\t")


if __name__ == "__main__":
    main()
