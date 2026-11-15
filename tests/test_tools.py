"""Fast checks of the pieces that need no solver."""
import io

import aiger
import atspm
import genspec
import smvtrace
import timing


def test_yellow_follows_the_ite_formula():
    # 1.0 + 1.47 * 45 / (2 * 10) = 4.31 s on level ground
    assert round(timing.yellow_s(45), 2) == 4.31
    assert timing.yellow_s(45, grade=-0.04) > timing.yellow_s(45)      # downhill needs more


def test_yellow_is_kept_in_the_mutcd_range():
    assert timing.yellow_s(15) == 3.0
    assert timing.yellow_s(80) == 6.0


def test_intervals_round_up_to_whole_steps():
    t = timing.timing({"phases": {"a": {"speed_mph": 45, "width_ft": 60, "min_green_s": 10}},
                       "conflicts": []}, step_s=2.0)["phases"]["a"]
    assert (t["yellow"], t["red"], t["min_green"]) == (3, 1, 5)     # 4.31 s, 1.21 s, 10 s


def test_formula_helpers():
    assert genspec.hold("a", 3) == "(a & X((a & X(a))))"
    assert genspec.within("a", 1) == "(a | X(a))"
    assert genspec.X("a", 2) == "X(X(a))"


AND_WITH_MEMORY = """aag 3 1 1 1 1
2
4 6
6
6 2 5
i0 x
o0 y
"""   # y = x and not latch; latch' = y


def test_circuit_step_and_round_trip():
    c = aiger.parse(AND_WITH_MEMORY)
    out, state = aiger.step(c, None, {"x": 1})
    assert out == {"y": True}
    out, state = aiger.step(c, state, {"x": 1})
    assert out == {"y": False}
    assert aiger.parse(aiger.dump(c)) == c


def test_log_intervals():
    events = [(0.0, atspm.CALL_ON, 2), (5.0, atspm.GREEN, 2), (15.0, atspm.YELLOW, 2),
              (19.0, atspm.RED_CLEARANCE, 2), (21.0, atspm.END, 2)]
    assert list(atspm.intervals(events)) == [
        (2, "wait", 0.0, 5.0), (2, "green", 5.0, 10.0),
        (2, "yellow", 15.0, 4.0), (2, "red_clearance", 19.0, 2.0)]


def test_log_reader_orders_events_and_counts_from_zero():
    text = "timestamp,code,param\n2017-10-17T17:00:02.5,8,2\n2017-10-17T17:00:01,1,2\n"
    assert atspm.read(io.StringIO(text)) == [(0.0, 1, 2), (1.5, 8, 2)]


def test_counterexample_trace_keeps_unchanged_values():
    text = """-- specification G !g is false
Trace Type: Counterexample
  -> State: 1.1 <-
    g = FALSE
    t = 0
  -> State: 1.2 <-
    t = 1
  -- Loop starts here
  -> State: 1.3 <-
    g = TRUE
"""
    (trace,) = smvtrace.traces(text)
    assert [s["g"] for s in trace] == ["FALSE", "FALSE", "TRUE"]
    assert [s["loop"] for s in trace] == ["FALSE", "FALSE", "TRUE"]
