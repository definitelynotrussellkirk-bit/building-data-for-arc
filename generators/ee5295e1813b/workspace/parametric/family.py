"""Deterministic native family for filling and relaying diamond centers."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "ee5295e1813b"
COMPOSITIONS = ("fill_centers", "connect_equal_centers")
_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_HERE = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "fill_centers": "canonical.rkt",
    "connect_equal_centers": "connect-equal-centers.rkt",
}


def validate_settings(settings: dict) -> str:
    if type(settings) is not dict or set(settings) != {"composition"}:
        raise ValueError("settings must contain exactly composition")
    composition = settings["composition"]
    if type(composition) is not str:
        raise TypeError("composition must be an exact string")
    if composition not in COMPOSITIONS:
        raise ValueError(f"composition must be one of {COMPOSITIONS}")
    return composition


def _integer(name: str, value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def program(settings: dict) -> str:
    return (_HERE / _PROGRAM_FILES[validate_settings(settings)]).read_text(
        encoding="utf-8"
    )


def _rng(seed: int, split: str, index: int) -> random.Random:
    material = f"{TASK_ID}|center-relay-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _empty(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _place_active(grid: list[list[int]], center: tuple[int, int], color: int) -> None:
    r, c = center
    for dr, dc in _DIAGONALS:
        if grid[r + dr][c + dc] != 0:
            raise ValueError("active motif overlaps existing authored content")
        grid[r + dr][c + dc] = color


def _place_blocked(grid: list[list[int]], center: tuple[int, int], ring: int, blocker: int) -> None:
    _place_active(grid, center, ring)
    r, c = center
    grid[r][c] = blocker


def _place_partial(grid: list[list[int]], center: tuple[int, int], color: int, missing: int) -> None:
    r, c = center
    for index, (dr, dc) in enumerate(_DIAGONALS):
        if index != missing:
            if grid[r + dr][c + dc] != 0:
                raise ValueError("partial motif overlaps existing authored content")
            grid[r + dr][c + dc] = color


def _place_mismatch(
    grid: list[list[int]], center: tuple[int, int], colors: tuple[int, int]
) -> None:
    r, c = center
    values = (colors[0], colors[1], colors[1], colors[0])
    for (dr, dc), value in zip(_DIAGONALS, values):
        if grid[r + dr][c + dc] != 0:
            raise ValueError("mismatched motif overlaps existing authored content")
        grid[r + dr][c + dc] = value


def _profile(split: str, index: int) -> tuple[int, int, int]:
    train = (
        (9, 13, 1),
        (11, 15, 1),
        (13, 17, 2),
        (15, 19, 2),
        (17, 21, 3),
        (20, 24, 3),
    )
    test = (
        (10, 14, 1),
        (14, 18, 2),
        (22, 26, 4),
        (30, 30, 7),
    )
    profiles = train if split == "train" else test
    return profiles[index % len(profiles)]


def _horizontal_rows(height: int, count: int) -> list[int]:
    if count == 1:
        return [height // 2]
    if count == 2:
        return [3, height - 4]
    if count == 3:
        return [3, height // 2, height - 4]
    # Seven evenly separated rows on the 30x30 stress profile.
    if count == 7 and height == 30:
        return [2, 6, 10, 14, 18, 22, 26]
    step = max(4, (height - 4) // max(1, count - 1))
    rows = [2 + i * step for i in range(count)]
    return [min(height - 3, row) for row in rows]


def _safe_center(
    grid: list[list[int]], candidates: Iterable[tuple[int, int]]
) -> tuple[int, int]:
    height, width = len(grid), len(grid[0])
    for r, c in candidates:
        if not (1 <= r < height - 1 and 1 <= c < width - 1):
            continue
        footprint = {(r + dr, c + dc) for dr, dc in _DIAGONALS} | {(r, c)}
        if all(grid[rr][cc] == 0 for rr, cc in footprint):
            return r, c
    raise ValueError("no safe center for authored distractor")


def build_input(seed: int, split: str, index: int) -> list[list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    _integer("index", index, 0, 10_000)
    height, width, pair_count = _profile(split, index)
    rng = _rng(seed, split, index)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    grid = _empty(height, width)

    # Every scene has at least one aligned equal-color pair.  Large scenes carry
    # several independent pairs, which makes the 30x30 query substantive.
    rows = _horizontal_rows(height, pair_count)
    left_col, right_col = 2, width - 3
    for pair_index, row in enumerate(rows):
        color = palette[pair_index % len(palette)]
        _place_active(grid, (row, left_col), color)
        _place_active(grid, (row, right_col), color)

    # A nonaligned valid center prevents the relay setting from degenerating to
    # "connect every visible motif" and varies active-color multiplicity.
    extra_candidates = [
        (height - 2, width // 2),
        (2, width // 2),
        (height // 2, width // 2),
        (height // 2, 5),
    ]
    extra = _safe_center(grid, extra_candidates)
    _place_active(grid, extra, palette[(pair_count + 1) % len(palette)])

    # Authored negative controls: small scenes get one, larger scenes get more.
    distractor_count = 4 if (height, width) == (30, 30) else (2 if pair_count >= 3 else 1)
    candidates = [
        (2, width // 2),
        (height - 2, width // 2),
        (height // 2, width // 2),
        (4, width // 2),
        (height - 5, width // 2),
        (height // 2, 5),
        (height // 2, width - 6),
    ]
    used = 0
    for candidate_index in range(distractor_count):
        center = _safe_center(grid, candidates[candidate_index:] + candidates[:candidate_index])
        kind = (index + candidate_index) % 3
        if kind == 0:
            _place_blocked(
                grid,
                center,
                palette[(pair_count + 2 + candidate_index) % len(palette)],
                palette[(pair_count + 5 + candidate_index) % len(palette)],
            )
        elif kind == 1:
            _place_partial(
                grid,
                center,
                palette[(pair_count + 2 + candidate_index) % len(palette)],
                (seed + index + candidate_index) % 4,
            )
        else:
            _place_mismatch(
                grid,
                center,
                (
                    palette[(pair_count + 2 + candidate_index) % len(palette)],
                    palette[(pair_count + 4 + candidate_index) % len(palette)],
                ),
            )
        used += 1
    if used != distractor_count:
        raise ValueError("failed to place requested distractors")

    # Recognizable orthogonal context around one active center.  It is ignored
    # by both rules and refutes an all-orthogonals-blank shortcut.
    if (seed + index) % 2 == 0:
        row = rows[0]
        active_color = grid[row - 1][left_col - 1]
        context_color = next(color for color in palette if color != active_color)
        for rr, cc in ((row, left_col - 1), (row, left_col + 1)):
            if grid[rr][cc] == 0:
                grid[rr][cc] = context_color

    anchors = center_intermediate(grid)
    if not any(
        a[2] == b[2] and (a[0] == b[0] or a[1] == b[1])
        for pos, a in enumerate(anchors)
        for b in anchors[pos + 1 :]
    ):
        raise ValueError("constructed input lacks an aligned equal-color anchor pair")
    if transform(grid, "fill_centers") == transform(grid, "connect_equal_centers"):
        raise ValueError("constructed input does not distinguish settings")
    return grid


def center_intermediate(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    height, width = len(grid), len(grid[0])
    anchors: list[tuple[int, int, int]] = []
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if grid[r][c] != 0:
                continue
            values = [grid[r + dr][c + dc] for dr, dc in _DIAGONALS]
            if values[0] != 0 and all(value == values[0] for value in values):
                anchors.append((r, c, values[0]))
    return anchors


def _line_between(
    first: tuple[int, int, int], second: tuple[int, int, int]
) -> list[tuple[int, int]]:
    r1, c1, color1 = first
    r2, c2, color2 = second
    if color1 != color2:
        return []
    if r1 == r2 and abs(c2 - c1) > 1:
        lo, hi = sorted((c1, c2))
        return [(r1, c) for c in range(lo + 1, hi)]
    if c1 == c2 and abs(r2 - r1) > 1:
        lo, hi = sorted((r1, r2))
        return [(r, c1) for r in range(lo + 1, hi)]
    return []


def _connect(
    out: list[list[int]], anchors: list[tuple[int, int, int]]
) -> None:
    for index, first in enumerate(anchors):
        for second in anchors[index + 1 :]:
            for r, c in _line_between(first, second):
                if out[r][c] == 0:
                    out[r][c] = first[2]


def transform(grid: list[list[int]], composition: str) -> list[list[int]]:
    if composition not in COMPOSITIONS:
        raise ValueError(f"unsupported composition {composition!r}")
    anchors = center_intermediate(grid)
    out = deepcopy(grid)
    for r, c, color in anchors:
        out[r][c] = color
    if composition == "connect_equal_centers":
        _connect(out, anchors)
    return out


def transform_wrong_intermediate(grid: list[list[int]]) -> list[list[int]]:
    """Ablation: shift every derived center down before connection."""
    anchors = center_intermediate(grid)
    out = deepcopy(grid)
    for r, c, color in anchors:
        out[r][c] = color
    shifted = [(r + 1, c, color) for r, c, color in anchors]
    _connect(out, shifted)
    return out


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    composition = validate_settings(settings)

    def pair(split: str, index: int) -> dict:
        grid = build_input(seed, split, index)
        return {"input": grid, "output": transform(grid, composition)}

    return {
        "train": [pair("train", index) for index in range(demos)],
        "test": [pair("test", index) for index in range(queries)],
        "program_solution": program(settings),
    }
