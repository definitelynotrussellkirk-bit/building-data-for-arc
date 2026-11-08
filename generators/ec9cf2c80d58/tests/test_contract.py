"""Regressions for observable controls, task structure, and teaching support."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "ec9cf2c80d58"
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_band_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_an_actual_integer(seed):
    with pytest.raises(TypeError):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75])
def test_sample_index_requires_an_actual_integer(sample_index):
    with pytest.raises(TypeError):
        GEN.generate(991, sample_index)


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError):
        GEN.generate(991, -1)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("orientation", ["horizontal", "vertical"])
@pytest.mark.parametrize("shape", [(9, 12), (14, 13)])
def test_requested_dimensions_are_final_coordinates(difficulty, orientation, shape):
    h, w = shape
    grid = GEN.generate(0, 0, difficulty=difficulty, grid_h=h, grid_w=w,
                        orientation=orientation)
    assert (len(grid), len(grid[0])) == shape
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("name,value", [("n_bands", 5), ("palette_size", 6),
                                        ("n_distinct_colors", 6)])
def test_count_controls_are_observable_in_all_bands(name, value):
    for difficulty in ("easy", "medium", "hard"):
        grid = GEN.generate(3, 1, difficulty=difficulty, **{name: value})
        assert len({v for row in grid for v in row if v}) == 5
        assert len({v for row in grid for v in row}) == 6
        assert GEN.observe_overrides(grid)[name] == value


def test_palette_compatibility_aliases_cover_their_full_range():
    # Shared AXES lists independent controls; aliases need their own matrix.
    for alias in ("palette_size", "n_distinct_colors"):
        for value in range(3, 7):
            for difficulty in ("easy", "medium", "hard"):
                grid = GEN.generate(7, 9, difficulty=difficulty, **{alias: value})
                assert len({v for row in grid for v in row}) == value
                assert GEN.observe_overrides(grid)["n_bands"] == value - 1


@pytest.mark.parametrize("options", [
    {"unknown_typo": 1}, {"orientation": "diagonal"},
    {"grid_h": True}, {"grid_w": 12.5}, {"n_bands": "3"},
    {"palette_size": 2}, {"n_distinct_colors": 7},
])
def test_invalid_controls_fail_loudly(options):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, **options)


@pytest.mark.parametrize("options", [
    {"n_bands": 2, "palette_size": 5},
    {"palette_size": 3, "n_distinct_colors": 6},
    {"grid_h": 6, "grid_w": 6, "n_bands": 5},
])
def test_incompatible_exact_controls_have_structured_rejection(options):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, **options)
    assert set(caught.value.incompatible_axes).issubset(options)
    assert len(caught.value.incompatible_axes) >= 2


@pytest.mark.parametrize("grid", [
    [], [[1, 0, 1], [2, 2]], [[1, False, 1], [2, 2, 2]],
    [[1, 0], [2, 3]], [[1, 0, 1], [1, 1, 1]],
    [[1, 0, 1], [1, 1, 1], [2, 2, 2], [2, 2, 12]],
])
def test_malformed_or_non_band_inputs_are_rejected_without_crashing(grid):
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list) and reasons


def test_every_canonical_variant_is_accepted():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []


def test_canonical_shape_and_palette_remain_in_every_difficulty():
    profiles = {(len(p["input"]), len(p["input"][0]),
                 len({v for row in p["input"] for v in row}))
                for p in canonical_pairs(TASK, root=ROOT)}
    for difficulty in ("easy", "medium", "hard"):
        generated = [GEN.generate(71, i, difficulty=difficulty) for i in range(20)]
        assert any((len(g), len(g[0]), len({v for row in g for v in row})) in profiles
                   for g in generated)


def test_reflected_teaching_holes_keep_the_selected_neighbor_in_the_band():
    # Seed 3, index 5 exposed the prior bottom-edge/left-neighbor crossover.
    for seed in range(8):
        for index in range(1, 24, 2):
            grid = GEN.generate(seed, index, difficulty="easy")
            assert GEN.self_check(grid) == [], (seed, index)
            expected = GEN.rule_model(grid)
            assert all(rival(grid) != expected
                       for rival in GEN.LESSON_COMPETITORS.values()), (seed, index)


@pytest.mark.parametrize("seed,index", [(2, 57), (2, 61), (4, 41)])
def test_reflected_pair_at_top_edge_cannot_select_the_other_band(seed, index):
    grid = GEN.generate(seed, index, difficulty="easy")
    assert GEN.self_check(grid) == []
    expected = GEN.rule_model(grid)
    assert all(rival(grid) != expected for rival in GEN.LESSON_COMPETITORS.values())


@pytest.mark.parametrize("grid,expected", [
    ([[1, 1, 1], [0, 1, 1], [2, 2, 2], [0, 2, 2]],
     [[0, 1, 1], [0, 1, 1], [0, 2, 2], [0, 2, 2]]),
    ([[1, 1, 2, 2], [0, 1, 2, 2], [0, 1, 2, 2]],
     [[1, 1, 2, 2], [0, 0, 2, 2], [0, 0, 2, 2]]),
    ([[0, 1, 0, 2], [0, 1, 2, 2], [1, 1, 2, 2]],
     [[0, 1, 0, 2], [0, 0, 0, 2], [0, 1, 0, 2]]),
])
def test_analysis_model_preserves_zero_extent_ties_and_original_grid(grid, expected):
    assert GEN.self_check(grid) == []
    assert GEN.rule_model(grid) == expected


def _audited_profile_template_rival(grid):
    """Retained audit rival: special-case v4 teaching, else perpendicular."""
    layout = GEN._layout(grid)
    if layout is None:
        return [row[:] for row in grid]
    orientation, bands = layout
    height, width = len(grid), len(grid[0])
    holes = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 0]
    teaching = (orientation == "vertical" and len(bands) == 2
                and width == 2 * (height - 1) and len(holes) == 3)
    output = [row[:] for row in grid]
    for row, col in holes:
        color = GEN._neighbor(grid, row, col)
        if color is None:
            continue
        clear_column = (sum(other_row == row for other_row, _ in holes) >= 2
                        if teaching else orientation == "horizontal")
        cells = (((r, col) for r in range(height)) if clear_column
                 else ((row, c) for c in range(width)))
        for r, c in cells:
            if grid[r][c] in (0, color):
                output[r][c] = 0
    return output


def test_retained_profile_shortcut_is_refuted_by_the_seed2_rotation():
    pairs = []
    for index in (7, 8, 9, 10):
        grid = GEN.generate(2, index, difficulty="easy")
        pairs.append({"input": grid, "output": GEN.rule_model(grid)})
    demos = pairs[:3]
    query = pairs[3]
    assert any(_audited_profile_template_rival(pair["input"]) != pair["output"]
               for pair in demos)
    assert GEN.lesson_identifiable(demos, query) == []


def test_each_rotated_default_lesson_refutes_declared_wrong_rules():
    # Exact labels for this Python model are checked separately against Racket.
    # This test catches a lost/reordered teaching slot and too-short lessons.
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(8):
                pairs = [{"input": (g := GEN.generate(seed, start+i,
                                                       difficulty=difficulty)),
                          "output": GEN.rule_model(g)} for i in range(4)]
                for query_index, query in enumerate(pairs):
                    demos = [p for i, p in enumerate(pairs) if i != query_index]
                    assert GEN.lesson_identifiable(demos, query) == []
                    for rival in GEN.LESSON_COMPETITORS.values():
                        assert any(rival(p["input"]) != p["output"] for p in demos)
