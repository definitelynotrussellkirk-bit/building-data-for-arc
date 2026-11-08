"""Semantic generator for ARC task ae7376fe4957.

The unique color-1 cell is the source marker.  The first color-2 cell in
row-major order is the target marker.  Every other non-zero cell is payload,
including any additional color-2 cells.  Translate the payload by
``target - source``, discard translated cells outside the canvas, and crop the
remaining non-zero result tightly.

Canonical examples make clipping and repeated red cells answer-bearing.  The
ordinary distribution therefore schedules all clipping modes and all four
translation quadrants, while canonical-profile anchors preserve the exact
linked morphologies of the four official inputs under harmless non-marker
color renaming.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ae7376fe4957"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "072dc737db06"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Use the unique blue(1) cell as the source and the first red(2) cell in "
    "row-major order as the target. Translate every other non-zero cell by "
    "the source-to-target vector, including later red cells, clip translated "
    "cells at the canvas boundary, then crop the surviving payload tightly."
)

INVARIANTS = [
    "background is color 0",
    "exactly one color-1 source cell is present",
    "at least one color-2 cell is present; the row-major first is the target",
    "all other non-zero cells are payload, including later color-2 cells",
    "at least one translated payload cell remains in bounds",
    "the answer is the tight crop of the clipped translated payload",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 9..18 with 1/4 canonical anchors",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 9..18 with 1/4 canonical anchors",
        "valid": "9..18",
    },
    "payload_cells": {
        "type": "int",
        "default": "scheduled 6..12; canonical anchors use 6",
        "valid": "6..12",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 2..4 distinct non-marker payload colors",
        "valid": "2..4",
    },
    "extra_reds": {
        "type": "int",
        "default": "general draws alternate 1..2; canonical anchors retain 0..2",
        "valid": "0..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_QUADRANTS = ("down_right", "down_left", "up_right", "up_left")
_CLIPPING_MODES = ("none", "rows", "cols", "both")
_QUADRANT_SIGNS = {
    "down_right": (1, 1),
    "down_left": (1, -1),
    "up_right": (-1, 1),
    "up_left": (-1, -1),
}
_NON_MARKER_COLORS = (3, 4, 5, 6, 7, 8, 9)

# Sparse official inputs.  A/B/C are equality classes for arbitrary
# non-marker colors; R is a payload cell whose literal color is red(2).
_CANONICAL_TEMPLATES = (
    {
        "dims": (10, 10),
        "source": (2, 2),
        "target": (7, 6),
        "payload": (
            (3, 3, "A"),
            (3, 5, "B"),
            (4, 3, "A"),
            (4, 4, "C"),
            (5, 4, "C"),
            (5, 5, "B"),
        ),
    },
    {
        "dims": (11, 12),
        "source": (3, 8),
        "target": (8, 2),
        "payload": (
            (4, 9, "A"),
            (4, 10, "A"),
            (5, 10, "B"),
            (5, 11, "B"),
            (6, 9, "C"),
            (6, 11, "B"),
        ),
    },
    {
        "dims": (9, 13),
        "source": (1, 4),
        "target": (2, 5),
        "payload": (
            (2, 7, "A"),
            (3, 5, "R"),
            (3, 6, "B"),
            (3, 7, "A"),
            (3, 8, "C"),
            (6, 10, "R"),
        ),
    },
    {
        "dims": (12, 12),
        "source": (8, 3),
        "target": (2, 9),
        "payload": (
            (9, 4, "A"),
            (9, 6, "B"),
            (10, 4, "A"),
            (10, 5, "C"),
            (11, 5, "C"),
            (11, 6, "B"),
        ),
    },
)


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    bounds = {
        "grid_h": (9, 18),
        "grid_w": (9, 18),
        "payload_cells": (6, 12),
        "palette_size": (2, 4),
        "extra_reds": (0, 2),
    }
    for name, (lo, hi) in bounds.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def _draw_fixed_or_override(ctx, name: str, lo: int, hi: int, fixed: int) -> int:
    """Use a scheduled default while retaining the full override domain."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, fixed, fixed)


def _canonical_anchor(ctx, seed: int, sample_index: int) -> list[list[int]]:
    template = _CANONICAL_TEMPLATES[(seed + sample_index // 4) % len(_CANONICAL_TEMPLATES)]
    h0, w0 = template["dims"]
    extra_reds0 = sum(label == "R" for _, _, label in template["payload"])
    h = _draw_fixed_or_override(ctx, "grid_h", 9, 18, h0)
    w = _draw_fixed_or_override(ctx, "grid_w", 9, 18, w0)
    _draw_fixed_or_override(ctx, "payload_cells", 6, 12, 6)
    _draw_fixed_or_override(ctx, "palette_size", 2, 4, 3)
    _draw_fixed_or_override(ctx, "extra_reds", 0, 2, extra_reds0)

    grid = full_grid(h, w, 0)
    source = template["source"]
    target = template["target"]
    grid[source[0]][source[1]] = 1
    grid[target[0]][target[1]] = 2
    palette = ctx.draw_rng("anchor_palette").sample(list(_NON_MARKER_COLORS), 3)
    color_for = {"A": palette[0], "B": palette[1], "C": palette[2], "R": 2}
    for row, col, label in template["payload"]:
        grid[row][col] = color_for[label]
    return grid


def _crop_to_content(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [values[left : right + 1] for values in grid[top : bottom + 1]]


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be within ARC bounds 1..30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color from 0 through 9"]
    return []


def _source_and_reds(grid) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    sources: list[tuple[int, int]] = []
    reds: list[tuple[int, int]] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 1:
                sources.append((row, col))
            elif value == 2:
                reds.append((row, col))
    return sources, reds


def _solve_variant(
    grid,
    *,
    target_selector: str = "first",
    drop_all_red_payload: bool = False,
    translate: bool = True,
) -> list[list[int]]:
    errors = _grid_shape_errors(grid)
    if errors:
        raise ValueError(errors[0])
    sources, reds = _source_and_reds(grid)
    if len(sources) != 1 or not reds:
        raise ValueError("variant solver requires exactly one source and at least one red cell")
    source = sources[0]
    if target_selector == "first":
        target = reds[0]
    elif target_selector == "last":
        target = reds[-1]
    elif target_selector == "nearest":
        target = min(
            reds,
            key=lambda cell: (
                abs(cell[0] - source[0]) + abs(cell[1] - source[1]),
                cell,
            ),
        )
    else:
        raise ValueError(f"unknown target selector: {target_selector}")

    delta_row = target[0] - source[0]
    delta_col = target[1] - source[1]
    h, w = len(grid), len(grid[0])
    painted = full_grid(h, w, 0)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (row, col) in (source, target):
                continue
            if drop_all_red_payload and value == 2:
                continue
            out_row = row + delta_row if translate else row
            out_col = col + delta_col if translate else col
            if 0 <= out_row < h and 0 <= out_col < w:
                painted[out_row][out_col] = value
    return _crop_to_content(painted)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    return _solve_variant(grid)


def rival_crop_payload_without_translation(grid) -> list[list[int]]:
    return _solve_variant(grid, translate=False)


def rival_drop_all_red_payload(grid) -> list[list[int]]:
    return _solve_variant(grid, drop_all_red_payload=True)


def rival_use_last_red_target(grid) -> list[list[int]]:
    return _solve_variant(grid, target_selector="last")


def rival_use_nearest_red_target(grid) -> list[list[int]]:
    return _solve_variant(grid, target_selector="nearest")


def _clipping_mode(row_clipped: bool, col_clipped: bool) -> str:
    if row_clipped and col_clipped:
        return "both"
    if row_clipped:
        return "rows"
    if col_clipped:
        return "cols"
    return "none"


def _quadrant(delta_row: int, delta_col: int) -> str | None:
    if delta_row == 0 or delta_col == 0:
        return None
    return (
        ("down" if delta_row > 0 else "up")
        + "_"
        + ("right" if delta_col > 0 else "left")
    )


def semantic_observables(grid) -> dict[str, Any]:
    errors = _grid_shape_errors(grid)
    if errors:
        return {"errors": errors}
    sources, reds = _source_and_reds(grid)
    if len(sources) != 1 or not reds:
        return {
            "errors": [
                f"expected exactly one source and at least one red; got {len(sources)}, {len(reds)}"
            ]
        }
    source = sources[0]
    target = reds[0]
    payload = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0 and (row, col) not in (source, target)
    ]
    delta_row = target[0] - source[0]
    delta_col = target[1] - source[1]
    h, w = len(grid), len(grid[0])
    shifted = [
        (row + delta_row, col + delta_col, value)
        for row, col, value in payload
    ]
    row_clipped = any(not 0 <= row < h for row, _, _ in shifted)
    col_clipped = any(not 0 <= col < w for _, col, _ in shifted)
    survivors = [
        cell for cell in shifted if 0 <= cell[0] < h and 0 <= cell[1] < w
    ]
    non_marker_colors = {value for _, _, value in payload if value not in (1, 2)}
    bbox = None
    if payload:
        bbox = (
            max(row for row, _, _ in payload) - min(row for row, _, _ in payload) + 1,
            max(col for _, col, _ in payload) - min(col for _, col, _ in payload) + 1,
        )
    return {
        "errors": [],
        "grid_h": h,
        "grid_w": w,
        "source": source,
        "target": target,
        "reds": tuple(reds),
        "delta": (delta_row, delta_col),
        "shift_quadrant": _quadrant(delta_row, delta_col),
        "payload": tuple(payload),
        "payload_cells": len(payload),
        "payload_bbox": bbox,
        "palette_size": len(non_marker_colors),
        "extra_reds": len(reds) - 1,
        "survivor_count": len(survivors),
        "clipped_count": len(payload) - len(survivors),
        "clipping_mode": _clipping_mode(row_clipped, col_clipped),
        "output": rule_mirror(grid) if payload and survivors else [],
    }


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return {}
    return {name: facts[name] for name in AXES}


def _build_payload_grid(
    *,
    h: int,
    w: int,
    payload_cells: int,
    palette_size: int,
    extra_reds: int,
    quadrant: str,
    clipping: str,
    rng,
) -> list[list[int]]:
    sign_row, sign_col = _QUADRANT_SIGNS[quadrant]
    max_row_delta = min(5, h - 3)
    max_col_delta = min(5, w - 3)
    layouts: list[tuple[tuple[int, int], tuple[int, int], int, int]] = []
    for row_mag in range(2, max_row_delta + 1):
        for col_mag in range(2, max_col_delta + 1):
            delta_row = sign_row * row_mag
            delta_col = sign_col * col_mag
            for source_row in range(h):
                target_row = source_row + delta_row
                if not 0 <= target_row < h:
                    continue
                for source_col in range(w):
                    target_col = source_col + delta_col
                    if not 0 <= target_col < w:
                        continue
                    layouts.append(
                        (
                            (source_row, source_col),
                            (target_row, target_col),
                            delta_row,
                            delta_col,
                        )
                    )
    rng.shuffle(layouts)

    for source, target, delta_row, delta_col in layouts:
        classified: list[tuple[tuple[int, int], bool, bool]] = []
        for row in range(h):
            for col in range(w):
                if (row, col) in (source, target):
                    continue
                out_row = row + delta_row
                out_col = col + delta_col
                row_oob = not 0 <= out_row < h
                col_oob = not 0 <= out_col < w
                if clipping == "none" and (row_oob or col_oob):
                    continue
                if clipping == "rows" and col_oob:
                    continue
                if clipping == "cols" and row_oob:
                    continue
                classified.append(((row, col), row_oob, col_oob))

        allowed = [cell for cell, _, _ in classified]
        survivors = [
            cell for cell, row_oob, col_oob in classified if not row_oob and not col_oob
        ]
        row_oob_cells = [cell for cell, row_oob, _ in classified if row_oob]
        col_oob_cells = [cell for cell, _, col_oob in classified if col_oob]
        after_target = [cell for cell in survivors if cell > target]
        target_distance = abs(delta_row) + abs(delta_col)
        nearer_after_target = [
            cell
            for cell in after_target
            if abs(cell[0] - source[0]) + abs(cell[1] - source[1]) < target_distance
        ]

        if len(allowed) < payload_cells or not survivors:
            continue
        if clipping in ("rows", "both") and not row_oob_cells:
            continue
        if clipping in ("cols", "both") and not col_oob_cells:
            continue
        if extra_reds and (
            len(after_target) < extra_reds or not nearer_after_target
        ):
            continue

        for _ in range(24):
            selected: set[tuple[int, int]] = set()
            if clipping in ("rows", "both"):
                selected.add(rng.choice(row_oob_cells))
            if clipping in ("cols", "both"):
                selected.add(rng.choice(col_oob_cells))

            red_cells: list[tuple[int, int]] = []
            if extra_reds:
                first_red = rng.choice(nearer_after_target)
                red_cells.append(first_red)
                remaining_reds = [cell for cell in after_target if cell != first_red]
                if len(remaining_reds) < extra_reds - 1:
                    continue
                red_cells.extend(rng.sample(remaining_reds, extra_reds - 1))
                selected.update(red_cells)

            # Keep the plausible "drop later red payload" competitor total:
            # at least one surviving payload cell must be non-red.  Otherwise
            # that rival predicts an empty (invalid ARC) grid and semantic
            # scoring reports an exception instead of a refutation.
            if not any(
                cell in survivors and cell not in red_cells for cell in selected
            ):
                survivor_choices = [
                    cell
                    for cell in survivors
                    if cell not in selected and cell not in red_cells
                ]
                if not survivor_choices:
                    continue
                selected.add(rng.choice(survivor_choices))

            remaining = [cell for cell in allowed if cell not in selected]
            need = payload_cells - len(selected)
            if need < 0 or len(remaining) < need:
                continue
            selected.update(rng.sample(remaining, need))
            if len(selected) != payload_cells:
                continue
            non_red_cells = [cell for cell in selected if cell not in red_cells]
            if len(non_red_cells) < palette_size:
                continue

            palette = rng.sample(list(_NON_MARKER_COLORS), palette_size)
            values = list(palette)
            values.extend(
                rng.choice(palette) for _ in range(len(non_red_cells) - palette_size)
            )
            rng.shuffle(values)

            grid = full_grid(h, w, 0)
            grid[source[0]][source[1]] = 1
            grid[target[0]][target[1]] = 2
            for cell in red_cells:
                grid[cell[0]][cell[1]] = 2
            for cell, value in zip(non_red_cells, values):
                grid[cell[0]][cell[1]] = value

            facts = semantic_observables(grid)
            if facts.get("errors"):
                continue
            if facts["clipping_mode"] != clipping:
                continue
            if facts["shift_quadrant"] != quadrant:
                continue
            if observe_overrides(grid) != {
                "grid_h": h,
                "grid_w": w,
                "payload_cells": payload_cells,
                "palette_size": palette_size,
                "extra_reds": extra_reds,
            }:
                continue
            official = facts["output"]
            if not official:
                continue
            if clipping != "none" and official == rival_crop_payload_without_translation(grid):
                continue
            if extra_reds:
                if official == rival_drop_all_red_payload(grid):
                    continue
                if official == rival_use_last_red_target(grid):
                    continue
                if official == rival_use_nearest_red_target(grid):
                    continue
            return grid

    raise ValueError(
        "could not construct lawful scene for "
        f"h={h}, w={w}, payload_cells={payload_cells}, palette_size={palette_size}, "
        f"extra_reds={extra_reds}, quadrant={quadrant}, clipping={clipping}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    has_override = any(overrides.get(name) is not None for name in AXES)
    if not has_override and sample_index % 4 == 0:
        return _canonical_anchor(ctx, seed, sample_index)

    h = ctx.draw_int_diff("grid_h", 9, 18)
    w = ctx.draw_int_diff("grid_w", 9, 18)
    payload_default = 6 + (sample_index % 7)
    palette_default = 2 + (sample_index % 3)
    # Every four-pair lesson window has three general draws and at most one
    # canonical anchor. Keeping every general draw multi-red means any
    # three-demo query rotation still contains a witness against nearest/last
    # target selection and against dropping later red payload cells.
    extra_reds_default = 1 + (sample_index % 2)
    payload_cells = _draw_fixed_or_override(
        ctx, "payload_cells", 6, 12, payload_default
    )
    palette_size = _draw_fixed_or_override(
        ctx, "palette_size", 2, 4, palette_default
    )
    extra_reds = _draw_fixed_or_override(
        ctx, "extra_reds", 0, 2, extra_reds_default
    )

    quadrant = _QUADRANTS[(seed + sample_index + sample_index // 4) % len(_QUADRANTS)]
    clipping = _CLIPPING_MODES[sample_index % len(_CLIPPING_MODES)]
    return _build_payload_grid(
        h=h,
        w=w,
        payload_cells=payload_cells,
        palette_size=palette_size,
        extra_reds=extra_reds,
        quadrant=quadrant,
        clipping=clipping,
        rng=ctx.draw_rng("layout"),
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return list(facts["errors"])
    sources, reds = _source_and_reds(grid)
    if len(sources) != 1:
        errors.append(f"expected exactly one color-1 source; got {len(sources)}")
    if not reds:
        errors.append("expected at least one color-2 target candidate")
    if facts["payload_cells"] < 1:
        errors.append("payload must contain at least one non-marker cell")
    if facts["survivor_count"] < 1:
        errors.append("translation clips every payload cell, leaving no crop")
    if not facts["output"]:
        errors.append("canonical rule produces an empty output")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    observed = observe_overrides(grid)
    for name in AXES:
        if name in requested and requested[name] is not None:
            if observed.get(name) != requested[name]:
                errors.append(
                    f"override {name}={requested[name]!r} realized as "
                    f"{observed.get(name)!r}"
                )
    return errors


def _symbolic_payload_pattern(grid) -> tuple | None:
    facts = semantic_observables(grid)
    if facts.get("errors") or facts["payload_cells"] < 1:
        return None
    source_row, source_col = facts["source"]
    color_ids: dict[int, int] = {}
    pattern = []
    for row, col, value in sorted(facts["payload"]):
        if value == 2:
            label: Any = "R"
        else:
            if value not in color_ids:
                color_ids[value] = len(color_ids)
            label = color_ids[value]
        pattern.append((row - source_row, col - source_col, label))
    return tuple(pattern)


def canonical_profile_signature(grid) -> tuple | None:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return None
    pattern = _symbolic_payload_pattern(grid)
    if pattern is None:
        return None
    return (
        facts["grid_h"],
        facts["grid_w"],
        facts["source"],
        facts["target"],
        pattern,
    )


def _template_signature(template) -> tuple:
    source_row, source_col = template["source"]
    label_ids = {"A": 0, "B": 1, "C": 2, "R": "R"}
    pattern = tuple(
        (row - source_row, col - source_col, label_ids[label])
        for row, col, label in sorted(template["payload"])
    )
    return (
        template["dims"][0],
        template["dims"][1],
        template["source"],
        template["target"],
        pattern,
    )


_CANONICAL_SIGNATURES = frozenset(
    _template_signature(template) for template in _CANONICAL_TEMPLATES
)
MIN_STRICT_FRAC = 0.20


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    signature = canonical_profile_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return ["linked source/target/payload morphology is outside the four official profiles"]
    return []


def _safe_facts(grid) -> dict[str, Any]:
    try:
        return semantic_observables(grid)
    except Exception as exc:
        return {"errors": [f"analysis failed: {type(exc).__name__}: {exc}"]}


def _rival_disagrees(grid, rival: Callable) -> bool:
    try:
        return rule_mirror(grid) != rival(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "clipping_rows": lambda grid: _safe_facts(grid).get("clipping_mode") == "rows",
    "clipping_cols": lambda grid: _safe_facts(grid).get("clipping_mode") == "cols",
    "clipping_both": lambda grid: _safe_facts(grid).get("clipping_mode") == "both",
    "copied_extra_red": lambda grid: (
        _safe_facts(grid).get("extra_reds", 0) > 0
        and _rival_disagrees(grid, rival_drop_all_red_payload)
    ),
    "first_red_not_last": lambda grid: (
        _safe_facts(grid).get("extra_reds", 0) > 0
        and _rival_disagrees(grid, rival_use_last_red_target)
    ),
    "first_red_not_nearest": lambda grid: (
        _safe_facts(grid).get("extra_reds", 0) > 0
        and _rival_disagrees(grid, rival_use_nearest_red_target)
    ),
}

SEMANTIC_RIVALS = {
    "crop_payload_without_translation": rival_crop_payload_without_translation,
    "drop_all_red_payload": rival_drop_all_red_payload,
    "use_last_red_target": rival_use_last_red_target,
    "use_nearest_red_target": rival_use_nearest_red_target,
}

WITNESS_RIVALS = {
    "clipping_rows": ["crop_payload_without_translation"],
    "clipping_cols": ["crop_payload_without_translation"],
    "clipping_both": ["crop_payload_without_translation"],
    "copied_extra_red": ["drop_all_red_payload"],
    "first_red_not_last": ["use_last_red_target"],
    "first_red_not_nearest": ["use_nearest_red_target"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    findings: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except Exception as exc:
            findings.append(f"pair {index} input is invalid: {type(exc).__name__}: {exc}")
            continue
        if expected != pair["output"]:
            findings.append(f"pair {index} output disagrees with the selected rule")
    if findings:
        return findings

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            findings.append(f"competitor {name} raised: {type(exc).__name__}: {exc}")
            continue
        if survives:
            rival_query = rival(query["input"])
            relation = "different" if rival_query != query["output"] else "same"
            findings.append(
                f"demos do not refute competitor {name}; its query answer is {relation}"
            )
    return findings
