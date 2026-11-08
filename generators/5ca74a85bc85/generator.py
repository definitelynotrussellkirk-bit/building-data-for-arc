"""Semantic generator for ARC task 5ca74a85bc85.

Find the full-height maroon 9 divider and copy every colored source cell to
its horizontal reflection across that divider, preserving the source cells,
their colors, and the divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "5ca74a85bc85"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "f57d1e04d7d6"
SUMMARY = "Copy the colored source shape across the full-height maroon vertical divider."
INVARIANTS = [
    "background is zero and exactly one full-height maroon 9 divider exists",
    "all non-divider source cells lie on one side of the divider",
    "every reflected destination is in bounds and initially empty",
    "the output preserves sources and divider while adding exact color-preserving reflections",
]

PUBLIC_PROFILES = (
    "public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1",
)
GENERAL_PROFILES = (
    "left_rectangle", "right_rectangle", "left_single_cell", "right_single_cell",
    "left_horizontal_bar", "right_vertical_bar", "multicolor_left", "multicolor_right",
    "boundary_mirror", "near_divider", "multiple_objects_left",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng: each public once and each generalized lesson twice",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_INPUTS = {
    "public_train_1": (
        "00000900000", "04400900000", "04400900000", "00000900000",
        "00000900000", "00000900000", "00000900000", "00000900000",
    ),
    "public_train_2": (
        "0000009000000", "0000009000000", "0000009000000", "0000009000000",
        "0000009003300", "0000009003300", "0000009000000", "0000009000000",
        "0000009000000",
    ),
    "public_train_3": (
        "000090000000", "000090000000", "000090000000", "000090000000",
        "000090000000", "000090000000", "000090011000", "000090011000",
        "000090011000", "000090000000",
    ),
    "public_train_4": (
        "0000090000", "0000090000", "0770090000", "0770090000",
        "0770090000", "0000090000", "0000090000", "0000090000",
    ),
    "public_test_1": (
        "0000009000000", "0000009004400", "0000009004400", "0000009004400",
        "0000009000000", "0000009000000", "0000009000000", "0000009000000",
        "0000009000000",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(cell) for cell in row) for row in rows): profile
    for profile, rows in _PUBLIC_INPUTS.items()
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"], h, w
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], h, w
    return [], h, w


def _components4(cells):
    remaining = set(cells)
    result = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = [start]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(result)


def _classify(info):
    axis = info["divider"]
    sources = info["source_cells"]
    side = info["source_side"]
    reflected_cols = [2 * axis - c for _, c, _ in sources]
    if any(c in (0, info["width"] - 1) for c in reflected_cols):
        return "boundary_mirror"
    if all(abs(c - axis) == 1 for _, c, _ in sources):
        return "near_divider"
    if len(info["source_colors"]) >= 2:
        return "multicolor_left" if side == "left" else "multicolor_right"
    if len(info["source_components"]) >= 2:
        return "multiple_objects_left"
    if len(sources) == 1:
        return "left_single_cell" if side == "left" else "right_single_cell"
    rows = [r for r, _, _ in sources]
    cols = [c for _, c, _ in sources]
    if len(set(rows)) == 1:
        return "left_horizontal_bar"
    if len(set(cols)) == 1:
        return "right_vertical_bar"
    return "left_rectangle" if side == "left" else "right_rectangle"


def _analysis(grid):
    errors, h, w = _validate_grid(grid)
    result = {"errors": errors, "height": h, "width": w, "scene_profile": None}
    if errors:
        return result
    dividers = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(dividers) != 1:
        errors.append("exactly one full-height maroon divider is required")
        return result
    divider = dividers[0]
    sources = tuple((r, c, grid[r][c]) for r in range(h) for c in range(w)
                    if grid[r][c] not in (0, 9))
    if not sources:
        errors.append("at least one colored source cell is required")
    sides = {"left" if c < divider else "right" for _, c, _ in sources}
    if len(sides) != 1:
        errors.append("all source cells must begin on exactly one side of the divider")
    source_side = next(iter(sides), None)
    output = [list(row) for row in grid]
    for r, c, value in sources:
        mirror_col = 2 * divider - c
        if not 0 <= mirror_col < w or mirror_col == divider:
            errors.append("every reflected destination must be in bounds and off the divider")
            continue
        if output[r][mirror_col] != 0:
            errors.append("every reflected destination must initially be empty")
            continue
        output[r][mirror_col] = value
    source_positions = tuple((r, c) for r, c, _ in sources)
    components = _components4(source_positions)
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    info = {
        "divider": divider,
        "source_cells": sources,
        "source_side": source_side,
        "source_colors": tuple(sorted({value for _, _, value in sources})),
        "source_components": components,
        "source_count": len(sources),
        "output": output,
    }
    if profile is None and not errors:
        profile = _classify(result | info)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared divider-reflection lesson")
    if output == [list(row) for row in grid]:
        errors.append("lesson must visibly add at least one reflected cell")
    result.update(info)
    result.update({"scene_profile": profile, "errors": errors})
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _filled_source_bbox(grid):
    """Teaching rival: copy the source's filled monochrome bounding rectangle.

    The first source color is used throughout, including on multicolor inputs,
    so this is a deterministic rule on every declared scene profile. Sparse or
    multicolor demonstrations can refute it. It is not the reference rule.
    """
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    sources = info["source_cells"]
    rows = [r for r, _, _ in sources]
    cols = [c for _, c, _ in sources]
    output = [list(row) for row in grid]
    for r in range(min(rows), max(rows) + 1):
        for c in range(min(cols), max(cols) + 1):
            output[r][2 * info["divider"] - c] = sources[0][2]
    return output


# The shared lesson gate rejects automatic episodes when this shortcut fits
# every demonstration but disagrees with a query. Explicit counts stay diagnostic.
LESSON_COMPETITORS = {"filled_source_bbox": _filled_source_bbox}


def _dimensions(rng, band):
    bounds = {
        "easy": ((7, 9), (9, 11)),
        "medium": ((8, 11), (10, 14)),
        "hard": ((10, 14), (13, 18)),
    }
    (h1, h2), (w1, w2) = bounds[band]
    return rng.randint(h1, h2), rng.randint(w1, w2)


def _blank(h, w, divider):
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r in range(h):
        grid[r][divider] = 9
    return grid


def _paint(grid, cells):
    for r, c, value in cells:
        grid[r][c] = value


def _general_grid(rng, profile, band):
    h, w = _dimensions(rng, band)
    if profile == "boundary_mirror" and w % 2 == 0:
        w += 1
    divider = (w - 1) // 2 if profile == "boundary_mirror" else rng.randint(3, w - 4)
    span = min(divider, w - 1 - divider)
    roomy_profiles = {"left_rectangle", "right_rectangle", "left_horizontal_bar",
                       "multicolor_left", "multicolor_right", "multiple_objects_left"}
    if profile in roomy_profiles and span < 4:
        divider = (w - 1) // 2
        span = min(divider, w - 1 - divider)
    color = rng.choice((1, 2, 3, 4, 5, 6, 7, 8))
    grid = _blank(h, w, divider)
    if profile == "boundary_mirror":
        side = rng.choice(("left", "right"))
        col = 0 if side == "right" else w - 1
        source_col = 2 * divider - col
        row0 = rng.randint(1, h - 4)
        cells = [(row0 + dr, source_col, color) for dr in range(3)]
    elif profile == "near_divider":
        side = rng.choice((-1, 1))
        source_col = divider + side
        row0 = rng.randint(1, h - 4)
        cells = [(row0 + dr, source_col, color) for dr in range(3)]
    elif profile in {"left_single_cell", "right_single_cell"}:
        sign = -1 if profile.startswith("left") else 1
        distance = rng.randint(2, max(2, span - 1))
        cells = [(rng.randrange(h), divider + sign * distance, color)]
    elif profile == "left_horizontal_bar":
        length = min(rng.randint(3, 5), span - 1)
        distance = rng.randint(length, span - 1)
        right_col = divider - distance + length - 1
        row = rng.randrange(h)
        cells = [(row, right_col - dc, color) for dc in range(length)]
    elif profile == "right_vertical_bar":
        distance = rng.randint(2, max(2, span - 1))
        row0 = rng.randint(0, h - 4)
        cells = [(row0 + dr, divider + distance, color) for dr in range(rng.randint(3, 4))]
    elif profile in {"multicolor_left", "multicolor_right"}:
        sign = -1 if profile.endswith("left") else 1
        distance = max(2, span - 2)
        col = divider + sign * distance
        row0 = rng.randint(0, h - 3)
        other = 1 + color % 8
        step = -sign
        cells = [(row0, col, color), (row0 + 1, col, other), (row0 + 1, col + step, color)]
    elif profile == "multiple_objects_left":
        far = max(2, span - 1)
        cells = [(1, divider - far, color), (h - 2, divider - far, color),
                 (h // 2, divider - 2, color)]
    elif profile in {"left_rectangle", "right_rectangle"}:
        sign = -1 if profile.startswith("left") else 1
        rect_h = rng.randint(2, min(4, h - 2))
        rect_w = rng.randint(2, min(3, span - 2))
        row0 = rng.randint(0, h - rect_h)
        nearest = divider + sign * 2
        cols = [nearest + sign * dc for dc in range(rect_w)]
        cells = [(row0 + dr, c, color) for dr in range(rect_h) for c in cols]
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    _paint(grid, cells)
    return grid


def _public_grid(profile):
    return [[int(cell) for cell in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                      difficulty=difficulty, overrides=overrides)
    weighted_profiles = PUBLIC_PROFILES + GENERAL_PROFILES + GENERAL_PROFILES
    profile = context.draw_choice("scene_profile", list(weighted_profiles))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
