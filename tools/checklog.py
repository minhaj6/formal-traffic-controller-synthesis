#!/usr/bin/env python3
"""Check a controller event log against the assumptions of the signal model.

Reads an event CSV (timestamp,code,param) on stdin and prints one
tab-separated row per check:  check, cases, violations.

    sequence        every green is followed by yellow, then red clearance
    yellow_fixed    a phase always shows the same yellow time
    red_fixed       a phase always shows the same red clearance time
    yellow_range    yellow time is within the given range (MUTCD: 3 to 6 s)
    conflict        two conflicting phases are never both between the start
                    of green and the end of red clearance
    call_persists   a call registered while the phase is not green stays on
                    until the phase turns green
"""
import argparse
import sys
from collections import defaultdict
from statistics import median

import atspm

NEMA_COMPATIBLE = "1-5,1-6,2-5,2-6,3-7,3-8,4-7,4-8"


def checks(events, compatible, yellow_range=(3.0, 6.0), tolerance=0.1):
    """Yield (check, cases, violations)."""
    found = defaultdict(list)                     # (phase, kind) -> [(start, duration)]
    for phase, kind, start, duration in atspm.intervals(events):
        found[phase, kind].append((start, duration))
    phases = sorted({p for p, _ in found})

    # every green that ended must be followed by a yellow and a red clearance;
    # one per phase may still be in progress when the log ends
    ended = sum(len(found[p, "green"]) for p in phases)
    unfinished = sum(max(len(found[p, "green"]) - len(found[p, "red_clearance"]) - 1, 0)
                     for p in phases)
    yield "sequence", ended, unfinished

    for check, kind in (("yellow_fixed", "yellow"), ("red_fixed", "red_clearance")):
        cases = bad = 0
        for p in phases:
            durations = [d for _, d in found[p, kind]]
            cases += len(durations)
            bad += sum(abs(d - median(durations)) > tolerance for d in durations)
        yield check, cases, bad

    yellows = [d for p in phases for _, d in found[p, "yellow"]]
    lo, hi = yellow_range
    yield "yellow_range", len(yellows), sum(not lo - tolerance <= d <= hi + tolerance for d in yellows)

    # active = from begin green to end of red clearance
    starts = defaultdict(list)
    active = defaultdict(list)
    for t, code, p in events:
        if code == atspm.GREEN:
            starts[p].append(t)
        elif code == atspm.END and starts[p]:
            active[p].append((starts[p].pop(), t))
    cases = bad = 0
    for i, p in enumerate(phases):
        for q in phases[i + 1:]:
            if frozenset((p, q)) in compatible:
                continue
            for a0, a1 in active[p]:
                cases += 1
                bad += any(b0 < a1 - tolerance and a0 < b1 - tolerance for b0, b1 in active[q])
    yield "conflict", cases, bad

    green, pending, cases, bad = set(), set(), 0, 0
    for t, code, p in events:
        if code == atspm.GREEN:
            green.add(p)
            pending.discard(p)
        elif code == atspm.YELLOW:
            green.discard(p)
        elif code == atspm.CALL_ON and p not in green and p not in pending:
            pending.add(p)
            cases += 1
        elif code == atspm.CALL_OFF and p in pending:
            pending.discard(p)
            bad += 1
    yield "call_persists", cases, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--compatible", default=NEMA_COMPATIBLE, metavar="A-B,...",
                    help="phase pairs that may run together; every other pair conflicts "
                         "(default: NEMA dual ring)")
    ap.add_argument("--yellow-range", type=float, nargs=2, default=(3.0, 6.0), metavar=("LO", "HI"))
    args = ap.parse_args()
    compatible = {frozenset(int(x) for x in pair.split("-")) for pair in args.compatible.split(",")}
    print("check", "cases", "violations", sep="\t")
    for row in checks(atspm.read(sys.stdin), compatible, args.yellow_range):
        print(*row, sep="\t")


if __name__ == "__main__":
    main()
