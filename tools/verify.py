#!/usr/bin/env python3
"""Model-check a NuSMV model against a spec JSON.

Every property is checked by its own NuSMV process, several at a time.
Prints one tab-separated line per property:  name, verdict, seconds,
where the verdict is true, false, timeout or error (NuSMV died, e.g. out
of memory).  Exits with status 1 unless
every property is true.  With --log, NuSMV's output for the properties
that are false (including counterexample traces) is saved to that file.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import spec2smv


def check_one(model_text, name, formula, timeout=None, nusmv_args=()):
    """Return (verdict, seconds, NuSMV output) for one LTL property."""
    with tempfile.NamedTemporaryFile("w", suffix=".smv") as f:
        f.write(f"{model_text}\nLTLSPEC NAME {name} := {spec2smv.to_smv(formula)};\n")
        f.flush()
        start = time.time()
        try:
            run = subprocess.run(["NuSMV", *nusmv_args, f.name], capture_output=True,
                                 text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return "timeout", time.time() - start, ""
    found = re.search(r"^-- specification .* is (true|false)$", run.stdout, re.M)
    if not found:      # NuSMV crashed or was killed, e.g. out of memory
        return "error", time.time() - start, run.stdout + run.stderr
    return found.group(1), time.time() - start, run.stdout


def check(model_text, spec, jobs=2, timeout=None, nusmv_args=()):
    """Return [(name, verdict, seconds, NuSMV output)] in the spec's order."""
    props = spec2smv.properties(spec)
    with ThreadPoolExecutor(jobs) as pool:
        results = pool.map(lambda p: check_one(model_text, *p, timeout, nusmv_args), props)
        return [(name, *r) for (name, _), r in zip(props, results)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", help="NuSMV model file")
    ap.add_argument("spec", help="spec JSON file")
    ap.add_argument("-j", "--jobs", type=int, default=2,
                    help="parallel NuSMV processes (default 2; each can use gigabytes)")
    ap.add_argument("--timeout", type=float, metavar="S", help="give up on a property after S seconds")
    ap.add_argument("--log", help="save NuSMV's output for false properties here")
    ap.add_argument("nusmv_args", nargs="*", help="extra NuSMV arguments (after --)")
    args = ap.parse_args()
    results = check(open(args.model).read(), json.load(open(args.spec)),
                    args.jobs, args.timeout, args.nusmv_args)
    if args.log:
        with open(args.log, "w") as f:
            f.writelines(out for _, verdict, _, out in results if verdict == "false")
    for name, verdict, seconds, _ in results:
        print(name, verdict, f"{seconds:.1f}", sep="\t")
    sys.exit(0 if all(verdict == "true" for _, verdict, _, _ in results) else 1)


if __name__ == "__main__":
    main()
