"""Portable regressions for exact controls and the fixed yellow-ring predicate.

The tiny oracle is independent of the implementation. Reference agreement is
checked against every labeled canonical pair; these are authoring tests.
"""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "7494855fa379"
ROOT = find_root(__file__)


def load_generator():
    selected = os.environ.get("GENERATOR_UNDER_TEST")
    if selected:
        source = Path(selected)
    else:
        candidates = (ROOT / "generators" / TASK_ID / "generator.py",
                      ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            raise FileNotFoundError(f"No selected generator under portable root {ROOT}")
    spec = importlib.util.spec_from_file_location("yellow_ring_generator_under_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def centers(grid):
    return [(r, c) for r in range(1, len(grid) - 1)
            for c in range(1, len(grid[0]) - 1)
            if grid[r][c] == 0 and all(grid[r + dr][c + dc] == 4
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if (dr, dc) != (0, 0))]


def oracle(grid):
    result = deepcopy(grid)
    for row, column in centers(grid):
        result[row][column] = 6
    return result


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_independent_predicate_matches_every_canonical_label(pair):
    assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_domain_is_not_a_difficulty_minimum(pair, band):
    assert GEN.self_check(pair["input"], difficulty=band) == []


def test_selected_rule_authority_is_pinned():
    assert getattr(GEN, "RULE_HASH", None) == "856baaecfaa1"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,count", [(6, 8, 1), (7, 9, 2), (11, 13, 4)])
def test_exact_controls_are_honored_across_difficulty_bands(band, height, width, count):
    options = {"grid_h": height, "grid_w": width, "n_blocks": count}
    grid = GEN.generate(17, 3, difficulty=band, **options)
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(centers(grid)) == count
    assert GEN.self_check(grid, difficulty=band) == []
    assert grid == GEN.generate(17, 3, difficulty=band, **options)


def test_infeasible_exact_count_is_reported_instead_of_clipped():
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(0, 0, difficulty="easy", grid_h=5, grid_w=6, n_blocks=2)


@pytest.mark.parametrize("texture", ["solid_squares", "center_already_filled"])
def test_degenerate_controls_preserve_dimensions_and_rule_domain(texture):
    grid = GEN.generate(4, 2, texture=texture, grid_h=7, grid_w=9)
    assert (len(grid), len(grid[0])) == (7, 9)
    assert GEN.self_check(grid) == []
    assert oracle(grid) == grid


def test_no_blocks_remains_an_explicit_negative_fixture_with_exact_dimensions():
    grid = GEN.generate(4, 2, texture="no_blocks", grid_h=7, grid_w=9)
    assert (len(grid), len(grid[0])) == (7, 9)
    assert oracle(grid) == grid
    assert GEN.self_check(grid)
    assert "no_blocks" not in GEN.AXES["texture"]["valid"].split("|")


@pytest.mark.parametrize("options", [
    {"misspelled_control": 1}, {"grid_h": True}, {"grid_w": 7.5},
    {"n_blocks": "2"}, {"texture": "typo"},
])
def test_unknown_or_noninteger_controls_fail_explicitly(options):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **options)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True]], [[0.0]], [[10]], [[-1]]])
def test_malformed_grid_has_diagnostics_without_exception(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_scattered_colors_are_outside_the_selected_sampler_grammar():
    # Reversal: Racket has a total local rule, but the sampler validator should
    # still reject arbitrary unrelated components. The unchanged label is not
    # a claim that this input belongs to the generator's advertised grammar.
    grid = [[0] * 7 for _ in range(6)]
    grid[1][1] = 2
    grid[2][2] = 8
    assert GEN.self_check(grid)
    assert oracle(grid) == grid


@pytest.mark.parametrize("value", [False, True, 4.0, "4", 10, -1])
def test_invalid_cells_are_rejected_even_when_positive_ring_count_survives(value):
    grid = deepcopy(PAIRS[0]["input"])
    # The background corner is outside the singleton canonical ring.
    assert grid[0][0] == 0 and len(centers(grid)) == 1
    grid[0][0] = value
    assert GEN.self_check(grid, difficulty="easy")


@pytest.mark.parametrize("key,value", [
    ("palette_kind", "warm"), ("palette_size", 2),
    ("n_distinct_colors", 2), ("density", "sparse"),
    ("position_bias", "spaced_3x3_hollow_blocks"),
])
def test_removed_noop_axes_are_explicitly_rejected(key, value):
    assert key not in GEN.AXES
    with pytest.raises(ValueError):
        GEN.generate(3, 4, **{key: value})


def contrast_features(grid):
    """Read the three rule-relevant distractors from pixels, independent of hooks."""
    result = {"missing_corner": 0, "other_color": 0, "occupied": 0}
    offsets = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]
    for row in range(1, len(grid) - 1):
        for column in range(1, len(grid[0]) - 1):
            ring = [grid[row + dr][column + dc] for dr, dc in offsets]
            center = grid[row][column]
            if center == 0 and ring.count(4) == 7 and all(
                grid[row + dr][column + dc] == 4 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            ):
                result["missing_corner"] += 1
            if center == 0 and ring[0] not in (0, 4) and all(value == ring[0] for value in ring):
                result["other_color"] += 1
            if center not in (0, 6) and all(value == 4 for value in ring):
                result["occupied"] += 1
    return result


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("count", [1, 2, 6])
def test_exact_contrast_counts_and_all_three_counterexamples(band, count):
    options = {"texture": "contrast", "grid_h": 11, "grid_w": 13, "n_blocks": count}
    grid = GEN.generate(87, 3, difficulty=band, **options)
    assert (len(grid), len(grid[0])) == (11, 13)
    assert len(centers(grid)) == count
    assert contrast_features(grid) == {"missing_corner": 1, "other_color": 1, "occupied": 1}
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == options
    before = deepcopy(grid)
    oracle(grid)
    assert grid == before


def test_contrast_geometry_failure_is_explicit():
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(3, 4, texture="contrast", grid_h=5, grid_w=6, n_blocks=1)


@pytest.mark.parametrize("texture", ["no_blocks", "solid_squares", "center_already_filled"])
def test_degenerate_texture_and_positive_count_are_incompatible(texture):
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 3, texture=texture, grid_h=7, grid_w=9, n_blocks=1)


def test_every_declared_canonical_shortcut_fits_all_labeled_pairs():
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in PAIRS:
            before = deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == before, name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(GEN.LESSON_SCHEDULE_PERIOD))
def test_three_demo_windows_and_all_query_holdouts_refute_declared_rivals(band, start):
    assert type(GEN.LESSON_SCHEDULE_PERIOD) is int and GEN.LESSON_SCHEDULE_PERIOD > 0
    assert len(GEN.SEMANTIC_RIVALS) == 7
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    # Four seeds exercise positions, palette, and count variation for all starts.
    for seed in (0, 17, 491, 881):
        pairs = []
        for index in range(start, start + 4):
            grid = GEN.generate(seed, index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            assert len(centers(grid)) >= 1
            if GEN.schedule_profile(seed, index, band) == "canonical_core":
                assert (len(grid), len(grid[0])) in {(5, 7), (8, 8), (9, 9)}
                assert contrast_features(grid) == {"missing_corner": 0, "other_color": 0, "occupied": 0}
            else:
                assert len(centers(grid)) >= 2
                assert all(contrast_features(grid).values())
            pairs.append({"input": grid, "output": oracle(grid)})
        for rival_name, rival in GEN.SEMANTIC_RIVALS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:3]), rival_name
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            for rival_name, rival in GEN.LESSON_COMPETITORS.items():
                fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
                assert not (fits_demos and rival(query["input"]) != query["output"]), rival_name
            assert GEN.lesson_identifiable(demos, query) == []


def blank(height=7, width=9):
    return [[0] * width for _ in range(height)]


def single_ring():
    grid = blank()
    for row in range(1, 4):
        for column in range(2, 5):
            if (row, column) != (2, 3):
                grid[row][column] = 4
    return grid


@pytest.mark.parametrize("kind", ["singleton", "short_line", "square2", "full_canvas", "shuffled", "broken_ring"])
def test_sampler_grammar_rejects_minimal_impostors_and_damaged_rings(kind):
    grid = blank()
    if kind == "singleton":
        grid[2][3] = 4
    elif kind == "short_line":
        grid[2][3:6] = [4, 4, 4]
    elif kind == "square2":
        for row in (2, 3):
            for column in (3, 4):
                grid[row][column] = 4
    elif kind == "full_canvas":
        grid = [[4] * 9 for _ in range(7)]
    elif kind == "shuffled":
        # Same yellow mass as a ring, deliberately dispersed into eight points.
        for row, column in [(0, 0), (0, 3), (0, 6), (2, 1), (2, 5), (4, 0), (4, 4), (6, 8)]:
            grid[row][column] = 4
    else:
        grid = single_ring()
        # One missing corner is a lawful contrast motif. A missing cardinal
        # side is outside the sampled templates and damages the ring grammar.
        grid[1][3] = 0
    assert GEN.self_check(grid), kind


@pytest.mark.parametrize("center", [0, 4, 8])
def test_sampler_grammar_accepts_positive_and_lawful_noaction_ring_templates(center):
    grid = single_ring()
    grid[2][3] = center
    assert GEN.self_check(grid) == []
    if center:
        assert oracle(grid) == grid
    else:
        assert len(centers(grid)) == 1


def test_missing_corner_only_is_a_lawful_noaction_template():
    grid = single_ring()
    grid[1][2] = 0
    assert GEN.self_check(grid) == []
    assert contrast_features(grid)["missing_corner"] == 1
    assert oracle(grid) == grid


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_two_diagonally_touching_rings_fit_exact_six_by_six_controls(band):
    # Odd index exercises numeric controls overriding the contrast schedule.
    options = {"grid_h": 6, "grid_w": 6, "n_blocks": 2}
    grid = GEN.generate(731, 1, difficulty=band, **options)
    assert (len(grid), len(grid[0])) == (6, 6)
    targets = centers(grid)
    assert len(targets) == 2
    assert abs(targets[0][0] - targets[1][0]) == 3
    assert abs(targets[0][1] - targets[1][1]) == 3
    assert sum(value == 4 for row in grid for value in row) == 16
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == dict(options, texture="default")
    assert grid == GEN.generate(731, 1, difficulty=band, **options)
    output = oracle(grid)
    assert sum(value == 6 for row in output for value in row) == 2


@pytest.mark.parametrize("height,width,count", [(6, 9, 3), (9, 9, 5)])
def test_diagonal_checkerboard_packings_honor_exact_counts(height, width, count):
    options = {"grid_h": height, "grid_w": width, "n_blocks": count}
    grid = GEN.generate(731, 1, **options)
    assert (len(grid), len(grid[0])) == (height, width)
    assert len(centers(grid)) == count
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == dict(options, texture="default")
    assert grid == GEN.generate(731, 1, **options)
