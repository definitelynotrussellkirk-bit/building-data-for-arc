from __future__ import annotations

import copy
import random
from pathlib import Path
from typing import Any

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "926c6bd137d3"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")


def _pairs() -> list[dict[str, Any]]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _lesson(seed: int, start: int, *, difficulty: str | None = "hard"):
    demos = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
    query_grid = GEN.generate(
        seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
    )
    return demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}


def test_metadata_pins_rule_and_declares_only_observable_controls() -> None:
    assert SOURCE.name == "generator.py"
    assert len(SOURCE_SHA256) == 64
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.1"
    assert GEN.RULE_HASH == "575c55ee70e4"
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_frames",
        "n_exterior_distractors",
    }


def test_all_canonical_pairs_validate_and_python_rule_is_exact_and_pure() -> None:
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 10, "grid_w": 10, "n_frames": 1, "n_exterior_distractors": 1},
        {"grid_h": 10, "grid_w": 10, "n_frames": 4, "n_exterior_distractors": 4},
        {"grid_h": 18, "grid_w": 18, "n_frames": 1, "n_exterior_distractors": 4},
        {"grid_h": 18, "grid_w": 18, "n_frames": 4, "n_exterior_distractors": 1},
    ],
)
def test_joint_exact_overrides_round_trip_in_every_band(
    difficulty: str | None, overrides: dict[str, int]
) -> None:
    grid = GEN.generate(8128, 73, difficulty=difficulty, **overrides)
    assert GEN.generation_check(grid) == []
    assert GEN.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"texture": "default"},
        {"palette_size": 3},
        {"position_bias": "scattered_yellow_frames"},
        {"density": "sparse"},
        {"grid_h": True},
        {"grid_h": 10.0},
        {"grid_w": "10"},
        {"n_frames": False},
        {"n_frames": 2.0},
        {"n_exterior_distractors": "2"},
        {"grid_h": 9},
        {"grid_h": 19},
        {"grid_w": 9},
        {"grid_w": 19},
        {"n_frames": 0},
        {"n_frames": 5},
        {"n_exterior_distractors": 0},
        {"n_exterior_distractors": 5},
    ],
)
def test_invalid_and_retired_overrides_fail_loudly(kwargs: dict[str, Any]) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("seed", [True, 1.0, "1"])
def test_seed_is_strict_integer(seed: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, 1.0, "1", -1])
def test_sample_index_is_strict_nonnegative_integer(sample_index: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_none_overrides_are_absent_and_bad_difficulty_fails() -> None:
    expected = GEN.generate(77, 8, difficulty="medium")
    actual = GEN.generate(
        77,
        8,
        difficulty="medium",
        grid_h=None,
        grid_w=None,
        n_frames=None,
        n_exterior_distractors=None,
    )
    assert actual == expected
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="expert")


def test_exact_frame_requests_never_silently_drop_objects() -> None:
    for difficulty in BANDS:
        for seed in range(40):
            grid = GEN.generate(
                10_000 + seed,
                seed * 17 + 3,
                difficulty=difficulty,
                n_frames=4,
            )
            info, errors = GEN._analyse(grid)
            assert errors == []
            assert len(info["frames"]) == 4
            assert GEN.observe_overrides(grid)["n_frames"] == 4


def test_default_curriculum_has_exterior_evidence_and_full_marker_palette() -> None:
    observed_marker_colors: set[int] = set()
    exact_profiles = {(14, 11, 5), (12, 11, 5), (12, 13, 4), (13, 11, 5), (14, 12, 6)}
    for difficulty in BANDS:
        band_profiles = set()
        for sample_index in range(32):
            grid = GEN.generate(271828, sample_index, difficulty=difficulty)
            info, errors = GEN._analyse(grid)
            assert errors == []
            assert info["exterior_cells"], "generated row must refute erase-the-exterior"
            observed_marker_colors.update(info["marker_colors"])
            band_profiles.add(
                (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            )
        assert band_profiles & exact_profiles
    assert observed_marker_colors == {1, 2, 3, 5, 6, 7, 8, 9}


def test_every_four_demo_window_refutes_all_named_rivals() -> None:
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    assert all(shortcut(pair["input"]) == pair["output"]
               for shortcut in GEN.CANONICAL_SHORTCUTS.values() for pair in _pairs())
    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    for difficulty in BANDS:
        for start in range(12):
            demos, query = _lesson(314159, start, difficulty=difficulty)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                ), name
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness_name_rivals := GEN.WITNESS_RIVALS[name]:
                    assert any(witness(pair["input"]) for pair in demos), (
                        name,
                        witness_name_rivals,
                    )


def test_validator_rejects_role_destroying_mutations_without_crashing() -> None:
    malformed = [None, [], [[]], [[0], [0, 1]], [[False]], [[10]]]
    for grid in malformed:
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors

    grid = GEN.generate(
        99,
        7,
        grid_h=14,
        grid_w=12,
        n_frames=3,
        n_exterior_distractors=2,
    )
    info, errors = GEN._analyse(grid)
    assert errors == []

    broken_frame = copy.deepcopy(grid)
    r0, c0, _r1, _c1 = info["frames"][0]
    broken_frame[r0][c0] = 0
    assert GEN.self_check(broken_frame)

    second_marker = copy.deepcopy(grid)
    r0, c0, r1, c1 = info["frames"][0]
    marker = info["markers"][0]
    free = next(
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if (r, c) != marker
    )
    second_marker[free[0]][free[1]] = 9 if info["marker_colors"][0] != 9 else 8
    assert any("exactly one" in message for message in GEN.self_check(second_marker))

    moved_outside = copy.deepcopy(grid)
    mr, mc = info["markers"][0]
    color = moved_outside[mr][mc]
    moved_outside[mr][mc] = 0
    exterior_zero = next(
        (r, c)
        for r, row in enumerate(moved_outside)
        for c, value in enumerate(row)
        if value == 0 and all(not (fr0 <= r <= fr1 and fc0 <= c <= fc1)
                              for fr0, fc0, fr1, fc1 in info["frames"])
    )
    moved_outside[exterior_zero[0]][exterior_zero[1]] = color
    assert any("exactly one" in message for message in GEN.self_check(moved_outside))


def test_deterministic_fresh_results_and_global_rng_purity() -> None:
    random.seed(20260729)
    before = random.getstate()
    first = GEN.generate(777, 12, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(777, 12, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert GEN.generate(777, 12, difficulty="hard") == second


def test_independent_count_axes_are_not_locked_in_default_schedule() -> None:
    observed = {
        tuple(
            GEN.observe_overrides(GEN.generate(424242, sample_index))[name]
            for name in ("n_frames", "n_exterior_distractors")
        )
        for sample_index in range(16)
    }
    assert any(n_frames != n_exterior for n_frames, n_exterior in observed)


def test_difficulty_changes_geometry_without_changing_public_axis_values() -> None:
    grids = {
        band: GEN.generate(9090, 7, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == 3
    observed = {band: GEN.observe_overrides(grid) for band, grid in grids.items()}
    assert observed["easy"] == observed["medium"] == observed["hard"]
    for grid in grids.values():
        assert GEN.generation_check(grid) == []
