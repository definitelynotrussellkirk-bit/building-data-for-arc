"""Focused contract tests for the native parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "99d71aabd753"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
SETTINGS = [
    {"alignment": alignment, "measure": measure}
    for alignment in ("right", "left")
    for measure in ("objects", "cells")
]


def _load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row["program_solution"])
    assert len(set(rows)) == 1
    return rows[0]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def test_sources_contract_and_exact_canonical_default() -> None:
    prototype = _load("prototype")
    adapter = _load("adapter")
    contract = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert contract["adapter"] == f"generators/{TASK_ID}/workspace/parametric/adapter.py"
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}
    assert contract["default"] == {"alignment": "right", "measure": "objects"}
    assert adapter.program(contract["default"]) == _canonical_source()
    programs = {adapter.program(setting) for setting in SETTINGS}
    assert len(programs) == 4
    assert prototype.program_for("objects", "right") == _canonical_source()


def test_inputs_are_setting_independent_distinct_and_boundary_bearing() -> None:
    adapter = _load("adapter")
    episodes = [adapter.generate(31, setting, 2, 4) for setting in SETTINGS]
    visible_inputs = [
        [_key(pair["input"]) for pair in episode["train"] + episode["test"]]
        for episode in episodes
    ]
    assert all(inputs == visible_inputs[0] for inputs in visible_inputs[1:])
    assert len(set(visible_inputs[0])) == 6
    boundary = episodes[0]["test"][-1]["input"]
    assert len(boundary) == len(boundary[0]) == 30
    assert sum(cell != 0 for row in boundary for cell in row) >= 30
    assert any(cell != 0 for cell in boundary[0])
    assert any(cell != 0 for cell in boundary[-1])
    assert any(row[0] != 0 for row in boundary)
    assert any(row[-1] != 0 for row in boundary)


def test_two_demonstrations_identify_every_setting_and_queries_vary() -> None:
    adapter = _load("adapter")
    episodes = {tuple(sorted(setting.items())): adapter.generate(83, setting, 2, 4) for setting in SETTINGS}
    demo_signatures = {
        key: tuple(_key(pair["output"]) for pair in episode["train"])
        for key, episode in episodes.items()
    }
    assert len(set(demo_signatures.values())) == 4
    for episode in episodes.values():
        outputs = {_key(pair["output"]) for pair in episode["train"] + episode["test"]}
        assert len(outputs) >= 5


def test_exact_requested_counts_and_total_validation() -> None:
    adapter = _load("adapter")
    for demos in (2, 6):
        episode = adapter.generate(107 + demos, SETTINGS[0], demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(SETTINGS[0])
    for bad in (1, 7, True, 2.0):
        with pytest.raises(ValueError):
            adapter.generate(1, SETTINGS[0], bad, 4)
    for bad in (3, 5, True):
        with pytest.raises(ValueError):
            adapter.generate(1, SETTINGS[0], 2, bad)
    with pytest.raises(ValueError):
        adapter.program({"alignment": "right", "measure": "objects", "extra": 1})
    with pytest.raises(ValueError):
        adapter.program({"alignment": "center", "measure": "objects"})
    with pytest.raises(ValueError):
        adapter.program({"alignment": "right", "measure": "area"})


def test_every_scene_refutes_rank_step_and_object_cell_aliases() -> None:
    prototype = _load("prototype")
    samples = prototype.sample_inputs(211, 10)
    for grid in samples:
        object_counts = sorted(prototype.component_counts(grid).values(), reverse=True)
        assert any(a - b > 1 for a, b in zip(object_counts, object_counts[1:]))
        object_right = prototype.python_output(grid, measure="objects", alignment="right")
        cell_right = prototype.python_output(grid, measure="cells", alignment="right")
        assert object_right != cell_right
        assert prototype.rank_step_output(grid) != object_right
