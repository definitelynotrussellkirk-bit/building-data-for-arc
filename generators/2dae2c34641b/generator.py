"""Generator for 2dae2c34641b — connect equal-color endpoint pairs by elbows.

For each nonzero color, sort its two endpoints by row.  Starting at the upper
endpoint, draw vertically to the lower endpoint's row, then horizontally to the
lower endpoint.  Inputs contain only endpoints; the canonical Racket authority
produces labels.
"""
from __future__ import annotations

from functools import lru_cache
from math import gcd
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2dae2c34641b"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "95bc32a62544"

SUMMARY = (
    "Two or three colors each mark two non-aligned endpoints. For every color, "
    "connect the upper endpoint vertically to the lower row and then "
    "horizontally to the lower endpoint. Generated elbow paths are disjoint."
)
INVARIANTS = [
    "background is 0 and every nonzero color appears exactly twice",
    "each pair occupies distinct rows and distinct columns",
    "the authoritative vertical-then-horizontal elbow paths are pairwise disjoint",
    "three consecutive default samples include left, right, and mixed bends and a three-pair case",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

PALETTES = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}
BEND_PATTERNS = ("left", "right", "mixed")
CANONICAL_PROFILES = {
    "easy": ((9, 11), (10, 12)),
    "medium": ((9, 11), (10, 12), (10, 13), (11, 13), (12, 10)),
    "hard": ((10, 13), (11, 13), (12, 10)),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile draw within the difficulty band",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile draw within the difficulty band",
        "valid": "10..13",
    },
    "n_pairs": {
        "type": "int",
        "default": "cycle 2,2,3 by sample_index",
        "valid": "2..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "cycle low,mid,high by sample_index",
        "valid": "low|mid|high",
    },
    "bend_pattern": {
        "type": "str",
        "default": "cycle left,right,mixed by sample_index",
        "valid": "left|right|mixed",
    },
}
# Every Cartesian combination above is feasible; opt into strict rejection accounting.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _colors_reading(grid: list[list[int]]) -> list[int]:
    colors: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
    return colors


def _cells_of(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _elbow_path(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    """Canonical path: lexicographically upper endpoint, vertical then horizontal."""
    (r1, c1), (r2, c2) = sorted((a, b))
    vertical = [(r, c1) for r in range(r1, r2 + 1)]
    step = 1 if c2 >= c1 else -1
    horizontal = [(r2, c) for c in range(c1, c2 + step, step)]
    # Preserve path order while dropping the duplicated bend cell.
    return tuple(dict.fromkeys((*vertical, *horizontal)))


def _horizontal_first_path(
    a: tuple[int, int], b: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    (r1, c1), (r2, c2) = sorted((a, b))
    cstep = 1 if c2 >= c1 else -1
    horizontal = [(r1, c) for c in range(c1, c2 + cstep, cstep)]
    vertical = [(r, c2) for r in range(r1, r2 + 1)]
    return tuple(dict.fromkeys((*horizontal, *vertical)))


def _paint_paths(
    grid: list[list[int]],
    *,
    path_fn=_elbow_path,
    limit: int | None = None,
) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    colors = _colors_reading(grid)
    if limit is not None:
        colors = colors[:limit]
    for color in colors:
        cells = sorted(_cells_of(grid, color))
        if len(cells) != 2:
            raise ValueError(f"color {color} must have exactly two endpoints")
        for r, c in path_fn(cells[0], cells[1]):
            out[r][c] = color
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for tests/rivals; Racket remains label authority."""
    return _paint_paths(grid)


def _horizontal_first(grid: list[list[int]]) -> list[list[int]]:
    """Rival: turn horizontally at the upper row, then descend."""
    return _paint_paths(grid, path_fn=_horizontal_first_path)


def _first_two_pairs_only(grid: list[list[int]]) -> list[list[int]]:
    """Canonical-fitting shortcut: silently ignore every color after the first two."""
    return _paint_paths(grid, limit=2)


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    info: dict[str, Any] = {}
    if not isinstance(grid, (list, tuple)) or not grid:
        return info, ["grid must be a nonempty rectangular list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return info, ["grid rows must be nonempty lists or tuples"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]

    errors: list[str] = []
    if not 9 <= h <= 12:
        errors.append(f"grid height must be 9..12, got {h}")
    if not 10 <= w <= 13:
        errors.append(f"grid width must be 10..13, got {w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer colors 0..9, not booleans")
        return info, errors

    normalized = [list(row) for row in grid]
    colors = _colors_reading(normalized)
    if not 2 <= len(colors) <= 3:
        errors.append(f"expected 2..3 nonzero colors, got {len(colors)}")

    paths: dict[int, frozenset[tuple[int, int]]] = {}
    directions: list[str] = []
    occupied: dict[tuple[int, int], int] = {}
    for color in colors:
        cells = sorted(_cells_of(normalized, color))
        if len(cells) != 2:
            errors.append(f"color {color} appears {len(cells)} times (expected 2)")
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            errors.append(f"color {color} endpoints must occupy distinct rows")
        if c1 == c2:
            errors.append(f"color {color} endpoints must occupy distinct columns")
        if r1 == r2 or c1 == c2:
            continue
        path = frozenset(_elbow_path(cells[0], cells[1]))
        paths[color] = path
        directions.append("right" if c2 > c1 else "left")
        for cell in path:
            prior = occupied.get(cell)
            if prior is not None and prior != color:
                errors.append(
                    f"authoritative paths for colors {prior} and {color} intersect at {cell}"
                )
                break
            occupied[cell] = color

    bend_pattern = None
    if directions:
        kinds = set(directions)
        bend_pattern = directions[0] if len(kinds) == 1 else "mixed"

    palette_kind = None
    color_set = set(colors)
    for name, palette in PALETTES.items():
        if color_set <= set(palette):
            palette_kind = name
            break

    info.update(
        {
            "grid_h": h,
            "grid_w": w,
            "n_pairs": len(colors),
            "palette_kind": palette_kind,
            "bend_pattern": bend_pattern,
            "colors": tuple(colors),
            "paths": paths,
            "directions": tuple(directions),
        }
    )
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    if info["palette_kind"] is None:
        raise ValueError("colors do not identify one generated palette_kind")
    return {name: info[name] for name in AXES}


@lru_cache(maxsize=None)
def _candidate_paths(
    h: int,
    w: int,
    direction: str,
    band: str,
) -> tuple[tuple[tuple[int, int], tuple[int, int], int], ...]:
    """Return immutable endpoint candidates with a compact occupied-cell mask.

    Override qualification calls the same small geometry domains thousands of
    times.  Caching these pure domains and storing paths as integer bitsets keeps
    that exact-contract sweep linear in draws rather than in all possible elbows.
    """
    candidates: list[tuple[tuple[int, int], tuple[int, int], int]] = []
    for r1 in range(h - 1):
        for r2 in range(r1 + 1, h):
            for c1 in range(w):
                c2s = range(0, c1) if direction == "left" else range(c1 + 1, w)
                for c2 in c2s:
                    span = (r2 - r1) + abs(c2 - c1)
                    if band == "easy" and span > 7:
                        continue
                    if band == "hard" and span < 7:
                        continue
                    a, b = (r1, c1), (r2, c2)
                    mask = 0
                    for r, c in _elbow_path(a, b):
                        mask |= 1 << (r * w + c)
                    candidates.append((a, b, mask))
    return tuple(candidates)


def _pool_order(pool, rng) -> tuple[int, int]:
    """Choose a lazy full permutation without copying or shuffling the pool."""
    size = len(pool)
    if size == 0:
        raise ValueError("candidate pool is empty")
    if size == 1:
        return 0, 1
    start = rng.randrange(size)
    step = rng.randrange(1, size)
    while gcd(step, size) != 1:
        step += 1
        if step == size:
            step = 1
    return start, step


def _ordered_pools(
    h: int,
    w: int,
    directions: list[str],
    band: str,
    rng,
):
    ordered = []
    for direction in directions:
        pool = _candidate_paths(h, w, direction, band)
        # Span is a curriculum preference, not a feasibility boundary.
        if not pool:
            pool = _candidate_paths(h, w, direction, "medium")
        start, step = _pool_order(pool, rng)
        ordered.append((pool, start, step))
    return ordered


def _select_disjoint_paths(
    h: int,
    w: int,
    directions: list[str],
    band: str,
    rng,
):
    pools = _ordered_pools(h, w, directions, band, rng)
    chosen: list[tuple[tuple[int, int], tuple[int, int], int]] = []

    def search(index: int, used: int) -> bool:
        if index == len(pools):
            return True
        pool, start, step = pools[index]
        for offset in range(len(pool)):
            candidate = pool[(start + offset * step) % len(pool)]
            if candidate[2] & used == 0:
                chosen.append(candidate)
                if search(index + 1, used | candidate[2]):
                    return True
                chosen.pop()
        return False

    if search(0, 0):
        return chosen

    # Retry over the complete lawful domain before reporting a true failure.
    pools = _ordered_pools(h, w, directions, "medium", rng)
    chosen.clear()
    if search(0, 0):
        return chosen
    raise ValueError("no disjoint elbow placement for the requested axes")


def _draw_dimensions(ctx, band: str, overrides: dict[str, Any]) -> tuple[int, int]:
    if overrides.get("grid_h") is None and overrides.get("grid_w") is None:
        profile_rng = ctx.draw_rng("canonical_profile")
        h0, w0 = profile_rng.choice(CANONICAL_PROFILES[band])
        return ctx.draw_choice("grid_h", [h0]), ctx.draw_choice("grid_w", [w0])
    return ctx.draw_int("grid_h", 9, 12), ctx.draw_int("grid_w", 10, 13)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_pairs"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"override {name!r} must be an integer")
    for name in ("palette_kind", "bend_pattern"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise ValueError(f"override {name!r} must be a string")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx, band, overrides)

    residue = sample_index % 3
    if overrides.get("n_pairs") is None:
        n_pairs = ctx.draw_choice("n_pairs", [3 if residue == 2 else 2])
    else:
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    if overrides.get("palette_kind") is None:
        palette_kind = ctx.draw_choice("palette_kind", [tuple(PALETTES)[residue]])
    else:
        palette_kind = ctx.draw_choice("palette_kind", tuple(PALETTES))
    if overrides.get("bend_pattern") is None:
        bend_pattern = ctx.draw_choice("bend_pattern", [BEND_PATTERNS[residue]])
    else:
        bend_pattern = ctx.draw_choice("bend_pattern", BEND_PATTERNS)

    layout_rng = ctx.draw_rng("layout")
    colors = list(layout_rng.sample(PALETTES[palette_kind], n_pairs))
    if bend_pattern == "mixed":
        directions = ["left", "right"]
        directions.extend(layout_rng.choice(("left", "right")) for _ in range(n_pairs - 2))
        layout_rng.shuffle(directions)
    else:
        directions = [bend_pattern] * n_pairs

    placements = _select_disjoint_paths(h, w, directions, band, layout_rng)
    grid = full_grid(h, w, 0)
    for color, (a, b, _path) in zip(colors, placements):
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
    return grid


def _info_predicate(grid, predicate) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(predicate(info))


def _has_left(grid) -> bool:
    return _info_predicate(grid, lambda info: "left" in info["directions"])


def _has_right(grid) -> bool:
    return _info_predicate(grid, lambda info: "right" in info["directions"])


def _has_mixed(grid) -> bool:
    return _info_predicate(grid, lambda info: info["bend_pattern"] == "mixed")


def _has_three_pairs(grid) -> bool:
    return _info_predicate(grid, lambda info: info["n_pairs"] == 3)


SEMANTIC_WITNESSES = {
    "left_bend": _has_left,
    "right_bend": _has_right,
    "mixed_bends": _has_mixed,
    "three_pairs": _has_three_pairs,
}
SEMANTIC_RIVALS = {
    "horizontal_first": _horizontal_first,
    "first_two_pairs_only": _first_two_pairs_only,
}
WITNESS_RIVALS = {
    "left_bend": ["horizontal_first"],
    "right_bend": ["horizontal_first"],
    "mixed_bends": ["horizontal_first"],
    "three_pairs": ["first_two_pairs_only"],
}
CANONICAL_SHORTCUTS = {"first_two_pairs_only": _first_two_pairs_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is outside the strict domain: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match vertical-then-horizontal elbows")

    valid_demos = [
        pair
        for pair in demos
        if isinstance(pair, dict) and "input" in pair and "output" in pair
    ]
    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qerrors = self_check(query["input"])
        if qerrors:
            reasons.append(f"query is outside the strict domain: {qerrors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match vertical-then-horizontal elbows")
    return reasons
