#!/usr/bin/env python3
"""Generate the LTL specification of a signal controller.

Reads a timing JSON (from timing.py) on stdin or from a file and prints a
spec JSON on stdout:

    ins          detector inputs          call_<phase>
    outs         signal outputs           g_<phase>, y_<phase>  (neither = red)
    safety       formulas that must hold on every run, whatever the detectors do
    assumptions  what we assume about the detectors
    guarantees   formulas that must hold on every run that meets the assumptions

Formulas use only  ! & | -> X F G  so that both Spot and NuSMV read them.
"""
import argparse
import json
import re
import sys


def X(f, k=1):
    """f, k steps from now."""
    for _ in range(k):
        f = f"X({f})"
    return f


def hold(f, k):
    """f now and for the k-1 following steps."""
    out = f
    for _ in range(k - 1):
        out = f"({f} & X({out}))"
    return out


def within(f, k):
    """f now or at one of the k following steps."""
    out = f
    for _ in range(k):
        out = f"({f} | X({out}))"
    return out


def any_of(fs):
    return "(" + " | ".join(fs) + ")" if fs else "false"


def spec(timing, max_wait_s=None, extend=False, locking=False, drop=()):
    phases = timing["phases"]
    for p in phases:   # ltlsynt lower-cases the names given to --ins/--outs
        if not re.fullmatch(r"[a-z0-9]+", p):
            sys.exit(f"phase name {p!r}: use lower-case letters and digits only")
    conflicts = {p: set() for p in phases}
    for a, b in timing["conflicts"]:
        conflicts[a].add(b)
        conflicts[b].add(a)

    # "clear" = red for at least the red clearance time (and at least one step)
    clear = {p: max(t["red"], 1) for p, t in phases.items()}
    k_all = max(clear.values())

    def group_clear(p):
        """p and its rivals have been clear up to step k_all - 1."""
        return " & ".join(X(hold(f"(!g_{q} & !y_{q})", clear[q]), k_all - clear[q])
                          for q in [p, *sorted(conflicts[p])])

    safety, assumptions, guarantees = {}, {}, {}
    for p, t in phases.items():
        g, y, call = f"g_{p}", f"y_{p}", f"call_{p}"
        red = f"(!{g} & !{y})"
        safety[f"init_{p}"] = red
        safety[f"one_colour_{p}"] = f"G(!({g} & {y}))"
        # colour order: green -> yellow -> red -> green
        safety[f"green_then_yellow_{p}"] = f"G({g} -> X({g} | {y}))"
        safety[f"yellow_then_red_{p}"] = f"G({y} -> X(!{g}))"
        safety[f"red_then_green_{p}"] = f"G({red} -> X(!{y}))"
        # interval lengths
        safety[f"min_green_{p}"] = f"G((!{g} & X({g})) -> X({hold(g, t['min_green'])}))"
        safety[f"yellow_min_{p}"] = f"G((!{y} & X({y})) -> X({hold(y, t['yellow'])}))"
        safety[f"yellow_max_{p}"] = f"G({hold(y, t['yellow'])} -> {X('!' + y, t['yellow'])})"
        for q in sorted(conflicts[p]):
            if p < q:
                safety[f"conflict_{p}_{q}"] = f"G(!(({g} | {y}) & (g_{q} | y_{q})))"
            if t["red"] > 0:
                safety[f"red_clearance_{p}_{q}"] = (
                    f"G(({y} & X(!{y})) -> X({hold('!g_' + q, t['red'])}))")

        if locking:   # detectors: a call stays on until the phase is green
            assumptions[f"call_persists_{p}"] = f"G(({call} & !{g}) -> X({call}))"

        # actuated operation
        rivals = sorted(conflicts[p])
        rival_call = any_of([f"call_{q}" for q in rivals])
        rival_green = any_of([f"g_{q}" for q in rivals])
        guarantees[f"green_needs_call_{p}"] = f"G((!{g} & X({g})) -> X({call}))"
        guarantees[f"rest_in_green_{p}"] = f"G(({g} & !{rival_call}) -> X({g}))"
        # gap-out: past minimum green, no demand left, a rival waiting -> end the green
        m = t["min_green"]
        guarantees[f"gap_out_{p}"] = (
            f"G(({hold(g, m)} & {X(f'!{call} & {rival_call}', m - 1)}) -> {X('!' + g, m)})")
        # no backing up: p may not return to green during its own red
        # clearance while a rival is calling
        for k in range(1, clear[p] + 1):
            guarantees[f"no_backup_{p}_{k}"] = (
                f"G({y} -> {X(f'(!{g} & X({g})) -> X(!{rival_call})', k - 1)})")
        # no idling: p and its rivals red and past red clearance, p called
        # -> p turns green, unless a rival does or a called rival is still blocked
        blocked = any_of([f"({X(f'call_{q}', k_all)} & !({group_clear(q)}))" for q in rivals])
        guarantees[f"no_idle_{p}"] = (
            f"G(({group_clear(p)} & {X(call, k_all)})"
            f" -> ({X(f'({g} | {rival_green})', k_all)} | {blocked}))")
        if extend:
            # never cut off a phase that still has demand (no max-out)
            guarantees[f"extend_{p}"] = f"G(({g} & {call}) -> X({g}))"
            assumptions[f"queue_clears_{p}"] = f"G(F(!{g} | !{call}))"
        # service: without locking a call may be withdrawn before it is served
        # (e.g. a right turn on red), so only a call that stays on is owed a green
        n = None if max_wait_s is None else int(max_wait_s // timing["step_s"])  # round down
        waiting = f"({call} & !{g})"
        if locking:
            served = f"F({g})" if n is None else within(g, n)
            guarantees[f"served_{p}"] = f"G({call} -> {served})"
        elif n is None:
            guarantees[f"served_{p}"] = f"G(F(!{waiting}))"
        else:
            guarantees[f"served_{p}"] = f"G(!{hold(waiting, n + 1)})"

    def keep(formulas):
        return {k: v for k, v in formulas.items() if not any(k.startswith(d) for d in drop)}

    return {
        "ins": [f"call_{p}" for p in phases],
        "outs": [v for p in phases for v in (f"g_{p}", f"y_{p}")],
        "safety": keep(safety), "assumptions": keep(assumptions), "guarantees": keep(guarantees),
    }


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
                    help="drop every formula whose name starts with PREFIX (repeatable)")
    args = ap.parse_args()
    timing = json.load(open(args.timing) if args.timing else sys.stdin)
    json.dump(spec(timing, args.max_wait, args.extend, args.locking, args.drop),
              sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
