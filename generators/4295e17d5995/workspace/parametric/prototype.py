"""Task-local matching/opposite-wall episodes; Python outputs are label claims.

The native worker independently executes every claim through the returned Racket
program.  The canonical generator and its selected authority are unchanged.
"""
from __future__ import annotations

from collections import Counter, deque
import hashlib
from pathlib import Path
import random
from typing import Any


Grid = list[list[int]]
Cells = list[tuple[int, int]]
SETTINGS = ("matching", "opposite")
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
MAX_ATTEMPTS = 64
QUERY_SIZES = ((9, 9), (16, 20), (24, 27), (30, 30))
_DIRECTIONS = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
_RIVALS = ("other_setting", "independent_no_blocking", "cellwise", "connectivity4",
           "identity", "nearest_wall", "farthest_wall")
_CANONICAL_DIRECTIONS = "(list (list lw -1) (list rw 1))"


def _relation(settings: dict[str, str]) -> str:
    if type(settings) is not dict or set(settings) != {"wall_relation"}:
        raise ValueError("settings must contain exactly wall_relation")
    relation = settings["wall_relation"]
    if type(relation) is not str or relation not in SETTINGS:
        raise ValueError("wall_relation must be matching or opposite")
    return relation


def _request(seed: int, demos: int, queries: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    for name, value, limits in (("demos", demos, DEMO_LIMITS), ("queries", queries, QUERY_LIMITS)):
        if type(value) is not int or not limits[0] <= value <= limits[1]:
            raise ValueError(f"{name} must be an exact integer in {limits[0]}..{limits[1]}")


def program(settings: dict[str, str]) -> str:
    """Return exact canonical bytes, or change only the color/direction list."""
    relation = _relation(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    if canonical.count(_CANONICAL_DIRECTIONS) != 1:
        raise ValueError("canonical resource does not contain one expected direction list")
    if relation == "matching":
        return canonical
    return canonical.replace(_CANONICAL_DIRECTIONS, "(list (list lw 1) (list rw -1))")


def _structure(grid: Grid) -> None:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 list rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 3..30 columns")
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("grid cells must be exact integer colors 0..9")
    left, right = grid[0][0], grid[0][-1]
    if left == right or 7 in (left, right):
        raise ValueError("walls must be distinct non-7 colors")
    if any(row[0] != left or row[-1] != right for row in grid):
        raise ValueError("walls must be full-height constant colors")
    interior = {v for row in grid for v in row[1:-1]}
    if not interior <= {7, left, right} or not {left, right} <= interior:
        raise ValueError("interior must contain both wall colors and no foreign color")


def components(grid: Grid, color: int, connectivity: int = 8) -> list[Cells]:
    """Interior components in canonical row-major discovery/BFS cell order."""
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    h, w = len(grid), len(grid[0])
    visited = set()
    groups = []
    directions = _DIRECTIONS if connectivity == 8 else ((-1, 0), (0, -1), (0, 1), (1, 0))
    for r in range(h):
        for c in range(1, w - 1):
            if grid[r][c] != color or (r, c) in visited:
                continue
            queue = deque([(r, c)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                if ((rr, cc) in visited or not (0 <= rr < h and 1 <= cc < w - 1)
                        or grid[rr][cc] != color):
                    continue
                visited.add((rr, cc))
                cells.append((rr, cc))
                queue.extend((rr + dr, cc + dc) for dr, dc in directions)
            groups.append(list(reversed(cells)))
    return groups


def _frame(h: int, w: int, left: int, right: int) -> Grid:
    grid = [[7] * w for _ in range(h)]
    for row in grid:
        row[0], row[-1] = left, right
    return grid


def _simulate(grid: Grid, relation: str, rival: str | None = None) -> tuple[Grid, bool]:
    h, w = len(grid), len(grid[0])
    left, right = grid[0][0], grid[0][-1]
    out = _frame(h, w, left, right)
    collision_free = True
    sign = -1 if relation == "matching" else 1
    for color, group_direction in ((left, sign), (right, -sign)):
        groups = components(grid, color, 4 if rival == "connectivity4" else 8)
        if rival == "cellwise":
            groups = [[cell] for group in groups for cell in group]
        # Python's stable sort preserves Racket's row-major discovery ties.
        groups.sort(key=lambda cells: min(c for _, c in cells) if group_direction == -1
                    else -max(c for _, c in cells))
        for cells in groups:
            direction = group_direction
            if rival in ("nearest_wall", "farthest_wall"):
                direction = -1 if sum(c for _, c in cells) / len(cells) < (w - 1) / 2 else 1
                if rival == "farthest_wall":
                    direction *= -1
            if any(out[r][c] != 7 for r, c in cells):
                collision_free = False
            if rival == "independent_no_blocking":
                shift = min(c - 1 if direction == -1 else w - 2 - c for _, c in cells)
            else:
                distances = []
                for r, c in cells:
                    cursor = c
                    while 0 <= cursor + direction < w and out[r][cursor + direction] == 7:
                        cursor += direction
                    distances.append(abs(cursor - c))
                shift = min(distances)
            moved = [(r, c + direction * shift) for r, c in cells]
            if any(out[r][c] != 7 for r, c in moved):
                collision_free = False
            for r, c in moved:
                out[r][c] = color
    return out, collision_free


def solve(grid: Grid, settings: dict[str, str]) -> Grid:
    """Exact Python label claim, including the authority's two color passes."""
    relation = _relation(settings)
    _structure(grid)
    return _simulate(grid, relation)[0]


def validate_grid(grid: Grid) -> None:
    """Check the shared sampled grammar, including safe settling both ways."""
    _structure(grid)
    if len(grid) < 9 or len(grid[0]) < 9:
        raise ValueError("sampled canvases must be at least 9x9")
    counts = Counter(v for row in grid for v in row)
    for relation in SETTINGS:
        out, collision_free = _simulate(grid, relation)
        if not collision_free or counts != Counter(v for row in out for v in row):
            raise ValueError(f"input fails collision-free rigid settling for {relation}")


def rival_names() -> tuple[str, ...]:
    return _RIVALS


def solve_rival(grid: Grid, settings: dict[str, str], name: str) -> Grid:
    """Finite authoring rivals; adjacent rivals.py supplies their Racket forms."""
    relation = _relation(settings)
    _structure(grid)
    if name not in _RIVALS:
        raise ValueError(f"unknown rival: {name}")
    if name == "identity":
        return [row[:] for row in grid]
    if name == "other_setting":
        return _simulate(grid, "opposite" if relation == "matching" else "matching")[0]
    return _simulate(grid, relation, name)[0]


def demo_rival_failures(demos: list[dict[str, Grid]], settings: dict[str, str]) -> list[str]:
    """Return rivals still fitting every supplied demonstration, no queries."""
    _relation(settings)
    return [name for name in _RIVALS
            if all(solve_rival(pair["input"], settings, name) == pair["output"] for pair in demos)]


def _rng(seed: int, split: str, index: int, attempt: int = 0) -> random.Random:
    key = f"4295e17d5995-parametric-v1:{seed}:{split}:{index}:{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _palette(rng: random.Random) -> tuple[int, int]:
    return tuple(rng.sample([0, 1, 2, 3, 4, 5, 6, 8, 9], 2))


def _shape(shape: tuple[tuple[int, int], ...], rng: random.Random) -> Cells:
    # Reflections change row supports, exposed ends, and blocking distances.
    reflect_r, reflect_c = rng.randrange(2), rng.randrange(2)
    cells = [(-r if reflect_r else r, -c if reflect_c else c) for r, c in shape]
    low_r, low_c = min(r for r, _ in cells), min(c for _, c in cells)
    return sorted((r - low_r, c - low_c) for r, c in cells)


def _paint(grid: Grid, shape: Cells, r0: int, c0: int, color: int) -> None:
    for r, c in shape:
        if grid[r0 + r][c0 + c] != 7:
            raise ValueError("constructive placement overlapped another cell")
        grid[r0 + r][c0 + c] = color


_SMALL = (
    ((0, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
)
_THREE = (
    ((0, 0), (1, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
)
_FOUR = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 1), (3, 1), (3, 2)),
    ((0, 0), (1, 1), (2, 2), (3, 3)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)),
)
_NARROW_FOUR = (
    ((0, 0), (0, 1), (1, 0), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 0), (3, 0), (3, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (3, 0), (3, 1)),
)


def _teaching_scene(seed: int, index: int, attempt: int) -> Grid:
    rng = _rng(seed, "teaching", index, attempt)
    h = (11 if index == 0 else 13) + rng.randrange(2)
    w = (17 if index == 0 else 19) + rng.randrange(2)
    left, right = _palette(rng)
    grid = _frame(h, w, left, right)
    # Two same-color queues at one starting side. The second demonstration
    # exchanges starting sides, so no location-only rule fits both examples.
    for role, color, r0 in ((0, left, 0), (1, right, h - 3)):
        right_side = bool(role) ^ bool(index)
        cols = (w - 8, w - 4) if right_side else (2, 6)
        diagonal = _shape(((0, 0), (1, 1), (2, 2)), rng)
        follower = _shape(rng.choice(( ((0, 0), (1, 0)),
                                      ((0, 0), (1, 0), (1, 1)) )), rng)
        _paint(grid, diagonal, r0, cols[0], color)
        _paint(grid, follower, r0 + rng.randrange(2), cols[1], color)
    # Both colors share this row band, with nonrectangular rigid pieces.
    middle = (h - 3) // 2
    _paint(grid, _shape(rng.choice(_THREE[1:]), rng), middle, 4, left)
    _paint(grid, _shape(rng.choice(_THREE[1:]), rng), middle, w - 7, right)
    return grid


def _teaching_inputs(seed: int) -> tuple[list[Grid], int]:
    for attempt in range(MAX_ATTEMPTS):
        grids = [_teaching_scene(seed, i, attempt) for i in range(2)]
        try:
            for grid in grids:
                validate_grid(grid)
        except ValueError:
            continue
        if all(not demo_rival_failures(
                [{"input": g, "output": solve(g, {"wall_relation": relation})} for g in grids],
                {"wall_relation": relation}) for relation in SETTINGS):
            return grids, attempt + 1
    raise ValueError(f"could not construct a distinguishing two-demo lesson in {MAX_ATTEMPTS} attempts")


def _spread(widths: list[int], start: int, end: int, rng: random.Random) -> list[int]:
    """Use both endpoints, with at least one blank column between boxes."""
    extra = end - start + 1 - sum(widths) - (len(widths) - 1)
    if extra < 0:
        raise ValueError("shape widths exceed constructive band")
    gaps = [1] * (len(widths) - 1)
    for _ in range(extra):
        gaps[rng.randrange(len(gaps))] += 1
    cols = [start]
    for i, gap in enumerate(gaps):
        cols.append(cols[-1] + widths[i] + gap)
    return cols


def _scene(rng: random.Random, h: int, w: int) -> Grid:
    left, right = _palette(rng)
    grid = _frame(h, w, left, right)
    if h < 10:
        bands = [(0, 2), (3, 3), (h - 2, 2)]
    else:
        bh = 4 if h >= 20 else 3
        n = h // (bh + 1)
        bands = [(round(i * (h - bh) / (n - 1)), bh) for i in range(n)]
    for index, (r0, bh) in enumerate(bands):
        mixed = index % 2 == 1
        if mixed and w >= 24 and bh == 4:
            shapes = [_shape(rng.choice(_NARROW_FOUR), rng) for _ in range(4)]
            colors = [left, left, right, right]
            rng.shuffle(colors)
            start, end = 7, w - 8
        elif mixed:
            pool = _SMALL if bh == 2 or w < 11 else _THREE
            shapes = [_shape(rng.choice(pool), rng) for _ in range(2)]
            colors = [left, right]
            rng.shuffle(colors)
            start, end = (2, w - 3) if w < 11 else (4, w - 5)
        else:
            n = 4 if w >= 24 else 3 if w >= 16 else 2
            pool = _FOUR if bh == 4 else _THREE if bh == 3 else _SMALL
            shapes = [_shape(rng.choice(pool), rng) for _ in range(n)]
            colors = [left if index % 4 == 0 else right] * n
            start, end = 1, w - 2
        widths = [max(c for _, c in s) + 1 for s in shapes]
        for shape, col, color in zip(shapes, _spread(widths, start, end, rng), colors):
            sh = max(r for r, _ in shape) + 1
            _paint(grid, shape, r0 + rng.randrange(bh - sh + 1), col, color)
    return grid


def _substantive(grid: Grid) -> bool:
    if (len(grid), len(grid[0])) != (30, 30):
        return True
    occupied = [(r, c) for r in range(30) for c in range(1, 29) if grid[r][c] != 7]
    if len(occupied) < 110 or len({r for r, _ in occupied}) < 22:
        return False
    for relation in SETTINGS:
        out = _simulate(grid, relation)[0]
        if sum(a != b for ra, rb in zip(grid, out) for a, b in zip(ra, rb)) < 100:
            return False
    return True


def _sample_scene(seed: int, split: str, index: int, h: int, w: int) -> tuple[Grid, int]:
    for attempt in range(MAX_ATTEMPTS):
        try:
            grid = _scene(_rng(seed, split, index, attempt), h, w)
            validate_grid(grid)
            if _substantive(grid):
                return grid, attempt + 1
        except ValueError:
            continue
    raise ValueError(f"could not construct {split} {index} at {h}x{w} in {MAX_ATTEMPTS} attempts")


def sample_inputs(seed: int, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    """Matched input streams; extending either count leaves every prefix fixed.

    The attempts field is private sampler diagnostics. It is never needed by a
    solver and is not part of a public challenge or its identity.
    """
    _request(seed, demos, queries)
    train, teach_attempts = _teaching_inputs(seed)
    train_attempts = [teach_attempts, teach_attempts]
    for index in range(2, demos):
        grid, attempts = _sample_scene(seed, "demo", index, 14 + index, 19 + index)
        train.append(grid)
        train_attempts.append(attempts)
    test, test_attempts = [], []
    for index, (h, w) in enumerate(QUERY_SIZES[:queries]):
        grid, attempts = _sample_scene(seed, "query", index, h, w)
        test.append(grid)
        test_attempts.append(attempts)
    keys = [tuple(tuple(row) for row in g) for g in train + test]
    if len(set(keys)) != len(keys):
        raise ValueError("sampler produced duplicate input grids")
    return {"train": train, "test": test,
            "attempts": {"train": train_attempts, "test": test_attempts,
                         "cap_per_draw": MAX_ATTEMPTS}}


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    """Materialize one private episode, ready for independent native execution."""
    _relation(settings)
    sampled = sample_inputs(seed, demos, queries)
    return {"train": [{"input": g, "output": solve(g, settings)} for g in sampled["train"]],
            "test": [{"input": g, "output": solve(g, settings)} for g in sampled["test"]],
            "program_solution": program(settings)}
