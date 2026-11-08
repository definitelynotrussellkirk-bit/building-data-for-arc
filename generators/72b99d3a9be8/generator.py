"""Generator for 72b99d3a9be8 (canonical source task 7e2bad24).

A diagonal color-1 seed extends in both directions.  Color-2 line segments are
reflecting walls: a horizontal wall flips the row direction and a vertical wall
flips the column direction.  Color 3 is a pass-through distractor.

Version 4 repairs the old sampler's horizontal-only shortcut.  Ordinary draws
now construct a real selected horizontal or vertical color-2 wall on the seed's
backward ray, plus an oppositely oriented color-3 pass-through segment.  The
rule-domain self-check accepts the canonical border-touching/no-wall examples;
generator-specific branch coverage is measured by trace_rule instead.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "72b99d3a9be8"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "72b99d3a9be8"

SUMMARY = (
    "A 12..22 square or rectangular zero-background grid contains a diagonal "
    "color-1 seed. Extend the seed in both directions. Color-2 line walls "
    "reflect the path according to their input-measured orientation; color-3 "
    "segments are pass-through distractors. Ordinary draws exercise both true "
    "horizontal and true vertical reflection branches."
)

INVARIANTS = [
    "background is color 0",
    "at least two color-1 cells contain an adjacent diagonal pair",
    "color-2 line segments reflect; color 3 does not",
    "all outputs stay within the original 1..30 ARC canvas",
]

DIAGONALS = ("down_right", "down_left")
WALL_ORIENTATIONS = ("horizontal", "vertical")
DEGENERATE_TEXTURES = ("no_pair", "single_cell", "full_grid")
HELPFUL_TEXTURES = DIAGONALS

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 12..22", "valid": "12..22"},
    "grid_w": {"type": "int", "default": "difficulty-aware 12..22", "valid": "12..22"},
    "diagonal": {"type": "str", "default": "rng", "valid": "|".join(DIAGONALS)},
    "wall_orientation": {"type": "str", "default": "rng", "valid": "|".join(WALL_ORIENTATIONS)},
    "n_bars": {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "texture": {"type": "str", "default": "alias for diagonal", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    for name, low, high in (("grid_h", 12, 22), ("grid_w", 12, 22), ("n_bars", 2, 5)):
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if not low <= value <= high:
            raise ValueError(f"override {name!r}={value} outside [{low}, {high}]")
    choices = {
        "diagonal": DIAGONALS,
        "wall_orientation": WALL_ORIENTATIONS,
        "texture": HELPFUL_TEXTURES + DEGENERATE_TEXTURES,
    }
    for name, options in choices.items():
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"override {name!r}={value!r} not in {options}")


def _segment(center: tuple[int, int], orientation: str, half: int = 1) -> list[tuple[int, int]]:
    r, c = center
    if orientation == "horizontal":
        return [(r, c + delta) for delta in range(-half, half + 1)]
    if orientation == "vertical":
        return [(r + delta, c) for delta in range(-half, half + 1)]
    raise ValueError(orientation)


def _in_bounds(cells: list[tuple[int, int]], h: int, w: int) -> bool:
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _paint_if_empty(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> bool:
    if not _in_bounds(cells, len(grid), len(grid[0])):
        return False
    if any(grid[r][c] != 0 for r, c in cells):
        return False
    for r, c in cells:
        grid[r][c] = color
    return True


def _marker_geometry(h: int, w: int, diagonal: str, length: int, rng) -> list[tuple[int, int]]:
    # Maintain at least five backward cells for decoy and wall, and at least two
    # forward cells.  The 12x12 minimum remains constructive for length 2..3.
    for _ in range(256):
        mr_low = 6
        mr_high = h - length - 2
        if mr_high < mr_low:
            break
        mr = rng.randint(mr_low, mr_high)
        if diagonal == "down_right":
            mc_low, mc_high = 6, w - length - 2
            if mc_high < mc_low:
                continue
            mc = rng.randint(mc_low, mc_high)
            marker = [(mr + i, mc + i) for i in range(length)]
        else:
            mc_low, mc_high = length + 1, w - 7
            if mc_high < mc_low:
                continue
            mc = rng.randint(mc_low, mc_high)
            marker = [(mr + i, mc - i) for i in range(length)]
        return marker
    # The supported minimum always has this centered fallback.
    mr = 6
    if diagonal == "down_right":
        mc = 6
        return [(mr + i, mc + i) for i in range(length)]
    mc = w - 7
    return [(mr + i, mc - i) for i in range(length)]


def _extra_candidates(h: int, w: int) -> list[tuple[list[tuple[int, int]], str]]:
    return [
        ([(1, c) for c in range(1, 4)], "horizontal"),
        ([(1, c) for c in range(w - 4, w - 1)], "horizontal"),
        ([(h - 2, c) for c in range(1, 4)], "horizontal"),
        ([(h - 2, c) for c in range(w - 4, w - 1)], "horizontal"),
        ([(r, 1) for r in range(2, 5)], "vertical"),
        ([(r, w - 2) for r in range(2, 5)], "vertical"),
        ([(r, 1) for r in range(h - 5, h - 2)], "vertical"),
        ([(r, w - 2) for r in range(h - 5, h - 2)], "vertical"),
    ]


def _construct_scene(h: int, w: int, diagonal: str, wall_orientation: str,
                     n_bars: int, rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    length = rng.randint(2, 3)
    marker = _marker_geometry(h, w, diagonal, length, rng)
    for r, c in marker:
        grid[r][c] = 1

    start_r, start_c = marker[0]
    backward_dc = -1 if diagonal == "down_right" else 1
    decoy_center = (start_r - 2, start_c + 2 * backward_dc)
    wall_center = (start_r - 4, start_c + 4 * backward_dc)
    decoy_orientation = "vertical" if wall_orientation == "horizontal" else "horizontal"
    if not _paint_if_empty(grid, _segment(decoy_center, decoy_orientation), 3):
        raise RuntimeError("could not place pass-through decoy")
    if not _paint_if_empty(grid, _segment(wall_center, wall_orientation), 2):
        raise RuntimeError("could not place reflecting wall")

    candidates = _extra_candidates(h, w)
    rng.shuffle(candidates)
    extras = n_bars - 2
    placed = 0
    for cells, _ in candidates:
        if placed >= extras:
            break
        # Extra bars are pass-through distractors.  Keeping color 2 unique to
        # the intended reflector prevents an earlier accidental bounce from
        # masking the sampled wall-orientation branch.
        if _paint_if_empty(grid, cells, 3):
            placed += 1
    if placed != extras:
        raise RuntimeError("could not place requested extra bars")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    diagonal = (texture if texture in DIAGONALS else None) or ctx.draw_choice("diagonal", DIAGONALS)
    h = ctx.draw_int_diff("grid_h", 12, 22)
    w = ctx.draw_int_diff("grid_w", 12, 22)
    wall_orientation = ctx.draw_choice("wall_orientation", WALL_ORIENTATIONS)
    n_bars = ctx.draw_int_strict("n_bars", 2, 5)
    grid = _construct_scene(h, w, diagonal, wall_orientation, n_bars, rng)
    domain_errors = self_check(grid)
    if domain_errors:
        raise RuntimeError("internal rule-domain error: " + "; ".join(domain_errors))
    trace = trace_rule(grid, reflector_color=2)
    if not trace["bounce_events"] or trace["bounce_events"][0]["orientation"] != wall_orientation:
        raise RuntimeError("constructed wall branch was not exercised")
    if not {2, 3} <= trace["crossed_colors"]:
        raise RuntimeError("constructed beam did not cross both wall and decoy colors")
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(10, 10, 0)
    if name == "no_pair":
        return grid
    if name == "single_cell":
        grid[5][5] = 1
        return grid
    if name == "full_grid":
        return full_grid(10, 10, 1)
    raise ValueError(name)


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return None, ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    values = []
    for r, row in enumerate(grid):
        if type(row) is not list or len(row) != width:
            return None, ["grid must be rectangular"]
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            return None, [f"row {r} contains a non-ARC cell"]
        values.append(list(row))
    if len(values) > 30 or width > 30:
        return None, ["grid exceeds ARC max size"]
    return values, []


def _seed_direction(ones: list[tuple[int, int]]) -> tuple[int, int] | None:
    if not ones:
        return None
    p1 = ones[0]
    for p2 in ones:
        if p2 != p1 and abs(p2[0] - p1[0]) == 1 and abs(p2[1] - p1[1]) == 1:
            return p2[0] - p1[0], p2[1] - p1[1]
    return None


def trace_rule(grid: Any, *, reflector_color: int = 2) -> dict[str, Any]:
    if type(reflector_color) is not int or reflector_color not in range(1, 10):
        raise ValueError("reflector_color must be an ARC foreground integer")
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    h, w = len(values), len(values[0])
    ones = [(r, c) for r, row in enumerate(values) for c, cell in enumerate(row) if cell == 1]
    direction = _seed_direction(ones) or (1, 1)
    output = deepcopy(values)
    events: list[dict[str, Any]] = []
    crossed_colors: set[int] = set()

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < h and 0 <= c < w

    def wall_orientation(r: int, c: int) -> str:
        up = in_bounds(r - 1, c) and values[r - 1][c] == reflector_color
        down = in_bounds(r + 1, c) and values[r + 1][c] == reflector_color
        return "vertical" if up or down else "horizontal"

    def walk(start: tuple[int, int], dr: int, dc: int, phase: str) -> None:
        nonlocal output
        r, c = start
        fuel = h * w * 4
        while fuel > 0:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                return
            cell = values[nr][nc]
            if cell != 0:
                crossed_colors.add(cell)
            if cell == reflector_color:
                orientation = wall_orientation(nr, nc)
                incoming = (dr, dc)
                if orientation == "horizontal":
                    dr = -dr
                else:
                    dc = -dc
                events.append({
                    "phase": phase,
                    "position": [nr, nc],
                    "orientation": orientation,
                    "incoming": list(incoming),
                    "outgoing": [dr, dc],
                    "reflector_color": reflector_color,
                })
                fuel -= 1
                continue
            output[nr][nc] = 1
            r, c = nr, nc
            fuel -= 1

    sorted_by_row = sorted(ones, key=lambda p: p[0])
    if not sorted_by_row:
        raise ValueError("grid contains no color-1 seed")
    start_backward = sorted_by_row[0]
    start_forward = sorted_by_row[-1]
    walk(start_forward, direction[0], direction[1], "forward")
    walk(start_backward, -direction[0], -direction[1], "backward")
    return {
        "output": output,
        "direction": list(direction),
        "bounce_events": events,
        "crossed_colors": crossed_colors,
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    return trace_rule(grid, reflector_color=2)["output"]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        return errors
    ones = [(r, c) for r, row in enumerate(values) for c, cell in enumerate(row) if cell == 1]
    if len(ones) < 2:
        errors.append("fewer than two color-1 seed cells")
    elif _seed_direction(ones) is None:
        errors.append("no adjacent diagonal color-1 pair")
    return errors
