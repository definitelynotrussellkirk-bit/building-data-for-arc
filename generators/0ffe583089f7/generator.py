"""Semantic generator for ARC task ``0ffe583089f7``.

The top-left cell is a transform key.  The only other non-zero cell in the
first row is a selector colour.  In the body, the largest connected component
with that selector colour is the source shape.  The source is transformed by
the key, centered inside the unique hollow colour-8 frame, and everything
except the frame and transformed source is erased.

Normal generated scenes deliberately include both a smaller selector-colour
decoy and a still-larger wrong-colour distractor.  Those two controls refute
the tempting shortcuts "first object of the selected colour" and "largest
object regardless of selector" while preserving the canonical rule.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "0ffe583089f7"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "7ebc8911fc48"

SUMMARY = (
    "Read the transform key at (0,0) and the sole non-zero selector colour "
    "elsewhere in row 0. Select the largest body component of that colour, "
    "transform its tight crop (1=clockwise, 2=left-right flip, 3=up-down "
    "flip, 4=180 degrees, 5/6=identity), then center it inside the unique "
    "hollow colour-8 frame on an otherwise blank output."
)

INVARIANTS = [
    "background is 0 and the input palette contains exactly six colours",
    "(0,0) is a transform key in 1..6 and row 0 has exactly one other non-zero selector marker",
    "the body contains exactly one hollow rectangular colour-8 frame with a blank interior",
    "the selector colour has one or two body components and has a unique largest component",
    "two distinct wrong-colour distractor components are present; generated scenes make one larger than the selected target",
    "the transformed target crop fits completely inside the frame interior",
]

# Five distinct behaviours exist: keys 5 and 6 share the same identity branch.
# Normal lessons cycle 1..5 so every consecutive five demonstrations expose the
# complete operation table and the next query repeats a demonstrated behaviour.
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (1, 2, 3, 4, 5)

GRID_PROFILES = ("11x14", "11x15", "12x15")
FRAME_PROFILES = ("7x7", "8x7", "8x6")
TARGET_ORDERS = ("target_first", "small_first")
MARKER_POSITIONS = ("right_edge", "interior")

AXES = {
    "transform_key": {
        "type": "int",
        "default": "cyclic 1..5 by sample_index; 6 is explicit-override only and shares identity with 5",
        "valid": "1..6",
    },
    "grid_profile": {
        "type": "str",
        "default": "deterministic canonical-shape cycle",
        "valid": "|".join(GRID_PROFILES),
    },
    "frame_profile": {
        "type": "str",
        "default": "deterministic canonical frame-size cycle",
        "valid": "|".join(FRAME_PROFILES),
    },
    "target_order": {
        "type": "str",
        "default": "alternates which selector-colour component is first in row-major order",
        "valid": "|".join(TARGET_ORDERS),
    },
    "marker_position": {
        "type": "str",
        "default": "varies between the canonical right edge and an interior top-row column",
        "valid": "|".join(MARKER_POSITIONS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Every source shape is asymmetric under clockwise rotation, horizontal flip,
# vertical flip, and 180-degree rotation. This makes transform keys observable.
_TARGET_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (3, 2)),
)
_SMALL_SELECTOR_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0), (1, 1)),
)
_BIG_DISTRACTOR_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
)
_SMALL_DISTRACTOR_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
)
_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _scheduled_key(sample_index: int) -> int:
    return 1 + (int(sample_index) % 5)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the five-behaviour transform schedule to the semantic gate."""
    del seed, difficulty
    return _scheduled_key(sample_index)


def _difficulty_offset(difficulty) -> int:
    if difficulty == "medium":
        return 1
    if difficulty == "hard":
        return 2
    return 0


def _scheduled_choice(
    values: tuple[str, ...], seed: int, sample_index: int, salt: int, difficulty=None
) -> str:
    # Difficulty deliberately changes only nuisance presentation controls, not
    # the task semantics.  This keeps all three bands semantically equivalent
    # while avoiding byte-identical cross-band instances.
    return values[
        (int(seed) + salt * int(sample_index) + salt + _difficulty_offset(difficulty))
        % len(values)
    ]


def _draw_choice_axis(ctx, overrides: dict[str, Any], name: str, scheduled: str,
                      values: tuple[str, ...]) -> str:
    if name in overrides:
        return str(ctx.draw_choice(name, list(values)))
    return str(ctx.draw_choice(name, [scheduled]))


def _draw_key_axis(ctx, overrides: dict[str, Any], scheduled: int) -> int:
    if "transform_key" in overrides:
        return ctx.draw_int("transform_key", 1, 6)
    return ctx.draw_int("transform_key", scheduled, scheduled)


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-colour 4-connected non-zero components in row-major order."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            box = _bbox(cells)
            out.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": box,
            })
    return out


def _frame_from_eights(grid: list[list[int]]) -> tuple[dict[str, int] | None, list[str]]:
    h, w = len(grid), len(grid[0])
    cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8}
    if not cells:
        return None, ["missing colour-8 frame"]
    r0, c0, r1, c1 = _bbox(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return None, ["colour-8 bounding box is too small to be a hollow frame"]
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    errors: list[str] = []
    if cells != expected:
        errors.append("colour-8 cells must be exactly one complete rectangular hollow frame border")
    interior = {
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    }
    if any(grid[r][c] != 0 for r, c in interior):
        errors.append("frame interior must be blank in the input")
    return {
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
    }, errors


def _crop_component(grid: list[list[int]], component: dict[str, Any]) -> list[list[int]]:
    r0, c0, r1, c1 = component["bbox"]
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in reversed(grid)]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _transform(grid: list[list[int]], key: int) -> list[list[int]]:
    if key == 1:
        return _rotate_cw(grid)
    if key == 2:
        return _flip_lr(grid)
    if key == 3:
        return _flip_ud(grid)
    if key == 4:
        return _rotate_180(grid)
    return [list(row) for row in grid]


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    h = len(grid)
    g = [list(row) for row in grid]
    for row in g:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                break
        if errors:
            break
    if h < 4 or w < 4:
        errors.append("grid is too small for controls, objects, and a frame")
        return {"errors": errors, "height": h, "width": w}

    key = g[0][0]
    if key not in range(1, 7):
        errors.append(f"(0,0) must be a transform key in 1..6, got {key!r}")
    row0_nonzero = [(c, g[0][c]) for c in range(1, w) if g[0][c] != 0]
    selector = row0_nonzero[0][1] if len(row0_nonzero) == 1 else None
    selector_col = row0_nonzero[0][0] if len(row0_nonzero) == 1 else None
    if len(row0_nonzero) != 1:
        errors.append(
            f"row 0 after the key must contain exactly one non-zero selector marker, found {len(row0_nonzero)}"
        )
    elif selector in (0, 8) or selector == key:
        errors.append("selector colour must be non-zero, non-frame, and distinct from the key colour")

    frame, frame_errors = _frame_from_eights(g)
    errors.extend(frame_errors)

    temp = [list(row) for row in g]
    temp[0] = [0] * w
    if frame is not None:
        for r in range(frame["r0"], frame["r1"] + 1):
            for c in range(frame["c0"], frame["c1"] + 1):
                if r in (frame["r0"], frame["r1"]) or c in (frame["c0"], frame["c1"]):
                    temp[r][c] = 0
    components = _components(temp)
    selector_components = (
        [component for component in components if component["color"] == selector]
        if selector is not None else []
    )
    distractors = (
        [component for component in components if component["color"] != selector]
        if selector is not None else list(components)
    )

    if selector is not None:
        if not (1 <= len(selector_components) <= 2):
            errors.append(
                f"expected one or two selector-colour body components, found {len(selector_components)}"
            )
        if selector_components:
            max_size = max(component["size"] for component in selector_components)
            largest = [component for component in selector_components if component["size"] == max_size]
            if len(largest) != 1:
                errors.append("selector-colour target must be uniquely largest")
                target = None
            else:
                target = largest[0]
        else:
            target = None
    else:
        target = None

    if len(distractors) != 2:
        errors.append(f"expected exactly two wrong-colour distractor components, found {len(distractors)}")
    distractor_colors = {component["color"] for component in distractors}
    if len(distractors) == 2 and len(distractor_colors) != 2:
        errors.append("the two distractor components must use distinct colours")
    if key in distractor_colors:
        errors.append("the key colour must not be reused by a body distractor")

    palette = sorted({value for row in g for value in row})
    if len(palette) != 6:
        errors.append(f"expected exactly six input colours including background, found {palette}")

    if target is not None and frame is not None and key in range(1, 7):
        crop = _crop_component(temp, target)
        crop_nonzero = {value for row in crop for value in row if value != 0}
        if crop_nonzero != {selector}:
            errors.append(
                "selected target bounding box must not contain cells from other colours "
                f"(found {sorted(crop_nonzero)})"
            )
        transformed = _transform(crop, key)
        ih = frame["height"] - 2
        iw = frame["width"] - 2
        if len(transformed) > ih or len(transformed[0]) > iw:
            errors.append(
                f"transformed target {len(transformed)}x{len(transformed[0])} does not fit frame interior {ih}x{iw}"
            )

    target_order = None
    if len(selector_components) == 2 and target is not None:
        ordered = sorted(selector_components, key=lambda component: component["bbox"])
        target_order = "target_first" if ordered[0] is target else "small_first"

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "key": key,
        "selector": selector,
        "selector_col": selector_col,
        "frame": frame,
        "components": components,
        "selector_components": selector_components,
        "distractors": distractors,
        "target": target,
        "target_order": target_order,
        "palette": palette,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed/shortcut-hiding structures."""
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


def observe_overrides(grid) -> dict[str, int | str | None]:
    """Recover every declared exact generator axis from a generated grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    frame = analysis["frame"]
    selector_col = analysis["selector_col"]
    return {
        "transform_key": analysis["key"],
        "grid_profile": f"{analysis['height']}x{analysis['width']}",
        "frame_profile": f"{frame['height']}x{frame['width']}",
        "target_order": analysis["target_order"],
        "marker_position": (
            "right_edge" if selector_col == analysis["width"] - 1 else "interior"
        ),
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical manifold: controls, object grammar, frame, and scale."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if f"{analysis['height']}x{analysis['width']}" not in GRID_PROFILES:
        errors.append("grid shape is outside the canonical 11x14/11x15/12x15 profiles")
    frame = analysis["frame"]
    if f"{frame['height']}x{frame['width']}" not in FRAME_PROFILES:
        errors.append("frame size is outside the canonical 7x7/8x7/8x6 profiles")
    return errors


def _empty_frame_output(analysis: dict[str, Any]) -> list[list[int]]:
    out = full_grid(analysis["height"], analysis["width"], 0)
    frame = analysis["frame"]
    draw_frame(out, frame["r0"], frame["c0"], frame["r1"], frame["c1"], 8)
    return out


def _render_choice(grid: list[list[int]], component: dict[str, Any] | None,
                   key: int) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"] or component is None:
        return [list(row) for row in grid]
    temp = [list(row) for row in grid]
    temp[0] = [0] * analysis["width"]
    frame = analysis["frame"]
    for r in range(frame["r0"], frame["r1"] + 1):
        for c in range(frame["c0"], frame["c1"] + 1):
            if r in (frame["r0"], frame["r1"]) or c in (frame["c0"], frame["c1"]):
                temp[r][c] = 0
    crop = _crop_component(temp, component)
    transformed = _transform(crop, key)
    out = _empty_frame_output(analysis)
    ih = frame["height"] - 2
    iw = frame["width"] - 2
    top = frame["r0"] + 1 + (ih - len(transformed)) // 2
    left = frame["c0"] + 1 + (iw - len(transformed[0])) // 2
    for r, row in enumerate(transformed):
        for c, value in enumerate(row):
            if value != 0:
                out[top + r][left + c] = value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure audit mirror of the selected Racket rule; never used as output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_choice(grid, analysis["target"], analysis["key"])


def _rival_ignore_transform(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_choice(grid, analysis["target"], 5)


def _rival_always_rotate_cw(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_choice(grid, analysis["target"], 1)


def _rival_global_largest(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    largest = max(analysis["components"], key=lambda component: (component["size"], -component["bbox"][0], -component["bbox"][1]))
    return _render_choice(grid, largest, analysis["key"])


def _rival_first_selector(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["selector_components"]:
        return [list(row) for row in grid]
    first = min(analysis["selector_components"], key=lambda component: component["bbox"])
    return _render_choice(grid, first, analysis["key"])


def _rival_fixed_right_selector(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    assumed = grid[0][-1]
    candidates = [component for component in analysis["components"] if component["color"] == assumed]
    if not candidates:
        return _empty_frame_output(analysis)
    chosen = max(candidates, key=lambda component: component["size"])
    return _render_choice(grid, chosen, analysis["key"])


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "ignore_transform_key": _rival_ignore_transform,
    "always_rotate_clockwise": _rival_always_rotate_cw,
    "largest_object_ignoring_selector": _rival_global_largest,
    "first_selector_object": _rival_first_selector,
    "selector_is_last_column": _rival_fixed_right_selector,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _key_witness(value: int):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and analysis["key"] == value
    return witness


def _selector_beats_global_largest(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["target"] is None or not analysis["distractors"]:
        return False
    return max(component["size"] for component in analysis["distractors"]) > analysis["target"]["size"]


def _small_selector_before_target(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["target_order"] == "small_first"


def _interior_selector_marker(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["selector_col"] not in (None, analysis["width"] - 1)
    )


SEMANTIC_WITNESSES = {
    "key_1_rotate_clockwise": _key_witness(1),
    "key_2_flip_left_right": _key_witness(2),
    "key_3_flip_up_down": _key_witness(3),
    "key_4_rotate_180": _key_witness(4),
    "key_5_identity_branch": _key_witness(5),
    "selector_beats_larger_wrong_color": _selector_beats_global_largest,
    "largest_selector_beats_first_selector": _small_selector_before_target,
    "selector_marker_not_fixed_to_last_column": _interior_selector_marker,
}
WITNESS_RIVALS = {
    "key_1_rotate_clockwise": ["ignore_transform_key"],
    "key_2_flip_left_right": ["ignore_transform_key"],
    "key_3_flip_up_down": ["ignore_transform_key"],
    "key_4_rotate_180": ["ignore_transform_key"],
    "key_5_identity_branch": ["always_rotate_clockwise"],
    "selector_beats_larger_wrong_color": ["largest_object_ignoring_selector"],
    "largest_selector_beats_first_selector": ["first_selector_object"],
    "selector_marker_not_fixed_to_last_column": ["selector_is_last_column"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require each five-demo lesson to kill the named shortcut family."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    keys: set[int] = set()
    orders: set[str | None] = set()
    markers: set[str | None] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the selector/transform/frame rule")
            continue
        analysis = _analysis(pair["input"])
        keys.add(analysis["key"])
        orders.add(analysis["target_order"])
        markers.add(observe_overrides(pair["input"]).get("marker_position"))
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the selector/transform/frame rule")
    query_analysis = _analysis(query["input"])
    if keys != {1, 2, 3, 4, 5}:
        reasons.append(f"demonstrations must cover keys 1..5 exactly, found {sorted(keys)}")
    if query_analysis.get("key") not in keys:
        reasons.append("query transform behaviour was not demonstrated")
    if not {"target_first", "small_first"}.issubset(orders):
        reasons.append("demonstrations must vary selector-component reading order")
    if not {"right_edge", "interior"}.issubset(markers):
        reasons.append("demonstrations must vary selector-marker position")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons


def _fits(grid: list[list[int]], shape: tuple[tuple[int, int], ...],
          top: int, left: int, *, r_lo: int, r_hi: int, c_lo: int, c_hi: int) -> bool:
    for dr, dc in shape:
        r, c = top + dr, left + dc
        if not (r_lo <= r <= r_hi and c_lo <= c <= c_hi):
            return False
        if grid[r][c] != 0:
            return False
        # Keep a one-cell moat around objects so same-colour components never
        # merge accidentally and object roles remain visually crisp.
        for rr in range(max(r_lo, r - 1), min(r_hi, r + 1) + 1):
            for cc in range(max(c_lo, c - 1), min(c_hi, c + 1) + 1):
                if grid[rr][cc] != 0:
                    return False
    return True


def _place_shape(grid: list[list[int]], shape: tuple[tuple[int, int], ...], color: int,
                 rng, *, r_lo: int, r_hi: int, c_lo: int, c_hi: int,
                 row_band: tuple[int, int] | None = None) -> tuple[int, int] | None:
    sh, sw = _shape_dims(shape)
    top_lo = r_lo
    top_hi = r_hi - sh + 1
    if row_band is not None:
        top_lo = max(top_lo, row_band[0])
        top_hi = min(top_hi, row_band[1])
    left_hi = c_hi - sw + 1
    if top_lo > top_hi or c_lo > left_hi:
        return None
    candidates = [
        (r, c)
        for r in range(top_lo, top_hi + 1)
        for c in range(c_lo, left_hi + 1)
    ]
    rng.shuffle(candidates)
    for top, left in candidates:
        if not _fits(
            grid, shape, top, left,
            r_lo=r_lo, r_hi=r_hi, c_lo=c_lo, c_hi=c_hi,
        ):
            continue
        for dr, dc in shape:
            grid[top + dr][left + dc] = color
        return top, left
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    key = _draw_key_axis(ctx, overrides, _scheduled_key(sample_index))
    grid_profile = _draw_choice_axis(
        ctx, overrides, "grid_profile",
        _scheduled_choice(GRID_PROFILES, seed, sample_index, 1, difficulty),
        GRID_PROFILES,
    )
    frame_profile = _draw_choice_axis(
        ctx, overrides, "frame_profile",
        _scheduled_choice(FRAME_PROFILES, seed, sample_index, 2, difficulty),
        FRAME_PROFILES,
    )
    target_order = _draw_choice_axis(
        ctx, overrides, "target_order",
        TARGET_ORDERS[(int(seed) + int(sample_index) + _difficulty_offset(difficulty)) % 2],
        TARGET_ORDERS,
    )
    marker_position = _draw_choice_axis(
        ctx, overrides, "marker_position",
        MARKER_POSITIONS[((int(seed) // 2) + int(sample_index) + _difficulty_offset(difficulty)) % 2],
        MARKER_POSITIONS,
    )

    h, w = (int(part) for part in grid_profile.split("x"))
    fh, fw = (int(part) for part in frame_profile.split("x"))
    rng = ctx.draw_rng("layout")

    # Canonical dimensions are tight. Keep the frame on the right, as in the
    # official tasks, but vary its vertical offset and all object locations.
    if fh > h - 2 or fw > w - 3:
        raise ValueError(f"frame profile {frame_profile} does not fit grid profile {grid_profile}")

    for attempt in range(240):
        g = full_grid(h, w, 0)
        g[0][0] = key

        selector_pool = [c for c in (1, 2, 3, 4, 5, 6, 7, 9) if c != key]
        selector = rng.choice(selector_pool)
        distractor_pool = [c for c in (1, 2, 3, 4, 5, 6, 7, 9) if c not in {key, selector}]
        d1, d2 = rng.sample(distractor_pool, 2)

        if marker_position == "right_edge":
            selector_col = w - 1
        else:
            selector_col = rng.randint(2, w - 3)
        g[0][selector_col] = selector

        fr_lo = 2
        fr_hi = h - fh - 1
        if fr_lo > fr_hi:
            continue
        fr = rng.randint(fr_lo, fr_hi)
        fc = w - fw
        draw_frame(g, fr, fc, fr + fh - 1, fc + fw - 1, 8)

        # Objects live to the left of the frame with a blank separating column.
        r_lo, r_hi = 1, h - 1
        c_lo, c_hi = 0, fc - 2
        if c_hi - c_lo + 1 < 4:
            continue

        target_shape = rng.choice(_TARGET_SHAPES)
        small_selector_shape = rng.choice(_SMALL_SELECTOR_SHAPES)
        big_distractor_shape = rng.choice(_BIG_DISTRACTOR_SHAPES)
        small_distractor_shape = rng.choice(_SMALL_DISTRACTOR_SHAPES)

        # To make the target-order axis deterministic, bias only the first two
        # selector components into opposite vertical halves. Distractors remain
        # free to appear anywhere in the left region.
        mid = (r_lo + r_hi) // 2
        if target_order == "target_first":
            target_band = (r_lo, max(r_lo, mid - 1))
            small_band = (min(r_hi, mid + 1), r_hi)
        else:
            small_band = (r_lo, max(r_lo, mid - 1))
            target_band = (min(r_hi, mid + 1), r_hi)

        first = _place_shape(
            g, target_shape, selector, rng,
            r_lo=r_lo, r_hi=r_hi, c_lo=c_lo, c_hi=c_hi,
            row_band=target_band,
        )
        second = _place_shape(
            g, small_selector_shape, selector, rng,
            r_lo=r_lo, r_hi=r_hi, c_lo=c_lo, c_hi=c_hi,
            row_band=small_band,
        )
        if first is None or second is None:
            continue
        if _place_shape(
            g, big_distractor_shape, d1, rng,
            r_lo=r_lo, r_hi=r_hi, c_lo=c_lo, c_hi=c_hi,
        ) is None:
            continue
        if _place_shape(
            g, small_distractor_shape, d2, rng,
            r_lo=r_lo, r_hi=r_hi, c_lo=c_lo, c_hi=c_hi,
        ) is None:
            continue

        errors = strict_canonical_like(g)
        if errors:
            continue
        observed = observe_overrides(g)
        requested = {
            "transform_key": key,
            "grid_profile": grid_profile,
            "frame_profile": frame_profile,
            "target_order": target_order,
            "marker_position": marker_position,
        }
        if observed != requested:
            continue
        if not _selector_beats_global_largest(g):
            continue
        # The source crop must reveal every non-identity operation, not hide a
        # key behind a symmetric shape.
        analysis = _analysis(g)
        crop = _crop_component(g, analysis["target"])
        if key in (1, 2, 3, 4) and _transform(crop, key) == crop:
            continue
        return g

    raise ValueError(
        "could not realize selector/key/frame lesson "
        f"after {attempt + 1} attempts: key={key} grid={grid_profile} "
        f"frame={frame_profile} order={target_order} marker={marker_position}"
    )
