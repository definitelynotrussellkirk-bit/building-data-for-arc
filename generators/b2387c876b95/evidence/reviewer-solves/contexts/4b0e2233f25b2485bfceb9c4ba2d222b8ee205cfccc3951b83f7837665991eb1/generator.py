"""Constructive sampler for reflecting the red object across a gray divider.

The pinned Racket authority paints the reflected copy color 3 while preserving
all input pixels.  Inputs deliberately vary divider orientation, source side,
red L-shape size/chirality, and an unrelated non-red distractor so lessons cannot
collapse to "copy right/down" or "reflect every object" shortcuts.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b2387c876b95"
TASK_ID = GENERATOR_ID
RULE_HASH = "d6356bd3481a"
VERSION = "3.0.0"
SUMMARY = (
    "A complete gray color-5 row or column separates a red color-2 L-shape "
    "from empty space. Reflect only the red cells across the divider and paint "
    "their blank mirror positions color 3. Preserve the red source, divider, "
    "background, and one unrelated non-red distractor object."
)
INVARIANTS = [
    "rectangular ARC grid with background 0 and no input color 3",
    "exactly one complete color-5 divider row or column and no extra color 5",
    "one connected red L triomino or L/J tetromino lies strictly on one side",
    "every red mirror destination is in bounds and blank in the input",
    "one connected color-4/6/7/8/9 distractor is preserved unchanged",
]

AXES = {
    "grid_h": {"type": "int", "default": "four canonical-size schedule profiles", "valid": "9..12"},
    "grid_w": {"type": "int", "default": "four canonical-size schedule profiles", "valid": "10..13"},
    "orientation": {"type": "str", "default": "scheduled vertical|horizontal", "valid": "vertical|horizontal"},
    "source_side": {"type": "str", "default": "scheduled negative|positive", "valid": "negative|positive"},
    "shape_variant": {"type": "int", "default": "scheduled L triomino/L-J tetromino", "valid": "0..11"},
    "distractor_color": {"type": "int", "default": "scheduled canonical palette", "valid": "4|6|7|8|9"},
    "distractor_shape": {"type": "int", "default": "scheduled block/line/L", "valid": "0..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (0, 1, 2, 3)
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)

_ORIENTATIONS = ("vertical", "horizontal")
_SIDES = ("negative", "positive")
_DISTRACTOR_COLORS = (4, 6, 7, 8, 9)


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dihedral_variants(base):
    variants = []
    for reflected in (False, True):
        for turns in range(4):
            points = []
            for row, col in base:
                if reflected:
                    col = -col
                for _ in range(turns):
                    row, col = col, -row
                points.append((row, col))
            normalized = _normalize(points)
            if normalized not in variants:
                variants.append(normalized)
    return tuple(variants)


# Four L-triomino orientations followed by all eight L/J-tetromino orientations.
SOURCE_SHAPES = _dihedral_variants(((0, 0), (1, 0), (1, 1))) + _dihedral_variants(
    ((0, 0), (1, 0), (2, 0), (2, 1))
)

# Canonical distractor families: square, 3/4 bars in both orientations, and L triominoes.
DISTRACTOR_SHAPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
) + _dihedral_variants(((0, 0), (1, 0), (1, 1)))

# Every consecutive four samples covers both divider orientations, both source
# sides, both source sizes, four source variants, four distractor colors/shapes,
# and the four linked canonical dimension profiles.
_DEFAULT_PROFILES = (
    dict(grid_h=10, grid_w=11, orientation="vertical", source_side="negative",
         shape_variant=0, distractor_color=7, distractor_shape=0),
    dict(grid_h=12, grid_w=10, orientation="horizontal", source_side="positive",
         shape_variant=4, distractor_color=8, distractor_shape=5),
    dict(grid_h=9, grid_w=13, orientation="vertical", source_side="positive",
         shape_variant=8, distractor_color=4, distractor_shape=3),
    dict(grid_h=11, grid_w=12, orientation="horizontal", source_side="negative",
         shape_variant=3, distractor_color=6, distractor_shape=8),
)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return int(sample_index) % len(_DEFAULT_PROFILES)


def _draw_scheduled_int(ctx, overrides, label, default, lo, hi):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return int(ctx.draw_choice(label, (default,)))


def _draw_scheduled_choice(ctx, overrides, label, default, options):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer (not bool)")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    integer_domains = {
        "grid_h": (9, 12),
        "grid_w": (10, 13),
        "shape_variant": (0, len(SOURCE_SHAPES) - 1),
        "distractor_shape": (0, len(DISTRACTOR_SHAPES) - 1),
    }
    for name, (lo, hi) in integer_domains.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"override {name} must be an integer in {lo}..{hi} (not bool)")

    for name, options in (("orientation", _ORIENTATIONS), ("source_side", _SIDES)):
        value = overrides.get(name)
        if value is not None and (type(value) is not str or value not in options):
            raise ValueError(f"override {name} must be one of {options}")

    value = overrides.get("distractor_color")
    if value is not None and (type(value) is not int or value not in _DISTRACTOR_COLORS):
        raise ValueError(f"override distractor_color must be one of {_DISTRACTOR_COLORS}")


def _divider(grid):
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    height, width = len(grid), len(grid[0])
    rows = [r for r in range(height) if all(grid[r][c] == 5 for c in range(width))]
    cols = [c for c in range(width) if all(grid[r][c] == 5 for r in range(height))]
    if len(rows) + len(cols) != 1:
        raise ValueError(f"expected exactly one divider; rows={rows}, cols={cols}")
    return ("horizontal", rows[0]) if rows else ("vertical", cols[0])


def _reflect(point, orientation, divider_index):
    row, col = point
    if orientation == "vertical":
        return row, 2 * divider_index - col
    return 2 * divider_index - row, col


def _red_cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}


def _source_side(grid):
    orientation, divider_index = _divider(grid)
    offsets = [
        (col - divider_index if orientation == "vertical" else row - divider_index)
        for row, col in _red_cells(grid)
    ]
    if offsets and max(offsets) < 0:
        return "negative"
    if offsets and min(offsets) > 0:
        return "positive"
    return "crosses"


def _rectangular_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["ARC grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors in 0..9 (not bool)"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the source manifold and reflection preconditions."""
    del difficulty, meta
    errors = _rectangular_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])

    try:
        orientation, divider_index = _divider(grid)
    except ValueError as exc:
        return [str(exc)]

    expected_fives = width if orientation == "horizontal" else height
    actual_fives = sum(value == 5 for row in grid for value in row)
    if actual_fives != expected_fives:
        errors.append(f"expected no color-5 cells outside the divider; found {actual_fives}")

    red = _red_cells(grid)
    red_shape = _normalize(red)
    if red_shape not in SOURCE_SHAPES:
        errors.append("red source must be one L triomino or L/J tetromino")
    side = _source_side(grid) if red else "crosses"
    if side not in _SIDES:
        errors.append("all red source cells must lie strictly on one divider side")

    for point in red:
        rr, cc = _reflect(point, orientation, divider_index)
        if not (0 <= rr < height and 0 <= cc < width):
            errors.append(f"red mirror destination {(rr, cc)} is out of bounds")
        elif grid[rr][cc] != 0:
            errors.append(f"red mirror destination {(rr, cc)} is not blank")

    non_task_colors = sorted({value for row in grid for value in row} - {0, 2, 5})
    if 3 in non_task_colors:
        errors.append("input color 3 is reserved for reflected output cells")
    distractor_colors = [color for color in non_task_colors if color != 3]
    if len(distractor_colors) != 1 or distractor_colors[0] not in _DISTRACTOR_COLORS:
        errors.append("expected exactly one distractor color from 4,6,7,8,9")
    else:
        color = distractor_colors[0]
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        if _normalize(cells) not in DISTRACTOR_SHAPES:
            errors.append("distractor must be a canonical block, line, or L triomino")

    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def rule_mirror(grid):
    """Independent authoring mirror; the Racket program remains label authority."""
    out = [list(row) for row in grid]
    orientation, divider_index = _divider(grid)
    height, width = len(grid), len(grid[0])
    for point in _red_cells(grid):
        rr, cc = _reflect(point, orientation, divider_index)
        if 0 <= rr < height and 0 <= cc < width and out[rr][cc] == 0:
            out[rr][cc] = 3
    return out


def observe_overrides(grid):
    orientation, _ = _divider(grid)
    red_shape = _normalize(_red_cells(grid))
    other_colors = sorted({value for row in grid for value in row} - {0, 2, 5})
    if 3 in other_colors:
        raise ValueError("input unexpectedly contains output color 3")
    if len(other_colors) != 1:
        raise ValueError(f"expected one distractor color, got {other_colors}")
    color = other_colors[0]
    distractor = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "orientation": orientation,
        "source_side": _source_side(grid),
        "shape_variant": SOURCE_SHAPES.index(red_shape),
        "distractor_color": color,
        "distractor_shape": DISTRACTOR_SHAPES.index(_normalize(distractor)),
    }


@lru_cache(maxsize=4096)
def _source_candidates(height, width, orientation, side, shape_variant):
    shape = SOURCE_SHAPES[shape_variant]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    axis_limit = width if orientation == "vertical" else height
    candidates = []
    for divider_index in range(1, axis_limit - 1):
        for top in range(height - shape_h + 1):
            for left in range(width - shape_w + 1):
                source = tuple((top + r, left + c) for r, c in shape)
                offsets = [
                    (c - divider_index if orientation == "vertical" else r - divider_index)
                    for r, c in source
                ]
                if side == "negative" and max(offsets) >= 0:
                    continue
                if side == "positive" and min(offsets) <= 0:
                    continue
                mirrored = tuple(_reflect(point, orientation, divider_index) for point in source)
                if not all(0 <= r < height and 0 <= c < width for r, c in mirrored):
                    continue
                candidates.append((divider_index, source, mirrored, min(abs(value) for value in offsets)))
    return tuple(candidates)


@lru_cache(maxsize=4096)
def _shape_placements(height, width, distractor_shape):
    shape = DISTRACTOR_SHAPES[distractor_shape]
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    return tuple(
        tuple((top + r, left + c) for r, c in shape)
        for top in range(height - shape_h + 1)
        for left in range(width - shape_w + 1)
    )


def _divider_cells(height, width, orientation, divider_index):
    if orientation == "vertical":
        return {(r, divider_index) for r in range(height)}
    return {(divider_index, c) for c in range(width)}


def _valid_distractor_placements(height, width, orientation, divider_index,
                                 distractor_shape, blocked):
    valid = []
    for cells_tuple in _shape_placements(height, width, distractor_shape):
        cells = set(cells_tuple)
        if cells & blocked:
            continue
        mirror = {
            point
            for point in (_reflect(cell, orientation, divider_index) for cell in cells)
            if 0 <= point[0] < height and 0 <= point[1] < width
        }
        # At least one in-bounds blank mirror cell is enough to refute the
        # "reflect every colored object" shortcut. Other distractor mirrors may
        # legitimately leave the canvas, as in the canonical test input.
        if not (mirror - blocked - cells):
            continue
        valid.append(cells_tuple)
    return valid


def _first_object_shortcut_fits_layout(divider_cells, source, mirrored, distractor):
    """Whether the gate's row-major first-object attribution keeps every fill."""
    components = sorted(
        (set(divider_cells), set(source), set(distractor)),
        key=min,
    )
    for row, col in mirrored:
        distances = [
            min(abs(row - rr) + abs(col - cc) for rr, cc in cells)
            for cells in components
        ]
        if distances.index(min(distances)) != 0:
            return False
    return True


def _construct(height, width, orientation, side, shape_variant,
               distractor_color, distractor_shape, difficulty,
               require_first_object_refutation, ctx):
    candidates = list(_source_candidates(height, width, orientation, side, shape_variant))
    if not candidates:
        raise ValueError("requested source geometry has no legal placement")

    placement_rng = ctx.draw_rng("source_placement")
    placement_rng.shuffle(candidates)
    if difficulty == "easy":
        preferred = [candidate for candidate in candidates if candidate[3] <= 2]
        candidates = preferred or candidates
    elif difficulty == "hard":
        max_distance = max(candidate[3] for candidate in candidates)
        preferred = [candidate for candidate in candidates if candidate[3] >= max(2, max_distance - 1)]
        candidates = preferred or candidates

    for divider_index, source, mirrored, _distance in candidates:
        divider_cells = _divider_cells(height, width, orientation, divider_index)
        blocked = divider_cells | set(source) | set(mirrored)
        distractors = _valid_distractor_placements(
            height, width, orientation, divider_index, distractor_shape, blocked
        )
        if require_first_object_refutation:
            distractors = [
                distractor
                for distractor in distractors
                if not _first_object_shortcut_fits_layout(
                    divider_cells, source, mirrored, distractor
                )
            ]
        if not distractors:
            continue
        distractor = ctx.draw_rng(
            f"distractor_placement:{divider_index}:{source[0]}"
        ).choice(distractors)
        grid = full_grid(height, width, 0)
        for row, col in divider_cells:
            grid[row][col] = 5
        for row, col in source:
            grid[row][col] = 2
        for row, col in distractor:
            grid[row][col] = distractor_color
        return grid
    raise ValueError("requested axis combination has no joint source/distractor placement")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    profile = _DEFAULT_PROFILES[schedule_profile(seed, sample_index, difficulty)]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_scheduled_int(ctx, overrides, "grid_h", profile["grid_h"], 9, 12)
    width = _draw_scheduled_int(ctx, overrides, "grid_w", profile["grid_w"], 10, 13)
    orientation = _draw_scheduled_choice(
        ctx, overrides, "orientation", profile["orientation"], _ORIENTATIONS
    )
    side = _draw_scheduled_choice(ctx, overrides, "source_side", profile["source_side"], _SIDES)
    profile_index = schedule_profile(seed, sample_index, difficulty)
    if profile["shape_variant"] < 4:
        default_shape_variant = (seed + sample_index // 4 + profile_index) % 4
    else:
        default_shape_variant = 4 + (3 * seed + sample_index // 4 + profile_index) % 8
    default_distractor_color = _DISTRACTOR_COLORS[(seed + 2 * sample_index) % len(_DISTRACTOR_COLORS)]
    default_distractor_shape = (3 * seed + 5 * sample_index) % len(DISTRACTOR_SHAPES)
    shape_variant = _draw_scheduled_int(
        ctx, overrides, "shape_variant", default_shape_variant, 0, len(SOURCE_SHAPES) - 1
    )
    distractor_color = _draw_scheduled_choice(
        ctx, overrides, "distractor_color", default_distractor_color, _DISTRACTOR_COLORS
    )
    distractor_shape = _draw_scheduled_int(
        ctx, overrides, "distractor_shape", default_distractor_shape, 0,
        len(DISTRACTOR_SHAPES) - 1
    )
    geometry_overridden = any(
        overrides.get(name) is not None
        for name in (
            "grid_h", "grid_w", "orientation", "source_side",
            "shape_variant", "distractor_shape",
        )
    )
    grid = _construct(
        height, width, orientation, side, shape_variant,
        distractor_color, distractor_shape, difficulty,
        not geometry_overridden and profile_index in (0, 3), ctx
    )
    expected = {
        "grid_h": height,
        "grid_w": width,
        "orientation": orientation,
        "source_side": side,
        "shape_variant": shape_variant,
        "distractor_color": distractor_color,
        "distractor_shape": distractor_shape,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"constructed grid violated exact controls: {observed} != {expected}")
    diagnostics = self_check(grid)
    if diagnostics:
        raise RuntimeError(f"constructed grid failed self_check: {diagnostics}")
    return grid


# --- Executable semantic shortcuts and witness predicates -----------------

def _negative_side_only(grid):
    return rule_mirror(grid) if _source_side(grid) == "negative" else [list(row) for row in grid]


def _vertical_only(grid):
    return rule_mirror(grid) if _divider(grid)[0] == "vertical" else [list(row) for row in grid]


def _tetromino_only(grid):
    return rule_mirror(grid) if len(_red_cells(grid)) == 4 else [list(row) for row in grid]


def _reflect_all_colored(grid):
    out = [list(row) for row in grid]
    orientation, divider_index = _divider(grid)
    height, width = len(grid), len(grid[0])
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    for point in points:
        rr, cc = _reflect(point, orientation, divider_index)
        if 0 <= rr < height and 0 <= cc < width and out[rr][cc] == 0:
            out[rr][cc] = 3
    return out


def _ordered_nonzero_objects(grid):
    """Row-major, same-color 4-connected objects used by the review gate."""
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value
    }
    result = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells = {start}
        todo = [start]
        remaining.remove(start)
        while todo:
            row, col = todo.pop()
            for point in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1),
            ):
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(tuple(sorted(cells)))
    return result


def _first_object_only(grid):
    """Shortcut: retain only output fills attributed to the first input object."""
    out = rule_mirror(grid)
    components = _ordered_nonzero_objects(grid)
    for row, values in enumerate(out):
        for col, value in enumerate(values):
            if value == grid[row][col]:
                continue
            distances = [
                min(abs(row - rr) + abs(col - cc) for rr, cc in cells)
                for cells in components
            ]
            if distances.index(min(distances)) != 0:
                out[row][col] = grid[row][col]
    return out


def _positive_source(grid):
    return _source_side(grid) == "positive"


def _horizontal_divider(grid):
    return _divider(grid)[0] == "horizontal"


def _triomino_source(grid):
    return len(_red_cells(grid)) == 3


def _nonred_distractor(grid):
    return any(value not in (0, 2, 5) for row in grid for value in row)


def _first_object_refuter(grid):
    return _first_object_only(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "positive_source": _positive_source,
    "horizontal_divider": _horizontal_divider,
    "triomino_source": _triomino_source,
    "nonred_distractor": _nonred_distractor,
    "first_object_refuter": _first_object_refuter,
}
SEMANTIC_RIVALS = {
    "negative_side_only": _negative_side_only,
    "vertical_only": _vertical_only,
    "tetromino_only": _tetromino_only,
    "reflect_all_colored": _reflect_all_colored,
    "first_object_only": _first_object_only,
}
WITNESS_RIVALS = {
    "positive_source": ["negative_side_only"],
    "horizontal_divider": ["vertical_only"],
    "triomino_source": ["tetromino_only"],
    "nonred_distractor": ["reflect_all_colored"],
    "first_object_refuter": ["first_object_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # pragma: no cover - gate reports exact failure
            reasons.append(f"rival {name} failed: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"rival {name} fits demonstrations but changes query")
    return reasons
