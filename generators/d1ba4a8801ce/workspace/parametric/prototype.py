"""Proposed episode-fixed shelving-axis variants for framed content blocks.

Inputs preserve the canonical checkerboard, dominant frame disruption, and
loose rectangular content blocks.  The private setting chooses whether the
blocks are re-shelved along the frame's long (canonical) or short axis.  Python
outputs are only claims until protected Racket executes every label.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "d1ba4a8801ce"
SETTINGS = ({"shelf_axis": "long"}, {"shelf_axis": "short"})

# height, width, frame height, frame width, loose block (height, width) shapes
_DEMO_PROFILES = (
    (13, 15, 6, 10, ((1, 1), (2, 1))),
    (15, 13, 10, 6, ((1, 2), (1, 1))),
    (18, 20, 8, 12, ((1, 1), (2, 1), (1, 2))),
    (20, 18, 12, 8, ((2, 1), (1, 2), (1, 1))),
    (24, 27, 10, 16, ((2, 2), (1, 2), (2, 1))),
    (27, 24, 16, 10, ((1, 2), (2, 2), (2, 1))),
)
_QUERY_PROFILES = (
    (11, 13, 6, 8, ((1, 1), (2, 1))),
    (21, 29, 9, 17, ((1, 1), (2, 1), (1, 2))),
    (29, 24, 17, 9, ((2, 1), (1, 2), (1, 1))),
    (30, 30, 12, 20, ((2, 2), (1, 2), (2, 1))),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"shelf_axis"}
        or type(settings["shelf_axis"]) is not str
        or settings["shelf_axis"] not in {"long", "short"}
    ):
        raise ValueError("settings must be exactly {'shelf_axis': 'long'|'short'}")
    return settings["shelf_axis"]


def program(settings):
    axis = _setting(settings)
    return (HERE / ("canonical.rkt" if axis == "long" else "short.rkt")).read_text()


def _rng(seed, split, index):
    raw = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _checker(height, width, even, odd):
    return [
        [odd if row % 2 == 1 and col % 2 == 1 else even for col in range(width)]
        for row in range(height)
    ]


def _paint_rect(grid, r0, c0, height, width, color):
    for row in range(r0, r0 + height):
        for col in range(c0, c0 + width):
            grid[row][col] = color


def _paint_frame(grid, r0, c0, height, width, color):
    r1, c1 = r0 + height - 1, c0 + width - 1
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if row in {r0, r1} or col in {c0, c1}:
                grid[row][col] = color


def sample_input(seed, split, index):
    """Deterministic, prefix-stable input independent of the private setting."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer(index, 0, len(profiles) - 1, "index")
    height, width, frame_h, frame_w, shapes = profiles[index]
    rng = _rng(seed, split, index)
    colors = rng.sample(range(1, 10), 3 + len(shapes))
    even, odd, frame_color, *block_colors = colors
    grid = _checker(height, width, even, odd)

    frame_r = (height - frame_h) // 2
    frame_c = (width - frame_w) // 2
    if frame_r < 2 or frame_c < 2:
        raise AssertionError("profiles must preserve two-cell margins")
    _paint_frame(grid, frame_r, frame_c, frame_h, frame_w, frame_color)

    # Unique row and column coordinates make both possible shelf-order keys
    # deterministic.  All blocks remain outside the frame and avoid (0,0)/(1,1).
    locations = (
        lambda bh, bw: (0, width - bw - 1),
        lambda bh, bw: (height - bh, 2),
        lambda bh, bw: (frame_r + 1, 0),
    )
    for shape, color, locate in zip(shapes, block_colors, locations):
        block_h, block_w = shape
        row, col = locate(block_h, block_w)
        cells = {
            (r, c)
            for r in range(row, row + block_h)
            for c in range(col, col + block_w)
        }
        frame_cells = {
            (r, c)
            for r in range(frame_r, frame_r + frame_h)
            for c in range(frame_c, frame_c + frame_w)
        }
        if cells & frame_cells or (0, 0) in cells or (1, 1) in cells:
            raise AssertionError("loose block placement violates profile contract")
        _paint_rect(grid, row, col, block_h, block_w, color)
    return grid


def _grid(value):
    if (
        type(value) is not list
        or not 2 <= len(value) <= 30
        or type(value[0]) is not list
        or not 2 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 2..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC integers 0..9")
    return value


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid):
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    even, odd = grid[0][0], grid[1][1]
    if even == odd:
        raise ValueError("checkerboard colors must differ")

    def expected(row, col):
        return odd if row % 2 == 1 and col % 2 == 1 else even

    by_color = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != expected(row, col):
                by_color[value].append((row, col))
    if len(by_color) < 3:
        raise ValueError("expected one frame and at least two content colors")
    ordered = sorted(by_color, key=lambda color: (-len(by_color[color]), color))
    frame_color = ordered[0]
    if len(by_color[frame_color]) <= max(len(by_color[color]) for color in ordered[1:]):
        raise ValueError("frame disruption color must be uniquely most frequent")
    fr0, fc0, fr1, fc1 = _bbox(by_color[frame_color])
    if fr1 - fr0 == fc1 - fc0:
        raise ValueError("frame must be non-square so long and short axes differ")
    perimeter = {
        (row, col)
        for row in range(fr0, fr1 + 1)
        for col in range(fc0, fc1 + 1)
        if row in {fr0, fr1} or col in {fc0, fc1}
    }
    if set(by_color[frame_color]) != perimeter:
        raise ValueError("dominant disruption must be one complete rectangular frame")

    contents = []
    for color in ordered[1:]:
        r0, c0, r1, c1 = _bbox(by_color[color])
        cells = {
            (row, col)
            for row in range(r0, r1 + 1)
            for col in range(c0, c1 + 1)
        }
        if set(by_color[color]) != cells:
            raise ValueError("each content color must form one solid rectangle")
        contents.append((color, r0, c0, r1 - r0 + 1, c1 - c0 + 1))
    return {
        "height": height,
        "width": width,
        "even": even,
        "odd": odd,
        "frame_color": frame_color,
        "frame": (fr0, fc0, fr1, fc1),
        "contents": contents,
    }


def transform(grid, settings):
    axis = _setting(settings)
    facts = _analyze(grid)
    fr0, fc0, fr1, fc1 = facts["frame"]
    frame_horizontal = (fc1 - fc0) >= (fr1 - fr0)
    horizontal = frame_horizontal if axis == "long" else not frame_horizontal
    contents = sorted(facts["contents"], key=lambda item: item[2] if horizontal else item[1])

    output = _checker(facts["height"], facts["width"], facts["even"], facts["odd"])
    for row in range(fr0 + 1, fr1):
        for col in range(fc0 + 1, fc1):
            output[row][col] = facts["even"]
    _paint_frame(output, fr0, fc0, fr1 - fr0 + 1, fc1 - fc0 + 1, facts["frame_color"])

    inner_r, inner_c = fr0 + 1, fc0 + 1
    inner_h, inner_w = fr1 - fr0 - 1, fc1 - fc0 - 1
    used = sum(item[4] if horizontal else item[3] for item in contents) + len(contents) - 1
    capacity = inner_w if horizontal else inner_h
    if used > capacity:
        raise ValueError("content blocks do not fit the requested shelf axis")
    cursor = (inner_c if horizontal else inner_r) + (capacity - used) // 2
    for color, _old_r, _old_c, block_h, block_w in contents:
        row = inner_r + (inner_h - block_h) // 2 if horizontal else cursor
        col = cursor if horizontal else inner_c + (inner_w - block_w) // 2
        _paint_rect(output, row, col, block_h, block_w, color)
        cursor += (block_w if horizontal else block_h) + 1
    return output


def generate(seed, settings, demos=3, queries=4):
    """Generate 2..6 demonstrations and 1..4 distinct queries independently."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    result = {
        "task_id": TASK_ID,
        "seed": seed,
        "settings": dict(settings),
        "program_solution": program(settings),
        "train": [],
        "test": [],
    }
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise ValueError(f"duplicate generated input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result
