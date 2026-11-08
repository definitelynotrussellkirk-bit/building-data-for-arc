"""Focused regressions and evidence helpers for generator 8cbd834f4187."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import shutil
from collections import Counter
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK = "8cbd834f4187"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
BASE_PATH = ROOT / "data/base/solutions/training/72207abc__8cbd834f4187.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise AssertionError(f"missing canonical row for {TASK}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_selected_authority_are_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    base = json.loads(BASE_PATH.read_text())
    assert base["racket_target"]["target_code"] == canonical
    assert base["racket_target"]["raw_code"] != canonical
    assert _normalized_hash(canonical) == GEN.RULE_HASH == "4db26130eaff"


def test_all_canonical_inputs_are_accepted_and_python_mirror_is_exact_and_pure():
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_is_exact_input_pure_and_a_b_a_reentrant():
    source = _canonical_row()["program_solution"]
    pairs = _pairs()
    bridge = RacketBridge()
    try:
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_w": 19},
        {"grid_w": 29},
        {"n_seed_cells": 2},
        {"n_seed_cells": 3},
        {"grid_w": 19, "n_seed_cells": 2},
        {"grid_w": 29, "n_seed_cells": 3},
    ],
)
def test_every_declared_override_boundary_is_realized_exactly(difficulty, overrides):
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
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(0, 0, grid_w=20)
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(0, 0, n_seed_cells=4)


def test_determinism_fresh_returns_mutation_safety_and_global_rng():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    frozen = _frozen(second)
    first[1][0] = 0
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(20)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(20)}
    assert len(by_seed) >= 16
    assert len(by_index) >= 16


def test_every_five_sample_window_covers_profiles_and_shortcut_rebuttal():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            grids = [GEN.generate(1234, start + i, difficulty=difficulty) for i in range(5)]
            profiles = {
                (GEN.observe_overrides(grid)["grid_w"], GEN.observe_overrides(grid)["n_seed_cells"])
                for grid in grids
            }
            assert profiles == {(19, 2), (19, 3), (29, 2), (29, 3)}
            demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
            query_grid = GEN.generate(1234, start + 4, difficulty=difficulty)
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_named_structural_impostors_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot


def test_negative_recombinations_are_rejected_but_oracle_remains_executable():
    canonical = GEN.generate(66, 0, difficulty="easy", grid_w=19, n_seed_cells=3)
    replacements = []

    moved_marker = copy.deepcopy(canonical)
    moved_marker[1][3] = 0
    moved_marker[1][4] = 8
    replacements.append(moved_marker)

    absent_feature = copy.deepcopy(canonical)
    absent_feature[1][1] = 0
    absent_feature[1][2] = 9
    replacements.append(absent_feature)

    for grid in replacements:
        assert GEN.self_check(grid)
        output = GEN.rule_mirror(grid)
        assert len(output) == len(grid) and len(output[0]) == len(grid[0])


def test_600_draw_linked_semantic_census_and_disjoint_stability():
    expected_profiles = {(19, 2), (19, 3), (29, 2), (29, 3)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(seed, seed * 17 + 3, difficulty=difficulty) for seed in range(200)]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        counts = Counter(
            (GEN.observe_overrides(grid)["grid_w"], GEN.observe_overrides(grid)["n_seed_cells"])
            for grid in grids
        )
        assert set(counts) == expected_profiles
        assert min(counts.values()) >= 45
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 145

        stable = [GEN.generate(10_000 + seed, 50_000 + seed, difficulty=difficulty) for seed in range(200)]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in stable)
        assert len({_frozen(grid) for grid in stable}) >= 145
