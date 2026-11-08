"""Generator for arc_additional_puzzles_21_set19_bundle:M128.

Extract every nonzero connected object, crop it to its bounding box, sort the
crops by cell area descending (color ascending on ties), then pack them
left-to-right with one zero column between crops.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5aa2b1bf7760"
VERSION = "3.0.0"
TASK_ID = "5aa2b1bf7760"
RULE_HASH = "ed659d688832"
SUMMARY = (
    "Canonical-scale zero-background scenes contain 3-5 separated 4-connected "
    "components; a color may label several diagonal singleton components. "
    "Extract and crop every component, sort by occupied cell count descending "
    "with ascending color as the tie-breaker, and pack the unchanged crops "
    "left-to-right, top-aligned, with one zero column between neighbors."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0; repeated colors occur only across disconnected singleton components",
    "3-5 separated 4-connected components at canonical 9-10 by 13-15 scale",
    "occupied-cell area, not bounding-box area, determines primary order",
    "equal-area objects expose the ascending-color tie-breaker",
    "cropped object texture is preserved and crops are separated by one zero column",
]

PALETTE_KINDS = ("default", "cool", "warm", "varied")
SHAPE_SETS = ("mixed", "wide", "tall")
SCENE_PROFILES = (
    "distinct3_largest",
    "distinct3_smallest",
    "distinct4_largest",
    "distinct4_smallest",
    "diagonal5",
)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-biased", "valid": "9..10"},
    "grid_w": {"type": "int", "default": "difficulty-biased", "valid": "13..15"},
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_KINDS),
    },
    "shape_set": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(SHAPE_SETS),
    },
    "scene_profile": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(SCENE_PROFILES),
    },
}

Mask = tuple[str, ...]
Cell = tuple[int, int]

_WIDE_MASKS: dict[str, Mask] = {
    "large6": ("111", "111"),
    "loose5": ("1111", "1000"),
    "compact5": ("111", "110"),
    "mid4": ("111", "010"),
    "small3a": ("111",),
    "small3b": ("110", "010"),
    "singleton1": ("1",),
}
_MIXED_MASKS: dict[str, Mask] = {
    "large6": ("111", "111"),          # strict wide
    "loose5": ("1111", "1000"),       # strict wide, sparse bbox
    "compact5": ("11", "11", "10"),  # strict tall
    "mid4": ("111", "010"),           # strict wide
    "small3a": ("1", "1", "1"),      # strict tall
    "small3b": ("111",),               # strict wide
    "singleton1": ("1",),
}

SCHEDULE_PROFILES = ("diagonal5", "distinct")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deliberate every-third-sample connectivity curriculum."""
    del seed, difficulty
    return "diagonal5" if sample_index % 3 == 0 else "distinct"


def _transpose(mask: Mask) -> Mask:
    return tuple(
        "".join(mask[r][c] for r in range(len(mask)))
        for c in range(len(mask[0]))
    )


def _mask_for(role: str, shape_set: str) -> Mask:
    if shape_set == "mixed":
        return _MIXED_MASKS[role]
    mask = _WIDE_MASKS[role]
    return mask if shape_set == "wide" else _transpose(mask)


def _mask_cells(mask: Mask) -> list[Cell]:
    return [
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value == "1"
    ]


def _palette(kind: str, n_objects: int, rng) -> list[int]:
    if kind == "default":
        colors = rng.sample(list(range(2, 9)), n_objects)
    elif kind == "cool":
        colors = [1, *rng.sample([2, 3, 4, 5], n_objects - 1)]
    elif kind == "warm":
        colors = [9, *rng.sample([5, 6, 7, 8], n_objects - 1)]
    elif kind == "varied":
        colors = [1, 9, *rng.sample(list(range(2, 9)), n_objects - 2)]
    else:  # guarded by GenCtx, retained for direct helper calls
        raise ValueError(f"unknown palette_kind {kind!r}")
    return sorted(colors)


def _official_components(
    scene_profile: str,
    shape_set: str,
    colors: list[int],
) -> list[dict]:
    """Build components already ordered by the official (-area, color) key."""
    if scene_profile == "distinct3_largest":
        roles = ("compact5", "loose5", "small3a")
        assigned = (colors[1], colors[2], colors[0])
    elif scene_profile == "distinct3_smallest":
        roles = ("large6", "compact5", "loose5")
        assigned = (colors[2], colors[0], colors[1])
    elif scene_profile == "distinct4_largest":
        roles = ("compact5", "loose5", "mid4", "small3a")
        assigned = (colors[1], colors[2], colors[3], colors[0])
    elif scene_profile == "distinct4_smallest":
        roles = ("large6", "loose5", "small3a", "small3b")
        assigned = (colors[3], colors[2], colors[0], colors[1])
    elif scene_profile == "diagonal5":
        roles = ("compact5", "loose5", "singleton1", "singleton1", "singleton1")
        assigned = (colors[1], colors[2], colors[0], colors[0], colors[0])
    else:
        raise ValueError(f"unknown scene_profile {scene_profile!r}")

    parts = []
    for role, color in zip(roles, assigned):
        mask = _mask_for(role, shape_set)
        parts.append(
            {
                "role": role,
                "color": color,
                "mask": mask,
                "area": len(_mask_cells(mask)),
            }
        )
    assert parts == sorted(parts, key=lambda part: (-part["area"], part["color"]))
    return parts


def _slot_anchors(h: int, w: int) -> list[tuple[int, int]]:
    """Four disjoint 4x4 slots with at least one blank row/column between."""
    return [(0, 0), (0, w - 4), (h - 4, 0), (h - 4, w - 4)]


def _paint_mask(
    grid: list[list[int]], mask: Mask, color: int, r0: int, c0: int
) -> None:
    for dr, dc in _mask_cells(mask):
        grid[r0 + dr][c0 + dc] = color


def _place_components(
    grid: list[list[int]], official: list[dict], scene_profile: str, rng
) -> None:
    h, w = len(grid), len(grid[0])
    if scene_profile == "diagonal5":
        # Three same-color cells touch only diagonally, so they are three
        # separate 4-connected components. This is the canonical hard branch.
        singleton_color = official[-1]["color"]
        for r, c in ((0, 0), (1, 1), (2, 2)):
            grid[r][c] = singleton_color
        # Put the tied large components later in row-major order, rebutting
        # both color grouping and spatial-order shortcuts.
        for obj, (slot_r, slot_c) in zip(official[:2], ((h - 4, 0), (h - 4, w - 4))):
            mh, mw = len(obj["mask"]), len(obj["mask"][0])
            r0 = slot_r + rng.randint(0, 4 - mh)
            c0 = slot_c + rng.randint(0, 4 - mw)
            _paint_mask(grid, obj["mask"], obj["color"], r0, c0)
        return

    anchors = _slot_anchors(h, w)
    if len(official) == 3:
        drop = rng.choice((1, 2, 3))
        anchors = [anchor for index, anchor in enumerate(anchors) if index != drop]
    # Row-major first appearance is the exact reverse of official order.
    for obj, (slot_r, slot_c) in zip(reversed(official), anchors):
        mask = obj["mask"]
        mh, mw = len(mask), len(mask[0])
        r0 = slot_r + rng.randint(0, 4 - mh)
        c0 = slot_c + rng.randint(0, 4 - mw)
        _paint_mask(grid, mask, obj["color"], r0, c0)


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
    h = ctx.draw_int_diff("grid_h", 9, 10)
    w = ctx.draw_int_diff("grid_w", 13, 15)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    shape_set = ctx.draw_choice("shape_set", SHAPE_SETS)
    if "scene_profile" in overrides:
        scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    elif sample_index % 3 == 0:
        scene_profile = ctx.draw_choice("scene_profile", ("diagonal5",))
    else:
        scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES[:-1])

    n_colors = 3 if scene_profile.startswith("distinct3") or scene_profile == "diagonal5" else 4
    colors = _palette(palette_kind, n_colors, ctx.draw_rng("colors"))
    official = _official_components(scene_profile, shape_set, colors)
    grid = full_grid(h, w, 0)
    _place_components(grid, official, scene_profile, ctx.draw_rng("placement"))
    return grid


def _components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells: set[Cell] = set()
            while queue:
                r, c = queue.popleft()
                cells.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rs = [r for r, _ in cells]
            cs = [c for _, c in cells]
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "area": len(cells),
                    "r1": min(rs),
                    "c1": min(cs),
                    "r2": max(rs),
                    "c2": max(cs),
                }
            )
    return components


def _crop(grid: list[list[int]], obj: dict, *, fill_bbox: bool = False) -> list[list[int]]:
    height = obj["r2"] - obj["r1"] + 1
    width = obj["c2"] - obj["c1"] + 1
    if fill_bbox:
        return full_grid(height, width, obj["color"])
    return [
        [grid[r][c] for c in range(obj["c1"], obj["c2"] + 1)]
        for r in range(obj["r1"], obj["r2"] + 1)
    ]


def _pack(crops: list[list[list[int]]]) -> list[list[int]]:
    height = max(len(crop) for crop in crops)
    width = sum(len(crop[0]) for crop in crops) + len(crops) - 1
    output = full_grid(height, width, 0)
    left = 0
    for crop in crops:
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                output[r][left + c] = value
        left += len(crop[0]) + 1
    return output


def _solve_with_order(
    grid: list[list[int]],
    key: Callable[[dict], tuple],
    *,
    fill_bbox: bool = False,
) -> list[list[int]]:
    components = sorted(_components(grid), key=key)
    return _pack([_crop(grid, obj, fill_bbox=fill_bbox) for obj in components])


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_order(grid, lambda obj: (-obj["area"], obj["color"]))


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Testing mirror only; the canonical Racket program remains authoritative."""
    return _solve_grid(grid)


def _color_only_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_order(grid, lambda obj: (obj["color"],))


def _spatial_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_order(grid, lambda obj: (obj["r1"], obj["c1"]))


def _bbox_area_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_order(
        grid,
        lambda obj: (
            -((obj["r2"] - obj["r1"] + 1) * (obj["c2"] - obj["c1"] + 1)),
            obj["color"],
        ),
    )


def _filled_bbox_rival(grid: list[list[int]]) -> list[list[int]]:
    return _solve_with_order(
        grid,
        lambda obj: (-obj["area"], obj["color"]),
        fill_bbox=True,
    )


def _color_group_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrongly merge every cell of a color into one bbox, ignoring connectivity."""
    grouped: list[dict] = []
    colors = sorted({value for row in grid for value in row if value})
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        grouped.append({
            "color": color, "cells": cells, "area": len(cells),
            "r1": min(rs), "c1": min(cs), "r2": max(rs), "c2": max(cs),
        })
    grouped.sort(key=lambda obj: (-obj["area"], obj["color"]))
    return _pack([_crop(grid, obj) for obj in grouped])


def _palette_kind_from_colors(colors: set[int]) -> str:
    if 1 in colors and 9 in colors:
        return "varied"
    if 1 in colors:
        return "cool"
    if 9 in colors:
        return "warm"
    return "default"


def _shape_set_from_components(components: list[dict]) -> str:
    relations = []
    for obj in components:
        height = obj["r2"] - obj["r1"] + 1
        width = obj["c2"] - obj["c1"] + 1
        relations.append((height, width))
    has_wide = any(width > height for height, width in relations)
    has_tall = any(height > width for height, width in relations)
    if has_wide and has_tall:
        return "mixed"
    if has_wide and all(width >= height for height, width in relations):
        return "wide"
    if has_tall and all(height >= width for height, width in relations):
        return "tall"
    return "unclassified"


def _scene_profile_from_components(components: list[dict]) -> str:
    by_color = Counter(obj["color"] for obj in components)
    repeated = [color for color, count in by_color.items() if count > 1]
    if (
        len(components) == 5
        and len(repeated) == 1
        and by_color[repeated[0]] == 3
        and all(obj["area"] == 1 for obj in components if obj["color"] == repeated[0])
    ):
        return "diagonal5"
    counts = Counter(obj["area"] for obj in components)
    areas = [obj["area"] for obj in components]
    tie = "largest" if counts[max(areas)] >= 2 else "smallest" if counts[min(areas)] >= 2 else "none"
    if len(components) in (3, 4) and len(by_color) == len(components) and tie != "none":
        return f"distinct{len(components)}_{tie}"
    return "unclassified"


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    components = _components(grid)
    colors = {obj["color"] for obj in components}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_kind": _palette_kind_from_colors(colors),
        "shape_set": _shape_set_from_components(components),
        "scene_profile": _scene_profile_from_components(components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding object-packing scenes."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be rectangular lists"]

    errors: list[str] = []
    h, w = len(grid), width
    if not (9 <= h <= 10 and 13 <= w <= 15):
        errors.append(f"expected canonical-scale dimensions 9..10x13..15, got {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    components = _components(grid)
    colors = [obj["color"] for obj in components]
    if not (3 <= len(components) <= 5):
        errors.append(f"expected 3..5 connected components, got {len(components)}")
    color_counts = Counter(colors)
    repeated = [color for color, count in color_counts.items() if count > 1]
    if len(components) == 5 and not repeated:
        errors.append("five-component scenes must use three repeated-color singletons")
    if repeated:
        repeated_components = [obj for obj in components if obj["color"] == repeated[0]]
        if (
            len(repeated) != 1
            or color_counts[repeated[0]] != 3
            or any(obj["area"] != 1 for obj in repeated_components)
        ):
            errors.append("repeated colors are allowed only as three singleton components")

    areas = [obj["area"] for obj in components]
    if areas and any(not 1 <= area <= 6 for area in areas):
        errors.append(f"object areas must be 1..6 cells, got {sorted(areas)}")
    if len(set(areas)) < 2:
        errors.append("at least two occupied-cell areas are required to make sorting nontrivial")

    nonrectangular = 0
    for obj in components:
        bh = obj["r2"] - obj["r1"] + 1
        bw = obj["c2"] - obj["c1"] + 1
        if bh > 4 or bw > 4:
            errors.append(f"color {obj['color']} bbox {bh}x{bw} exceeds 4x4 teaching grammar")
        if obj["area"] < bh * bw:
            nonrectangular += 1
        for r, c in obj["cells"]:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] not in (0, obj["color"])
                    ):
                        errors.append(
                            f"color {obj['color']} is not separated by a blank buffer near ({r},{c})"
                        )
                        break
                else:
                    continue
                break
    if components and nonrectangular == 0:
        errors.append("at least one non-rectangular crop is required to preserve shape texture")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _has_equal_area_pair(grid: list[list[int]]) -> bool:
    counts = Counter(obj["area"] for obj in _components(grid))
    return any(count >= 2 for count in counts.values())


def _spatial_order_differs(grid: list[list[int]]) -> bool:
    official = sorted(_components(grid), key=lambda obj: (-obj["area"], obj["color"]))
    spatial = sorted(_components(grid), key=lambda obj: (obj["r1"], obj["c1"]))
    return [obj["color"] for obj in official] != [obj["color"] for obj in spatial]


def _bbox_order_differs(grid: list[list[int]]) -> bool:
    return _solve_grid(grid) != _bbox_area_rival(grid)


def _has_repeated_singletons(grid: list[list[int]]) -> bool:
    return _scene_profile_from_components(_components(grid)) == "diagonal5"


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    profile: (
        lambda grid, expected=profile:
        _scene_profile_from_components(_components(grid)) == expected
    )
    for profile in SCENE_PROFILES
}
SEMANTIC_WITNESSES.update({
    "equal_area_color_tie": _has_equal_area_pair,
    "repeated_color_singletons": _has_repeated_singletons,
    "non_rectangular_crop": lambda grid: _solve_grid(grid) != _filled_bbox_rival(grid),
    "spatial_order_rebuttal": _spatial_order_differs,
    "bbox_area_rebuttal": _bbox_order_differs,
    "color_only_rebuttal": lambda grid: _solve_grid(grid) != _color_only_rival(grid),
    "color_grouping_rebuttal": lambda grid: _solve_grid(grid) != _color_group_rival(grid),
})

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "sort by color only": _color_only_rival,
    "preserve row-major spatial order": _spatial_rival,
    "sort by bounding-box area": _bbox_area_rival,
    "replace crop by filled bbox": _filled_bbox_rival,
    "merge disconnected cells by color": _color_group_rival,
}

WITNESS_RIVALS = {
    "distinct3_largest": ["sort by color only", "preserve row-major spatial order"],
    "distinct3_smallest": ["sort by color only", "preserve row-major spatial order"],
    "distinct4_largest": ["sort by color only", "preserve row-major spatial order"],
    "distinct4_smallest": ["sort by color only", "preserve row-major spatial order"],
    "diagonal5": ["merge disconnected cells by color", "preserve row-major spatial order"],
    "equal_area_color_tie": ["sort by color only"],
    "repeated_color_singletons": ["merge disconnected cells by color"],
    "non_rectangular_crop": ["replace crop by filled bbox"],
    "spatial_order_rebuttal": ["preserve row-major spatial order"],
    "bbox_area_rebuttal": ["sort by bounding-box area"],
    "color_only_rebuttal": ["sort by color only"],
    "color_grouping_rebuttal": ["merge disconnected cells by color"],
}

LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that still support named, query-disagreeing rivals."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        if pair["output"] != _solve_grid(pair["input"]):
            reasons.append(f"pair {index} output disagrees with the area-then-color packing rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def _fresh_copy_probe(grid: list[list[int]]) -> list[list[int]]:
    """Small public helper used by focused determinism tests."""
    return deepcopy(grid)
