#!/bin/sh
# Regenerate results/ and figures/.  Run inside the container from the project
# root.  The scaling experiment takes the longest (about an hour and a half,
# most of it model checking); every solver run is time- and memory-limited.
#
# Not produced here: results/verify_four_phase_{1,2}s.tsv are the output of
#   make I=four_phase STEP=<1|2> TIMEOUT=600 JOBS=6
# run in a container with 20 GB and 7 cores.
set -eu
cd "$(dirname "$0")"
T=../tools

python3 timing_table.py       > ../results/timing.tsv
python3 minwait.py            > ../results/minwait.tsv
python3 assumptions.py        > ../results/assumptions.tsv
python3 realizability_map.py  > ../results/realizability_map.tsv
python3 scaling.py            > ../results/scaling.tsv

# the public UDOT log
python3 $T/logintervals.py < ../data/udot7185/events.csv \
  | python3 $T/stats.py --by phase,interval --value duration_s > ../results/udot7185_intervals.tsv
python3 $T/checklog.py < ../data/udot7185/events.csv > ../results/udot7185_checks.tsv

# figures
python3 ring_barrier.py ../figures/ring_barrier.png
python3 intersection.py ../figures/intersection.png
typst compile --root .. pipeline.typ ../figures/pipeline.svg   # first use downloads the fletcher package
python3 plot_map.py ../figures/realizability_map.png < ../results/realizability_map.tsv
python3 $T/log2timeline.py --start 240 --end 600 < ../data/udot7185/events.csv \
  | python3 $T/plot_timeline.py -o ../figures/timeline_udot7185.png
sh figures.sh
