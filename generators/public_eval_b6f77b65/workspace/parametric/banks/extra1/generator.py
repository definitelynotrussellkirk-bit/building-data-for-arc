"""Portable scaffold-deletion inputs for public ARC parent b6f77b65.

The parser separates each arch's horizontal interior runs from its endpoint
posts, including same-color joints. The Python simulator is an analytical
mirror for tests and private explanations; protected Racket supplies labels.
One frozen original gold contains a documented upstream extra cell. This
module follows the general mechanics and never reproduces that source defect.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "public_eval_b6f77b65"
TASK_ID = "public_eval_b6f77b65"
RULE_TASK_ID = "ee_b6f77b65"
VERSION = "1.0.0"
RULE_HASH = "ef06dc0a5b58"
EXAMPLES_NEEDED = 2
SUMMARY = (
    "Delete scaffold pieces whose colors appear in the header, then settle "
    "disjoint posts and horizontal beams bottom-first until stable; beams "
    "can also be held by their lateral neighbors."
)
INVARIANTS = [
    "Exact integer grids use colors 0..9 and dimensions at most 30 by 30; background is zero.",
    "One or two distinct selector colors form a row-zero prefix, followed by zeros; row one is empty.",
    "Arch roofs are maximal nonzero horizontal runs of length at least three below the header.",
    "Roof interiors split into equal-color horizontal pieces; their endpoints start vertical posts.",
    "Posts terminate before the next lower roof covering their column; pieces reconstruct every input cell exactly once.",
    "Generated scaffolds are initially stable before deletion under both supported lateral-support settings.",
    "Settlement uses stable bottom-first ordering once per pass and updates occupancy after each single-cell move.",
    "The first two demonstrations use two present selectors, nontrivial cascades, and separated same-color piece motion.",
]
AXES = {
    "selector_count": {
        "type": "int",
        "default": "rng 1..2 (first two teaching profiles use 2)",
        "valid": "1..2",
        "description": "Exact number of distinct header selectors; changing it preserves the entire scaffold.",
    },
}

_MAX_INTEGER = 2**63 - 1


def _copy_piece(piece):
    return {"id": piece["id"], "kind": piece["kind"], "color": piece["color"],
            "cells": [cell[:] for cell in piece["cells"]]}


def analyze(grid):
    """Recover disjoint physical pieces from input geometry only.

    Stable integer IDs follow roof row/column order, with its horizontal runs
    followed by its left and right posts. This order is retained for equal
    bottom coordinates during simulation; no order-independence is assumed.
    """
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("grid must be an exact list with 3..30 rows")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid must have exact list rows of width 3..30")
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with exact list rows")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers in 0..9")
    selector_count = 0
    while selector_count < width and grid[0][selector_count] != 0:
        selector_count += 1
    header_values = grid[0][:selector_count]
    if not 1 <= selector_count <= 2 or len(set(header_values)) != selector_count:
        raise ValueError("header needs one or two distinct nonzero selector colors")
    if any(grid[0][selector_count:]):
        raise ValueError("selector colors must be a contiguous prefix followed by zeros")
    if any(grid[1]):
        raise ValueError("row one must be an empty separator")
    roofs = []
    for row in range(2, height):
        col = 0
        while col < width:
            if grid[row][col] == 0:
                col += 1
                continue
            right = col
            while right + 1 < width and grid[row][right + 1] != 0:
                right += 1
            if right - col >= 2:
                roofs.append((row, col, right))
            col = right + 1
    if not roofs:
        raise ValueError("scaffold needs at least one complete arch roof")
    pieces = []
    for row, left, right in roofs:
        col = left + 1
        while col < right:
            end = col
            while end + 1 < right and grid[row][end + 1] == grid[row][col]:
                end += 1
            pieces.append({"id": len(pieces), "kind": "horizontal", "color": grid[row][col],
                           "cells": [[row, c] for c in range(col, end + 1)]})
            col = end + 1
        for col in (left, right):
            color = grid[row][col]
            floor = min((r for r, l, k in roofs if r > row and l <= col <= k), default=height)
            end = row
            while end + 1 < floor and grid[end + 1][col] == color:
                end += 1
            pieces.append({"id": len(pieces), "kind": "vertical", "color": color,
                           "cells": [[r, col] for r in range(row, end + 1)]})
    recovered = [[0] * width for _ in range(height)]
    recovered[0] = grid[0][:]
    for piece in pieces:
        for row, col in piece["cells"]:
            if recovered[row][col] != 0:
                raise ValueError("arch interpretation overlaps physical pieces")
            recovered[row][col] = piece["color"]
    if recovered != grid:
        raise ValueError("scaffold contains cells outside its arch beams and endpoint posts")
    return {"height": height, "width": width, "header": grid[0][:],
            "selected_colors": sorted(header_values), "pieces": pieces}


def _settle(pieces, height, support_mode, trace):
    settled = [_copy_piece(piece) for piece in pieces]
    occupied = {(r, c): piece["id"] for piece in settled for r, c in piece["cells"]}
    moves = []
    # Every successful move strictly decreases a finite sum of remaining drop
    # distances. The cap bounds passes, not a change in the physical rule.
    for tick in range(height * max(1, len(settled)) + 1):
        moved = False
        order = sorted(range(len(settled)),
                       key=lambda index: max(r for r, _ in settled[index]["cells"]),
                       reverse=True)
        for index in order:
            piece = settled[index]
            piece_id = piece["id"]
            candidate = [[r + 1, c] for r, c in piece["cells"]]
            if any(r >= height or ((r, c) in occupied and occupied[r, c] != piece_id)
                   for r, c in candidate):
                continue
            if piece["kind"] == "horizontal":
                row = piece["cells"][0][0]
                left = min(c for _, c in piece["cells"])
                right = max(c for _, c in piece["cells"])
                left_support = (row, left - 1) in occupied
                right_support = (row, right + 1) in occupied
                if ((left_support and right_support) if support_mode == "both"
                        else (left_support or right_support)):
                    continue
            if trace:
                moves.append({"tick": tick, "piece_id": piece_id,
                              "from": [cell[:] for cell in piece["cells"]],
                              "to": [cell[:] for cell in candidate]})
            for r, c in piece["cells"]:
                del occupied[r, c]
            for r, c in candidate:
                occupied[r, c] = piece_id
            piece["cells"] = candidate
            moved = True
        if not moved:
            return settled, moves
    raise RuntimeError("monotone scaffold settlement exceeded its proven movement bound")


def simulate(grid, support_mode="both", trace=False):
    """Return the analytical output and private piece states.

    `survivors` is the deletion result before gravity. `settled_pieces` is the
    fixed point reached by the specified bottom-first in-place update rule.
    `moves` is empty unless trace=True, then records each piece ID and exact
    before/after cells. The input and every returned snapshot are independent.
    """
    if type(support_mode) is not str or support_mode not in ("both", "either"):
        raise ValueError("support_mode must be both or either")
    if type(trace) is not bool:
        raise TypeError("trace must be an exact bool")
    parsed = analyze(grid)
    initial = [_copy_piece(piece) for piece in parsed["pieces"]]
    survivors = [_copy_piece(piece) for piece in initial if piece["color"] not in parsed["selected_colors"]]
    settled, moves = _settle(survivors, parsed["height"], support_mode, trace)
    output = [[0] * parsed["width"] for _ in range(parsed["height"])]
    output[0] = parsed["header"][:]
    for piece in settled:
        for row, col in piece["cells"]:
            if output[row][col] != 0:
                raise RuntimeError("settlement produced overlapping pieces")
            output[row][col] = piece["color"]
    return {"output": output, "initial_pieces": initial, "survivors": survivors,
            "settled_pieces": settled, "moves": moves}


def observe_overrides(grid):
    parsed = analyze(grid)
    return {"selector_count": len(parsed["selected_colors"])}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        parsed = analyze(grid)
        unchanged, _ = _settle(parsed["pieces"], parsed["height"], "both", False)
        if unchanged != parsed["pieces"]:
            return ["input scaffold is not initially stable before color deletion"]
    except (TypeError, ValueError) as error:
        return [str(error)]
    return []


def _validate_request(seed, sample_index, difficulty, overrides):
    for name, value in (("seed", seed), ("sample_index", sample_index)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer")
        if not 0 <= value <= _MAX_INTEGER:
            raise ValueError(f"{name} must be in 0..2**63-1")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if "selector_count" in overrides:
        value = overrides["selector_count"]
        if type(value) is not int:
            raise TypeError("selector_count must be an exact integer")
        if not 1 <= value <= 2:
            raise ValueError("selector_count must be in 1..2")


# Entries are (support tier from bottom, left anchor, right anchor, color role).
# All global anchor columns have at least one empty column between them, so
# independent posts cannot accidentally form an additional horizontal roof.
_PROFILES = (
    (9, (16, 18), (21, 23), ((0, 0, 8, "base"), (1, 1, 3, "left"), (1, 5, 7, "right"), (2, 2, 6, "bridge"))),
    (9, (20, 22), (21, 23), ((0, 0, 8, "base"), (1, 1, 3, "left"), (1, 5, 7, "right"), (2, 2, 6, "bridge"), (3, 3, 5, "cap"))),
    (5, (9, 11), (13, 15), ((0, 0, 4, "base"), (1, 1, 3, "bridge"))),
    (7, (12, 14), (17, 19), ((0, 0, 6, "base"), (1, 1, 5, "left"), (2, 2, 4, "bridge"))),
    (11, (20, 22), (25, 27), ((0, 0, 10, "base"), (1, 0, 3, "left"), (1, 4, 6, "middle"), (1, 7, 10, "right"), (2, 1, 9, "bridge"), (3, 3, 7, "cap"))),
    (11, (24, 26), (25, 27), ((0, 0, 4, "base"), (0, 6, 10, "base2"), (1, 1, 3, "left"), (1, 7, 9, "right"), (2, 2, 8, "bridge"), (3, 3, 5, "cap"), (3, 6, 7, "cap"))),
    (9, (24, 26), (21, 23), ((0, 0, 3, "base"), (0, 5, 8, "base2"), (1, 1, 2, "left"), (1, 6, 7, "right"), (2, 2, 6, "bridge"))),
    (13, (26, 28), (27, 29), ((0, 0, 5, "base"), (0, 7, 12, "base2"), (1, 1, 4, "left"), (1, 8, 11, "right"), (2, 2, 10, "bridge"), (3, 4, 8, "cap"))),
    (12, (28, 30), (25, 27), ((0, 0, 11, "base"), (1, 0, 2, "left"), (1, 3, 5, "middle"), (1, 6, 8, "right"), (1, 9, 11, "right"), (2, 1, 4, "bridge"), (2, 7, 10, "bridge"), (3, 2, 9, "cap"))),
    (13, (30, 30), (30, 30), ((0, 0, 12, "base"), (1, 0, 2, "left"), (1, 3, 5, "middle"), (1, 7, 9, "right"), (1, 10, 12, "right"), (2, 1, 4, "bridge"), (2, 8, 11, "bridge"), (3, 2, 10, "cap"), (4, 4, 8, "cap"))),
)
_ROLE_COLORS = {
    "base": (0, 1, 1), "base2": (3, 5, 4),
    "left": (3, 2, 3), "right": (4, 5, 4),
    "middle": (3, 6, 4), "bridge": (6, 6, 4), "cap": (3, 5, 6),
}


def _beam_colors(ctx, index, role, length, profile):
    base_color = _ROLE_COLORS[role][1]
    rng = ctx.draw_rng(f"roof_segments.{index}")
    if profile in (0, 1):
        # Keep the causal teaching components intact. The unselected right
        # roof and cap still demonstrate genuine multicolor beam segmentation.
        colors = [5, 6] if role == "right" else [5, 3] if role == "cap" else [base_color]
    else:
        count = rng.randint(1, min(3, length))
        others = [color for color in range(1, 7) if color != base_color]
        rng.shuffle(others)
        colors = [base_color] + others[:count - 1]
    colors = colors[:length]
    cuts = sorted(rng.sample(range(1, length), len(colors) - 1))
    boundaries = [0, *cuts, length]
    return [color for color, left, right in zip(colors, boundaries, boundaries[1:])
            for _ in range(left, right)]


def _append_order_teaching_arches(grid, palette, ctx):
    """Add an independent two-arch race between a beam and falling posts.

    After the two selector colors disappear, a one-cell lower beam must move
    before the two posts above it can arrive beside it. Top-first processing
    would trap that beam. The upper posts are long enough to keep the rival's
    premature lateral support through the final state, under either policy.
    """
    rng = ctx.draw_rng("teaching.order_geometry")
    base_post_height = rng.randint(2, 3)
    upper_post_height = base_post_height + rng.randint(0, 2)
    lower_row = len(grid) - base_post_height
    upper_row = lower_row - upper_post_height
    left = len(grid[0]) + 1
    for row in grid:
        row.extend([0] * 6)
    selected_a, selected_c = palette[0], palette[2]
    moving_color, fixed_color = palette[6], palette[1]
    grid[upper_row][left + 1:left + 4] = [moving_color, selected_c, moving_color]
    for row in range(upper_row + 1, lower_row):
        grid[row][left + 1] = moving_color
        grid[row][left + 3] = moving_color
    grid[lower_row][left:left + 5] = [selected_a, selected_c, moving_color, selected_a, fixed_color]
    for row in range(lower_row + 1, len(grid)):
        grid[row][left] = selected_a
        grid[row][left + 4] = fixed_color
    return grid


def _append_joint_teaching_arches(grid, palette):
    """Keep a post and its same-color lower beam physically independent.

    The neighboring lower beam moves between that lower beam and the upper
    post in the canonical schedule. Rigidly binding the joint would move the
    post early and trap its neighbor. This left-to-right arrangement must be
    installed after reflection because same-height pieces retain reading-order
    ties. The two arch bodies occupy the final four rows of the canvas.
    """
    lower_row = len(grid) - 2
    upper_row = lower_row - 2
    left = len(grid[0]) + 1
    for row in grid:
        row.extend([0] * 5)
    selected_a, selected_c = palette[0], palette[2]
    joint_color, neighbor_color, fixed_color = palette[6], palette[3], palette[1]
    grid[upper_row][left + 1:left + 4] = [joint_color, selected_c, fixed_color]
    grid[upper_row + 1][left + 1] = joint_color
    grid[upper_row + 1][left + 3] = fixed_color
    grid[lower_row][left:left + 4] = [selected_a, joint_color, neighbor_color, fixed_color]
    grid[lower_row + 1][left] = selected_a
    grid[lower_row + 1][left + 3] = fixed_color
    return grid


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    """Construct an initially stable scaffold with a separate selector prefix.

    The first six profiles are demonstrations and the next four are queries;
    later indices repeat the geometry schedule with fresh keyed draws. All
    sampling uses GenCtx streams, with an exact recorded selector-count draw.
    No sampling depends on the support-mode parameter or future queries.
    """
    _validate_request(seed, sample_index, difficulty, overrides)
    profile = sample_index % 10
    effective_overrides = dict(overrides)
    if profile in (0, 1):
        effective_overrides.setdefault("selector_count", 2)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective_overrides)
    anchor_count, height_bounds, width_bounds, structure = _PROFILES[profile]
    rng = ctx.draw_rng(f"layout.{difficulty or 'medium'}")
    height = rng.randint(*height_bounds)
    width = rng.randint(*width_bounds)
    gap_sizes = [2] * (anchor_count - 1)
    extra_max = width - 3 - sum(gap_sizes)
    extra = rng.randint(0, min(3, extra_max))
    if profile == 9:
        extra = rng.randint(2, 3)
    for _ in range(extra):
        gap_sizes[rng.randrange(len(gap_sizes))] += 1
    anchors = [rng.randint(1, width - 1 - sum(gap_sizes))]
    for gap in gap_sizes:
        anchors.append(anchors[-1] + gap)
    highest_tier = max(tier for tier, _, _, _ in structure)
    bottom = height - rng.randint(3, 4)
    top = rng.randint(2, min(4, bottom - 3 * highest_tier))
    tier_rows = [bottom - ((bottom - top) * tier // highest_tier)
                 for tier in range(highest_tier + 1)]
    arches = []
    for index, (tier, left_anchor, right_anchor, role) in enumerate(structure):
        row = tier_rows[tier]
        if 0 < tier < highest_tier:
            row += (-1 if role == "left" else 1 if role == "right" else rng.randint(-1, 1))
        elif tier == 0 and role == "base2":
            row -= 1
        arches.append((row, anchors[left_anchor], anchors[right_anchor], role, index))
    palette = list(range(1, 10))
    ctx.draw_rng("palette").shuffle(palette)
    grid = [[0] * width for _ in range(height)]
    # Paint roofs first, then extend endpoint posts exactly to their next
    # supporting roof or the canvas floor. Same-color joints stay disjoint.
    for row, left, right, role, index in arches:
        left_color, _, right_color = _ROLE_COLORS[role]
        grid[row][left] = palette[left_color]
        grid[row][right] = palette[right_color]
        for col, color in zip(range(left + 1, right), _beam_colors(ctx, index, role, right - left - 1, profile)):
            grid[row][col] = palette[color]
    for row, left, right, role, _ in arches:
        left_color, _, right_color = _ROLE_COLORS[role]
        for col, color in ((left, left_color), (right, right_color)):
            floor = min((r for r, l, k, _, _ in arches if r > row and l <= col <= k), default=height)
            for r in range(row + 1, floor):
                if grid[r][col] != 0:
                    raise RuntimeError("constructed arches overlap an endpoint post")
                grid[r][col] = palette[color]
    if profile == 0:
        grid = _append_order_teaching_arches(grid, palette, ctx)
    if ctx.draw_rng("reflection").randrange(2):
        grid = [row[::-1] for row in grid]
    if profile == 1:
        grid = _append_joint_teaching_arches(grid, palette)
    selector_roles = {
        0: (0, 2), 1: (0, 2), 2: (7, 8), 3: (2, 7), 4: (2, 5),
        5: (3, 0), 6: (0, 5), 7: (1, 2), 8: (3, 5), 9: (0, 2),
    }[profile]
    selector_bank = [palette[index] for index in selector_roles]
    selector_count = ctx.draw_int_strict("selector_count", 1, 2)
    grid[0][:selector_count] = selector_bank[:selector_count]
    problems = self_check(grid)
    if problems:
        raise RuntimeError("constructed scaffold violates grammar: " + "; ".join(problems))
    return grid
