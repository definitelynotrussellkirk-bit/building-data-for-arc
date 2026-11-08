"""Regressions for the opt-in gravity/line-clear family, not production sampling."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace/parametric/prototype.py"
MODES = ("fall", "fall_then_clear", "clear_then_fall")
INPUT = [
    [1, 1, 1, 1, 1],
    [1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0],
    [1, 0, 0, 0, 1],
    [0, 1, 0, 1, 0],
]
ZERO = [0, 0, 0, 0, 0]
BAR = [1, 1, 0, 1, 0]
FULL = [1, 1, 1, 1, 1]
EXPECTED = {
    "fall": [ZERO, ZERO, BAR, FULL, FULL],
    "fall_then_clear": [ZERO, ZERO, ZERO, ZERO, BAR],
    "clear_then_fall": [ZERO, ZERO, ZERO, BAR, FULL],
}


@pytest.fixture(scope="module")
def proto():
    assert PROTO.is_file(), "The native parametric implementation has not been built"
    spec = importlib.util.spec_from_file_location("gravity_clear_test_prototype", PROTO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    root = find_root(HOME)
    runtime = root / "shared/runtime"
    with _local_imports(runtime, runtime):
        apply, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket" and identity["protected"] is True
        try:
            yield apply
        finally:
            bridge.close()


@pytest.mark.parametrize("mode", MODES)
def test_order_has_literal_noncommuting_racket_answers(proto, racket, mode):
    original = copy.deepcopy(INPUT)
    assert proto.transform(INPUT, mode) == EXPECTED[mode]
    assert racket(proto.program({"mode": mode}), INPUT) == EXPECTED[mode]
    assert INPUT == original


def test_default_keeps_exact_canonical_program(proto):
    root = find_root(HOME)
    row = next(json.loads(line) for line in canonical_path(root).read_text().splitlines()
               if json.loads(line)["task_id"] == "8811ea806605")
    assert proto.program({"mode": "fall"}) == row["program_solution"]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("size,value", [(5, 0), (5, 1), (30, 0), (30, 1)])
def test_totality_when_every_row_or_no_row_is_cleared(proto, racket, mode, size, value):
    grid = [[value] * size for _ in range(size)]
    output_value = value if mode == "fall" else 0
    want = [[output_value] * size for _ in range(size)]
    assert proto.transform(grid, mode) == want
    assert racket(proto.program({"mode": mode}), grid) == want


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("demos,queries", [(3, 1), (3, 4), (6, 8)])
def test_supported_counts_produce_distinct_identified_typed_pairs(proto, mode, demos, queries):
    episode = proto.generate(17, {"mode": mode}, demos, queries)
    assert len(episode["train"]) == demos and len(episode["test"]) == queries
    pairs = episode["train"] + episode["test"]
    keys = [json.dumps(pair["input"]) for pair in pairs]
    assert len(set(keys)) == len(keys)
    for pair in pairs:
        for grid in (pair["input"], pair["output"]):
            assert 5 <= len(grid) <= 30 and 5 <= len(grid[0]) <= 30
            assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
            assert all(type(x) is int and x in (0, 1) for row in grid for x in row)
    certificate = proto.teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], {"mode": mode})
    assert certificate["ok"] and certificate["unique_setting"]
    assert certificate["surviving_modes"] == [mode]


def test_count_and_setting_choices_cannot_encode_rule_in_inputs(proto):
    episodes = [proto.generate(103, {"mode": mode}, 3, 4) for mode in MODES]
    for split in ("train", "test"):
        inputs = [[pair["input"] for pair in ep[split]] for ep in episodes]
        assert inputs[0] == inputs[1] == inputs[2]
    short = proto.generate(103, {"mode": "fall"}, 3, 1)
    long = proto.generate(103, {"mode": "fall"}, 6, 8)
    assert short["train"] == long["train"][:3]
    assert short["test"] == long["test"][:1]
    four = proto.generate(103, {"mode": "fall"}, 3, 4)
    assert proto.public_view(short, 0) == proto.public_view(four, 0)
    visible = json.loads(proto.public_view(long, 0))
    assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}


def test_maximum_canvas_has_content_at_all_four_edges(proto, racket):
    for mode in MODES:
        ep = proto.generate(0, {"mode": mode}, 3, 4)
        pair = ep["test"][3]
        grid = pair["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        assert all(any(row) for row in grid)
        assert all(any(row[c] for row in grid) for c in range(30))
        assert any(grid[0]) and any(grid[-1])
        assert any(row[0] for row in grid) and any(row[-1] for row in grid)
        assert 200 <= sum(map(sum, grid)) <= 800
        assert racket(ep["program_solution"], grid) == pair["output"]


def test_teaching_checker_rejects_demo_only_ambiguity_before_novel_query(proto):
    # Empty columns prevent both kinds of clearing: these demos teach only fall.
    weak = [[1, 0, 1, 0, 0], [0, 1, 0, 0, 0], ZERO, [1, 0, 0, 0, 0], ZERO]
    train = [{"input": weak, "output": proto.transform(weak, "fall")}]
    result = proto.teaching_certificate(train, [INPUT], {"mode": "fall"})
    assert result["surviving_modes"] == list(MODES)
    assert result["ok"] is False
    assert result["query_disagreements"][0]["modes"] == ["fall_then_clear", "clear_then_fall"]
    equivalent = proto.teaching_certificate(train, [weak], {"mode": "fall"})
    assert equivalent["ok"] is True and equivalent["unique_setting"] is False


@pytest.mark.parametrize("row_range", ["(range 1 h)", "(range (- h 1))", "(range 1 (- h 1))"])
def test_demos_reject_clearing_only_interior_or_one_border_rows(proto, racket, row_range):
    rival = """(rule!
      (lambda (g)
        (let ((k (count-where
                   (lambda (r)
                     (= (count-where (lambda (c) (= (at g r c) 1)) (range w)) w))
                   ROW_RANGE)))
          (grid-from-fn h w (lambda (r c)
            (let ((n (- (count-where (lambda (rr) (= (at g rr c) 1)) (range h)) k)))
              (if (>= r (- h n)) 1 0)))))))""".replace("ROW_RANGE", row_range)
    ep = proto.generate(0, {"mode": "clear_then_fall"}, 3, 4)
    assert any(racket(rival, pair["input"]) != pair["output"] for pair in ep["train"])


def test_public_bytes_ignore_private_metadata_and_future_answers(proto):
    ep = proto.generate(0, {"mode": "fall_then_clear"}, 3, 4)
    expected = proto.public_view(ep, 0)
    altered = copy.deepcopy(ep)
    altered.update(seed=987, settings={"mode": "bogus"}, program_solution="private")
    for pair in altered["test"]:
        pair["output"] = [[9]]
    for pair in altered["test"][1:]:
        pair["input"] = [[8]]
    assert proto.public_view(altered, 0) == expected
    assert expected == public_challenge_bytes({"train": ep["train"], "test": ep["test"][:1]})


@pytest.mark.parametrize("settings", [{}, {"mode": "up"}, {"mode": True}, {"mode": "fall", "x": 1}, None])
def test_unknown_settings_are_not_silently_ignored(proto, settings):
    with pytest.raises(ValueError):
        proto.generate(0, settings, 3, 4)


@pytest.mark.parametrize("demos,queries", [(2, 4), (7, 4), (3, 0), (3, 9), (True, 4), (3, 4.0)])
def test_unsupported_or_inexact_counts_fail_loudly(proto, demos, queries):
    with pytest.raises(ValueError):
        proto.generate(0, {"mode": "fall"}, demos, queries)


@pytest.mark.parametrize("bad", [True, 1.0, "1"])
def test_inexact_colors_are_rejected(proto, bad):
    grid = copy.deepcopy(INPUT)
    grid[0][0] = bad
    with pytest.raises(ValueError):
        proto.transform(grid, "fall")
