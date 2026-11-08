"""Portable, pixel-based regressions for the quadrant rotation analogy.

The oracle and geometry checks are independent of generator helpers and draw
metadata. Canonical examples establish the existing rule; generated examples
must also teach it and honor the five exact public controls.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9d2f7c9e2ac4"
ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("rotation_contract_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
POSITIONS = {"origin": (0, 0), "down": (1, 0), "right": (0, 1), "diagonal": (1, 1)}
AXES = {"grid_n", "shape_variant", "example_color", "source_color", "source_position"}


def _quadrants(grid):
    middle = len(grid) // 2
    spans = {
        "TL": (0, middle, 0, middle),
        "TR": (0, middle, middle + 1, len(grid)),
        "BL": (middle + 1, len(grid), 0, middle),
        "BR": (middle + 1, len(grid), middle + 1, len(grid)),
    }
    return {
        name: {(r - r0, c - c0): grid[r][c]
               for r in range(r0, r1) for c in range(c0, c1)
               if grid[r][c] != 0}
        for name, (r0, r1, c0, c1) in spans.items()
    }


def _offset(cells):
    return min(r for r, _ in cells), min(c for _, c in cells)


def _normalize(cells):
    r0, c0 = _offset(cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _rotate(cells):
    """Clockwise rotation around the object's bbox, retaining bbox offsets."""
    r0, c0 = _offset(cells)
    height = max(r for r, _ in cells) - r0 + 1
    return {(r0 + c - c0, c0 + height - 1 - (r - r0)): color
            for (r, c), color in cells.items()}


def _orbit(cells):
    """Eight square symmetries, computed without generator functions."""
    shape = _normalize(cells)
    signatures = set()
    for reflected in (False, True):
        current = {(r, -c if reflected else c) for r, c in shape}
        for _ in range(4):
            signatures.add(_normalize(current))
            current = {(c, -r) for r, c in current}
    return signatures


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    todo = [remaining.pop()]
    while todo:
        r, c = todo.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in remaining:
                remaining.remove(point)
                todo.append(point)
    return not remaining


def _assert_scene(grid, *, generated=False):
    n = len(grid)
    assert n and all(len(row) == n for row in grid), "grid must be nonempty and square"
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    middle = n // 2
    actual_nines = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9}
    expected_nines = {(middle, i) for i in range(n)} | {(i, middle) for i in range(n)}
    assert actual_nines == expected_nines, "one complete centered cross, with no stray 9s"
    parts = _quadrants(grid)
    for name in ("TL", "TR", "BL"):
        assert parts[name], f"{name} must contain a visible shape"
        assert len(set(parts[name].values())) == 1, f"{name} must be single-color"
        assert _connected(parts[name]), f"{name} must be four-connected"
    assert not parts["BR"], "the query target quadrant must start empty"
    assert parts["TR"] == _rotate(parts["TL"]), "upper panels must show bbox-offset-preserving CW rotation"
    target = _rotate(parts["BL"])
    capacity = n - middle - 1
    assert all(0 <= r < capacity and 0 <= c < capacity for r, c in target), "BR rotation must fit without clipping"
    if generated:
        source = _normalize(parts["BL"])
        assert len(source) in (4, 5, 6)
        assert max(r for r, _ in source) < 3 and max(c for _, c in source) < 3
        assert len(_orbit(source)) == 8, "source must distinguish all eight square symmetries"
        assert source != _normalize(parts["TL"]), "copying the top result must not solve the lower query"
    return parts


def _expected_output(grid):
    output = [row[:] for row in grid]
    start = len(grid) // 2 + 1
    for (r, c), color in _rotate(_quadrants(grid)["BL"]).items():
        assert start + r < len(grid) and start + c < len(grid)
        output[start + r][start + c] = color
    return output


def _make_scene(n=11, *, source=None, source_offset=(1, 0), example_color=8, source_color=1):
    """Hand-authored valid context, independent of the generator under test."""
    grid = [[0] * n for _ in range(n)]
    middle = n // 2
    for i in range(n):
        grid[middle][i] = grid[i][middle] = 9
    top = {(0, 1): example_color, (1, 1): example_color,
           (2, 1): example_color, (2, 2): example_color}
    for (r, c), color in top.items():
        grid[r][c] = color
    for (r, c), color in _rotate(top).items():
        grid[r][middle + 1 + c] = color
    if source is None:
        source = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}
    for r, c in source:
        grid[middle + 1 + source_offset[0] + r][source_offset[1] + c] = source_color
    return grid


def test_generated_grid_has_the_visible_upper_analogy():
    # This is deliberately the first reproduction: fail on pixels, not a new hook.
    grid = gen.generate(41, 0, difficulty="medium", grid_n=11)
    parts = _quadrants(grid)
    assert parts["TL"] and parts["TR"], "baseline drops both upper CW-demonstration shapes"
    _assert_scene(grid, generated=True)


@pytest.mark.parametrize("variant", range(3))
def test_shape_variant_controls_actual_source_cell_count(variant):
    grid = gen.generate(41, 0, grid_n=11, shape_variant=variant)
    source = _quadrants(grid)["BL"]
    assert len(source) == 4 + variant, "shape_variant must control returned pixels, not metadata"
    assert _connected(source)
    normalized = _normalize(source)
    assert max(r for r, _ in normalized) < 3 and max(c for _, c in normalized) < 3


@pytest.mark.parametrize("pair", PAIRS, ids=lambda pair: f"{pair['split']}-{pair['pair_index']}")
def test_all_canonical_inputs_are_accepted_and_oracle_matches_labels(pair):
    assert len(PAIRS) == 3, "retain coverage of both train inputs and the canonical test input"
    _assert_scene(pair["input"])
    assert _expected_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("n", range(9, 16))
def test_every_grid_size_is_exact_in_every_difficulty_band(n, band):
    grid = gen.generate(121, n, difficulty=band, grid_n=n)
    assert len(grid) == n and all(len(row) == n for row in grid), "legal override must not be clamped by difficulty"
    _assert_scene(grid, generated=True)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("position,expected", POSITIONS.items())
@pytest.mark.parametrize("variant", range(3))
def test_position_and_shape_controls_jointly_fit_even_small_quadrants(position, expected, variant):
    grid = gen.generate(1201, 7, grid_n=10, shape_variant=variant, source_position=position)
    source = _quadrants(grid)["BL"]
    assert _offset(source) == expected, "source_position names bbox offsets in BL"
    assert len(source) == 4 + variant
    _assert_scene(grid, generated=True)
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("color", range(1, 9))
def test_all_exact_colors_are_visible_and_equal_colors_are_supported(color):
    for source_color in (color, 9 - color):
        grid = gen.generate(302, color, grid_n=11, example_color=color, source_color=source_color)
        parts = _quadrants(grid)
        assert set(parts["TL"].values()) == {color}
        assert set(parts["TR"].values()) == {color}
        assert set(parts["BL"].values()) == {source_color}
        _assert_scene(grid, generated=True)
        assert gen.self_check(grid) == []


def test_observer_reports_all_axes_from_hand_authored_pixels():
    assert set(gen.AXES) == AXES
    for offset, position, example_color, source_color in [
        ((1, 0), "down", 8, 1),
        ((1, 1), "diagonal", 2, 2),
    ]:
        grid = _make_scene(source_offset=offset, example_color=example_color, source_color=source_color)
        _assert_scene(grid, generated=True)
        assert gen.observe_overrides(grid) == {
            "grid_n": 11,
            "shape_variant": 1,
            "example_color": example_color,
            "source_color": source_color,
            "source_position": position,
        }


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_and_shapes_disambiguate_rotation(band):
    positions = tuple(POSITIONS)
    for seed in (0, 1, 41, 991):
        for index in range(12):
            grid = gen.generate(seed, index, difficulty=band)
            source = _quadrants(grid)["BL"]
            assert len(_orbit(source)) == 8, (seed, index, band, "D4-ambiguous source")
            assert _offset(source) == POSITIONS[positions[index % 4]], (seed, index, band)
            parts = _assert_scene(grid, generated=True)
            assert set(parts["TL"].values()) != set(parts["BL"].values()), "default colors should differ"
            assert gen.self_check(grid) == []
            if index == 0:
                assert grid == gen.generate(seed, index, difficulty=band)
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("axis,invalid_values", [
    ("grid_n", (8, 16, True, 11.0, "11")),
    ("shape_variant", (-1, 3, False, 1.0, "1")),
    ("example_color", (0, 9, True, 2.0, "2")),
    ("source_color", (0, 9, False, 3.0, "3")),
    ("source_position", ("unknown", 0, False, [], {})),
])
def test_invalid_override_values_raise_value_error(axis, invalid_values):
    for value in invalid_values:
        with pytest.raises(ValueError):
            gen.generate(3, 0, **{axis: value})


@pytest.mark.parametrize("value", (1, None))
def test_unknown_override_names_raise_value_error(value):
    with pytest.raises(ValueError):
        gen.generate(3, 0, misspelled_axis=value)


def test_none_for_each_declared_axis_is_identical_to_omission():
    for band in BANDS:
        baseline = gen.generate(3201, 5, difficulty=band)
        assert gen.generate(3201, 5, difficulty=band, **dict.fromkeys(AXES)) == baseline
        for axis in AXES:
            assert gen.generate(3201, 5, difficulty=band, **{axis: None}) == baseline


@pytest.mark.parametrize("malformation", [
    "none", "empty", "zero-width", "ragged", "non-grid", "float-cell", "bool-cell", "invalid-color",
])
def test_self_check_reports_malformed_grids_without_crashing(malformation):
    grid = _make_scene()
    if malformation == "none":
        grid = None
    elif malformation == "empty":
        grid = []
    elif malformation == "zero-width":
        grid = [[]]
    elif malformation == "ragged":
        grid[-1] = grid[-1][:-1]
    elif malformation == "non-grid":
        grid = "not a grid"
    elif malformation == "float-cell":
        grid[-1][-1] = 0.0
    elif malformation == "bool-cell":
        grid[-1][-1] = False
    elif malformation == "invalid-color":
        grid[-1][-1] = 10
    reasons = gen.self_check(grid)
    assert isinstance(reasons, list) and reasons, f"malformed grid was accepted: {malformation}"


@pytest.mark.parametrize("defect", [
    "missing-TL", "missing-TR", "bad-TR", "wrong-TR-color", "wrong-TR-offset",
    "multicolor-BL", "disconnected-BL", "filled-BR", "stray-9", "off-center-cross",
])
def test_self_check_rejects_broken_context_not_only_bad_bl(defect):
    grid = _make_scene()
    middle = len(grid) // 2
    if defect in ("missing-TL", "missing-TR"):
        start, stop = (0, middle) if defect == "missing-TL" else (middle + 1, len(grid))
        for r in range(middle):
            for c in range(start, stop):
                grid[r][c] = 0
    elif defect == "bad-TR":
        grid[0][middle + 2] = 0
    elif defect == "wrong-TR-color":
        for r in range(middle):
            for c in range(middle + 1, len(grid)):
                if grid[r][c]:
                    grid[r][c] = 7
    elif defect == "wrong-TR-offset":
        for r in range(middle - 1, 0, -1):
            grid[r][middle + 1:] = grid[r - 1][middle + 1:]
        grid[0][middle + 1:] = [0] * (len(grid) - middle - 1)
    elif defect == "multicolor-BL":
        grid[middle + 2][0] = 3
    elif defect == "disconnected-BL":
        grid[-1][middle - 1] = 1
    elif defect == "filled-BR":
        grid[-1][-1] = 1
    elif defect == "stray-9":
        grid[-1][-1] = 9
    elif defect == "off-center-cross":
        for c in range(len(grid)):
            grid[middle][c] = 9 if c == middle else 0
            grid[middle - 1][c] = 9
    reasons = gen.self_check(grid)
    assert isinstance(reasons, list) and reasons, f"broken context was accepted: {defect}"


@pytest.mark.parametrize("direction", ("right", "down"))
def test_self_check_rejects_source_that_fits_bl_but_rotation_would_clip(direction):
    if direction == "right":
        grid = _make_scene(10, source={(0, 0), (1, 0), (2, 0), (2, 1)}, source_offset=(0, 3))
    else:
        grid = _make_scene(9, source={(0, 0), (0, 1), (0, 2), (1, 0)}, source_offset=(2, 0))
    parts = _quadrants(grid)
    assert parts["TL"] and parts["TR"] and parts["BL"] and not parts["BR"]
    assert _connected(parts["BL"])
    assert parts["TR"] == _rotate(parts["TL"])
    capacity = len(grid) - len(grid) // 2 - 1
    assert any(r >= capacity or c >= capacity for r, c in _rotate(parts["BL"]))
    assert gen.self_check(grid), "context is valid except the rotated source cannot fit BR"
