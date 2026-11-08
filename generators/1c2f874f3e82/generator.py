"""Constructive sampler for ARC task 1c2f874f3e82.

The immutable Racket authority interprets the lone color-1 cell as an origin and
the connected color-2 object as signed offsets from that origin.  It stamps the
shape in color 8 at every marker: color 3 keeps the offsets, color 4 rotates
(dr, dc) -> (dc, -dr), and color 5 mirrors (dr, dc) -> (dr, -dc).

This module generates inputs only.  It deliberately uses complete, disjoint,
in-bounds stamps so every advertised source cell and repeated marker is visible
in the labelled output rather than being hidden by clipping or overlap.
"""
from __future__ import annotations

from collections import deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c2f874f3e82"
TASK_ID = GENERATOR_ID
RULE_HASH = "bb27569b9c6f"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "A connected color-2 source is encoded as signed offsets from one color-1 "
    "anchor. Colors 3, 4 and 5 request identity, clockwise-quarter-turn and "
    "vertical-mirror copies respectively; every resulting cell is color 8."
)

INVARIANTS = [
    "grid uses only colors 0..5 and contains exactly one color-1 anchor",
    "the color-2 source is one 4-connected asymmetric object with 3..7 cells",
    "there is at least one marker of each color 3, 4 and 5 (3..5 total)",
    "all transformed stamps are complete, pairwise disjoint and avoid input symbols",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 10..14; canonical profiles recur", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "scheduled 16..20; canonical profiles recur", "valid": "16..20"},
    "source_cells": {"type": "int", "default": "scheduled 3..7; every four-pair lesson includes >5", "valid": "3..7"},
    "n_markers": {"type": "int", "default": "scheduled 3..5; every four-pair lesson includes a repeated color", "valid": "3..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

# The seven-slot curriculum covers every exact control value.  More importantly,
# every four consecutive slots contain (a) a 6/7-cell source, refuting truncation
# to the <=5 cells seen canonically, and (b) a repeated marker color, refuting
# "use only the first marker of each color".  The first three size pairs are the
# three canonical input profiles.
_SCHEDULE = (
    (10, 18, 6, 4),
    (12, 18, 3, 5),
    (12, 19, 7, 3),
    (11, 16, 4, 4),
    (13, 17, 6, 5),
    (14, 20, 5, 4),
    (10, 19, 7, 5),
)

# Connected, asymmetric source offsets relative to the color-1 anchor.  The
# anchor itself is never a source cell.  Variants stay within Chebyshev radius 3,
# making all advertised combinations constructive even on a 10x16 grid.
_TEMPLATES = {
    3: (
        ((1, 0), (1, 1), (2, 1)),
        ((0, 2), (1, 1), (1, 2)),
    ),
    4: (
        ((0, 2), (1, 1), (1, 2), (1, 3)),
        ((1, -1), (2, -1), (3, -1), (3, 0)),
    ),
    5: (
        ((1, -1), (2, -1), (2, 0), (3, 0), (3, 1)),
        ((0, 2), (1, 1), (1, 2), (2, 2), (2, 3)),
    ),
    6: (
        ((0, 2), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
        ((1, -2), (1, -1), (2, -1), (2, 0), (3, 0), (3, 1)),
    ),
    7: (
        ((0, 2), (1, 1), (1, 2), (2, 1), (2, 2), (2, 3), (3, 3)),
        ((1, -2), (1, -1), (2, -1), (2, 0), (2, 1), (3, 0), (3, 1)),
    ),
}

_DIhedral = (
    lambda r, c: (r, c),
    lambda r, c: (c, -r),
    lambda r, c: (-r, -c),
    lambda r, c: (-c, r),
    lambda r, c: (r, -c),
    lambda r, c: (-r, c),
    lambda r, c: (c, r),
    lambda r, c: (-c, -r),
)


def _schedule_slot(sample_index, difficulty):
    shift = {"easy": 0, "medium": 2, "hard": 4}.get(difficulty, 0)
    return (sample_index + shift) % len(_SCHEDULE)


def schedule_profile(seed, sample_index, difficulty=None):
    """Public schedule identifier used by semantic-census diagnostics."""
    del seed
    return f"slot-{_schedule_slot(sample_index, difficulty)}"


SCHEDULE_PROFILES = [f"slot-{i}" for i in range(len(_SCHEDULE))]


def _scheduled_choice(ctx, name, domain, target):
    """Draw ``target`` while exposing the complete exact-override domain.

    GenCtx's keyed RNG is reproducible.  We first ask an equivalent fresh RNG
    which position draw_choice will select, then place the scheduled value at
    that position while retaining every legal value in the option tuple.  Thus
    the recorded draw is truthful, every override is accepted in every band,
    and the lesson schedule is deterministic rather than probabilistic.
    """
    domain = tuple(domain)
    if target not in domain:
        raise ValueError(f"scheduled {name}={target!r} outside {domain!r}")
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, domain)
    length = max(16, len(domain) * 3)
    picked = ctx.draw_rng(name).choice(range(length))
    options = [target] * length
    positions = [i for i in range(length) if i != picked]
    for position, value in zip(positions, (v for v in domain if v != target)):
        options[position] = value
    return ctx.draw_choice(name, options)


def _transform(offset, marker_color):
    dr, dc = offset
    if marker_color == 3:
        return dr, dc
    if marker_color == 4:
        return dc, -dr
    if marker_color == 5:
        return dr, -dc
    raise ValueError(f"unsupported marker color {marker_color}")


def _oriented_template(ctx, source_cells):
    variants = _TEMPLATES[source_cells]
    template = ctx.draw_choice("source_template", variants)
    orientation = ctx.draw_int("source_orientation", 0, 7)
    transform = _DIhedral[orientation]
    return tuple(sorted(transform(r, c) for r, c in template))


def _stamp(marker, color, offsets):
    mr, mc = marker
    return frozenset((mr + dr, mc + dc) for dr, dc in (_transform(x, color) for x in offsets))


def _in_bounds(cells, h, w):
    return all(0 <= r < h and 0 <= c < w for r, c in cells)


def _anchor_candidates(h, w, offsets, rng):
    candidates = []
    for ar in range(h):
        for ac in range(w):
            source = {(ar + dr, ac + dc) for dr, dc in offsets}
            if _in_bounds(source, h, w) and (ar, ac) not in source:
                candidates.append((ar, ac))
    rng.shuffle(candidates)
    # Prefer a canonical-like source on the left while retaining every feasible
    # anchor as a deterministic fallback.
    candidates.sort(key=lambda p: (p[1] > w // 2, abs(p[0] - h // 2), p[1]))
    return candidates


def _marker_plan(ctx, count):
    plan = [3, 4, 5]
    if count >= 4:
        plan.append(ctx.draw_choice("extra_marker_color_0", (3, 4, 5)))
    if count >= 5:
        first = plan[-1]
        plan.append(ctx.draw_choice("extra_marker_color_1", tuple(c for c in (3, 4, 5) if c != first)))
    ctx.draw_rng("marker_order").shuffle(plan)
    return tuple(plan)


def _place_markers(h, w, offsets, occupied, plan, rng):
    """Backtrack over complete-stamp candidates; returns marker/color pairs."""
    candidates = {}
    for color in (3, 4, 5):
        rows = []
        for r in range(h):
            for c in range(w):
                point = (r, c)
                if point in occupied:
                    continue
                stamp = _stamp(point, color, offsets)
                if _in_bounds(stamp, h, w) and not (stamp & occupied) and point not in stamp:
                    rows.append((point, stamp))
        rng.shuffle(rows)
        # Spread early attempts around the canvas; random order breaks ties.
        rows.sort(key=lambda item: (abs(item[0][0] - h // 2) + abs(item[0][1] - (3 * w) // 4)))
        candidates[color] = rows

    chosen: list[tuple[int, tuple[int, int], frozenset]] = []
    marker_points: set[tuple[int, int]] = set()
    output_points: set[tuple[int, int]] = set()

    def search(index):
        if index == len(plan):
            return True
        color = plan[index]
        for point, stamp in candidates[color]:
            if point in marker_points or point in output_points:
                continue
            if stamp & output_points or stamp & marker_points:
                continue
            if any(abs(point[0] - old[0]) + abs(point[1] - old[1]) < 2 for old in marker_points):
                continue
            chosen.append((color, point, stamp))
            marker_points.add(point)
            output_points.update(stamp)
            if search(index + 1):
                return True
            chosen.pop()
            marker_points.remove(point)
            output_points.difference_update(stamp)
        return False

    if search(0):
        return [(color, point) for color, point, _ in chosen]
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    target_h, target_w, target_source, target_markers = _SCHEDULE[_schedule_slot(sample_index, difficulty)]
    h = _scheduled_choice(ctx, "grid_h", range(10, 15), target_h)
    w = _scheduled_choice(ctx, "grid_w", range(16, 21), target_w)
    source_cells = _scheduled_choice(ctx, "source_cells", range(3, 8), target_source)
    n_markers = _scheduled_choice(ctx, "n_markers", range(3, 6), target_markers)

    offsets = _oriented_template(ctx, source_cells)
    plan = _marker_plan(ctx, n_markers)
    layout_rng = ctx.draw_rng("constructive_layout")
    for anchor in _anchor_candidates(h, w, offsets, layout_rng):
        source = {(anchor[0] + dr, anchor[1] + dc) for dr, dc in offsets}
        occupied = source | {anchor}
        placements = _place_markers(h, w, offsets, occupied, plan, layout_rng)
        if placements is None:
            continue
        grid = full_grid(h, w, 0)
        grid[anchor[0]][anchor[1]] = 1
        for r, c in source:
            grid[r][c] = 2
        for color, (r, c) in placements:
            grid[r][c] = color
        errors = self_check(grid)
        if errors:
            raise RuntimeError("constructive generator violated its contract: " + "; ".join(errors))
        return grid
    raise RuntimeError("no constructive anchor/marker layout exists for declared axes")


def _cells(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    todo = deque(seen)
    while todo:
        r, c = todo.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in remaining and point not in seen:
                seen.add(point)
                todo.append(point)
    return seen == remaining


def observe_overrides(grid):
    """Recover every advertised exact control from a generated input."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "source_cells": len(_cells(grid, 2)),
        "n_markers": sum(len(_cells(grid, color)) for color in (3, 4, 5)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 1, 2, 3, 4, 5) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,3,4,5"]

    h = len(grid)
    errors = []
    if not 10 <= h <= 14:
        errors.append(f"grid_h={h} outside [10,14]")
    if not 16 <= w <= 20:
        errors.append(f"grid_w={w} outside [16,20]")

    anchors = _cells(grid, 1)
    source = _cells(grid, 2)
    markers = {color: _cells(grid, color) for color in (3, 4, 5)}
    if len(anchors) != 1:
        errors.append(f"expected exactly one color-1 anchor, found {len(anchors)}")
    if not 3 <= len(source) <= 7:
        errors.append(f"source_cells={len(source)} outside [3,7]")
    elif not _connected(source):
        errors.append("color-2 source must be one 4-connected object")
    for color in (3, 4, 5):
        if not markers[color]:
            errors.append(f"missing color-{color} transform marker")
    marker_count = sum(len(points) for points in markers.values())
    if not 3 <= marker_count <= 5:
        errors.append(f"n_markers={marker_count} outside [3,5]")
    if errors or len(anchors) != 1 or not source:
        return errors

    ar, ac = anchors[0]
    offsets = tuple((r - ar, c - ac) for r, c in source)
    transformed_shapes = {
        color: frozenset(_transform(offset, color) for offset in offsets)
        for color in (3, 4, 5)
    }
    if len(set(transformed_shapes.values())) != 3:
        errors.append("source must distinguish identity, rotation and mirror transforms")

    input_symbols = set(anchors) | set(source)
    for points in markers.values():
        input_symbols.update(points)
    seen_output: set[tuple[int, int]] = set()
    for color in (3, 4, 5):
        for marker in markers[color]:
            stamp = _stamp(marker, color, offsets)
            if not _in_bounds(stamp, h, w):
                errors.append(f"color-{color} marker at {marker} clips its stamp")
                continue
            if stamp & input_symbols:
                errors.append(f"color-{color} stamp at {marker} overlaps an input symbol")
            if stamp & seen_output:
                errors.append(f"color-{color} stamp at {marker} overlaps another stamp")
            seen_output.update(stamp)
    return errors


def strict_canonical_like(grid):
    """The declared lawful manifold; canonical examples satisfy it exactly."""
    return self_check(grid)


def _rule_output(grid, *, source_limit=None, first_marker_only=False):
    """Task-domain rival helper, independent from the immutable Racket labels."""
    h, w = len(grid), len(grid[0])
    anchor = _cells(grid, 1)[0]
    source = sorted(_cells(grid, 2))
    if source_limit is not None:
        source = source[:source_limit]
    offsets = [(r - anchor[0], c - anchor[1]) for r, c in source]
    output = [[0] * w for _ in range(h)]
    for color in (3, 4, 5):
        markers = sorted(_cells(grid, color))
        if first_marker_only:
            markers = markers[:1]
        for marker in markers:
            for dr, dc in (_transform(offset, color) for offset in offsets):
                rr, cc = marker[0] + dr, marker[1] + dc
                if 0 <= rr < h and 0 <= cc < w:
                    output[rr][cc] = 8
    return output


def _fixed_four_source_cells(grid):
    """Rival: only the lexicographically first four source cells matter."""
    return _rule_output(grid, source_limit=4)


def _at_most_five_source_cells(grid):
    """Rival: only the <=5 source cells seen in all canonical pairs matter."""
    return _rule_output(grid, source_limit=5)


def _first_marker_only(grid):
    """Rival: process only one marker of each transform color."""
    return _rule_output(grid, first_marker_only=True)


def _source_more_than_four(grid):
    return len(_cells(grid, 2)) > 4


def _source_more_than_five(grid):
    return len(_cells(grid, 2)) > 5


def _repeated_marker_color(grid):
    return any(len(_cells(grid, color)) > 1 for color in (3, 4, 5))


SEMANTIC_WITNESSES = {
    "source_more_than_four": _source_more_than_four,
    "source_more_than_five": _source_more_than_five,
    "repeated_marker_color": _repeated_marker_color,
}
SEMANTIC_RIVALS = {
    "fixed_four_source_cells": _fixed_four_source_cells,
    "at_most_five_source_cells": _at_most_five_source_cells,
    "first_marker_only": _first_marker_only,
}
WITNESS_RIVALS = {
    "source_more_than_four": ["fixed_four_source_cells"],
    "source_more_than_five": ["at_most_five_source_cells"],
    "repeated_marker_color": ["first_marker_only"],
}
# These two rivals fit every canonical labelled pair, not merely its training
# demonstrations, so they are always scored by the lesson gate.
CANONICAL_SHORTCUTS = {
    "at_most_five_source_cells": _at_most_five_source_cells,
    "first_marker_only": _first_marker_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Return named rivals that survive every demo but disagree on the query."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
            differs = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives and differs:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
