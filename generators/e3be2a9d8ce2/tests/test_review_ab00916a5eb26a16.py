from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_e3be2a9d8ce2_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

CANONICAL_PROFILES = {
    (12, 10, 4),
    (14, 15, 3),
    (11, 8, 2),
    (12, 12, 3),
    (11, 16, 5),
}


def _profile(grid):
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_exact_seed_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_non_exact_or_negative_sample_indices(bad_index):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(991, bad_index, difficulty="easy")


@pytest.mark.parametrize(
    "bad_difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_generate_rejects_invalid_difficulty_scalars(bad_difficulty):
    with pytest.raises((TypeError, ValueError)):
        MODULE.generate(991, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    "axis,valid,invalids",
    [
        ("grid_h", 8, ["8", 8.0, 8.75, True]),
        ("grid_w", 22, ["22", 22.0, 22.75, True]),
        ("n_pixels", 3, ["3", 3.0, 3.75, True]),
        ("palette_size", 2, ["2", 2.0, 2.75, True]),
    ],
)
def test_integer_overrides_reject_scalar_coercion(axis, valid, invalids):
    base = {"n_pixels": 3, "palette_size": 2}
    base[axis] = valid
    MODULE.generate(17, 3, difficulty="medium", **base)
    for invalid in invalids:
        bad = dict(base)
        bad[axis] = invalid
        with pytest.raises((TypeError, ValueError)):
            MODULE.generate(17, 3, difficulty="medium", **bad)


def test_unpinned_anchor_residue_matches_a_canonical_profile_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in (0, 4, 8, 12):
            grid = MODULE.generate(20261021, sample_index, difficulty=difficulty)
            assert _profile(grid) in CANONICAL_PROFILES


def test_semantic_contract_refutes_basic_shortcuts_and_accepts_a_lesson():
    assert MODULE.strict_canonical_like is not None
    assert set(MODULE.LESSON_COMPETITORS) == {
        "identity",
        "vertical_only",
        "horizontal_only",
    }
    grids = [MODULE.generate(314159, index, difficulty="medium") for index in range(4)]
    pairs = [
        {"input": grid, "output": MODULE.diagnostic_transform(grid)}
        for grid in grids
    ]
    for pair in pairs:
        assert MODULE.strict_canonical_like(pair["input"]) == []
        for rival in MODULE.LESSON_COMPETITORS.values():
            assert rival(pair["input"]) != pair["output"]
    assert MODULE.lesson_identifiable(pairs[:3], {"input": pairs[3]["input"]}) == []


def test_four_pair_schedule_keeps_two_multicolor_teaching_witnesses():
    seed = 24303300002611
    grids = [MODULE.generate(seed, index, difficulty="easy") for index in range(33, 37)]
    palette_sizes = [
        len({cell for row in grid for cell in row if cell != 0}) for grid in grids
    ]
    assert sum(size >= 2 for size in palette_sizes) >= 2, palette_sizes


def test_single_emitter_overrides_win_over_multicolor_teaching_schedule():
    for sample_index in (1, 3):
        grid = MODULE.generate(
            404, sample_index, difficulty="medium", n_pixels=1, palette_size=1
        )
        assert MODULE.observe_overrides(grid)["n_pixels"] == 1
        assert MODULE.observe_overrides(grid)["palette_size"] == 1


def test_every_four_pair_schedule_start_retains_a_multicolor_demo_under_rotation():
    """Exercise all four cyclic starts, all bands, and every held-out query."""
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 17, 20261021):
            for start_residue in range(4):
                start = 40 + start_residue
                grids = [
                    MODULE.generate(seed, start + offset, difficulty=difficulty)
                    for offset in range(4)
                ]
                is_multicolor = [
                    len({cell for row in grid for cell in row if cell != 0}) >= 2
                    for grid in grids
                ]
                assert sum(is_multicolor) >= 2, (
                    difficulty,
                    seed,
                    start_residue,
                    is_multicolor,
                )
                for query_index in range(4):
                    demo_flags = [
                        flag for index, flag in enumerate(is_multicolor)
                        if index != query_index
                    ]
                    assert any(demo_flags), (
                        difficulty,
                        seed,
                        start_residue,
                        query_index,
                        is_multicolor,
                    )
