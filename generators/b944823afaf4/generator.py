"""Generator for ``b944823afaf4`` — row-span closure inside gray walls.

A full-height color-5 wall is a hard horizontal boundary.  In each row and
inside each wall-bounded segment independently, the canonical rule replaces
all cells from the first through last non-zero marker by color 8.  Wall cells
stay 5 and empty segments stay 0.

The curriculum is deliberately three-phase.  Canonical anchors reproduce the
public wall/marker grammar; the two other phases put markers in more than one
room on the same row and include singleton rooms.  Those controls refute the
otherwise-plausible shortcuts "ignore the walls" and "only fill between a
pair".  Non-anchor phases also vary the marker color so color 2 is not learned
as the transformation trigger.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b944823afaf4"
TASK_ID = "b944823afaf4"
VERSION = "4.0.0"
RULE_HASH = "45961b26424c"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "Full-height color-5 walls split every row into independent horizontal "
    "segments. In each segment containing markers, replace the complete span "
    "from its first through last non-zero marker by color 8; preserve walls "
    "and leave empty segments at 0."
)

INVARIANTS = [
    "background is 0 and every wall is a full-height interior color-5 column",
    "generated markers use one non-special input color, observable from the grid",
    "wall-bounded row segments are transformed independently",
    "ordinary lessons always contain a visible within-segment gap to close",
    "every two-example curriculum window contains wall-separation, singleton, and non-color-2 controls",
]

MARKER_COLORS = (1, 2, 3, 4, 6, 7, 9)
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "8..9"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "13..14"},
    "n_walls": {"type": "int", "default": "difficulty-shaped 1..3", "valid": "1..3"},
    "marker_rows": {"type": "int", "default": "difficulty-shaped 2..6", "valid": "2..6"},
    "marker_color": {
        "type": "int",
        "default": "2 on canonical anchors; otherwise non-2 scheduled palette",
        "valid": "1|2|3|4|6|7|9",
    },
}

# The strict semantic hook is intentionally task-linked and should occupy one
# of the three scheduled curriculum slots rather than only a vanishing tail.
MIN_STRICT_FRAC = 0.25
SCHEDULE_PROFILES = tuple(range(3))

_CANONICAL_DIMENSIONS = ((8, 13), (8, 14), (9, 14))
_CANONICAL_WALLS = {
    (8, 13): (4, 9),
    (8, 14): (4, 9),
    (9, 14): (5, 10),
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> int:
    """Three-slot curriculum schedule; independent of seed and difficulty."""
    del seed, difficulty
    return sample_index % 3


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label in ("grid_h", "grid_w", "n_walls", "marker_rows", "marker_color"):
        if label in overrides and overrides[label] is not None:
            value = overrides[label]
            if type(value) is not int:
                raise ValueError(f"{label} must be an integer")


def _axis_overridden(ctx, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _draw_int_axis(ctx, label: str, default_lo: int, default_hi: int, full_lo: int, full_hi: int) -> int:
    """Use the full declared domain for explicit overrides, band defaults otherwise."""
    if _axis_overridden(ctx, label):
        return ctx.draw_int(label, full_lo, full_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_dimensions(ctx, profile: int) -> tuple[int, int]:
    # Normal draws stay on the exact canonical (h, w, palette-size) envelope in
    # every difficulty band.  Exact overrides may request the lawful 9x13
    # cross-product point too; the observer verifies it from the returned grid.
    canonical_h, canonical_w = _CANONICAL_DIMENSIONS[(ctx.sample_index // 3) % len(_CANONICAL_DIMENSIONS)]
    if _axis_overridden(ctx, "grid_h"):
        h = ctx.draw_int("grid_h", 8, 9)
    else:
        h = ctx.draw_int("grid_h", canonical_h, canonical_h)
    if _axis_overridden(ctx, "grid_w"):
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        w = ctx.draw_int("grid_w", canonical_w, canonical_w)
    del profile
    return h, w


def _draw_parameters(ctx, profile: int, band: str) -> tuple[int, int, int]:
    if profile == 0:
        n_walls = _draw_int_axis(ctx, "n_walls", 2, 2, 1, 3)
        marker_rows = _draw_int_axis(ctx, "marker_rows", 4, 4, 2, 6)
    elif band == "easy":
        n_walls = _draw_int_axis(ctx, "n_walls", 1, 2, 1, 3)
        marker_rows = _draw_int_axis(ctx, "marker_rows", 2, 3, 2, 6)
    elif band == "hard":
        n_walls = _draw_int_axis(ctx, "n_walls", 2, 3, 1, 3)
        marker_rows = _draw_int_axis(ctx, "marker_rows", 4, 6, 2, 6)
    else:
        n_walls = _draw_int_axis(ctx, "n_walls", 1, 3, 1, 3)
        marker_rows = _draw_int_axis(ctx, "marker_rows", 3, 5, 2, 6)

    if _axis_overridden(ctx, "marker_color"):
        marker_color = ctx.draw_choice("marker_color", MARKER_COLORS)
    elif profile == 0:
        marker_color = ctx.draw_choice("marker_color", (2,))
    else:
        # All non-anchor slots are explicit counterexamples to a color-2-only
        # interpretation.  Different seeds still vary the non-2 color.
        marker_color = ctx.draw_choice("marker_color", tuple(c for c in MARKER_COLORS if c != 2))
    return n_walls, marker_rows, marker_color


def _wall_sets(width: int, n_walls: int) -> list[tuple[int, ...]]:
    """Interior wall layouts leaving at least two columns in every segment."""
    choices: list[tuple[int, ...]] = []
    for walls in combinations(range(2, width - 2), n_walls):
        bounds = (-1, *walls, width)
        segment_widths = [right - left - 1 for left, right in zip(bounds, bounds[1:])]
        if min(segment_widths) >= 2:
            choices.append(tuple(walls))
    return choices


def _segments(walls: tuple[int, ...] | list[int], width: int) -> list[tuple[int, int]]:
    bounds = (-1, *sorted(walls), width)
    return [(left + 1, right - 1) for left, right in zip(bounds, bounds[1:]) if right - left > 1]


def _choose_walls(ctx, height: int, width: int, n_walls: int, profile: int) -> tuple[int, ...]:
    if profile == 0 and not _axis_overridden(ctx, "n_walls") and (height, width) in _CANONICAL_WALLS:
        return _CANONICAL_WALLS[(height, width)]
    candidates = _wall_sets(width, n_walls)
    if not candidates:
        raise ValueError(f"no legal {n_walls}-wall layout for width {width}")
    return ctx.draw_rng("wall_layout").choice(candidates)


def _two_with_gap(rng, segment: tuple[int, int]) -> tuple[int, int]:
    lo, hi = segment
    pairs = [(a, b) for a in range(lo, hi + 1) for b in range(a + 2, hi + 1)]
    if not pairs:
        raise ValueError(f"segment {segment} has no two-marker visible-gap placement")
    return rng.choice(pairs)


def _put(grid: list[list[int]], row: int, columns: list[int] | tuple[int, ...], color: int) -> None:
    for column in columns:
        grid[row][column] = color


def _populate_anchor(grid, rows, segments, color, rng) -> None:
    roomy = [segment for segment in segments if segment[1] - segment[0] >= 2]
    if not roomy:
        raise ValueError("canonical anchor requires a segment at least three cells wide")
    for row in rows:
        segment = rng.choice(roomy)
        _put(grid, row, _two_with_gap(rng, segment), color)


def _populate_controlled(grid, rows, segments, color, rng, profile: int) -> None:
    """Create controls that *guarantee* disagreement with the named rivals."""
    roomy = [segment for segment in segments if segment[1] - segment[0] >= 2]
    if len(segments) < 2 or not roomy:
        raise ValueError("controlled lesson requires two rooms and one width>=3 room")

    # Put one singleton at the far side of each of two adjacent rooms.  The
    # true rule changes only those singleton cells to 8.  A wall-blind row-span
    # rule necessarily paints additional blank cells on at least one side of
    # the separating wall, so this is a guaranteed killing witness rather than
    # merely a row that happens to contain markers in multiple rooms.
    first_row = rows[0]
    pair_index = rng.randrange(len(segments) - 1)
    left_segment = segments[pair_index]
    right_segment = segments[pair_index + 1]
    _put(grid, first_row, [left_segment[0], right_segment[1]], color)

    # A second row carries a genuine interior gap, killing the marker-only
    # recoloring shortcut.  The cross-wall row above simultaneously supplies
    # singleton rooms, killing the "two endpoints required" shortcut.
    second_row = rows[1]
    gap_segment = rng.choice(roomy)
    _put(grid, second_row, _two_with_gap(rng, gap_segment), color)

    for row in rows[2:]:
        segment = rng.choice(segments)
        lo, hi = segment
        if profile == 1 and hi - lo >= 2 and rng.random() < 0.7:
            _put(grid, row, _two_with_gap(rng, segment), color)
        else:
            _put(grid, row, [rng.randint(lo, hi)], color)


def _grid_facts(grid) -> dict[str, Any]:
    """Analyze the task grammar without computing the transformation output."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    height = len(grid)
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"]}
    if not (8 <= height <= 9 and 13 <= width <= 14):
        errors.append(f"dimensions {height}x{width} outside task grammar 8..9 x 13..14")

    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("grid contains a non-integer or color outside 0..9")
                return {"errors": errors}

    full_walls = [column for column in range(width) if all(grid[row][column] == 5 for row in range(height))]
    partial_wall_cells = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == 5 and column not in full_walls
    ]
    if partial_wall_cells:
        errors.append(f"color-5 walls must be full height; partial cells include {partial_wall_cells[:3]}")
    if not (1 <= len(full_walls) <= 3):
        errors.append(f"expected 1..3 full-height walls, found {full_walls}")
    if any(column < 2 or column > width - 3 for column in full_walls):
        errors.append("walls must be interior and leave at least two edge-segment columns")
    if len(full_walls) >= 2 and any(b - a < 3 for a, b in zip(full_walls, full_walls[1:])):
        errors.append("adjacent walls must leave at least two columns between them")

    marker_cells = [
        (row, column, grid[row][column])
        for row in range(height)
        for column in range(width)
        if column not in full_walls and grid[row][column] != 0
    ]
    marker_colors = sorted({value for _, _, value in marker_cells})
    if any(value in (5, 8) for value in marker_colors):
        errors.append(f"marker colors may not use wall/output colors 5 or 8: {marker_colors}")
    if len(marker_colors) != 1:
        errors.append(f"expected one marker color, found {marker_colors}")
    marker_rows = sorted({row for row, _, _ in marker_cells})
    if not (1 <= len(marker_rows) <= 6):
        errors.append(f"expected 1..6 marker rows, found {len(marker_rows)}")

    segments = _segments(full_walls, width) if full_walls else []
    per_row_segments: dict[int, list[list[int]]] = {}
    visible_gap = False
    singleton_segment = False
    cross_wall_row = False
    for row in marker_rows:
        row_groups: list[list[int]] = []
        for lo, hi in segments:
            marks = [column for rr, column, _ in marker_cells if rr == row and lo <= column <= hi]
            if marks:
                row_groups.append(sorted(marks))
                if len(marks) == 1:
                    singleton_segment = True
                if len(marks) >= 2 and max(marks) - min(marks) >= 2:
                    visible_gap = True
        if len(row_groups) >= 2:
            cross_wall_row = True
        per_row_segments[row] = row_groups

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "walls": tuple(full_walls),
        "segments": tuple(segments),
        "marker_cells": tuple(marker_cells),
        "marker_colors": tuple(marker_colors),
        "marker_color": marker_colors[0] if len(marker_colors) == 1 else None,
        "marker_rows": tuple(marker_rows),
        "per_row_segments": per_row_segments,
        "visible_gap": visible_gap,
        "singleton_segment": singleton_segment,
        "cross_wall_row": cross_wall_row,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural task-grammar checker; teaching controls are checked elsewhere."""
    del difficulty, meta
    return list(_grid_facts(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from a returned generated grid."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_walls": len(facts["walls"]),
        "marker_rows": len(facts["marker_rows"]),
        "marker_color": facts["marker_color"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, band)
    height, width = _draw_dimensions(ctx, profile)
    n_walls, marker_rows, marker_color = _draw_parameters(ctx, profile, band)
    walls = _choose_walls(ctx, height, width, n_walls, profile)
    segments = _segments(walls, width)

    grid = full_grid(height, width, 0)
    for column in walls:
        for row in range(height):
            grid[row][column] = 5

    row_rng = ctx.draw_rng("marker_rows_layout")
    rows = sorted(row_rng.sample(range(height), marker_rows))
    marker_rng = ctx.draw_rng("marker_layout")
    if profile == 0 and not overrides:
        _populate_anchor(grid, rows, segments, marker_color, marker_rng)
    elif profile == 0:
        # Explicit overrides must remain valid even when they intentionally move
        # away from the canonical anchor slot.  The scene still teaches a real
        # visible span but is not forced to satisfy curriculum-only controls.
        roomy = [segment for segment in segments if segment[1] - segment[0] >= 2]
        if not roomy:
            raise ValueError("requested wall layout leaves no room for a visible span")
        _put(grid, rows[0], _two_with_gap(marker_rng, marker_rng.choice(roomy)), marker_color)
        for row in rows[1:]:
            segment = marker_rng.choice(segments)
            _put(grid, row, [marker_rng.randint(segment[0], segment[1])], marker_color)
    else:
        _populate_controlled(grid, rows, segments, marker_color, marker_rng, profile)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator constructed invalid grid: " + "; ".join(errors))

    facts = _grid_facts(grid)
    # These are curriculum obligations, deliberately NOT self_check grammar.
    if not facts["visible_gap"]:
        raise AssertionError("ordinary draw hid the within-segment gap-close operation")
    if not overrides and profile in (1, 2):
        if not facts["cross_wall_row"]:
            raise AssertionError("control profile failed to place markers across a wall")
        if not facts["singleton_segment"]:
            raise AssertionError("control profile failed to include a singleton segment")
        if facts["marker_color"] == 2:
            raise AssertionError("control profile failed to refute the color-2-only shortcut")

    observed = observe_overrides(grid)
    for axis in AXES:
        requested = ctx.axis_value(axis)
        if requested is not None and observed[axis] != requested:
            raise AssertionError(
                f"constructed {axis}={observed[axis]!r}, requested {requested!r}"
            )
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python audit mirror; canonical Racket remains output authority."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    out = full_grid(facts["height"], facts["width"], 0)
    for column in facts["walls"]:
        for row in range(facts["height"]):
            out[row][column] = 5
    for row in range(facts["height"]):
        for lo, hi in facts["segments"]:
            marks = [column for rr, column, _ in facts["marker_cells"] if rr == row and lo <= column <= hi]
            if marks:
                _put(out, row, list(range(min(marks), max(marks) + 1)), 8)
    return out


def strict_canonical_like(grid) -> list[str]:
    """Recognize the public canonical grammar, including its wall positions."""
    facts = _grid_facts(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    dimensions = (facts["height"], facts["width"])
    expected_walls = _CANONICAL_WALLS.get(dimensions)
    if expected_walls is None:
        reasons.append(f"dimensions {dimensions} are not a canonical profile")
        return reasons
    if facts["walls"] != expected_walls:
        reasons.append(f"canonical {dimensions} walls are {expected_walls}, got {facts['walls']}")
    if facts["marker_color"] != 2:
        reasons.append(f"canonical markers are color 2, got {facts['marker_color']}")
    if len(facts["marker_rows"]) != 4:
        reasons.append(f"canonical inputs have four active rows, got {len(facts['marker_rows'])}")
    for row in facts["marker_rows"]:
        groups = facts["per_row_segments"].get(row, [])
        if len(groups) != 1 or len(groups[0]) != 2 or groups[0][1] - groups[0][0] < 2:
            reasons.append(
                f"canonical active row {row} has exactly two separated markers in one room"
            )
            break
    return reasons


def _global_row_close(grid) -> list[list[int]]:
    """Plausible rival: walls are decorative, so close one span per whole row."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    out = full_grid(facts["height"], facts["width"], 0)
    wall_set = set(facts["walls"])
    for column in facts["walls"]:
        for row in range(facts["height"]):
            out[row][column] = 5
    for row in range(facts["height"]):
        marks = [column for rr, column, _ in facts["marker_cells"] if rr == row]
        if marks:
            for column in range(min(marks), max(marks) + 1):
                if column not in wall_set:
                    out[row][column] = 8
    return out


def _pair_required(grid) -> list[list[int]]:
    """Plausible rival: a singleton is not a span and therefore stays unchanged."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    out = full_grid(facts["height"], facts["width"], 0)
    for column in facts["walls"]:
        for row in range(facts["height"]):
            out[row][column] = 5
    for row in range(facts["height"]):
        for lo, hi in facts["segments"]:
            marks = [(column, value) for rr, column, value in facts["marker_cells"] if rr == row and lo <= column <= hi]
            if len(marks) >= 2:
                for column in range(min(c for c, _ in marks), max(c for c, _ in marks) + 1):
                    out[row][column] = 8
            elif len(marks) == 1:
                column, value = marks[0]
                out[row][column] = value
    return out


def _markers_only(grid) -> list[list[int]]:
    """Plausible rival: recolor marker cells but never close an interior gap."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    out = full_grid(facts["height"], facts["width"], 0)
    for column in facts["walls"]:
        for row in range(facts["height"]):
            out[row][column] = 5
    for row, column, _value in facts["marker_cells"]:
        out[row][column] = 8
    return out


def _color2_only(grid) -> list[list[int]]:
    """Plausible rival: only canonical color-2 markers trigger closure."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid scene: " + "; ".join(facts["errors"]))
    out = full_grid(facts["height"], facts["width"], 0)
    for column in facts["walls"]:
        for row in range(facts["height"]):
            out[row][column] = 5
    for row in range(facts["height"]):
        for lo, hi in facts["segments"]:
            marks = [column for rr, column, value in facts["marker_cells"] if rr == row and value == 2 and lo <= column <= hi]
            if marks:
                for column in range(min(marks), max(marks) + 1):
                    out[row][column] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "markers_only": _markers_only,
    "ignore_walls": _global_row_close,
    "pair_required": _pair_required,
    "color2_only": _color2_only,
}


def _rival_differs(grid, rival_name: str) -> bool:
    facts = _grid_facts(grid)
    if facts["errors"]:
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "visible_gap_close": lambda grid: _rival_differs(grid, "markers_only"),
    "wall_separates_spans": lambda grid: _rival_differs(grid, "ignore_walls"),
    "singleton_recolors": lambda grid: _rival_differs(grid, "pair_required"),
    "marker_color_not_2": lambda grid: _rival_differs(grid, "color2_only"),
}

WITNESS_RIVALS = {
    "visible_gap_close": ["markers_only"],
    "wall_separates_spans": ["ignore_walls"],
    "singleton_recolors": ["pair_required"],
    "marker_color_not_2": ["color2_only"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_walls": _global_row_close,
    "pair_required": _pair_required,
    "color2_only": _color2_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson whose demonstrations leave a named rival alive."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    episodes = [*demos, query]
    for index, episode in enumerate(episodes):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(episode, dict) or "input" not in episode or "output" not in episode:
            reasons.append(f"{role} is not an input/output pair")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{role} input is malformed: {errors[:2]}")
            continue
        if rule_mirror(episode["input"]) != episode["output"]:
            reasons.append(f"{role} output disagrees with the wall-segment span rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"demos do not falsify shortcut '{name}'")
    return reasons
