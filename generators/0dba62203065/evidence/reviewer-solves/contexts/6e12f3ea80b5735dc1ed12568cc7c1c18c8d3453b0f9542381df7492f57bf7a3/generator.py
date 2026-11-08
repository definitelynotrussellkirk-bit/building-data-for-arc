"""Generate lessons for ARC task 0dba62203065.

The first row is a full color header over ARC colors 2..8. Every blue (1) body
object is recolored uniformly with the *actual* header color above the object's
bounding-box left edge. Row-2 lessons retain the canonical cyclic header;
row-1 lessons swap one later object-anchor entry with a non-anchor entry while
preserving header cells 0 and 1. That counterexample defeats a solver that
reconstructs the complete cycle from the first two cells instead of reading the
lookup cell. The last body column stays empty because the selected Racket
authority intentionally excludes it from the object subgrid.

Ordinary lessons alternate two decisive controls:

* body objects begin in row 1 vs. row 2, refuting a hard-coded separator-row
  shortcut;
* canonical size multiset (2, 3, 3) vs. an extended (2, 3, 4) multiset,
  refuting the canonical-ambiguous "only recolor observed small objects"
  shortcut.

Every generated scene also contains a component whose row-major first cell is
not in its leftmost column. That directly separates the selected bbox-left rule
from the tempting first/topmost-cell-column rule. Difficulty is a real,
controlled distribution knob: easy defaults to ascending base cycles, medium
samples either direction, and hard defaults to descending base cycles;
explicit header-direction overrides still win exactly.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "0dba62203065"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "75437b07b887"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid has a FULL header row exposing colors 2..8. Its "
    "base is an ascending or descending cyclic sequence; row-1 lessons swap one later "
    "object-anchor entry with a non-anchor entry, so the actual lookup cells "
    "must be read. The body contains three isolated blue (1) objects. Recolor "
    "every object uniformly with the header color above the object's bounding-"
    "box LEFTMOST column; preserve the header and all background cells. The "
    "body's final column remains blank because the selected rule excludes it "
    "from object extraction."
)

INVARIANTS = [
    "row 0 exposes colors 2..8 and is a base cycle or one controlled anchor swap",
    "the body uses only background 0 and object color 1",
    "exactly three isolated 4-connected body objects have size multiset (2,3,3) or (2,3,4)",
    "the last body column is blank, matching the selected Racket subgrid",
    "at least one object separates bbox-left from row-major-first-column interpretations",
    "row-1 lessons change a real object-anchor header entry while preserving header cells 0 and 1",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

HEADER_COLORS = tuple(range(2, 9))
HEADER_DIRECTIONS = ("ascending", "descending")
LEGEND_PROFILES = ("cyclic", "anchor_swap")
BLOB_PROFILES = ("canonical", "extended")
SCHEDULE_PROFILES = BLOB_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "8x10 / 9x11 / 10x12 canonical-profile cycle",
        "valid": "8..12",
    },
    "grid_w": {
        "type": "int",
        "default": "8x10 / 9x11 / 10x12 canonical-profile cycle",
        "valid": "10..13",
    },
    "header_start": {
        "type": "int",
        "default": "rng color 2..8",
        "valid": "2..8",
    },
    "header_direction": {
        "type": "str",
        "default": "easy=ascending, medium=rng, hard=descending",
        "valid": "ascending|descending",
    },
    "body_origin": {
        "type": "int",
        "default": "alternating 2|1 schedule",
        "valid": "1..2",
    },
    "blob_profile": {
        "type": "str",
        "default": "alternating canonical|extended schedule",
        "valid": "canonical|extended",
    },
}

_CANONICAL_DIMENSIONS = ((8, 10), (9, 11), (10, 12))
_PROFILE_SIZES = {
    "canonical": (2, 3, 3),
    "extended": (2, 3, 4),
}

# Coordinates are relative to a shape's top-left corner.
_TRAP_SHAPES = {
    # Row-major first cell is at column +1, while bbox-left is column +0.
    "canonical": ((0, 1), (1, 0), (1, 1)),
    "extended": ((0, 1), (1, 0), (1, 1), (1, 2)),
}
_SIZE_THREE_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 1), (1, 0), (1, 1)),
)
_SIZE_TWO_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
)

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = tuple[Cell, ...]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override(s): {', '.join(unknown)}; valid axes: {', '.join(AXES)}"
        )

    for name, lo, hi in (
        ("grid_h", 8, 12),
        ("grid_w", 10, 13),
        ("header_start", 2, 8),
        ("body_origin", 1, 2),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    direction = overrides.get("header_direction")
    if direction is not None and direction not in HEADER_DIRECTIONS:
        raise ValueError(
            f"header_direction must be one of {HEADER_DIRECTIONS}, found {direction!r}"
        )
    profile = overrides.get("blob_profile")
    if profile is not None and profile not in BLOB_PROFILES:
        raise ValueError(f"blob_profile must be one of {BLOB_PROFILES}, found {profile!r}")
    return band


def _draw_int_axis(
    ctx: Any,
    name: str,
    default: int,
    lo: int,
    hi: int,
    overrides: dict[str, Any],
) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_int(name, default, default))


def _draw_choice_axis(
    ctx: Any,
    name: str,
    default: str,
    options: tuple[str, ...],
    overrides: dict[str, Any],
) -> str:
    if name in overrides and overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Expose the two-slot semantic schedule to the coverage gate."""
    del seed, difficulty
    return BLOB_PROFILES[int(sample_index) % len(BLOB_PROFILES)]


def schedule_legend_profile(
    seed: int,
    sample_index: int,
    difficulty: str | None = None,
) -> str:
    """Alternate canonical cycles with a direct header-lookup counterexample."""
    del seed, difficulty
    return LEGEND_PROFILES[int(sample_index) % len(LEGEND_PROFILES)]


def _header(width: int, start: int, direction: str) -> list[int]:
    step = 1 if direction == "ascending" else -1
    start_index = HEADER_COLORS.index(start)
    return [HEADER_COLORS[(start_index + step * col) % len(HEADER_COLORS)] for col in range(width)]


def _anchor_swap_header(
    header: list[int],
    placements: list[tuple[Cell, ...]],
    rng: Any,
) -> list[int]:
    """Swap one object-anchor legend cell with a non-anchor while preserving cells 0..1."""
    left_columns = {min(col for _, col in cells) for cells in placements}
    trap = placements[0]
    trap_top = min(row for row, _ in trap)
    trap_left = min(col for _, col in trap)
    trap_first = min(col for row, col in trap if row == trap_top)
    anchor_candidates = [col for col in sorted(left_columns) if col >= 2]
    rng.shuffle(anchor_candidates)
    for anchor in anchor_candidates:
        partner_candidates = [
            col
            for col in range(2, len(header))
            if col != anchor
            and col not in left_columns
            and header[col] != header[anchor]
        ]
        rng.shuffle(partner_candidates)
        for partner in partner_candidates:
            result = header[:]
            result[anchor], result[partner] = result[partner], result[anchor]
            if result[trap_left] == result[trap_first]:
                continue
            return result
    raise ValueError("cannot construct anchor_swap legend profile")


def _shape_bounds(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _translate(shape: Shape, top: int, left: int) -> tuple[Cell, ...]:
    return tuple((top + row, left + col) for row, col in shape)


def _has_moat(cells: Iterable[Cell], occupied: set[Cell]) -> bool:
    """Require a one-cell Chebyshev moat between distinct objects."""
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (row + dr, col + dc) in occupied:
                    return False
    return True


def _candidate_placements(
    shape: Shape,
    height: int,
    width: int,
    body_origin: int,
    *,
    force_top: bool,
) -> list[tuple[Cell, ...]]:
    shape_h, shape_w = _shape_bounds(shape)
    # The authority's body subgrid has width (cols - 1), so usable columns are
    # 0..width-2 and a shape's right edge must be <= width-2.
    max_left = (width - 1) - shape_w
    if max_left < 0 or body_origin + shape_h > height:
        return []
    rows = (body_origin,) if force_top else range(body_origin, height - shape_h + 1)
    return [
        _translate(shape, top, left)
        for top in rows
        for left in range(max_left + 1)
    ]


def _place_shapes(
    height: int,
    width: int,
    body_origin: int,
    shapes: tuple[Shape, ...],
    rng: Any,
) -> list[tuple[Cell, ...]]:
    """Backtrack over tiny candidate sets; guarantees exact object counts."""
    candidate_sets: list[list[tuple[Cell, ...]]] = []
    for index, shape in enumerate(shapes):
        candidates = _candidate_placements(
            shape,
            height,
            width,
            body_origin,
            force_top=index == 0,
        )
        rng.shuffle(candidates)
        candidate_sets.append(candidates)

    def search(
        index: int,
        occupied: set[Cell],
        left_columns: set[int],
        chosen: list[tuple[Cell, ...]],
    ) -> list[tuple[Cell, ...]] | None:
        if index == len(candidate_sets):
            return chosen[:]
        for cells in candidate_sets[index]:
            left = min(col for _, col in cells)
            if left in left_columns or not _has_moat(cells, occupied):
                continue
            chosen.append(cells)
            result = search(
                index + 1,
                occupied | set(cells),
                left_columns | {left},
                chosen,
            )
            if result is not None:
                return result
            chosen.pop()
        return None

    result = search(0, set(), set(), [])
    if result is None:
        raise ValueError(
            f"cannot place profile shapes in {height}x{width} with body_origin={body_origin}"
        )
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _CANONICAL_DIMENSIONS[int(sample_index) % 3]
    scheduled_origin = 2 if int(sample_index) % 2 == 0 else 1
    scheduled_profile = schedule_profile(seed, sample_index, difficulty)

    height = _draw_int_axis(ctx, "grid_h", scheduled_h, 8, 12, overrides)
    width = _draw_int_axis(ctx, "grid_w", scheduled_w, 10, 13, overrides)
    header_start = int(ctx.draw_int("header_start", 2, 8))
    if band == "medium":
        header_direction = str(ctx.draw_choice("header_direction", HEADER_DIRECTIONS))
    else:
        scheduled_direction = "ascending" if band == "easy" else "descending"
        header_direction = _draw_choice_axis(
            ctx,
            "header_direction",
            scheduled_direction,
            HEADER_DIRECTIONS,
            overrides,
        )
    body_origin = _draw_int_axis(ctx, "body_origin", scheduled_origin, 1, 2, overrides)
    blob_profile = _draw_choice_axis(
        ctx,
        "blob_profile",
        scheduled_profile,
        BLOB_PROFILES,
        overrides,
    )
    # Row-1 lessons carry the non-cyclic counterexample. Coupling this to the
    # existing body-origin schedule preserves the public six-axis API and makes
    # the existing row_one_body witness cover both shortcuts exactly.
    legend_profile = "anchor_swap" if body_origin == 1 else "cyclic"

    rng = ctx.draw_rng("layout")
    other_three = _SIZE_THREE_SHAPES[rng.randrange(len(_SIZE_THREE_SHAPES))]
    size_two = _SIZE_TWO_SHAPES[rng.randrange(len(_SIZE_TWO_SHAPES))]
    shapes = (_TRAP_SHAPES[blob_profile], other_three, size_two)
    placements = _place_shapes(height, width, body_origin, shapes, rng)

    header = _header(width, header_start, header_direction)
    if legend_profile == "anchor_swap":
        header = _anchor_swap_header(
            header,
            placements,
            ctx.draw_rng("legend_perturbation"),
        )

    grid = full_grid(height, width, 0)
    grid[0] = header
    for cells in placements:
        for row, col in cells:
            grid[row][col] = 1

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "header_start": header_start,
        "header_direction": header_direction,
        "body_origin": body_origin,
        "blob_profile": blob_profile,
    }
    if observed != expected:
        raise AssertionError(f"axis provenance mismatch: expected {expected}, observed {observed}")
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list or tuple"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a non-empty list or tuple"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid: Grid) -> list[tuple[Cell, ...]]:
    """4-connected non-background objects in the authority's body subgrid."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[tuple[Cell, ...]] = []
    for row in range(1, height):
        for col in range(width - 1):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (r + dr, c + dc)
                    rr, cc = neighbor
                    if (
                        1 <= rr < height
                        and 0 <= cc < width - 1
                        and grid[rr][cc] != 0
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(cells)))
    return sorted(
        components,
        key=lambda cells: (min(row for row, _ in cells), min(col for _, col in cells)),
    )


def _header_analysis(row: list[int]) -> dict[str, Any] | None:
    """Recognize an exact cycle or one controlled swap beyond cells 0 and 1."""
    if len(row) < 2 or row[0] not in HEADER_COLORS:
        return None

    matches: list[dict[str, Any]] = []
    for direction in HEADER_DIRECTIONS:
        base = _header(len(row), row[0], direction)
        changed = tuple(index for index, (actual, expected) in enumerate(zip(row, base)) if actual != expected)
        if not changed:
            matches.append(
                {
                    "direction": direction,
                    "legend_profile": "cyclic",
                    "base_header": base,
                    "changed_columns": changed,
                }
            )
            continue
        if len(changed) != 2 or min(changed) < 2:
            continue
        first, second = changed
        if row[first] == base[second] and row[second] == base[first]:
            matches.append(
                {
                    "direction": direction,
                    "legend_profile": "anchor_swap",
                    "base_header": base,
                    "changed_columns": changed,
                }
            )

    return matches[0] if len(matches) == 1 else None


def _header_direction(row: list[int]) -> str | None:
    analysis = _header_analysis(row)
    return None if analysis is None else str(analysis["direction"])


def _analysis(grid: Any) -> tuple[dict[str, Any], list[str]]:
    errors = _basic_grid_errors(grid)
    if errors:
        return {}, errors
    grid = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    if not 8 <= height <= 12:
        errors.append(f"height {height} outside supported 8..12")
    if not 10 <= width <= 13:
        errors.append(f"width {width} outside supported 10..13")

    header = grid[0]
    header_analysis = _header_analysis(header)
    direction = None if header_analysis is None else header_analysis["direction"]
    legend_profile = None if header_analysis is None else header_analysis["legend_profile"]
    changed_columns: tuple[int, ...] = (
        () if header_analysis is None else tuple(header_analysis["changed_columns"])
    )
    if header_analysis is None:
        errors.append(
            "row 0 must be an ascending/descending cycle over colors 2..8 or one "
            "two-cell anchor swap that preserves header cells 0 and 1"
        )
    elif set(header) != set(HEADER_COLORS):
        errors.append("row 0 must expose all seven header colors 2..8")

    illegal_body = sorted(
        {
            grid[row][col]
            for row in range(1, height)
            for col in range(width)
            if grid[row][col] not in (0, 1)
        }
    )
    if illegal_body:
        errors.append(f"body contains colors {illegal_body}; expected only 0 and 1")
    if any(grid[row][width - 1] != 0 for row in range(1, height)):
        errors.append("last body column must be blank because the selected rule excludes it")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly 3 body objects, found {len(components)}")
    sizes = tuple(sorted(len(cells) for cells in components))
    profile = next((name for name, expected in _PROFILE_SIZES.items() if sizes == expected), None)
    if profile is None:
        errors.append(
            f"object size multiset {sizes} is neither canonical {_PROFILE_SIZES['canonical']} "
            f"nor extended {_PROFILE_SIZES['extended']}"
        )

    body_origin = min((row for cells in components for row, _ in cells), default=None)
    if body_origin not in (1, 2):
        errors.append(f"first occupied body row must be 1 or 2, found {body_origin}")
    left_columns = [min(col for _, col in cells) for cells in components]
    if len(set(left_columns)) != len(left_columns):
        errors.append("body objects must have distinct bounding-box left columns")
    if legend_profile == "anchor_swap" and not set(changed_columns).intersection(left_columns):
        errors.append("anchor_swap must change the header above at least one object left edge")

    features = {
        "grid_h": height,
        "grid_w": width,
        "header_start": header[0] if header else None,
        "header_direction": direction,
        "legend_profile": legend_profile,
        "body_origin": body_origin,
        "blob_profile": profile,
        "components": components,
        "sizes": sizes,
    }
    return features, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    features, errors = _analysis(grid)
    if errors:
        return errors

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    for axis, expected in requested.items():
        if axis in AXES and expected is not None and features.get(axis) != expected:
            errors.append(
                f"requested {axis}={expected!r}, observed {features.get(axis)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is a strict superset containing every public input."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    features, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe invalid lesson: " + "; ".join(errors))
    return {
        "grid_h": int(features["grid_h"]),
        "grid_w": int(features["grid_w"]),
        "header_start": int(features["header_start"]),
        "header_direction": str(features["header_direction"]),
        "body_origin": int(features["body_origin"]),
        "blob_profile": str(features["blob_profile"]),
    }


def observe_legend_profile(grid) -> str:
    """Return the internal lesson profile without expanding the public override API."""
    features, errors = _analysis(grid)
    if errors:
        raise ValueError("cannot observe invalid lesson: " + "; ".join(errors))
    return str(features["legend_profile"])


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror of the selected bbox-left Racket rule."""
    output = deepcopy(grid)
    for cells in _components(grid):
        left = min(col for _, col in cells)
        color = grid[0][left]
        for row, col in cells:
            output[row][col] = color
    return output


def _rival_first_cell_column(grid: Grid) -> Grid:
    """Tempting shortcut: index the header by each object's row-major first cell."""
    output = deepcopy(grid)
    for cells in _components(grid):
        first = min(cells)
        color = grid[0][first[1]]
        for row, col in cells:
            output[row][col] = color
    return output


def _rival_per_cell_column(grid: Grid) -> Grid:
    """Tempting shortcut: independently project every blue cell to its header."""
    output = deepcopy(grid)
    for cells in _components(grid):
        for row, col in cells:
            output[row][col] = grid[0][col]
    return output


def _rival_skip_row_one(grid: Grid) -> Grid:
    """Tempting shortcut: assume row 1 is always a separator and ignore it."""
    output = deepcopy(grid)
    for cells in _components(grid):
        left = min(col for _, col in cells)
        color = grid[0][left]
        for row, col in cells:
            if row >= 2:
                output[row][col] = color
    return output


def _rival_size_at_most_three(grid: Grid) -> Grid:
    """Canonical-ambiguous shortcut: only recolor the object sizes seen publicly."""
    output = deepcopy(grid)
    for cells in _components(grid):
        if len(cells) > 3:
            continue
        left = min(col for _, col in cells)
        color = grid[0][left]
        for row, col in cells:
            output[row][col] = color
    return output


def _rival_cycle_from_first_two(grid: Grid) -> Grid:
    """Canonical shortcut: reconstruct the legend cycle and ignore later header cells."""
    start_index = HEADER_COLORS.index(grid[0][0])
    if grid[0][1] == HEADER_COLORS[(start_index + 1) % len(HEADER_COLORS)]:
        direction = "ascending"
    elif grid[0][1] == HEADER_COLORS[(start_index - 1) % len(HEADER_COLORS)]:
        direction = "descending"
    else:
        raise ValueError("first two header cells do not identify a cyclic direction")
    inferred_header = _header(len(grid[0]), grid[0][0], direction)

    output = deepcopy(grid)
    for cells in _components(grid):
        left = min(col for _, col in cells)
        color = inferred_header[left]
        for row, col in cells:
            output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "first_cell_column": _rival_first_cell_column,
    "per_cell_column": _rival_per_cell_column,
    "skip_row_one": _rival_skip_row_one,
    "size_at_most_three": _rival_size_at_most_three,
    "cycle_from_first_two": _rival_cycle_from_first_two,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "size_at_most_three": _rival_size_at_most_three,
    "cycle_from_first_two": _rival_cycle_from_first_two,
}


def _witness_topmost_cell_not_leftmost(grid: Grid) -> bool:
    for cells in _components(grid):
        top = min(row for row, _ in cells)
        top_left = min(col for row, col in cells if row == top)
        if top_left != min(col for _, col in cells):
            return True
    return False


def _witness_multi_column_object(grid: Grid) -> bool:
    return any(len({col for _, col in cells}) > 1 for cells in _components(grid))


def _witness_row_one_body(grid: Grid) -> bool:
    return any(row == 1 for cells in _components(grid) for row, _ in cells)


SEMANTIC_WITNESSES = {
    "topmost_cell_not_leftmost": _witness_topmost_cell_not_leftmost,
    "multi_column_object": _witness_multi_column_object,
    "row_one_body": _witness_row_one_body,
}
WITNESS_RIVALS = {
    "topmost_cell_not_leftmost": ["first_cell_column"],
    "multi_column_object": ["per_cell_column", "size_at_most_three"],
    "row_one_body": ["skip_row_one", "cycle_from_first_two"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when a declared competing rule survives every demo."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    refuted = {name: False for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {errors[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(pair["input"]) != truth:
                refuted[name] = True

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute competitor {name!r}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input invalid: {query_errors[0]}")
        return reasons
    truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != truth:
        reasons.append("query output disagrees with the selected rule")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and {"input", "output"} <= set(pair)
            and competitor(pair["input"]) == pair["output"]
            for pair in demos
        ) and competitor(query["input"]) != truth:
            reasons.append(
                f"competitor {name!r} fits every demo but changes the query answer"
            )
    return reasons
