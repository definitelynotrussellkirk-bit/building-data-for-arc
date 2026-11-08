"""Native admission tests for the wall-distance scope family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "dc382c7da9a9"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def test_native_adapter_preserves_exact_canonical_program_and_validates_settings():
    assert ADAPTER_PATH.is_file()
    adapter = _load(ADAPTER_PATH, "native_dc382c7da9a9_adapter")
    assert adapter.program({"distance_scope": "all_equidistant"}) == _canonical_program()
    assert adapter.program({"distance_scope": "shortest_path_midpoints"}) != _canonical_program()
    for bad in (None, {}, {"distance_scope": "bad"}, {"distance_scope": 1}, {"distance_scope": "all_equidistant", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def _keys(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_literal_open_room_distinguishes_all_ties_from_shortest_path_midpoint():
    prototype = _load(PROTOTYPE_PATH, "native_dc382c7da9a9_literal")
    grid = [[5] * 9 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 8):
            grid[row][col] = 0
    grid[3][2] = 2
    grid[3][6] = 3
    canonical = [row[:] for row in grid]
    for row in range(1, 6):
        canonical[row][4] = 8
    midpoint = [row[:] for row in grid]
    midpoint[3][4] = 8
    assert prototype.solve(grid, "all_equidistant") == canonical
    assert prototype.solve(grid, "shortest_path_midpoints") == midpoint


def test_native_counts_are_independent_prefix_stable_and_inputs_match_across_settings():
    adapter = _load(ADAPTER_PATH, "native_dc382c7da9a9_counts")
    settings = [
        {"distance_scope": "all_equidistant"},
        {"distance_scope": "shortest_path_midpoints"},
    ]
    full = [adapter.generate(17, value, demos=6, queries=4) for value in settings]
    assert _keys(full[0]) == _keys(full[1])
    assert len(set(_keys(full[0]))) == 10
    for value, complete in zip(settings, full, strict=True):
        for demos in (2, 3, 5):
            short = adapter.generate(17, value, demos=demos, queries=4)
            assert short["train"] == complete["train"][:demos]
            assert short["test"] == complete["test"]
        for queries in (1, 2, 3):
            short = adapter.generate(17, value, demos=6, queries=queries)
            assert short["train"] == complete["train"]
            assert short["test"] == complete["test"][:queries]


def test_first_two_demonstrations_refute_declared_shortcuts():
    adapter = _load(ADAPTER_PATH, "native_dc382c7da9a9_teaching")
    prototype = _load(PROTOTYPE_PATH, "native_dc382c7da9a9_teaching_impl")
    rivals = (
        "all_equidistant",
        "shortest_path_midpoints",
        "manhattan_equidistant",
        "all_shortest_path_cells",
        "first_equidistant_only",
        "red_one_step_farther",
        "identity",
    )
    for seed in (0, 17, 31):
        for scope in prototype.DISTANCE_SCOPES:
            episode = adapter.generate(seed, {"distance_scope": scope}, demos=2, queries=4)
            for rival in rivals:
                if rival == scope:
                    continue
                assert any(
                    prototype.rival_output(pair["input"], rival) != pair["output"]
                    for pair in episode["train"]
                ), (seed, scope, rival)
                assert any(
                    prototype.rival_output(pair["input"], rival) != pair["output"]
                    for pair in episode["test"]
                ), (seed, scope, rival)


def test_fourth_query_is_substantive_30x30_and_uses_global_shortest_distance():
    adapter = _load(ADAPTER_PATH, "native_dc382c7da9a9_large")
    prototype = _load(PROTOTYPE_PATH, "native_dc382c7da9a9_large_impl")
    inputs = []
    for scope in prototype.DISTANCE_SCOPES:
        pair = adapter.generate(17, {"distance_scope": scope}, demos=3, queries=4)["test"][3]
        grid = pair["input"]
        inputs.append(grid)
        assert (len(grid), len(grid[0])) == (30, 30)
        assert sum(cell == 5 for row in grid for cell in row) >= 180
        assert {cell for row in grid for cell in row} == {0, 2, 3, 5}
        facts = prototype.analyze(grid)
        assert len(facts["equal_cells"]) >= 100
        assert len(facts["midpoint_cells"]) == 1
    assert inputs[0] == inputs[1]
    assert prototype.solve(inputs[0], prototype.DISTANCE_SCOPES[0]) != prototype.solve(inputs[0], prototype.DISTANCE_SCOPES[1])


def test_invalid_requests_fail_and_generation_returns_fresh_data():
    adapter = _load(ADAPTER_PATH, "native_dc382c7da9a9_validation")
    valid = {
        "seed": 17,
        "settings": {"distance_scope": "all_equidistant"},
        "demos": 3,
        "queries": 4,
    }
    for field, values in {
        "seed": (-1, 2**63, True, 1.5, "17"),
        "demos": (1, 7, True, 3.0, "3"),
        "queries": (0, 5, True, 1.0, "1"),
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, field: value})
    first = adapter.generate(**valid)
    second = adapter.generate(**valid)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 0
    assert adapter.generate(**valid) == second
