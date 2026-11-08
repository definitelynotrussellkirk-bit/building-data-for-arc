"""Semantic generator for ARC task bb43febb / 70205357c60a.

The authoritative rule is local: a color-5 cell becomes color 2 exactly when
all four cardinal neighbours are also color 5.  Every other cell is preserved.

The curriculum deliberately mixes solid and notched blocks.  The notches make
some color-5 cells lie strictly inside a component bounding box while lacking
one required neighbour, so they remain 5.  That is the decisive counterexample
to the tempting but wrong shortcut "fill every rectangle/bounding-box interior".
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70205357c60a"
TASK_ID = "70205357c60a"
VERSION = "3.0.0"
RULE_HASH = "24d0faa4acb9"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "On a 0-background grid, recolor a 5 to 2 iff its up, down, left, and "
    "right neighbours are all 5; preserve every other cell. Lessons cycle "
    "through solid rectangles, one-cell border notches, and two-cell deep "
    "notches. The notched scenes retain bbox-interior 5s beside the notch, "
    "refuting rectangle-fill and bbox-interior shortcuts."
)

INVARIANTS = [
    "inputs use only background 0 and object color 5; color 2 is output-only",
    "every ordinary scene has two to four separated 4-connected components",
    "every component contains at least one 5 with four cardinal 5-neighbours",
    "every scene also contains 5s that lack at least one required neighbour",
    "scene profile is observable as solid, single-notch, or deep-notch components",
]

SCENE_PROFILES = (
    "solid_rectangles",
    "single_notches",
    "deep_notches",
)
SCHEDULE_PROFILES = SCENE_PROFILES
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 9..18 with every-third-sample 10x10 canonical anchor",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..20 with every-third-sample 10x10 canonical anchor",
        "valid": "9..20",
    },
    "n_components": {
        "type": "int",
        "default": "difficulty-aware 2..4; canonical anchors pin 2",
        "valid": "2..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index cycle solid|single-notch|deep-notch",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be within ARC bounds 1..30"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integer colors 0..9"]
    return []


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror used only for tests; the canonical Racket rule is authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    output = [list(row) for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 5:
                continue
            if (
                row > 0
                and row + 1 < height
                and col > 0
                and col + 1 < width
                and grid[row - 1][col] == 5
                and grid[row + 1][col] == 5
                and grid[row][col - 1] == 5
                and grid[row][col + 1] == 5
            ):
                output[row][col] = 2
    return output


def _components(grid: list[list[int]]) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    }
    result: list[tuple[tuple[int, int], ...]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for dr, dc in _DIR4:
                neighbour = (row + dr, col + dc)
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: cells[0])


def _component_facts(cells: tuple[tuple[int, int], ...]) -> dict[str, Any]:
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    height, width = bottom - top + 1, right - left + 1
    normalized = {(row - top, col - left) for row, col in cells}
    box = {(row, col) for row in range(height) for col in range(width)}
    missing = box - normalized

    profile = "other"
    if not missing:
        profile = "solid_rectangles"
    elif len(missing) == 1:
        row, col = next(iter(missing))
        on_edge = row in (0, height - 1) or col in (0, width - 1)
        at_corner = row in (0, height - 1) and col in (0, width - 1)
        if on_edge and not at_corner:
            profile = "single_notches"
    elif len(missing) == 2:
        first, second = tuple(missing)
        adjacent = abs(first[0] - second[0]) + abs(first[1] - second[1]) == 1
        edge = [
            point
            for point in missing
            if point[0] in (0, height - 1) or point[1] in (0, width - 1)
        ]
        interior = [
            point
            for point in missing
            if 0 < point[0] < height - 1 and 0 < point[1] < width - 1
        ]
        if adjacent and len(edge) == 1 and len(interior) == 1:
            er, ec = edge[0]
            ir, ic = interior[0]
            aligned = er == ir or ec == ic
            if aligned:
                profile = "deep_notches"

    return {
        "cells": cells,
        "cell_set": set(cells),
        "bbox": (top, left, height, width),
        "profile": profile,
        "missing": tuple(sorted(missing)),
    }


def _analysis(grid: list[list[int]]) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    components = [_component_facts(cells) for cells in _components(grid)]
    active: list[tuple[int, int]] = []
    inactive: list[tuple[int, int]] = []
    protected_bbox_interior: list[tuple[int, int]] = []
    for component in components:
        top, left, box_h, box_w = component["bbox"]
        for row, col in component["cells"]:
            is_active = (
                row > 0
                and row + 1 < height
                and col > 0
                and col + 1 < width
                and all(grid[row + dr][col + dc] == 5 for dr, dc in _DIR4)
            )
            (active if is_active else inactive).append((row, col))
            if (
                not is_active
                and top < row < top + box_h - 1
                and left < col < left + box_w - 1
            ):
                protected_bbox_interior.append((row, col))

    profiles = {component["profile"] for component in components}
    scene_profile = next(iter(profiles)) if len(profiles) == 1 else None
    output = rule_mirror(grid)
    return {
        "errors": [],
        "height": height,
        "width": width,
        "components": components,
        "n_components": len(components),
        "scene_profile": scene_profile,
        "active": tuple(active),
        "inactive": tuple(inactive),
        "protected_bbox_interior": tuple(protected_bbox_interior),
        "output": output,
        "palette": {value for row in grid for value in row},
    }


def observe_overrides(grid: list[list[int]]) -> dict[str, Any]:
    info = _analysis(grid)
    if info.get("errors") or info.get("scene_profile") not in SCENE_PROFILES:
        return {}
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "n_components": info["n_components"],
        "scene_profile": info["scene_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    info = _analysis(grid)
    errors = list(info.get("errors", []))
    if errors:
        return errors
    if info["palette"] - {0, 5}:
        errors.append("input grammar permits only background 0 and object color 5")
    if 0 not in info["palette"]:
        errors.append("scene must retain visible background 0")
    if not 2 <= info["n_components"] <= 4:
        errors.append("scene must contain two to four separated color-5 components")
    if any(len(component["cells"]) < 5 for component in info["components"]):
        errors.append("every color-5 component must contain at least five cells")
    if not info["active"]:
        errors.append("identity lesson: no 5 has all four cardinal 5-neighbours")
    if not info["inactive"]:
        errors.append("missing unchanged branch: every 5 would transform")
    for index, component in enumerate(info["components"]):
        if not any(cell in info["active"] for cell in component["cells"]):
            errors.append(f"component {index} has no positive rule witness")
    if info["scene_profile"] not in SCENE_PROFILES:
        errors.append("components do not share a declared solid/notch scene profile")

    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        requested.update(meta.get("overrides") or {})
        for name in AXES:
            if name in meta:
                requested[name] = meta[name]
    observed = observe_overrides(grid)
    for name, value in requested.items():
        if name in AXES and value is not None and observed.get(name) != value:
            errors.append(
                f"override {name}={value!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    info = _analysis(grid)
    profile = (info["height"], info["width"], len(info["palette"]))
    if profile != (10, 10, 2):
        errors.append(f"profile {profile} differs from canonical (10, 10, 2)")
    if info["n_components"] != 2:
        errors.append("canonical scenes contain exactly two color-5 components")
    return errors


MIN_STRICT_FRAC = 0.15


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _draw_int_axis(ctx, label: str, lo: int, hi: int, fixed: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if fixed is not None:
        return ctx.draw_int(label, fixed, fixed)
    return ctx.draw_int_diff(label, lo, hi)


def _draw_profile(ctx, sample_index: int) -> str:
    if "scene_profile" in ctx.overrides and ctx.overrides["scene_profile"] is not None:
        return ctx.draw_choice("scene_profile", SCENE_PROFILES)
    scheduled = schedule_profile(ctx.seed, sample_index, ctx.difficulty)
    return ctx.draw_choice("scene_profile", (scheduled,))


def _slots(height: int, width: int, count: int, rng) -> list[tuple[int, int, int, int]]:
    """Return count disjoint slots, each at least 4x4, with a blank separator."""
    if count == 2 and rng.random() < 0.5:
        split = height // 2
        slots = [(0, 0, split, width), (split + 1, 0, height, width)]
    elif count == 2:
        split = width // 2
        slots = [(0, 0, height, split), (0, split + 1, height, width)]
    else:
        row_split = height // 2
        col_split = width // 2
        slots = [
            (0, 0, row_split, col_split),
            (0, col_split + 1, row_split, width),
            (row_split + 1, 0, height, col_split),
            (row_split + 1, col_split + 1, height, width),
        ]
        rng.shuffle(slots)
        slots = slots[:count]
    if any(r1 - r0 < 4 or c1 - c0 < 4 for r0, c0, r1, c1 in slots):
        raise ValueError("requested grid/count combination cannot host 4x4 components")
    return slots


def _notch_cells(height: int, width: int, profile: str, rng) -> set[tuple[int, int]]:
    cells = {(row, col) for row in range(height) for col in range(width)}
    if profile == "solid_rectangles":
        return cells
    side = rng.choice(("top", "bottom", "left", "right"))
    if side in {"top", "bottom"}:
        col = rng.randint(1, width - 2)
        row = 0 if side == "top" else height - 1
        cells.remove((row, col))
        if profile == "deep_notches":
            inner_row = 1 if side == "top" else height - 2
            cells.remove((inner_row, col))
    else:
        row = rng.randint(1, height - 2)
        col = 0 if side == "left" else width - 1
        cells.remove((row, col))
        if profile == "deep_notches":
            inner_col = 1 if side == "left" else width - 2
            cells.remove((row, inner_col))
    return cells


def _draw_component(grid, slot, profile: str, rng) -> None:
    r0, c0, r1, c1 = slot
    slot_h, slot_w = r1 - r0, c1 - c0
    min_h = max(4, slot_h - 2)
    min_w = max(4, slot_w - 2)
    shape_h = rng.randint(min_h, slot_h)
    shape_w = rng.randint(min_w, slot_w)
    top = rng.randint(r0, r1 - shape_h)
    left = rng.randint(c0, c1 - shape_w)
    for dr, dc in _notch_cells(shape_h, shape_w, profile, rng):
        grid[top + dr][left + dc] = 5


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_components"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (bool is not accepted)")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, or hard")
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    numeric_overridden = any(
        name in overrides and overrides[name] is not None
        for name in ("grid_h", "grid_w", "n_components")
    )
    canonical_anchor = not numeric_overridden and sample_index % 3 == 0
    height = _draw_int_axis(ctx, "grid_h", 9, 18, 10 if canonical_anchor else None)
    width = _draw_int_axis(ctx, "grid_w", 9, 20, 10 if canonical_anchor else None)
    count = _draw_int_axis(ctx, "n_components", 2, 4, 2 if canonical_anchor else None)
    profile = _draw_profile(ctx, sample_index)

    rng = ctx.draw_rng("layout")
    grid = full_grid(height, width, 0)
    for slot in _slots(height, width, count, rng):
        _draw_component(grid, slot, profile, rng)
    return grid


def _bbox_interior_rival(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _components(grid):
        top = min(row for row, _ in component)
        bottom = max(row for row, _ in component)
        left = min(col for _, col in component)
        right = max(col for _, col in component)
        for row, col in component:
            if top < row < bottom and left < col < right:
                output[row][col] = 2
    return output


def _solid_rectangle_only_rival(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for component in _components(grid):
        facts = _component_facts(component)
        if facts["profile"] != "solid_rectangles":
            continue
        for row, col in component:
            top, left, height, width = facts["bbox"]
            if top < row < top + height - 1 and left < col < left + width - 1:
                output[row][col] = 2
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "bbox_interior_fill": _bbox_interior_rival,
    "solid_rectangle_only": _solid_rectangle_only_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _safe_analysis(grid) -> dict[str, Any]:
    try:
        return _analysis(grid)
    except Exception:
        return {"errors": ["analysis failed"]}


def _profile_is(name: str) -> Callable[[list[list[int]]], bool]:
    return lambda grid: _safe_analysis(grid).get("scene_profile") == name


def _has_protected_bbox_interior(grid) -> bool:
    return bool(_safe_analysis(grid).get("protected_bbox_interior"))


def _rule_fires_and_preserves(grid) -> bool:
    info = _safe_analysis(grid)
    return bool(info.get("active") and info.get("inactive"))


SEMANTIC_WITNESSES = {
    # Only discriminative witnesses belong here. Canonical-scale support and
    # positive/negative rule branches are enforced by strict_canonical_like,
    # self_check, and the exact three-profile schedule instead of being weak
    # presence-only witnesses.
    "single_notches": _profile_is("single_notches"),
    "deep_notches": _profile_is("deep_notches"),
    "protected_bbox_interior_5": _has_protected_bbox_interior,
}
WITNESS_RIVALS = {
    "single_notches": ["solid_rectangle_only"],
    "deep_notches": ["solid_rectangle_only", "bbox_interior_fill"],
    "protected_bbox_interior_5": ["bbox_interior_fill"],
}


def lesson_identifiable(demos, query) -> list[str]:
    findings: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            findings.append(f"pair {index} is malformed")
            continue
        if rule_mirror(pair["input"]) != [list(row) for row in pair["output"]]:
            findings.append(f"pair {index} output disagrees with the four-neighbour rule")
    if findings:
        return findings

    profiles = {_analysis(pair["input"])["scene_profile"] for pair in demos}
    missing = set(SCENE_PROFILES) - profiles
    if missing:
        findings.append(f"demos omit scheduled profile(s): {sorted(missing)}")
    if not any(_has_protected_bbox_interior(pair["input"]) for pair in demos):
        findings.append("demos permit the bbox-interior-fill shortcut")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            findings.append(f"demos do not refute competitor {name!r}")
    return findings
