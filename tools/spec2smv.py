#!/usr/bin/env python3
"""Turn a spec JSON into NuSMV LTLSPEC lines.

Safety formulas are checked as they are; each guarantee is checked as
"all assumptions -> guarantee".  Append the output to any NuSMV model that
defines the spec's inputs and outputs.
"""
import json
import re
import sys


def to_smv(formula):
    return re.sub(r"\b(true|false)\b", lambda m: m.group(1).upper(), formula)


def properties(spec):
    """[(name, formula)] in checking order."""
    assume = " & ".join(f"({f})" for f in spec["assumptions"].values()) or "true"
    props = list(spec["safety"].items())
    props += [(name, f"({assume}) -> ({f})") for name, f in spec["guarantees"].items()]
    return props


def main():
    spec = json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)
    for name, f in properties(spec):
        print(f"LTLSPEC NAME {name} := {to_smv(f)};")


if __name__ == "__main__":
    main()
