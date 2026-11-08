"""Constructive, setting-independent inputs for the native eight-setting family.

Three demonstrations teach component selection and color selection together.
Six demos and four queries are always materialized before either count prefix is
taken. Query presentation has its own SHA-derived stream; changing demo count,
query count, or rule settings cannot change the common inputs or their ordering.
The sampler imports neither the selected generator nor the label implementation.
"""
from __future__ import annotations

import hashlib
import random


TASK_ID = "11c53dabb028"
SAMPLER_VERSION = "native-component-frame-v1"


def _rng(seed: int, split: str, slot: int, purpose: str) -> random.Random:
    identity = f"{TASK_ID}|{SAMPLER_VERSION}|{seed}|{split}|{slot}|{purpose}"
    return random.Random(int.from_bytes(hashlib.sha256(identity.encode("ascii")).digest(), "big"))


def _palette(seed: int, split: str, slot: int) -> list[int]:
    colors = list(range(1, 10))
    _rng(seed, split, slot, "palette").shuffle(colors)
    return colors


def _selection_demo(seed: int) -> list[list[int]]:
    """Largest pixel count beats first/last/largest bbox and diagonal contact."""
    rng = _rng(seed, "train", 0, "geometry")
    paint = _rng(seed, "train", 0, "paint")
    low, global_first, selected_first, high = sorted(_palette(seed, "train", 0)[:4])
    padding = rng.randrange(2)
    height, width = 10 + padding, 14
    top, left = 2 + padding, 4 + rng.randrange(2)
    grid = [[0] * width for _ in range(height)]

    # Twenty connected pixels in a 5x7 box: remove the top-left corner of
    # a ring and reconnect its left edge through local (1,1). The first
    # occupied crop cell is column 1; column-major scanning sees another color.
    ring = {(r, c) for r in range(5) for c in range(7)
            if r in (0, 4) or c in (0, 6)}
    ring.remove((0, 0))
    ring.add((1, 1))
    fixed = {(0, 1): selected_first, (1, 0): low, (4, 6): high}
    colors = [low] * 11 + [high] * 6
    paint.shuffle(colors)
    for (r, c), color in zip(sorted(ring - fixed.keys()), colors):
        grid[top + r][left + c] = color
    for (r, c), color in fixed.items():
        grid[top + r][left + c] = color

    # This earlier singleton gives the original frame a different first color.
    # Both first colors are middle-ranked minorities, never min/max or mode.
    grid[0][rng.randint(9, 12)] = global_first
    grid[top - 1][left + 7] = high  # diagonal-only contact with the ring
    grid[top + 2][left + 3] = low   # separated island inside the selected bbox

    # An 18-pixel L has a 5x14 box, twice the ring's bounding-box area. Its
    # first pixel follows the ring's; its last pixel follows the inner island.
    bottom = height - 2
    for row in range(bottom - 4, bottom + 1):
        grid[row][0] = low
    for column in range(1, width):
        grid[bottom][column] = low if column < width - 1 else high
    return grid


def _tie_demo(seed: int) -> list[list[int]]:
    """Equal pixel counts; actual first cells disagree with bbox/left order."""
    rng = _rng(seed, "train", 1, "geometry")
    paint = _rng(seed, "train", 1, "paint")
    low, middle, high = sorted(_palette(seed, "train", 1)[:3])
    down, across = rng.randrange(2), rng.randrange(2)
    top = 1 + down
    grid = [[0] * (13 + across) for _ in range(9 + down)]
    ring = {(r, c) for r in range(5) for c in range(5)
            if r in (0, 4) or c in (0, 4)} | {(1, 1), (2, 1)}
    fixed = {(0, 0): low, (0, 1): middle}
    colors = [low] * 13 + [middle] * 2 + [high]
    paint.shuffle(colors)
    for (r, c), color in zip(sorted(ring - fixed.keys()), colors):
        grid[top + r][4 + across + c] = color
    for (r, c), color in fixed.items():
        grid[top + r][4 + across + c] = color

    # The second 18-cell component begins later in the same row, then descends
    # and extends to the left. Its bbox corner is earlier than the winner's,
    # but no actual pixel is. One blank row keeps the two components apart.
    rival = {(r, 11) for r in range(7)} | {(6, c) for c in range(11)}
    first, *remaining = sorted(rival)
    grid[top + first[0]][across + first[1]] = high
    colors = [low] * 5 + [middle] * 12
    paint.shuffle(colors)
    for (r, c), color in zip(remaining, colors):
        grid[top + r][across + c] = color
    # First is the minimum and a strict majority in both the winning component
    # (14/18) and original input (19/36), defeating second-frequency selection.
    return grid


def _left_edge_demo(seed: int) -> list[list[int]]:
    """Small asymmetric anchor that closes the retained left-edge scan hole."""
    rng = _rng(seed, "train", 2, "geometry")
    low, middle, high = sorted(_palette(seed, "train", 2)[:3])
    mask = [[1, 1, 1, 0, 0],
            [1, 0, 1, 1, 1],
            [1, 1, 1, 0, 0],
            [0, 1, 0, 0, 0]]
    mask[2][3] = rng.randrange(2)
    mask[3][2] = rng.randrange(2)
    grid = [[high if value else 0 for value in row] for row in mask]
    grid[0][1] = low
    grid[1][4] = middle
    # The first nonzero in both frames is column 0, followed in the SAME ROW
    # by another color. Scanning columns 1..w-1 then 0 therefore picks low.
    # High is also the maximum and strict majority, complementing demos 0/1.
    return grid


def _dense(seed: int, split: str, slot: int,
           height: int, width: int) -> list[list[int]]:
    """Full-span connected structure, varied holes, and a guaranteed island."""
    rng = _rng(seed, split, slot, "geometry")
    paint = _rng(seed, split, slot, "paint")
    palette = _palette(seed, split, slot)[:paint.randint(3, 9)]
    center = height // 2, width // 2
    moat = {(center[0] + dr, center[1] + dc)
            for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
    # The border plus two full internal rows/columns are connected by design.
    # For the 15x15 query these 104 pixels already fill nearly half the canvas;
    # the largest component therefore reaches all edges before random filling.
    occupied = {(r, c) for r in range(height) for c in range(width)
                if r in (0, 2, height - 3, height - 1)
                or c in (0, 2, width - 3, width - 1)}
    occupied -= moat
    available = sorted({(r, c) for r in range(height) for c in range(width)}
                       - occupied - moat)
    count = rng.randint(len(available) // 3, 2 * len(available) // 3)
    occupied.update(rng.sample(available, count))
    occupied.add(center)
    grid = [[0] * width for _ in range(height)]
    for r, c in sorted(occupied):
        grid[r][c] = paint.choice(palette)
    grid[0][0], grid[0][1], grid[0][2] = palette[:3]
    return grid


def _line(seed: int) -> list[list[int]]:
    rng = _rng(seed, "train", 3, "geometry")
    palette = _palette(seed, "train", 3)
    cells = {0, 1, 2, 5, 6, 7, 8, 12, 14}
    if rng.randrange(2):
        cells.add(9)
    return [[rng.choice(palette[:4]) if c in cells else 0 for c in range(15)]]


def _tiny(seed: int) -> list[list[int]]:
    color = _palette(seed, "test", 0)[0]
    row = [color, 0]
    if _rng(seed, "test", 0, "geometry").randrange(2):
        row.reverse()
    return [row]


def _exact_int(name: str, value: int, low: int, high: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")


def sample_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict:
    """Return fresh grids from stable independent banks, without labels."""
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 3, 6)
    _exact_int("queries", queries, 1, 4)
    train = [
        _selection_demo(seed), _tie_demo(seed), _left_edge_demo(seed),
        _line(seed), _dense(seed, "train", 4, 12, 7),
        _dense(seed, "train", 5, 8, 15),
    ]
    test = [
        _tiny(seed), _dense(seed, "test", 1, 9, 13),
        _dense(seed, "test", 2, 13, 11), _dense(seed, "test", 3, 15, 15),
    ]
    _rng(seed, "test", 0, "presentation").shuffle(test)
    return {"train": train[:demos], "test": test[:queries]}
