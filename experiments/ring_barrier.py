#!/usr/bin/env python3
"""Draw the NEMA dual-ring, eight-phase diagram used by intersections/nema8.json."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MOVEMENT = {1: "major left", 2: "major through", 3: "minor left", 4: "minor through",
            5: "major left", 6: "major through", 7: "minor left", 8: "minor through"}
RINGS = [[1, 2, 3, 4], [5, 6, 7, 8]]


def main():
    fig, ax = plt.subplots(figsize=(7, 2.4))
    for row, ring in enumerate(RINGS):
        y = 1 - row
        for col, phase in enumerate(ring):
            x = col + (0.15 if col >= 2 else 0)
            ax.add_patch(plt.Rectangle((x, y), 0.92, 0.8, fill=False, lw=1.2))
            ax.text(x + 0.46, y + 0.52, f"p{phase}", ha="center", va="center", fontsize=12,
                    weight="bold")
            ax.text(x + 0.46, y + 0.2, MOVEMENT[phase], ha="center", va="center", fontsize=8)
        ax.text(-0.12, y + 0.4, f"ring {row + 1}", ha="right", va="center", fontsize=9)
    for x in (2.035,):
        ax.plot([x, x], [-0.15, 1.95], color="black", lw=3)
        ax.text(x, 2.02, "barrier", ha="center", va="bottom", fontsize=9)
    ax.plot([4.11, 4.11], [-0.15, 1.95], color="black", lw=3)
    ax.set_xlim(-0.8, 4.3)
    ax.set_ylim(-0.25, 2.3)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(sys.argv[1], dpi=160)


if __name__ == "__main__":
    main()
