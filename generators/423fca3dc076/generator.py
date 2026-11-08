"""Generator for ARC task 423fca3dc076 — flood each seeded gray-walled room.

Canonical rule: color 5 is an impassable wall.  Every nonzero/non-5 seed
floods the entire 4-connected non-wall chamber that contains it; a chamber
without a seed remains zero.  The canonical set contains vertical, horizontal,
cross, and right-hand T partitions, so the teaching distribution deliberately
covers all four rather than collapsing the task to a two-room vertical strip.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

TASK_ID = GENERATOR_ID = "423fca3dc076"
VERSION = "2.0.0"
RULE_HASH = "675cabbc5188"

SUMMARY = (
    "Gray (5) walls partition the bordered grid into 2..4 rectangular rooms. "
    "Each seeded room contains one distinct colored seed; flood that whole room "
    "with its seed color without crossing gray walls, while unseeded rooms stay zero."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is 0 and every wall is color 5",
    "the outer border is entirely gray and internal gray walls form a vertical, horizontal, cross, or right-T partition",
    "each chamber contains at most one non-0/non-5 seed and every seeded chamber also contains a zero cell",
    "at least two chambers are seeded and seed colors are distinct across chambers",
    "unseeded chambers contain only zero cells and must remain zero under the rule",
]

LAYOUTS = ("vertical_2", "horizontal_2", "cross_4", "t_right_3")
HELPFUL_TEXTURES = ("top_left_seeds", "off_corner_seeds")
DEGENERATE_TEXTURES = ("no_walls", "no_seeds", "two_seeds_one_room", "duplicate_seed_colors")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "keyed 8..10 with canonical anchors", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "keyed 9..12 with canonical anchors", "valid": "9..12"},
    "layout": {"type": "str", "default": "sample-index schedule", "valid": "|".join(LAYOUTS)},
    "texture": {"type": "str", "default": "alternating keyed seed placement", "valid": "|".join(HELPFUL_TEXTURES)},
}

_CANONICAL_SHAPES = {
    "vertical_2": (9, 9),
    "horizontal_2": (8, 10),
    "cross_4": (9, 11),
    "t_right_3": (8, 11),
}
_SEED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


def _coerce_grid(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return [], ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return [], ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return [], ["grid is ragged"]
    out: list[list[int]] = []
    for r, row in enumerate(grid):
        out_row = []
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"cell {(r, c)} is not an integer ARC color")
                out_row.append(0)
            else:
                out_row.append(value)
                if not 0 <= value <= 9:
                    errors.append(f"cell {(r, c)} has ARC color {value} outside 0..9")
        out.append(out_row)
    return out, errors


def _components_without_walls(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 5}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        components.append(cells)
    return components


def _classify_wall_layout(grid):
    """Return the canonical partition family, or None for a malformed wall mask."""
    h, w = len(grid), len(grid[0])
    internal_walls = {(r, c) for r in range(1, h - 1) for c in range(1, w - 1) if grid[r][c] == 5}
    full_cols = [c for c in range(1, w - 1) if all(grid[r][c] == 5 for r in range(h))]
    full_rows = [r for r in range(1, h - 1) if all(grid[r][c] == 5 for c in range(w))]

    if len(full_cols) == 1 and not full_rows:
        vc = full_cols[0]
        expected = {(r, vc) for r in range(1, h - 1)}
        if internal_walls == expected:
            return "vertical_2"
        # Canonical right-hand T: a full vertical separator plus one horizontal
        # arm extending from the separator through the right border.
        extra = internal_walls - expected
        rows = sorted({r for r, _ in extra})
        if len(rows) == 1:
            hr = rows[0]
            expected |= {(hr, c) for c in range(vc + 1, w - 1)}
            if internal_walls == expected:
                return "t_right_3"
        return None

    if len(full_rows) == 1 and not full_cols:
        hr = full_rows[0]
        expected = {(hr, c) for c in range(1, w - 1)}
        return "horizontal_2" if internal_walls == expected else None

    if len(full_cols) == 1 and len(full_rows) == 1:
        vc, hr = full_cols[0], full_rows[0]
        expected = (
            {(r, vc) for r in range(1, h - 1)}
            | {(hr, c) for c in range(1, w - 1)}
        )
        return "cross_4" if internal_walls == expected else None
    return None


def _scene_analysis(grid):
    grid, errors = _coerce_grid(grid)
    if errors:
        return grid, {}, errors
    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 14 or not 7 <= w <= 14:
        errors.append(f"grid dimensions {h}x{w} must both be in 7..14")
        return grid, {}, errors
    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errors.append("top and bottom borders must be entirely color 5")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("left and right borders must be entirely color 5")
    if errors:
        return grid, {}, errors

    layout = _classify_wall_layout(grid)
    if layout is None:
        errors.append("internal gray walls are not one canonical vertical/horizontal/cross/right-T partition")

    rooms = []
    seed_colors = []
    for cells in sorted(_components_without_walls(grid), key=lambda cs: min(cs)):
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        rectangle = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if cells != rectangle:
            errors.append(f"chamber bbox {(r1, c1, r2, c2)} is not a solid rectangle")
        seeds = [(r, c, grid[r][c]) for r, c in sorted(cells) if grid[r][c] not in (0, 5)]
        if len(seeds) > 1:
            errors.append(f"chamber {(r1, c1, r2, c2)} has {len(seeds)} seeds; expected at most one")
        if seeds:
            zeros = sum(grid[r][c] == 0 for r, c in cells)
            if zeros == 0:
                errors.append(f"seeded chamber {(r1, c1, r2, c2)} has no zero cell to flood")
            seed_colors.append(seeds[0][2])
        rooms.append({"bbox": (r1, c1, r2, c2), "cells": cells, "seed": seeds[0] if seeds else None})

    expected_rooms = {"vertical_2": 2, "horizontal_2": 2, "cross_4": 4, "t_right_3": 3}.get(layout)
    if expected_rooms is not None and len(rooms) != expected_rooms:
        errors.append(f"layout {layout} produced {len(rooms)} chambers; expected {expected_rooms}")
    if not 2 <= len(rooms) <= 4:
        errors.append(f"found {len(rooms)} chambers; expected 2..4")
    if len(seed_colors) < 2:
        errors.append(f"found {len(seed_colors)} seeded chambers; expected at least 2")
    if len(seed_colors) != len(set(seed_colors)):
        errors.append("seed colors must be distinct across chambers")

    seeded = [room for room in rooms if room["seed"] is not None]
    top_left = bool(seeded) and all(room["seed"][:2] == room["bbox"][:2] for room in seeded)
    off_corner = bool(seeded) and all(room["seed"][:2] != room["bbox"][:2] for room in seeded)
    texture = "top_left_seeds" if top_left else "off_corner_seeds" if off_corner else "mixed_seed_positions"
    features = {
        "grid_h": h,
        "grid_w": w,
        "layout": layout,
        "texture": texture,
        "rooms": rooms,
        "seed_colors": tuple(seed_colors),
        "seeded_count": len(seed_colors),
        "unseeded_count": len(rooms) - len(seed_colors),
    }
    return grid, features, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural recognizer for the task's wall/chamber input grammar."""
    del difficulty
    _grid, _features, errors = _scene_analysis(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the four canonical partition families at canonical scale."""
    _grid, features, errors = _scene_analysis(grid)
    if errors:
        return errors
    reasons = []
    if not 8 <= features["grid_h"] <= 10 or not 9 <= features["grid_w"] <= 12:
        reasons.append("grid lies outside the canonical-scale 8..10 by 9..12 envelope")
    if features["layout"] not in LAYOUTS:
        reasons.append("partition family is not represented by canonical examples")
    if features["seeded_count"] < 2:
        reasons.append("canonical-like scenes need at least two distinct seeded chambers")
    return reasons


def observe_overrides(grid):
    """Recover every declared exact generator axis from a generated grid."""
    _grid, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    if features["texture"] not in HELPFUL_TEXTURES:
        raise ValueError(f"generated texture is not exact-observable: {features['texture']!r}")
    return {axis: features[axis] for axis in AXES}


def rule_mirror(grid):
    """Independent Python mirror used for semantic tests; Racket remains authority."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid room scene: " + "; ".join(errors))
    out = deepcopy(coerced)
    for room in features["rooms"]:
        seed = room["seed"]
        if seed is None:
            continue
        color = seed[2]
        for r, c in room["cells"]:
            if out[r][c] == 0:
                out[r][c] = color
    return out


def _draw_degenerate(name):
    h, w = 9, 11
    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 5
    if name == "no_walls":
        grid[2][2] = 2
        grid[6][8] = 3
        return grid
    vc = 5
    for r in range(h):
        grid[r][vc] = 5
    if name == "no_seeds":
        return grid
    if name == "two_seeds_one_room":
        grid[2][2] = 2
        grid[5][3] = 3
        grid[3][7] = 4
        return grid
    if name == "duplicate_seed_colors":
        grid[2][2] = 4
        grid[5][7] = 4
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def _pin_int(ctx, name, default, lo, hi, overrides):
    requested = overrides.get(name)
    value = default if requested is None else int(requested)
    if not lo <= value <= hi:
        raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    return ctx.draw_int(name, value, value)


def _pin_choice(ctx, name, default, options, overrides):
    requested = overrides.get(name)
    value = default if requested is None else requested
    if value not in options:
        raise ValueError(f"{name} override {value!r} not in {options!r}")
    return ctx.draw_choice(name, (value,))


def _make_walls(grid, layout, rng):
    h, w = len(grid), len(grid[0])
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 5

    vc = rng.randint(3, w - 4)
    hr = rng.randint(3, h - 4)
    if layout in ("vertical_2", "cross_4", "t_right_3"):
        for r in range(h):
            grid[r][vc] = 5
    if layout in ("horizontal_2", "cross_4"):
        for c in range(w):
            grid[hr][c] = 5
    elif layout == "t_right_3":
        for c in range(vc, w):
            grid[hr][c] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        if len(overrides) != 1:
            raise ValueError("degenerate texture fixtures cannot be combined with semantic overrides")
        ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
        ctx.draw_choice("texture", (requested_texture,))
        return _draw_degenerate(requested_texture)

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    scheduled_layout = LAYOUTS[sample_index % len(LAYOUTS)]
    layout = _pin_choice(ctx, "layout", scheduled_layout, LAYOUTS, overrides)
    scheduled_texture = HELPFUL_TEXTURES[sample_index % len(HELPFUL_TEXTURES)]
    texture = _pin_choice(ctx, "texture", scheduled_texture, HELPFUL_TEXTURES, overrides)

    # Half the ordinary stream sits exactly on a canonical (h,w,palette-size)
    # profile; the other half broadens dimensions while keeping the same rule.
    if sample_index % 8 < 4:
        default_h, default_w = _CANONICAL_SHAPES[layout]
    else:
        size_rng = ctx.draw_rng(f"size_prior:{difficulty}")
        if difficulty == "easy":
            default_h = size_rng.choice((8, 9))
            default_w = size_rng.choice((9, 10, 11))
        elif difficulty == "hard":
            default_h = size_rng.choice((9, 10))
            default_w = size_rng.choice((10, 11, 12))
        else:
            default_h = size_rng.randint(8, 10)
            default_w = size_rng.randint(9, 12)
    h = _pin_int(ctx, "grid_h", default_h, 8, 10, overrides)
    w = _pin_int(ctx, "grid_w", default_w, 9, 12, overrides)

    grid = full_grid(h, w, 0)
    _make_walls(grid, layout, ctx.draw_rng(f"wall_positions:{difficulty}"))
    _coerced, features, wall_errors = _scene_analysis(grid)
    # The seed-count checks in _scene_analysis are expected to fail before seeds
    # are placed; only the wall/room geometry is needed here.
    structural_errors = [e for e in wall_errors if "seeded chambers" not in e]
    if structural_errors:
        raise AssertionError("wall construction failed: " + "; ".join(structural_errors))

    rooms = features["rooms"]
    seeded_rooms = list(rooms)
    if layout == "cross_4":
        empty_index = ctx.draw_rng(f"unseeded_room:{difficulty}").randrange(len(rooms))
        seeded_rooms = [room for i, room in enumerate(rooms) if i != empty_index]

    colors = list(_SEED_COLORS)
    color_rng = ctx.draw_rng(f"seed_colors:{difficulty}")
    color_rng.shuffle(colors)
    position_rng = ctx.draw_rng(f"seed_positions:{difficulty}")
    for room, color in zip(seeded_rooms, colors):
        r1, c1, r2, c2 = room["bbox"]
        cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        if texture == "top_left_seeds":
            r, c = r1, c1
        else:
            choices = [cell for cell in cells if cell != (r1, c1)]
            r, c = position_rng.choice(choices)
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, requested in overrides.items():
        if requested is not None and observed[axis] != requested:
            raise AssertionError(f"{axis} override {requested!r} observed as {observed[axis]!r}")
    return grid


def _copy_grid(grid):
    return [list(row) for row in grid]


def _valid_features(grid):
    _grid, features, errors = _scene_analysis(grid)
    return None if errors else features


def _rival_global_first_seed(grid):
    features = _valid_features(grid)
    if not features or not features["seed_colors"]:
        return _copy_grid(grid)
    color = features["seed_colors"][0]
    return [[color if value == 0 else value for value in row] for row in grid]


def _rival_horizontal_only(grid):
    features = _valid_features(grid)
    return rule_mirror(grid) if features and features["layout"] == "horizontal_2" else _copy_grid(grid)


def _rival_vertical_only(grid):
    features = _valid_features(grid)
    return rule_mirror(grid) if features and features["layout"] == "vertical_2" else _copy_grid(grid)


def _rival_strip_only(grid):
    features = _valid_features(grid)
    return rule_mirror(grid) if features and features["layout"] in ("vertical_2", "horizontal_2") else _copy_grid(grid)


def _rival_two_chambers_only(grid):
    features = _valid_features(grid)
    if not features:
        return _copy_grid(grid)
    out = _copy_grid(grid)
    filled = 0
    for room in features["rooms"]:
        seed = room["seed"]
        if seed is None or filled >= 2:
            continue
        for r, c in room["cells"]:
            if out[r][c] == 0:
                out[r][c] = seed[2]
        filled += 1
    return out


def _rival_fill_empty_chambers(grid):
    features = _valid_features(grid)
    if not features:
        return _copy_grid(grid)
    out = rule_mirror(grid)
    fallback = features["seed_colors"][0]
    for room in features["rooms"]:
        if room["seed"] is None:
            for r, c in room["cells"]:
                if out[r][c] == 0:
                    out[r][c] = fallback
    return out


def _rival_top_left_seed_assumption(grid):
    features = _valid_features(grid)
    if not features:
        return _copy_grid(grid)
    out = _copy_grid(grid)
    for room in features["rooms"]:
        r1, c1, _r2, _c2 = room["bbox"]
        color = grid[r1][c1]
        if color in (0, 5):
            continue
        for r, c in room["cells"]:
            if out[r][c] == 0:
                out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "global_first_seed": _rival_global_first_seed,
    "horizontal_only": _rival_horizontal_only,
    "vertical_only": _rival_vertical_only,
    "strip_only": _rival_strip_only,
    "two_chambers_only": _rival_two_chambers_only,
    "fill_empty_chambers": _rival_fill_empty_chambers,
    "top_left_seed_assumption": _rival_top_left_seed_assumption,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_layout(name):
    return lambda grid: bool((features := _valid_features(grid)) and features["layout"] == name)


def _witness_junction(grid):
    features = _valid_features(grid)
    return bool(features and features["layout"] in ("cross_4", "t_right_3"))


def _witness_three_seeds(grid):
    features = _valid_features(grid)
    return bool(features and features["seeded_count"] >= 3)


def _witness_unseeded(grid):
    features = _valid_features(grid)
    return bool(features and features["unseeded_count"] >= 1)


def _witness_off_corner(grid):
    features = _valid_features(grid)
    if not features:
        return False
    return any(room["seed"] is not None and room["seed"][:2] != room["bbox"][:2] for room in features["rooms"])


def _witness_multiple_colors(grid):
    features = _valid_features(grid)
    return bool(features and len(set(features["seed_colors"])) >= 2)


SEMANTIC_WITNESSES = {
    "vertical_partition": _witness_layout("vertical_2"),
    "horizontal_partition": _witness_layout("horizontal_2"),
    "junction_partition": _witness_junction,
    "three_seeded_chambers": _witness_three_seeds,
    "unseeded_chamber": _witness_unseeded,
    "off_corner_seed": _witness_off_corner,
    "multiple_seed_colors": _witness_multiple_colors,
}
WITNESS_RIVALS = {
    "vertical_partition": ["horizontal_only"],
    "horizontal_partition": ["vertical_only"],
    "junction_partition": ["strip_only"],
    "three_seeded_chambers": ["two_chambers_only"],
    "unseeded_chamber": ["fill_empty_chambers"],
    "off_corner_seed": ["top_left_seed_assumption"],
    "multiple_seed_colors": ["global_first_seed"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Every four-demo window must eliminate the named plausible shortcuts."""
    reasons: list[str] = []
    episodes = [(f"demo {i}", d) for i, d in enumerate(demos)] + [("query", query)]
    for label, episode in episodes:
        if not isinstance(episode, dict) or "input" not in episode:
            reasons.append(f"{label}: malformed episode")
            continue
        errors = self_check(episode["input"])
        if errors:
            reasons.append(f"{label}: malformed input: {'; '.join(errors)}")
            continue
        expected = rule_mirror(episode["input"])
        if episode.get("output") is not None and episode["output"] != expected:
            reasons.append(f"{label}: output disagrees with the seeded-room flood rule")
    if reasons:
        return reasons

    required = {
        "vertical partition": SEMANTIC_WITNESSES["vertical_partition"],
        "horizontal partition": SEMANTIC_WITNESSES["horizontal_partition"],
        "junction partition": SEMANTIC_WITNESSES["junction_partition"],
        "unseeded chamber": SEMANTIC_WITNESSES["unseeded_chamber"],
        "off-corner seed": SEMANTIC_WITNESSES["off_corner_seed"],
        "third seeded chamber": SEMANTIC_WITNESSES["three_seeded_chambers"],
    }
    for name, predicate in required.items():
        if not any(predicate(demo["input"]) for demo in demos):
            reasons.append(f"demos lack a {name} control")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons
