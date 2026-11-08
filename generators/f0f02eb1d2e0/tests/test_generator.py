"""Semantic, schedule, and exact-override regressions for f0f02eb1d2e0."""
from __future__ import annotations

import copy
import hashlib
import importlib
import itertools
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "f0f02eb1d2e0"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.f0f02eb1d2e0.generator"
)


def _pair(seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_mirrored():
    assert gen.RULE_HASH == "bf8c9dd4f7fa"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_rule_ignores_bent_three_cells_and_diagonal_pairs():
    grid = [
        [1, 0, 0, 0, 0, 0, 2],
        [0, 1, 0, 0, 0, 2, 0],
        [1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 3, 0, 3, 0],
        [0, 0, 0, 3, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ]
    # Color 1 spans three rows, color 2 is a diagonal pair, and only color 3
    # is an exact three-corner rectangle.
    out = gen.rule_mirror(grid)
    assert out[0][1] == 0 and out[2][1] == 0
    assert out[0][5] == 0 and out[1][6] == 0
    assert out[4][5] == 3
    assert gen.self_check(grid) == []


def test_all_declared_axis_boundaries_round_trip_exactly():
    axis_values = {
        "grid_h": (6, 12),
        "grid_w": (9, 14),
        "n_targets": (1, 4),
        "n_bent_decoys": (0, 2),
        "n_other_decoys": (0, 2),
        "corner_offset": (0, 3),
    }
    for index, values in enumerate(itertools.product(*axis_values.values())):
        overrides = dict(zip(axis_values, values))
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(9100 + index, 1000 + index, difficulty=band, **overrides)
        assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_bad_type_and_out_of_range_controls_reject_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="impossible")
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)
    with pytest.raises((TypeError, ValueError), match="integer"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, n_targets=5)


def test_four_profile_curriculum_and_every_query_rotation_refute_competitors():
    assert gen.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            pairs = [_pair(7000 + start, start + offset, band) for offset in range(4)]
            for query_index in range(4):
                query = pairs[query_index]
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, query) == []
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert sum(
                    competitor(pair["input"]) != pair["output"] for pair in pairs
                ) >= 2, (band, start, name)


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_profiles_supply_redundant_teaching_witnesses():
    for band in ("easy", "medium", "hard"):
        rows = [
            gen.semantic_observables(gen.generate(12345, index, difficulty=band))
            for index in range(4)
        ]
        assert sum(row["canonical_anchor"] for row in rows) == 1
        assert sum(row["has_bent_three"] for row in rows) == 3
        assert sum(row["has_diagonal_pair"] for row in rows) == 2
        assert sum(row["n_targets"] > 2 for row in rows) == 2
        assert sum(row["outside_canonical_dimensions"] for row in rows) == 2
        assert all(row["has_long_target"] for row in rows)


def test_generated_inputs_are_lawful_deterministic_fresh_and_rng_pure():
    random.seed(20261008)
    state = random.getstate()
    first = gen.generate(
        42,
        7,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        n_targets=4,
        n_bent_decoys=2,
        n_other_decoys=2,
        corner_offset=3,
    )
    assert random.getstate() == state
    second = gen.generate(
        42,
        7,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        n_targets=4,
        n_bent_decoys=2,
        n_other_decoys=2,
        corner_offset=3,
    )
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert gen.self_check(first) == []

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(100):
            grid = gen.generate(10000 + band_index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid


def test_default_palette_median_stays_within_canonical_drift_gate():
    # Canonical inputs use three colors including background.  The shared defect
    # lint allows broad teaching examples, but its robust wrong-task threshold is
    # 2.5x; keep every default profile at seven colors or fewer.
    for band in ("easy", "medium", "hard"):
        palette_sizes = [
            len({value for row in gen.generate(31415, index, difficulty=band) for value in row})
            for index in range(4)
        ]
        assert max(palette_sizes) <= 7


def test_pinned_profile_floor_keeps_at_least_quarter_canonical_envelope():
    canonical = canonical_pairs(TASK_ID, root=find_root(__file__))
    profiles = {
        (len(pair["input"]), len(pair["input"][0]),
         len({value for row in pair["input"] for value in row}))
        for pair in canonical
    }
    total_hits = 0
    for band in ("easy", "medium", "hard"):
        band_hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid), len(grid[0]),
                len({value for row in grid for value in row}),
            )
            band_hits += profile in profiles
        assert band_hits >= 1
        total_hits += band_hits
    assert total_hits >= 15
