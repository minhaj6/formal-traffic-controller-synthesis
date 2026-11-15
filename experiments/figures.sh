#!/bin/sh
# Timeline figures: synthesized controllers and the baseline's counterexample.
set -eu
cd "$(dirname "$0")"
T=../tools
B=../build
mkdir -p $B

# two-phase controller with the tightest waiting bound (24 s at 1 s steps)
python3 $T/timing.py ../intersections/two_phase.json > $B/fig2.timing.json
python3 $T/gr1spec.py $B/fig2.timing.json --max-wait 24 | python3 $T/gr1synth.py \
  | python3 $T/bdd2aag.py > $B/fig2.aag
python3 $T/arrivals.py call_ns=0.12 call_ew=0.06 --steps 180 --seed 3 \
  | python3 $T/simulate.py $B/fig2.aag --lock \
  | python3 $T/plot_timeline.py -o ../figures/timeline_two_phase.png --phases ns,ew

# hand-written fixed-time controller with a short red clearance
python3 $T/genspec.py $B/fig2.timing.json --max-wait 24 > $B/fig2.spec.json
python3 $T/verify.py ../baselines/fixed_time_bug.smv $B/fig2.spec.json -j 1 --log $B/bug.log \
  > /dev/null || true
python3 $T/smvtrace.py --unroll 1 < $B/bug.log \
  | python3 $T/plot_timeline.py -o ../figures/counterexample.png --phases ns,ew --mark 31

# six-phase dual-ring controller at 4 s steps
python3 $T/timing.py ../intersections/six_phase.json --step 4 > $B/fig6.timing.json
python3 $T/gr1spec.py $B/fig6.timing.json | python3 $T/gr1synth.py \
  | python3 $T/bdd2aag.py > $B/fig6.aag
python3 $T/arrivals.py call_p1=0.02 call_p2=0.2 call_p4=0.1 call_p5=0.02 call_p6=0.2 \
    call_p8=0.1 --steps 100 --seed 5 \
  | python3 $T/simulate.py $B/fig6.aag --lock \
  | python3 $T/plot_timeline.py -o ../figures/timeline_six_phase.png --step 4

# NEMA eight-phase controller at 4 s steps, synthesized by ltlsynt from the LTL spec
python3 $T/timing.py ../intersections/nema8.json --step 4 > $B/fig8.timing.json
python3 $T/genspec.py $B/fig8.timing.json | python3 $T/synth.py > $B/fig8.aag
python3 $T/arrivals.py call_p1=0.03 call_p2=0.2 call_p3=0.02 call_p4=0.1 call_p5=0.03 \
    call_p6=0.2 call_p7=0.02 call_p8=0.1 --steps 100 --seed 5 \
  | python3 $T/simulate.py $B/fig8.aag --lock \
  | python3 $T/plot_timeline.py -o ../figures/timeline_nema8.png --step 4
