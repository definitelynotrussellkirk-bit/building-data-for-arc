"""Generator for 12b:m81 — select the area-matched monochrome object and scale 2×.

The authoritative rule counts color-1 cells in row 0, finds the monochrome
4-connected object below the header whose area equals that count, crops the
original body grid to that object's bounding box, and upscales the crop 2×.

The four-profile default schedule teaches two distinctions absent from the
canonical examples alone: only color 1 contributes to the header count, and
objects are separated by color even when different colors touch edge-to-edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0444de97675"
TASK_ID = GENERATOR_ID
RULE_HASH = "e92da57c2394"
VERSION = "3.0.0"
SUMMARY = (
    "Count color-1 header markers, select the uniquely area-matched monochrome "
    "body object, crop its original-grid bounding box, and upscale 2×. Four "
    "scheduled profiles vary canonical scale, non-1 header distractors, and "
    "touching different-color objects."
)

INVARIANTS = [
    "row 0 contains K color-1 markers; only those markers define K",
    "rows 1+ contain monochrome 4-connected objects with exactly one area-K object",
    "the selected generated object is bbox-open, so its 2× crop is not a solid block",
    "different-colored objects may touch and remain distinct objects",
]

TOUCHING_MODES = ("separated", "target_touching")
AXES = {
    "grid_h": {"type": "int", "default": "profile/difficulty schedule", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "profile/difficulty schedule", "valid": "9..14"},
    "target_size": {"type": "int", "default": "difficulty schedule", "valid": "3..6"},
    "header_distractors": {"type": "int", "default": "profile 0/2: 0; 1/3: 1", "valid": "0..2"},
    "touching_mode": {"type": "str", "default": "profile 0/1: separated; 2/3: target_touching", "valid": "separated|target_touching"},
    "target_color": {"type": "int", "default": "uniform 2..9", "valid": "2..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (0, 1, 2, 3)
MIN_STRICT_FRAC = 0.20

_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SENTINEL_OUTPUT = [[0]]


def schedule_profile(seed, sample_index, difficulty=None):
    """Four cyclic profiles; every three-profile subset exposes both rivals."""
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return sample_index % 4


def _draw_int(ctx, label, lo, hi, default_lo, default_hi):
    """Use a scheduled default while preserving the full exact override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _draw_choice(ctx, label, options, default):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _normalize(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _rand_poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice(_NEIGHBORS)
        cells.add((r + dr, c + dc))
    return _normalize(cells)


def _rand_poly_open(rng, size):
    for _ in range(80):
        cells = _rand_poly(rng, size)
        height = max(r for r, _ in cells) + 1
        width = max(c for _, c in cells) + 1
        if height * width > size:
            return cells
    # Deterministic open fallback for every supported size (3..6).
    cells = [(0, 0), (1, 0), (1, 1)]
    for index in range(3, size):
        cells.append((1 + (index - 2) // 2, (index - 2) % 2))
    return _normalize(cells)


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _translations(shape, height, width):
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    return [
        frozenset((row0 + r, col0 + c) for r, c in shape)
        for row0 in range(1, height - shape_h + 1)
        for col0 in range(0, width - shape_w + 1)
    ]


def _touches(first, second):
    second = set(second)
    return any((r + dr, c + dc) in second for r, c in first for dr, dc in _NEIGHBORS)


def _separated(candidate, occupied):
    occupied = set(occupied)
    if candidate & occupied:
        return False
    return not _touches(candidate, occupied)


def _shuffle_copy(rng, values):
    values = list(values)
    rng.shuffle(values)
    return values


def _place_shapes(height, width, shapes, target_index, touching_mode, rng):
    """Return translated cell sets, or None if these random shapes do not fit."""
    placements = [_translations(shape, height, width) for shape in shapes]
    target_candidates = _shuffle_copy(rng, placements[target_index])
    other_indices = [index for index in range(3) if index != target_index]

    if touching_mode == "separated":
        order = _shuffle_copy(rng, other_indices)
        for target in target_candidates:
            for second in _shuffle_copy(rng, placements[order[0]]):
                if not _separated(second, target):
                    continue
                occupied = target | second
                for third in _shuffle_copy(rng, placements[order[1]]):
                    if _separated(third, occupied):
                        result = [None, None, None]
                        result[target_index] = target
                        result[order[0]] = second
                        result[order[1]] = third
                        return result
        return None

    touch_orders = _shuffle_copy(rng, other_indices)
    for touch_index in touch_orders:
        third_index = next(index for index in other_indices if index != touch_index)
        for target in target_candidates:
            tr0, tc0, tr1, tc1 = _bbox(target)
            for touching in _shuffle_copy(rng, placements[touch_index]):
                if touching & target or not _touches(touching, target):
                    continue
                # Keep the selected crop pure: the touching object lies just
                # outside the target bbox rather than inside a concavity.
                if any(tr0 <= r <= tr1 and tc0 <= c <= tc1 for r, c in touching):
                    continue
                occupied = target | touching
                for third in _shuffle_copy(rng, placements[third_index]):
                    if _separated(third, occupied):
                        result = [None, None, None]
                        result[target_index] = target
                        result[touch_index] = touching
                        result[third_index] = third
                        return result
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    if profile in (0, 2):
        default_h = (8, 8)
        default_w = (9, 9)
    elif difficulty == "easy":
        default_h = (8, 10)
        default_w = (9, 11)
    elif difficulty == "hard":
        default_h = (11, 14)
        default_w = (12, 14)
    else:
        default_h = (9, 12)
        default_w = (10, 13)

    height = _draw_int(ctx, "grid_h", 8, 14, *default_h)
    width = _draw_int(ctx, "grid_w", 9, 14, *default_w)
    if profile == 0 or difficulty == "easy":
        size_defaults = (3, 4)
    elif difficulty == "hard":
        size_defaults = (4, 6)
    else:
        size_defaults = (3, 5)
    target_size = _draw_int(ctx, "target_size", 3, 6, *size_defaults)
    header_default = 1 if profile in (1, 3) else 0
    header_distractors = _draw_int(
        ctx, "header_distractors", 0, 2, header_default, header_default
    )
    touching_default = "target_touching" if profile in (2, 3) else "separated"
    touching_mode = _draw_choice(ctx, "touching_mode", TOUCHING_MODES, touching_default)
    target_color = _draw_int(ctx, "target_color", 2, 9, 2, 9)

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    shape_rng = ctx.draw_rng("shapes")
    header_rng = ctx.draw_rng("header")

    other_colors = color_rng.sample(
        [color for color in range(2, 10) if color != target_color], 2
    )
    colors = [target_color, *other_colors]
    target_index = 0

    size_pool = [size for size in range(2, 8) if size != target_size]
    for _ in range(120):
        distractor_sizes = shape_rng.sample(size_pool, 2)
        shapes = [
            _rand_poly_open(shape_rng, target_size),
            _rand_poly(shape_rng, distractor_sizes[0]),
            _rand_poly(shape_rng, distractor_sizes[1]),
        ]
        placed = _place_shapes(
            height, width, shapes, target_index, touching_mode, layout_rng
        )
        if placed is None:
            continue

        grid = full_grid(height, width, 0)
        for cells, color in zip(placed, colors):
            for row, col in cells:
                grid[row][col] = color

        header_columns = header_rng.sample(
            range(width), target_size + header_distractors
        )
        for col in header_columns[:target_size]:
            grid[0][col] = 1
        for index, col in enumerate(header_columns[target_size:]):
            grid[0][col] = other_colors[index % len(other_colors)]

        if self_check(grid, difficulty=difficulty) == []:
            return grid

    raise RuntimeError(
        "failed to construct a lawful three-object scene for the requested axes"
    )


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    return []


def _body_objects(grid, *, color_sensitive=True):
    """4-connected body objects; authoritative objects are color-sensitive."""
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(1, height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for dr, dc in _NEIGHBORS:
                    next_row, next_col = current_row + dr, current_col + dc
                    if not (1 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == 0:
                        continue
                    if color_sensitive and grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(tuple(sorted(cells)))
    return components


def _selected_object(grid, count, *, color_sensitive=True):
    matches = [
        obj
        for obj in _body_objects(grid, color_sensitive=color_sensitive)
        if len(obj) == count
    ]
    if not matches:
        return None
    return min(matches, key=_bbox)


def _crop_scale(grid, obj):
    if obj is None:
        return [row[:] for row in _SENTINEL_OUTPUT]
    row0, col0, row1, col1 = _bbox(obj)
    crop = [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]
    output = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        output.extend([doubled[:], doubled[:]])
    return output


def _solve_with_count(grid, count, *, color_sensitive=True):
    return _crop_scale(
        grid, _selected_object(grid, count, color_sensitive=color_sensitive)
    )


def rule_mirror(grid):
    """Pure Python mirror of the selected Racket rule for tests and rivals."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    count = sum(value == 1 for value in grid[0])
    return _solve_with_count(grid, count, color_sensitive=True)


def _rival_count_all_header_nonzero(grid):
    count = sum(value != 0 for value in grid[0])
    return _solve_with_count(grid, count, color_sensitive=True)


def _rival_color_agnostic_components(grid):
    count = sum(value == 1 for value in grid[0])
    return _solve_with_count(grid, count, color_sensitive=False)


def _target_touches_other_color(grid):
    count = sum(value == 1 for value in grid[0])
    target = _selected_object(grid, count, color_sensitive=True)
    if target is None:
        return False
    target_cells = set(target)
    target_color = grid[target[0][0]][target[0][1]]
    for row, col in target:
        for dr, dc in _NEIGHBORS:
            neighbor = (row + dr, col + dc)
            if neighbor in target_cells:
                continue
            nr, nc = neighbor
            if 1 <= nr < len(grid) and 0 <= nc < len(grid[0]):
                value = grid[nr][nc]
                if value not in (0, target_color):
                    return True
    return False


def observe_overrides(grid):
    errors = _validate_grid(grid)
    if errors:
        raise ValueError(errors[0])
    count = sum(value == 1 for value in grid[0])
    target = _selected_object(grid, count, color_sensitive=True)
    if target is None:
        raise ValueError("grid has no area-matched monochrome target")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_size": count,
        "header_distractors": sum(value not in (0, 1) for value in grid[0]),
        "touching_mode": "target_touching" if _target_touches_other_color(grid) else "separated",
        "target_color": grid[target[0][0]][target[0][1]],
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _validate_grid(grid)
    if errors:
        return errors
    count = sum(value == 1 for value in grid[0])
    if count == 0:
        return ["row 0 must contain at least one color-1 marker"]
    if any(value == 1 for row in grid[1:] for value in row):
        return ["color 1 is reserved for header markers and may not occur in the body"]
    matches = [obj for obj in _body_objects(grid) if len(obj) == count]
    if len(matches) != 1:
        return [
            f"expected exactly 1 monochrome body object with K={count} cells, got {len(matches)}"
        ]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) != (8, 9):
        return ["canonical profile uses an 8x9 input"]
    if len({value for row in grid for value in row}) != 5:
        return ["canonical profile uses exactly five colors including background"]
    if len(_body_objects(grid)) != 3:
        return ["canonical profile contains exactly three monochrome body objects"]
    return []


def _witness_non_one_header(grid):
    return any(value not in (0, 1) for value in grid[0])


SEMANTIC_WITNESSES = {
    "non_one_header_cue": _witness_non_one_header,
    "target_touches_other_color": _target_touches_other_color,
}
SEMANTIC_RIVALS = {
    "count_all_header_nonzero": _rival_count_all_header_nonzero,
    "color_agnostic_components": _rival_color_agnostic_components,
}
WITNESS_RIVALS = {
    "non_one_header_cue": ["count_all_header_nonzero"],
    "target_touches_other_color": ["color_agnostic_components"],
}
CANONICAL_SHORTCUTS = {
    "count_all_header_nonzero": _rival_count_all_header_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
