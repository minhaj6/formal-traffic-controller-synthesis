#!/usr/bin/env python3
"""Draw a signal timeline from a CSV of 0/1 signals.

For every pair of columns g_X, y_X the plot has one row showing phase X as
green, yellow or red over time.  A column call_X, when present, is drawn as
a thin black strip under the row wherever the call is on.
"""
import argparse
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

COLOURS = {"G": "#2e9e4f", "Y": "#f2c230", "R": "#d0453a"}


def runs(values):
    """Yield (start, length, value) for each run of equal values."""
    start = 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[start]:
            yield start, i - start, values[start]
            start = i


def plot(rows, step_s=1.0, title=None, mark=None, phases=None):
    phases = phases or [c[2:] for c in rows[0] if c.startswith("g_") and "y_" + c[2:] in rows[0]]
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(phases) + 1.2))
    for row, p in enumerate(phases):
        y = len(phases) - 1 - row
        colours = ["G" if r["g_" + p] == "1" else "Y" if r["y_" + p] == "1" else "R" for r in rows]
        for start, length, c in runs(colours):
            ax.broken_barh([(start * step_s, length * step_s)], (y - 0.3, 0.6),
                           facecolors=COLOURS[c], edgecolor="none")
        if "call_" + p in rows[0]:
            for start, length, on in runs([r["call_" + p] for r in rows]):
                if on == "1":
                    ax.broken_barh([(start * step_s, length * step_s)], (y - 0.42, 0.08),
                                   facecolors="black")
    if mark is not None:
        ax.axvspan(mark * step_s, (mark + 1) * step_s, color="black", alpha=0.25, lw=0)
    ax.set_yticks(range(len(phases)), reversed(phases))
    ax.set_ylim(-0.6, len(phases) - 0.4)
    ax.set_xlim(0, len(rows) * step_s)
    ax.set_xlabel("time (s)")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False)
    handles = [Patch(color=COLOURS[c], label=l) for c, l in
               (("G", "green"), ("Y", "yellow"), ("R", "red"))]
    handles.append(Patch(color="black", label="call"))
    ax.legend(handles=handles, ncol=4, frameon=False, loc="lower right",
              bbox_to_anchor=(1, 1), fontsize=8)
    if title:
        ax.set_title(title, loc="left", fontsize=10)
    fig.tight_layout()
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", required=True, help="image file to write")
    ap.add_argument("--step", type=float, default=1.0, help="seconds per row (default 1)")
    ap.add_argument("--title")
    ap.add_argument("--mark", type=int, metavar="ROW", help="shade this row (e.g. a violation)")
    ap.add_argument("--phases", help="comma-separated phases to draw, top to bottom "
                                     "(default: all, in column order)")
    args = ap.parse_args()
    rows = list(csv.DictReader(sys.stdin))
    phases = args.phases.split(",") if args.phases else None
    plot(rows, args.step, args.title, args.mark, phases).savefig(args.output, dpi=160)


if __name__ == "__main__":
    main()
