"""Generate rooms separated by gray walls, each with one flood-fill seed.

The canonical examples are two rectangular rooms in a vertical strip.  The
lawful generalization keeps the same grammar while varying strip orientation,
room count, dimensions, room widths/heights, and seed positions.  Every room
contains exactly one nonzero/non-gray seed and at least one zero cell, so the
Racket oracle must visibly fill every room.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

TASK_ID = GENERATOR_ID = "1ec2e9f43682"
VERSION = "2.0.2"
RULE_HASH = "2944822b1e33"

SUMMARY = (
    "Gray (5) walls form 2..6 rectangular strip rooms. Each room contains "
    "exactly one colored seed and at least one zero; the rule fills that "
    "room's zeros with its seed color while preserving every wall."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and every wall is color 5",
    "the outer border is gray and full gray separators make rectangular rooms",
    "each room has exactly one non-0/non-5 seed and at least one zero cell",
    "seed colors are distinct across rooms, preventing a one-color fill shortcut",
]

LAYOUTS = ("vertical_strip", "horizontal_strip")
HELPFUL_TEXTURES = ("top_left_seeds", "varied_seeds")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "multiple_markers_per_chamber")
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALL_TEXTURES = HELPFUL_TEXTURES + DEGENERATE_TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-feasible keyed draw",
        "valid": "4..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-feasible keyed draw",
        "valid": "4..22",
    },
    "n_chambers": {
        "type": "int",
        "default": "difficulty-feasible keyed draw",
        "valid": "2..6",
    },
    "layout": {
        "type": "str",
        "default": "keyed feasible strip orientation",
        "valid": "|".join(LAYOUTS),
    },
    "texture": {
        "type": "str",
        "default": "keyed seed-position profile",
        "valid": "|".join(HELPFUL_TEXTURES),
    },
}

_BAND_OFFSET = {None: 0, "easy": 1, "medium": 2, "hard": 3}

_BANDS = {
    None: ((4, 13), (7, 18), (2, 4)),
    "easy": ((4, 8), (4, 13), (2, 3)),
    "medium": ((4, 13), (5, 18), (2, 4)),
    "hard": ((5, 22), (7, 22), (3, 6)),
}

# Exact canonical dimension/palette anchors.  The first component is the
# room-interior width sequence; colors are intentionally not hard-coded.
_CANONICAL_PROFILES = (
    (4, 7, (2, 2)),
    (4, 8, (3, 2)),
    (5, 9, (3, 3)),
)


def _coerce_grid(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return [], ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return [], ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return [], ["ragged grid"]
    coerced: list[list[int]] = []
    for r, row in enumerate(grid):
        out_row: list[int] = []
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"cell {(r, c)} is not an integer color")
                out_row.append(0)
            elif not 0 <= value <= 9:
                errors.append(f"cell {(r, c)} has ARC color {value} outside 0..9")
                out_row.append(value)
            else:
                out_row.append(value)
        coerced.append(out_row)
    return coerced, errors


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


def _scene_analysis(grid):
    grid, errors = _coerce_grid(grid)
    if errors:
        return grid, {}, errors
    h, w = len(grid), len(grid[0])
    if not 4 <= h <= 22 or not 4 <= w <= 22:
        errors.append(f"grid dimensions {h}x{w} must both be in 4..22")
        return grid, {}, errors

    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errors.append("top and bottom borders must be entirely color 5")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("left and right borders must be entirely color 5")
    if errors:
        return grid, {}, errors

    raw_components = _components_without_walls(grid)
    rooms = []
    marker_colors = []
    for cells in raw_components:
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        rectangle = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}
        if cells != rectangle:
            errors.append(
                f"room bbox {(r1, c1, r2, c2)} is not a solid rectangle"
            )
        markers = [(r, c, grid[r][c]) for r, c in sorted(cells) if grid[r][c] != 0]
        zeros = sum(grid[r][c] == 0 for r, c in cells)
        if len(markers) != 1:
            errors.append(
                f"room {(r1, c1, r2, c2)} has {len(markers)} seeds; expected exactly 1"
            )
        if zeros < 1:
            errors.append(
                f"room {(r1, c1, r2, c2)} has no zero cell for the rule to fill"
            )
        if len(markers) == 1:
            marker_colors.append(markers[0][2])
        rooms.append(
            {
                "bbox": (r1, c1, r2, c2),
                "cells": cells,
                "marker": markers[0] if len(markers) == 1 else None,
            }
        )

    if not 2 <= len(rooms) <= 6:
        errors.append(f"found {len(rooms)} rooms; expected 2..6")
    if len(marker_colors) != len(set(marker_colors)):
        errors.append("seed colors must be distinct across rooms")

    vertical = False
    horizontal = False
    if rooms:
        by_col = sorted(rooms, key=lambda room: room["bbox"][1])
        vertical = (
            all(room["bbox"][0] == 1 and room["bbox"][2] == h - 2 for room in by_col)
            and by_col[0]["bbox"][1] == 1
            and by_col[-1]["bbox"][3] == w - 2
            and all(
                right["bbox"][1] == left["bbox"][3] + 2
                for left, right in zip(by_col, by_col[1:])
            )
        )
        by_row = sorted(rooms, key=lambda room: room["bbox"][0])
        horizontal = (
            all(room["bbox"][1] == 1 and room["bbox"][3] == w - 2 for room in by_row)
            and by_row[0]["bbox"][0] == 1
            and by_row[-1]["bbox"][2] == h - 2
            and all(
                lower["bbox"][0] == upper["bbox"][2] + 2
                for upper, lower in zip(by_row, by_row[1:])
            )
        )
    if vertical == horizontal:
        errors.append("rooms must form exactly one complete vertical or horizontal strip partition")
        layout = None
        ordered = rooms
    elif vertical:
        layout = "vertical_strip"
        ordered = sorted(rooms, key=lambda room: room["bbox"][1])
    else:
        layout = "horizontal_strip"
        ordered = sorted(rooms, key=lambda room: room["bbox"][0])

    top_left = bool(ordered) and all(
        room["marker"] is not None
        and room["marker"][:2] == room["bbox"][:2]
        for room in ordered
    )
    texture = "top_left_seeds" if top_left else "varied_seeds"
    room_spans = tuple(
        (room["bbox"][3] - room["bbox"][1] + 1)
        if layout == "vertical_strip"
        else (room["bbox"][2] - room["bbox"][0] + 1)
        for room in ordered
    )
    features = {
        "grid_h": h,
        "grid_w": w,
        "n_chambers": len(rooms),
        "layout": layout,
        "texture": texture,
        "rooms": ordered,
        "room_spans": room_spans,
        "marker_colors": tuple(marker_colors),
    }
    return grid, features, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Strict recognizer for the lawful room-and-seed teaching grammar."""
    del difficulty
    _grid, features, errors = _scene_analysis(grid)
    if errors:
        return errors
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        observed = observe_overrides(grid)
        for axis in AXES:
            if axis in requested and requested[axis] is not None:
                if observed.get(axis) != requested[axis]:
                    errors.append(
                        f"{axis} requested {requested[axis]!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def observe_overrides(grid):
    """Recover every declared exact axis from the returned grid."""
    _grid, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {axis: features[axis] for axis in AXES}


def rule_mirror(grid):
    """Independent Python mirror used only for focused tests."""
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid room lesson: " + "; ".join(errors))
    output = deepcopy(coerced)
    for room in features["rooms"]:
        color = room["marker"][2]
        for r, c in room["cells"]:
            if output[r][c] == 0:
                output[r][c] = color
    return output


def canonical_profile_index(grid):
    """Return a canonical structural-profile index, ignoring seed colors."""
    _grid, features, errors = _scene_analysis(grid)
    if errors or features["layout"] != "vertical_strip" or features["texture"] != "top_left_seeds":
        return None
    signature = (features["grid_h"], features["grid_w"], features["room_spans"])
    try:
        return _CANONICAL_PROFILES.index(signature)
    except ValueError:
        return None


def is_canonical_profile(grid):
    return canonical_profile_index(grid) is not None


def _positive_partition(total: int, parts: int, rng) -> list[int]:
    """Random positive composition of total into parts."""
    if total < parts:
        raise ValueError(f"cannot partition {total} cells into {parts} positive rooms")
    if parts == 1:
        return [total]
    cuts = sorted(rng.sample(range(1, total), parts - 1))
    points = [0, *cuts, total]
    return [b - a for a, b in zip(points, points[1:])]


def _candidate_configurations(difficulty, overrides):
    if difficulty not in _BANDS:
        raise ValueError(f"difficulty must be easy, medium, hard, or None; got {difficulty!r}")
    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _BANDS[difficulty]

    def int_values(name, lo, hi, global_lo, global_hi):
        if name not in overrides or overrides[name] is None:
            return range(lo, hi + 1)
        value = int(overrides[name])
        if not global_lo <= value <= global_hi:
            raise ValueError(f"{name} override {value} outside [{global_lo}, {global_hi}]")
        return (value,)

    heights = int_values("grid_h", h_lo, h_hi, 4, 22)
    widths = int_values("grid_w", w_lo, w_hi, 4, 22)
    counts = int_values("n_chambers", n_lo, n_hi, 2, 6)
    if overrides.get("layout") is None:
        layouts = LAYOUTS
    else:
        layout = str(overrides["layout"])
        if layout not in LAYOUTS:
            raise ValueError(f"layout override {layout!r} not in {LAYOUTS!r}")
        layouts = (layout,)

    candidates = []
    for layout in layouts:
        for n in counts:
            for h in heights:
                for w in widths:
                    if layout == "vertical_strip" and h >= 4 and w >= 2 * n + 1:
                        candidates.append((h, w, n, layout))
                    if layout == "horizontal_strip" and w >= 4 and h >= 2 * n + 1:
                        candidates.append((h, w, n, layout))
    if not candidates:
        shown = {key: overrides.get(key) for key in ("grid_h", "grid_w", "n_chambers", "layout")}
        raise ValueError(f"incompatible room-layout overrides: {shown}")
    return candidates


def _draw_degenerate(texture):
    h, w = 4, 7
    grid = full_grid(h, w, 0)
    if texture == "no_walls":
        grid[1][1] = 2
        grid[2][5] = 3
        return grid
    fill_box(grid, 0, 0, 0, w - 1, 5)
    fill_box(grid, h - 1, 0, h - 1, w - 1, 5)
    fill_box(grid, 0, 0, h - 1, 0, 5)
    fill_box(grid, 0, 3, h - 1, 3, 5)
    fill_box(grid, 0, w - 1, h - 1, w - 1, 5)
    if texture == "multiple_markers_per_chamber":
        grid[1][1] = 2
        grid[2][2] = 4
        grid[1][4] = 3
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
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

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        if len(overrides) != 1:
            raise ValueError("degenerate texture overrides cannot be combined with semantic axes")
        ctx.draw_choice("texture", DEGENERATE_TEXTURES)
        return _draw_degenerate(requested_texture)
    if requested_texture is not None and requested_texture not in HELPFUL_TEXTURES:
        raise ValueError(f"texture override {requested_texture!r} not in {_ALL_TEXTURES!r}")

    canonical_schedule = not overrides and sample_index % 10 == 0
    if canonical_schedule:
        profile_rng = ctx.draw_rng(f"canonical_profile:{difficulty}")
        h, w, spans = profile_rng.choice(_CANONICAL_PROFILES)
        n_chambers = 2
        layout = "vertical_strip"
        texture = "top_left_seeds"
    else:
        candidates = _candidate_configurations(difficulty, overrides)
        h, w, n_chambers, layout = ctx.draw_rng(f"configuration:{difficulty}").choice(candidates)
        spans = None
        if requested_texture is not None:
            texture = requested_texture
        else:
            texture = ctx.draw_rng(f"texture_prior:{difficulty}").choice(
                ("top_left_seeds", "varied_seeds", "varied_seeds")
            )

    # Pin every exact axis through GenCtx after joint feasibility is resolved.
    h = ctx.draw_int("grid_h", h, h)
    w = ctx.draw_int("grid_w", w, w)
    n_chambers = ctx.draw_int("n_chambers", n_chambers, n_chambers)
    layout = ctx.draw_choice("layout", (layout,))
    texture = ctx.draw_choice("texture", (texture,))

    grid = full_grid(h, w, 0)
    fill_box(grid, 0, 0, 0, w - 1, 5)
    fill_box(grid, h - 1, 0, h - 1, w - 1, 5)
    fill_box(grid, 0, 0, h - 1, 0, 5)
    fill_box(grid, 0, w - 1, h - 1, w - 1, 5)

    layout_rng = ctx.draw_rng(f"room_partition:{difficulty}")
    rooms = []
    if layout == "vertical_strip":
        if spans is None:
            spans = tuple(_positive_partition(w - (n_chambers + 1), n_chambers, layout_rng))
        cursor = 1
        for index, span in enumerate(spans):
            rooms.append((1, cursor, h - 2, cursor + span - 1))
            cursor += span
            if index < n_chambers - 1:
                fill_box(grid, 0, cursor, h - 1, cursor, 5)
                cursor += 1
    else:
        spans = tuple(_positive_partition(h - (n_chambers + 1), n_chambers, layout_rng))
        cursor = 1
        for index, span in enumerate(spans):
            rooms.append((cursor, 1, cursor + span - 1, w - 2))
            cursor += span
            if index < n_chambers - 1:
                fill_box(grid, cursor, 0, cursor, w - 1, 5)
                cursor += 1

    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    if canonical_schedule:
        first_color = (1, 2, 3, 4)[_BAND_OFFSET[difficulty]]
        remaining = [color for color in palette if color != first_color]
        second_color = remaining[(seed + sample_index // 10) % len(remaining)]
        palette = [first_color, second_color] + [
            color for color in remaining if color != second_color
        ]
    else:
        color_rng = ctx.draw_rng(f"seed_colors:{difficulty}")
        color_rng.shuffle(palette)
        offset = _BAND_OFFSET[difficulty] % len(palette)
        palette = palette[offset:] + palette[:offset]
    seed_rng = ctx.draw_rng(f"seed_positions:{difficulty}")
    for index, ((r1, c1, r2, c2), color) in enumerate(zip(rooms, palette)):
        cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        if texture == "top_left_seeds":
            r, c = r1, c1
        elif index == 0:
            non_top_left = [cell for cell in cells if cell != (r1, c1)]
            r, c = seed_rng.choice(non_top_left)
        else:
            r, c = seed_rng.choice(cells)
        grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generator constructed an invalid scene: " + "; ".join(errors))
    return grid
