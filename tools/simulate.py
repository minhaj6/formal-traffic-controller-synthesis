#!/usr/bin/env python3
"""Run an AIGER circuit on a sequence of inputs.

Reads CSV rows of inputs on stdin (header = input names, values 0/1) and
prints one CSV row per step with the step number, inputs and outputs.

With --lock, an input call_X that has been 1 stays 1 until output g_X is 1,
which models a detector with locking memory: a waiting vehicle keeps its
call until it is served.
"""
import argparse
import csv
import sys

import aiger


def run(circuit, rows, lock=False):
    """Yield {signal: 0/1} for every input row."""
    state, held = None, {}
    for row in rows:
        inputs = {name: int(row[name]) for name, _ in circuit.inputs}
        if lock:
            for name in held:
                inputs[name] |= held[name]
        outputs, state = aiger.step(circuit, state, inputs)
        if lock:
            held = {name: int(inputs[name] and not outputs["g_" + name[5:]])
                    for name in inputs
                    if name.startswith("call_") and "g_" + name[5:] in outputs}
        yield {**inputs, **{k: int(v) for k, v in outputs.items()}}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("circuit", help="ASCII AIGER file")
    ap.add_argument("--lock", action="store_true", help="hold each call_X until g_X")
    args = ap.parse_args()
    circuit = aiger.parse(open(args.circuit).read())
    out = None
    for t, signals in enumerate(run(circuit, csv.DictReader(sys.stdin), args.lock)):
        if out is None:
            out = csv.DictWriter(sys.stdout, ["step", *signals], lineterminator="\n")
            out.writeheader()
        out.writerow({"step": t, **signals})


if __name__ == "__main__":
    main()
