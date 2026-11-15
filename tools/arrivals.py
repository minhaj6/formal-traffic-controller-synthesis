#!/usr/bin/env python3
"""Print a random CSV of 0/1 columns, one row per step.

Each NAME=P argument makes a column that is 1 with probability P at every
step, independently (Bernoulli arrivals).
"""
import argparse
import random


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("columns", nargs="+", metavar="NAME=P")
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    cols = [(name, float(p)) for name, p in (c.split("=") for c in args.columns)]
    rng = random.Random(args.seed)
    print(",".join(name for name, _ in cols))
    for _ in range(args.steps):
        print(",".join(str(int(rng.random() < p)) for _, p in cols))


if __name__ == "__main__":
    main()
