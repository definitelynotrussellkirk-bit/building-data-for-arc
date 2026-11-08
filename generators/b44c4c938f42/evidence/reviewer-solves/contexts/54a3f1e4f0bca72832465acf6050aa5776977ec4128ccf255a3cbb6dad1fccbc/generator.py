"""Input generator for ARC task 337b420f / b44c4c938f42.

The canonical rule splits an input on all-zero separator columns, selects the
largest same-color 4-connected non-8 component in each panel, sorts those
objects largest-first, and greedily overlays them on one panel-width canvas
using a fixed sequence of small conflict-avoiding shifts.

Version 3 repairs the former curriculum defect: one-component panels made
"largest component" observationally identical to "all components".  Every
ordinary draw now has one unique-largest object and one disconnected same-color
distractor per panel, and the selected objects overlap before placement so the
conflict-shift branch is also taught by every example.  Version 3.1 alternates
small-winner/singleton-distractor and larger-winner/domino-distractor examples,
so short lessons also refute fixed absolute component-size thresholds.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b44c4c938f42"
TASK_ID = GENERATOR_ID
RULE_HASH = "10339930cb51"
VERSION = "3.1.0"
SUMMARY = (
    "Zero-separated panels each contain a unique-largest colored component and "
    "a same-color distractor; largest components are overlaid largest-first with "
    "conflict-avoiding shifts on one 8-background panel."
)

INVARIANTS = [
    "two or three equal-width panels are separated by single all-zero columns",
    "each panel has background 8 and exactly two same-color 4-connected components",
    "the larger component in every panel is unique and panel colors are distinct",
    "selected components overlap at zero shift, but all fit under the authority shift list",
    "ordinary draws refute both select-all-components and no-shift rival rules",
    "every four-example production window alternates size-2 winners and size-2 distractors",
]

AXES = {
    "grid_h": {
        "type": "int", "default": "5..8; every fourth sample anchors 5",
        "valid": "5..8",
    },
    "panel_w": {
        "type": "int", "default": "5..7; every fourth sample anchors 5",
        "valid": "5..7",
    },
    "panel_count": {
        "type": "int", "default": "2..3; every fourth sample anchors 3",
        "valid": "2..3",
    },
    "distractor_size": {
        "type": "int", "default": "1..2", "valid": "1..2",
    },
    "size_order": {
        "type": "str", "default": "alternates by sample index",
        "valid": "ascending|descending",
    },
    "rotation": {
        "type": "int", "default": "sample index modulo 4", "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

EXAMPLES_NEEDED = 3

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SHIFTS = (
    (0, 0), (0, -1), (0, 1), (-1, 0), (1, 0),
    (-1, -1), (-1, 1), (1, -1), (1, 1),
    (0, -2), (0, 2), (-2, 0), (2, 0),
)

# Shapes are expressed in a 5x5 local teaching frame.  The two profiles
# deliberately cross the absolute-size boundary: the small profile contains a
# size-2 winner with singleton distractors, while the standard profile contains
# size-2 distractors with winners of size at least 3.  Within each profile the
# selected objects overlap at zero shift and fit under the authority shift list.
_SMALL_MAIN_BY_SIZE = {
    2: frozenset({(1, 1), (2, 1)}),
    3: frozenset({(1, 1), (2, 1), (2, 2)}),
    4: frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}),
}
_STANDARD_MAIN_BY_SIZE = {
    5: frozenset({(1, 1), (2, 0), (2, 1), (2, 2), (3, 1)}),
    4: frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}),
    3: frozenset({(3, 3), (4, 3), (4, 4)}),
}
_SMALL_DISTRACTOR_BY_SIZE = {
    2: ((4, 4),),
    3: ((4, 4),),
    4: ((4, 3),),
}
_STANDARD_DISTRACTOR_BY_SIZE = {
    5: ((0, 3), (0, 4)),
    4: ((4, 3), (4, 4)),
    3: ((0, 0), (0, 1)),
}


def _rotate5(cells, turns: int):
    result = set(cells)
    for _ in range(turns % 4):
        result = {(c, 4 - r) for r, c in result}
    return frozenset(result)


def _embed(cells, h: int, w: int):
    roff = (h - 5) // 2
    coff = (w - 5) // 2
    return frozenset((r + roff, c + coff) for r, c in cells)


def _split_panels(grid):
    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    starts = [0] + [c + 1 for c in separators]
    ends = separators + [w]
    return [[row[a:b] for row in grid] for a, b in zip(starts, ends) if a < b]


def _components(panel):
    h, w = len(panel), len(panel[0])
    seen = set()
    records = []
    for r in range(h):
        for c in range(w):
            color = panel[r][c]
            if color == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and panel[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            records.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "size": len(cells),
            })
    return records


def _place(records, h: int, w: int, *, shifts=_SHIFTS):
    placed = {}
    used = []
    for obj in sorted(records, key=lambda item: item["size"], reverse=True):
        selected_shift = None
        for dr, dc in shifts:
            cells = [(r + dr, c + dc) for r, c in obj["cells"]]
            if all(0 <= r < h and 0 <= c < w and (r, c) not in placed for r, c in cells):
                for cell in cells:
                    placed[cell] = obj["color"]
                selected_shift = (dr, dc)
                break
        used.append((obj["color"], selected_shift))
    output = [[placed.get((r, c), 8) for c in range(w)] for r in range(h)]
    return output, used


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket authority (for contracts/tests)."""
    panels = _split_panels(grid)
    selected = [max(_components(panel), key=lambda obj: obj["size"]) for panel in panels]
    return _place(selected, len(grid), len(panels[0][0]))[0]


def _all_components_rival(grid):
    panels = _split_panels(grid)
    records = [obj for panel in panels for obj in _components(panel)]
    return _place(records, len(grid), len(panels[0][0]))[0]


def _zero_shift_rival(grid):
    panels = _split_panels(grid)
    selected = [max(_components(panel), key=lambda obj: obj["size"]) for panel in panels]
    return _place(selected, len(grid), len(panels[0][0]), shifts=((0, 0),))[0]


def _absolute_size_gt_1_rival(grid):
    panels = _split_panels(grid)
    selected = [obj for panel in panels for obj in _components(panel) if obj["size"] > 1]
    return _place(selected, len(grid), len(panels[0][0]))[0]


def _absolute_size_gt_2_rival(grid):
    panels = _split_panels(grid)
    selected = [obj for panel in panels for obj in _components(panel) if obj["size"] > 2]
    return _place(selected, len(grid), len(panels[0][0]))[0]


def _validate_override_types(overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name in ("grid_h", "panel_w", "panel_count", "distractor_size", "rotation"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    if ("size_order" in overrides and overrides["size_order"] is not None and
            type(overrides["size_order"]) is not str):
        raise TypeError("size_order override must be a string")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    _validate_override_types(overrides)

    # Exact canonical profile support is deterministic in every band.  User
    # overrides still win because setdefault never replaces them.
    effective = dict(overrides)
    if sample_index % 4 == 0:
        effective.setdefault("grid_h", 5)
        effective.setdefault("panel_w", 5)
        effective.setdefault("panel_count", 3)
    # Alternate the two size profiles in every band.  Any three examples from a
    # four-example production window contain both a size-2 winner and a size-2
    # distractor, refuting fixed thresholds (>1 and >2) under query rotation.
    # Band-specific phase/seed choices keep difficulty behavior observable.
    if difficulty == "easy":
        default_distractor = 1 if sample_index % 2 == 0 else 2
    elif difficulty == "hard":
        default_distractor = 2 if sample_index % 2 == 0 else 1
    else:
        default_distractor = 1 if (seed + sample_index) % 2 == 0 else 2
    effective.setdefault("distractor_size", default_distractor)
    effective.setdefault("size_order", "ascending" if sample_index % 2 == 0 else "descending")
    effective.setdefault("rotation", sample_index % 4)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_strict("grid_h", 5, 8)
    panel_w = ctx.draw_int_strict("panel_w", 5, 7)
    panel_count = ctx.draw_int_strict("panel_count", 2, 3)
    distractor_size = ctx.draw_int_strict("distractor_size", 1, 2)
    size_order = ctx.draw_choice("size_order", ("ascending", "descending"))
    rotation = ctx.draw_int_strict("rotation", 0, 3)
    colors = ctx.draw_distinct_colors("colors", n=panel_count, exclude={0, 8})

    if distractor_size == 1:
        profile = "small"
        main_templates = _SMALL_MAIN_BY_SIZE
        distractor_templates = _SMALL_DISTRACTOR_BY_SIZE
        ranked_sizes = [2, 3] if panel_count == 2 else [2, 3, 4]
    else:
        profile = "standard"
        main_templates = _STANDARD_MAIN_BY_SIZE
        distractor_templates = _STANDARD_DISTRACTOR_BY_SIZE
        ranked_sizes = [4, 5] if panel_count == 2 else [3, 4, 5]
    if size_order == "descending":
        ranked_sizes.reverse()

    width = panel_count * panel_w + panel_count - 1
    grid = full_grid(h, width, 8)
    for separator_index in range(1, panel_count):
        separator = separator_index * panel_w + separator_index - 1
        for r in range(h):
            grid[r][separator] = 0

    for panel_index, (color, main_size) in enumerate(zip(colors, ranked_sizes)):
        start_c = panel_index * (panel_w + 1)
        main = _embed(_rotate5(main_templates[main_size], rotation), h, panel_w)
        distractor_template = _rotate5(
            distractor_templates[main_size][:distractor_size], rotation)
        distractor = _embed(distractor_template, h, panel_w)
        for r, c in main | distractor:
            grid[r][start_c + c] = color

    # These are construction assertions, not acceptance filters.  A future edit
    # that breaks the teaching witness fails loudly instead of silently emitting
    # ambiguous data.
    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    official = rule_mirror(grid)
    if official == _all_components_rival(grid):
        raise AssertionError("construction failed to distinguish all-components rival")
    if official == _zero_shift_rival(grid):
        raise AssertionError("construction failed to distinguish no-shift rival")
    return grid


def _analysis(grid):
    errors = []
    facts = {}
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if any(not isinstance(row, list) or not row for row in grid):
        return {"errors": ["every row must be a non-empty list"]}
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        return {"errors": ["grid must be rectangular"]}
    if any(type(value) is not int or not (0 <= value <= 9) for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9 (not bool)"]}

    h, w = len(grid), len(grid[0])
    separators = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    if not separators:
        return {"errors": ["expected all-zero separator columns"]}
    if separators[0] == 0 or separators[-1] == w - 1:
        errors.append("separator cannot be at an outer edge")
    if any(b == a + 1 for a, b in zip(separators, separators[1:])):
        errors.append("separator columns must be single-width")

    starts = [0] + [c + 1 for c in separators]
    ends = separators + [w]
    spans = [(a, b) for a, b in zip(starts, ends) if a < b]
    panels = [[row[a:b] for row in grid] for a, b in spans]
    if len(panels) not in (2, 3):
        errors.append(f"expected 2 or 3 panels; found {len(panels)}")
    panel_widths = {len(panel[0]) for panel in panels} if panels else set()
    if len(panel_widths) != 1:
        errors.append("panels must have equal width")

    panel_facts = []
    panel_colors = []
    for index, panel in enumerate(panels):
        records = _components(panel)
        colors = {obj["color"] for obj in records}
        if len(colors) != 1:
            errors.append(f"panel {index} must use exactly one non-8 color")
        if len(records) != 2:
            errors.append(f"panel {index} must contain exactly two components; found {len(records)}")
        sizes = sorted((obj["size"] for obj in records), reverse=True)
        if len(sizes) >= 2 and sizes[0] == sizes[1]:
            errors.append(f"panel {index} has no unique largest component")
        if records:
            panel_colors.append(records[0]["color"])
        panel_facts.append({"records": records, "sizes": sizes})
    if len(panel_colors) != len(set(panel_colors)):
        errors.append("panel object colors must be distinct")

    facts.update({
        "errors": errors,
        "h": h,
        "w": w,
        "separators": separators,
        "spans": spans,
        "panels": panels,
        "panel_width": next(iter(panel_widths)) if len(panel_widths) == 1 else None,
        "panel_facts": panel_facts,
    })
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    facts = _analysis(grid)
    if facts["errors"]:
        return {}
    result = {
        "grid_h": facts["h"],
        "panel_w": facts["panel_width"],
        "panel_count": len(facts["panels"]),
    }
    sizes_by_panel = [row["sizes"] for row in facts["panel_facts"]]
    distractors = [sizes[1] for sizes in sizes_by_panel]
    if len(set(distractors)) == 1:
        result["distractor_size"] = distractors[0]
    largest = [sizes[0] for sizes in sizes_by_panel]
    if all(a < b for a, b in zip(largest, largest[1:])):
        result["size_order"] = "ascending"
    elif all(a > b for a, b in zip(largest, largest[1:])):
        result["size_order"] = "descending"

    h, panel_w = facts["h"], facts["panel_width"]
    profile_templates = (_SMALL_MAIN_BY_SIZE if min(largest) == 2
                         else _STANDARD_MAIN_BY_SIZE)
    rotations = []
    for rotation in range(4):
        matches = True
        for panel_fact in facts["panel_facts"]:
            largest_obj = max(panel_fact["records"], key=lambda obj: obj["size"])
            size = largest_obj["size"]
            template = profile_templates.get(size)
            if template is None:
                matches = False
                break
            expected = _embed(_rotate5(template, rotation), h, panel_w)
            if frozenset(largest_obj["cells"]) != expected:
                matches = False
                break
        if matches:
            rotations.append(rotation)
    if len(rotations) == 1:
        result["rotation"] = rotations[0]
    return result


def _witness_all_components(grid):
    try:
        return rule_mirror(grid) != _all_components_rival(grid)
    except Exception:
        return False


def _witness_conflict_shift(grid):
    try:
        return rule_mirror(grid) != _zero_shift_rival(grid)
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable] = {
    "select_all_components": _all_components_rival,
    "overlay_without_shifts": _zero_shift_rival,
}
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "absolute_size_gt_1": _absolute_size_gt_1_rival,
    "absolute_size_gt_2": _absolute_size_gt_2_rival,
}
SEMANTIC_WITNESSES = {
    "distractor_requires_largest_selection": _witness_all_components,
    "overlap_requires_conflict_shift": _witness_conflict_shift,
}
WITNESS_RIVALS = {
    "distractor_requires_largest_selection": ["select_all_components"],
    "overlap_requires_conflict_shift": ["overlay_without_shifts"],
}


def lesson_identifiable(demos, query):
    reasons = []
    query_grid = query["input"]
    authority_query = rule_mirror(query_grid)
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query_grid) != authority_query:
            reasons.append(f"declared rival {name!r} fits every demo but changes the query")
    return reasons
