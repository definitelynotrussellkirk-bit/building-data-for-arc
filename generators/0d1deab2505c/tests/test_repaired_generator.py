"""Independent behavioral regressions for the whole-creature wall transfer.

Run through `arcpuzzles check 0d1deab2505c --stage task_tests`.
Expected outputs below are hand-written fixtures, checked against the real
canonical Racket authority through Catalog.apply. No Python diagnostic creates
their labels; no runtime implementation is copied into this test.
"""
from __future__ import annotations

from copy import deepcopy
import importlib
import json
import random

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "0d1deab2505c"
gen = importlib.import_module("puzzle_generators.per_puzzle." + TASK + ".generator")


def canvas(height, width, cells):
    grid = [[8] * width for _ in range(height)]
    for (row, col), color in cells.items():
        assert grid[row][col] == 8, "fixture cells must not overlap"
        grid[row][col] = color
    return grid


# A deliberately asymmetric, noncanonical tail; source and destination overlap.
ASYMMETRIC_INPUT = canvas(9, 13, {
    (3, 4): 4, (2, 4): 2, (3, 5): 3, (4, 4): 5, (3, 3): 6,
    (3, 6): 1, (3, 7): 1, (2, 8): 1, (4, 8): 1, (5, 9): 1,
})
ASYMMETRIC_OUTPUT = canvas(9, 13, {
    (3, 1): 4, (2, 1): 5, (3, 2): 6, (4, 1): 2, (3, 0): 3,
    (3, 3): 1, (3, 4): 1, (2, 5): 1, (4, 5): 1, (5, 6): 1,
})

# The winding tail extends left of the body. The WHOLE creature bbox must
# touch the wall: the destination center is column 3, not column 1.
WINDING_INPUT = canvas(9, 13, {
    (3, 4): 4, (2, 4): 2, (3, 5): 3, (4, 4): 5, (3, 3): 6,
    (3, 6): 1, (2, 7): 1, (1, 7): 1, (0, 7): 1, (0, 6): 1,
    (0, 5): 1, (0, 4): 1, (0, 3): 1, (0, 2): 1, (1, 1): 1,
    (2, 1): 1, (3, 1): 1, (4, 1): 1, (5, 1): 1, (6, 2): 1,
})
WINDING_OUTPUT = canvas(9, 13, {
    (3, 3): 4, (2, 3): 5, (3, 4): 6, (4, 3): 2, (3, 2): 3,
    (3, 5): 1, (2, 6): 1, (1, 6): 1, (0, 6): 1, (0, 5): 1,
    (0, 4): 1, (0, 3): 1, (0, 2): 1, (0, 1): 1, (1, 0): 1,
    (2, 0): 1, (3, 0): 1, (4, 0): 1, (5, 0): 1, (6, 1): 1,
})

# Opposite movements, unrelated palettes, and genuine foreground color zero.
MULTI_INPUT = canvas(11, 14, {
    (2, 4): 4, (1, 4): 2, (2, 5): 3, (3, 4): 5, (2, 3): 6,
    (2, 6): 1, (2, 7): 1, (1, 8): 1,
    (8, 9): 4, (7, 9): 0, (8, 10): 7, (9, 9): 9, (8, 8): 2,
    (8, 7): 1, (9, 6): 1,
})
MULTI_OUTPUT = canvas(11, 14, {
    (2, 1): 4, (1, 1): 5, (2, 2): 6, (3, 1): 2, (2, 0): 3,
    (2, 3): 1, (2, 4): 1, (1, 5): 1,
    (8, 12): 4, (7, 12): 9, (8, 13): 2, (9, 12): 0, (8, 11): 7,
    (8, 10): 1, (9, 9): 1,
})


def rotate(grid):
    """Rigidly rotate an already labeled fixture, not infer an answer."""
    return [list(row) for row in zip(*grid[::-1])]


HANDMADE = []
_pair = ASYMMETRIC_INPUT, ASYMMETRIC_OUTPUT
for _direction in ("right", "down", "left", "up"):
    HANDMADE.append((_direction, *_pair))
    _pair = rotate(_pair[0]), rotate(_pair[1])
HANDMADE += [("winding_bbox", WINDING_INPUT, WINDING_OUTPUT),
             ("opposite_creatures", MULTI_INPUT, MULTI_OUTPUT)]


@pytest.fixture(scope="module")
def canonical():
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    unique = {}
    for pair in pairs:
        key = json.dumps(pair["input"])
        if key in unique:
            assert pair["output"] == unique[key]["output"]
        unique[key] = pair
    assert len(unique) == 4, "do not silently lose any canonical example"
    assert {sum(row.count(4) for row in pair["input"])
            for pair in unique.values()} == {1, 2, 3, 4}
    return list(unique.values())


@pytest.fixture(scope="module")
def scheduled():
    return [(difficulty, [gen.generate(311, index, difficulty=difficulty)
                          for index in range(4)])
            for difficulty in ("easy", "medium", "hard")]


@pytest.fixture(scope="module")
def authority(canonical, scheduled):
    catalog = Catalog(find_root(__file__))
    inputs = [pair["input"] for pair in canonical]
    inputs += [pair[1] for pair in HANDMADE]
    inputs += [grid for _, grids in scheduled for grid in grids]
    result = catalog.apply(TASK, inputs, reference="canonical", timeout=300)
    assert result["rule_hash_matches_catalog"] is True
    assert result["generator_sha256"] == catalog.describe(TASK)["generator_sha256"]
    assert len(result["results"]) == len(inputs)
    assert all(row["error"] is None for row in result["results"]), result
    return result["results"]


def test_every_canonical_input_is_accepted_and_reproduced(canonical, authority):
    for pair, actual in zip(canonical, authority):
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        creatures = gen.parse_creatures(pair["input"])
        assert len(creatures) == sum(row.count(4) for row in pair["input"])
        assert 1 <= len(creatures) <= 4
        assert actual["output"] == pair["output"]
        assert gen.diagnostic_transform(pair["input"]) == pair["output"]


@pytest.mark.parametrize("index", range(len(HANDMADE)),
                         ids=[pair[0] for pair in HANDMADE])
def test_handmade_expected_outputs_against_racket(index, canonical, authority):
    _, inp, expected = HANDMADE[index]
    before = deepcopy(inp)
    assert gen.self_check(inp) == []
    assert gen.strict_canonical_like(inp) == []
    assert gen.diagnostic_transform(inp) == expected
    assert authority[len(canonical) + index]["output"] == expected
    assert inp == before, "parsing and diagnostics must not mutate the input"


def damaged(name):
    grid = deepcopy(ASYMMETRIC_INPUT)
    if name == "missing_center":
        grid[3][4] = 8
    elif name == "missing_arm":
        grid[2][4] = 8
    elif name == "duplicate_arms":
        grid[2][4] = grid[4][4]
    elif name == "tail_color_arm":
        grid[2][4] = 1
    elif name == "missing_tail":
        grid = [[8 if color == 1 else color for color in row] for row in grid]
    elif name == "stray_tail":
        grid[8][12] = 1
    elif name == "stray_foreground":
        grid[8][12] = 7
    elif name == "ambiguous_tail_root":
        grid[1][4] = 1
    elif name == "extra_center_without_body":
        grid[8][12] = 4
    else:
        raise AssertionError(name)
    return grid


@pytest.mark.parametrize("name", [
    "missing_center", "missing_arm", "duplicate_arms", "tail_color_arm",
    "missing_tail", "stray_tail", "stray_foreground", "ambiguous_tail_root",
    "extra_center_without_body",
])
def test_structurally_invalid_inputs_rejected(name):
    grid = damaged(name)
    assert gen.self_check(grid), name
    assert gen.strict_canonical_like(grid), name


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[8, 8], [8]], [[True]], [[1.0]], [[10]], [[-1]],
    [[8] * 8 for _ in range(8)],
])
def test_malformed_or_empty_inputs_reject_without_crashing(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


def test_two_creatures_cannot_claim_one_connected_tail():
    grid = canvas(9, 15, {
        (3, 4): 4, (2, 4): 2, (3, 5): 3, (4, 4): 5, (3, 3): 6,
        (3, 10): 4, (2, 10): 0, (3, 11): 7, (4, 10): 9, (3, 9): 2,
        (3, 6): 1, (3, 7): 1, (3, 8): 1,
    })
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


def test_disjoint_inputs_with_colliding_destinations_reject():
    grid = canvas(9, 16, {
        (3, 3): 4, (2, 3): 2, (3, 4): 3, (4, 3): 5, (3, 2): 6,
        (3, 5): 1, (3, 6): 1,
        (3, 10): 4, (2, 10): 0, (3, 11): 7, (4, 10): 9, (3, 9): 2,
        (3, 12): 1, (3, 13): 1,
    })
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


INTEGER_AXES = ("grid_h", "grid_w", "creature_count", "tail_length", "palette_size")


@pytest.mark.parametrize("axis", INTEGER_AXES)
@pytest.mark.parametrize("value", [True, 2.0, "2"])
def test_integer_axes_do_not_coerce_invalid_types(axis, value):
    with pytest.raises(ValueError):
        gen.generate(107, 0, **{axis: value})


@pytest.mark.parametrize("axis,value", [
    ("grid_h", 4), ("grid_h", 25), ("grid_w", 4), ("grid_w", 25),
    ("creature_count", 0), ("creature_count", 5),
    ("tail_length", 0), ("tail_length", 6),
    ("palette_size", 6), ("palette_size", 11),
])
def test_axis_bounds_are_global_and_explicit(axis, value):
    with pytest.raises(ValueError):
        gen.generate(107, 0, **{axis: value})


@pytest.mark.parametrize("overrides", [
    {"tail_branch": 1}, {"tail_branch": "true"},
    {"tail_direction": "diagonal"}, {"unknown_axis": 3},
])
def test_other_invalid_axes_reject(overrides):
    with pytest.raises(ValueError):
        gen.generate(107, 0, **overrides)


EXACT_SETTINGS = [
    dict(grid_h=5, grid_w=5, creature_count=1, tail_direction="right",
         tail_length=1, tail_branch=False, palette_size=7),
    dict(grid_h=24, grid_w=24, creature_count=4, tail_direction="left",
         tail_length=5, tail_branch=True, palette_size=10),
    dict(grid_h=16, grid_w=12, creature_count=2, tail_direction="up",
         tail_length=3, tail_branch=False, palette_size=8),
    dict(grid_h=15, grid_w=19, creature_count=3, tail_direction="down",
         tail_length=2, tail_branch=True, palette_size=9),
]


@pytest.mark.parametrize("settings", EXACT_SETTINGS)
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_compatible_exact_overrides_across_difficulty(settings, difficulty):
    grid = gen.generate(241, 5, difficulty=difficulty, **settings)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    for axis, requested in settings.items():
        assert observed[axis] == requested, (axis, requested, observed)
    assert len(grid) == settings["grid_h"]
    assert all(len(row) == settings["grid_w"] for row in grid)
    assert sum(row.count(4) for row in grid) == settings["creature_count"]
    assert len({color for row in grid for color in row}) == settings["palette_size"]
    for creature in gen.parse_creatures(grid):
        row, col = creature["center"]
        dr, dc = {"right": (0, 1), "left": (0, -1),
                  "down": (1, 0), "up": (-1, 0)}[creature["direction"]]
        # Independently count the declared consecutive axial stem.
        stem = 0
        for distance in range(2, 8):
            rr, cc = row + distance * dr, col + distance * dc
            if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])
                    and grid[rr][cc] == 1):
                break
            stem += 1
        assert stem == settings["tail_length"]
        # A pin applies to every creature, not merely the first lane.
        assert len(creature["tail"]) == stem + (2 if settings["tail_branch"] else 0)


@pytest.mark.parametrize("settings", [
    {"grid_h": 5, "grid_w": 5, "creature_count": 4},
    {"creature_count": 1, "palette_size": 10},
    {"grid_w": 5, "tail_direction": "right", "tail_length": 5},
])
def test_incompatible_pins_report_conflict_without_relaxing(settings):
    with pytest.raises(ValueError) as error:
        gen.generate(107, 0, **settings)
    assert getattr(error.value, "incompatible_axes", None), str(error.value)
    assert set(error.value.incompatible_axes) <= set(settings)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_seed_replay_is_independent_of_global_rng_and_call_order(difficulty):
    first = gen.generate(8081, 17, difficulty=difficulty)
    first_bytes = json.dumps(first, separators=(",", ":"))
    random.seed(99)
    for index in (55, 0, 18, 4):
        gen.generate(8081, index, difficulty=difficulty)
    random.seed(707)
    repeated = gen.generate(8081, 17, difficulty=difficulty)
    assert json.dumps(repeated, separators=(",", ":")) == first_bytes
    assert gen.self_check(repeated) == []


@pytest.mark.parametrize("name,inp,expected", [
    ("canonical_tail_template", ASYMMETRIC_INPUT, ASYMMETRIC_OUTPUT),
    ("copy_first_tail", MULTI_INPUT, MULTI_OUTPUT),
])
def test_declared_shortcuts_fit_canonical_and_have_real_counterexamples(
        canonical, name, inp, expected):
    rival = gen.CANONICAL_SHORTCUTS[name]
    for pair in canonical:
        assert rival(pair["input"]) == pair["output"]
    assert rival(inp) != expected


def test_lesson_hook_reports_a_canonical_fitting_tail_shortcut(canonical):
    query = {"input": ASYMMETRIC_INPUT, "output": ASYMMETRIC_OUTPUT}
    reasons = gen.lesson_identifiable(canonical, query)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) for reason in reasons)
    assert any("canonical_tail_template" in reason for reason in reasons)
    # A distinct, rotated asymmetric demo supplies the missing evidence.
    # copy_first_tail survives but agrees on this one-creature query.
    rotated_demo = {"input": HANDMADE[1][1], "output": HANDMADE[1][2]}
    assert rotated_demo["input"] != query["input"]
    assert gen.lesson_identifiable(canonical + [rotated_demo], query) == []
    # The lesson decision must not peek at the stored query answer.
    hidden_answer = {"input": query["input"], "output": [[0]]}
    assert gen.lesson_identifiable(canonical, hidden_answer) == reasons
    assert gen.lesson_identifiable(canonical + [rotated_demo], hidden_answer) == []


@pytest.mark.parametrize("band_index", range(3), ids=["easy", "medium", "hard"])
def test_scheduled_lessons_have_true_refutations_in_every_query_rotation(
        band_index, canonical, scheduled, authority):
    _, grids = scheduled[band_index]
    start = len(canonical) + len(HANDMADE) + 4 * band_index
    pairs = [{"input": grid, "output": authority[start + index]["output"]}
             for index, grid in enumerate(grids)]
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.diagnostic_transform(pair["input"]) == pair["output"]
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
        assert gen.lesson_identifiable(demos, query) == []
