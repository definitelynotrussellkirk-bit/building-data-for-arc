"""Generator for ARC task 78e78cff / 30d3af94d21e.

A singleton color is the fill seed.  The other non-background color supplies
scanline markers.  On every marker row, the nearest marker strictly left of
the seed column and the nearest marker at-or-right of it bound a fill interval;
a missing side means the grid edge.  Unmarked rows between the first and last
marker rows fill completely, while rows above/below inherit the first/last
marker interval.  Marker cells are preserved.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "30d3af94d21e"
TASK_ID = "30d3af94d21e"
VERSION = "2.0.0"
RULE_HASH = "f03fe4970d9d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

SPAN_KINDS = ("bounded", "left_open", "right_open")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")

SUMMARY = (
    "Find the unique singleton non-background color and use its column as the "
    "scanline reference.  The other non-background color marks row boundaries. "
    "On a marker row, fill between the nearest marker strictly left of the seed "
    "column and the nearest marker at-or-right of it; a missing side opens to "
    "the grid edge.  Rows strictly between the first and last marker rows that "
    "have no markers fill edge-to-edge.  Rows above/below inherit the first/last "
    "marker-row interval.  Preserve all marker cells."
)

INVARIANTS = [
    "the grid has exactly three colors and a unique nonzero modal background",
    "exactly one non-background cell is the fill seed",
    "the remaining non-background color forms at least two marker rows",
    "marker rows may be bounded, left-open, or right-open relative to the seed column",
    "the first and last marker rows are interior and leave at least one unmarked row between them",
    "outer marker distractors do not change the nearest-marker interval",
    "the canonical rule changes at least one background cell and preserves every marker",
]

AXES = {
    "height": {
        "type": "int",
        "default": "sample-index schedule with canonical 11/12 profiles",
        "valid": "9..14",
    },
    "width": {
        "type": "int",
        "default": "sample-index schedule with canonical 11/12 profiles",
        "valid": "9..14",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(PALETTE_KINDS),
    },
    "top_span_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(SPAN_KINDS),
    },
    "bottom_span_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "|".join(SPAN_KINDS),
    },
    "marker_row_count": {
        "type": "int",
        "default": "sample-index schedule",
        "valid": "2..6",
    },
    "seed_on_marker_row": {
        "type": "bool",
        "default": "sample-index schedule",
        "valid": "true|false",
    },
    "asymmetry_force": {
        "type": "bool",
        "default": "sample-index schedule",
        "valid": "true|false",
    },
}

# Four consecutive sample indices form an intentionally identifiable lesson:
# bounded/symmetric, opposite open sides, mixed open/bounded with a marker on
# the seed column, then bounded/asymmetric.  The remaining two profiles expose
# symmetric one-sided edge openings.
_PROFILE_SIZES = (
    (11, 11),
    (11, 12),
    (12, 12),
    (11, 12),
    (10, 13),
    (13, 10),
)
_PROFILE_SPANS = (
    ("bounded", "bounded", False),
    ("left_open", "right_open", True),
    ("right_open", "bounded", True),
    ("bounded", "bounded", True),
    ("left_open", "left_open", False),
    ("right_open", "right_open", False),
)
_MARKER_COUNT_SCHEDULE = (4, 4, 6, 3, 2, 5)
_SEED_ON_SCHEDULE = (False, True, False, True, False, True)
_PALETTE_SCHEDULE = ("broad", "primary", "warm", "cool", "primary", "broad")


def _scheduled_int(ctx, label: str, value: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, value, value)


def _scheduled_choice(ctx, label: str, value: Any, options: tuple[Any, ...]) -> Any:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (value,))


def _scheduled_bool(ctx, label: str, value: bool) -> bool:
    return bool(_scheduled_choice(ctx, label, bool(value), (False, True)))


def _default_size(profile: int, difficulty: str | None) -> tuple[int, int]:
    if profile < 4:
        return _PROFILE_SIZES[profile]
    if profile == 4:
        return {
            "easy": (9, 10),
            "hard": (13, 14),
        }.get(difficulty, _PROFILE_SIZES[profile])
    return {
        "easy": (10, 9),
        "hard": (14, 13),
    }.get(difficulty, _PROFILE_SIZES[profile])


def _resolve_span_axes(ctx, profile: int) -> tuple[str, str, bool]:
    default_top, default_bottom, default_asym = _PROFILE_SPANS[profile]
    top_override = ctx.overrides.get("top_span_kind")
    bottom_override = ctx.overrides.get("bottom_span_kind")
    asym_override = ctx.overrides.get("asymmetry_force")

    if asym_override is not None:
        asymmetry = _scheduled_bool(ctx, "asymmetry_force", bool(asym_override))
    elif top_override is not None and bottom_override is not None:
        # Different kinds are necessarily asymmetric.  Equal kinds follow the
        # scheduled width-asymmetry branch for this profile.
        inferred = str(top_override) != str(bottom_override) or default_asym
        asymmetry = _scheduled_bool(ctx, "asymmetry_force", inferred)
    else:
        asymmetry = _scheduled_bool(ctx, "asymmetry_force", default_asym)

    if top_override is not None:
        top_kind = ctx.draw_choice("top_span_kind", SPAN_KINDS)
    elif bottom_override is not None and not asymmetry:
        top_kind = ctx.draw_choice("top_span_kind", (str(bottom_override),))
    else:
        top_kind = ctx.draw_choice("top_span_kind", (default_top,))

    if bottom_override is not None:
        bottom_kind = ctx.draw_choice("bottom_span_kind", SPAN_KINDS)
    elif not asymmetry:
        bottom_kind = ctx.draw_choice("bottom_span_kind", (top_kind,))
    else:
        bottom_kind = ctx.draw_choice("bottom_span_kind", (default_bottom,))

    if not asymmetry and top_kind != bottom_kind:
        raise ValueError(
            "asymmetry_force=false requires identical top_span_kind and "
            "bottom_span_kind"
        )
    return str(top_kind), str(bottom_kind), asymmetry


def _build_palette(kind: str, rng) -> tuple[int, int, int]:
    pools = {
        "warm": [2, 3, 4, 6, 9],
        "cool": [1, 5, 7, 8, 9],
        "primary": [1, 2, 3, 4, 8],
        "broad": list(range(10)),
    }
    pool = list(pools[kind])
    # The authoritative Racket rule calls `(mode g)`.  In this repository that
    # primitive reserves color 0 as its ignored background argument, so a scene
    # whose modal canvas is 0 is misread even though the visual pattern is
    # otherwise lawful.  Canonical demonstrations all use a nonzero canvas.
    background = rng.choice([color for color in pool if color != 0])
    remaining = [color for color in pool if color != background]
    rng.shuffle(remaining)
    return background, remaining[0], remaining[1]


def _interval_candidates(
    kind: str,
    width: int,
    seed_col: int,
    *,
    require_seed: bool = False,
    require_outer_room: bool = False,
) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    if kind == "bounded":
        for left_marker in range(0, seed_col):
            for right_marker in range(seed_col, width):
                a, b = left_marker + 1, right_marker - 1
                if a > b:
                    continue
                if require_seed and not (a <= seed_col <= b):
                    continue
                if require_outer_room and not (
                    left_marker > 0 or right_marker < width - 1
                ):
                    continue
                result.append((a, b))
    elif kind == "left_open":
        for right_marker in range(seed_col, width):
            a, b = 0, right_marker - 1
            if a > b:
                continue
            if require_seed and not (a <= seed_col <= b):
                continue
            if require_outer_room and right_marker >= width - 1:
                continue
            result.append((a, b))
    elif kind == "right_open":
        for left_marker in range(0, seed_col):
            a, b = left_marker + 1, width - 1
            if require_seed and not (a <= seed_col <= b):
                continue
            if require_outer_room and left_marker <= 0:
                continue
            result.append((a, b))
    else:  # defensive; draw_choice already validates normal generation
        raise ValueError(f"unknown span kind: {kind}")
    return sorted(set(result))


def _pick_interval(
    kind: str,
    width: int,
    seed_col: int,
    rng,
    *,
    require_seed: bool = False,
    require_outer_room: bool = False,
    avoid: tuple[int, int] | None = None,
    prefer_right_marker_at_seed: bool = False,
) -> tuple[int, int]:
    candidates = _interval_candidates(
        kind,
        width,
        seed_col,
        require_seed=require_seed,
        require_outer_room=require_outer_room,
    )
    if avoid is not None:
        alternatives = [span for span in candidates if span != avoid]
        if alternatives:
            candidates = alternatives
    if prefer_right_marker_at_seed and kind in ("bounded", "left_open"):
        special = [span for span in candidates if span[1] == seed_col - 1]
        if special:
            candidates = special
    if not candidates:
        raise ValueError(
            f"no feasible {kind} interval for width={width}, seed_col={seed_col}"
        )
    # Prefer medium-width intervals, then use keyed randomness inside that band.
    ranked = sorted(candidates, key=lambda ab: (abs((ab[1] - ab[0] + 1) - 4), ab))
    pool = ranked[: max(1, min(len(ranked), 6))]
    return rng.choice(pool)


def _boundary_markers(kind: str, span: tuple[int, int], width: int) -> list[int]:
    a, b = span
    if kind == "bounded":
        return [a - 1, b + 1]
    if kind == "left_open":
        return [b + 1]
    if kind == "right_open":
        return [a - 1]
    raise ValueError(f"unknown span kind: {kind}")


def _markers_for_span(
    kind: str,
    span: tuple[int, int],
    width: int,
    rng,
    *,
    add_outer: bool,
) -> list[int]:
    markers = _boundary_markers(kind, span, width)
    if not add_outer:
        return sorted(markers)

    if kind == "bounded":
        left, right = markers
        outer = list(range(0, left)) + list(range(right + 1, width))
    elif kind == "left_open":
        right = markers[0]
        outer = list(range(right + 1, width))
    else:
        left = markers[0]
        outer = list(range(0, left))
    if outer:
        markers.append(rng.choice(outer))
    return sorted(set(markers))


def _choose_marker_rows(height: int, count: int, rng) -> list[int]:
    if count >= 4:
        top, bottom = 1, height - 2
    else:
        top = 1 + rng.randint(0, 1)
        bottom = height - 2 - rng.randint(0, 1)
        if bottom - top + 1 < count + 1:
            top, bottom = 1, height - 2
    interior = list(range(top + 1, bottom))
    if len(interior) < count - 1:
        raise ValueError(
            f"height={height} cannot place {count} marker rows with an interior gap"
        )
    rng.shuffle(interior)
    middle = sorted(interior[: count - 2])
    rows = [top, *middle, bottom]
    if len(set(range(top + 1, bottom)) - set(middle)) < 1:
        raise ValueError("marker rows must leave an unmarked interior row")
    return rows


def _span_kind_from_markers(markers: list[int], seed_col: int) -> str:
    has_left = any(c < seed_col for c in markers)
    has_right = any(c >= seed_col for c in markers)
    if has_left and has_right:
        return "bounded"
    if has_right:
        return "left_open"
    return "right_open"


def _interval_from_markers(markers: list[int], seed_col: int, width: int) -> tuple[int, int]:
    lefts = [c for c in markers if c < seed_col]
    rights = [c for c in markers if c >= seed_col]
    left = max(lefts) if lefts else -1
    right = min(rights) if rights else width
    return left + 1, right - 1


def _rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        raise ValueError("invalid grid for rule mirror: " + "; ".join(errors))
    h, w = facts["height"], facts["width"]
    bg, fill, mark = facts["background"], facts["fill"], facts["marker"]
    marker_rows = facts["marker_rows"]
    row_markers = facts["row_markers"]
    min_row, max_row = marker_rows[0], marker_rows[-1]
    first_span = _interval_from_markers(row_markers[min_row], facts["seed_col"], w)
    last_span = _interval_from_markers(row_markers[max_row], facts["seed_col"], w)

    out = deepcopy(grid)
    for r in range(h):
        if row_markers[r]:
            a, b = _interval_from_markers(row_markers[r], facts["seed_col"], w)
        elif min_row < r < max_row:
            a, b = 0, w - 1
        elif r < min_row:
            a, b = first_span
        else:
            a, b = last_span
        for c in range(w):
            if a <= c <= b and grid[r][c] in (bg, fill):
                out[r][c] = fill
            elif grid[r][c] == mark:
                out[r][c] = mark
    return out


def _analyze(grid: Any, *, apply_rule: bool = True) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return facts, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular and non-empty"]
    height = len(grid)
    if not (6 <= height <= 30 and 6 <= width <= 30):
        errors.append(f"grid size {height}x{width} lies outside 6..30")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not (0 <= value <= 9)
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
        return facts, errors

    counts = Counter(value for row in grid for value in row)
    facts.update(height=height, width=width, counts=dict(counts))
    if len(counts) != 3:
        errors.append(f"expected exactly three colors, got {sorted(counts)}")
        return facts, errors
    ordered = counts.most_common()
    if len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        errors.append("background must be the unique modal color")
        return facts, errors
    background = ordered[0][0]
    if background == 0:
        errors.append(
            "modal background must be nonzero because the canonical Racket "
            "mode primitive ignores color 0"
        )
        return facts, errors
    non_background = [color for color in counts if color != background]
    singleton = [color for color in non_background if counts[color] == 1]
    if len(singleton) != 1:
        errors.append(f"expected one singleton fill color, got {singleton}")
        return facts, errors
    fill = singleton[0]
    marker = next(color for color in non_background if color != fill)
    if counts[marker] < 4:
        errors.append(f"expected at least four marker cells, got {counts[marker]}")

    seed = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == fill
    )
    seed_row, seed_col = seed
    row_markers = {
        r: [c for c, value in enumerate(grid[r]) if value == marker]
        for r in range(height)
    }
    marker_rows = [r for r in range(height) if row_markers[r]]
    if len(marker_rows) < 2:
        errors.append(f"expected at least two marker rows, got {marker_rows}")
        return facts, errors
    if marker_rows[0] == 0 or marker_rows[-1] == height - 1:
        errors.append("first and last marker rows must be interior")
    if not any(not row_markers[r] for r in range(marker_rows[0] + 1, marker_rows[-1])):
        errors.append("marker rows leave no unmarked row strictly between their extremes")
    if not (1 <= seed_col <= width - 2):
        errors.append("seed column must be interior")

    spans = {
        r: _interval_from_markers(row_markers[r], seed_col, width)
        for r in marker_rows
    }
    if any(a > b for a, b in spans.values()):
        errors.append("a marker row induces an empty nearest-marker interval")

    top_row, bottom_row = marker_rows[0], marker_rows[-1]
    top_kind = _span_kind_from_markers(row_markers[top_row], seed_col)
    bottom_kind = _span_kind_from_markers(row_markers[bottom_row], seed_col)
    facts.update(
        background=background,
        fill=fill,
        marker=marker,
        seed=seed,
        seed_row=seed_row,
        seed_col=seed_col,
        row_markers=row_markers,
        marker_rows=marker_rows,
        marker_row_count=len(marker_rows),
        spans=spans,
        top_span=spans[top_row],
        bottom_span=spans[bottom_row],
        top_span_kind=top_kind,
        bottom_span_kind=bottom_kind,
        seed_on_marker_row=bool(row_markers[seed_row]),
        asymmetry_force=spans[top_row] != spans[bottom_row],
        has_left_open=any(
            _span_kind_from_markers(row_markers[r], seed_col) == "left_open"
            for r in marker_rows
        ),
        has_right_open=any(
            _span_kind_from_markers(row_markers[r], seed_col) == "right_open"
            for r in marker_rows
        ),
        has_bounded=any(
            _span_kind_from_markers(row_markers[r], seed_col) == "bounded"
            for r in marker_rows
        ),
        has_single_marker_row=any(len(row_markers[r]) == 1 for r in marker_rows),
        has_outer_distractor=any(
            len(row_markers[r]) > len(_boundary_markers(
                _span_kind_from_markers(row_markers[r], seed_col),
                spans[r],
                width,
            ))
            for r in marker_rows
        ),
        marker_on_seed_column=any(seed_col in row_markers[r] for r in marker_rows),
    )

    if apply_rule and not errors:
        out = _rule_mirror(grid)
        changed = sum(
            grid[r][c] != out[r][c]
            for r in range(height)
            for c in range(width)
        )
        facts["changed_cells"] = changed
        if changed == 0:
            errors.append("canonical rule produces an identity output")
        if any(
            out[r][c] != marker
            for r in marker_rows
            for c in row_markers[r]
        ):
            errors.append("canonical rule does not preserve all markers")
        if sum(value == fill for row in out for value in row) <= 1:
            errors.append("fill seed does not expand")
    return facts, errors


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = sample_index % len(_PROFILE_SIZES)
    default_h, default_w = _default_size(profile, difficulty)
    height = _scheduled_int(ctx, "height", default_h, 9, 14)
    width = _scheduled_int(ctx, "width", default_w, 9, 14)
    palette_kind = str(_scheduled_choice(
        ctx,
        "palette_kind",
        _PALETTE_SCHEDULE[profile],
        PALETTE_KINDS,
    ))
    marker_row_count = _scheduled_int(
        ctx,
        "marker_row_count",
        _MARKER_COUNT_SCHEDULE[profile],
        2,
        6,
    )
    seed_on_marker_row = _scheduled_bool(
        ctx,
        "seed_on_marker_row",
        _SEED_ON_SCHEDULE[profile],
    )
    top_kind, bottom_kind, asymmetry = _resolve_span_axes(ctx, profile)

    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    background, fill, marker = _build_palette(palette_kind, palette_rng)
    grid = full_grid(height, width, background)
    seed_col = layout_rng.randint(2, width - 3)
    marker_rows = _choose_marker_rows(height, marker_row_count, layout_rng)

    # A seed placed on the top marker row needs that row's interval to include
    # the seed column; other profiles may deliberately place a marker at the
    # seed column to exercise the canonical >= right-bucket boundary.
    top_span = _pick_interval(
        top_kind,
        width,
        seed_col,
        layout_rng,
        require_seed=seed_on_marker_row,
        require_outer_room=True,
    )
    if asymmetry:
        bottom_span = _pick_interval(
            bottom_kind,
            width,
            seed_col,
            layout_rng,
            require_outer_room=True,
            avoid=top_span if bottom_kind == top_kind else None,
            prefer_right_marker_at_seed=(profile in (2, 3)),
        )
    else:
        bottom_span = top_span

    row_spans: dict[int, tuple[str, tuple[int, int]]] = {
        marker_rows[0]: (top_kind, top_span),
        marker_rows[-1]: (bottom_kind, bottom_span),
    }
    middle_kind_cycle = ("bounded", "left_open", "right_open")
    for index, row in enumerate(marker_rows[1:-1], 1):
        kind = middle_kind_cycle[(profile + index) % len(middle_kind_cycle)]
        prefer_seed_boundary = profile == 2 and index == 1
        span = _pick_interval(
            kind,
            width,
            seed_col,
            layout_rng,
            require_outer_room=False,
            prefer_right_marker_at_seed=prefer_seed_boundary,
        )
        row_spans[row] = (kind, span)

    for index, row in enumerate(marker_rows):
        kind, span = row_spans[row]
        # Top and bottom rows always carry enough outer evidence that a
        # two-row all-open scene still has >=4 markers.  Alternating middle
        # rows remain single-marker witnesses when their side is open.
        add_outer = row in (marker_rows[0], marker_rows[-1]) or index % 2 == 0
        cols = _markers_for_span(
            kind,
            span,
            width,
            layout_rng,
            add_outer=add_outer,
        )
        for col in cols:
            grid[row][col] = marker

    if seed_on_marker_row:
        seed_row = marker_rows[0]
        if grid[seed_row][seed_col] == marker:
            raise ValueError("selected seed-on-marker profile placed a marker on the seed cell")
    else:
        top_row, bottom_row = marker_rows[0], marker_rows[-1]
        role = profile % 3
        candidates: list[int]
        if role == 1:
            candidates = [r for r in range(0, top_row) if not row_spans.get(r)]
        elif role == 2:
            candidates = [r for r in range(bottom_row + 1, height) if not row_spans.get(r)]
        else:
            candidates = [
                r for r in range(top_row + 1, bottom_row)
                if r not in row_spans
            ]
        if not candidates:
            candidates = [r for r in range(height) if r not in row_spans]
        seed_row = layout_rng.choice(candidates)
    grid[seed_row][seed_col] = fill

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or semantically degenerate instances."""
    del difficulty, meta
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict[str, int | bool | str]:
    """Recover every exact semantic axis represented in the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "top_span_kind": str(facts["top_span_kind"]),
        "bottom_span_kind": str(facts["bottom_span_kind"]),
        "marker_row_count": int(facts["marker_row_count"]),
        "seed_on_marker_row": bool(facts["seed_on_marker_row"]),
        "asymmetry_force": bool(facts["asymmetry_force"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a scene falls outside the task-linked manifold."""
    facts, errors = _analyze(grid)
    reasons = list(errors)
    if errors:
        return reasons
    h, w = facts["height"], facts["width"]
    if not (9 <= h <= 14 and 9 <= w <= 14):
        reasons.append(f"size {h}x{w} is outside the 9..14 teaching envelope")
    if not (2 <= facts["marker_row_count"] <= 6):
        reasons.append("marker-row count is outside 2..6")
    marker_count = facts["counts"][facts["marker"]]
    if not (4 <= marker_count <= 24):
        reasons.append(f"marker count {marker_count} is outside 4..24")
    if facts.get("changed_cells", 0) < 5:
        reasons.append("too few cells change to identify interval propagation")
    if len(set(facts["spans"].values())) < 1:
        reasons.append("no marker-row span is available")
    return reasons


def _witness(name: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid) -> bool:
        facts, errors = _analyze(grid)
        if errors:
            return False
        return bool(facts[name])
    return predicate


SEMANTIC_WITNESSES = {
    "bounded_marker_interval": _witness("has_bounded"),
    "left_open_to_grid_edge": _witness("has_left_open"),
    "right_open_to_grid_edge": _witness("has_right_open"),
    "seed_on_marker_row": _witness("seed_on_marker_row"),
    "seed_off_marker_row": lambda grid: not bool(_analyze(grid)[0].get("seed_on_marker_row"))
    if not _analyze(grid)[1] else False,
    "single_marker_row": _witness("has_single_marker_row"),
    "outer_marker_distractor": _witness("has_outer_distractor"),
    "marker_at_seed_column_uses_right_bucket": _witness("marker_on_seed_column"),
    "top_bottom_interval_asymmetry": _witness("asymmetry_force"),
}


def _rival_outermost_markers(grid):
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    h, w = facts["height"], facts["width"]
    bg, fill = facts["background"], facts["fill"]
    rows = facts["marker_rows"]
    row_markers = facts["row_markers"]
    top, bottom = rows[0], rows[-1]

    def outer_span(markers):
        lefts = [c for c in markers if c < facts["seed_col"]]
        rights = [c for c in markers if c >= facts["seed_col"]]
        left = min(lefts) if lefts else -1
        right = max(rights) if rights else w
        return left + 1, right - 1

    first, last = outer_span(row_markers[top]), outer_span(row_markers[bottom])
    out = deepcopy(grid)
    for r in range(h):
        if row_markers[r]:
            a, b = outer_span(row_markers[r])
        elif top < r < bottom:
            a, b = 0, w - 1
        elif r < top:
            a, b = first
        else:
            a, b = last
        for c in range(w):
            if a <= c <= b and grid[r][c] in (bg, fill):
                out[r][c] = fill
    return out


def _rival_marker_rows_only(grid):
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    out = deepcopy(grid)
    for r in facts["marker_rows"]:
        a, b = facts["spans"][r]
        for c in range(facts["width"]):
            if a <= c <= b and grid[r][c] in (facts["background"], facts["fill"]):
                out[r][c] = facts["fill"]
    return out


def _rival_vertical_seed_column(grid):
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    out = deepcopy(grid)
    c = facts["seed_col"]
    for r in range(facts["height"]):
        if out[r][c] == facts["background"]:
            out[r][c] = facts["fill"]
    return out


def _rival_full_rectangle(grid):
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    out = deepcopy(grid)
    top, bottom = facts["marker_rows"][0], facts["marker_rows"][-1]
    for r in range(top, bottom + 1):
        for c in range(facts["width"]):
            if grid[r][c] in (facts["background"], facts["fill"]):
                out[r][c] = facts["fill"]
    return out


def _rival_repeat_top_interval(grid):
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    out = deepcopy(grid)
    a, b = facts["top_span"]
    for r in range(facts["height"]):
        for c in range(facts["width"]):
            if a <= c <= b and grid[r][c] in (facts["background"], facts["fill"]):
                out[r][c] = facts["fill"]
    return out


def _rival_strict_right_bucket(grid):
    """Plausible off-by-one rival: right markers must be > seed column."""
    facts, errors = _analyze(grid, apply_rule=False)
    if errors:
        return None
    h, w = facts["height"], facts["width"]
    bg, fill = facts["background"], facts["fill"]
    rows, row_markers = facts["marker_rows"], facts["row_markers"]
    top, bottom = rows[0], rows[-1]

    def span(markers):
        lefts = [c for c in markers if c <= facts["seed_col"]]
        rights = [c for c in markers if c > facts["seed_col"]]
        left = max(lefts) if lefts else -1
        right = min(rights) if rights else w
        return left + 1, right - 1

    first, last = span(row_markers[top]), span(row_markers[bottom])
    out = deepcopy(grid)
    for r in range(h):
        if row_markers[r]:
            a, b = span(row_markers[r])
        elif top < r < bottom:
            a, b = 0, w - 1
        elif r < top:
            a, b = first
        else:
            a, b = last
        for c in range(w):
            if a <= c <= b and grid[r][c] in (bg, fill):
                out[r][c] = fill
    return out


_RIVALS = {
    "outermost-rather-than-nearest markers": _rival_outermost_markers,
    "fill marker rows only": _rival_marker_rows_only,
    "fill only the seed column": _rival_vertical_seed_column,
    "fill one rectangle between extreme marker rows": _rival_full_rectangle,
    "repeat the top interval on every row": _rival_repeat_top_interval,
    "classify seed-column markers as left rather than right boundaries": _rival_strict_right_bucket,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival fits demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["no demonstrations supplied"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} lacks input/output")
    if reasons:
        return reasons

    for name, rival in _RIVALS.items():
        consistent = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if consistent and rival(query["input"]) != query["output"]:
            reasons.append(f"rival remains consistent: {name}")
    return reasons
