"""Focused regressions for seeded rectangular frames, using a pixel oracle."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest

TASK_ID = "59c2f0a5d4a9"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BOUNDS = {
    "grid_h": (9, 20),
    "grid_w": (9, 20),
    "n_frames": (2, 4),
    "n_seeded": (1, 4),
    "max_seeds_per_frame": (1, 4),
    "n_outside_seeds": (0, 3),
}
BANDS = (None, "easy", "medium", "hard")


@pytest.fixture(scope="module")
def gen():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"tested_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _draw_scene(boxes, seeds, outside=(), *, h=9, w=9):
    grid = [[0] * w for _ in range(h)]
    for top, left, bottom, right in boxes:
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    grid[r][c] = 1
    for r, c in [*seeds, *outside]:
        grid[r][c] = 2
    return grid


def _one_seed_scene():
    return _draw_scene([(0, 0, 3, 3), (0, 5, 3, 8)], [(1, 1)])


def _pixel_scene(grid):
    """Independently extract full frames and the input-to-output operation."""
    assert isinstance(grid, list) and grid
    assert all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    assert grid[0]
    assert all(type(value) is int and value in (0, 1, 2) for row in grid for value in row)
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    boxes = []
    counts = []
    output = deepcopy(grid)
    while pending:
        start = min(pending)
        pending.remove(start)
        component, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in pending:
                    pending.remove(cell)
                    component.add(cell)
                    todo.append(cell)
        top = min(r for r, _ in component)
        bottom = max(r for r, _ in component)
        left = min(c for _, c in component)
        right = max(c for _, c in component)
        assert bottom - top >= 2 and right - left >= 2
        border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        assert component == border
        interior = [(r, c) for r in range(top + 1, bottom) for c in range(left + 1, right)]
        assert all(grid[r][c] in (0, 2) for r, c in interior)
        count = sum(grid[r][c] == 2 for r, c in interior)
        if count:
            for r, c in interior:
                output[r][c] = 4
        boxes.append((top, left, bottom, right))
        counts.append(count)
    assert 2 <= len(boxes) <= 4
    for i, (top, left, bottom, right) in enumerate(boxes):
        for t, l, b, r in boxes[i + 1:]:
            assert bottom + 1 < t or b + 1 < top or right + 1 < l or r + 1 < left
    assert any(counts)
    observed = {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(boxes),
        "n_seeded": sum(count > 0 for count in counts),
        "max_seeds_per_frame": max(counts),
        "n_outside_seeds": sum(v == 2 for row in grid for v in row) - sum(counts),
    }
    return observed, counts, output


def _canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    task_key = re.compile(r'"task_id"\s*:\s*"' + TASK_ID + r'"')
    with path.open() as stream:
        for line in stream:
            if task_key.search(line):
                row = json.loads(line)
                tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
                pairs = [*row["train"], *tests]
                return [{key: [[int(v) for v in line] for line in pair[key]]
                         for key in ("input", "output")} for pair in pairs]
    raise AssertionError(f"canonical row {TASK_ID} is missing")


def test_declared_axes_are_exact_pixel_controls(gen):
    assert set(gen.AXES) == set(BOUNDS)
    assert all(gen.AXES[key]["type"] == "int" for key in BOUNDS)


def test_accepts_every_canonical_input_including_two_seeded_query(gen):
    pairs = _canonical_pairs()
    assert _pixel_scene(pairs[-1]["input"])[0]["n_seeded"] == 2
    for pair in pairs:
        assert _pixel_scene(pair["input"])[2] == pair["output"]
        assert gen.self_check(deepcopy(pair["input"])) == []


def test_accepts_genuine_one_cell_gap_multiple_markers_and_exterior_seed(gen):
    grid = _draw_scene([(0, 0, 3, 3), (0, 5, 3, 8)], [(1, 1), (2, 2), (1, 6)], [(8, 8)])
    assert _pixel_scene(grid)[0]["n_seeded"] == 2
    assert gen.self_check(grid) == []


_SHORT_ROW = _one_seed_scene()
_SHORT_ROW[-1].pop()
_LONG_ROW = _one_seed_scene()
_LONG_ROW[-1].append(0)


@pytest.mark.parametrize("grid", [None, [], [[]], _SHORT_ROW, _LONG_ROW],
                         ids=["none", "empty", "empty-row", "short-row", "long-row"])
def test_malformed_grid_returns_diagnostics_without_raising(gen, grid):
    errors = gen.self_check(deepcopy(grid))
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


def test_rejects_alien_colors_boolean_and_noninteger_cells(gen):
    accepted = []
    for bad_value in (10, 3, True, 1.0):
        grid = _one_seed_scene()
        grid[8][0] = bad_value
        if not gen.self_check(grid):
            accepted.append(repr(bad_value))
    assert not accepted, f"invalid cells accepted: {accepted}"


@pytest.mark.parametrize("kind", ["incomplete", "filled", "nested", "touching", "unseeded"])
def test_rejects_invalid_frame_topology_and_absent_interior_seed(gen, kind):
    grid = _one_seed_scene()
    if kind == "incomplete":
        grid[0][1] = 0
    elif kind == "filled":
        # A two-row solid blue rectangle has no interior and is not a frame.
        grid = _draw_scene([(0, 0, 3, 3), (0, 5, 1, 8)], [(1, 1)])
    elif kind == "nested":
        grid = _draw_scene([(0, 0, 6, 6), (2, 2, 4, 4)], [(1, 1)])
    elif kind == "touching":
        # Diagonal contact is missed by a four-connected component count.
        grid = _draw_scene([(0, 0, 3, 3), (4, 4, 7, 7)], [(1, 1)])
    elif kind == "unseeded":
        grid[1][1] = 0
        grid[8][8] = 2
    assert gen.self_check(grid), kind


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_smallest_grid_supports_all_maximum_counts_in_every_band(gen, band):
    options = {"grid_h": 9, "grid_w": 9, "n_frames": 4, "n_seeded": 4,
               "max_seeds_per_frame": 4, "n_outside_seeds": 3}
    grid = gen.generate(17, 5, difficulty=band, **options)
    observed, counts, _ = _pixel_scene(grid)
    assert observed == options
    assert 1 in counts and 4 in counts
    assert gen.observe_overrides(grid) == options
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.generate(17, 5, difficulty=band, **options) == grid


def test_every_declared_integer_domain_is_supported_in_every_band(gen):
    base = {"grid_h": 12, "grid_w": 12, "n_frames": 4, "n_seeded": 1,
            "max_seeds_per_frame": 1, "n_outside_seeds": 0}
    for band in BANDS:
        for key, (low, high) in BOUNDS.items():
            for value in range(low, high + 1):
                options = {**base, key: value}
                grid = gen.generate(29, 4, difficulty=band, **options)
                assert _pixel_scene(grid)[0] == options, (band, key, value)
                assert gen.observe_overrides(grid) == options
                assert gen.self_check(grid, difficulty=band) == []


def test_unknown_out_of_range_and_nongenuine_integer_overrides_are_rejected(gen):
    bad_options = [{"typo_axis": 1}]
    for key, (low, high) in BOUNDS.items():
        bad_options.extend({key: value} for value in (low - 1, high + 1, True, float(low), str(low), None))
    accepted = []
    for options in bad_options:
        try:
            gen.generate(7, 0, **options)
        except ValueError:
            pass
        else:
            accepted.append(options)
    assert not accepted, f"invalid overrides accepted: {accepted}"


def test_incompatible_explicit_frame_counts_raise_structured_value_error(gen):
    for band in BANDS:
        with pytest.raises(ValueError) as failure:
            gen.generate(11, 0, difficulty=band, n_frames=2, n_seeded=3)
        assert set(failure.value.incompatible_axes) == {"n_frames", "n_seeded"}


def test_observer_measures_pixels_and_does_not_require_generator_metadata(gen):
    grid = _draw_scene([(0, 0, 3, 3), (0, 5, 3, 8)], [(1, 1), (2, 2), (1, 6)], [(8, 8)])
    assert gen.observe_overrides(grid) == _pixel_scene(grid)[0]
    grid[2][1] = 2
    assert gen.observe_overrides(grid)["max_seeds_per_frame"] == 3
    grid[8][8] = 0
    assert gen.observe_overrides(grid)["n_outside_seeds"] == 0


def test_default_schedule_is_deterministic_and_covers_three_semantic_states(gen):
    for band in BANDS:
        for seed in (0, 17, 29):
            for index in range(6):
                grid = gen.generate(seed, index, difficulty=band)
                assert grid == gen.generate(seed, index, difficulty=band)
                observed, counts, _ = _pixel_scene(grid)
                assert gen.observe_overrides(grid) == observed
                assert gen.self_check(grid, difficulty=band) == []
                assert all(low <= observed[key] <= high for key, (low, high) in BOUNDS.items())
                if index % 3 == 0:
                    assert 1 <= observed["n_seeded"] < observed["n_frames"]
                    assert (observed["max_seeds_per_frame"], observed["n_outside_seeds"]) == (1, 0)
                elif index % 3 == 1:
                    assert observed["n_seeded"] >= 2
                    assert observed["max_seeds_per_frame"] >= 2
                    assert 1 in counts
                else:
                    assert observed["n_outside_seeds"] >= 1
                    assert observed["n_seeded"] < observed["n_frames"]


def test_validation_observation_and_replay_do_not_mutate_or_alias_grids(gen):
    first = gen.generate(31, 0, difficulty="medium")
    original = deepcopy(first)
    assert gen.self_check(first) == []
    gen.observe_overrides(first)
    assert first == original
    replay = gen.generate(31, 0, difficulty="medium")
    assert replay == original and replay is not first
    assert len({id(row) for row in first}) == len(first)
    assert not ({id(row) for row in first} & {id(row) for row in replay})
    first[0][0] = 9
    assert replay == original
    assert gen.generate(31, 0, difficulty="medium") == original


def test_default_supports_multiple_single_marker_frames_without_exterior_red(gen):
    for band in BANDS:
        observations = [gen.observe_overrides(gen.generate(seed, 0, difficulty=band))
                        for seed in range(100)]
        assert any(o['n_seeded'] >= 2 and o['max_seeds_per_frame'] == 1
                   and o['n_outside_seeds'] == 0 for o in observations), band


def test_three_frame_layout_can_stagger_across_a_shared_column_gap(gen):
    # The canonical 12x12 query's lower frame bridges the upper pair's column
    # gap. A rigid2x2 partition can never cover every internal blue column.
    witnessed = False
    for seed in range(100):
        grid = gen.generate(seed, 0, grid_h=12, grid_w=12, n_frames=3)
        cols = {c for row in grid for c, color in enumerate(row) if color == 1}
        if cols == set(range(min(cols), max(cols)+1)):
            witnessed = True
            break
    assert witnessed, 'No staggered three-frame arrangement was generated in seeds0..99'
