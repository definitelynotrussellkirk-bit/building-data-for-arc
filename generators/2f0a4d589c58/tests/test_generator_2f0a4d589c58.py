"""Focused regression tests for generator 2f0a4d589c58."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
TASK = "2f0a4d589c58"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATH = ROOT / "data/base/solutions/training/ba97ae07__2f0a4d589c58.json"
CANONICAL_PATH = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_selected_authority_are_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text())
    assert base["racket_target"]["target_code"] == canonical
    assert base["racket_target"]["raw_code"] != canonical
    assert _normalized_hash(canonical) == GEN.RULE_HASH == "70d63db0a1f2"


def test_all_canonical_pairs_are_accepted_and_python_mirror_is_exact_and_pure():
    pairs = canonical_pairs(TASK)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 6},
        {"grid_h": 13, "grid_w": 13},
        {"horizontal_thickness": 1, "vertical_thickness": 1},
        {"horizontal_thickness": 3, "vertical_thickness": 2},
        {"horizontal_position": "top", "vertical_position": "left"},
        {"horizontal_position": "bottom", "vertical_position": "right"},
        {"horizontal_position": "center", "vertical_position": "center"},
        {"horizontal_color": 1, "vertical_color_offset": 1},
        {"horizontal_color": 9, "vertical_color_offset": 8},
        {"occluder": "horizontal"},
        {"occluder": "vertical"},
    ],
)
def test_declared_override_boundaries_are_realized_exactly(difficulty, overrides):
    grid = GEN.generate(771, 991, difficulty=difficulty, **overrides)
    assert GEN.self_check(grid) == []
    observed = GEN.observe_overrides(grid)
    for key, value in overrides.items():
        assert observed[key] == value


def test_invalid_controls_fail_closed():
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, invented_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=6)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, horizontal_position="middle")
    with pytest.raises(ValueError):
        GEN.generate(0, 0, vertical_color_offset=0)


def test_ordinary_keyed_draws_equal_grid_observations_in_every_band():
    contexts = []
    generator_base.set_ctx_observer(contexts.append)
    try:
        for difficulty in ("easy", "medium", "hard"):
            for index in range(40):
                grid = GEN.generate(9_001 + index, 17_000 + index, difficulty=difficulty)
                context = contexts[-1]
                observed = GEN.observe_overrides(grid)
                requested = context.recorded_draws()
                assert set(requested) == set(GEN.AXES)
                assert {key: observed[key] for key in GEN.AXES} == requested
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_mutation_safety_and_global_rng_state():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    frozen = _frozen(second)
    first[0][0] = 9
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(30)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(30)}
    assert len(by_seed) >= 25
    assert len(by_index) >= 25


def test_self_check_rejects_named_structural_impostors_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 6
    for name, grid in fixtures:
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot


def test_every_three_demo_window_identifies_rule_against_declared_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(36):
            demos = []
            for offset in range(3):
                grid = GEN.generate(4_000 + start, start + offset, difficulty=difficulty)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(4_000 + start, start + 3, difficulty=difficulty)
            assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []


def test_linked_semantic_census_has_every_branch_and_high_variation():
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(20_000 + seed, 30_000 + seed * 13, difficulty=difficulty)
            for seed in range(200)
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        observations = [GEN.observe_overrides(grid) for grid in grids]
        occluders = Counter(item["occluder"] for item in observations)
        h_positions = Counter(item["horizontal_position"] for item in observations)
        v_positions = Counter(item["vertical_position"] for item in observations)
        overlap_areas = Counter(
            item["horizontal_thickness"] * item["vertical_thickness"]
            for item in observations
        )
        assert set(occluders) == {"horizontal", "vertical"}
        assert set(h_positions) == {"top", "center", "bottom"}
        assert set(v_positions) == {"left", "center", "right"}
        assert 1 in overlap_areas and any(area > 1 for area in overlap_areas)
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 180
