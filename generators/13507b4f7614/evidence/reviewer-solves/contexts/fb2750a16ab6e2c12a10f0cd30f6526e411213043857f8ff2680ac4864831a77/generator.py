"""Generator for ARC task 13507b4f7614 — rectangles to center crosses.

The selected Racket authority reduces every odd-by-odd solid color-4 rectangle
to its middle row plus middle column and leaves other objects unchanged.  This
sampler keeps the public control surface deliberately small and observable:
``grid_profile`` selects one exact canvas shape.  A deterministic four-scene
schedule varies object count and includes both odd-only and odd/even lessons so
the hidden odd-dimension guard is taught rather than merely encoded.
"""
from __future__ import annotations

from collections import deque
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "13507b4f7614"
TASK_ID = GENERATOR_ID
RULE_HASH = "812105731900"
VERSION = "2.0.0"
SUMMARY = (
    "Two or three separated solid yellow rectangles. Odd-by-odd rectangles "
    "reduce to center crosses; an occasional even rectangle remains unchanged."
)

INVARIANTS = [
    "background is 0 and every foreground cell is color 4",
    "foreground components are solid axis-aligned rectangles with a blank margin",
    "rectangles are separated from one another by at least one blank row or column",
    "every input has at least one odd-by-odd rectangle; scheduled mixed scenes add one even rectangle",
]

_GRID_DIMS = {
    "canonical_9x12": (9, 12),
    "canonical_11x11": (11, 11),
    "canonical_12x13": (12, 13),
    "wide_10x16": (10, 16),
    "tall_16x10": (16, 10),
    "large_16x18": (16, 18),
}
GRID_PROFILES = tuple(_GRID_DIMS)
AXES = {
    "grid_profile": {
        "type": "str",
        "default": "difficulty-weighted exact canvas profile",
        "valid": "canonical_9x12|canonical_11x11|canonical_12x13|wide_10x16|tall_16x10|large_16x18",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = (
    "odd_two",
    "mixed_two",
    "odd_three",
    "mixed_three",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_SCENE_PARITIES = {
    "odd_two": ("odd", "odd"),
    "mixed_two": ("odd", "even"),
    "odd_three": ("odd", "odd", "odd"),
    "mixed_three": ("odd", "odd", "even"),
}

# All bands retain substantial exact canonical-profile support. Repetition is
# intentional weighting; every listed value remains a valid exact override.
_PROFILE_OPTIONS = {
    None: (
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "wide_10x16", "tall_16x10", "large_16x18",
    ),
    "easy": (
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "wide_10x16", "tall_16x10", "large_16x18",
    ),
    "medium": (
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "wide_10x16", "tall_16x10", "large_16x18",
    ),
    "hard": (
        "canonical_9x12", "canonical_11x11", "canonical_12x13",
        "wide_10x16", "wide_10x16",
        "tall_16x10", "tall_16x10",
        "large_16x18", "large_16x18",
    ),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the source-independent scene profile for this lesson position."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _axis_bands(length: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Two interior bands separated by one guaranteed blank coordinate."""
    gap = length // 2
    upper = (1, gap - 1)
    lower = (gap + 1, length - 2)
    if upper[1] - upper[0] + 1 < 3 or lower[1] - lower[0] + 1 < 3:
        raise ValueError(f"canvas dimension {length} is too small for the slot grammar")
    return upper, lower


def _dimension_choices(maximum: int, parity: str) -> list[int]:
    if parity == "odd":
        return [value for value in (3, 5, 7) if value <= maximum]
    if parity == "even":
        return [value for value in (2, 4, 6) if value <= maximum]
    raise ValueError(f"unknown rectangle parity {parity!r}")


def _draw_scene(ctx, height: int, width: int, scene_profile: str):
    row_bands = _axis_bands(height)
    col_bands = _axis_bands(width)
    slots = [
        (row_band, col_band)
        for row_band in row_bands
        for col_band in col_bands
    ]
    rng = ctx.draw_rng("rectangle_layout")
    rng.shuffle(slots)
    parities = list(_SCENE_PARITIES[scene_profile])
    rng.shuffle(parities)

    grid = full_grid(height, width, 0)
    for parity, slot in zip(parities, slots):
        (row_lo, row_hi), (col_lo, col_hi) = slot
        row_sizes = _dimension_choices(row_hi - row_lo + 1, parity)
        col_sizes = _dimension_choices(col_hi - col_lo + 1, parity)
        if not row_sizes or not col_sizes:
            raise ValueError(
                f"grid profile cannot fit {parity} rectangle in slot {slot}"
            )
        rect_h = rng.choice(row_sizes)
        rect_w = rng.choice(col_sizes)
        top = rng.randint(row_lo, row_hi - rect_h + 1)
        left = rng.randint(col_lo, col_hi - rect_w + 1)
        draw_rect(grid, top, left, rect_h, rect_w, 4)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("grid_profile", _PROFILE_OPTIONS[difficulty])
    height, width = _GRID_DIMS[profile]
    scene = schedule_profile(seed, sample_index, difficulty)
    return _draw_scene(ctx, height, width, scene)


def _validate_grid_shape(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or value not in (0, 4) for row in grid for value in row):
        raise ValueError("cells must be integer colors 0 or 4")
    return len(grid), width


def _component(start, foreground: set[tuple[int, int]]) -> set[tuple[int, int]]:
    reached = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = row + dr, col + dc
            if neighbor in foreground and neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return reached


def _rectangles_or_raise(grid) -> list[tuple[int, int, int, int]]:
    height, width = _validate_grid_shape(grid)
    foreground = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 4
    }
    if not foreground:
        raise ValueError("at least one color-4 rectangle is required")

    components: list[set[tuple[int, int]]] = []
    remaining = set(foreground)
    while remaining:
        part = _component(next(iter(remaining)), remaining)
        components.append(part)
        remaining.difference_update(part)

    if not 1 <= len(components) <= 3:
        raise ValueError(f"expected 1..3 rectangles, found {len(components)}")

    rectangles: list[tuple[int, int, int, int]] = []
    for cells in components:
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        expected = {
            (row, col)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        }
        if cells != expected:
            raise ValueError("every color-4 component must be a solid rectangle")
        rect_h = bottom - top + 1
        rect_w = right - left + 1
        if not (2 <= rect_h <= 7 and 2 <= rect_w <= 7):
            raise ValueError(
                f"rectangle dimensions {rect_h}x{rect_w} outside supported 2..7"
            )
        if top < 1 or left < 1 or bottom >= height - 1 or right >= width - 1:
            raise ValueError("every rectangle must have a one-cell canvas margin")
        rectangles.append((top, left, bottom, right))

    rectangles.sort()
    for index, first in enumerate(rectangles):
        f_top, f_left, f_bottom, f_right = first
        for second in rectangles[index + 1 :]:
            s_top, s_left, s_bottom, s_right = second
            separated = (
                f_bottom + 1 < s_top
                or s_bottom + 1 < f_top
                or f_right + 1 < s_left
                or s_right + 1 < f_left
            )
            if not separated:
                raise ValueError("rectangles must be separated by at least one blank cell")

    if not any(
        (bottom - top + 1) % 2 == 1 and (right - left + 1) % 2 == 1
        for top, left, bottom, right in rectangles
    ):
        raise ValueError("at least one odd-by-odd rectangle is required")
    return rectangles


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        _rectangles_or_raise(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str]:
    _validate_grid_shape(grid)
    dimensions = (len(grid), len(grid[0]))
    for name, shape in _GRID_DIMS.items():
        if dimensions == shape:
            return {"grid_profile": name}
    raise ValueError(f"grid dimensions {dimensions} do not match a declared profile")


def _paint_crosses(grid, *, include_even: bool) -> list[list[int]]:
    rectangles = _rectangles_or_raise(grid)
    output = [list(row) for row in grid]
    for top, left, bottom, right in rectangles:
        rect_h = bottom - top + 1
        rect_w = right - left + 1
        is_odd = rect_h % 2 == 1 and rect_w % 2 == 1
        if not is_odd and not include_even:
            continue
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                output[row][col] = 0
        middle_row = (top + bottom) // 2
        middle_col = (left + right) // 2
        for col in range(left, right + 1):
            output[middle_row][col] = 4
        for row in range(top, bottom + 1):
            output[row][middle_col] = 4
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for focused tests and rivals."""
    return _paint_crosses(grid, include_even=False)


def _reduce_even_rectangles_too(grid) -> list[list[int]]:
    """Plausible shortcut: ignore the authority's odd-dimension guard."""
    return _paint_crosses(grid, include_even=True)


def _has_even_rectangle(grid) -> bool:
    try:
        rectangles = _rectangles_or_raise(grid)
    except (TypeError, ValueError):
        return False
    return any(
        (bottom - top + 1) % 2 == 0 or (right - left + 1) % 2 == 0
        for top, left, bottom, right in rectangles
    )


def lesson_identifiable(demos, query):
    del query
    for pair in demos:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return ["each demonstration must contain input and output grids"]
        try:
            rival_output = _reduce_even_rectangles_too(pair["input"])
        except (TypeError, ValueError) as exc:
            return [f"invalid demonstration input: {exc}"]
        if rival_output != pair["output"]:
            return []
    return [
        "demonstrations do not show an even rectangle remaining unchanged; "
        "the reduce-even-rectangles shortcut survives"
    ]


SEMANTIC_WITNESSES = {"even_rectangle_unchanged": _has_even_rectangle}
SEMANTIC_RIVALS = {"reduce_even_rectangles_too": _reduce_even_rectangles_too}
WITNESS_RIVALS = {
    "even_rectangle_unchanged": ["reduce_even_rectangles_too"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
