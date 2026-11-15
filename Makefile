# Synthesize, verify and simulate a signal controller for one intersection.
# Run inside the container:  docker compose run --rm dev make
#
#   make                         two-phase intersection, 1 s steps
#   make I=nema8 STEP=2          another intersection / step length
#   make MAX_WAIT=24             bound the waiting time (seconds)
#   make test                    run the test suite
#   make experiments             regenerate results/ and figures/  (slow)
#   make clean                   delete build/
#
# How to read a Makefile
# ----------------------
# A rule has the form
#
#     target: inputs
#     <TAB>command
#
# and means: "to make the file `target`, first make sure the `inputs` exist
# and are up to date, then run the command". make only reruns a command when
# the target is missing or older than one of its inputs, so a second `make`
# after a finished one does nothing.
#
# Inside a command:
#     $@   the target of the rule
#     $<   the first input
#     $^   all inputs
#     $(NAME)   the value of the variable NAME
# A command line starting with @ is run without being printed first.

# --- Settings ---------------------------------------------------------------
# `?=` gives a default that the command line overrides: `make STEP=2`.

# intersection: the name of a file in intersections/, without .json
I        ?= two_phase
# length of one time step, in seconds
STEP     ?= 1
# longest wait to guarantee, in seconds; empty means "eventually"
MAX_WAIT ?=
# how many properties NuSMV checks at the same time (each can use gigabytes)
JOBS     ?= 2
# time limit per property, in seconds
TIMEOUT  ?= 900
# simulation: chance per step that a call arrives on each phase
ARRIVALS ?= 0.10
# simulation: number of steps
STEPS    ?= 180

# --- Derived names ----------------------------------------------------------
# `:=` computes the value once, here.

T := tools

# Every output file starts with this prefix, so runs with different settings
# do not overwrite each other, for example build/two_phase-1s or
# build/two_phase-1s-w24.  $(if X,Y) gives Y when X is not empty.
B := build/$(I)-$(STEP)s$(if $(MAX_WAIT),-w$(MAX_WAIT))

# option passed to both spec generators when a waiting bound is set
SPEC_OPTS := $(if $(MAX_WAIT),--max-wait $(MAX_WAIT))

# the phase names of the intersection, read from its JSON file ("ns ew")
PHASES := $(shell python3 -c "import json;print(' '.join(json.load(open('intersections/$(I).json'))['phases']))")

# --- What `make` builds ------------------------------------------------------
# The first rule in the file is the default.  It has no command; it only says
# that "all" needs the verification table and the timeline picture, and the
# rules below say how to make each of them.

all: $(B).verify.tsv $(B).png

# --- The pipeline, one rule per step ----------------------------------------

# intersection -> interval lengths (yellow, red clearance, ...) in steps
$(B).timing.json: intersections/$(I).json
	@mkdir -p build
	python3 $(T)/timing.py $< --step $(STEP) > $@

# timing -> LTL spec.  This is the spec that gets verified.
$(B).spec.json: $(B).timing.json
	python3 $(T)/genspec.py $< $(SPEC_OPTS) > $@

# timing -> GR(1) spec for Slugs.  This is the spec that gets synthesized.
$(B).slugs: $(B).timing.json
	python3 $(T)/gr1spec.py $< $(SPEC_OPTS) > $@

# GR(1) spec -> winning strategy, as a BDD (runs Slugs)
$(B).bdd: $(B).slugs
	python3 $(T)/gr1synth.py $< > $@

# strategy -> circuit (AIGER format)
$(B).aag: $(B).bdd
	python3 $(T)/bdd2aag.py $< > $@

# circuit -> NuSMV model
$(B).smv: $(B).aag
	python3 $(T)/aag2smv.py $< > $@

# model + LTL spec -> one line per property: name, verdict, seconds.
# `; cat $@` also prints the table to the terminal.
$(B).verify.tsv: $(B).smv $(B).spec.json
	python3 $(T)/verify.py $^ -j $(JOBS) --timeout $(TIMEOUT) > $@; cat $@

# circuit -> simulated run under random arrivals.
# $(foreach p,LIST,TEXT) repeats TEXT for each item of LIST, which gives
# one "call_<phase>=<probability>" argument per phase.  The trailing
# backslash continues the command on the next line.
$(B).csv: $(B).aag
	python3 $(T)/arrivals.py $(foreach p,$(PHASES),call_$(p)=$(ARRIVALS)) --steps $(STEPS) \
	  | python3 $(T)/simulate.py $< > $@

# simulated run -> timeline picture
$(B).png: $(B).csv
	python3 $(T)/plot_timeline.py -o $@ --step $(STEP) < $<

# --- Other commands -----------------------------------------------------------

test:
	python3 -m pytest -q tests

experiments:
	sh experiments/run_all.sh

clean:
	rm -rf build

# These targets are commands, not files: always run them when asked.
.PHONY: all test experiments clean

# If a command fails, delete its half-written target so the next `make` does
# not mistake it for a finished file.
.DELETE_ON_ERROR:
