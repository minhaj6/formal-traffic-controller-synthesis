#!/usr/bin/env python3
"""Draw the realizability map from the TSV written by realizability_map.py."""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def main():
    rows = list(csv.DictReader(sys.stdin, delimiter="\t"))
    greens = sorted({int(r["min_green_s"]) for r in rows})
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for r in rows:
        ok = r["realizable"] == "1"
        ax.scatter(int(r["max_wait_s"]), int(r["min_green_s"]), marker="s", s=150,
                   color="#2e9e4f" if ok else "#d0453a")
    bound = {int(r["min_green_s"]): int(r["formula_s"]) for r in rows}
    ax.step([bound[s] - 0.5 for s in greens for _ in (0, 1)],
            [y for s in greens for y in (s - 1, s + 1)], color="black", lw=1.5)
    ax.set_xlabel("waiting-time bound (s)")
    ax.set_ylabel("major-street minimum green (s)")
    ax.set_yticks(greens)
    ax.legend(handles=[Patch(color="#2e9e4f", label="realizable"),
                       Patch(color="#d0453a", label="unrealizable"),
                       plt.Line2D([], [], color="black", label="hand formula")],
              ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1), fontsize=8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(sys.argv[1], dpi=160)


if __name__ == "__main__":
    main()
