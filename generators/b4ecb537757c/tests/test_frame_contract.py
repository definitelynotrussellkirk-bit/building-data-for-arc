"""Portable public-contract regressions for keyed frame-and-insert scenes.

The geometry checks below inspect cells independently of generator helpers.
Reference labels are exercised separately through the unchanged Racket rule.
"""
from __future__ import annotations

import hashlib

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "b4ecb537757c"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK, root=ROOT)
PAIRS = canonical_pairs(TASK, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _components(grid):
    """Monochrome cardinal components, including singleton transform keys."""
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, color in enumerate(row) if color != 0}
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        pending, cells = [start], {start}
        remaining.remove(start)
        while pending:
            r, c = pending.pop()
            for pos in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if pos in remaining and grid[pos[0]][pos[1]] == color:
                    remaining.remove(pos)
                    cells.add(pos)
                    pending.append(pos)
        result.append((color, cells))
    return result


def _bounds(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _frame_bounds(cells):
    top, left, bottom, right = _bounds(cells)
    if bottom - top < 2 or right - left < 2:
        return None
    perimeter = ({(r, c) for r in (top, bottom) for c in range(left, right + 1)}
                 | {(r, c) for c in (left, right) for r in range(top, bottom + 1)})
    return (top, left, bottom, right) if cells == perimeter else None


def _frames(grid):
    return [(color, cells, bounds) for color, cells in _components(grid)
            if (bounds := _frame_bounds(cells)) is not None]


def _assert_fitting_scene(grid):
    """Every moved insert must land strictly inside its intact frame."""
    components = _components(grid)
    frames = _frames(grid)
    assert frames, "normal draw has no complete hollow frame"
    assert len({color for color, _, _ in frames}) == len(frames)
    for color, frame_cells, (top, left, bottom, right) in frames:
        keys = [(key_color, next(iter(cells))) for key_color, cells in components
                if key_color in (1, 2, 3, 4) and len(cells) == 1
                and all(top < r < bottom and left < c < right for r, c in cells)]
        assert len(keys) == 1, (color, "expected one isolated interior key", keys)
        inserts = [cells for insert_color, cells in components
                   if insert_color == color and len(cells) > 1
                   and _frame_bounds(cells) is None]
        assert len(inserts) == 1, (color, "expected one matching insert", inserts)
        insert = inserts[0]
        for r, c in insert:
            assert all(not (t <= r <= b and l <= c <= rr)
                       for _, _, (t, l, b, rr) in frames), "insert lies in a frame"
        r0, c0, r1, c1 = _bounds(insert)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        normalized = {(r - r0, c - c0) for r, c in insert}
        key = keys[0][0]
        if key == 1:
            rotated = normalized
        elif key == 2:
            rotated = {(c, height - 1 - r) for r, c in normalized}
        elif key == 3:
            rotated = {(height - 1 - r, width - 1 - c) for r, c in normalized}
        else:
            rotated = {(width - 1 - c, r) for r, c in normalized}
        moved = {(top + 1 + r, left + 1 + c) for r, c in rotated}
        assert all(top < r < bottom and left < c < right for r, c in moved), (
            color, key, (height, width), (bottom - top - 1, right - left - 1),
            "selected rotation overflows its frame interior")
        assert moved.isdisjoint(frame_cells), "pasting an insert would overwrite its frame"
    return frames


def _two_frame_scene(first_key=1):
    """A 2x3 insert fits the first 2x4 interior only without a quarter turn."""
    grid = [[0] * 18 for _ in range(12)]
    for color, top, left, height, width, key in (
        (5, 1, 1, 4, 6, first_key), (6, 7, 1, 4, 5, 1),
    ):
        for r in range(top, top + height):
            for c in range(left, left + width):
                if r in (top, top + height - 1) or c in (left, left + width - 1):
                    grid[r][c] = color
        grid[top + 1][left + 1] = key
    for r, c in ((1, 11), (1, 12), (1, 13), (2, 11)):
        grid[r][c] = 5
    for r, c in ((8, 11), (9, 11), (9, 12)):
        grid[r][c] = 6
    return grid


def _scene_with_invalid_cell(value):
    grid = _two_frame_scene()
    grid[0][0] = value
    return grid


@pytest.mark.parametrize("pair", PAIRS,
                         ids=lambda p: f'v{p["variant"]}-{p["split"]}-{p["pair_index"]}')
def test_all_canonical_inputs_are_accepted_without_metadata(pair):
    assert len(PAIRS) == 4
    assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("grid", [
    None, [], [[]], [0, 1], "not-a-grid", 7,
    [[0, 0], [0]], [[0], [0, 0]], [[0], None],
    *[_scene_with_invalid_cell(value) for value in (True, 1.5, "1", None, 10, -1)],
], ids=["none", "empty", "empty-row", "scalar-rows", "string-grid", "scalar-grid",
        "ragged-short", "ragged-long", "missing-row", "bool", "float", "string-cell",
        "none-cell", "color-too-large", "negative-color"])
def test_malformed_grids_return_error_reasons_without_crashing(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list)
    assert errors and all(isinstance(reason, str) and reason for reason in errors)


def test_complete_frame_without_matching_insert_is_rejected():
    grid = _two_frame_scene()
    assert GEN.self_check(grid) == []
    _assert_fitting_scene(grid)
    for color, cells in _components(grid):
        if color == 5 and _frame_bounds(cells) is None:
            for r, c in cells:
                grid[r][c] = 0
    assert GEN.self_check(grid), "complete frame without its insert was accepted"


@pytest.mark.parametrize("key", [2, 4])
def test_selected_key_rotation_must_fit_the_frame_interior(key):
    fitting = _two_frame_scene(first_key=1)
    assert GEN.self_check(fitting) == []
    _assert_fitting_scene(fitting)
    rotated = _two_frame_scene(first_key=key)
    assert GEN.self_check(rotated), "quarter-turn overflow was accepted"


@pytest.mark.parametrize("band", BANDS)
def test_normal_draws_preserve_frames_when_inserts_are_moved(band):
    for index in range(12):
        grid = GEN.generate(61, index, difficulty=band)
        assert GEN.self_check(grid) == [], (band, index)
        _assert_fitting_scene(grid)


def test_unknown_override_is_rejected():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(19, 3, imaginary_axis=1)


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("height,width", [(7, 12), (22, 24)])
def test_declared_grid_dimensions_are_honored_in_every_band(band, height, width):
    grid = GEN.generate(31, 7, difficulty=band,
                        grid_h=height, grid_w=width, n_frames=1)
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid) == []
    assert len(_assert_fitting_scene(grid)) == 1


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("count", [1, 2, 3, 4])
def test_frame_count_override_is_observable_on_feasible_grid(band, count):
    grid = GEN.generate(73, 4, difficulty=band, grid_h=20, grid_w=24, n_frames=count)
    assert (len(grid), len(grid[0])) == (20, 24)
    assert len(_frames(grid)) == count
    assert GEN.self_check(grid) == []
    _assert_fitting_scene(grid)


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_include_canonical_profiles_in_every_band(band):
    profiles = {(len(pair["input"]), len(pair["input"][0]),
                 len({color for row in pair["input"] for color in row})) for pair in PAIRS}
    observed = set()
    for index in range(20):
        seed = int(hashlib.sha256(f"profile-floor:v1:{TASK}:{band}:{index}".encode())
                   .hexdigest()[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        observed.add((len(grid), len(grid[0]), len({color for row in grid for color in row})))
    assert profiles & observed, (band, "no canonical profile in pinned 20 draws", observed)
