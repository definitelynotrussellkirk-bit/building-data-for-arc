"""Constructive connect-then-mark-crossings family for task 6c08e545720f.

``connect_only`` is the exact canonical rule: every color represented by two
objects is joined along its 45-degree diagonal.  ``connect_then_mark_crossings``
first builds that complete intermediate, then finds every genuine X crossing
formed by two differently colored diagonals and recolors the crossing center
with the singleton cue color from the input.
"""
from __future__ import annotations

import hashlib
import json
import random

MODES = ("connect_only", "connect_then_mark_crossings")
_TRAIN_SIZES = (15, 17, 19, 21, 24, 27)
_TEST_SIZES = (16, 20, 25, 30)
_BACKGROUND = 7
_PALETTE = (0, 1, 2, 3, 4, 5, 6, 8, 9)


def _rng(*parts: object) -> random.Random:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _cells_by_color(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != _BACKGROUND:
                by_color.setdefault(value, []).append((r, c))
    return by_color


def _color_order(grid: list[list[int]]) -> list[int]:
    # The protected DSL's ``objects`` primitive returns monochrome objects in
    # numeric color order for this singleton grammar; ``unique`` preserves it.
    return sorted(_cells_by_color(grid))


def _draw_pair(
    out: list[list[int]], first: tuple[int, int], second: tuple[int, int], color: int
) -> None:
    r0, c0 = first
    r1, c1 = second
    dr = 1 if r1 > r0 else -1
    dc = 1 if c1 > c0 else -1
    r, c = r0 + dr, c0 + dc
    # The canonical rule excludes the second object, which is already present.
    while r != r1:
        out[r][c] = color
        r += dr
        c += dc


def stage_a(grid: list[list[int]]) -> list[list[int]]:
    """Mirror the canonical behavior for the constructed singleton objects."""
    out = _copy(grid)
    by_color = _cells_by_color(grid)
    for color in _color_order(grid):
        cells = by_color[color]
        if len(cells) != 2:
            continue
        first, second = cells
        if abs(first[0] - second[0]) != abs(first[1] - second[1]) or first == second:
            raise ValueError(f"paired color {color} is not on a nonzero diagonal")
        _draw_pair(out, first, second, color)
    return out


def crossings(grid: list[list[int]]) -> list[tuple[int, int]]:
    """Return centers whose four diagonal neighbors form a two-color X."""
    h, w = len(grid), len(grid[0])
    found: list[tuple[int, int]] = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            nw = grid[r - 1][c - 1]
            ne = grid[r - 1][c + 1]
            sw = grid[r + 1][c - 1]
            se = grid[r + 1][c + 1]
            if (
                nw != _BACKGROUND
                and ne != _BACKGROUND
                and nw == se
                and ne == sw
                and nw != ne
            ):
                found.append((r, c))
    return found


def _cue_color(grid: list[list[int]]) -> int:
    singleton = [color for color, cells in _cells_by_color(grid).items() if len(cells) == 1]
    if len(singleton) != 1:
        raise ValueError(f"expected exactly one singleton cue color, found {singleton}")
    return singleton[0]


def analyze(grid: list[list[int]]) -> dict[str, object]:
    connected = stage_a(grid)
    return {
        "cue_color": _cue_color(grid),
        "crossings": [list(cell) for cell in crossings(connected)],
        "input_crossings": [list(cell) for cell in crossings(grid)],
        "paired_colors": sorted(
            color for color, cells in _cells_by_color(grid).items() if len(cells) == 2
        ),
        "stage_a_non_background": sum(
            value != _BACKGROUND for row in connected for value in row
        ),
    }


def _mark(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> list[list[int]]:
    out = _copy(grid)
    for r, c in cells:
        out[r][c] = color
    return out


def solve(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    connected = stage_a(grid)
    if mode == "connect_only":
        return connected
    return _mark(connected, crossings(connected), _cue_color(grid))


def _line_cells(first: tuple[int, int], second: tuple[int, int]) -> set[tuple[int, int]]:
    r0, c0 = first
    r1, c1 = second
    dr = 1 if r1 > r0 else -1
    dc = 1 if c1 > c0 else -1
    return {(r0 + k * dr, c0 + k * dc) for k in range(abs(r1 - r0) + 1)}


def _cluster(
    center: tuple[int, int], span: int
) -> tuple[tuple[tuple[int, int], tuple[int, int]], tuple[tuple[int, int], tuple[int, int]]]:
    """Build asymmetric paired diagonals whose intersection is not a pair midpoint."""
    r, c = center
    a = ((r - (span - 1), c - (span - 1)), (r + span, c + span))
    b = ((r - span, c + span), (r + (span - 1), c - (span - 1)))
    return a, b


def _safe_cue_cell(
    size: int, occupied_lines: set[tuple[int, int]], rng: random.Random
) -> tuple[int, int]:
    candidates = [
        (r, c)
        for r in range(size)
        for c in range(size)
        if (r, c) not in occupied_lines
        and all((r + dr, c + dc) not in occupied_lines for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)))
    ]
    if not candidates:
        raise ValueError("no safe singleton cue location")
    # Prefer an edge/corner region so it cannot be mistaken for a crossing marker.
    edge = [p for p in candidates if min(p[0], p[1], size - 1 - p[0], size - 1 - p[1]) <= 1]
    pool = edge or candidates
    return pool[rng.randrange(len(pool))]


def _cue_for(seed: int, split: str, index: int) -> int:
    # The first two visible demonstrations deliberately disagree with a fixed-0 shortcut.
    if split == "train" and index == 0:
        return 0
    if split == "train" and index == 1:
        return 5
    offset = 0 if split == "train" else 4
    return _PALETTE[(seed * 3 + index * 5 + offset) % len(_PALETTE)]


def _construct_pair(seed: int, split: str, index: int, size: int, attempt: int) -> list[list[int]]:
    rng = _rng(seed, split, index, size, attempt)
    span = min(6, max(3, size // 4))
    if size == 30:
        shift = rng.choice((-1, 0, 1))
        centers = ((8 + shift, 8 + shift), (21 + shift, 21 + shift))
    else:
        lo = span + 1
        hi = size - span - 2
        if lo > hi:
            raise ValueError("canvas too small for asymmetric crossing")
        centers = ((rng.randint(lo, hi), rng.randint(lo, hi)),)

    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    line_sets: list[set[tuple[int, int]]] = []
    for center in centers:
        for pair in _cluster(center, span):
            cells = _line_cells(*pair)
            if any(not (0 <= r < size and 0 <= c < size) for r, c in cells):
                raise ValueError("cluster escaped canvas")
            pairs.append(pair)
            line_sets.append(cells)

    # Distinct clusters must not share or touch their line systems; each cluster's
    # own two lines are allowed to share exactly its crossing center.
    if len(centers) == 2:
        first_union = line_sets[0] | line_sets[1]
        second_union = line_sets[2] | line_sets[3]
        if first_union & second_union:
            raise ValueError("crossing clusters overlap")

    cue = _cue_for(seed, split, index)
    pair_palette = [color for color in _PALETTE if color != cue]
    rng.shuffle(pair_palette)
    colors = pair_palette[: len(pairs)]

    grid = [[_BACKGROUND for _ in range(size)] for _ in range(size)]
    occupied_endpoints: set[tuple[int, int]] = set()
    for color, pair in zip(colors, pairs, strict=True):
        for r, c in pair:
            if (r, c) in occupied_endpoints:
                raise ValueError("paired endpoints collide")
            occupied_endpoints.add((r, c))
            grid[r][c] = color

    occupied_lines = set().union(*line_sets)
    cue_cell = _safe_cue_cell(size, occupied_lines, rng)
    if cue_cell in occupied_endpoints:
        raise ValueError("cue collides with endpoint")
    grid[cue_cell[0]][cue_cell[1]] = cue

    info = analyze(grid)
    expected = len(centers)
    if info["input_crossings"]:
        raise ValueError("input already contains an X crossing")
    if len(info["crossings"]) != expected:
        raise ValueError(
            f"expected {expected} independent crossing(s), found {info['crossings']}"
        )
    if size == 30 and int(info["stage_a_non_background"]) < 45:
        raise ValueError("30x30 construction is not substantive enough")
    return grid


def _pair(
    seed: int,
    split: str,
    index: int,
    size: int,
    mode: str,
    seen: set[str],
) -> dict[str, list[list[int]]]:
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


def generate_episode(
    seed: int, mode: str, demos: int, queries: int, program_solution: str
) -> dict[str, object]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    seen: set[str] = set()
    train = [_pair(seed, "train", i, _TRAIN_SIZES[i], mode, seen) for i in range(demos)]
    test = [_pair(seed, "test", i, _TEST_SIZES[i], mode, seen) for i in range(queries)]
    return {"train": train, "test": test, "program_solution": program_solution}


# Named plausible wrong rules retained for bounded adversarial review.
def rival_connect_only(grid: list[list[int]]) -> list[list[int]]:
    return stage_a(grid)


def rival_fixed_zero(grid: list[list[int]]) -> list[list[int]]:
    connected = stage_a(grid)
    return _mark(connected, crossings(connected), 0)


def rival_pair_midpoints(grid: list[list[int]]) -> list[list[int]]:
    connected = stage_a(grid)
    cells: list[tuple[int, int]] = []
    for color, endpoints in _cells_by_color(grid).items():
        if len(endpoints) != 2:
            continue
        (r0, c0), (r1, c1) = endpoints
        if (r0 + r1) % 2 == 0 and (c0 + c1) % 2 == 0:
            cells.append(((r0 + r1) // 2, (c0 + c1) // 2))
    return _mark(connected, cells, _cue_color(grid))


def rival_input_crossings(grid: list[list[int]]) -> list[list[int]]:
    connected = stage_a(grid)
    return _mark(connected, crossings(grid), _cue_color(grid))
