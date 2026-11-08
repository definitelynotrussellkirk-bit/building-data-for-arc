"""Input sampler for fd277c567993 — transfer an additive color-8 stencil.

Two full color-5 columns delimit three equal panels.  The first two panels
show one object before and after adding color-8 cells.  The third panel holds
a query object.  The selected rule transfers the added cells by their offsets
from the first object's bounding-box top-left, overwriting query-object cells
when the stencil lands on them.
"""
from __future__ import annotations

import copy
import itertools
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fd277c567993"
TASK_ID = GENERATOR_ID
RULE_HASH = "1890aa619f98"
VERSION = "3.1.0"

SUMMARY = (
    "Two color-5 separator columns create equal before, after, and query panels. "
    "The after panel copies the before object and adds 1..4 color-8 cells. "
    "Transfer those additions by offsets from the before object's bbox top-left "
    "to the query object's bbox top-left; in-bounds additions overwrite any "
    "query cell they land on."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "two full color-5 columns delimit three equal 5..10 by 5..9 panels",
    "before and after contain the same one-color connected object at the same cells",
    "after adds exactly 1..4 color-8 cells on before-panel background",
    "query contains one connected one-color object that differs in color or geometry",
    "every transferred offset is in bounds for the query panel",
    "every four consecutive samples contain both clear and query-overwrite transfers",
    "any one pair can be held out from five consecutive samples without removing all overwrite witnesses",
]

_PANEL_H = tuple(range(5, 11))
_PANEL_W = tuple(range(5, 10))
_SHAPE_SIZES = tuple(range(3, 7))
_N_DIFF = tuple(range(1, 5))
_PALETTE_KINDS = ("distinct", "separator_shared")
_OFFSET_RELATIONS = ("clear", "overwrite")

AXES = {
    "panel_h": {
        "type": "int",
        "default": "5..10; canonical height 5 is strongly favored in every band",
        "valid": "5..10",
    },
    "panel_w": {
        "type": "int",
        "default": "5..9; canonical width 5 is strongly favored in every band",
        "valid": "5..9",
    },
    "shape_size_ab": {
        "type": "int",
        "default": "3..6 with difficulty-aware weighting",
        "valid": "3..6",
    },
    "shape_size_c": {
        "type": "int",
        "default": "3..6 with difficulty-aware weighting",
        "valid": "3..6",
    },
    "n_diff": {
        "type": "int",
        "default": "1..4 with difficulty-aware weighting",
        "valid": "1..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "distinct favored; separator_shared preserves canonical palette-4 support",
        "valid": "distinct|separator_shared",
    },
    "offset_relation": {
        "type": "str",
        "default": "alternating clear/overwrite by sample index for rotation-robust lessons",
        "valid": "clear|overwrite",
    },
}

# Every cross-product of the finite domains above is constructively realizable.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def _shape_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All normalized connected 3x3 polyominoes of the advertised sizes."""
    cells = tuple(itertools.product(range(3), repeat=2))
    catalog: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in _SHAPE_SIZES:
        shapes = []
        for combo in itertools.combinations(cells, size):
            shape = set(combo)
            if min(r for r, _ in shape) or min(c for _, c in shape):
                continue
            if _connected(shape):
                shapes.append(tuple(sorted(shape)))
        catalog[size] = tuple(shapes)
    return catalog


_SHAPES_BY_SIZE = _shape_catalog()


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    int_domains = {
        "panel_h": _PANEL_H,
        "panel_w": _PANEL_W,
        "shape_size_ab": _SHAPE_SIZES,
        "shape_size_c": _SHAPE_SIZES,
        "n_diff": _N_DIFF,
    }
    str_domains = {
        "palette_kind": _PALETTE_KINDS,
        "offset_relation": _OFFSET_RELATIONS,
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if name in int_domains:
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if value not in int_domains[name]:
                raise ValueError(f"{name}={value!r} outside {int_domains[name]}")
        else:
            if type(value) is not str:
                raise ValueError(f"{name} must be a string, not {type(value).__name__}")
            if value not in str_domains[name]:
                raise ValueError(f"{name}={value!r} outside {str_domains[name]}")


def _weighted_draw(ctx, name: str, domain: Sequence[Any], favored: Sequence[Any]) -> Any:
    """Draw from the full override domain while weighting ordinary samples."""
    return ctx.draw_choice(name, tuple(domain) + tuple(favored))


def _size_favorites(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (3, 3, 4)
    if difficulty == "hard":
        return (5, 6, 6)
    return (4, 5)


def _diff_favorites(difficulty: Any) -> tuple[int, ...]:
    if difficulty == "easy":
        return (1, 1, 2)
    if difficulty == "hard":
        return (3, 4, 4)
    return (2, 3)


def _scheduled_relation(sample_index: int) -> str:
    # Alternation gives every four-demo window two overwrite witnesses.  More
    # importantly, any pair may be held out from a five-pair lesson and the
    # remaining four demonstrations still contain both semantic branches.
    return "overwrite" if sample_index % 2 else "clear"


def _select_shapes(ctx, size_ab: int, size_c: int, relation: str):
    before_options = _SHAPES_BY_SIZE[size_ab]
    pair_options = [
        (before, query)
        for before in before_options
        for query in _SHAPES_BY_SIZE[size_c]
        if before != query
        and (relation != "overwrite" or set(query) - set(before))
    ]
    if not pair_options:
        raise ValueError(
            f"no shape pair for sizes {size_ab}/{size_c} and relation {relation}"
        )
    return ctx.draw_rng("shape_pair").choice(pair_options)


def _select_positions(ctx, panel_h: int, panel_w: int):
    # A 4x4 relative-stencil frame fits at every candidate origin.  Shapes fit
    # inside its upper-left 3x3 region, leaving enough lawful cells for n_diff=4.
    positions = [
        (r, c)
        for r in range(panel_h - 3)
        for c in range(panel_w - 3)
    ]
    before = ctx.draw_rng("before_position").choice(positions)
    query = ctx.draw_rng("query_position").choice([point for point in positions if point != before])
    return before, query


def _select_offsets(ctx, before_shape, query_shape, n_diff: int, relation: str):
    before = set(before_shape)
    query = set(query_shape)
    frame = {(r, c) for r in range(4) for c in range(4)}
    rng = ctx.draw_rng("stencil_offsets")
    if relation == "clear":
        pool = sorted(frame - before - query)
        if len(pool) < n_diff:
            raise ValueError("clear stencil pool is unexpectedly too small")
        return tuple(sorted(rng.sample(pool, n_diff)))

    overwrite = sorted(query - before)
    if not overwrite:
        raise ValueError("overwrite relation requires a query-only shape cell")
    first = rng.choice(overwrite)
    remainder = sorted((frame - before) - {first})
    chosen = [first] + rng.sample(remainder, n_diff - 1)
    return tuple(sorted(chosen))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)

    # Route the deterministic four-example curriculum schedule through GenCtx,
    # so provenance records the exact semantic value returned in the pixels.
    effective_overrides = dict(overrides)
    if effective_overrides.get("offset_relation") is None:
        effective_overrides["offset_relation"] = _scheduled_relation(sample_index)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    panel_h = _weighted_draw(ctx, "panel_h", _PANEL_H, (5,) * 16)
    panel_w = _weighted_draw(ctx, "panel_w", _PANEL_W, (5,) * 16)
    shape_size_ab = _weighted_draw(
        ctx, "shape_size_ab", _SHAPE_SIZES, _size_favorites(difficulty)
    )
    shape_size_c = _weighted_draw(
        ctx, "shape_size_c", _SHAPE_SIZES, _size_favorites(difficulty)
    )
    n_diff = _weighted_draw(ctx, "n_diff", _N_DIFF, _diff_favorites(difficulty))
    palette_kind = _weighted_draw(
        ctx, "palette_kind", _PALETTE_KINDS, ("distinct", "distinct")
    )
    relation = ctx.draw_choice("offset_relation", _OFFSET_RELATIONS)

    before_shape, query_shape = _select_shapes(
        ctx, shape_size_ab, shape_size_c, relation
    )
    (before_top, before_left), (query_top, query_left) = _select_positions(
        ctx, panel_h, panel_w
    )
    offsets = _select_offsets(ctx, before_shape, query_shape, n_diff, relation)

    color_rng = ctx.draw_rng("object_colors")
    ordinary_colors = (1, 2, 3, 4, 6, 7, 9)
    if palette_kind == "separator_shared":
        before_color = 5
        query_color = color_rng.choice(ordinary_colors)
    else:
        before_color, query_color = color_rng.sample(ordinary_colors, 2)

    total_w = panel_w * 3 + 2
    grid = full_grid(panel_h, total_w, 0)
    sep1, sep2 = panel_w, panel_w * 2 + 1
    for row in range(panel_h):
        grid[row][sep1] = 5
        grid[row][sep2] = 5

    for dr, dc in before_shape:
        grid[before_top + dr][before_left + dc] = before_color
        grid[before_top + dr][sep1 + 1 + before_left + dc] = before_color
    for dr, dc in query_shape:
        grid[query_top + dr][sep2 + 1 + query_left + dc] = query_color
    for dr, dc in offsets:
        grid[before_top + dr][sep1 + 1 + before_left + dc] = 8
    return grid


def _well_formed_grid(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def _split_panels(grid: Sequence[Sequence[int]]):
    panel_w = (len(grid[0]) - 2) // 3
    sep1, sep2 = panel_w, 2 * panel_w + 1
    starts = (0, sep1 + 1, sep2 + 1)
    panels = tuple(
        [[*row[start:start + panel_w]] for row in grid]
        for start in starts
    )
    return panels, panel_w, sep1, sep2


def _object_points(panel: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 8)
    }


def _bbox_top(points: Iterable[tuple[int, int]]) -> tuple[int, int]:
    pts = list(points)
    if not pts:
        raise ValueError("object is empty")
    return min(r for r, _ in pts), min(c for _, c in pts)


def _normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    pts = set(points)
    top, left = _bbox_top(pts)
    return frozenset((r - top, c - left) for r, c in pts)


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not _well_formed_grid(grid):
        return {"errors": ["expected a nonempty rectangular integer-color grid"]}
    height, width = len(grid), len(grid[0])
    if (width - 2) % 3:
        return {"errors": ["grid must split into three equal panels plus two separators"]}
    panels, panel_w, sep1, sep2 = _split_panels(grid)
    before, after, query = panels
    if not (_PANEL_H[0] <= height <= _PANEL_H[-1]):
        errors.append(f"panel_h={height} outside {_PANEL_H[0]}..{_PANEL_H[-1]}")
    if not (_PANEL_W[0] <= panel_w <= _PANEL_W[-1]):
        errors.append(f"panel_w={panel_w} outside {_PANEL_W[0]}..{_PANEL_W[-1]}")
    if not all(row[sep1] == 5 and row[sep2] == 5 for row in grid):
        errors.append("separator columns must be color 5")

    before_points = _object_points(before)
    after_points = _object_points(after)
    query_points = _object_points(query)
    if not before_points:
        errors.append("before panel must contain an object")
    if not query_points:
        errors.append("query panel must contain an object")
    if errors and (not before_points or not query_points):
        return {"errors": errors}

    before_colors = {before[r][c] for r, c in before_points}
    query_colors = {query[r][c] for r, c in query_points}
    if len(before_colors) != 1:
        errors.append("before object must use exactly one color")
    if len(query_colors) != 1:
        errors.append("query object must use exactly one color")
    if not _connected(before_points):
        errors.append("before object must be 4-connected")
    if not _connected(query_points):
        errors.append("query object must be 4-connected")
    if not (3 <= len(before_points) <= 6):
        errors.append("before object size must be 3..6")
    if not (3 <= len(query_points) <= 6):
        errors.append("query object size must be 3..6")

    for r in range(height):
        for c in range(panel_w):
            b0, b1 = before[r][c], after[r][c]
            if b0 == 8:
                errors.append("before panel may not contain color 8")
                break
            if b0 not in (0, 8) and b1 != b0:
                errors.append("after panel must preserve every before-object cell")
                break
            if b0 == 0 and b1 not in (0, 8):
                errors.append("after panel may differ from before only by added color-8 cells")
                break
        if errors and errors[-1].startswith("after panel"):
            break
    if after_points != before_points:
        errors.append("after non-8 object cells must equal before object cells")

    additions = {
        (r, c)
        for r, row in enumerate(after)
        for c, value in enumerate(row)
        if value == 8 and before[r][c] == 0
    }
    if not (1 <= len(additions) <= 4):
        errors.append("after panel must add exactly 1..4 color-8 cells")
    if any(value == 8 for row in query for value in row):
        errors.append("query panel must not contain color 8 before transfer")

    before_top = _bbox_top(before_points)
    query_top = _bbox_top(query_points)
    offsets = {
        (r - before_top[0], c - before_top[1])
        for r, c in additions
    }
    target_points = {
        (query_top[0] + dr, query_top[1] + dc)
        for dr, dc in offsets
    }
    if any(not (0 <= r < height and 0 <= c < panel_w) for r, c in target_points):
        errors.append("all transferred offsets must land in query bounds")
    if before_top == query_top:
        errors.append("before and query bbox anchors must differ")
    before_shape = _normalize(before_points)
    query_shape = _normalize(query_points)
    if before_shape == query_shape and before_colors == query_colors:
        errors.append("query object must differ from the before object in color or geometry")

    palette_kind = "separator_shared" if before_colors == {5} else "distinct"
    if palette_kind == "distinct" and before_colors & query_colors:
        errors.append("distinct palette requires different before/query colors")
    relation = "overwrite" if target_points & query_points else "clear"
    return {
        "errors": errors,
        "panels": panels,
        "panel_h": height,
        "panel_w": panel_w,
        "before_points": before_points,
        "after_points": after_points,
        "query_points": query_points,
        "before_top": before_top,
        "query_top": query_top,
        "before_shape": before_shape,
        "query_shape": query_shape,
        "before_colors": before_colors,
        "query_colors": query_colors,
        "additions": additions,
        "offsets": offsets,
        "target_points": target_points,
        "palette_kind": palette_kind,
        "offset_relation": relation,
    }


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    """The declared sampler manifold; all ordinary generated draws must pass."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid generated grid: " + "; ".join(info["errors"]))
    return {
        "panel_h": info["panel_h"],
        "panel_w": info["panel_w"],
        "shape_size_ab": len(info["before_points"]),
        "shape_size_c": len(info["query_points"]),
        "n_diff": len(info["additions"]),
        "palette_kind": info["palette_kind"],
        "offset_relation": info["offset_relation"],
    }


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; selected Racket remains label authority."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("invalid input: " + "; ".join(info["errors"]))
    query = info["panels"][2]
    out = copy.deepcopy(query)
    for row, col in info["target_points"]:
        out[row][col] = 8
    return out


def _safe_info(grid: Any) -> dict[str, Any] | None:
    try:
        info = _analysis(grid)
    except Exception:
        return None
    return None if info.get("errors") else info


def _copy_query(grid):
    info = _safe_info(grid)
    return copy.deepcopy(info["panels"][2]) if info else []


def _copy_after_panel(grid):
    info = _safe_info(grid)
    return copy.deepcopy(info["panels"][1]) if info else []


def _absolute_8_positions(grid):
    """Rival: copy B's 8 cells at panel-local absolute coordinates."""
    info = _safe_info(grid)
    if not info:
        return []
    out = copy.deepcopy(info["panels"][2])
    for row, col in info["additions"]:
        out[row][col] = 8
    return out


def _skip_occupied_query(grid):
    """Rival: transfer offsets only onto query background, never overwrite."""
    info = _safe_info(grid)
    if not info:
        return []
    out = copy.deepcopy(info["panels"][2])
    for row, col in info["target_points"]:
        if out[row][col] == 0:
            out[row][col] = 8
    return out


def _witness(predicate):
    def wrapped(grid):
        info = _safe_info(grid)
        return bool(info is not None and predicate(info))
    return wrapped


SEMANTIC_RIVALS = {
    "copy_query": _copy_query,
    "copy_after_panel": _copy_after_panel,
    "absolute_8_positions": _absolute_8_positions,
    "skip_occupied_query": _skip_occupied_query,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# The public canonical pairs never place a transferred 8 on an occupied query
# cell, so this plausible but wrong shortcut needs a generated counterexample.
CANONICAL_SHORTCUTS = {"skip_occupied_query": _skip_occupied_query}

SEMANTIC_WITNESSES = {
    "nontrivial_stencil": _witness(lambda info: bool(info["additions"])),
    "translated_bbox": _witness(lambda info: info["before_top"] != info["query_top"]),
    "query_differs_from_after": _witness(
        lambda info: info["before_shape"] != info["query_shape"]
        or info["before_colors"] != info["query_colors"]
    ),
    "overwrites_query_object": _witness(
        lambda info: bool(info["target_points"] & info["query_points"])
    ),
}
WITNESS_RIVALS = {
    "nontrivial_stencil": ["copy_query"],
    "translated_bbox": ["absolute_8_positions"],
    "query_differs_from_after": ["copy_after_panel"],
    "overwrites_query_object": ["skip_occupied_query"],
}


def _strict_grid_equal(left: Any, right: Any) -> bool:
    return _well_formed_grid(left) and _well_formed_grid(right) and [list(r) for r in left] == [list(r) for r in right]


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when four demonstrations leave a named rival alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    pairs = list(demos) + [query]
    reasons: list[str] = []
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        if not _well_formed_grid(pair["input"]):
            reasons.append(f"pair {index} has a malformed input grid")
            continue
        if not _well_formed_grid(pair["output"]):
            reasons.append(f"pair {index} has a malformed output grid")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"pair {index} has an invalid input: {exc}")
            continue
        if not _strict_grid_equal(expected, pair["output"]):
            reasons.append(f"pair {index} disagrees with the additive-stencil rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            _strict_grid_equal(competitor(pair["input"]), pair["output"])
            for pair in demos
        )
        if survives and not _strict_grid_equal(
            competitor(query["input"]), query["output"]
        ):
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
