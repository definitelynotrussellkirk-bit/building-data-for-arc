"""Generator for ARC task 72416068b0cf.

The first three cells encode ``(shape_code, transform_1, transform_2)``.
Exactly one body object has the requested normalized binary shape.  Crop that
object and apply the two D4 transform codes in order.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "72416068b0cf"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "7dc6818bbe6b"

SUMMARY = (
    "Read the three-cell header as (shape_code, step1, step2). Match the one "
    "body object whose normalized binary crop equals the requested shape "
    "class, crop it with its original color, then apply transform step1 and "
    "transform step2 in that order. Transform codes are 1 identity, 2 rotate "
    "clockwise, 3 rotate 180, 4 rotate counterclockwise, 5 flip left-right, "
    "6 flip up-down, and 7 transpose."
)

INVARIANTS = [
    "background is 0 and row 0 contains only the three header codes",
    "shape_code is 1..4 and each transform code is 1..7",
    "the body contains exactly one object matching the requested normalized shape",
    "the body contains two or three disconnected distractor objects",
    "ordinary draws include equal-size and larger competing shape classes",
    "object colors are distinct and the selected object's color is preserved",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 9..12", "valid": "9..12"},
    "grid_w": {"type": "int", "default": "scheduled 11..15", "valid": "11..15"},
    "n_distractors": {"type": "int", "default": "scheduled 2..3", "valid": "2..3"},
    "shape_code": {"type": "int", "default": "four-step lesson schedule", "valid": "1..4"},
    "step1": {"type": "int", "default": "four-step lesson schedule", "valid": "1..7"},
    "step2": {"type": "int", "default": "four-step lesson schedule", "valid": "1..7"},
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# These are the four exact binary templates encoded by shape_code.  Orientation
# is part of the class: the canonical Racket rule compares normalized crops,
# not D4-equivalence classes.
TARGETS: dict[int, tuple[tuple[int, int], ...]] = {
    1: ((0, 0), (1, 0), (2, 0), (2, 1)),
    2: ((0, 0), (0, 1), (0, 2), (1, 1)),
    3: ((0, 0), (0, 1), (1, 1), (1, 2)),
    4: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
}

# Every four consecutive examples contain every transform code at least once.
# The independent seed-derived offset prevents transform-pair identity from
# being permanently correlated with a particular shape code.
_TRANSFORM_PAIRS = ((1, 2), (3, 5), (4, 6), (7, 1))

_BOUNDS = {
    "grid_h": (9, 12),
    "grid_w": (11, 15),
    "n_distractors": (2, 3),
    "shape_code": (1, 4),
    "step1": (1, 7),
    "step2": (1, 7),
}


def _validate_identity(seed: int, sample_index: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, (lo, hi) in _BOUNDS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_exact_int(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _BOUNDS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _default_layout(ctx, sample_index: int, difficulty: str | None) -> tuple[int, int, int, bool]:
    """Return (height, width, distractors, canonical_profile_anchor)."""
    canonical_anchor = sample_index % 5 == 0
    if canonical_anchor:
        return 9, 11, 2, True

    if difficulty == "easy":
        h = 9 + ctx.draw_rng("height_band").randrange(2)
        w = 11 + ctx.draw_rng("width_band").randrange(2)
        n = 2
    elif difficulty == "medium":
        h = 10 + ctx.draw_rng("height_band").randrange(2)
        w = 12 + ctx.draw_rng("width_band").randrange(3)
        n = 2 + ctx.draw_rng("distractor_band").randrange(2)
    elif difficulty == "hard":
        h = 11 + ctx.draw_rng("height_band").randrange(2)
        w = 14 + ctx.draw_rng("width_band").randrange(2)
        n = 3
    else:
        h = 9 + ctx.draw_rng("height_band").randrange(4)
        w = 11 + ctx.draw_rng("width_band").randrange(5)
        n = 2 + ctx.draw_rng("distractor_band").randrange(2)
    return h, w, n, False


def _dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _can_place(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], top: int, left: int
) -> bool:
    """Objects may touch diagonally but never orthogonally in the body."""
    h, w = len(grid), len(grid[0])
    absolute = {(top + dr, left + dc) for dr, dc in cells}
    if any(r < 1 or r >= h or c < 0 or c >= w for r, c in absolute):
        return False
    if any(grid[r][c] != 0 for r, c in absolute):
        return False
    for r, c in absolute:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (r + dr, c + dc)
            if q in absolute:
                continue
            qr, qc = q
            if 1 <= qr < h and 0 <= qc < w and grid[qr][qc] != 0:
                return False
    return True


def _paint(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], top: int, left: int, color: int
) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def _erase(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], top: int, left: int
) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = 0


def _place_objects(
    grid: list[list[int]],
    specs: list[tuple[str, tuple[tuple[int, int], ...], int]],
    rng,
) -> None:
    """Backtrack over shuffled legal placements; the smallest grid is ample."""
    ordered = list(specs)
    rng.shuffle(ordered)

    def search(index: int) -> bool:
        if index == len(ordered):
            return True
        _, cells, color = ordered[index]
        sh, sw = _dims(cells)
        candidates = [
            (r, c)
            for r in range(1, len(grid) - sh + 1)
            for c in range(0, len(grid[0]) - sw + 1)
        ]
        rng.shuffle(candidates)
        for top, left in candidates:
            if not _can_place(grid, cells, top, left):
                continue
            _paint(grid, cells, top, left, color)
            if search(index + 1):
                return True
            _erase(grid, cells, top, left)
        return False

    if not search(0):
        raise ValueError("could not place the requested body objects")


def _canonical_palette_colors(
    header: tuple[int, int, int], rng
) -> list[int]:
    """Choose three object colors so the canonical 9x11 profile has palette 6."""
    header_colors = sorted(set(header))
    new_needed = 5 - len(header_colors)  # five non-background colors total
    outside = [c for c in range(2, 10) if c not in header_colors]
    rng.shuffle(outside)
    fresh = outside[:new_needed]
    overlap_needed = 3 - len(fresh)
    overlaps = list(header_colors)
    rng.shuffle(overlaps)
    colors = [fresh[0], *fresh[1:], *overlaps[:overlap_needed]]
    if len(colors) != 3 or len(set(colors)) != 3:
        raise ValueError("could not construct canonical-profile colors")
    return colors


def _ordinary_colors(
    header: tuple[int, int, int], n_objects: int, rng
) -> list[int]:
    outside = [c for c in range(2, 10) if c not in set(header)]
    inside = [c for c in range(2, 10) if c in set(header)]
    rng.shuffle(outside)
    rng.shuffle(inside)
    colors = (outside + inside)[:n_objects]
    if len(colors) != n_objects:
        raise ValueError("not enough distinct object colors")
    return colors


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            raise ValueError("each row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("rows must be non-empty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(type(v) is not int or not 0 <= v <= 9 for v in values):
            raise ValueError("grid cells must be integer ARC colors in 0..9")
        rows.append(values)
    return rows


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return nonzero 4-connected body components, independent of color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                p = queue.popleft()
                cells.append(p)
                pr, pc = p
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    q = (pr + dr, pc + dc)
                    qr, qc = q
                    if (
                        qr >= 1
                        and qr < h
                        and 0 <= qc < w
                        and grid[qr][qc] != 0
                        and q not in seen
                    ):
                        seen.add(q)
                        queue.append(q)
            colors = {grid[rr][cc] for rr, cc in cells}
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            r1 = max(rr for rr, _ in cells)
            c1 = max(cc for _, cc in cells)
            shape = tuple(sorted((rr - r0, cc - c0) for rr, cc in cells))
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": colors,
                    "color": next(iter(colors)) if len(colors) == 1 else None,
                    "bbox": (r0, c0, r1, c1),
                    "shape": shape,
                    "size": len(cells),
                }
            )
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    if not 9 <= h <= 12 or not 11 <= w <= 15:
        errors.append(f"grid dimensions {h}x{w} must be within 9..12 by 11..15")
    if w < 3:
        errors.append("grid is too narrow for the three-cell header")
        return {"errors": errors, "grid": values}

    shape_code, step1, step2 = values[0][0], values[0][1], values[0][2]
    if shape_code not in TARGETS:
        errors.append(f"shape_code must be 1..4, found {shape_code}")
    if step1 not in range(1, 8):
        errors.append(f"step1 must be 1..7, found {step1}")
    if step2 not in range(1, 8):
        errors.append(f"step2 must be 1..7, found {step2}")
    if any(values[0][c] != 0 for c in range(3, w)):
        errors.append("row 0 must be zero outside the three header cells")

    components = _components(values)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3 or 4 body objects, found {len(components)}")
    for i, comp in enumerate(components):
        if len(comp["colors"]) != 1:
            errors.append(f"body object {i} contains multiple colors")
        if not 3 <= comp["size"] <= 6:
            errors.append(f"body object {i} size {comp['size']} must be 3..6")
        r0, c0, r1, c1 = comp["bbox"]
        if r1 - r0 + 1 > 3 or c1 - c0 + 1 > 3:
            errors.append(f"body object {i} bbox exceeds 3x3")

    target_matches: list[dict[str, Any]] = []
    if shape_code in TARGETS:
        target_matches = [comp for comp in components if comp["shape"] == TARGETS[shape_code]]
        if len(target_matches) != 1:
            errors.append(
                f"expected exactly one object matching shape_code {shape_code}, "
                f"found {len(target_matches)}"
            )
    colors = [comp["color"] for comp in components if comp["color"] is not None]
    if len(colors) != len(set(colors)):
        errors.append("body object colors must be distinct")

    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "shape_code": shape_code,
        "step1": step1,
        "step2": step2,
        "components": components,
        "target": target_matches[0] if len(target_matches) == 1 else None,
        "n_distractors": max(0, len(components) - 1),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed headers, bodies, ambiguous selectors, and tiny impostors."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked authority grammar; all canonical train/test inputs satisfy it."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_distractors": analysis["n_distractors"],
        "shape_code": analysis["shape_code"],
        "step1": analysis["step1"],
        "step2": analysis["step2"],
    }


def _crop_component(grid: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = component["bbox"]
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    operations: dict[int, Callable[[list[list[int]]], list[list[int]]]] = {
        1: lambda value: [list(row) for row in value],
        2: _rotate_cw,
        3: _rotate_180,
        4: _rotate_ccw,
        5: _flip_lr,
        6: _flip_ud,
        7: _transpose,
    }
    return operations[code](grid)


def _valid_analysis(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def _solve(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    crop = _crop_component(analysis["grid"], analysis["target"])
    return _transform(_transform(crop, analysis["step1"]), analysis["step2"])


def _rival_largest_object(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    selected = min(
        analysis["components"],
        key=lambda comp: (-comp["size"], comp["bbox"][0], comp["bbox"][1]),
    )
    crop = _crop_component(analysis["grid"], selected)
    return _transform(_transform(crop, analysis["step1"]), analysis["step2"])


def _rival_first_object(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    selected = min(analysis["components"], key=lambda comp: comp["bbox"][:2])
    crop = _crop_component(analysis["grid"], selected)
    return _transform(_transform(crop, analysis["step1"]), analysis["step2"])


def _rival_fixed_shape_one(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    matches = [comp for comp in analysis["components"] if comp["shape"] == TARGETS[1]]
    selected = matches[0] if matches else min(analysis["components"], key=lambda comp: comp["bbox"][:2])
    crop = _crop_component(analysis["grid"], selected)
    return _transform(_transform(crop, analysis["step1"]), analysis["step2"])


def _rival_reverse_order(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    crop = _crop_component(analysis["grid"], analysis["target"])
    return _transform(_transform(crop, analysis["step2"]), analysis["step1"])


def _rival_ignore_step2(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    crop = _crop_component(analysis["grid"], analysis["target"])
    return _transform(crop, analysis["step1"])


def _rival_header_color(grid: Any) -> list[list[int]]:
    analysis = _valid_analysis(grid)
    crop = _crop_component(analysis["grid"], analysis["target"])
    recolored = [
        [analysis["shape_code"] if cell else 0 for cell in row]
        for row in crop
    ]
    return _transform(_transform(recolored, analysis["step1"]), analysis["step2"])


SEMANTIC_RIVALS = {
    "largest_object": _rival_largest_object,
    "first_object": _rival_first_object,
    "fixed_shape_one": _rival_fixed_shape_one,
    "reverse_transform_order": _rival_reverse_order,
}

# Reverse-order can be answer-equivalent on a particular query even when the
# global rule is ordered; keep it as a census rival, but do not make the lesson
# gate reject an otherwise determined query merely because both orders agree.
LESSON_COMPETITORS = {
    "largest_object": _rival_largest_object,
    "first_object": _rival_first_object,
    "fixed_shape_one": _rival_fixed_shape_one,
    "reverse_transform_order": _rival_reverse_order,
    "ignore_step2": _rival_ignore_step2,
    "header_color": _rival_header_color,
}

# These rivals are useful lesson-level alternatives, but each is already
# refuted by at least one labeled canonical pair.  CANONICAL_SHORTCUTS is
# reserved for wrong rules that fit every labeled canonical pair.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}


def _disagrees(rival: Callable[[Any], list[list[int]]]) -> Callable[[Any], bool]:
    def witness(grid: Any) -> bool:
        try:
            return rival(grid) != _solve(grid)
        except (TypeError, ValueError):
            return False

    return witness


# Every retained semantic witness is tied to a named rival disagreement.
# Shape-code coverage is enforced at the lesson level by lesson_identifiable;
# presence-only witnesses would be weak evidence under the strict after gate.
SEMANTIC_WITNESSES = {
    "target_not_largest": _disagrees(_rival_largest_object),
    "target_not_first": _disagrees(_rival_first_object),
    "shape_selector_refutes_fixed_one": _disagrees(_rival_fixed_shape_one),
    "ordered_composition_matters": _disagrees(_rival_reverse_order),
}

WITNESS_RIVALS = {
    "target_not_largest": ["largest_object"],
    "target_not_first": ["first_object"],
    "shape_selector_refutes_fixed_one": ["fixed_shape_one"],
    "ordered_composition_matters": ["reverse_transform_order"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require full selector/code coverage and reject named surviving rivals."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return reasons

    analyses: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        analysis = _analyze(demo.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} malformed: {analysis['errors'][0]}")
        else:
            analyses.append(analysis)
    query_analysis = _analyze(query.get("input"))
    if query_analysis["errors"]:
        reasons.append(f"query malformed: {query_analysis['errors'][0]}")
    if reasons:
        return reasons

    shape_codes = {analysis["shape_code"] for analysis in analyses}
    transform_codes = {
        code
        for analysis in analyses
        for code in (analysis["step1"], analysis["step2"])
    }
    if shape_codes != {1, 2, 3, 4}:
        reasons.append(f"demos cover shape codes {sorted(shape_codes)}, not all 1..4")
    if transform_codes != set(range(1, 8)):
        reasons.append(
            f"demos cover transform codes {sorted(transform_codes)}, not all 1..7"
        )

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_all = all(rival(demo["input"]) == demo["output"] for demo in demos)
            if fits_all and rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} fits every demo but changes the query answer")
        except (TypeError, ValueError) as exc:
            reasons.append(f"rival {name} could not be evaluated: {exc}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_identity(seed, sample_index)
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    default_h, default_w, default_n, canonical_anchor = _default_layout(
        ctx, int(sample_index), difficulty
    )
    h = _draw_exact_int(ctx, overrides, "grid_h", default_h)
    w = _draw_exact_int(ctx, overrides, "grid_w", default_w)
    n_distractors = _draw_exact_int(ctx, overrides, "n_distractors", default_n)

    shape_offset = stable_rng(seed, f"{TASK_ID}|shape_schedule", VERSION).randrange(4)
    pair_offset = stable_rng(seed, f"{TASK_ID}|transform_schedule", VERSION).randrange(4)
    default_shape = 1 + (int(sample_index) + shape_offset) % 4
    code_order = list(range(1, 8))
    stable_rng(seed, f"{TASK_ID}|transform_code_permutation", VERSION).shuffle(code_order)
    code_map = {base: code_order[base - 1] for base in range(1, 8)}
    base_step1, base_step2 = _TRANSFORM_PAIRS[
        (int(sample_index) + pair_offset) % 4
    ]
    default_step1, default_step2 = code_map[base_step1], code_map[base_step2]
    shape_code = _draw_exact_int(ctx, overrides, "shape_code", default_shape)
    step1 = _draw_exact_int(ctx, overrides, "step1", default_step1)
    step2 = _draw_exact_int(ctx, overrides, "step2", default_step2)

    grid = full_grid(h, w, 0)
    grid[0][0], grid[0][1], grid[0][2] = shape_code, step1, step2

    color_rng = ctx.draw_rng("object_colors")
    header = (shape_code, step1, step2)
    if canonical_anchor and n_distractors == 2 and not any(
        name in overrides for name in ("shape_code", "step1", "step2")
    ):
        colors = _canonical_palette_colors(header, color_rng)
    else:
        colors = _ordinary_colors(header, n_distractors + 1, color_rng)

    other_codes = [code for code in TARGETS if code != shape_code]
    if n_distractors == 2:
        if shape_code != 4:
            remaining = [code for code in other_codes if code != 4]
            chosen = [4, ctx.draw_rng("secondary_distractor").choice(remaining)]
        else:
            chosen = ctx.draw_rng("secondary_distractor").sample(other_codes, 2)
    else:
        chosen = other_codes
    ctx.draw_rng("distractor_order").shuffle(chosen)

    specs = [("target", TARGETS[shape_code], colors[0])]
    specs.extend(
        (f"distractor_{code}", TARGETS[code], color)
        for code, color in zip(chosen, colors[1:])
    )

    # Every four-example lesson contains both target-first and target-not-first
    # layouts, so a fixed scan-position selector cannot survive all demos.
    position_offset = stable_rng(seed, f"{TASK_ID}|position_schedule", VERSION).randrange(4)
    require_target_first = (int(sample_index) + position_offset) % 4 == 0
    for attempt in range(32):
        for r in range(1, h):
            grid[r] = [0] * w
        _place_objects(grid, specs, ctx.draw_rng(f"layout_{attempt}"))
        components = _components(grid)
        first = min(components, key=lambda comp: comp["bbox"][:2])
        target_is_first = first["color"] == colors[0]
        if target_is_first == require_target_first:
            break
    else:
        raise ValueError("could not realize the scheduled target position")

    errors = self_check(grid)
    if errors:
        raise AssertionError("generator produced invalid grid: " + "; ".join(errors))
    return grid
