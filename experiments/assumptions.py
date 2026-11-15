#!/usr/bin/env python3
"""Which spec variants are realizable, according to both solvers.

Each row changes the spec of the two-phase intersection (2 s steps) by
adding an option or dropping the rules whose names start with a prefix.

Prints TSV: variant, options, slugs, ltlsynt  (realizable / unrealizable).
"""
import sys

from common import run

VARIANTS = [
    ("default: no assumption, calls may be withdrawn", ""),
    ("default, a waiting call is served within 26 s", "--max-wait 26"),
    ("default, a waiting call is served within 24 s", "--max-wait 24"),
    ("locking detectors: every call is served", "--locking"),
    ("locking detectors, without assuming that calls persist", "--locking --drop call_persists"),
    ("no max-out: a green with demand is never cut off", "--extend"),
    ("no max-out, without assuming that queues clear", "--extend --drop queue_clears"),
    ("no max-out, a waiting call is served within 40 s", "--extend --max-wait 40"),
]


def verdict(pipeline, timing):
    status, _, _ = run(pipeline, stdin=timing)
    return {"ok": "realizable", "fail": "unrealizable"}.get(status, status)


def main():
    _, timing, _ = run("python3 timing.py ../intersections/two_phase.json --step 2")
    print("variant", "options", "slugs", "ltlsynt", sep="\t")
    for name, options in VARIANTS:
        slugs = verdict(f"python3 gr1spec.py {options} | python3 gr1synth.py --check", timing)
        ltlsynt = verdict(f"python3 genspec.py {options} | python3 synth.py --check", timing)
        print(name, options or "-", slugs, ltlsynt, sep="\t")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
