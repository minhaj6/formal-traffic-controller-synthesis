#!/usr/bin/env python3
"""Translate an ASCII AIGER circuit into a NuSMV module.

Inputs become unconstrained boolean variables, latches become state
variables, AND gates and outputs become DEFINEs.  Reads the circuit from a
file or stdin and prints the module on stdout.
"""
import sys

import aiger


def smv(circuit):
    name = {0: "FALSE"}
    for n, lit in circuit.inputs:
        name[lit] = n
    for lit, _ in circuit.latches:
        name[lit] = f"l{lit}"
    for lit, _, _ in circuit.ands:
        name[lit] = f"a{lit}"

    def ref(lit):
        if lit == 1:
            return "TRUE"
        return ("!" if lit & 1 else "") + name[lit & ~1]

    out = ["MODULE main", "VAR"]
    out += [f"  {n} : boolean;" for n, _ in circuit.inputs]
    out += [f"  l{lit} : boolean;" for lit, _ in circuit.latches]
    out.append("DEFINE")
    out += [f"  a{lit} := {ref(a)} & {ref(b)};" for lit, a, b in circuit.ands]
    out += [f"  {n} := {ref(lit)};" for n, lit in circuit.outputs]
    out.append("ASSIGN")
    for lit, nxt in circuit.latches:
        out.append(f"  init(l{lit}) := FALSE;")
        out.append(f"  next(l{lit}) := {ref(nxt)};")
    return "\n".join(out)


def main():
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    print(smv(aiger.parse(text)))


if __name__ == "__main__":
    main()
