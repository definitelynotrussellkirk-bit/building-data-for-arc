"""Generate sparse corner pairs whose per-colour rectangle borders are drawn.

The selected Racket rule treats each non-zero colour independently: exactly two
cells of a colour are opposite corners, and the output paints that rectangle's
outline in the same colour.  The authority grammar accepts overlapping boxes
and 2x2 rectangles because the oracle defines them unambiguously.  The teaching
distribution is deliberately narrower: generated boxes have visible interiors
and are disjoint, avoiding hidden overwrite-order lessons absent from every
canonical example.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7672a367745"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f641b0a1fe42"

SUMMARY = (
    "A zero-background grid contains nonzero colours, each appearing at exactly "
    "two diagonally opposite corners of a rectangle. For every colour, draw the "
    "complete rectangle border in that colour on a same-size zero background. "
    "Generated lessons use one to five disjoint, interior-bearing rectangles."
)

INVARIANTS = [
    "background is 0 and all cells are literal ARC colours 0..9",
    "every active colour appears exactly twice",
    "the two same-colour cells differ in both row and column",
    "generated rectangles have an interior",
    "generated rectangle bounding boxes are pairwise disjoint",
]

# Each profile is an observable linked (height, width, rectangle-count) grammar
# point.  Four profiles per band form a deterministic curriculum; the first
# three demonstrations of every sliding window always include a multi-rectangle
# example, which refutes the global-bounding-box shortcut.
_PROFILE_ROWS = (
    ("easy", "easy_single_10x10", 10, 10, 1),
    ("easy", "easy_pair_8x10", 8, 10, 2),
    ("easy", "easy_pair_9x11", 9, 11, 2),
    ("easy", "easy_triple_9x12", 9, 12, 3),
    ("medium", "medium_single_11x12", 11, 12, 1),
    ("medium", "medium_pair_7x12", 7, 12, 2),
    ("medium", "medium_triple_12x15", 12, 15, 3),
    ("medium", "medium_quad_14x16", 14, 16, 4),
    ("hard", "hard_pair_9x9", 9, 9, 2),
    ("hard", "hard_single_15x15", 15, 15, 1),
    ("hard", "hard_quad_18x20", 18, 20, 4),
    ("hard", "hard_five_20x22", 20, 22, 5),
)
_PROFILE_BY_NAME = {
    name: (band, height, width, count)
    for band, name, height, width, count in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (height, width, count): name
    for _band_name, name, height, width, count in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(name for row_band, name, *_rest in _PROFILE_ROWS if row_band == band)
    for band in ("easy", "medium", "hard")
}
SCENE_PROFILES = tuple(name for _band, name, *_rest in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-profile curriculum for the difficulty band",
        "valid": (
            "easy_single_10x10|easy_pair_8x10|easy_pair_9x11|easy_triple_9x12|"
            "medium_single_11x12|medium_pair_7x12|medium_triple_12x15|"
            "medium_quad_14x16|hard_pair_9x9|hard_single_15x15|"
            "hard_quad_18x20|hard_five_20x22"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

Grid = list[list[int]]
Box = tuple[int, int, int, int]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact profile used at this curriculum position."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides and overrides["scene_profile"] not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {overrides['scene_profile']!r}")


def _segments(length: int, parts: int) -> list[tuple[int, int]]:
    """Balanced inclusive segments that cover ``range(length)``."""
    base, remainder = divmod(length, parts)
    out: list[tuple[int, int]] = []
    start = 0
    for index in range(parts):
        size = base + (1 if index < remainder else 0)
        out.append((start, start + size - 1))
        start += size
    return out


def _layout_shape(count: int) -> tuple[int, int]:
    return {
        1: (1, 1),
        2: (1, 2),
        3: (1, 3),
        4: (2, 2),
        5: (2, 3),
    }[count]


def _draw_box(region: Box, shape: str, rng) -> Box:
    """Draw one interior-bearing box inside an assigned disjoint region."""
    top, left, bottom, right = region
    max_row_span = bottom - top
    max_col_span = right - left
    if max_row_span < 2 or max_col_span < 2:
        raise ValueError(f"region too small for a rectangle: {region}")

    if shape == "tall" and max_row_span >= 3:
        row_span = rng.randint(3, max_row_span)
        col_span = 2
    elif shape == "wide" and max_col_span >= 3:
        row_span = 2
        col_span = rng.randint(3, max_col_span)
    else:
        row_span = rng.randint(2, max_row_span)
        col_span = rng.randint(2, max_col_span)

    row0 = rng.randint(top, bottom - row_span)
    col0 = rng.randint(left, right - col_span)
    return row0, col0, row0 + row_span, col0 + col_span


def _draw_boxes(height: int, width: int, count: int, rng) -> list[Box]:
    rows, cols = _layout_shape(count)
    row_segments = _segments(height, rows)
    col_segments = _segments(width, cols)
    regions = [
        (row0, col0, row1, col1)
        for row0, row1 in row_segments
        for col0, col1 in col_segments
    ][:count]
    boxes: list[Box] = []
    for index, region in enumerate(regions):
        # Every multi-rectangle scene includes both a tall and a wide witness.
        shape = "tall" if count > 1 and index == 0 else "wide" if count > 1 and index == 1 else "free"
        boxes.append(_draw_box(region, shape, rng))
    return boxes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    scheduled = overrides.get("scene_profile") or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", (scheduled,))
    _profile_band, height, width, count = _PROFILE_BY_NAME[profile]

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    boxes = _draw_boxes(height, width, count, layout_rng)
    colors = color_rng.sample(tuple(range(1, 10)), count)
    grid = full_grid(height, width, 0)
    for color, (row0, col0, row1, col1) in zip(colors, boxes):
        if layout_rng.random() < 0.5:
            corners = ((row0, col0), (row1, col1))
        else:
            corners = ((row0, col1), (row1, col0))
        for row, col in corners:
            grid[row][col] = color

    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise AssertionError(
            f"constructed profile {profile!r} observed as {observed.get('scene_profile')!r}"
        )
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _boxes_overlap(a: Box, b: Box) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _analysis(grid: Any, *, teaching: bool = False) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "boxes": [], "positions": {}}

    height, width = len(grid), len(grid[0])
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions[value].append((row, col))

    if not positions:
        errors.append("expected at least one same-colour corner pair")
    if len(positions) > 9:
        errors.append(f"expected at most nine active colours, found {len(positions)}")

    boxes: list[tuple[int, Box]] = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            errors.append(f"colour {color} must appear exactly twice, found {len(cells)}")
            continue
        (row_a, col_a), (row_b, col_b) = cells
        if row_a == row_b or col_a == col_b:
            errors.append(f"colour {color} corners must be diagonal, found {cells}")
            continue
        row0, row1 = sorted((row_a, row_b))
        col0, col1 = sorted((col_a, col_b))
        boxes.append((color, (row0, col0, row1, col1)))

    signature = (height, width, len(positions))
    scene_profile = _PROFILE_BY_SIGNATURE.get(signature)
    if teaching and not errors:
        if not 5 <= height <= 26 or not 5 <= width <= 26:
            errors.append(
                f"teaching grid dimensions must be in 5..26, found {height}x{width}"
            )
        if not 1 <= len(positions) <= 5:
            errors.append(
                f"teaching scenes require one to five active colours, found {len(positions)}"
            )
        for color, (row0, col0, row1, col1) in boxes:
            if row1 - row0 < 2 or col1 - col0 < 2:
                errors.append(
                    "teaching rectangles must have an interior; "
                    f"colour {color} span={(row1-row0, col1-col0)}"
                )
        for left_index, (left_color, left_box) in enumerate(boxes):
            for right_color, right_box in boxes[left_index + 1 :]:
                if _boxes_overlap(left_box, right_box):
                    errors.append(
                        "teaching rectangles must be disjoint; implied boxes "
                        f"for colours {left_color} and {right_color} overlap"
                    )
        if scene_profile is None:
            errors.append(
                "teaching scene must realize one declared linked "
                f"(height,width,count) profile, found {signature}"
            )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "positions": dict(positions),
        "boxes": boxes,
        "scene_profile": scene_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar, independently of curriculum."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrower generated/lesson grammar and exact profile axis."""
    del difficulty
    analysis = _analysis(grid, teaching=True)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = {"scene_profile": analysis["scene_profile"]}
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the complete exact declared profile from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid) -> int | None:
    """Index the five published linked (height,width,palette) profiles."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    signatures = (
        (8, 10, 2),
        (9, 9, 2),
        (7, 12, 2),
        (10, 10, 1),
        (9, 11, 2),
    )
    signature = (analysis["height"], analysis["width"], len(analysis["positions"]))
    try:
        return signatures.index(signature)
    except ValueError:
        return None


def _border_cells(box: Box) -> set[tuple[int, int]]:
    row0, col0, row1, col1 = box
    return {
        *((row0, col) for col in range(col0, col1 + 1)),
        *((row1, col) for col in range(col0, col1 + 1)),
        *((row, col0) for row in range(row0, row1 + 1)),
        *((row, col1) for row in range(row0, row1 + 1)),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    for color, box in analysis["boxes"]:
        for row, col in _border_cells(box):
            output[row][col] = color
    return output


def _rival_fill_rectangles(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = full_grid(analysis["height"], analysis["width"], 0)
    for color, (row0, col0, row1, col1) in analysis["boxes"]:
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                output[row][col] = color
    return output


def _rival_global_bbox(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    cells = [cell for positions in analysis["positions"].values() for cell in positions]
    row0 = min(row for row, _col in cells)
    row1 = max(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    col1 = max(col for _row, col in cells)
    first_color = next(value for row in grid for value in row if value != 0)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for row, col in _border_cells((row0, col0, row1, col1)):
        output[row][col] = first_color
    return output


def _rival_copy_markers(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def strict_canonical_like(grid) -> list[str]:
    """The complete generator grammar is a canonical-like task manifold."""
    return teaching_check(grid)


def _valid_analysis(grid: Grid) -> dict[str, Any] | None:
    analysis = _analysis(grid, teaching=True)
    return None if analysis["errors"] else analysis


def _single_rectangle(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["boxes"]) == 1


def _multiple_rectangles(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["boxes"]) >= 2


def _tall_rectangle(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        box[2] - box[0] > box[3] - box[1] for _color, box in analysis["boxes"]
    )


def _wide_rectangle(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        box[3] - box[1] > box[2] - box[0] for _color, box in analysis["boxes"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "single_rectangle": _single_rectangle,
    "multiple_rectangles": _multiple_rectangles,
    "tall_rectangle": _tall_rectangle,
    "wide_rectangle": _wide_rectangle,
}

SEMANTIC_RIVALS = {
    "fill_rectangles": _rival_fill_rectangles,
    "global_bbox": _rival_global_bbox,
    "copy_markers": _rival_copy_markers,
}
WITNESS_RIVALS = {
    "single_rectangle": ["fill_rectangles", "copy_markers"],
    "multiple_rectangles": ["fill_rectangles", "global_bbox", "copy_markers"],
    "tall_rectangle": ["fill_rectangles", "copy_markers"],
    "wide_rectangle": ["fill_rectangles", "copy_markers"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demos to eliminate the named marker/fill/global-box rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if teaching_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = teaching_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the per-colour rectangle outline")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
