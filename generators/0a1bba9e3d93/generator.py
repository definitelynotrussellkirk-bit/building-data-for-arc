"""Generator for ARC task 0a1bba9e3d93 — transfer a learned edit delta.

The input is three equal panels separated by full color-8 columns:
BEFORE | AFTER | QUERY.  Normalize BEFORE and AFTER to their own bounding-box
minimums, subtract BEFORE support from AFTER support, and stamp only those added
relative cells at the QUERY bounding-box minimum in the query color.  Stamps
outside the query panel are clipped.

The sampler has a four-position teaching schedule.  Every four consecutive
examples contain exact canonical-scale anchors plus a different-query witness
and a partial-clipping witness, so the two canonical-fitting shortcuts declared
below are falsified by every ordinary lesson.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a1bba9e3d93"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "386c52a84df2"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Three color-8-separated panels show BEFORE, AFTER, and QUERY. Normalize "
    "the first two supports to their own bbox minima, transfer only AFTER's "
    "added relative cells to QUERY in the query color, and clip out-of-panel "
    "stamps. Every four-demo lesson includes different-query and partial-clip "
    "counterexamples to canonical-fitting shortcuts."
)

INVARIANTS = [
    "grid_h is 3..12 and width is exactly 3*panel_w+2 for panel_w 3..8",
    "separator columns are entirely color 8 and color 8 never occurs in a panel",
    "BEFORE and AFTER are connected one-color objects of the same color; QUERY is a connected object in a different color",
    "normalized BEFORE is a proper subset of normalized AFTER and at least one transferred cell changes QUERY",
    "clip boards retain at least one in-bounds addition while clipping at least one other addition",
]

_TEXTURES = ("plain", "diff_query", "clip")
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "panel_w": {
        "type": "int",
        "default": "canonical anchors at 3 or 4; otherwise difficulty-aware 3..8",
        "valid": "3..8",
    },
    "grid_h": {
        "type": "int",
        "default": "canonical anchors at 3 or 4; otherwise difficulty-aware 3..12",
        "valid": "3..12",
    },
    "texture": {
        "type": "str",
        "default": "four-step schedule plain|diff_query|clip|plain",
        "valid": "plain|diff_query|clip",
        "doc": (
            "diff_query changes QUERY's normalized support while preserving its "
            "cardinality; clip places QUERY so one learned addition clips and "
            "another remains visible."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_small",
    "diff_query",
    "clip",
    "canonical_large",
)


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Name the deterministic teaching branch for this sample index."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


# Each family is constructive in the minimum 3x3 panel.  AFTER is BEFORE plus
# two cells: one interior addition and one bbox-extending addition.  The latter
# makes a partial-clip witness possible without making the output an identity.
_SHAPE_FAMILIES = (
    {
        "before": frozenset({(0, 0), (0, 1), (1, 0)}),
        "delta": frozenset({(1, 1), (2, 0)}),
        "different_query": frozenset({(0, 0), (0, 1), (0, 2)}),
    },
    {
        "before": frozenset({(0, 0), (0, 1), (1, 1)}),
        "delta": frozenset({(1, 0), (2, 1)}),
        "different_query": frozenset({(0, 0), (0, 1), (0, 2)}),
    },
    {
        "before": frozenset({(0, 0), (0, 1), (1, 0)}),
        "delta": frozenset({(1, 1), (0, 2)}),
        "different_query": frozenset({(0, 0), (1, 0), (2, 0)}),
    },
    {
        "before": frozenset({(0, 0), (1, 0), (1, 1)}),
        "delta": frozenset({(0, 1), (1, 2)}),
        "different_query": frozenset({(0, 0), (1, 0), (2, 0)}),
    },
)

_BAND_RANGES = {
    None: ((3, 12), (3, 8)),
    "easy": ((3, 6), (3, 4)),
    "medium": ((5, 9), (4, 6)),
    "hard": ((8, 12), (6, 8)),
}


def _draw_axis_int(ctx, label: str, valid: tuple[int, int], default: tuple[int, int]) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *default)


def _draw_scheduled_int(
    ctx, label: str, valid: tuple[int, int], scheduled: int
) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, options: Sequence[str], scheduled: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _origins(shape: Iterable[tuple[int, int]], height: int, width: int) -> list[tuple[int, int]]:
    shape_h, shape_w = _shape_size(shape)
    return [
        (row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]


def _query_origins(
    query_shape: frozenset[tuple[int, int]],
    delta: frozenset[tuple[int, int]],
    height: int,
    width: int,
    texture: str,
) -> list[tuple[int, int]]:
    candidates: list[tuple[int, int]] = []
    for row0, col0 in _origins(query_shape, height, width):
        placed_query = {(row0 + row, col0 + col) for row, col in query_shape}
        stamps = [(row0 + row, col0 + col) for row, col in delta]
        in_bounds = {
            (row, col)
            for row, col in stamps
            if 0 <= row < height and 0 <= col < width
        }
        clipped = len(in_bounds) != len(stamps)
        changed = in_bounds - placed_query
        if not changed:
            continue
        if texture == "clip" and clipped:
            candidates.append((row0, col0))
        elif texture != "clip" and not clipped:
            candidates.append((row0, col0))
    return candidates


def _paint(
    grid: list[list[int]],
    shape: Iterable[tuple[int, int]],
    origin: tuple[int, int],
    left: int,
    color: int,
) -> None:
    row0, col0 = origin
    for row, col in shape:
        grid[row0 + row][left + col0 + col] = color


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for name in ("grid_h", "panel_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a literal integer, not {type(value).__name__}")
    texture_override = overrides.get("texture")
    if texture_override is not None and type(texture_override) is not str:
        raise ValueError(
            f"texture must be a string, not {type(texture_override).__name__}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_texture = {
        "canonical_small": "plain",
        "diff_query": "diff_query",
        "clip": "clip",
        "canonical_large": "plain",
    }[profile]
    texture = _draw_scheduled_choice(ctx, "texture", _TEXTURES, scheduled_texture)

    if profile == "canonical_small":
        height = _draw_scheduled_int(ctx, "grid_h", (3, 12), 3)
        panel_w = _draw_scheduled_int(ctx, "panel_w", (3, 8), 3)
    elif profile == "canonical_large":
        height = _draw_scheduled_int(ctx, "grid_h", (3, 12), 4)
        panel_w = _draw_scheduled_int(ctx, "panel_w", (3, 8), 4)
    else:
        h_range, w_range = _BAND_RANGES[difficulty]
        height = _draw_axis_int(ctx, "grid_h", (3, 12), h_range)
        panel_w = _draw_axis_int(ctx, "panel_w", (3, 8), w_range)

    layout_rng = ctx.draw_rng("layout")
    family = layout_rng.choice(_SHAPE_FAMILIES)
    before = family["before"]
    delta = family["delta"]
    after = before | delta
    query_shape = family["different_query"] if texture == "diff_query" else before

    before_origins = _origins(before, height, panel_w)
    after_origins = _origins(after, height, panel_w)
    query_origins = _query_origins(query_shape, delta, height, panel_w, texture)
    if not before_origins or not after_origins or not query_origins:
        raise RuntimeError(
            f"constructive family has no placement for {height}x{panel_w}/{texture}"
        )

    before_origin = layout_rng.choice(before_origins)
    after_origin = layout_rng.choice(after_origins)
    query_origin = layout_rng.choice(query_origins)
    demo_color, query_color = ctx.draw_rng("palette").sample(_COLORS, 2)

    width = 3 * panel_w + 2
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][panel_w] = 8
        grid[row][2 * panel_w + 1] = 8
    _paint(grid, before, before_origin, 0, demo_color)
    _paint(grid, after, after_origin, panel_w + 1, demo_color)
    _paint(grid, query_shape, query_origin, 2 * (panel_w + 1), query_color)

    expected = {"grid_h": height, "panel_w": panel_w, "texture": texture}
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed axes drifted: expected {expected}, observed {observed}")
    findings = self_check(grid)
    if findings:
        raise RuntimeError("constructed invalid transfer board: " + "; ".join(findings))
    return [row[:] for row in grid]


def _normalize(points: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = tuple(points)
    row0 = min(row for row, _ in points)
    col0 = min(col for _, col in points)
    return frozenset((row - row0, col - col0) for row, col in points)


def _connected(points: Iterable[tuple[int, int]]) -> bool:
    remaining = set(points)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen = {stack[0]}
    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == remaining


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty sequence of rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return facts, ["every row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return facts, ["grid must be rectangular with positive width"]
    height = len(grid)
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return facts, ["every cell must be a literal ARC color integer 0..9"]
    if not 3 <= height <= 12:
        errors.append(f"grid_h={height} outside declared range 3..12")
    if width < 11 or (width - 2) % 3:
        return facts, errors + [
            f"width {width} must equal 3*panel_w+2 for an integer panel width"
        ]
    panel_w = (width - 2) // 3
    if not 3 <= panel_w <= 8:
        errors.append(f"panel_w={panel_w} outside declared range 3..8")

    sep1, sep2 = panel_w, 2 * panel_w + 1
    if any(row[sep1] != 8 or row[sep2] != 8 for row in grid):
        errors.append("both separator columns must be entirely color 8")
    panels = tuple(
        [list(row[index * (panel_w + 1): index * (panel_w + 1) + panel_w]) for row in grid]
        for index in range(3)
    )
    panel_names = ("BEFORE", "AFTER", "QUERY")
    supports: list[frozenset[tuple[int, int]]] = []
    colors: list[int | None] = []
    for name, panel in zip(panel_names, panels):
        if any(value == 8 for row in panel for value in row):
            errors.append(f"{name} contains separator color 8")
        points = frozenset(
            (row, col)
            for row, values in enumerate(panel)
            for col, value in enumerate(values)
            if value != 0
        )
        palette = sorted({panel[row][col] for row, col in points})
        if not points:
            errors.append(f"{name} must contain foreground")
            supports.append(points)
            colors.append(None)
            continue
        if len(palette) != 1:
            errors.append(f"{name} must contain exactly one foreground color, got {palette}")
            colors.append(palette[0] if palette else None)
        else:
            colors.append(palette[0])
        if not _connected(points):
            errors.append(f"{name} foreground must be 4-connected")
        supports.append(points)

    facts.update({
        "grid_h": height,
        "panel_w": panel_w,
        "panels": panels,
        "supports": tuple(supports),
        "colors": tuple(colors),
    })
    if any(not support for support in supports):
        return facts, errors

    before_cells, after_cells, query_cells = supports
    before_norm = _normalize(before_cells)
    after_norm = _normalize(after_cells)
    query_norm = _normalize(query_cells)
    delta = after_norm - before_norm
    if colors[0] is not None and colors[1] is not None and colors[0] != colors[1]:
        errors.append("BEFORE and AFTER must use the same foreground color")
    if colors[2] is not None and colors[0] is not None and colors[2] == colors[0]:
        errors.append("QUERY must use a foreground color distinct from BEFORE/AFTER")
    if not before_norm < after_norm:
        errors.append("normalized BEFORE must be a proper subset of normalized AFTER")
    if len(before_norm) not in (3, 4):
        errors.append(f"BEFORE support size {len(before_norm)} must be 3 or 4")
    if len(query_norm) != len(before_norm):
        errors.append("QUERY support cardinality must equal BEFORE support cardinality")
    if len(delta) not in (1, 2):
        errors.append(f"learned delta size {len(delta)} must be 1 or 2")

    qrow = min(row for row, _ in query_cells)
    qcol = min(col for _, col in query_cells)
    stamps = tuple((qrow + row, qcol + col) for row, col in sorted(delta))
    in_bounds = tuple(
        point for point in stamps
        if 0 <= point[0] < height and 0 <= point[1] < panel_w
    )
    clipped = tuple(point for point in stamps if point not in in_bounds)
    changed = tuple(point for point in in_bounds if point not in query_cells)
    if not changed:
        errors.append("delta must add at least one new in-bounds QUERY cell")
    texture = "clip" if clipped else ("diff_query" if query_norm != before_norm else "plain")

    used = {value for row in grid for value in row}
    expected_palette = {0, 8, colors[0], colors[2]}
    if None not in expected_palette and used != expected_palette:
        errors.append(
            f"grid palette {sorted(used)} must be exactly {sorted(expected_palette)}"
        )

    facts.update({
        "before_support": before_norm,
        "after_support": after_norm,
        "query_support": query_norm,
        "delta": frozenset(delta),
        "query_origin": (qrow, qcol),
        "query_color": colors[2],
        "stamps": stamps,
        "in_bounds_stamps": in_bounds,
        "clipped_stamps": clipped,
        "changed_stamps": changed,
        "texture": texture,
    })
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return _analyze(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    """The declared sampler manifold; all canonical inputs are included."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "panel_w": facts["panel_w"],
        "texture": facts["texture"],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror for focused tests; the immutable Racket remains authority."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid transfer board: " + "; ".join(errors))
    query = [list(row) for row in facts["panels"][2]]
    color = facts["query_color"]
    for row, col in facts["in_bounds_stamps"]:
        query[row][col] = color
    return query


def profile_signature(grid) -> tuple[Any, ...]:
    facts, errors = _analyze(grid)
    if errors:
        return ("invalid", tuple(errors))
    palette_size = len({value for row in grid for value in row})
    return (
        facts["grid_h"],
        3 * facts["panel_w"] + 2,
        palette_size,
        facts["texture"],
        tuple(sorted(facts["before_support"])),
        tuple(sorted(facts["query_support"])),
        tuple(sorted(facts["delta"])),
    )


def _copy_after_shape(grid) -> list[list[int]]:
    """RIVAL: replace QUERY by normalized AFTER, ignoring QUERY's own shape."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid transfer board: " + "; ".join(errors))
    out = full_grid(facts["grid_h"], facts["panel_w"], 0)
    row0, col0 = facts["query_origin"]
    for row, col in facts["after_support"]:
        rr, cc = row0 + row, col0 + col
        if 0 <= rr < facts["grid_h"] and 0 <= cc < facts["panel_w"]:
            out[rr][cc] = facts["query_color"]
    return out


def _reject_partial_clip(grid) -> list[list[int]]:
    """RIVAL: apply growth only when every learned cell fits in the panel."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid transfer board: " + "; ".join(errors))
    if facts["clipped_stamps"]:
        return [list(row) for row in facts["panels"][2]]
    return rule_mirror(grid)


def _different_query_witness(grid) -> bool:
    facts, errors = _analyze(grid)
    return (
        not errors
        and facts["texture"] == "diff_query"
        and _copy_after_shape(grid) != rule_mirror(grid)
    )


def _partial_clip_witness(grid) -> bool:
    facts, errors = _analyze(grid)
    return (
        not errors
        and facts["texture"] == "clip"
        and bool(facts["clipped_stamps"])
        and bool(facts["changed_stamps"])
        and _reject_partial_clip(grid) != rule_mirror(grid)
    )


SEMANTIC_RIVALS = {
    "copy_after_shape": _copy_after_shape,
    "reject_partial_clip": _reject_partial_clip,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "different_query_shape": _different_query_witness,
    "partial_clip": _partial_clip_witness,
}
WITNESS_RIVALS = {
    "different_query_shape": ["copy_after_shape"],
    "partial_clip": ["reject_partial_clip"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every ordinary four-demo lesson to refute both named shortcuts."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    valid_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"demo {index} malformed: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match delta transfer")
            continue
        valid_demos.append(pair)

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        findings = self_check(query["input"])
        if findings:
            reasons.append(f"query malformed: {findings[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match delta transfer")
    return reasons
