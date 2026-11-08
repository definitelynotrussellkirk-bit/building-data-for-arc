"""Generator for the typed shape/color relation-matrix task.

Color-9 frames form a top gallery and a left gallery.  Each frame contains
one colored shape.  For every (left, top) pair, the canonical rule emits 8 for
same rotation class and same color, 6 for shape only, 3 for color only, and 0
for neither.

The sampler deliberately constructs all three positive relation types, then
permutes both galleries independently.  This preserves teaching support while
preventing the old fixed-position 2x2 answer template.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "5fdbbb5a53ef"
TASK_ID = GENERATOR_ID
RULE_HASH = "b12aeca2f818"
VERSION = "3.1.0"
SUMMARY = (
    "0-background grids contain color-9 5x5 frames in top and left galleries. "
    "Each 3x3 interior contains one colored shape.  The output is a left-by-top "
    "relation matrix: 8=same shape up to rotation and same color, 6=shape only, "
    "3=color only, 0=neither.  Gallery order, sizes, offsets, shapes, rotations, "
    "and colors vary; every generated input teaches 8, 6, and 3."
)

INVARIANTS = [
    "color-9 5x5 frames form one minimum-row top gallery and one minimum-column left gallery",
    "every framed 3x3 interior is nonempty and uses exactly one color from 1..8",
    "generated inputs contain at least two top and two left frames",
    "generated relation matrices contain joint, shape-only, and color-only matches",
    "top and left frame order are independently permuted rather than tied to relation type",
]

AXES = {
    "top_count": {"type": "int", "default": "difficulty-aware; seed-hashed canonical support", "valid": "2..4"},
    "left_count": {"type": "int", "default": "difficulty-aware; seed-hashed canonical support", "valid": "2..3"},
    "row_offset": {"type": "int", "default": "0..2; canonical support uses 2", "valid": "0..2"},
    "col_offset": {"type": "int", "default": "0..2; canonical support uses 2", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"top_count": 4, "col_offset": 2},
]
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("canonical_support", "broad")
MIN_STRICT_FRAC = 1.0

_MOTIFS = (
    ((0, 0), (1, 0), (1, 1)),                 # L tromino
    ((0, 0), (0, 1), (0, 2)),                 # I tromino
    ((0, 0), (0, 1), (1, 1), (1, 2)),         # S tetromino
    ((0, 0), (0, 1), (0, 2), (1, 1)),         # T tetromino
    ((0, 0), (1, 0), (2, 0), (2, 1)),         # L tetromino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)), # plus
)
_COLORS = tuple(range(1, 9))
_ALLOWED_OVERRIDES = frozenset(AXES)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return a deterministic, seed-sensitive curriculum profile.

    A hash-based quarter-rate avoids a short fixed sample-index period while
    still providing frequent canonical morphology and palette-role support.
    """
    payload = f"{TASK_ID}:{VERSION}:{seed}:{sample_index}:{difficulty or 'default'}"
    bucket = hashlib.sha256(payload.encode("utf-8")).digest()[0]
    return "canonical_support" if bucket < 64 else "broad"


def _norm(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rot_cw(cells):
    return [(col, -row) for row, col in cells]


def _rotations_norm(cells):
    current = list(cells)
    result = set()
    for _ in range(4):
        result.add(_norm(current))
        current = _rot_cw(current)
    return result


def _realize(rng, motif):
    cells = list(motif)
    for _ in range(rng.randint(0, 3)):
        cells = _rot_cw(cells)
    normalized = sorted(_norm(cells))
    if max(row for row, _ in normalized) > 2 or max(col for _, col in normalized) > 2:
        normalized = sorted(_norm(motif))
    return normalized


def _paint_panel(grid, top, left, cells, color):
    draw_frame(grid, top, left, top + 4, left + 4, 9)
    for row, col in cells:
        grid[top + 1 + row][left + 1 + col] = color


def _other_cls(rng, cls):
    return rng.choice([index for index in range(len(_MOTIFS)) if index != cls])


def _make_spec(rng, cls=None, color=None):
    if cls is None:
        cls = rng.randrange(len(_MOTIFS))
    if color is None:
        color = rng.choice(_COLORS)
    return {
        "cls": cls,
        "cells": _realize(rng, _MOTIFS[cls]),
        "color": color,
    }


def _draw_axis(ctx, label, legal, default):
    """Draw an exact integer axis; explicit overrides always see the full legal domain."""
    options = tuple(legal if ctx.overrides.get(label) is not None else default)
    return ctx.draw_choice(label, options)


def _draw_layout(ctx, difficulty, overrides):
    profile = schedule_profile(ctx.seed, ctx.sample_index, difficulty)

    requested_top = overrides.get("top_count")
    requested_col = overrides.get("col_offset")
    if requested_top == 4 and requested_col == 2:
        raise ValueError("top_count=4 is incompatible with col_offset=2 (width would exceed 30)")

    top_legal = (2, 3) if requested_col == 2 else (2, 3, 4)
    if profile == "canonical_support":
        top_default = (3,) if requested_col != 2 or 3 in top_legal else top_legal
        left_default = (3,)
        row_default = (2,)
    elif difficulty == "easy":
        top_default = tuple(value for value in (2, 2, 3) if value in top_legal)
        left_default = (2, 2, 3)
        row_default = (0, 1, 2)
    elif difficulty == "hard":
        top_default = tuple(value for value in (3, 4, 4) if value in top_legal)
        left_default = (2, 3, 3)
        row_default = (0, 1, 2)
    else:
        top_default = top_legal
        left_default = (2, 3)
        row_default = (0, 1, 2)

    top_count = _draw_axis(ctx, "top_count", top_legal, top_default)
    left_count = _draw_axis(ctx, "left_count", (2, 3), left_default)
    row_offset = _draw_axis(ctx, "row_offset", (0, 1, 2), row_default)

    col_legal = (0, 1) if top_count == 4 else (0, 1, 2)
    if profile == "canonical_support" and top_count == 3:
        col_default = (2,)
    else:
        col_default = col_legal
    col_offset = _draw_axis(ctx, "col_offset", col_legal, col_default)
    return top_count, left_count, row_offset, col_offset


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an exact integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")

    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    top_count, left_count, row_offset, col_offset = _draw_layout(ctx, difficulty, overrides)

    height = row_offset + 6 * left_count + 5
    width = col_offset + 6 * top_count + 5
    if height > 30 or width > 30:
        raise ValueError(f"layout exceeds ARC bounds: {height}x{width}")
    grid = full_grid(height, width, 0)

    rng = ctx.draw_rng("panel_content")
    base_cls = rng.randrange(len(_MOTIFS))
    color_only_cls = _other_cls(rng, base_cls)
    profile = schedule_profile(ctx.seed, ctx.sample_index, difficulty)
    if profile == "canonical_support" and top_count >= 3 and left_count >= 3:
        # Match a real canonical palette-role signature without copying a
        # canonical scene: two relation-label colors are already present in the
        # input, one is introduced by the output, and three input roles vanish.
        base_color, other_color = rng.sample((3, 6, 8), 2)
        top_extra_color, left_extra_color = rng.sample((1, 2, 4, 5, 7), 2)
    else:
        base_color, other_color, top_extra_color, left_extra_color = rng.sample(
            _COLORS, 4
        )

    # These anchors force real examples of all typed relations.  Their eventual
    # positions are not fixed: each gallery is shuffled independently below.
    top_specs = [
        _make_spec(rng, base_cls, base_color),
        _make_spec(rng, color_only_cls, base_color),
    ]
    if top_count >= 3:
        top_specs.append(_make_spec(rng, color=top_extra_color))
    while len(top_specs) < top_count:
        top_specs.append(_make_spec(rng, color=rng.choice(_COLORS)))

    left_specs = [
        _make_spec(rng, base_cls, base_color),
        _make_spec(rng, base_cls, other_color),
    ]
    if left_count >= 3:
        left_specs.append(_make_spec(rng, color=left_extra_color))
    while len(left_specs) < left_count:
        left_specs.append(_make_spec(rng, color=rng.choice(_COLORS)))

    ctx.draw_rng("top_gallery_order").shuffle(top_specs)
    ctx.draw_rng("left_gallery_order").shuffle(left_specs)

    for index, spec in enumerate(top_specs):
        _paint_panel(grid, row_offset, col_offset + 6 * index, spec["cells"], spec["color"])
    for index, spec in enumerate(left_specs):
        _paint_panel(
            grid,
            row_offset + 6 * (index + 1),
            col_offset,
            spec["cells"],
            spec["color"],
        )
    return grid


def _frame_specs_from_grid(grid):
    height, width = len(grid), len(grid[0])
    frames = []
    for top in range(height - 4):
        for left in range(width - 4):
            if any(
                grid[row][col] != 9
                for row in range(top, top + 5)
                for col in range(left, left + 5)
                if row in (top, top + 4) or col in (left, left + 4)
            ):
                continue
            cells = []
            colors = set()
            for row in range(3):
                for col in range(3):
                    value = grid[top + 1 + row][left + 1 + col]
                    if value != 0:
                        cells.append((row, col))
                        colors.add(value)
            if cells:
                frames.append(
                    {
                        "top": top,
                        "left": left,
                        "shape": _norm(cells),
                        "color": next(iter(colors)),
                        "colors": frozenset(colors),
                        "n_colors": len(colors),
                    }
                )
    return frames


def _gallery_parts(grid):
    frames = _frame_specs_from_grid(grid)
    if not frames:
        return frames, [], [], []
    top_band = min(frame["top"] for frame in frames)
    left_band = min(frame["left"] for frame in frames)
    top_frames = sorted(
        (frame for frame in frames if frame["top"] == top_band),
        key=lambda frame: frame["left"],
    )
    left_frames = sorted(
        (
            frame
            for frame in frames
            if frame["left"] == left_band and frame["top"] != top_band
        ),
        key=lambda frame: frame["top"],
    )
    used = {(frame["top"], frame["left"]) for frame in top_frames + left_frames}
    orphans = [frame for frame in frames if (frame["top"], frame["left"]) not in used]
    return frames, top_frames, left_frames, orphans


def _relation_matrix(grid):
    _, top_frames, left_frames, _ = _gallery_parts(grid)
    output = []
    for left in left_frames:
        row = []
        left_rotations = _rotations_norm(left["shape"])
        for top in top_frames:
            same_shape = top["shape"] in left_rotations
            same_color = left["color"] == top["color"]
            row.append(8 if same_shape and same_color else 6 if same_shape else 3 if same_color else 0)
        output.append(row)
    return output, top_frames, left_frames


def _relation_values(grid):
    matrix, top_frames, left_frames = _relation_matrix(grid)
    return [value for row in matrix for value in row], top_frames, left_frames


def observe_overrides(grid):
    """Recover every advertised layout axis from returned pixels."""
    frames, top_frames, left_frames, orphans = _gallery_parts(grid)
    if not frames or orphans or not top_frames or not left_frames:
        raise ValueError("grid does not contain one clean top/left gallery layout")
    return {
        "top_count": len(top_frames),
        "left_count": len(left_frames),
        "row_offset": min(frame["top"] for frame in frames),
        "col_offset": min(frame["left"] for frame in frames),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]

    frames, top_frames, left_frames, orphans = _gallery_parts(grid)
    errors = []
    if not frames:
        return ["no nonempty color-9 5x5 frames found"]
    if len(top_frames) < 2:
        errors.append(f"expected at least two top-gallery frames; found {len(top_frames)}")
    if len(left_frames) < 2:
        errors.append(f"expected at least two left-gallery frames; found {len(left_frames)}")
    if orphans:
        errors.append(f"found {len(orphans)} frame(s) outside the top/left galleries")

    footprints = []
    covered = set()
    for frame in frames:
        footprint = {
            (row, col)
            for row in range(frame["top"], frame["top"] + 5)
            for col in range(frame["left"], frame["left"] + 5)
        }
        if covered & footprint:
            errors.append("frame footprints must not overlap")
        covered |= footprint
        footprints.append(footprint)
        if frame["n_colors"] != 1:
            errors.append("each framed interior must use exactly one non-background color")
        elif frame["color"] not in _COLORS:
            errors.append("framed interior colors must be in 1..8, never 9")

    stray = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in covered
    ]
    if stray:
        errors.append(f"found {len(stray)} non-background cell(s) outside all frames")
    return errors


def strict_canonical_like(grid):
    """Lawful rule inputs in the declared gallery domain."""
    return self_check(grid)


def _fixed_position_template(grid):
    """Rival: predict the old anchor layout without reading panel contents."""
    _, top_frames, left_frames, _ = _gallery_parts(grid)
    rows, cols = len(left_frames), len(top_frames)
    output = [[0 for _ in range(cols)] for _ in range(rows)]
    if rows and cols:
        output[0][0] = 8
    if rows and cols >= 2:
        output[0][1] = 3
    if rows >= 2 and cols:
        output[1][0] = 6
    if rows and cols >= 3:
        output[0][2] = 6
    if rows >= 2 and cols >= 3:
        output[1][2] = 8
    return output


def _has_permuted_relation_positions(grid):
    try:
        matrix, _, _ = _relation_matrix(grid)
        return matrix != _fixed_position_template(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {"permuted_relation_positions": _has_permuted_relation_positions}
SEMANTIC_RIVALS = {"fixed_position_template": _fixed_position_template}
WITNESS_RIVALS = {"permuted_relation_positions": ["fixed_position_template"]}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared shortcut fits every demo but changes the query."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            changes_query = competitor(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} competitor failed to score: {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
