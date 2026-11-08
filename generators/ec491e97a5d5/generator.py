"""Constructive curriculum for solid rectangles -> hollow frames.

The Racket rule is the label authority.  This generator owns the canonical
inputs, exposes four honest instance controls, and alternates ordinary
canonical-like scenes with a repeated-colour witness.  The witness separates
object-wise hollowing from the strongest shortcut that fits every canonical
pair: hollowing one global bounding box per colour.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec491e97a5d5"
TASK_ID = GENERATOR_ID
RULE_HASH = "56f21366dd85"
VERSION = "3.0.0"
SUMMARY = (
    "Hollow every solid monochrome rectangular component independently, "
    "preserving its coloured border and clearing its strict interior to 0."
)
INVARIANTS = [
    "background is 0 and every foreground component is a solid monochrome rectangle",
    "there are 2..4 rectangular components using 1..4 foreground colours",
    "rectangle sides are at least 2 and at least one rectangle has a nonempty interior",
    "different-colour rectangles may touch; repeated-colour rectangles remain disconnected",
    "default four-pair windows contain two repeated-colour witnesses",
]
AXES = {
    "grid_h": {
        "type": "int",
        "default": "8..16 with strong canonical-profile mixture",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "9..18 with strong canonical-profile mixture",
        "valid": "9..18",
    },
    "n_rects": {
        "type": "int",
        "default": "2 canonical-core or 3 shortcut-witness rectangles",
        "valid": "2..4",
    },
    "n_colors": {
        "type": "int",
        "default": "2 foreground colours",
        "valid": "1..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_rects": 2, "n_colors": 3},
    {"n_rects": 2, "n_colors": 4},
    {"n_rects": 3, "n_colors": 4},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("shortcut_witness", "canonical_core")
MIN_STRICT_FRAC = 1.0

_GRID_H_DOMAIN = tuple(range(8, 17))
_GRID_W_DOMAIN = tuple(range(9, 19))
_CANONICAL_PROFILES = ((8, 10), (9, 9), (9, 11), (10, 12))
_DIFFICULTIES = ("easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternating schedule makes every four-pair window rotation-safe."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _components(grid):
    """Same-colour four-connected components as ``(colour, cells)`` pairs."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    parts: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == colour
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            parts.append((colour, tuple(cells)))
    return parts


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def self_check(grid, *, difficulty=None, meta=None):
    """Accept exactly the object family on which the canonical rule is taught."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        return ["grid dimensions must be in ARC range 1..30"]
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width for row in grid
    ):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colours 0..9"]

    palette = {value for row in grid for value in row}
    if 0 not in palette:
        return ["background colour 0 must be present"]
    foreground = palette - {0}
    if not 1 <= len(foreground) <= 4:
        return ["require 1..4 foreground colours"]

    parts = _components(grid)
    errors: list[str] = []
    if not 2 <= len(parts) <= 4:
        errors.append("require 2..4 foreground rectangular components")

    has_strict_interior = False
    for colour, cells in parts:
        top, left, bottom, right = _bbox(cells)
        rect_h, rect_w = bottom - top + 1, right - left + 1
        if rect_h < 2 or rect_w < 2:
            errors.append(f"colour {colour} component must be at least 2x2")
        if rect_h >= 3 and rect_w >= 3:
            has_strict_interior = True
        expected = rect_h * rect_w
        if len(cells) != expected or any(
            grid[row][col] != colour
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        ):
            errors.append(f"colour {colour} component is not a solid filled rectangle")
    if parts and not has_strict_interior:
        errors.append("at least one rectangle needs a strict interior to hollow")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    parts = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_rects": len(parts),
        "n_colors": len({colour for colour, _ in parts}),
    }


def _draw_dimension(ctx, label, domain, anchor):
    """Weight canonical dimensions without hiding any declared endpoint."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, domain)
    return ctx.draw_choice(label, domain + (anchor,) * 96)


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative exact integer")
    if difficulty is not None and (
        type(difficulty) is not str or difficulty not in _DIFFICULTIES
    ):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (not bool)")


def _paint_rect(grid, top, left, rect_h, rect_w, colour):
    for row in range(top, top + rect_h):
        for col in range(left, left + rect_w):
            grid[row][col] = colour


def _touching_core(height, width, colours, difficulty):
    """Canonical-like pair whose geometry is observably difficulty-sensitive."""
    grid = full_grid(height, width, 0)
    top = max(0, (height - 6) // 2)
    left = max(0, (width - 5) // 2)
    band = difficulty or "medium"
    if band == "easy":
        first = (top, left + 1, 3, 3)
        second = (top + 3, left, 3, 5)
    elif band == "hard":
        first = (top, left + 1, 4, 3)
        second = (top + 4, left, 2, 5)
    else:
        first = (top, left, 3, 4)
        second = (top + 3, left, 3, 5)
    _paint_rect(grid, *first, colours[0])
    _paint_rect(grid, *second, colours[1])
    return grid


def _quadrant_regions(height, width):
    row_gap = height // 2
    col_gap = width // 2
    return (
        (0, row_gap, 0, col_gap),
        (0, row_gap, col_gap + 1, width),
        (row_gap + 1, height, 0, col_gap),
        (row_gap + 1, height, col_gap + 1, width),
    )


def _component_colours(palette, n_rects, rng):
    """Use every requested colour and repeat only across disconnected slots."""
    colours = list(palette)
    while len(colours) < n_rects:
        colours.append(palette[(len(colours) - len(palette)) % len(palette)])
    # Preserve at least one repeat when needed, but vary which slot receives it.
    if len(palette) < n_rects:
        head = colours[: len(palette)]
        tail = colours[len(palette) :]
        rng.shuffle(head)
        rng.shuffle(tail)
        colours = head + tail
    else:
        rng.shuffle(colours)
    return colours[:n_rects]


def _separated_layout(height, width, n_rects, colours, rng, difficulty):
    """Place up to four rectangles in regions split by a blank row and column."""
    grid = full_grid(height, width, 0)
    regions = list(_quadrant_regions(height, width))
    slot_order = list(range(4))
    rng.shuffle(slot_order)

    # Difficulty changes geometry only; all override domains remain available.
    band = difficulty or "medium"
    for index, (colour, slot) in enumerate(zip(colours, slot_order[:n_rects])):
        r0, r1, c0, c1 = regions[slot]
        region_h, region_w = r1 - r0, c1 - c0
        if band == "easy":
            rect_h, rect_w = ((3, 3) if index == 0 else (2, 2))
        elif band == "hard":
            rect_h, rect_w = region_h, region_w
        else:
            rect_h, rect_w = ((3, 4) if index == 0 else (2, 3))
        top = rng.randint(r0, r1 - rect_h)
        left = rng.randint(c0, c1 - rect_w)
        _paint_rect(grid, top, left, rect_h, rect_w, colour)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
    height = _draw_dimension(ctx, "grid_h", _GRID_H_DOMAIN, anchor[0])
    width = _draw_dimension(ctx, "grid_w", _GRID_W_DOMAIN, anchor[1])

    profile = schedule_profile(seed, sample_index, difficulty)
    requested_colors = overrides.get("n_colors")
    scheduled_rects = 3 if profile == "shortcut_witness" else 2
    # A single colour-count override is independently reachable: increase the
    # dependent default object count rather than rejecting an otherwise legal
    # axis value.  Explicitly pinned incompatible count pairs still fail below.
    default_rects = max(scheduled_rects, requested_colors or 0)
    n_rects = ctx.draw_choice(
        "n_rects", (2, 3, 4) if overrides.get("n_rects") is not None else (default_rects,)
    )
    n_colors = ctx.draw_choice(
        "n_colors", (1, 2, 3, 4) if requested_colors is not None else (2,)
    )
    if n_colors > n_rects:
        raise ValueError("n_colors cannot exceed n_rects")

    palette = ctx.draw_distinct_colors("foreground_palette", n=n_colors, exclude={0})
    layout_rng = ctx.draw_rng("layout")
    colours = _component_colours(palette, n_rects, layout_rng)

    # The ordinary profile deliberately includes the canonical edge-touching
    # relation.  All other cases use separated slots, which support repeated
    # colours without accidentally merging their components.
    if profile == "canonical_core" and n_rects == 2 and n_colors == 2:
        grid = _touching_core(height, width, colours, difficulty)
    else:
        grid = _separated_layout(height, width, n_rects, colours, layout_rng, difficulty)

    errors = self_check(grid)
    if errors:  # fail loudly: construction bugs must never leak into training.
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _objectwise(grid):
    """Independent Python semantic mirror used only by review hooks."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for colour, cells in _components(grid):
        top, left, bottom, right = _bbox(cells)
        for col in range(left, right + 1):
            output[top][col] = colour
            output[bottom][col] = colour
        for row in range(top, bottom + 1):
            output[row][left] = colour
            output[row][right] = colour
    return output


def _by_colour(grid):
    """Canonical-fitting shortcut: one global hollow box per foreground colour."""
    output = full_grid(len(grid), len(grid[0]), 0)
    by_colour: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, colour in enumerate(values):
            if colour != 0:
                by_colour.setdefault(colour, []).append((row, col))
    for colour, cells in by_colour.items():
        top, left, bottom, right = _bbox(cells)
        for col in range(left, right + 1):
            output[top][col] = colour
            output[bottom][col] = colour
        for row in range(top, bottom + 1):
            output[row][left] = colour
            output[row][right] = colour
    return output


def _separate_same_colour(grid):
    return any(count >= 2 for count in Counter(colour for colour, _ in _components(grid)).values())


SEMANTIC_RIVALS = {"by_color": _by_colour}
CANONICAL_SHORTCUTS = {"by_color": _by_colour}
LESSON_COMPETITORS = {"by_color": _by_colour}
SEMANTIC_WITNESSES = {"separate_same_color": _separate_same_colour}
WITNESS_RIVALS = {"separate_same_color": ["by_color"]}

def lesson_identifiable(demos, query):
    """Return reasons when a declared rival can still alter the query answer."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = _objectwise(demo["input"])
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with object-wise hollowing")

    try:
        query_answer = _objectwise(query["input"])
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(demo["input"]) == demo.get("output") for demo in demos
            )
            if survives and competitor(query["input"]) != query_answer:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            reasons.append(f"competing rule {name!r} could not be evaluated: {exc}")
    return reasons

