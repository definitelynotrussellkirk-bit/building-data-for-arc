"""Generate same-color corner markers for independent rectangle fills.

Each nonzero color occurs at exactly the four corners of one axis-aligned
rectangle.  The canonical Racket rule fills every such rectangle with its
corner color.  Rectangle bodies never overlap, so multi-color lessons expose
independent per-color filling rather than an order-dependent overwrite rule.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cdf26af5c935"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "f0bf24a90ea6"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "For each nonzero color, find its four cells at the corners of one "
    "axis-aligned rectangle and fill that entire rectangle with the same "
    "color.  Treat colors independently."
)

INVARIANTS = [
    "background is color 0 and remains the modal input color",
    "one to three nonzero colors each occur exactly four times",
    "each color's four cells are exactly the corners of one non-degenerate rectangle",
    "every rectangle has area greater than four, so the rule changes the input",
    "different rectangle bodies are disjoint, so color application order is irrelevant",
]

PALETTES = {
    "low": (1, 2, 3),
    "mid": (4, 5, 6),
    "high": (7, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "sample schedule plus difficulty-aware variation",
        "valid": "6..14",
    },
    "grid_w": {
        "type": "int",
        "default": "sample schedule plus difficulty-aware variation",
        "valid": "7..14",
    },
    "n_rects": {
        "type": "int",
        "default": "sample schedule plus difficulty-aware variation",
        "valid": "1..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "low|mid|high",
    },
}

# The first four profiles reproduce all canonical (height, width, palette-size)
# profiles in every difficulty band.  Consecutive indices 0, 1, 2 also form an
# identifiable three-demo lesson: one rectangle, then two separated rectangles,
# then a tall rectangle, with three disjoint palette families.
_SCHEDULED_PROFILES = (
    (6, 7, 1),
    (7, 10, 2),
    (8, 8, 1),
    (8, 10, 2),
    (9, 11, 3),
)
_PALETTE_SCHEDULE = ("low", "mid", "high", "low", "mid", "high")


def _draw_int_axis(
    ctx,
    label: str,
    default_lo: int,
    default_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    """Draw an integer axis while giving explicit overrides the full domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_choice_axis(ctx, label: str, default: str, options: tuple[str, ...]) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _band_defaults(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (7, 10), (1, 2)
    if difficulty == "hard":
        return (9, 14), (10, 14), (2, 3)
    return (7, 11), (8, 12), (1, 3)


def _partition(length: int, count: int) -> list[tuple[int, int]]:
    """Split [0, length) into ``count`` contiguous bands, each at least 2."""
    if length < 2 * count:
        raise ValueError(
            f"dimension {length} cannot host {count} disjoint two-cell bands"
        )
    sizes = [2] * count
    for index in range(length - 2 * count):
        sizes[index % count] += 1
    bands: list[tuple[int, int]] = []
    cursor = 0
    for size in sizes:
        bands.append((cursor, cursor + size - 1))
        cursor += size
    return bands


def _span_start(total: int, span: int, mode: int, rng) -> int:
    if span > total:
        raise ValueError(f"span {span} exceeds dimension {total}")
    room = total - span
    if room == 0:
        return 0
    if mode % 3 == 0:
        return 0
    if mode % 3 == 1:
        return room
    if room >= 2:
        return rng.randint(1, room - 1)
    return rng.randint(0, room)


def _row_band_layout(height: int, width: int, count: int, profile: int, rng):
    """Place rectangles in disjoint row bands with randomized shapes."""
    rects = []
    for index, (band_top, band_bottom) in enumerate(_partition(height, count)):
        band_height = band_bottom - band_top + 1
        rect_h = rng.randint(2, band_height)
        top = rng.randint(band_top, band_bottom - rect_h + 1)
        min_width = 3 if rect_h == 2 else 2
        if min_width > width:
            raise ValueError("grid width cannot make a non-identity rectangle")
        if index % 2 == 0 and rect_h < width:
            min_width = max(min_width, rect_h + 1)
        span = rng.randint(min_width, width)
        left = _span_start(width, span, profile + index, rng)
        rects.append((top, left, top + rect_h - 1, left + span - 1))
    return rects


def _gapped_pair_layout(height: int, width: int, profile: int, rng):
    """Place two rectangles on opposite sides of a guaranteed empty column."""
    gap = width // 2
    bands = ((0, gap - 1), (gap + 1, width - 1))
    rects = []
    for index, (band_left, band_right) in enumerate(bands):
        band_width = band_right - band_left + 1
        min_width = 3 if index == 0 else 2
        rect_w = rng.randint(min_width, band_width)
        left = rng.randint(band_left, band_right - rect_w + 1)
        min_height = 3 if index == 0 or rect_w == 2 else 2
        rect_h = rng.randint(min_height, height)
        top = _span_start(height, rect_h, profile + index, rng)
        rects.append((top, left, top + rect_h - 1, left + rect_w - 1))
    return rects


def _column_band_layout(height: int, width: int, count: int, profile: int, rng):
    """Place rectangles in disjoint column bands with randomized shapes."""
    rects = []
    for index, (band_left, band_right) in enumerate(_partition(width, count)):
        band_width = band_right - band_left + 1
        rect_w = rng.randint(2, band_width)
        left = rng.randint(band_left, band_right - rect_w + 1)
        min_height = 3 if rect_w == 2 else 2
        if min_height > height:
            raise ValueError("grid height cannot make a non-identity rectangle")
        if index % 2 == 0 and rect_w < height:
            min_height = max(min_height, rect_w + 1)
        span = rng.randint(min_height, height)
        top = _span_start(height, span, profile + index, rng)
        rects.append((top, left, top + span - 1, left + rect_w - 1))
    return rects


def _single_layout(height: int, width: int, orientation: str, rng):
    """Return one variable wide or tall rectangle for lesson profiles."""
    if orientation == "wide":
        rect_h = rng.randint(2, min(4, height))
        min_width = max(3 if rect_h == 2 else 2, rect_h + 1)
        if min_width > width:
            rect_h = 2
            min_width = 3
        rect_w = rng.randint(min_width, width)
    elif orientation == "tall":
        rect_w = rng.randint(2, min(4, width))
        min_height = max(3 if rect_w == 2 else 2, rect_w + 1)
        if min_height > height:
            rect_w = 2
            min_height = 3
        rect_h = rng.randint(min_height, height)
    else:
        raise ValueError(f"unknown orientation: {orientation}")
    top = rng.randint(0, height - rect_h)
    left = rng.randint(0, width - rect_w)
    return [(top, left, top + rect_h - 1, left + rect_w - 1)]


def _rectangle_cells(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = rect
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    }


def _corner_cells(rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = rect
    return {
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic lawful input; the Racket rule owns outputs."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    for axis in ("grid_h", "grid_w", "n_rects"):
        value = overrides.get(axis)
        if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
            raise TypeError(f"{axis} override must be an integer, not {type(value).__name__}")
    palette_value = overrides.get("palette_kind")
    if palette_value is not None and not isinstance(palette_value, str):
        raise TypeError("palette_kind override must be a string")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = sample_index % 6
    scheduled = profile < len(_SCHEDULED_PROFILES)
    if scheduled:
        scheduled_h, scheduled_w, scheduled_n = _SCHEDULED_PROFILES[profile]
        h_range = (scheduled_h, scheduled_h)
        w_range = (scheduled_w, scheduled_w)
        n_range = (scheduled_n, scheduled_n)
    else:
        h_range, w_range, n_range = _band_defaults(difficulty)

    height = _draw_int_axis(ctx, "grid_h", *h_range, 6, 14)
    width = _draw_int_axis(ctx, "grid_w", *w_range, 7, 14)
    n_rects = _draw_int_axis(ctx, "n_rects", *n_range, 1, 3)
    palette_kind = _draw_choice_axis(
        ctx,
        "palette_kind",
        _PALETTE_SCHEDULE[profile],
        PALETTE_KINDS,
    )

    rng = ctx.draw_rng("layout")
    if n_rects == 1 and profile == 0:
        rects = _single_layout(height, width, "wide", rng)
    elif n_rects == 1 and profile == 2:
        rects = _single_layout(height, width, "tall", rng)
    elif n_rects == 2 and profile == 1:
        rects = _gapped_pair_layout(height, width, profile, rng)
    elif profile in (1, 2, 5):
        rects = _column_band_layout(height, width, n_rects, profile, rng)
    else:
        rects = _row_band_layout(height, width, n_rects, profile, rng)

    filled = set().union(*(_rectangle_cells(rect) for rect in rects))
    if len(filled) == height * width:
        for index, (top, left, bottom, right) in enumerate(rects):
            rect_h = bottom - top + 1
            rect_w = right - left + 1
            if rect_h > 2:
                rects[index] = (top, left, bottom - 1, right)
                break
            if rect_w > 2:
                rects[index] = (top, left, bottom, right - 1)
                break
        else:
            raise ValueError("internal layout error: cannot preserve background")

    colors = list(PALETTES[palette_kind])
    rng.shuffle(colors)
    colors = colors[:n_rects]
    grid = full_grid(height, width, 0)
    occupied: set[tuple[int, int]] = set()
    for color, rect in zip(colors, rects):
        body = _rectangle_cells(rect)
        if body & occupied:
            raise ValueError("internal layout error: rectangle bodies overlap")
        occupied.update(body)
        for row, col in _corner_cells(rect):
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal layout error: " + "; ".join(errors))
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["cells must be literal ARC integers 0..9"]
    return []


def _rectangles_from_grid(grid: Any) -> tuple[list[dict[str, Any]], list[str]]:
    errors = _grid_errors(grid)
    if errors:
        return [], errors
    height, width = len(grid), len(grid[0])
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                by_color.setdefault(value, []).append((row, col))

    errors = []
    if not 1 <= len(by_color) <= 3:
        errors.append(
            f"expected 1-3 rectangle colors, found {len(by_color)}"
        )
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")

    rectangles: list[dict[str, Any]] = []
    for color, cells in sorted(by_color.items()):
        rows = sorted({row for row, _ in cells})
        cols = sorted({col for _, col in cells})
        if len(cells) != 4 or len(rows) != 2 or len(cols) != 2:
            errors.append(
                f"color {color} must occupy exactly four cells on two rows and two columns"
            )
            continue
        rect = (rows[0], cols[0], rows[1], cols[1])
        corners = _corner_cells(rect)
        if set(cells) != corners:
            errors.append(f"color {color} cells are not the four rectangle corners")
            continue
        rect_h = rows[1] - rows[0] + 1
        rect_w = cols[1] - cols[0] + 1
        area = rect_h * rect_w
        if area <= 4:
            errors.append(
                f"color {color} rectangle has area {area}; filling would be identity"
            )
        rectangles.append(
            {
                "color": color,
                "bbox": rect,
                "height": rect_h,
                "width": rect_w,
                "area": area,
                "touches_edge": (
                    rows[0] == 0
                    or cols[0] == 0
                    or rows[1] == height - 1
                    or cols[1] == width - 1
                ),
                "fully_interior": (
                    rows[0] > 0
                    and cols[0] > 0
                    and rows[1] < height - 1
                    and cols[1] < width - 1
                ),
                "has_true_interior": rect_h >= 3 and rect_w >= 3,
            }
        )

    for index, left in enumerate(rectangles):
        left_body = _rectangle_cells(left["bbox"])
        for right in rectangles[index + 1 :]:
            if left_body & _rectangle_cells(right["bbox"]):
                errors.append(
                    f"rectangle bodies for colors {left['color']} and {right['color']} overlap"
                )

    if rectangles:
        filled_cells: set[tuple[int, int]] = set()
        for rectangle in rectangles:
            filled_cells.update(_rectangle_cells(rectangle["bbox"]))
        if len(filled_cells) == height * width:
            errors.append("rectangle fill would erase the entire background")

    zero_count = sum(value == 0 for row in grid for value in row)
    if by_color and zero_count <= max(len(cells) for cells in by_color.values()):
        errors.append("background color 0 is not uniquely modal")
    return rectangles, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, overlapping, and identity scenes."""
    _, errors = _rectangles_from_grid(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict task manifold is the structural grammar above."""
    return self_check(grid)


def _palette_kind(colors: Iterable[int]) -> str | None:
    color_set = set(colors)
    for name, palette in PALETTES.items():
        if color_set and color_set <= set(palette):
            return name
    return None


def semantic_observables(grid) -> dict[str, Any]:
    rectangles, errors = _rectangles_from_grid(grid)
    if errors:
        return {"errors": errors, "rectangles": rectangles}
    height, width = len(grid), len(grid[0])
    all_body: set[tuple[int, int]] = set()
    for rect in rectangles:
        all_body.update(_rectangle_cells(rect["bbox"]))
    top = min(rect["bbox"][0] for rect in rectangles)
    left = min(rect["bbox"][1] for rect in rectangles)
    bottom = max(rect["bbox"][2] for rect in rectangles)
    right = max(rect["bbox"][3] for rect in rectangles)
    global_bbox = _rectangle_cells((top, left, bottom, right))
    return {
        "errors": [],
        "grid_h": height,
        "grid_w": width,
        "n_rects": len(rectangles),
        "palette_kind": _palette_kind(rect["color"] for rect in rectangles),
        "rectangles": rectangles,
        "has_wide": any(rect["width"] > rect["height"] for rect in rectangles),
        "has_tall": any(rect["height"] > rect["width"] for rect in rectangles),
        "has_true_interior": any(rect["has_true_interior"] for rect in rectangles),
        "has_edge_touch": any(rect["touches_edge"] for rect in rectangles),
        "has_fully_interior": any(rect["fully_interior"] for rect in rectangles),
        "per_color_not_global_bbox": (
            len(rectangles) >= 2 and bool(global_bbox - all_body)
        ),
        "distinct_areas": len({rect["area"] for rect in rectangles}),
    }


def observe_overrides(grid) -> dict[str, int | str]:
    facts = semantic_observables(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    palette_kind = facts["palette_kind"]
    if palette_kind is None:
        raise ValueError("nonzero colors do not belong to one declared palette family")
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "n_rects": int(facts["n_rects"]),
        "palette_kind": palette_kind,
    }


def _filled_output(grid):
    """Python mirror used only for semantic tests; Racket remains authority."""
    rectangles, errors = _rectangles_from_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = [list(row) for row in grid]
    for rect in rectangles:
        for row, col in _rectangle_cells(rect["bbox"]):
            out[row][col] = rect["color"]
    return out


def _witness(name: str):
    def predicate(grid) -> bool:
        facts = semantic_observables(grid)
        if facts["errors"]:
            return False
        return bool(facts[name])

    return predicate


SEMANTIC_WITNESSES = {
    "single_rectangle": lambda grid: not self_check(grid)
    and semantic_observables(grid)["n_rects"] == 1,
    "multiple_rectangles": lambda grid: not self_check(grid)
    and semantic_observables(grid)["n_rects"] >= 2,
    "three_rectangles": lambda grid: not self_check(grid)
    and semantic_observables(grid)["n_rects"] == 3,
    "solid_fill_has_true_interior": _witness("has_true_interior"),
    "wide_rectangle": _witness("has_wide"),
    "tall_rectangle": _witness("has_tall"),
    "edge_touching_rectangle": _witness("has_edge_touch"),
    "fully_interior_rectangle": _witness("has_fully_interior"),
    "per_color_not_global_bbox": _witness("per_color_not_global_bbox"),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos that refute the main plausible shortcut rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the rectangle-corner grammar")

    facts = []
    palettes = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        input_errors = self_check(demo["input"])
        if input_errors:
            reasons.append(f"demo {index} input is malformed: {input_errors[0]}")
            continue
        expected = _filled_output(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the per-color solid rectangle fill")
            continue
        observed = semantic_observables(demo["input"])
        facts.append(observed)
        palettes.add(observed["palette_kind"])

    if facts:
        counts = {fact["n_rects"] for fact in facts}
        if 1 not in counts or not any(count >= 2 for count in counts):
            reasons.append("demos do not vary from one to multiple independent rectangles")
        if not any(fact["has_true_interior"] for fact in facts):
            reasons.append("demos do not distinguish solid fill from outline completion")
        if not any(fact["per_color_not_global_bbox"] for fact in facts):
            reasons.append("demos do not refute filling one global marker bounding box")
        if not any(fact["has_wide"] for fact in facts):
            reasons.append("demos do not include a wide rectangle")
        if not any(fact["has_tall"] for fact in facts):
            reasons.append("demos do not include a tall rectangle")
        if len(palettes) < 2:
            reasons.append("demos do not vary the palette family")
    return reasons
