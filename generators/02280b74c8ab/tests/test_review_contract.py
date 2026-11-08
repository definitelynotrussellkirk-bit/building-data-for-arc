"""Focused review regressions for the public controls and clean mosaic domain.

The literal code-6/7 label below was executed through Catalog.apply using the
unchanged canonical Racket authority (rule hash a7b2395a133e). Domain rejection
tests enforce this generator's clean, equal-square template contract; they do
not claim that the Racket program is undefined for every rejected grid.
"""
from copy import deepcopy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "02280b74c8ab"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("mosaic_under_review", GENERATOR_PATH)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)

CODE67_INPUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 6, 0, 0, 0, 0, 7, 7, 0, 0],
    [0, 6, 6, 0, 0, 0, 7, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 6, 7, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
CODE67_OUTPUT = [[7, 7, 0, 7], [0, 7, 7, 7]]


def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _selected_templates(grid):
    """Observe monochrome 4-components without importing generator helpers."""
    selected = []
    for color in (6, 7):
        remaining = {(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == color}
        components = []
        while remaining:
            component = {remaining.pop()}
            frontier = list(component)
            while frontier:
                r, c = frontier.pop()
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        frontier.append(neighbor)
            components.append(component)
        assert components, f"no template of color {color}"
        components.sort(key=len, reverse=True)
        assert len(components) == 1 or len(components[0]) > len(components[1])
        selected.append(components[0])
    return selected


def _code_crop(grid):
    used = set.union(*_selected_templates(grid))
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if 1 <= value <= 8 and (r, c) not in used}
    top, left, bottom, right = _bbox(cells)
    return [row[left:right] for row in grid[top:bottom]]


@pytest.mark.parametrize("shape,expected", [
    ("2x4", (2, 4)), ("2x3", (2, 3)), ("3x3", (3, 3)), ("gapped", (2, 4)),
])
def test_code_shape_override_is_observable(shape, expected):
    grid = gen.generate(17, 9, code_shape=shape, tpl_size=2, decor_9=False)
    code = _code_crop(grid)
    assert (len(code), len(code[0])) == expected
    if shape == "gapped":
        assert any(value == 0 for row in code for value in row)
    else:
        assert all(1 <= value <= 8 for row in code for value in row)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_template_size_three_is_honored_in_every_band(band):
    grid = gen.generate(29, 4, difficulty=band, tpl_size=3, decor_9=False)
    for template in _selected_templates(grid):
        top, left, bottom, right = _bbox(template)
        assert (bottom - top, right - left) == (3, 3)


def test_difficulty_changes_the_default_distribution():
    easy = [gen.generate(seed, 2 * seed, difficulty="easy") for seed in range(6)]
    hard = [gen.generate(seed, 2 * seed, difficulty="hard") for seed in range(6)]
    assert easy != hard, "the advertised difficulty knob must affect a draw"
    assert all(gen.self_check(grid) == [] for grid in easy + hard)


def test_default_draw_provenance_matches_observed_controls():
    from puzzle_generators.base import set_ctx_observer

    captured = []
    try:
        set_ctx_observer(captured.append)
        grid = gen.generate(17, 3, difficulty="hard")
    finally:
        set_ctx_observer(None)
    # The supported override checker reads the last published draw context.
    draws = captured[-1].recorded_draws()
    for name, actual in gen.observe_overrides(grid).items():
        assert draws.get(name) == actual, (name, draws.get(name), actual)


def test_defaults_cross_template_size_with_gaps_and_decoration():
    size_decor, size_gap = set(), set()
    for seed in range(3):
        for index in range(10):
            grid = gen.generate(seed, index, difficulty="medium")
            top, left, bottom, right = _bbox(_selected_templates(grid)[0])
            side = bottom - top
            code = _code_crop(grid)
            size_decor.add((side, any(9 in row for row in grid)))
            size_gap.add((side, any(0 in row for row in code)))
    expected = {(2, False), (2, True), (3, False), (3, True)}
    assert size_decor == expected
    assert size_gap == expected


def test_defaults_include_canonical_sparse_asymmetric_and_symmetric_templates():
    for seed in range(3):
        for index in range(10):
            grid = gen.generate(seed, index, difficulty="medium")
            parts = _selected_templates(grid)
            orbits = []
            for cells in parts:
                top, left, bottom, right = _bbox(cells)
                pattern = tuple(tuple(row[left:right]) for row in grid[top:bottom])
                rotations = set()
                for _ in range(4):
                    rotations.add(pattern)
                    pattern = tuple(zip(*pattern[::-1]))
                orbits.append(len(rotations))
            if any(len(parts[i]) in (5, 6) and orbits[i] == 4 and orbits[1-i] == 1
                   for i in range(2)):
                return
    pytest.fail("default sampler omitted the canonical mixed sparse/symmetric texture")


@pytest.mark.parametrize("height,width", [(10, 12), (20, 22)])
def test_advertised_grid_size_boundaries_are_honored(height, width):
    grid = gen.generate(31, 2, grid_h=height, grid_w=width, tpl_size=2)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("overrides", [
    {"code_shape": "unknown"}, {"texture": "unknown"}, {"tpl_size": 4},
    {"decor_9": 2}, {"grid_h": 13.5}, {"grid_w": "15"},
    {"code_shpae": "2x3"}, {"code_shape": "2x3", "texture": "3x3"},
])
def test_invalid_or_conflicting_controls_fail_explicitly(overrides):
    with pytest.raises(ValueError):
        gen.generate(17, 9, **overrides)


def test_self_check_accepts_code_cells_six_and_seven_outside_templates():
    assert gen.self_check(deepcopy(CODE67_INPUT)) == []


def test_self_check_accepts_all_canonical_inputs_including_symmetric_templates():
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        assert gen.self_check(pair["input"]) == [], (
            pair["variant"], pair["split"], pair["pair_index"])


def _ordinary_input():
    grid = deepcopy(CODE67_INPUT)
    grid[5][3:5] = [1, 5]
    return grid


@pytest.mark.parametrize("bad_value", [10, -1, True, "1"])
def test_self_check_reports_invalid_arc_values_without_raising(bad_value):
    grid = _ordinary_input()
    grid[0][0] = bad_value
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("mutation", [
    "unequal_bbox", "foreign_template_cell", "decor_inside_code",
    "template_inside_code_bbox", "oversize_output", "no_code",
])
def test_self_check_rejects_outside_declared_clean_mosaic_domain(mutation):
    grid = _ordinary_input()
    if mutation == "unequal_bbox":
        grid[2][1:3] = [0, 0]
        grid[1][1:4] = [6, 6, 6]
    elif mutation == "foreign_template_cell":
        grid[1][2] = 9
    elif mutation == "decor_inside_code":
        grid[5][3:6] = [1, 9, 5]
    elif mutation == "template_inside_code_bbox":
        grid[0][0] = 1
    elif mutation == "oversize_output":
        grid = [row + [0] * 10 for row in grid]
        grid[5][19] = 1  # code bbox width 17; 2x2 tiles require width 34
    elif mutation == "no_code":
        grid[5][3:5] = [0, 0]
    assert gen.self_check(grid), mutation


def test_literal_and_canonical_labels_match_racket_authority():
    from arcpuzzles import Catalog

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    inputs = [CODE67_INPUT] + [pair["input"] for pair in pairs]
    expected = [CODE67_OUTPUT] + [pair["output"] for pair in pairs]
    receipt = Catalog(ROOT).apply(TASK_ID, inputs, timeout=90)
    assert receipt["rule_hash_matches_catalog"]
    assert all(result["valid_output"] for result in receipt["results"])
    assert [result["output"] for result in receipt["results"]] == expected
