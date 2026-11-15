#!/usr/bin/env python3
"""Realizability of a waiting bound as the major street's minimum green changes.

Uses the two-phase intersection at 1 s steps.  For each minimum green of the
first phase and each waiting bound, Slugs decides realizability; the hand
formula (minimum cycle minus the shortest minimum green) is printed alongside.

Prints TSV: min_green_s, max_wait_s, realizable (1/0), formula_s.
"""
import json
import sys

from common import ROOT, run

MIN_GREENS = range(4, 18, 2)
WAITS = range(18, 33)


def main():
    base = json.load(open(f"{ROOT}/intersections/two_phase.json"))
    major = next(iter(base["phases"]))
    print("min_green_s", "max_wait_s", "realizable", "formula_s", sep="\t")
    for green in MIN_GREENS:
        base["phases"][major]["min_green_s"] = green
        _, timing, _ = run("python3 timing.py /dev/stdin", stdin=json.dumps(base))
        phases = json.loads(timing)["phases"].values()
        bound = (sum(p["min_green"] + p["yellow"] + p["red"] for p in phases)
                 - min(p["min_green"] for p in phases))
        for wait in WAITS:
            status, _, _ = run(f"python3 gr1spec.py --max-wait {wait} | python3 gr1synth.py --check",
                               stdin=timing)
            print(green, wait, int(status == "ok"), bound, sep="\t")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
