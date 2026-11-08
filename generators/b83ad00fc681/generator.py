"""Generator for keyed multicolor prototype-dictionary stamping.

The top four rows contain compact multicolor prototypes separated by full
color-9 columns.  The unique minimum color in each panel is its key/anchor.
After a full color-9 divider, isolated key-colored cells request copies of the
corresponding prototype, preserving colors and anchor-relative offsets.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b83ad00fc681"
TASK_ID = GENERATOR_ID
RULE_HASH = "46157a601fce"
VERSION = "2.0.0"

SUMMARY = (
    "A four-row dictionary contains 3-4 compact multicolor prototypes, split "
    "by full color-9 columns.  Each prototype's unique minimum color is its "
    "key and anchor.  Below a full color-9 divider, every key-colored marker "
    "is replaced by the complete anchor-relative prototype on a blank body."
)

INVARIANTS = [
    "background is color 0; color 9 is used only for the panel separators and divider",
    "the dictionary has 3-4 connected prototypes of equal size 3-5",
    "each prototype has one unique minimum-color key, and keys are distinct",
    "the body has 4-5 markers and uses every dictionary key at least once",
    "all requested stamps fit and occupy disjoint 3x3 placement slots",
]

AXES = {
    "grid_h": {"type": "int", "default": "10..14; scheduled canonical profiles", "valid": "10..14"},
    "grid_w": {"type": "int", "default": "15..20; scheduled canonical profiles", "valid": "15..20"},
    "n_panels": {"type": "int", "default": "3..4; canonical schedule uses 3", "valid": "3..4"},
    "marker_count": {"type": "int", "default": "4..5", "valid": "4..5"},
    "motif_size": {"type": "int", "default": "3..5; canonical schedule uses 4", "valid": "3..5"},
    "color_count": {"type": "int", "default": "8..9; canonical schedule uses 8", "valid": "8..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_PROFILES = ((11, 15, 8), (12, 15, 8), (12, 16, 8))
SCHEDULE_PROFILES = ("canonical", "broad")
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
_TOP_H = 4
_DIVIDER = 9

# Compact connected bases.  D4 variants are formed below; every bounding box is
# at most 3x3, which makes all advertised marker-count combinations constructive
# even on the smallest 5x15 body.
_BASE_SHAPES = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)),
    ),
}

# Exact public-canonical dictionary.  The corresponding rule is intentionally
# WRONG on generated inputs: it ignores the visible dictionary and memorizes
# the three repeated public prototypes.
_FIXED_CANONICAL_PATTERNS = {
    1: ((0, 0, 1), (0, 1, 5), (1, 0, 5), (1, 1, 5)),
    2: ((-1, 0, 6), (0, 0, 2), (0, 1, 6), (1, 0, 6)),
    3: ((0, 0, 3), (0, 1, 7), (0, 2, 7), (1, 1, 7)),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every fourth sample index is an exact canonical size/palette anchor."""
    return "canonical" if sample_index % 4 == 0 else "broad"


def _normalize(cells):
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_variants(size: int):
    variants = set()
    for base in _BASE_SHAPES[size]:
        for reflected in (False, True):
            cells = tuple((r, -c if reflected else c) for r, c in base)
            for turns in range(4):
                current = cells
                for _ in range(turns):
                    current = tuple((c, -r) for r, c in current)
                norm = _normalize(current)
                height = 1 + max(r for r, _ in norm)
                width = 1 + max(c for _, c in norm)
                if height <= 3 and width <= 3:
                    variants.add(norm)
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {size: _shape_variants(size) for size in _BASE_SHAPES}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _draw_axis(ctx, overrides, name, lo, hi, *, scheduled=None, favored=()):
    """Use a scheduled default while retaining the entire exact override domain."""
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    if scheduled is not None:
        return ctx.draw_int_strict(name, scheduled, scheduled)
    choices = list(range(lo, hi + 1)) + list(favored) * 8
    return ctx.draw_choice(name, choices)


def _broad_favored(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (10, 11), "grid_w": (15, 16), "n_panels": (3,),
            "marker_count": (4,), "motif_size": (3, 4), "color_count": (8,),
        }
    if difficulty == "hard":
        return {
            "grid_h": (13, 14), "grid_w": (19, 20), "n_panels": (4,),
            "marker_count": (5,), "motif_size": (5,), "color_count": (9,),
        }
    return {name: () for name in AXES}


def _panel_widths(width: int, count: int, rng, *, canonical: bool):
    content = width - (count - 1)
    if content < 3 * count:
        raise ValueError("canvas is too narrow for the requested panel count")
    if canonical:
        base, extra = divmod(content, count)
        return [base] * (count - extra) + [base + 1] * extra
    widths = [3] * count
    for _ in range(content - 3 * count):
        widths[rng.randrange(count)] += 1
    return widths


def _panel_spans(widths):
    spans = []
    left = 0
    for index, panel_width in enumerate(widths):
        spans.append((left, left + panel_width))
        left += panel_width
        if index + 1 < len(widths):
            left += 1
    return spans


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    queue = deque([next(iter(remaining))])
    seen = set(queue)
    while queue:
        r, c = queue.popleft()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return len(seen) == len(remaining)


def _build_dictionary(ctx, grid, spans, n_panels, motif_size, color_count):
    palette_rng = ctx.draw_rng("palette")
    if n_panels == 3:
        keys = palette_rng.sample((1, 2, 3), 2) + [4]
    else:
        keys = [1, 2, 3, 4]
    palette_rng.shuffle(keys)
    decoration_count = color_count - 2 - n_panels
    decorations = palette_rng.sample((5, 6, 7, 8), decoration_count)

    motifs = []
    open_slots = []
    for index, (left, right) in enumerate(spans):
        rng = ctx.draw_rng(f"prototype_{index}")
        candidates = [
            shape for shape in _SHAPE_VARIANTS[motif_size]
            if 1 + max(c for _, c in shape) <= right - left
        ]
        shape = rng.choice(candidates)
        shape_h = 1 + max(r for r, _ in shape)
        shape_w = 1 + max(c for _, c in shape)
        top = rng.randint(0, _TOP_H - shape_h)
        offset = rng.randint(0, right - left - shape_w)
        anchor = rng.choice(shape)
        absolute = tuple((top + r, left + offset + c) for r, c in shape)
        anchor_absolute = (top + anchor[0], left + offset + anchor[1])
        motifs.append({
            "key": keys[index], "cells": absolute, "anchor": anchor_absolute,
        })
        for cell in absolute:
            if cell != anchor_absolute:
                open_slots.append((index, cell))

    # Every selected decoration is realized at least once; remaining motif cells
    # reuse those colors.  Keys and decorations are disjoint, so each key stays
    # the unique minimum of its own panel.
    palette_rng.shuffle(open_slots)
    assigned = list(decorations)
    while len(assigned) < len(open_slots):
        assigned.append(palette_rng.choice(decorations))
    palette_rng.shuffle(assigned)
    colors_by_cell = {slot: color for slot, color in zip(open_slots, assigned)}

    patterns = {}
    for index, motif in enumerate(motifs):
        key = motif["key"]
        ar, ac = motif["anchor"]
        rels = []
        for cell in motif["cells"]:
            r, c = cell
            color = key if cell == motif["anchor"] else colors_by_cell[(index, cell)]
            grid[r][c] = color
            rels.append((r - ar, c - ac, color))
        patterns[key] = tuple(rels)
    return keys, patterns


def _put_markers(ctx, grid, patterns, keys, marker_count):
    body_h = len(grid) - (_TOP_H + 1)
    width = len(grid[0])
    rng = ctx.draw_rng("marker_layout")
    marker_keys = list(keys)
    while len(marker_keys) < marker_count:
        marker_keys.append(rng.choice(keys))
    rng.shuffle(marker_keys)

    # Five nonoverlapping 3x3 boxes always fit in the smallest body (5x15).
    strip_top = rng.randint(0, body_h - 3)
    horizontal_slack = width - 15
    strip_left = rng.randint(0, horizontal_slack)
    slots = [(strip_top, strip_left + 3 * index) for index in range(5)]
    rng.shuffle(slots)

    for key, (box_top, box_left) in zip(marker_keys, slots):
        pattern = patterns[key]
        min_dr = min(dr for dr, _, _ in pattern)
        min_dc = min(dc for _, dc, _ in pattern)
        anchor_r = box_top - min_dr
        anchor_c = box_left - min_dc
        grid[_TOP_H + 1 + anchor_r][anchor_c] = key


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    profile_name = schedule_profile(seed, sample_index, difficulty)
    canonical = profile_name == "canonical"
    scheduled = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES) if canonical else None
    favored = _broad_favored(difficulty)

    height = _draw_axis(
        ctx, overrides, "grid_h", 10, 14,
        scheduled=scheduled[0] if scheduled else None,
        favored=favored["grid_h"],
    )
    width = _draw_axis(
        ctx, overrides, "grid_w", 15, 20,
        scheduled=scheduled[1] if scheduled else None,
        favored=favored["grid_w"],
    )
    n_panels = _draw_axis(
        ctx, overrides, "n_panels", 3, 4,
        scheduled=3 if canonical else None,
        favored=favored["n_panels"],
    )
    marker_count = _draw_axis(
        ctx, overrides, "marker_count", 4, 5,
        scheduled=4 if canonical else None,
        favored=favored["marker_count"],
    )
    motif_size = _draw_axis(
        ctx, overrides, "motif_size", 3, 5,
        scheduled=4 if canonical else None,
        favored=favored["motif_size"],
    )
    color_count = _draw_axis(
        ctx, overrides, "color_count", 8, 9,
        scheduled=scheduled[2] if scheduled else None,
        favored=favored["color_count"],
    )

    grid = full_grid(height, width, 0)
    widths = _panel_widths(
        width, n_panels, ctx.draw_rng("panel_widths"), canonical=canonical,
    )
    spans = _panel_spans(widths)
    for left, right in spans[:-1]:
        separator = right
        for r in range(_TOP_H):
            grid[r][separator] = _DIVIDER
    for c in range(width):
        grid[_TOP_H][c] = _DIVIDER

    keys, patterns = _build_dictionary(
        ctx, grid, spans, n_panels, motif_size, color_count,
    )
    _put_markers(ctx, grid, patterns, keys, marker_count)
    return grid


def _split_structure(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")
    divider_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    if divider_rows != [_TOP_H]:
        raise ValueError(f"expected exactly one full color-9 divider at row 4, found {divider_rows}")
    if len(grid) <= _TOP_H + 1:
        raise ValueError("divider must leave a nonempty body")
    top = grid[:_TOP_H]
    body = grid[_TOP_H + 1:]
    sep_cols = [c for c in range(width) if all(top[r][c] == 9 for r in range(_TOP_H))]
    if any(top[r][c] == 9 and c not in sep_cols for r in range(_TOP_H) for c in range(width)):
        raise ValueError("color 9 may appear in the dictionary only as a full separator column")
    if any(value == 9 for row in body for value in row):
        raise ValueError("color 9 may not appear in the body")
    spans = []
    start = 0
    for cut in sep_cols + [width]:
        if cut <= start:
            raise ValueError("empty or adjacent prototype panels")
        spans.append((start, cut))
        start = cut + 1
    return top, body, spans


def _parse_patterns(grid):
    top, body, spans = _split_structure(grid)
    patterns = {}
    panel_sizes = []
    for left, right in spans:
        if right - left < 3:
            raise ValueError("prototype panels must be at least three columns wide")
        cells = [
            (r, c, top[r][c])
            for r in range(_TOP_H)
            for c in range(left, right)
            if top[r][c] != 0
        ]
        if not cells:
            raise ValueError("every panel needs a prototype")
        positions = {(r, c) for r, c, _ in cells}
        if not _connected(positions):
            raise ValueError("each prototype must be 4-connected")
        key = min(value for _, _, value in cells)
        anchors = [(r, c) for r, c, value in cells if value == key]
        if len(anchors) != 1:
            raise ValueError("prototype minimum/key must be unique")
        if key in patterns:
            raise ValueError("prototype keys must be distinct")
        ar, ac = anchors[0]
        patterns[key] = tuple((r - ar, c - ac, value) for r, c, value in cells)
        panel_sizes.append(len(cells))
    return body, spans, patterns, panel_sizes


def self_check(grid, *, difficulty=None, meta=None):
    try:
        body, spans, patterns, panel_sizes = _parse_patterns(grid)
    except (TypeError, ValueError, IndexError) as exc:
        return [str(exc)]
    errors = []
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 14:
        errors.append(f"grid height {height} outside 10..14")
    if not 15 <= width <= 20:
        errors.append(f"grid width {width} outside 15..20")
    if not 3 <= len(spans) <= 4:
        errors.append(f"need 3-4 prototype panels, found {len(spans)}")
    if len(set(panel_sizes)) != 1 or not 3 <= panel_sizes[0] <= 5:
        errors.append(f"prototype sizes must agree in 3..5, found {panel_sizes}")
    markers = [(r, c, value) for r, row in enumerate(body) for c, value in enumerate(row) if value != 0]
    if not 3 <= len(markers) <= 6:
        errors.append(f"body needs 3-6 markers, found {len(markers)}")
    keys = set(patterns)
    if any(value not in keys for _, _, value in markers):
        errors.append("every body marker must name a prototype key")
    used = {value for _, _, value in markers}
    if used != keys:
        errors.append(f"every prototype key must be requested; used={sorted(used)}, keys={sorted(keys)}")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (8, 9):
        errors.append(f"realized color count must be 8 or 9, found {palette_size}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    body, spans, patterns, panel_sizes = _parse_patterns(grid)
    if len(set(panel_sizes)) != 1:
        raise ValueError("cannot observe one motif_size from unequal panels")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_panels": len(spans),
        "marker_count": sum(value != 0 for row in body for value in row),
        "motif_size": panel_sizes[0],
        "color_count": len({value for row in grid for value in row}),
    }


def _stamp(grid, patterns):
    body, _, _, _ = _parse_patterns(grid)
    height, width = len(body), len(body[0])
    out = full_grid(height, width, 0)
    for r in range(height):
        for c in range(width):
            pattern = patterns.get(body[r][c])
            if pattern is None:
                continue
            for dr, dc, color in pattern:
                rr, cc = r + dr, c + dc
                if 0 <= rr < height and 0 <= cc < width:
                    out[rr][cc] = color
    return out


def _intended_python(grid):
    _, _, patterns, _ = _parse_patterns(grid)
    return _stamp(grid, patterns)


def _fixed_canonical_dictionary(grid):
    return _stamp(grid, _FIXED_CANONICAL_PATTERNS)


def _fixed_dictionary_counterexample(grid):
    return _intended_python(grid) != _fixed_canonical_dictionary(grid)


SEMANTIC_WITNESSES = {
    "fixed_dictionary_counterexample": _fixed_dictionary_counterexample,
}
SEMANTIC_RIVALS = {
    "fixed_canonical_dictionary": _fixed_canonical_dictionary,
}
WITNESS_RIVALS = {
    "fixed_dictionary_counterexample": ["fixed_canonical_dictionary"],
}
CANONICAL_SHORTCUTS = {
    "fixed_canonical_dictionary": _fixed_canonical_dictionary,
}
LESSON_COMPETITORS = {
    "fixed_canonical_dictionary": _fixed_canonical_dictionary,
}
