"""Input curriculum for task 5a70e1b62a50 — fill enclosed zero regions.

The unchanged Racket authority flood-fills zero regions, retaining only regions
that do not touch the canvas border and whose non-zero neighbours use one color.
This sampler teaches that topology directly instead of reducing every example to
completion of one rectangular outline.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a70e1b62a50"
TASK_ID = GENERATOR_ID
RULE_HASH = "92650211204a"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

PROFILE_CANONICAL = "canonical_rectangle"
PROFILE_IRREGULAR = "irregular_enclosure"
PROFILE_SHARED = "shared_color_pair"
PROFILE_CONTRAST = "closure_contrast"
SCHEDULE_PROFILES = (
    PROFILE_CANONICAL,
    PROFILE_IRREGULAR,
    PROFILE_SHARED,
    PROFILE_CONTRAST,
)

SUMMARY = (
    "A canonical-scale zero-background grid contains one or two same-color wall "
    "objects. Closed walls enclose one or two zero regions; an optional open "
    "wall is a contrast object. Fill exactly the zero regions disconnected from "
    "the canvas border and surrounded by one color. Scheduled profiles include "
    "a canonical rectangle, an irregular enclosure, two separated same-color "
    "holes, and a closed/open contrast."
)

INVARIANTS = [
    "background is 0 and all wall cells share one non-zero color",
    "every generated input contains at least one enclosed 4-connected zero region",
    "each enclosed region has exactly one neighboring non-zero color",
    "the four observable profiles are scheduled once per four consecutive draws",
]

AXES = {
    "profile": {
        "type": "str",
        "default": "four-slot semantic lesson schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# These are the five exact canonical canvas profiles.
_CANVASES = ((6, 10), (7, 8), (8, 9), (8, 10), (9, 9))
_IRREGULAR_INTERIORS = (
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
    frozenset({(0, 0), (1, 0), (2, 0), (2, 1)}),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Deterministically cover every semantic profile in each four-item window."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = frozenset(cells)
    if not points:
        return points
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r - r0, c - c0) for r, c in points)


def _transform_object(
    wall: frozenset[tuple[int, int]],
    footprint: frozenset[tuple[int, int]],
    transform: int,
) -> tuple[frozenset[tuple[int, int]], frozenset[tuple[int, int]]]:
    def raw(points):
        out = set(points)
        if transform >= 4:
            out = {(r, -c) for r, c in out}
        for _ in range(transform % 4):
            out = {(c, -r) for r, c in out}
        return out

    raw_wall = raw(wall)
    raw_footprint = raw(footprint)
    r0 = min(r for r, _ in raw_footprint)
    c0 = min(c for _, c in raw_footprint)
    shift = lambda points: frozenset((r - r0, c - c0) for r, c in points)
    return shift(raw_wall), shift(raw_footprint)


def _bbox_footprint(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    points = frozenset(cells)
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    return frozenset((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def _rectangle_wall(height: int, width: int) -> frozenset[tuple[int, int]]:
    return frozenset(
        (r, c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    )


def _irregular_object(interior):
    interior = _normalize(interior)
    # Moore-neighbour dilation gives a connected, one-cell-thick wall even at
    # concave turns; the original polyomino remains a single zero hole.
    wall = {
        (r + dr, c + dc)
        for r, c in interior
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0) and (r + dr, c + dc) not in interior
    }
    union = wall | set(interior)
    r0 = min(r for r, _ in union)
    c0 = min(c for _, c in union)
    wall = frozenset((r - r0, c - c0) for r, c in wall)
    interior = frozenset((r - r0, c - c0) for r, c in interior)
    return wall, _bbox_footprint(wall | interior)


def _open_u_object():
    wall = frozenset(
        {
            (0, 0), (0, 2),
            (1, 0), (1, 2),
            (2, 0), (2, 1), (2, 2),
        }
    )
    return wall, _bbox_footprint(wall)


def _placements(
    wall: frozenset[tuple[int, int]],
    footprint: frozenset[tuple[int, int]],
    h: int,
    w: int,
    *,
    margin: int = 0,
):
    height = max(r for r, _ in footprint) + 1
    width = max(c for _, c in footprint) + 1
    out = []
    for top in range(margin, h - height - margin + 1):
        for left in range(margin, w - width - margin + 1):
            out.append(
                (
                    frozenset((r + top, c + left) for r, c in wall),
                    frozenset((r + top, c + left) for r, c in footprint),
                )
            )
    return out


def _separated(first, second) -> bool:
    return all(
        max(abs(r1 - r2), abs(c1 - c2)) > 1
        for r1, c1 in first
        for r2, c2 in second
    )


def _choose_single(wall, footprint, h, w, rng, *, margin=0):
    options = _placements(wall, footprint, h, w, margin=margin)
    if not options:
        raise ValueError("canvas cannot fit the requested enclosure profile")
    return rng.choice(options)[0]


def _choose_pair(first, second, h, w, rng):
    left = _placements(*first, h, w)
    right = _placements(*second, h, w)
    options = [
        (wall_a, wall_b)
        for wall_a, footprint_a in left
        for wall_b, footprint_b in right
        if _separated(footprint_a, footprint_b)
    ]
    if not options:
        raise ValueError("canvas cannot fit two separated wall objects")
    return rng.choice(options)


def _draw_profile(ctx, seed, sample_index, difficulty, overrides):
    if overrides.get("profile") is not None:
        return ctx.draw_choice("profile", SCHEDULE_PROFILES)
    return ctx.draw_choice(
        "profile", (schedule_profile(seed, sample_index, difficulty),)
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)}")
    if "profile" in overrides and overrides["profile"] is not None:
        if type(overrides["profile"]) is not str:
            raise ValueError("profile override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, seed, sample_index, difficulty, overrides)
    band_tag = difficulty or "default"
    h, w = ctx.draw_rng(f"canvas:{band_tag}").choice(_CANVASES)
    color = ctx.draw_color(f"wall_color:{band_tag}", exclude={0})
    grid = full_grid(h, w, 0)

    shape_rng = ctx.draw_rng(f"shape:{band_tag}")
    layout_rng = ctx.draw_rng(f"layout:{band_tag}")

    if profile == PROFILE_CANONICAL:
        outer_h = shape_rng.randint(4, min(6, h - 2))
        outer_w = shape_rng.randint(4, min(7, w - 2))
        wall = _rectangle_wall(outer_h, outer_w)
        placed = _choose_single(wall, _bbox_footprint(wall), h, w, layout_rng, margin=1)
        walls = (placed,)
    elif profile == PROFILE_IRREGULAR:
        wall, footprint = _irregular_object(shape_rng.choice(_IRREGULAR_INTERIORS))
        wall, footprint = _transform_object(wall, footprint, shape_rng.randrange(8))
        walls = (_choose_single(wall, footprint, h, w, layout_rng),)
    elif profile == PROFILE_SHARED:
        wall = _rectangle_wall(3, 4)
        obj = (wall, _bbox_footprint(wall))
        walls = _choose_pair(obj, obj, h, w, layout_rng)
    elif profile == PROFILE_CONTRAST:
        closed_wall = _rectangle_wall(4, 4)
        closed = (closed_wall, _bbox_footprint(closed_wall))
        open_wall, open_footprint = _open_u_object()
        opened = _transform_object(open_wall, open_footprint, shape_rng.randrange(8))
        walls = _choose_pair(closed, opened, h, w, layout_rng)
    else:  # draw_choice already validates; defensive for static analyzers.
        raise ValueError(f"unknown profile {profile!r}")

    for wall in walls:
        for r, c in wall:
            grid[r][c] = color
    return grid


def _zero_regions(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    regions = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        cells = {start}
        colors = set()
        touches_border = False
        while queue:
            r, c = queue.popleft()
            touches_border |= r in (0, h - 1) or c in (0, w - 1)
            for dr, dc in _CARDINAL:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                value = grid[rr][cc]
                if value == 0 and (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    cells.add((rr, cc))
                    queue.append((rr, cc))
                elif value != 0:
                    colors.add(value)
        regions.append(
            {
                "cells": frozenset(cells),
                "colors": frozenset(colors),
                "touches_border": touches_border,
            }
        )
    return regions


def _nonzero_components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        cells = {start}
        colors = {grid[start[0]][start[1]]}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    colors.add(grid[point[0]][point[1]])
                    queue.append(point)
        components.append({"cells": frozenset(cells), "colors": frozenset(colors)})
    return components


def _is_rectangle_outline(cells) -> bool:
    if not cells:
        return False
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(cells) == expected


def profile_signature(grid) -> str | None:
    try:
        if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
            return None
        components = _nonzero_components(grid)
        regions = _zero_regions(grid)
    except (TypeError, IndexError):
        return None
    colors = {value for row in grid for value in row if value != 0}
    enclosed = [
        region
        for region in regions
        if not region["touches_border"] and len(region["colors"]) == 1
    ]
    if len(colors) != 1:
        return None
    if len(components) == 1 and len(enclosed) == 1:
        return (
            PROFILE_CANONICAL
            if _is_rectangle_outline(components[0]["cells"])
            else PROFILE_IRREGULAR
        )
    if len(components) == 2 and len(enclosed) == 2:
        return PROFILE_SHARED
    if len(components) == 2 and len(enclosed) == 1:
        return PROFILE_CONTRAST
    return None


def observe_overrides(grid):
    profile = profile_signature(grid)
    if profile is None:
        raise ValueError("grid does not realize a declared profile")
    return {"profile": profile}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is not rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        return [f"expected exactly one wall color, found {len(colors)}"]
    regions = _zero_regions(grid)
    enclosed = [region for region in regions if not region["touches_border"]]
    if not enclosed:
        return ["input contains no enclosed zero region"]
    if any(len(region["colors"]) != 1 for region in enclosed):
        return ["every enclosed zero region must have exactly one neighboring color"]
    profile = profile_signature(grid)
    if profile not in SCHEDULE_PROFILES:
        return ["input does not realize a supported enclosure profile"]
    return []

# ---------------------------------------------------------------------------
# Diagnostic semantic contract.  These functions are never label authorities:
# generated training outputs still come from the selected Racket program.
# ---------------------------------------------------------------------------


def rule_mirror(grid):
    """Independent Python mirror used only by tests and semantic probes."""
    out = [list(row) for row in grid]
    for region in _zero_regions(grid):
        if region["touches_border"] or len(region["colors"]) != 1:
            continue
        color = next(iter(region["colors"]))
        for r, c in region["cells"]:
            out[r][c] = color
    return out


def global_color_bbox(grid):
    """Plausible wrong rule: complete one global bounding box per color."""
    out = [list(row) for row in grid]
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = color
    return out


def strict_canonical_like(grid):
    """Accept the task's canonical one-rectangle manifold, not coarse marginals."""
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in set(_CANVASES):
        return ["canvas dimensions are outside the five canonical profiles"]
    if profile_signature(grid) != PROFILE_CANONICAL:
        return ["canonical inputs contain exactly one hollow rectangular wall"]
    return []


def _profile_witness(profile):
    return lambda grid: profile_signature(grid) == profile


def _bbox_counterexample(grid):
    return rule_mirror(grid) != global_color_bbox(grid)


SEMANTIC_WITNESSES = {
    "canonical_rectangle_profile": _profile_witness(PROFILE_CANONICAL),
    "irregular_enclosure_profile": _profile_witness(PROFILE_IRREGULAR),
    "shared_color_pair_profile": _profile_witness(PROFILE_SHARED),
    "closure_contrast_profile": _profile_witness(PROFILE_CONTRAST),
    "bbox_counterexample": _bbox_counterexample,
}
SEMANTIC_RIVALS = {"global_color_bbox": global_color_bbox}
WITNESS_RIVALS = {"bbox_counterexample": ["global_color_bbox"]}
BRANCH_WITNESSES = (
    "canonical_rectangle_profile",
    "irregular_enclosure_profile",
    "shared_color_pair_profile",
    "closure_contrast_profile",
)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Check a materialized lesson against the declared finite rival family."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"pair {index} lacks input/output")
            continue
        grammar_errors = self_check(pair["input"])
        if grammar_errors:
            reasons.append(f"pair {index} violates the input grammar: {grammar_errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} disagrees with the diagnostic rule mirror")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if (
            all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]
        ):
            reasons.append(f"unrefuted rival changes query: {name}")
    return reasons

