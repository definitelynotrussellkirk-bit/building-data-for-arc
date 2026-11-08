"""Generator for ARC task ``cefd2849a551`` — Object Outline Only.

A lawful input contains one solid, hole-free, 4-connected monochrome object on
background 0.  The selected Racket authority emits the object's 4-neighbour
boundary in the original colour and erases every 4-neighbour interior cell.

The four-sample teaching schedule cycles through a rectangle, a one-cell corner
step, a larger corner-notch L, and a thick T.  Every shape has an interior;
the three concave profiles distinguish the intended 4-neighbour boundary from
an 8-neighbour outline and a bounding-box perimeter shortcut.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cefd2849a551"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "4681778f7a43"

SUMMARY = (
    "One solid 4-connected object on background 0 is replaced by its "
    "same-colour 4-neighbour boundary; interior cells become 0."
)
INVARIANTS = [
    "the grid is rectangular ARC data with background 0",
    "exactly one nonzero colour forms exactly one 4-connected object",
    "the object is hole-free, does not touch the canvas edge, and has interior",
    "the selected canonical Racket program is output authority",
]

SHAPE_KINDS = ("rect", "step", "L", "T")
PALETTE_KINDS = ("default", "warm", "cool", "varied")
PALETTES = {
    "default": (4,),
    "warm": (2, 3),
    "cool": (1, 8),
    "varied": (6, 7, 9),
}
GRID_H_RANGE = (6, 16)
GRID_W_RANGE = (7, 18)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchors or banded keyed choice",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchors or banded keyed choice",
        "valid": "7..18",
    },
    "shape_kind": {
        "type": "str",
        "default": "sample_index mod 4",
        "valid": "rect|step|L|T",
    },
    "palette_kind": {
        "type": "str",
        "default": "keyed choice",
        "valid": "default|warm|cool|varied",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = SHAPE_KINDS
MIN_STRICT_FRAC = 1.0

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)
Grid = list[list[int]]
Cell = tuple[int, int]
Rival = Callable[[Sequence[Sequence[int]]], Grid]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(sorted(unknown)))
    clean = {name: value for name, value in overrides.items() if value is not None}

    for name, (low, high) in (
        ("grid_h", GRID_H_RANGE),
        ("grid_w", GRID_W_RANGE),
    ):
        if name in clean and (
            type(clean[name]) is not int or not low <= clean[name] <= high
        ):
            raise ValueError(f"{name} must be an integer in {low}..{high}")
    for name, choices in (
        ("shape_kind", SHAPE_KINDS),
        ("palette_kind", PALETTE_KINDS),
    ):
        if name in clean and (
            type(clean[name]) is not str or clean[name] not in choices
        ):
            raise ValueError(f"{name} must be one of {choices}")
    return clean


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the shape profile; every consecutive four indices are complete."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _axis_choice(ctx, name: str, legal: Sequence[Any], defaults: Sequence[Any]):
    options = legal if name in ctx.overrides else defaults
    return ctx.draw_choice(name, tuple(options))


def _dimension_defaults(profile_index: int, difficulty: str | None):
    # Two of every four samples are exact canonical profiles.  This deliberately
    # makes the strict profile floor robust in every difficulty band while the
    # other two profiles retain broad shape and placement diversity.
    if profile_index == 0:
        return (6,), (9,)
    if profile_index == 1:
        return (6,), (7,)
    band = difficulty or "medium"
    ranges = {
        "easy": ((6, 10), (7, 12)),
        "medium": ((7, 13), (8, 15)),
        "hard": ((10, 16), (12, 18)),
    }
    (h_low, h_high), (w_low, w_high) = ranges[band]
    return tuple(range(h_low, h_high + 1)), tuple(range(w_low, w_high + 1))


def _box_extent(rng, maximum: int, difficulty: str | None) -> int:
    minimum = 4
    if maximum <= minimum:
        return minimum
    band = difficulty or "medium"
    if band == "easy":
        high = max(minimum, minimum + (maximum - minimum) // 2)
        return rng.randint(minimum, high)
    if band == "hard":
        low = min(maximum, minimum + (maximum - minimum + 1) // 2)
        return rng.randint(low, maximum)
    return rng.randint(minimum, maximum)


def _corner_predicate(
    corner: int,
    height: int,
    width: int,
    notch_h: int,
    notch_w: int,
):
    def is_removed(row: int, col: int) -> bool:
        top = row < notch_h
        bottom = row >= height - notch_h
        left = col < notch_w
        right = col >= width - notch_w
        return (
            (corner == 0 and top and left)
            or (corner == 1 and top and right)
            or (corner == 2 and bottom and right)
            or (corner == 3 and bottom and left)
        )

    return is_removed


def _shape_mask(rng, shape_kind: str, height: int, width: int) -> set[Cell]:
    all_cells = {(row, col) for row in range(height) for col in range(width)}
    if shape_kind == "rect":
        return all_cells

    if shape_kind == "step":
        corner = rng.randrange(4)
        removed = _corner_predicate(corner, height, width, 1, 1)
        return {cell for cell in all_cells if not removed(*cell)}

    if shape_kind == "L":
        notch_h = rng.randint(1, height - 2)
        notch_w = rng.randint(1, width - 2)
        if notch_h * notch_w == 1:
            notch_w = 2
        corner = rng.randrange(4)
        removed = _corner_predicate(
            corner, height, width, notch_h, notch_w
        )
        return {cell for cell in all_cells if not removed(*cell)}

    # Thick T: a full top bar plus a centered stem.  Both side notches are
    # nonempty and disconnected inside the bounding box, making this profile
    # independently observable from the pixels.
    top_height = rng.randint(2, height - 2)
    stem_width = rng.randint(2, width - 2)
    stem_left = (width - stem_width) // 2
    stem_right = stem_left + stem_width
    mask = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row < top_height or stem_left <= col < stem_right
    }
    if rng.randrange(2):
        mask = {(height - 1 - row, col) for row, col in mask}
    return mask


def generate(seed, sample_index, *, difficulty=None, **overrides):
    clean = _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=clean,
    )

    profile_index = sample_index % LESSON_SCHEDULE_PERIOD
    default_heights, default_widths = _dimension_defaults(
        profile_index, difficulty
    )
    height = _axis_choice(
        ctx,
        "grid_h",
        tuple(range(GRID_H_RANGE[0], GRID_H_RANGE[1] + 1)),
        default_heights,
    )
    width = _axis_choice(
        ctx,
        "grid_w",
        tuple(range(GRID_W_RANGE[0], GRID_W_RANGE[1] + 1)),
        default_widths,
    )
    shape_kind = _axis_choice(
        ctx,
        "shape_kind",
        SHAPE_KINDS,
        (schedule_profile(seed, sample_index, difficulty),),
    )
    palette_kind = _axis_choice(
        ctx,
        "palette_kind",
        PALETTE_KINDS,
        PALETTE_KINDS,
    )
    color = ctx.draw_choice("object_color", PALETTES[palette_kind])

    rng = ctx.draw_rng("object_geometry")
    box_height = _box_extent(rng, height - 2, difficulty)
    box_width = _box_extent(rng, width - 2, difficulty)
    top = rng.randint(1, height - box_height - 1)
    left = rng.randint(1, width - box_width - 1)
    mask = _shape_mask(rng, shape_kind, box_height, box_width)

    grid = full_grid(height, width, 0)
    for row, col in mask:
        grid[top + row][left + col] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:  # construction invariant: loud, never silently resample/fallback
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    height = len(grid)
    if not GRID_H_RANGE[0] <= height <= GRID_H_RANGE[1]:
        return [f"height must be in {GRID_H_RANGE[0]}..{GRID_H_RANGE[1]}"]
    if not GRID_W_RANGE[0] <= width <= GRID_W_RANGE[1]:
        return [f"width must be in {GRID_W_RANGE[0]}..{GRID_W_RANGE[1]}"]
    return []


def _foreground(grid: Sequence[Sequence[int]]) -> tuple[int | None, set[Cell]]:
    colors = {
        value
        for row in grid
        for value in row
        if value != 0
    }
    if len(colors) != 1:
        return None, set()
    color = next(iter(colors))
    return color, {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def _connected(cells: set[Cell]) -> bool:
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        row, col = stack.pop()
        for dr, dc in CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    return not remaining


def _background_reachable(grid: Sequence[Sequence[int]]) -> set[Cell]:
    height, width = len(grid), len(grid[0])
    starts = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row in (0, height - 1) or col in (0, width - 1))
        and grid[row][col] == 0
    }
    queue = deque(starts)
    seen = set(starts)
    while queue:
        row, col = queue.popleft()
        for dr, dc in CARDINAL:
            neighbor = (row + dr, col + dc)
            if (
                0 <= neighbor[0] < height
                and 0 <= neighbor[1] < width
                and neighbor not in seen
                and grid[neighbor[0]][neighbor[1]] == 0
            ):
                seen.add(neighbor)
                queue.append(neighbor)
    return seen


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful single-solid-object manifold used by this task."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    colors = sorted(
        {
            value
            for row in grid
            for value in row
            if value != 0
        }
    )
    if len(colors) != 1:
        return [f"expected exactly one nonzero color; found {colors}"]
    color, cells = _foreground(grid)
    assert color is not None
    if not _connected(cells):
        errors.append("foreground must be one 4-connected component")
    if any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in cells
    ):
        errors.append("foreground must retain a one-cell background margin")
    interior = {
        (row, col)
        for row, col in cells
        if all((row + dr, col + dc) in cells for dr, dc in CARDINAL)
    }
    if not interior:
        errors.append("foreground must contain a 4-neighbour interior cell")
    background = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    }
    if not background:
        errors.append("grid must contain background 0")
    elif background - _background_reachable(grid):
        errors.append("foreground may not enclose a background hole")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold intentionally contains every canonical input."""
    return list(self_check(grid))


def _missing_components(cells: set[Cell]) -> list[set[Cell]]:
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    remaining = {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if (row, col) not in cells
    }
    result: list[set[Cell]] = []
    while remaining:
        component = {remaining.pop()}
        stack = list(component)
        while stack:
            row, col = stack.pop()
            for dr, dc in CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def observe_overrides(grid) -> dict[str, int | str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    color, cells = _foreground(grid)
    assert color is not None
    missing = _missing_components(cells)
    missing_count = sum(len(component) for component in missing)
    if missing_count == 0:
        shape_kind = "rect"
    elif missing_count == 1:
        shape_kind = "step"
    elif len(missing) == 1:
        shape_kind = "L"
    elif len(missing) == 2:
        shape_kind = "T"
    else:
        raise ValueError("object is outside the advertised shape grammar")

    palette_kind = next(
        (
            name
            for name, colors in PALETTES.items()
            if color in colors
        ),
        None,
    )
    if palette_kind is None:
        raise ValueError(f"color {color} is outside the advertised palettes")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_kind": shape_kind,
        "palette_kind": palette_kind,
    }


def _boundary_output(
    grid: Sequence[Sequence[int]],
    neighborhood: Iterable[tuple[int, int]],
) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid outline input: " + "; ".join(errors))
    color, cells = _foreground(grid)
    assert color is not None
    height, width = len(grid), len(grid[0])
    boundary = {
        (row, col)
        for row, col in cells
        if any(
            (row + dr, col + dc) not in cells
            for dr, dc in neighborhood
        )
    }
    return [
        [color if (row, col) in boundary else 0 for col in range(width)]
        for row in range(height)
    ]


def rule_mirror(grid) -> Grid:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    return _boundary_output(grid, CARDINAL)


def _rival_identity(grid) -> Grid:
    return deepcopy(grid)


def _rival_eight_neighbor_boundary(grid) -> Grid:
    return _boundary_output(grid, EIGHT)


def _rival_bbox_perimeter(grid) -> Grid:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid outline input: " + "; ".join(errors))
    color, cells = _foreground(grid)
    assert color is not None
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    height, width = len(grid), len(grid[0])
    return [
        [
            color
            if top <= row <= bottom
            and left <= col <= right
            and (row in (top, bottom) or col in (left, right))
            else 0
            for col in range(width)
        ]
        for row in range(height)
    ]


def _witness_has_erased_interior(grid) -> bool:
    try:
        return rule_mirror(grid) != _rival_identity(grid)
    except ValueError:
        return False


def _witness_four_not_eight(grid) -> bool:
    try:
        return rule_mirror(grid) != _rival_eight_neighbor_boundary(grid)
    except ValueError:
        return False


def _witness_not_bbox_perimeter(grid) -> bool:
    try:
        return rule_mirror(grid) != _rival_bbox_perimeter(grid)
    except ValueError:
        return False


SEMANTIC_WITNESSES = {
    "interior_is_erased": _witness_has_erased_interior,
    "four_neighbor_not_eight": _witness_four_not_eight,
    "object_outline_not_bbox": _witness_not_bbox_perimeter,
}
SEMANTIC_RIVALS: dict[str, Rival] = {
    "identity": _rival_identity,
    "eight_neighbor_boundary": _rival_eight_neighbor_boundary,
    "bbox_perimeter": _rival_bbox_perimeter,
}
WITNESS_RIVALS = {
    "interior_is_erased": ("identity",),
    "four_neighbor_not_eight": ("eight_neighbor_boundary",),
    "object_outline_not_bbox": ("bbox_perimeter",),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Rival] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to refute every declared plausible rival."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(deepcopy(pair["input"]))
        except Exception as exc:
            reasons.append(
                f"demo {index} is invalid: {type(exc).__name__}: {exc}"
            )
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the outline rule")

    try:
        query_answer = rule_mirror(deepcopy(query["input"]))
    except Exception as exc:
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the outline rule")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output")
            for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons


def mutation_fixtures():
    """Task-local must-reject semantic near misses for the defect linter."""
    blank = full_grid(6, 7, 0)
    singleton = full_grid(6, 7, 0)
    singleton[2][3] = 4
    hollow = full_grid(6, 7, 0)
    for col in range(1, 6):
        hollow[1][col] = hollow[4][col] = 4
    for row in range(1, 5):
        hollow[row][1] = hollow[row][5] = 4
    disconnected = full_grid(6, 7, 0)
    for row in range(1, 4):
        for col in range(1, 4):
            disconnected[row][col] = 4
    disconnected[4][5] = 4
    return [
        ("blank", blank),
        ("singleton", singleton),
        ("hollow_ring", hollow),
        ("disconnected_extra_cell", disconnected),
    ]
