#!/usr/bin/env python3
"""Synthesize a controller from a spec JSON with Spot's ltlsynt.

Prints the controller as an ASCII AIGER circuit on stdout.  Exits with
status 1 and prints nothing when the spec is unrealizable.
"""
import argparse
import json
import subprocess
import sys


def conj(formulas):
    return " & ".join(f"({f})" for f in formulas) or "true"


def formula(spec):
    """safety & (assumptions -> guarantees)"""
    return (f"{conj(spec['safety'].values())} & "
            f"(({conj(spec['assumptions'].values())}) -> ({conj(spec['guarantees'].values())}))")


def realizable(spec, extra_args=()):
    """Decide realizability without building a circuit."""
    return synthesize(spec, ["--realizability", *extra_args]) is not None


def synthesize(spec, extra_args=()):
    """Return the AIGER text, or None when unrealizable."""
    cmd = ["ltlsynt", "--ins=" + ",".join(spec["ins"]), "--outs=" + ",".join(spec["outs"]),
           "--aiger", "-f", formula(spec), *extra_args]
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode not in (0, 1):
        sys.stderr.write(out.stderr)
        sys.exit(2)
    status, _, circuit = out.stdout.partition("\n")
    return circuit if status == "REALIZABLE" else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", nargs="?", help="spec JSON file (default: stdin)")
    ap.add_argument("--check", action="store_true",
                    help="only decide realizability; print no circuit")
    args = ap.parse_args()
    spec = json.load(open(args.spec) if args.spec else sys.stdin)
    circuit = synthesize(spec, ["--realizability"] if args.check else [])
    if circuit is None:
        print("UNREALIZABLE", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(circuit)


if __name__ == "__main__":
    main()
