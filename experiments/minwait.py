#!/usr/bin/env python3
"""Smallest realizable waiting bound, from synthesis and from the hand formula.

For an intersection in which every pair of phases conflicts, the worst case
for phase p is a call that arrives as p's own yellow begins while every other
phase is called: p waits for its yellow and red clearance and then for the
minimum green, yellow and red clearance of every other phase.  The bound is
the largest such wait, i.e. the minimum cycle length minus the shortest
minimum green.

Prints TSV: intersection, step_s, formula, slugs, ltlsynt  (bounds in steps).
"""
import json
import sys

from common import run

CASES = [("two_phase", s) for s in (4, 2, 1)] + [("four_phase", s) for s in (4, 2, 1)]


def formula(timing):
    phases = timing["phases"].values()
    cycle = sum(p["min_green"] + p["yellow"] + p["red"] for p in phases)
    return cycle - min(p["min_green"] for p in phases)


def main():
    print("intersection", "step_s", "formula", "slugs", "ltlsynt", sep="\t")
    for name, step in CASES:
        _, timing, _ = run(f"python3 timing.py ../intersections/{name}.json --step {step}")
        found = []
        for solver in ("slugs", "ltlsynt"):
            status, out, _ = run(f"python3 minwait.py --solver {solver}", stdin=timing)
            found.append(out.strip() if status == "ok" else status)
        print(name, step, formula(json.loads(timing)), *found, sep="\t")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
