#!/usr/bin/env python3
"""Generate a GR(1) specification of a signal controller for Slugs.

Reads a timing JSON (from timing.py) and prints a "structured slugs" spec.
It states the same requirements as genspec.py, rule for rule and under the
same names, but with explicit counters instead of nested next-operators,
which is the form GR(1) solvers need:

    t_<p>   steps spent in the current colour, counting the present step
    w_<p>   steps the present call has been waiting   (only with --max-wait)
    _bad    a detector assumption has been broken     (only with --locking)
    _run    0 in the boot state, 1 from the first real step on

Safety rules hold always; with assumptions, the guarantees are only required
until `_bad`.  A primed name is the value at the next step.

The game starts in a boot state where every output is 0, one step before
time 0.  A controller circuit can therefore start with all its memory at 0
and needs no separate description of the initial state.
"""
import argparse
import json
import sys


def rules(timing, max_wait_s=None, extend=False, locking=False):
    """Return the spec as dictionaries of named formulas."""
    phases = timing["phases"]
    rivals = {p: set() for p in phases}
    for a, b in timing["conflicts"]:
        rivals[a].add(b)
        rivals[b].add(a)
    n = None if max_wait_s is None else int(max_wait_s // timing["step_s"])

    def red(p):
        return f"(!g_{p} & !y_{p})"

    def any_of(terms):
        return "(" + " | ".join(terms) + ")" if terms else "FALSE"

    def group_clear(p):
        """p and its rivals are red and past their red clearance."""
        return "(" + " & ".join(f"{red(q)} & t_{q} >= {max(phases[q]['red'], 1)}"
                                for q in [p, *sorted(rivals[p])]) + ")"

    r = {"outputs": [], "init": {}, "safety": {}, "bookkeeping": {},
         "assumptions": {}, "guarantees": {}, "env_liveness": {}, "sys_liveness": {}}
    for p, t in phases.items():
        g, y, call, tm, w = f"g_{p}", f"y_{p}", f"call_{p}", f"t_{p}", f"w_{p}"
        m, yel = t["min_green"], t["yellow"]
        cap = max(m, yel, t["red"], 1)
        rs = sorted(rivals[p])
        r["outputs"] += [g, y, f"{tm}:0...{cap}"]
        r["init"][f"init_{p}"] = f"!{g}' & !{y}' & {tm}' = {cap}"   # red for a long time

        same = f"(({g} <-> {g}') & ({y} <-> {y}'))"
        r["bookkeeping"][f"timer_{p}"] = (
            f"_run -> ((({same} & {tm} < {cap}) -> ({tm}' = {tm} + 1))"
            f" & (({same} & {tm} = {cap}) -> ({tm}' = {cap}))"
            f" & (!{same} -> ({tm}' = 1)))")

        s = r["safety"]
        s[f"one_colour_{p}"] = f"!({g}' & {y}')"
        s[f"green_then_yellow_{p}"] = f"{g} -> ({g}' | {y}')"
        s[f"yellow_then_red_{p}"] = f"{y} -> !{g}'"
        s[f"red_then_green_{p}"] = f"{red(p)} -> !{y}'"
        s[f"min_green_{p}"] = f"({g} & {tm} < {m}) -> {g}'"
        s[f"yellow_min_{p}"] = f"({y} & {tm} < {yel}) -> {y}'"
        s[f"yellow_max_{p}"] = f"({y} & {tm} >= {yel}) -> !{y}'"
        for q in rs:
            if p < q:
                s[f"conflict_{p}_{q}"] = f"!(({g}' | {y}') & (g_{q}' | y_{q}'))"
            if t["red"] > 0:   # q may not start before p's red clearance is over
                s[f"red_clearance_{p}_{q}"] = (
                    f"(!g_{q} & g_{q}') -> ({red(p)} & {tm} >= {t['red']})")

        if locking:
            r["assumptions"][f"call_persists_{p}"] = f"({call} & !{g}) -> {call}'"

        rival_call = any_of([f"call_{q}" for q in rs])
        rival_green_next = any_of([f"g_{q}'" for q in rs])
        blocked = any_of([f"(call_{q}' & !{group_clear(q)})" for q in rs])
        gu = r["guarantees"]
        gu[f"green_needs_call_{p}"] = f"(!{g} & {g}') -> {call}'"
        gu[f"rest_in_green_{p}"] = f"({g} & !{rival_call}) -> {g}'"
        gu[f"gap_out_{p}"] = f"({g} & {tm} >= {m} & !{call} & {rival_call}) -> !{g}'"
        rival_call_next = any_of([f"call_{q}'" for q in rs])
        gu[f"no_backup_{p}"] = (f"(!{g} & {g}' & {tm} < {max(t['red'], 1)})"
                                f" -> !{rival_call_next}")
        gu[f"no_idle_{p}"] = (f"({group_clear(p)} & {call}')"
                              f" -> ({g}' | {rival_green_next} | {blocked})")
        if extend:
            gu[f"extend_{p}"] = f"({g} & {call}) -> {g}'"
            r["env_liveness"][f"queue_clears_{p}"] = f"!{g} | !{call}"
        # service.  Without locking, a call is owed a green only while it stays
        # on; with locking, every call is, even if the detector then lets go.
        if n is None:
            if locking:
                r["outputs"].append(f"pend_{p}")
                r["bookkeeping"][f"wait_{p}"] = f"pend_{p}' <-> (({call}' | pend_{p}) & !{g}')"
                r["sys_liveness"][f"served_{p}"] = f"!pend_{p}"
            else:
                r["sys_liveness"][f"served_{p}"] = f"!{call} | {g}"
        else:
            still = f" | {w} > 0" if locking else ""
            waiting = f"(({call}'{still}) & !{g}')"
            r["outputs"].append(f"{w}:0...{n}")
            r["bookkeeping"][f"wait_{p}"] = (
                f"(({waiting} & {w} < {n}) -> ({w}' = {w} + 1))"
                f" & (({waiting} & {w} = {n}) -> ({w}' = {n}))"
                f" & (!{waiting} -> ({w}' = 0))")
            gu[f"served_{p}"] = f"!({waiting} & {w} = {n})"
    r["inputs"] = [f"call_{p}" for p in phases]
    return r


def structured_slugs(r):
    """Text of the spec in the structured-slugs input language."""
    outputs = ["_run"] + r["outputs"]
    trans = ["_run'"] + [f"!_run -> ({f})" for f in r["init"].values()]
    trans += list(r["safety"].values()) + list(r["bookkeeping"].values())
    liveness = list(r["sys_liveness"].values()) or ["TRUE"]   # Slugs wants at least one goal
    if r["assumptions"]:   # guarantees are owed only while the assumptions have held
        outputs.append("_bad")
        held = " & ".join(f"({f})" for f in r["assumptions"].values())
        trans.append(f"_bad' <-> (_bad | (_run & !({held})))")
        trans += [f"!_bad' -> ({f})" for f in r["guarantees"].values()]
        liveness = [f"_bad | {f}" for f in liveness]
    else:
        trans += list(r["guarantees"].values())
    # boot state: every output is 0
    init = [f"{v.split(':')[0]} = 0" if ":" in v else f"!{v}" for v in outputs]
    sections = [("INPUT", r["inputs"]), ("OUTPUT", outputs), ("SYS_INIT", init),
                ("SYS_TRANS", trans), ("ENV_LIVENESS", list(r["env_liveness"].values())),
                ("SYS_LIVENESS", liveness)]
    return "\n\n".join(f"[{name}]\n" + "\n".join(lines) for name, lines in sections if lines)


def spec(timing, max_wait_s=None, extend=False, locking=False, drop=()):
    r = rules(timing, max_wait_s, extend, locking)
    for part in ("safety", "assumptions", "guarantees", "env_liveness", "sys_liveness"):
        r[part] = {k: v for k, v in r[part].items() if not any(k.startswith(d) for d in drop)}
    return structured_slugs(r)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timing", nargs="?", help="timing JSON file (default: stdin)")
    ap.add_argument("--max-wait", type=float, metavar="S",
                    help="serve every call within S seconds (default: eventually)")
    ap.add_argument("--extend", action="store_true",
                    help="never end a green that still has a call (no max-out); "
                         "adds the assumption that queues eventually clear")
    ap.add_argument("--locking", action="store_true",
                    help="assume calls persist until served, and promise a green "
                         "after every call (default: only to calls that stay on)")
    ap.add_argument("--drop", action="append", default=[], metavar="PREFIX",
                    help="drop every rule whose name starts with PREFIX (repeatable)")
    args = ap.parse_args()
    timing = json.load(open(args.timing) if args.timing else sys.stdin)
    print(spec(timing, args.max_wait, args.extend, args.locking, args.drop))


if __name__ == "__main__":
    main()
