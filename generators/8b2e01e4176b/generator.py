"""Generator for ``Expand the Singletons into Diamonds``.

The selected rule is cell-local: every nonzero input cell paints itself and
its four cardinal neighbours, clipping arms that leave the grid.  Generated
scenes keep source cells separated so differently coloured expansions never
fight over an output cell, but deliberately include repeated source colours
and clipped edge seeds so the lesson cannot collapse to "one object per
colour" or "only expand interior cells".
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b2e01e4176b"
TASK_ID = "8b2e01e4176b"
VERSION = "3.0.1"  # reject invalid difficulty + scheduled shortcut-rebutting curriculum
RULE_HASH = "1e68480e5183"

SUMMARY = (
    "On a zero background, each separated nonzero singleton seed expands on "
    "a fresh same-size output into its Manhattan-radius-1 diamond: the seed "
    "cell plus its up/down/left/right neighbours, all in the seed's own "
    "colour.  Out-of-bounds arms are clipped.  Ordinary lessons alternate "
    "between canonical anchors and scenes containing both an edge-clipped "
    "seed and two separated seeds that reuse a colour."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

INVARIANTS = [
    "background is 0 and every nonzero input cell is a singleton seed",
    "there are at least two seeds",
    "seed centres have Manhattan distance at least 3, so output diamonds do not overlap",
    "seed colours may repeat; each seed is expanded independently",
    "edge and corner seeds are lawful and their out-of-bounds arms are clipped",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical/expanded shape",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical/expanded shape",
        "valid": "8..14",
    },
    "n_seeds": {
        "type": "int",
        "default": "2..3 anchor / 3..6 both-controls",
        "valid": "2..6",
    },
    "edge_mode": {
        "type": "enum",
        "default": "scheduled",
        "valid": "interior|clipped",
    },
    "color_pattern": {
        "type": "enum",
        "default": "scheduled",
        "valid": "distinct|reused",
    },
}

SCHEDULE_PROFILES = ("anchor", "both_controls")
_CANONICAL_SHAPES = ((8, 8), (7, 9), (9, 9), (8, 10), (7, 8))
_EXPANDED_SHAPES = {
    "easy": ((8, 9), (9, 10), (7, 11)),
    "medium": ((8, 11), (9, 12), (10, 10), (10, 12)),
    "hard": ((9, 11), (10, 12), (11, 13), (12, 14)),
}
_CARDINAL = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
_SQUARE = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Four-slot schedule: anchor / both / both / anchor.

    Every sliding three-demo window therefore contains both a canonical anchor
    and a joint repeated-colour + clipped-edge counterexample.
    """
    del seed, difficulty
    return "anchor" if sample_index % 4 in (0, 3) else "both_controls"


def _default_controls(ctx, sample_index: int, difficulty) -> dict[str, object]:
    profile = schedule_profile(ctx.seed, sample_index, difficulty=difficulty)
    band = difficulty if difficulty in _EXPANDED_SHAPES else "medium"
    rng = ctx.draw_rng("default_controls")
    if profile == "anchor":
        height, width = rng.choice(_CANONICAL_SHAPES)
        n_seeds = rng.choice((2, 3))
        edge_mode = "interior"
        color_pattern = "distinct"
    else:
        height, width = rng.choice(_EXPANDED_SHAPES[band])
        n_seeds = rng.choice(
            (3, 4) if band == "easy" else (4, 5) if band == "medium" else (5, 6)
        )
        edge_mode = "clipped"
        color_pattern = "reused"
    return {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": n_seeds,
        "edge_mode": edge_mode,
        "color_pattern": color_pattern,
    }


def _spaced(point: tuple[int, int], chosen: list[tuple[int, int]]) -> bool:
    row, col = point
    return all(abs(row - other_row) + abs(col - other_col) >= 3
               for other_row, other_col in chosen)


def _search_positions(
    candidates: list[tuple[int, int]],
    target: int,
    chosen: list[tuple[int, int]],
    start: int = 0,
) -> list[tuple[int, int]] | None:
    if len(chosen) == target:
        return list(chosen)
    need = target - len(chosen)
    if len(candidates) - start < need:
        return None
    for index in range(start, len(candidates)):
        point = candidates[index]
        if not _spaced(point, chosen):
            continue
        chosen.append(point)
        result = _search_positions(candidates, target, chosen, index + 1)
        if result is not None:
            return result
        chosen.pop()
    return None


def _place_seeds(
    height: int,
    width: int,
    count: int,
    edge_mode: str,
    rng,
) -> list[tuple[int, int]]:
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(interior)
    if edge_mode == "interior":
        result = _search_positions(interior, count, [])
        if result is None:
            raise ValueError(
                f"could not place n_seeds={count} interior seeds on "
                f"grid_h={height}, grid_w={width}"
            )
        return result

    boundary = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ]
    rng.shuffle(boundary)
    # Exactly one scheduled boundary seed plus interior companions makes the
    # clipping branch visible without sacrificing a full interior diamond.
    for edge_seed in boundary:
        result = _search_positions(interior, count, [edge_seed])
        if result is not None:
            return result
    raise ValueError(
        f"could not place n_seeds={count} with edge_mode={edge_mode!r} on "
        f"grid_h={height}, grid_w={width}"
    )


def _draw_colors(count: int, pattern: str, rng) -> list[int]:
    if pattern == "distinct":
        return rng.sample(list(range(1, 10)), count)
    if count == 2:
        color = rng.choice(list(range(1, 10)))
        return [color, color]
    first, second = rng.sample(list(range(1, 10)), 2)
    colors = [first if index % 2 == 0 else second for index in range(count)]
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: "
            f"{', '.join(AXES)}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Defaults are scheduled first, then consumed by the same typed GenCtx
    # draws as explicit caller overrides.  This leaves exact provenance for
    # every ordinary draw without narrowing the override domain by difficulty.
    for axis, value in _default_controls(ctx, sample_index, difficulty).items():
        if ctx.overrides.get(axis) is None:
            ctx.overrides[axis] = value

    height = ctx.draw_int("grid_h", 7, 12)
    width = ctx.draw_int("grid_w", 8, 14)
    n_seeds = ctx.draw_int("n_seeds", 2, 6)
    edge_mode = ctx.draw_choice("edge_mode", ("interior", "clipped"))
    color_pattern = ctx.draw_choice("color_pattern", ("distinct", "reused"))

    positions = _place_seeds(
        height, width, n_seeds, edge_mode, ctx.draw_rng("layout")
    )
    colors = _draw_colors(n_seeds, color_pattern, ctx.draw_rng("colors"))
    grid = full_grid(height, width, 0)
    for (row, col), color in zip(positions, colors):
        grid[row][col] = color
    return grid


def _grid_shape_errors(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, list) or not grid:
        return 0, 0, ["empty grid"]
    if not all(isinstance(row, list) for row in grid) or not grid[0]:
        return 0, 0, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return len(grid), width, ["ragged grid"]
    return len(grid), width, []


def _seed_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def observe_overrides(grid) -> dict[str, object]:
    seeds = _seed_cells(grid)
    colors = [color for _, _, color in seeds]
    height, width = len(grid), len(grid[0])
    return {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": len(seeds),
        "edge_mode": (
            "clipped"
            if any(row in (0, height - 1) or col in (0, width - 1)
                   for row, col, _ in seeds)
            else "interior"
        ),
        "color_pattern": (
            "distinct" if len(colors) == len(set(colors)) else "reused"
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept separated singleton scenes and reject malformed lesson inputs."""
    del difficulty
    height, width, errors = _grid_shape_errors(grid)
    if errors:
        return errors
    if not (3 <= height <= 30 and 3 <= width <= 30):
        errors.append(f"grid shape {height}x{width} is outside ARC bounds 3..30")

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC colour {value!r} at {(row, col)}")
                return errors

    seeds = _seed_cells(grid)
    if not (2 <= len(seeds) <= 9):
        errors.append(f"expected 2..9 singleton seeds, found {len(seeds)}")
        return errors
    positions = [(row, col) for row, col, _ in seeds]
    for index, first in enumerate(positions):
        for second in positions[index + 1:]:
            if abs(first[0] - second[0]) + abs(first[1] - second[1]) < 3:
                errors.append(
                    f"seeds {first} and {second} are too close; their "
                    "radius-1 diamonds would overlap"
                )
                return errors

    requested: dict[str, object] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(
                    f"{axis} requested {expected!r}, observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The exact linked profile shared by the five canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    if (observed["grid_h"], observed["grid_w"]) not in set(_CANONICAL_SHAPES):
        reasons.append(
            f"shape {observed['grid_h']}x{observed['grid_w']} is not canonical"
        )
    if observed["n_seeds"] not in (2, 3):
        reasons.append(
            f"canonical inputs contain two or three seeds, found {observed['n_seeds']}"
        )
    if observed["color_pattern"] != "distinct":
        reasons.append("canonical inputs use a distinct colour for each seed")
    return reasons


def _paint_offsets(out, row: int, col: int, color: int, offsets) -> None:
    height, width = len(out), len(out[0])
    for delta_row, delta_col in offsets:
        target_row, target_col = row + delta_row, col + delta_col
        if 0 <= target_row < height and 0 <= target_col < width:
            out[target_row][target_col] = color


def rule_mirror(grid):
    """Python mirror used only for tests; the Racket rule remains authority."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for row, col, color in _seed_cells(grid):
        _paint_offsets(out, row, col, color, _CARDINAL)
    return out


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_chebyshev_square(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for row, col, color in _seed_cells(grid):
        _paint_offsets(out, row, col, color, _SQUARE)
    return out


def _rival_first_seed_only(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    row, col, color = _seed_cells(grid)[0]
    _paint_offsets(out, row, col, color, _CARDINAL)
    return out


def _rival_fixed_first_color(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    seeds = _seed_cells(grid)
    fixed_color = seeds[0][2]
    for row, col, _ in seeds:
        _paint_offsets(out, row, col, fixed_color, _CARDINAL)
    return out


def _rival_one_diamond_per_color(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    seen: set[int] = set()
    for row, col, color in _seed_cells(grid):
        if color in seen:
            continue
        seen.add(color)
        _paint_offsets(out, row, col, color, _CARDINAL)
    return out


def _rival_interior_only(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    height, width = len(grid), len(grid[0])
    for row, col, color in _seed_cells(grid):
        if row in (0, height - 1) or col in (0, width - 1):
            continue
        _paint_offsets(out, row, col, color, _CARDINAL)
    return out


def _valid(grid) -> bool:
    return not self_check(grid)


def _has_interior_seed(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(0 < row < height - 1 and 0 < col < width - 1
               for row, col, _ in _seed_cells(grid))


def _witness_full_cardinal(grid) -> bool:
    return _valid(grid) and _has_interior_seed(grid)


def _witness_multiple_seeds(grid) -> bool:
    return _valid(grid) and len(_seed_cells(grid)) >= 2


def _witness_multiple_colors(grid) -> bool:
    return _valid(grid) and len({color for _, _, color in _seed_cells(grid)}) >= 2


def _witness_reused_color(grid) -> bool:
    colors = [color for _, _, color in _seed_cells(grid)]
    return _valid(grid) and len(colors) != len(set(colors))


def _witness_clipped_seed(grid) -> bool:
    return _valid(grid) and observe_overrides(grid)["edge_mode"] == "clipped"


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "cardinal_not_identity_or_square": _witness_full_cardinal,
    "every_seed_expands": _witness_multiple_seeds,
    "seed_colour_is_preserved": _witness_multiple_colors,
    "reused_colour_seeds_are_independent": _witness_reused_color,
    "edge_seed_is_clipped_not_skipped": _witness_clipped_seed,
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _rival_identity,
    "chebyshev_square": _rival_chebyshev_square,
    "first_seed_only": _rival_first_seed_only,
    "fixed_first_colour": _rival_fixed_first_color,
    "one_diamond_per_color": _rival_one_diamond_per_color,
    "interior_only": _rival_interior_only,
}

WITNESS_RIVALS = {
    "cardinal_not_identity_or_square": ["identity", "chebyshev_square"],
    "every_seed_expands": ["first_seed_only"],
    "seed_colour_is_preserved": ["fixed_first_colour"],
    "reused_colour_seeds_are_independent": ["one_diamond_per_color"],
    "edge_seed_is_clipped_not_skipped": ["interior_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # Every canonical scene uses each colour once, so canonical alone cannot
    # distinguish this shortcut from the selected per-cell rule.
    "one_diamond_per_color": _rival_one_diamond_per_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo window to refute all named competitors."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    killed = {name: False for name in LESSON_COMPETITORS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match the selected rule")
        for name, rival in LESSON_COMPETITORS.items():
            killed[name] = killed[name] or rival(demo["input"]) != expected

    for name, was_killed in killed.items():
        if not was_killed:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
