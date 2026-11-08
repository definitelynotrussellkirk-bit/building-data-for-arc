"""Generator for task 3ffc7ef20035 — fill the blue cells' bounding box.

The input contains one sparse, 8-connected blue (1) object and one separate
non-blue distractor.  The output fills the tight bounding box of every blue
cell with cyan (8), replacing the blue cells and any background gaps while
preserving everything outside that box.

The teaching schedule deliberately varies blue count, bbox size, 4-connectivity,
placement, distractor size, and distractor color.  It alternates ordinary
4-connected profiles with diagonal-only 8-connected profiles and interleaves
canonical with off-canonical blue geometries.  Every four-pair lesson and every
single-query rotation therefore refutes both connectivity and shape-whitelist
shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3ffc7ef20035"
TASK_ID = GENERATOR_ID
VERSION = "3.2.1"
RULE_HASH = "bde384898938"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An 8-12 by 9-12 zero-background grid contains one sparse blue (1) "
    "object and one separate straight distractor in another color. Find all "
    "blue cells, compute their tight bounding box, and paint every cell in "
    "that rectangle cyan (8). The blue cells are replaced; the distractor "
    "and all cells outside the blue bounding box are preserved."
)

INVARIANTS = [
    "the blue cells form one 8-connected object spanning at least two rows and columns",
    "the blue bounding box contains at least one background gap, so filling is observable",
    "exactly one non-blue foreground color forms a separate 1-3 cell straight distractor",
    "the distractor lies outside the blue bounding box",
    "input color 8 is absent and reserved for the output fill",
]

SHAPE_PROFILES = (
    # Alternate 4-connected and diagonal-only 8-connected objects.  Canonical
    # geometries (C) are also interleaved with off-canonical geometries (N).
    # Thus every cyclic four-pair lesson has two diagonal witnesses and at least
    # two off-canonical witnesses; holding out any query leaves one of each in
    # the demonstrations.
    "l3_2x2",                 # 4-connected, C
    "diagonal4_4x2",         # diagonal-only, N
    "stair4_3x2",            # 4-connected, C
    "diagonal4_3x3",         # diagonal-only, N
    "wide4_2x3",             # 4-connected, N
    "diagonal3_3x2",         # diagonal-only, C
    "zigzag5_3x3",           # 4-connected, N
    "canonical_hook4_3x3",   # diagonal-only, C
    "stair6_4x3",            # 4-connected, N
    "diagonal5_4x3",         # diagonal-only, N
)
SCHEDULE_PROFILES = SHAPE_PROFILES
LESSON_SCHEDULE_PERIOD = len(SHAPE_PROFILES)

# Shapes are orientation-specific on purpose: profile identity is recoverable
# exactly from the returned grid.  The expanded family includes the canonical
# test geometry, branching/path-like objects, tall/wide/square boxes, and five
# objects whose only connection between blue subparts is diagonal.
_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "l3_2x2": ((0, 0), (1, 0), (1, 1)),
    "diagonal3_3x2": ((0, 1), (1, 1), (2, 0)),
    "stair4_3x2": ((0, 0), (1, 0), (1, 1), (2, 1)),
    # Exact normalized blue geometry of the canonical test pair.
    "canonical_hook4_3x3": ((0, 0), (1, 0), (2, 1), (2, 2)),
    "wide4_2x3": ((0, 0), (0, 1), (1, 1), (1, 2)),
    "diagonal4_4x2": ((0, 1), (1, 1), (2, 0), (3, 0)),
    "zigzag5_3x3": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    "diagonal4_3x3": ((0, 2), (1, 1), (2, 0), (2, 1)),
    "stair6_4x3": ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    "diagonal5_4x3": ((0, 2), (1, 2), (2, 1), (3, 0), (3, 1)),
}
_SHAPE_BY_NORMALIZED = {tuple(sorted(cells)): name for name, cells in _SHAPES.items()}

# These are exactly the four distinct normalized blue geometries in the five
# canonical pairs (one training geometry repeats).  Keeping the set explicit
# makes the canonical-fitting shape-whitelist rival deterministic and auditable.
_CANONICAL_SHAPE_PROFILES = (
    "l3_2x2",
    "stair4_3x2",
    "diagonal3_3x2",
    "canonical_hook4_3x3",
)
_CANONICAL_BLUE_SHAPES = frozenset(
    tuple(sorted(_SHAPES[name])) for name in _CANONICAL_SHAPE_PROFILES
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-keyed 8..12",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-keyed 9..12",
        "valid": "9..12",
    },
    "shape_profile": {
        "type": "enum",
        "default": "sample_index schedule",
        "valid": SHAPE_PROFILES,
    },
    "distractor_size": {
        "type": "int",
        "default": "sample_index schedule 1..3",
        "valid": "1..3",
    },
    "distractor_color": {
        "type": "color",
        "default": "rng among 2..7 or 9",
        "valid": "2..7,9",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(row for row, _col in cells),
        min(col for _row, col in cells),
        max(row for row, _col in cells),
        max(col for _row, col in cells),
    )


def _normalized(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _col in cells)
    c0 = min(col for _row, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _components(
    cells: Iterable[tuple[int, int]], *, connectivity: int
) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    if connectivity == 4:
        deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    elif connectivity == 8:
        deltas = tuple(
            (dr, dc)
            for dr in (-1, 0, 1)
            for dc in (-1, 0, 1)
            if (dr, dc) != (0, 0)
        )
    else:
        raise ValueError(f"unsupported connectivity {connectivity}")

    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        component = {start}
        remaining.remove(start)
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in deltas:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        result.append(component)
    return result


def _straight_bar(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = {row for row, _col in cells}
    cols = {col for _row, col in cells}
    if len(rows) == 1:
        values = sorted(col for _row, col in cells)
    elif len(cols) == 1:
        values = sorted(row for row, _col in cells)
    else:
        return False
    return values == list(range(values[0], values[-1] + 1))


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list/tuple"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"grid dimensions must be within 1..30, got {len(grid)}x{width}"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC color integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    blue = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 1
    }
    if len(blue) < 3:
        errors.append(f"need at least three blue cells, got {len(blue)}")
    if any(value == 8 for row in grid for value in row):
        errors.append("input must not contain reserved output color 8")

    blue_bbox = _bbox(blue) if blue else None
    if blue_bbox is not None:
        r0, c0, r1, c1 = blue_bbox
        bbox_h, bbox_w = r1 - r0 + 1, c1 - c0 + 1
        if bbox_h < 2 or bbox_w < 2:
            errors.append(
                f"blue cells must span at least two rows and columns, got {bbox_h}x{bbox_w}"
            )
        if bbox_h > 4 or bbox_w > 4:
            errors.append(f"blue bbox must be at most 4x4, got {bbox_h}x{bbox_w}")
        if r0 == 0 or c0 == 0 or r1 == height - 1 or c1 == width - 1:
            errors.append("blue bbox must have at least a one-cell grid margin")
        if len(blue) >= bbox_h * bbox_w:
            errors.append("blue bbox must contain a background gap to make filling observable")
        if len(_components(blue, connectivity=8)) != 1:
            errors.append("blue cells must form one 8-connected object")

    other_colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 1, 8)
        }
    )
    distractor_color = other_colors[0] if len(other_colors) == 1 else None
    if len(other_colors) != 1:
        errors.append(
            f"expected exactly one distractor color outside {{0,1,8}}, got {other_colors}"
        )
    distractor = (
        {
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == distractor_color
        }
        if distractor_color is not None
        else set()
    )
    if distractor_color is not None:
        if not 1 <= len(distractor) <= 3:
            errors.append(
                f"distractor must contain 1..3 cells, got {len(distractor)}"
            )
        if not _straight_bar(distractor):
            errors.append("distractor cells must form one contiguous straight bar")
        if blue_bbox is not None:
            r0, c0, r1, c1 = blue_bbox
            if any(r0 <= row <= r1 and c0 <= col <= c1 for row, col in distractor):
                errors.append("distractor must lie outside the blue bounding box")
            if any(
                max(abs(br - dr), abs(bc - dc)) <= 1
                for br, bc in blue
                for dr, dc in distractor
            ):
                errors.append("distractor must be visibly separate from the blue object")

    shape_profile = None
    if blue:
        shape_profile = _SHAPE_BY_NORMALIZED.get(_normalized(blue))

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "blue": blue,
        "blue_bbox": blue_bbox,
        "shape_profile": shape_profile,
        "distractor_color": distractor_color,
        "distractor": distractor,
        "blue_4_components": (
            len(_components(blue, connectivity=4)) if blue else 0
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding scenes while accepting all canonicals."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def strict_canonical_like(grid) -> list[str]:
    """Task-linked predicate for the canonical sparse-blue-object grammar."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not 8 <= analysis["height"] <= 12 or not 8 <= analysis["width"] <= 12:
        errors.append(
            f"canonical canvas envelope is 8..12 per side, got "
            f"{analysis['height']}x{analysis['width']}"
        )
    if len(analysis["blue"]) > 6:
        errors.append("canonical-like blue object has at most six cells")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "shape_profile": analysis["shape_profile"],
        "distractor_size": len(analysis["distractor"]),
        "distractor_color": analysis["distractor_color"],
    }


def schedule_profile(seed, sample_index, difficulty=None):
    """Observable ordinary-draw morphology schedule used by lesson replay."""
    del seed, difficulty
    return SHAPE_PROFILES[int(sample_index) % len(SHAPE_PROFILES)]


def _draw_dimension(ctx, overrides, label: str, band: str) -> int:
    full = {"grid_h": (8, 12), "grid_w": (9, 12)}[label]
    per_band = {
        "easy": {"grid_h": (8, 9), "grid_w": (9, 10)},
        "medium": {"grid_h": (9, 11), "grid_w": (9, 11)},
        "hard": {"grid_h": (10, 12), "grid_w": (10, 12)},
    }
    lo, hi = full if label in overrides else per_band[band][label]
    return ctx.draw_int(label, lo, hi)


def _draw_shape_profile(ctx, overrides, sample_index: int) -> str:
    if "shape_profile" in overrides:
        return ctx.draw_choice("shape_profile", SHAPE_PROFILES)
    scheduled = SHAPE_PROFILES[int(sample_index) % len(SHAPE_PROFILES)]
    return ctx.draw_choice("shape_profile", (scheduled,))


def _draw_distractor_size(ctx, overrides, sample_index: int) -> int:
    if "distractor_size" in overrides:
        return ctx.draw_int("distractor_size", 1, 3)
    scheduled = 1 + (int(sample_index) % 3)
    return ctx.draw_int("distractor_size", scheduled, scheduled)


def _shape_dimensions(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return (
        max(row for row, _col in cells) + 1,
        max(col for _row, col in cells) + 1,
    )


def _distractor_candidates(
    height: int,
    width: int,
    size: int,
    blue: set[tuple[int, int]],
    blue_bbox: tuple[int, int, int, int],
) -> list[tuple[tuple[int, int], ...]]:
    candidates: set[tuple[tuple[int, int], ...]] = set()
    orientations = ((0, 1), (1, 0)) if size > 1 else ((0, 1),)
    r0, c0, r1, c1 = blue_bbox
    for dr, dc in orientations:
        max_row = height - 1 - dr * (size - 1)
        max_col = width - 1 - dc * (size - 1)
        for row in range(max_row + 1):
            for col in range(max_col + 1):
                cells = tuple((row + i * dr, col + i * dc) for i in range(size))
                if any(r0 <= rr <= r1 and c0 <= cc <= c1 for rr, cc in cells):
                    continue
                if any(
                    max(abs(br - rr), abs(bc - cc)) <= 1
                    for br, bc in blue
                    for rr, cc in cells
                ):
                    continue
                candidates.add(cells)
    return sorted(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_dimension(ctx, overrides, "grid_h", band)
    width = _draw_dimension(ctx, overrides, "grid_w", band)
    profile = _draw_shape_profile(ctx, overrides, sample_index)
    distractor_size = _draw_distractor_size(ctx, overrides, sample_index)
    distractor_color = ctx.draw_color("distractor_color", exclude=(0, 1, 8))

    shape = _SHAPES[profile]
    shape_h, shape_w = _shape_dimensions(shape)
    position_rng = ctx.draw_rng("blue_position")
    top = position_rng.randint(1, height - shape_h - 1)
    left = position_rng.randint(1, width - shape_w - 1)
    blue = {(top + row, left + col) for row, col in shape}
    blue_bbox = _bbox(blue)

    candidates = _distractor_candidates(
        height, width, distractor_size, blue, blue_bbox
    )
    if not candidates:
        raise ValueError(
            f"no legal distractor placement for {height}x{width}, "
            f"profile={profile}, size={distractor_size}"
        )
    distractor_rng = ctx.draw_rng("distractor_position")
    distractor = candidates[distractor_rng.randrange(len(candidates))]

    grid = full_grid(height, width, 0)
    for row, col in blue:
        grid[row][col] = 1
    for row, col in distractor:
        grid[row][col] = distractor_color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Python test mirror; canonical Racket remains the output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    output = _copy_grid(grid)
    r0, c0, r1, c1 = analysis["blue_bbox"]
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            output[row][col] = 8
    return output


def _paint_blue_only(grid) -> list[list[int]]:
    output = _copy_grid(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 1:
                output[row][col] = 8
    return output


def _four_corners_only(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    r0, c0, r1, c1 = analysis["blue_bbox"]
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    if analysis["blue"] == corners:
        return rule_mirror(grid)
    return _paint_blue_only(grid)


def _fixed_3x4_only(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    r0, c0, r1, c1 = analysis["blue_bbox"]
    if (r1 - r0 + 1, c1 - c0 + 1) == (3, 4):
        return rule_mirror(grid)
    return _paint_blue_only(grid)


def _all_foreground_bbox(grid) -> list[list[int]]:
    foreground = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    output = _copy_grid(grid)
    if not foreground:
        return output
    r0, c0, r1, c1 = _bbox(foreground)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            output[row][col] = 8
    return output


def _first_4_connected_blue_component(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    components = _components(analysis["blue"], connectivity=4)
    selected = min(components, key=lambda cells: min(cells))
    output = _copy_grid(grid)
    r0, c0, r1, c1 = _bbox(selected)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            output[row][col] = 8
    return output


def _canonical_shape_whitelist(grid) -> list[list[int]]:
    """Fit all canonical pairs, but generalize only their four blue shapes."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return _copy_grid(grid)
    if _normalized(analysis["blue"]) in _CANONICAL_BLUE_SHAPES:
        return rule_mirror(grid)
    return _paint_blue_only(grid)


def _blue_bbox_has_gap(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    r0, c0, r1, c1 = analysis["blue_bbox"]
    return len(analysis["blue"]) < (r1 - r0 + 1) * (c1 - c0 + 1)


def _not_four_corners(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    r0, c0, r1, c1 = analysis["blue_bbox"]
    corners = {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}
    return analysis["blue"] != corners


def _bbox_not_fixed_3x4(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    r0, c0, r1, c1 = analysis["blue_bbox"]
    return (r1 - r0 + 1, c1 - c0 + 1) != (3, 4)


def _distractor_outside_target_bbox(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return False
    r0, c0, r1, c1 = analysis["blue_bbox"]
    return bool(analysis["distractor"]) and all(
        not (r0 <= row <= r1 and c0 <= col <= c1)
        for row, col in analysis["distractor"]
    )


def _diagonal_only_blue_link(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["blue_4_components"] > 1


def _outside_canonical_shape_family(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _normalized(analysis["blue"]) not in _CANONICAL_BLUE_SHAPES
    )


SEMANTIC_RIVALS = {
    "paint_blue_only": _paint_blue_only,
    "four_blue_corners_only": _four_corners_only,
    "fixed_3x4_bbox_only": _fixed_3x4_only,
    "all_foreground_bbox": _all_foreground_bbox,
    "first_4_connected_blue_component": _first_4_connected_blue_component,
    "canonical_shape_whitelist": _canonical_shape_whitelist,
}

SEMANTIC_WITNESSES = {
    "blank_inside_blue_bbox": _blue_bbox_has_gap,
    "non_corner_blue_geometry": _not_four_corners,
    "bbox_not_fixed_3x4": _bbox_not_fixed_3x4,
    "separate_distractor_outside_target": _distractor_outside_target_bbox,
    "diagonal_only_blue_link": _diagonal_only_blue_link,
    "outside_canonical_shape_family": _outside_canonical_shape_family,
}

WITNESS_RIVALS = {
    "blank_inside_blue_bbox": ["paint_blue_only"],
    "non_corner_blue_geometry": ["four_blue_corners_only"],
    "bbox_not_fixed_3x4": ["fixed_3x4_bbox_only"],
    "separate_distractor_outside_target": ["all_foreground_bbox"],
    "diagonal_only_blue_link": ["first_4_connected_blue_component"],
    "outside_canonical_shape_family": ["canonical_shape_whitelist"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# A canonical shortcut must fit every usable canonical pair.  Broader plausible
# rivals remain in LESSON_COMPETITORS even when the canonical data already refute
# them; only the shape whitelist satisfies the stricter canonical-fit contract.
CANONICAL_SHORTCUTS = {
    "canonical_shape_whitelist": SEMANTIC_RIVALS["canonical_shape_whitelist"],
}


def _same_grid(left, right) -> bool:
    return tuple(map(tuple, left)) == tuple(map(tuple, right))


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a rival only when it fits every demo and changes this query."""
    errors: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        changes_query = not _same_grid(
            competitor(query["input"]), query["output"]
        )
        fits_demos = all(
            _same_grid(competitor(pair["input"]), pair["output"])
            for pair in demos
        )
        if fits_demos and changes_query:
            errors.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return errors
