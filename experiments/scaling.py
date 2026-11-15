#!/usr/bin/env python3
"""Cost of each pipeline stage as the intersection and time resolution grow.

For every case: decide realizability with both solvers, extract the Slugs
strategy, turn it into a circuit and model-check it.  Every stage runs under
a time and memory limit; a stage that hits one is reported as such and the
later stages are skipped.

Prints TSV, one row per case.
"""
import argparse
import os
import sys
import tempfile

from common import run

CASES = [(name, step) for name in ("two_phase", "four_phase", "six_phase", "nema8") for step in (4, 2, 1)]
COLUMNS = ["intersection", "step_s", "ltlsynt_s", "slugs_s", "bdd_nodes", "latches", "gates",
           "circuit_s", "properties", "proved", "verify_s"]


def seconds(status, elapsed):
    return f"{elapsed:.1f}" if status == "ok" else status


def case(name, step, limit, verify_limit, jobs):
    row = dict.fromkeys(COLUMNS, "-")
    row.update(intersection=name, step_s=step)
    _, timing, _ = run(f"python3 timing.py ../intersections/{name}.json --step {step}")
    row["ltlsynt_s"] = seconds(*run("python3 genspec.py | python3 synth.py --check",
                                    limit, stdin=timing)[::2])
    with tempfile.TemporaryDirectory() as tmp:
        f = lambda ext: os.path.join(tmp, "c." + ext)   # noqa: E731
        open(f("timing"), "w").write(timing)
        status, _, t = run(f"python3 gr1spec.py {f('timing')} | python3 gr1synth.py > {f('bdd')}", limit)
        row["slugs_s"] = seconds(status, t)
        if status != "ok":
            return row
        row["bdd_nodes"] = run(f"grep -m1 nnodes {f('bdd')}")[1].split()[-1]
        status, _, t = run(f"python3 bdd2aag.py {f('bdd')} > {f('aag')}", limit)
        row["circuit_s"] = seconds(status, t)
        if status != "ok":
            return row
        header = open(f("aag")).readline().split()
        row["latches"], row["gates"] = header[3], header[5]
        _, verdicts, t = run(
            f"python3 genspec.py {f('timing')} > {f('spec')}; python3 aag2smv.py {f('aag')} > {f('smv')};"
            f" python3 verify.py {f('smv')} {f('spec')} -j {jobs} --timeout {verify_limit}",
            seconds=24 * 3600, memory_gb=3)
        lines = verdicts.splitlines()
        row["properties"] = len(lines)
        row["proved"] = sum(line.split("\t")[1] == "true" for line in lines)
        row["verify_s"] = f"{t:.1f}"
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=300, help="seconds per synthesis stage")
    ap.add_argument("--verify-limit", type=int, default=120, help="seconds per property")
    ap.add_argument("--jobs", type=int, default=2, help="parallel model-checker processes")
    ap.add_argument("--only", help="run only this intersection")
    args = ap.parse_args()
    print(*COLUMNS, sep="\t")
    for name, step in CASES:
        if args.only in (None, name):
            print(*case(name, step, args.limit, args.verify_limit, args.jobs).values(), sep="\t")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
