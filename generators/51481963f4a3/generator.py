"""Semantic generator for ARC task 51481963f4a3.

Every nonzero 4-connected object whose color is 1 is a query.  Its exact
translation-normalized shape identifies one non-1 template object, and the
query is recolored to that template's color.  Generated scenes are
constructive: every query has exactly one match, every template is used, and
multi-template scenes contain equal-area shape confusors so area alone cannot
solve the task.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "51481963f4a3"
TASK_ID = "51481963f4a3"
VERSION = "3.0.0"
RULE_HASH = "560348b96220"
SUMMARY = (
    "Recolor each color-1 object with the color of the uniquely matching "
    "non-1 template object's exact normalized shape."
)
INVARIANTS = [
    "literal color 0 is the background and literal color 1 marks every query",
    "objects are monochrome 4-connected components and distinct colors never touch by an edge",
    "template normalized shapes are pairwise distinct",
    "every color-1 query has exactly one equal normalized template shape",
    "every template shape is used by at least one query",
    "every generated input changes under the canonical rule",
    "multi-template lessons include at least two templates with equal cell count",
    "lessons with at least three templates also include more than one object area",
    "the five-template lesson repeats a template color across two different shapes",
    "the repeated-query lesson uses one template shape for two separate queries",
]

SCENE_PROFILES = (
    "single_match",
    "two_bijection",
    "three_bijection",
    "four_bijection",
    "five_shared_color",
    "repeated_query",
)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform over six exact observable shape-matching lessons",
        "valid": "single_match|two_bijection|three_bijection|four_bijection|five_shared_color|repeated_query",
    }
}

# Representatives span areas two through six and distinct free-polyomino D4
# orbits.  Multi-template lessons deliberately choose an equal-area pair of
# different shapes, then add different-area shapes when the profile has room.
# Thus neither a fixed object size nor cell count can stand in for exact shape.
_SHAPE_CATALOG = (
    ((0, 0), (0, 1)),  # domino, area 2
    ((0, 0), (0, 1), (0, 2)),  # I triomino, area 3
    ((0, 0), (1, 0), (1, 1)),  # L triomino, area 3
    ((0, 0), (0, 1), (1, 0), (1, 1)),  # O tetromino, area 4
    ((0, 0), (0, 1), (0, 2), (1, 1)),  # T tetromino, area 4
    ((0, 0), (1, 0), (2, 0), (2, 1)),  # L tetromino, area 4
    ((0, 0), (0, 1), (1, 1), (1, 2)),  # S tetromino, area 4
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),  # X pentomino
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),  # U pentomino
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),  # W pentomino
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),  # P pentomino
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),  # T pentomino
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),  # V pentomino
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),  # rectangle, area 6
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),  # hook, area 6
)

_SHAPE_GROUPS = {
    2: (0,),
    3: (1, 2),
    4: (3, 4, 5, 6),
    5: (7, 8, 9, 10, 11, 12),
    6: (13, 14),
}
_PAIRABLE_AREAS = tuple(
    area for area, indices in _SHAPE_GROUPS.items() if len(indices) >= 2
)

_PROFILE_COUNTS = {
    "single_match": (1, (0,)),
    "two_bijection": (2, (0, 1)),
    "three_bijection": (3, (0, 1, 2)),
    "four_bijection": (4, (0, 1, 2, 3)),
    "five_shared_color": (5, (0, 1, 2, 3, 4)),
    "repeated_query": (3, (0, 0, 1, 2)),
}

# (rows, columns) of 3x3 object slots.  Every pair is exact and constructive;
# no placement retry, shrinking, clamping, or fallback path exists.
_LAYOUTS = {
    2: ((1, 2), (2, 1)),
    4: ((1, 4), (2, 2), (4, 1)),
    6: ((2, 3), (3, 2)),
    7: ((2, 4), (4, 2), (3, 3)),
    8: ((2, 4), (4, 2), (3, 3)),
    10: ((2, 5), (5, 2), (3, 4), (4, 3)),
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _normalize(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    row0, col0 = min(rows), min(cols)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _transform_shape(shape, code):
    transformed = []
    for row, col in shape:
        if code == 0:
            point = (row, col)
        elif code == 1:
            point = (col, -row)
        elif code == 2:
            point = (-row, -col)
        elif code == 3:
            point = (-col, row)
        elif code == 4:
            point = (row, -col)
        elif code == 5:
            point = (-col, -row)
        elif code == 6:
            point = (-row, col)
        elif code == 7:
            point = (col, row)
        else:  # internal programming error, never caller-controlled
            raise ValueError(f"unknown D4 transform {code}")
        transformed.append(point)
    return _normalize(transformed)


def _shape_extent(shape):
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _select_template_shapes(template_count, rng):
    if template_count == 1:
        selected = [rng.randrange(len(_SHAPE_CATALOG))]
    else:
        pair_area = rng.choice(_PAIRABLE_AREAS)
        selected = list(rng.sample(_SHAPE_GROUPS[pair_area], 2))

        # For three or more templates, add other areas before any remaining
        # shape of the paired area.  This guarantees within-scene size range
        # while preserving the equal-area exact-shape confusor.
        other_areas = [
            index
            for area, indices in _SHAPE_GROUPS.items()
            if area != pair_area
            for index in indices
        ]
        same_area = [
            index
            for index in _SHAPE_GROUPS[pair_area]
            if index not in selected
        ]
        rng.shuffle(other_areas)
        rng.shuffle(same_area)
        selected.extend((other_areas + same_area)[: template_count - 2])

    rng.shuffle(selected)
    return [
        _transform_shape(_SHAPE_CATALOG[index], rng.randrange(8))
        for index in selected
    ]


def _profile_palette(profile, template_count, rng):
    if profile != "five_shared_color":
        return list(rng.sample(range(2, 10), template_count))
    distinct = list(rng.sample(range(2, 10), 4))
    duplicate_index = rng.randrange(4)
    colors = distinct + [distinct[duplicate_index]]
    rng.shuffle(colors)
    return colors


def _spacing(difficulty, rng):
    if difficulty == "easy":
        return 1, 1
    if difficulty == "medium":
        return rng.choice((1, 2)), 1
    if difficulty == "hard":
        return 2, 2
    return rng.choice((1, 2)), rng.choice((1, 2))


def _paint(grid, origin, shape, color):
    row0, col0 = origin
    for row, col in shape:
        grid[row0 + row][col0 + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, exact, semantically complete input grid."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    template_count, query_assignments = _PROFILE_COUNTS[profile]

    shape_rng = ctx.draw_rng("shape_selection")
    shapes = _select_template_shapes(template_count, shape_rng)

    colors = _profile_palette(
        profile, template_count, ctx.draw_rng("template_palette")
    )
    scene_items = [
        {"shape": shapes[index], "color": colors[index]}
        for index in range(template_count)
    ]
    scene_items.extend(
        {"shape": shapes[index], "color": 1}
        for index in query_assignments
    )

    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(scene_items)
    slot_rows, slot_cols = layout_rng.choice(_LAYOUTS[len(scene_items)])
    border, gap = _spacing(difficulty, ctx.draw_rng("spacing"))
    height = 2 * border + 3 * slot_rows + gap * (slot_rows - 1)
    width = 2 * border + 3 * slot_cols + gap * (slot_cols - 1)
    grid = [[0 for _ in range(width)] for _ in range(height)]

    slots = [
        (row, col)
        for row in range(slot_rows)
        for col in range(slot_cols)
    ]
    layout_rng.shuffle(slots)
    for obj, (slot_row, slot_col) in zip(scene_items, slots):
        shape = obj["shape"]
        shape_h, shape_w = _shape_extent(shape)
        offset_row = layout_rng.randint(0, 3 - shape_h)
        offset_col = layout_rng.randint(0, 3 - shape_w)
        origin = (
            border + slot_row * (3 + gap) + offset_row,
            border + slot_col * (3 + gap) + offset_col,
        )
        _paint(grid, origin, shape, obj["color"])

    return grid


def _component_records(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    records = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for drow, dcol in _NEIGHBORS4:
                    neighbor = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            signature = _normalize(cells)
            records.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "shape": signature,
                    "size": len(cells),
                    "extent": _shape_extent(signature),
                }
            )
    return records


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list or tuple of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty lists or tuples"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed the ARC 30x30 limit"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9 (not booleans)"]
    if not any(value == 0 for row in grid for value in row):
        return ["literal color 0 background is missing"]
    return []


def _classify_profile(templates, queries):
    template_count = len(templates)
    query_count = len(queries)
    template_colors = [obj["color"] for obj in templates]
    query_counts = Counter(obj["shape"] for obj in queries)
    one_each = set(query_counts.values()) == {1}

    if template_count == 1 and query_count == 1 and one_each:
        return "single_match"
    if (
        template_count == 2
        and query_count == 2
        and one_each
        and len(set(template_colors)) == 2
    ):
        return "two_bijection"
    if (
        template_count == 3
        and query_count == 3
        and one_each
        and len(set(template_colors)) == 3
    ):
        return "three_bijection"
    if (
        template_count == 4
        and query_count == 4
        and one_each
        and len(set(template_colors)) == 4
    ):
        return "four_bijection"
    if (
        template_count == 5
        and query_count == 5
        and one_each
        and sorted(Counter(template_colors).values()) == [1, 1, 1, 2]
    ):
        return "five_shared_color"
    if (
        template_count == 3
        and query_count == 4
        and sorted(query_counts.values()) == [1, 1, 2]
        and len(set(template_colors)) == 3
    ):
        return "repeated_query"
    return None


def _analyze_scene(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for drow, dcol in ((1, 0), (0, 1)):
                other_row, other_col = row + drow, col + dcol
                if (
                    other_row < height
                    and other_col < width
                    and grid[other_row][other_col] not in (0, color)
                ):
                    errors.append(
                        "distinct-colored objects touch along an edge"
                    )
                    break
            if errors:
                break
        if errors:
            break

    component_records = _component_records(grid)
    templates = [obj for obj in component_records if obj["color"] != 1]
    queries = [obj for obj in component_records if obj["color"] == 1]
    if not templates:
        errors.append("no non-1 template object")
    if not queries:
        errors.append("no color-1 query object")

    template_shapes = [obj["shape"] for obj in templates]
    shape_counts = Counter(template_shapes)
    if any(count != 1 for count in shape_counts.values()):
        errors.append("template normalized shapes must be pairwise distinct")

    template_by_shape = {
        obj["shape"]: obj for obj in templates if shape_counts[obj["shape"]] == 1
    }
    used_shapes = set()
    for query in queries:
        match = template_by_shape.get(query["shape"])
        if match is None:
            errors.append(
                "a color-1 query lacks exactly one equal normalized template shape"
            )
            break
        used_shapes.add(query["shape"])
    if templates and used_shapes != set(template_shapes):
        errors.append("at least one template shape is unused by the queries")

    if len(templates) > 1:
        size_counts = Counter(obj["size"] for obj in templates)
        if max(size_counts.values(), default=0) < 2:
            errors.append(
                "multi-template scene lacks an equal-area shape confusor"
            )

    profile = None if errors else _classify_profile(templates, queries)
    if not errors and profile is None:
        errors.append("scene does not match any supported exact lesson profile")

    return {
        "errors": errors,
        "components": component_records,
        "templates": templates,
        "queries": queries,
        "template_by_shape": template_by_shape,
        "profile": profile,
        "height": height,
        "width": width,
    }


def observe_overrides(grid):
    """Recover the exact declared semantic profile from a valid returned grid."""
    info = _analyze_scene(grid)
    if info.get("errors") or info.get("profile") is None:
        return {}
    return {"scene_profile": info["profile"]}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject inputs outside the exact, mutation-sensitive lesson grammar."""
    errors = list(_analyze_scene(grid).get("errors", ()))
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append("unknown difficulty band")
    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict) and "scene_profile" in requested:
            observed = observe_overrides(grid).get("scene_profile")
            if observed != requested["scene_profile"]:
                errors.append(
                    f"scene_profile observed {observed!r}, requested "
                    f"{requested['scene_profile']!r}"
                )
    return errors


def rule_mirror(grid):
    """Pure Python mirror of the canonical Racket transformation."""
    info = _analyze_scene(grid)
    if info.get("errors"):
        raise ValueError("invalid shape-matching input: " + "; ".join(info["errors"]))
    output = [list(row) for row in grid]
    for query in info["queries"]:
        color = info["template_by_shape"][query["shape"]]["color"]
        for row, col in query["cells"]:
            output[row][col] = color
    return output
