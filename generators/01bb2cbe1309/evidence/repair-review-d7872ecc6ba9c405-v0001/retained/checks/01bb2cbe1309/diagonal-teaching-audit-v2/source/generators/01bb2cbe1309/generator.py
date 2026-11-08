"""Generator for ``arc_puzzle_bank_21_set4_d:easy_d03``.

The authoritative rule scans the ORIGINAL input.  A 2x2 window changes only
when one diagonal contains two equal non-zero cells and both opposite corners
are zero; those two zero corners are filled with the diagonal color.

The four-scene schedule deliberately separates the necessary conditions:
canonical positives, a blocked missing corner, an axis-aligned equal pair, and
a diagonal whose endpoint colors differ.  Every four consecutive examples
contain all four scenes, so a lesson cannot silently teach any of the three
canonical-compatible overgeneralizations.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01bb2cbe1309"
TASK_ID = GENERATOR_ID
RULE_HASH = "d45fd86e0516"
VERSION = "2.0.0"

SUMMARY = (
    "Complete an equal-color diagonal pair into its enclosing 2x2 block only "
    "when both missing corners are zero. Blocked diagonals, axis-aligned equal "
    "pairs, and unequal-color diagonals remain unchanged."
)

EXAMPLES_NEEDED = 4
SCENE_PROFILES = ("canonical", "blocked", "axis", "mismatch")
SCHEDULE_PROFILES = SCENE_PROFILES
MIN_STRICT_FRAC = 0.10
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "background is 0 and exactly two non-zero colors are used",
    "every non-zero component fits inside one local 2x2 window",
    "at least one component is an equal-color diagonal pair with two empty corners",
    "at most one negative component appears, selected by scene_profile",
    "distinct local components are separated so no cross-component 2x2 can fire",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted schedule; broad shapes vary by difficulty",
        "valid": "5..12",
        "doc": "Grid height; every value supports every scene profile.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted schedule; broad shapes vary by difficulty",
        "valid": "6..13",
        "doc": "Grid width; every value supports every scene profile.",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 4",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Positive core or one named negative condition.",
    },
}

_CANONICAL_SHAPES = ((6, 7), (5, 6), (7, 7), (6, 8))
_BROAD_SHAPES = {
    "easy": ((7, 9), (8, 9), (7, 10), (8, 10)),
    "medium": ((8, 10), (9, 11), (10, 12), (9, 12)),
    "hard": ((10, 12), (11, 13), (12, 13), (10, 13)),
}
_ALLOWED_KINDS = {
    "positive_main",
    "positive_anti",
    "blocked_main",
    "blocked_anti",
    "axis_horizontal",
    "axis_vertical",
    "mismatch_main",
    "mismatch_anti",
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared four-example teaching schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, got {profile!r}"
        )


def _scheduled_shape(ctx):
    """Choose shape independently of the semantic profile.

    Three fifths of default draws use an exact canonical (h,w,palette-size)
    profile.  The remainder widen spatial/count coverage by difficulty.
    """
    rng = ctx.draw_rng("shape_schedule")
    if rng.randrange(5) < 3:
        return rng.choice(_CANONICAL_SHAPES)
    band = ctx.difficulty if ctx.difficulty in _BROAD_SHAPES else "medium"
    return rng.choice(_BROAD_SHAPES[band])


def _draw_axis(ctx, name, scheduled, options):
    """Record a scheduled default while retaining the complete exact domain."""
    choices = options if ctx.overrides.get(name) is not None else (scheduled,)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=96)
def _all_anchors(h, w):
    return tuple((r, c) for r in range(h - 1) for c in range(w - 1))


@lru_cache(maxsize=96)
def _anchor_pairs(h, w):
    """Pairs of 2x2 anchors with at least one empty row or column between."""
    anchors = _all_anchors(h, w)
    return tuple(
        (first, second)
        for index, first in enumerate(anchors)
        for second in anchors[index + 1 :]
        if abs(first[0] - second[0]) >= 3
        or abs(first[1] - second[1]) >= 3
    )


def _choose_anchors(h, w, target, rng):
    pairs = _anchor_pairs(h, w)
    if not pairs:
        raise ValueError(f"grid {h}x{w} cannot fit two separated 2x2 motifs")
    selected = list(rng.choice(pairs))
    candidates = [anchor for anchor in _all_anchors(h, w) if anchor not in selected]
    rng.shuffle(candidates)
    for anchor in candidates:
        if len(selected) >= target:
            break
        if all(
            abs(anchor[0] - other[0]) >= 3
            or abs(anchor[1] - other[1]) >= 3
            for other in selected
        ):
            selected.append(anchor)
    rng.shuffle(selected)
    return selected


def _positive_count(ctx, h, w):
    if (h, w) in _CANONICAL_SHAPES:
        return 2
    rng = ctx.draw_rng("motif_count")
    band = ctx.difficulty
    if band == "easy":
        return rng.randint(2, 3)
    if band == "hard":
        return rng.randint(4, 6)
    return rng.randint(3, 5)


def _diagonal_cells(anchor, orientation):
    r0, c0 = anchor
    if orientation == "main":
        return ((r0, c0), (r0 + 1, c0 + 1)), ((r0, c0 + 1), (r0 + 1, c0))
    return ((r0, c0 + 1), (r0 + 1, c0)), ((r0, c0), (r0 + 1, c0 + 1))


def _paint_positive(grid, anchor, color, orientation):
    pair, _ = _diagonal_cells(anchor, orientation)
    for r, c in pair:
        grid[r][c] = color


def _paint_negative(grid, anchor, profile, colors, rng):
    first, second = colors
    if profile == "blocked":
        orientation = rng.choice(("main", "anti"))
        pair, holes = _diagonal_cells(anchor, orientation)
        for r, c in pair:
            grid[r][c] = second
        blocker = rng.choice(holes)
        grid[blocker[0]][blocker[1]] = first
        return
    if profile == "axis":
        r0, c0 = anchor
        patterns = (
            ((r0, c0), (r0, c0 + 1)),
            ((r0 + 1, c0), (r0 + 1, c0 + 1)),
            ((r0, c0), (r0 + 1, c0)),
            ((r0, c0 + 1), (r0 + 1, c0 + 1)),
        )
        for r, c in rng.choice(patterns):
            grid[r][c] = second
        return
    if profile == "mismatch":
        orientation = rng.choice(("main", "anti"))
        pair, _ = _diagonal_cells(anchor, orientation)
        assigned = [first, second]
        rng.shuffle(assigned)
        for (r, c), color in zip(pair, assigned):
            grid[r][c] = color
        return
    raise ValueError(f"unsupported negative profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_shape(ctx)
    h = _draw_axis(ctx, "grid_h", scheduled_h, tuple(range(5, 13)))
    w = _draw_axis(ctx, "grid_w", scheduled_w, tuple(range(6, 14)))
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile = _draw_axis(ctx, "scene_profile", scheduled_profile, SCENE_PROFILES)

    layout_rng = ctx.draw_rng("layout")
    colors = tuple(ctx.draw_rng("colors").sample(range(1, 10), 2))
    target_components = _positive_count(ctx, h, w)
    anchors = _choose_anchors(h, w, target_components, layout_rng)
    grid = full_grid(h, w, 0)

    negative_anchor = None
    if profile != "canonical":
        negative_anchor = anchors.pop(layout_rng.randrange(len(anchors)))
    start_orientation = layout_rng.randrange(2)
    for index, anchor in enumerate(anchors):
        orientation = "main" if (index + start_orientation) % 2 == 0 else "anti"
        _paint_positive(grid, anchor, colors[index % 2], orientation)
    if negative_anchor is not None:
        _paint_negative(grid, negative_anchor, profile, colors, layout_rng)
    return grid


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if not width or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return [f"grid dimensions must be within 1..30, got {len(grid)}x{width}"]
    bad = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad:
        return [f"invalid ARC cell(s): {bad[:3]}"]
    return []


def _components8(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        stack.append(neighbor)
        components.append(tuple(sorted(cells)))
    return components


def _classify_component(grid, cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    if r1 - r0 > 1 or c1 - c0 > 1:
        return {"kind": "invalid", "cells": cells, "reason": "bbox exceeds 2x2"}
    values = {(r, c): grid[r][c] for r, c in cells}
    colors = tuple(sorted(set(values.values())))
    if len(cells) == 2:
        (a, b) = cells
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        same = values[a] == values[b]
        if dr == 1 and dc == 1:
            orientation = "main" if (a[0] - a[1]) == (b[0] - b[1]) else "anti"
            kind = ("positive_" if same else "mismatch_") + orientation
            return {"kind": kind, "cells": cells, "colors": colors}
        if same and dr + dc == 1:
            kind = "axis_horizontal" if dr == 0 else "axis_vertical"
            return {"kind": kind, "cells": cells, "colors": colors}
    if len(cells) == 3 and r1 - r0 == 1 and c1 - c0 == 1:
        tl = values.get((r0, c0), 0)
        tr = values.get((r0, c1), 0)
        bl = values.get((r1, c0), 0)
        br = values.get((r1, c1), 0)
        if tl != 0 and tl == br:
            return {"kind": "blocked_main", "cells": cells, "colors": colors}
        if tr != 0 and tr == bl:
            return {"kind": "blocked_anti", "cells": cells, "colors": colors}
    return {
        "kind": "invalid",
        "cells": cells,
        "colors": colors,
        "reason": "not a supported local motif",
    }


def _analysis(grid):
    errors = _grid_errors(grid)
    if errors:
        return [], errors
    components = _components8(grid)
    if not (2 <= len(components) <= 8):
        return [], [f"expected 2..8 separated local components, got {len(components)}"]
    records = [_classify_component(grid, cells) for cells in components]
    invalid = [record for record in records if record["kind"] not in _ALLOWED_KINDS]
    if invalid:
        return records, [
            "unsupported component(s): "
            + "; ".join(
                f"{record.get('cells')} ({record.get('reason', record['kind'])})"
                for record in invalid[:3]
            )
        ]
    positives = [record for record in records if record["kind"].startswith("positive_")]
    if not positives:
        return records, ["no completing equal-color diagonal component"]
    negatives = [record for record in records if not record["kind"].startswith("positive_")]
    if len(negatives) > 1:
        return records, [f"expected at most one negative teaching component, got {len(negatives)}"]
    palette = {value for row in grid for value in row if value != 0}
    if len(palette) != 2:
        return records, [f"expected exactly two non-zero colors, got {sorted(palette)}"]
    return records, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _, errors = _analysis(grid)
    return errors


def observe_overrides(grid):
    records, errors = _analysis(grid)
    if errors:
        raise ValueError("; ".join(errors))
    negatives = [record["kind"] for record in records if not record["kind"].startswith("positive_")]
    if not negatives:
        profile = "canonical"
    elif negatives[0].startswith("blocked_"):
        profile = "blocked"
    elif negatives[0].startswith("axis_"):
        profile = "axis"
    elif negatives[0].startswith("mismatch_"):
        profile = "mismatch"
    else:
        raise ValueError(f"cannot infer scene_profile from {negatives[0]!r}")
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "scene_profile": profile}


def strict_canonical_like(grid):
    records, errors = _analysis(grid)
    if errors:
        return errors
    reasons = []
    if (len(grid), len(grid[0])) not in _CANONICAL_SHAPES:
        reasons.append("shape is not one of the four canonical input shapes")
    if len(records) != 2:
        reasons.append(f"canonical inputs contain exactly two motifs, got {len(records)}")
    kinds = sorted(record["kind"] for record in records)
    if kinds != ["positive_anti", "positive_main"]:
        reasons.append(f"canonical inputs require one main and one anti target, got {kinds}")
    component_colors = [set(record.get("colors", ())) for record in records]
    if len(component_colors) == 2 and component_colors[0] == component_colors[1]:
        reasons.append("canonical target motifs use distinct colors")
    return reasons


def rule_mirror(grid):
    """Independent Python transcription of the immutable Racket authority."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tl != 0 and tl == br and tr == 0 and bl == 0:
                out[r][c + 1] = tl
                out[r + 1][c] = tl
            elif tr != 0 and tr == bl and tl == 0 and br == 0:
                out[r][c] = tr
                out[r + 1][c + 1] = tr
    return out


def _rival_ignore_blockers(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tl != 0 and tl == br:
                out[r][c + 1] = tl
                out[r + 1][c] = tl
            elif tr != 0 and tr == bl:
                out[r][c] = tr
                out[r + 1][c + 1] = tr
    return out


def _rival_complete_axis_pairs(grid):
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tl != 0 and tl == tr and bl == 0 and br == 0:
                out[r + 1][c] = tl
                out[r + 1][c + 1] = tl
            elif bl != 0 and bl == br and tl == 0 and tr == 0:
                out[r][c] = bl
                out[r][c + 1] = bl
            elif tl != 0 and tl == bl and tr == 0 and br == 0:
                out[r][c + 1] = tl
                out[r + 1][c + 1] = tl
            elif tr != 0 and tr == br and tl == 0 and bl == 0:
                out[r][c] = tr
                out[r + 1][c] = tr
    return out


def _rival_ignore_endpoint_color(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tl != 0 and br != 0 and tr == 0 and bl == 0:
                out[r][c + 1] = tl
                out[r + 1][c] = tl
            elif tr != 0 and bl != 0 and tl == 0 and br == 0:
                out[r][c] = tr
                out[r + 1][c + 1] = tr
    return out


def _rival_main_only(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tl != 0 and tl == br and tr == 0 and bl == 0:
                out[r][c + 1] = tl
                out[r + 1][c] = tl
    return out


def _rival_anti_only(grid):
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            if tr != 0 and tr == bl and tl == 0 and br == 0:
                out[r][c] = tr
                out[r + 1][c + 1] = tr
    return out


def _profile_is(grid, expected):
    try:
        return observe_overrides(grid)["scene_profile"] == expected
    except (TypeError, ValueError, IndexError):
        return False


def _has_both_orientations(grid):
    records, errors = _analysis(grid)
    if errors:
        return False
    kinds = {record["kind"] for record in records}
    return "positive_main" in kinds and "positive_anti" in kinds


SEMANTIC_RIVALS = {
    "main_diagonal_only": _rival_main_only,
    "anti_diagonal_only": _rival_anti_only,
    "ignore_blocked_corners": _rival_ignore_blockers,
    "also_complete_axis_pairs": _rival_complete_axis_pairs,
    "ignore_endpoint_color_equality": _rival_ignore_endpoint_color,
}

SEMANTIC_WITNESSES = {
    "both_diagonal_orientations": _has_both_orientations,
    "blocked_corner_is_preserved": lambda grid: _profile_is(grid, "blocked"),
    "axis_pair_is_not_a_target": lambda grid: _profile_is(grid, "axis"),
    "endpoint_colors_must_match": lambda grid: _profile_is(grid, "mismatch"),
}

WITNESS_RIVALS = {
    "both_diagonal_orientations": ["main_diagonal_only", "anti_diagonal_only"],
    "blocked_corner_is_preserved": ["ignore_blocked_corners"],
    "axis_pair_is_not_a_target": ["also_complete_axis_pairs"],
    "endpoint_colors_must_match": ["ignore_endpoint_color_equality"],
}

CANONICAL_SHORTCUTS = {
    "ignore_blocked_corners": _rival_ignore_blockers,
    "also_complete_axis_pairs": _rival_complete_axis_pairs,
    "ignore_endpoint_color_equality": _rival_ignore_endpoint_color,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject a lesson only when a declared wrong rule survives its demos.

    The four-profile schedule should refute every named competitor before the
    query.  The query clause keeps this hook correct for hand-built lessons too:
    a surviving competitor is harmless when it predicts the same query answer.
    """
    errors = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(example["input"]) == example["output"] for example in demos
            )
            disagrees = competitor(query["input"]) != query["output"]
        except (KeyError, TypeError, IndexError) as exc:
            errors.append(f"{name} could not score lesson: {exc}")
            continue
        if survives and disagrees:
            errors.append(f"{name} fits every demo but predicts the query incorrectly")
    return errors
