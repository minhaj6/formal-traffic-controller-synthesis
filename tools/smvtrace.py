#!/usr/bin/env python3
"""Extract a counterexample trace from NuSMV output as CSV.

Reads NuSMV's output on stdin and prints the N-th trace (default: the
first) with one row per state and one 0/1 column per boolean variable.
The `loop` column is 1 from the state where the lasso loop begins.
"""
import argparse
import csv
import re
import sys


def traces(text):
    """Yield each trace as a list of {variable: value}; NuSMV prints only changes."""
    trace, state, loop = [], None, False
    for line in text.splitlines():
        if re.match(r"\s*-> State: \d+\.1 <-", line) and trace:
            yield trace
            trace, state = [], None
        if re.match(r"\s*-> State: ", line):
            state = dict(trace[-1]) if trace else {}
            state["loop"] = "TRUE" if loop or state.get("loop") == "TRUE" else "FALSE"
            loop = False
            trace.append(state)
        elif "Loop starts here" in line:
            loop = True
        elif (m := re.match(r"\s+(\S+) = (\S+)$", line)) and state is not None:
            state[m.group(1)] = m.group(2)
        elif line.startswith("-- specification") and trace:
            yield trace
            trace, state = [], None
    if trace:
        yield trace


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("n", nargs="?", type=int, default=1, help="which trace (default 1)")
    ap.add_argument("--unroll", type=int, default=0, metavar="K",
                    help="repeat the loop K more times")
    args = ap.parse_args()
    found = list(traces(sys.stdin.read()))
    if len(found) < args.n:
        sys.exit(f"only {len(found)} trace(s) in the input")
    trace = found[args.n - 1]
    # the last state of a lasso repeats the state where the loop begins
    start = next((i for i, s in enumerate(trace) if s["loop"] == "TRUE"), len(trace))
    trace = trace + trace[start + 1:] * args.unroll
    columns = [k for k in trace[-1] if all(s.get(k, "FALSE") in ("TRUE", "FALSE") for s in trace)]
    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow(["step", *columns])
    for t, state in enumerate(trace):
        out.writerow([t, *(int(state.get(k) == "TRUE") for k in columns)])


if __name__ == "__main__":
    main()
