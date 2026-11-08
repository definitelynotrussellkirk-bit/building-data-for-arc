"""Semantic generator for ``32169a05c213`` — pack objects by cell count.

The authoritative rule extracts every non-zero 4-connected component, crops
it to its bounding box, sorts by ``(cell_count, color, top_row, left_col)``,
and packs the crops left-to-right, top-aligned, with one zero column between
neighbors.  Canonical demonstrations contain size ties, so the color tie-break
is a real branch rather than a degenerate case.

This generator keeps half of its ordinary schedule on exact canonical
morphology while using the other profiles to refute scan-order, color-only,
bounding-box-area, descending-size, solid-bbox, alignment, and gap shortcuts.
Every four consecutive demonstrations visit all four semantic profiles.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "32169a05c213"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
# Re-pinned after the comment-preserving authority synchronization below.
RULE_HASH = "4e4923071f2f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A zero-background grid contains exactly three separated monochrome "
    "objects. Crop each object to its own bounding box, sort the crops by "
    "occupied cell count ascending; ties are broken by color ascending, then "
    "original top-left position. Pack the crops left-to-right, top-aligned, "
    "with exactly one zero column between neighboring crops, preserving the "
    "object shapes and colors."
)

INVARIANTS = [
    "background is 0 and every object is a 4-connected monochrome component",
    "exactly three components occupy the generated/canonical teaching grammar",
    "different components are spatially separated and generated colors are distinct",
    "output order is ascending occupied-cell count with color as the visible tie-break",
    "each bbox crop is preserved exactly, top-aligned, with one zero-column gap",
]

COUNTER_HYPOTHESES = [
    "pack objects in row-major input scan order",
    "sort all objects by color and ignore occupied-cell count",
    "sort tied objects only by stable scan order and ignore the color tie-break",
    "sort by bounding-box area instead of occupied-cell count",
    "sort largest-to-smallest",
    "replace each crop by a solid bounding-box rectangle",
    "bottom-align shorter crops",
    "remove the one-column separators",
    "memorize fixed canonical positions, dimensions, or colors",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "profile-linked; canonical anchors plus 11..12 generalization",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "profile-linked; canonical anchors plus 14..15 generalization",
        "valid": "11..15",
    },
    "scene_profile": {
        "type": "str",
        "default": "four-profile deterministic curriculum schedule",
        "valid": "canonical_tie_344|canonical_tie_334|bbox_area_conflict|distinct_size_conflict",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)

SCHEDULE_PROFILES = (
    "canonical_tie_344",
    "canonical_tie_334",
    "bbox_area_conflict",
    "distinct_size_conflict",
)
_SCENE_PROFILES = SCHEDULE_PROFILES
_PROFILE_SIZES = {
    "canonical_tie_344": (3, 4, 4),
    "canonical_tie_334": (3, 3, 4),
    "bbox_area_conflict": (3, 5, 6),
    "distinct_size_conflict": (2, 4, 6),
}
_PROFILE_BY_SIZES = {tuple(sorted(v)): k for k, v in _PROFILE_SIZES.items()}
_CANONICAL_DIMENSIONS = {(9, 11), (9, 12), (10, 12), (10, 13)}
_CANONICAL_SIZE_SETS = {(3, 4, 4), (3, 3, 4)}

# Normalized 4-connected templates, all at most 3x3.  The 5-cell profile uses
# a 3x3 bbox (area 9) while the larger 6-cell rectangle has bbox area 6; that
# makes bbox-area sorting provably disagree with occupied-cell sorting.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")

    for name, lo, hi in (("grid_h", 9, 12), ("grid_w", 11, 15)):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")

    profile = overrides.get("scene_profile")
    if profile is not None and profile not in _SCENE_PROFILES:
        raise ValueError(
            f"override 'scene_profile'={profile!r} not in {_SCENE_PROFILES}"
        )


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive sample indexes contain every semantic profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(int(seed), f"{TASK_ID}|{sample_index}|dims", VERSION)
    if profile == "canonical_tie_344":
        h, w = rng.choice(((9, 12), (10, 13)))
    elif profile == "canonical_tie_334":
        h, w = rng.choice(((9, 11), (10, 12)))
    elif band == "easy":
        h, w = rng.choice(((9, 12), (10, 13)))
    elif band == "hard":
        h, w = rng.choice(((11, 14), (12, 15)))
    else:
        h, w = rng.choice(((10, 13), (11, 14)))
    return {"grid_h": h, "grid_w": w, "scene_profile": profile}


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = list(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _reflect_shape(
    shape: tuple[tuple[int, int], ...], *, flip_r: bool, flip_c: bool
) -> tuple[tuple[int, int], ...]:
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    return _normalize_shape(
        (
            (height - 1 - r if flip_r else r,
             width - 1 - c if flip_c else c)
            for r, c in shape
        )
    )


def _shape_for(profile: str, identity: int, size: int, rng) -> tuple[tuple[int, int], ...]:
    if profile == "canonical_tie_344":
        base = (
            _SHAPES[3][0],
            _SHAPES[4][0],
            _SHAPES[4][1],
        )[identity]
    elif profile == "canonical_tie_334":
        base = (
            _SHAPES[3][0],
            _SHAPES[3][2],
            _SHAPES[4][0],
        )[identity]
    elif profile == "bbox_area_conflict":
        base = (
            _SHAPES[3][0],
            _SHAPES[5][0],  # bbox area 9
            _SHAPES[6][0],  # bbox area 6 despite larger cell count
        )[identity]
    else:
        base = (
            _SHAPES[2][rng.randrange(len(_SHAPES[2]))],
            _SHAPES[4][1],
            _SHAPES[6][0],
        )[identity]
    if len(base) != size:
        raise AssertionError(f"shape/profile mismatch: {profile} id={identity} size={size}")
    return _reflect_shape(
        base,
        flip_r=bool(rng.randrange(2)),
        flip_c=bool(rng.randrange(2)),
    )


def _component_plan(profile: str, rng) -> tuple[list[dict[str, Any]], list[int]]:
    sizes = list(_PROFILE_SIZES[profile])
    colors = sorted(rng.sample(range(1, 10), 3))
    lo, mid, hi = colors

    # identities are already in authoritative output order.  The explicit scan
    # permutations reverse the equal-size pair in canonical tie profiles so a
    # stable "size only" rival cannot accidentally learn the tie behavior.
    if profile == "canonical_tie_344":
        assigned_colors = [hi, lo, mid]
        scan_order = [2, 0, 1]
    elif profile == "canonical_tie_334":
        assigned_colors = [mid, hi, lo]
        scan_order = [1, 2, 0]
    elif profile == "bbox_area_conflict":
        assigned_colors = [hi, lo, mid]
        scan_order = [2, 1, 0]
    else:
        assigned_colors = [hi, lo, mid]
        scan_order = [1, 2, 0]

    components = [
        {"size": size, "color": color}
        for size, color in zip(sizes, assigned_colors)
    ]
    assert sorted(
        range(3),
        key=lambda i: (components[i]["size"], components[i]["color"]),
    ) == [0, 1, 2]
    return components, scan_order


def _slot_origins(h: int, w: int, rng) -> list[tuple[int, int]]:
    top = 1 if h == 9 else rng.choice((1, 2))
    bottom = h - 4
    left = 1 if w == 11 else rng.choice((1, 2))
    right = w - 4
    slots = [(top, left), (top, right), (bottom, left), (bottom, right)]
    omitted = rng.randrange(4)
    return sorted(slot for i, slot in enumerate(slots) if i != omitted)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_overrides(overrides)
    defaults = _scheduled_defaults(int(seed), int(sample_index), band)
    effective_overrides = {**defaults, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective_overrides,
    )

    h = ctx.draw_int("grid_h", 9, 12)
    w = ctx.draw_int("grid_w", 11, 15)
    profile = ctx.draw_choice("scene_profile", _SCENE_PROFILES)
    layout_rng = ctx.draw_rng("layout")
    components, scan_order = _component_plan(profile, layout_rng)
    slots = _slot_origins(h, w, layout_rng)

    grid = full_grid(h, w, 0)
    for scan_index, identity in enumerate(scan_order):
        spec = components[identity]
        shape_rng = ctx.draw_rng(f"shape_{identity}_{spec['size']}")
        shape = _shape_for(profile, identity, spec["size"], shape_rng)
        r0, c0 = slots[scan_index]
        for rr, cc in shape:
            r, c = r0 + rr, c0 + cc
            if grid[r][c] != 0:
                raise AssertionError("slot layout overlap")
            grid[r][c] = spec["color"]

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, "
                f"observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and Python rule mirror (Racket remains authority)
# ---------------------------------------------------------------------------


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for r, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError:
                return None, [f"row {r} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {r} is not a sequence"]
        if not values:
            return None, ["grid rows must be nonempty"]
        if width is None:
            width = len(values)
        elif len(values) != width:
            return None, ["ragged grid"]
        for c, value in enumerate(values):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return None, [f"invalid ARC color at ({r},{c}): {value!r}"]
        rows.append(values)
    return rows, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
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
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            crop = [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                    "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                    "crop": crop,
                }
            )
    components.sort(key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))
    return components


def _authority_order(components: list[dict[str, Any]]) -> list[int]:
    return sorted(
        range(len(components)),
        key=lambda i: (
            components[i]["size"],
            components[i]["color"],
            components[i]["bbox"][0],
            components[i]["bbox"][1],
        ),
    )


def _pack_components(
    components: list[dict[str, Any]],
    *,
    order: list[int],
    gap: int = 1,
    alignment: str = "top",
    solid_bbox: bool = False,
) -> list[list[int]]:
    selected = [components[i] for i in order]
    if not selected:
        return [[0]]
    height = max(comp["height"] for comp in selected)
    width = sum(comp["width"] for comp in selected) + gap * (len(selected) - 1)
    out = full_grid(height, width, 0)
    left = 0
    for comp in selected:
        if alignment == "top":
            top = 0
        elif alignment == "bottom":
            top = height - comp["height"]
        else:
            raise ValueError(f"unknown alignment: {alignment}")
        if solid_bbox:
            for r in range(comp["height"]):
                for c in range(comp["width"]):
                    out[top + r][left + c] = comp["color"]
        else:
            for r, row in enumerate(comp["crop"]):
                for c, value in enumerate(row):
                    if value != 0:
                        out[top + r][left + c] = value
        left += comp["width"] + gap
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror for focused tests/rivals; canonical Racket is authority."""
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    components = _components(values)
    return _pack_components(components, order=_authority_order(components))


def semantic_observables(grid: Any) -> dict[str, Any]:
    values, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if errors or values is None:
        return result
    components = _components(values)
    sizes = [comp["size"] for comp in components]
    sorted_sizes = tuple(sorted(sizes))
    result.update(
        {
            "grid": values,
            "height": len(values),
            "width": len(values[0]),
            "components": components,
            "n_objects": len(components),
            "sizes_scan_order": sizes,
            "sizes_sorted": sorted_sizes,
            "colors_scan_order": [comp["color"] for comp in components],
            "scene_profile": _PROFILE_BY_SIZES.get(sorted_sizes),
            "authority_order": _authority_order(components) if components else [],
            "has_size_tie": len(set(sizes)) < len(sizes),
            "has_bbox_hole": any(comp["bbox_area"] > comp["size"] for comp in components),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept every canonical input and reject malformed teaching scenes."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors

    h, w = facts["height"], facts["width"]
    if not 9 <= h <= 12 or not 11 <= w <= 15:
        errors.append(f"supported teaching envelope is h=9..12, w=11..15; found {h}x{w}")

    components = facts["components"]
    if len(components) != 3:
        errors.append(f"expected exactly three components, found {len(components)}")
        return errors

    colors = [comp["color"] for comp in components]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be pairwise distinct in this teaching grammar")

    sizes = tuple(sorted(comp["size"] for comp in components))
    if sizes not in _PROFILE_BY_SIZES:
        errors.append(f"unsupported component-size profile: {sizes}")

    for comp in components:
        if comp["height"] > 3 or comp["width"] > 3:
            errors.append(
                f"component crop exceeds 3x3: {comp['height']}x{comp['width']}"
            )

    owner = {
        cell: index
        for index, comp in enumerate(components)
        for cell in comp["cells"]
    }
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append("different components touch, including diagonally")
                    return errors

    if not facts["has_bbox_hole"]:
        errors.append("all crops are solid rectangles; shape-preservation branch is hidden")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact task-linked canonical morphology, not just generic marginals."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if (facts["height"], facts["width"]) not in _CANONICAL_DIMENSIONS:
        reasons.append("dimensions are outside the canonical profile set")
    if facts["sizes_sorted"] not in _CANONICAL_SIZE_SETS:
        reasons.append("component-size multiset is outside canonical tie profiles")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(errors))
    profile = facts.get("scene_profile")
    if profile is None:
        raise ValueError(f"unrecognized generated size profile: {facts['sizes_sorted']}")
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "scene_profile": profile,
    }


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["height"],
        facts["width"],
        facts["scene_profile"],
        tuple(facts["sizes_scan_order"]),
        tuple(facts["colors_scan_order"]),
        tuple((comp["height"], comp["width"], comp["bbox_area"]) for comp in facts["components"]),
    )


# ---------------------------------------------------------------------------
# Named rivals, branch witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------


def _valid_components(grid: Any) -> list[dict[str, Any]]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    components = _components(values)
    if not components:
        raise ValueError("no objects")
    return components


def _rival_input_scan_order(grid):
    comps = _valid_components(grid)
    return _pack_components(comps, order=list(range(len(comps))))


def _rival_color_only(grid):
    comps = _valid_components(grid)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["color"])
    return _pack_components(comps, order=order)


def _rival_size_only_stable_ties(grid):
    comps = _valid_components(grid)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"])
    return _pack_components(comps, order=order)


def _rival_bbox_area(grid):
    comps = _valid_components(grid)
    order = sorted(
        range(len(comps)),
        key=lambda i: (comps[i]["bbox_area"], comps[i]["color"]),
    )
    return _pack_components(comps, order=order)


def _rival_descending_size(grid):
    comps = _valid_components(grid)
    order = sorted(
        range(len(comps)),
        key=lambda i: (-comps[i]["size"], comps[i]["color"]),
    )
    return _pack_components(comps, order=order)


def _rival_solid_bbox(grid):
    comps = _valid_components(grid)
    return _pack_components(
        comps, order=_authority_order(comps), solid_bbox=True
    )


def _rival_bottom_align(grid):
    comps = _valid_components(grid)
    return _pack_components(
        comps, order=_authority_order(comps), alignment="bottom"
    )


def _rival_no_gap(grid):
    comps = _valid_components(grid)
    return _pack_components(comps, order=_authority_order(comps), gap=0)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "input_scan_order": _rival_input_scan_order,
    "color_only": _rival_color_only,
    "size_only_stable_ties": _rival_size_only_stable_ties,
    "bbox_area_ascending": _rival_bbox_area,
    "descending_size": _rival_descending_size,
    "solid_bbox_crops": _rival_solid_bbox,
    "bottom_align": _rival_bottom_align,
    "omit_gap_columns": _rival_no_gap,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _rival_disagrees(name: str, grid: Any) -> bool:
    return not _grids_equal(rule_mirror(grid), SEMANTIC_RIVALS[name](grid))


def _profile_is(name: str, grid: Any) -> bool:
    return semantic_observables(grid).get("scene_profile") == name


def _w_tie_color_break(grid) -> bool:
    facts = semantic_observables(grid)
    return bool(facts.get("has_size_tie")) and _rival_disagrees("size_only_stable_ties", grid)


def _w_bbox_area_conflict(grid) -> bool:
    return _rival_disagrees("bbox_area_ascending", grid)


def _w_top_alignment(grid) -> bool:
    return _rival_disagrees("bottom_align", grid)


def _w_shape_preserved(grid) -> bool:
    return _rival_disagrees("solid_bbox_crops", grid)


SEMANTIC_WITNESSES = {
    "canonical_tie_344_branch": lambda g: _profile_is("canonical_tie_344", g),
    "canonical_tie_334_branch": lambda g: _profile_is("canonical_tie_334", g),
    "bbox_area_conflict_branch": lambda g: _profile_is("bbox_area_conflict", g),
    "distinct_size_conflict_branch": lambda g: _profile_is("distinct_size_conflict", g),
    "scan_order_not_output_order": lambda g: _rival_disagrees("input_scan_order", g),
    "cell_count_precedes_color": lambda g: _rival_disagrees("color_only", g),
    "color_breaks_size_ties": _w_tie_color_break,
    "cell_count_not_bbox_area": _w_bbox_area_conflict,
    "ascending_not_descending": lambda g: _rival_disagrees("descending_size", g),
    "crop_texture_is_preserved": _w_shape_preserved,
    "top_alignment_is_visible": _w_top_alignment,
    "one_column_gaps_are_visible": lambda g: _rival_disagrees("omit_gap_columns", g),
}
BRANCH_WITNESSES = {
    "canonical_tie_344_branch",
    "canonical_tie_334_branch",
    "bbox_area_conflict_branch",
    "distinct_size_conflict_branch",
}
WITNESS_RIVALS = {
    "scan_order_not_output_order": ["input_scan_order"],
    "cell_count_precedes_color": ["color_only"],
    "color_breaks_size_ties": ["size_only_stable_ties"],
    "cell_count_not_bbox_area": ["bbox_area_ascending"],
    "ascending_not_descending": ["descending_size"],
    "crop_texture_is_preserved": ["solid_bbox_crops"],
    "top_alignment_is_visible": ["bottom_align"],
    "one_column_gaps_are_visible": ["omit_gap_columns"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any materialized lesson where a plausible wrong rule survives."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(pair["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} outside rule grammar: {exc}")
            continue
        if not _grids_equal(expected, pair["output"]):
            reasons.append(f"demo {index} output disagrees with pinned rule")

    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query outside rule grammar: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                _grids_equal(competitor(pair["input"]), pair["output"])
                for pair in demos
            )
            if survives and not _grids_equal(competitor(query["input"]), query_answer):
                reasons.append(
                    f"competitor '{name}' fits every demo but changes the query answer"
                )
        except ValueError as exc:
            reasons.append(f"competitor '{name}' raised: {exc}")
    return reasons
