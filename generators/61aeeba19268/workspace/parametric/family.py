"""Constructive sweep-then-drop family for task 61aeeba19268.

``sweep_only`` is the exact canonical rule. ``sweep_then_drop`` first forms
that complete sweep, then finds the unique non-marker 7 cue that becomes
orthogonally adjacent to the swept object and draws a source-colored vertical
ray from that cue to the bottom edge.
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Iterable

MODES = ("sweep_only", "sweep_then_drop")
_TRAIN_SIZES = (9, 11, 14, 18, 23, 27)
_TEST_SIZES = (12, 17, 24, 30)
_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_NEIGHBORS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Every shape occupies four rows. Above-shapes expose a rightmost cell on the
# top row; below-shapes expose one on the bottom row. This lets a cue sit just
# outside the source rows and become adjacent only after the horizontal sweep.
_ABOVE_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (3, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 0)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (3, 1)),
)
_BELOW_SHAPES = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (3, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1)),
)


def _rng(*parts: object) -> random.Random:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _object_cells(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 7)
    ]


def stage_a(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the exact canonical row-major sweep semantics."""
    obj = _object_cells(grid)
    if not obj:
        return _copy(grid)
    width = len(grid[0])
    max_col = max(c for _, c, _ in obj)
    out = _copy(grid)
    for shift in range(1, width - max_col):
        for r, c, value in obj:
            out[r][c + shift] = value
    return out


def _source_color(grid: list[list[int]]) -> int:
    colors = {value for _, _, value in _object_cells(grid)}
    if len(colors) != 1:
        raise ValueError(f"expected one non-marker source color, found {sorted(colors)}")
    return next(iter(colors))


def _adjacent_cues(grid: list[list[int]], colored: list[list[int]], source: int) -> list[tuple[int, int]]:
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 7
        and (r, c) != (0, 0)
        and any(
            0 <= r + dr < h
            and 0 <= c + dc < w
            and colored[r + dr][c + dc] == source
            for dr, dc in _NEIGHBORS4
        )
    ]


def _drop(stage: list[list[int]], cue: tuple[int, int], source: int) -> list[list[int]]:
    out = _copy(stage)
    r, c = cue
    for rr in range(r, len(out)):
        out[rr][c] = source
    return out


def analyze(grid: list[list[int]]) -> dict[str, object]:
    source = _source_color(grid)
    swept = stage_a(grid)
    original = _adjacent_cues(grid, grid, source)
    after = _adjacent_cues(grid, swept, source)
    if len(after) != 1:
        raise ValueError(f"expected exactly one cue selected by the swept intermediate, found {after}")
    return {
        "source_color": source,
        "selected_cue": list(after[0]),
        "original_adjacent_cues": [list(cell) for cell in original],
        "stage_a_adjacent_cues": [list(cell) for cell in after],
        "stage_a_colored_cells": sum(value == source for row in swept for value in row),
    }


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    swept = stage_a(grid)
    if mode == "sweep_only":
        return swept
    info = analyze(grid)
    return _drop(swept, tuple(info["selected_cue"]), int(info["source_color"]))


def _choose_safe_cue(
    grid: list[list[int]],
    swept: list[list[int]],
    source: int,
    *,
    required_col: int | None = None,
    forbidden: set[tuple[int, int]] | None = None,
) -> tuple[int, int]:
    forbidden = forbidden or set()
    h, w = len(grid), len(grid[0])
    candidates = []
    for r in range(1, h):
        columns: Iterable[int] = (required_col,) if required_col is not None else range(1, w)
        for c in columns:
            if c is None or not 0 <= c < w or (r, c) in forbidden or grid[r][c] != 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and swept[r + dr][c + dc] == source
                for dr, dc in _NEIGHBORS4
            ):
                continue
            candidates.append((r, c))
    if not candidates:
        raise ValueError("could not place a non-adjacent cue distractor")
    return candidates[0]


def _construct_pair(seed: int, split: str, index: int, size: int, attempt: int) -> list[list[int]]:
    rng = _rng(seed, split, index, size, attempt)
    h = w = size
    grid = [[0 for _ in range(w)] for _ in range(h)]
    grid[0][0] = 7
    source = _COLORS[(seed + index + (0 if split == "train" else 3) + attempt) % len(_COLORS)]

    above = index % 2 == 0
    shapes = _ABOVE_SHAPES if above else _BELOW_SHAPES
    shape = shapes[rng.randrange(len(shapes))]
    shape_h = 1 + max(r for r, _ in shape)
    shape_w = 1 + max(c for _, c in shape)
    c0_hi = max(2, min(w // 3, w - shape_w - 4))
    c0 = rng.randint(2, c0_hi)
    if above:
        r0 = rng.randint(3, max(3, h - shape_h - 2))
        boundary_row = r0
        cue_row = boundary_row - 1
    else:
        r0 = rng.randint(2, max(2, h - shape_h - 3))
        boundary_row = r0 + shape_h - 1
        cue_row = boundary_row + 1
    for r, c in shape:
        grid[r0 + r][c0 + c] = source

    max_col = c0 + max(c for _, c in shape)
    available = list(range(max_col + 2, w - 1))
    if len(available) < 2:
        raise ValueError("canvas too narrow for a newly adjacent cue")
    if split == "train" and index == 0:
        cue_col = available[-1]
    elif split == "train" and index == 1:
        cue_col = available[0]
    else:
        cue_col = available[(seed + index + attempt) % len(available)]
    grid[cue_row][cue_col] = 7

    swept = stage_a(grid)
    selected = (cue_row, cue_col)
    # A guaranteed rightmost decoy defeats "choose the rightmost 7".
    right_decoy = _choose_safe_cue(grid, swept, source, required_col=w - 1, forbidden={selected})
    grid[right_decoy[0]][right_decoy[1]] = 7
    swept = stage_a(grid)
    left_decoy = _choose_safe_cue(
        grid, swept, source, required_col=1, forbidden={selected, right_decoy}
    )
    grid[left_decoy[0]][left_decoy[1]] = 7

    info = analyze(grid)
    if tuple(info["selected_cue"]) != selected or info["original_adjacent_cues"]:
        raise ValueError("constructed scene violates the sweep-selected cue contract")
    return grid


def _pair(seed: int, split: str, index: int, size: int, mode: str, seen: set[str]) -> dict[str, list[list[int]]]:
    for attempt in range(128):
        try:
            grid = _construct_pair(seed, split, index, size, attempt)
        except ValueError:
            continue
        fingerprint = json.dumps(grid, separators=(",", ":"))
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        return {"input": grid, "output": solve(grid, mode)}
    raise RuntimeError(f"could not construct distinct {split} pair {index}")


def generate_episode(seed: int, mode: str, demos: int, queries: int, program_solution: str) -> dict[str, object]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    seen: set[str] = set()
    train = [_pair(seed, "train", i, _TRAIN_SIZES[i], mode, seen) for i in range(demos)]
    test = [_pair(seed, "test", i, _TEST_SIZES[i], mode, seen) for i in range(queries)]
    return {"train": train, "test": test, "program_solution": program_solution}


# Named plausible wrong rules retained for bounded adversarial review.
def rival_sweep_only(grid: list[list[int]]) -> list[list[int]]:
    return stage_a(grid)


def rival_original_adjacency(grid: list[list[int]]) -> list[list[int]]:
    source = _source_color(grid)
    cues = _adjacent_cues(grid, grid, source)
    return _drop(stage_a(grid), cues[0], source) if len(cues) == 1 else stage_a(grid)


def rival_rightmost_cue(grid: list[list[int]]) -> list[list[int]]:
    source = _source_color(grid)
    cues = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7 and (r, c) != (0, 0)]
    cue = max(cues, key=lambda p: (p[1], -p[0]))
    return _drop(stage_a(grid), cue, source)


def rival_fixed_w_minus_2(grid: list[list[int]]) -> list[list[int]]:
    source = _source_color(grid)
    c = len(grid[0]) - 2
    cues = [(r, c) for r in range(len(grid)) if grid[r][c] == 7 and (r, c) != (0, 0)]
    return _drop(stage_a(grid), cues[0], source) if len(cues) == 1 else stage_a(grid)
