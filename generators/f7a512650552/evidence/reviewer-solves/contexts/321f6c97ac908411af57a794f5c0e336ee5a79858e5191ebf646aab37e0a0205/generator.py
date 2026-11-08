"""Input generator for the worked-example closure task f7a512650552.

Two full color-5 columns split the input into SOURCE, worked RESULT, and QUERY
panels.  The canonical Racket rule checks whether row-span closure of SOURCE is
exactly RESULT; if so it row-closes QUERY, otherwise it column-closes QUERY.  It
then crops the largest transformed query object and recolors it 8.

The default curriculum alternates row and column modes, periodically emits the
exact canonical 9x23/four-color profile in every difficulty band, and requires
both the worked example and query to distinguish row closure from column
closure.  Query outputs also differ from both the untouched crop and a solid
bounding-box shortcut, two failure modes hidden by the canonical labels.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7a512650552"
TASK_ID = GENERATOR_ID
RULE_HASH = "25622d47ca31"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "Two full color-5 columns form source, worked-result, and query panels. "
    "Infer row-span versus column-span closure from the first two panels, apply "
    "that closure to the query object, crop it, and recolor it orange (8)."
)

INVARIANTS = [
    "exactly two full color-5 separator columns and no other color-5 cells",
    "source and worked-result panels have equal widths and one aligned object",
    "the worked result is exactly one row- or column-span closure of the source",
    "generated worked examples distinguish row closure from column closure",
    "generated query objects distinguish both modes and defeat crop/bbox shortcuts",
    "the input is an ARC-legal grid no larger than 30 by 30",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9 on canonical anchors; otherwise difficulty-shaped 6..20",
        "valid": "6..20",
    },
    "example_w": {
        "type": "int",
        "default": "7 on canonical anchors; otherwise 3..8",
        "valid": "3..8",
    },
    "query_w": {
        "type": "int",
        "default": "7 on canonical anchors; otherwise 3..12",
        "valid": "3..12",
    },
    "mode": {
        "type": "int",
        "default": "alternates by sample index",
        "valid": "0..1",
    },
}
# The maximum advertised width is 2*8 + 2 separators + 12 = 30, and the
# minimum 6x3 panels fit the constructive fallback shapes below.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_SHAPE_COLORS = (1, 2, 3, 4, 6, 7, 9)  # reserve 0, separator 5, output 8
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = (9, 7, 7)  # height, example width, query width -> 9x23
_DIFFICULTY_RANGES = {
    None: ((8, 14), (4, 8), (5, 10)),
    "easy": ((6, 10), (3, 6), (3, 7)),
    "medium": ((8, 15), (4, 8), (5, 10)),
    "hard": ((11, 20), (5, 8), (7, 12)),
}

# A four-pair lesson remains mode-balanced after any one query rotation.
SCHEDULE_PROFILES = (
    ("canonical", 0),
    ("canonical", 1),
    ("broad", 0),
    ("broad", 1),
)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    family = "canonical" if sample_index % 6 in (0, 1) else "broad"
    return family, sample_index % 2


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (6, 20),
        "example_w": (3, 8),
        "query_w": (3, 12),
        "mode": (0, 1),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, name, lo, hi, scheduled):
    options = tuple(range(lo, hi + 1)) if name in ctx.overrides else (scheduled,)
    return ctx.draw_choice(name, options)


def _scheduled_dimensions(ctx, sample_index, difficulty):
    if sample_index % 6 in (0, 1):
        return _CANONICAL_DIMS
    hr, er, qr = _DIFFICULTY_RANGES.get(difficulty, _DIFFICULTY_RANGES[None])
    rng = ctx.draw_rng("broad_dimensions")
    return rng.randint(*hr), rng.randint(*er), rng.randint(*qr)


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    if not cells:
        return cells
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _row_close(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    rows: dict[int, list[int]] = {}
    for r, c in cells:
        rows.setdefault(r, []).append(c)
    out = set(cells)
    for r, cols in rows.items():
        out.update((r, c) for c in range(min(cols), max(cols) + 1))
    return frozenset(out)


def _col_close(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = frozenset(cells)
    cols: dict[int, list[int]] = {}
    for r, c in cells:
        cols.setdefault(c, []).append(r)
    out = set(cells)
    for c, rows in cols.items():
        out.update((r, c) for r in range(min(rows), max(rows) + 1))
    return frozenset(out)


def _solid_bbox(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    h, w = _bbox(cells)
    return frozenset((r, c) for r in range(h) for c in range(w))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = min(remaining)
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == remaining


def _random_polyomino(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(_CARDINAL)
        cells.add((r + dr, c + dc))
    return _normalize(cells)


def _fallback_shape(mode, rng):
    # Connected 3x3 shape. Row closure adds (0,1) but remains non-rectangular;
    # transposition gives the corresponding column-mode witness.
    cells = {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)}
    if mode == 1:
        cells = {(c, r) for r, c in cells}
    if rng.randrange(2):
        h, _ = _bbox(cells)
        cells = {(h - 1 - r, c) for r, c in cells}
    if rng.randrange(2):
        _, w = _bbox(cells)
        cells = {(r, w - 1 - c) for r, c in cells}
    return _normalize(cells)


def _shape_is_teaching(cells, h, w, mode, *, query):
    cells = _normalize(cells)
    sh, sw = _bbox(cells)
    if sh > h or sw > w or not _connected(cells):
        return False
    row = _row_close(cells)
    col = _col_close(cells)
    selected = row if mode == 0 else col
    if row == col or selected == cells:
        return False
    if query and selected == _solid_bbox(cells):
        return False
    return True


def _teaching_shape(ctx, label, h, w, mode, *, query, difficulty):
    rng = ctx.draw_rng(label)
    area = h * w
    band_cap = 9 if difficulty == "easy" else (14 if difficulty == "hard" else 11)
    lo = min(6, area - 1)
    hi = max(lo, min(area - 1, band_cap))
    for _ in range(320):
        size = rng.randint(lo, hi)
        cells = _random_polyomino(rng, size)
        if _shape_is_teaching(cells, h, w, mode, query=query):
            return cells
    fallback = _fallback_shape(mode, rng)
    if not _shape_is_teaching(fallback, h, w, mode, query=query):
        raise RuntimeError(f"no constructive teaching shape for {h}x{w} mode={mode}")
    return fallback


def _paint(grid, top, left, cells, color):
    for r, c in cells:
        grid[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_example_w, scheduled_query_w = _scheduled_dimensions(
        ctx, sample_index, difficulty
    )
    h = _draw_axis(ctx, "grid_h", 6, 20, scheduled_h)
    example_w = _draw_axis(ctx, "example_w", 3, 8, scheduled_example_w)
    query_w = _draw_axis(ctx, "query_w", 3, 12, scheduled_query_w)
    mode = _draw_axis(ctx, "mode", 0, 1, sample_index % 2)

    source = _teaching_shape(
        ctx, "source_shape", h, example_w, mode, query=False, difficulty=difficulty
    )
    query = _teaching_shape(
        ctx, "query_shape", h, query_w, mode, query=True, difficulty=difficulty
    )
    result = _row_close(source) if mode == 0 else _col_close(source)

    source_h, source_w = _bbox(source)
    query_h, query_shape_w = _bbox(query)
    source_position_rng = ctx.draw_rng("source_position")
    query_position_rng = ctx.draw_rng("query_position")
    source_top = source_position_rng.randint(0, h - source_h)
    source_left = source_position_rng.randint(0, example_w - source_w)
    query_top = query_position_rng.randint(0, h - query_h)
    query_left = query_position_rng.randint(0, query_w - query_shape_w)

    source_color, query_color = ctx.draw_rng("shape_colors").sample(_SHAPE_COLORS, 2)
    total_w = 2 * example_w + 2 + query_w
    grid = full_grid(h, total_w, 0)
    sep1 = example_w
    sep2 = 2 * example_w + 1
    for r in range(h):
        grid[r][sep1] = 5
        grid[r][sep2] = 5

    _paint(grid, source_top, source_left, source, source_color)
    _paint(grid, source_top, sep1 + 1 + source_left, result, source_color)
    _paint(grid, query_top, sep2 + 1 + query_left, query, query_color)
    return grid


def _panel_info(panel, label):
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"{label} panel must contain exactly one nonzero color, found {sorted(colors)}")
    color = next(iter(colors))
    if color in (5, 8):
        raise ValueError(f"{label} object color {color} is reserved")
    cells = frozenset(
        (r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0
    )
    if not _connected(cells):
        raise ValueError(f"{label} object must be four-connected")
    return color, cells


def _parse_scene(grid):
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list")
    if not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colors 0..9")
    h = len(grid)
    if not 6 <= h <= 20 or not 8 <= width <= 30:
        raise ValueError(f"grid dimensions {h}x{width} outside the declared ARC-legal envelope")

    separators = [c for c in range(width) if all(grid[r][c] == 5 for r in range(h))]
    if len(separators) != 2:
        raise ValueError(f"expected exactly two full color-5 separator columns, found {separators}")
    sep1, sep2 = separators
    if sep1 != sep2 - sep1 - 1:
        raise ValueError("source and worked-result panels must have equal widths")
    example_w = sep1
    query_w = width - sep2 - 1
    if not 3 <= example_w <= 8 or not 3 <= query_w <= 12:
        raise ValueError(f"panel widths example={example_w}, query={query_w} outside declared domains")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if c not in separators and value == 5:
                raise ValueError(f"color 5 occurs inside a panel at {(r, c)}")

    source_panel = [row[:sep1] for row in grid]
    result_panel = [row[sep1 + 1 : sep2] for row in grid]
    query_panel = [row[sep2 + 1 :] for row in grid]
    source_color, source = _panel_info(source_panel, "source")
    result_color, result = _panel_info(result_panel, "worked result")
    query_color, query = _panel_info(query_panel, "query")
    if result_color != source_color:
        raise ValueError("source and worked-result colors must match")
    if query_color == source_color:
        raise ValueError("query object must use a distinct color from the worked example")

    row_result = _row_close(source)
    col_result = _col_close(source)
    if result == row_result:
        mode = 0  # exact Racket branch order, including an ambiguous canonical source
    elif result == col_result:
        mode = 1
    else:
        raise ValueError("worked result is neither row-span nor column-span closure of source")

    return {
        "height": h,
        "width": width,
        "example_w": example_w,
        "query_w": query_w,
        "mode": mode,
        "source": source,
        "result": result,
        "query": query,
        "source_color": source_color,
        "query_color": query_color,
        "row_source": row_result,
        "col_source": col_result,
    }


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    scene = _parse_scene(grid)
    return {
        "grid_h": scene["height"],
        "example_w": scene["example_w"],
        "query_w": scene["query_w"],
        "mode": scene["mode"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    try:
        _parse_scene(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    requested = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        requested.update({name: meta[name] for name in AXES if name in meta})
    observed = observe_overrides(grid)
    errors = []
    for name, expected in requested.items():
        if name in AXES and expected is not None and observed.get(name) != expected:
            errors.append(f"override {name}={expected!r} realized as {observed.get(name)!r}")
    return errors


def strict_canonical_like(grid):
    """Exact canonical profile support, while accepting every canonical input."""
    errors = self_check(grid)
    if errors:
        return errors
    palette = len({value for row in grid for value in row})
    if (len(grid), len(grid[0]), palette) != (9, 23, 4):
        return [f"profile {(len(grid), len(grid[0]), palette)} is not canonical (9, 23, 4)"]
    return []


def _crop(cells, color=8):
    cells = frozenset(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [
        [color if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def rule_mirror(grid):
    """Pure Python mirror used only for tests/semantic contracts; Racket is authority."""
    scene = _parse_scene(grid)
    transformed = _row_close(scene["query"]) if scene["mode"] == 0 else _col_close(scene["query"])
    return _crop(transformed, 8)


def _always_row(grid):
    return _crop(_row_close(_parse_scene(grid)["query"]), 8)


def _always_column(grid):
    return _crop(_col_close(_parse_scene(grid)["query"]), 8)


def _copy_query(grid):
    return _crop(_parse_scene(grid)["query"], 8)


def _solid_bbox_output(grid):
    query = _parse_scene(grid)["query"]
    h, w = _bbox(_normalize(query))
    return full_grid(h, w, 8)


SEMANTIC_RIVALS = {
    "always_row": _always_row,
    "always_column": _always_column,
    "copy_query_without_closure": _copy_query,
    "solid_bbox": _solid_bbox_output,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every canonical answer is a solid query bounding box, so this wrong rule is
# unfalsifiable from the original three labels and needs generated witnesses.
CANONICAL_SHORTCUTS = {"solid_bbox": _solid_bbox_output}


def _rival_differs(name, grid):
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "row_mode_refutes_always_column": lambda grid: (
        observe_overrides(grid)["mode"] == 0 and _rival_differs("always_column", grid)
    ),
    "column_mode_refutes_always_row": lambda grid: (
        observe_overrides(grid)["mode"] == 1 and _rival_differs("always_row", grid)
    ),
    "closure_changes_query": lambda grid: _rival_differs("copy_query_without_closure", grid),
    "non_rectangular_result_refutes_solid_bbox": lambda grid: _rival_differs("solid_bbox", grid),
}
WITNESS_RIVALS = {
    "row_mode_refutes_always_column": ["always_column"],
    "column_mode_refutes_always_row": ["always_row"],
    "closure_changes_query": ["copy_query_without_closure"],
    "non_rectangular_result_refutes_solid_bbox": ["solid_bbox"],
}


def lesson_identifiable(demos, query):
    """Reject a lesson when a named wrong solver fits demos but changes query."""
    findings = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            findings.append(f"pair {index} input is invalid: {exc}")
            continue
        if expected != pair["output"]:
            findings.append(f"pair {index} output disagrees with the canonical closure rule")
    if findings:
        return findings
    if len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                findings.append(f"competitor {name!r} fits every demo but changes the query answer")
    return findings
