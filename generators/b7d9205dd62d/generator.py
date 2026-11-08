"""Generate diagonal corner pairs whose rectangles are filled solid.

The selected Racket rule treats each nonzero colour independently.  Exactly two
cells of a colour define a rectangle only when they differ in both row and
column; that rectangle is filled solid in the same colour.  Collinear two-cell
colours are left unchanged.  Generated lessons use disjoint interior-bearing
rectangles and, in alternating curriculum profiles, a collinear distractor that
makes the diagonal condition observable.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7d9205dd62d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "913178465622"

SUMMARY = (
    "A zero-background grid contains at least two nonzero colours whose two "
    "cells are diagonally opposite corners of separate axis-aligned rectangles. "
    "Fill every cell of each implied rectangle with that pair's colour. Some "
    "lessons also contain a different colour appearing twice on one row or one "
    "column; that collinear pair stays unchanged because it is not diagonal."
)

INVARIANTS = [
    "background is 0 and every cell is a literal ARC colour 0..9",
    "every active colour appears exactly twice",
    "at least two colours form non-degenerate diagonal corner pairs",
    "generated diagonal rectangles have an interior and pairwise-disjoint boxes",
    "an optional collinear two-cell colour lies outside every diagonal rectangle",
]

# One exact observable axis replaces the former nine-axis surface, five members
# of which were accepted but ignored.  The four canonical (height, width,
# active-colour-count) profiles are retained exactly; the additional profiles
# expose rectangle count and the collinear non-trigger branch.  Difficulty only
# chooses the default schedule.  Any named profile is a lawful explicit
# override in any band.
_PROFILE_ROWS = (
    ("canonical_10x11_pair2", 10, 11, 2, 0),
    ("canonical_10x12_pair2", 10, 12, 2, 0),
    ("canonical_11x11_pair2", 11, 11, 2, 0),
    ("canonical_11x12_pair2", 11, 12, 2, 0),
    ("pair_collinear_10x12", 10, 12, 2, 1),
    ("triple_collinear_11x11", 11, 11, 3, 1),
    ("quad_collinear_10x11", 10, 11, 4, 1),
    ("five_collinear_11x12", 11, 12, 5, 1),
)
_PROFILE_BY_NAME = {
    name: (height, width, pair_count, collinear_count)
    for name, height, width, pair_count, collinear_count in _PROFILE_ROWS
}
_PROFILE_BY_SIGNATURE = {
    (height, width, pair_count, collinear_count): name
    for name, height, width, pair_count, collinear_count in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    # A / B / B / A: every cyclic three-demo window includes a collinear
    # discriminator while all four positions contain multiple diagonal boxes.
    "easy": (
        "canonical_10x11_pair2",
        "pair_collinear_10x12",
        "triple_collinear_11x11",
        "canonical_11x12_pair2",
    ),
    "medium": (
        "canonical_10x12_pair2",
        "triple_collinear_11x11",
        "quad_collinear_10x11",
        "canonical_11x11_pair2",
    ),
    "hard": (
        "canonical_11x12_pair2",
        "quad_collinear_10x11",
        "five_collinear_11x12",
        "canonical_10x11_pair2",
    ),
}
SCENE_PROFILES = tuple(name for name, *_rest in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic A/B/B/A curriculum for the difficulty band",
        "valid": (
            "canonical_10x11_pair2|canonical_10x12_pair2|"
            "canonical_11x11_pair2|canonical_11x12_pair2|"
            "pair_collinear_10x12|triple_collinear_11x11|"
            "quad_collinear_10x11|five_collinear_11x12"
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
        # Every scene has both tall and wide rectangles, which prevents square-
        # only and fixed-aspect shortcuts while guaranteeing visible interiors.
        shape = "tall" if index == 0 else "wide" if index == 1 else "free"
        boxes.append(_draw_box(region, shape, rng))
    return boxes


def _box_cells(box: Box) -> set[tuple[int, int]]:
    row0, col0, row1, col1 = box
    return {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
    }


def _collinear_candidates(
    height: int, width: int, blocked: set[tuple[int, int]]
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """All length>=3 horizontal/vertical free segments, represented by ends."""
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row in range(height):
        for left in range(width - 2):
            if (row, left) in blocked:
                continue
            for right in range(left + 2, width):
                if any((row, col) in blocked for col in range(left, right + 1)):
                    break
                candidates.append(((row, left), (row, right)))
    for col in range(width):
        for top in range(height - 2):
            if (top, col) in blocked:
                continue
            for bottom in range(top + 2, height):
                if any((row, col) in blocked for row in range(top, bottom + 1)):
                    break
                candidates.append(((top, col), (bottom, col)))
    return candidates


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
    height, width, pair_count, collinear_count = _PROFILE_BY_NAME[profile]

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    total_colors = pair_count + collinear_count
    colors = color_rng.sample(tuple(range(1, 10)), total_colors)

    for _attempt in range(100):
        boxes = _draw_boxes(height, width, pair_count, layout_rng)
        blocked = set().union(*(_box_cells(box) for box in boxes))
        candidates = _collinear_candidates(height, width, blocked)
        if collinear_count and not candidates:
            continue

        grid = full_grid(height, width, 0)
        for color, (row0, col0, row1, col1) in zip(colors[:pair_count], boxes):
            if layout_rng.random() < 0.5:
                corners = ((row0, col0), (row1, col1))
            else:
                corners = ((row0, col1), (row1, col0))
            for row, col in corners:
                grid[row][col] = color

        if collinear_count:
            first, second = layout_rng.choice(candidates)
            distractor_color = colors[-1]
            grid[first[0]][first[1]] = distractor_color
            grid[second[0]][second[1]] = distractor_color

        observed = observe_overrides(grid)
        if observed.get("scene_profile") != profile:
            raise AssertionError(
                f"constructed profile {profile!r} observed as "
                f"{observed.get('scene_profile')!r}"
            )
        return grid
    raise ValueError(f"could not construct profile {profile!r}")


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
        return {"errors": errors, "boxes": [], "collinear": [], "positions": {}}

    height, width = len(grid), len(grid[0])
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                positions[value].append((row, col))

    if not positions:
        errors.append("expected at least two diagonal same-colour corner pairs")
    if len(positions) > 9:
        errors.append(f"expected at most nine active colours, found {len(positions)}")

    boxes: list[tuple[int, Box]] = []
    collinear: list[tuple[int, tuple[tuple[int, int], tuple[int, int]]]] = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            errors.append(f"colour {color} must appear exactly twice, found {len(cells)}")
            continue
        (row_a, col_a), (row_b, col_b) = cells
        if row_a != row_b and col_a != col_b:
            row0, row1 = sorted((row_a, row_b))
            col0, col1 = sorted((col_a, col_b))
            boxes.append((color, (row0, col0, row1, col1)))
        else:
            collinear.append((color, ((row_a, col_a), (row_b, col_b))))

    if len(boxes) < 2:
        errors.append(f"expected at least two diagonal target pairs, found {len(boxes)}")
    for left_index, (left_color, left_box) in enumerate(boxes):
        for right_color, right_box in boxes[left_index + 1 :]:
            if _boxes_overlap(left_box, right_box):
                errors.append(
                    "diagonal rectangle boxes must be disjoint; implied boxes "
                    f"for colours {left_color} and {right_color} overlap"
                )
    for color, endpoints in collinear:
        for _box_color, box in boxes:
            if any(cell in _box_cells(box) for cell in endpoints):
                errors.append(
                    f"collinear colour {color} must lie outside diagonal rectangles"
                )
                break

    signature = (height, width, len(boxes), len(collinear))
    scene_profile = _PROFILE_BY_SIGNATURE.get(signature)
    if teaching and not errors:
        for color, (row0, col0, row1, col1) in boxes:
            if row1 - row0 < 2 or col1 - col0 < 2:
                errors.append(
                    "teaching rectangles must have a visible interior; "
                    f"colour {color} span={(row1-row0, col1-col0)}"
                )
        for color, (first, second) in collinear:
            span = abs(first[0] - second[0]) + abs(first[1] - second[1])
            if span < 2:
                errors.append(
                    f"teaching collinear colour {color} must span at least three cells"
                )
        if scene_profile is None:
            errors.append(
                "teaching scene must realize one declared linked "
                f"(height,width,diagonal-count,collinear-count) profile, found {signature}"
            )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "positions": dict(positions),
        "boxes": boxes,
        "collinear": collinear,
        "scene_profile": scene_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the intended authority-level input grammar."""
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
    """Validate the generated lesson grammar and exact linked profile axis."""
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
    """Index the four published (height,width,palette-size) profiles."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    signatures = (
        (10, 11, 3),
        (10, 12, 3),
        (11, 12, 3),
        (11, 11, 3),
    )
    palette_size = len(analysis["positions"]) + 1
    signature = (analysis["height"], analysis["width"], palette_size)
    try:
        return signatures.index(signature)
    except ValueError:
        return None


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for color, (row0, col0, row1, col1) in analysis["boxes"]:
        for row in range(row0, row1 + 1):
            for col in range(col0, col1 + 1):
                output[row][col] = color
    return output


def _rival_outline_rectangles(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = [list(row) for row in grid]
    for color, (row0, col0, row1, col1) in analysis["boxes"]:
        for col in range(col0, col1 + 1):
            output[row0][col] = color
            output[row1][col] = color
        for row in range(row0, row1 + 1):
            output[row][col0] = color
            output[row][col1] = color
    return output


def _rival_fill_all_two_cell_bboxes(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    output = [list(row) for row in grid]
    for color, cells in analysis["positions"].items():
        (row_a, col_a), (row_b, col_b) = cells
        for row in range(min(row_a, row_b), max(row_a, row_b) + 1):
            for col in range(min(col_a, col_b), max(col_a, col_b) + 1):
                output[row][col] = color
    return output


def _rival_global_bbox(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    endpoints = [cell for _color, box in analysis["boxes"] for cell in ((box[0], box[1]), (box[2], box[3]))]
    row0 = min(row for row, _col in endpoints)
    row1 = max(row for row, _col in endpoints)
    col0 = min(col for _row, col in endpoints)
    col1 = max(col for _row, col in endpoints)
    first_color = analysis["boxes"][0][0]
    output = [list(row) for row in grid]
    for row in range(row0, row1 + 1):
        for col in range(col0, col1 + 1):
            output[row][col] = first_color
    return output


def _rival_copy_markers(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def strict_canonical_like(grid) -> list[str]:
    """The complete generated grammar is a canonical-like task manifold."""
    return teaching_check(grid)


def _valid_analysis(grid: Grid) -> dict[str, Any] | None:
    analysis = _analysis(grid, teaching=True)
    return None if analysis["errors"] else analysis


def _multiple_rectangles(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["boxes"]) >= 2


def _solid_interior_required(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and all(
        box[2] - box[0] >= 2 and box[3] - box[1] >= 2
        for _color, box in analysis["boxes"]
    )


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


def _collinear_distractor(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["collinear"]) >= 1


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "multiple_rectangles": _multiple_rectangles,
    "solid_interior_required": _solid_interior_required,
    "tall_rectangle": _tall_rectangle,
    "wide_rectangle": _wide_rectangle,
    "collinear_distractor": _collinear_distractor,
}

SEMANTIC_RIVALS = {
    "outline_rectangles": _rival_outline_rectangles,
    "fill_all_two_cell_bboxes": _rival_fill_all_two_cell_bboxes,
    "global_bbox": _rival_global_bbox,
    "copy_markers": _rival_copy_markers,
}
WITNESS_RIVALS = {
    "multiple_rectangles": ["global_bbox", "copy_markers"],
    "solid_interior_required": ["outline_rectangles", "copy_markers"],
    "tall_rectangle": ["outline_rectangles", "copy_markers"],
    "wide_rectangle": ["outline_rectangles", "copy_markers"],
    "collinear_distractor": ["fill_all_two_cell_bboxes"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to eliminate outline, collinear, global-box, and copy rivals."""
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
            reasons.append(f"demo {index} output is not the per-colour solid rectangle fill")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
