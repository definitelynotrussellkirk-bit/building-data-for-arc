"""Behavioral contract for the connect-then-mark-crossings native family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "6c08e545720f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def _pairs(episode: dict) -> list[dict]:
    return [*episode["train"], *episode["test"]]


def test_default_program_is_exact_canonical_and_contract_is_finite():
    adapter = _load("adapter")
    assert adapter.program({"mode": "connect_only"}) == _canonical_program()
    assert adapter.program({"mode": "connect_then_mark_crossings"}) != _canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {
        "mode": ["connect_only", "connect_then_mark_crossings"]
    }
    assert contract["default"] == {"mode": "connect_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 2


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_inputs_are_matched_distinct_and_include_30x30_crossing_stress(demos: int):
    adapter = _load("adapter")
    family = _load("family")
    canonical = adapter.generate(911, {"mode": "connect_only"}, demos, 4)
    sequential = adapter.generate(911, {"mode": "connect_then_mark_crossings"}, demos, 4)
    left = _pairs(canonical)
    right = _pairs(sequential)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    assert [p["input"] for p in left] == [p["input"] for p in right]
    assert len({json.dumps(p["input"], separators=(",", ":")) for p in left}) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(left, right, strict=True))
    stress = [p for p in canonical["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert len(stress) == 1
    info = family.analyze(stress[0]["input"])
    assert len(info["crossings"]) >= 2
    assert sum(v != 7 for row in stress[0]["output"] for v in row) >= 45


def test_stage_a_creates_crossings_and_stage_b_marks_them_with_singleton_cue_color():
    adapter = _load("adapter")
    family = _load("family")
    cue_colors = set()
    crossing_locations = set()
    for seed in range(12):
        episode = adapter.generate(seed, {"mode": "connect_then_mark_crossings"}, 2, 4)
        for pair in _pairs(episode):
            info = family.analyze(pair["input"])
            cue = int(info["cue_color"])
            cue_colors.add(cue)
            crossings = [tuple(cell) for cell in info["crossings"]]
            crossing_locations.update(crossings)
            assert info["input_crossings"] == []
            assert crossings
            assert pair["output"] == family.solve(pair["input"], "connect_then_mark_crossings")
            assert all(pair["output"][r][c] == cue for r, c in crossings)
            assert family.solve(pair["input"], "connect_only") != pair["output"]
    assert len(cue_colors) >= 4
    assert len(crossing_locations) >= 12


def test_minimum_demos_defeat_named_shortcuts():
    adapter = _load("adapter")
    family = _load("family")
    for seed in range(24):
        episode = adapter.generate(seed, {"mode": "connect_then_mark_crossings"}, 2, 4)
        train = episode["train"]
        assert not all(family.rival_connect_only(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_fixed_zero(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_pair_midpoints(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_input_crossings(p["input"]) == p["output"] for p in train)


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.program({"mode": True}),
        lambda a: a.program({"mode": "unknown"}),
        lambda a: a.generate(True, {"mode": "connect_only"}, 2, 4),
        lambda a: a.generate(0, {"mode": "connect_only"}, True, 4),
        lambda a: a.generate(0, {"mode": "connect_only"}, 2, True),
        lambda a: a.generate(0, {"mode": "connect_only"}, 1, 4),
        lambda a: a.generate(0, {"mode": "connect_only"}, 2, 3),
    ],
)
def test_adapter_rejects_out_of_contract_values(call):
    adapter = _load("adapter")
    with pytest.raises(ValueError):
        call(adapter)


def test_bounded_audit_reports_zero_named_rival_survivors():
    audit = _load("audit")
    report = audit.audit(seeds=range(16), demo_counts=(2, 3, 6))
    assert report["status"] == "passed"
    assert report["scope"]["episodes_per_setting_pair"] == 48
    assert report["scope"]["thirty_by_thirty_queries"] == 48
    assert all(row["demo_episodes_survived"] == 0 for row in report["named_rivals"].values())


def test_stage_a_uses_canonical_numeric_color_order_at_crossing():
    family = _load("family")
    grid = [[7 for _ in range(11)] for _ in range(11)]
    # Color 8 appears first in row-major input order, but the canonical objects
    # traversal processes numeric colors 2 then 8, leaving 8 at the crossing.
    grid[1][9] = 8
    grid[9][1] = 8
    grid[2][2] = 2
    grid[8][8] = 2
    grid[0][0] = 5  # singleton cue, ignored by stage A
    assert family.stage_a(grid)[5][5] == 8
