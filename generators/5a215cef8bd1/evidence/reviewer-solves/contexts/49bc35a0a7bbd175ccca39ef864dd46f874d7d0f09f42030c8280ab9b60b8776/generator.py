"""Generator for “Make a Transform Panel from a Single Template”.

A lawful input contains one connected color-2 template plus four singleton
control markers arranged as the corners of an abstract 2x2 code grid.  Ranking
the two marker rows and columns selects the output quadrants.  Control colors
map to transforms as follows: 1=identity, 3=rotate clockwise, 4=rotate 180,
6=flip left-right.  Each transformed template is recolored to 7 and the four
blocks are separated by one blank row and column.

The selected Racket authority allocates every output slot from the *original*
template height and width.  A non-square template therefore cannot safely hold
its 90-degree rotation: cells can cross a separator or clip at the canvas edge.
This generator makes that executable boundary explicit by using connected,
asymmetric square-bounding-box templates of size 2, 3, or 4.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations, permutations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a215cef8bd1"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "b5c73de1606e"

SUMMARY = (
    "One connected color-2 template with a square 2x2, 3x3, or 4x4 bounding "
    "box is spatially separated from a 2x2 rectangle of singleton controls. "
    "Control colors 1/3/4/6 mean identity/rotate-cw/rotate-180/flip-lr; their "
    "ranked row and column choose the output quadrant. The four transformed "
    "copies are recolored 7 and separated by one blank row and column. "
    "A twelve-profile schedule includes every canonical canvas profile and "
    "interleaves non-3x3 counterexamples so fixed-7x7 lessons are refuted."
)

INVARIANTS = [
    "exactly one 4-connected color-2 template object",
    "the template bounding box is square and size 2..4; generated shapes distinguish all four used transforms",
    "colors 1, 3, 4, and 6 each occur exactly once at all four corners of two rows x two columns",
    "the template and control rectangle are separated on at least one axis",
    "only colors 0, 1, 2, 3, 4, and 6 occur in the input",
]

LAYOUT_MODES = (
    "controls_above",
    "controls_below",
    "controls_left",
    "controls_right",
)
CONTROL_COLORS = (1, 3, 4, 6)
CONTROL_ORDERS = tuple(permutations(CONTROL_COLORS))
CANONICAL_DIMS = ((8, 10), (8, 12), (9, 11), (9, 12))

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchor or band draw",
        "valid": "8..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchor or band draw",
        "valid": "8..18",
    },
    "template_size": {
        "type": "int",
        "default": "schedule cycles 3,2,4",
        "valid": "2..4",
    },
    "control_order": {
        "type": "int",
        "default": "rng permutation index",
        "valid": "0..23",
    },
    "layout_mode": {
        "type": "str",
        "default": "rng",
        "valid": "controls_above|controls_below|controls_left|controls_right",
    },
}

# Every combination of the declared axes is constructible, including 8x8 with
# a size-4 template.  Declaring the empty set opts into strict rejection audit.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Residues 0/3/6/9 are exact canonical-profile anchors.  Every three
# consecutive residues contain template sizes 3, 2, and 4 respectively.
SCHEDULE_PROFILES = tuple(range(12))
_PROFILE_SIZES = (3, 2, 4) * 4
_PROFILE_ANCHORS = {
    0: (8, 10),
    3: (8, 12),
    6: (9, 11),
    9: (9, 12),
}
_BAND_DIM_RANGES = {
    None: (8, 18),
    "easy": (8, 12),
    "medium": (9, 15),
    "hard": (10, 18),
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Return the deterministic curriculum residue; seed/band do not alter it."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_overrides(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_DIM_RANGES:
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected None, easy, medium, or hard"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    integer_ranges = {
        "grid_h": (8, 18),
        "grid_w": (8, 18),
        "template_size": (2, 4),
        "control_order": (0, 23),
    }
    for name, (lo, hi) in integer_ranges.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}, got {value!r}")
    if "layout_mode" in overrides and overrides["layout_mode"] is not None:
        value = overrides["layout_mode"]
        if not isinstance(value, str) or value not in LAYOUT_MODES:
            raise ValueError(
                f"layout_mode must be one of {LAYOUT_MODES!r}, got {value!r}"
            )


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [min(remaining)]
    seen: set[tuple[int, int]] = set()
    while stack:
        r, c = stack.pop()
        if (r, c) in seen:
            continue
        seen.add((r, c))
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining and neighbor not in seen:
                stack.append(neighbor)
    return seen == remaining


def _rotate_cells_cw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    height = max(r for r, _ in normalized) + 1
    return _normalize((c, height - 1 - r) for r, c in normalized)


def _rotate_cells_180(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _rotate_cells_cw(_rotate_cells_cw(cells))


def _flip_cells_lr(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    normalized = _normalize(cells)
    width = max(c for _, c in normalized) + 1
    return _normalize((r, width - 1 - c) for r, c in normalized)


def _used_transform_signatures(
    cells: Iterable[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    normalized = _normalize(cells)
    return (
        normalized,
        _rotate_cells_cw(normalized),
        _rotate_cells_180(normalized),
        _flip_cells_lr(normalized),
    )


@lru_cache(maxsize=None)
def _shape_families(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Connected square-bbox shapes whose four used transforms are distinct."""
    if size not in (2, 3, 4):
        raise ValueError(f"unsupported template size: {size}")
    counts = {2: (3,), 3: (5, 6, 7, 8), 4: (7, 8, 9, 10)}[size]
    positions = tuple((r, c) for r in range(size) for c in range(size))
    families: list[tuple[tuple[int, int], ...]] = []
    for count in counts:
        for cells in combinations(positions, count):
            rows = {r for r, _ in cells}
            cols = {c for _, c in cells}
            if 0 not in rows or size - 1 not in rows or 0 not in cols or size - 1 not in cols:
                continue
            if not _connected(cells):
                continue
            normalized = _normalize(cells)
            if len(set(_used_transform_signatures(normalized))) != 4:
                continue
            families.append(normalized)
    if not families:
        raise AssertionError(f"no lawful template families for size {size}")
    return tuple(families)


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_dimension(ctx, overrides, label: str, profile: int, difficulty: str | None) -> int:
    axis = 0 if label == "grid_h" else 1
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, 8, 18)
    if profile in _PROFILE_ANCHORS:
        value = _PROFILE_ANCHORS[profile][axis]
        return ctx.draw_int(label, value, value)
    lo, hi = _BAND_DIM_RANGES[difficulty]
    return ctx.draw_int(label, lo, hi)


def _overlaps(a0: int, a1: int, b0: int, b1: int) -> bool:
    return max(a0, b0) <= min(a1, b1)


def _choose_pair(rng, first_max: int, second_max: int, predicate) -> tuple[int, int]:
    choices = [
        (first, second)
        for first in range(first_max + 1)
        for second in range(second_max + 1)
        if predicate(first, second)
    ]
    if not choices:
        raise ValueError("requested grid/layout has no legal placement")
    return rng.choice(choices)


def _place_regions(
    rng,
    h: int,
    w: int,
    size: int,
    layout_mode: str,
) -> tuple[int, int, int, int, int, int]:
    """Return template top/left, controls top/left, row-gap, col-gap."""
    if layout_mode in ("controls_above", "controls_below"):
        feasible_row_gaps = [gap for gap in (2, 3) if gap + 1 + 1 + size <= h]
        row_gap = rng.choice(feasible_row_gaps)
        col_gap = rng.choice([gap for gap in (2, 3) if gap + 1 <= w])
    else:
        row_gap = rng.choice([gap for gap in (2, 3) if gap + 1 <= h])
        feasible_col_gaps = [gap for gap in (2, 3) if gap + 1 + 1 + size <= w]
        col_gap = rng.choice(feasible_col_gaps)

    control_h, control_w = row_gap + 1, col_gap + 1
    if layout_mode == "controls_above":
        control_top, template_top = _choose_pair(
            rng, h - control_h, h - size,
            lambda ct, tt: ct + control_h < tt,
        )
        control_left, template_left = _choose_pair(
            rng, w - control_w, w - size,
            lambda cl, tl: _overlaps(cl, cl + control_w - 1, tl, tl + size - 1),
        )
    elif layout_mode == "controls_below":
        template_top, control_top = _choose_pair(
            rng, h - size, h - control_h,
            lambda tt, ct: tt + size < ct,
        )
        control_left, template_left = _choose_pair(
            rng, w - control_w, w - size,
            lambda cl, tl: _overlaps(cl, cl + control_w - 1, tl, tl + size - 1),
        )
    elif layout_mode == "controls_left":
        control_left, template_left = _choose_pair(
            rng, w - control_w, w - size,
            lambda cl, tl: cl + control_w < tl,
        )
        control_top, template_top = _choose_pair(
            rng, h - control_h, h - size,
            lambda ct, tt: _overlaps(ct, ct + control_h - 1, tt, tt + size - 1),
        )
    else:  # controls_right
        template_left, control_left = _choose_pair(
            rng, w - size, w - control_w,
            lambda tl, cl: tl + size < cl,
        )
        control_top, template_top = _choose_pair(
            rng, h - control_h, h - size,
            lambda ct, tt: _overlaps(ct, ct + control_h - 1, tt, tt + size - 1),
        )
    return template_top, template_left, control_top, control_left, row_gap, col_gap


def _paint(grid: list[list[int]], top: int, left: int,
           cells: Iterable[tuple[int, int]], color: int) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    grid_h = _draw_dimension(ctx, overrides, "grid_h", profile, difficulty)
    grid_w = _draw_dimension(ctx, overrides, "grid_w", profile, difficulty)
    template_size = _draw_profile_int(
        ctx, overrides, "template_size", _PROFILE_SIZES[profile], 2, 4
    )
    control_order = ctx.draw_int("control_order", 0, 23)
    layout_mode = ctx.draw_choice("layout_mode", LAYOUT_MODES)

    shape_rng = ctx.draw_rng("template_shape")
    layout_rng = ctx.draw_rng("spatial_layout")
    shape = shape_rng.choice(_shape_families(template_size))
    (template_top, template_left, control_top, control_left,
     row_gap, col_gap) = _place_regions(
        layout_rng, grid_h, grid_w, template_size, layout_mode
    )

    grid = full_grid(grid_h, grid_w, 0)
    _paint(grid, template_top, template_left, shape, 2)
    slots = (
        (control_top, control_left),
        (control_top, control_left + col_gap),
        (control_top + row_gap, control_left),
        (control_top + row_gap, control_left + col_gap),
    )
    for (row, col), color in zip(slots, CONTROL_ORDERS[control_order]):
        grid[row][col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "template_size": template_size,
            "control_order": control_order,
            "layout_mode": layout_mode,
        }},
    )
    if errors:
        raise AssertionError(f"internal invalid generation: {errors}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"]
    errors: list[str] = []
    if not 8 <= len(grid) <= 18 or not 8 <= width <= 18:
        errors.append(f"grid dimensions must be 8..18, got {len(grid)}x{width}")
    allowed = {0, 1, 2, 3, 4, 6}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or value not in allowed:
                errors.append(f"cell ({r},{c}) has invalid input color/value {value!r}")
                if len(errors) >= 8:
                    return errors
    return errors


def _color_components(grid: Any, color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        seen: set[tuple[int, int]] = set()
        while stack:
            r, c = stack.pop()
            if (r, c) in seen:
                continue
            seen.add((r, c))
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and neighbor not in seen:
                    stack.append(neighbor)
        components.append(seen)
        remaining -= seen
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyze(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return None, errors

    template_components = _color_components(grid, 2)
    if len(template_components) != 1:
        errors.append(
            f"expected exactly one connected color-2 object, found {len(template_components)}"
        )
        return None, errors
    template = template_components[0]
    tr1, tc1, tr2, tc2 = _bbox(template)
    th, tw = tr2 - tr1 + 1, tc2 - tc1 + 1
    if th != tw:
        errors.append(
            f"template bbox must be square so rotate-cw fits its slot, got {th}x{tw}"
        )
    if not 2 <= th <= 4 or not 2 <= tw <= 4:
        errors.append(f"template bbox must be 2..4 per side, got {th}x{tw}")
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in CONTROL_COLORS
    ]
    counts = {color: sum(value == color for _, _, value in markers) for color in CONTROL_COLORS}
    bad_counts = {color: count for color, count in counts.items() if count != 1}
    if bad_counts:
        errors.append(f"each control color must occur exactly once, got {bad_counts}")
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    if len(rows) != 2 or len(cols) != 2:
        errors.append(f"controls must occupy exactly two rows and two columns, got {rows} x {cols}")
    elif {(r, c) for r, c, _ in markers} != {(r, c) for r in rows for c in cols}:
        errors.append("controls must occupy all four corners of their row/column rectangle")

    if errors:
        return None, errors

    cr1, cr2 = rows
    cc1, cc2 = cols
    candidates: list[str] = []
    gaps: dict[str, int] = {}
    if cr2 < tr1:
        candidates.append("controls_above")
        gaps["controls_above"] = tr1 - cr2 - 1
    if cr1 > tr2:
        candidates.append("controls_below")
        gaps["controls_below"] = cr1 - tr2 - 1
    if cc2 < tc1:
        candidates.append("controls_left")
        gaps["controls_left"] = tc1 - cc2 - 1
    if cc1 > tc2:
        candidates.append("controls_right")
        gaps["controls_right"] = cc1 - tc2 - 1
    if not candidates:
        return None, ["template and controls must be separated on at least one axis"]
    layout_mode = max(
        candidates,
        key=lambda name: (gaps[name], -LAYOUT_MODES.index(name)),
    )
    order_tuple = tuple(
        next(value for r, c, value in markers if r == rr and c == cc)
        for rr in rows
        for cc in cols
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": th,
        "control_order": CONTROL_ORDERS.index(order_tuple),
        "layout_mode": layout_mode,
        "template_cells": template,
        "template_bbox": (tr1, tc1, tr2, tc2),
        "controls": markers,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    stats, errors = _analyze(grid)
    if errors:
        return errors
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict):
            for axis in AXES:
                if axis in requested and requested[axis] is not None and stats[axis] != requested[axis]:
                    errors.append(
                        f"{axis} requested {requested[axis]!r}, realized {stats[axis]!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    stats, errors = _analyze(grid)
    if errors or stats is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {axis: stats[axis] for axis in AXES}


def _template_matrix(grid) -> list[list[int]]:
    stats, errors = _analyze(grid)
    if errors or stats is None:
        raise ValueError("invalid transform-panel input: " + "; ".join(errors))
    r1, c1, r2, c2 = stats["template_bbox"]
    cells = stats["template_cells"]
    return [
        [2 if (r, c) in cells else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _paste(out: list[list[int]], block: list[list[int]], top: int, left: int) -> None:
    for r, row in enumerate(block):
        for c, value in enumerate(row):
            rr, cc = top + r, left + c
            if value and 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = 7


def _panel_output(grid, *, fixed_size: int | None = None) -> list[list[int]]:
    stats, errors = _analyze(grid)
    if errors or stats is None:
        raise ValueError("invalid transform-panel input: " + "; ".join(errors))
    template = _template_matrix(grid)
    if fixed_size is not None:
        fixed = [[0] * fixed_size for _ in range(fixed_size)]
        for r, row in enumerate(template[:fixed_size]):
            for c, value in enumerate(row[:fixed_size]):
                fixed[r][c] = value
        template = fixed
    size_h, size_w = len(template), len(template[0])
    out = full_grid(2 * size_h + 1, 2 * size_w + 1, 0)
    markers = stats["controls"]
    rows = sorted({r for r, _, _ in markers})
    cols = sorted({c for _, c, _ in markers})
    transforms = {
        1: lambda x: [list(row) for row in x],
        3: _rotate_cw,
        4: _rotate_180,
        6: _flip_lr,
    }
    for row, col, color in markers:
        block = transforms[color](template)
        _paste(out, block, rows.index(row) * (size_h + 1), cols.index(col) * (size_w + 1))
    return out


def fixed_3x3_panel(grid):
    """Wrong but canonical-fitting solver: force every template/output to 3x3/7x7."""
    return _panel_output(grid, fixed_size=3)


def _non_3x3_template(grid) -> bool:
    stats, errors = _analyze(grid)
    return not errors and stats is not None and stats["template_size"] != 3


def lesson_identifiable(demos, query) -> list[str]:
    del query
    for demo in demos:
        stats, errors = _analyze(demo.get("input")) if isinstance(demo, dict) else (None, ["bad demo"])
        if not errors and stats is not None and stats["template_size"] != 3:
            return []
    return ["fixed_3x3_panel fits every demonstration; include a size-2 or size-4 template"]


EXAMPLES_NEEDED = 3
SEMANTIC_WITNESSES = {"non_3x3_template": _non_3x3_template}
SEMANTIC_RIVALS = {"fixed_3x3_panel": fixed_3x3_panel}
WITNESS_RIVALS = {"non_3x3_template": ["fixed_3x3_panel"]}
CANONICAL_SHORTCUTS = {"fixed_3x3_panel": fixed_3x3_panel}
LESSON_COMPETITORS = {"fixed_3x3_panel": fixed_3x3_panel}
