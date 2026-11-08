"""Semantic generator for ``a88fd33fba06`` (keep deepest valid frame).

The canonical examples contain a nested chain of rectangular outline frames.
Some examples also contain a smaller singleton/domino *inside* the deepest
frame; those cells are not themselves frames and must be ignored.  The Racket
authority filters complete rectangular frames, scores each by how many other
frame bounding boxes strictly contain it, and keeps the uniquely deepest frame.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "a88fd33fba06"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "8fc6512eb9ff"
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a black background, identify the complete one-cell rectangular outline "
    "frames, ignore any non-frame singleton/domino inside them, and keep only "
    "the frame nested inside the greatest number of other frames."
)
INVARIANTS = [
    "background is 0 and all nonzero cells belong to monochrome 4-connected objects",
    "there are 2-5 complete rectangular outline frames in one strictly nested chain",
    "successive frame bounding boxes have at least one blank-cell moat (inset >= 2)",
    "there is at most one inner non-frame distractor, either a singleton or domino",
    "any non-frame distractor lies strictly inside the deepest valid frame",
    "the uniquely deepest valid frame is preserved in place and every other cell becomes 0",
]
COUNTER_HYPOTHESES = [
    "keep the globally smallest/innermost nonzero object, even when it is not a frame",
    "keep the second-largest nonzero object, which happens to fit every canonical pair",
    "assume the answer frame is centered and redraw it at the canvas center",
    "select a fixed color instead of reasoning over frame geometry",
    "assume exactly two valid frames rather than comparing nesting depth",
]

AXES = {
    "frame_count": {
        "type": "int",
        "default": "four-profile sample-index schedule",
        "valid": "2..5",
        "doc": "number of valid rectangular outline frames in the nested chain",
    },
    "inner_decoy": {
        "type": "str",
        "default": "four-profile sample-index schedule",
        "valid": "none|singleton|domino",
        "doc": "optional non-frame object strictly inside the deepest valid frame",
    },
    "layout_style": {
        "type": "str",
        "default": "four-profile sample-index schedule",
        "valid": "canonical|offset",
        "doc": "canonical uses equal 2-cell insets; offset adds asymmetric nesting",
    },
    "outer_margin": {
        "type": "str",
        "default": "four-profile sample-index schedule",
        "valid": "edge|inset",
        "doc": "whether the outer frame touches the canvas edge or has a black margin",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_ALLOWED_OVERRIDES = frozenset(AXES)
_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}

# Every three consecutive samples contains:
# - a non-frame distractor,
# - a chain of at least three valid frames,
# - an offset nesting witness,
# - both edge-touching and inset outer-frame examples.
_PROFILES = (
    (2, "none", "canonical", "edge"),
    (2, "domino", "canonical", "inset"),
    (5, "singleton", "offset", "inset"),
    (3, "domino", "offset", "edge"),
)

BBox = tuple[int, int, int, int]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the four-step lesson schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % len(_PROFILES)


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], default: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def _copy_grid(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangular sequence"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC 30x30 limit: {len(grid)}x{width}"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _bbox(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> BBox:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(box: BBox) -> int:
    r0, c0, r1, c1 = box
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _outline_cells(box: BBox) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _components(grid: Any) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            queue = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            for r, c in queue:
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            box = _bbox(cells)
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": box,
                    "bbox_area": _bbox_area(box),
                    "size": len(cells),
                }
            )
    return result


def _is_frame(obj: dict[str, Any]) -> bool:
    r0, c0, r1, c1 = obj["bbox"]
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    return set(obj["cells"]) == _outline_cells(obj["bbox"])


def _strictly_contains(outer: BBox, inner: BBox) -> bool:
    return (
        outer[0] < inner[0]
        and outer[1] < inner[1]
        and outer[2] > inner[2]
        and outer[3] > inner[3]
    )


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    h, w = len(grid), len(grid[0])
    palette = {value for row in grid for value in row}
    if 0 not in palette:
        errors.append("background color 0 must occur in the input")

    components = _components(grid)
    frames = [obj for obj in components if _is_frame(obj)]
    nonframes = [obj for obj in components if not _is_frame(obj)]
    if not 2 <= len(frames) <= 5:
        errors.append(f"expected 2-5 complete rectangular frames, found {len(frames)}")
    if len(nonframes) > 1:
        errors.append(f"expected at most one non-frame distractor, found {len(nonframes)}")

    frames.sort(key=lambda obj: (-obj["bbox_area"], obj["bbox"], obj["color"]))
    insets: list[tuple[int, int, int, int]] = []
    for index, (outer, inner) in enumerate(zip(frames, frames[1:])):
        ob, ib = outer["bbox"], inner["bbox"]
        if not _strictly_contains(ob, ib):
            errors.append(f"frames {index} and {index + 1} are not one strictly nested chain")
            continue
        inset = (ib[0] - ob[0], ib[1] - ob[1], ob[2] - ib[2], ob[3] - ib[3])
        insets.append(inset)
        if min(inset) < 2:
            errors.append(
                f"frames {index} and {index + 1} lack a blank moat: insets={inset}"
            )

    decoy_kind = "none"
    if nonframes:
        decoy = nonframes[0]
        cells = set(decoy["cells"])
        if decoy["size"] == 1:
            decoy_kind = "singleton"
        elif decoy["size"] == 2:
            (a, b) = tuple(cells)
            if abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1:
                decoy_kind = "domino"
            else:
                errors.append("two-cell distractor must be an orthogonal domino")
        else:
            errors.append(
                f"non-frame distractor must be singleton/domino, found size {decoy['size']}"
            )
        if frames:
            deepest = frames[-1]["bbox"]
            if not all(
                deepest[0] < r < deepest[2] and deepest[1] < c < deepest[3]
                for r, c in decoy["cells"]
            ):
                errors.append("non-frame distractor must lie strictly inside deepest frame")

    layout_style = None
    outer_margin = None
    margins = None
    if frames:
        layout_style = (
            "canonical"
            if insets and all(inset == (2, 2, 2, 2) for inset in insets)
            else "offset"
        )
        r0, c0, r1, c1 = frames[0]["bbox"]
        margins = (r0, c0, h - 1 - r1, w - 1 - c1)
        outer_margin = "edge" if min(margins) == 0 else "inset"

    result.update(
        {
            "height": h,
            "width": w,
            "palette": frozenset(palette),
            "components": components,
            "frames": frames,
            "nonframes": nonframes,
            "frame_count": len(frames),
            "decoy_kind": decoy_kind,
            "insets": insets,
            "layout_style": layout_style,
            "outer_margin": outer_margin,
            "margins": margins,
        }
    )
    return result


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes while accepting all canonicals."""
    del difficulty
    analysis = _analyze(grid)
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


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws obey the task's canonical nested-frame grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact caller-facing axis from a valid returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "frame_count": analysis["frame_count"],
        "inner_decoy": analysis["decoy_kind"],
        "layout_style": analysis["layout_style"],
        "outer_margin": analysis["outer_margin"],
    }


def _paint_object(output: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    for r, c in obj["cells"]:
        output[r][c] = obj["color"]
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    output = full_grid(analysis["height"], analysis["width"], 0)
    return _paint_object(output, analysis["frames"][-1])


def _rival_second_largest_object(grid):
    """Shortcut fitting all canonicals: keep the second-largest nonzero object."""
    analysis = _analyze(grid)
    components = sorted(
        analysis.get("components", ()),
        key=lambda obj: (-obj["bbox_area"], -obj["size"], obj["bbox"], obj["color"]),
    )
    output = full_grid(analysis["height"], analysis["width"], 0)
    if len(components) >= 2:
        _paint_object(output, components[1])
    return output


def _rival_innermost_nonzero_object(grid):
    """Shortcut: keep the smallest-bounding-box object whether or not it is a frame."""
    analysis = _analyze(grid)
    components = sorted(
        analysis.get("components", ()),
        key=lambda obj: (obj["bbox_area"], obj["size"], obj["bbox"], obj["color"]),
    )
    output = full_grid(analysis["height"], analysis["width"], 0)
    if components:
        _paint_object(output, components[0])
    return output


def _rival_recenter_innermost_frame(grid):
    """Canonical-fitting shortcut: redraw the selected frame at canvas center."""
    analysis = _analyze(grid)
    selected = analysis["frames"][-1]
    r0, c0, r1, c1 = selected["bbox"]
    frame_h, frame_w = r1 - r0 + 1, c1 - c0 + 1
    nr0 = (analysis["height"] - frame_h) // 2
    nc0 = (analysis["width"] - frame_w) // 2
    box = (nr0, nc0, nr0 + frame_h - 1, nc0 + frame_w - 1)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for r, c in _outline_cells(box):
        output[r][c] = selected["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "second_largest_object": _rival_second_largest_object,
    "innermost_nonzero_object": _rival_innermost_nonzero_object,
    "recenter_innermost_frame": _rival_recenter_innermost_frame,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "second_largest_object": _rival_second_largest_object,
    "recenter_innermost_frame": _rival_recenter_innermost_frame,
}


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _plain_two_frame(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["frame_count"] == 2 and analysis["decoy_kind"] == "none")


def _decoy_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["decoy_kind"] != "none"
        and _rival_innermost_nonzero_object(grid) != rule_mirror(grid)
    )


def _deep_chain_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["frame_count"] >= 3
        and _rival_second_largest_object(grid) != rule_mirror(grid)
    )


def _offset_recenter_killer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["layout_style"] == "offset"
        and _rival_recenter_innermost_frame(grid) != rule_mirror(grid)
    )


def _edge_outer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["outer_margin"] == "edge")


def _inset_outer(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and analysis["outer_margin"] == "inset")


SEMANTIC_WITNESSES = {
    "nonframe_decoy_kills_object_depth": _decoy_killer,
    "deep_chain_kills_second_largest": _deep_chain_killer,
    "offset_recenter_killer": _offset_recenter_killer,
}
WITNESS_RIVALS = {
    "nonframe_decoy_kills_object_depth": ["innermost_nonzero_object"],
    "deep_chain_kills_second_largest": ["second_largest_object"],
    "offset_recenter_killer": ["recenter_innermost_frame"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo window to falsify the named shortcut family."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the nested-frame teaching grammar")

    analyses: list[dict[str, Any]] = []
    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the nested-frame grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the exact deepest-frame selection")
        analyses.append(analysis)
        valid_demos.append(demo)

    if analyses and not any(a["decoy_kind"] != "none" for a in analyses):
        reasons.append("demonstrations never show a non-frame inner distractor")
    if analyses and not any(a["frame_count"] >= 3 for a in analyses):
        reasons.append("demonstrations never refute the canonical-fitting second-largest-object shortcut")
    if analyses and not any(a["layout_style"] == "offset" for a in analyses):
        reasons.append("demonstrations never refute centered-only frame reconstruction")
    if analyses and not any(a["outer_margin"] == "edge" for a in analyses):
        reasons.append("demonstrations never show an edge-touching outer frame")
    if analyses and not any(a["outer_margin"] == "inset" for a in analyses):
        reasons.append("demonstrations never show an inset outer frame")

    if len(valid_demos) == len(demos):
        for name, competitor in LESSON_COMPETITORS.items():
            if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
                reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons


def _paint_frame(grid: list[list[int]], box: BBox, color: int) -> None:
    for r, c in _outline_cells(box):
        grid[r][c] = color


def _build_nested_boxes(
    count: int, layout_style: str, inner_decoy: str, rng, difficulty: Any
) -> list[BBox]:
    inner_hi = {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5)
    inner_lo = 3 if difficulty != "hard" else 4
    inner_h = rng.randint(inner_lo, inner_hi)
    inner_w = rng.randint(inner_lo, inner_hi + 1)
    if inner_decoy == "domino" and inner_h == 3 and inner_w == 3:
        inner_w = 4
    if rng.randrange(2) and inner_h == inner_w:
        inner_w = min(inner_hi + 1, inner_w + 1)

    boxes_inner_to_outer: list[BBox] = [(0, 0, inner_h - 1, inner_w - 1)]
    skew = rng.choice(("top", "left", "bottom", "right"))
    for _ in range(count - 1):
        top = bottom = left = right = 2
        if layout_style == "offset":
            if skew == "top":
                top += 1
            elif skew == "left":
                left += 1
            elif skew == "bottom":
                bottom += 1
            else:
                right += 1
        r0, c0, r1, c1 = boxes_inner_to_outer[-1]
        boxes_inner_to_outer.append(
            (r0 - top, c0 - left, r1 + bottom, c1 + right)
        )

    outer = boxes_inner_to_outer[-1]
    shift_r, shift_c = -outer[0], -outer[1]
    return [
        (r0 + shift_r, c0 + shift_c, r1 + shift_r, c1 + shift_c)
        for r0, c0, r1, c1 in reversed(boxes_inner_to_outer)
    ]


def _place_boxes(boxes: list[BBox], outer_margin: str) -> tuple[list[list[int]], list[BBox]]:
    outer = boxes[0]
    outer_h = outer[2] - outer[0] + 1
    outer_w = outer[3] - outer[1] + 1
    margin = 0 if outer_margin == "edge" else 1
    h, w = outer_h + 2 * margin, outer_w + 2 * margin
    if h > 30 or w > 30:
        raise ValueError(f"constructed grid exceeds ARC limit: {h}x{w}")
    shifted = [
        (r0 + margin, c0 + margin, r1 + margin, c1 + margin)
        for r0, c0, r1, c1 in boxes
    ]
    return full_grid(h, w, 0), shifted


def _place_decoy(grid, deepest: BBox, kind: str, color: int, rng) -> None:
    if kind == "none":
        return
    r0, c0, r1, c1 = deepest
    interior = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
    ]
    if kind == "singleton":
        r, c = rng.choice(interior)
        grid[r][c] = color
        return
    candidates = []
    inside = set(interior)
    for r, c in interior:
        for dr, dc in ((0, 1), (1, 0)):
            other = (r + dr, c + dc)
            if other in inside:
                candidates.append(((r, c), other))
    if not candidates:
        raise ValueError("deepest frame interior cannot host requested domino")
    for r, c in rng.choice(candidates):
        grid[r][c] = color


def _anchor_grid(profile: int, rng) -> list[list[int]]:
    """Canonical-scale anchors with seed-varying colors and decoy placement."""
    if profile == 0:
        h = w = 9
        boxes = [(0, 0, 8, 8), (2, 2, 6, 6)]
        decoy_kind = "none"
    elif profile == 1:
        h = w = 11
        boxes = [(1, 1, 9, 9), (3, 3, 7, 7)]
        decoy_kind = "domino"
    else:
        raise ValueError(f"unknown anchor profile {profile}")
    grid = full_grid(h, w, 0)
    colors = rng.sample(range(1, 10), 2 + (decoy_kind != "none"))
    for box, color in zip(boxes, colors):
        _paint_frame(grid, box, color)
    if decoy_kind != "none":
        _place_decoy(grid, boxes[-1], decoy_kind, colors[-1], rng)
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = int(sample_index) % len(_PROFILES)
    default_count, default_decoy, default_layout, default_margin = _PROFILES[profile]
    frame_count = _scheduled_int(ctx, "frame_count", 2, 5, default_count)
    inner_decoy = _scheduled_choice(
        ctx, "inner_decoy", ("none", "singleton", "domino"), default_decoy
    )
    layout_style = _scheduled_choice(
        ctx, "layout_style", ("canonical", "offset"), default_layout
    )
    outer_margin = _scheduled_choice(
        ctx, "outer_margin", ("edge", "inset"), default_margin
    )

    rng = ctx.draw_rng(f"geometry:{difficulty or 'medium'}")
    # Keep two ordinary profiles on exact canonical mechanical profiles. Any
    # explicit override takes the fully constructive path so every requested
    # axis value remains observable rather than being silently pinned.
    if not overrides and profile in (0, 1):
        grid = _anchor_grid(profile, rng)
    else:
        boxes = _build_nested_boxes(frame_count, layout_style, inner_decoy, rng, difficulty)
        grid, boxes = _place_boxes(boxes, outer_margin)
        colors = rng.sample(range(1, 10), frame_count + (inner_decoy != "none"))
        for box, color in zip(boxes, colors):
            _paint_frame(grid, box, color)
        if inner_decoy != "none":
            _place_decoy(grid, boxes[-1], inner_decoy, colors[-1], rng)

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Targeted malformed scenes used by strict defect-lint mutation probes."""
    base = generate(314159, 2, difficulty="medium")
    analysis = _analyze(base)
    fixtures: list[tuple[str, list[list[int]]]] = []

    blank = full_grid(len(base), len(base[0]), 0)
    fixtures.append(("blank_grid", blank))

    broken = _copy_grid(base)
    r, c = analysis["frames"][0]["cells"][0]
    broken[r][c] = 0
    fixtures.append(("broken_outer_frame", broken))

    stray = _copy_grid(base)
    used = {value for row in stray for value in row}
    color = next(value for value in range(1, 10) if value not in used)
    outer = analysis["frames"][0]["bbox"]
    candidates = [
        (r, c)
        for r in range(len(stray))
        for c in range(len(stray[0]))
        if stray[r][c] == 0
        and not (outer[0] < r < outer[2] and outer[1] < c < outer[3])
    ]
    if candidates:
        r, c = candidates[0]
        stray[r][c] = color
    else:
        # profile 2 is inset, so this should not be needed; retain a deterministic fallback.
        stray[0][0] = color
    fixtures.append(("stray_nonframe_outside_deepest", stray))

    malformed_decoy = _copy_grid(base)
    decoy = analysis["nonframes"][0]
    decoy_color = decoy["color"]
    deepest = analysis["frames"][-1]["bbox"]
    occupied = set(decoy["cells"])
    extra = next(
        (pos for pos in _outline_cells((deepest[0] + 1, deepest[1] + 1, deepest[2] - 1, deepest[3] - 1))
         if pos not in occupied and malformed_decoy[pos[0]][pos[1]] == 0),
        None,
    )
    if extra is None:
        extra = (deepest[0] + 1, deepest[1] + 1)
    malformed_decoy[extra[0]][extra[1]] = decoy_color
    fixtures.append(("malformed_inner_decoy", malformed_decoy))

    extra_object = _copy_grid(base)
    used = {value for row in extra_object for value in row}
    color = next(value for value in range(1, 10) if value not in used)
    deepest = analysis["frames"][-1]["bbox"]
    for r in range(deepest[0] + 1, deepest[2]):
        for c in range(deepest[1] + 1, deepest[3]):
            if extra_object[r][c] == 0:
                extra_object[r][c] = color
                fixtures.append(("second_inner_nonframe", extra_object))
                return fixtures
    return fixtures
