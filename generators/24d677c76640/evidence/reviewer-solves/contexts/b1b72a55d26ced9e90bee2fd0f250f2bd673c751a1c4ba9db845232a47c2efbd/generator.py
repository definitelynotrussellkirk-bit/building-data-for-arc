"""Generator for arc_puzzle_bank_21_set10_s:S10_E4 — move shape to anchor.

The color-1 cell marks the destination for the top-left corner of the source
shape's bounding box.  The source is the one connected, monochromatic object
using a color other than 0 or 1.  The output contains only an exact translated
copy of that object on a black background.

Normal lessons cover all eight relative destination directions, including the
north-east branch used by two canonical pairs.  Source and destination bounding
boxes are disjoint, so every lesson is a genuine move rather than an identity or
an overlap/occlusion puzzle.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24d677c76640"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4358f37c5cb2"
SUMMARY = (
    "Find the single color-1 anchor and the single connected monochromatic "
    "object made from a nonzero, non-1 color. Translate every object cell by "
    "the vector that moves the object's bounding-box top-left corner onto the "
    "anchor. Output only the translated object on a black grid."
)
INVARIANTS = [
    "the background is 0, with exactly one color-1 anchor",
    "there is exactly one 4-connected monochromatic source object in color 2..9",
    "the anchor is a legal in-bounds destination for the source bbox top-left",
    "source and destination bounding boxes are disjoint and the translation is nonzero",
    "all eight relative anchor directions occur in the normal teaching schedule",
]

RELATIONS = ("nw", "n", "ne", "w", "e", "sw", "s", "se")

# IDs 0, 1, and 2 are the three exact canonical source morphologies.  The
# remaining entries are generalized connected witnesses, not claimed to be
# canonical.  Every bbox is at most 3x3 so every declared boundary combination
# remains constructible on a 7x7 grid.
SHAPES = (
    ((0, 0), (1, 0), (1, 1)),                          # canonical L (3)
    ((0, 0), (0, 1), (1, 1), (1, 2)),                  # canonical zigzag (4)
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),          # canonical plus (5)
    ((0, 0), (0, 1), (1, 0)),                          # corner (3)
    ((0, 0), (1, 0), (2, 0), (2, 1)),                  # J (4)
    ((0, 0), (0, 1), (0, 2), (1, 1)),                  # T (4)
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),          # bent stair (5)
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),          # U (5)
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),          # stair (5)
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),  # 3x2 block (6)
    ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2),
     (2, 0), (2, 1), (2, 2)),                          # ring (8)
)
SHAPE_TO_ID = {frozenset(shape): index for index, shape in enumerate(SHAPES)}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "rng 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "rng 7..12",
        "valid": "7..12",
    },
    "shape_id": {
        "type": "int",
        "default": "rng 0..11",
        "valid": "0..11",
    },
    "shape_color": {
        "type": "color",
        "default": "rng 2..9",
        "valid": "2..9",
    },
    "anchor_relation": {
        "type": "str",
        "default": "four-pair episode schedule over all eight relations",
        "valid": "|".join(RELATIONS),
    },
}


def _shape_dims(shape):
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rectangles_disjoint(left, right):
    ltop, lleft, lbottom, lright = left
    rtop, rleft, rbottom, rright = right
    return (
        lbottom < rtop
        or rbottom < ltop
        or lright < rleft
        or rright < lleft
    )


def _relation(dr, dc):
    vertical = "n" if dr < 0 else "s" if dr > 0 else ""
    horizontal = "w" if dc < 0 else "e" if dc > 0 else ""
    return vertical + horizontal


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for neighbor in (
            (row + 1, col),
            (row - 1, col),
            (row, col + 1),
            (row, col - 1),
        ):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _placement_candidates(height, width, shape, relation):
    shape_h, shape_w = _shape_dims(shape)
    candidates = []
    for source_row in range(height - shape_h + 1):
        for source_col in range(width - shape_w + 1):
            source_rect = (
                source_row,
                source_col,
                source_row + shape_h - 1,
                source_col + shape_w - 1,
            )
            for anchor_row in range(height - shape_h + 1):
                for anchor_col in range(width - shape_w + 1):
                    dr = anchor_row - source_row
                    dc = anchor_col - source_col
                    if _relation(dr, dc) != relation:
                        continue
                    destination_rect = (
                        anchor_row,
                        anchor_col,
                        anchor_row + shape_h - 1,
                        anchor_col + shape_w - 1,
                    )
                    if not _rectangles_disjoint(source_rect, destination_rect):
                        continue
                    candidates.append(
                        (source_row, source_col, anchor_row, anchor_col)
                    )
    return candidates


def _difficulty_candidates(candidates, difficulty):
    """Use translation distance as the difficulty effect without narrowing AXES."""
    by_distance = {}
    for candidate in candidates:
        source_row, source_col, anchor_row, anchor_col = candidate
        distance = abs(anchor_row - source_row) + abs(anchor_col - source_col)
        by_distance.setdefault(distance, []).append(candidate)
    distances = sorted(by_distance)
    if difficulty is None or len(distances) < 2:
        chosen_distances = distances
    else:
        n = len(distances)
        cut1 = max(1, (n + 2) // 3)
        cut2 = max(cut1 + 1, (2 * n + 2) // 3)
        cut2 = min(cut2, n)
        if difficulty == "easy":
            chosen_distances = distances[:cut1]
        elif difficulty == "medium":
            chosen_distances = distances[cut1:cut2] or distances[:cut1]
        else:
            chosen_distances = distances[cut2:] or distances[-cut1:]
    return [candidate for distance in chosen_distances for candidate in by_distance[distance]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, non-degenerate teaching input."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
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
    height = ctx.draw_int("grid_h", 7, 12)
    width = ctx.draw_int("grid_w", 7, 12)
    shape_id = ctx.draw_int("shape_id", 0, len(SHAPES) - 1)
    shape_color = ctx.draw_color("shape_color", exclude=(0, 1))

    # The runner materializes three demonstrations plus one query using
    # consecutive sample indexes.  Rotating the eight-relation cycle by seed
    # gives every lesson several directions while covering all relations across
    # episodes.  Explicit overrides remain exact and unrestricted.
    if "anchor_relation" in overrides and overrides["anchor_relation"] is not None:
        anchor_relation = ctx.draw_choice("anchor_relation", RELATIONS)
    else:
        scheduled = RELATIONS[(int(seed) + int(sample_index)) % len(RELATIONS)]
        anchor_relation = ctx.draw_choice("anchor_relation", (scheduled,))

    shape = SHAPES[shape_id]
    candidates = _placement_candidates(height, width, shape, anchor_relation)
    candidates = _difficulty_candidates(candidates, difficulty)
    if not candidates:
        raise ValueError(
            "requested axis combination has no disjoint in-bounds placement: "
            f"grid={height}x{width} shape_id={shape_id} relation={anchor_relation}"
        )
    source_row, source_col, anchor_row, anchor_col = ctx.draw_rng(
        "placement"
    ).choice(candidates)

    grid = full_grid(height, width, 0)
    for row, col in shape:
        grid[source_row + row][source_col + col] = shape_color
    grid[anchor_row][anchor_col] = 1

    expected = {
        "grid_h": height,
        "grid_w": width,
        "shape_id": shape_id,
        "shape_color": shape_color,
        "anchor_relation": anchor_relation,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"internal axis drift: expected={expected}, observed={observed}")
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal invalid scene: " + "; ".join(errors))
    return grid


def _analysis(grid):
    result = {"errors": []}
    errors = result["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("empty or non-list grid")
        return result
    height, width = len(grid), len(grid[0])
    result["grid_h"] = height
    result["grid_w"] = width
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("ragged grid")
        return result
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer colors 0..9")
        return result

    anchors = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    ]
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-1 anchor; found {len(anchors)}")

    colored = [
        (row, col, grid[row][col])
        for row in range(height)
        for col in range(width)
        if grid[row][col] not in (0, 1)
    ]
    if not colored:
        errors.append("expected one non-0/non-1 source object; found none")
        return result
    colors = {color for _, _, color in colored}
    if len(colors) != 1:
        errors.append(f"source object must be monochromatic; found colors {sorted(colors)}")
    shape_color = next(iter(colors)) if len(colors) == 1 else None
    cells = {(row, col) for row, col, _ in colored}
    if not _connected(cells):
        errors.append("source object must be one 4-connected component")
    if not 3 <= len(cells) <= 8:
        errors.append(f"source object must contain 3..8 cells; found {len(cells)}")

    source_top, source_left, source_bottom, source_right = _bbox(cells)
    shape_h = source_bottom - source_top + 1
    shape_w = source_right - source_left + 1
    if shape_h > 3 or shape_w > 3:
        errors.append(f"source bbox must be at most 3x3; found {shape_h}x{shape_w}")
    normalized = frozenset(
        (row - source_top, col - source_left) for row, col in cells
    )
    shape_id = SHAPE_TO_ID.get(normalized)
    if shape_id is None:
        errors.append("source morphology is outside the declared teaching shape bank")

    result.update(
        {
            "anchors": anchors,
            "shape_cells": cells,
            "shape_color": shape_color,
            "shape_id": shape_id,
            "source_bbox": (source_top, source_left, source_bottom, source_right),
            "shape_h": shape_h,
            "shape_w": shape_w,
            "normalized_shape": normalized,
        }
    )

    if len(anchors) != 1:
        return result
    anchor_row, anchor_col = anchors[0]
    dr = anchor_row - source_top
    dc = anchor_col - source_left
    relation = _relation(dr, dc)
    result["anchor_relation"] = relation
    if relation not in RELATIONS:
        errors.append("anchor would create a zero-vector/identity translation")

    destination_cells = {(row + dr, col + dc) for row, col in cells}
    if any(not (0 <= row < height and 0 <= col < width) for row, col in destination_cells):
        errors.append("translated object would leave the grid")
    destination_bbox = (
        anchor_row,
        anchor_col,
        anchor_row + shape_h - 1,
        anchor_col + shape_w - 1,
    )
    result["destination_bbox"] = destination_bbox
    result["destination_cells"] = destination_cells
    if not _rectangles_disjoint(result["source_bbox"], destination_bbox):
        errors.append("source and destination bounding boxes must be disjoint")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, identity, clipping, and overlap lessons."""
    return list(_analysis(grid)["errors"])


def observe_overrides(grid):
    """Recover every exact declared axis from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "shape_id": analysis["shape_id"],
        "shape_color": analysis["shape_color"],
        "anchor_relation": analysis["anchor_relation"],
    }


def rule_mirror(grid):
    """Small Python parity mirror; production outputs still come from Racket."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    source_top, source_left, _, _ = analysis["source_bbox"]
    anchor_row, anchor_col = analysis["anchors"][0]
    dr = anchor_row - source_top
    dc = anchor_col - source_left
    for row, col in analysis["shape_cells"]:
        output[row + dr][col + dc] = analysis["shape_color"]
    return output
