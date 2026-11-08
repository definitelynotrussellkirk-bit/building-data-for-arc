"""Generator for ``b5c887448ed9`` — connect color pairs with ordered elbows.

Every nonzero color occurs exactly twice.  Sort each color's two endpoints in
row-major order, draw the horizontal leg from the upper endpoint to the lower
endpoint's column, then draw the vertical leg down to the lower endpoint.
Colors are processed by the row-major position of their first endpoint, so a
later color wins at an interior crossing.

The four-example schedule alternates disjoint and crossing layouts, both
horizontal directions, two/three/four color counts, and low/high palettes.
Every four consecutive examples therefore rebut the alternative elbow,
identity/one-pair, color-blind, and reverse-overwrite shortcuts.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b5c887448ed9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "c56faa67ac6f"

SUMMARY = (
    "For each color pair, sort endpoints in row-major order, draw horizontally "
    "from the upper endpoint to the lower endpoint's column and then vertically "
    "to the lower endpoint; later-read colors overwrite earlier colors at crossings."
)

INVARIANTS = [
    "the rectangular input uses background 0 and ARC colors 1..9",
    "each nonzero color appears exactly twice",
    "ordinary lessons contain 2..4 non-aligned color pairs",
    "ordinary lessons never place one color's endpoint on another color's elbow",
    "crossing lessons contain an interior crossing whose winner is fixed by color reading order",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded with canonical-scale schedule anchors",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded with canonical-scale schedule anchors",
        "valid": "8..14",
    },
    "n_colors": {
        "type": "int",
        "default": "four-example schedule 2,3,4,3",
        "valid": "2..4",
    },
    "palette_band": {
        "type": "str",
        "default": "four-example schedule low|high|high|low",
        "valid": "low|high",
    },
    "layout_profile": {
        "type": "str",
        "default": "four-example schedule separated|crossing|separated|crossing",
        "valid": "separated|crossing",
    },
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

_SCHEDULE = (
    ("separated_two", 2, "low", "separated"),
    ("crossing_three", 3, "high", "crossing"),
    ("separated_four", 4, "high", "separated"),
    ("crossing_three_low", 3, "low", "crossing"),
)
SCHEDULE_PROFILES = tuple(row[0] for row in _SCHEDULE)
_PALETTES = {
    "low": (1, 2, 3, 4),
    "high": (6, 7, 8, 9),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic four-example lesson schedule."""
    del seed, difficulty
    return _SCHEDULE[int(sample_index) % len(_SCHEDULE)][0]


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid must be rectangular"]
    normalized = [list(row) for row in grid]
    invalid = sorted(
        {
            value
            for row in normalized
            for value in row
            if isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
        },
        key=repr,
    )
    if invalid:
        errors.append(f"cells must be integer ARC colors 0..9, got {invalid}")
    return normalized, errors


def _color_cells(grid: list[list[int]]) -> dict[int, list[tuple[int, int]]]:
    cells: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                cells.setdefault(value, []).append((r, c))
    return cells


def _ordered_elbow(
    first: tuple[int, int], second: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    """Horizontal from the row-major first endpoint, then vertical."""
    (r0, c0), (r1, c1) = sorted((first, second))
    c_step = 1 if c1 >= c0 else -1
    r_step = 1 if r1 >= r0 else -1
    horizontal = [(r0, c) for c in range(c0, c1 + c_step, c_step)]
    vertical = [(r, c1) for r in range(r0, r1 + r_step, r_step)]
    return tuple(dict.fromkeys(horizontal + vertical))


def _vertical_first_elbow(
    first: tuple[int, int], second: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    """Named rival: vertical from the upper endpoint, then horizontal below."""
    (r0, c0), (r1, c1) = sorted((first, second))
    r_step = 1 if r1 >= r0 else -1
    c_step = 1 if c1 >= c0 else -1
    vertical = [(r, c0) for r in range(r0, r1 + r_step, r_step)]
    horizontal = [(r1, c) for c in range(c0, c1 + c_step, c_step)]
    return tuple(dict.fromkeys(vertical + horizontal))


def _analysis(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    result: dict[str, Any] = {"errors": errors, "grid": normalized}
    if normalized is None or errors:
        return result

    h, w = len(normalized), len(normalized[0])
    cells_by_color = _color_cells(normalized)
    if not cells_by_color:
        errors.append("expected at least one nonzero color pair")

    pairs: dict[int, tuple[tuple[int, int], tuple[int, int]]] = {}
    for color, cells in sorted(cells_by_color.items()):
        if len(cells) != 2:
            errors.append(
                f"color {color} appears {len(cells)} times; expected exactly two endpoints"
            )
            continue
        pairs[color] = tuple(sorted(cells))  # type: ignore[assignment]

    reading_order = sorted(pairs, key=lambda color: pairs[color][0])
    paths = {
        color: frozenset(_ordered_elbow(*pairs[color]))
        for color in reading_order
    }
    endpoint_owner = {
        point: color
        for color, pair in pairs.items()
        for point in pair
    }
    endpoint_conflicts: list[tuple[int, int, tuple[int, int]]] = []
    intersections: list[tuple[int, int, tuple[tuple[int, int], ...]]] = []
    for index, color_a in enumerate(reading_order):
        for color_b in reading_order[index + 1 :]:
            overlap = set(paths[color_a]) & set(paths[color_b])
            if overlap:
                intersections.append((color_a, color_b, tuple(sorted(overlap))))
            for point in sorted(overlap):
                owner = endpoint_owner.get(point)
                if owner is not None:
                    endpoint_conflicts.append((color_a, color_b, point))

    nonaligned = {
        color: pair[0][0] != pair[1][0] and pair[0][1] != pair[1][1]
        for color, pair in pairs.items()
    }
    rightward = sum(pair[0][1] < pair[1][1] for pair in pairs.values())
    leftward = sum(pair[0][1] > pair[1][1] for pair in pairs.values())

    palette = frozenset(cells_by_color)
    if palette and palette <= frozenset(_PALETTES["low"]):
        palette_band = "low"
    elif palette and palette <= frozenset(_PALETTES["high"]):
        palette_band = "high"
    else:
        palette_band = None

    result.update(
        {
            "grid_h": h,
            "grid_w": w,
            "cells_by_color": cells_by_color,
            "pairs": pairs,
            "reading_order": reading_order,
            "paths": paths,
            "n_colors": len(cells_by_color),
            "palette": palette,
            "palette_band": palette_band,
            "nonaligned": nonaligned,
            "rightward": rightward,
            "leftward": leftward,
            "intersections": intersections,
            "crossing_count": sum(len(points) for _, _, points in intersections),
            "endpoint_conflicts": endpoint_conflicts,
            "layout_profile": "crossing" if intersections else "separated",
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority-valid pair grammar and reject structural impostors."""
    del difficulty, meta
    analysis = _analysis(grid)
    return list(analysis["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Generated lessons stay on a nondegenerate extension of canonical inputs."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not (7 <= analysis["grid_h"] <= 14 and 8 <= analysis["grid_w"] <= 14):
        errors.append("dimensions must lie in the generated 7..14 by 8..14 envelope")
    if not 2 <= analysis["n_colors"] <= 4:
        errors.append(f"teaching lessons need 2..4 colors, got {analysis['n_colors']}")
    if not all(analysis["nonaligned"].values()):
        errors.append("every teaching pair must differ in both row and column")
    if analysis["endpoint_conflicts"]:
        errors.append("an endpoint lies on another color's elbow")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    errors = strict_canonical_like(grid)
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    if analysis["palette_band"] is None:
        raise ValueError("generated palette does not identify low/high palette_band")
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_colors": analysis["n_colors"],
        "palette_band": analysis["palette_band"],
        "layout_profile": analysis["layout_profile"],
    }


def _draw_int_axis(ctx, label: str, valid: tuple[int, int], default: tuple[int, int]) -> int:
    bounds = valid if label in ctx.overrides and ctx.overrides[label] is not None else default
    return ctx.draw_int(label, *bounds)


def _draw_choice_axis(ctx, label: str, valid: tuple[str, ...], default: str) -> str:
    options = valid if label in ctx.overrides and ctx.overrides[label] is not None else (default,)
    return ctx.draw_choice(label, options)


def _separated_pairs(h: int, w: int, n_colors: int, rng) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Place one elbow inside each of four disjoint quadrants."""
    row_gap = h // 2
    col_gap = w // 2
    row_ranges = ((0, row_gap - 1), (row_gap + 1, h - 1))
    col_ranges = ((0, col_gap - 1), (col_gap + 1, w - 1))
    blocks = [(rr, cc) for rr in row_ranges for cc in col_ranges]
    rng.shuffle(blocks)

    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for (r_lo, r_hi), (c_lo, c_hi) in blocks[:n_colors]:
        rows = rng.sample(range(r_lo, r_hi + 1), 2)
        cols = rng.sample(range(c_lo, c_hi + 1), 2)
        rows.sort()
        if rng.randrange(2):
            pair = ((rows[0], cols[0]), (rows[1], cols[1]))
        else:
            pair = ((rows[0], cols[1]), (rows[1], cols[0]))
        pairs.append(tuple(sorted(pair)))
    return pairs


def _crossing_pairs(h: int, w: int, n_colors: int, rng) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Construct an endpoint-safe interior crossing plus optional local pairs."""
    top = rng.randint(0, min(1, h - 7))
    bottom = h - 1
    cross_col = w // 2

    # A's vertical leg crosses B's horizontal leg.  A is first in reading order,
    # so B must own the crossing in the authoritative output.
    pairs = [
        ((top, 0), (bottom - 2, cross_col)),
        ((top + 2, w - 1), (bottom, 1)),
        ((top, w - 3), (top + 1, w - 2)),
        ((bottom - 1, 2), (bottom, 3)),
    ]
    if rng.randrange(2):
        pairs = [
            tuple(sorted(((r0, w - 1 - c0), (r1, w - 1 - c1))))
            for (r0, c0), (r1, c1) in pairs
        ]
    return [tuple(sorted(pair)) for pair in pairs[:n_colors]]


def _choose_colors(n_colors: int, palette_band: str, rng) -> tuple[int, ...]:
    palette = list(_PALETTES[palette_band])
    rng.shuffle(palette)
    return tuple(palette[:n_colors])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    slot = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    _, scheduled_n, scheduled_palette, scheduled_layout = slot

    # Slot 1 is a canonical-scale anchor in every difficulty band.  Other slots
    # expand search load by band while exact overrides retain the full envelope.
    if int(sample_index) % len(_SCHEDULE) == 1:
        anchors = {
            "easy": ((8, 8), (9, 9)),
            "medium": ((8, 8), (10, 10)),
            "hard": ((10, 10), (10, 10)),
        }
        default_h, default_w = anchors[band]
    else:
        ranges = {
            "easy": ((7, 9), (8, 10)),
            "medium": ((8, 11), (9, 12)),
            "hard": ((9, 14), (10, 14)),
        }
        default_h, default_w = ranges[band]

    h = _draw_int_axis(ctx, "grid_h", (7, 14), default_h)
    w = _draw_int_axis(ctx, "grid_w", (8, 14), default_w)
    n_colors = _draw_int_axis(ctx, "n_colors", (2, 4), (scheduled_n, scheduled_n))
    palette_band = _draw_choice_axis(
        ctx, "palette_band", tuple(_PALETTES), scheduled_palette
    )
    layout_profile = _draw_choice_axis(
        ctx, "layout_profile", ("separated", "crossing"), scheduled_layout
    )

    layout_rng = ctx.draw_rng("layout")
    if layout_profile == "separated":
        pairs = _separated_pairs(h, w, n_colors, layout_rng)
    else:
        pairs = _crossing_pairs(h, w, n_colors, layout_rng)
    colors = _choose_colors(n_colors, palette_band, ctx.draw_rng("colors"))

    grid = full_grid(h, w, 0)
    for color, pair in zip(colors, pairs):
        for r, c in pair:
            if grid[r][c] != 0:
                raise AssertionError(f"duplicate generated endpoint at {(r, c)}")
            grid[r][c] = color

    errors = strict_canonical_like(grid)
    if errors:
        raise AssertionError("generated invalid ordered-elbow lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_colors": n_colors,
        "palette_band": palette_band,
        "layout_profile": layout_profile,
    }
    if observed != expected:
        raise AssertionError(f"generated axes are not observable: expected {expected}, got {observed}")
    return grid


def _predict(
    grid,
    *,
    vertical_first: bool = False,
    reverse_order: bool = False,
    color_limit: int | None = None,
    fixed_color: int | None = None,
):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    colors = list(analysis["reading_order"])
    if reverse_order:
        colors.reverse()
    if color_limit is not None:
        colors = colors[:color_limit]
    path_fn = _vertical_first_elbow if vertical_first else _ordered_elbow
    for color in colors:
        paint_color = fixed_color if fixed_color is not None else color
        for r, c in path_fn(*analysis["pairs"][color]):
            out[r][c] = paint_color
    return out


def _identity(grid):
    return copy.deepcopy(grid)


def _vertical_first(grid):
    return _predict(grid, vertical_first=True)


def _reverse_overwrite(grid):
    return _predict(grid, reverse_order=True)


def _first_color_only(grid):
    return _predict(grid, color_limit=1)


def _color_blind(grid):
    return _predict(grid, fixed_color=1)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "vertical_first": _vertical_first,
    "reverse_overwrite": _reverse_overwrite,
    "first_color_only": _first_color_only,
    "color_blind": _color_blind,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if strict_canonical_like(grid) else analysis


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "nontrivial_elbow": lambda grid: _valid_analysis(grid) is not None,
    "rightward_upper_leg": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None and analysis["rightward"] > 0
    ),
    "leftward_upper_leg": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None and analysis["leftward"] > 0
    ),
    "multiple_colors": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None and analysis["n_colors"] >= 2
    ),
    "non_one_color_preserved": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and any(color != 1 for color in analysis["palette"])
    ),
    "crossing_overwrite": lambda grid: (
        (analysis := _valid_analysis(grid)) is not None
        and analysis["layout_profile"] == "crossing"
    ),
}

WITNESS_RIVALS = {
    "nontrivial_elbow": ["identity"],
    "rightward_upper_leg": ["vertical_first"],
    "leftward_upper_leg": ["vertical_first"],
    "multiple_colors": ["first_color_only"],
    "non_one_color_preserved": ["color_blind"],
    "crossing_overwrite": ["reverse_overwrite"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival fits all demos but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]

    for index, pair in enumerate(demos):
        input_errors = strict_canonical_like(pair.get("input"))
        if input_errors:
            reasons.append(f"demo {index} input outside teaching grammar")
        elif _predict(pair["input"]) != pair.get("output"):
            reasons.append(f"demo {index} output disagrees with ordered-elbow rule")
    query_errors = strict_canonical_like(query.get("input"))
    if query_errors:
        reasons.append("query input outside teaching grammar")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a different query output"
                )
    return reasons
