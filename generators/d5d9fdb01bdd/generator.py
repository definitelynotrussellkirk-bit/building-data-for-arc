"""Generator for ``d5d9fdb01bdd``: transpose the tight content crop.

The canonical task uses sparse, path-like one- and two-colour patterns rather
than dense four-colour rectangles.  This sampler keeps a canonical-scale core
while also emitting wider, taller, connected, and disconnected lawful scenes.
The Racket authority remains unchanged; this module generates inputs only.
"""
from __future__ import annotations

from dataclasses import dataclass

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5d9fdb01bdd"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "1b9c6046c883"

SUMMARY = (
    "Place a sparse one- to three-colour pattern inside a black border. "
    "The nonzero content may be connected or disconnected and may be tall, "
    "square, or wide. Crop to the tight bbox of every nonzero cell, preserving "
    "internal zeros, then transpose that crop."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the complete content bbox has visible outer padding",
    "the tight crop is sparse and asymmetric, so transposition is observable",
    "all nonzero cells participate, including disconnected cells and all colours",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors alternating with difficulty-aware 5..11",
        "valid": "5..11",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors alternating with difficulty-aware 6..12",
        "valid": "6..12",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "canonical 1/2-colour schedule; generalized 1..3",
        "valid": "1..3",
    },
}

# Every advertised cross-product is constructive, including 5x6 with 3 colours.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class _Template:
    height: int
    width: int
    cells: tuple[tuple[int, int], ...]
    accents: tuple[tuple[int, int], ...]


# Connected tall patterns.  ``accents`` occupy the terminal boundary segment;
# assigning secondary colours there guarantees that colour-limited crops differ.
_TALL_TEMPLATES = (
    _Template(
        3,
        2,
        ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
        ((2, 0), (2, 1)),
    ),
    _Template(
        4,
        2,
        ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (3, 0)),
        ((2, 0), (3, 0)),
    ),
    _Template(
        4,
        3,
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
        ((2, 2), (3, 2)),
    ),
    _Template(
        5,
        3,
        (
            (0, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (2, 2),
            (3, 2),
            (4, 2),
            (4, 1),
        ),
        ((3, 2), (4, 2), (4, 1)),
    ),
)

# Wide two-component patterns.  Either component alone gives a different crop;
# the union spans a wider bbox and therefore simultaneously refutes the two
# canonical-compatible rivals used by the teaching contract.
_WIDE_DISCONNECTED_TEMPLATES = (
    _Template(
        3,
        4,
        ((0, 0), (1, 0), (1, 1), (1, 3), (2, 3), (2, 2)),
        ((1, 3), (2, 3), (2, 2)),
    ),
    _Template(
        4,
        5,
        (
            (0, 0),
            (1, 0),
            (1, 1),
            (2, 1),
            (1, 4),
            (2, 4),
            (3, 4),
            (3, 3),
        ),
        ((1, 4), (2, 4), (3, 4), (3, 3)),
    ),
)

# role 0 is a canonical-scale anchor.  Roles 1 and 2 are independent wide,
# disconnected witnesses.  Thus every three consecutive demonstrations—and
# every three-of-four query rotation—contains a sample refuting both declared
# rivals rather than depending on a fixed query position.
_CANONICAL_AXIS_DEFAULTS = {
    0: (6, 7, 2),
    1: (5, 8, 1),
    2: (6, 8, 2),
}


def _validate_request(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and (type(value) is not int):
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _draw_scheduled_int(ctx, name, lo, hi, default, *, generalized) -> int:
    """Use a pinned curriculum value unless the caller overrides it.

    The override branch always validates against the complete advertised domain;
    generalized draws use the same complete bounds with a difficulty skew.
    """
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    if generalized:
        return ctx.draw_int_diff(name, lo, hi)
    return ctx.draw_choice(name, (default,))


def _transpose_template(template: _Template) -> _Template:
    return _Template(
        template.width,
        template.height,
        tuple((c, r) for r, c in template.cells),
        tuple((c, r) for r, c in template.accents),
    )


def _transform_template(template: _Template, *, reverse_rows: bool, reverse_cols: bool) -> _Template:
    def transform(cell):
        r, c = cell
        if reverse_rows:
            r = template.height - 1 - r
        if reverse_cols:
            c = template.width - 1 - c
        return r, c

    return _Template(
        template.height,
        template.width,
        tuple(transform(cell) for cell in template.cells),
        tuple(transform(cell) for cell in template.accents),
    )


def _choose_template(ctx, role: int, max_h: int, max_w: int, *, canonical: bool) -> _Template:
    if role in (1, 2):
        candidates = [
            template
            for template in _WIDE_DISCONNECTED_TEMPLATES
            if template.height <= max_h and template.width <= max_w
        ]
    else:
        candidates = [
            template
            for template in _TALL_TEMPLATES
            if template.height <= max_h and template.width <= max_w
        ]
        if canonical:
            exact = [
                template
                for template in candidates
                if (template.height, template.width) == (4, 3)
            ]
            if exact:
                candidates = exact
    if not candidates:
        raise ValueError(
            f"grid interior {max_h}x{max_w} cannot host role {role} pattern"
        )
    template = ctx.draw_rng("template").choice(candidates)
    flip_rng = ctx.draw_rng("template_flip")
    return _transform_template(
        template,
        reverse_rows=bool(flip_rng.randrange(2)),
        reverse_cols=bool(flip_rng.randrange(2)),
    )


def _paint(grid, top, left, template: _Template, palette: tuple[int, ...]) -> None:
    accents = set(template.accents)
    base = [cell for cell in template.cells if cell not in accents]
    if not base:
        raise RuntimeError("template has no base cells")

    assignments: dict[tuple[int, int], int] = {cell: palette[0] for cell in base}
    if len(palette) == 1:
        assignments.update({cell: palette[0] for cell in template.accents})
    else:
        secondary = palette[1:]
        if len(template.accents) < len(secondary):
            raise RuntimeError("template cannot realize all requested colours")
        for index, cell in enumerate(template.accents):
            assignments[cell] = secondary[index % len(secondary)]

    for (row, col), color in assignments.items():
        grid[top + row][left + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    role = sample_index % 3
    canonical = role == 0
    default_h, default_w, default_colors = _CANONICAL_AXIS_DEFAULTS[role]
    h = _draw_scheduled_int(
        ctx, "grid_h", 5, 11, default_h, generalized=not canonical
    )
    w = _draw_scheduled_int(
        ctx, "grid_w", 6, 12, default_w, generalized=not canonical
    )
    n_colors = _draw_scheduled_int(
        ctx,
        "n_distinct_colors",
        1,
        3,
        default_colors,
        generalized=not canonical,
    )

    template = _choose_template(ctx, role, h - 2, w - 2, canonical=canonical)
    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={0})
    placement_rng = ctx.draw_rng("placement")
    top = placement_rng.randint(1, h - template.height - 1)
    left = placement_rng.randint(1, w - template.width - 1)

    grid = full_grid(h, w, 0)
    _paint(grid, top, left, template, palette)
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return {}, ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append(
                    f"cell ({row_index},{col_index}) must be an integer colour 0..9"
                )
    if errors:
        return {}, errors

    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return {}, ["grid has no nonzero content to crop"]

    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    crop = [values[left : right + 1] for values in grid[top : bottom + 1]]
    colors = {grid[row][col] for row, col in cells}
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "n_distinct_colors": len(colors),
        "bbox_h": bottom - top + 1,
        "bbox_w": right - left + 1,
        "occupied": len(cells),
        "top": top,
        "left": left,
        "bottom_padding": len(grid) - bottom - 1,
        "right_padding": width - right - 1,
        "crop": crop,
    }, []


def observe_overrides(grid) -> dict[str, int]:
    analysis, errors = _analyze(grid)
    if errors:
        return {}
    return {name: analysis[name] for name in AXES}


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket authority."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    crop = analysis["crop"]
    return [list(row) for row in zip(*crop)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    analysis, errors = _analyze(grid)
    if errors:
        return errors

    if not 5 <= analysis["grid_h"] <= 11:
        errors.append("canvas height must be 5..11")
    if not 6 <= analysis["grid_w"] <= 12:
        errors.append("canvas width must be 6..12")
    if not 2 <= analysis["bbox_h"] <= 5:
        errors.append("tight bbox height must be 2..5")
    if not 2 <= analysis["bbox_w"] <= 5:
        errors.append("tight bbox width must be 2..5")
    if not 5 <= analysis["occupied"] <= 10:
        errors.append("content must contain 5..10 nonzero cells")
    if not 1 <= analysis["n_distinct_colors"] <= 3:
        errors.append("content must use 1..3 nonzero colours")
    if min(
        analysis["top"],
        analysis["left"],
        analysis["bottom_padding"],
        analysis["right_padding"],
    ) < 1:
        errors.append("content must leave at least one black row/column on every side")
    crop = analysis["crop"]
    if all(value != 0 for row in crop for value in row):
        errors.append("tight crop must preserve at least one internal black cell")
    transpose = [list(row) for row in zip(*crop)]
    if crop == transpose:
        errors.append("tight crop must be asymmetric so transpose is observable")
    return errors


# Canonical-coverage and semantic teaching hooks consumed by the shared review
# battery.  The strict profile intentionally describes the original lesson
# rather than every lawful generalized sample.
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "wide_disconnected_a",
    "wide_disconnected_b",
)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def strict_canonical_like(grid) -> list[str]:
    analysis, errors = _analyze(grid)
    if errors:
        return errors

    if self_check(grid):
        errors.append("grid is outside the lawful task family")
    if (analysis["grid_h"], analysis["grid_w"]) not in {
        (5, 8),
        (6, 6),
        (6, 7),
        (6, 8),
    }:
        errors.append("outer dimensions are outside canonical profiles")
    if (analysis["bbox_h"], analysis["bbox_w"]) not in {
        (3, 3),
        (4, 2),
        (4, 3),
    }:
        errors.append("tight-crop dimensions are outside canonical profiles")
    if analysis["occupied"] not in {5, 6}:
        errors.append("canonical content contains five or six nonzero cells")
    if analysis["n_distinct_colors"] not in {1, 2}:
        errors.append("canonical content uses one or two nonzero colours")
    return errors


def _nonzero_components(grid) -> tuple[tuple[tuple[int, int], ...], ...]:
    remaining = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    components: list[tuple[tuple[int, int], ...]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        component: list[tuple[int, int]] = []
        while stack:
            row, col = stack.pop()
            component.append((row, col))
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(sorted(components, key=lambda cells: (-len(cells), cells)))


def _rival_transpose_only_tall_or_square(grid):
    """Plausible canonical shortcut: skip transpose for a wide crop."""
    analysis, errors = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    crop = [row[:] for row in analysis["crop"]]
    if analysis["bbox_h"] >= analysis["bbox_w"]:
        return [list(row) for row in zip(*crop)]
    return crop


def _rival_largest_component_only(grid):
    """Plausible object shortcut: ignore every component but the largest."""
    components = _nonzero_components(grid)
    if not components:
        raise ValueError("grid has no nonzero content to crop")
    keep = set(components[0])
    restricted = [
        [value if (row, col) in keep else 0 for col, value in enumerate(values)]
        for row, values in enumerate(grid)
    ]
    return rule_mirror(restricted)


SEMANTIC_RIVALS = {
    "transpose_only_tall_or_square": _rival_transpose_only_tall_or_square,
    "largest_component_only": _rival_largest_component_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "transpose_only_tall_or_square": _rival_transpose_only_tall_or_square,
}


def _witness_wide_crop_requires_transpose(grid) -> bool:
    analysis, errors = _analyze(grid)
    return bool(
        not errors
        and analysis["bbox_w"] > analysis["bbox_h"]
        and _rival_transpose_only_tall_or_square(grid) != rule_mirror(grid)
    )


def _witness_disconnected_content_uses_all_cells(grid) -> bool:
    return bool(
        len(_nonzero_components(grid)) >= 2
        and _rival_largest_component_only(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "wide_crop_requires_transpose": _witness_wide_crop_requires_transpose,
    "disconnected_content_uses_all_cells": _witness_disconnected_content_uses_all_cells,
}
WITNESS_RIVALS = {
    "wide_crop_requires_transpose": ("transpose_only_tall_or_square",),
    "disconnected_content_uses_all_cells": ("largest_component_only",),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return surviving rivals that fit demos but disagree on the query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        if not all(rival(pair["input"]) == pair["output"] for pair in demos):
            continue
        if rival(query["input"]) != query["output"]:
            reasons.append(f"rival {name!r} still fits every demonstration")
    return reasons
