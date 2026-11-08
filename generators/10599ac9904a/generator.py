"""Generator for M151 / 10599ac9904a — translate payload by the last 2→3 vector.

The selected Racket authority scans in row-major order, uses the LAST color-2
cell and the LAST color-3 cell as anchors, and translates every cell whose
color is not 0, 2, or 3 by that vector onto a blank output.  Translation is
cellwise: off-grid destinations are dropped, while in-bounds payload cells
survive.  All marker-colored cells disappear.

A five-slot lesson schedule keeps the generated distribution anchored to the
five public (height, width, palette-size) profiles while forcing the semantic
branches that the original one-marker / isolated-pixel generator omitted:
empty payload, repeated marker colors combined with multiple payload
colors/components, partial clipping, and full clipping.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "10599ac9904a"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "6bbf0525c028"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read cells in row-major order. The last color-2 cell is the source anchor "
    "and the last color-3 cell is the destination anchor. Translate every "
    "non-{0,2,3} payload cell by that 2→3 offset into a blank same-size grid; "
    "drop translated cells that leave the grid and erase all marker cells."
)

INVARIANTS = [
    "the input is a rectangular ARC grid with at least one color-2 and one color-3 cell",
    "the last row-major 2 and last row-major 3 define a nonzero translation vector",
    "payload is exactly every cell whose color is not 0, 2, or 3 and may be empty",
    "payload translation is cellwise, so partial and complete clipping are lawful",
    "every five consecutive scheduled samples cover all decisive scene profiles",
]

SCENE_PROFILES = (
    "basic",
    "empty_payload",
    "repeated_multi_payload",
    "partial_clip",
    "full_clip",
)
SCHEDULE_PROFILES = SCENE_PROFILES

VECTOR_OPTIONS = {
    "down_right_3_4": (3, 4),
    "down_left_2_3": (2, -3),
    "up_right_4_4": (-4, 4),
    "up_left_3_4": (-3, -4),
    "down_right_2_6": (2, 6),
    "up_right_2_5": (-2, 5),
    "down_left_4_2": (4, -2),
    "up_left_4_3": (-4, -3),
}
_VECTOR_NAMES = tuple(VECTOR_OPTIONS)
_VECTOR_BY_DELTA = {delta: name for name, delta in VECTOR_OPTIONS.items()}

# Each profile uses one of the public (h, w, palette-size) triples by default.
_PROFILE_DIMS = {
    "basic": (9, 10),          # palette 4
    "empty_payload": (10, 11), # palette 3
    "repeated_multi_payload": (8, 12),  # palette 5
    "partial_clip": (10, 12),
    "full_clip": (11, 11),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-linked canonical schedule",
        "valid": "8..12",
        "doc": "Input height.",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-linked canonical schedule",
        "valid": "10..12",
        "doc": "Input width.",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index mod 5 schedule",
        "valid": "basic|empty_payload|repeated_multi_payload|partial_clip|full_clip",
        "doc": "Observable semantic branch of the generated scene.",
    },
    "vector": {
        "type": "str",
        "default": "sample_index mod 8 schedule",
        "valid": "down_right_3_4|down_left_2_3|up_right_4_4|up_left_3_4|down_right_2_6|up_right_2_5|down_left_4_2|up_left_4_3",
        "doc": "Exact last-2 to last-3 translation vector.",
    },
}

# Every Cartesian boundary combination is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the exact five-slot teaching cadence to the semantic gate."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    return "medium" if difficulty is None else str(difficulty)



def _resolved_choice(ctx, overrides, name: str, scheduled: str, options):
    if name in overrides and overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def _resolved_int(ctx, overrides, name: str, scheduled: int, lo: int, hi: int):
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, scheduled, scheduled))


def _row_major_cells(grid, color: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]


def _payload_cells(grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2, 3)
    ]


def _anchors_and_delta(grid):
    twos = _row_major_cells(grid, 2)
    threes = _row_major_cells(grid, 3)
    if not twos or not threes:
        raise ValueError("grid requires at least one color-2 and color-3 cell")
    src, dst = twos[-1], threes[-1]
    return src, dst, (dst[0] - src[0], dst[1] - src[1])


def _translate_subset(
    grid,
    cells: Iterable[tuple[int, int, int]],
    delta: tuple[int, int],
    *,
    clamp: bool = False,
):
    h, w = len(grid), len(grid[0])
    dr, dc = delta
    out = full_grid(h, w, 0)
    for r, c, value in cells:
        nr, nc = r + dr, c + dc
        if clamp:
            nr = min(max(nr, 0), h - 1)
            nc = min(max(nc, 0), w - 1)
        if 0 <= nr < h and 0 <= nc < w:
            out[nr][nc] = value
    return out


def _python_apply(grid):
    """Independent executable spelling of the selected Racket authority."""
    _src, _dst, delta = _anchors_and_delta(grid)
    return _translate_subset(grid, _payload_cells(grid), delta)


def _in_bounds_after(cell: tuple[int, int], delta, h: int, w: int) -> bool:
    r, c = cell
    dr, dc = delta
    return 0 <= r + dr < h and 0 <= c + dc < w


def _connected_subset(
    candidates: set[tuple[int, int]],
    size: int,
    rng,
) -> list[tuple[int, int]] | None:
    """Find a deterministic-random connected subset of exactly ``size``."""
    if size <= 0:
        return []
    starts = sorted(candidates)
    rng.shuffle(starts)
    for start in starts:
        chosen = [start]
        chosen_set = {start}
        frontier = [
            (start[0] + dr, start[1] + dc)
            for dr, dc in _NEIGHBORS
            if (start[0] + dr, start[1] + dc) in candidates
        ]
        rng.shuffle(frontier)
        while frontier and len(chosen) < size:
            cell = frontier.pop()
            if cell in chosen_set:
                continue
            chosen.append(cell)
            chosen_set.add(cell)
            nxt = [
                (cell[0] + dr, cell[1] + dc)
                for dr, dc in _NEIGHBORS
                if (cell[0] + dr, cell[1] + dc) in candidates
                and (cell[0] + dr, cell[1] + dc) not in chosen_set
            ]
            rng.shuffle(nxt)
            frontier.extend(nxt)
        if len(chosen) == size:
            return chosen
    return None


def _separated_subset(
    candidates: set[tuple[int, int]],
    occupied: set[tuple[int, int]],
    size: int,
    rng,
) -> list[tuple[int, int]] | None:
    blocked = set(occupied)
    for r, c in list(occupied):
        blocked.update((r + dr, c + dc) for dr, dc in _NEIGHBORS)
    return _connected_subset(candidates - blocked, size, rng)


def _prefix_positions(anchor: tuple[int, int], h: int, w: int):
    limit = anchor[0] * w + anchor[1]
    return [(index // w, index % w) for index in range(limit)]


def _choose_anchors(h: int, w: int, delta, repeated: bool, rng):
    dr, dc = delta
    candidates = [
        ((r, c), (r + dr, c + dc))
        for r in range(h)
        for c in range(w)
        if 0 <= r + dr < h and 0 <= c + dc < w
    ]
    rng.shuffle(candidates)
    for src, dst in candidates:
        if not repeated:
            return src, dst, [], []
        occupied = {src, dst}
        two_prefix = [p for p in _prefix_positions(src, h, w) if p not in occupied]
        three_prefix = [p for p in _prefix_positions(dst, h, w) if p not in occupied]
        rng.shuffle(two_prefix)
        rng.shuffle(three_prefix)
        selected = None
        for first_two in two_prefix:
            for first_three in three_prefix:
                if first_three == first_two:
                    continue
                first_delta = (
                    first_three[0] - first_two[0],
                    first_three[1] - first_two[1],
                )
                if first_delta != delta:
                    selected = (first_two, first_three)
                    break
            if selected is not None:
                break
        if selected is None:
            continue
        first_two, first_three = selected
        extra_twos = [first_two]
        extra_threes = [first_three]
        occupied.update(extra_twos)
        occupied.update(extra_threes)
        # Add later (but still pre-anchor) distractors without changing the
        # first-occurrence rival vector chosen above.
        first_two_index = first_two[0] * w + first_two[1]
        first_three_index = first_three[0] * w + first_three[1]
        later_twos = [
            p for p in two_prefix
            if p not in occupied and p[0] * w + p[1] > first_two_index
        ]
        later_threes = [
            p for p in three_prefix
            if p not in occupied and p[0] * w + p[1] > first_three_index
        ]
        rng.shuffle(later_twos)
        rng.shuffle(later_threes)
        extra_twos.extend(later_twos[:2])
        occupied.update(extra_twos[1:])
        extra_threes.extend([p for p in later_threes if p not in occupied][:1])
        return src, dst, extra_twos, extra_threes
    raise ValueError("could not place selected anchors and earlier marker distractors")


def _payload_sizes(profile: str, band: str) -> tuple[int, int]:
    bump = {"easy": 0, "medium": 1, "hard": 2}[band]
    if profile == "basic":
        return 3 + bump, 0
    if profile == "repeated_multi_payload":
        return 3 + min(bump, 1), 1 + min(bump, 1)
    if profile == "partial_clip":
        return 3 + min(bump, 1), 0
    if profile == "full_clip":
        return 2 + min(bump, 2), 0
    return 0, 0


def _partial_subset(
    available: set[tuple[int, int]],
    safe: set[tuple[int, int]],
    unsafe: set[tuple[int, int]],
    size: int,
    rng,
) -> list[tuple[int, int]] | None:
    boundaries = []
    for cell in safe:
        for dr, dc in _NEIGHBORS:
            other = (cell[0] + dr, cell[1] + dc)
            if other in unsafe:
                boundaries.append((cell, other))
    rng.shuffle(boundaries)
    for first, second in boundaries:
        chosen = [first, second]
        chosen_set = set(chosen)
        frontier = []
        for cell in chosen:
            frontier.extend(
                (cell[0] + dr, cell[1] + dc)
                for dr, dc in _NEIGHBORS
                if (cell[0] + dr, cell[1] + dc) in available
            )
        rng.shuffle(frontier)
        while frontier and len(chosen) < size:
            cell = frontier.pop()
            if cell in chosen_set:
                continue
            chosen.append(cell)
            chosen_set.add(cell)
            frontier.extend(
                (cell[0] + dr, cell[1] + dc)
                for dr, dc in _NEIGHBORS
                if (cell[0] + dr, cell[1] + dc) in available
                and (cell[0] + dr, cell[1] + dc) not in chosen_set
            )
        if len(chosen) == size and chosen_set & safe and chosen_set & unsafe:
            return chosen
    return None


def _draw_scene(h: int, w: int, profile: str, delta, band: str, ctx):
    rng = ctx.draw_rng("layout")
    repeated = profile == "repeated_multi_payload"
    src, dst, extra_twos, extra_threes = _choose_anchors(
        h, w, delta, repeated, rng
    )
    grid = full_grid(h, w, 0)
    for cell in extra_twos:
        grid[cell[0]][cell[1]] = 2
    for cell in extra_threes:
        grid[cell[0]][cell[1]] = 3
    grid[src[0]][src[1]] = 2
    grid[dst[0]][dst[1]] = 3

    if profile == "empty_payload":
        return grid

    marker_cells = set(extra_twos) | set(extra_threes) | {src, dst}
    available = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in marker_cells
    }
    safe = {cell for cell in available if _in_bounds_after(cell, delta, h, w)}
    unsafe = available - safe
    size_a, size_b = _payload_sizes(profile, band)

    if profile == "basic":
        cells_a = _connected_subset(safe, size_a, rng)
        cells_b = None
    elif profile == "repeated_multi_payload":
        cells_a = _connected_subset(safe, size_a, rng)
        cells_b = (
            _separated_subset(safe, set(cells_a or ()), size_b, rng)
            if cells_a
            else None
        )
    elif profile == "partial_clip":
        cells_a = _partial_subset(available, safe, unsafe, size_a, rng)
        cells_b = None
    elif profile == "full_clip":
        cells_a = _connected_subset(unsafe, size_a, rng)
        cells_b = None
    else:  # guarded by AXES + _validate_call
        raise ValueError(f"unsupported scene_profile {profile!r}")

    if cells_a is None or (profile == "repeated_multi_payload" and cells_b is None):
        raise ValueError(
            f"could not construct scene_profile={profile!r} for {h}x{w} vector={delta}"
        )

    n_colors = 2 if profile == "repeated_multi_payload" else 1
    colors = ctx.draw_distinct_colors(
        "payload_colors", n=n_colors, exclude=(0, 2, 3)
    )
    for r, c in cells_a:
        grid[r][c] = colors[0]
    if cells_b:
        for r, c in cells_b:
            grid[r][c] = colors[1]

    # The repeated-marker profile is specifically a last-occurrence witness.
    if repeated and _python_apply(grid) == _rival_first_markers(grid):
        raise ValueError("repeated-marker scene failed to distinguish first vs last anchors")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile = _resolved_choice(
        ctx, overrides, "scene_profile", scheduled_profile, SCENE_PROFILES
    )
    default_h, default_w = _PROFILE_DIMS[profile]
    h = _resolved_int(ctx, overrides, "grid_h", default_h, 8, 12)
    w = _resolved_int(ctx, overrides, "grid_w", default_w, 10, 12)
    scheduled_vector = _VECTOR_NAMES[int(sample_index) % len(_VECTOR_NAMES)]
    vector_name = _resolved_choice(
        ctx, overrides, "vector", scheduled_vector, _VECTOR_NAMES
    )
    return _draw_scene(h, w, profile, VECTOR_OPTIONS[vector_name], band, ctx)


def _analyse(grid) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid rows must be non-empty sequences"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {}, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return {}, [f"cell ({r},{c})={value!r} is not an ARC integer color 0..9"]
    twos = _row_major_cells(grid, 2)
    threes = _row_major_cells(grid, 3)
    errors = []
    if not (2 <= h <= 30 and 2 <= w <= 30):
        errors.append(f"dimensions {h}x{w} must lie in 2..30")
    if not twos:
        errors.append("expected at least one color-2 anchor candidate")
    if not threes:
        errors.append("expected at least one color-3 anchor candidate")
    delta = None
    if twos and threes:
        delta = (threes[-1][0] - twos[-1][0], threes[-1][1] - twos[-1][1])
        if delta == (0, 0):
            errors.append("selected last 2 and last 3 must define a nonzero vector")
    payload = _payload_cells(grid)
    safe_count = 0
    if delta is not None:
        safe_count = sum(
            _in_bounds_after((r, c), delta, h, w) for r, c, _value in payload
        )
    return {
        "grid_h": h,
        "grid_w": w,
        "twos": twos,
        "threes": threes,
        "delta": delta,
        "payload": payload,
        "payload_colors": {value for _r, _c, value in payload},
        "safe_payload": safe_count,
        "unsafe_payload": len(payload) - safe_count,
        "palette_size": len({value for row in grid for value in row}),
    }, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-valid input grammar, including empty/clipped payload."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    """Validate the linked canonical envelope without imposing curriculum-only witnesses."""
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons = []
    if not (8 <= info["grid_h"] <= 11 and 10 <= info["grid_w"] <= 12):
        reasons.append(
            f"dimensions {(info['grid_h'], info['grid_w'])!r} leave canonical 8..11 x 10..12 envelope"
        )
    if not (3 <= info["palette_size"] <= 5):
        reasons.append(f"palette size {info['palette_size']} leaves canonical 3..5 envelope")
    if not (1 <= len(info["twos"]) <= 6):
        reasons.append(f"color-2 count {len(info['twos'])} leaves canonical 1..6 envelope")
    if not (1 <= len(info["threes"]) <= 3):
        reasons.append(f"color-3 count {len(info['threes'])} leaves canonical 1..3 envelope")
    if len(info["payload"]) > 8:
        reasons.append(f"payload cell count {len(info['payload'])} exceeds linked envelope 0..8")
    return reasons


def _scene_profile(grid) -> str | None:
    info, errors = _analyse(grid)
    if errors:
        return None
    payload_n = len(info["payload"])
    if payload_n == 0:
        return "empty_payload"
    if info["safe_payload"] and info["unsafe_payload"]:
        return "partial_clip"
    if info["unsafe_payload"] and not info["safe_payload"]:
        return "full_clip"
    if len(info["twos"]) > 1 or len(info["threes"]) > 1:
        return "repeated_multi_payload"
    return "basic"


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned input grid."""
    info, errors = _analyse(grid)
    if errors:
        return {}
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "scene_profile": _scene_profile(grid),
        "vector": _VECTOR_BY_DELTA.get(info["delta"]),
    }


def _payload_components(grid):
    coords = {(r, c): value for r, c, value in _payload_cells(grid)}
    seen = set()
    result = []
    for start in sorted(coords):
        if start in seen:
            continue
        queue = deque([start])
        seen.add(start)
        comp = []
        while queue:
            cell = queue.popleft()
            comp.append((cell[0], cell[1], coords[cell]))
            for dr, dc in _NEIGHBORS:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt in coords and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        result.append(comp)
    return result


def _rival_first_markers(grid):
    twos = _row_major_cells(grid, 2)
    threes = _row_major_cells(grid, 3)
    if not twos or not threes:
        return full_grid(len(grid), len(grid[0]), 0)
    delta = (threes[0][0] - twos[0][0], threes[0][1] - twos[0][1])
    return _translate_subset(grid, _payload_cells(grid), delta)


def _rival_largest_component_only(grid):
    comps = _payload_components(grid)
    if not comps:
        return full_grid(len(grid), len(grid[0]), 0)
    chosen = max(comps, key=lambda comp: (len(comp), tuple(comp)))
    _src, _dst, delta = _anchors_and_delta(grid)
    return _translate_subset(grid, chosen, delta)


def _rival_one_payload_color_only(grid):
    payload = _payload_cells(grid)
    if not payload:
        return full_grid(len(grid), len(grid[0]), 0)
    counts: dict[int, int] = {}
    for _r, _c, value in payload:
        counts[value] = counts.get(value, 0) + 1
    chosen = max(sorted(counts), key=lambda value: counts[value])
    subset = [cell for cell in payload if cell[2] == chosen]
    _src, _dst, delta = _anchors_and_delta(grid)
    return _translate_subset(grid, subset, delta)


def _rival_all_or_nothing_clipping(grid):
    payload = _payload_cells(grid)
    _src, _dst, delta = _anchors_and_delta(grid)
    h, w = len(grid), len(grid[0])
    if any(not _in_bounds_after((r, c), delta, h, w) for r, c, _v in payload):
        return full_grid(h, w, 0)
    return _translate_subset(grid, payload, delta)


def _rival_clamp_to_edge(grid):
    _src, _dst, delta = _anchors_and_delta(grid)
    return _translate_subset(grid, _payload_cells(grid), delta, clamp=True)


def _rival_keep_markers(grid):
    out = _python_apply(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3):
                out[r][c] = value
    return out


def _rival_fixed_vector(grid):
    return _translate_subset(grid, _payload_cells(grid), (1, 1))


def _witness_profile(name: str, rival: Callable):
    return lambda grid: _scene_profile(grid) == name and _python_apply(grid) != rival(grid)


def _quadrant(grid):
    info, errors = _analyse(grid)
    if errors or not info["payload"]:
        return None
    dr, dc = info["delta"]
    return ("down" if dr > 0 else "up") + "_" + ("right" if dc > 0 else "left")


def _witness_quadrant(name: str):
    return lambda grid: _quadrant(grid) == name and _python_apply(grid) != _rival_fixed_vector(grid)


SEMANTIC_WITNESSES = {
    "empty_payload_returns_blank": _witness_profile("empty_payload", _rival_keep_markers),
    "repeated_markers_select_last": _witness_profile("repeated_multi_payload", _rival_first_markers),
    "all_payload_colors_move": _witness_profile("repeated_multi_payload", _rival_one_payload_color_only),
    "all_payload_components_move": _witness_profile("repeated_multi_payload", _rival_largest_component_only),
    "partial_clipping_is_cellwise": _witness_profile("partial_clip", _rival_all_or_nothing_clipping),
    "full_clipping_drops_every_cell": _witness_profile("full_clip", _rival_clamp_to_edge),
    "down_right_vector": _witness_quadrant("down_right"),
    "down_left_vector": _witness_quadrant("down_left"),
    "up_right_vector": _witness_quadrant("up_right"),
    "up_left_vector": _witness_quadrant("up_left"),
}

SEMANTIC_RIVALS = {
    "first_marker_occurrences": _rival_first_markers,
    "largest_payload_component_only": _rival_largest_component_only,
    "one_payload_color_only": _rival_one_payload_color_only,
    "all_or_nothing_clipping": _rival_all_or_nothing_clipping,
    "clamp_out_of_bounds_to_edge": _rival_clamp_to_edge,
    "keep_marker_cells": _rival_keep_markers,
    "fixed_down_right_one": _rival_fixed_vector,
}

WITNESS_RIVALS = {
    "empty_payload_returns_blank": ["keep_marker_cells"],
    "repeated_markers_select_last": ["first_marker_occurrences"],
    "all_payload_colors_move": ["one_payload_color_only"],
    "all_payload_components_move": ["largest_payload_component_only"],
    "partial_clipping_is_cellwise": ["all_or_nothing_clipping"],
    "full_clipping_drops_every_cell": ["clamp_out_of_bounds_to_edge"],
    "down_right_vector": ["fixed_down_right_one"],
    "down_left_vector": ["fixed_down_right_one"],
    "up_right_vector": ["fixed_down_right_one"],
    "up_left_vector": ["fixed_down_right_one"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# These three wrong rules reproduce the sparse public examples surprisingly
# well; generated counterexamples are therefore required, not optional.
CANONICAL_SHORTCUTS = {
    "largest_payload_component_only": _rival_largest_component_only,
    "one_payload_color_only": _rival_one_payload_color_only,
    "all_or_nothing_clipping": _rival_all_or_nothing_clipping,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require one full five-profile teaching cycle and kill every named rival."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    demo_inputs = []
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        output = pair.get("output")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = _python_apply(grid)
        if output != expected:
            reasons.append(f"demo {index} output disagrees with last-2→last-3 translation")
        demo_inputs.append(grid)

    profiles = {_scene_profile(grid) for grid in demo_inputs}
    if profiles != set(SCENE_PROFILES):
        reasons.append(f"demos cover profiles {sorted(profiles)!r}, not all five")
    quadrants = {_quadrant(grid) for grid in demo_inputs if _quadrant(grid)}
    row_signs = {name.split("_", 1)[0] for name in quadrants}
    col_signs = {name.rsplit("_", 1)[1] for name in quadrants}
    if len(quadrants) < 3 or row_signs != {"up", "down"} or col_signs != {"left", "right"}:
        reasons.append(
            f"demos cover vector quadrants {sorted(quadrants)!r}; need at least three spanning both row and column signs"
        )
    for name, rival in LESSON_COMPETITORS.items():
        if not any(_python_apply(grid) != rival(grid) for grid in demo_inputs):
            reasons.append(f"{name} rival survives every demo")

    q_grid = query.get("input")
    q_output = query.get("output")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
    elif q_output != _python_apply(q_grid):
        reasons.append("query answer disagrees with last-2→last-3 translation")
    return reasons


def mutation_fixtures():
    """Structural near misses that the authority-valid self_check must reject."""
    no_markers = full_grid(8, 10, 0)
    no_markers[2][2] = 4

    no_three = full_grid(8, 10, 0)
    no_three[1][1] = 2
    no_three[2][2] = 4

    no_two = full_grid(8, 10, 0)
    no_two[4][5] = 3
    no_two[2][2] = 4

    ragged = [row[:] for row in no_three]
    ragged[-1] = ragged[-1][:-1]

    invalid_color = [row[:] for row in no_three]
    invalid_color[0][0] = 10

    return [
        ("missing_both_marker_colors", no_markers),
        ("missing_color_3", no_three),
        ("missing_color_2", no_two),
        ("ragged_grid", ragged),
        ("invalid_arc_color", invalid_color),
    ]
