"""Curriculum generator for ARC task 983d0ea3bd17 (Beacon Cross Rays).

Every red (2) source emits orange (7) rays in the four cardinal directions.
A ray paints only zero-valued cells and stops at the grid edge or at the first
nonzero cell; sources and blockers are preserved.

The public examples contain only red sources on black backgrounds.  Several
wrong rules therefore fit every canonical pair: rays can be allowed to pass
through obstacles, a solver can special-case one obstacle color, every nonzero
cell can be treated as an emitter, or aligned sources can be deduplicated.
Every three-sample teaching window contains two canonical-like anchors and one
structured two-color probe that refutes those shortcuts independently.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "983d0ea3bd17"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "fd605125c9f8"
SUMMARY = (
    "Two or three red sources emit orange cardinal rays through zeros; every "
    "three-sample lesson includes a two-color obstacle probe showing that "
    "rays stop at every nonzero cell and only red cells emit."
)

SOURCE_COLOR = 2
RAY_COLOR = 7
ANCHOR_BLOCKER_COLOR = 8
SECONDARY_BLOCKER_COLORS = (1, 3, 4, 5, 6, 9)
LAWFUL_BLOCKER_COLORS = (ANCHOR_BLOCKER_COLOR, *SECONDARY_BLOCKER_COLORS)
# Backward-compatible name used by the first review package.
BLOCKER_COLOR = ANCHOR_BLOCKER_COLOR
CARDINAL_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
SCENE_KINDS = (
    "scattered",
    "edge_anchored",
    "row_aligned",
    "col_aligned",
    "blocked",
)
ORDINARY_SCENES = SCENE_KINDS[:-1]
CANONICAL_SHAPES = ((7, 8), (8, 9), (6, 10), (9, 9))

INVARIANTS = [
    "the grid is rectangular with height 6..10 and width 8..12",
    "the background is 0 and every input contains exactly two or three red (2) sources",
    "an input has either no blockers or exactly two differently colored blockers",
    "a blocker probe includes color 8 and a second lawful nonzero color",
    "each blocker independently stops a source ray with a visible zero cell beyond it",
    "blocked probes include both an edge source and a pair of axis-aligned sources",
    "the oracle paints 7 only through input zeros and stops at the first nonzero input cell",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "mostly canonical heights; difficulty-aware exploration",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "mostly canonical widths; difficulty-aware exploration",
        "valid": "8..12",
    },
    "seed_count": {
        "type": "int",
        "default": "balanced 2/3-source teaching schedule",
        "valid": "2..3",
    },
    "scene_kind": {
        "type": "str",
        "default": "canonical anchor / two-color blocker probe schedule",
        "valid": "|".join(SCENE_KINDS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = (
    "canonical_pair",
    "two_color_blocker_probe",
    "canonical_triple",
)

_BAND_RANGES = {
    "easy": ((6, 7), (8, 10)),
    "medium": ((7, 9), (8, 11)),
    "hard": ((8, 10), (9, 12)),
}
_CANONICAL_SHAPES_BY_BAND = {
    "easy": ((7, 8), (6, 10)),
    "medium": CANONICAL_SHAPES,
    "hard": ((8, 9), (9, 9)),
}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    return str(difficulty)


def _normalize_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: value for key, value in overrides.items() if value is not None}
    unknown = sorted(set(normalized) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    return normalized


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic three-slot teaching profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_scene(sample_index: int, profile: str) -> str:
    del sample_index
    if profile == "two_color_blocker_probe":
        return "blocked"
    # Both anchors remain on the exact canonical geometry family.  Explicit
    # overrides still exercise edge/aligned ordinary scenes independently.
    return "scattered"


def _draw_dimensions(
    ctx,
    overrides: dict[str, Any],
    band: str,
    sample_index: int,
) -> tuple[int, int]:
    has_h = "grid_h" in overrides
    has_w = "grid_w" in overrides

    if not has_h and not has_w and sample_index % 5 != 4:
        shapes = _CANONICAL_SHAPES_BY_BAND[band]
        h, w = shapes[(sample_index // 5 + sample_index) % len(shapes)]
        return (
            int(ctx.draw_int("grid_h", h, h)),
            int(ctx.draw_int("grid_w", w, w)),
        )

    (h_lo, h_hi), (w_lo, w_hi) = _BAND_RANGES[band]
    h = int(
        ctx.draw_int("grid_h", 6, 10)
        if has_h
        else ctx.draw_int_diff("grid_h", h_lo, h_hi)
    )
    w = int(
        ctx.draw_int("grid_w", 8, 12)
        if has_w
        else ctx.draw_int_diff("grid_w", w_lo, w_hi)
    )
    return h, w


def _draw_seed_count(
    ctx,
    overrides: dict[str, Any],
    profile: str,
    sample_index: int,
) -> int:
    if "seed_count" in overrides:
        return int(ctx.draw_int("seed_count", 2, 3))
    if profile == "canonical_pair":
        scheduled = 2
    elif profile == "canonical_triple":
        scheduled = 3
    else:
        # The probe alternates pair/triple by schedule cycle.  Across six
        # consecutive samples the source counts are exactly 2,2,3,2,3,3.
        cycle = int(sample_index) // len(SCHEDULE_PROFILES)
        scheduled = 2 + (cycle % 2)
    return int(ctx.draw_int("seed_count", scheduled, scheduled))


def _draw_scene_kind(
    ctx,
    overrides: dict[str, Any],
    sample_index: int,
    profile: str,
) -> str:
    if "scene_kind" in overrides:
        return str(ctx.draw_choice("scene_kind", SCENE_KINDS))
    scheduled = _scheduled_scene(sample_index, profile)
    return str(ctx.draw_choice("scene_kind", (scheduled,)))


def _sample_distinct_rows_cols(
    rows: Sequence[int],
    cols: Sequence[int],
    count: int,
    rng,
) -> list[tuple[int, int]]:
    if count > len(rows) or count > len(cols):
        raise ValueError("not enough distinct rows or columns for requested sources")
    selected_rows = rng.sample(list(rows), count)
    selected_cols = rng.sample(list(cols), count)
    rng.shuffle(selected_cols)
    return list(zip(selected_rows, selected_cols))


def _ordinary_positions(
    h: int,
    w: int,
    count: int,
    scene_kind: str,
    rng,
) -> list[tuple[int, int]]:
    interior_rows = list(range(1, h - 1))
    interior_cols = list(range(1, w - 1))

    if scene_kind == "scattered":
        return _sample_distinct_rows_cols(interior_rows, interior_cols, count, rng)

    if scene_kind == "edge_anchored":
        side = rng.choice(("top", "bottom", "left", "right"))
        if side == "top":
            anchor = (0, rng.choice(interior_cols))
        elif side == "bottom":
            anchor = (h - 1, rng.choice(interior_cols))
        elif side == "left":
            anchor = (rng.choice(interior_rows), 0)
        else:
            anchor = (rng.choice(interior_rows), w - 1)
        remaining_rows = [row for row in interior_rows if row != anchor[0]]
        remaining_cols = [col for col in interior_cols if col != anchor[1]]
        return [
            anchor,
            *_sample_distinct_rows_cols(
                remaining_rows,
                remaining_cols,
                count - 1,
                rng,
            ),
        ]

    if scene_kind == "row_aligned":
        row = rng.choice(interior_rows)
        cols = rng.sample(interior_cols, count)
        return [(row, col) for col in cols]

    if scene_kind == "col_aligned":
        col = rng.choice(interior_cols)
        rows = rng.sample(interior_rows, count)
        return [(row, col) for row in rows]

    raise ValueError(f"ordinary scene builder does not support {scene_kind!r}")


def _choose_extra_blocked_source(
    h: int,
    w: int,
    *,
    forbidden: set[tuple[int, int]],
    forbidden_rows: set[int],
    forbidden_cols: set[int],
    rng,
) -> tuple[int, int]:
    candidates = [
        (row, col)
        for row in range(1, h - 1)
        for col in range(1, w - 1)
        if (row, col) not in forbidden
        and row not in forbidden_rows
        and col not in forbidden_cols
    ]
    rng.shuffle(candidates)
    if not candidates:
        raise AssertionError("could not place third source in blocker probe")
    return candidates[0]


def _blocked_layout(
    h: int,
    w: int,
    count: int,
    rng,
) -> tuple[
    list[tuple[int, int]],
    list[tuple[tuple[int, int], int]],
]:
    """Build a probe with two independent differently colored ray stops.

    The first two sources share an axis, one of them lies on an edge, and each
    source owns a blocker/witness lane.  The optional third source is kept off
    both witness lanes so neither counterexample is accidentally masked.
    """
    if count not in (2, 3):
        raise ValueError(f"blocked source count must be 2 or 3, got {count}")

    secondary_color = rng.choice(SECONDARY_BLOCKER_COLORS)
    blocker_colors = [ANCHOR_BLOCKER_COLOR, secondary_color]
    rng.shuffle(blocker_colors)

    if rng.choice(("row", "col")) == "row":
        delta_row = rng.choice((-1, 1))
        source_row = h - 2 if delta_row < 0 else 1
        edge_col = rng.choice((0, w - 1))
        interior_col = rng.choice(list(range(2, w - 2)))

        sources = [(source_row, edge_col), (source_row, interior_col)]
        blockers = [
            (source_row + 2 * delta_row, edge_col),
            (source_row + 2 * delta_row, interior_col),
        ]
        witnesses = [
            (source_row + 3 * delta_row, edge_col),
            (source_row + 3 * delta_row, interior_col),
        ]
        if count == 3:
            extra = _choose_extra_blocked_source(
                h,
                w,
                forbidden=set(sources + blockers + witnesses),
                forbidden_rows={source_row, blockers[0][0], witnesses[0][0]},
                forbidden_cols={edge_col, interior_col},
                rng=rng,
            )
            sources.append(extra)
    else:
        delta_col = rng.choice((-1, 1))
        source_col = w - 2 if delta_col < 0 else 1
        edge_row = rng.choice((0, h - 1))
        interior_row = rng.choice(list(range(2, h - 2)))

        sources = [(edge_row, source_col), (interior_row, source_col)]
        blockers = [
            (edge_row, source_col + 2 * delta_col),
            (interior_row, source_col + 2 * delta_col),
        ]
        witnesses = [
            (edge_row, source_col + 3 * delta_col),
            (interior_row, source_col + 3 * delta_col),
        ]
        if count == 3:
            extra = _choose_extra_blocked_source(
                h,
                w,
                forbidden=set(sources + blockers + witnesses),
                forbidden_rows={edge_row, interior_row},
                forbidden_cols={source_col, blockers[0][1], witnesses[0][1]},
                rng=rng,
            )
            sources.append(extra)

    return sources, list(zip(blockers, blocker_colors))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = _normalize_overrides(overrides)
    band = _band(difficulty)
    sample_index = int(sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    h, w = _draw_dimensions(ctx, overrides, band, sample_index)
    source_count = _draw_seed_count(ctx, overrides, profile, sample_index)
    scene_kind = _draw_scene_kind(ctx, overrides, sample_index, profile)
    layout_rng = ctx.draw_rng("layout")

    blocker_entries: list[tuple[tuple[int, int], int]] = []
    if scene_kind == "blocked":
        sources, blocker_entries = _blocked_layout(h, w, source_count, layout_rng)
    else:
        sources = _ordinary_positions(h, w, source_count, scene_kind, layout_rng)

    grid = full_grid(h, w, 0)
    for row, col in sources:
        grid[row][col] = SOURCE_COLOR
    for (row, col), color in blocker_entries:
        grid[row][col] = color

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise AssertionError("constructed invalid beacon scene: " + "; ".join(errors))
    return grid


def _rectangular_grid_errors(grid: Any) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty row sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], 0, 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], len(grid), width
    invalid_cells = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if invalid_cells:
        return ["cells must be integer ARC colors in 0..9"], len(grid), width
    return [], len(grid), width


def _positions(grid: Iterable[Iterable[int]], color: int) -> list[tuple[int, int]]:
    return [
        (row_index, col_index)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value == color
    ]


def _blocker_entries(grid: Iterable[Iterable[int]]) -> list[tuple[int, int, int]]:
    return [
        (row_index, col_index, value)
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value not in (0, SOURCE_COLOR)
    ]


def _sources_have_shared_axis(sources: Sequence[tuple[int, int]]) -> bool:
    return (
        len({row for row, _ in sources}) < len(sources)
        or len({col for _, col in sources}) < len(sources)
    )


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors, h, w = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors, "facts": None}

    if not 6 <= h <= 10:
        errors.append(f"grid_h must be in 6..10, got {h}")
    if not 8 <= w <= 12:
        errors.append(f"grid_w must be in 8..12, got {w}")

    lawful_colors = {0, SOURCE_COLOR, *LAWFUL_BLOCKER_COLORS}
    unexpected = sorted({value for row in grid for value in row if value not in lawful_colors})
    if unexpected:
        errors.append(
            f"unexpected input colors: {unexpected}; lawful colors are "
            f"{sorted(lawful_colors)}"
        )

    sources = _positions(grid, SOURCE_COLOR)
    blocker_entries = _blocker_entries(grid)
    blockers = [(row, col) for row, col, _ in blocker_entries]
    blocker_colors = [value for _, _, value in blocker_entries]
    if not 2 <= len(sources) <= 3:
        errors.append(f"expected 2-3 red sources; found {len(sources)}")
    if len(blockers) not in (0, 2):
        errors.append(f"expected zero or two blockers; found {len(blockers)}")
    if not any(value == 0 for row in grid for value in row):
        errors.append("at least one background zero is required")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "sources": sources,
        "blockers": blockers,
        "blocker_entries": blocker_entries,
        "blocker_colors": blocker_colors,
    }
    if errors:
        return {"errors": errors, "facts": facts}

    if blockers:
        colors = set(blocker_colors)
        if len(colors) != 2:
            errors.append("the two blockers must use two distinct colors")
        if ANCHOR_BLOCKER_COLOR not in colors:
            errors.append(
                f"a blocker probe must include anchor color {ANCHOR_BLOCKER_COLOR}"
            )
        if not any(
            row in (0, h - 1) or col in (0, w - 1)
            for row, col in sources
        ):
            errors.append("a blocker probe must include an edge source")
        if not _sources_have_shared_axis(sources):
            errors.append("a blocker probe must include axis-aligned sources")
        for blocker in blockers:
            if not _blocker_is_observable(grid, blocker):
                errors.append(
                    f"blocker at {blocker} has no independently observable stopped ray"
                )
        for rival_name in (
            "paint_through_nonzero",
            "single_blocker_color_only",
            "all_nonzero_cells_emit",
            "dedupe_shared_axis",
        ):
            if not _rival_differs(grid, rival_name):
                errors.append(
                    f"blocker probe does not refute semantic rival {rival_name!r}"
                )
    return {"errors": errors, "facts": facts}


def _classify_scene(facts: dict[str, Any]) -> str:
    sources = facts["sources"]
    h, w = facts["grid_h"], facts["grid_w"]
    if facts["blockers"]:
        return "blocked"
    if len({row for row, _ in sources}) == 1:
        return "row_aligned"
    if len({col for _, col in sources}) == 1:
        return "col_aligned"
    if any(row in (0, h - 1) or col in (0, w - 1) for row, col in sources):
        return "edge_anchored"
    return "scattered"


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analyze_scene(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe invalid beacon scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "seed_count": len(facts["sources"]),
        "scene_kind": _classify_scene(facts),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze_scene(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({axis: meta[axis] for axis in AXES if axis in meta})
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis not in AXES or expected is None:
                continue
            normalized = (
                int(expected)
                if axis in ("grid_h", "grid_w", "seed_count")
                else str(expected)
            )
            if observed[axis] != normalized:
                errors.append(
                    f"override {axis}={normalized!r} was not realized; "
                    f"observed {observed[axis]!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    facts = _analyze_scene(grid)["facts"]
    strict_errors: list[str] = []
    if (facts["grid_h"], facts["grid_w"]) not in CANONICAL_SHAPES:
        strict_errors.append("shape is not one of the four canonical input shapes")
    if facts["blockers"]:
        strict_errors.append("canonical inputs contain no blocker")
    sources = facts["sources"]
    if len({row for row, _ in sources}) != len(sources):
        strict_errors.append("canonical sources occupy distinct rows")
    if len({col for _, col in sources}) != len(sources):
        strict_errors.append("canonical sources occupy distinct columns")
    return strict_errors


def _paint_with_policy(
    grid: Sequence[Sequence[int]],
    sources: Sequence[tuple[int, int]],
    directions: Sequence[tuple[int, int]],
    *,
    should_stop: Callable[[int, int, int], bool],
) -> list[list[int]]:
    errors, h, w = _rectangular_grid_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for start_row, start_col in sources:
        for delta_row, delta_col in directions:
            row = start_row + delta_row
            col = start_col + delta_col
            while 0 <= row < h and 0 <= col < w:
                value = grid[row][col]
                if value != 0:
                    if should_stop(value, row, col):
                        break
                else:
                    out[row][col] = RAY_COLOR
                row += delta_row
                col += delta_col
    return out


def _paint_directions(
    grid: Sequence[Sequence[int]],
    sources: Sequence[tuple[int, int]],
    directions: Sequence[tuple[int, int]],
    *,
    stop_at_nonzero: bool,
) -> list[list[int]]:
    return _paint_with_policy(
        grid,
        sources,
        directions,
        should_stop=(
            (lambda value, row, col: True)
            if stop_at_nonzero
            else (lambda value, row, col: False)
        ),
    )


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Pure Python mirror of the pinned canonical Racket solution."""
    return _paint_directions(
        grid,
        _positions(grid, SOURCE_COLOR),
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _paint_through_nonzero(grid):
    return _paint_directions(
        grid,
        _positions(grid, SOURCE_COLOR),
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=False,
    )


def _single_blocker_color_only(grid):
    """Wrong rule: red sources and color 8 stop rays; other colors do not."""
    return _paint_with_policy(
        grid,
        _positions(grid, SOURCE_COLOR),
        CARDINAL_DIRECTIONS,
        should_stop=lambda value, row, col: value
        in (SOURCE_COLOR, ANCHOR_BLOCKER_COLOR),
    )


def _all_nonzero_cells_emit(grid):
    emitters = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    return _paint_directions(
        grid,
        emitters,
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _dedupe_shared_axis(grid):
    kept: list[tuple[int, int]] = []
    used_rows: set[int] = set()
    used_cols: set[int] = set()
    for row, col in sorted(_positions(grid, SOURCE_COLOR)):
        if row in used_rows or col in used_cols:
            continue
        kept.append((row, col))
        used_rows.add(row)
        used_cols.add(col)
    return _paint_directions(
        grid,
        kept,
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _horizontal_only(grid):
    return _paint_directions(
        grid,
        _positions(grid, SOURCE_COLOR),
        ((0, -1), (0, 1)),
        stop_at_nonzero=True,
    )


def _vertical_only(grid):
    return _paint_directions(
        grid,
        _positions(grid, SOURCE_COLOR),
        ((-1, 0), (1, 0)),
        stop_at_nonzero=True,
    )


def _first_source_only(grid):
    sources = sorted(_positions(grid, SOURCE_COLOR))
    return _paint_directions(
        grid,
        sources[:1],
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _first_two_sources_only(grid):
    sources = sorted(_positions(grid, SOURCE_COLOR))
    return _paint_directions(
        grid,
        sources[:2],
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _interior_sources_only(grid):
    _, h, w = _rectangular_grid_errors(grid)
    sources = [
        (row, col)
        for row, col in _positions(grid, SOURCE_COLOR)
        if row not in (0, h - 1) and col not in (0, w - 1)
    ]
    return _paint_directions(
        grid,
        sources,
        CARDINAL_DIRECTIONS,
        stop_at_nonzero=True,
    )


def _recolor_sources(grid):
    out = rule_mirror(grid)
    for row, col in _positions(grid, SOURCE_COLOR):
        out[row][col] = RAY_COLOR
    return out


def _erase_blockers(grid):
    out = rule_mirror(grid)
    for row, col, _ in _blocker_entries(grid):
        out[row][col] = 0
    return out


def _recolor_blockers_orange(grid):
    out = rule_mirror(grid)
    for row, col, _ in _blocker_entries(grid):
        out[row][col] = RAY_COLOR
    return out


def _ignore_one_blocker(grid, ignored: tuple[int, int]):
    return _paint_with_policy(
        grid,
        _positions(grid, SOURCE_COLOR),
        CARDINAL_DIRECTIONS,
        should_stop=lambda value, row, col: (row, col) != ignored,
    )


def _blocker_is_observable(grid, blocker: tuple[int, int]) -> bool:
    """Whether making only `blocker` transparent changes the answer."""
    return _ignore_one_blocker(grid, blocker) != rule_mirror(grid)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "paint_through_nonzero": _paint_through_nonzero,
    "single_blocker_color_only": _single_blocker_color_only,
    "all_nonzero_cells_emit": _all_nonzero_cells_emit,
    "dedupe_shared_axis": _dedupe_shared_axis,
    "horizontal_rays_only": _horizontal_only,
    "vertical_rays_only": _vertical_only,
    "first_source_only": _first_source_only,
    "first_two_sources_only": _first_two_sources_only,
    "interior_sources_only": _interior_sources_only,
    "recolor_sources_orange": _recolor_sources,
    "erase_blockers": _erase_blockers,
    "recolor_blockers_orange": _recolor_blockers_orange,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "paint_through_nonzero": _paint_through_nonzero,
    "single_blocker_color_only": _single_blocker_color_only,
    "all_nonzero_cells_emit": _all_nonzero_cells_emit,
    "dedupe_shared_axis": _dedupe_shared_axis,
}


def _rival_differs(grid, rival_name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "stops_at_every_nonzero_color": lambda grid: (
        bool(_blocker_entries(grid))
        and _rival_differs(grid, "paint_through_nonzero")
        and _rival_differs(grid, "single_blocker_color_only")
    ),
    "only_red_cells_emit": lambda grid: _rival_differs(
        grid, "all_nonzero_cells_emit"
    ),
    "aligned_sources_remain_independent": lambda grid: _rival_differs(
        grid, "dedupe_shared_axis"
    ),
    "edge_sources_emit": lambda grid: _rival_differs(
        grid, "interior_sources_only"
    ),
    "emits_horizontal_rays": lambda grid: _rival_differs(
        grid, "vertical_rays_only"
    ),
    "emits_vertical_rays": lambda grid: _rival_differs(
        grid, "horizontal_rays_only"
    ),
    "all_sources_emit": lambda grid: _rival_differs(grid, "first_source_only"),
    "third_source_emits": lambda grid: _rival_differs(
        grid, "first_two_sources_only"
    ),
    "red_sources_are_preserved": lambda grid: _rival_differs(
        grid, "recolor_sources_orange"
    ),
    "blockers_are_preserved": lambda grid: (
        bool(_blocker_entries(grid))
        and _rival_differs(grid, "erase_blockers")
        and _rival_differs(grid, "recolor_blockers_orange")
    ),
}
WITNESS_RIVALS = {
    "stops_at_every_nonzero_color": [
        "paint_through_nonzero",
        "single_blocker_color_only",
    ],
    "only_red_cells_emit": ["all_nonzero_cells_emit"],
    "aligned_sources_remain_independent": ["dedupe_shared_axis"],
    "edge_sources_emit": ["interior_sources_only"],
    "emits_horizontal_rays": ["vertical_rays_only"],
    "emits_vertical_rays": ["horizontal_rays_only"],
    "all_sources_emit": ["first_source_only"],
    "third_source_emits": ["first_two_sources_only"],
    "red_sources_are_preserved": ["recolor_sources_orange"],
    "blockers_are_preserved": [
        "erase_blockers",
        "recolor_blockers_orange",
    ],
}


def _validate_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    input_errors = self_check(pair["input"])
    if input_errors:
        return [f"{label} input: {reason}" for reason in input_errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not match the pinned cross-ray rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons for which a named plausible wrong rule still survives."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_pair(demo, f"demo {index}"))
    reasons.extend(_validate_pair(query, "query"))
    if reasons:
        return reasons

    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small malformed scenes that exercise independent validator branches."""
    all_background = full_grid(6, 8, 0)

    one_source = full_grid(6, 8, 0)
    one_source[2][3] = SOURCE_COLOR

    four_sources = full_grid(6, 8, 0)
    for row, col in ((1, 1), (1, 6), (4, 1), (4, 6)):
        four_sources[row][col] = SOURCE_COLOR

    input_contains_7 = full_grid(6, 8, 0)
    input_contains_7[1][1] = SOURCE_COLOR
    input_contains_7[4][6] = SOURCE_COLOR
    input_contains_7[2][2] = RAY_COLOR

    one_blocker = full_grid(6, 8, 0)
    one_blocker[1][0] = SOURCE_COLOR
    one_blocker[1][4] = SOURCE_COLOR
    one_blocker[3][0] = ANCHOR_BLOCKER_COLOR

    same_color_blockers = full_grid(6, 8, 0)
    same_color_blockers[1][0] = SOURCE_COLOR
    same_color_blockers[1][4] = SOURCE_COLOR
    same_color_blockers[3][0] = ANCHOR_BLOCKER_COLOR
    same_color_blockers[3][4] = ANCHOR_BLOCKER_COLOR

    invisible_blockers = full_grid(6, 8, 0)
    invisible_blockers[1][0] = SOURCE_COLOR
    invisible_blockers[1][4] = SOURCE_COLOR
    invisible_blockers[3][2] = ANCHOR_BLOCKER_COLOR
    invisible_blockers[4][6] = SECONDARY_BLOCKER_COLORS[0]

    no_edge_source = full_grid(6, 8, 0)
    no_edge_source[1][1] = SOURCE_COLOR
    no_edge_source[1][4] = SOURCE_COLOR
    no_edge_source[3][1] = ANCHOR_BLOCKER_COLOR
    no_edge_source[3][4] = SECONDARY_BLOCKER_COLORS[0]

    return [
        ("all_background", all_background),
        ("one_source", one_source),
        ("four_sources", four_sources),
        ("input_contains_7", input_contains_7),
        ("one_blocker", one_blocker),
        ("same_color_blockers", same_color_blockers),
        ("invisible_blockers", invisible_blockers),
        ("no_edge_source", no_edge_source),
    ]
