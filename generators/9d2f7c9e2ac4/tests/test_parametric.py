"""Behavioral contract for the native parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "9d2f7c9e2ac4"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"_{TASK_ID}_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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


def _br_non_source_colors(grid: list[list[int]], source_color: int) -> set[int]:
    split = len(grid) // 2
    return {
        grid[r][c]
        for r in range(split + 1, len(grid))
        for c in range(split + 1, len(grid[0]))
        if grid[r][c] not in (0, 9, source_color)
    }


def _replace(grid: list[list[int]], old: int, new: int) -> list[list[int]]:
    return [[new if value == old else value for value in row] for row in grid]


def test_default_program_is_exact_canonical_and_contract_is_finite():
    adapter = _load("adapter")
    assert adapter.program({"mode": "copy_only"}) == _canonical_program()
    assert adapter.program({"mode": "cue_payload"}) != _canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["parameters"] == {"mode": ["copy_only", "cue_payload"]}
    assert contract["default"] == {"mode": "copy_only"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_distinct_inputs_matched_grammar_and_30x30_query(demos: int):
    adapter = _load("adapter")
    copy_episode = adapter.generate(317, {"mode": "copy_only"}, demos, 4)
    cue_episode = adapter.generate(317, {"mode": "cue_payload"}, demos, 4)
    assert len(copy_episode["train"]) == demos
    assert len(copy_episode["test"]) == 4
    copy_inputs = [pair["input"] for pair in _pairs(copy_episode)]
    cue_inputs = [pair["input"] for pair in _pairs(cue_episode)]
    assert copy_inputs == cue_inputs
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in copy_inputs}
    assert len(fingerprints) == demos + 4
    assert any(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in copy_episode["test"])
    assert all(left["output"] != right["output"] for left, right in zip(_pairs(copy_episode), _pairs(cue_episode)))


def test_cue_is_selected_from_rotated_intermediate_and_varies_across_lessons():
    adapter = _load("adapter")
    family = _load("family")
    selected = set()
    for seed in range(12):
        episode = adapter.generate(seed, {"mode": "cue_payload"}, 3, 4)
        for pair in _pairs(episode):
            info = family.analyze(pair["input"])
            selected.add(info["selected_cue_color"])
            stage_a = family.solve(pair["input"], "copy_only")
            assert pair["output"] == _replace(stage_a, info["selected_cue_color"], info["source_color"])
            assert info["selected_cue_color"] in _br_non_source_colors(pair["input"], info["source_color"])
            assert info["remote_payload_count"] >= 2
    assert len(selected) >= 4


def test_fixed_lowest_cue_and_no_postprocess_shortcuts_fail_visible_demos():
    adapter = _load("adapter")
    family = _load("family")
    fixed_lowest_survives = 0
    no_postprocess_survives = 0
    for seed in range(20):
        episode = adapter.generate(seed, {"mode": "cue_payload"}, 2, 4)
        low_ok = True
        none_ok = True
        for pair in episode["train"]:
            info = family.analyze(pair["input"])
            stage_a = family.solve(pair["input"], "copy_only")
            cue_colors = _br_non_source_colors(pair["input"], info["source_color"])
            low_rival = _replace(stage_a, min(cue_colors), info["source_color"])
            low_ok &= low_rival == pair["output"]
            none_ok &= stage_a == pair["output"]
        fixed_lowest_survives += int(low_ok)
        no_postprocess_survives += int(none_ok)
    assert fixed_lowest_survives == 0
    assert no_postprocess_survives == 0


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"mode": "unknown"}, 3, 4),
        ({"mode": "copy_only", "extra": True}, 3, 4),
        ({"mode": "copy_only"}, True, 4),
        ({"mode": "copy_only"}, 1, 4),
        ({"mode": "copy_only"}, 7, 4),
        ({"mode": "copy_only"}, 3, 3),
        ({"mode": "copy_only"}, 3, 5),
    ],
)
def test_invalid_settings_and_counts_fail_loudly(settings: dict, demos: int, queries: int):
    adapter = _load("adapter")
    with pytest.raises(ValueError):
        adapter.generate(1, settings, demos, queries)
