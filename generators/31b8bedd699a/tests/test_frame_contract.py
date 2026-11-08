"""Portable regressions for the hollow-frame generator's observable contract.

The inventory and output oracle deliberately do not call generator analyzers or
``observe_overrides``. They inspect the supplied cells independently, so a
self-consistent generator/observer mistake cannot certify its own output.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest


# A library and a staged runtime expose the same public helper at different
# roots. Discover the local tree rather than depending on cwd or a sibling tree.
for _ancestor in Path(__file__).resolve().parents:
    _runtime = _ancestor / "shared" / "runtime"
    if (_ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_ancestor))
        break
    if (_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(_runtime))
        break
else:
    raise ImportError("The test's tree does not contain reviewer_support.py")

from reviewer_support import canonical_pairs, find_root


TASK_ID = "31b8bedd699a"
ROOT = find_root(__file__)
for _source in (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
):
    if _source.is_file():
        break
else:
    raise FileNotFoundError(f"No selected generator for {TASK_ID} under {ROOT}")
_SPEC = importlib.util.spec_from_file_location("frame_contract_generator", _source)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = GEN
_SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK_ID, root=find_root(__file__))
CANONICAL_IDS = [f"v{p['variant']}-{p['split']}-{p['pair_index']}" for p in CANONICAL]


def _scene(frames, solids=(), *, height=24, width=24):
    """Construct explicit fixtures; boxes are (top, left, height, width, color)."""
    grid = [[0] * width for _ in range(height)]
    for hollow, boxes in ((True, frames), (False, solids)):
        for top, left, bh, bw, color in boxes:
            for row in range(top, top + bh):
                for col in range(left, left + bw):
                    if not hollow or row in (top, top + bh - 1) or col in (left, left + bw - 1):
                        assert grid[row][col] == 0, "fixture boxes overlap"
                        grid[row][col] = color
    return grid


def _inventory(grid):
    """Independent nonzero 4-component parser and complete-box classifier."""
    assert isinstance(grid, list) and grid and isinstance(grid[0], list) and grid[0]
    height, width = len(grid), len(grid[0])
    assert all(isinstance(row, list) and len(row) == width for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    remaining = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    objects = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending = deque([start])
        cells = {start}
        while pending:
            r, c = pending.popleft()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    pending.append(neighbor)
        colors = {grid[r][c] for r, c in cells}
        assert len(colors) == 1, f"mixed-color object: {colors}"
        top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
        left, right = min(c for _, c in cells), max(c for _, c in cells)
        rectangle = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)}
        outline = {(r, c) for r, c in rectangle if r in (top, bottom) or c in (left, right)}
        if bottom - top >= 2 and right - left >= 2 and cells == outline:
            kind = "frame"
        elif cells == rectangle:
            kind = "solid"
        else:
            raise AssertionError(f"partial or nonrectangular object at {(top, left, bottom, right)}")
        objects.append({"kind": kind, "top": top, "left": left, "bottom": bottom,
                        "right": right, "color": next(iter(colors))})
    return objects


def _assert_contract(grid, *, frames=None, solids=None):
    objects = _inventory(grid)
    assert len(grid) <= 30 and len(grid[0]) <= 30
    hollow = [obj for obj in objects if obj["kind"] == "frame"]
    filled = [obj for obj in objects if obj["kind"] == "solid"]
    assert 2 <= len(hollow) <= 5, f"observed {len(hollow)} frames"
    assert 0 <= len(filled) <= 3, f"observed {len(filled)} solid distractors"
    for obj in objects:
        assert 3 <= obj["bottom"] - obj["top"] + 1 <= 8
        assert 3 <= obj["right"] - obj["left"] + 1 <= 8
    for i, a in enumerate(objects):
        for b in objects[i + 1:]:
            assert (a["bottom"] + 1 < b["top"] or b["bottom"] + 1 < a["top"]
                    or a["right"] + 1 < b["left"] or b["right"] + 1 < a["left"]), \
                f"boxes lack a separating background cell: {a}, {b}"
    if frames is not None:
        assert len(hollow) == frames, f"requested {frames} frames; observed {len(hollow)}"
    if solids is not None:
        assert len(filled) == solids, f"requested {solids} solids; observed {len(filled)}"
    return hollow, filled


def _expected_output(grid):
    frames, _ = _assert_contract(grid)
    row_range = max(obj["top"] for obj in frames) - min(obj["top"] for obj in frames)
    col_range = max(obj["left"] for obj in frames) - min(obj["left"] for obj in frames)
    horizontal = col_range >= row_range
    primary, secondary = ("left", "top") if horizontal else ("top", "left")
    frames.sort(key=lambda obj: (obj[primary], obj[secondary]))
    panels = []
    for obj in frames:
        color = obj["color"]
        panels.append([[color] * 4, [color, 0, 0, color],
                       [color, 0, 0, color], [color] * 4])
    if horizontal:
        return [sum((panel[r] for panel in panels), []) for r in range(4)]
    return [row for panel in panels for row in panel]


def _mirror(grid):
    mirror = getattr(GEN, "rule_mirror", None)
    assert callable(mirror), "The generator must expose its declared rule_mirror"
    return mirror(grid)


def _assert_rejected(grid):
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list), "self_check must return a list of validation reasons"
    assert reasons, "self_check accepted an input outside the structural frame contract"


LAWFUL = _scene([(1, 1, 4, 5, 1), (10, 1, 3, 7, 7), (2, 14, 7, 3, 3)],
                [(13, 14, 4, 5, 8)])


@pytest.mark.parametrize("name,grid", [
    ("all_solid", _scene([], [(2, 2, 4, 4, 2), (9, 9, 4, 4, 3)])),
    ("solid_2x2", [[2, 2], [2, 2]]),
    ("short_line", [[0, 0, 0], [2, 2, 0], [0, 0, 0]]),
    ("singleton", [[2]]),
    ("full_grid", [[2] * 18 for _ in range(18)]),
    ("no_foreground", [[0] * 15 for _ in range(15)]),
    ("empty", []),
    ("ragged", [[1, 1], [1]]),
    ("too_tall", LAWFUL + [[0] * len(LAWFUL[0]) for _ in range(7)]),
    ("too_wide", [row + [0] * 7 for row in LAWFUL]),
], ids=lambda value: value if isinstance(value, str) else None)
def test_validator_rejects_frame_free_and_malformed_grids(name, grid):
    _assert_rejected(grid)


@pytest.mark.parametrize("value,coordinate", [
    (True, (1, 1)), (False, (0, 0)), (1.0, (1, 1)), (0.0, (0, 0)),
    (2.5, (0, 0)), ("1", (1, 1)), (None, (0, 0)), (-1, (0, 0)), (10, (0, 0)),
], ids=["true", "false", "float_foreground", "float_background", "fraction",
        "string", "none", "negative", "ten"])
def test_validator_rejects_noninteger_and_illegal_colors(value, coordinate):
    grid = deepcopy(LAWFUL)
    grid[coordinate[0]][coordinate[1]] = value
    _assert_rejected(grid)


@pytest.mark.parametrize("mutation", ["edge_gap", "corner_gap", "spur", "interior_pixel", "mixed_color"])
def test_validator_rejects_broken_outline_with_two_other_valid_frames(mutation):
    grid = deepcopy(LAWFUL)
    row, col, color = {
        "edge_gap": (1, 2, 0), "corner_gap": (1, 1, 0), "spur": (0, 2, 1),
        "interior_pixel": (2, 2, 1), "mixed_color": (1, 2, 4),
    }[mutation]
    grid[row][col] = color
    _assert_rejected(grid)


@pytest.mark.parametrize("pair", CANONICAL, ids=CANONICAL_IDS)
def test_validator_accepts_every_canonical_pair(pair):
    _assert_contract(pair["input"])
    assert GEN.self_check(pair["input"]) == []


@pytest.mark.parametrize("pair", CANONICAL, ids=CANONICAL_IDS)
def test_validator_rejects_a_deleted_canonical_outline_edge(pair):
    grid = deepcopy(pair["input"])
    frames, _ = _assert_contract(grid)
    frame = frames[0]
    grid[frame["top"]][frame["left"] + 1] = 0
    _assert_rejected(grid)


@pytest.mark.parametrize("pair", CANONICAL, ids=CANONICAL_IDS)
def test_rule_mirror_matches_every_canonical_label(pair):
    assert _expected_output(pair["input"]) == pair["output"]
    assert _mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("grid", [
    _scene([(1, 1, 3, 3, 2)]),
    _scene([(1 + 5 * r, 1 + 5 * c, 3, 3, 2 + r + c) for r in range(2) for c in range(3)]),
    _scene([(1, 1, 3, 3, 2), (1, 7, 3, 3, 3)],
           [(8, 1 + 5 * i, 3, 3, 4 + i) for i in range(4)]),
    _scene([(1, 1, 3, 9, 2), (10, 1, 3, 3, 3)]),
    _scene([(1, 1, 9, 3, 2), (1, 10, 3, 3, 3)]),
    _scene([(1, 1, 4, 4, 2), (1, 5, 4, 4, 3)]),
    _scene([(1, 1, 4, 4, 2), (5, 5, 4, 4, 3)]),
], ids=["one_frame", "six_frames", "four_solids", "frame_width_nine", "frame_height_nine",
        "edge_touching_boxes", "corner_touching_boxes"])
def test_validator_rejects_object_count_size_and_separation_violations(grid):
    _assert_rejected(grid)


@pytest.mark.parametrize("frames,solids,shape", [
    ([(0, 0, 3, 8, 2), (10, 10, 8, 3, 2)], [], (4, 8)),
    ([(1, 12, 8, 3, 3), (5, 1, 3, 8, 2)], [(22, 1, 3, 3, 9)], (4, 8)),
    ([(1, 6, 3, 8, 2), (12, 3, 8, 3, 3)], [(1, 24, 3, 3, 9)], (8, 4)),
], ids=["tie_horizontal_boundary_repeated_color", "horizontal_ignore_solid", "vertical_ignore_solid"])
def test_variable_sized_frames_normalize_to_four_by_four_and_use_frame_spread(frames, solids, shape):
    grid = _scene(frames, solids, height=28, width=30)
    _assert_contract(grid, frames=2, solids=len(solids))
    assert GEN.self_check(grid) == []
    expected = _expected_output(grid)
    assert (len(expected), len(expected[0])) == shape
    assert _mirror(grid) == expected


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generation_is_deterministic_for_seed_index_and_difficulty(difficulty):
    first = GEN.generate(872341, 17, difficulty=difficulty)
    GEN.generate(42, 9, difficulty=difficulty)
    assert GEN.generate(872341, 17, difficulty=difficulty) == first


ENDPOINT_CASES = list(product((15, 30), (15, 30), (2, 5), (0, 3)))


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width,n_frames,n_solids", ENDPOINT_CASES)
def test_exact_controls_at_all_endpoints_in_every_difficulty(difficulty, height, width, n_frames, n_solids):
    for seed in (0, 271, 65537):
        grid = GEN.generate(seed, 3, difficulty=difficulty, grid_h=height, grid_w=width,
                            n_frames=n_frames, n_solids=n_solids)
        assert (len(grid), len(grid[0])) == (height, width)
        _assert_contract(grid, frames=n_frames, solids=n_solids)
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("difficulty,height,width,n_frames,n_solids", [
    ("medium", 18, 18, 3, 2), ("hard", 22, 22, 5, 2),
])
def test_generation_never_drops_objects_on_existing_dense_controls(difficulty, height, width, n_frames, n_solids):
    for seed in (0, 1, 2, 7, 17, 41, 271):
        grid = GEN.generate(seed, 0, difficulty=difficulty, grid_h=height, grid_w=width,
                            n_frames=n_frames, n_solids=n_solids)
        assert (len(grid), len(grid[0])) == (height, width)
        _assert_contract(grid, frames=n_frames, solids=n_solids)


INVALID_CONTROLS = [
    (name, value)
    for name, low, high, valid in (("grid_h", 15, 30, 20), ("grid_w", 15, 30, 20),
                                   ("n_frames", 2, 5, 2), ("n_solids", 0, 3, 1))
    for value in (low - 1, high + 1, float(valid), str(valid), True)
]


@pytest.mark.parametrize("name,value", INVALID_CONTROLS)
def test_integer_controls_reject_out_of_range_values_and_coercion(name, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(872341, 0, **{name: value})


@pytest.mark.parametrize("name,value", [("anchor_corner", False), ("asymmetry_force", False),
                                         ("palette_size", 4), ("position_bias", "rng"),
                                         ("palette_kind", "warm"), ("texture", "warm")])
def test_retired_inert_controls_are_rejected(name, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(872341, 0, **{name: value})


def test_retired_controls_are_not_advertised():
    assert not {"anchor_corner", "asymmetry_force", "palette_size", "position_bias",
                "palette_kind", "texture"}.intersection(GEN.AXES)
