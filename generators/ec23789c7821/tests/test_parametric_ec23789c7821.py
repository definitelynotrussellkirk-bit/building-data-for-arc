"""Behavioral tests for the native vertical/plus family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "ec23789c7821"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def _load():
    assert PROTOTYPE.is_file(), "task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_ec23789c7821", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load()


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=60) as runtime:
        yield runtime


def _canonical() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(sources) == 1
    return sources.pop()


def _apply(bridge, source, grid):
    bridge.eval_text(f"(define ec-rule-under-test {wrap_rule(source)})")
    bridge.define_grid("ec-grid-under-test", grid)
    return bridge.eval_text("(ec-rule-under-test ec-grid-under-test)")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_is_byte_exact_canonical_and_plus_names_both_stages(proto):
    assert proto.program({"finish": "vertical"}) == _canonical()
    plus = proto.program({"finish": "plus"})
    assert plus != _canonical()
    assert "canonical-intermediate" in plus
    assert "exact vertical triples" in plus


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_inputs_uniqueness_and_demo_only_identification(proto, demos):
    vertical = proto.generate(17, {"finish": "vertical"}, demos=demos, queries=4)
    plus = proto.generate(17, {"finish": "plus"}, demos=demos, queries=4)
    assert len(vertical["train"]) == len(plus["train"]) == demos
    assert len(vertical["test"]) == len(plus["test"]) == 4
    assert _inputs(vertical) == _inputs(plus)
    assert len({proto.digest(grid) for grid in _inputs(vertical)}) == demos + 4
    assert vertical["certificate"]["survivors"] == [{"finish": "vertical"}]
    assert plus["certificate"]["survivors"] == [{"finish": "plus"}]
    assert any(a["output"] != b["output"] for a, b in zip(vertical["train"], plus["train"]))


def test_prefixes_are_count_independent(proto):
    short = proto.generate(31, {"finish": "vertical"}, demos=2, queries=1)
    long = proto.generate(31, {"finish": "vertical"}, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]


def test_preserved_distractors_and_composed_geometry(proto):
    grid = [
        [4, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 8, 0],
        [0, 0, 0, 0, 0, 8, 0],
        [0, 0, 6, 6, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    intermediate = proto.canonical_transform(grid)
    final = proto.transform(grid, {"finish": "plus"})
    assert intermediate[0][0] == 4
    assert intermediate[1][5] == intermediate[2][5] == 8
    assert intermediate[3][2:4] == [6, 6]
    assert final == proto.plus_from_intermediate(intermediate)
    assert final != intermediate
    assert final[1][1:4] == [2, 2, 2]


def test_both_settings_match_protected_racket_including_30_square(proto, bridge):
    for finish in ("vertical", "plus"):
        episode = proto.generate(23, {"finish": finish}, demos=2, queries=4)
        for pair in episode["train"] + episode["test"]:
            assert _apply(bridge, episode["program_solution"], pair["input"]) == pair["output"]
    stress = proto.generate(23, {"finish": "plus"}, demos=2, queries=4)["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    counts = [
        sum(value != 0 for row in stress["output"][r:r+15] for value in row[c:c+15])
        for r in (0, 15) for c in (0, 15)
    ]
    assert min(counts) >= 5

    minimum = proto.sample_input(29, "minimum-racket", 0, 7, 7)
    for finish in ("vertical", "plus"):
        source = proto.program({"finish": finish})
        assert _apply(bridge, source, minimum) == proto.transform(minimum, {"finish": finish})


def test_skip_a_counterfactual_changes_the_second_stage(proto):
    grid = proto.sample_input(5, "witness", 0, 15, 17)
    intermediate = proto.canonical_transform(grid)
    final = proto.plus_from_intermediate(intermediate)
    skipped = proto.plus_from_intermediate(grid)
    assert final != skipped
    assert proto.transform(grid, {"finish": "plus"}) == final


@pytest.mark.parametrize("shape", [(7, 7), (8, 7), (7, 8), (9, 8)])
def test_sampler_honors_declared_minimum_rectangles(proto, shape):
    grid = proto.sample_input(37, "minimum", 0, *shape)
    assert (len(grid), len(grid[0])) == shape
    assert len(proto._target_windows(grid)) >= 2
    assert proto.transform(grid, {"finish": "vertical"}) != proto.transform(
        grid, {"finish": "plus"}
    )


def test_certificate_rejects_duplicate_inputs(proto):
    episode = proto.generate(41, {"finish": "plus"}, demos=2, queries=4)
    episode["test"][1] = {
        "input": [row[:] for row in episode["test"][0]["input"]],
        "output": [row[:] for row in episode["test"][0]["output"]],
    }
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(episode)


def test_certificate_enforces_declared_counts(proto):
    episode = proto.generate(43, {"finish": "vertical"}, demos=2, queries=4)
    episode["train"] = episode["train"][:1]
    with pytest.raises(ValueError, match="demonstration count"):
        proto.certify(episode)


@pytest.mark.parametrize(
    "payload",
    [
        {"seed": True, "settings": {"finish": "vertical"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"finish": "wrong"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"finish": "vertical", "extra": 1}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"finish": "vertical"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"finish": "vertical"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_fail_closed(proto, payload):
    with pytest.raises(ValueError):
        proto.generate(**payload)
