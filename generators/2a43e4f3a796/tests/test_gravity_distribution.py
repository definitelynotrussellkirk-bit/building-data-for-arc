"""Behavior regressions for stable column gravity's input distribution."""
from collections import Counter
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "2a43e4f3a796"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("gravity_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
BANDS = ("easy", "medium", "hard")


def compact(grid):
    """Independent adjacent-swap diagnostic; actual labels come from Racket."""
    out = [row[:] for row in grid]
    for _ in range(len(grid)):
        for r in range(len(grid) - 2, -1, -1):
            for c in range(len(grid[0])):
                if out[r][c] and not out[r + 1][c]:
                    out[r][c], out[r + 1][c] = 0, out[r][c]
    return out


def observed(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "active_cols": sum(any(col) for col in zip(*grid)),
        "n_distinct_colors": len({v for row in grid for v in row if v}),
    }


@pytest.mark.parametrize("band", BANDS)
def test_ordinary_draws_cover_occupied_bottom_and_canonical_singletons(band):
    cohort = [GEN.generate(seed, i, difficulty=band) for seed in range(5) for i in range(12)]
    assert any(any(g[-1]) for g in cohort), "ordinary support still excludes the bottom row"
    assert any(any(sum(v != 0 for v in col) == 1 for col in zip(*g)) for g in cohort)
    assert any(len(g) == 7 for g in cohort), "canonical height 7 is absent"
    assert any(observed(g)["active_cols"] >= 7 for g in cohort)
    assert all(GEN.self_check(g, difficulty=band) == [] for g in cohort)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width,columns,colors", [(3, 2, 1, 1), (3, 18, 18, 9), (24, 2, 2, 9), (24, 18, 18, 9)])
def test_exact_joint_controls_do_not_clamp_or_follow_difficulty_bounds(band, height, width, columns, colors):
    g = GEN.generate(17, 5, difficulty=band, grid_h=height, grid_w=width,
                     active_cols=columns, n_distinct_colors=colors)
    assert observed(g) == {"grid_h": height, "grid_w": width,
                           "active_cols": columns, "n_distinct_colors": colors}
    assert GEN.self_check(g) == []
    assert GEN.observe_overrides(g)["palette_size"] == colors


@pytest.mark.parametrize("colors", [1, 2, 5, 9])
def test_palette_size_alias_is_exact(colors):
    g = GEN.generate(2, 3, grid_h=12, grid_w=9, palette_size=colors)
    assert observed(g)["n_distinct_colors"] == colors


@pytest.mark.parametrize("overrides", [
    {"active_colz": 2}, {"grid_h": True}, {"grid_w": 7.5}, {"active_cols": "3"},
    {"grid_h": 2}, {"grid_w": 19}, {"n_distinct_colors": 10},
    {"palette_size": 2, "n_distinct_colors": 3},
    {"grid_w": 2, "active_cols": 3},
    {"grid_h": 3, "active_cols": 1, "n_distinct_colors": 4},
])
def test_invalid_and_incompatible_controls_reject_instead_of_silently_changing(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(5, 4, **overrides)


@pytest.mark.parametrize("grid", [[], [[]], [[0, 1], [0]], [[True, 0]], [[-1, 0]], [[10, 0]], [[1.0, 0]], [["1", 0]], None, [None]])
def test_metadata_never_waives_invalid_arc_grids(grid):
    assert GEN.self_check(grid, meta={"texture": "no_cells"})


@pytest.mark.parametrize("grid", [
    [[0, 0], [0, 0]], [[7, 0], [0, 0]], [[2, 2], [2, 2]],
    [[0, 3, 3, 0], [0, 0, 0, 0]], [[8]],
])
def test_lawful_gravity_endpoints_remain_accepted(grid):
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []


@pytest.mark.parametrize("texture", ["all_at_bottom", "single_value_columns", "no_cells"])
def test_explicit_edges_honor_dimensions_and_realize_their_structure(texture):
    g = GEN.generate(11, 9, grid_h=6, grid_w=11, texture=texture)
    assert (len(g), len(g[0])) == (6, 11)
    assert GEN.self_check(g) == []
    if texture == "no_cells":
        assert all(v == 0 for row in g for v in row)
    elif texture == "all_at_bottom":
        assert compact(g) == g
    else:
        assert all(sum(v != 0 for v in col) <= 1 for col in zip(*g))


def test_every_declared_canonical_shortcut_really_fits_all_canonical_pairs():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert shortcuts, "a canonical-fit shortcut needs executable coverage"
    pairs = canonical_pairs(TASK, root=ROOT)
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert compact(pair["input"]) == pair["output"]
        for name, rival in shortcuts.items():
            assert rival(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("band", BANDS)
def test_five_pair_windows_keep_a_refutation_after_any_query_holdout(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "teachability cannot be checked with an empty rival family"
    for seed in range(5):
        grids = [GEN.generate(seed, i, difficulty=band) for i in range(15)]
        labels = [compact(g) for g in grids]
        for start in range(11):
            for holdout in range(start, start + 5):
                demos = [i for i in range(start, start + 5) if i != holdout]
                for name, rival in rivals.items():
                    assert any(rival(grids[i]) != labels[i] for i in demos), (seed, start, holdout, name)


@pytest.mark.parametrize("band", BANDS)
def test_determinism_and_no_cross_call_grid_aliasing(band):
    expected = GEN.generate(23, 8, difficulty=band)
    actual = GEN.generate(23, 8, difficulty=band)
    assert actual == expected
    actual[0][0] = (actual[0][0] + 1) % 10
    assert GEN.generate(23, 8, difficulty=band) == expected


@pytest.mark.parametrize("band", BANDS)
def test_free_profile_color_coverage_does_not_overflow_five_cell_columns(band):
    # The first repair added eight colors to one free column (old seed 3/index 5).
    # The five-profile schedule now puts its free draw at index 4.
    g = GEN.generate(3, 4, difficulty=band)
    assert max(sum(value != 0 for value in col) for col in zip(*g)) <= 5
    assert GEN.self_check(g) == []


@pytest.mark.parametrize("band", BANDS)
def test_ordinary_support_includes_long_columns_when_zero_is_modal(band):
    # Independent modal/count observations expose the coupling between two
    # individually refuted rivals; cap-five-when-zero-is-modal used to survive.
    cases = [GEN.generate(seed, i, difficulty=band) for seed in range(5) for i in range(15)]
    def distinguishes(grid):
        counts = Counter(v for row in grid for v in row)
        zero_is_modal = counts[0] > max(n for v, n in counts.items() if v != 0)
        long = any(sum(v != 0 for v in col) > 5 for col in zip(*grid))
        return zero_is_modal and long
    assert any(distinguishes(g) for g in cases), "zero-modal long columns are missing"
