"""Generator for arc_puzzle_bank_thirteenth21:H88 — mask one panel, then crop.

A full-height colour-9 separator splits the input into equal left and right
panels.  The left panel is a binary mask: keep each non-zero right-panel cell
only when the corresponding left-panel cell is also non-zero, then crop the
surviving coloured image to its tight non-zero bounding box.

The generated teaching distribution deliberately includes right-only cells,
left-only cells, internal holes, multicolour right images, and outputs smaller
than either source panel.  Those cases refute the tempting shortcuts "copy the
right crop", "recolour the left mask", "do not crop", "fill the bbox", and
"use one modal right colour".
"""
from __future__ import annotations

from collections import Counter
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2bcad02eb7da"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "558c87e0fb71"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.30

SUMMARY = (
    "Split at the full-height 9 column, use the left panel as a non-zero mask "
    "on the coloured right panel, and crop the surviving right colours. "
    "Generated scenes make masking, colour preservation, and final cropping "
    "independently observable."
)

INVARIANTS = [
    "exactly one full-height colour-9 separator column",
    "equal-width left and right panels",
    "the left panel is a monochrome non-zero mask",
    "the right panel is a non-empty coloured image and may be multicolour or disconnected",
    "left and right non-zero masks have a non-empty intersection",
]

HELPFUL_TEXTURES = ("canonical", "warm", "cool", "varied")
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every declared axis is exact and recoverable from the returned grid.  The
# small count ranges are intentional: even the all-minimum 3x3 panel can hold
# overlap_k=4 plus two left-only and two right-only cells without conflict.
AXES = {
    "panel_h": {"type": "int", "default": "difficulty-skewed", "valid": "3..6"},
    "panel_w": {"type": "int", "default": "difficulty-skewed", "valid": "3..6"},
    "overlap_k": {"type": "int", "default": "scheduled 1,2,4,5", "valid": "1..5"},
    "left_extra": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
    "right_extra": {"type": "int", "default": "scheduled 1..2", "valid": "1..2"},
    "texture": {
        "type": "str",
        "default": "scheduled",
        "valid": "canonical|warm|cool|varied",
    },
}

_TEXTURE_LEFT_COLOR = {
    "canonical": 1,
    "warm": 2,
    "cool": 8,
    "varied": 3,
}
_TEXTURE_RIGHT_PALETTE = {
    "canonical": (4, 5, 6),
    "warm": (3, 4, 5),
    "cool": (1, 6, 7),
    "varied": (2, 4, 6, 8),
}
_LEFT_COLOR_TEXTURE = {value: name for name, value in _TEXTURE_LEFT_COLOR.items()}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Five consecutive sample indexes contain two canonical anchors plus every
# broader texture and overlap-size branch.  The semantic gate's five-demo
# lessons therefore refute colour and geometry shortcuts deterministically.
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % 5


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _neighbors(cell, h, w):
    row, col = cell
    for dr, dc in _CARDINAL:
        nr, nc = row + dr, col + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _place_overlap(rng, h, w, k):
    """Sample an exact-k pattern whose tight bbox is smaller than the panel.

    For k>=2 the bbox also contains at least one zero.  This makes both the
    crop and the difference between true masking and bbox filling observable.
    """
    rectangles = [
        (rect_h, rect_w)
        for rect_h in range(1, h + 1)
        for rect_w in range(1, w + 1)
        if rect_h * rect_w >= k + (1 if k >= 2 else 0)
        and (rect_h < h or rect_w < w)
    ]
    if not rectangles:
        raise ValueError(f"no lawful overlap rectangle for panel {h}x{w}, k={k}")
    rng.shuffle(rectangles)
    for rect_h, rect_w in rectangles:
        local = [(row, col) for row in range(rect_h) for col in range(rect_w)]
        for _ in range(80):
            chosen = set(rng.sample(local, k))
            rows = {row for row, _ in chosen}
            cols = {col for _, col in chosen}
            if min(rows) != 0 or max(rows) != rect_h - 1:
                continue
            if min(cols) != 0 or max(cols) != rect_w - 1:
                continue
            top = rng.randrange(h - rect_h + 1)
            left = rng.randrange(w - rect_w + 1)
            return {(top + row, left + col) for row, col in chosen}
    raise ValueError(f"could not sample exact overlap for panel {h}x{w}, k={k}")

def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _choose_extras(rng, h, w, overlap, left_count, right_count):
    """Choose disjoint one-sided cells, preferring holes inside overlap bbox."""
    r0, c0, r1, c1 = _bbox(overlap)
    holes = [
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in overlap
    ]
    outside = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if (row, col) not in overlap and (row, col) not in holes
    ]
    rng.shuffle(holes)
    rng.shuffle(outside)
    available = holes + outside
    need = left_count + right_count
    if len(available) < need:
        raise ValueError(
            f"panel {h}x{w} cannot hold overlap={len(overlap)}, "
            f"left_extra={left_count}, right_extra={right_count}"
        )
    chosen = available[:need]
    return set(chosen[:left_count]), set(chosen[left_count:])


def _split(grid):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("empty or non-grid value")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    height = len(grid)
    separators = [
        col for col in range(width) if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected exactly one full-height 9 separator, got {separators}")
    sep = separators[0]
    if sep * 2 + 1 != width:
        raise ValueError(f"separator at {sep} does not split width {width} equally")
    left = [row[:sep] for row in grid]
    right = [row[sep + 1 :] for row in grid]
    return sep, left, right


def _nonzero_cells(panel):
    return {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    }


def _crop_nonzero(grid):
    cells = _nonzero_cells(grid)
    if not cells:
        return [[0]]
    r0, c0, r1, c1 = _bbox(cells)
    return [list(row[c0 : c1 + 1]) for row in grid[r0 : r1 + 1]]


def semantic_observables(grid):
    """Recover all exact axes and decisive task facts from returned cells."""
    sep, left, right = _split(grid)
    left_mask = _nonzero_cells(left)
    right_mask = _nonzero_cells(right)
    overlap = left_mask & right_mask
    left_colors = {left[row][col] for row, col in left_mask}
    right_colors = {right[row][col] for row, col in right_mask}
    texture = (
        _LEFT_COLOR_TEXTURE.get(next(iter(left_colors)))
        if len(left_colors) == 1
        else "mixed_or_invalid"
    )
    output = rule_mirror(grid)
    out_cells = _nonzero_cells(output)
    return {
        "panel_h": len(grid),
        "panel_w": sep,
        "overlap_k": len(overlap),
        "left_extra": len(left_mask - overlap),
        "right_extra": len(right_mask - overlap),
        "texture": texture,
        "left_mask": left_mask,
        "right_mask": right_mask,
        "overlap": overlap,
        "left_colors": left_colors,
        "right_colors": right_colors,
        "output": output,
        "output_colors": {output[row][col] for row, col in out_cells},
        "output_bbox_area": len(output) * len(output[0]),
    }


def observe_overrides(grid):
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def rule_mirror(grid):
    """Independent Python mirror; canonical Racket remains output authority."""
    _, left, right = _split(grid)
    masked = [
        [
            right[row][col]
            if left[row][col] != 0 and right[row][col] != 0
            else 0
            for col in range(len(left[0]))
        ]
        for row in range(len(left))
    ]
    return _crop_nonzero(masked)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the full lawful masking grammar and reject malformed scenes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["empty or non-grid value"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colours 0..9"]

    errors = []
    try:
        sep, left, right = _split(grid)
    except ValueError as exc:
        return [str(exc)]

    height = len(grid)
    if not 2 <= height <= 8 or not 2 <= sep <= 8:
        errors.append(f"panel dimensions {height}x{sep} outside supported 2..8")
    if any(
        grid[row][col] == 9
        for row in range(height)
        for col in range(width)
        if col != sep
    ):
        errors.append("colour 9 may appear only in the separator column")

    left_mask = _nonzero_cells(left)
    right_mask = _nonzero_cells(right)
    if not left_mask:
        errors.append("left mask must contain at least one non-zero cell")
    if not right_mask:
        errors.append("right image must contain at least one non-zero cell")
    left_colors = {left[row][col] for row, col in left_mask}
    if len(left_colors) != 1:
        errors.append(f"left panel must be a monochrome mask, got {sorted(left_colors)}")
    if left_mask and right_mask and not (left_mask & right_mask):
        errors.append("left and right non-zero masks must overlap")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the scale/palette manifold shown by all three canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["panel_h"] != 4 or facts["panel_w"] not in (3, 4):
        reasons.append("canonical panels are height 4 and width 3 or 4")
    if facts["left_colors"] != {1}:
        reasons.append("canonical left masks use colour 1")
    if len(facts["right_colors"]) != 1 or not facts["right_colors"] <= {4, 5, 6}:
        reasons.append("canonical right images are monochrome in colour 4, 5, or 6")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)

    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = {
        "texture": ("canonical", "canonical", "warm", "cool", "varied")[profile],
        "overlap_k": (1, 2, 3, 4, 5)[profile],
        "left_extra": 1,
        "right_extra": 1,
    }
    # One quarter of ordinary draws are deliberately canonical-scale in every
    # difficulty band, preventing hard-band drift away from the examples.
    if profile in (0, 1):
        scheduled["panel_h"] = 4
        scheduled["panel_w"] = 3 + (seed % 2)
    effective = {**scheduled, **overrides}

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    panel_h = ctx.draw_int_diff("panel_h", 3, 6)
    panel_w = ctx.draw_int("panel_w", 3, 6)
    overlap_k = ctx.draw_int("overlap_k", 1, 5)
    left_extra = ctx.draw_int("left_extra", 1, 2)
    right_extra = ctx.draw_int("right_extra", 1, 2)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    rng = ctx.draw_rng("layout")

    overlap = _place_overlap(rng, panel_h, panel_w, overlap_k)
    left_only, right_only = _choose_extras(
        rng, panel_h, panel_w, overlap, left_extra, right_extra
    )
    left_mask = overlap | left_only
    right_mask = overlap | right_only

    grid = full_grid(panel_h, panel_w * 2 + 1, 0)
    for row in range(panel_h):
        grid[row][panel_w] = 9

    left_color = _TEXTURE_LEFT_COLOR[texture]
    for row, col in left_mask:
        grid[row][col] = left_color

    palette = _TEXTURE_RIGHT_PALETTE[texture]
    if texture == "canonical":
        palette = (rng.choice(palette),)
    ordered_right = sorted(right_mask)
    # Cycle colors over overlap first so every non-canonical k>=2 output is
    # genuinely multicolour; right-only cells follow without changing overlap.
    ordered_overlap = sorted(overlap)
    ordered_extras = [cell for cell in ordered_right if cell not in overlap]
    for index, (row, col) in enumerate(ordered_overlap + ordered_extras):
        grid[row][panel_w + 1 + col] = palette[index % len(palette)]

    observed = observe_overrides(grid)
    expected = {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "overlap_k": overlap_k,
        "left_extra": left_extra,
        "right_extra": right_extra,
        "texture": texture,
    }
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Named wrong rules and task-linked semantic witnesses.
# ---------------------------------------------------------------------------


def _modal_nonzero(panel):
    counts = Counter(value for row in panel for value in row if value != 0)
    if not counts:
        return 0
    best = max(counts.values())
    return min(color for color, count in counts.items() if count == best)


def _rival_copy_right_crop(grid):
    _, _, right = _split(grid)
    return _crop_nonzero(right)


def _rival_left_shape_modal(grid):
    _, left, right = _split(grid)
    color = _modal_nonzero(right)
    recolored = [[color if value != 0 else 0 for value in row] for row in left]
    return _crop_nonzero(recolored)


def _rival_no_crop(grid):
    _, left, right = _split(grid)
    return [
        [
            right[row][col]
            if left[row][col] != 0 and right[row][col] != 0
            else 0
            for col in range(len(left[0]))
        ]
        for row in range(len(left))
    ]


def _rival_modal_overlap(grid):
    _, left, right = _split(grid)
    color = _modal_nonzero(right)
    masked = [
        [color if left[row][col] != 0 and right[row][col] != 0 else 0
         for col in range(len(left[0]))]
        for row in range(len(left))
    ]
    return _crop_nonzero(masked)


def _rival_bbox_fill(grid):
    true = rule_mirror(grid)
    color = _modal_nonzero(true)
    return [[color for _ in row] for row in true]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "copy_right_crop": _rival_copy_right_crop,
    "left_shape_modal": _rival_left_shape_modal,
    "no_crop": _rival_no_crop,
    "modal_overlap": _rival_modal_overlap,
    "bbox_fill": _rival_bbox_fill,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"modal_overlap": _rival_modal_overlap}


def _lawful_difference(rival):
    def witness(grid):
        return not self_check(grid) and rule_mirror(grid) != rival(grid)
    return witness


SEMANTIC_WITNESSES = {
    "left_mask_filters_right": _lawful_difference(_rival_copy_right_crop),
    "right_image_filters_left": _lawful_difference(_rival_left_shape_modal),
    "final_crop_changes_canvas": _lawful_difference(_rival_no_crop),
    "right_colours_are_preserved": _lawful_difference(_rival_modal_overlap),
    "overlap_is_not_bbox_fill": _lawful_difference(_rival_bbox_fill),
}
WITNESS_RIVALS = {
    "left_mask_filters_right": ["copy_right_crop"],
    "right_image_filters_left": ["left_shape_modal"],
    "final_crop_changes_canvas": ["no_crop"],
    "right_colours_are_preserved": ["modal_overlap"],
    "overlap_is_not_bbox_fill": ["bbox_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every named shortcut."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with mask-then-crop")
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with mask-then-crop")
    if reasons:
        return reasons

    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            relation = (
                "same query answer"
                if rival(query["input"]) == query["output"]
                else "different query answer"
            )
            reasons.append(
                f"competing rule {name!r} survives every demonstration ({relation})"
            )
    return reasons
