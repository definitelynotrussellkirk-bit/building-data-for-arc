"""Native parametric family for fixed-block mode extraction.

`all_modes` is the exact canonical rule. `duplicate_bbox` first extracts the
six unique block modes, then finds the sole duplicated mode and fills the
axis-aligned bounding box between its two positions. Sampling is independent of
the private setting and supports independent demonstration/query prefixes.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import random


HOME = Path(__file__).resolve().parent
OPERATIONS = ("all_modes", "duplicate_bbox")
DEMO_SHAPES = ((9, 10), (10, 12), (12, 13), (13, 14), (9, 14), (13, 10))
QUERY_SHAPES = ((9, 10), (10, 11), (12, 13), (13, 14))
DOMAIN_LIMIT = "fixed six 3x2 blocks; larger canvases add only ignored background"
_PAIR_PROFILES = (
    ((0, 0), (1, 2)),
    ((0, 0), (1, 1)),
    ((0, 1), (1, 2)),
    ((0, 0), (0, 2)),
    ((0, 1), (1, 1)),
    ((0, 2), (1, 0)),
    ((0, 2), (1, 1)),
    ((0, 0), (1, 2)),
    ((0, 1), (1, 2)),
    ((0, 0), (0, 2)),
)


def _operation(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"operation"}
        or type(settings["operation"]) is not str
        or settings["operation"] not in OPERATIONS
    ):
        raise ValueError("settings must contain exactly one supported operation")
    return settings["operation"]


def _integer(name, value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def program(settings):
    name = "canonical.rkt" if _operation(settings) == "all_modes" else "duplicate-bbox.rkt"
    return (HOME / name).read_text(encoding="utf-8")


def _validate_grid(grid):
    if type(grid) is not list or not 8 <= len(grid) <= 30:
        raise ValueError("grid must have 8..30 rows")
    if type(grid[0]) is not list or not 9 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 9..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _block_mode(grid, r1, c1):
    counts = Counter(
        grid[r][c]
        for r in range(r1, r1 + 3)
        for c in range(c1, c1 + 2)
        if grid[r][c] != 0
    )
    if not counts:
        raise ValueError("every fixed block needs a nonzero mode")
    maximum = max(counts.values())
    winners = [color for color, count in counts.items() if count == maximum]
    if len(winners) != 1:
        raise ValueError("every fixed block needs one unique nonzero mode")
    return winners[0]


def extract_modes(grid):
    """Stage A: return the input-dependent 2x3 board of unique block modes."""
    _validate_grid(grid)
    return [
        [_block_mode(grid, 1 + 4 * br, 1 + 3 * bc) for bc in range(3)]
        for br in range(2)
    ]


def _bordered(interior):
    return [[0, 0, 0, 0, 0], [0, *interior[0], 0], [0, *interior[1], 0], [0, 0, 0, 0, 0]]


def _duplicate_bbox(modes):
    counts = Counter(value for row in modes for value in row)
    repeated = [value for value, count in counts.items() if count == 2]
    if len(repeated) != 1:
        raise ValueError("duplicate_bbox needs exactly one mode occurring twice")
    target = repeated[0]
    points = [(r, c) for r in range(2) for c in range(3) if modes[r][c] == target]
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    return [
        [target if r0 <= r <= r1 and c0 <= c <= c1 else 0 for c in range(3)]
        for r in range(2)
    ]


def solve(grid, operation):
    _operation({"operation": operation})
    modes = extract_modes(grid)
    return _bordered(modes if operation == "all_modes" else _duplicate_bbox(modes))


def _rng(seed, stream, index, attempt=0):
    return random.Random(f"c0bd45c81959:parametric-v1:{seed}:{stream}:{index}:{attempt}")


def _mode_board(rng, profile_index):
    colors = rng.sample(list(range(1, 10)), 5)
    target = colors[0]
    pair = set(_PAIR_PROFILES[profile_index % len(_PAIR_PROFILES)])
    others = iter(colors[1:])
    return [
        [target if (r, c) in pair else next(others) for c in range(3)]
        for r in range(2)
    ], pair


def _scene(seed, stream, index, shape, attempt=0):
    rng = _rng(seed, stream, index, attempt)
    height, width = shape
    grid = [[0 for _ in range(width)] for _ in range(height)]
    modes, repeated_positions = _mode_board(rng, index + (0 if stream == "demo" else 6))
    for br in range(2):
        for bc in range(3):
            r1, c1 = 1 + 4 * br, 1 + 3 * bc
            mode = modes[br][bc]
            for r in range(r1, r1 + 3):
                for c in range(c1, c1 + 2):
                    grid[r][c] = mode
            count = 1 + ((index + br * 3 + bc) % 3)
            positions = [(r, c) for r in range(r1, r1 + 3) for c in range(c1, c1 + 2)]
            rng.shuffle(positions)
            if (br, bc) in repeated_positions:
                top_left = (r1, c1)
                positions.remove(top_left)
                positions.insert(0, top_left)
            available = [color for color in range(1, 10) if color != mode]
            distractors = rng.sample(available, count)
            for (r, c), color in zip(positions, distractors):
                grid[r][c] = color
    return grid


def generate(seed, settings, demos, queries):
    operation = _operation(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)

    seen = set()
    buckets = []
    for stream, shapes in (("demo", DEMO_SHAPES), ("query", QUERY_SHAPES)):
        pairs = []
        for index, shape in enumerate(shapes):
            for attempt in range(32):
                grid = _scene(seed, stream, index, shape, attempt)
                key = tuple(tuple(row) for row in grid)
                if key not in seen:
                    seen.add(key)
                    pairs.append({"input": grid, "output": solve(grid, operation)})
                    break
            else:
                raise RuntimeError("distinct input construction exhausted 32 retries")
        buckets.append(pairs)
    return {
        "train": buckets[0][:demos],
        "test": buckets[1][:queries],
        "program_solution": program(settings),
    }
