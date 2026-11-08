"""Semantic generator for ARC task 6ffe8f07 / 0b8ba9bb3c63.

A solid cyan rectangle emits a yellow cross along its row and column bands.
Colored blocker rectangles clip individual beam rows/columns and are restored
after painting.  Red rectangles are transparent to the beam and are therefore
overwritten wherever the cross reaches them.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0b8ba9bb3c63"
VERSION = "4.1.0"
TASK_ID = "0b8ba9bb3c63"
RULE_HASH = "757441c9ab4a"
SUMMARY = (
    "A cyan(8) rectangle emits yellow(4) horizontal and vertical beams. "
    "Non-red colored rectangles clip each beam row or column and are restored "
    "on top; red(2) rectangles are transparent and are overwritten where a "
    "beam crosses them."
)
INVARIANTS = [
    "exactly one solid cyan rectangle and no yellow input cells",
    "at least one solid blocker rectangle clips a beam direction",
    "at least one red rectangle intersects and is overwritten by a beam",
    "the cross has visible yellow cells in all four directions",
    "black is the modal background and all source objects are solid rectangles",
]
EXAMPLES_NEEDED = 3
# Every four consecutive positions contain at least two non-blue witnesses.
# Consequently three-demo lessons, including any single query holdout, retain
# evidence against the canonical-fitting blue-only blocker shortcut.
_FAMILY_SCHEDULE = ("public", "generalized", "public", "generalized", "generalized")
LESSON_SCHEDULE_PERIOD = len(_FAMILY_SCHEDULE)
MIN_STRICT_FRAC = 0.3
AXES = {
    "scene_family": {
        "type": "str",
        "default": "cyclic public|generalized (2:3)",
        "valid": "public|generalized",
        "doc": (
            "public matches the canonical size, palette, object-count, and "
            "changed-cell envelope; generalized broadens scale and blocker colors "
            "and visibly refutes blue-only clipping. Explicit overrides bypass the schedule."
        ),
    },
}

BACKGROUND = 0
BLUE_BLOCKER = 1
TRANSPARENT = 2
BEAM = 4
CYAN = 8
_BLOCKER_COLORS = (1, 3, 5, 6, 7, 9)
_GENERALIZED_BLOCKER_COLORS = (3, 5, 6, 7, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
_BANDS = {
    "easy": {"dims": (11, 16), "cyan": (2, 4), "reds": (1, 3), "blockers": (1, 3)},
    "medium": {"dims": (17, 23), "cyan": (3, 6), "reds": (2, 6), "blockers": (2, 4)},
    "hard": {"dims": (22, 30), "cyan": (5, 9), "reds": (4, 8), "blockers": (3, 4)},
}
# Linked facts recovered from the six unique official inputs.  Keeping these
# tuples intact prevents a broad range checker from accepting a Frankenstein
# recombination of cyan geometry and role counts from unrelated examples.
_PUBLIC_LINKED_PROFILES = (
    # h, w, cyan_h, cyan_w, blockers, red objects, clipping directions
    (19, 19, 4, 4, 1, 2, 1),
    (19, 19, 7, 6, 4, 6, 3),
    (19, 19, 4, 7, 3, 3, 3),
    (19, 18, 4, 4, 4, 5, 4),
    (19, 19, 5, 7, 2, 3, 2),
    (19, 19, 5, 6, 3, 4, 3),
)
_PUBLIC_PROFILE_KEYS = frozenset(
    (*profile,)
    for linked in _PUBLIC_LINKED_PROFILES
    for profile in (
        linked,
        (
            linked[1], linked[0], linked[3], linked[2], linked[4],
            linked[5], linked[6],
        ),
    )
)
_PUBLIC_BLOCKER_SIZES = (
    (3, 5), (3, 3), (2, 2), (2, 4), (2, 9), (5, 3),
    (2, 7), (2, 3), (5, 2), (4, 3), (3, 8), (8, 5), (5, 5),
)
_PUBLIC_RED_SIZES = (
    (3, 13), (4, 6), (6, 5), (3, 4), (4, 4), (3, 2),
    (3, 5), (2, 3), (3, 6), (2, 7), (3, 7), (6, 4), (2, 4),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _components(grid):
    """Return 4-connected non-background components as color/cell records."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == BACKGROUND or (row, col) in seen:
                continue
            seen.add((row, col))
            stack = [(row, col)]
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    pos = current[0] + dr, current[1] + dc
                    if not (0 <= pos[0] < height and 0 <= pos[1] < width):
                        continue
                    if pos in seen or grid[pos[0]][pos[1]] != color:
                        continue
                    seen.add(pos)
                    stack.append(pos)
            rows = [pos[0] for pos in cells]
            cols = [pos[1] for pos in cells]
            bbox = min(rows), min(cols), max(rows), max(cols)
            result.append({"color": color, "cells": tuple(sorted(cells)), "bbox": bbox})
    return result


def _solid_rectangle(obj):
    row1, col1, row2, col2 = obj["bbox"]
    return len(obj["cells"]) == (row2 - row1 + 1) * (col2 - col1 + 1)


def _paint_cross(grid, cyan, blockers):
    """Independent-equivalent Python mirror of the canonical Racket rule."""
    height, width = len(grid), len(grid[0])
    row1, col1, row2, col2 = cyan["bbox"]
    output = _copy_grid(grid)
    for row in range(row1, row2 + 1):
        left_limit = 0
        right_limit = width - 1
        for blocker in blockers:
            br1, bc1, br2, bc2 = blocker["bbox"]
            if br1 <= row <= br2 and bc2 < col1:
                left_limit = max(left_limit, bc1)
            if br1 <= row <= br2 and bc1 > col2:
                right_limit = min(right_limit, bc2)
        for col in range(left_limit, right_limit + 1):
            if not col1 <= col <= col2:
                output[row][col] = BEAM
    for col in range(col1, col2 + 1):
        up_limit = 0
        down_limit = height - 1
        for blocker in blockers:
            br1, bc1, br2, bc2 = blocker["bbox"]
            if bc1 <= col <= bc2 and br2 < row1:
                up_limit = max(up_limit, br1)
            if bc1 <= col <= bc2 and br1 > row2:
                down_limit = min(down_limit, br2)
        for row in range(up_limit, down_limit + 1):
            if not row1 <= row <= row2:
                output[row][col] = BEAM
    for row, col in cyan["cells"]:
        output[row][col] = CYAN
    for blocker in blockers:
        for row, col in blocker["cells"]:
            output[row][col] = blocker["color"]
    return output


def _directional_blockers(cyan, blockers):
    row1, col1, row2, col2 = cyan["bbox"]
    directions = set()
    for blocker in blockers:
        br1, bc1, br2, bc2 = blocker["bbox"]
        if br1 <= row2 and br2 >= row1:
            if bc2 < col1:
                directions.add("left")
            if bc1 > col2:
                directions.add("right")
        if bc1 <= col2 and bc2 >= col1:
            if br2 < row1:
                directions.add("up")
            if br1 > row2:
                directions.add("down")
    return frozenset(directions)


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be nonempty and rectangular"], "facts": None}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"], "facts": None}

    height = len(grid)
    if not (11 <= height <= 30 and 11 <= width <= 30):
        errors.append("dimensions must lie in 11..30")
    palette = {value for row in grid for value in row}
    allowed = {BACKGROUND, TRANSPARENT, CYAN, *_BLOCKER_COLORS}
    if BEAM in palette:
        errors.append("yellow 4 is an output-only beam color")
    illegal = palette - allowed
    if illegal:
        errors.append(f"unsupported input colors: {sorted(illegal)}")
    for required in (BACKGROUND, TRANSPARENT, CYAN):
        if required not in palette:
            errors.append(f"required color {required} is missing")

    source_objects = _components(grid)
    if any(not _solid_rectangle(obj) for obj in source_objects):
        errors.append("every non-background object must be a solid rectangle")
    cyan_objects = [obj for obj in source_objects if obj["color"] == CYAN]
    red_objects = [obj for obj in source_objects if obj["color"] == TRANSPARENT]
    blockers = [
        obj for obj in source_objects if obj["color"] not in (TRANSPARENT, CYAN)
    ]
    if len(cyan_objects) != 1:
        errors.append(f"expected exactly one cyan rectangle, found {len(cyan_objects)}")
    if not red_objects:
        errors.append("at least one red transparent rectangle is required")
    if not blockers:
        errors.append("at least one colored blocker rectangle is required")
    counts = Counter(value for row in grid for value in row)
    if counts[BACKGROUND] <= max((count for color, count in counts.items() if color != BACKGROUND), default=0):
        errors.append("black must be the modal background color")
    if len(cyan_objects) != 1:
        return {"errors": errors, "facts": None}

    cyan = cyan_objects[0]
    clipped = _directional_blockers(cyan, blockers)
    if not clipped:
        errors.append("at least one blocker must intersect a beam band")
    output = _paint_cross(grid, cyan, blockers)
    changes = Counter(
        (grid[row][col], output[row][col])
        for row in range(height) for col in range(width)
        if grid[row][col] != output[row][col]
    )
    bad_changes = set(changes) - {(BACKGROUND, BEAM), (TRANSPARENT, BEAM)}
    if bad_changes:
        errors.append(f"unexpected transformation classes: {sorted(bad_changes)}")
    if changes[(BACKGROUND, BEAM)] < 1:
        errors.append("the beam must paint black background")
    if changes[(TRANSPARENT, BEAM)] < 1:
        errors.append("the beam must visibly overwrite a red object")

    row1, col1, row2, col2 = cyan["bbox"]
    direction_cells = {
        "left": [(row, col) for row in range(row1, row2 + 1) for col in range(col1)],
        "right": [(row, col) for row in range(row1, row2 + 1) for col in range(col2 + 1, width)],
        "up": [(row, col) for row in range(row1) for col in range(col1, col2 + 1)],
        "down": [(row, col) for row in range(row2 + 1, height) for col in range(col1, col2 + 1)],
    }
    visible_directions = frozenset(
        direction for direction, cells in direction_cells.items()
        if any(output[row][col] == BEAM for row, col in cells)
    )
    if visible_directions != {"left", "right", "up", "down"}:
        errors.append("the yellow cross must be visible in all four directions")
    if output == [list(row) for row in grid]:
        errors.append("the transformation must not be identity")

    cyan_height = row2 - row1 + 1
    cyan_width = col2 - col1 + 1
    facts = {
        "height": height,
        "width": width,
        "palette": frozenset(palette),
        "objects": tuple(source_objects),
        "cyan": cyan,
        "cyan_size": (cyan_height, cyan_width),
        "cyan_margins": (row1, col1, height - row2 - 1, width - col2 - 1),
        "red_count": len(red_objects),
        "blocker_count": len(blockers),
        "object_count": len(source_objects),
        "clipped_directions": clipped,
        "visible_directions": visible_directions,
        "changed_background": changes[(BACKGROUND, BEAM)],
        "changed_red": changes[(TRANSPARENT, BEAM)],
        "max_object_size": max(
            (len(obj["cells"]) for obj in source_objects), default=0
        ),
        "output": output,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def blue_only_blocks(grid):
    """Plausible rival: only blue clips, while every blocker is restored."""
    objects = _components(grid)
    cyan = next(obj for obj in objects if obj["color"] == CYAN)
    blockers = [obj for obj in objects if obj["color"] not in (TRANSPARENT, CYAN)]
    output = _paint_cross(
        grid, cyan, [obj for obj in blockers if obj["color"] == BLUE_BLOCKER]
    )
    for obj in blockers:
        for row, col in obj["cells"]:
            output[row][col] = obj["color"]
    return output


def _nonblue_clipping_witness(grid):
    analysis = _analyze(grid)
    return not analysis["errors"] and blue_only_blocks(grid) != analysis["facts"]["output"]


SEMANTIC_RIVALS = {"blue_only_blocks": blue_only_blocks}
CANONICAL_SHORTCUTS = {"blue_only_blocks": blue_only_blocks}
LESSON_COMPETITORS = {"blue_only_blocks": blue_only_blocks}
SEMANTIC_WITNESSES = {"nonblue_clipping": _nonblue_clipping_witness}
WITNESS_RIVALS = {"nonblue_clipping": ["blue_only_blocks"]}


def _is_public_facts(facts):
    height, width = facts["height"], facts["width"]
    profile_key = (
        height,
        width,
        facts["cyan_size"][0],
        facts["cyan_size"][1],
        facts["blocker_count"],
        facts["red_count"],
        len(facts["clipped_directions"]),
    )
    return (
        profile_key in _PUBLIC_PROFILE_KEYS
        and facts["palette"] == {BACKGROUND, BLUE_BLOCKER, TRANSPARENT, CYAN}
        and all(4 <= margin <= 10 for margin in facts["cyan_margins"])
        and 4 <= facts["object_count"] <= 11
        and 82 <= facts["changed_background"] <= 98
        and 6 <= facts["changed_red"] <= 50
        and 4 <= facts["max_object_size"] <= 42
    )


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return "public" if _is_public_facts(analysis["facts"]) else "generalized"


def strict_canonical_like(grid):
    return canonical_profile_signature(grid) == "public"


def observe_overrides(grid):
    family = canonical_profile_signature(grid)
    return {} if family == "invalid" else {"scene_family": family}


def _rect_clear(grid, row1, col1, height, width, *, moat=True):
    grid_height, grid_width = len(grid), len(grid[0])
    if not (0 <= row1 <= grid_height - height and 0 <= col1 <= grid_width - width):
        return False
    if any(
        grid[row][col] != BACKGROUND
        for row in range(row1, row1 + height)
        for col in range(col1, col1 + width)
    ):
        return False
    if not moat:
        return True
    return all(
        grid[row][col] == BACKGROUND
        for row in range(max(0, row1 - 1), min(grid_height, row1 + height + 1))
        for col in range(max(0, col1 - 1), min(grid_width, col1 + width + 1))
    )


def _paint_rect(grid, row1, col1, height, width, color):
    for row in range(row1, row1 + height):
        for col in range(col1, col1 + width):
            grid[row][col] = color


def _place_directional_blocker(grid, cyan_bbox, direction, sizes, color, rng):
    grid_height, grid_width = len(grid), len(grid[0])
    row1, col1, row2, col2 = cyan_bbox
    for _ in range(180):
        rect_height, rect_width = rng.choice(sizes)
        if direction in ("left", "right"):
            top_low = max(0, row1 - rect_height + 1)
            top_high = min(row2, grid_height - rect_height)
            if direction == "left":
                left_low, left_high = 0, col1 - rect_width - 1
            else:
                left_low, left_high = col2 + 2, grid_width - rect_width
        else:
            left_low = max(0, col1 - rect_width + 1)
            left_high = min(col2, grid_width - rect_width)
            if direction == "up":
                top_low, top_high = 0, row1 - rect_height - 1
            else:
                top_low, top_high = row2 + 2, grid_height - rect_height
        if top_high < top_low or left_high < left_low:
            continue
        top = rng.randint(top_low, top_high)
        left = rng.randint(left_low, left_high)
        if not _rect_clear(grid, top, left, rect_height, rect_width):
            continue
        _paint_rect(grid, top, left, rect_height, rect_width, color)
        return True
    return False


def _place_red_crossing(grid, cyan_obj, sizes, minimum_overlap, rng):
    base_objects = _components(grid)
    blockers = [obj for obj in base_objects if obj["color"] not in (TRANSPARENT, CYAN)]
    beam_output = _paint_cross(grid, cyan_obj, blockers)
    beam_cells = {
        (row, col)
        for row in range(len(grid)) for col in range(len(grid[0]))
        if grid[row][col] == BACKGROUND and beam_output[row][col] == BEAM
    }
    if not beam_cells:
        return False
    ordered_beam = tuple(sorted(beam_cells))
    for _ in range(320):
        rect_height, rect_width = rng.choice(sizes)
        anchor_row, anchor_col = rng.choice(ordered_beam)
        top = anchor_row - rng.randrange(rect_height)
        left = anchor_col - rng.randrange(rect_width)
        if not _rect_clear(grid, top, left, rect_height, rect_width):
            continue
        overlap = sum(
            (row, col) in beam_cells
            for row in range(top, top + rect_height)
            for col in range(left, left + rect_width)
        )
        if overlap < minimum_overlap:
            continue
        _paint_rect(grid, top, left, rect_height, rect_width, TRANSPARENT)
        return True
    return False


def _place_decoy_blocker(grid, cyan_bbox, sizes, color, rng):
    """Place a diagonal blocker that intersects neither cyan beam band."""
    row1, col1, row2, col2 = cyan_bbox
    for _ in range(320):
        height, width = rng.choice(sizes)
        if height > len(grid) or width > len(grid[0]):
            continue
        top = rng.randint(0, len(grid) - height)
        left = rng.randint(0, len(grid[0]) - width)
        bottom = top + height - 1
        right = left + width - 1
        separated_rows = bottom < row1 or top > row2
        separated_cols = right < col1 or left > col2
        if not (separated_rows and separated_cols):
            continue
        if not _rect_clear(grid, top, left, height, width):
            continue
        _paint_rect(grid, top, left, height, width, color)
        return True
    return False


def _place_random_rect(grid, sizes, color, rng):
    for _ in range(240):
        height, width = rng.choice(sizes)
        if height > len(grid) or width > len(grid[0]):
            continue
        top = rng.randint(0, len(grid) - height)
        left = rng.randint(0, len(grid[0]) - width)
        if not _rect_clear(grid, top, left, height, width):
            continue
        _paint_rect(grid, top, left, height, width, color)
        return True
    return False


def _general_sizes(rng, lower, upper, count=18):
    return tuple(
        (rng.randint(lower, upper), rng.randint(lower, upper))
        for _ in range(count)
    )


def _construct_scene(rng, band, family):
    public = family == "public"
    public_profile = None
    if public:
        public_profile = rng.choice(_PUBLIC_LINKED_PROFILES)
        if rng.choice((False, True)):
            public_profile = (
                public_profile[1],
                public_profile[0],
                public_profile[3],
                public_profile[2],
                public_profile[4],
                public_profile[5],
                public_profile[6],
            )
    for _attempt in range(2_000):
        if public:
            (
                height,
                width,
                cyan_height,
                cyan_width,
                blocker_target,
                red_target,
                clipped_target,
            ) = public_profile
            top_options = range(4, height - cyan_height - 3)
            left_options = range(4, width - cyan_width - 3)
            if not top_options or not left_options:
                continue
            cyan_top = rng.choice(tuple(top_options))
            cyan_left = rng.choice(tuple(left_options))
            blocker_sizes = _PUBLIC_BLOCKER_SIZES
            red_sizes = _PUBLIC_RED_SIZES
        else:
            bounds = _BANDS[band]
            height = rng.randint(*bounds["dims"])
            width = rng.randint(*bounds["dims"])
            cyan_height = rng.randint(*bounds["cyan"])
            cyan_width = rng.randint(*bounds["cyan"])
            if height - cyan_height < 4 or width - cyan_width < 4:
                continue
            cyan_top = rng.randint(2, height - cyan_height - 2)
            cyan_left = rng.randint(2, width - cyan_width - 2)
            blocker_target = rng.randint(*bounds["blockers"])
            clipped_target = blocker_target
            red_target = rng.randint(*bounds["reds"])
            max_side = 3 if band == "easy" else (5 if band == "medium" else 7)
            blocker_sizes = _general_sizes(rng, 1, max_side)
            red_sizes = _general_sizes(rng, 2, max_side)

        grid = full_grid(height, width, BACKGROUND)
        _paint_rect(grid, cyan_top, cyan_left, cyan_height, cyan_width, CYAN)
        cyan_bbox = (
            cyan_top, cyan_left,
            cyan_top + cyan_height - 1, cyan_left + cyan_width - 1,
        )
        directions = ["left", "right", "up", "down"]
        rng.shuffle(directions)
        direction_plan = directions[:clipped_target]
        if not public and clipped_target >= 2 and rng.random() < 0.35:
            # Exercise the rule's nearest-blocker reduction: two separated
            # rectangles may constrain overlapping rays from the same side.
            direction_plan[1] = direction_plan[0]
        blocker_colors = [BLUE_BLOCKER] * blocker_target if public else [
            rng.choice(_GENERALIZED_BLOCKER_COLORS) for _ in range(blocker_target)
        ]
        placed = True
        for direction, color in zip(direction_plan, blocker_colors):
            if not _place_directional_blocker(
                grid, cyan_bbox, direction, blocker_sizes, color, rng
            ):
                placed = False
                break
        for color in blocker_colors[clipped_target:]:
            if not _place_decoy_blocker(
                grid, cyan_bbox, blocker_sizes, color, rng
            ):
                placed = False
                break
        if not placed:
            continue

        cyan_obj = next(obj for obj in _components(grid) if obj["color"] == CYAN)
        minimum_overlap = 6 if public else min(3, cyan_height, cyan_width)
        if not _place_red_crossing(grid, cyan_obj, red_sizes, minimum_overlap, rng):
            continue
        for _ in range(red_target - 1):
            if not _place_random_rect(grid, red_sizes, TRANSPARENT, rng):
                placed = False
                break
        if not placed:
            continue

        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        actual = "public" if _is_public_facts(analysis["facts"]) else "generalized"
        if actual == family:
            # A non-blue rectangle touching the outer edge can be semantically
            # redundant after restoration. Require actual output disagreement,
            # not merely the presence of a different blocker color.
            if not public and blue_only_blocks(grid) == analysis["facts"]["output"]:
                continue
            return grid
    raise RuntimeError(f"could not construct a valid {band}/{family} beam scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer, not bool")
    if isinstance(sample_index, bool) or not isinstance(sample_index, int) or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    options = ("public", "generalized") if overrides.get("scene_family") is not None else (
        _FAMILY_SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD],
    )
    family = ctx.draw_choice("scene_family", options)
    band = "medium" if difficulty in (None, "default") else difficulty
    return _construct_scene(ctx.draw_rng("layout"), band, family)
