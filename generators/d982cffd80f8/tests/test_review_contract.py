"""Focused repair regressions; portable between the library and review runtime."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "d982cffd80f8"
ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
) if path.is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_ring_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def reference_scan(grid):
    """Handwritten simultaneous transform, independent of generator helpers."""
    result = deepcopy(grid)
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            surrounding = [grid[row + dr][col + dc]
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                           if dr or dc]
            if grid[row][col] == 0 and surrounding[0] != 0:
                if all(value == surrounding[0] for value in surrounding):
                    result[row][col] = surrounding[0]
    return result


def foreground_colors(grid):
    return {value for row in grid for value in row if value != 0}


def paint_ring(grid, top, left, color):
    for dr in range(3):
        for dc in range(3):
            if (dr, dc) != (1, 1):
                grid[top + dr][left + dc] = color


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 17])
def test_default_scene_passes_its_difficulty_validator(difficulty, seed):
    grid = GEN.generate(seed, 0, difficulty=difficulty)
    before = deepcopy(grid)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert grid == before
    assert reference_scan(grid) != grid


def test_three_ring_medium_scene_is_lawful():
    grid = [[0] * 7 for _ in range(9)]
    for top, left, color in ((0, 0, 4), (0, 4, 8), (4, 0, 9)):
        paint_ring(grid, top, left, color)
    assert len(GEN._fillable_centers(grid)) == 3
    assert GEN.self_check(grid, difficulty="medium") == []


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}")
def test_canonical_input_is_accepted_and_scan_matches_label(pair):
    assert GEN.self_check(deepcopy(pair["input"])) == []
    assert reference_scan(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "hard"])
@pytest.mark.parametrize("count", [1, 3, 6])
def test_ring_override_is_exact_and_difficulty_is_only_a_hint(difficulty, count):
    grid = GEN.generate(5, 2, difficulty=difficulty, n_rings=count)
    assert len(GEN._fillable_centers(grid)) == count
    assert GEN.observe_overrides(grid)["n_rings"] == count
    assert GEN.self_check(grid, difficulty=difficulty,
                          meta={"overrides": {"n_rings": count}}) == []


@pytest.mark.parametrize("axis,value", [("grid_h", 5), ("grid_h", 14),
                                         ("grid_w", 5), ("grid_w", 16)])
def test_dimension_override_honors_advertised_endpoint(axis, value):
    grid = GEN.generate(7, 0, difficulty="hard", **{axis: value})
    actual = len(grid) if axis == "grid_h" else len(grid[0])
    assert actual == value
    assert GEN.self_check(grid, difficulty="hard") == []


@pytest.mark.parametrize("axis", ["palette_size", "n_distinct_colors"])
@pytest.mark.parametrize("count", [1, 3, 6])
def test_color_count_aliases_mean_exact_realized_foreground_colors(axis, count):
    grid = GEN.generate(11, 1, **{axis: count})
    assert len(foreground_colors(grid)) == count
    observations = GEN.observe_overrides(grid)
    assert observations["palette_size"] == count
    assert observations["n_distinct_colors"] == count
    assert GEN.self_check(grid, meta={"overrides": {axis: count}}) == []


def test_conflicting_color_count_aliases_are_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, palette_size=1, n_distinct_colors=2)


@pytest.mark.parametrize("kind", ["default", "warm", "cool", "varied"])
def test_helpful_texture_and_palette_kind_are_equivalent_aliases(kind):
    first = GEN.generate(19, 3, palette_kind=kind)
    second = GEN.generate(19, 3, texture=kind)
    assert first == second


def test_conflicting_palette_kind_aliases_are_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, palette_kind="warm", texture="cool")


def test_unknown_axis_is_not_silently_ignored():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, misspelled_ring_count=2)


@pytest.mark.parametrize("axis", ["grid_h", "n_rings", "n_distinct_colors"])
@pytest.mark.parametrize("value", [True, 2.0, "2"])
def test_exact_integer_axes_do_not_coerce_other_types(axis, value):
    # For dimensions, exercise numerically valid coercions rather than allowing
    # an unrelated range rejection to conceal the strict-type contract.
    if axis == "grid_h" and value is not True:
        value = 7.0 if isinstance(value, float) else "7"
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


def test_pinned_impossible_layout_has_structured_incompatibility():
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, grid_h=5, grid_w=5, n_rings=6)
    assert {"grid_h", "grid_w", "n_rings"}.issubset(
        set(getattr(caught.value, "incompatible_axes", ())))


@pytest.mark.parametrize("grid", [[], [[]], [[], []], [1, 2], [[0], [0, 0]]])
def test_malformed_grid_returns_reasons_without_crashing(grid):
    findings = GEN.self_check(grid)
    assert isinstance(findings, list) and findings
    assert all(isinstance(reason, str) for reason in findings)


@pytest.mark.parametrize("color", [True, 2.0])
def test_noninteger_colors_cannot_disguise_valid_ring_structure(color):
    grid = [[0] * 7 for _ in range(7)]
    paint_ring(grid, 0, 0, color)
    paint_ring(grid, 4, 4, color)
    assert GEN.self_check(grid)


def test_touching_rings_and_inert_singleton_are_lawful():
    grid = [[0] * 8 for _ in range(7)]
    paint_ring(grid, 0, 0, 2)
    paint_ring(grid, 2, 3, 4)
    grid[6][7] = 9
    assert GEN.self_check(grid) == []
    output = reference_scan(grid)
    assert output[6][7] == 9
    assert output[1][1] == 2 and output[3][4] == 4


def test_generation_and_observation_are_deterministic_and_pure():
    grid = GEN.generate(23, 4, n_rings=3, n_distinct_colors=3)
    before = deepcopy(grid)
    observations = GEN.observe_overrides(grid)
    assert grid == GEN.generate(23, 4, n_rings=3, n_distinct_colors=3)
    assert observations == GEN.observe_overrides(grid)
    assert grid == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_examples_visibly_refute_declared_teaching_rivals(difficulty):
    grid = GEN.generate(0, 0, difficulty=difficulty)
    output = reference_scan(grid)
    for name in ("four_neighbors", "seven_neighbors", "overwrite_nonzero", "identity"):
        rival = GEN.LESSON_COMPETITORS[name]
        before = deepcopy(grid)
        assert rival(grid) != output, name
        assert grid == before, f"{name} mutates its input"


def test_declared_canonical_shortcuts_really_fit_the_canonical_labels():
    for name in ("four_neighbors", "seven_neighbors", "overwrite_nonzero"):
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        for pair in CANONICAL:
            assert shortcut(deepcopy(pair["input"])) == pair["output"], name


@pytest.mark.parametrize("texture", ["no_rings", "filled_centers", "partial_ring"])
def test_named_negative_fixtures_remain_callable_and_fail_validation(texture):
    assert texture not in GEN.AXES["texture"]["valid"].split("|")
    grid = GEN.generate(0, 0, texture=texture)
    assert GEN.self_check(grid)


@pytest.mark.parametrize("overrides", [
    {"palette_kind": "cool", "n_distinct_colors": 6},
    {"texture": "warm", "palette_size": 6},
])
def test_incompatibility_names_only_the_actual_supplied_axes(overrides):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, **overrides)
    axes = set(caught.value.incompatible_axes)
    assert axes and axes.issubset(overrides)


def test_ordinary_color_count_varies_across_seeds_at_fixed_index():
    counts = {len(foreground_colors(GEN.generate(seed, 0))) for seed in range(60)}
    assert len(counts) > 1


@pytest.mark.parametrize("sample_index", [2251, 8152])
def test_single_color_override_is_not_rejected_by_a_full_tiling(sample_index):
    grid = GEN.generate(0, sample_index, n_distinct_colors=6)
    assert len(foreground_colors(grid)) == 6


def test_six_colors_fit_two_positives_and_two_contrasts_on_six_by_six():
    for seed in range(12):
        grid = GEN.generate(seed, 1, grid_h=6, grid_w=6, n_rings=2, palette_size=6)
        assert len(GEN._fillable_centers(grid)) == 2
        assert len(foreground_colors(grid)) == 6
        expected = reference_scan(grid)
        assert all(rival(grid) != expected for rival in GEN.LESSON_COMPETITORS.values())
