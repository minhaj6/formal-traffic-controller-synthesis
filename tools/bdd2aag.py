#!/usr/bin/env python3
"""Turn a Slugs symbolic strategy (a BDD) into an ASCII AIGER circuit.

The strategy is a relation between the current state and the next state:
for the current values of all variables and the next inputs it allows one
or more next output valuations.  This tool fixes one of them, bit by bit:
an output bit is 1 whenever that still leaves a legal choice for the bits
not yet decided.  Each bit ends up as a function of the current state and
the next inputs, and is written out as a network of multiplexers.

The circuit keeps the previous value of every variable in a latch.  Latches
start at 0, which is the boot state of the specs written by gr1spec.py.
Variables whose name starts with '_' or contains '@' (bits of integers)
stay internal; every other output variable becomes a circuit output.
"""
import argparse
import re
import sys

from dd import cudd

import aiger

FALSE, TRUE = 0, 1


def read_strategy(text, bdd):
    """Load a DDDMP text dump.  Returns (root, variable names, input names)."""
    header = dict(re.findall(r"^\.(\w+) (.*)$", text, re.M))
    names = header["suppvarnames"].split()
    by_id = dict(zip(header["ids"].split(), names))
    inputs = set(re.findall(r"^#\t\d+: in_(\S+)$", text, re.M))
    bdd.declare(*names)
    node = {}
    for line in text[text.index(".nodes"):].splitlines()[1:]:
        if line.startswith(".end"):
            break
        ident, var_id, _level, then, other = line.split()
        if var_id == "T":
            node[int(ident)] = bdd.true
            continue

        def child(ref):
            return ~node[-int(ref)] if int(ref) < 0 else node[int(ref)]
        node[int(ident)] = bdd.ite(bdd.var(by_id[var_id]), child(then), child(other))
    root = int(header["rootids"])
    return (~node[-root] if root < 0 else node[root]), names, inputs


class Gates:
    """AND gates with constant folding and sharing."""

    def __init__(self, first_free_variable):
        self.next = first_free_variable
        self.known = {}

    def AND(self, a, b):
        if a == FALSE or b == FALSE or a == b ^ 1:
            return FALSE
        if a == TRUE or a == b:
            return b
        if b == TRUE:
            return a
        key = (min(a, b), max(a, b))
        if key not in self.known:
            self.known[key] = 2 * self.next
            self.next += 1
        return self.known[key]

    def MUX(self, sel, a, b):
        """a if sel else b"""
        if a == b:
            return a
        return self.AND(self.AND(sel, a) ^ 1, self.AND(sel ^ 1, b) ^ 1) ^ 1

    def list(self):
        return sorted((lhs, a, b) for (a, b), lhs in self.known.items())


def convert(text):
    bdd = cudd.BDD()
    relation, names, input_names = read_strategy(text, bdd)
    current = [n for n in names if not n.endswith("'")]
    ins = [n for n in current if n in input_names]
    outs = [n for n in current if n not in input_names]

    # circuit variables: inputs (their value now), then one latch per variable (value before)
    literal = {n + "'": 2 * (k + 1) for k, n in enumerate(ins)}
    literal.update({n: 2 * (len(ins) + k + 1) for k, n in enumerate(current)})
    gates = Gates(len(ins) + len(current) + 1)
    done = {}

    def circuit(f):
        """Literal computing BDD f from the literals of its variables."""
        if f == bdd.true:
            return TRUE
        if f == bdd.false:
            return FALSE
        key = int(f)
        if key not in done:
            v = f.var
            done[key] = gates.MUX(literal[v], circuit(bdd.let({v: True}, f)),
                                  circuit(bdd.let({v: False}, f)))
        return done[key]

    # legal[i]: relation with the output bits after bit i quantified away
    legal = [relation]
    for n in reversed(outs[1:]):
        legal.append(bdd.exist([n + "'"], legal[-1]))
    # choose each bit as a function of the current state and next inputs only,
    # by substituting the choices already made for the earlier bits
    chosen = {}
    for n, f in zip(outs, reversed(legal)):
        f = bdd.let({n + "'": True}, f)
        chosen[n + "'"] = bdd.let(chosen, f) if chosen else f
    for name, f in chosen.items():
        literal[name] = circuit(f)

    return aiger.Circuit(
        inputs=[(n, literal[n + "'"]) for n in ins],
        latches=[(literal[n], literal[n + "'"]) for n in current],
        outputs=[(n, literal[n + "'"]) for n in outs if "@" not in n and not n.startswith("_")],
        ands=gates.list(),
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("strategy", nargs="?", help="Slugs strategy BDD (default: stdin)")
    args = ap.parse_args()
    sys.setrecursionlimit(100000)
    text = open(args.strategy).read() if args.strategy else sys.stdin.read()
    sys.stdout.write(aiger.dump(convert(text)))


if __name__ == "__main__":
    main()
