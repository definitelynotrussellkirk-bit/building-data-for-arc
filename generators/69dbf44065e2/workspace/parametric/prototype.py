"""Deterministic matched-input scenes for the turn-after-down-smear family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from typing import Any

TURNS = ("none", "left", "right")
COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _strict_int(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}; bool is forbidden")
    return value


def validate_turn(value: Any) -> str:
    if type(value) is not str or value not in TURNS:
        raise ValueError(f"turn must be one of {TURNS}")
    return value


def validate_grid(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with literal integer ARC colors 0..9")
    return deepcopy(grid)


def seeds(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]


def down_smear(grid):
    source = validate_grid(grid)
    out = deepcopy(source)
    for r, c, value in seeds(source):
        rr = r + 1
        while rr < len(source) and source[rr][c] == 0:
            out[rr][c] = value
            rr += 1
    return out


def endpoint(source, row: int, col: int) -> int:
    rr = row + 1
    last = row
    while rr < len(source) and source[rr][col] == 0:
        last = rr
        rr += 1
    return last


def solve(grid, turn: str):
    turn = validate_turn(turn)
    source = validate_grid(grid)
    down = down_smear(source)
    if turn == "none":
        return down
    delta = -1 if turn == "left" else 1
    out = deepcopy(down)
    width = len(source[0])
    for row, col, value in seeds(source):
        last = endpoint(source, row, col)
        if last == row:
            continue
        cc = col + delta
        while 0 <= cc < width and down[last][cc] == 0:
            out[last][cc] = value
            cc += delta
    return out


def skip_stage_a(grid, turn: str):
    """Ablation: run the horizontal operation at original seed rows."""
    turn = validate_turn(turn)
    source = validate_grid(grid)
    if turn == "none":
        return deepcopy(source)
    delta = -1 if turn == "left" else 1
    out = deepcopy(source)
    width = len(source[0])
    for row, col, value in seeds(source):
        cc = col + delta
        while 0 <= cc < width and source[row][cc] == 0:
            out[row][cc] = value
            cc += delta
    return out


def wrong_order(grid, turn: str):
    """Ablation: smear horizontally first, then smear the resulting cells down."""
    turn = validate_turn(turn)
    source = validate_grid(grid)
    if turn == "none":
        return down_smear(source)
    turned = skip_stage_a(source, turn)
    return down_smear(turned)


def dependency_facts(grid, turn: str) -> dict:
    turn = validate_turn(turn)
    source = validate_grid(grid)
    stage_a = down_smear(source)
    final = solve(source, turn)
    active = [
        {"seed": [row, col], "endpoint": [endpoint(source, row, col), col], "color": value}
        for row, col, value in seeds(source)
        if endpoint(source, row, col) != row
    ]
    return {
        "active_endpoints": active,
        "stage_a_changed_cells": sum(
            a != b for row_a, row_b in zip(source, stage_a) for a, b in zip(row_a, row_b)
        ),
        "stage_b_changed_cells": sum(
            a != b for row_a, row_b in zip(stage_a, final) for a, b in zip(row_a, row_b)
        ),
    }


def _rng(seed: int, index: int) -> random.Random:
    digest = hashlib.sha256(f"69dbf44065e2|turn-v2|{seed}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _dimensions(seed: int, index: int) -> tuple[int, int]:
    profiles = (
        (8, 10),
        (12, 9),
        (30, 30),
        (7, 24),
        (24, 7),
        (15, 18),
        (20, 20),
        (9, 13),
        (18, 12),
        (12, 20),
    )
    h, w = profiles[index % len(profiles)]
    if (h, w) not in {(30, 30), (7, 24), (24, 7)}:
        rng = _rng(seed ^ 0x5A5A, index)
        h = min(30, max(7, h + rng.choice((-1, 0, 1))))
        w = min(30, max(7, w + rng.choice((-1, 0, 1))))
    return h, w


def _put(grid, used, row, col, value):
    if not (0 <= row < len(grid) and 0 <= col < len(grid[0])):
        return False
    if (row, col) in used:
        return False
    grid[row][col] = value
    used.add((row, col))
    return True


def make_scene(seed: int, index: int) -> list[list[int]]:
    _strict_int(seed, 0, 2**63 - 1, "seed")
    _strict_int(index, 0, 10_000, "pair index")
    height, width = _dimensions(seed, index)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    rng = _rng(seed, index)
    palette = list(COLORS)
    rng.shuffle(palette)
    center = width // 2
    gap = max(2, min(width // 3, 6))
    left = max(1, center - gap)
    right = min(width - 2, center + gap)
    if not left < center < right:
        left, center, right = 1, width // 2, width - 2

    used: set[tuple[int, int]] = set()
    # The central seed ends above its wall.  The two side trails cross that
    # endpoint row and therefore become input-dependent stage-B blockers.
    anchors = (
        (1, center, palette[0]),
        (0, left, palette[1]),
        (0, right, palette[2]),
    )
    for row, col, color in anchors:
        assert _put(grid, used, row, col, color)
    assert _put(grid, used, height - 3, center, 5)
    assert _put(grid, used, height - 1, left, 5)
    assert _put(grid, used, height - 1, right, 5)

    # Boundary/no-op distractors and distributed seed/wall pairs ensure the
    # large scene uses the canvas rather than padding a tiny central motif.
    extra_seed_target = 7 if height == 30 and width == 30 else 3 + (index % 3)
    candidates = []
    # Reserve every column between the two side trails, not only the three
    # anchor columns.  Any extra seed in this interval can smear through the
    # central endpoint row and silently erase one turn setting (seed 53,
    # pair 4 exposed this on the 24x7 profile).
    reserved_turn_columns = set(range(left, right + 1))
    rows = [2, max(2, height // 4), max(2, height // 2), max(2, 3 * height // 4)]
    cols = [0, width - 1, 2, max(0, width - 3), max(0, center - 1), min(width - 1, center + 1)]
    for row in rows:
        for col in cols:
            if row < height - 2 and col not in reserved_turn_columns:
                candidates.append((row, col))
    candidates.extend(
        (row, col)
        for row in range(1, height - 2)
        for col in range(width)
        if col not in reserved_turn_columns
    )
    rng.shuffle(candidates)
    extras = 0
    color_index = 3
    while extras < extra_seed_target and candidates:
        row, col = candidates.pop()
        if not _put(grid, used, row, col, palette[color_index % len(palette)]):
            continue
        extras += 1
        color_index += 1
        wall_row = min(height - 1, row + 2 + rng.randrange(max(1, height - row - 2)))
        if wall_row > row + 1:
            _put(grid, used, wall_row, col, 5)

    # One bottom-row colored decoy and one corner wall add no stage-A branch.
    for col in (0, width - 1, center):
        if _put(grid, used, height - 1, col, palette[color_index % len(palette)]):
            color_index += 1
            break
    for row, col in ((0, 0), (0, width - 1), (height - 2, width - 1)):
        if _put(grid, used, row, col, 5):
            break

    # Ensure each declared setting is behaviorally distinct on every scene.
    outputs = [solve(grid, turn) for turn in TURNS]
    if len({repr(output) for output in outputs}) != len(TURNS):
        raise AssertionError("scene failed to distinguish turn settings")
    if any(output == grid for output in outputs):
        raise AssertionError("scene failed to exercise the rule")
    return grid


def generate_episode(seed: int, turn: str, demos: int, queries: int) -> dict:
    seed = _strict_int(seed, 0, 2**63 - 1, "seed")
    turn = validate_turn(turn)
    demos = _strict_int(demos, 2, 6, "demos")
    queries = _strict_int(queries, 1, 4, "queries")
    grids = [make_scene(seed, index) for index in range(demos + queries)]
    if len({repr(grid) for grid in grids}) != len(grids):
        raise AssertionError("episode inputs must be distinct")
    pairs = [{"input": grid, "output": solve(grid, turn)} for grid in grids]
    return {"train": pairs[:demos], "test": pairs[demos:]}
