"""Generator for Bounding-Box Corners (task ``47993d3762b9``).

For every non-background color, compute the bounding box of all cells of that
color and emit only its four corners on a fresh background-zero canvas.

The teaching schedule deliberately includes examples where the extrema are
spread across four non-corner cells.  Those examples distinguish the true
all-cells bounding-box rule from the tempting shortcut "take two diagonal
endpoints and complete their rectangle".
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "47993d3762b9"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b7993576241a"  # whitespace-normalized canonical program_solution
SUMMARY = (
    "For each nonzero color independently, use every cell of that color to "
    "find its axis-aligned bounding box, clear the canvas, and paint the four "
    "bounding-box corners in that color. Normal lessons cycle through diagonal "
    "endpoint pairs, edge distractors, interior distractors, and distributed "
    "extrema with no input corner pair."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

HELPFUL_TEXTURES = (
    "opposite_pair",
    "edge_distractors",
    "interior_distractors",
    "distributed_extrema",
)
SCHEDULE_PROFILES = HELPFUL_TEXTURES

INVARIANTS = [
    "background is 0 and all other cells are ARC colors 1..9",
    "normal draws contain 2..4 distinct non-background colors",
    "each color has a non-degenerate bbox spanning at least 3 rows and 3 columns",
    "each color is missing at least one bbox corner, so the transformation is visible",
    "bbox-corner coordinates of different colors never conflict",
]

# Only controls that are exactly recoverable from the returned grid are public.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 7..14",
        "valid": "7..14",
    },
    "n_colors": {
        "type": "int",
        "default": "2 easy; 2..3 medium; 3..4 hard",
        "valid": "2..4",
    },
    "texture": {
        "type": "str",
        "default": "sample_index schedule over four helpful families",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_BAND_RANGES = {
    None: ((7, 11), (8, 12), (2, 3)),
    "easy": ((7, 9), (8, 11), (2, 2)),
    "medium": ((8, 11), (8, 12), (2, 3)),
    "hard": ((9, 14), (9, 14), (3, 4)),
}


def _draw_axis_int(ctx, label: str, valid: tuple[int, int], default: tuple[int, int]) -> int:
    """Honor declared boundaries while retaining narrower default bands."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *default)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the residue-scheduled texture; seed/difficulty do not alter it."""
    del seed, difficulty
    return HELPFUL_TEXTURES[int(sample_index) % len(HELPFUL_TEXTURES)]


def _split_interval(length: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Split an interval into two >=3-cell regions separated by one cell."""
    middle = length // 2
    first = (0, middle - 1)
    second = (middle + 1, length - 1)
    if first[1] - first[0] + 1 < 3 or second[1] - second[0] + 1 < 3:
        raise ValueError(f"length {length} cannot hold two 3-cell regions with a gap")
    return first, second


def _layout_slots(height: int, width: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    """Return disjoint placement slots, each at least 3x3."""
    rows = _split_interval(height)
    cols = _split_interval(width)
    quadrants = [
        (rows[0][0], cols[0][0], rows[0][1], cols[0][1]),
        (rows[0][0], cols[1][0], rows[0][1], cols[1][1]),
        (rows[1][0], cols[0][0], rows[1][1], cols[0][1]),
        (rows[1][0], cols[1][0], rows[1][1], cols[1][1]),
    ]
    if count >= 3:
        rng.shuffle(quadrants)
        return quadrants[:count]

    horizontal = [
        (0, cols[0][0], height - 1, cols[0][1]),
        (0, cols[1][0], height - 1, cols[1][1]),
    ]
    vertical = [
        (rows[0][0], 0, rows[0][1], width - 1),
        (rows[1][0], 0, rows[1][1], width - 1),
    ]
    diagonal = rng.choice(
        [
            [quadrants[0], quadrants[3]],
            [quadrants[1], quadrants[2]],
        ]
    )
    return rng.choice([horizontal, vertical, diagonal])


def _choose_bbox(slot: tuple[int, int, int, int], rng) -> tuple[int, int, int, int]:
    rlo, clo, rhi, chi = slot
    slot_h = rhi - rlo + 1
    slot_w = chi - clo + 1
    box_h = rng.randint(3, min(slot_h, 7))
    box_w = rng.randint(3, min(slot_w, 7))
    top = rng.randint(rlo, rhi - box_h + 1)
    left = rng.randint(clo, chi - box_w + 1)
    return top, left, top + box_h - 1, left + box_w - 1


def _opposite_pairs(box: tuple[int, int, int, int]):
    top, left, bottom, right = box
    return (
        ((top, left), (bottom, right)),
        ((top, right), (bottom, left)),
    )


def _cells_for_texture(
    box: tuple[int, int, int, int], texture: str, rng
) -> tuple[tuple[int, int], ...]:
    top, left, bottom, right = box
    pair = rng.choice(_opposite_pairs(box))
    if texture == "opposite_pair":
        return tuple(pair)

    if texture == "edge_distractors":
        edge_choices = [
            (top, rng.randint(left + 1, right - 1)),
            (bottom, rng.randint(left + 1, right - 1)),
            (rng.randint(top + 1, bottom - 1), left),
            (rng.randint(top + 1, bottom - 1), right),
        ]
        extra = rng.choice([cell for cell in edge_choices if cell not in pair])
        return tuple(pair) + (extra,)

    if texture == "interior_distractors":
        extra = (
            rng.randint(top + 1, bottom - 1),
            rng.randint(left + 1, right - 1),
        )
        return tuple(pair) + (extra,)

    if texture == "distributed_extrema":
        # No bbox corner is present. Four side cells independently establish
        # top, bottom, left and right, so no diagonal-endpoint shortcut works.
        return (
            (top, rng.randint(left + 1, right - 1)),
            (bottom, rng.randint(left + 1, right - 1)),
            (rng.randint(top + 1, bottom - 1), left),
            (rng.randint(top + 1, bottom - 1), right),
        )

    raise ValueError(f"unsupported texture: {texture!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")
    if difficulty not in _BAND_RANGES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_default, w_default, colors_default = _BAND_RANGES[difficulty]
    height = _draw_axis_int(ctx, "grid_h", (7, 14), h_default)
    width = _draw_axis_int(ctx, "grid_w", (7, 14), w_default)
    n_colors = _draw_axis_int(ctx, "n_colors", (2, 4), colors_default)

    if "texture" in overrides and overrides["texture"] is not None:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    else:
        texture = ctx.draw_choice(
            "texture", (schedule_profile(seed, sample_index, difficulty),)
        )

    layout_rng = ctx.draw_rng("layout")
    colors = layout_rng.sample(list(range(1, 10)), n_colors)
    slots = _layout_slots(height, width, n_colors, layout_rng)
    grid = full_grid(height, width, 0)
    for color, slot in zip(colors, slots):
        box = _choose_bbox(slot, layout_rng)
        cells = _cells_for_texture(box, texture, layout_rng)
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("internal placement collision")
            grid[row][col] = color
    return grid


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _corners(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    }


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return facts, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return facts, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return facts, ["grid must be rectangular with positive width"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return facts, ["all cells must be integer ARC colors 0..9"]

    height = len(grid)
    by_color: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                by_color[value].append((row, col))

    color_facts: dict[int, dict[str, Any]] = {}
    corner_owners: dict[tuple[int, int], list[int]] = defaultdict(list)
    for color, cells_list in sorted(by_color.items()):
        cells = set(cells_list)
        box = _bbox(cells)
        corners = _corners(box)
        top, left, bottom, right = box
        edge_noncorner = {
            cell
            for cell in cells
            if cell not in corners
            and (cell[0] in {top, bottom} or cell[1] in {left, right})
        }
        interior = {
            cell
            for cell in cells
            if top < cell[0] < bottom and left < cell[1] < right
        }
        for corner in corners:
            corner_owners[corner].append(color)
        color_facts[color] = {
            "cells": cells,
            "count": len(cells),
            "bbox": box,
            "bbox_h": bottom - top + 1,
            "bbox_w": right - left + 1,
            "corners": corners,
            "present_corners": cells & corners,
            "missing_corners": corners - cells,
            "edge_noncorner": edge_noncorner,
            "interior": interior,
            "touches_all_sides": (
                any(row == top for row, _ in cells)
                and any(row == bottom for row, _ in cells)
                and any(col == left for _, col in cells)
                and any(col == right for _, col in cells)
            ),
        }

    conflicts = {
        cell: tuple(colors)
        for cell, colors in corner_owners.items()
        if len(colors) > 1
    }
    facts.update(
        grid_h=height,
        grid_w=width,
        colors=tuple(sorted(by_color)),
        n_colors=len(by_color),
        by_color=color_facts,
        corner_conflicts=conflicts,
        nonbg_count=sum(len(cells) for cells in by_color.values()),
    )
    return facts, errors


def _texture_for_color(info: dict[str, Any]) -> str | None:
    cells = info["cells"]
    corners = info["corners"]
    box = info["bbox"]
    opposite_pairs = [set(pair) for pair in _opposite_pairs(box)]
    has_opposite_pair = any(pair <= cells for pair in opposite_pairs)

    if len(cells) == 2 and cells in opposite_pairs:
        return "opposite_pair"
    if (
        len(cells) == 3
        and has_opposite_pair
        and len(info["edge_noncorner"]) == 1
        and not info["interior"]
    ):
        return "edge_distractors"
    if (
        len(cells) == 3
        and has_opposite_pair
        and len(info["interior"]) == 1
        and not info["edge_noncorner"]
    ):
        return "interior_distractors"
    if (
        len(cells) == 4
        and not info["present_corners"]
        and info["touches_all_sides"]
        and not info["interior"]
    ):
        return "distributed_extrema"
    return None


def _observed_texture(facts: dict[str, Any]) -> str | None:
    textures = {_texture_for_color(info) for info in facts["by_color"].values()}
    if len(textures) == 1:
        return next(iter(textures))
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the non-degenerate task grammar and any requested exact axes."""
    del difficulty
    facts, errors = _analyze(grid)
    if errors:
        return errors

    if not 2 <= facts["n_colors"] <= 4:
        errors.append(f"expected 2..4 non-background colors, got {facts['n_colors']}")
    for color, info in facts["by_color"].items():
        if info["count"] < 2:
            errors.append(f"color {color} has {info['count']} cell(s); need at least 2")
        if info["bbox_h"] < 3 or info["bbox_w"] < 3:
            errors.append(
                f"color {color} bbox {info['bbox_h']}x{info['bbox_w']} is rule-hiding; "
                "need at least 3x3"
            )
        if not info["missing_corners"]:
            errors.append(f"color {color} already occupies all four bbox corners (no-op)")
        if not info["touches_all_sides"]:
            errors.append(f"color {color} does not visibly establish all four bbox sides")
    if facts["corner_conflicts"]:
        errors.append(
            "different colors claim the same output corner(s): "
            f"{facts['corner_conflicts']}"
        )

    requested = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        requested = nested if isinstance(nested, dict) else meta
    if isinstance(requested, dict) and requested:
        observed = {
            "grid_h": facts["grid_h"],
            "grid_w": facts["grid_w"],
            "n_colors": facts["n_colors"],
            "texture": _observed_texture(facts),
        }
        for axis in AXES:
            if axis in requested and requested[axis] is not None:
                if observed.get(axis) != requested[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as "
                        f"{observed.get(axis)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked manifold shared by canonical inputs and normal draws."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    errors.extend(self_check(grid))
    if not 7 <= facts["grid_h"] <= 14 or not 7 <= facts["grid_w"] <= 14:
        errors.append(
            f"canvas {facts['grid_h']}x{facts['grid_w']} lies outside 7..14"
        )
    if facts["nonbg_count"] > (facts["grid_h"] * facts["grid_w"]) // 3:
        errors.append("scene is too dense for the sparse canonical manifold")
    for color, info in facts["by_color"].items():
        if info["count"] > 8:
            errors.append(f"color {color} has {info['count']} cells; expected <=8")
        if info["bbox_h"] > 9 or info["bbox_w"] > 9:
            errors.append(f"color {color} bbox exceeds canonical-scale 9x9")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public exact axis from the returned grid."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    texture = _observed_texture(facts)
    if texture is None:
        raise ValueError("cannot observe texture: scene is not one generated family")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_colors": facts["n_colors"],
        "texture": texture,
    }


def rule_mirror(grid):
    """Python test mirror; canonical Racket remains the output authority."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for color, info in facts["by_color"].items():
        for row, col in info["corners"]:
            output[row][col] = color
    return output


def _identity_rival(grid):
    return [row[:] for row in grid]


def _diagonal_endpoints_rival(grid):
    """Complete a rectangle from the lexicographically first/farthest cells."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for color, info in facts["by_color"].items():
        cells = sorted(info["cells"])
        first = cells[0]
        farthest = max(
            cells[1:],
            key=lambda cell: (
                abs(cell[0] - first[0]) + abs(cell[1] - first[1]),
                cell,
            ),
        )
        top, bottom = sorted((first[0], farthest[0]))
        left, right = sorted((first[1], farthest[1]))
        for row, col in ((top, left), (top, right), (bottom, left), (bottom, right)):
            output[row][col] = color
    return output


def _texture_witness(name: str):
    def predicate(grid) -> bool:
        facts, errors = _analyze(grid)
        return not errors and _observed_texture(facts) == name

    return predicate


SEMANTIC_RIVALS = {
    "identity": _identity_rival,
    "diagonal_endpoints": _diagonal_endpoints_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    name: _texture_witness(name) for name in HELPFUL_TEXTURES
}
WITNESS_RIVALS = {
    "opposite_pair": ["identity"],
    "edge_distractors": ["identity"],
    "interior_distractors": ["identity"],
    "distributed_extrema": ["identity", "diagonal_endpoints"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-example window to kill the named shortcut rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    textures: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the bbox-corner rule")
        facts, errors = _analyze(pair["input"])
        texture = None if errors else _observed_texture(facts)
        if texture:
            textures.add(texture)
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the bbox-corner rule")
    missing = set(HELPFUL_TEXTURES) - textures
    if missing:
        reasons.append(f"demonstrations miss scheduled texture(s): {sorted(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
