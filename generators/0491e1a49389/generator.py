"""Generator for bank task H26: mirror objects across a maroon guide row.

The generated curriculum deliberately includes three complementary profiles in
any three consecutive examples: a canonical-sized two-sided scene, an
off-center guide, and a partially clipped reflection.  That schedule prevents
three attractive shortcuts: treating the canvas midpoint as the axis, moving
only objects above the guide, and discarding a whole object when one reflected
cell leaves the board.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0491e1a49389"
TASK_ID = GENERATOR_ID
RULE_HASH = "d6db986b56c9"
VERSION = "3.0.0"

SUMMARY = (
    "0-background grids with one full-width maroon(9) guide row and 2-4 "
    "distinct-color polyominoes on both sides.  The output is a fresh canvas "
    "containing the guide plus every object reflected across that row; source "
    "objects disappear and off-board reflected cells are clipped."
)

EXAMPLES_NEEDED = 3

SCHEDULE_PROFILES = (
    "canonical_both_sides",
    "off_center_both_sides",
    "clip_both_sides",
)
HELPFUL_TEXTURES = ("both_sides", "off_center", "clip", "touching_guide")
DEGENERATE_TEXTURES = ("no_objects",)

INVARIANTS = [
    "exactly one full-width color-9 guide row and no other color-9 cells",
    "2-4 connected monochrome objects using distinct nonzero, non-guide colors",
    "at least one object on each side of the guide",
    "every object has at least one visible reflected cell",
    "reflected objects do not collide with one another",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 8..19; one scheduled profile uses canonical 8/9",
        "valid": "8..19",
        "doc": "Grid height. Exact overrides are valid in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 8..18; one scheduled profile uses canonical 9/10/11",
        "valid": "8..18",
        "doc": "Grid width. Exact overrides are valid in every difficulty band.",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-skewed 2..4; canonical profile uses 2",
        "valid": "2..4",
        "doc": "Number of distinct-color source objects.",
    },
    "texture": {
        "type": "str",
        "default": "scheduled both_sides/off_center/clip",
        "valid": "|".join(HELPFUL_TEXTURES),
        "doc": "Guide/object arrangement. no_objects is a negative fixture, not ordinary data.",
    },
}

_CANONICAL_PROFILES = ((8, 9, 4), (9, 10, 4), (9, 11, 4))
_CANONICAL_SHAPES = tuple((h, w) for h, w, _ in _CANONICAL_PROFILES)
_PROFILE_TEXTURE = {
    "canonical_both_sides": "both_sides",
    "off_center_both_sides": "off_center",
    "clip_both_sides": "clip",
}

# Connected motifs, all normalized at (0, 0).  Several one-row/two-row motifs
# are intentional: boundary combinations such as 8x8, four objects, and an
# off-center guide remain exactly realizable rather than silently clamping.
_MOTIFS = (
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """A three-cycle: every lesson-sized window covers all key branches."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_difficulty(difficulty):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_int_axis(ctx, label, lo, hi, *, default=None):
    """Use global bounds for overrides while retaining scheduled defaults."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    if default is not None:
        return ctx.draw_choice(label, (default,))
    return ctx.draw_int_diff(label, lo, hi)


def _middle_guide(height):
    return (height - 1) // 2


def _guide_candidates(height, texture, rng):
    middle = _middle_guide(height)
    if texture == "clip":
        # Reflecting an object near the top across this lower guide gives a
        # deterministic partial clip while leaving room for a lower object.
        return [min(height - 3, middle + 1)]
    if texture != "off_center":
        return [middle]
    candidates = [
        row
        for row in range(2, height - 2)
        if row != middle
    ]
    # Prefer a visible but not extreme displacement; keep all lawful fallbacks.
    candidates.sort(key=lambda row: (abs(abs(row - middle) - 1), abs(row - middle), row))
    grouped = candidates[:]
    rng.shuffle(grouped)
    grouped.sort(key=lambda row: abs(row - middle))
    return grouped


def _motif_size(motif):
    return max(r for r, _ in motif) + 1, max(c for _, c in motif) + 1


def _candidate_tops(height, guide, motif_height, side, special):
    if side == "above":
        if special == "touch":
            top = guide - motif_height
            return [top] if top >= 0 else []
        # Ordinary objects leave one blank row next to the guide.
        return list(range(0, guide - motif_height))
    if special == "touch":
        top = guide + 1
        return [top] if top + motif_height <= height else []
    return list(range(guide + 2, height - motif_height + 1))


def _balanced_sides(n_objects, texture, rng):
    if texture == "clip":
        sides = ["above", "below"]
        sides.extend("above" if index % 2 == 0 else "below" for index in range(n_objects - 2))
        return sides
    if texture == "touching_guide":
        first = rng.choice(("above", "below"))
        other = "below" if first == "above" else "above"
        sides = [first, other]
        sides.extend(first if index % 2 == 0 else other for index in range(n_objects - 2))
        return sides
    sides = ["above", "below"]
    sides.extend("above" if index % 2 == 0 else "below" for index in range(n_objects - 2))
    rng.shuffle(sides)
    return sides


def _try_place_scene(height, width, guide, n_objects, texture, rng):
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[guide][col] = 9

    colors = rng.sample(list(range(1, 9)), n_objects)
    sides = _balanced_sides(n_objects, texture, rng)
    occupied_mirrors = set()

    for index, (color, side) in enumerate(zip(colors, sides)):
        special = None
        if texture == "clip" and index == 0:
            special = "clip"
        elif texture == "touching_guide" and index == 0:
            special = "touch"

        motifs = list(_MOTIFS)
        rng.shuffle(motifs)
        placed = False
        for motif in motifs:
            motif_height, motif_width = _motif_size(motif)
            if motif_width > width:
                continue
            tops = _candidate_tops(height, guide, motif_height, side, special)
            positions = [
                (top, left)
                for top in tops
                for left in range(0, width - motif_width + 1)
            ]
            rng.shuffle(positions)
            for top, left in positions:
                cells = [(top + r, left + c) for r, c in motif]
                if any(grid[r][c] != 0 for r, c in cells):
                    continue
                mirrored = [(2 * guide - r, c) for r, c in cells]
                visible = [(r, c) for r, c in mirrored if 0 <= r < height]
                if not visible:
                    continue
                is_partial = len(visible) != len(mirrored)
                if special == "clip":
                    if not is_partial:
                        continue
                elif is_partial:
                    continue
                if occupied_mirrors.intersection(visible):
                    continue
                for r, c in cells:
                    grid[r][c] = color
                occupied_mirrors.update(visible)
                placed = True
                break
            if placed:
                break
        if not placed:
            return None
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    _validate_difficulty(difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    texture_override = overrides.get("texture")
    if texture_override is not None:
        texture = ctx.draw_choice(
            "texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES
        )
        profile = None
    else:
        profile = scheduled
        texture = ctx.draw_choice("texture", (_PROFILE_TEXTURE[profile],))

    canonical_shape = None
    if profile == "canonical_both_sides":
        shape_rng = ctx.draw_rng("canonical_shape")
        canonical_shape = _CANONICAL_SHAPES[shape_rng.randrange(len(_CANONICAL_SHAPES))]

    height = _draw_int_axis(
        ctx, "grid_h", 8, 19,
        default=canonical_shape[0] if canonical_shape else None,
    )
    width = _draw_int_axis(
        ctx, "grid_w", 8, 18,
        default=canonical_shape[1] if canonical_shape else None,
    )
    n_objects = _draw_int_axis(
        ctx, "n_objects", 2, 4,
        default=2 if canonical_shape else None,
    )

    if texture == "no_objects":
        grid = full_grid(height, width, 0)
        guide = _middle_guide(height)
        for col in range(width):
            grid[guide][col] = 9
        return grid

    rng = ctx.draw_rng("layout")
    guides = _guide_candidates(height, texture, rng)
    # Retry motif/position choices, then try the next lawful guide candidate.
    for attempt in range(80):
        guide = guides[attempt % len(guides)]
        grid = _try_place_scene(
            height, width, guide, n_objects, texture, rng
        )
        if grid is not None:
            return grid
    raise ValueError(
        "could not realize requested mirror-guide scene "
        f"(h={height}, w={width}, n_objects={n_objects}, texture={texture!r})"
    )


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 9) or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append("grid dimensions must be within ARC's 1..30 bounds")
    for row in grid:
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("grid values must be integer ARC colors 0..9")
                break
        if errors and errors[-1].startswith("grid values"):
            break

    guides = [
        row
        for row, values in enumerate(grid)
        if all(value == 9 for value in values)
    ]
    guide = guides[0] if len(guides) == 1 else None
    if len(guides) != 1:
        errors.append(f"expected exactly one full-width color-9 guide row, got {guides}")
    if guide is not None and any(
        grid[row][col] == 9
        for row in range(height)
        if row != guide
        for col in range(width)
    ):
        errors.append("color 9 may appear only in the full-width guide row")

    components = _components(grid) if not errors or guide is not None else []
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "guide": guide,
        "components": components,
    }


def _partial_clip(component, guide, height):
    visibility = [0 <= 2 * guide - row < height for row, _ in component["cells"]]
    return any(visibility) and not all(visibility)


def observe_overrides(grid):
    """Recover every exact declared axis from an ordinary generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["guide"] is None:
        raise ValueError("cannot observe overrides from an invalid grid")
    height = analysis["height"]
    guide = analysis["guide"]
    components = analysis["components"]
    if any(_partial_clip(component, guide, height) for component in components):
        texture = "clip"
    elif any(
        any(abs(row - guide) == 1 for row, _ in component["cells"])
        for component in components
    ):
        texture = "touching_guide"
    elif guide != _middle_guide(height):
        texture = "off_center"
    else:
        texture = "both_sides"
    return {
        "grid_h": height,
        "grid_w": analysis["width"],
        "n_objects": len(components),
        "texture": texture,
    }


def rule_mirror(grid):
    """Independent Python mirror; the synchronized Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["guide"] is None:
        raise ValueError("grid has no unique full-width color-9 guide row")
    height, width, guide = analysis["height"], analysis["width"], analysis["guide"]
    output = full_grid(height, width, 0)
    for col in range(width):
        output[guide][col] = 9
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 9):
                continue
            reflected = 2 * guide - row
            if 0 <= reflected < height:
                output[reflected][col] = value
    return output


def self_check(grid, *, seed=None, sample_index=None, difficulty=None, **kwargs):
    del seed, sample_index, difficulty, kwargs
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    guide = analysis.get("guide")
    if guide is None:
        return errors
    components = analysis["components"]
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2-4 source objects, got {len(components)}")
    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("each source object must use a distinct color")
    if any(not 3 <= len(component["cells"]) <= 5 for component in components):
        errors.append("each source object must contain 3-5 cells")
    if any(
        any(row < guide for row, _ in component["cells"])
        and any(row > guide for row, _ in component["cells"])
        for component in components
    ):
        errors.append("a source object may not cross the guide")
    if components:
        has_above = any(all(row < guide for row, _ in component["cells"]) for component in components)
        has_below = any(all(row > guide for row, _ in component["cells"]) for component in components)
        if not (has_above and has_below):
            errors.append("source objects must occur on both sides of the guide")

    reflected_owners = {}
    for index, component in enumerate(components):
        visible = [
            (2 * guide - row, col)
            for row, col in component["cells"]
            if 0 <= 2 * guide - row < analysis["height"]
        ]
        if not visible:
            errors.append(f"object {index} has no visible reflected cell")
        for cell in visible:
            previous = reflected_owners.setdefault(cell, index)
            if previous != index:
                errors.append("reflected objects collide")
                break
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    palette = {value for row in grid for value in row}
    profile = (analysis["height"], analysis["width"], len(palette))
    if profile not in _CANONICAL_PROFILES:
        errors.append(f"profile {profile} is outside the three canonical profiles")
    if analysis["guide"] != _middle_guide(analysis["height"]):
        errors.append("canonical guide is the middle/upper-middle row")
    return errors


def _rival_fixed_middle_axis(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None:
        return [list(row) for row in grid]
    height, width = analysis["height"], analysis["width"]
    axis = _middle_guide(height)
    output = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 9):
                continue
            reflected = 2 * axis - row
            if 0 <= reflected < height:
                output[reflected][col] = value
    for col in range(width):
        output[analysis["guide"]][col] = 9
    return output


def _rival_above_only(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None:
        return [list(row) for row in grid]
    height, width, guide = analysis["height"], analysis["width"], analysis["guide"]
    output = full_grid(height, width, 0)
    for col in range(width):
        output[guide][col] = 9
    for row in range(guide):
        for col, value in enumerate(grid[row]):
            if value in (0, 9):
                continue
            reflected = 2 * guide - row
            if 0 <= reflected < height:
                output[reflected][col] = value
    return output


def _rival_discard_partially_clipped(grid):
    analysis = _analyze(grid)
    if analysis["guide"] is None:
        return [list(row) for row in grid]
    height, width, guide = analysis["height"], analysis["width"], analysis["guide"]
    output = full_grid(height, width, 0)
    for col in range(width):
        output[guide][col] = 9
    for component in analysis["components"]:
        mirrored = [(2 * guide - row, col) for row, col in component["cells"]]
        if not all(0 <= row < height for row, _ in mirrored):
            continue
        for row, col in mirrored:
            output[row][col] = component["color"]
    return output


SEMANTIC_RIVALS = {
    "fixed_middle_axis": _rival_fixed_middle_axis,
    "above_only": _rival_above_only,
    "discard_partially_clipped_object": _rival_discard_partially_clipped,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_middle_axis": _rival_fixed_middle_axis}


def _witness_off_center(grid):
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["guide"] != _middle_guide(analysis["height"])
    )


def _witness_below_to_above(grid):
    analysis = _analyze(grid)
    guide = analysis.get("guide")
    return (
        not analysis["errors"]
        and guide is not None
        and any(all(row > guide for row, _ in component["cells"]) for component in analysis["components"])
    )


def _witness_partial_clip(grid):
    analysis = _analyze(grid)
    guide = analysis.get("guide")
    return (
        not analysis["errors"]
        and guide is not None
        and any(
            _partial_clip(component, guide, analysis["height"])
            for component in analysis["components"]
        )
    )


SEMANTIC_WITNESSES = {
    "off_center_guide": _witness_off_center,
    "below_to_above": _witness_below_to_above,
    "partial_clip_visible": _witness_partial_clip,
}
WITNESS_RIVALS = {
    "off_center_guide": ["fixed_middle_axis"],
    "below_to_above": ["above_only"],
    "partial_clip_visible": ["discard_partially_clipped_object"],
}


def lesson_identifiable(demos, query):
    """A lesson is sufficient only when every named rival is falsified."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the guide-reflection rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the guide-reflection rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
