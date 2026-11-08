"""Generator for 058ae70e4bdb — flood single-color wall compartments.

Color 8 is a wall.  Treat every 4-connected component of non-8 cells as a
compartment.  If the distinct non-{0,8} colors in a compartment form exactly
one color, flood the whole compartment with that color.  Empty compartments
and compartments containing two colors stay unchanged.

The ordinary three-example schedule is deliberately semantic rather than
purely random.  Its first profile alone shows both a same-color marker pair
(which still fills) and a two-color compartment (which stays); the other two
profiles show a punched-wall non-rectangle with either one or two colors.
Thus every consecutive three-example lesson refutes the canonical shortcuts
"exactly one marker", "fill every nonempty room", and "colors are globally
unique", while also exercising non-rectangular connected regions.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "058ae70e4bdb"
TASK_ID = "058ae70e4bdb"
VERSION = "3.0.0"
RULE_HASH = "f3ddcec3d159"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SCENE_PROFILES = (
    "canonical_mix",
    "all_fill",
    "same_color_pair",
    "two_color_stay",
    "merged_single_color",
    "merged_two_color",
)
SCHEDULE_PROFILES = (
    "same_color_pair",
    "merged_two_color",
    "merged_single_color",
)

SUMMARY = (
    "Canonical-size color-8 wall lattices contain empty, one-color, repeated-"
    "marker, and two-color regions.  A deterministic three-profile teaching "
    "cycle additionally punches one wall so a non-rectangular merged region "
    "must be judged by its combined palette, not by marker count or shape."
)

INVARIANTS = [
    "the complete outer border is color 8",
    "there are 4..9 non-wall regions and at most one is non-rectangular",
    "each region contains zero cells and at most two non-wall markers",
    "a one-color region fills even with two equal markers or a non-rectangular shape",
    "an empty or two-color region stays unchanged",
    "every ordinary draw changes under the canonical rule",
]

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "sample_index schedule: same_color_pair|merged_two_color|merged_single_color",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Exact observable semantic scene profile.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

# Exact (height, width, total palette size) profiles present in the five
# authoritative inputs.  Every difficulty band cycles through all five.
_CANONICAL_PROFILES = (
    (9, 11, 5),
    (10, 12, 5),
    (9, 13, 5),
    (11, 11, 6),
    (10, 14, 5),
)
_BAND_PROFILE_OFFSET = {None: 3, "easy": 0, "medium": 1, "hard": 2}
_SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the replayable ordinary teaching profile.

    Seed and difficulty vary layout, colors, and canonical morphology, but not
    the three-example semantic order.  Consequently every consecutive three
    sample indices contain the full teaching cycle.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _split_span(rng, span: int, count: int) -> list[tuple[int, int]]:
    """Split an interior span into `count` >=2-wide bands and 1-wide walls."""
    minimum = 2 * count + (count - 1)
    if span < minimum:
        raise ValueError(f"span {span} is too small for {count} compartments")
    widths = [2] * count
    for _ in range(span - minimum):
        widths[rng.randrange(count)] += 1
    bands: list[tuple[int, int]] = []
    position = 1
    for width in widths:
        bands.append((position, position + width - 1))
        position += width + 1
    return bands


def _room_cells(room: tuple[int, int, int, int]) -> list[tuple[int, int]]:
    r0, c0, r1, c1 = room
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def _paint_markers(
    grid: list[list[int]],
    room: tuple[int, int, int, int],
    colors: tuple[int, ...],
    rng,
) -> None:
    cells = _room_cells(room)
    if len(cells) < len(colors):
        raise ValueError("room is too small for requested markers")
    rng.shuffle(cells)
    for (r, c), color in zip(cells, colors):
        grid[r][c] = color


def _profile_assignments(profile: str, colors: tuple[int, ...]) -> list[tuple[int, ...]]:
    """Six room marker-tuples before optional wall merging.

    The `same_color_pair` scene intentionally bundles the three canonical
    shortcut counterexamples: an equal-color pair, a two-color keeper, and a
    color repeated in another region.  That makes query rotation safe even
    when one of the other two scheduled profiles is held out.
    """
    a, b, c, *rest = colors
    d = rest[0] if rest else None
    if profile == "canonical_mix":
        assignments = [(a,), (b,), (c,)]
        if d is not None:
            assignments.append((d,))
            assignments.extend([(a,), ()])
        else:
            assignments.extend([(a,), (), ()])
    elif profile == "all_fill":
        cycle = list(colors)
        assignments = [(cycle[i % len(cycle)],) for i in range(6)]
    elif profile == "same_color_pair":
        assignments = [(a, a), (b, c), (a,), (b,), (c,), ()]
        if d is not None:
            assignments[4] = (d,)
    elif profile == "two_color_stay":
        singles = list(colors[2:]) + [a, b, c, a]
        assignments = [(a, b)] + [(color,) for color in singles[:5]]
    elif profile == "merged_single_color":
        # Rooms 0 and 3 are merged later; equal markers in the two lobes show
        # that marker count and rectangularity are both irrelevant.
        tail = list(colors[1:]) + [a, b, c, a]
        assignments = [(a,)] + [(color,) for color in tail[:2]] + [(a,)]
        assignments += [(color,) for color in tail[2:4]]
    elif profile == "merged_two_color":
        # Rooms 0 and 3 are merged later and carry different colors, so the
        # connected union stays unchanged while other one-color rooms fill.
        tail = list(colors[2:]) + [a, c, b, a]
        assignments = [(a,)] + [(color,) for color in tail[:2]] + [(b,)]
        assignments += [(color,) for color in tail[2:4]]
    else:  # guarded by draw_choice, retained as a loud defensive check
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if len(assignments) != 6:
        raise RuntimeError(f"profile {profile!r} produced {len(assignments)} room assignments")
    return assignments


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides,
) -> list[list[int]]:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    if difficulty not in _BAND_PROFILE_OFFSET:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    options = SCENE_PROFILES if "scene_profile" in overrides else (scheduled,)
    profile = ctx.draw_choice("scene_profile", options)
    rng = ctx.draw_rng(f"layout:{difficulty or 'default'}")

    offset = _BAND_PROFILE_OFFSET[difficulty]
    h, w, palette_size = _CANONICAL_PROFILES[(sample_index + offset) % len(_CANONICAL_PROFILES)]
    row_bands = _split_span(rng, h - 2, 2)
    col_bands = _split_span(rng, w - 2, 3)

    grid = full_grid(h, w, 8)
    rooms: list[tuple[int, int, int, int]] = []
    for r0, r1 in row_bands:
        for c0, c1 in col_bands:
            room = (r0, c0, r1, c1)
            rooms.append(room)
            for r, c in _room_cells(room):
                grid[r][c] = 0

    colors = tuple(rng.sample(_SEED_COLORS, palette_size - 2))
    assignments = _profile_assignments(profile, colors)

    # Randomly permute columns and swap the two row bands.  For merged profiles
    # the assignments at logical positions 0 and 3 remain vertically adjacent.
    column_order = list(range(3))
    rng.shuffle(column_order)
    row_order = [0, 1]
    if rng.randrange(2):
        row_order.reverse()
    physical_rooms = [rooms[row_order[r] * 3 + column_order[c]] for r in range(2) for c in range(3)]

    for room, marker_colors in zip(physical_rooms, assignments):
        _paint_markers(grid, room, marker_colors, rng)

    if profile in {"merged_single_color", "merged_two_color"}:
        top = physical_rooms[0]
        bottom = physical_rooms[3]
        upper, lower = sorted((top, bottom), key=lambda room: room[0])
        wall_row = upper[2] + 1
        if wall_row != lower[0] - 1:
            raise RuntimeError("selected rooms are not separated by a one-cell horizontal wall")
        c0 = max(upper[1], lower[1])
        c1 = min(upper[3], lower[3])
        grid[wall_row][rng.randint(c0, c1)] = 0

    meta = {"scene_profile": profile}
    errors = self_check(grid, difficulty=difficulty, meta=meta)
    if errors:
        raise ValueError(f"generated invalid {profile!r} scene: {errors}")
    observed = observe_overrides(grid)
    if observed != meta:
        raise ValueError(f"scene_profile not recoverable: requested={meta}, observed={observed}")
    return grid


def _regions(grid: list[list[int]]) -> list[dict[str, Any]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    regions: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 8 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIR4:
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < h
                        and 0 <= cc < w
                        and grid[rr][cc] != 8
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            cells.sort()
            markers = tuple((r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 8))
            colors = Counter(color for _, _, color in markers)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            rectangular = len(cells) == (
                (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
            )
            regions.append(
                {
                    "cells": tuple(cells),
                    "markers": markers,
                    "colors": colors,
                    "marker_count": len(markers),
                    "zeros": sum(grid[r][c] == 0 for r, c in cells),
                    "rectangular": rectangular,
                }
            )
    return regions


def _has_same_color_pair(grid: list[list[int]]) -> bool:
    return any(len(region["colors"]) == 1 and region["marker_count"] == 2 for region in _regions(grid))


def _has_two_color_region(grid: list[list[int]]) -> bool:
    return any(len(region["colors"]) == 2 for region in _regions(grid))


def _has_nonrect_single_color(grid: list[list[int]]) -> bool:
    return any(not region["rectangular"] and len(region["colors"]) == 1 for region in _regions(grid))


def _has_nonrect_two_color(grid: list[list[int]]) -> bool:
    return any(not region["rectangular"] and len(region["colors"]) == 2 for region in _regions(grid))


def _has_empty_region(grid: list[list[int]]) -> bool:
    return any(not region["colors"] for region in _regions(grid))


def _has_repeated_color_across_regions(grid: list[list[int]]) -> bool:
    counts: Counter[int] = Counter()
    for region in _regions(grid):
        counts.update(region["colors"].keys())
    return any(count >= 2 for count in counts.values())


def _all_regions_rectangular(grid: list[list[int]]) -> bool:
    regions = _regions(grid)
    return bool(regions) and all(region["rectangular"] for region in regions)


def _all_singleton_filled_rooms(grid: list[list[int]]) -> bool:
    regions = _regions(grid)
    return bool(regions) and all(len(region["colors"]) == 1 and region["marker_count"] == 1 for region in regions)


def observe_overrides(grid: list[list[int]]) -> dict[str, str]:
    regions = _regions(grid)
    nonrect = [region for region in regions if not region["rectangular"]]
    if nonrect:
        if len(nonrect) != 1:
            raise ValueError(f"expected at most one non-rectangular region, got {len(nonrect)}")
        color_count = len(nonrect[0]["colors"])
        if color_count == 1:
            return {"scene_profile": "merged_single_color"}
        if color_count == 2:
            return {"scene_profile": "merged_two_color"}
        raise ValueError(f"unrecognized non-rectangular region palette size: {color_count}")
    if _has_same_color_pair(grid):
        return {"scene_profile": "same_color_pair"}
    if _has_two_color_region(grid):
        return {"scene_profile": "two_color_stay"}
    if _all_singleton_filled_rooms(grid):
        return {"scene_profile": "all_fill"}
    if _all_regions_rectangular(grid) and _has_empty_region(grid):
        if all(region["marker_count"] <= 1 for region in regions):
            return {"scene_profile": "canonical_mix"}
    raise ValueError("grid does not realize a declared scene_profile")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9"]

    errors: list[str] = []
    h, w = len(grid), width
    if any(grid[0][c] != 8 or grid[h - 1][c] != 8 for c in range(w)) or any(
        grid[r][0] != 8 or grid[r][w - 1] != 8 for r in range(h)
    ):
        errors.append("complete outer border must be color 8")

    regions = _regions(grid)
    if not 4 <= len(regions) <= 9:
        errors.append(f"expected 4..9 non-wall regions, got {len(regions)}")
    if sum(not region["rectangular"] for region in regions) > 1:
        errors.append("at most one region may be non-rectangular")
    for index, region in enumerate(regions):
        if region["zeros"] == 0:
            errors.append(f"region {index} must contain at least one zero cell")
        if region["marker_count"] > 2:
            errors.append(f"region {index} has more than two marker cells")
        if len(region["colors"]) > 2:
            errors.append(f"region {index} has more than two distinct marker colors")

    seed_colors = {value for row in grid for value in row if value not in (0, 8)}
    if not 3 <= len(seed_colors) <= 4:
        errors.append(f"expected 3..4 distinct seed colors, got {len(seed_colors)}")
    if regions and not any(len(region["colors"]) == 1 for region in regions):
        errors.append("at least one single-color region must make the rule non-identity")

    try:
        observed = observe_overrides(grid)
    except Exception as exc:
        errors.append(f"scene_profile is not observable: {exc}")
    else:
        if meta and "scene_profile" in meta and observed.get("scene_profile") != meta["scene_profile"]:
            errors.append(
                f"scene_profile mismatch: expected {meta['scene_profile']!r}, "
                f"observed {observed.get('scene_profile')!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"shape/palette profile {profile} is not one of the five canonical profiles")
    return reasons


def _fill_regions(
    grid: list[list[int]],
    predicate: Callable[[dict[str, Any]], bool],
    choose_color: Callable[[dict[str, Any]], int],
) -> list[list[int]]:
    output = deepcopy(grid)
    for region in _regions(grid):
        if not predicate(region):
            continue
        color = choose_color(region)
        for r, c in region["cells"]:
            output[r][c] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; the selected Racket rule is authority."""
    return _fill_regions(
        grid,
        lambda region: len(region["colors"]) == 1,
        lambda region: next(iter(region["colors"])),
    )


def _rival_exactly_one_marker(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: fill only regions containing exactly one marker cell."""
    return _fill_regions(
        grid,
        lambda region: region["marker_count"] == 1,
        lambda region: region["markers"][0][2],
    )


def _rival_fill_every_nonempty(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: fill every marked region using its row-major first marker."""
    return _fill_regions(
        grid,
        lambda region: region["marker_count"] > 0,
        lambda region: region["markers"][0][2],
    )


def _rival_unique_color_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: a one-color room fills only when that color occurs in one room."""
    occurrences: Counter[int] = Counter()
    regions = _regions(grid)
    for region in regions:
        occurrences.update(region["colors"].keys())
    output = deepcopy(grid)
    for region in regions:
        if len(region["colors"]) != 1:
            continue
        color = next(iter(region["colors"]))
        if occurrences[color] != 1:
            continue
        for r, c in region["cells"]:
            output[r][c] = color
    return output


def _rival_rectangular_singleton_only(grid: list[list[int]]) -> list[list[int]]:
    """Wrong: only rectangular rooms with one marker may fill."""
    return _fill_regions(
        grid,
        lambda region: region["rectangular"] and region["marker_count"] == 1,
        lambda region: region["markers"][0][2],
    )


SEMANTIC_RIVALS = {
    "exactly_one_marker": _rival_exactly_one_marker,
    "fill_every_nonempty_region": _rival_fill_every_nonempty,
    "globally_unique_color_only": _rival_unique_color_only,
    "rectangular_singleton_only": _rival_rectangular_singleton_only,
}
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "exactly_one_marker",
        "fill_every_nonempty_region",
        "globally_unique_color_only",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "same_color_pair_fills": _has_same_color_pair,
    "two_color_region_stays": _has_two_color_region,
    "nonrect_single_color_fills": _has_nonrect_single_color,
    "color_repeated_across_regions": _has_repeated_color_across_regions,
}
WITNESS_RIVALS = {
    "same_color_pair_fills": ["exactly_one_marker", "rectangular_singleton_only"],
    "two_color_region_stays": ["fill_every_nonempty_region"],
    "nonrect_single_color_fills": ["rectangular_singleton_only"],
    "color_repeated_across_regions": ["globally_unique_color_only"],
}

PROFILE_WITNESSES = {
    "canonical_mix": {
        "all_regions_rectangular": _all_regions_rectangular,
        "has_empty_region": _has_empty_region,
        "at_most_one_marker_per_region": lambda grid: all(
            region["marker_count"] <= 1 for region in _regions(grid)
        ),
    },
    "all_fill": {
        "all_regions_are_singleton_marked": _all_singleton_filled_rooms,
    },
    "same_color_pair": {
        "all_regions_rectangular": _all_regions_rectangular,
        "has_same_color_pair": _has_same_color_pair,
    },
    "two_color_stay": {
        "all_regions_rectangular": _all_regions_rectangular,
        "has_two_color_region": _has_two_color_region,
    },
    "merged_single_color": {
        "exactly_one_nonrect": lambda grid: sum(
            not region["rectangular"] for region in _regions(grid)
        ) == 1,
        "nonrect_has_one_color": _has_nonrect_single_color,
    },
    "merged_two_color": {
        "exactly_one_nonrect": lambda grid: sum(
            not region["rectangular"] for region in _regions(grid)
        ) == 1,
        "nonrect_has_two_colors": _has_nonrect_two_color,
    },
}


def lesson_identifiable(demos, query) -> list[str]:
    del query
    survivors = [
        name
        for name, competitor in LESSON_COMPETITORS.items()
        if all(competitor(pair["input"]) == pair["output"] for pair in demos)
    ]
    if survivors:
        return [f"plausible rival(s) survive every demonstration: {', '.join(sorted(survivors))}"]
    return []
