from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "394fc1eaa85e"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _episode(seed, start, difficulty):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    qidx = start + GEN.EXAMPLES_NEEDED
    qgrid = GEN.generate(seed, qidx, difficulty=difficulty)
    return demos, {"input": qgrid, "output": GEN.rule_mirror(qgrid)}


def test_canonical_inputs_and_outputs():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_rule_hash_matches_synced_authority():
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_curriculum_is_strict_and_wall_calibrated(difficulty):
    profiles = []
    for sample_index in range(12):
        grid = GEN.generate(271828, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        obs = GEN.semantic_observables(grid)
        profiles.append(obs["wall_profile"])
        assert obs["tie_count"] >= 2
        assert obs["non_tie_open_count"] >= 1
        if obs["wall_profile"] != "none":
            assert obs["wall_sensitive"] is True
    assert profiles == list(GEN.WALL_PROFILES) * 3


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_schedule_phase_is_identifiable(difficulty):
    for start in range(len(GEN.WALL_PROFILES)):
        demos, query = _episode(161803, start, difficulty)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


def test_mutation_fixtures_reject():
    assert len(GEN.mutation_fixtures()) >= 5
    for name, grid in GEN.mutation_fixtures():
        assert GEN.self_check(grid), name


def test_blank_grid_is_not_a_lawful_scene():
    assert GEN.self_check([[0] * 11 for _ in range(7)])


def test_dimension_override_boundaries_are_exact_and_observable():
    for i, (h, w) in enumerate([(7, 11), (7, 13), (9, 11), (9, 13), (8, 12)]):
        grid = GEN.generate(424242, i, difficulty="medium", grid_h=h, grid_w=w)
        assert GEN.observe_overrides(grid) == {"grid_h": h, "grid_w": w}
        assert GEN.self_check(grid, difficulty="medium", meta={"overrides": {"grid_h": h, "grid_w": w}}) == []


@pytest.mark.parametrize("kwargs", [
    {"unknown_axis": 1}, {"anchor_corner": True}, {"asymmetry_force": True}, {"palette_kind": "warm"}, {"grid_h": 6}, {"grid_h": 10}, {"grid_w": 10}, {"grid_w": 14}
])
def test_unknown_and_out_of_range_overrides_reject(kwargs):
    with pytest.raises((ValueError, AssertionError)):
        GEN.generate(99, 0, difficulty="easy", **kwargs)


def test_deterministic_fresh_and_global_rng_safe():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(1234, 2, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(1234, 2, difficulty="hard")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    replay = GEN.generate(1234, 2, difficulty="hard")
    assert replay[0][0] != 9
    assert random.getstate() == state


def test_seed_and_index_variation_changes_content():
    grids = [GEN.generate(seed, idx, difficulty="medium") for seed, idx in
             ((100, 0), (101, 0), (100, 1), (101, 1), (100, 2), (101, 2))]
    assert len({_digest(g) for g in grids}) >= 5
