"""Generator for ``easy_98_stamp_pluses_at_markers``.

Every nonzero input cell is an independent marker.  The Racket authority
replaces each marker by the same-color orthogonal radius-1 plus.

The teaching distribution deliberately includes repeated marker colors.  The
canonical examples use a different color at every marker, so without that
counterexample a plausible wrong rule -- "stamp once per color" -- is never
falsified.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e294395dad07"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e9582d2bcde1"
EXAMPLES_NEEDED = 3
LESSON_SAMPLE_STRIDE = 11
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero background, replace every separated interior point marker by "
    "a same-color five-cell orthogonal plus, preserving grid size."
)

INVARIANTS = [
    "background is color 0",
    "the input contains three to five isolated one-cell markers",
    "every marker is one cell inside the border or farther",
    "radius-1 plus footprints are pairwise disjoint",
    "marker colors may repeat; every marker is stamped independently",
]

COLOR_MODES = ("all_distinct", "repeated", "monochrome")
POSITION_PROFILES = ("all_border_touching", "mixed", "all_interior")
SCHEDULE_PROFILES = (0, 1, 2, 3)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile anchor or difficulty-aware 8..16",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile anchor or difficulty-aware 9..16",
        "valid": "9..16",
    },
    "markers": {
        "type": "int",
        "default": "scheduled 3|4|5|4",
        "valid": "3..5",
    },
    "color_mode": {
        "type": "str",
        "default": "scheduled all_distinct|repeated|monochrome|repeated",
        "valid": "all_distinct|repeated|monochrome",
    },
    "position_profile": {
        "type": "str",
        "default": "scheduled all_border_touching|mixed|all_interior|mixed",
        "valid": "all_border_touching|mixed|all_interior",
    },
}

# Exact canonical (height, width) profiles.  Slot 0 anchors one of these in
# every four ordinary draws; marker/palette scheduling then reproduces the
# canonical (h, w, palette-size) profile exactly.
_CANONICAL_DIMS = ((9, 11), (8, 10), (10, 12), (9, 9), (8, 12))
_COLOR_SCHEDULE = ("all_distinct", "repeated", "monochrome", "repeated")
_POSITION_SCHEDULE = (
    "all_border_touching",
    "mixed",
    "all_interior",
    "mixed",
)
_MARKER_SCHEDULE = (3, 4, 5, 4)


def _plus_cells(r: int, c: int) -> set[tuple[int, int]]:
    return {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def _compatible(a: tuple[int, int], b: tuple[int, int]) -> bool:
    # Two radius-1 orthogonal pluses are disjoint exactly when their centers
    # have Manhattan distance at least 3.
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) >= 3


def _is_border_touching_center(r: int, c: int, h: int, w: int) -> bool:
    return r in (1, h - 2) or c in (1, w - 2)


def _record_int(ctx, label: str, lo: int, hi: int, default: int) -> int:
    """Validate an exact override, otherwise record a scheduled default."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = int(ctx.overrides[label])
        if not lo <= value <= hi:
            raise ValueError(f"{label} override {value} outside [{lo}, {hi}]")
        return int(ctx._record(label, value, from_override=True))
    if not lo <= default <= hi:
        raise ValueError(f"internal {label} default {default} outside [{lo}, {hi}]")
    return int(ctx._record(label, int(default), from_override=False))


def _record_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    """Validate an exact string override, otherwise record a scheduled value."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        value = str(ctx.overrides[label])
        if value not in options:
            raise ValueError(f"{label} override {value!r} not in {options}")
        return str(ctx._record(label, value, from_override=True))
    if default not in options:
        raise ValueError(f"internal {label} default {default!r} not in {options}")
    return str(ctx._record(label, default, from_override=False))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _default_dims(ctx, slot: int, difficulty) -> tuple[int, int]:
    if slot == 0:
        rng = ctx.draw_rng("canonical_profile")
        return _CANONICAL_DIMS[rng.randrange(len(_CANONICAL_DIMS))]

    ranges = {
        "easy": ((8, 10), (9, 12)),
        "medium": ((9, 13), (10, 14)),
        "hard": ((11, 16), (12, 16)),
        None: ((8, 16), (9, 16)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[difficulty]
    return (
        ctx.draw_rng("grid_h_default").randint(h_lo, h_hi),
        ctx.draw_rng("grid_w_default").randint(w_lo, w_hi),
    )


def _candidate_centers(h: int, w: int, profile: str) -> list[tuple[int, int]]:
    centers = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    if profile == "all_border_touching":
        return [p for p in centers if _is_border_touching_center(*p, h, w)]
    if profile == "all_interior":
        return [p for p in centers if not _is_border_touching_center(*p, h, w)]
    return centers


def _find_centers(
    h: int,
    w: int,
    count: int,
    profile: str,
    rng,
) -> list[tuple[int, int]]:
    candidates = _candidate_centers(h, w, profile)
    rng.shuffle(candidates)

    # Put both required categories early for mixed scenes.  The recursive search
    # still checks the final semantic condition, so ordering affects only which
    # lawful layout is chosen, not whether a bad one is accepted.
    if profile == "mixed":
        candidates.sort(
            key=lambda p: (
                0 if _is_border_touching_center(*p, h, w) else 1,
                rng.random(),
            )
        )

    chosen: list[tuple[int, int]] = []

    def final_ok() -> bool:
        if profile != "mixed":
            return True
        flags = [_is_border_touching_center(*p, h, w) for p in chosen]
        return any(flags) and not all(flags)

    def search(start: int) -> bool:
        if len(chosen) == count:
            return final_ok()
        if len(chosen) + len(candidates) - start < count:
            return False
        for index in range(start, len(candidates)):
            point = candidates[index]
            if all(_compatible(point, other) for other in chosen):
                chosen.append(point)
                if search(index + 1):
                    return True
                chosen.pop()
        return False

    if not search(0):
        raise ValueError(
            f"cannot place {count} disjoint markers in {h}x{w} "
            f"with position_profile={profile!r}"
        )
    return chosen


def _marker_colors(mode: str, count: int, rng) -> list[int]:
    if mode == "monochrome":
        return [rng.choice(range(1, 10))] * count
    if mode == "all_distinct":
        return rng.sample(range(1, 10), count)
    # Exactly two colors, both present, with the first color repeated.  This is
    # the decisive generated counterexample to "stamp once per color".
    first, second = rng.sample(range(1, 10), 2)
    colors = [first, second] + [first if i % 2 == 0 else second for i in range(count - 2)]
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w = _default_dims(ctx, slot, difficulty)
    h = _record_int(ctx, "grid_h", 8, 16, default_h)
    w = _record_int(ctx, "grid_w", 9, 16, default_w)
    marker_count = _record_int(ctx, "markers", 3, 5, _MARKER_SCHEDULE[slot])
    color_mode = _record_choice(ctx, "color_mode", COLOR_MODES, _COLOR_SCHEDULE[slot])
    position_profile = _record_choice(
        ctx,
        "position_profile",
        POSITION_PROFILES,
        _POSITION_SCHEDULE[slot],
    )

    layout_rng = ctx.draw_rng("layout")
    centers = _find_centers(h, w, marker_count, position_profile, layout_rng)
    colors = _marker_colors(color_mode, marker_count, ctx.draw_rng("colors"))

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(centers, colors):
        grid[r][c] = color
    return grid


def _markers(grid) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]


def observe_overrides(grid) -> dict[str, int | str]:
    markers = _markers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    distinct = len({value for _, _, value in markers})
    if distinct == len(markers):
        color_mode = "all_distinct"
    elif distinct == 1:
        color_mode = "monochrome"
    else:
        color_mode = "repeated"

    border_flags = [
        _is_border_touching_center(r, c, h, w) for r, c, _ in markers
    ]
    if border_flags and all(border_flags):
        position_profile = "all_border_touching"
    elif border_flags and not any(border_flags):
        position_profile = "all_interior"
    else:
        position_profile = "mixed"

    return {
        "grid_h": h,
        "grid_w": w,
        "markers": len(markers),
        "color_mode": color_mode,
        "position_profile": position_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or rule-hiding inputs from this task's grammar."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 16 and 9 <= w <= 16):
        errors.append(f"grid dimensions {h}x{w} outside canonical teaching envelope")
    for row in grid:
        if not isinstance(row, list) or len(row) != w:
            return errors + ["ragged grid"]
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"invalid cell value {value!r}")
                return errors

    markers = _markers(grid)
    if not (3 <= len(markers) <= 5):
        errors.append(f"expected 3..5 markers, found {len(markers)}")
    footprints: list[tuple[tuple[int, int], set[tuple[int, int]]]] = []
    for r, c, _ in markers:
        if r in (0, h - 1) or c in (0, w - 1):
            errors.append(f"marker at border: {(r, c)}")
        footprint = _plus_cells(r, c)
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in footprint):
            errors.append(f"plus footprint leaves grid at {(r, c)}")
        footprints.append(((r, c), footprint))
    for index, (left, left_fp) in enumerate(footprints):
        for right, right_fp in footprints[index + 1 :]:
            if left_fp & right_fp:
                errors.append(f"plus footprints overlap: {left} and {right}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    # Every ordinary draw intentionally remains on the same sparse point-marker
    # manifold as all five canonical inputs.
    return self_check(grid)


def _analysis(grid) -> dict[str, object]:
    markers = _markers(grid)
    h = len(grid)
    w = len(grid[0]) if h else 0
    colors = [value for _, _, value in markers]
    border = [_is_border_touching_center(r, c, h, w) for r, c, _ in markers]
    return {
        "markers": markers,
        "colors": colors,
        "distinct_colors": len(set(colors)),
        "has_border_touching": any(border),
        "has_deep_interior": bool(border) and not all(border),
    }


def _witness_valid_plus_scene(grid) -> bool:
    return not self_check(grid)


def _witness_multiple_markers(grid) -> bool:
    return len(_markers(grid)) >= 3


def _witness_repeated_color_locations(grid) -> bool:
    info = _analysis(grid)
    return int(info["distinct_colors"]) < len(info["markers"])


def _witness_mixed_marker_colors(grid) -> bool:
    return int(_analysis(grid)["distinct_colors"]) >= 2


def _witness_monochrome_markers(grid) -> bool:
    return int(_analysis(grid)["distinct_colors"]) == 1


def _witness_all_distinct_markers(grid) -> bool:
    info = _analysis(grid)
    return int(info["distinct_colors"]) == len(info["markers"])


def _witness_border_touching_stamp(grid) -> bool:
    return bool(_analysis(grid)["has_border_touching"])


def _witness_fully_interior_stamp(grid) -> bool:
    markers = _markers(grid)
    h, w = len(grid), len(grid[0])
    return bool(markers) and all(
        not _is_border_touching_center(r, c, h, w) for r, c, _ in markers
    )


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "orthogonal_plus_rebuttal": _witness_valid_plus_scene,
    "all_markers_matter": _witness_multiple_markers,
    "repeated_color_locations": _witness_repeated_color_locations,
    "mixed_marker_colors": _witness_mixed_marker_colors,
    "monochrome_markers": _witness_monochrome_markers,
    "all_distinct_marker_colors": _witness_all_distinct_markers,
    "border_touching_output": _witness_border_touching_stamp,
    "fully_interior_output": _witness_fully_interior_stamp,
}


def _paint_neighborhood(grid, cells_fn, color_fn=None):
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = full_grid(h, w, 0)
    markers = _markers(grid)
    for index, (r, c, color) in enumerate(markers):
        paint_color = color_fn(markers, index) if color_fn else color
        for rr, cc in cells_fn(r, c):
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = paint_color
    return out


def rule_mirror(grid):
    """Pure test mirror; generated outputs still come only from Racket."""
    return _paint_neighborhood(grid, _plus_cells)


def _identity(grid):
    return [list(row) for row in grid]


def _horizontal_only(grid):
    return _paint_neighborhood(grid, lambda r, c: {(r, c - 1), (r, c), (r, c + 1)})


def _vertical_only(grid):
    return _paint_neighborhood(grid, lambda r, c: {(r - 1, c), (r, c), (r + 1, c)})


def _diagonal_x(grid):
    return _paint_neighborhood(
        grid,
        lambda r, c: {(r, c), (r - 1, c - 1), (r - 1, c + 1), (r + 1, c - 1), (r + 1, c + 1)},
    )


def _square_3x3(grid):
    return _paint_neighborhood(
        grid,
        lambda r, c: {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)},
    )


def _first_marker_only(grid):
    markers = _markers(grid)
    if not markers:
        return full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    r, c, color = markers[0]
    out = full_grid(len(grid), len(grid[0]), 0)
    for rr, cc in _plus_cells(r, c):
        if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
            out[rr][cc] = color
    return out


def _one_stamp_per_color(grid):
    seen: set[int] = set()
    h, w = len(grid), len(grid[0]) if grid else 0
    out = full_grid(h, w, 0)
    for r, c, color in _markers(grid):
        if color in seen:
            continue
        seen.add(color)
        for rr, cc in _plus_cells(r, c):
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = color
    return out


def _modal_color_plus(grid):
    colors = [value for _, _, value in _markers(grid)]
    if not colors:
        return full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    counts = Counter(colors)
    modal = min((-count, color) for color, count in counts.items())[1]
    return _paint_neighborhood(grid, _plus_cells, lambda markers, index: modal)


SEMANTIC_RIVALS = {
    "identity": _identity,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "diagonal_x": _diagonal_x,
    "square_3x3": _square_3x3,
    "first_marker_only": _first_marker_only,
    "one_stamp_per_color": _one_stamp_per_color,
    "modal_color_plus": _modal_color_plus,
}

WITNESS_RIVALS = {
    "orthogonal_plus_rebuttal": [
        "identity",
        "horizontal_only",
        "vertical_only",
        "diagonal_x",
        "square_3x3",
    ],
    "all_markers_matter": ["first_marker_only"],
    "repeated_color_locations": ["one_stamp_per_color"],
    "mixed_marker_colors": ["modal_color_plus"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    # Every canonical scene uses distinct marker colors, so canonical data alone
    # cannot distinguish this rival from the true per-marker rule.
    "one_stamp_per_color": _one_stamp_per_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            rival_query = competitor(query["input"])
            if rival_query != query["output"]:
                reasons.append(
                    f"{name} fits every demonstration but answers the query differently"
                )
            else:
                reasons.append(
                    f"{name} survives every demonstration and the query"
                )
    return reasons
