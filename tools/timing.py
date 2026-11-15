#!/usr/bin/env python3
"""Compute signal change intervals from an intersection description.

Reads an intersection JSON file, applies the ITE kinematic formulas and
rounds every interval to whole time steps.  Prints a timing JSON on stdout.
The formulas and default constants are Equation 5-2 of the FHWA Traffic Signal
Timing Manual (FHWA-HOP-08-024, 2008).

    yellow        = t + 1.47 v / (2 a + 64.4 g)   clamped to the MUTCD 3-6 s range
    red clearance = (W + L) / (1.47 v)

v is the approach speed in mph, g the grade as a decimal (uphill positive),
W the width to clear in feet.  Rounding to steps is always upward, so the
discrete intervals are never shorter than the computed ones.
"""
import argparse
import json
import math
import sys

FPS_PER_MPH = 1.47           # 1 mph = 5280 ft / 3600 s = 1.47 ft/s
GRAVITY_TERM = 64.4          # 2 * 32.2 ft/s^2 (g = 32.2 ft/s^2 = 9.8 m/s^2)
YELLOW_RANGE = (3.0, 6.0)    # MUTCD 11th ed., Section 4F.17, paragraph 13 (guidance)


def yellow_s(speed_mph, grade=0.0, perception_s=1.0, decel=10.0):
    y = perception_s + FPS_PER_MPH * speed_mph / (2 * decel + GRAVITY_TERM * grade)
    return min(max(y, YELLOW_RANGE[0]), YELLOW_RANGE[1])


def red_clearance_s(speed_mph, width_ft, vehicle_ft=20.0):
    return (width_ft + vehicle_ft) / (FPS_PER_MPH * speed_mph)


def steps(seconds, step_s):
    """Smallest whole number of steps covering `seconds`."""
    return math.ceil(seconds / step_s - 1e-9)


def timing(intersection, step_s, perception_s=1.0, decel=10.0, vehicle_ft=20.0):
    phases = {}
    for name, p in intersection["phases"].items():
        y = yellow_s(p["speed_mph"], p.get("grade", 0.0), perception_s, decel)
        r = red_clearance_s(p["speed_mph"], p["width_ft"], vehicle_ft)
        g = p["min_green_s"]
        phases[name] = {
            "min_green_s": g, "yellow_s": round(y, 2), "red_s": round(r, 2),
            "min_green": steps(g, step_s), "yellow": steps(y, step_s),
            "red": steps(r, step_s),
        }
    return {"name": intersection.get("name", ""), "step_s": step_s,
            "phases": phases, "conflicts": intersection["conflicts"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("intersection", help="intersection JSON file")
    ap.add_argument("--step", type=float, default=1.0, help="step length in seconds (default 1)")
    ap.add_argument("--perception", type=float, default=1.0, help="perception-reaction time, s")
    ap.add_argument("--decel", type=float, default=10.0, help="deceleration rate, ft/s^2")
    ap.add_argument("--vehicle", type=float, default=20.0, help="vehicle length, ft")
    args = ap.parse_args()
    with open(args.intersection) as f:
        intersection = json.load(f)
    json.dump(timing(intersection, args.step, args.perception, args.decel, args.vehicle),
              sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
