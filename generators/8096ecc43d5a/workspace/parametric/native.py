"""Native script-order family for 8096ecc43d5a."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "8096ecc43d5a"
SETTINGS = ("left_to_right", "right_to_left")
DEMO_PROFILES = (
    (8, 9, 3, 4, (1, 2)),
    (9, 10, 4, 5, (2, 1, 4, 4)),
    (10, 12, 5, 6, (2, 1, 3)),
    (12, 14, 6, 8, (4, 1, 3)),
    (14, 16, 8, 10, (1, 2, 3, 3)),
    (16, 18, 10, 12, (1, 4, 2, 2)),
)
QUERY_PROFILES = (
    (12, 14, 7, 9, (1, 2, 3)),
    (18, 20, 12, 14, (4, 3, 1)),
    (24, 26, 18, 20, (1, 2, 3, 3)),
    (30, 30, 28, 30, (1, 1, 1, 2, 3)),
)


def _read(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _setting(settings) -> str:
    if type(settings) is not dict or set(settings) != {"script_order"}:
        raise ValueError("settings must name exactly script_order")
    value = settings["script_order"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"script_order must be one of {SETTINGS}")
    return value


def program(settings) -> str:
    value = _setting(settings)
    return _read("canonical.rkt" if value == "left_to_right" else "reverse_script.rkt")


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _apply(grid, code: int):
    return {
        1: _rotate_cw,
        2: _flip_lr,
        3: _rotate_180,
        4: _flip_ud,
    }[code](grid)


def _crop(grid):
    cells = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value != 0]
    if not cells:
        raise ValueError("body is empty")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _apply_codes(grid, codes):
    result = _crop(grid)
    for code in codes:
        result = _apply(result, code)
    return result


def transform(grid, script_order: str):
    if script_order not in SETTINGS:
        raise ValueError("unknown script order")
    codes = [value for value in grid[0] if value != 0]
    if script_order == "right_to_left":
        codes.reverse()
    return _apply_codes(grid, codes)


def rival_transform(grid, mode: str):
    codes = [value for value in grid[0] if value != 0]
    if mode in SETTINGS:
        return transform(grid, mode)
    if mode == "sorted_codes":
        codes = sorted(codes)
    elif mode == "deduplicate_codes":
        codes = list(dict.fromkeys(codes))
    elif mode == "collapse_adjacent_codes":
        codes = [value for index, value in enumerate(codes)
                 if index == 0 or codes[index - 1] != value]
    elif mode == "first_only":
        codes = codes[:1]
    elif mode == "last_only":
        codes = codes[-1:]
    elif mode == "ignore_script":
        codes = []
    else:
        raise ValueError("unknown rival mode")
    return _apply_codes(grid, codes)


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}:native-v1:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _motif(mh: int, mw: int, color: int, variant: int):
    mask = [[True for _ in range(mw)] for _ in range(mh)]
    # Keep the full outer frame, and carve asymmetric interior holes. The frame
    # makes the body connected and preserves the requested crop dimensions.
    if mh >= 3 and mw >= 4:
        mask[0][1] = False
        mask[1][mw - 2] = False
    if mh >= 4 and mw >= 5:
        mask[mh - 2][2] = False
    if mh >= 6 and mw >= 7:
        for c in range(2, min(mw - 2, 2 + max(1, mw // 5))):
            mask[2 + (variant % max(1, mh - 4))][c] = False
    if mh >= 9 and mw >= 10:
        row = mh // 2
        for c in range(mw // 2, min(mw - 2, mw // 2 + max(2, mw // 7))):
            mask[row][c] = False
    return [[color if mask[r][c] else 0 for c in range(mw)] for r in range(mh)]


def _input(seed: int, split: str, index: int):
    profiles = DEMO_PROFILES if split == "train" else QUERY_PROFILES
    h, w, mh, mw, codes = profiles[index]
    rng = _rng(seed, split, index)
    color = 5 + rng.randrange(5)
    grid = [[0 for _ in range(w)] for _ in range(h)]
    positions = [max(1, min(w - 1, ((j + 1) * w) // (len(codes) + 1))) for j in range(len(codes))]
    if len(set(positions)) != len(positions):
        raise RuntimeError("script positions collided")
    for c, code in zip(positions, codes):
        grid[0][c] = code
    body = _motif(mh, mw, color, (seed + index) % 17)
    if h == 30 and w == 30:
        r0, c0 = 2, 0
    else:
        r0 = 2 + rng.randrange(max(1, h - 2 - mh + 1))
        c0 = rng.randrange(max(1, w - mw + 1))
    for r, row in enumerate(body):
        for c, value in enumerate(row):
            grid[r0 + r][c0 + c] = value
    return grid


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def generate(seed, settings, demos, queries):
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    selected = _setting(settings)
    train = []
    test = []
    for split, count, target in (("train", demos, train), ("test", queries, test)):
        for index in range(count):
            grid = _input(seed, split, index)
            target.append({"input": grid, "output": transform(grid, selected)})
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_turn(episode, query_index: int):
    if type(query_index) is not int or not 0 <= query_index < len(episode.get("test", [])):
        raise ValueError("query_index is outside the episode")
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(episode["test"][query_index]["input"])}],
    }
