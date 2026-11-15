#!/usr/bin/env python3
"""Summarise a column of a tab-separated table by groups.

Reads a TSV with a header on stdin and prints, for every combination of the
--by columns, the count, minimum, median and maximum of the --value column.
"""
import argparse
import csv
import sys
from collections import defaultdict
from statistics import median


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--by", required=True, help="comma-separated group columns")
    ap.add_argument("--value", required=True, help="numeric column to summarise")
    args = ap.parse_args()
    by = args.by.split(",")
    groups = defaultdict(list)
    for row in csv.DictReader(sys.stdin, delimiter="\t"):
        groups[tuple(row[c] for c in by)].append(float(row[args.value]))
    print(*by, "n", "min", "median", "max", sep="\t")
    for key in sorted(groups):
        v = groups[key]
        print(*key, len(v), min(v), median(v), max(v), sep="\t")


if __name__ == "__main__":
    main()
