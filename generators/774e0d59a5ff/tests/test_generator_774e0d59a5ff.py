"""Portable regressions for top-panel reflection across a color-5 divider."""
from __future__ import annotations

from copy import deepcopy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "774e0d59a5ff"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def expected_output(grid):
    """Independent Python description of the unchanged Racket authority."""
    out = deepcopy(grid)
    divider = len(grid) // 2
    for row in range(divider):
        mirror_row = 2 * divider - row
        for col, value in enumerate(grid[row]):
            if value != 0:
                out[mirror_row][col] = value
    return out


def grid_signature(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_all_canonical_pairs() -> None:
    assert GEN.RULE_HASH == "73a966cdbca0"
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert expected_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_axis_contract_contains_only_observable_controls() -> None:
    assert set(GEN.AXES) == {"panel_h", "grid_w", "marks", "n_colors", "motif_style"}
    assert GEN.AXES["panel_h"]["valid"] == "4..5"
    assert GEN.AXES["grid_w"]["valid"] == "8..11"
    assert GEN.AXES["marks"]["valid"] == "4..8"
    assert GEN.AXES["n_colors"]["valid"] == "1..4"
    assert GEN.AXES["motif_style"]["valid"] == "points|mixed"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize(
    "options",
    [
        {"panel_h": 4, "grid_w": 8, "marks": 4, "n_colors": 1, "motif_style": "points"},
        {"panel_h": 5, "grid_w": 11, "marks": 8, "n_colors": 4, "motif_style": "mixed"},
        {"panel_h": 4, "grid_w": 11, "marks": 7, "n_colors": 3, "motif_style": "mixed"},
    ],
)
def test_every_exact_axis_round_trips_in_every_band(difficulty, options) -> None:
    grid = GEN.generate(913, 27, difficulty=difficulty, **options)
    assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": options}) == []
    assert GEN.observe_overrides(grid) == options
    assert expected_output(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"palette_size": 4},
        {"texture": "default"},
        {"panel_h": 3},
        {"panel_h": 6},
        {"grid_w": 7},
        {"grid_w": 12},
        {"marks": 3},
        {"marks": 9},
        {"n_colors": 0},
        {"n_colors": 5},
        {"motif_style": "diagonal"},
        {"panel_h": True},
        {"grid_w": 9.0},
        {"marks": "4"},
        {"n_colors": False},
    ],
)
def test_unknown_invalid_and_coercible_overrides_fail_closed(kwargs) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


@pytest.mark.parametrize("seed", [True, 1.0, "1"])
def test_seed_requires_a_genuine_integer(seed) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_genuine_integer(sample_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, sample_index)


def test_unknown_difficulty_fails_closed() -> None:
    with pytest.raises(ValueError):
        GEN.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize("difficulty", BANDS)
def test_defaults_are_deterministic_lawful_diverse_and_semantically_useful(difficulty) -> None:
    shapes = set()
    mark_counts = set()
    color_counts = set()
    styles = set()
    outputs = set()
    before = random.getstate()
    for index in range(96):
        seed = 7000 + index
        sample_index = index * 7 + 2
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert grid == GEN.generate(seed, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid, difficulty=difficulty) == []
        assert GEN.strict_canonical_like(grid) == []
        observed = GEN.observe_overrides(grid)
        assert expected_output(grid) != grid
        assert GEN.SEMANTIC_WITNESSES["vertical_order"](grid)
        assert GEN.SEMANTIC_RIVALS["copy_without_reflection"](grid) != expected_output(grid)
        assert GEN.LESSON_COMPETITORS["copy_without_reflection"](grid) != expected_output(grid)
        shapes.add((len(grid), len(grid[0])))
        mark_counts.add(observed["marks"])
        color_counts.add(observed["n_colors"])
        styles.add(observed["motif_style"])
        outputs.add(grid_signature(grid))
    assert random.getstate() == before
    assert len(outputs) >= 90
    assert len(shapes) >= 4
    assert {4, 8} <= mark_counts
    assert {1, 4} <= color_counts
    assert styles == {"points", "mixed"}


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_default_distribution_hits_a_canonical_size_palette_profile(difficulty) -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in PAIRS
    }
    profiles = set()
    for index in range(20):
        grid = GEN.generate(index, index * 11, difficulty=difficulty)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
    assert profiles & canonical_profiles


@pytest.mark.parametrize(
    "mutation",
    ["divider", "bottom", "extra_five", "too_few_marks", "vertical_symmetry"],
)
def test_validator_rejects_destructive_or_teaching_defect_mutations(mutation) -> None:
    grid = GEN.generate(41, 7, panel_h=4, grid_w=9, marks=4, n_colors=4, motif_style="points")
    divider = len(grid) // 2
    if mutation == "divider":
        grid[divider][0] = 0
    elif mutation == "bottom":
        grid[divider + 1][0] = 2
    elif mutation == "extra_five":
        grid[0][0] = 5
    elif mutation == "too_few_marks":
        for row in range(divider):
            for col in range(len(grid[0])):
                grid[row][col] = 0
        grid[0][0] = 2
    elif mutation == "vertical_symmetry":
        for row in range(divider):
            for col in range(len(grid[0])):
                grid[row][col] = 0
        grid[0][1] = grid[divider - 1][1] = 2
        grid[1][3] = grid[divider - 2][3] = 3
    assert GEN.self_check(grid)


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 0]], [[True] * 9 for _ in range(9)], [[10] * 9 for _ in range(9)]],
)
def test_malformed_grid_is_diagnostic_not_exception(bad) -> None:
    reasons = GEN.self_check(bad)
    assert isinstance(reasons, list) and reasons
