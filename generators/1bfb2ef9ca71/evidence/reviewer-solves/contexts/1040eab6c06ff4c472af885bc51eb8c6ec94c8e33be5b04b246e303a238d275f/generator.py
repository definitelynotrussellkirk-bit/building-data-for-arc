"""Generator for ARC task 1bfb2ef9ca71 / bank E126.

Each non-zero color appears at two diagonally opposed cells.  The pinned rule
uses those cells as opposite corners and draws that rectangle's hollow border.
This sampler keeps canonical-size examples common while varying rectangle
height, width, placement, color, and both diagonal corner orientations.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bfb2ef9ca71"
TASK_ID = GENERATOR_ID
RULE_HASH = "a0ec8172be31"
VERSION = "3.1.0"

SUMMARY = (
    "On a zero background, each of two or three colors marks exactly two "
    "opposite corners of a separated axis-aligned rectangle. Draw each hollow "
    "rectangle border in its marker color. Both diagonal endpoint orientations, "
    "canonical-size scenes, and taller-than-canonical rectangles are sampled."
)

INVARIANTS = [
    "background is 0 and every active color appears exactly twice",
    "same-color endpoints are diagonally opposite corners of a 3..5 by 3..6 rectangle",
    "inferred rectangle boxes are separated by at least one empty row or column",
    "ordinary inputs contain both NW-SE and NE-SW endpoint orientations",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted by every difficulty band",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted by every difficulty band",
        "valid": "7..14",
    },
    "rectangles": {
        "type": "int",
        "default": "2 for canonical core; 2..3 in broad support",
        "valid": "2..3",
    },
}

# Every Cartesian combination of the three exact controls is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical_height3", "height_variation")
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the alternating teaching schedule to lesson validators."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


_CANONICAL_SHAPES = ((8, 7), (8, 8), (9, 9))
_BROAD_SHAPES = {
    "easy": ((8, 9), (9, 10), (10, 8), (10, 11), (11, 9)),
    "medium": ((8, 12), (9, 11), (10, 12), (11, 13), (12, 10)),
    "hard": ((9, 14), (10, 13), (11, 12), (12, 11), (12, 14)),
}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")
    ):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _draw_axis(ctx, name, scheduled, legal_values):
    """Record a scheduled default while accepting the complete exact domain."""
    choices = tuple(legal_values) if ctx.overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, choices)


def _scheduled_controls(ctx):
    rng = ctx.draw_rng("curriculum_profile")
    if rng.randrange(5) < 3:
        height, width = rng.choice(_CANONICAL_SHAPES)
        rectangles = 2
    else:
        band = ctx.difficulty or "medium"
        height, width = rng.choice(_BROAD_SHAPES[band])
        if band == "easy":
            rectangles = rng.choice((2, 2, 3))
        elif band == "hard":
            rectangles = rng.choice((2, 3, 3))
        else:
            rectangles = rng.choice((2, 3))
    height = _draw_axis(ctx, "grid_h", height, range(8, 13))
    width = _draw_axis(ctx, "grid_w", width, range(7, 15))
    rectangles = _draw_axis(ctx, "rectangles", rectangles, (2, 3))
    return height, width, rectangles


def _distribute_slack(total, rng):
    """Split non-negative slack into before / between / after amounts."""
    before = rng.randint(0, total)
    remaining = total - before
    between = rng.randint(0, remaining)
    return before, between, remaining - between


def _two_boxes(height, width, *, varied_height, rng):
    """Construct two boxes with a guaranteed empty row or column between."""
    if varied_height:
        first_h = 3
        second_h = rng.randint(4, min(5, height - first_h - 1))
        first_w = rng.randint(3, min(6, width))
        second_w = rng.randint(3, min(6, width))
        before, extra_gap, _ = _distribute_slack(height - first_h - second_h - 1, rng)
        first_r = before
        second_r = first_r + first_h + 1 + extra_gap
        first_c = rng.randint(0, width - first_w)
        second_c = rng.randint(0, width - second_w)
        return [
            (first_r, first_c, first_r + first_h - 1, first_c + first_w - 1),
            (second_r, second_c, second_r + second_h - 1, second_c + second_w - 1),
        ]

    # Canonical-height scenes alternate between vertical and horizontal packing.
    if rng.randrange(2) == 0:
        first_w = rng.randint(3, min(6, width))
        second_w = rng.randint(3, min(6, width))
        before, extra_gap, _ = _distribute_slack(height - 7, rng)
        first_r = before
        second_r = first_r + 4 + extra_gap
        first_c = rng.randint(0, width - first_w)
        second_c = rng.randint(0, width - second_w)
        return [
            (first_r, first_c, first_r + 2, first_c + first_w - 1),
            (second_r, second_c, second_r + 2, second_c + second_w - 1),
        ]
    first_w = second_w = 3
    first_h = rng.randint(3, min(5, height))
    second_h = rng.randint(3, min(5, height))
    before, extra_gap, _ = _distribute_slack(width - 7, rng)
    first_c = before
    second_c = first_c + 4 + extra_gap
    first_r = rng.randint(0, height - first_h)
    second_r = rng.randint(0, height - second_h)
    return [
        (first_r, first_c, first_r + first_h - 1, first_c + first_w - 1),
        (second_r, second_c, second_r + second_h - 1, second_c + second_w - 1),
    ]



def _three_boxes(height, width, *, varied_height, rng):
    """Place three rectangles in three of four gutter-separated quadrants."""
    split_r = rng.randint(3, height - 4)
    split_c = rng.randint(3, width - 4)
    slots = [
        (0, 0, split_r - 1, split_c - 1),
        (0, split_c + 1, split_r - 1, width - 1),
        (split_r + 1, 0, height - 1, split_c - 1),
        (split_r + 1, split_c + 1, height - 1, width - 1),
    ]
    selected = rng.sample(slots, 3)
    boxes = []
    grew_height = False
    for slot_index, (sr0, sc0, sr1, sc1) in enumerate(selected):
        slot_h = sr1 - sr0 + 1
        slot_w = sc1 - sc0 + 1
        box_h = 3
        if varied_height and not grew_height and slot_h >= 4:
            box_h = rng.randint(4, min(5, slot_h))
            grew_height = True
        elif slot_h > 3 and rng.randrange(3) == 0:
            box_h = rng.randint(3, min(5, slot_h))
        box_w = rng.randint(3, min(6, slot_w))
        r0 = rng.randint(sr0, sr1 - box_h + 1)
        c0 = rng.randint(sc0, sc1 - box_w + 1)
        boxes.append((r0, c0, r0 + box_h - 1, c0 + box_w - 1))
    if varied_height and not grew_height:
        # With the declared minimum height, every three-quadrant layout has at
        # least one four-row slot. Keep this explicit rather than silently
        # returning an all-height-three scene if that assumption changes.
        raise RuntimeError("constructive layout failed to realize height variation")
    return boxes


def _rectangle_boxes(ctx, height, width, count):
    rng = ctx.draw_rng("rectangle_geometry")
    varied_height = ctx.sample_index % 2 == 1
    if count == 2:
        return _two_boxes(height, width, varied_height=varied_height, rng=rng)
    return _three_boxes(height, width, varied_height=varied_height, rng=rng)


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
    height, width, rectangle_count = _scheduled_controls(ctx)
    boxes = _rectangle_boxes(ctx, height, width, rectangle_count)
    colors = ctx.draw_rng("colors").sample(range(1, 10), rectangle_count)
    orientations = ["nw_se", "ne_sw"]
    if rectangle_count == 3:
        orientations.append(ctx.draw_rng("third_orientation").choice(orientations))
    ctx.draw_rng("orientation_assignment").shuffle(orientations)

    grid = full_grid(height, width, 0)
    for color, orientation, (r0, c0, r1, c1) in zip(colors, orientations, boxes):
        if orientation == "nw_se":
            endpoints = ((r0, c0), (r1, c1))
        else:
            endpoints = ((r0, c1), (r1, c0))
        for row, col in endpoints:
            if grid[row][col] != 0:
                raise RuntimeError("constructive rectangle endpoints collided")
            grid[row][col] = color
    return grid


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    by_color = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(
                    f"cell ({row_index},{col_index}) must be a literal ARC color 0..9"
                )
                continue
            if value:
                by_color.setdefault(value, []).append((row_index, col_index))
    boxes = []
    orientations = []
    for color, points in sorted(by_color.items()):
        if len(points) != 2:
            errors.append(f"color {color} must appear exactly twice, found {len(points)}")
            continue
        (ra, ca), (rb, cb) = points
        if ra == rb or ca == cb:
            errors.append(f"color {color} endpoints must be diagonally opposite")
            continue
        r0, r1 = sorted((ra, rb))
        c0, c1 = sorted((ca, cb))
        box_h, box_w = r1 - r0 + 1, c1 - c0 + 1
        if not 3 <= box_h <= 5:
            errors.append(f"color {color} rectangle height {box_h} outside 3..5")
        if not 3 <= box_w <= 6:
            errors.append(f"color {color} rectangle width {box_w} outside 3..6")
        boxes.append((r0, c0, r1, c1, color))
        orientations.append("nw_se" if (ra - rb) * (ca - cb) > 0 else "ne_sw")
    for first, second in combinations(boxes, 2):
        ar0, ac0, ar1, ac1, acolor = first
        br0, bc0, br1, bc1, bcolor = second
        separated = (
            ar1 + 1 < br0
            or br1 + 1 < ar0
            or ac1 + 1 < bc0
            or bc1 + 1 < ac0
        )
        if not separated:
            errors.append(
                f"rectangles for colors {acolor} and {bcolor} need an empty row or column between boxes"
            )
    return {
        "height": len(grid),
        "width": width,
        "by_color": by_color,
        "boxes": boxes,
        "orientations": orientations,
        "errors": errors,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "rectangles": len(analysis["by_color"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if "height" not in analysis:
        return errors
    if not 8 <= analysis["height"] <= 12:
        errors.append(f"grid height {analysis['height']} outside 8..12")
    if not 7 <= analysis["width"] <= 14:
        errors.append(f"grid width {analysis['width']} outside 7..14")
    rectangle_count = len(analysis["by_color"])
    if not 2 <= rectangle_count <= 3:
        errors.append(f"expected 2..3 active rectangle colors, found {rectangle_count}")
    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed[name] != value:
                errors.append(f"override {name} requested {value!r}, observed {observed[name]!r}")
    return errors


def strict_canonical_like(grid):
    """Lawful inputs in this sampler's source-bound rectangle-corner domain."""
    return self_check(grid)


def rule_mirror(grid):
    """Independent Python mirror of the pinned rectangle-border authority."""
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    by_color = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color != 0:
                by_color.setdefault(color, []).append((row, col))
    for color, points in by_color.items():
        if len(points) != 2:
            continue
        (ra, ca), (rb, cb) = points
        if ra == rb or ca == cb:
            continue
        r0, r1 = sorted((ra, rb))
        c0, c1 = sorted((ca, cb))
        for col in range(c0, c1 + 1):
            output[r0][col] = color
            output[r1][col] = color
        for row in range(r0, r1 + 1):
            output[row][c0] = color
            output[row][c1] = color
    return output


def _fixed_height_three(grid):
    """Canonical-fitting rival: force every inferred rectangle to height three."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid rectangle-corner input: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for r0, c0, _r1, c1, color in analysis["boxes"]:
        r1 = r0 + 2
        for col in range(c0, c1 + 1):
            output[r0][col] = color
            output[r1][col] = color
        for row in range(r0, r1 + 1):
            output[row][c0] = color
            output[row][c1] = color
    return output


def _has_non_three_height(grid) -> bool:
    analysis = _analyze(grid)
    return bool(
        not analysis["errors"]
        and any(r1 - r0 + 1 != 3 for r0, _c0, r1, _c1, _color in analysis["boxes"])
    )


SEMANTIC_RIVALS = {
    "fixed_height_three": _fixed_height_three,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "fixed_height_three": _fixed_height_three,
}
SEMANTIC_WITNESSES = {
    "non_three_height": _has_non_three_height,
}
WITNESS_RIVALS = {
    "non_three_height": ["fixed_height_three"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each three-demo lesson to disprove the fixed-height shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the rectangle-corner grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the rectangle-corner grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the pinned rectangle-border rule")
            continue
        valid_demos.append(demo)

    if len(valid_demos) == len(demos):
        if not any(_has_non_three_height(demo["input"]) for demo in valid_demos):
            reasons.append("demonstrations never expose a rectangle taller than three rows")
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons

