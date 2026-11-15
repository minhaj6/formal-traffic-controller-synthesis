"""The two synthesis routes must agree.  Needs ltlsynt and slugs (the container)."""
import json
import os
import shutil

import pytest

import genspec
import gr1spec
import gr1synth
import synth
import timing

pytestmark = pytest.mark.skipif(not (shutil.which("ltlsynt") and shutil.which("slugs")),
                                reason="needs ltlsynt and slugs")
ROOT = os.path.dirname(os.path.dirname(__file__))


def two_phase(step_s=4.0):
    with open(os.path.join(ROOT, "intersections", "two_phase.json")) as f:
        return timing.timing(json.load(f), step_s)


@pytest.mark.parametrize("options, expected", [
    ({}, True),
    ({"max_wait_s": 32}, True),                      # 8 steps: the minimum
    ({"max_wait_s": 28}, False),
    ({"locking": True}, True),
    ({"locking": True, "drop": ["call_persists"]}, False),
    ({"extend": True}, True),
    ({"extend": True, "drop": ["queue_clears"]}, False),
])
def test_both_solvers_agree(options, expected):
    t = two_phase()
    assert synth.realizable(genspec.spec(t, **options)) == expected
    assert gr1synth.realizable(gr1spec.spec(t, **options)) == expected
