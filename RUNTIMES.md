# Execution times and machine configuration

Notes for the presentation: how long each stage took, and on what. All numbers below were measured on 12 November 2026. Tables with the raw values are in `results/`.

## Machine

| | |
|---|---|
| Computer | laptop, Intel Core Ultra 7 258V, 8 cores (no hyper-threading), up to 4.8 GHz |
| Memory | 30 GB |
| Host OS | Ubuntu 26.04.1 LTS, Linux 7.0.0 |
| Container | Docker 29.8.2, image based on Debian 13 (trixie) |

## Software (inside the container)

| Tool | Version | Used for |
|---|---|---|
| Spot `ltlsynt` | 2.16.2 | LTL synthesis |
| Slugs | commit `ac09bf6` (built from source, CUDD 3.0.0) | GR(1) synthesis |
| NuSMV | 2.7.1 | model checking |
| Python | 3.13.5, `dd` 0.6.0 | glue tools, BDD-to-circuit conversion |
| Typst | 0.15.1 | report |

## Resource limits

After an early invocation without limits froze the laptop (eight NuSMV processes in parallel, no memory cap), everything executed under hard limits:

- Container: 10 GB memory and 4 cores for most invocations; 20 GB and 7 cores for the final verification invocations.
- Each synthesis stage in the scaling experiment: 300 s and 6 GB.
- Each model-checked property: its own NuSMV process, 3 GB, with the time limit given in the tables below.

An invocation that hits a limit is recorded as a timeout, not dropped.

## Synthesis and circuit conversion (seconds)

From `results/scaling.tsv`. "ltlsynt" is the time to decide realizability of the LTL spec. "Slugs" is the time to solve the GR(1) game and write the strategy. "to circuit" is `bdd2aag.py` turning that strategy into a circuit. Unbounded-wait spec.

| Intersection | Step | ltlsynt | Slugs | Strategy BDD nodes | to circuit | Circuit (latches / gates) |
|---|---|---|---|---|---|---|
| two-phase | 4 s | 0.1 | 0.2 | 798 | 0.3 | 13 / 467 |
| two-phase | 2 s | 0.1 | 0.2 | 1,471 | 0.3 | 15 / 563 |
| two-phase | 1 s | 0.1 | 0.2 | 2,114 | 0.4 | 16 / 632 |
| four-phase | 4 s | 0.1 | 0.3 | 6,988 | 0.9 | 22 / 1,357 |
| four-phase | 2 s | 0.1 | 0.4 | 35,028 | 2.4 | 26 / 2,781 |
| four-phase | 1 s | 0.1 | 0.6 | 60,918 | 4.0 | 29 / 3,614 |
| six-phase | 4 s | 0.2 | 1.2 | 354,297 | 38.4 | 32 / 6,242 |
| six-phase | 2 s | 0.2 | 1.5 | 1,608,466 | timeout (300 s) | - |
| six-phase | 1 s | 0.7 | 1.8 | 1,556,021 | 163.5 | 42 / 15,742 |
| NEMA eight-phase | 4 s | 1.6 | 13.9 | 4,006,405 | timeout (300 s) | - |
| NEMA eight-phase | 2 s | 4.6 | 63.4 | 18,081,167 | timeout (300 s) | - |
| NEMA eight-phase | 1 s | 18.9 | timeout (300 s) | - | - | - |

Other measurements:

- Full `ltlsynt` synthesis (circuit, not just realizability) of the NEMA eight-phase controller at 4 s steps: 4 s, giving 10 latches and 306,814 gates.
- A separate attempt to convert the eight-phase Slugs strategy at 4 s steps with an 8 GB limit was stopped after 2,400 s without finishing.

## Model checking with NuSMV

Wall-clock time for all properties of one controller. The first three columns of limits differ between rows, so compare with care.

| Controller | Properties | Proved | Wall time | Time limit per property | Parallel checks |
|---|---|---|---|---|---|
| two-phase, 4 s | 31 | 31 | 1.2 s | 120 s | 2 |
| two-phase, 2 s | 32 | 32 | 1.6 s | 120 s | 2 |
| two-phase, 1 s | 34 | 34 | 3.2 s | 120 s | 2 |
| two-phase, 1 s, waiting call served within 24 s | 34 | 34 | 323 s | 400 s | 2 |
| four-phase, 4 s | 74 | 74 | 101 s | 120 s | 2 |
| four-phase, 2 s | 77 | 74 | 533 s | 120 s | 2 |
| four-phase, 1 s | 83 | 74 | 1,223 s | 120 s | 2 |
| six-phase, 4 s | 114 | 28 | 1,740 s | 120 s | 6 |
| six-phase, 1 s | 126 | 22 | 2,190 s | 120 s | 6 |

"Proved" counts properties NuSMV confirmed within the limit. For the rows where it is below the number of properties, the scaling table does not record whether the rest timed out or were refuted; see the repeated invocations below.

Repeated invocations with a 600 s limit per property, 6 checks in parallel, container at 20 GB and 7 cores (verdicts by name in `results/verify_four_phase_*.tsv`):

| Controller | Properties | Proved | Slowest property | Wall time |
|---|---|---|---|---|
| four-phase, 2 s | 77 | 77 | 70 s | under 5 min |
| four-phase, 1 s | 83 | 83 | 299 s | about 8 min |

So the four-phase properties left unproved at 120 s were not failures.

Not completed:

- six-phase, 1 s steps: circuit built in 164 s (42 latches, 15,742 gates); 22 of 126 properties proved in 2,190 s (120 s limit, 6 parallel checks).
- six-phase, 2 s steps: strategy of 1,608,466 BDD nodes; conversion to a circuit timed out at 300 s.
- The unproved six-phase properties were not repeated with a longer limit, so it is not known whether they hold.
- NEMA eight-phase (the 306,814-gate `ltlsynt` circuit): only a three-property trial was executed. NuSMV proved one conflict property and then exhausted its 5 GB memory limit. A full invocation was started and cancelled.

## Smallest waiting bound (bisection)

From `results/minwait.tsv`; each solver had 300 s per intersection and step.

| Intersection | Step | Hand formula | Slugs | ltlsynt |
|---|---|---|---|---|
| two-phase | 4 s | 8 steps | 8 | 8 |
| two-phase | 2 s | 13 | 13 | 13 |
| two-phase | 1 s | 24 | 24 | 24 |
| four-phase | 4 s | 15 | 15 | timeout |
| four-phase | 2 s | 27 | 27 | timeout |
| four-phase | 1 s | 49 | timeout | timeout |

The bisection for the two-phase intersection took 1 to 3 s per step size with either solver in earlier invocations.

## Things that were fast

- The 105 Slugs invocations behind the realizability map (two-phase, 1 s steps) were not timed individually; a single such invocation takes well under a second (0.2 s in the table above).
- Reading and checking the one-hour UDOT log (24,485 events): under a second.
- The test suite: 15 tests in about 1 s.
