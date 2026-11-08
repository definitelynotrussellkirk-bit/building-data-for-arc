"""Semantic, distribution, and override regressions for dadeacb21d08."""
from __future__ import annotations

import copy
import importlib
import itertools
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "dadeacb21d08"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.dadeacb21d08.generator"
)


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_accepted_and_mirrored():
    assert gen.RULE_HASH == "4dc2707cc06e"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_occupied_missing_corner_is_overwritten_but_distractors_survive():
    grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 2, 5, 0, 7, 0],
        [0, 0, 0, 0, 7, 7],
        [2, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    out = gen.rule_mirror(grid)
    assert [row[1:3] for row in out[1:3]] == [[3, 3], [3, 3]]
    assert out[4][:3] == [2, 2, 2]
    assert out[2][4] == out[3][4] == out[3][5] == 7
    assert grid[2][2] == 5


def test_all_declared_axis_boundaries_round_trip_exactly():
    axis_values = {
        "grid_h": (10, 16),
        "grid_w": (10, 16),
        "n_target_l": (2, 4),
        "n_red_decoys": (1, 3),
        "n_colored_decoys": (1, 2),
        "hole_mode": ("empty", "occupied", "mixed"),
        "target_position": ("interior", "edge"),
    }
    for index, values in enumerate(itertools.product(*axis_values.values())):
        overrides = dict(zip(axis_values, values))
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(9100 + index, 1000 + index, difficulty=band, **overrides)
        assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_difficulty_and_override_reject_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="impossible")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_four_profile_curriculum_refutes_every_declared_competitor():
    assert gen.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            demos = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            query = _pair(7000 + start, start + 4, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"] for demo in demos
                ), (band, start, name)


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_profile_exposes_its_intended_semantic_controls():
    grids = [gen.generate(12345, index, difficulty="medium") for index in range(4)]
    rows = [gen.semantic_observables(grid) for grid in grids]
    assert sum(bool(row["canonical_anchor"]) for row in rows) == 1
    assert any(row["has_red_straight_triomino"] for row in rows)
    assert any(row["has_red_square"] for row in rows)
    assert any(row["has_nonred_l"] for row in rows)
    assert any(row["hole_mode"] == "occupied" for row in rows)
    assert any(row["hole_mode"] == "mixed" for row in rows)
    assert any(row["target_position"] == "edge" for row in rows)
    assert any(row["n_target_l"] == 4 for row in rows)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    kwargs = dict(
        difficulty="hard",
        grid_h=16,
        grid_w=16,
        n_target_l=4,
        n_red_decoys=3,
        n_colored_decoys=2,
        hole_mode="mixed",
        target_position="edge",
    )
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(42, 7, **kwargs)
    assert random.getstate() == state
    second = gen.generate(42, 7, **kwargs)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
