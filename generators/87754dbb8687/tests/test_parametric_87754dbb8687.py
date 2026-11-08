"""Behavioral tests for the native equality/matched-box family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_path, find_root

TASK_ID = "87754dbb8687"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def _load():
    assert PROTOTYPE.is_file(), "task-local parametric prototype is missing"
    spec = importlib.util.spec_from_file_location("parametric_87754dbb8687", PROTOTYPE)
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
    bridge.eval_text(f"(define rule-under-test {wrap_rule(source)})")
    bridge.define_grid("grid-under-test", grid)
    return bridge.eval_text("(rule-under-test grid-under-test)")


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_default_program_is_byte_exact_canonical_and_alternate_is_composed(proto):
    assert proto.program({"output_mode": "equality"}) == _canonical()
    alternate = proto.program({"output_mode": "match_boxes"})
    assert alternate != _canonical()
    assert "canonical-equality" in alternate
    assert "bbox-of-cells" in alternate


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_setting_independence_uniqueness_and_demo_identification(proto, demos):
    equality = proto.generate(17, {"output_mode": "equality"}, demos=demos, queries=4)
    boxes = proto.generate(17, {"output_mode": "match_boxes"}, demos=demos, queries=4)
    assert len(equality["train"]) == len(boxes["train"]) == demos
    assert len(equality["test"]) == len(boxes["test"]) == 4
    assert _inputs(equality) == _inputs(boxes)
    assert len({proto.digest(grid) for grid in _inputs(equality)}) == demos + 4
    assert equality["certificate"]["survivors"] == [{"output_mode": "equality"}]
    assert boxes["certificate"]["survivors"] == [{"output_mode": "match_boxes"}]
    assert any(a["output"] != b["output"] for a, b in zip(equality["train"], boxes["train"]))


def test_prefixes_do_not_change_with_requested_counts(proto):
    short = proto.generate(29, {"output_mode": "equality"}, demos=2, queries=1)
    long = proto.generate(29, {"output_mode": "equality"}, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]


def test_both_settings_match_protected_racket_including_30_square(proto, bridge):
    for mode in ("equality", "match_boxes"):
        episode = proto.generate(23, {"output_mode": mode}, demos=2, queries=4)
        for pair in episode["train"] + episode["test"]:
            assert _apply(bridge, episode["program_solution"], pair["input"]) == pair["output"]
    stress = proto.generate(23, {"output_mode": "match_boxes"}, demos=2, queries=4)["test"][-1]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    assert (len(stress["output"]), len(stress["output"][0])) == (29, 29)
    quadrants = [
        sum(v != 0 for row in stress["output"][r:r+14] for v in row[c:c+14])
        for r in (0, 15) for c in (0, 15)
    ]
    assert min(quadrants) >= 4


def test_boxes_use_canonical_intermediate_and_change_it(proto):
    grid = proto.sample_input(5, "witness", 0, 12, 13)
    intermediate = proto.transform(grid, {"output_mode": "equality"})
    final = proto.transform(grid, {"output_mode": "match_boxes"})
    assert final != intermediate
    assert proto.match_boxes_from_intermediate(intermediate) == final
    assert any(
        intermediate[r][c] == 0 and final[r][c] != 0
        for r in range(len(final)) for c in range(len(final[0]))
    )


def test_match_boxes_rejects_malformed_intermediates(proto):
    for malformed in ([], [[1], [1, 2]], [[10]], [[True]]):
        with pytest.raises(ValueError):
            proto.match_boxes_from_intermediate(malformed)


def test_certificate_rejects_duplicate_inputs(proto):
    episode = proto.generate(41, {"output_mode": "match_boxes"}, demos=2, queries=4)
    episode["test"][1] = {
        "input": [row[:] for row in episode["test"][0]["input"]],
        "output": [row[:] for row in episode["test"][0]["output"]],
    }
    with pytest.raises(ValueError, match="distinct"):
        proto.certify(episode)


def test_certificate_enforces_declared_counts(proto):
    episode = proto.generate(43, {"output_mode": "equality"}, demos=2, queries=4)
    episode["train"] = episode["train"][:1]
    with pytest.raises(ValueError, match="demonstration count"):
        proto.certify(episode)


@pytest.mark.parametrize(
    "payload",
    [
        {"seed": True, "settings": {"output_mode": "equality"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"output_mode": "wrong"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"output_mode": "equality", "extra": 1}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"output_mode": "equality"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"output_mode": "equality"}, "demos": 2, "queries": 5},
    ],
)
def test_invalid_requests_fail_closed(proto, payload):
    with pytest.raises(ValueError):
        proto.generate(**payload)
