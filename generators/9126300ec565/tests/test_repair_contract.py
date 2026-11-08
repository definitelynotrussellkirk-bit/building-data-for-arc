"""Public input/override regressions for the frame-symmetry repair.

These tests inspect observable grids and hand-checked fixtures.  They do not
call private generator helpers or implement a substitute label authority.
Run from the packet with its Racket wrapper, or in a staged task-test runtime.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "9126300ec565"
ROOT = find_root(__file__)


@pytest.fixture(scope="module")
def generator():
    paths = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in paths if path.is_file()), None)
    assert source is not None, f"Missing selected generator under {ROOT}"
    spec = importlib.util.spec_from_file_location("frame_repair_contract_target", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT)


def _fixture():
    """9x14 canvas; 5x7 color-6 frame at (2,3); off-center, mixed content."""
    return [
        [0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 6, 6, 6, 6, 6, 6, 6, 0, 0, 0, 0],
        [0, 0, 0, 6, 2, 0, 3, 0, 0, 6, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 3, 6, 0, 0, 0, 0],
        [0, 0, 0, 6, 0, 2, 0, 0, 0, 6, 0, 0, 0, 0],
        [0, 0, 0, 6, 6, 6, 6, 6, 6, 6, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0],
    ]


def _observable(grid):
    """Independent geometry/count checks on generated, public input grids."""
    assert grid and grid[0]
    height, width = len(grid), len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    frames = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        cells, pending = set(), [start]
        unseen.remove(start)
        while pending:
            r, c = pending.pop()
            cells.add((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                nr, nc = neighbor
                if neighbor in unseen and grid[nr][nc] == color:
                    unseen.remove(neighbor)
                    pending.append(neighbor)
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        if bottom - top < 2 or right - left < 2:
            continue
        border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                  if r in (top, bottom) or c in (left, right)}
        if cells == border:
            frames.append((len(cells), color, top, left, bottom, right))
    assert frames, "No monochrome rectangular outline"
    largest = max(item[0] for item in frames)
    selected = [item for item in frames if item[0] == largest]
    assert len(selected) == 1, "Frame choice is tied"
    _, color, top, left, bottom, right = selected[0]
    assert (right - left + 1) % 2 == 1, "Frame width must be odd"
    axis = (left + right) // 2
    interior = [(r, c, grid[r][c])
                for r in range(top + 1, bottom) for c in range(left + 1, right)
                if grid[r][c]]
    assert all(value != color for r, c, value in interior)
    marks = [(r, c, value) for r, c, value in interior if c != axis]
    orbits = {(r, min(c, left + right - c)) for r, c, value in marks}
    assert len(orbits) == len(marks), "Generated cells share a mirror orbit"
    sides = {"left" if c < axis else "right" for r, c, value in marks}
    outside = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value and not (top <= r <= bottom and left <= c <= right)]
    metrics = {
        "grid_h": height,
        "grid_w": width,
        "frame_h": bottom - top + 1,
        "frame_w": right - left + 1,
        "frame_color": color,
        "n_marks": len(marks),
        "n_colors": len({value for r, c, value in interior}),
        "n_axis": sum(c == axis for r, c, value in interior),
        "n_distractors": len(outside),
        "content_side": "mixed" if len(sides) == 2 else next(iter(sides), None),
    }
    return metrics, (top, left, bottom, right), interior


def test_canonical_inputs_pass_color_agnostic_self_check(generator, canonical):
    assert len(canonical) == 3
    for pair in canonical:
        before = deepcopy(pair["input"])
        assert generator.self_check(pair["input"]) == [], (pair["split"], pair["pair_index"])
        assert pair["input"] == before, "self_check mutated its input"


def test_hand_checked_off_center_mixed_frame_and_observer(generator):
    grid = _fixture()
    assert generator.self_check(grid) == []
    observed = generator.observe_overrides(grid)
    expected = {
        "grid_h": 9, "grid_w": 14, "frame_h": 5, "frame_w": 7,
        "frame_color": 6, "n_marks": 3, "n_colors": 2, "n_axis": 1,
        "n_distractors": 2, "content_side": "mixed",
    }
    assert {key: observed[key] for key in expected} == expected


def test_matching_completed_pair_is_allowed_beside_unfinished_content(generator):
    grid = _fixture()
    grid[3][8] = 2  # Existing red pair agrees; other rows still need completion.
    assert generator.self_check(grid) == []


def _malformed_cases():
    # Color 4 keeps the former check's literal-color precondition satisfied.
    base = [[4 if value == 6 else value for value in row] for row in _fixture()]
    partial = deepcopy(base)
    partial[2][5] = 0
    even = [row[:7] + row[8:] for row in base]
    conflict = deepcopy(base)
    conflict[3][8] = 7
    axis_only = deepcopy(base)
    axis_only[3][4] = axis_only[4][8] = axis_only[5][5] = 0
    frame_color_inside = deepcopy(base)
    frame_color_inside[4][5] = 4
    tied = [[0] * 20 for _ in range(7)]
    for color, left, right in ((4, 1, 7), (6, 11, 17)):
        for r in range(1, 6):
            for c in range(left, right + 1):
                if r in (1, 5) or c in (left, right):
                    tied[r][c] = color
    tied[2][2] = 2
    tied[3][3] = 3
    return [
        pytest.param([], id="empty"),
        pytest.param([[]], id="empty-row"),
        pytest.param([[0, 4], [2]], id="ragged"),
        pytest.param([[4, 2]], id="two-pixels-are-not-a-frame"),
        pytest.param([[4, 2, 99]], id="out-of-range"),
        pytest.param([[4, 2, -1]], id="negative"),
        pytest.param([[4, 2, "x"]], id="noninteger"),
        pytest.param([[4, 2, True]], id="boolean-color"),
        pytest.param(partial, id="partial-frame"),
        pytest.param(even, id="even-width-frame"),
        pytest.param(conflict, id="conflicting-opposite-colors"),
        pytest.param(axis_only, id="no-transformative-content"),
        pytest.param(frame_color_inside, id="ambiguous-frame-color-content"),
        pytest.param(tied, id="equal-largest-frame-tie"),
    ]


@pytest.mark.parametrize("grid", _malformed_cases())
@pytest.mark.parametrize("meta", [None, {"texture": "no_frame"}, {"texture": "even_width_frame"}])
def test_bad_inputs_are_rejected_without_metadata_bypass(generator, grid, meta):
    before = deepcopy(grid)
    errors = generator.self_check(grid, meta=meta)
    assert isinstance(errors, list) and errors, "Malformed input was silently accepted"
    assert grid == before


AXIS_VALUES = {
    "grid_h": range(7, 25),
    "grid_w": range(9, 26),
    "frame_h": range(5, 12),
    "frame_w": (7, 9, 11, 13),
    "frame_color": range(1, 10),
    "n_marks": range(3, 7),
    "n_colors": range(1, 4),
    "n_axis": range(3),
    "n_distractors": range(4),
    "content_side": ("left", "right", "mixed"),
}


@pytest.mark.parametrize("axis,value", [(axis, value) for axis, values in AXIS_VALUES.items() for value in values])
def test_every_single_axis_value_is_constructible_and_recoverable(generator, axis, value):
    grid = generator.generate(17, 2, difficulty="medium", **{axis: value})
    actual, _, _ = _observable(grid)
    assert actual[axis] == value, (axis, value, actual[axis])
    assert generator.self_check(grid) == []
    observed = generator.observe_overrides(grid)
    assert {key: observed[key] for key in AXIS_VALUES} == actual


@pytest.mark.parametrize("overrides", [
    {"grid_h": 7, "frame_h": 11},
    {"grid_w": 9, "frame_w": 13},
])
def test_infeasible_joint_dimensions_raise(generator, overrides):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, difficulty="medium", **overrides)


@pytest.mark.parametrize("overrides", [
    {"grid_h": 6}, {"grid_h": 25}, {"grid_w": 8}, {"grid_w": 26},
    {"frame_h": 4}, {"frame_h": 12}, {"frame_w": 8}, {"frame_w": 15},
    {"frame_color": 0}, {"frame_color": 10}, {"n_marks": 2}, {"n_marks": 7},
    {"n_colors": 0}, {"n_colors": 4}, {"n_axis": -1}, {"n_axis": 3},
    {"n_distractors": -1}, {"n_distractors": 4}, {"content_side": "diagonal"},
    {"n_marks": True}, {"frame_w": 9.0}, {"grid_h": "12"},
    {"unknown_key": "x"}, {"texture": "no_frame"},
])
def test_invalid_and_unknown_overrides_raise(generator, overrides):
    with pytest.raises((TypeError, ValueError)):
        generator.generate(0, 0, difficulty="medium", **overrides)


def test_tight_feasible_joint_overrides_are_exact(generator):
    overrides = {
        "grid_h": 7, "grid_w": 9, "frame_h": 5, "frame_w": 7,
        "frame_color": 1, "n_marks": 6, "n_colors": 3, "n_axis": 2,
        "n_distractors": 3, "content_side": "mixed",
    }
    grid = generator.generate(3, 4, difficulty="hard", **overrides)
    actual, _, _ = _observable(grid)
    assert actual == overrides
    assert generator.self_check(grid) == []


@pytest.fixture(scope="module")
def draws(generator):
    return [(band, seed, index, generator.generate(seed, index, difficulty=band))
            for band in ("easy", "medium", "hard")
            for seed in range(16) for index in range(4)]


def test_ordinary_draws_are_well_formed_and_never_noop(generator, draws):
    for band, seed, index, grid in draws:
        actual, _, _ = _observable(grid)
        assert actual["n_marks"] >= 3, (band, seed, index)
        assert generator.self_check(grid) == [], (band, seed, index)


def test_defaults_teach_frame_and_content_color_variation(draws):
    measurements = [_observable(grid) for _, _, _, grid in draws]
    frame_colors = {metrics["frame_color"] for metrics, _, _ in measurements}
    content_colors = {value for _, _, inside in measurements for r, c, value in inside}
    assert {1, 4, 6, 8} <= frame_colors
    assert 1 in content_colors
    assert any(max(Counter(value for r, c, value in inside).values()) > 1
               for _, _, inside in measurements), "No repeated-color interior motifs"


def test_defaults_teach_frame_axis_instead_of_canvas_axis(draws):
    measurements = [_observable(grid) for _, _, _, grid in draws]
    assert any(left + right != metrics["grid_w"] - 1
               for metrics, (top, left, bottom, right), _ in measurements)
    assert len({(top, left) for _, (top, left, bottom, right), _ in measurements}) > 1
    assert {metrics["content_side"] for metrics, _, _ in measurements} == {"left", "right", "mixed"}
    assert any(metrics["n_distractors"] > 0 for metrics, _, _ in measurements)


def test_same_seed_index_and_overrides_are_deterministic(generator):
    overrides = {"frame_color": 6, "content_side": "mixed", "n_marks": 5}
    first = generator.generate(19, 3, difficulty="hard", **overrides)
    assert first == generator.generate(19, 3, difficulty="hard", **overrides)


def test_difficulty_changes_realized_content_without_shrinking_override_domains(generator):
    # Catch a declared difficulty knob that never changes an observable draw.
    counts = {}
    for band in ("easy", "medium", "hard"):
        counts[band] = [_observable(generator.generate(seed, 0, difficulty=band))[0]["n_marks"]
                        for seed in range(24)]
    assert sum(counts["easy"]) < sum(counts["hard"])
    assert len({tuple(values) for values in counts.values()}) == 3


def test_default_exterior_noise_does_not_predict_content_side_or_frame_color_role(generator):
    # Catch curricula that only show right-side content when distractors exist.
    scenes = [_observable(generator.generate(seed, index, difficulty="medium"))[0]
              for seed in range(32) for index in range(4)]
    assert {(scene["n_distractors"], scene["content_side"]) for scene in scenes} == {
        (noise, side) for noise in range(4) for side in ("left", "right", "mixed")}
    assert {scene["frame_color"] in (4, 6, 8) for scene in scenes
            if scene["n_distractors"] == 0} == {False, True}


def test_five_pair_windows_preserve_both_noise_conditions_after_one_holdout(generator):
    for seed in range(8):
        scenes = [_observable(generator.generate(seed, index, difficulty="medium"))[0]
                  for index in range(24)]
        for start in range(20):
            window = scenes[start:start + 5]
            assert sum(scene["n_distractors"] == 0 and scene["content_side"] != "left"
                       for scene in window) >= 2, (seed, start, window)
            assert sum(scene["n_distractors"] > 0 for scene in window) >= 2, (seed, start, window)


def test_feasible_full_canvas_frame_does_not_require_pinning_noise(generator):
    grid = generator.generate(0, 2, difficulty="medium", grid_h=7, grid_w=9,
                              frame_h=7, frame_w=9)
    actual, _, _ = _observable(grid)
    assert actual["n_distractors"] == 0
    assert generator.self_check(grid) == []
