#!/usr/bin/env python3
"""Find the smallest realizable waiting-time bound for an intersection.

Reads a timing JSON and prints the smallest number of steps N such that
"every call is served within N steps" is realizable together with the rest
of the spec.  Realizability is monotone in N, so a doubling search followed
by bisection is enough.
"""
import argparse
import json
import sys

import genspec
import gr1spec
import gr1synth
import synth

SOLVERS = {
    "slugs": lambda timing, **opt: gr1synth.realizable(gr1spec.spec(timing, **opt)),
    "ltlsynt": lambda timing, **opt: synth.realizable(genspec.spec(timing, **opt)),
}


def min_wait(timing, solver="slugs", limit=1024, **spec_options):
    """Smallest realizable bound in steps, or None if there is none up to `limit`."""
    def ok(n):
        return SOLVERS[solver](timing, max_wait_s=n * timing["step_s"], **spec_options)
    hi = 1
    while not ok(hi):
        hi *= 2
        if hi > limit:
            return None
    lo = hi // 2          # lo is unrealizable (or 0), hi is realizable
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("timing", nargs="?", help="timing JSON file (default: stdin)")
    ap.add_argument("--solver", choices=SOLVERS, default="slugs")
    ap.add_argument("--limit", type=int, default=1024, help="give up above this many steps")
    args = ap.parse_args()
    timing = json.load(open(args.timing) if args.timing else sys.stdin)
    n = min_wait(timing, args.solver, args.limit)
    if n is None:
        sys.exit(f"not realizable for any bound up to {args.limit} steps")
    print(n)


if __name__ == "__main__":
    main()
