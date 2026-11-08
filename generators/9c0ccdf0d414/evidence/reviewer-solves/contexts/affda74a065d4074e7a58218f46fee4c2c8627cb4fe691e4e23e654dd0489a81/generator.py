"""Constructive input generator for a quadrant-normalization mosaic task.

The selected Racket authority finds same-color 4-connected objects, assigns each
object to a source quadrant by its cell-centroid, crops it tightly, and pastes the
first object from each quadrant into the corresponding cell of a 2x2 mosaic.
This generator therefore emits at most one object per occupied quadrant.  It
never creates an input object that the authority silently discards.
"""
from __future__ import annotations

from itertools import combinations, permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c0ccdf0d414"
TASK_ID = GENERATOR_ID
RULE_HASH = "559cd5677fd5"
VERSION = "2.0.0"

SUMMARY = (
    "Three or four distinct-color connected motifs occupy distinct source "
    "quadrants. The rule classifies each motif by its centroid, crops it, and "
    "reassembles the occupied quadrants as a normalized 2x2 mosaic with one "
    "background row and column between mosaic cells."
)

INVARIANTS = [
    "background is 0 and all colors are ARC integers 0..9",
    "exactly 3-4 monochrome 4-connected motifs, each with 3-6 cells",
    "motif colors are distinct and at most one motif occupies each centroid quadrant",
    "every input motif color survives the authoritative quadrant mosaic",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

PALETTE_KINDS = ("canonical", "low", "high", "mixed")
POSITION_STYLES = ("outer", "inner")
PALETTES = {
    "canonical": (2, 5, 7, 9),
    "low": (1, 2, 3, 4),
    "high": (6, 7, 8, 9),
    "mixed": (1, 4, 6, 8),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical/broad profile",
        "valid": "8..14",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical/broad profile",
        "valid": "8..14",
        "doc": "Input grid width.",
    },
    "n_motifs": {
        "type": "int",
        "default": "scheduled 3 or 4",
        "valid": "3..4",
        "doc": "Number of occupied source quadrants.",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(PALETTE_KINDS),
        "doc": "One of four observable fixed four-color families.",
    },
    "position_style": {
        "type": "str",
        "default": "scheduled",
        "valid": "|".join(POSITION_STYLES),
        "doc": "Align motif boxes to the outer or inner corner of each source quadrant.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

SCHEDULE_PROFILES = (
    "omit_tl",
    "omit_tr",
    "omit_bl",
    "omit_br",
    "all_four",
)

# The first four profiles deliberately match the four canonical (height, width,
# palette-size) signatures measured by the profile floor.  Five consecutive
# generated pairs include every missing-quadrant case plus a four-object case.
_PROFILE_SPECS = {
    "omit_tl": {
        "missing": 0,
        "dims": (8, 8),
        "n_motifs": 3,
        "palette_kind": "canonical",
        "position_style": "outer",
    },
    "omit_tr": {
        "missing": 1,
        "dims": (9, 9),
        "n_motifs": 3,
        "palette_kind": "low",
        "position_style": "inner",
    },
    "omit_bl": {
        "missing": 2,
        "dims": (9, 10),
        "n_motifs": 3,
        "palette_kind": "high",
        "position_style": "outer",
    },
    "omit_br": {
        "missing": 3,
        "dims": (10, 10),
        "n_motifs": 3,
        "palette_kind": "mixed",
        "position_style": "inner",
    },
    "all_four": {
        "missing": None,
        "dims": None,
        "n_motifs": 4,
        "palette_kind": "canonical",
        "position_style": "outer",
    },
}

_DIFFICULTY_DIMS = {
    None: (11, 11),
    "easy": (8, 10),
    "medium": (11, 12),
    "hard": (13, 14),
}
_SIZE_OPTIONS = {
    None: (3, 4, 5, 6),
    "easy": (3, 3, 4),
    "medium": (3, 4, 5),
    "hard": (4, 5, 6),
}
_QUADRANT_NAMES = ("tl", "tr", "bl", "br")
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_DOMAINS = {
    "grid_h": (8, 14),
    "grid_w": (8, 14),
    "n_motifs": (3, 4),
}
_ENUM_DOMAINS = {
    "palette_kind": PALETTE_KINDS,
    "position_style": POSITION_STYLES,
}


def _connected(cells: set[tuple[int, int]]) -> bool:
    pending = [next(iter(cells))]
    seen = {pending[0]}
    while pending:
        row, col = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (row + dr, col + dc)
            if point in cells and point not in seen:
                seen.add(point)
                pending.append(point)
    return len(seen) == len(cells)


def _normalized(cells: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All normalized 3..6-cell polyominoes inside 3x3, excluding 3x3 bboxes.

    Excluding a full 3x3 bounding box guarantees that ``outer`` and ``inner``
    remain distinguishable even in the minimum 8x8 canvas, whose safe quadrant
    regions are exactly 3x3.
    """
    points = tuple((row, col) for row in range(3) for col in range(3))
    result: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 7):
        shapes = set()
        for chosen in combinations(points, size):
            cells = set(chosen)
            if not _connected(cells):
                continue
            shape = _normalized(cells)
            height = max(row for row, _ in shape) + 1
            width = max(col for _, col in shape) + 1
            if (height, width) == (3, 3):
                continue
            shapes.add(shape)
        if not shapes:
            raise RuntimeError(f"no constructive shape catalog for size {size}")
        result[size] = tuple(sorted(shapes))
    return result


_SHAPES_BY_SIZE = _shape_catalog()


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the five-state teaching profile selected by sample-index residue."""
    del seed
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    for name, (low, high) in _INT_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not low <= value <= high:
            raise ValueError(
                f"{name} must be a literal integer in {low}..{high}"
            )
    for name, options in _ENUM_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not str or value not in options:
            raise ValueError(f"{name} must be one of {options}")


def _draw_int_axis(ctx, name: str, default: int) -> int:
    low, high = _INT_DOMAINS[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_int(name, default, default)


def _draw_enum_axis(ctx, name: str, default: str) -> str:
    options = _ENUM_DOMAINS[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (default,))


def _safe_quadrants(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Inclusive rectangles separated by one (odd) or two (even) center lines."""
    top_last = height // 2 - (1 if height % 2 else 2)
    bottom_first = height // 2 + 1
    left_last = width // 2 - (1 if width % 2 else 2)
    right_first = width // 2 + 1
    quadrants = (
        (0, top_last, 0, left_last),
        (0, top_last, right_first, width - 1),
        (bottom_first, height - 1, 0, left_last),
        (bottom_first, height - 1, right_first, width - 1),
    )
    if any(r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3 for r0, r1, c0, c1 in quadrants):
        raise ValueError("grid dimensions cannot fit four separated 3x3 quadrant regions")
    return quadrants


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _placement_origin(
    rect: tuple[int, int, int, int],
    shape_dims: tuple[int, int],
    quadrant: int,
    style: str,
) -> tuple[int, int]:
    r0, r1, c0, c1 = rect
    shape_h, shape_w = shape_dims
    top = r0
    bottom = r1 - shape_h + 1
    left = c0
    right = c1 - shape_w + 1
    if style == "outer":
        return ((top, left), (top, right), (bottom, left), (bottom, right))[quadrant]
    if style == "inner":
        return ((bottom, right), (bottom, left), (top, right), (top, left))[quadrant]
    raise ValueError(f"unknown position style: {style}")


def _selected_quadrants(ctx, profile: str, n_motifs: int) -> tuple[int, ...]:
    if n_motifs == 4:
        return (0, 1, 2, 3)
    missing = _PROFILE_SPECS[profile]["missing"]
    if missing is None:
        missing = ctx.draw_rng("missing_quadrant").randrange(4)
    return tuple(index for index in range(4) if index != missing)


def _assigned_colors(ctx, palette_kind: str, n_motifs: int) -> tuple[int, ...]:
    base = tuple(PALETTES[palette_kind][:n_motifs])
    # Canonical examples happen to place ascending colors in quadrant order.
    # Excluding that one permutation makes every generated input an explicit
    # counterexample to the otherwise canonical-fitting color-order shortcut.
    alternatives = tuple(order for order in permutations(base) if order != base)
    return ctx.draw_rng("quadrant_color_order").choice(alternatives)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    spec = _PROFILE_SPECS[profile]
    default_dims = spec["dims"] or _DIFFICULTY_DIMS[difficulty]

    height = _draw_int_axis(ctx, "grid_h", default_dims[0])
    width = _draw_int_axis(ctx, "grid_w", default_dims[1])
    n_motifs = _draw_int_axis(ctx, "n_motifs", spec["n_motifs"])
    palette_kind = _draw_enum_axis(ctx, "palette_kind", spec["palette_kind"])
    position_style = _draw_enum_axis(ctx, "position_style", spec["position_style"])

    quadrants = _safe_quadrants(height, width)
    selected = _selected_quadrants(ctx, profile, n_motifs)
    colors = _assigned_colors(ctx, palette_kind, n_motifs)
    grid = full_grid(height, width, 0)

    for color, quadrant in zip(colors, selected):
        rng = ctx.draw_rng(f"shape_q{quadrant}")
        size = rng.choice(_SIZE_OPTIONS[difficulty])
        shape = rng.choice(_SHAPES_BY_SIZE[size])
        origin = _placement_origin(
            quadrants[quadrant], _shape_dims(shape), quadrant, position_style
        )
        for dr, dc in shape:
            row, col = origin[0] + dr, origin[1] + dc
            if grid[row][col] != 0:
                raise RuntimeError("constructive quadrant placement collided")
            grid[row][col] = color

    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    bad = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    return ["grid colors must be literal integers in 0..9"] if bad else []


def _objects(grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    motifs = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            motifs.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "size": len(cells),
                }
            )
    return motifs


def _quadrant(obj: dict[str, Any], height: int, width: int) -> int:
    cells = obj["cells"]
    top = 2 * sum(row for row, _ in cells) < len(cells) * (height - 1)
    left = 2 * sum(col for _, col in cells) < len(cells) * (width - 1)
    return (0 if top else 2) + (0 if left else 1)


def _crop(grid, obj: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = obj["bbox"]
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def _mosaic(shapes: list[list[list[int]] | None]) -> list[list[int]]:
    tl, tr, bl, br = shapes
    top_h = max(len(tl) if tl else 1, len(tr) if tr else 1)
    bottom_h = max(len(bl) if bl else 1, len(br) if br else 1)
    left_w = max(len(tl[0]) if tl else 1, len(bl[0]) if bl else 1)
    right_w = max(len(tr[0]) if tr else 1, len(br[0]) if br else 1)
    output = full_grid(top_h + 1 + bottom_h, left_w + 1 + right_w, 0)

    def paste(shape, row0, col0):
        if shape is None:
            return
        for row, values in enumerate(shape):
            for col, value in enumerate(values):
                if value != 0:
                    output[row0 + row][col0 + col] = value

    paste(tl, 0, 0)
    paste(tr, 0, left_w + 1)
    paste(bl, top_h + 1, 0)
    paste(br, top_h + 1, left_w + 1)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected Racket authority on ordinary grids."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    slots: list[list[list[int]] | None] = [None, None, None, None]
    for obj in _objects(grid):
        quadrant = _quadrant(obj, height, width)
        if slots[quadrant] is None:  # Racket keeps (first quadrant-list).
            slots[quadrant] = _crop(grid, obj)
    return _mosaic(slots)


def _pack_by_color(grid) -> list[list[int]]:
    motifs = sorted(_objects(grid), key=lambda obj: obj["color"])
    shapes: list[list[list[int]] | None] = [None, None, None, None]
    for index, obj in enumerate(motifs[:4]):
        shapes[index] = _crop(grid, obj)
    return _mosaic(shapes)


def _compress_occupied_quadrants(grid) -> list[list[int]]:
    motifs = _objects(grid)  # row-major motif order
    shapes: list[list[list[int]] | None] = [None, None, None, None]
    for index, obj in enumerate(motifs[:4]):
        shapes[index] = _crop(grid, obj)
    return _mosaic(shapes)


def analyze_grid(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    height, width = len(grid), len(grid[0])
    motifs = _objects(grid)
    quadrants = tuple(_quadrant(obj, height, width) for obj in motifs)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_motifs": len(motifs),
        "colors": tuple(obj["color"] for obj in motifs),
        "quadrants": quadrants,
        "sizes": tuple(obj["size"] for obj in motifs),
        "bboxes": tuple(obj["bbox"] for obj in motifs),
    }


def _infer_palette_kind(colors: set[int], n_motifs: int) -> str:
    matches = [
        name
        for name, palette in PALETTES.items()
        if colors == set(palette[:n_motifs])
    ]
    if len(matches) != 1:
        raise ValueError(f"cannot infer palette_kind from colors {sorted(colors)}")
    return matches[0]


def _infer_position_style(grid, motifs: list[dict[str, Any]]) -> str:
    height, width = len(grid), len(grid[0])
    quadrants = _safe_quadrants(height, width)
    matches = []
    for style in POSITION_STYLES:
        good = True
        for obj in motifs:
            quadrant = _quadrant(obj, height, width)
            r0, c0, r1, c1 = obj["bbox"]
            expected = _placement_origin(
                quadrants[quadrant], (r1 - r0 + 1, c1 - c0 + 1), quadrant, style
            )
            if (r0, c0) != expected:
                good = False
                break
        if good:
            matches.append(style)
    if len(matches) != 1:
        raise ValueError(f"cannot infer unique position_style; candidates={matches}")
    return matches[0]


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from returned pixels."""
    analysis = analyze_grid(grid)
    motifs = _objects(grid)
    colors = {obj["color"] for obj in motifs}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_motifs": analysis["n_motifs"],
        "palette_kind": _infer_palette_kind(colors, analysis["n_motifs"]),
        "position_style": _infer_position_style(grid, motifs),
    }


def strict_canonical_like(grid) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 14 or not 8 <= width <= 14:
        errors.append(f"dimensions must be within 8..14, got {height}x{width}")

    motifs = _objects(grid)
    if not 3 <= len(motifs) <= 4:
        errors.append(f"expected 3-4 motifs, got {len(motifs)}")
    colors = [obj["color"] for obj in motifs]
    if len(colors) != len(set(colors)):
        errors.append("motif colors must be distinct")
    bad_sizes = [obj["size"] for obj in motifs if not 3 <= obj["size"] <= 6]
    if bad_sizes:
        errors.append(f"motif sizes must be 3..6, got {bad_sizes}")

    quadrants = [_quadrant(obj, height, width) for obj in motifs]
    if len(quadrants) != len(set(quadrants)):
        errors.append(
            "at most one motif may occupy each centroid quadrant; got "
            f"{[_QUADRANT_NAMES[index] for index in quadrants]}"
        )

    if motifs and len(quadrants) == len(set(quadrants)):
        input_colors = set(colors)
        output_colors = {
            value for row in rule_mirror(grid) for value in row if value != 0
        }
        if input_colors != output_colors:
            errors.append(
                f"authority would lose colors: input={sorted(input_colors)} "
                f"output={sorted(output_colors)}"
            )
    return errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = strict_canonical_like(grid)
    supplied = (meta or {}).get("overrides", {})
    if supplied and not errors:
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for name, expected in supplied.items():
                if name in AXES and expected is not None and observed[name] != expected:
                    errors.append(
                        f"override {name}={expected!r} not observed; "
                        f"got {observed[name]!r}"
                    )
    return errors


def _rival_differs(rival: Callable[[Any], Any], grid) -> bool:
    return rival(grid) != rule_mirror(grid)


def _three_motif_branch(grid) -> bool:
    return len(_objects(grid)) == 3


def _four_motif_branch(grid) -> bool:
    return len(_objects(grid)) == 4


def _position_branch(style: str) -> Callable[[Any], bool]:
    def predicate(grid) -> bool:
        try:
            return observe_overrides(grid)["position_style"] == style
        except ValueError:
            return False

    return predicate


SEMANTIC_RIVALS = {
    "pack_by_color_into_leading_slots": _pack_by_color,
    "compress_occupied_quadrants": _compress_occupied_quadrants,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
# Only the color-sorted shortcut fits every canonical pair.  The compressed-
# quadrant program remains a useful generated-lesson competitor, but declaring
# it as a canonical shortcut would overstate the ambiguity in the source task.
CANONICAL_SHORTCUTS = {
    "pack_by_color_into_leading_slots": _pack_by_color,
}

SEMANTIC_WITNESSES = {
    "counterexample_to_color_sorted_packing": lambda grid: _rival_differs(
        _pack_by_color, grid
    ),
    "counterexample_to_compressed_quadrants": lambda grid: _rival_differs(
        _compress_occupied_quadrants, grid
    ),
    "three_motif_branch": _three_motif_branch,
    "four_motif_branch": _four_motif_branch,
    "outer_placement_branch": _position_branch("outer"),
    "inner_placement_branch": _position_branch("inner"),
}
WITNESS_RIVALS = {
    "counterexample_to_color_sorted_packing": [
        "pack_by_color_into_leading_slots"
    ],
    "counterexample_to_compressed_quadrants": [
        "compress_occupied_quadrants"
    ],
}
BRANCH_WITNESSES = {
    "three_motif_branch",
    "four_motif_branch",
    "outer_placement_branch",
    "inner_placement_branch",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject only measured ambiguity against the declared finite rivals."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(
            rival(pair["input"]) == pair["output"] for pair in demos
        )
        if fits_demos and rival(query["input"]) != query["output"]:
            reasons.append(
                f"declared rival {name} fits every demonstration but changes the query"
            )
    return reasons
