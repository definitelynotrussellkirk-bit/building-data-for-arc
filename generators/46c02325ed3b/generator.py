"""Generator for f9a67cb5 — directed waterfall around gapped 8-walls.

A single red (2) source lies on exactly one grid edge.  That edge fixes gravity:
top/down, bottom/up, left/right, or right/left.  Cyan (8) walls are full lines
perpendicular to gravity, with one to three holes.  Water advances in the
gravity direction; when the next cell is a wall it spreads sideways along the
wall in both directions and falls through every reachable hole.  Every visited
empty cell becomes red.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "46c02325ed3b"
# 3.1.0: repair the v6 exact-override contract and canonical profile coverage.
# - dimensions and wall counts now accept their full declared domains in every
#   difficulty band, with incompatible mixed requests rejected explicitly;
# - every returned draw realizes the keyed n_walls request exactly;
# - observe_overrides exposes all exact semantic axes;
# - canonical 1..3-hole wall profiles are represented (the prior 1..2 claim was
#   false for two official pairs);
# - ordinary draws contain both a shifted-hole and an aligned-hole transition;
# - self_check now validates the full task grammar and is mutation-sensitive.
VERSION = "3.1.0"
TASK_ID = "46c02325ed3b"
RULE_HASH = "253f10f62a51"

SUMMARY = (
    "A 10..18 by 10..18 zero-background grid has one red(2) source on exactly "
    "one non-corner edge. Its edge determines inward gravity. There are 2..5 "
    "cyan(8) wall lines perpendicular to gravity, each at least two cells from "
    "the flow-axis ends and separated by at least one open row/column. Every "
    "wall spans the cross-axis except for 1..3 holes. Ordinary draws use at "
    "least three walls and include both shifted and aligned holes. The output "
    "is the directed waterfall: move inward, spread sideways in both directions "
    "when blocked, fall through every reachable hole, and recolor every visited "
    "empty cell to 2."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "rectangular 10..18 ARC grid with palette exactly {0,2,8}",
    "exactly one color-2 source on one non-corner edge",
    "the source's inward neighbor is open and the first wall blocks its column/row",
    "2..5 full-span color-8 walls perpendicular to gravity",
    "each wall has exactly 1..3 holes and wall positions are at least two apart",
    "ordinary draws contain both shifted-hole and aligned-hole transitions",
]

# These are deliberately malformed probes used by generator_defect_lint.  They
# are not lawful training axes and therefore are not advertised in AXES.
DEGENERATE_TEXTURES = ("no_walls", "interior_source", "walled_source")
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "difficulty-biased", "valid": "10..18"},
    "n_walls": {
        "type": "int",
        "default": "3..5 difficulty-biased; 2 allowed explicitly",
        "valid": "2..5",
    },
    "edge": {
        "type": "enum",
        "default": "keyed random",
        "valid": "top|bottom|left|right",
    },
}

_EDGES = ("top", "bottom", "left", "right")


def _valid_color(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _source_and_edge(grid: list[list[int]]) -> tuple[tuple[int, int], str] | None:
    h, w = len(grid), len(grid[0])
    sources = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(sources) != 1:
        return None
    sr, sc = sources[0]
    memberships = [
        name
        for name, test in (
            ("top", sr == 0),
            ("bottom", sr == h - 1),
            ("left", sc == 0),
            ("right", sc == w - 1),
        )
        if test
    ]
    if len(memberships) != 1:
        return None
    return (sr, sc), memberships[0]


def _wall_profile(
    grid: list[list[int]], edge: str
) -> tuple[list[int], list[set[int]]]:
    """Return wall positions in gravity order and their cross-axis holes."""
    h, w = len(grid), len(grid[0])
    vertical = edge in ("top", "bottom")
    if vertical:
        positions = [r for r in range(h) if any(grid[r][c] == 8 for c in range(w))]
        hole_map = {r: {c for c in range(w) if grid[r][c] != 8} for r in positions}
        positions.sort(reverse=edge == "bottom")
    else:
        positions = [c for c in range(w) if any(grid[r][c] == 8 for r in range(h))]
        hole_map = {c: {r for r in range(h) if grid[r][c] != 8} for c in positions}
        positions.sort(reverse=edge == "right")
    return positions, [hole_map[position] for position in positions]


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Expose exact axis values recoverable from a returned input grid."""
    h = len(grid)
    w = len(grid[0]) if grid else 0
    source = _source_and_edge(grid) if grid and w else None
    edge = source[1] if source else "invalid"
    n_walls = len(_wall_profile(grid, edge)[0]) if source else 0
    return {"grid_h": h, "grid_w": w, "n_walls": n_walls, "edge": edge}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar, not merely palette and source count."""
    del difficulty
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["every row must be a nonempty list"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(not _valid_color(value) for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    h = len(grid)
    errors: list[str] = []
    if not (10 <= h <= 18 and 10 <= w <= 18):
        errors.append(f"expected dimensions in 10..18; got {h}x{w}")

    palette = {value for row in grid for value in row}
    if palette != {0, 2, 8}:
        errors.append(f"expected palette exactly [0, 2, 8]; got {sorted(palette)}")

    source = _source_and_edge(grid)
    if source is None:
        count = sum(value == 2 for row in grid for value in row)
        errors.append(
            "expected exactly one source on exactly one non-corner edge; "
            f"found {count} source cells"
        )
        return errors
    (sr, sc), edge = source

    dr, dc = {
        "top": (1, 0),
        "bottom": (-1, 0),
        "left": (0, 1),
        "right": (0, -1),
    }[edge]
    nr, nc = sr + dr, sc + dc
    if grid[nr][nc] == 8:
        errors.append("the source's inward neighbour must be open")

    positions, holes = _wall_profile(grid, edge)
    if not 2 <= len(positions) <= 5:
        errors.append(f"expected 2..5 wall lines; got {len(positions)}")

    vertical = edge in ("top", "bottom")
    flow_len = h if vertical else w
    cross_len = w if vertical else h
    numeric_positions = sorted(positions)
    if any(position < 2 or position > flow_len - 3 for position in numeric_positions):
        errors.append("wall lines must be at least two cells from both flow-axis ends")
    if any(right - left < 2 for left, right in zip(numeric_positions, numeric_positions[1:])):
        errors.append("adjacent wall lines are not allowed")

    for index, (position, gap_cells) in enumerate(zip(positions, holes)):
        wall_count = sum(
            grid[position][c] == 8 for c in range(w)
        ) if vertical else sum(grid[r][position] == 8 for r in range(h))
        if wall_count != cross_len - len(gap_cells):
            errors.append(f"wall {index} contains inconsistent non-wall cells")
        if not 1 <= len(gap_cells) <= 3:
            errors.append(
                f"wall {index} must have 1..3 holes; got {len(gap_cells)}"
            )
        if any(cell in (0, cross_len - 1) for cell in gap_cells):
            errors.append(f"wall {index} holes must be interior to the cross-axis")

    source_cross = sc if vertical else sr
    if holes and source_cross in holes[0]:
        errors.append("the first wall must block the source's straight path")

    # Every 8 must belong to one of the detected full-span wall lines.  The
    # per-line density checks above make a perpendicular or fragmentary wall
    # fail rather than being miscounted as a valid extra line.
    if vertical:
        off_line = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8 and r not in positions]
    else:
        off_line = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8 and c not in positions]
    if off_line:
        errors.append(f"found {len(off_line)} wall cells outside perpendicular wall lines")

    overrides = meta.get("overrides", {}) if isinstance(meta, dict) else {}
    observed = observe_overrides(grid)
    if isinstance(overrides, dict):
        for axis, requested in overrides.items():
            if axis in observed and observed[axis] != requested:
                errors.append(
                    f"override {axis} requested {requested!r}, observed {observed[axis]!r}"
                )
    return errors



def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests; Racket remains output authority."""
    source = _source_and_edge(grid)
    if source is None:
        raise ValueError("rule_mirror requires one non-corner edge source")
    (sr, sc), edge = source
    h, w = len(grid), len(grid[0])
    dr, dc = {
        "top": (1, 0),
        "bottom": (-1, 0),
        "left": (0, 1),
        "right": (0, -1),
    }[edge]
    pr, pc = ((0, 1) if dr else (1, 0))
    water: set[tuple[int, int]] = {(sr, sc)}

    def in_bounds(row: int, col: int) -> bool:
        return 0 <= row < h and 0 <= col < w

    def wall(row: int, col: int) -> bool:
        return in_bounds(row, col) and grid[row][col] == 8

    def flow(row: int, col: int) -> None:
        if not in_bounds(row, col) or wall(row, col) or (row, col) in water:
            return
        water.add((row, col))
        next_row, next_col = row + dr, col + dc
        if not in_bounds(next_row, next_col):
            return
        if not wall(next_row, next_col):
            flow(next_row, next_col)
        else:
            side(row, col, pr, pc)
            side(row, col, -pr, -pc)

    def side(row: int, col: int, step_row: int, step_col: int) -> None:
        next_row, next_col = row + step_row, col + step_col
        if (
            not in_bounds(next_row, next_col)
            or wall(next_row, next_col)
            or (next_row, next_col) in water
        ):
            return
        water.add((next_row, next_col))
        below_row, below_col = next_row + dr, next_col + dc
        if not in_bounds(below_row, below_col):
            return
        if not wall(below_row, below_col):
            flow(below_row, below_col)
        else:
            side(next_row, next_col, step_row, step_col)

    next_row, next_col = sr + dr, sc + dc
    if in_bounds(next_row, next_col):
        if wall(next_row, next_col):
            side(sr, sc, pr, pc)
            side(sr, sc, -pr, -pc)
        else:
            flow(next_row, next_col)

    output = [row[:] for row in grid]
    for row, col in water:
        output[row][col] = 2
    return output

def _max_walls(flow_len: int) -> int:
    # Legal positions are 2..flow_len-3 inclusive and differ by at least two.
    return min(5, (flow_len - 3) // 2)


def _requested_int(overrides: dict[str, Any], key: str, lo: int, hi: int) -> int | None:
    raw = overrides.get(key)
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError(f"{key} override must be an integer, not bool")
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} override must be an integer") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{key} override {value} outside [{lo}, {hi}]")
    return value


def _wall_positions(flow_len: int, n_walls: int, rng) -> list[int]:
    candidates = [
        combo
        for combo in combinations(range(2, flow_len - 2), n_walls)
        if all(b - a >= 2 for a, b in zip(combo, combo[1:]))
    ]
    if not candidates:
        raise ValueError(
            f"flow length {flow_len} cannot realize {n_walls} walls with required spacing"
        )
    return list(rng.choice(candidates))


def _gap_sets(cross_len: int, n_walls: int, sample_index: int, rng) -> list[set[int]]:
    interior = list(range(1, cross_len - 1))
    counts = [1 + ((sample_index + index) % 3) for index in range(n_walls)]
    # Exactly one aligned transition is enough to rebut an always-zig shortcut.
    # Choose it only after a wall with >=2 holes, so at least one other incoming
    # stream still hits the aligned wall and exposes its sideways-spread branch.
    aligned_index = next(
        (index for index in range(1, n_walls) if counts[index - 1] >= 2),
        1,
    )

    gaps: list[set[int]] = []
    for index, count in enumerate(counts):
        previous = gaps[-1] if gaps else set()
        if index == 0:
            chosen = set(rng.sample(interior, count))
        elif index == aligned_index:
            aligned = rng.choice(sorted(previous))
            pool = [cell for cell in interior if cell != aligned]
            chosen = {aligned, *rng.sample(pool, count - 1)}
        else:
            # Shifted-hole transition: no direct fall-through from prior holes.
            pool = [cell for cell in interior if cell not in previous]
            chosen = set(rng.sample(pool, count))
        gaps.append(chosen)
    return gaps


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard") and not (
        isinstance(difficulty, (int, float))
        and not isinstance(difficulty, bool)
        and 0.0 <= float(difficulty) <= 1.0
    ):
        raise ValueError("difficulty must be easy, medium, hard, None, or a number in [0,1]")

    unknown = sorted(set(overrides) - set(AXES) - {"texture"})
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        return _draw_from_degenerate(texture)

    # Parse explicit numeric values first so mixed feasibility can be decided
    # before any keyed draw is silently narrowed or replaced.
    requested_h = _requested_int(overrides, "grid_h", 10, 18)
    requested_w = _requested_int(overrides, "grid_w", 10, 18)
    requested_walls = _requested_int(overrides, "n_walls", 2, 5)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    edge = ctx.draw_choice("edge", _EDGES)
    vertical = edge in ("top", "bottom")
    flow_key, cross_key = ("grid_h", "grid_w") if vertical else ("grid_w", "grid_h")
    requested_flow = requested_h if vertical else requested_w

    # If the caller pins the flow length, choose only a feasible wall count
    # unless they pin an incompatible count too, in which case reject loudly.
    if requested_flow is not None:
        flow_len = ctx.draw_int(flow_key, 10, 18)
        max_walls = _max_walls(flow_len)
        if requested_walls is not None:
            n_walls = ctx.draw_int("n_walls", 2, 5)
            if n_walls > max_walls:
                raise ValueError(
                    f"{flow_key}={flow_len} cannot realize n_walls={n_walls}; "
                    f"maximum is {max_walls}"
                )
        else:
            n_walls = ctx.draw_int_diff("n_walls", 3, max_walls)
    else:
        # Ordinary draws use >=3 walls so every grid contains both shifted and
        # aligned hole transitions. Explicit n_walls=2 remains lawful.
        if requested_walls is not None:
            n_walls = ctx.draw_int("n_walls", 2, 5)
        else:
            n_walls = ctx.draw_int_diff("n_walls", 3, 5)
        min_flow_len = max(10, 2 * n_walls + 3)
        flow_len = ctx.draw_int_diff(flow_key, min_flow_len, 18)

    cross_len = ctx.draw_int_diff(cross_key, 10, 18)
    h, w = (flow_len, cross_len) if vertical else (cross_len, flow_len)

    rng = ctx.draw_rng("layout")
    positions = _wall_positions(flow_len, n_walls, rng)
    ordered_positions = sorted(positions, reverse=edge in ("bottom", "right"))
    gap_sets = _gap_sets(cross_len, n_walls, sample_index, rng)

    grid = full_grid(h, w, 0)
    for position, gaps in zip(ordered_positions, gap_sets):
        for cross in range(cross_len):
            if cross in gaps:
                continue
            if vertical:
                grid[position][cross] = 8
            else:
                grid[cross][position] = 8

    source_pool = [cell for cell in range(1, cross_len - 1) if cell not in gap_sets[0]]
    source_cross = rng.choice(source_pool)
    if edge == "top":
        grid[0][source_cross] = 2
    elif edge == "bottom":
        grid[h - 1][source_cross] = 2
    elif edge == "left":
        grid[source_cross][0] = 2
    else:
        grid[source_cross][w - 1] = 2

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failure: {errors}")
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(11, 11, 0)
    if name == "no_walls":
        grid[0][3] = 2
        return grid
    for col in range(11):
        if col != 5:
            grid[4][col] = 8
    if name == "interior_source":
        grid[6][5] = 2
        return grid
    if name == "walled_source":
        grid[0][2] = 2
        for col in range(11):
            grid[1][col] = 8
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")
