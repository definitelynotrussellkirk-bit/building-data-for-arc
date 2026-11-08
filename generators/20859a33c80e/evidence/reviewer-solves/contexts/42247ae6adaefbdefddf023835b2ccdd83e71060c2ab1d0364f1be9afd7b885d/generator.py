"""Semantic generator for ARC task ``20859a33c80e``.

Every nonzero 4-connected same-color component is recolored according to the
number of *other component bounding boxes* that contain its bounding box.
Outermost components have depth 1 and become red (2); depth 2 becomes green
(3), depth 3 yellow (4), depth 4 gray (5), depth 5 magenta (6), and deeper
objects use maroon (9), matching the canonical Racket authority.

The generated curriculum deliberately includes ordinary nested frames,
multiple independent roots, a child on a parent's bounding-box boundary, and
children inside the bounding box of a non-frame L-shaped parent.  Those scenes
separate bounding-box containment from visual enclosure, strict-interior, and
frame-only shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "20859a33c80e"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "c7c12a48b62f"
MIN_STRICT_FRAC = 0.90
EXAMPLES_NEEDED = 5

SUMMARY = (
    "A 0-background grid contains 3-4 nonzero connected components whose "
    "bounding boxes form one or two containment trees. Recolor every component "
    "by inclusive bounding-box depth: depth 1->2, 2->3, 3->4, 4->5, 5->6, "
    "and deeper->9. Component shape and source color do not determine the answer."
)

INVARIANTS = [
    "background is 0 and every cell is an ARC color 0..9",
    "there are 3-4 nonzero 4-connected same-color components",
    "at least one component bounding box contains another",
    "containment depths are contiguous from 1 through the maximum depth",
    "normal draws contain no equal-bounding-box ambiguity",
]

COUNTER_HYPOTHESES = [
    "paint every nonzero component red",
    "use only strict-interior containment and ignore boundary-contained children",
    "count only clean rectangular frames as containers",
    "cap all nested objects at depth 2",
    "preserve or remap source colors instead of using containment depth",
    "merge disconnected components of the same color before counting containers",
    "cap the output palette at canonical maximum depth 3",
    "rank components by area, position, or object count rather than containment",
]

SCENE_KINDS = (
    "single_chain",
    "two_roots",
    "boundary_child",
    "bbox_only",
    "deep_chain",
)
COLOR_PATTERNS = ("distinct", "repeat_depth")
SCHEDULE_PROFILES = SCENE_KINDS
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed choices with an 11x11 anchor every seven draws",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed choices with an 11x11 anchor every seven draws",
        "valid": "11..18",
    },
    "scene_kind": {
        "type": "str",
        "default": "five-profile sample_index schedule",
        "valid": "|".join(SCENE_KINDS),
    },
    "color_pattern": {
        "type": "str",
        "default": "alternates distinct/repeated across successive sample indices",
        "valid": "|".join(COLOR_PATTERNS),
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
_HEIGHTS_BY_BAND = {
    "easy": (9, 10, 11),
    "medium": (9, 10, 11, 11, 12, 13),
    "hard": (11, 11, 11, 12, 13, 14, 15, 16),
}
_WIDTHS_BY_BAND = {
    "easy": (11, 12, 13),
    "medium": (11, 12, 13, 13, 14),
    "hard": (11, 12, 13, 13, 14, 15, 16, 17, 18),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"invalid ARC color at ({r},{c}): {value!r}")
    return errors


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Canonical object model: 4-connected components of one nonzero color."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "size": len(cells),
                }
            )
    return result


def _bbox_contains(parent: dict[str, Any], child: dict[str, Any]) -> bool:
    pr1, pc1, pr2, pc2 = parent["bbox"]
    cr1, cc1, cr2, cc2 = child["bbox"]
    return parent["bbox"] != child["bbox"] and (
        pr1 <= cr1 and pc1 <= cc1 and pr2 >= cr2 and pc2 >= cc2
    )


def _strict_bbox_contains(parent: dict[str, Any], child: dict[str, Any]) -> bool:
    pr1, pc1, pr2, pc2 = parent["bbox"]
    cr1, cc1, cr2, cc2 = child["bbox"]
    return pr1 < cr1 and pc1 < cc1 and pr2 > cr2 and pc2 > cc2


def _is_rect_frame(component: dict[str, Any]) -> bool:
    r1, c1, r2, c2 = component["bbox"]
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return False
    expected = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return set(component["cells"]) == expected


def _depths(components: list[dict[str, Any]], *, mode: str = "canonical") -> list[int]:
    depths: list[int] = []
    for child in components:
        count = 0
        for parent in components:
            if parent is child:
                continue
            if mode == "canonical":
                contains = _bbox_contains(parent, child)
            elif mode == "strict":
                contains = _strict_bbox_contains(parent, child)
            elif mode == "frames_only":
                contains = _is_rect_frame(parent) and _bbox_contains(parent, child)
            else:
                raise ValueError(f"unknown depth mode: {mode}")
            count += int(contains)
        depths.append(count + 1)
    return depths


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result
    components = _components(grid)
    bboxes = [component["bbox"] for component in components]
    depths = _depths(components)
    roots = sum(depth == 1 for depth in depths)
    max_depth = max(depths, default=0)
    present_depths = sorted(set(depths))
    boundary_relations = []
    nonframe_containers = []
    for pi, parent in enumerate(components):
        children = []
        for ci, child in enumerate(components):
            if pi == ci or not _bbox_contains(parent, child):
                continue
            children.append(ci)
            pr1, pc1, pr2, pc2 = parent["bbox"]
            cr1, cc1, cr2, cc2 = child["bbox"]
            if cr1 == pr1 or cc1 == pc1 or cr2 == pr2 or cc2 == pc2:
                boundary_relations.append((pi, ci))
        if children and not _is_rect_frame(parent):
            nonframe_containers.append(pi)
    result.update(
        {
            "height": len(grid),
            "width": len(grid[0]),
            "components": components,
            "bboxes": bboxes,
            "depths": depths,
            "roots": roots,
            "max_depth": max_depth,
            "present_depths": present_depths,
            "boundary_relations": boundary_relations,
            "nonframe_containers": nonframe_containers,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the intended authority-compatible input grammar.

    Curriculum-only requirements (which rival each scene kills, schedule
    coverage, and repeated-color examples) are intentionally left to the
    semantic witnesses and ``lesson_identifiable``.
    """
    del difficulty, meta
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    h, w = analysis["height"], analysis["width"]
    if not 3 <= len(analysis["components"]) <= 8:
        errors.append(
            f"expected 3..8 nonzero components, found {len(analysis['components'])}"
        )
    if len(set(analysis["bboxes"])) != len(analysis["bboxes"]):
        errors.append("components must not have identical bounding boxes")
    if analysis["max_depth"] < 2:
        errors.append("at least one component must be bbox-contained by another")
    if analysis["max_depth"] > 5:
        errors.append(f"maximum supported curriculum depth is 5, found {analysis['max_depth']}")
    expected_depths = list(range(1, analysis["max_depth"] + 1))
    if analysis["present_depths"] != expected_depths:
        errors.append(
            "containment depths must be contiguous: "
            f"found {analysis['present_depths']}, expected {expected_depths}"
        )
    if h > 30 or w > 30:
        errors.append(f"ARC grid exceeds 30x30: {h}x{w}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    reasons.extend(self_check(grid))
    h, w = analysis["height"], analysis["width"]
    n = len(analysis["components"])
    if not 9 <= h <= 16:
        reasons.append(f"height {h} is outside the canonical-like 9..16 range")
    if not 9 <= w <= 18:
        reasons.append(f"width {w} is outside the canonical-like 9..18 range")
    if not 3 <= n <= 5:
        reasons.append(f"canonical-like scenes use 3..5 components, found {n}")
    if not 1 <= analysis["roots"] <= 2:
        reasons.append(f"canonical-like scenes use one or two roots, found {analysis['roots']}")
    if not 2 <= analysis["max_depth"] <= 4:
        reasons.append(
            f"canonical-like scenes use maximum depth 2..4, found {analysis['max_depth']}"
        )
    return reasons


def _depth_color(depth: int) -> int:
    return {1: 2, 2: 3, 3: 4, 4: 5, 5: 6}.get(depth, 9)


def _render_depth_rule(grid: list[list[int]], *, mode: str) -> list[list[int]]:
    components = _components(grid)
    depths = _depths(components, mode=mode)
    output = full_grid(len(grid), len(grid[0]), 0)
    for component, depth in zip(components, depths):
        color = _depth_color(depth)
        for r, c in component["cells"]:
            output[r][c] = color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror for tests and semantic competitors; Racket stays authoritative."""
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _render_depth_rule(grid, mode="canonical")


def _rival_all_red(grid: list[list[int]]) -> list[list[int]]:
    return [[2 if value != 0 else 0 for value in row] for row in grid]


def _rival_cap_at_two(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    depths = _depths(components)
    output = full_grid(len(grid), len(grid[0]), 0)
    for component, depth in zip(components, depths):
        color = 2 if depth == 1 else 3
        for r, c in component["cells"]:
            output[r][c] = color
    return output


def _rival_cap_at_three(grid: list[list[int]]) -> list[list[int]]:
    return [[4 if value in (5, 6, 9) else value for value in row]
            for row in rule_mirror(grid)]


def _rival_global_color_components(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical-fitting mistake: treat each color as one object."""
    by_color: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                by_color.setdefault(color, []).append((r, c))
    grouped_components = []
    for color, cells in by_color.items():
        grouped_components.append({"color": color, "cells": cells,
                        "bbox": (min(r for r, _ in cells), min(c for _, c in cells),
                                 max(r for r, _ in cells), max(c for _, c in cells))})
    output = full_grid(len(grid), len(grid[0]), 0)
    for obj, depth in zip(grouped_components, _depths(grouped_components)):
        for r, c in obj["cells"]:
            output[r][c] = _depth_color(depth)
    return output


def _rival_strict_interior(grid: list[list[int]]) -> list[list[int]]:
    return _render_depth_rule(grid, mode="strict")


def _rival_frames_only(grid: list[list[int]]) -> list[list[int]]:
    return _render_depth_rule(grid, mode="frames_only")


def _rival_preserve_input_colors(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "all_components_red": _rival_all_red,
    "cap_depth_at_two": _rival_cap_at_two,
    "cap_depth_at_three": _rival_cap_at_three,
    "global_color_components": _rival_global_color_components,
    "strict_interior_only": _rival_strict_interior,
    "frames_only_containment": _rival_frames_only,
    "preserve_input_colors": _rival_preserve_input_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only genuine survivors of ALL four canonical pairs belong here. The other
# rivals remain valuable lesson checks, but canonical already refutes them.
CANONICAL_SHORTCUTS = {
    "cap_depth_at_three": _rival_cap_at_three,
    "global_color_components": _rival_global_color_components,
}


def _scene_kind_from_analysis(analysis: dict[str, Any]) -> str:
    if analysis["roots"] == 2:
        return "two_roots"
    if analysis["max_depth"] >= 4:
        return "deep_chain"
    if analysis["boundary_relations"]:
        return "boundary_child"
    if analysis["nonframe_containers"]:
        return "bbox_only"
    return "single_chain"


def _color_pattern_from_analysis(analysis: dict[str, Any]) -> str:
    by_color: dict[int, set[int]] = {}
    for component, depth in zip(analysis["components"], analysis["depths"]):
        by_color.setdefault(component["color"], set()).add(depth)
    return "repeat_depth" if any(len(depths) > 1 for depths in by_color.values()) else "distinct"


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_kind": _scene_kind_from_analysis(analysis),
        "color_pattern": _color_pattern_from_analysis(analysis),
    }


def _witness_depth_three(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["max_depth"] >= 3


def _witness_depth_four(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["max_depth"] >= 4


def _witness_multiple_roots(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["roots"] >= 2 and analysis["max_depth"] >= 2


def _witness_boundary_containment(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["boundary_relations"])


def _witness_nonframe_container(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and bool(analysis["nonframe_containers"])


def _witness_same_color_different_depth(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and _color_pattern_from_analysis(analysis) == "repeat_depth"


SEMANTIC_WITNESSES = {
    "depth_three_present": _witness_depth_three,
    "depth_four_present": _witness_depth_four,
    "multiple_independent_roots": _witness_multiple_roots,
    "bbox_boundary_child": _witness_boundary_containment,
    "nonframe_bbox_container": _witness_nonframe_container,
    "same_source_color_different_depth": _witness_same_color_different_depth,
}
WITNESS_RIVALS = {
    "depth_three_present": ["cap_depth_at_two", "all_components_red"],
    "depth_four_present": ["cap_depth_at_two", "cap_depth_at_three"],
    "multiple_independent_roots": ["all_components_red"],
    "bbox_boundary_child": ["strict_interior_only"],
    "nonframe_bbox_container": ["frames_only_containment"],
    "same_source_color_different_depth": ["global_color_components"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    seen_profiles: set[str] = set()
    for index, pair in enumerate(demos):
        grid = pair.get("input")
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        truth = rule_mirror(grid)
        if pair.get("output") != truth:
            reasons.append(f"demo {index} output disagrees with the containment-depth rule")
        seen_profiles.add(_scene_kind_from_analysis(_analyze(grid)))
    missing = set(SCENE_KINDS) - seen_profiles
    if missing:
        reasons.append(f"demonstrations omit scene profiles: {sorted(missing)}")

    q_grid = query.get("input")
    q_errors = self_check(q_grid)
    if q_errors:
        reasons.append(f"query malformed: {q_errors[0]}")
        return reasons
    q_truth = rule_mirror(q_grid)
    if query.get("output") is not None and query.get("output") != q_truth:
        reasons.append("query output disagrees with the containment-depth rule")

    # Report malformed pairs before asking rival solvers to consume them.
    # A validation failure is a reason, not an opportunity for IndexError.
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos) and (
            competitor(q_grid) != q_truth
        ):
            reasons.append(
                f"competing rule '{name}' fits every demo but predicts a different query"
            )
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_KINDS[int(sample_index) % len(SCENE_KINDS)]


def _draw_dimension(ctx, label: str, *, lo: int, hi: int, choices: tuple[int, ...], overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, choices)


def _draw_scheduled_choice(ctx, label: str, choices: tuple[str, ...], scheduled: str, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    # A singleton keyed draw records the exact scheduled public axis without
    # introducing a second source of randomness.
    return ctx.draw_choice(label, (scheduled,))


def _draw_frame(grid, bbox: tuple[int, int, int, int], color: int, *, gap=None) -> None:
    r1, c1, r2, c2 = bbox
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if r in (r1, r2) or c in (c1, c2):
                if gap is None or (r, c) != gap:
                    grid[r][c] = color


def _draw_l_parent(grid, bbox: tuple[int, int, int, int], color: int) -> None:
    r1, c1, r2, c2 = bbox
    for c in range(c1, c2 + 1):
        grid[r1][c] = color
    for r in range(r1, r2 + 1):
        grid[r][c1] = color


def _paint_block(grid, r1: int, c1: int, h: int, w: int, color: int) -> None:
    for r in range(r1, r1 + h):
        for c in range(c1, c1 + w):
            grid[r][c] = color


def _outer_box(h: int, w: int, rng, *, min_h: int = 7, min_w: int = 7):
    bh = max(min_h, min(h, rng.choice((7, 8, 9, 10, 11))))
    bw = max(min_w, min(w, rng.choice((7, 8, 9, 10, 11))))
    bh = min(bh, h)
    bw = min(bw, w)
    r1 = rng.randint(0, h - bh)
    c1 = rng.randint(0, w - bw)
    return (r1, c1, r1 + bh - 1, c1 + bw - 1)


def _colors_for_scene(ctx, count: int, pattern: str) -> list[int]:
    rng = ctx.draw_rng("colors")
    if pattern == "distinct":
        return rng.sample(list(range(1, 10)), count)
    if pattern != "repeat_depth":
        raise ValueError(f"unknown color pattern: {pattern}")
    unique = rng.sample(list(range(1, 10)), count - 1)
    return [unique[0], *unique[1:], unique[0]]


def _scene_single_chain(h: int, w: int, colors: list[int], rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    outer = _outer_box(h, w, rng, min_h=7, min_w=7)
    r1, c1, r2, c2 = outer
    inner = (r1 + 2, c1 + 2, r2 - 2, c2 - 2)
    _draw_frame(grid, outer, colors[0])
    _draw_frame(grid, inner, colors[1])
    grid[(inner[0] + inner[2]) // 2][(inner[1] + inner[3]) // 2] = colors[3]
    grid[r1 + 1][c1 + 1] = colors[2]
    return grid


def _scene_two_roots(h: int, w: int, colors: list[int], rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    gap = 1
    margin = 1 if w >= 11 else 0
    available = w - 2 * margin - gap
    left_w = max(4, available // 2)
    right_w = max(4, available - left_w)
    if left_w + right_w + gap > w:
        left_w = right_w = 4
        margin = max(0, (w - 9) // 2)
    bh = min(h, rng.choice((5, 6, 7)))
    bh = max(5, bh)
    top = rng.randint(0, h - bh)
    left = (top, margin, top + bh - 1, margin + left_w - 1)
    right_c = left[3] + gap + 1
    right = (top, right_c, top + bh - 1, min(w - 1, right_c + right_w - 1))
    _draw_frame(grid, left, colors[0])
    grid[(left[0] + left[2]) // 2][(left[1] + left[3]) // 2] = colors[1]
    _draw_frame(grid, right, colors[2])
    grid[(right[0] + right[2]) // 2][(right[1] + right[3]) // 2] = colors[3]
    return grid


def _scene_boundary_child(h: int, w: int, colors: list[int], rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    outer = _outer_box(h, w, rng, min_h=7, min_w=7)
    r1, c1, r2, c2 = outer
    gap = (r1, c2)
    inner = (r1 + 2, c1 + 2, r2 - 2, c2 - 2)
    _draw_frame(grid, outer, colors[0], gap=gap)
    _draw_frame(grid, inner, colors[1])
    grid[(inner[0] + inner[2]) // 2][(inner[1] + inner[3]) // 2] = colors[3]
    grid[gap[0]][gap[1]] = colors[2]
    return grid


def _scene_bbox_only(h: int, w: int, colors: list[int], rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    outer = _outer_box(h, w, rng, min_h=7, min_w=7)
    r1, c1, r2, c2 = outer
    _draw_l_parent(grid, outer, colors[0])
    mid_r = (r1 + r2) // 2
    mid_c = (c1 + c2) // 2
    grid[mid_r][mid_c] = colors[1]
    # A second strictly interior child with a non-singleton shape makes object
    # count and area useless as proxies for depth.
    block_r = min(r2 - 2, mid_r + 1)
    block_c = min(c2 - 2, mid_c + 1)
    _paint_block(grid, block_r, block_c, 1, 2, colors[2])
    # Keep the repeated-depth color far from the parent support.
    grid[r2 - 1][c2 - 1] = colors[3]
    return grid


def _scene_deep_chain(h: int, w: int, colors: list[int], rng) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    outer = _outer_box(h, w, rng, min_h=7, min_w=7)
    r1, c1, r2, c2 = outer
    middle = (r1 + 1, c1 + 1, r2 - 1, c2 - 1)
    inner = (r1 + 2, c1 + 2, r2 - 2, c2 - 2)
    _draw_frame(grid, outer, colors[0])
    _draw_frame(grid, middle, colors[1])
    _draw_frame(grid, inner, colors[2])
    grid[(inner[0] + inner[2]) // 2][(inner[1] + inner[3]) // 2] = colors[3]
    return grid


_SCENE_BUILDERS = {
    "single_chain": _scene_single_chain,
    "two_roots": _scene_two_roots,
    "boundary_child": _scene_boundary_child,
    "bbox_only": _scene_bbox_only,
    "deep_chain": _scene_deep_chain,
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - _ALLOWED_OVERRIDES
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    # An explicit joint-size anchor avoids a fragile product of independent
    # height/width probabilities. Seven is coprime to the five-scene/two-color
    # cycle, so every scene/color pair receives anchors over 70 draws. Exact
    # dimension overrides still take precedence in _draw_dimension.
    canonical_anchor = int(sample_index) % 7 == 0
    h = _draw_dimension(
        ctx,
        "grid_h",
        lo=9,
        hi=16,
        choices=(11,) if canonical_anchor else _HEIGHTS_BY_BAND[band],
        overrides=overrides,
    )
    w = _draw_dimension(
        ctx,
        "grid_w",
        lo=11,
        hi=18,
        choices=(11,) if canonical_anchor else _WIDTHS_BY_BAND[band],
        overrides=overrides,
    )
    scheduled_scene = SCENE_KINDS[int(sample_index) % len(SCENE_KINDS)]
    scene_kind = _draw_scheduled_choice(
        ctx, "scene_kind", SCENE_KINDS, scheduled_scene, overrides
    )
    # Five same-palette demos followed by a repeated-color query left a
    # canonical-fitting color-grouping rival alive. Alternating at period two
    # supplies the component/color distinction in EVERY consecutive five-demo
    # window, while each scene still gets both palettes over the ten-draw cycle.
    scheduled_colors = COLOR_PATTERNS[int(sample_index) % len(COLOR_PATTERNS)]
    color_pattern = _draw_scheduled_choice(
        ctx, "color_pattern", COLOR_PATTERNS, scheduled_colors, overrides
    )
    colors = _colors_for_scene(ctx, 4, color_pattern)
    grid = _SCENE_BUILDERS[scene_kind](h, w, colors, ctx.draw_rng("layout"))
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal generator error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "scene_kind": scene_kind,
        "color_pattern": color_pattern,
    }
    if observed != expected:
        raise RuntimeError(f"internal axis observation mismatch: {observed} != {expected}")
    return grid
