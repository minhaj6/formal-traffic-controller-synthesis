#!/usr/bin/env python3
"""Draw a four-leg intersection with its signal phases on the approaches.

Usage: intersection.py OUT.png [LAYOUT]

LAYOUT is one of the names in LAYOUTS (default nema8). The major street runs
north-south.

nema8      a left-turn lane and a through lane per approach, eight phases. Even
           phases are through movements, odd phases the left turns that oppose
           them, as in intersections/nema8.json.
two_phase  one shared through-left lane per approach, one phase per street, as
           in intersections/two_phase.json.
"""
import math
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Polygon, Rectangle
from matplotlib.path import Path

LANE = 0.8        # lane width
REACH = 5.6       # how far each leg is drawn from the centre
ROAD, PAINT, YELLOW = "#5a5f66", "white", "#f2c12e"
RING_COLOUR = {1: "#ffffff", 2: "#f6c9a8"}

# degrees to rotate the northbound drawing to get each approach
ROTATION = {"northbound": 0, "westbound": 90, "southbound": 180, "eastbound": 270}

# layout -> approach -> lanes from the centre line outwards, as (movement, phase, ring).
# movement is "left", "through" or "through-left".
LAYOUTS = {
    "nema8": {
        "northbound": [("left", "p5", 2), ("through", "p2", 1)],
        "westbound": [("left", "p3", 1), ("through", "p8", 2)],
        "southbound": [("left", "p1", 1), ("through", "p6", 2)],
        "eastbound": [("left", "p7", 2), ("through", "p4", 1)],
    },
    "two_phase": {
        "northbound": [("through-left", "ns", 1)],
        "southbound": [("through-left", "ns", 1)],
        "eastbound": [("through-left", "ew", 1)],
        "westbound": [("through-left", "ew", 1)],
    },
}


def rotate(points, degrees):
    c, s = round(math.cos(math.radians(degrees))), round(math.sin(math.radians(degrees)))
    return [(c * x - s * y, s * x + c * y) for x, y in points]


def shaft(ax, points, codes):
    ax.add_patch(PathPatch(Path(points, codes), fill=False, edgecolor=PAINT, lw=3.2,
                           capstyle="butt", zorder=3))


def head(ax, points):
    ax.add_patch(Polygon(points, closed=True, facecolor=PAINT, edgecolor="none", zorder=3))


def lane_arrow(ax, r, x, base, movement):
    """Pavement-marking arrow in a lane centred on x, starting at base, heading +y.

    r rotates local points into place. A left turn is a hooked arrow; a shared
    lane is a straight arrow with the hook branching off its shaft.
    """
    line, curve = [Path.MOVETO, Path.LINETO], [Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3]
    through, left = "through" in movement, "left" in movement
    sx = x + 0.16 if left else x                     # shaft sits right of centre to fit the hook
    if through:
        top = base + 1.7
        shaft(ax, r((sx, base), (sx, top - 0.5)), line)
        head(ax, r((sx - 0.17, top - 0.55), (sx + 0.17, top - 0.55), (sx, top)))
    if left:
        y = base + (0.85 if through else 1.45)       # height of the hook
        start = base + 0.3 if through else base
        shaft(ax, r((sx, start), (sx, y - 0.4), (sx, y), (sx - 0.2, y)), curve)
        head(ax, r((sx - 0.15, y - 0.19), (sx - 0.15, y + 0.19), (sx - 0.48, y)))


def label(ax, xy, phase, ring):
    ax.add_patch(Circle(xy, 0.36, facecolor=RING_COLOUR[ring], edgecolor="black", lw=1, zorder=4))
    ax.text(*xy, phase, ha="center", va="center", fontsize=10, weight="bold", zorder=5)


def approach(ax, degrees, lanes, half):
    """One approach, drawn as the northbound one (south leg) and then rotated."""
    def r(*points):
        return rotate(points, degrees)

    stop = -half - 0.1
    ax.plot(*zip(*r((0, stop), (half, stop))), color=PAINT, lw=3, zorder=2)
    ax.plot(*zip(*r((0, stop), (0, -REACH))), color=YELLOW, lw=2, zorder=2)
    for i in range(1, len(lanes)):
        for x in (-i * LANE, i * LANE):
            ax.plot(*zip(*r((x, stop), (x, -REACH))), color=PAINT, lw=1, ls=(0, (6, 6)), zorder=2)
    tip = stop - 0.3
    for i, (movement, phase, ring) in enumerate(lanes):
        x = (i + 0.5) * LANE
        lane_arrow(ax, r, x, tip - 1.7, movement)
        label(ax, r((x, tip - 2.3))[0], phase, ring)


def main():
    layout = LAYOUTS[sys.argv[2] if len(sys.argv) > 2 else "nema8"]
    half = LANE * max(len(lanes) for lanes in layout.values())
    rings = sorted({ring for lanes in layout.values() for _, _, ring in lanes})

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_patch(Rectangle((-half, -REACH), 2 * half, 2 * REACH, color=ROAD, zorder=1))
    ax.add_patch(Rectangle((-REACH, -half), 2 * REACH, 2 * half, color=ROAD, zorder=1))
    for name, lanes in layout.items():
        approach(ax, ROTATION[name], lanes, half)

    ax.text(half + 0.25, REACH - 0.2, "major street", ha="left", va="top", fontsize=10)
    ax.text(-REACH + 0.1, half + 0.25, "minor street", ha="left", va="bottom", fontsize=10)
    ax.annotate("N", xy=(-REACH + 0.7, REACH - 0.3), xytext=(-REACH + 0.7, REACH - 1.6),
                ha="center", va="center", fontsize=11, weight="bold",
                arrowprops={"arrowstyle": "-|>", "color": "black", "lw": 1.5})
    if len(rings) > 1:
        for ring in rings:
            y = -REACH + 2.1 - 0.8 * ring
            ax.add_patch(Circle((half + 0.6, y), 0.27, facecolor=RING_COLOUR[ring],
                                edgecolor="black", lw=1))
            ax.text(half + 1.05, y, f"ring {ring}", ha="left", va="center", fontsize=10)

    ax.set_xlim(-REACH, REACH)
    ax.set_ylim(-REACH, REACH)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(sys.argv[1], dpi=160)


if __name__ == "__main__":
    main()
