"""Input curriculum for task 9349fabc466a: connect same-color axis markers.

For each nonzero color, the canonical Racket rule fills background cells lying
between any two markers of that color in a shared row or shared column. Existing
markers are preserved. When two colors would fill the same background cell, the
numerically smaller color wins because ``grid-colors`` is sorted.

The sampler deliberately mixes canonical-scale sparse cases with semantic
counterexamples to four plausible shortcuts: exactly-two-only, first-pair-only,
highest-color overlap priority, and bounding-box connection.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9349fabc466a"
TASK_ID = GENERATOR_ID
RULE_HASH = "bde71b91a345"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Sparse 0-background grids with 2-3 colors. Same-color markers may form a "
    "single row/column pair, a gapped collinear triple, several row/column "
    "spans, a lowest-color overlap, or an unaligned distractor. Fill every "
    "background cell between same-color markers sharing a row or column; keep "
    "existing markers, and let the numerically smallest eligible color win "
    "overlaps."
)

INVARIANTS = [
    "background is 0 and there are exactly 2 or 3 nonzero colors",
    "every color has 2-4 marker cells and at least one color changes the output",
    "canonical-sized 7x9 or 8x8 examples recur in every difficulty band",
    "even-index teaching cases jointly refute all declared canonical shortcuts",
]

_SHAPES = {
    "7x9": (7, 9),
    "8x8": (8, 8),
    "10x12": (10, 12),
    "14x14": (14, 14),
    "18x18": (18, 18),
}
_PALETTES = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}

AXES = {
    "grid_shape": {
        "type": "str",
        "default": "alternating canonical profile and difficulty-scaled broad profile",
        "valid": "7x9|8x8|10x12|14x14|18x18",
    },
    "n_colors": {"type": "int", "default": "2 canonical / 2-3 broad", "valid": "2..3"},
    "palette_kind": {"type": "str", "default": "uniform", "valid": "low|mid|high"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

# Coordinates live in a 7x7 local canvas.  Color indices map to the sorted
# palette.  Every template has a visible rule effect; the comprehensive
# teaching template refutes every declared shortcut in one example.
_TEMPLATES: dict[str, tuple[tuple[int, int, int], ...]] = {
    "pair": (
        (0, 1, 0), (0, 1, 6),
        (1, 3, 6), (1, 6, 6),
        (2, 5, 1), (2, 5, 2),
    ),
    "triplet": (
        (0, 1, 0), (0, 1, 2), (0, 1, 6),
        (1, 3, 6), (1, 6, 6),
        (2, 5, 1), (2, 5, 2),
    ),
    "rectangle": (
        (0, 1, 1), (0, 1, 5), (0, 5, 1), (0, 5, 5),
        (1, 3, 0), (1, 3, 6),
        (2, 6, 0), (2, 6, 1),
    ),
    "crossing": (
        (0, 3, 0), (0, 3, 6),
        (1, 0, 3), (1, 6, 3),
        (2, 1, 5), (2, 1, 6),
    ),
    "distractor": (
        (0, 2, 0), (0, 2, 6),
        (1, 4, 1), (1, 6, 5),
        (2, 0, 4), (2, 6, 4),
    ),
    "teaching": (
        (0, 1, 1), (0, 1, 5), (0, 5, 1), (0, 5, 5),
        (1, 0, 3), (1, 6, 3), (1, 1, 6),
        (2, 6, 0), (2, 6, 1),
    ),
}
_VARIED_LAYOUTS = ("pair", "triplet", "rectangle", "crossing", "distractor")


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if "grid_shape" in overrides and overrides["grid_shape"] is not None:
        value = overrides["grid_shape"]
        if type(value) is not str or value not in _SHAPES:
            raise ValueError(f"grid_shape must be one of {sorted(_SHAPES)}, got {value!r}")
    if "n_colors" in overrides and overrides["n_colors"] is not None:
        value = overrides["n_colors"]
        if type(value) is not int:
            raise TypeError("n_colors must be an integer (not bool)")
        if value not in (2, 3):
            raise ValueError("n_colors must be 2 or 3")
    if "palette_kind" in overrides and overrides["palette_kind"] is not None:
        value = overrides["palette_kind"]
        if type(value) is not str or value not in _PALETTES:
            raise ValueError(f"palette_kind must be one of {sorted(_PALETTES)}, got {value!r}")


def _axis_choice(ctx, overrides, name, domain, default):
    """Record an exact axis while allowing a deterministic scheduled default."""
    options = tuple(domain) if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, options)


def _default_shape(ctx, sample_index: int, difficulty) -> str:
    # Half the stream is source-shaped by construction.  This also gives every
    # four-pair lesson at least two canonical-profile opportunities.
    if sample_index % 2 == 0:
        return ("7x9", "8x8")[(sample_index // 2 + ctx.seed) % 2]
    choices = {
        "easy": ("7x9", "8x8", "10x12"),
        "medium": ("8x8", "10x12", "14x14"),
        "hard": ("10x12", "14x14", "18x18"),
    }.get(difficulty, tuple(_SHAPES))
    return ctx.draw_rng("default_grid_shape").choice(choices)


def _default_n_colors(ctx, sample_index: int) -> int:
    if sample_index % 2 == 0:
        return 2
    return ctx.draw_rng("default_n_colors").choice((2, 3))


def _transform_point(r: int, c: int, code: int) -> tuple[int, int]:
    """Apply one of the eight dihedral transforms to a 7x7 coordinate."""
    if code >= 4:
        c = 6 - c
        code -= 4
    for _ in range(code):
        r, c = c, 6 - r
    return r, c


def _layout_name(ctx, sample_index: int) -> str:
    # Teaching cases at every even accepted index guarantee that any four
    # consecutive pairs retain one after any single query rotation.
    if sample_index % 2 == 0:
        return "teaching"
    return ctx.draw_rng("varied_layout").choice(_VARIED_LAYOUTS)


def _build_grid(ctx, h: int, w: int, colors: tuple[int, ...], layout: str):
    grid = full_grid(h, w, 0)
    turn = ctx.draw_int("dihedral", 0, 7)
    top = ctx.draw_int("offset_r", 0, h - 7)
    left = ctx.draw_int("offset_c", 0, w - 7)
    for color_index, r, c in _TEMPLATES[layout]:
        if color_index >= len(colors):
            continue
        rr, cc = _transform_point(r, c, turn)
        rr += top
        cc += left
        if grid[rr][cc] != 0:
            raise RuntimeError("template transform collided; refusing a shortened draw")
        grid[rr][cc] = colors[color_index]
    return grid


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
    shape = _axis_choice(
        ctx, overrides, "grid_shape", _SHAPES,
        _default_shape(ctx, sample_index, difficulty),
    )
    if overrides.get("n_colors") is not None:
        n_colors = ctx.draw_int_strict("n_colors", 2, 3)
    else:
        n_colors = ctx.draw_choice("n_colors", (_default_n_colors(ctx, sample_index),))
    palette_kind = ctx.draw_choice("palette_kind", tuple(_PALETTES))
    colors = tuple(sorted(_PALETTES[palette_kind][:n_colors]))
    h, w = _SHAPES[shape]
    return _build_grid(ctx, h, w, colors, _layout_name(ctx, sample_index))


def _grid_findings(grid) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9 (not bool)"]
    return []


def _positions(grid) -> dict[int, list[tuple[int, int]]]:
    result: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                result[value].append((r, c))
    return dict(result)


def _axis_spans(points: list[tuple[int, int]]):
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    for r, c in points:
        rows[r].append(c)
        cols[c].append(r)
    row_spans = {r: (min(cs), max(cs)) for r, cs in rows.items() if len(cs) >= 2}
    col_spans = {c: (min(rs), max(rs)) for c, rs in cols.items() if len(rs) >= 2}
    return row_spans, col_spans


def _solve_axis_rule(
    grid,
    *,
    points_filter: Callable[[int, list[tuple[int, int]]], list[tuple[int, int]]] | None = None,
    reverse_priority: bool = False,
):
    positions = _positions(grid)
    colors = sorted(positions, reverse=reverse_priority)
    spans = {}
    for color in colors:
        points = positions[color]
        if points_filter is not None:
            points = points_filter(color, points)
        spans[color] = _axis_spans(points)
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            for color in colors:
                row_spans, col_spans = spans[color]
                horizontal = r in row_spans and row_spans[r][0] <= c <= row_spans[r][1]
                vertical = c in col_spans and col_spans[c][0] <= r <= col_spans[c][1]
                if horizontal or vertical:
                    out[r][c] = color
                    break
    return out


def _reference_output(grid):
    """Independent Python oracle for the pinned canonical Racket rule."""
    return _solve_axis_rule(grid)


def _exactly_two_only(grid):
    return _solve_axis_rule(grid, points_filter=lambda _color, points: points if len(points) == 2 else [])


def _first_pair_only(grid):
    return _solve_axis_rule(grid, points_filter=lambda _color, points: sorted(points)[:2])


def _highest_color_wins(grid):
    return _solve_axis_rule(grid, reverse_priority=True)


def _bounding_box_connect(grid):
    positions = _positions(grid)
    colors = sorted(positions)
    boxes = {
        color: (
            min(r for r, _ in points), max(r for r, _ in points),
            min(c for _, c in points), max(c for _, c in points),
        )
        for color, points in positions.items()
    }
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            for color in colors:
                r0, r1, c0, c1 = boxes[color]
                on_border = (
                    (r in (r0, r1) and c0 <= c <= c1)
                    or (c in (c0, c1) and r0 <= r <= r1)
                )
                if on_border:
                    out[r][c] = color
                    break
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    findings = _grid_findings(grid)
    if findings:
        return findings
    positions = _positions(grid)
    if not 2 <= len(positions) <= 3:
        findings.append(f"expected 2-3 nonzero colors, found {len(positions)}")
    for color, points in positions.items():
        if not 2 <= len(points) <= 4:
            findings.append(f"color {color} must have 2-4 markers, found {len(points)}")
    if not findings and _reference_output(grid) == grid:
        findings.append("the canonical rule makes no visible change")
    return findings


def strict_canonical_like(grid):
    findings = self_check(grid)
    if findings:
        return findings
    h, w = len(grid), len(grid[0])
    palette_size = len(_positions(grid)) + 1
    if (h, w, palette_size) not in {(5, 7, 3), (7, 9, 3), (8, 8, 3)}:
        return [f"profile {(h, w, palette_size)} is outside the canonical profiles"]
    return []


MIN_STRICT_FRAC = 0.25


def observe_overrides(grid):
    findings = _grid_findings(grid)
    if findings:
        raise ValueError("; ".join(findings))
    dims = (len(grid), len(grid[0]))
    shape = next((name for name, value in _SHAPES.items() if value == dims), None)
    if shape is None:
        raise ValueError(f"unrecognized generated shape {dims}")
    colors = set(_positions(grid))
    palette_kind = next(
        (name for name, palette in _PALETTES.items() if colors <= set(palette)),
        None,
    )
    if palette_kind is None:
        raise ValueError(f"colors {sorted(colors)} do not identify a palette_kind")
    return {"grid_shape": shape, "n_colors": len(colors), "palette_kind": palette_kind}


def _differs_from(rival):
    return lambda grid: rival(grid) != _reference_output(grid)


SEMANTIC_RIVALS = {
    "exactly_two_only": _exactly_two_only,
    "first_pair_only": _first_pair_only,
    "highest_color_wins": _highest_color_wins,
    "bounding_box_connect": _bounding_box_connect,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "multi_marker_gap": _differs_from(_exactly_two_only),
    "multiple_spans": _differs_from(_first_pair_only),
    "overlap_priority": _differs_from(_highest_color_wins),
    "axis_only_not_bbox": _differs_from(_bounding_box_connect),
}
WITNESS_RIVALS = {
    "multi_marker_gap": ["exactly_two_only"],
    "multiple_spans": ["first_pair_only"],
    "overlap_priority": ["highest_color_wins"],
    "axis_only_not_bbox": ["bounding_box_connect"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return "teaching" if sample_index % 2 == 0 else "varied"


SCHEDULE_PROFILES = ("teaching", "varied")
