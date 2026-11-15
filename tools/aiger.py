"""Read and run ASCII AIGER (.aag) circuits, the format ltlsynt writes.

A literal is an even number 2*v for variable v, or 2*v+1 for its negation;
0 is false and 1 is true.  Latches start at 0.
"""
from collections import namedtuple

Circuit = namedtuple("Circuit", "inputs latches outputs ands")
# inputs  : [(name, literal)]
# latches : [(literal, next_literal)]
# outputs : [(name, literal)]
# ands    : [(literal, literal_a, literal_b)]   in evaluation order


def parse(text):
    lines = text.splitlines()
    _, _, n_in, n_latch, n_out, n_and = lines[0].split()
    n_in, n_latch, n_out, n_and = int(n_in), int(n_latch), int(n_out), int(n_and)
    body = [[int(x) for x in line.split()] for line in lines[1:1 + n_in + n_latch + n_out + n_and]]
    ins = [row[0] for row in body[:n_in]]
    latches = [(row[0], row[1]) for row in body[n_in:n_in + n_latch]]
    outs = [row[0] for row in body[n_in + n_latch:n_in + n_latch + n_out]]
    ands = sorted(tuple(row) for row in body[n_in + n_latch + n_out:])
    for lhs, a, b in ands:
        assert a < lhs and b < lhs, "AND gates are not in evaluation order"

    names = {}
    for line in lines[1 + len(body):]:
        if line == "c":
            break
        key, _, name = line.partition(" ")
        names[key] = name
    return Circuit(
        inputs=[(names.get(f"i{k}", f"i{k}"), lit) for k, lit in enumerate(ins)],
        latches=latches,
        outputs=[(names.get(f"o{k}", f"o{k}"), lit) for k, lit in enumerate(outs)],
        ands=ands,
    )


def step(circuit, state, inputs):
    """One clock tick.

    state  : {latch literal: bool}, or None for the initial state
    inputs : {input name: bool}
    Returns ({output name: bool}, next state).
    """
    val = {0: False}
    for lit, _ in circuit.latches:
        val[lit] = state[lit] if state else False
    for name, lit in circuit.inputs:
        val[lit] = bool(inputs[name])

    def value(lit):
        return val[lit & ~1] ^ bool(lit & 1)

    for lhs, a, b in circuit.ands:
        val[lhs] = value(a) and value(b)
    outputs = {name: value(lit) for name, lit in circuit.outputs}
    return outputs, {lit: value(nxt) for lit, nxt in circuit.latches}


def dump(circuit):
    """ASCII AIGER text of a circuit."""
    c = circuit
    top = max([0] + [lit for _, lit in c.inputs] + [lit for lit, _ in c.latches]
              + [lit for lit, _, _ in c.ands]) // 2
    lines = [f"aag {top} {len(c.inputs)} {len(c.latches)} {len(c.outputs)} {len(c.ands)}"]
    lines += [str(lit) for _, lit in c.inputs]
    lines += [f"{lit} {nxt}" for lit, nxt in c.latches]
    lines += [str(lit) for _, lit in c.outputs]
    lines += [f"{lhs} {a} {b}" for lhs, a, b in c.ands]
    lines += [f"i{k} {name}" for k, (name, _) in enumerate(c.inputs)]
    lines += [f"o{k} {name}" for k, (name, _) in enumerate(c.outputs)]
    return "\n".join(lines) + "\n"
