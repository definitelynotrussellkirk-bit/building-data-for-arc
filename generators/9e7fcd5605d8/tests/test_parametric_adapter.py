"""Behavioral contracts for the opt-in topology-threshold family.

These tests catch setting-dependent input leakage, short/duplicate lessons,
lost query-prefix stability, malformed controls and decorative large canvases.
Racket label and finite-rival checks live in the runnable verifier/native gate.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]


def load(name):
    path = HOME / "workspace" / "parametric" / f"{name}.py"
    assert path.is_file(), f"Missing native parametric {name}"
    spec = importlib.util.spec_from_file_location(f"_topology_test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inputs(episode):
    return [p["input"] for split in ("train", "test") for p in episode[split]]


def test_default_program_is_exact_selected_authority():
    adapter = load("adapter")
    rows = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()]
    canonical = next(row for row in rows if row["task_id"] == "9e7fcd5605d8")
    assert adapter.program({"min_holes": 1}) == canonical["program_solution"]
    assert adapter.program({"min_holes": 2}) != canonical["program_solution"]


@pytest.mark.parametrize("seed,demos,queries", [(0, 2, 4), (17, 3, 4), (91, 6, 4), (3, 2, 1)])
def test_complete_deterministic_matched_inputs(seed, demos, queries):
    adapter = load("adapter")
    settings = {"min_holes": 1}
    before = deepcopy(settings)
    one = adapter.generate(seed, settings, demos, queries)
    two = adapter.generate(seed, {"min_holes": 2}, demos, queries)
    assert settings == before
    assert one == adapter.generate(seed, settings, demos, queries)
    assert len(one["train"]) == demos and len(one["test"]) == queries
    assert inputs(one) == inputs(two)
    assert len({json.dumps(grid) for grid in inputs(one)}) == demos + queries
    assert one["program_solution"] == adapter.program(settings)
    assert any(a["output"] != b["output"] for a, b in zip(one["train"], two["train"]))
    for episode in (one, two):
        for split in ("train", "test"):
            for pair in episode[split]:
                for key in ("input", "output"):
                    grid = pair[key]
                    assert type(grid) is list and 1 <= len(grid) <= 30
                    assert 1 <= len(grid[0]) <= 30
                    assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
                    assert all(type(c) is int and 0 <= c <= 9 for row in grid for c in row)


def test_query_and_demo_prefixes_do_not_depend_on_requested_counts():
    adapter = load("adapter")
    small = adapter.generate(31, {"min_holes": 2}, 2, 1)
    large = adapter.generate(31, {"min_holes": 2}, 6, 4)
    assert small["train"] == large["train"][:2]
    assert small["test"] == large["test"][:1]


def test_maximum_canvas_has_many_objects_spread_and_boundary_content():
    prototype = load("prototype")
    episode = prototype.generate(17, {"min_holes": 2}, 2, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    info = prototype.analyze(grid)
    assert len(info) >= 12
    assert {0, 1, 2, 3} <= {obj["holes"] for obj in info}
    assert sum(c != 0 for row in grid for c in row) >= 240
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    for r0 in (0, 15):
        for c0 in (0, 15):
            assert sum(grid[r][c] != 0 for r in range(r0, r0+15) for c in range(c0, c0+15)) >= 40


def test_smallest_query_and_two_demos_cover_topology_contrasts():
    prototype = load("prototype")
    episode = prototype.generate(0, {"min_holes": 2}, 2, 4)
    assert (len(episode["test"][0]["input"]), len(episode["test"][0]["input"][0])) == (11, 11)
    for pair in episode["train"]:
        objects = prototype.analyze(pair["input"])
        assert {0, 1, 2, 3} <= {obj["holes"] for obj in objects}
    first = episode["train"][0]["input"]
    assert len({c for row in first for c in row if c}) == 1


@pytest.mark.parametrize("settings", [{}, {"min_holes": True}, {"min_holes": 1.0},
    {"min_holes": "1"}, {"min_holes": 0}, {"min_holes": 3}, {"min_holes": 1, "extra": 2}, None])
def test_invalid_settings_are_rejected_before_sampling(settings):
    adapter = load("adapter")
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
    (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 2.0, 4), (0, 3, 0), (0, 3, 5), (0, 3, True)])
def test_invalid_counts_and_seeds_are_rejected(seed, demos, queries):
    adapter = load("adapter")
    with pytest.raises((ValueError, TypeError)):
        adapter.generate(seed, {"min_holes": 1}, demos, queries)


def test_public_projection_ignores_private_answers_and_settings():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    adapter = load("adapter")
    episode = adapter.generate(23, {"min_holes": 2}, 3, 4)
    single = adapter.generate(23, {"min_holes": 2}, 3, 1)
    first_turn = {"train": episode["train"], "test": episode["test"][:1]}
    assert public_challenge_bytes(first_turn) == public_challenge_bytes(single)
    changed = deepcopy(first_turn)
    changed["settings"] = {"min_holes": 1}
    changed["seed"] = 99
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_id(changed) == public_challenge_id(first_turn)
    visible = json.loads(public_challenge_bytes(first_turn))
    assert set(visible) == {"train", "test"} and len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
