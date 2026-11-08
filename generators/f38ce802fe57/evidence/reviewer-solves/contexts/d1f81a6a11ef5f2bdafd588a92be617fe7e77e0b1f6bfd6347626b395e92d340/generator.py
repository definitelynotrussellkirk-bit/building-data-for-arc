"""Generator for bank task M45 / f38ce802fe57.

Color-5 walls recursively partition a bordered grid into rectangular rooms.
Exactly one room contains a colored seed. The rule flood-fills only the
4-connected zero cells in that seed's room, using the seed's own color, while
all walls and unreachable rooms remain unchanged.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f38ce802fe57"
VERSION = "4.0.0"
TASK_ID = "f38ce802fe57"
RULE_HASH = "8dfb2acf65d6"

SUMMARY = (
    "Build a color-5 outer frame and a recursive guillotine partition with "
    "three through six rectangular rooms. Partial wall segments terminate in "
    "T-junctions rather than forcing a Cartesian lattice. Place one colored "
    "seed in one room; only that connected room fills with the seed color."
)

INVARIANTS = [
    "zero is background and five is the fixed wall color",
    "the outer border is solid color 5",
    "partial one-cell wall cuts recursively partition three through six rooms",
    "every non-wall room is rectangular and the wall graph has no crossings",
    "exactly one seed uses a color from 2,3,4,6,7,8",
    "the seed room contains at least one reachable zero cell",
    "at least two unreachable rooms remain zero",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_SEED_COLORS = (2, 3, 4, 6, 7, 8)
_ROOM_COUNTS = (3, 4, 5, 6)
_PROFILE_PRIOR = 0.10
_BAND_ROOM_COUNTS = {
    "easy": (3,),
    "medium": (3, 4),
    "hard": (4, 5, 6),
}
_BAND_HEIGHT = {
    "easy": (7, 12),
    "medium": (8, 20),
    "hard": (12, 30),
}
_BAND_WIDTH = {
    "easy": (8, 14),
    "medium": (8, 20),
    "hard": (12, 30),
}

AXES = {
    "room_count": {
        "type": "int",
        "default": "difficulty-aware choice",
        "valid": "3|4|5|6",
    },
    "seed_color": {
        "type": "int",
        "default": "choice from 2,3,4,6,7,8",
        "valid": "2|3|4|6|7|8",
    },
}

# Every public input. A canonical feature profile retains the complete wall
# mask and which connected room is seeded, while treating the seed's concrete
# position within that room, its color, and D4 orientation as lawful nuisance
# variation.
_PROFILE_GRIDS = (
    (
        "555555555555",
        "500005000005",
        "503005000005",
        "500005000005",
        "500005555555",
        "500005000005",
        "500005000005",
        "500005000005",
        "555555555555",
    ),
    (
        "5555555555555",
        "5000000500005",
        "5000000500005",
        "5000000555555",
        "5000000500005",
        "5000000500005",
        "5555555500005",
        "5000000500005",
        "5000000500205",
        "5555555555555",
    ),
    (
        "55555555555",
        "50050000005",
        "50050000405",
        "50050000005",
        "50050000005",
        "55555555555",
        "50000005005",
        "50000005005",
        "50000005005",
        "50000005005",
        "55555555555",
    ),
    (
        "555555555555",
        "500050005005",
        "500050005005",
        "500050005005",
        "500050005005",
        "500050005005",
        "500050005005",
        "500055555005",
        "500050605005",
        "555555555555",
    ),
    (
        "55555555555555",
        "50000050000005",
        "50000050003005",
        "50000055555555",
        "50000050000005",
        "50000050000005",
        "50000050000005",
        "55555550000005",
        "50000050000005",
        "55555555555555",
    ),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    room_count = overrides.get("room_count")
    if room_count is not None:
        if type(room_count) is not int:
            raise ValueError("room_count must be an integer")
        if room_count not in _ROOM_COUNTS:
            raise ValueError("room_count must be 3, 4, 5, or 6")
    seed_color = overrides.get("seed_color")
    if seed_color is not None:
        if type(seed_color) is not int:
            raise ValueError("seed_color must be an integer")
        if seed_color not in _SEED_COLORS:
            raise ValueError(
                "seed_color must be one of 2, 3, 4, 6, 7, or 8"
            )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _region_from(grid, start):
    height = len(grid)
    width = len(grid[0])
    region = {start}
    pending = [start]
    while pending:
        row, col = pending.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr = row + dr
            nc = col + dc
            neighbor = nr, nc
            if (
                0 <= nr < height
                and 0 <= nc < width
                and grid[nr][nc] != 5
                and neighbor not in region
            ):
                region.add(neighbor)
                pending.append(neighbor)
    return region


def _nonwall_regions(grid):
    remaining = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 5
    }
    regions = []
    while remaining:
        region = _region_from(grid, next(iter(remaining)))
        regions.append(region)
        remaining.difference_update(region)
    return tuple(regions)


def _guillotine_leaves(grid):
    height = len(grid)
    width = len(grid[0])
    memo = {}

    def visit(top, left, bottom, right):
        key = top, left, bottom, right
        if key in memo:
            return memo[key]
        if top > bottom or left > right:
            memo[key] = None
            return None
        if all(
            grid[row][col] != 5
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        ):
            memo[key] = (key,)
            return memo[key]

        row_cuts = [
            row
            for row in range(top + 1, bottom)
            if all(
                grid[row][col] == 5
                for col in range(left, right + 1)
            )
        ]
        col_cuts = [
            col
            for col in range(left + 1, right)
            if all(
                grid[row][col] == 5
                for row in range(top, bottom + 1)
            )
        ]
        for row in row_cuts:
            upper = visit(top, left, row - 1, right)
            lower = visit(row + 1, left, bottom, right)
            if upper is not None and lower is not None:
                memo[key] = upper + lower
                return memo[key]
        for col in col_cuts:
            left_leaves = visit(top, left, bottom, col - 1)
            right_leaves = visit(top, col + 1, bottom, right)
            if left_leaves is not None and right_leaves is not None:
                memo[key] = left_leaves + right_leaves
                return memo[key]
        memo[key] = None
        return None

    return visit(1, 1, height - 2, width - 2)


def _scene_analysis(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, None, ["grid must be a non-empty list or tuple"]
    if not all(
        isinstance(row, (list, tuple, str)) and row for row in grid
    ):
        return None, None, [
            "rows must be non-empty lists, tuples, or digit strings"
        ]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]
    height = len(coerced)
    errors = []
    if not 5 <= height <= 30 or not 5 <= width <= 30:
        errors.append("grid dimensions must be between 5 and 30")
    if any(
        type(value) is not int
        or value not in (0, 2, 3, 4, 5, 6, 7, 8)
        for row in coerced
        for value in row
    ):
        errors.append(
            "cells must be 0, wall color 5, or an allowed seed color"
        )
        return coerced, None, errors
    if errors:
        return coerced, None, errors

    if (
        any(value != 5 for value in coerced[0])
        or any(value != 5 for value in coerced[-1])
        or any(row[0] != 5 or row[-1] != 5 for row in coerced)
    ):
        errors.append("the full outer border must be color 5")

    seeds = tuple(
        (row, col, value)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value in _SEED_COLORS
    )
    if len(seeds) != 1:
        errors.append("the grid must contain exactly one allowed seed")

    leaves = _guillotine_leaves(coerced)
    if leaves is None:
        errors.append(
            "internal walls must form a recursive guillotine partition"
        )
        leaves = ()
    if not 3 <= len(leaves) <= 6:
        errors.append("the partition must contain three through six rooms")

    regions = _nonwall_regions(coerced)
    if len(regions) != len(leaves):
        errors.append(
            "guillotine leaves and connected non-wall rooms must agree"
        )
    for region in regions:
        top = min(row for row, _col in region)
        bottom = max(row for row, _col in region)
        left = min(col for _row, col in region)
        right = max(col for _row, col in region)
        if len(region) != (bottom - top + 1) * (right - left + 1):
            errors.append("every connected room must be rectangular")
            break

    full_rows = frozenset(
        row
        for row, values in enumerate(coerced)
        if all(value == 5 for value in values)
    )
    full_cols = frozenset(
        col
        for col in range(width)
        if all(coerced[row][col] == 5 for row in range(height))
    )
    residual_walls = tuple(
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if (
            coerced[row][col] == 5
            and row not in full_rows
            and col not in full_cols
        )
    )
    if not residual_walls:
        errors.append(
            "at least one partial wall segment must create a T-junction"
        )

    wall_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if coerced[row][col] == 5
    }
    wall_degrees = tuple(
        sum(
            (row + dr, col + dc) in wall_cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
        for row, col in wall_cells
    )
    if any(degree not in (2, 3) for degree in wall_degrees):
        errors.append(
            "wall graph must use lines and T-junctions without crossings"
        )

    seed_region = None
    if len(seeds) == 1:
        seed_position = seeds[0][0], seeds[0][1]
        seed_region = next(
            (
                region
                for region in regions
                if seed_position in region
            ),
            None,
        )
        if seed_region is None or len(seed_region) < 2:
            errors.append(
                "the seed room must contain a reachable zero cell"
            )
    if errors:
        return coerced, None, errors

    return coerced, {
        "height": height,
        "width": width,
        "seed": seeds[0],
        "seed_color": seeds[0][2],
        "seed_region": frozenset(seed_region),
        "regions": tuple(frozenset(region) for region in regions),
        "room_count": len(regions),
        "leaves": tuple(sorted(leaves)),
        "full_rows": full_rows,
        "full_cols": full_cols,
        "residual_walls": residual_walls,
        "t_junctions": sum(degree == 3 for degree in wall_degrees),
    }, []


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "room_count": features["room_count"],
        "seed_color": features["seed_color"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    output = [row[:] for row in coerced]
    color = features["seed_color"]
    for row, col in features["seed_region"]:
        if output[row][col] == 0:
            output[row][col] = color
    return output


def _rotate_90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _reflect(grid):
    return [row[::-1] for row in grid]


def _d4_grids(grid):
    current = _coerce_grid(grid)
    variants = []
    for _turn in range(4):
        variants.append([row[:] for row in current])
        variants.append(_reflect(current))
        current = _rotate_90(current)
    return tuple(variants)


def _profile_feature(grid):
    coerced = _coerce_grid(grid)
    seeds = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value in _SEED_COLORS
    ]
    if len(seeds) != 1:
        return None
    seed_region = _region_from(coerced, seeds[0])
    return tuple(
        tuple(
            5
            if value == 5
            else 1
            if (row, col) in seed_region
            else 0
            for col, value in enumerate(values)
        )
        for row, values in enumerate(coerced)
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_feature(variant)
    for source in _PROFILE_GRIDS
    for variant in _d4_grids(source)
)
_PROFILE_SIGNATURE_TO_INDEX = {
    _profile_feature(variant): index
    for index, source in enumerate(_PROFILE_GRIDS)
    for variant in _d4_grids(source)
}


def canonical_profile_signature(grid):
    signature = _profile_feature(grid)
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def canonical_profile_index(grid):
    return _PROFILE_SIGNATURE_TO_INDEX.get(_profile_feature(grid))


def _draw_profile(source, rng):
    grid = [row[:] for row in rng.choice(_d4_grids(source))]
    seeds = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in _SEED_COLORS
    ]
    if len(seeds) != 1:
        raise AssertionError("embedded profile must have exactly one seed")
    seed_region = tuple(sorted(_region_from(grid, seeds[0])))
    grid[seeds[0][0]][seeds[0][1]] = 0
    row, col = rng.choice(seed_region)
    grid[row][col] = rng.choice(_SEED_COLORS)
    if canonical_profile_signature(grid) is None:
        raise AssertionError("constructed public profile drifted")
    return grid


def _cut_would_cross(grid, room, axis, position):
    top, left, bottom, right = room
    if axis == "horizontal":
        before = (
            left - 2 >= 0
            and grid[position][left - 2] == 5
        )
        after = (
            right + 2 < len(grid[0])
            and grid[position][right + 2] == 5
        )
    else:
        before = (
            top - 2 >= 0
            and grid[top - 2][position] == 5
        )
        after = (
            bottom + 2 < len(grid)
            and grid[bottom + 2][position] == 5
        )
    return before or after


def _cut_candidates(grid, rooms, axes):
    preferred = []
    fallback = []
    for index, room in enumerate(rooms):
        top, left, bottom, right = room
        if "horizontal" in axes:
            for row in range(top + 1, bottom):
                if _cut_would_cross(
                    grid,
                    room,
                    "horizontal",
                    row,
                ):
                    continue
                entry = index, "horizontal", row
                fallback.append(entry)
                if row - top >= 2 and bottom - row >= 2:
                    preferred.append(entry)
        if "vertical" in axes:
            for col in range(left + 1, right):
                if _cut_would_cross(
                    grid,
                    room,
                    "vertical",
                    col,
                ):
                    continue
                entry = index, "vertical", col
                fallback.append(entry)
                if col - left >= 2 and right - col >= 2:
                    preferred.append(entry)
    return preferred or fallback


def _apply_cut(grid, rooms, candidate):
    index, axis, position = candidate
    top, left, bottom, right = rooms.pop(index)
    if axis == "horizontal":
        for col in range(left, right + 1):
            grid[position][col] = 5
        rooms.extend((
            (top, left, position - 1, right),
            (position + 1, left, bottom, right),
        ))
    else:
        for row in range(top, bottom + 1):
            grid[row][position] = 5
        rooms.extend((
            (top, left, bottom, position - 1),
            (top, position + 1, bottom, right),
        ))


def _partition_grid(rng, height, width, room_count):
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 5
        grid[row][-1] = 5
    for col in range(width):
        grid[0][col] = 5
        grid[-1][col] = 5
    rooms = [(1, 1, height - 2, width - 2)]

    root_axes = []
    if height - 2 >= 5:
        root_axes.append("horizontal")
    if width - 2 >= 5:
        root_axes.append("vertical")
    if not root_axes:
        return None
    root_axis = rng.choice(root_axes)
    candidates = _cut_candidates(grid, rooms, (root_axis,))
    if not candidates:
        return None
    _apply_cut(grid, rooms, rng.choice(candidates))

    opposite = (
        "vertical"
        if root_axis == "horizontal"
        else "horizontal"
    )
    candidates = _cut_candidates(grid, rooms, (opposite,))
    if not candidates:
        return None
    _apply_cut(grid, rooms, rng.choice(candidates))

    while len(rooms) < room_count:
        axes = (
            ("horizontal", "vertical")
            if rng.random() < 0.5
            else ("vertical", "horizontal")
        )
        candidates = _cut_candidates(grid, rooms, axes)
        if not candidates:
            return None
        _apply_cut(grid, rooms, rng.choice(candidates))
    return grid, tuple(rooms)


def _draw_general(ctx, band, overrides):
    room_options = (
        _ROOM_COUNTS
        if overrides.get("room_count") is not None
        else _BAND_ROOM_COUNTS[band]
    )
    room_count = ctx.draw_choice("room_count", room_options)
    seed_color = ctx.draw_choice("seed_color", _SEED_COLORS)
    rng = ctx.draw_rng("layout")

    height_low, height_high = _BAND_HEIGHT[band]
    width_low, width_high = _BAND_WIDTH[band]
    height_low = max(height_low, room_count + 3)
    width_low = max(width_low, room_count + 3)
    for _attempt in range(100):
        height = rng.randint(height_low, height_high)
        width = rng.randint(width_low, width_high)
        partition = _partition_grid(
            rng,
            height,
            width,
            room_count,
        )
        if partition is None:
            continue
        grid, rooms = partition
        seed_rooms = [
            room
            for room in rooms
            if (
                (room[2] - room[0] + 1)
                * (room[3] - room[1] + 1)
            ) >= 2
        ]
        if not seed_rooms:
            continue
        top, left, bottom, right = rng.choice(seed_rooms)
        row = rng.randint(top, bottom)
        col = rng.randint(left, right)
        grid[row][col] = seed_color
        if not self_check(grid):
            return grid
    raise AssertionError("failed to construct a valid room partition")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_GRIDS))),
            )

    if profile_index is not None:
        grid = _draw_profile(
            _PROFILE_GRIDS[profile_index],
            ctx.draw_rng("profile_layout"),
        )
        _coerced, features, errors = _scene_analysis(grid)
        if errors:
            raise AssertionError(
                "generated invalid profile: " + "; ".join(errors)
            )
        ctx.draw_choice("room_count", (features["room_count"],))
        ctx.draw_choice("seed_color", (features["seed_color"],))
    else:
        grid = _draw_general(ctx, band, overrides)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
