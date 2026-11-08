"""Generator for ARC task 2f0c5170.

The input contains two color-8-separated rectangular panels. One source panel
contains a connected yellow shape around a colored marker; the other target
panel contains only a marker of the same color. The answer is the target-panel
crop, with the complete source shape translated so its marker lands on the
target marker.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5a053ea7753b"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"  # four-way canonical layout/size coverage + connected shapes
RULE_HASH = "6b3acc6fab9f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A color-8 background contains exactly two solid rectangular non-8 "
    "panels, separated horizontally or vertically. The SOURCE panel contains "
    "one non-{0,4,8} marker embedded in a connected yellow shape; the TARGET "
    "panel contains a second marker of the same color and no yellow. Crop the "
    "target panel and translate every yellow source offset so the source "
    "marker aligns with the target marker."
)

INVARIANTS = [
    "exactly two rectangular non-8 panels are separated by color 8",
    "the source may be above, below, left, or right of the target",
    "the two panels contain exactly one same-colored marker each",
    "all yellow cells are in exactly one source panel and connect through its marker",
    "the yellow-plus-marker shape has canonical Chebyshev radius 2",
    "the translated yellow offsets fit inside the target panel",
    "the output is the target-panel crop, not the full input grid or source crop",
]

PANEL_LAYOUTS = (
    "source_above",
    "source_right",
    "source_below",
    "source_left",
)
_PROFILE_LAYOUT = PANEL_LAYOUTS
_PROFILE_AREA_RELATION = (
    "source_smaller",
    "source_larger",
    "source_larger",
    "source_smaller",
)

AXES = {
    "grid_h": {"type": "int", "default": "rng 19..23", "valid": "19..23"},
    "grid_w": {"type": "int", "default": "rng 18..23", "valid": "18..23"},
    "source_h": {
        "type": "int",
        "default": "scheduled canonical-anchored rng 4..7",
        "valid": "4..7",
    },
    "source_w": {
        "type": "int",
        "default": "scheduled canonical-anchored rng 4..7",
        "valid": "4..7",
    },
    "target_h": {
        "type": "int",
        "default": "scheduled canonical-anchored rng 5..9",
        "valid": "5..9",
    },
    "target_w": {
        "type": "int",
        "default": "scheduled canonical-anchored rng 5..9",
        "valid": "5..9",
    },
    "shape_size": {
        "type": "int",
        "default": "difficulty-aware rng 7..12; scheduled >7 controls",
        "valid": "7..12",
    },
    "dot_color": {
        "type": "color",
        "default": "rng 1|2|3|5|6|7|9",
        "valid": "1|2|3|5|6|7|9",
    },
    "panel_layout": {
        "type": "str",
        "default": "four-slot schedule",
        "valid": "|".join(PANEL_LAYOUTS),
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """ABBA schedule over reading order, orientation, and size relation.

    Every three-demonstration sliding window contains both horizontal and
    vertical scenes, both first/second source positions, and both source-smaller
    and source-larger controls.
    """
    del seed, difficulty
    return int(sample_index) % 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 19, 23)
    w = ctx.draw_int("grid_w", 18, 23)
    profile = schedule_profile(seed, sample_index, difficulty)
    layout = _draw_layout(ctx, profile, overrides)
    source_h, source_w, target_h, target_w = _draw_panel_dimensions(
        ctx, profile, overrides
    )
    shape_size = _draw_shape_size(ctx, profile, overrides)
    dot_color = ctx.draw_color("dot_color", exclude={0, 4, 8})

    source_r, source_c, target_r, target_c = _place_panels(
        ctx.draw_rng("panel_placement"),
        h,
        w,
        source_h,
        source_w,
        target_h,
        target_w,
        layout,
    )
    source_rel, target_rel, offsets = _draw_shape_geometry(
        ctx.draw_rng("shape_geometry"),
        source_h,
        source_w,
        target_h,
        target_w,
        shape_size,
        profile,
    )

    grid = full_grid(h, w, 8)
    _clear_rect(grid, source_r, source_c, source_h, source_w)
    _clear_rect(grid, target_r, target_c, target_h, target_w)

    sr, sc = source_r + source_rel[0], source_c + source_rel[1]
    tr, tc = target_r + target_rel[0], target_c + target_rel[1]
    grid[sr][sc] = dot_color
    grid[tr][tc] = dot_color
    for dr, dc in offsets:
        grid[sr + dr][sc + dc] = 4

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # fail closed; a malformed data row is worse than a loud crash
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def _draw_layout(ctx, profile, overrides):
    scheduled = _PROFILE_LAYOUT[profile]
    if overrides.get("panel_layout") is not None:
        return str(ctx.draw_choice("panel_layout", PANEL_LAYOUTS))
    return str(ctx.draw_choice("panel_layout", (scheduled,)))


def _draw_panel_dimensions(ctx, profile, overrides):
    explicit = any(
        overrides.get(name) is not None
        for name in ("source_h", "source_w", "target_h", "target_w")
    )
    if explicit:
        return (
            ctx.draw_int("source_h", 4, 7),
            ctx.draw_int("source_w", 4, 7),
            ctx.draw_int("target_h", 5, 9),
            ctx.draw_int("target_w", 5, 9),
        )

    relation = _PROFILE_AREA_RELATION[profile]
    if relation == "source_smaller":
        # The asymmetric ranges avoid a false height/width alias while keeping
        # max source area 6*7 below min target area 7*7.
        if profile == 0:
            source_h = ctx.draw_int("source_h", 4, 6)
            source_w = ctx.draw_int("source_w", 5, 7)
        else:
            source_h = ctx.draw_int("source_h", 5, 7)
            source_w = ctx.draw_int("source_w", 4, 6)
        return (
            source_h,
            source_w,
            ctx.draw_int("target_h", 7, 9),
            ctx.draw_int("target_w", 7, 9),
        )
    # The two source-larger profiles swap the fixed long side; min source
    # area 6*7 remains above max target area 6*6.
    if profile == 1:
        source_h = ctx.draw_int("source_h", 6, 7)
        source_w = ctx.draw_int("source_w", 7, 7)
    else:
        source_h = ctx.draw_int("source_h", 7, 7)
        source_w = ctx.draw_int("source_w", 6, 7)
    return (
        source_h,
        source_w,
        ctx.draw_int("target_h", 5, 6),
        ctx.draw_int("target_w", 5, 6),
    )


def _draw_shape_size(ctx, profile, overrides):
    if overrides.get("shape_size") is not None:
        return ctx.draw_int_diff("shape_size", 7, 12)
    # Profiles 1 and 2 occur in every three-slot window, so a fixed-seven
    # shortcut is always contradicted by at least one demonstration.
    lower = 8 if profile in (1, 2) else 7
    return ctx.draw_int_diff("shape_size", lower, 12)


def _place_panels(
    rng,
    h,
    w,
    source_h,
    source_w,
    target_h,
    target_w,
    layout,
):
    if layout in {"source_above", "source_below"}:
        combined = source_h + 1 + target_h
        if combined > h:
            raise ValueError("panel heights do not fit grid_h")
        top_r = rng.randint(0, h - combined)
        if layout == "source_above":
            source_r = top_r
            target_r = top_r + source_h + 1
        else:
            target_r = top_r
            source_r = top_r + target_h + 1
        source_c, target_c = rng.choice(
            _overlapping_starts(w, source_w, target_w)
        )
        return source_r, source_c, target_r, target_c

    combined = source_w + 1 + target_w
    if combined > w:
        raise ValueError("panel widths do not fit grid_w")
    left_c = rng.randint(0, w - combined)
    if layout == "source_left":
        source_c = left_c
        target_c = left_c + source_w + 1
    elif layout == "source_right":
        target_c = left_c
        source_c = left_c + target_w + 1
    else:
        raise ValueError(f"unsupported panel_layout: {layout!r}")
    source_r, target_r = rng.choice(_overlapping_starts(h, source_h, target_h))
    return source_r, source_c, target_r, target_c


def _overlapping_starts(extent, first_size, second_size):
    pairs = [
        (first, second)
        for first in range(extent - first_size + 1)
        for second in range(extent - second_size + 1)
        if max(first, second)
        <= min(first + first_size - 1, second + second_size - 1)
    ]
    if not pairs:
        raise ValueError("panel intervals cannot overlap in the orthogonal axis")
    return pairs


def _draw_shape_geometry(
    rng,
    source_h,
    source_w,
    target_h,
    target_w,
    shape_size,
    profile,
):
    marker_candidates = []
    for r in range(source_h):
        for c in range(source_w):
            allowed = _allowed_offsets(source_h, source_w, (r, c))
            if len(allowed) >= shape_size and any(
                max(abs(dr), abs(dc)) == 2 for dr, dc in allowed
            ):
                marker_candidates.append((r, c))
    if not marker_candidates:
        raise ValueError("source panel cannot host the requested radius-2 shape")

    preferred_corners = (
        (0, 0),
        (0, target_w - 1),
        (target_h - 1, target_w - 1),
        (target_h - 1, 0),
    )
    preferred_corner = preferred_corners[profile]

    for _ in range(256):
        source_rel = rng.choice(marker_candidates)
        allowed = _allowed_offsets(source_h, source_w, source_rel)
        outer = [offset for offset in allowed if max(map(abs, offset)) == 2]
        goal = rng.choice(outer)
        chosen = set(_manhattan_path(goal, rng))

        while len(chosen) < shape_size:
            connected = chosen | {(0, 0)}
            frontier = [
                offset
                for offset in allowed - chosen
                if any(
                    (offset[0] + dr, offset[1] + dc) in connected
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
            ]
            if not frontier:
                break
            chosen.add(rng.choice(frontier))
        if len(chosen) != shape_size:
            continue

        offsets = sorted(chosen)
        target_positions = _valid_target_positions(
            target_h, target_w, offsets, exclude_center=True
        )
        if not target_positions:
            continue
        best_distance = min(
            abs(r - preferred_corner[0]) + abs(c - preferred_corner[1])
            for r, c in target_positions
        )
        best = [
            pos
            for pos in target_positions
            if abs(pos[0] - preferred_corner[0])
            + abs(pos[1] - preferred_corner[1])
            == best_distance
        ]
        return source_rel, rng.choice(best), offsets

    raise RuntimeError("could not mint a connected off-center radius-2 shape")


def _allowed_offsets(height, width, marker):
    mr, mc = marker
    return {
        (r - mr, c - mc)
        for r in range(height)
        for c in range(width)
        if (r, c) != marker and max(abs(r - mr), abs(c - mc)) <= 2
    }


def _manhattan_path(goal, rng):
    current = (0, 0)
    path = []
    while current != goal:
        options = []
        if current[0] != goal[0]:
            options.append(
                (current[0] + (1 if goal[0] > current[0] else -1), current[1])
            )
        if current[1] != goal[1]:
            options.append(
                (current[0], current[1] + (1 if goal[1] > current[1] else -1))
            )
        current = rng.choice(options)
        path.append(current)
    return path


def _valid_target_positions(height, width, offsets, *, exclude_center):
    center = (height // 2, width // 2)
    return [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (not exclude_center or (r, c) != center)
        and all(0 <= r + dr < height and 0 <= c + dc < width for dr, dc in offsets)
    ]


def _clear_rect(grid, r0, c0, height, width):
    for r in range(r0, r0 + height):
        for c in range(c0, c0 + width):
            grid[r][c] = 0


def _rectangular_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    if len(grid) > 30 or width > 30:
        raise ValueError(f"grid too large: {len(grid)}x{width}")
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid contains a non-ARC color")
    return len(grid), width


def _components_not_8(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 8
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _panel_record(grid, cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    area = (r1 - r0 + 1) * (c1 - c0 + 1)
    if len(cells) != area or any(
        grid[r][c] == 8
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    ):
        raise ValueError("a non-8 component is not a filled rectangular panel")
    dots = [
        (r, c, grid[r][c])
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if grid[r][c] not in (0, 4, 8)
    ]
    yellows = [
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if grid[r][c] == 4
    ]
    return {
        "r0": r0,
        "r1": r1,
        "c0": c0,
        "c1": c1,
        "h": r1 - r0 + 1,
        "w": c1 - c0 + 1,
        "dots": dots,
        "yellows": yellows,
    }


def _shape_connected(offsets):
    remaining = set(offsets)
    remaining.add((0, 0))
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for neighbor in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _panel_layout(source, target):
    if source["r1"] < target["r0"]:
        return "source_above"
    if target["r1"] < source["r0"]:
        return "source_below"
    if source["c1"] < target["c0"]:
        return "source_left"
    if target["c1"] < source["c0"]:
        return "source_right"
    raise ValueError("source and target panels overlap in both axes")


def _analyze(grid):
    h, w = _rectangular_grid(grid)
    values = {value for row in grid for value in row}
    dots = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 4, 8)
    ]
    if len(dots) != 2:
        raise ValueError(f"expected exactly two marker cells, found {len(dots)}")
    if dots[0][2] != dots[1][2]:
        raise ValueError("the two marker colors differ")
    dot_color = dots[0][2]
    if values - {0, 4, 8, dot_color}:
        raise ValueError("unexpected distractor color outside {0,4,8,dot_color}")

    components = _components_not_8(grid)
    if len(components) != 2:
        raise ValueError(f"expected exactly two non-8 panels, found {len(components)}")
    panels = [_panel_record(grid, cells) for cells in components]
    if any(len(panel["dots"]) != 1 for panel in panels):
        raise ValueError("each panel must contain exactly one marker")

    source_candidates = [panel for panel in panels if panel["yellows"]]
    target_candidates = [panel for panel in panels if not panel["yellows"]]
    if len(source_candidates) != 1 or len(target_candidates) != 1:
        raise ValueError("exactly one panel must contain all yellow source cells")
    source, target = source_candidates[0], target_candidates[0]
    if not (4 <= source["h"] <= 10 and 4 <= source["w"] <= 10):
        raise ValueError("source panel dimensions are outside the canonical envelope")
    if not (5 <= target["h"] <= 10 and 5 <= target["w"] <= 10):
        raise ValueError("target panel dimensions are outside the canonical envelope")

    sr, sc, _ = source["dots"][0]
    tr, tc, _ = target["dots"][0]
    offsets = sorted((r - sr, c - sc) for r, c in source["yellows"])
    if not 7 <= len(offsets) <= 16:
        raise ValueError(f"yellow shape size {len(offsets)} is outside 7..16")
    if not _shape_connected(offsets):
        raise ValueError("yellow cells and source marker do not form one 4-connected shape")
    if not any(max(abs(dr), abs(dc)) <= 1 for dr, dc in offsets):
        raise ValueError("no yellow cell is adjacent to the source marker")
    if max(max(abs(dr), abs(dc)) for dr, dc in offsets) != 2:
        raise ValueError("yellow shape must have canonical Chebyshev radius 2")

    target_rel = (tr - target["r0"], tc - target["c0"])
    for dr, dc in offsets:
        rr, cc = target_rel[0] + dr, target_rel[1] + dc
        if not (0 <= rr < target["h"] and 0 <= cc < target["w"]):
            raise ValueError("translated source shape does not fit target panel")

    return {
        "h": h,
        "w": w,
        "dot_color": dot_color,
        "source": source,
        "target": target,
        "source_dot": source["dots"][0],
        "target_dot": target["dots"][0],
        "offsets": offsets,
        "target_rel": target_rel,
        "panel_layout": _panel_layout(source, target),
    }


def strict_canonical_like(grid) -> list[str]:
    try:
        _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return strict_canonical_like(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    info = _analyze(grid)
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "source_h": info["source"]["h"],
        "source_w": info["source"]["w"],
        "target_h": info["target"]["h"],
        "target_w": info["target"]["w"],
        "shape_size": len(info["offsets"]),
        "dot_color": info["dot_color"],
        "panel_layout": info["panel_layout"],
    }


def _official_output(grid):
    """Python mirror used only for contract probes; Racket remains authority."""
    info = _analyze(grid)
    out = full_grid(info["target"]["h"], info["target"]["w"], 0)
    rr, cc = info["target_rel"]
    out[rr][cc] = info["dot_color"]
    for dr, dc in info["offsets"]:
        out[rr + dr][cc + dc] = 4
    return out


def _rival_center_alignment(grid):
    info = _analyze(grid)
    out = full_grid(info["target"]["h"], info["target"]["w"], 0)
    rr, cc = info["target"]["h"] // 2, info["target"]["w"] // 2
    out[rr][cc] = info["dot_color"]
    for dr, dc in info["offsets"]:
        nr, nc = rr + dr, cc + dc
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 4
    return out


def _rival_source_crop(grid):
    info = _analyze(grid)
    panel = info["source"]
    return [
        list(row[panel["c0"] : panel["c1"] + 1])
        for row in grid[panel["r0"] : panel["r1"] + 1]
    ]


def _rival_target_crop_without_transfer(grid):
    info = _analyze(grid)
    panel = info["target"]
    return [
        list(row[panel["c0"] : panel["c1"] + 1])
        for row in grid[panel["r0"] : panel["r1"] + 1]
    ]


def _rival_full_input(grid):
    return deepcopy(grid)


def _rival_fixed_seven(grid):
    info = _analyze(grid)
    out = full_grid(info["target"]["h"], info["target"]["w"], 0)
    rr, cc = info["target_rel"]
    out[rr][cc] = info["dot_color"]
    for dr, dc in info["offsets"][:7]:
        out[rr + dr][cc + dc] = 4
    return out


def _rival_fixed_l(grid):
    info = _analyze(grid)
    out = full_grid(info["target"]["h"], info["target"]["w"], 0)
    rr, cc = info["target_rel"]
    out[rr][cc] = info["dot_color"]
    for dr, dc in ((-1, 0), (0, 1), (1, 0), (1, 1)):
        nr, nc = rr + dr, cc + dc
        if 0 <= nr < len(out) and 0 <= nc < len(out[0]):
            out[nr][nc] = 4
    return out


def _render_assumed_transfer(grid, assumed_source, assumed_target):
    sr, sc, _ = assumed_source["dots"][0]
    tr, tc, target_color = assumed_target["dots"][0]
    offsets = [(r - sr, c - sc) for r, c in assumed_source["yellows"]]
    out = full_grid(assumed_target["h"], assumed_target["w"], 0)
    rr, cc = tr - assumed_target["r0"], tc - assumed_target["c0"]
    out[rr][cc] = target_color
    for dr, dc in offsets:
        nr, nc = rr + dr, cc + dc
        if 0 <= nr < assumed_target["h"] and 0 <= nc < assumed_target["w"]:
            out[nr][nc] = 4
    return out


def _ordered_panels(info):
    panels = (info["source"], info["target"])
    if info["panel_layout"] in {"source_above", "source_below"}:
        return sorted(panels, key=lambda panel: (panel["r0"], panel["c0"]))
    return sorted(panels, key=lambda panel: (panel["c0"], panel["r0"]))


def _rival_first_panel_source(grid):
    info = _analyze(grid)
    first, second = _ordered_panels(info)
    return _render_assumed_transfer(grid, first, second)


def _rival_second_panel_source(grid):
    info = _analyze(grid)
    first, second = _ordered_panels(info)
    return _render_assumed_transfer(grid, second, first)


def _rival_smaller_panel_source(grid):
    info = _analyze(grid)
    first, second = _ordered_panels(info)
    first_area = first["h"] * first["w"]
    second_area = second["h"] * second["w"]
    if first_area <= second_area:
        return _render_assumed_transfer(grid, first, second)
    return _render_assumed_transfer(grid, second, first)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "center_alignment": _rival_center_alignment,
    "source_crop": _rival_source_crop,
    "target_crop_without_transfer": _rival_target_crop_without_transfer,
    "full_input": _rival_full_input,
    "fixed_seven_yellows": _rival_fixed_seven,
    "fixed_l_shape": _rival_fixed_l,
    "first_panel_is_source": _rival_first_panel_source,
    "second_panel_is_source": _rival_second_panel_source,
    "smaller_panel_is_source": _rival_smaller_panel_source,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "center_alignment": _rival_center_alignment,
    "source_crop": _rival_source_crop,
    "target_crop_without_transfer": _rival_target_crop_without_transfer,
    "smaller_panel_is_source": _rival_smaller_panel_source,
}


def _source_first(grid):
    info = _analyze(grid)
    return _ordered_panels(info)[0] is info["source"]


def _vertical_layout(grid):
    return _analyze(grid)["panel_layout"] in {"source_above", "source_below"}


def _source_area_relation(grid):
    info = _analyze(grid)
    source_area = info["source"]["h"] * info["source"]["w"]
    target_area = info["target"]["h"] * info["target"]["w"]
    if source_area < target_area:
        return "source_smaller"
    if source_area > target_area:
        return "source_larger"
    return "equal"


def _source_above(grid):
    return _analyze(grid)["panel_layout"] == "source_above"


def _source_below(grid):
    return _analyze(grid)["panel_layout"] == "source_below"


def _source_left(grid):
    return _analyze(grid)["panel_layout"] == "source_left"


def _source_right(grid):
    return _analyze(grid)["panel_layout"] == "source_right"


def _off_center_target(grid):
    info = _analyze(grid)
    center = (info["target"]["h"] // 2, info["target"]["w"] // 2)
    return info["target_rel"] != center


def _different_panel_sizes(grid):
    info = _analyze(grid)
    return (info["source"]["h"], info["source"]["w"]) != (
        info["target"]["h"],
        info["target"]["w"],
    )


def _more_than_seven(grid):
    return len(_analyze(grid)["offsets"]) > 7


def _non_fixed_l(grid):
    return set(_analyze(grid)["offsets"]) != {(-1, 0), (0, 1), (1, 0), (1, 1)}


def _source_larger(grid):
    return _source_area_relation(grid) == "source_larger"


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "source_above_target": _source_above,
    "source_below_target": _source_below,
    "source_left_of_target": _source_left,
    "source_right_of_target": _source_right,
    "off_center_target_marker": _off_center_target,
    "different_source_target_sizes": _different_panel_sizes,
    "more_than_seven_yellows": _more_than_seven,
    "non_fixed_l_shape": _non_fixed_l,
    "source_larger_than_target": _source_larger,
}
WITNESS_RIVALS = {
    "source_above_target": ["second_panel_is_source"],
    "source_below_target": ["first_panel_is_source"],
    "source_left_of_target": ["second_panel_is_source"],
    "source_right_of_target": ["first_panel_is_source"],
    "off_center_target_marker": ["center_alignment"],
    "different_source_target_sizes": ["source_crop"],
    "more_than_seven_yellows": ["fixed_seven_yellows"],
    "non_fixed_l_shape": ["fixed_l_shape"],
    "source_larger_than_target": ["smaller_panel_is_source"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    all_pairs = demos + [query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"pair {index} is missing input/output"]
        errors = strict_canonical_like(pair["input"])
        if errors:
            return [f"pair {index} malformed: {errors[0]}"]
        if pair["output"] != _official_output(pair["input"]):
            return [f"pair {index} output does not match the task rule"]

    orientations = {"vertical" if _vertical_layout(pair["input"]) else "horizontal" for pair in demos}
    if orientations != {"vertical", "horizontal"}:
        return ["demonstrations do not cover both panel orientations"]
    source_orders = {_source_first(pair["input"]) for pair in demos}
    if source_orders != {False, True}:
        return ["demonstrations do not refute a fixed first/second source rule"]
    area_relations = {_source_area_relation(pair["input"]) for pair in demos}
    if not {"source_smaller", "source_larger"}.issubset(area_relations):
        return ["demonstrations do not refute a smaller-panel source rule"]

    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes query answer")
    return reasons
