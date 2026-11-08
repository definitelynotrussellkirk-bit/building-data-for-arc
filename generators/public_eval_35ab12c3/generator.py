"""Public 35ab12c3: complete angular polygon edges, then paint adjacent shadows.

The standalone sampler uses only the standard library and the shared keyed
``gen_ctx`` helper.  Racket remains the label authority through the native
adapter; the Python solver is an independently tested mirror and audit oracle.
"""
from __future__ import annotations

from collections import Counter
import copy
import math

from puzzle_generators.base import gen_ctx

TASK_ID = GENERATOR_ID = "public_eval_35ab12c3"
RULE_TASK_ID = "ee_35ab12c3"
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
SUMMARY = "Complete aligned angular-neighbor edges, then translate completed shapes from adjacent singleton markers."
AXES = {}
EDGE_MODES = ("all_8", "orthogonal")


def _int(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _validate_grid(grid: object) -> tuple[int, int, int]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid height must be 1..30")
    if not grid or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 1..30")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    return len(grid), width, background


def _angular_order(cells: set[tuple[int, int]]) -> list[tuple[int, int]]:
    points = sorted(cells)
    if len(points) <= 1:
        return points
    n = len(points)
    sum_r = sum(r for r, _ in points)
    sum_c = sum(c for _, c in points)

    def key(point: tuple[int, int]) -> tuple[float, int, int, int]:
        y = n * point[0] - sum_r
        x = n * point[1] - sum_c
        return (math.atan2(y, x), y * y + x * x, point[0], point[1])

    return sorted(points, key=key)


def _aligned(a: tuple[int, int], b: tuple[int, int], edge_mode: str) -> bool:
    dr = b[0] - a[0]
    dc = b[1] - a[1]
    return dr == 0 or dc == 0 or (edge_mode == "all_8" and abs(dr) == abs(dc))


def _segment(a: tuple[int, int], b: tuple[int, int]) -> set[tuple[int, int]]:
    dr = b[0] - a[0]
    dc = b[1] - a[1]
    steps = max(abs(dr), abs(dc))
    step_r = (dr > 0) - (dr < 0)
    step_c = (dc > 0) - (dc < 0)
    return {(a[0] + k * step_r, a[1] + k * step_c) for k in range(steps + 1)}


def _complete_cells(
    cells: set[tuple[int, int]],
    edge_mode: str,
    foil: str | None = None,
) -> set[tuple[int, int]]:
    if edge_mode not in EDGE_MODES:
        raise ValueError("unknown edge mode")
    points = sorted(cells)
    result = set(points)
    if len(points) < 2:
        return result

    if foil == "row_order":
        order = points
    elif foil == "convex_hull":
        # Monotone-chain hull: a plausible but wrong substitute for angular order.
        def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower: list[tuple[int, int]] = []
        for point in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
                lower.pop()
            lower.append(point)
        upper: list[tuple[int, int]] = []
        for point in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
                upper.pop()
            upper.append(point)
        order = lower[:-1] + upper[:-1]
    else:
        order = _angular_order(cells)

    if foil == "all_pairs":
        edges = [(a, b) for i, a in enumerate(points) for b in points[i + 1 :]]
    elif len(order) == 2:
        edges = [(order[0], order[1])]
    else:
        edges = list(zip(order, order[1:] + order[:1]))

    mode = "orthogonal" if foil == "orthogonal_only" else edge_mode
    for a, b in edges:
        if _aligned(a, b, mode):
            result.update(_segment(a, b))
    return result


def analyse(grid: list[list[int]], edge_mode: str = "all_8", foil: str | None = None) -> dict[str, object]:
    height, width, background = _validate_grid(grid)
    if edge_mode not in EDGE_MODES:
        raise ValueError("unknown edge mode")
    colors = sorted({value for row in grid for value in row if value != background})
    seeds = {
        color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        for color in colors
    }
    completed = {color: _complete_cells(cells, edge_mode, foil) for color, cells in seeds.items()}
    companions: dict[int, tuple[tuple[int, int], int, tuple[int, int]]] = {}
    for color, cells in seeds.items():
        if len(cells) != 1:
            continue
        marker = next(iter(cells))
        adjacent: list[tuple[tuple[int, int], int]] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                r, c = marker[0] + dr, marker[1] + dc
                if 0 <= r < height and 0 <= c < width:
                    target = grid[r][c]
                    if target != background and target != color:
                        adjacent.append(((r, c), target))
        if len(adjacent) == 1:
            anchor, target = adjacent[0]
            companions[color] = (anchor, target, (marker[0] - anchor[0], marker[1] - anchor[1]))
    return {
        "height": height,
        "width": width,
        "background": background,
        "colors": colors,
        "seeds": seeds,
        "completed": completed,
        "companions": companions,
    }


def solve(
    grid: list[list[int]],
    edge_mode: str = "all_8",
    foil: str | None = None,
) -> list[list[int]]:
    info = analyse(grid, edge_mode, foil)
    background = info["background"]
    colors = info["colors"]
    seeds = info["seeds"]
    completed = info["completed"]
    companions = info["companions"]
    height = info["height"]
    width = info["width"]
    out = copy.deepcopy(grid)

    for color in colors:
        for r, c in completed[color]:
            if out[r][c] == background:
                out[r][c] = color

    if foil == "no_shadow":
        return out

    for color in colors:
        if color not in companions:
            continue
        _, target, (dr, dc) = companions[color]
        source = seeds[target] if foil == "seed_shadow" else completed[target]
        for r, c in source:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                if foil == "overwrite_shadow" or out[rr][cc] == background:
                    out[rr][cc] = color
    return out


# Coordinates are relative to each motif origin.  The first two profiles both
# contain diagonal and orthogonal angular-neighbor edges, so the two-example
# minimum teaches the episode-fixed edge mode.
_MOTIFS: dict[str, tuple[tuple[int, int], ...]] = {
    "hexagon": ((0, 3), (0, 4), (3, 0), (3, 7), (6, 3), (6, 4)),
    "concave": ((0, 0), (0, 6), (1, 7), (6, 2), (6, 0)),
    "inner_chain": ((0, 5), (3, 8), (7, 8), (7, 6), (5, 4), (5, 1)),
    "rectangle": ((0, 0), (0, 7), (5, 7), (5, 0)),
    "kite": ((0, 4), (4, 8), (7, 5), (7, 3), (4, 0)),
    "unaligned": ((0, 0), (2, 5), (5, 1)),
}


def _place(
    grid: list[list[int]],
    origin: tuple[int, int],
    points: tuple[tuple[int, int], ...],
    color: int,
) -> list[tuple[int, int]]:
    absolute = [(origin[0] + r, origin[1] + c) for r, c in points]
    for r, c in absolute:
        if grid[r][c] != grid[0][0]:
            raise ValueError("motif collision")
        grid[r][c] = color
    return absolute


def _marker(
    grid: list[list[int]],
    anchor: tuple[int, int],
    offset: tuple[int, int],
    color: int,
) -> None:
    r, c = anchor[0] + offset[0], anchor[1] + offset[1]
    if grid[r][c] != grid[0][0]:
        raise ValueError("marker collision")
    grid[r][c] = color


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    if code & 4:
        out = [row[::-1] for row in out]
    for _ in range(code % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def sample(seed: int, index: int) -> list[list[int]]:
    _int(seed, 0, 2**63 - 1, "seed")
    _int(index, 0, 2**31 - 1, "sample_index")
    ctx = gen_ctx(seed=seed, sample_index=index, version="1.0", task_id=TASK_ID)
    rng = ctx.draw_rng("geometry_palette_angular_shadows")
    profile = index % 4
    height, width = ((18, 20), (20, 18), (24, 24), (30, 30))[profile]
    background = rng.randrange(10)
    palette = rng.sample([value for value in range(10) if value != background], 8)
    grid = [[background] * width for _ in range(height)]

    if profile == 0:
        first = _place(grid, (2, 2), _MOTIFS["hexagon"], palette[0])
        _marker(grid, first[2], (0, -1), palette[1])
        second = _place(grid, (9, 10), _MOTIFS["concave"], palette[2])
        _marker(grid, second[2], (0, 1), palette[3])
        _place(grid, (9, 1), _MOTIFS["inner_chain"], palette[4])
    elif profile == 1:
        first = _place(grid, (2, 2), _MOTIFS["concave"], palette[0])
        _marker(grid, first[0], (-1, 0), palette[1])
        second = _place(grid, (10, 8), _MOTIFS["kite"], palette[2])
        _marker(grid, second[1], (-1, 1), palette[3])
        _place(grid, (3, 12), _MOTIFS["unaligned"], palette[4])
    elif profile == 2:
        first = _place(grid, (2, 2), _MOTIFS["inner_chain"], palette[0])
        _marker(grid, first[5], (0, -1), palette[1])
        second = _place(grid, (13, 13), _MOTIFS["hexagon"], palette[2])
        _marker(grid, second[3], (0, 1), palette[3])
        third = _place(grid, (15, 2), _MOTIFS["rectangle"], palette[4])
        _marker(grid, third[0], (-1, 0), palette[5])
    else:
        first = _place(grid, (2, 2), _MOTIFS["hexagon"], palette[0])
        _marker(grid, first[2], (0, -1), palette[1])
        second = _place(grid, (2, 18), _MOTIFS["concave"], palette[2])
        _marker(grid, second[2], (0, 1), palette[3])
        third = _place(grid, (17, 2), _MOTIFS["inner_chain"], palette[4])
        _marker(grid, third[5], (0, -1), palette[5])
        fourth = _place(grid, (18, 19), _MOTIFS["kite"], palette[6])
        _marker(grid, fourth[1], (-1, 1), palette[7])

    # Small keyed jitter changes appearance without changing the semantic profile.
    transform = rng.randrange(8)
    grid = _transform(grid, transform)
    info = analyse(grid)
    # Every generated marker must have exactly one original adjacent target.
    expected_markers = 2 if profile < 2 else 3 if profile == 2 else 4
    if len(info["companions"]) != expected_markers:
        raise ValueError("generated companion relation is ambiguous")
    return grid


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: object) -> list[list[int]]:
    if difficulty not in (None, "easy", "medium", "hard") or overrides:
        raise ValueError("unsupported difficulty or override")
    return sample(seed, sample_index)


def check_invariants(grid: list[list[int]]) -> list[str]:
    try:
        analyse(grid)
    except ValueError as error:
        return [str(error)]
    return []
