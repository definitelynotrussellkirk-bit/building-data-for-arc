"""Generator for ARC task e50d258f / content hash 90870ec1dd92.

Every input is a 10x10 black canvas containing two or three separated, solid
multicolor rectangles.  The authoritative rule counts red (2) cells inside
each 8-connected non-background object and returns the bounding-box crop of
the unique maximum.

The ordinary schedule deliberately changes the winner's size relation and
texture so that "largest object", "smallest object", red-density, fixed
position, and modal-color shortcuts do not survive a three-demonstration
lesson.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "90870ec1dd92"
VERSION = "3.0.0"
TASK_ID = "90870ec1dd92"
RULE_HASH = "5fd3be80705d"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a 10x10 black canvas, place two or three separated solid rectangular "
    "8-connected objects using colors 1, 2, and 8. Count red (2) cells in "
    "each object. Exactly one object has the largest red count. Return that "
    "object's complete bounding-box crop, preserving its internal colors."
)

INVARIANTS = [
    "the input is a 10x10 rectangular grid with palette exactly {0,1,2,8}",
    "there are exactly two or three 8-connected nonzero objects",
    "every object is a completely filled axis-aligned rectangle",
    "objects are separated even under 8-connectivity",
    "red counts are all distinct and have one strict maximum",
    "every rectangle contains both non-red colors 1 and 8",
]

AXES = {
    "n_clusters": {
        "type": "int",
        "default": "scheduled 2|2|3 with difficulty-shaped variation",
        "valid": "2..3",
    },
    "winner_red_count": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
    },
    "red_gap": {
        "type": "int",
        "default": "1..2 gap over the runner-up",
        "valid": "1..2",
    },
    "winner_position": {
        "type": "str",
        "default": "rng over four canvas quadrants",
        "valid": "top_left|top_right|bottom_left|bottom_right",
    },
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_POSITIONS = ("top_left", "top_right", "bottom_left", "bottom_right")
_CARDINAL_AND_DIAGONAL = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# The three consecutive profiles are load-bearing: every materialized lesson
# receives consecutive sample indices, so it sees one winner-smaller scene,
# one winner-larger scene, and one middle-size/density-reversal scene.
SCHEDULE_PROFILES = ("winner_smaller", "winner_larger", "density_reversal")

_SMALL_SIZES = ((3, 3), (3, 4), (4, 3))
_MEDIUM_SIZES = ((4, 4), (5, 3), (3, 5), (4, 5), (5, 4))
_LARGE_SIZES = ((6, 3), (3, 6), (6, 4), (4, 6), (7, 3))
_HUGE_SIZES = ((7, 4), (6, 5), (5, 6))


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared semantic schedule branch for gate auditing."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("n_clusters", "winner_red_count", "red_gap"):
        value = overrides.get(label)
        if value is not None and (type(value) is not int):
            raise ValueError(f"{label} must be an integer")
    position = overrides.get("winner_position")
    if position is not None and type(position) is not str:
        raise ValueError("winner_position must be a string")


def _coerce_grid(grid):
    if not isinstance(grid, list):
        return grid
    return [
        [int(value) if isinstance(value, str) and value.isdigit() else value
         for value in row]
        if isinstance(row, (list, str))
        else row
        for row in grid
    ]


def _components_8(grid):
    h = len(grid)
    w = len(grid[0]) if grid else 0
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _CARDINAL_AND_DIAGONAL:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return tuple(sorted(components, key=lambda cells: cells[0]))


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _position_of_bbox(box):
    r0, c0, r1, c1 = box
    row_center = (r0 + r1) / 2
    col_center = (c0 + c1) / 2
    vertical = "top" if row_center < 5 else "bottom"
    horizontal = "left" if col_center < 5 else "right"
    return f"{vertical}_{horizontal}"


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    if not isinstance(grid, list) or not grid:
        return {"grid": grid, "h": 0, "w": 0, "rectangles": (), "winner": None}
    if not all(isinstance(row, list) for row in grid):
        return {"grid": grid, "h": len(grid), "w": 0, "rectangles": (), "winner": None}
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        return {"grid": grid, "h": len(grid), "w": w, "rectangles": (), "winner": None}

    rectangles = []
    for cells in _components_8(grid):
        box = _bbox(cells)
        r0, c0, r1, c1 = box
        counts = Counter(grid[r][c] for r, c in cells)
        rectangles.append({
            "cells": cells,
            "bbox": box,
            "height": r1 - r0 + 1,
            "width": c1 - c0 + 1,
            "area": len(cells),
            "bbox_area": (r1 - r0 + 1) * (c1 - c0 + 1),
            "counts": counts,
            "red": counts[2],
            "position": _position_of_bbox(box),
        })
    red_counts = [rect["red"] for rect in rectangles]
    winner = None
    if red_counts and red_counts.count(max(red_counts)) == 1:
        winner = red_counts.index(max(red_counts))
    return {
        "grid": grid,
        "h": len(grid),
        "w": w,
        "rectangles": tuple(rectangles),
        "winner": winner,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar while accepting every canonical input."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and len(row) > 0 for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    if not all(isinstance(row, list) for row in coerced):
        return ["grid rows must be lists or digit strings"]
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if (h, w) != (10, 10):
        errors.append(f"canonical canvas must be 10x10, found {h}x{w}")
    values = [value for row in coerced for value in row]
    if any(type(value) is not int or value not in (0, 1, 2, 8) for value in values):
        errors.append("grid values must be integer colors from {0,1,2,8}")
    if set(values) != {0, 1, 2, 8}:
        errors.append(f"palette must be exactly {{0,1,2,8}}, found {sorted(set(values))}")

    scene = _analyze_scene(coerced)
    rectangles = scene["rectangles"]
    if len(rectangles) not in (2, 3):
        errors.append(
            f"expected exactly 2 or 3 nonzero 8-connected objects, "
            f"found {len(rectangles)}"
        )
    for index, rect in enumerate(rectangles):
        if rect["area"] != rect["bbox_area"]:
            errors.append(f"object {index} must completely fill its bounding rectangle")
        if not (3 <= rect["height"] <= 7 and 3 <= rect["width"] <= 6):
            errors.append(
                f"object {index} dimensions {rect['height']}x{rect['width']} "
                "fall outside canonical 3..7 by 3..6 envelope"
            )
        missing = {1, 8} - set(rect["counts"])
        if missing:
            errors.append(f"object {index} must contain both colors 1 and 8")

    red_counts = [rect["red"] for rect in rectangles]
    if len(red_counts) != len(set(red_counts)):
        errors.append(f"object red counts must all be distinct, found {red_counts}")
    if scene["winner"] is None:
        errors.append("exactly one object must have the largest red count")
    elif red_counts[scene["winner"]] < 3:
        errors.append("winning object must contain at least three red cells")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict predicate for ordinary and canonical-scale scenes."""
    errors = self_check(grid)
    if errors:
        return errors
    scene = _analyze_scene(grid)
    rectangles = scene["rectangles"]
    if not any(rect["height"] != rect["width"] for rect in rectangles):
        return ["at least one nonsquare rectangle is required to expose bbox cropping"]
    return []


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared axis from the returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    rectangles = scene["rectangles"]
    winner = rectangles[scene["winner"]]
    red_counts = sorted((rect["red"] for rect in rectangles), reverse=True)
    return {
        "n_clusters": len(rectangles),
        "winner_red_count": red_counts[0],
        "red_gap": red_counts[0] - red_counts[1],
        "winner_position": winner["position"],
    }


def _crop_object(grid, rect):
    r0, c0, r1, c1 = rect["bbox"]
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid task scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    return _crop_object(scene["grid"], scene["rectangles"][scene["winner"]])


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    return (
        scene["h"],
        scene["w"],
        tuple(sorted(scene["grid"][r][c] for r in range(scene["h"]) for c in range(scene["w"]))),
        tuple(sorted((rect["height"], rect["width"], rect["red"]) for rect in scene["rectangles"])),
    )


def is_canonical_profile(grid):
    """All lawful scenes are canonical-scale; exact canonical replay is optional."""
    return self_check(grid) == []


def _rectangles_conflict(a, b):
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    rows_separate = ar1 + 1 < br0 or br1 + 1 < ar0
    cols_separate = ac1 + 1 < bc0 or bc1 + 1 < ac0
    return not (rows_separate or cols_separate)


def _candidate_boxes(height, width, *, winner_position=None):
    boxes = []
    for r0 in range(0, 10 - height + 1):
        for c0 in range(0, 10 - width + 1):
            box = (r0, c0, r0 + height - 1, c0 + width - 1)
            if winner_position is None or _position_of_bbox(box) == winner_position:
                boxes.append(box)
    return boxes


def _place_rectangles(sizes, winner_position, rng):
    order = sorted(range(len(sizes)), key=lambda i: (i != 0, -sizes[i][0] * sizes[i][1]))
    placed = [None] * len(sizes)

    def search(depth):
        if depth == len(order):
            return True
        index = order[depth]
        height, width = sizes[index]
        candidates = _candidate_boxes(
            height,
            width,
            winner_position=winner_position if index == 0 else None,
        )
        rng.shuffle(candidates)
        for box in candidates:
            if any(
                other is not None and _rectangles_conflict(box, other)
                for other in placed
            ):
                continue
            placed[index] = box
            if search(depth + 1):
                return True
            placed[index] = None
        return False

    if not search(0):
        return None
    return tuple(placed)


def _choose_sizes(profile, n_clusters, rng):
    if profile == "winner_smaller":
        pools = (_SMALL_SIZES, _LARGE_SIZES, _MEDIUM_SIZES)
    elif profile == "winner_larger":
        pools = (_HUGE_SIZES, _SMALL_SIZES, _MEDIUM_SIZES)
    else:
        # A 28..30-cell winner against a 9-cell runner-up guarantees a
        # red-density reversal even at the hardest boundary: 3 red versus 1.
        pools = (_HUGE_SIZES, ((3, 3),), ((3, 4), (4, 3)))
    return tuple(rng.choice(pools[index]) for index in range(n_clusters))


def _red_counts(n_clusters, winner_red_count, red_gap):
    runner_up = winner_red_count - red_gap
    counts = [winner_red_count, runner_up]
    if n_clusters == 3:
        counts.append(max(0, runner_up - 1))
    if len(counts) != len(set(counts)):
        raise AssertionError(f"could not construct distinct red counts: {counts}")
    return tuple(counts)


def _paint_rectangle(grid, box, red_count, mode, rng):
    r0, c0, r1, c1 = box
    cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
    if red_count > len(cells) - 2:
        raise ValueError("rectangle is too small to retain colors 1 and 8")

    red_cells = set(rng.sample(cells, red_count))
    remaining = [cell for cell in cells if cell not in red_cells]
    if mode == "fragmented":
        for r, c in remaining:
            grid[r][c] = 1 if (r + c) % 2 == 0 else 8
    elif mode == "dominant_1":
        for r, c in remaining:
            grid[r][c] = 1
        n_eights = max(1, min(len(remaining) - 1, len(remaining) // 4))
        for r, c in rng.sample(remaining, n_eights):
            grid[r][c] = 8
    else:
        for r, c in remaining:
            grid[r][c] = 8
        n_ones = max(1, min(len(remaining) - 1, len(remaining) // 4))
        for r, c in rng.sample(remaining, n_ones):
            grid[r][c] = 1

    # A sparse checker remainder can accidentally contain one parity only.
    # Force both non-red colors on distinct surviving cells before adding red.
    non_red_values = {grid[r][c] for r, c in remaining}
    if 1 not in non_red_values:
        r, c = remaining[0]
        grid[r][c] = 1
    non_red_values = {grid[r][c] for r, c in remaining}
    if 8 not in non_red_values:
        r, c = remaining[-1]
        grid[r][c] = 8
    if remaining[0] == remaining[-1]:
        raise AssertionError("rectangle needs at least two non-red cells")

    # Red replaces only the preselected cells.
    for r, c in red_cells:
        grid[r][c] = 2

    values = {grid[r][c] for r, c in cells}
    if not {1, 8}.issubset(values):
        raise AssertionError("rectangle lost a required non-red color")


def _texture_modes(profile, n_clusters):
    if profile == "winner_smaller":
        # The larger loser has more of BOTH non-red colors than the small
        # winner, jointly refuting most-color-1 and most-color-8 shortcuts.
        modes = ("dominant_8", "fragmented", "dominant_1")
    elif profile == "winner_larger":
        modes = ("dominant_8", "fragmented", "dominant_1")
    else:
        modes = ("dominant_1", "fragmented", "dominant_8")
    return modes[:n_clusters]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)

    scheduled_n = 3 if profile == "density_reversal" else 2
    if overrides.get("n_clusters") is not None:
        n_clusters = ctx.draw_int("n_clusters", 2, 3)
    else:
        # Hard draws add more three-object scenes without breaking the
        # three-profile lesson schedule.
        if band == "hard" and profile == "winner_larger":
            scheduled_n = 3
        n_clusters = ctx.draw_int("n_clusters", scheduled_n, scheduled_n)

    if overrides.get("winner_red_count") is not None:
        winner_red_count = ctx.draw_int("winner_red_count", 3, 6)
    else:
        lo, hi = {
            "easy": (3, 4),
            "medium": (4, 5),
            "hard": (5, 6),
        }[band]
        winner_red_count = ctx.draw_int("winner_red_count", lo, hi)

    if overrides.get("red_gap") is not None:
        red_gap = ctx.draw_int("red_gap", 1, 2)
    else:
        red_gap = ctx.draw_int("red_gap", 1, 2)
    if overrides.get("winner_position") is not None:
        winner_position = ctx.draw_choice("winner_position", _POSITIONS)
    else:
        scheduled_position = _POSITIONS[sample_index % len(_POSITIONS)]
        winner_position = ctx.draw_choice("winner_position", (scheduled_position,))

    rng = ctx.draw_rng("scene")
    red_counts = _red_counts(n_clusters, winner_red_count, red_gap)
    placements = None
    sizes = None
    for _ in range(240):
        sizes = _choose_sizes(profile, n_clusters, rng)
        if any(red > height * width - 2 for red, (height, width) in zip(red_counts, sizes)):
            continue
        placements = _place_rectangles(sizes, winner_position, rng)
        if placements is not None:
            break
    if placements is None or sizes is None:
        raise RuntimeError("failed to place separated canonical rectangles")

    grid = full_grid(10, 10, 0)
    for box, red_count, mode in zip(
        placements,
        red_counts,
        _texture_modes(profile, n_clusters),
    ):
        _paint_rectangle(grid, box, red_count, mode, rng)

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "n_clusters": n_clusters,
        "winner_red_count": winner_red_count,
        "red_gap": red_gap,
        "winner_position": winner_position,
    }
    if observed != expected:
        raise AssertionError(f"observable axis mismatch: expected {expected}, got {observed}")
    return grid


def _valid_scene(grid):
    return self_check(grid) == []


def _select_by(grid, key, *, reverse=True):
    scene = _analyze_scene(grid)
    if not scene["rectangles"]:
        raise ValueError("no objects")
    indexed = list(enumerate(scene["rectangles"]))
    indexed.sort(key=lambda item: (key(item[1]), -item[0]), reverse=reverse)
    return _crop_object(scene["grid"], indexed[0][1])


def _largest_area(grid):
    return _select_by(grid, lambda rect: rect["area"])


def _smallest_area(grid):
    return _select_by(grid, lambda rect: -rect["area"])


def _highest_red_density(grid):
    return _select_by(grid, lambda rect: rect["red"] / rect["area"])


def _most_ones(grid):
    return _select_by(grid, lambda rect: rect["counts"][1])


def _most_eights(grid):
    return _select_by(grid, lambda rect: rect["counts"][8])


def _fixed_position(position):
    def solve(grid):
        scene = _analyze_scene(grid)
        candidates = [rect for rect in scene["rectangles"] if rect["position"] == position]
        if candidates:
            return _crop_object(scene["grid"], candidates[0])
        # A literal fixed-quadrant rule has no selected object when that
        # quadrant is empty; return a visible wrong answer rather than quietly
        # becoming a nearest-object heuristic.
        return [[0]]
    return solve


def _square_crop(grid):
    scene = _analyze_scene(grid)
    winner = scene["rectangles"][scene["winner"]]
    crop = _crop_object(scene["grid"], winner)
    side = min(len(crop), len(crop[0]))
    return [row[:side] for row in crop[:side]]


LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "largest_area": _largest_area,
    "smallest_area": _smallest_area,
    "highest_red_density": _highest_red_density,
    "most_color_1": _most_ones,
    "most_color_8": _most_eights,
    "square_crop": _square_crop,
    "fixed_top_left": _fixed_position("top_left"),
    "fixed_top_right": _fixed_position("top_right"),
    "fixed_bottom_left": _fixed_position("bottom_left"),
    "fixed_bottom_right": _fixed_position("bottom_right"),
}
SEMANTIC_RIVALS = LESSON_COMPETITORS
CANONICAL_SHORTCUTS = LESSON_COMPETITORS


def _rival_differs(name, grid):
    if not _valid_scene(grid):
        return False
    return LESSON_COMPETITORS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "winner_not_largest_area": lambda grid: _rival_differs("largest_area", grid),
    "winner_not_smallest_area": lambda grid: _rival_differs("smallest_area", grid),
    "absolute_count_not_density": lambda grid: _rival_differs("highest_red_density", grid),
    "color_1_count_is_distractor": lambda grid: _rival_differs("most_color_1", grid),
    "color_8_count_is_distractor": lambda grid: _rival_differs("most_color_8", grid),
    "nonsquare_bbox_crop": lambda grid: _rival_differs("square_crop", grid),
}


WITNESS_RIVALS = {
    "winner_not_largest_area": ["largest_area"],
    "winner_not_smallest_area": ["smallest_area"],
    "absolute_count_not_density": ["highest_red_density"],
    "color_1_count_is_distractor": ["most_color_1"],
    "color_8_count_is_distractor": ["most_color_8"],
    "nonsquare_bbox_crop": ["square_crop"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival can answer the query differently."""
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} must be a pair dict")
            continue
        input_grid = pair.get("input")
        output_grid = pair.get("output")
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
        elif output_grid != rule_mirror(input_grid):
            reasons.append(f"demo {index} output disagrees with the max-red crop rule")

    if not isinstance(query, dict):
        return reasons + ["query must be a pair dict"]
    query_input = query.get("input")
    query_output = query.get("output")
    query_errors = self_check(query_input)
    if query_errors:
        return reasons + ["query input invalid: " + "; ".join(query_errors)]
    intended_query = rule_mirror(query_input)
    if query_output is not None and query_output != intended_query:
        reasons.append("query output disagrees with the max-red crop rule")

    survivors = []
    divergent = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        except Exception:
            fits = False
        if not fits:
            continue
        survivors.append(name)
        if competitor(query_input) != intended_query:
            divergent.append(name)
    if survivors:
        detail = ", ".join(sorted(survivors))
        if divergent:
            reasons.append("demonstrations leave query-divergent rival(s): " + detail)
        else:
            reasons.append("demonstrations fail to refute rival(s): " + detail)
    return reasons
