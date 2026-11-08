"""Generate two aligned red markers for the cyan segment-completion rule.

The canonical Racket oracle discards the red marker color, creates a blank grid
of the same shape, and paints the inclusive straight lattice segment between
the two markers cyan (8).  Lawful inputs therefore contain exactly two red (2)
markers aligned horizontally, vertically, or on a 45-degree diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4d80a5dc7716"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "89dfbab7de55"

SUMMARY = (
    "Place exactly two red (2) markers on an otherwise black grid so they are "
    "horizontal, vertical, or 45-degree diagonal endpoints; the rule replaces "
    "them with the full inclusive connecting segment in cyan (8) on a blank "
    "grid of the same size."
)

INVARIANTS = [
    "the input is an 8..12 by 8..12 rectangular ARC grid",
    "the only input colors are background 0 and exactly two red (2) markers",
    "the markers are horizontally, vertically, or 45-degree diagonally aligned",
    "the Chebyshev span between markers is 3..6 cells",
    "the output authority is the canonical Racket rule, which paints the inclusive segment cyan (8)",
]

ORIENTATIONS = ("horizontal", "vertical", "diag_down", "diag_up")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked profile",
        "valid": "8..12",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked profile",
        "valid": "8..12",
        "doc": "Input-grid width.",
    },
    "orientation": {
        "type": "enum",
        "default": "linked profile",
        "valid": ["horizontal", "vertical", "diag_down", "diag_up"],
        "doc": "Alignment of the two red endpoints.",
    },
    "span": {
        "type": "int",
        "default": "linked profile",
        "valid": "3..6",
        "doc": "Chebyshev distance between the endpoints.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

# Each consecutive four-profile block is a complete demonstration curriculum:
# one example per orientation and one per span 3, 4, 5, and 6. Difficulty shifts
# between those blocks, so every band teaches all decisive branches before its
# query while the full cycle broadens dimensions and retains canonical profiles.
_PROFILES = (
    {"grid_h": 8, "grid_w": 8, "orientation": "horizontal", "span": 4},
    {"grid_h": 10, "grid_w": 11, "orientation": "vertical", "span": 3},
    {"grid_h": 11, "grid_w": 10, "orientation": "diag_down", "span": 5},
    {"grid_h": 12, "grid_w": 12, "orientation": "diag_up", "span": 6},
    {"grid_h": 10, "grid_w": 12, "orientation": "horizontal", "span": 6},
    {"grid_h": 9, "grid_w": 9, "orientation": "vertical", "span": 4},
    {"grid_h": 12, "grid_w": 11, "orientation": "diag_down", "span": 5},
    {"grid_h": 11, "grid_w": 9, "orientation": "diag_up", "span": 3},
    {"grid_h": 12, "grid_w": 10, "orientation": "horizontal", "span": 3},
    {"grid_h": 10, "grid_w": 12, "orientation": "vertical", "span": 5},
    {"grid_h": 8, "grid_w": 8, "orientation": "diag_down", "span": 4},
    {"grid_h": 9, "grid_w": 12, "orientation": "diag_up", "span": 6},
)

_CANONICAL_LINKED_KEYS = {
    (8, 8, "horizontal", 4),
    (9, 9, "vertical", 4),
    (8, 8, "diag_down", 4),
}


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use the full declared range for an explicit override, else pin profile."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _endpoint_pair(rng, h: int, w: int, orientation: str, span: int):
    if orientation == "horizontal":
        row = rng.randrange(h)
        col = rng.randint(0, w - span - 1)
        return (row, col), (row, col + span)
    if orientation == "vertical":
        row = rng.randint(0, h - span - 1)
        col = rng.randrange(w)
        return (row, col), (row + span, col)
    if orientation == "diag_down":
        row = rng.randint(0, h - span - 1)
        col = rng.randint(0, w - span - 1)
        return (row, col), (row + span, col + span)
    if orientation == "diag_up":
        row = rng.randint(span, h - 1)
        col = rng.randint(0, w - span - 1)
        return (row, col), (row - span, col + span)
    raise ValueError(f"unsupported orientation {orientation!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; the Racket rule owns the output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    # Difficulty changes the phase of the linked schedule without narrowing the
    # lawful grammar.  Every band still sees every profile over a 12-draw cycle.
    band_offset = {None: 0, "easy": 0, "medium": 4, "hard": 8}[difficulty]
    profile = _PROFILES[(sample_index + band_offset) % len(_PROFILES)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_int_axis(ctx, overrides, "grid_h", profile["grid_h"], 8, 12)
    w = _draw_int_axis(ctx, overrides, "grid_w", profile["grid_w"], 8, 12)
    orientation = _draw_choice_axis(
        ctx, overrides, "orientation", profile["orientation"], ORIENTATIONS
    )
    span = _draw_int_axis(ctx, overrides, "span", profile["span"], 3, 6)

    # The declared minimum dimensions make every orientation/span combination
    # constructible, including the full override boundary matrix.
    if span >= h and orientation in ("vertical", "diag_down", "diag_up"):
        raise ValueError(f"span {span} does not fit height {h}")
    if span >= w and orientation in ("horizontal", "diag_down", "diag_up"):
        raise ValueError(f"span {span} does not fit width {w}")

    grid = full_grid(h, w, 0)
    first, second = _endpoint_pair(
        ctx.draw_rng("placement"), h, w, orientation, span
    )
    grid[first[0]][first[1]] = 2
    grid[second[0]][second[1]] = 2

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analyze(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not 8 <= h <= 12:
        errors.append(f"grid height {h} outside 8..12")
    if not 8 <= w <= 12:
        errors.append(f"grid width {w} outside 8..12")

    bad_colors = sorted({value for row in grid for value in row if value not in (0, 2)})
    if bad_colors:
        errors.append(f"unexpected input colors {bad_colors}; only 0 and 2 are lawful")

    endpoints = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(endpoints) != 2:
        errors.append(f"expected exactly two red endpoints, found {len(endpoints)}")
        return {
            "errors": errors,
            "grid_h": h,
            "grid_w": w,
            "endpoints": endpoints,
        }

    (r1, c1), (r2, c2) = endpoints
    dr, dc = r2 - r1, c2 - c1
    abs_dr, abs_dc = abs(dr), abs(dc)
    orientation = None
    if dr == 0 and dc != 0:
        orientation = "horizontal"
    elif dc == 0 and dr != 0:
        orientation = "vertical"
    elif abs_dr == abs_dc and dr != 0:
        orientation = "diag_down" if dr * dc > 0 else "diag_up"
    else:
        errors.append(
            f"endpoints are not horizontal, vertical, or 45-degree aligned: {endpoints}"
        )

    span = max(abs_dr, abs_dc)
    if not 3 <= span <= 6:
        errors.append(f"endpoint span {span} outside 3..6")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "endpoints": endpoints,
        "orientation": orientation,
        "span": span,
        "touches_edge": any(
            row in (0, h - 1) or col in (0, w - 1) for row, col in endpoints
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, and rule-hiding endpoint scenes."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "orientation": analysis["orientation"],
        "span": analysis["span"],
    }


def semantic_observables(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    key = (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["orientation"],
        analysis["span"],
    )
    return {
        **observe_overrides(grid),
        "canonical_linked_profile": key in _CANONICAL_LINKED_KEYS,
        "touches_edge": analysis["touches_edge"],
        "segment_cells": analysis["span"] + 1,
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    key = (
        analysis["grid_h"],
        analysis["grid_w"],
        analysis["orientation"],
        analysis["span"],
    )
    if key not in _CANONICAL_LINKED_KEYS:
        return [f"linked profile {key!r} is outside the three canonical profiles"]
    return []


def _witness(grid, **expected) -> bool:
    observed = semantic_observables(grid)
    return not observed.get("errors") and all(
        observed.get(key) == value for key, value in expected.items()
    )


SEMANTIC_WITNESSES = {
    "horizontal_segment": lambda grid: _witness(grid, orientation="horizontal"),
    "vertical_segment": lambda grid: _witness(grid, orientation="vertical"),
    "descending_diagonal_segment": lambda grid: _witness(grid, orientation="diag_down"),
    "ascending_diagonal_segment": lambda grid: _witness(grid, orientation="diag_up"),
    "span_3": lambda grid: _witness(grid, span=3),
    "span_4": lambda grid: _witness(grid, span=4),
    "span_5": lambda grid: _witness(grid, span=5),
    "span_6": lambda grid: _witness(grid, span=6),
}


def _segment_cells(grid) -> list[tuple[int, int]]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    first, second = analysis["endpoints"]
    r1, c1 = first
    r2, c2 = second
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    return [(r1 + index * dr, c1 + index * dc) for index in range(analysis["span"] + 1)]


def rule_mirror(grid):
    """Pure Python mirror used only for semantic tests; Racket remains authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for row, col in _segment_cells(grid):
        out[row][col] = 8
    return out


def _endpoints_only(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for row, col in analysis["endpoints"]:
        out[row][col] = 8
    return out


def _preserve_red_endpoints(grid):
    out = rule_mirror(grid)
    for row, col in _analyze(grid)["endpoints"]:
        out[row][col] = 2
    return out


def _paint_red_segment(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for row, col in _segment_cells(grid):
        out[row][col] = 2
    return out


def _bounding_box(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    endpoints = analysis["endpoints"]
    r0, r1 = sorted(row for row, _ in endpoints)
    c0, c1 = sorted(col for _, col in endpoints)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            out[row][col] = 8
    return out


def _axis_aligned_only(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    if analysis["orientation"] in ("horizontal", "vertical"):
        return rule_mirror(grid)
    return _endpoints_only(grid)


def _descending_diagonal_only(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    if analysis["orientation"] != "diag_up":
        return rule_mirror(grid)
    return _endpoints_only(grid)


def _span_four_only(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    if analysis["span"] == 4:
        return rule_mirror(grid)
    return _endpoints_only(grid)


_COMPETITORS = {
    "recolor only the two endpoints": _endpoints_only,
    "fill the segment but preserve red endpoints": _preserve_red_endpoints,
    "draw the segment in the marker color": _paint_red_segment,
    "fill the endpoints' bounding box": _bounding_box,
    "connect only horizontal and vertical markers": _axis_aligned_only,
    "support only descending diagonals": _descending_diagonal_only,
    "apply the rule only at canonical span four": _span_four_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to falsify named shortcuts that change the query answer."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    seen_orientations = set()
    seen_spans = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the inclusive cyan-segment rule")
        observed = observe_overrides(demo["input"])
        seen_orientations.add(observed["orientation"])
        seen_spans.add(observed["span"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    if reasons:
        return reasons

    missing_orientations = sorted(set(ORIENTATIONS) - seen_orientations)
    if missing_orientations:
        reasons.append(f"demonstrations omit orientation branches {missing_orientations}")
    if len(seen_spans) < 4:
        reasons.append(
            f"demonstrations expose only spans {sorted(seen_spans)}; spans 3,4,5,6 are required"
        )

    query_truth = rule_mirror(query["input"])
    for name, competitor in _COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            query_alt = competitor(query["input"])
            if query_alt != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor '{name}', which changes the query answer"
                )
    return reasons
