"""Focused regressions for canonical support, exact controls and useful lessons."""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK_ID = "41851e57e1a5"
HOME = ROOT / "generators" / TASK_ID
PROBE_PATH = HOME / "workspace" / "probe_lessons.py"
spec = importlib.util.spec_from_file_location("bbox_lesson_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
GENERATOR_PATH = HOME / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
# Explicit source selection permits the same assertions to reproduce a RED
# run against a retained snapshot without replacing the live implementation.
GENERATOR_PATH = Path(os.environ.get("ARCPUZZLES_TEST_GENERATOR_PATH", GENERATOR_PATH))
gen = probe.load_generator(GENERATOR_PATH)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")


def accepted(result):
    return result is True or result == []


def hand_witness(key=6):
    """Seven-cell connected Ls enclose a wholly empty 3x3 bbox intersection."""
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((2, 2), (3, 2), (4, 2), (5, 2), (5, 3), (5, 4), (5, 5)):
        grid[r][c] = 2
    for r, c in ((1, 3), (1, 4), (1, 5), (1, 6), (2, 6), (3, 6), (4, 6)):
        grid[r][c] = 1
    grid[0][0] = key
    return grid


@pytest.mark.parametrize("pair", CANONICAL,
                         ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_canonical_shape_sizes_and_labels(pair):
    assert probe.predict(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert accepted(gen.strict_canonical_like(pair["input"]))


def test_literal_rectangle_requires_background_and_interior_fill():
    grid = hand_witness()
    before = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert not accepted(gen.strict_canonical_like(grid))
    expected = [[0] * 8 for _ in range(8)]
    for r in (2, 3, 4):
        for c in (3, 4, 5):
            expected[r][c] = 6
    assert probe.predict(grid) == expected
    assert expected[3][4] == 6 and grid[3][4] == 0
    assert grid == before


@pytest.mark.parametrize("height,width", [(13, 17), (30, 30)])
def test_strict_profile_does_not_label_every_lawful_grid_canonical(height, width):
    original = CANONICAL[0]["input"]
    grid = [row + [0] * (width - len(row)) for row in original]
    grid.extend([[0] * width for _ in range(height - len(grid))])
    assert gen.self_check(grid) == []
    assert not accepted(gen.strict_canonical_like(grid))


def invalid_grids():
    yield "empty", []
    yield "empty_row", [[]]
    yield "ragged", [[0], [0, 1]]
    for value in (-1, 10, True, 6.0, "6"):
        grid = hand_witness()
        if value is True:
            # Preserve every color role and connected component: only the
            # illegal bool type changes, so another invariant cannot mask it.
            grid[1][3] = value
        else:
            grid[0][0] = value
        yield f"cell_{value!r}", grid
    for missing in (1, 2, 6):
        grid = hand_witness()
        grid = [[0 if value == missing else value for value in row] for row in grid]
        yield f"missing_{missing}", grid
    grid = hand_witness()
    grid[7][7] = 7
    yield "two_keys", grid
    grid = hand_witness()
    grid[0][0], grid[0][2] = 0, 6
    yield "touching_key", grid
    for color in (1, 2):
        grid = hand_witness()
        grid[7][7] = color
        yield f"disconnected_{color}", grid
    grid = hand_witness()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2 and (r, c) not in ((2, 2), (3, 2)):
                grid[r][c] = 0
    yield "two_cell_shape", grid
    grid = hand_witness() + [[0] * 8 for _ in range(23)]
    yield "height_31", grid
    yield "width_31", [row + [0] * 23 for row in hand_witness()]
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((2, 1), (3, 1), (3, 2)):
        grid[r][c] = 2
    for r, c in ((5, 5), (6, 5), (6, 6)):
        grid[r][c] = 1
    grid[0][7] = 6
    yield "disjoint_bboxes", grid


@pytest.mark.parametrize("name,grid", list(invalid_grids()), ids=lambda value: value if isinstance(value, str) else None)
def test_validator_reports_invalid_inputs(name, grid):
    reasons = gen.self_check(grid)
    assert isinstance(reasons, list) and reasons, name
    assert all(isinstance(reason, str) for reason in reasons)
    assert not accepted(gen.strict_canonical_like(grid)), name


def test_only_three_meaningful_exact_axes():
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "key_color"}
    assert all(gen.AXES[name]["type"] == "int" for name in gen.AXES)


@pytest.mark.parametrize("band", BANDS)
def test_exact_override_boundaries_and_observer_in_every_band(band):
    for h, w in ((8, 8), (8, 20), (20, 8), (20, 20), (13, 17)):
        for key in (3, 6, 9):
            for index in range(3):
                requested = {"grid_h": h, "grid_w": w, "key_color": key}
                grid = gen.generate(17, index, difficulty=band, **requested)
                assert (len(grid), len(grid[0]), probe.key_color(grid)) == (h, w, key)
                assert gen.observe_overrides(grid) == requested
                assert gen.self_check(grid) == []


@pytest.mark.parametrize("name,values", [
    ("grid_h", (7, 21, True, 8.0, "8", None)),
    ("grid_w", (7, 21, False, 12.0, "12", None)),
    ("key_color", (2, 10, True, 6.0, "6", None)),
])
def test_numeric_overrides_are_exact_integers(name, values):
    for band in BANDS:
        for value in values:
            with pytest.raises((TypeError, ValueError), match=".+"):
                gen.generate(0, 0, difficulty=band, **{name: value})


@pytest.mark.parametrize("name,value", [
    ("palette_kind", "warm"), ("palette_size", 3), ("n_distinct_colors", 3),
    ("position_bias", "red_blue_overlap_plus_key"), ("density", "sparse"),
    ("texture", "cool"), ("texture", "no_overlap"), ("unknown_control", 4),
])
def test_unused_and_unknown_controls_fail_clearly(name, value):
    with pytest.raises((TypeError, ValueError), match=".+"):
        gen.generate(0, 0, **{name: value})


@pytest.mark.parametrize("band", BANDS)
def test_repeatability_key_cycle_and_informative_three_example_windows(band):
    for seed in (0, 8, 42):
        grids = [gen.generate(seed, index, difficulty=band) for index in range(15)]
        assert grids[4] == gen.generate(seed, 4, difficulty=band)
        colors = [probe.key_color(grid) for grid in grids]
        assert set(colors[:7]) == set(range(3, 10))
        assert colors[:7] == colors[7:14]
        profiles = [probe.features(grid) for grid in grids]
        for start in range(12):
            assert sum(profile["rich"] for profile in profiles[start:start + 3]) == 2
            assert len(set(colors[start:start + 3])) >= 2
        for grid in grids:
            assert gen.self_check(grid) == []
            assert 8 <= len(grid) <= 20 and 8 <= len(grid[0]) <= 20


def test_default_support_retains_singletons_both_lines_and_rich_rectangles():
    shapes = set()
    blank = False
    five_cell_shape = False
    for band in BANDS:
        for seed in (0, 1, 2, 3, 4, 5, 8, 42):
            for index in range(18):
                profile = probe.features(gen.generate(seed, index, difficulty=band))
                shapes.add((profile["overlap_h"], profile["overlap_w"]))
                blank |= profile["interior_blank_fill"] > 0
                five_cell_shape |= profile["red_size"] == 5 or profile["blue_size"] == 5
    assert (1, 1) in shapes
    assert any(h == 1 and w >= 3 for h, w in shapes)
    assert any(h >= 3 and w == 1 for h, w in shapes)
    assert any(h >= 3 and w >= 3 for h, w in shapes)
    assert blank and five_cell_shape


def test_named_rivals_have_the_claimed_meanings():
    assert set(probe.RIVAL_NAMES) <= set(gen.LESSON_COMPETITORS)
    grids = [hand_witness(), *[pair["input"] for pair in CANONICAL]]
    for name in probe.RIVAL_NAMES:
        for grid in grids:
            assert gen.LESSON_COMPETITORS[name](deepcopy(grid)) == probe.FIXED_RIVALS[name](grid), name


@pytest.mark.parametrize("seed,rival", [(0, "corner_only"), (8, "occupied_only"), (42, "fixed_key_3")])
def test_hook_exposes_retained_weak_baseline_lessons(seed, rival):
    pairs = probe.baseline_lesson(seed)
    expected = probe.ambiguous_rivals(pairs[:3], pairs[3])
    assert rival in expected
    reasons = gen.lesson_identifiable(deepcopy(pairs[:3]), deepcopy(pairs[3]))
    assert isinstance(reasons, list) and reasons
    assert any(rival in reason for reason in reasons), (seed, rival, reasons)
    # A rival agreeing on the query is harmless, even if it survives all demos.
    assert gen.lesson_identifiable(deepcopy(pairs[:3]), deepcopy(pairs[0])) == []


@pytest.mark.parametrize("band", BANDS)
def test_all_cyclic_starts_and_single_query_rotations_identify_the_answer(band):
    for seed in (0, 8, 42):
        pairs = [probe.labeled(gen.generate(seed, index, difficulty=band)) for index in range(15)]
        cache = {}
        for start in range(12):
            window = pairs[start:start + 4]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(window) if index != query_index]
                query = window[query_index]
                score = probe.score_lesson(demos, query, cache=cache)
                failures = [name for name, status in score.items() if status == "ambiguous"]
                assert failures == [], (seed, band, start, query_index, failures)
                assert gen.lesson_identifiable(deepcopy(demos), deepcopy(query)) == []
