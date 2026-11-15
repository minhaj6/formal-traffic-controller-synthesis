#!/usr/bin/env python3
"""Synthesize a controller from a structured-slugs spec with Slugs.

Prints the winning strategy on stdout as a BDD in Slugs's text (DDDMP)
format.  Exits with status 1 and prints nothing when the spec is unrealizable.
"""
import argparse
import os
import subprocess
import sys
import tempfile

COMPILER = os.environ.get("SLUGS_COMPILER", "/opt/slugs-compiler/compiler.py")


def run_slugs(structured, slugs_args, out_file=None):
    """Compile the spec, run Slugs, and return True when realizable."""
    with tempfile.TemporaryDirectory() as tmp:
        src, compiled = os.path.join(tmp, "spec.structuredslugs"), os.path.join(tmp, "spec.slugsin")
        with open(src, "w") as f:
            f.write(structured)
        with open(compiled, "w") as f:
            subprocess.run([sys.executable, COMPILER, src], stdout=f, check=True)
        cmd = ["slugs", *slugs_args, compiled] + ([out_file] if out_file else [])
        log = subprocess.run(cmd, capture_output=True, text=True).stderr
    if "Specification is realizable" in log:
        return True
    if "Specification is unrealizable" in log:
        return False
    sys.stderr.write(log)
    sys.exit(2)


def realizable(structured):
    return run_slugs(structured, [])   # no option: realizability check only


def synthesize(structured):
    """Return the strategy BDD as text, or None when unrealizable."""
    with tempfile.NamedTemporaryFile("r", suffix=".bdd") as out:
        if not run_slugs(structured, ["--simpleSymbolicStrategy"], out.name):
            return None
        return out.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("spec", nargs="?", help="structured-slugs file (default: stdin)")
    ap.add_argument("--check", action="store_true",
                    help="only decide realizability; print no strategy")
    args = ap.parse_args()
    structured = open(args.spec).read() if args.spec else sys.stdin.read()
    strategy = ("" if realizable(structured) else None) if args.check else synthesize(structured)
    if strategy is None:
        print("UNREALIZABLE", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(strategy)


if __name__ == "__main__":
    main()
