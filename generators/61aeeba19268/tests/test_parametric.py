"""Behavioral contract for the sweep-then-drop native family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "61aeeba19268"
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
    assert adapter.program({"mode": "sweep_only"}) == _canonical_program()
    assert adapter.program({"mode": "sweep_then_drop"}) != _canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": ["sweep_only", "sweep_then_drop"]}
    assert contract["default"] == {"mode": "sweep_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 2


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_inputs_are_matched_distinct_and_include_substantive_30x30(demos: int):
    adapter = _load("adapter")
    canonical = adapter.generate(317, {"mode": "sweep_only"}, demos, 4)
    sequential = adapter.generate(317, {"mode": "sweep_then_drop"}, demos, 4)
    assert len(canonical["train"]) == demos
    assert len(canonical["test"]) == 4
    left = _pairs(canonical)
    right = _pairs(sequential)
    assert [p["input"] for p in left] == [p["input"] for p in right]
    assert len({json.dumps(p["input"], separators=(",", ":")) for p in left}) == demos + 4
    assert all(a["output"] != b["output"] for a, b in zip(left, right, strict=True))
    stress = [p for p in canonical["test"] if len(p["input"]) == len(p["input"][0]) == 30]
    assert len(stress) == 1
    assert sum(v not in (0, 7) for row in stress[0]["output"] for v in row) >= 80


def test_stage_a_selects_one_newly_adjacent_cue_and_stage_b_uses_its_location():
    adapter = _load("adapter")
    family = _load("family")
    locations = set()
    for seed in range(12):
        episode = adapter.generate(seed, {"mode": "sweep_then_drop"}, 2, 4)
        for pair in _pairs(episode):
            info = family.analyze(pair["input"])
            cue = tuple(info["selected_cue"])
            locations.add(cue)
            assert info["original_adjacent_cues"] == []
            assert len(info["stage_a_adjacent_cues"]) == 1
            assert pair["output"] == family.solve(pair["input"], "sweep_then_drop")
            stage_a = family.solve(pair["input"], "sweep_only")
            assert stage_a != pair["output"]
            r, c = cue
            source = info["source_color"]
            assert all(pair["output"][rr][c] == source for rr in range(r, len(pair["output"])))
    assert len(locations) >= 8


def test_minimum_demos_defeat_named_shortcuts():
    adapter = _load("adapter")
    family = _load("family")
    for seed in range(24):
        episode = adapter.generate(seed, {"mode": "sweep_then_drop"}, 2, 4)
        train = episode["train"]
        assert not all(family.rival_sweep_only(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_original_adjacency(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_rightmost_cue(p["input"]) == p["output"] for p in train)
        assert not all(family.rival_fixed_w_minus_2(p["input"]) == p["output"] for p in train)


@pytest.mark.parametrize(
    "call",
    [
        lambda a: a.program({"mode": True}),
        lambda a: a.program({"mode": "unknown"}),
        lambda a: a.generate(True, {"mode": "sweep_only"}, 2, 4),
        lambda a: a.generate(0, {"mode": "sweep_only"}, True, 4),
        lambda a: a.generate(0, {"mode": "sweep_only"}, 2, True),
        lambda a: a.generate(0, {"mode": "sweep_only"}, 1, 4),
        lambda a: a.generate(0, {"mode": "sweep_only"}, 2, 3),
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
