"""Semantic generator for ARC task ``5666b68dd4b9`` (Keyed Frame Insert).

The top-left cell selects a body colour.  The top-right cell is a transform
code: 1 rotates the selected tight crop clockwise, 2 rotates it 180 degrees,
3 flips it left-right, and every other code is identity (the canonical task
uses 4).  The transformed crop is centered in the *interior* of the unique
hollow colour-8 frame on an otherwise blank output.  Centering follows the
Racket authority exactly, including transparent paste that may overwrite a
frame edge when a crop is wider than the interior.

Generated four-example lessons hold selector and source shape fixed while
cycling codes 1..4.  They also contain a larger wrong-colour object and, in
alternating examples, wrong-colour cells inside the frame.  Those controls
make selector/code memorization, largest-object selection, identity-only
transforms, and preservation of frame contents directly falsifiable.
"""
from __future__ import annotations

import hashlib
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "5666b68dd4b9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "5a2705a2ea24"

SUMMARY = (
    "(0,0) selects a body colour and (0,w-1) selects cw/180/flip-LR/identity; "
    "transform the selected tight crop and transparently center it in the "
    "hollow colour-8 frame after clearing every other cell."
)

INVARIANTS = [
    "background is 0 and the input palette contains exactly six colours",
    "(0,0) is the selector colour and (0,w-1) is a transform code in 1..4",
    "the body contains one connected selected motif outside one complete rectangular colour-8 frame",
    "exactly two other body colours are distractors; one may occur inside the frame interior",
    "codes 1/2/3 mean clockwise/180/left-right flip and code 4 follows the rule's identity fallback",
    "the transformed crop is centered with floor division and transparent whole-grid paste, so a tight frame may be overwritten",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (1, 2, 3, 4)

GRID_PROFILES = ("10x11", "10x12", "11x12", "11x13")
FRAME_PROFILES = ("6x5", "7x4")
DISTRACTOR_LAYOUTS = ("outside_only", "inside_frame")

AXES = {
    "transform_code": {
        "type": "int",
        "default": "cyclic 1..4 by sample_index",
        "valid": "1..4",
    },
    "grid_profile": {
        "type": "str",
        "default": "deterministic cycle over exact canonical grid dimensions",
        "valid": "|".join(GRID_PROFILES),
    },
    "frame_profile": {
        "type": "str",
        "default": "deterministic cycle over the two canonical frame dimensions",
        "valid": "|".join(FRAME_PROFILES),
    },
    "distractor_layout": {
        "type": "str",
        "default": "alternates outside-only and frame-interior noise",
        "valid": "|".join(DISTRACTOR_LAYOUTS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# All source shapes have a 3x2 or 3x3 canonical-sized bounding box and are
# asymmetric under each non-identity transform.  Keeping the chosen shape
# stable across a four-example lesson isolates transform-code evidence.
_SOURCE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
)

# Eight cells, larger than every source motif, to refute global-largest-object
# selection while remaining a compact canonical-style distractor.
_BIG_DISTRACTOR: tuple[tuple[int, int], ...] = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)

_CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))
_CANONICAL_PAIR_TO_CODE = {(6, 1): 1, (7, 2): 2, (9, 3): 3, (6, 4): 4}
_SELECTOR_TO_CODE = {6: 1, 7: 2, 9: 3}


def _scheduled_code(sample_index: int) -> int:
    return 1 + (int(sample_index) % 4)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the complete four-transform lesson schedule to the gate."""
    del seed, difficulty
    return _scheduled_code(sample_index)


def _difficulty_offset(difficulty) -> int:
    if difficulty == "medium":
        return 1
    if difficulty == "hard":
        return 2
    if difficulty is None:
        return 3
    return 0


def _scheduled_choice(
    values: tuple[str, ...], seed: int, sample_index: int, salt: int, difficulty=None
) -> str:
    return values[
        (int(seed) + salt * int(sample_index) + salt + _difficulty_offset(difficulty))
        % len(values)
    ]


def _draw_choice_axis(ctx, overrides: dict[str, Any], name: str, scheduled: str,
                      values: tuple[str, ...]) -> str:
    if name in overrides:
        return str(ctx.draw_choice(name, list(values)))
    return str(ctx.draw_choice(name, [scheduled]))


def _draw_code_axis(ctx, overrides: dict[str, Any], scheduled: int) -> int:
    if "transform_code" in overrides:
        return int(ctx.draw_int("transform_code", 1, 4))
    return int(ctx.draw_int("transform_code", scheduled, scheduled))


def _stable_index(seed: int, difficulty: Any, salt: str, modulus: int) -> int:
    payload = f"{VERSION}|{int(seed)}|{difficulty!r}|{salt}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return value % modulus


def _shape_dims(shape: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _paint_shape(grid: list[list[int]], shape: tuple[tuple[int, int], ...],
                 top: int, left: int, color: int) -> None:
    for dr, dc in shape:
        grid[top + dr][left + dc] = color


def _bbox(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> tuple[int, int, int, int]:
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
            out.append({
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": _bbox(cells),
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
        errors.append("colour-8 cells must be exactly one complete rectangular frame border")
    return {
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
    }, errors


def _crop_box(grid: list[list[int]], box: tuple[int, int, int, int]) -> list[list[int]]:
    r0, c0, r1, c1 = box
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def _transform(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return _rotate_cw(grid)
    if code == 2:
        return _rotate_180(grid)
    if code == 3:
        return _flip_lr(grid)
    return [list(row) for row in grid]


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a non-empty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    g = [list(row) for row in grid]
    height = len(g)
    for row in g:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                break
        if errors:
            break
    if height < 5 or width < 5:
        errors.append("grid is too small for controls, source, and frame")
        return {"errors": errors, "height": height, "width": width}

    selector = g[0][0]
    code = g[0][width - 1]
    if selector in (0, 8):
        errors.append(f"(0,0) selector must be non-zero and not colour 8, got {selector!r}")
    if code not in (1, 2, 3, 4):
        errors.append(f"(0,w-1) transform code must be in 1..4, got {code!r}")
    if selector == code:
        errors.append("selector and transform-code colours must be distinct")
    stray_controls = [c for c in range(1, width - 1) if g[0][c] != 0]
    if stray_controls:
        errors.append(f"top row must be blank between selector and code; non-zero columns {stray_controls}")

    frame, frame_errors = _frame_from_eights(g)
    errors.extend(frame_errors)

    body = [list(row) for row in g]
    body[0] = [0] * width
    if frame is not None:
        for r in range(frame["r0"], frame["r1"] + 1):
            for c in range(frame["c0"], frame["c1"] + 1):
                if r in (frame["r0"], frame["r1"]) or c in (frame["c0"], frame["c1"]):
                    body[r][c] = 0

    components = _components(body)
    selected_components = [component for component in components if component["color"] == selector]
    source = selected_components[0] if len(selected_components) == 1 else None
    if len(selected_components) != 1:
        errors.append(f"expected exactly one connected selected-colour body motif, found {len(selected_components)}")

    source_crop = None
    source_dims = None
    if source is not None:
        source_crop = _crop_box(body, source["bbox"])
        source_dims = (len(source_crop), len(source_crop[0]))
        crop_nonzero = {value for row in source_crop for value in row if value != 0}
        if crop_nonzero != {selector}:
            errors.append(
                "selected tight crop must contain only selector colour and background; "
                f"found {sorted(crop_nonzero)}"
            )
        if frame is not None:
            sr0, sc0, sr1, sc1 = source["bbox"]
            if not (sr1 < frame["r0"] or sr0 > frame["r1"] or sc1 < frame["c0"] or sc0 > frame["c1"]):
                errors.append("selected motif must lie outside the target frame")
        if code in (1, 2, 3) and _transform(source_crop, code) == source_crop:
            errors.append("selected motif is symmetric under its requested non-identity transform")

    distractor_components = [component for component in components if component["color"] != selector]
    distractor_colors = {component["color"] for component in distractor_components}
    if code in distractor_colors:
        errors.append("transform-code colour must not be reused by a body distractor")
    if len(distractor_colors) != 2:
        errors.append(
            f"expected exactly two wrong-colour distractor colours, found {sorted(distractor_colors)}"
        )

    palette = sorted({value for row in g for value in row})
    if len(palette) != 6:
        errors.append(f"expected exactly six input colours including background, found {palette}")

    interior_noise: list[tuple[int, int, int]] = []
    if frame is not None:
        for r in range(frame["r0"] + 1, frame["r1"]):
            for c in range(frame["c0"] + 1, frame["c1"]):
                value = g[r][c]
                if value != 0:
                    interior_noise.append((r, c, value))
                    if value in (8, selector, code):
                        errors.append(
                            "frame-interior noise must use a distractor colour, not frame/selector/code"
                        )
                        break
            if errors and errors[-1].startswith("frame-interior noise"):
                break

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "selector": selector,
        "code": code,
        "frame": frame,
        "body": body,
        "components": components,
        "selected_components": selected_components,
        "source": source,
        "source_crop": source_crop,
        "source_dims": source_dims,
        "distractor_components": distractor_components,
        "distractor_colors": distractor_colors,
        "interior_noise": interior_noise,
        "palette": palette,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept every canonical input and reject malformed shortcut-hiding rows."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def observe_overrides(grid) -> dict[str, int | str | None]:
    """Recover every exact declared axis from a valid generated/canonical grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    frame = analysis["frame"]
    return {
        "transform_code": analysis["code"],
        "grid_profile": f"{analysis['height']}x{analysis['width']}",
        "frame_profile": f"{frame['height']}x{frame['width']}",
        "distractor_layout": "inside_frame" if analysis["interior_noise"] else "outside_only",
    }


def strict_canonical_like(grid) -> list[str]:
    """Require the exact public dimension, frame, palette, and source envelope."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    grid_profile = f"{analysis['height']}x{analysis['width']}"
    frame = analysis["frame"]
    frame_profile = f"{frame['height']}x{frame['width']}"
    if grid_profile not in GRID_PROFILES:
        errors.append(f"grid profile {grid_profile} is outside the canonical dimension set")
    if frame_profile not in FRAME_PROFILES:
        errors.append(f"frame profile {frame_profile} is outside the canonical frame set")
    source = analysis["source"]
    if not 4 <= source["size"] <= 7:
        errors.append(f"selected motif size {source['size']} is outside canonical range 4..7")
    if analysis["source_dims"] not in {(3, 2), (3, 3)}:
        errors.append(f"selected motif bbox {analysis['source_dims']} is outside canonical 3x2/3x3 range")
    return errors


def _empty_frame_output(analysis: dict[str, Any]) -> list[list[int]]:
    out = full_grid(analysis["height"], analysis["width"], 0)
    frame = analysis["frame"]
    draw_frame(out, frame["r0"], frame["c0"], frame["r1"], frame["c1"], 8)
    return out


def _render_crop(grid: list[list[int]], crop: list[list[int]], code: int) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    transformed = _transform(crop, code)
    out = _empty_frame_output(analysis)
    frame = analysis["frame"]
    interior_h = frame["height"] - 2
    interior_w = frame["width"] - 2
    top = frame["r0"] + 1 + (interior_h - len(transformed)) // 2
    left = frame["c0"] + 1 + (interior_w - len(transformed[0])) // 2
    for r, row in enumerate(transformed):
        for c, value in enumerate(row):
            rr, cc = top + r, left + c
            if value != 0 and 0 <= rr < analysis["height"] and 0 <= cc < analysis["width"]:
                out[rr][cc] = value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure audit mirror of the selected Racket rule; never output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_crop(grid, analysis["source_crop"], analysis["code"])


def _rival_ignore_transform_code(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_crop(grid, analysis["source_crop"], 4)


def _rival_always_rotate_clockwise(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    return _render_crop(grid, analysis["source_crop"], 1)


def _rival_selector_color_lookup(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    guessed = _SELECTOR_TO_CODE.get(analysis["selector"], 4)
    return _render_crop(grid, analysis["source_crop"], guessed)


def _rival_canonical_pair_lookup(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    guessed = _CANONICAL_PAIR_TO_CODE.get((analysis["selector"], analysis["code"]), 4)
    return _render_crop(grid, analysis["source_crop"], guessed)


def _rival_largest_body_object(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        return [list(row) for row in grid]
    largest = max(
        analysis["components"],
        key=lambda component: (component["size"], -component["bbox"][0], -component["bbox"][1]),
    )
    crop = _crop_box(analysis["body"], largest["bbox"])
    return _render_crop(grid, crop, analysis["code"])


def _rival_preserve_frame_interior(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    out = rule_mirror(grid)
    for r, c, value in analysis["interior_noise"]:
        out[r][c] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "ignore_transform_code": _rival_ignore_transform_code,
    "always_rotate_clockwise": _rival_always_rotate_clockwise,
    "selector_color_lookup": _rival_selector_color_lookup,
    "memorize_canonical_selector_code_pairs": _rival_canonical_pair_lookup,
    "largest_body_object": _rival_largest_body_object,
    "preserve_frame_interior": _rival_preserve_frame_interior,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "memorize_canonical_selector_code_pairs": _rival_canonical_pair_lookup,
}


def _code_witness(value: int):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and analysis["code"] == value
    return witness


def _selector_code_decorrelated(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and _SELECTOR_TO_CODE.get(analysis["selector"], 4) != analysis["code"]
    )


def _unseen_selector_code_pair(grid) -> bool:
    analysis = _analysis(grid)
    return (
        not analysis["errors"]
        and analysis["code"] in (1, 2, 3)
        and (analysis["selector"], analysis["code"]) not in _CANONICAL_PAIR_TO_CODE
    )


def _larger_wrong_colour(grid) -> bool:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["source"] is None:
        return False
    return any(
        component["size"] > analysis["source"]["size"]
        for component in analysis["distractor_components"]
    )


def _has_frame_interior_noise(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and bool(analysis["interior_noise"])


SEMANTIC_WITNESSES = {
    "code_1_rotate_clockwise": _code_witness(1),
    "code_2_rotate_180": _code_witness(2),
    "code_3_flip_left_right": _code_witness(3),
    "code_4_identity_fallback": _code_witness(4),
    "selector_code_decorrelation": _selector_code_decorrelated,
    "unseen_selector_code_pair": _unseen_selector_code_pair,
    "selector_beats_larger_wrong_colour": _larger_wrong_colour,
    "frame_interior_noise_is_cleared": _has_frame_interior_noise,
}
WITNESS_RIVALS = {
    "code_1_rotate_clockwise": ["ignore_transform_code"],
    "code_2_rotate_180": ["ignore_transform_code"],
    "code_3_flip_left_right": ["ignore_transform_code"],
    "code_4_identity_fallback": ["always_rotate_clockwise"],
    "selector_code_decorrelation": ["selector_color_lookup"],
    "unseen_selector_code_pair": ["memorize_canonical_selector_code_pairs"],
    "selector_beats_larger_wrong_colour": ["largest_body_object"],
    "frame_interior_noise_is_cleared": ["preserve_frame_interior"],
}


def _normalized_source_shape(analysis: dict[str, Any]) -> tuple[tuple[int, int], ...]:
    crop = analysis["source_crop"]
    return tuple(
        (r, c)
        for r, row in enumerate(crop)
        for c, value in enumerate(row)
        if value == analysis["selector"]
    )


def lesson_identifiable(demos, query) -> list[str]:
    """Require a four-demo lesson to isolate the code and kill named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    codes: set[int] = set()
    selectors: set[int] = set()
    source_shapes: set[tuple[tuple[int, int], ...]] = set()
    layouts: set[str] = set()
    checked_demos = list(demos[:EXAMPLES_NEEDED])
    for index, pair in enumerate(checked_demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the keyed-frame rule")
            continue
        analysis = _analysis(pair["input"])
        codes.add(analysis["code"])
        selectors.add(analysis["selector"])
        source_shapes.add(_normalized_source_shape(analysis))
        layouts.add(observe_overrides(pair["input"])["distractor_layout"])

    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the keyed-frame rule")
    query_analysis = _analysis(query["input"])
    if codes != {1, 2, 3, 4}:
        reasons.append(f"demonstrations must cover transform codes 1..4 exactly, found {sorted(codes)}")
    if len(selectors) != 1:
        reasons.append("demonstrations must hold selector colour fixed while varying the code")
    if len(source_shapes) != 1:
        reasons.append("demonstrations must hold source shape fixed while varying the code")
    if layouts != {"outside_only", "inside_frame"}:
        reasons.append(f"demonstrations must cover both frame-noise layouts, found {sorted(layouts)}")
    if query_analysis.get("code") not in codes:
        reasons.append("query transform behaviour was not demonstrated")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in checked_demos):
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons


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
    code = _draw_code_axis(ctx, overrides, _scheduled_code(sample_index))
    grid_profile = _draw_choice_axis(
        ctx,
        overrides,
        "grid_profile",
        _scheduled_choice(GRID_PROFILES, seed, sample_index, 1, difficulty),
        GRID_PROFILES,
    )
    frame_profile = _draw_choice_axis(
        ctx,
        overrides,
        "frame_profile",
        _scheduled_choice(FRAME_PROFILES, seed, sample_index, 2, difficulty),
        FRAME_PROFILES,
    )
    distractor_layout = _draw_choice_axis(
        ctx,
        overrides,
        "distractor_layout",
        DISTRACTOR_LAYOUTS[(int(seed) + int(sample_index) + _difficulty_offset(difficulty)) % 2],
        DISTRACTOR_LAYOUTS,
    )

    height, width = (int(part) for part in grid_profile.split("x"))
    frame_h, frame_w = (int(part) for part in frame_profile.split("x"))
    if frame_h > height - 1 or frame_w > width - 2:
        raise ValueError(f"frame profile {frame_profile} does not fit grid profile {grid_profile}")

    source_shape = _SOURCE_SHAPES[
        _stable_index(seed, difficulty, "source-shape", len(_SOURCE_SHAPES))
    ]
    selector = (6, 7, 9)[_stable_index(seed, difficulty, "selector", 3)]
    colour_pool = [colour for colour in (5, 6, 7, 9) if colour != selector]
    colour_shift = _stable_index(seed, difficulty, "distractor-colours", len(colour_pool))
    colour_pool = colour_pool[colour_shift:] + colour_pool[:colour_shift]
    distractor_large, distractor_small = colour_pool[:2]

    grid = full_grid(height, width, 0)
    grid[0][0] = selector
    grid[0][width - 1] = code

    frame_left = width - frame_w - 1
    frame_top_count = height - frame_h
    frame_top = 1 + (
        int(seed) + 3 * int(sample_index) + _difficulty_offset(difficulty)
    ) % frame_top_count
    draw_frame(
        grid,
        frame_top,
        frame_left,
        frame_top + frame_h - 1,
        frame_left + frame_w - 1,
        8,
    )

    # Source and larger distractor occupy vertically separated 3-row slots on
    # the left.  Their relation is stable within a lesson but varies by seed.
    upper_top = 1
    lower_top = height - 3
    source_above = (
        _stable_index(seed, difficulty, "source-order", 2)
        + int(sample_index) // EXAMPLES_NEEDED
    ) % 2 == 0
    source_top = upper_top if source_above else lower_top
    distractor_top = lower_top if source_above else upper_top
    source_left = 1
    _paint_shape(grid, source_shape, source_top, source_left, selector)
    _paint_shape(grid, _BIG_DISTRACTOR, distractor_top, source_left, distractor_large)

    if distractor_layout == "inside_frame":
        # Opposite interior corners guarantee at least one survives as evidence
        # under every canonical-sized <=3-row source crop.
        grid[frame_top + 1][frame_left + 1] = distractor_small
        grid[frame_top + frame_h - 2][frame_left + frame_w - 2] = distractor_small
    else:
        margin_col = width - 1
        mid = max(2, height // 2 - 1)
        grid[mid][margin_col] = distractor_small
        grid[mid + 1][margin_col] = distractor_small

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid keyed-frame scene: " + "; ".join(errors))
    return grid
