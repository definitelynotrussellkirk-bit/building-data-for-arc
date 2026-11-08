"""Input generator for task 99d5bc858270.

A unique yellow cell on the border is the light.  Every other nonzero cell is
an interior shadow caster.  The selected Racket program remains the sole label
authority; the Python code below only constructs inputs, validates the input
domain, and defines deliberately wrong competitors for curriculum checks.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99d5bc858270"
VERSION = "3.1.1"
TASK_ID = "99d5bc858270"
RULE_HASH = "e48cc46570d0"

SUMMARY = (
    "A 0-background grid contains exactly one yellow (4) border light and "
    "one or more non-yellow interior caster cells. The light may occupy any "
    "edge or corner; at corners, the selected rule gives left/right borders "
    "priority. The Racket authority casts a yellow ray from every caster cell "
    "away from the light and clears the original light. Generated scenes "
    "include separated collinear casters so a canonical-fitting "
    "farthest-caster-only shortcut is visibly wrong."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.05

INVARIANTS = [
    "background is color 0",
    "exactly one color-4 cell exists and it lies on the border",
    "all other nonzero cells are non-4 interior shadow casters",
    "corner lights are lawful and use left/right-border priority",
    "every generated input contains separated casters on one ray projection",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted with canonical 6-row anchor",
        "valid": "6..15",
        "doc": "Grid height; every exact value is legal in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with canonical 9-column anchor",
        "valid": "7..16",
        "doc": "Grid width; every exact value is legal in every band.",
    },
    "light_position": {
        "type": "int",
        "default": "uniform 0..7",
        "valid": "0..7",
        "doc": (
            "0 top, 1 right, 2 bottom, 3 left, 4 top-left, "
            "5 top-right, 6 bottom-right, 7 bottom-left."
        ),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_HEIGHTS = tuple(range(6, 16))
_WIDTHS = tuple(range(7, 17))
_LIGHT_POSITIONS = tuple(range(8))
_CASTER_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)


def _weighted_axis_options(
    domain: Sequence[int],
    *,
    canonical_anchor: int,
    preferred: Sequence[int],
) -> tuple[int, ...]:
    """Keep full override support while weighting defaults by curriculum band."""
    return tuple(domain) + (canonical_anchor,) * 36 + tuple(preferred) * 4


def _preferred_dimensions(difficulty) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if difficulty == "easy":
        return (6, 7, 8), (7, 8, 9, 10)
    if difficulty == "hard":
        return (11, 12, 13, 14, 15), (12, 13, 14, 15, 16)
    return (8, 9, 10, 11), (9, 10, 11, 12, 13)


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    bounds = {
        "grid_h": (6, 15),
        "grid_w": (7, 16),
        "light_position": (0, 7),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} override must be an exact int, got {value!r}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _place_light(grid: list[list[int]], position: int, rng) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    if position == 0:
        cell = (0, rng.randint(1, w - 2))
    elif position == 1:
        cell = (rng.randint(1, h - 2), w - 1)
    elif position == 2:
        cell = (h - 1, rng.randint(1, w - 2))
    elif position == 3:
        cell = (rng.randint(1, h - 2), 0)
    elif position == 4:
        cell = (0, 0)
    elif position == 5:
        cell = (0, w - 1)
    elif position == 6:
        cell = (h - 1, w - 1)
    else:
        cell = (h - 1, 0)
    grid[cell[0]][cell[1]] = 4
    return cell


def _direction_from_light(light: tuple[int, int], h: int, w: int) -> tuple[int, int]:
    """Selected-rule edge priority: left, right, top, then bottom."""
    r, c = light
    if c == 0:
        return 0, 1
    if c == w - 1:
        return 0, -1
    if r == 0:
        return 1, 0
    return -1, 0


def _witness_motif(
    h: int,
    w: int,
    direction: tuple[int, int],
    rng,
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Build varied collinear casters while preserving at least one real gap.

    The three styles deliberately avoid making one fixed U template synonymous
    with the task: an open pair, two parallel dominoes, or a bridge around the
    protected ray gap.  Separation also varies with available interior space.
    """
    _dr, dc = direction
    style = rng.choice(("open_pair", "parallel_dominoes", "bridge"))
    if dc:
        span = rng.randint(2, min(5, w - 3))
        top = rng.randint(1, h - 3)
        left = rng.randint(1, w - 2 - span)
        endpoint_row = top + rng.choice((0, 1))
        companion_row = top + (1 if endpoint_row == top else 0)
        cells = {(endpoint_row, left), (endpoint_row, left + span)}
        if style == "parallel_dominoes":
            cells.update({(companion_row, left), (companion_row, left + span)})
        elif style == "bridge":
            cells.update((companion_row, c) for c in range(left, left + span + 1))
        protected = {
            (endpoint_row, c) for c in range(left + 1, left + span)
        }
    else:
        span = rng.randint(2, min(5, h - 3))
        top = rng.randint(1, h - 2 - span)
        left = rng.randint(1, w - 3)
        endpoint_col = left + rng.choice((0, 1))
        companion_col = left + (1 if endpoint_col == left else 0)
        cells = {(top, endpoint_col), (top + span, endpoint_col)}
        if style == "parallel_dominoes":
            cells.update({(top, companion_col), (top + span, companion_col)})
        elif style == "bridge":
            cells.update((r, companion_col) for r in range(top, top + span + 1))
        protected = {
            (r, endpoint_col) for r in range(top + 1, top + span)
        }
    return cells, protected


def _extra_count(difficulty, rng) -> int:
    if difficulty == "easy":
        return rng.randint(0, 2)
    if difficulty == "hard":
        return rng.randint(3, 7)
    return rng.randint(1, 5)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    preferred_h, preferred_w = _preferred_dimensions(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice(
        "grid_h",
        _weighted_axis_options(_HEIGHTS, canonical_anchor=6, preferred=preferred_h),
    )
    w = ctx.draw_choice(
        "grid_w",
        _weighted_axis_options(_WIDTHS, canonical_anchor=9, preferred=preferred_w),
    )
    position = ctx.draw_choice("light_position", _LIGHT_POSITIONS)

    grid = full_grid(h, w, 0)
    light = _place_light(grid, position, ctx.draw_rng("light_offset"))
    direction = _direction_from_light(light, h, w)

    motif, protected_gaps = _witness_motif(
        h, w, direction, ctx.draw_rng("shared_projection_motif")
    )
    palette_rng = ctx.draw_rng("caster_palette")
    primary = palette_rng.choice(_CASTER_COLORS)
    two_colors = bool(palette_rng.randrange(2))
    remaining = tuple(color for color in _CASTER_COLORS if color != primary)
    secondary = palette_rng.choice(remaining) if two_colors else None
    for r, c in motif:
        grid[r][c] = primary

    decoration_rng = ctx.draw_rng("decorations")
    count = _extra_count(difficulty, decoration_rng)
    if secondary is not None:
        count = max(1, count)
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0 and (r, c) not in protected_gaps
    ]
    decoration_rng.shuffle(candidates)
    for index, (r, c) in enumerate(candidates[:count]):
        if secondary is not None and index == 0:
            color = secondary
        elif secondary is not None:
            color = decoration_rng.choice((primary, secondary))
        else:
            color = primary
        grid[r][c] = color

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise ValueError("constructed invalid shadow scene: " + "; ".join(findings))
    return grid


def _shape_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], 0, 0
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a sequence"], 0, 0
    widths = [len(row) for row in grid]
    if not widths or widths[0] == 0 or any(width != widths[0] for width in widths):
        return ["grid must be nonempty and rectangular"], 0, 0
    return [], len(grid), widths[0]


def _border(r: int, c: int, h: int, w: int) -> bool:
    return r in (0, h - 1) or c in (0, w - 1)


def _find_light(grid) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    lights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4 and _border(r, c, h, w)
    ]
    if len(lights) != 1:
        raise ValueError(f"expected one border light, found {len(lights)}")
    return lights[0]


def _caster_cells(grid, light: tuple[int, int]) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != light
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors, h, w = _shape_errors(grid)
    if errors:
        return errors
    if h < 3 or w < 3:
        errors.append(f"grid must be at least 3x3, got {h}x{w}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({r},{c}) must be an exact int color in 0..9, got {value!r}"
                )
                if len(errors) >= 8:
                    return errors

    if errors:
        return errors

    all_lights = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    if len(all_lights) != 1:
        errors.append(f"expected exactly one color-4 light, found {len(all_lights)}")
        return errors
    light = all_lights[0]
    if not _border(light[0], light[1], h, w):
        errors.append("the unique color-4 light must lie on the border")

    casters = _caster_cells(grid, light)
    if not casters:
        errors.append("expected at least one non-light caster cell")
    for r, c, _ in casters:
        if _border(r, c, h, w):
            errors.append(f"caster at ({r},{c}) must be strictly interior")
            if len(errors) >= 8:
                break
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    if (h, w) != (6, 9):
        errors.append(f"canonical dimensions are 6x9, got {h}x{w}")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (3, 4):
        errors.append(f"canonical palette size is 3 or 4, got {palette_size}")
    return errors


def _position_code(light: tuple[int, int], h: int, w: int) -> int:
    r, c = light
    if (r, c) == (0, 0):
        return 4
    if (r, c) == (0, w - 1):
        return 5
    if (r, c) == (h - 1, w - 1):
        return 6
    if (r, c) == (h - 1, 0):
        return 7
    if r == 0:
        return 0
    if c == w - 1:
        return 1
    if r == h - 1:
        return 2
    if c == 0:
        return 3
    raise ValueError("light is not on the border")


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    return {
        "grid_h": h,
        "grid_w": w,
        "light_position": _position_code(_find_light(grid), h, w),
    }


def _shared_projection_gap(grid) -> bool:
    if self_check(grid):
        return False
    h, w = len(grid), len(grid[0])
    light = _find_light(grid)
    dr, dc = _direction_from_light(light, h, w)
    groups: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, c, _ in _caster_cells(grid, light):
        groups[r if dc else c].append((r, c))
    for cells in groups.values():
        cells.sort(key=(lambda cell: cell[1]) if dc else (lambda cell: cell[0]))
        for first, second in zip(cells, cells[1:]):
            a = first[1] if dc else first[0]
            b = second[1] if dc else second[0]
            if b - a <= 1:
                continue
            for coordinate in range(a + 1, b):
                r, c = (first[0], coordinate) if dc else (coordinate, first[1])
                if grid[r][c] == 0:
                    return True
    return False


def _farthest_caster_per_projection(grid) -> list[list[int]]:
    """Wrong rule: keep only the farthest caster on each projected ray."""
    if self_check(grid):
        raise ValueError("rival requires a lawful task input")
    h, w = len(grid), len(grid[0])
    light = _find_light(grid)
    dr, dc = _direction_from_light(light, h, w)
    casters = _caster_cells(grid, light)
    groups: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for cell in casters:
        r, c, _ = cell
        groups[r if dc else c].append(cell)

    if dr > 0:
        selected = [max(group, key=lambda cell: cell[0]) for group in groups.values()]
    elif dr < 0:
        selected = [min(group, key=lambda cell: cell[0]) for group in groups.values()]
    elif dc > 0:
        selected = [max(group, key=lambda cell: cell[1]) for group in groups.values()]
    else:
        selected = [min(group, key=lambda cell: cell[1]) for group in groups.values()]

    out = full_grid(h, w, 0)
    for r, c, _ in selected:
        r += dr
        c += dc
        while 0 <= r < h and 0 <= c < w:
            out[r][c] = 4
            r += dr
            c += dc
    for r, c, value in casters:
        out[r][c] = value
    return out


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "shared_projection_gap": _shared_projection_gap,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "farthest_caster_per_projection": _farthest_caster_per_projection,
}
WITNESS_RIVALS = {
    "shared_projection_gap": ["farthest_caster_per_projection"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is adequate only when its demonstrations refute each rival."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    errors: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} is missing input/output")
            continue
        findings = self_check(pair["input"])
        if findings:
            errors.append(f"pair {index} input is outside the task domain: {findings[0]}")
    if errors:
        return errors

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                errors.append(f"demonstrations do not refute rival: {name}")
        except Exception as exc:
            errors.append(f"rival {name} raised {type(exc).__name__}: {exc}")
    return errors
