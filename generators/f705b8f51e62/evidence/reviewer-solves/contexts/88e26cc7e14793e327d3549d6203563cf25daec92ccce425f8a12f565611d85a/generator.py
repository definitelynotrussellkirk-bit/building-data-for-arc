"""Generator for H2 — infer a full shape from copies and recolor it by its defect.

The selected Racket authority identifies the largest normalized component shape,
finds the unique smaller component whose normalized cells are a strict subset,
and outputs the full shape painted with that defective component's color.

Canonical examples are monochrome, so the tempting shortcut "crop any largest
component" fits every source pair.  This curriculum keeps frequent canonical-
profile anchors but alternates in contrast examples where the defective copy has
a distinct color.  Every three-example lesson therefore contains an observable
color-transfer witness while preserving the original component/shape grammar.
"""
from __future__ import annotations

from itertools import combinations
from math import ceil
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f705b8f51e62"
TASK_ID = GENERATOR_ID
RULE_HASH = "4ad429046360"
VERSION = "4.0.0"

SUMMARY = (
    "A 0-background grid contains two to four complete copies of one connected "
    "polyomino and exactly one connected defective strict subset. Canonical-profile "
    "anchors are monochrome; contrast examples give the defect a distinct color. "
    "Output the full normalized polyomino painted in the defective copy's color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical", "contrast")
BAND_DEFAULTS = {
    None: {
        "template_size": tuple(range(4, 10)),
        "n_canon": (2, 3, 4),
        "missing": (1, 2),
    },
    "easy": {
        "template_size": (4, 5),
        "n_canon": (3, 4),
        "missing": (1,),
    },
    "medium": {
        "template_size": (5, 6, 7),
        "n_canon": (2, 3, 4),
        "missing": (1, 2),
    },
    "hard": {
        "template_size": (7, 8, 9),
        "n_canon": (2, 3),
        "missing": (2,),
    },
}

INVARIANTS = [
    "background is 0 and every nonzero component is monochrome and 4-connected",
    "two to four largest components are identical normalized full copies",
    "exactly one smaller component is a connected strict normalized subset",
    "the defect is missing one or two cells from a 4..9-cell full template",
    "full copies share one color; the defect either matches it or has one distinct color",
    "components are separated by a one-cell moat so object extraction is unambiguous",
]

AXES = {
    "profile": {
        "type": "str",
        "default": "alternating canonical|contrast lesson schedule",
        "valid": "canonical|contrast",
    },
    "template_size": {
        "type": "int",
        "default": "4 on canonical anchors; easy 4..5, medium 5..7, hard 7..9 on contrast",
        "valid": "4..9",
    },
    "n_canon": {
        "type": "int",
        "default": "2 on canonical anchors; easy 3..4, medium 2..4, hard 2..3 on contrast",
        "valid": "2..4",
    },
    "missing": {
        "type": "int",
        "default": "1 on canonical anchors; easy 1, medium 1..2, hard 2 on contrast",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORHOOD = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
)
Grid = list[list[int]]
Shape = tuple[tuple[int, int], ...]
Rival = Callable[[Sequence[Sequence[int]]], Grid]


def _norm(cells: Sequence[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _shape(cells: Sequence[tuple[int, int]]) -> Shape:
    return tuple(sorted(_norm(cells)))


def _connected(cells: Sequence[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    start = min(remaining)
    seen = {start}
    stack = [start]
    while stack:
        row, col = stack.pop()
        for dr, dc in _CARDINAL:
            point = row + dr, col + dc
            if point in remaining and point not in seen:
                seen.add(point)
                stack.append(point)
    return len(seen) == len(remaining)


def _bbox_size(shape: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _transform(shape: Sequence[tuple[int, int]], code: int) -> Shape:
    transformed = []
    for row, col in shape:
        if code == 0:
            point = row, col
        elif code == 1:
            point = row, -col
        elif code == 2:
            point = -row, col
        elif code == 3:
            point = -row, -col
        elif code == 4:
            point = col, row
        elif code == 5:
            point = col, -row
        elif code == 6:
            point = -col, row
        elif code == 7:
            point = -col, -row
        else:  # defensive: callers use 0..7
            raise ValueError(f"unknown transform code: {code}")
        transformed.append(point)
    return _shape(transformed)


def _grow_polyomino(rng, size: int) -> Shape:
    cells = {(0, 0)}
    while len(cells) < size:
        frontier = sorted({
            (row + dr, col + dc)
            for row, col in cells
            for dr, dc in _CARDINAL
            if (row + dr, col + dc) not in cells
        })
        cells.add(rng.choice(frontier))
    return _shape(tuple(cells))


def _fallback_template(size: int) -> Shape:
    width = (size + 1) // 2
    top = [(0, col) for col in range(width)]
    lower_count = size - width
    bottom = [(1, col) for col in range(width - lower_count, width)]
    return _shape(top + bottom)


def _defective_candidates(template: Shape, missing: int) -> tuple[Shape, ...]:
    canonical = frozenset(template)
    candidates: set[Shape] = set()
    for removed in combinations(template, missing):
        kept = set(template) - set(removed)
        if len(kept) < 2 or not _connected(tuple(kept)):
            continue
        normalized = _norm(tuple(kept))
        if normalized < canonical:
            candidates.add(tuple(sorted(normalized)))
    return tuple(sorted(candidates))


def _template_and_defect(ctx, size: int, missing: int) -> tuple[Shape, Shape]:
    rng = ctx.draw_rng("template_shape")
    for _ in range(160):
        template = _transform(_grow_polyomino(rng, size), rng.randrange(8))
        height, width = _bbox_size(template)
        if min(height, width) < 2:
            continue
        candidates = _defective_candidates(template, missing)
        if candidates:
            return template, rng.choice(candidates)

    template = _fallback_template(size)
    candidates = _defective_candidates(template, missing)
    if not candidates:  # exhaustive defensive guard for the fixed 4..9 catalog
        raise AssertionError(f"no lawful defect for fallback size={size} missing={missing}")
    return template, ctx.draw_rng("fallback_defect").choice(candidates)


def _can_place(grid: Grid, shape: Shape, row0: int, col0: int) -> bool:
    height, width = len(grid), len(grid[0])
    for dr, dc in shape:
        row, col = row0 + dr, col0 + dc
        if not (0 <= row < height and 0 <= col < width):
            return False
        for nr, nc in _NEIGHBORHOOD:
            rr, cc = row + nr, col + nc
            if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 0:
                return False
    return True


def _paint(grid: Grid, shape: Shape, row0: int, col0: int, color: int) -> None:
    for dr, dc in shape:
        grid[row0 + dr][col0 + dc] = color


def _pack_exact(
    height: int,
    width: int,
    pieces: Sequence[tuple[Shape, int]],
    rng,
) -> Grid | None:
    """Backtracking packer used only for the three-piece canonical anchors."""
    grid = full_grid(height, width, 0)
    ordered = list(pieces)
    rng.shuffle(ordered)

    def place(index: int) -> bool:
        if index == len(ordered):
            return True
        shape, color = ordered[index]
        sh, sw = _bbox_size(shape)
        positions = [
            (row, col)
            for row in range(height - sh + 1)
            for col in range(width - sw + 1)
        ]
        rng.shuffle(positions)
        for row0, col0 in positions:
            if not _can_place(grid, shape, row0, col0):
                continue
            _paint(grid, shape, row0, col0, color)
            if place(index + 1):
                return True
            for dr, dc in shape:
                grid[row0 + dr][col0 + dc] = 0
        return False

    return grid if place(0) else None


def _pack_broad(
    ctx,
    template: Shape,
    defective: Shape,
    n_canon: int,
    full_color: int,
    defective_color: int,
) -> Grid:
    pieces = [(template, full_color) for _ in range(n_canon)]
    pieces.append((defective, defective_color))
    ctx.draw_rng("component_order").shuffle(pieces)

    max_height = max(_bbox_size(shape)[0] for shape, _ in pieces)
    max_width = max(_bbox_size(shape)[1] for shape, _ in pieces)
    slot_height = max_height + 2
    slot_width = max_width + 2
    count = len(pieces)
    feasible_columns = []
    for columns in range(1, count + 1):
        rows = ceil(count / columns)
        base_height = rows * slot_height + 1
        base_width = columns * slot_width + 1
        if base_height <= 26 and base_width <= 26:
            feasible_columns.append(columns)
    if not feasible_columns:
        raise AssertionError("component slots do not fit an ARC canvas")

    columns = ctx.draw_rng("layout").choice(feasible_columns)
    rows = ceil(count / columns)
    base_height = rows * slot_height + 1
    base_width = columns * slot_width + 1
    extra_height = ctx.draw_int("padding_height", 0, min(4, 30 - base_height))
    extra_width = ctx.draw_int("padding_width", 0, min(4, 30 - base_width))
    top = ctx.draw_int("top_offset", 0, extra_height)
    left = ctx.draw_int("left_offset", 0, extra_width)
    grid = full_grid(base_height + extra_height, base_width + extra_width, 0)

    for index, (shape, color) in enumerate(pieces):
        slot_row, slot_col = divmod(index, columns)
        sh, sw = _bbox_size(shape)
        jitter = ctx.draw_rng(f"piece_jitter_{index}")
        row0 = top + 1 + slot_row * slot_height + jitter.randint(0, max_height - sh)
        col0 = left + 1 + slot_col * slot_width + jitter.randint(0, max_width - sw)
        if not _can_place(grid, shape, row0, col0):
            raise AssertionError("constructive slot placement unexpectedly collided")
        _paint(grid, shape, row0, col0, color)
    return grid


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    phase = (int(seed) ^ (int(seed) >> 1)) & 1
    return SCHEDULE_PROFILES[(int(sample_index) + phase) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_choices = SCHEDULE_PROFILES if overrides.get("profile") is not None else (scheduled,)
    profile = str(ctx.draw_choice("profile", profile_choices))

    anchor = (
        profile == "canonical"
        and overrides.get("template_size") is None
        and overrides.get("n_canon") is None
        and overrides.get("missing") is None
    )
    if anchor:
        # Frequent exact canonical-profile support: dimensions/palette match one
        # of the source inputs while shapes and placements remain freshly drawn.
        template_size = int(ctx.draw_choice("template_size", (4,)))
        n_canon = int(ctx.draw_choice("n_canon", (2,)))
        missing = int(ctx.draw_choice("missing", (1,)))
    else:
        defaults = BAND_DEFAULTS[difficulty]
        template_size = (
            ctx.draw_int_strict("template_size", 4, 9)
            if overrides.get("template_size") is not None
            else int(ctx.draw_choice("template_size", defaults["template_size"]))
        )
        n_canon = (
            ctx.draw_int_strict("n_canon", 2, 4)
            if overrides.get("n_canon") is not None
            else int(ctx.draw_choice("n_canon", defaults["n_canon"]))
        )
        missing = (
            ctx.draw_int_strict("missing", 1, 2)
            if overrides.get("missing") is not None
            else int(ctx.draw_choice("missing", defaults["missing"]))
        )

    template, defective = _template_and_defect(ctx, template_size, missing)
    full_color, contrast_color = ctx.draw_distinct_colors("component_colors", n=2, exclude=(0,))
    defective_color = full_color if profile == "canonical" else contrast_color
    pieces = [(template, full_color) for _ in range(n_canon)] + [(defective, defective_color)]

    if anchor:
        canonical_sizes = ((7, 9), (8, 10), (7, 11))
        height, width = ctx.draw_rng("canonical_canvas").choice(canonical_sizes)
        grid = _pack_exact(height, width, pieces, ctx.draw_rng("canonical_placement"))
        if grid is None:
            # All size-4 templates fit the source canvases; this is a loud guard,
            # not a silent distribution fallback.
            raise AssertionError(f"could not pack canonical anchor into {(height, width)}")
    else:
        grid = _pack_broad(
            ctx, template, defective, n_canon, full_color, defective_color
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"constructed invalid {profile} example: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "profile": profile,
        "template_size": template_size,
        "n_canon": n_canon,
        "missing": missing,
    }
    if observed != expected:
        raise AssertionError(f"requested {expected}, observed {observed}")
    return [row[:] for row in grid]


def _components(grid: Sequence[Sequence[int]]):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((int(color), tuple(sorted(cells))))
    return result


def _entries(grid: Sequence[Sequence[int]]):
    result = []
    for color, cells in _components(grid):
        result.append({
            "color": color,
            "cells": cells,
            "shape": _norm(cells),
            "bbox": (
                min(row for row, _ in cells),
                min(col for _, col in cells),
                max(row for row, _ in cells),
                max(col for _, col in cells),
            ),
        })
    return result


def _shape_grid(shape: Sequence[tuple[int, int]], color: int) -> Grid:
    height, width = _bbox_size(tuple(shape))
    out = full_grid(height, width, 0)
    for row, col in shape:
        out[row][col] = int(color)
    return out


def _analysis(grid: Sequence[Sequence[int]]):
    entries = _entries(grid)
    if not entries:
        return None
    largest = max(len(item["shape"]) for item in entries)
    fulls = [item for item in entries if len(item["shape"]) == largest]
    defectives = [item for item in entries if len(item["shape"]) < largest]
    canonical = fulls[0]["shape"] if fulls else frozenset()
    subset_defects = [item for item in defectives if item["shape"] < canonical]
    return entries, fulls, defectives, subset_defects, canonical


def observe_overrides(grid: Sequence[Sequence[int]]) -> dict[str, object | None]:
    try:
        analysed = _analysis(grid)
    except Exception:
        analysed = None
    if analysed is None:
        return {"profile": None, "template_size": None, "n_canon": None, "missing": None}
    _, fulls, defectives, subset_defects, canonical = analysed
    if len(defectives) != 1 or len(subset_defects) != 1 or not fulls:
        return {"profile": None, "template_size": len(canonical) or None,
                "n_canon": len(fulls), "missing": None}
    full_colors = {item["color"] for item in fulls}
    defective = defectives[0]
    if len(full_colors) != 1:
        profile = None
    elif defective["color"] in full_colors:
        profile = "canonical"
    else:
        profile = "contrast"
    return {
        "profile": profile,
        "template_size": len(canonical),
        "n_canon": len(fulls),
        "missing": len(canonical) - len(defective["shape"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be non-empty and rectangular"]
    if len(grid) > 30 or width > 30:
        errors.append(f"ARC grids must be at most 30x30, got {len(grid)}x{width}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("all cells must be integer ARC colors 0..9 (bool is not accepted)")
        return errors

    entries = _entries(grid)
    if not 3 <= len(entries) <= 5:
        errors.append(f"expected 3..5 nonzero components, got {len(entries)}")
        return errors
    analysed = _analysis(grid)
    assert analysed is not None
    _, fulls, defectives, subset_defects, canonical = analysed
    if not 4 <= len(canonical) <= 9:
        errors.append(f"canonical template must contain 4..9 cells, got {len(canonical)}")
    if not 2 <= len(fulls) <= 4:
        errors.append(f"expected 2..4 full copies, got {len(fulls)}")
    if len({item["shape"] for item in fulls}) != 1:
        errors.append("largest components must have one identical normalized shape")
    if len(defectives) != 1:
        errors.append(f"expected exactly one smaller defective component, got {len(defectives)}")
    if len(subset_defects) != 1:
        errors.append("the unique smaller component must be a strict normalized subset")
    if len(defectives) == 1:
        missing = len(canonical) - len(defectives[0]["shape"])
        if missing not in (1, 2):
            errors.append(f"defective copy must be missing 1 or 2 cells, got {missing}")
    full_colors = {item["color"] for item in fulls}
    if len(full_colors) != 1:
        errors.append("all full copies must share one color")
    if len(defectives) == 1 and len(full_colors) == 1:
        colors = full_colors | {defectives[0]["color"]}
        if len(colors) not in (1, 2):
            errors.append("defect color must match the full copies or be one distinct color")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    entries = _entries(grid)
    if not entries:
        raise ValueError("no nonzero components")
    canonical_entry = sorted(
        entries, key=lambda item: (-len(item["shape"]), item["bbox"])
    )[0]
    canonical = canonical_entry["shape"]
    hits = [
        item for item in entries
        if item["shape"] != canonical and item["shape"] < canonical
    ]
    defective = hits[0] if hits else min(entries, key=lambda item: len(item["shape"]))
    return _shape_grid(tuple(canonical), int(defective["color"]))


def _crop_largest_component(grid: Sequence[Sequence[int]]) -> Grid:
    entries = _entries(grid)
    if not entries:
        raise ValueError("no nonzero components")
    chosen = sorted(entries, key=lambda item: (-len(item["shape"]), item["bbox"]))[0]
    return _shape_grid(tuple(chosen["shape"]), int(chosen["color"]))


CANONICAL_SHORTCUTS: dict[str, Rival] = {
    "crop_largest_component": _crop_largest_component,
}
SEMANTIC_RIVALS: dict[str, Rival] = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS: dict[str, Rival] = dict(SEMANTIC_RIVALS)


def _defective_color_transfer(grid: Sequence[Sequence[int]]) -> bool:
    return (
        observe_overrides(grid).get("profile") == "contrast"
        and _crop_largest_component(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Sequence[Sequence[int]]], bool]] = {
    "defective_color_transfer": _defective_color_transfer,
}
WITNESS_RIVALS = {
    "defective_color_transfer": ["crop_largest_component"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, item in enumerate(demos):
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"demo {index} is not a labeled pair")
            continue
        errors = self_check(item["input"])
        if errors:
            reasons.append(f"demo {index} is outside grammar: {errors[0]}")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not a labeled pair")
    else:
        errors = self_check(query["input"])
        if errors:
            reasons.append(f"query is outside grammar: {errors[0]}")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(item["input"]) == item["output"] for item in demos):
            reasons.append(f"{name} fits every demonstration")
    return reasons
