"""Deterministic two-stage parametric family for ARC task 0d27a69b5a98.

The canonical setting completes every colored cell across the full color-9
axis.  The composed setting then chooses the unique most frequent non-axis
color in that completed intermediate and recolors all of it to color 8.
"""
from __future__ import annotations

from hashlib import sha256
from math import ceil, sqrt
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "0d27a69b5a98"
MODES = ("canonical", "largest_completed_color_highlight")
AXIS_COLOR = 9
HIGHLIGHT_COLOR = 8
PARAMETRIC_DIR = Path(__file__).resolve().parent

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]

DEMO_SIZES = ((15, 17), (17, 19), (19, 21), (21, 23), (23, 25), (25, 27))
QUERY_SIZES = ((17, 21), (19, 25), (27, 29), (30, 30))

# (role name, placement mode, input count).  Bilateral counts are split evenly
# across both sides; one-sided counts are doubled by the canonical reflection.
PROFILES: tuple[tuple[tuple[str, str, int], ...], ...] = (
    (
        ("growth", "one_sided", 7),
        ("static_1", "bilateral", 10),
        ("small_one", "one_sided", 3),
        ("small_bilateral", "bilateral", 4),
    ),
    (
        ("growth", "one_sided", 9),
        ("static_1", "bilateral", 14),
        ("static_2", "bilateral", 12),
        ("small_one", "one_sided", 4),
        ("small_bilateral", "bilateral", 6),
    ),
    (
        ("growth", "one_sided", 11),
        ("static_1", "bilateral", 18),
        ("static_2", "bilateral", 16),
        ("static_3", "bilateral", 14),
        ("small_one", "one_sided", 5),
        ("small_bilateral", "bilateral", 8),
    ),
)
STRESS_PROFILE = (
    ("growth", "one_sided", 24),
    ("static_1", "bilateral", 36),
    ("static_2", "bilateral", 34),
    ("static_3", "bilateral", 32),
    ("small_one", "one_sided", 10),
    ("small_bilateral", "bilateral", 16),
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_settings(settings: Any) -> dict[str, str]:
    if not isinstance(settings, dict) or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly the key 'mode'")
    mode = settings["mode"]
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return {"mode": mode}


def _validate_request(seed: Any, demos: Any, queries: Any) -> tuple[int, int, int]:
    return (
        _strict_int("seed", seed, 0, 2**63 - 1),
        _strict_int("demos", demos, 2, 6),
        _strict_int("queries", queries, 1, 4),
    )


def _normalise(cells: Iterable[Cell]) -> Shape:
    points = tuple(cells)
    if not points:
        return ()
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _shape_bounds(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _compact_shape(size: int) -> Shape:
    width = ceil(sqrt(size))
    return _normalise((index // width, index % width) for index in range(size))


def _rotate(shape: Shape) -> Shape:
    height, _ = _shape_bounds(shape)
    return _normalise((c, height - 1 - r) for r, c in shape)


def _flip(shape: Shape) -> Shape:
    _, width = _shape_bounds(shape)
    return _normalise((r, width - 1 - c) for r, c in shape)


def _transform(shape: Shape, code: int) -> Shape:
    out = shape
    if code >= 4:
        out = _flip(out)
    for _ in range(code % 4):
        out = _rotate(out)
    return _normalise(out)


def _axis(grid: Grid) -> tuple[str, int]:
    height = len(grid)
    width = len(grid[0])
    full_columns = [
        c for c in range(width) if all(grid[r][c] == AXIS_COLOR for r in range(height))
    ]
    full_rows = [
        r for r in range(height) if all(grid[r][c] == AXIS_COLOR for c in range(width))
    ]
    if len(full_columns) == 1 and not full_rows:
        return "vertical", full_columns[0]
    if len(full_rows) == 1 and not full_columns:
        return "horizontal", full_rows[0]
    raise ValueError("grid must contain exactly one full color-9 row or column")


def _canonical(grid: Grid) -> Grid:
    orientation, axis = _axis(grid)
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, AXIS_COLOR):
                continue
            if orientation == "vertical":
                rr, cc = r, 2 * axis - c
            else:
                rr, cc = 2 * axis - r, c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value
    return out


def _counts(grid: Grid) -> dict[int, int]:
    counts: dict[int, int] = {}
    for row in grid:
        for value in row:
            if value not in (0, AXIS_COLOR, HIGHLIGHT_COLOR):
                counts[value] = counts.get(value, 0) + 1
    return counts


def _winner(counts: dict[int, int]) -> int:
    if not counts:
        raise ValueError("grid contains no candidate colors")
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    if len(ranked) > 1 and counts[ranked[0]] == counts[ranked[1]]:
        raise ValueError("candidate color winner is not unique")
    return ranked[0]


def _paint_color(grid: Grid, source_color: int, target_color: int) -> Grid:
    return [
        [target_color if value == source_color else value for value in row]
        for row in grid
    ]


def solve(grid: Grid, mode: str) -> Grid:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    intermediate = _canonical(grid)
    if mode == "canonical":
        return intermediate
    selected = _winner(_counts(intermediate))
    return _paint_color(intermediate, selected, HIGHLIGHT_COLOR)


def solve_wrong_order(grid: Grid) -> Grid:
    selected = _winner(_counts(grid))
    return _paint_color(_canonical(grid), selected, HIGHLIGHT_COLOR)


def solve_fixed_color(grid: Grid, color: int) -> Grid:
    return _paint_color(_canonical(grid), color, HIGHLIGHT_COLOR)


def solve_fixed_original_rank(grid: Grid, rank: int) -> Grid:
    counts = _counts(grid)
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    if not 1 <= rank <= len(ranked):
        return _canonical(grid)
    return _paint_color(_canonical(grid), ranked[rank - 1], HIGHLIGHT_COLOR)


def trace(grid: Grid) -> dict[str, Any]:
    orientation, axis = _axis(grid)
    pre_counts = _counts(grid)
    intermediate = _canonical(grid)
    post_counts = _counts(intermediate)
    pre_winner = _winner(pre_counts)
    post_winner = _winner(post_counts)
    original_ranked = sorted(pre_counts, key=lambda color: (-pre_counts[color], color))
    return {
        "axis_orientation": orientation,
        "axis_index": axis,
        "axis_cells": len(grid) if orientation == "vertical" else len(grid[0]),
        "intermediate": intermediate,
        "pre_counts": pre_counts,
        "post_counts": post_counts,
        "pre_winner_color": pre_winner,
        "post_winner_color": post_winner,
        "post_winner_original_rank": original_ranked.index(post_winner) + 1,
        "pre_winner_count": pre_counts[pre_winner],
        "post_winner_count": post_counts[post_winner],
        "color_count": len(pre_counts),
        "non_axis_foreground": sum(pre_counts.values()),
        "completed_non_axis_foreground": sum(post_counts.values()),
    }


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = sha256(f"{TASK_ID}:{seed}:{split}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _buffered_conflict(cells: set[Cell], occupied: set[Cell]) -> bool:
    for r, c in cells:
        if (r, c) in occupied:
            return True
        if any(
            neighbour in occupied
            for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            return True
    return False


def _place_roles(
    side_height: int,
    side_width: int,
    profile: tuple[tuple[str, str, int], ...],
    rng: random.Random,
) -> dict[str, set[Cell]]:
    items = []
    for name, placement, input_count in profile:
        base_size = input_count if placement == "one_sided" else input_count // 2
        variants = [_transform(_compact_shape(base_size), code) for code in range(8)]
        variants = list(dict.fromkeys(variants))
        rng.shuffle(variants)
        items.append((name, base_size, variants))
    items.sort(key=lambda item: -item[1])

    def search(position: int, occupied: set[Cell], placed: dict[str, set[Cell]]):
        if position == len(items):
            return placed
        name, _, variants = items[position]
        for shape in variants:
            shape_height, shape_width = _shape_bounds(shape)
            if shape_height > side_height or shape_width > side_width:
                continue
            anchors = [
                (r, c)
                for r in range(side_height - shape_height + 1)
                for c in range(side_width - shape_width + 1)
            ]
            rng.shuffle(anchors)
            for anchor_r, anchor_c in anchors:
                absolute = {(anchor_r + r, anchor_c + c) for r, c in shape}
                if _buffered_conflict(absolute, occupied):
                    continue
                answer = search(
                    position + 1,
                    occupied | absolute,
                    {**placed, name: absolute},
                )
                if answer is not None:
                    return answer
        return None

    answer = search(0, set(), {})
    if answer is None:
        raise RuntimeError(
            f"could not place {len(profile)} role footprints in {side_height}x{side_width}"
        )
    return answer


def _profile_for(split: str, index: int):
    if split == "train":
        if not 0 <= index < len(DEMO_SIZES):
            raise ValueError("train profile index out of range")
        return DEMO_SIZES[index], PROFILES[index % len(PROFILES)]
    if split == "test":
        if not 0 <= index < len(QUERY_SIZES):
            raise ValueError("test profile index out of range")
        profile = STRESS_PROFILE if index == 3 else PROFILES[(index + 1) % len(PROFILES)]
        return QUERY_SIZES[index], profile
    raise ValueError("split must be 'train' or 'test'")


def sample_input(seed: int, split: str, index: int) -> Grid:
    (height, width), profile = _profile_for(split, index)
    orientation = "vertical" if (index + (0 if split == "train" else 1)) % 2 == 0 else "horizontal"
    axis = width // 2 if orientation == "vertical" else height // 2
    if orientation == "vertical":
        primary_positions = [
            c for c in range(axis) if 0 <= 2 * axis - c < width
        ]
        side_height, side_width = height, len(primary_positions)
    else:
        primary_positions = [
            r for r in range(axis) if 0 <= 2 * axis - r < height
        ]
        side_height, side_width = len(primary_positions), width

    rng = _rng(seed, split, index)
    local_placements = _place_roles(side_height, side_width, profile, rng)
    colors = list(range(1, len(profile) + 1))
    rng.shuffle(colors)
    color_by_role = {
        role[0]: color for role, color in zip(profile, colors)
    }
    grid = [[0 for _ in range(width)] for _ in range(height)]
    if orientation == "vertical":
        for r in range(height):
            grid[r][axis] = AXIS_COLOR
    else:
        for c in range(width):
            grid[axis][c] = AXIS_COLOR

    def to_primary(local: Cell) -> Cell:
        r, c = local
        if orientation == "vertical":
            return r, primary_positions[c]
        return primary_positions[r], c

    def mirror(cell: Cell) -> Cell:
        r, c = cell
        if orientation == "vertical":
            return r, 2 * axis - c
        return 2 * axis - r, c

    role_metadata = {}
    for ordinal, (name, placement, input_count) in enumerate(profile):
        primary_cells = {to_primary(cell) for cell in local_placements[name]}
        mirrored_cells = {mirror(cell) for cell in primary_cells}
        color = color_by_role[name]
        if placement == "bilateral":
            source_cells = primary_cells | mirrored_cells
            source_side = "bilateral"
        else:
            use_primary = (rng.randrange(2) + ordinal + seed + index) % 2 == 0
            source_cells = primary_cells if use_primary else mirrored_cells
            source_side = "primary" if use_primary else "secondary"
        if len(source_cells) != input_count:
            raise AssertionError(f"role {name} count drifted")
        for r, c in source_cells:
            if grid[r][c] != 0:
                raise AssertionError("role placement collision")
            grid[r][c] = color
        role_metadata[color] = (name, placement, source_side)

    details = trace(grid)
    growth_color = color_by_role["growth"]
    if details["post_winner_color"] != growth_color:
        raise AssertionError("growth role did not become the completed winner")
    if details["pre_winner_color"] == growth_color:
        raise AssertionError("growth role was already the original winner")
    if details["pre_winner_color"] == details["post_winner_color"]:
        raise AssertionError("profile failed to force a pre/post winner swap")
    return grid


def rule_text(mode: str) -> str:
    if mode == "canonical":
        name = "canonical.rkt"
    elif mode == "largest_completed_color_highlight":
        name = "largest_completed_color_highlight.rkt"
    else:
        raise ValueError(f"mode must be one of {MODES}")
    return (PARAMETRIC_DIR / name).read_text(encoding="utf-8")


def generate_episode(seed: Any, mode: str, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    seed, demos, queries = _validate_request(seed, demos, queries)
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    train = []
    test = []
    for index in range(demos):
        grid = sample_input(seed, "train", index)
        train.append({"input": grid, "output": solve(grid, mode)})
    for index in range(queries):
        grid = sample_input(seed, "test", index)
        test.append({"input": grid, "output": solve(grid, mode)})
    return {"train": train, "test": test, "program_solution": rule_text(mode)}
