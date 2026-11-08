"""Sampler for ARC task 2db2974cdb04: extract holes of hollow objects.

Each input contains one or two monochrome hollow objects on background 0.  The
selected Racket authority returns a zero grid with only background regions that
are wholly enclosed by an object's bounding box, painted in that object's
color.  Object borders disappear.

The sampler deliberately includes both ordinary rectangular frames and
"stemmed" frames.  A two-cell outward stem expands an object's bounding box
without enclosing the adjacent exterior background, supplying a constructive
counterexample to the tempting shortcut "paint every zero inside the bbox".
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2db2974cdb04"
TASK_ID = GENERATOR_ID
RULE_HASH = "c621ef85bf9e"
VERSION = "3.0.0"
SUMMARY = (
    "One or two distinct-colored hollow objects appear on background 0. "
    "Objects vary in size, position, edge contact, mutual contact, and may be "
    "rectangular frames or frames with a two-cell outward stem.  The output is "
    "otherwise zero: remove every object border and paint only each truly "
    "enclosed zero-region with that object's color."
)

INVARIANTS = [
    "one or two same-color 4-connected hollow objects in distinct nonzero colors",
    "each object is a closed rectangular frame, optionally with one two-cell outward stem",
    "each object encloses exactly one nonempty global background region",
    "object bounding boxes are disjoint; different-colored borders may touch",
]

_LAYOUTS = {
    "canonical_9x9": (9, 9),
    "canonical_9x11": (9, 11),
    "canonical_10x10": (10, 10),
    "canonical_10x12": (10, 12),
    "expanded_12x14": (12, 14),
}
_LAYOUT_NAMES = tuple(_LAYOUTS)
_SHAPES = ("rectangular", "stemmed")
_BORDERS = ("interior", "edge")
_CONTACTS = ("separated", "touching")

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "difficulty-aware draw across four canonical sizes plus 12x14",
        "valid": "canonical_9x9|canonical_9x11|canonical_10x10|canonical_10x12|expanded_12x14",
    },
    "n_objects": {
        "type": "int",
        "default": "three-profile curriculum: 2, 2, 1",
        "valid": "1..2",
    },
    "shape_profile": {
        "type": "str",
        "default": "three-profile curriculum: stemmed, rectangular, stemmed",
        "valid": "rectangular|stemmed",
    },
    "border_profile": {
        "type": "str",
        "default": "three-profile curriculum: edge, interior, interior",
        "valid": "interior|edge",
    },
    "contact_profile": {
        "type": "str",
        "default": "three-profile curriculum: touching, separated, separated",
        "valid": "separated|touching",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_objects": 1, "contact_profile": "touching"},
]

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "stemmed_pair_touching_edge",
    "rectangular_pair_separated_interior",
    "stemmed_single_interior",
)
_PROFILE_DEFAULTS = {
    SCHEDULE_PROFILES[0]: {
        "n_objects": 2,
        "shape_profile": "stemmed",
        "border_profile": "edge",
        "contact_profile": "touching",
    },
    SCHEDULE_PROFILES[1]: {
        "n_objects": 2,
        "shape_profile": "rectangular",
        "border_profile": "interior",
        "contact_profile": "separated",
    },
    SCHEDULE_PROFILES[2]: {
        "n_objects": 1,
        "shape_profile": "stemmed",
        "border_profile": "interior",
        "contact_profile": "separated",
    },
}
MIN_STRICT_FRAC = 0.95


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in ("easy", "medium", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle three complementary demonstrations in every difficulty band."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name == "n_objects":
            if type(value) is not int:
                raise TypeError("n_objects must be an integer, not bool/float/string")
            if value not in (1, 2):
                raise ValueError("n_objects must be 1 or 2")
        elif name == "layout_profile":
            if type(value) is not str or value not in _LAYOUTS:
                raise ValueError(f"layout_profile must be one of {_LAYOUT_NAMES}")
        elif name == "shape_profile":
            if type(value) is not str or value not in _SHAPES:
                raise ValueError(f"shape_profile must be one of {_SHAPES}")
        elif name == "border_profile":
            if type(value) is not str or value not in _BORDERS:
                raise ValueError(f"border_profile must be one of {_BORDERS}")
        elif name == "contact_profile":
            if type(value) is not str or value not in _CONTACTS:
                raise ValueError(f"contact_profile must be one of {_CONTACTS}")
    if overrides.get("n_objects") == 1 and overrides.get("contact_profile") == "touching":
        raise ValueError("one object cannot have contact_profile='touching'")


def _resolved_profiles(seed: int, sample_index: int, band: str, overrides: dict[str, Any]):
    profile = schedule_profile(seed, sample_index, band)
    resolved = dict(_PROFILE_DEFAULTS[profile])
    explicit = {name: value for name, value in overrides.items() if value is not None}
    resolved.update({name: value for name, value in explicit.items() if name != "layout_profile"})
    # Make one-axis overrides constructive rather than accidentally inheriting
    # an incompatible scheduled partner.
    if explicit.get("n_objects") == 1 and "contact_profile" not in explicit:
        resolved["contact_profile"] = "separated"
    if explicit.get("contact_profile") == "touching" and "n_objects" not in explicit:
        resolved["n_objects"] = 2
    if resolved["n_objects"] == 1 and resolved["contact_profile"] == "touching":
        raise ValueError("one object cannot have contact_profile='touching'")
    return profile, resolved


def _perimeter(height: int, width: int, top: int = 0, left: int = 0):
    return {
        (top + r, left + c)
        for r in range(height)
        for c in range(width)
        if r in (0, height - 1) or c in (0, width - 1)
    }


def _normalize(cells: Iterable[tuple[int, int]]):
    points = tuple(cells)
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    normalized = tuple(sorted((r - min_r, c - min_c) for r, c in points))
    height = max(r for r, _ in normalized) + 1
    width = max(c for _, c in normalized) + 1
    return normalized, height, width


def _shape(core_h: int, core_w: int, direction: str | None):
    if direction is None:
        cells = _perimeter(core_h, core_w)
        normalized, height, width = _normalize(cells)
        return normalized, height, width, 0, 0
    if direction == "top":
        core_top, core_left = 2, 0
        anchor = core_w // 2
        cells = _perimeter(core_h, core_w, core_top, core_left)
        cells.update(((1, anchor), (0, anchor)))
    elif direction == "bottom":
        core_top, core_left = 0, 0
        anchor = core_w // 2
        cells = _perimeter(core_h, core_w, core_top, core_left)
        cells.update(((core_h, anchor), (core_h + 1, anchor)))
    elif direction == "left":
        core_top, core_left = 0, 2
        anchor = core_h // 2
        cells = _perimeter(core_h, core_w, core_top, core_left)
        cells.update(((anchor, 1), (anchor, 0)))
    elif direction == "right":
        core_top, core_left = 0, 0
        anchor = core_h // 2
        cells = _perimeter(core_h, core_w, core_top, core_left)
        cells.update(((anchor, core_w), (anchor, core_w + 1)))
    else:  # pragma: no cover - internal programming error
        raise ValueError(direction)
    normalized, height, width = _normalize(cells)
    return normalized, height, width, core_top, core_left


def _translate(cells: Iterable[tuple[int, int]], dr: int, dc: int):
    return tuple(sorted((r + dr, c + dc) for r, c in cells))


def _parts_touch(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]) -> bool:
    right_set = set(right)
    return any(
        (r - 1, c) in right_set or (r + 1, c) in right_set
        or (r, c - 1) in right_set or (r, c + 1) in right_set
        for r, c in left
    )


@lru_cache(maxsize=128)
def _scene_candidates(
    available_h: int,
    available_w: int,
    n_objects: int,
    shape_profile: str,
    contact_profile: str,
):
    """Enumerate finite constructive geometry; generation never retries or clips."""
    candidates: set[tuple[tuple[tuple[int, int], ...], ...]] = set()
    sizes = range(3, 7)
    if n_objects == 1:
        directions = (None,) if shape_profile == "rectangular" else ("top", "bottom", "left", "right")
        for core_h in sizes:
            for core_w in sizes:
                for direction in directions:
                    cells, height, width, _, _ = _shape(core_h, core_w, direction)
                    if height <= available_h and width <= available_w:
                        candidates.add((cells,))
        return tuple(sorted(candidates))

    gap = 0 if contact_profile == "touching" else 1
    for orientation in ("horizontal", "vertical"):
        if shape_profile == "rectangular":
            directions = (None,)
        elif orientation == "horizontal":
            directions = ("top", "bottom")
        else:
            directions = ("left", "right")
        for direction in directions:
            for h1 in sizes:
                for w1 in sizes:
                    first = _shape(h1, w1, direction)
                    for h2 in sizes:
                        for w2 in sizes:
                            second = _shape(h2, w2, direction)
                            c1, sh1, sw1, ct1, cl1 = first
                            c2, sh2, sw2, ct2, cl2 = second
                            if orientation == "horizontal":
                                common_core_top = max(ct1, ct2)
                                r1, r2 = common_core_top - ct1, common_core_top - ct2
                                first_cells = _translate(c1, r1, 0)
                                second_cells = _translate(c2, r2, sw1 + gap)
                            else:
                                common_core_left = max(cl1, cl2)
                                c_off1, c_off2 = common_core_left - cl1, common_core_left - cl2
                                first_cells = _translate(c1, 0, c_off1)
                                second_cells = _translate(c2, sh1 + gap, c_off2)
                            all_cells = first_cells + second_cells
                            _, scene_h, scene_w = _normalize(all_cells)
                            if scene_h > available_h or scene_w > available_w:
                                continue
                            if set(first_cells) & set(second_cells):
                                continue
                            touching = _parts_touch(first_cells, second_cells)
                            if touching != (contact_profile == "touching"):
                                continue
                            normalized_all, _, _ = _normalize(all_cells)
                            # Apply the same normalization shift independently to
                            # each object by deriving it from the combined points.
                            min_r = min(r for r, _ in all_cells)
                            min_c = min(c for _, c in all_cells)
                            norm_first = _translate(first_cells, -min_r, -min_c)
                            norm_second = _translate(second_cells, -min_r, -min_c)
                            assert tuple(sorted(norm_first + norm_second)) == normalized_all
                            candidates.add((norm_first, norm_second))
    return tuple(sorted(candidates))


def _candidate_extent(scene):
    cells = tuple(point for obj in scene for point in obj)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _part_has_bbox_exterior(cells):
    """Whether bbox filling would paint exterior-connected background."""
    points, height, width = _normalize(cells)
    blocked = {(r + 1, c + 1) for r, c in points}
    padded_h, padded_w = height + 2, width + 2
    reachable = {(0, 0)}
    stack = [(0, 0)]
    while stack:
        r, c = stack.pop()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if not (0 <= nr < padded_h and 0 <= nc < padded_w):
                continue
            point = (nr, nc)
            if point in blocked or point in reachable:
                continue
            reachable.add(point)
            stack.append(point)
    return any(
        (r + 1, c + 1) in reachable
        for r in range(1, height - 1)
        for c in range(1, width - 1)
        if (r, c) not in set(points)
    )


def _scene_refutes_bbox(scene):
    return any(_part_has_bbox_exterior(cells) for cells in scene)


def _select_scene(candidates, band: str, rng, *, prefer_bbox_counterexample=False):
    if not candidates:
        raise ValueError("no constructive geometry for requested axis combination")
    eligible = list(candidates)
    if prefer_bbox_counterexample:
        counterexamples = [scene for scene in eligible if _scene_refutes_bbox(scene)]
        if counterexamples:
            eligible = counterexamples
    ranked = sorted(eligible, key=lambda scene: (_candidate_extent(scene), len(scene[0]), scene))
    if band == "easy":
        pool = ranked[: max(1, (2 * len(ranked)) // 3)]
    elif band == "hard":
        pool = ranked[len(ranked) // 3 :]
    else:
        pool = ranked
    return rng.choice(pool)


def _placement_options(grid_h: int, grid_w: int, scene, border_profile: str):
    scene_h, scene_w = _candidate_extent(scene)
    result = []
    for top in range(grid_h - scene_h + 1):
        for left in range(grid_w - scene_w + 1):
            if border_profile == "interior":
                if top < 1 or left < 1 or top + scene_h >= grid_h or left + scene_w >= grid_w:
                    continue
            else:
                if not (top == 0 or left == 0 or top + scene_h == grid_h or left + scene_w == grid_w):
                    continue
            result.append((top, left))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    _, resolved = _resolved_profiles(seed, sample_index, band, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    ordinary_layouts = {
        "easy": _LAYOUT_NAMES[:4],
        "medium": _LAYOUT_NAMES,
        "hard": (_LAYOUT_NAMES[2], _LAYOUT_NAMES[3], _LAYOUT_NAMES[4], _LAYOUT_NAMES[1], _LAYOUT_NAMES[4]),
    }[band]
    layout_options = _LAYOUT_NAMES if overrides.get("layout_profile") is not None else ordinary_layouts
    layout_profile = ctx.draw_choice("layout_profile", layout_options)
    n_objects = ctx.draw_choice("n_objects", (resolved["n_objects"],))
    shape_profile = ctx.draw_choice("shape_profile", (resolved["shape_profile"],))
    border_profile = ctx.draw_choice("border_profile", (resolved["border_profile"],))
    contact_profile = ctx.draw_choice("contact_profile", (resolved["contact_profile"],))

    h, w = _LAYOUTS[layout_profile]
    available_h = h - 2 if border_profile == "interior" else h
    available_w = w - 2 if border_profile == "interior" else w
    candidates = _scene_candidates(
        available_h, available_w, n_objects, shape_profile, contact_profile
    )
    scene = _select_scene(
        candidates,
        band,
        ctx.draw_rng("geometry"),
        prefer_bbox_counterexample=(shape_profile == "stemmed"),
    )
    placements = _placement_options(h, w, scene, border_profile)
    if not placements:  # should be impossible if candidate dimensions are correct
        raise RuntimeError("constructive scene has no lawful placement")
    top, left = ctx.draw_rng("placement").choice(placements)
    colors = list(range(1, 10))
    ctx.draw_rng("colors").shuffle(colors)

    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, scene):
        for r, c in cells:
            if grid[top + r][left + c] != 0:
                raise RuntimeError("constructive objects overlap")
            grid[top + r][left + c] = color
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9 (not bool)"]
    return []


def _components(grid: list[list[int]], *, zero: bool):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (grid[r][c] == 0) is zero
    }
    result = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        todo = [start]
        cells = {start}
        while todo:
            r, c = todo.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    nr, nc = point
                    if zero or grid[nr][nc] == color:
                        unseen.remove(point)
                        cells.add(point)
                        todo.append(point)
        result.append({"color": color, "cells": cells})
    return result


def _bbox(cells: Iterable[tuple[int, int]]):
    points = tuple(cells)
    return (
        min(r for r, _ in points), min(c for _, c in points),
        max(r for r, _ in points), max(c for _, c in points),
    )


def _classify_shape(cells: set[tuple[int, int]]):
    r1, c1, r2, c2 = _bbox(cells)
    if r2 - r1 + 1 >= 3 and c2 - c1 + 1 >= 3:
        if cells == _perimeter(r2 - r1 + 1, c2 - c1 + 1, r1, c1):
            return {"style": "rectangular", "core_bbox": (r1, c1, r2, c2)}

    # A stemmed object is exactly a rectangular perimeter plus two collinear
    # outward cells.  Enumerating candidate cores keeps recognition independent
    # of the generator's chosen direction and accepts boundary-touching objects.
    for top in range(r1, r2 + 1):
        for bottom in range(top + 2, r2 + 1):
            for left in range(c1, c2 + 1):
                for right in range(left + 2, c2 + 1):
                    frame = _perimeter(bottom - top + 1, right - left + 1, top, left)
                    for col in range(left + 1, right):
                        candidates = (
                            {(top - 1, col), (top - 2, col)},
                            {(bottom + 1, col), (bottom + 2, col)},
                        )
                        for stem in candidates:
                            if cells == frame | stem:
                                return {"style": "stemmed", "core_bbox": (top, left, bottom, right)}
                    for row in range(top + 1, bottom):
                        candidates = (
                            {(row, left - 1), (row, left - 2)},
                            {(row, right + 1), (row, right + 2)},
                        )
                        for stem in candidates:
                            if cells == frame | stem:
                                return {"style": "stemmed", "core_bbox": (top, left, bottom, right)}
    return None


def _bbox_disjoint(left, right):
    lr1, lc1, lr2, lc2 = left
    rr1, rc1, rr2, rc2 = right
    return lr2 < rr1 or rr2 < lr1 or lc2 < rc1 or rc2 < lc1


def _analyze(grid: Any):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    colored_parts = _components(grid, zero=False)
    zero_regions = [part["cells"] for part in _components(grid, zero=True)]
    if not 1 <= len(colored_parts) <= 2:
        errors.append(f"expected one or two colored objects, found {len(colored_parts)}")
    colors = [obj["color"] for obj in colored_parts]
    if len(set(colors)) != len(colors):
        errors.append("each object must use a distinct nonzero color")

    styles = []
    for index, obj in enumerate(colored_parts):
        obj["bbox"] = _bbox(obj["cells"])
        shape = _classify_shape(obj["cells"])
        if shape is None:
            errors.append(f"object {index} is neither a rectangular nor a two-cell-stemmed frame")
            continue
        obj.update(shape)
        styles.append(shape["style"])
        r1, c1, r2, c2 = obj["bbox"]
        holes = [
            region for region in zero_regions
            if region and all(r1 < r < r2 and c1 < c < c2 for r, c in region)
        ]
        obj["holes"] = holes
        if len(holes) != 1:
            errors.append(f"object {index} must enclose exactly one global background region")

    if len(set(styles)) > 1:
        errors.append("all objects in one scene must share one shape_profile")
    for index, left in enumerate(colored_parts):
        for right in colored_parts[index + 1 :]:
            if "bbox" in left and "bbox" in right and not _bbox_disjoint(left["bbox"], right["bbox"]):
                errors.append("object bounding boxes must be disjoint")

    occupied = set().union(*(obj["cells"] for obj in colored_parts)) if colored_parts else set()
    edge = any(r in (0, h - 1) or c in (0, w - 1) for r, c in occupied)
    touching = len(colored_parts) == 2 and _parts_touch(colored_parts[0]["cells"], colored_parts[1]["cells"])
    layout = next((name for name, dims in _LAYOUTS.items() if dims == (h, w)), None)
    if layout is None:
        errors.append(f"grid dimensions {(h, w)} are outside declared layout profiles")
    return {
        "errors": errors,
        "colored_parts": colored_parts,
        "zero_regions": zero_regions,
        "layout_profile": layout,
        "n_objects": len(colored_parts),
        "shape_profile": styles[0] if styles and len(set(styles)) == 1 else None,
        "border_profile": "edge" if edge else "interior",
        "contact_profile": "touching" if touching else "separated",
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize task-valid scenes, including every selected canonical input."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    requested = None
    if isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = {k: v for k, v in meta["overrides"].items() if v is not None}
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in observed and observed[name] != value:
                errors.append(f"override {name} requested {value!r}, observed {observed[name]!r}")
    return errors


def strict_canonical_like(grid):
    """Task-linked strict predicate: lawful hollow-object extraction input."""
    return self_check(grid)


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"cannot observe malformed grid: {analysis['errors'][0]}")
    return {name: analysis[name] for name in AXES}


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority for probes."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(f"invalid input: {analysis['errors'][0]}")
    out = [[0 for _ in row] for row in grid]
    for obj in analysis["colored_parts"]:
        for region in obj["holes"]:
            for r, c in region:
                out[r][c] = obj["color"]
    return out


def _rival_preserve_borders(grid):
    out = deepcopy(grid)
    intended = rule_mirror(grid)
    for r, row in enumerate(intended):
        for c, value in enumerate(row):
            if value:
                out[r][c] = value
    return out


def _rival_bbox_interior(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    out = [[0 for _ in row] for row in grid]
    for obj in analysis["colored_parts"]:
        r1, c1, r2, c2 = obj["bbox"]
        for r in range(r1 + 1, r2):
            for c in range(c1 + 1, c2):
                if grid[r][c] == 0:
                    out[r][c] = obj["color"]
    return out


def _rival_largest_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError(analysis["errors"][0])
    out = [[0 for _ in row] for row in grid]
    if not analysis["colored_parts"]:
        return out
    obj = max(analysis["colored_parts"], key=lambda item: (len(item["cells"]), item["color"]))
    for region in obj["holes"]:
        for r, c in region:
            out[r][c] = obj["color"]
    return out


def _lawful(grid):
    return not _analyze(grid)["errors"]


def _stem_refutes_bbox(grid):
    analysis = _analyze(grid)
    return (
        not analysis["errors"]
        and analysis["shape_profile"] == "stemmed"
        and _rival_bbox_interior(grid) != rule_mirror(grid)
    )


def _has_multiple(grid):
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["n_objects"] == 2


def _removes_border(grid):
    return _lawful(grid) and rule_mirror(grid) != _rival_preserve_borders(grid)


SEMANTIC_RIVALS = {
    "preserve_borders": _rival_preserve_borders,
    "bbox_interior": _rival_bbox_interior,
    "largest_only": _rival_largest_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"bbox_interior": _rival_bbox_interior}
SEMANTIC_WITNESSES = {
    "border_removed": _removes_border,
    "stemmed_bbox_counterexample": _stem_refutes_bbox,
    "multiple_objects": _has_multiple,
}
WITNESS_RIVALS = {
    "border_removed": ["preserve_borders"],
    "stemmed_bbox_counterexample": ["bbox_interior"],
    "multiple_objects": ["largest_only"],
}


def lesson_identifiable(demos, query):
    """Reject a materialized lesson whenever a named shortcut survives demos."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        label = "query" if index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{label} is malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{label} disagrees with the hole-extraction rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
