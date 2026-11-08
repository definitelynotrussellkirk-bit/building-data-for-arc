"""Generator for arc_puzzle_bank_nineteenth21:E130.

Rule: erase same-color 4-connected components of size one; preserve every
same-color 4-connected component of size two or more.

The first three default samples deliberately form a compact lesson:
  0. a singleton touches a differently colored survivor (color matters),
  1. two same-color singletons touch only diagonally (4-connectivity matters),
  2. an ordinary separated scene (the simple rule remains visible).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b765f6c9ebeb"
VERSION = "3.0.0"
TASK_ID = "b765f6c9ebeb"
RULE_HASH = "22554e067bcc"

SUMMARY = (
    "Zero-background grids containing both singleton and multi-cell same-color "
    "4-connected components.  Singletons are erased; larger components are "
    "preserved.  A three-sample schedule covers canonical 5-row shape/palette "
    "profiles and includes mixed-color cardinal contact plus same-color diagonal "
    "singletons, refuting multicolor-component and 8-connectivity shortcuts."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "at least one same-color 4-connected singleton component",
    "at least one same-color 4-connected component of size at least 2",
    "component identity is color-sensitive and uses 4-connectivity",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = ("color_touch", "diagonal_same_color", "separated")
DEGENERATE_TEXTURES = ("no_singletons", "no_objects", "all_singletons")
SCHEDULE_PROFILES = HELPFUL_TEXTURES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-profile schedule 5..8",
        "valid": "5..8",
    },
    "grid_w": {
        "type": "int",
        "default": "six-profile schedule 5..10",
        "valid": "5..10",
    },
    "singletons": {
        "type": "int",
        "default": "six-profile schedule 2..3",
        "valid": "2..3",
    },
    "objects": {
        "type": "int",
        "default": "six-profile schedule 2..3",
        "valid": "2..3",
    },
    "palette_kind": {
        "type": "str",
        "default": "six-profile schedule",
        "valid": "default|warm|cool|varied",
    },
    "texture": {
        "type": "str",
        "default": "sample_index modulo 3",
        "valid": "color_touch|diagonal_same_color|separated",
    },
}

_DEFAULT_PROFILES = (
    # These first three exactly cover the canonical (h, w, palette-size)
    # profiles reported by canonical_profile_gate.
    {"grid_h": 5, "grid_w": 6, "singletons": 2, "objects": 3, "palette_kind": "default"},
    {"grid_h": 5, "grid_w": 5, "singletons": 2, "objects": 3, "palette_kind": "warm"},
    {"grid_h": 5, "grid_w": 7, "singletons": 2, "objects": 3, "palette_kind": "cool"},
    # Broader profiles exercise every declared numeric boundary in ordinary draws.
    {"grid_h": 6, "grid_w": 8, "singletons": 3, "objects": 2, "palette_kind": "varied"},
    {"grid_h": 7, "grid_w": 9, "singletons": 3, "objects": 3, "palette_kind": "warm"},
    {"grid_h": 8, "grid_w": 10, "singletons": 3, "objects": 3, "palette_kind": "cool"},
)

_PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (1, 2, 4, 7),
    "cool": (3, 5, 8, 9),
    "varied": (1, 3, 4, 6, 8),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_EIGHT = _CARDINAL + _DIAGONAL

# Normalized connected shapes.  Small boards intentionally use the small end of
# this bank; larger/harder boards unlock the richer shapes.
_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
)


def _grid_error(grid: object) -> str | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return "empty or non-grid value"
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return f"grid dimensions outside ARC bounds: {h}x{w}"
    for row in grid:
        if not isinstance(row, list) or len(row) != w:
            return "ragged grid"
        if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9 for v in row):
            return "grid contains a non-integer or out-of-range color"
    return None


def _components(
    grid: list[list[int]],
    *,
    connectivity: int = 4,
    color_sensitive: bool = True,
) -> list[dict[str, object]]:
    """Return nonzero connected components in row-major discovery order."""
    h, w = len(grid), len(grid[0])
    deltas = _CARDINAL if connectivity == 4 else _EIGHT
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in deltas:
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if value == 0:
                        continue
                    if color_sensitive and value != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            result.append({"color": color, "cells": tuple(cells), "size": len(cells)})
    return result


def _component_index(grid: list[list[int]]) -> tuple[list[dict[str, object]], dict[tuple[int, int], int]]:
    comps = _components(grid)
    index: dict[tuple[int, int], int] = {}
    for i, comp in enumerate(comps):
        for cell in comp["cells"]:  # type: ignore[index]
            index[cell] = i
    return comps, index


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small Python oracle used only by tests/semantic diagnostics."""
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    out = full_grid(len(grid), len(grid[0]), 0)
    for comp in _components(grid):
        if comp["size"] <= 1:
            continue
        for r, c in comp["cells"]:  # type: ignore[index]
            out[r][c] = grid[r][c]
    return out


def _multicolor_4_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: color-blind 4-connected nonzero components."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for comp in _components(grid, connectivity=4, color_sensitive=False):
        if comp["size"] <= 1:
            continue
        for r, c in comp["cells"]:  # type: ignore[index]
            out[r][c] = grid[r][c]
    return out


def _same_color_8_rival(grid: list[list[int]]) -> list[list[int]]:
    """Wrong shortcut: same-color 8-connected components."""
    out = full_grid(len(grid), len(grid[0]), 0)
    for comp in _components(grid, connectivity=8, color_sensitive=True):
        if comp["size"] <= 1:
            continue
        for r, c in comp["cells"]:  # type: ignore[index]
            out[r][c] = grid[r][c]
    return out


def _identity_rival(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _witness_keep_and_erase(grid: list[list[int]]) -> bool:
    comps = _components(grid)
    return any(c["size"] == 1 for c in comps) and any(c["size"] > 1 for c in comps)


def _witness_mixed_color_contact(grid: list[list[int]]) -> bool:
    comps, owner = _component_index(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w) or grid[nr][nc] in (0, grid[r][c]):
                    continue
                left = comps[owner[(r, c)]]
                right = comps[owner[(nr, nc)]]
                if {left["size"] == 1, right["size"] == 1} == {False, True}:
                    return True
    return False


def _witness_same_color_diagonal_singletons(grid: list[list[int]]) -> bool:
    comps, _ = _component_index(grid)
    singles = [comp for comp in comps if comp["size"] == 1]
    for i, left in enumerate(singles):
        lr, lc = left["cells"][0]  # type: ignore[index]
        for right in singles[i + 1 :]:
            if right["color"] != left["color"]:
                continue
            rr, rc = right["cells"][0]  # type: ignore[index]
            if abs(lr - rr) == 1 and abs(lc - rc) == 1:
                return True
    return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "keep_and_erase": _witness_keep_and_erase,
    "mixed_color_contact": _witness_mixed_color_contact,
    "same_color_diagonal_singletons": _witness_same_color_diagonal_singletons,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _identity_rival,
    "multicolor_4": _multicolor_4_rival,
    "same_color_8": _same_color_8_rival,
}
WITNESS_RIVALS = {
    "keep_and_erase": ("identity",),
    "mixed_color_contact": ("multicolor_4",),
    "same_color_diagonal_singletons": ("same_color_8",),
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the canonical manifold while requiring both rule branches."""
    error = _grid_error(grid)
    if error:
        return [error]
    comps = _components(grid)
    singles = sum(comp["size"] == 1 for comp in comps)
    multis = sum(comp["size"] > 1 for comp in comps)
    errors: list[str] = []
    if singles < 1:
        errors.append("no singleton component present; erase branch is absent")
    if multis < 1:
        errors.append("no multi-cell component present; preserve branch is absent")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    comps = _components(grid)
    return {
        "singletons": sum(comp["size"] == 1 for comp in comps),
        "objects": sum(comp["size"] > 1 for comp in comps),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    del seed, difficulty
    return HELPFUL_TEXTURES[sample_index % len(HELPFUL_TEXTURES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Require a three-example lesson to refute both connectivity shortcuts."""
    del query
    inputs = []
    for demo in demos:
        if isinstance(demo, dict) and "input" in demo:
            inputs.append(demo["input"])
        elif isinstance(demo, (tuple, list)) and demo:
            inputs.append(demo[0])
        else:
            return ["lesson contains an unrecognized demo representation"]
    errors = []
    if not any(_witness_mixed_color_contact(grid) for grid in inputs):
        errors.append("no demo refutes color-blind multicolor components")
    if not any(_witness_same_color_diagonal_singletons(grid) for grid in inputs):
        errors.append("no demo refutes 8-connected same-color components")
    if not all(_witness_keep_and_erase(grid) for grid in inputs):
        errors.append("a demo omits either the erase or preserve branch")
    return errors


def _cells_at(top: int, left: int, shape: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {(top + r, left + c) for r, c in shape}


def _can_place(
    grid: list[list[int]],
    cells: set[tuple[int, int]],
    color: int,
    *,
    allow_mixed_touch: bool,
) -> bool:
    h, w = len(grid), len(grid[0])
    if any(not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0 for r, c in cells):
        return False
    for r, c in cells:
        for dr, dc in _CARDINAL:
            neighbor = (r + dr, c + dc)
            if neighbor in cells:
                continue
            nr, nc = neighbor
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            value = grid[nr][nc]
            if value == 0:
                continue
            if value == color or not allow_mixed_touch:
                return False
    return True


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for r, c in cells:
        grid[r][c] = color


def _color_touch_motifs(h: int, w: int):
    seen = set()
    for shape in (_SHAPES[0], _SHAPES[1]):
        sh = max(r for r, _ in shape)
        sw = max(c for _, c in shape)
        for top in range(h - sh):
            for left in range(w - sw):
                obj = _cells_at(top, left, shape)
                for r, c in obj:
                    for dr, dc in _CARDINAL:
                        singleton = (r + dr, c + dc)
                        if singleton in obj or not (0 <= singleton[0] < h and 0 <= singleton[1] < w):
                            continue
                        key = (frozenset(obj), singleton)
                        if key not in seen:
                            seen.add(key)
                            yield obj, {singleton}


def _diagonal_pairs(h: int, w: int):
    for r in range(h - 1):
        for c in range(w - 1):
            yield {(r, c), (r + 1, c + 1)}
            yield {(r, c + 1), (r + 1, c)}


def _component_colors(
    rng,
    palette_kind: str,
    object_count: int,
    singleton_count: int,
    texture: str,
) -> tuple[list[int], list[int]]:
    palette = list(_PALETTES[palette_kind])
    rng.shuffle(palette)
    if texture == "diagonal_same_color":
        pair_color = palette[0]
        object_colors = [palette[(i + 1) % len(palette)] for i in range(object_count)]
        singleton_colors = [pair_color, pair_color]
        singleton_colors.extend(
            palette[(object_count + i + 1) % len(palette)]
            for i in range(singleton_count - 2)
        )
        return object_colors, singleton_colors
    sequence = [palette[i % len(palette)] for i in range(object_count + singleton_count)]
    return sequence[:object_count], sequence[object_count:]


def _shape_candidates(max_size: int):
    return [shape for shape in _SHAPES if len(shape) <= max_size]


def _place_object(
    grid: list[list[int]],
    rng,
    color: int,
    max_size: int,
    *,
    allow_mixed_touch: bool,
) -> bool:
    h, w = len(grid), len(grid[0])
    shapes = _shape_candidates(max_size)
    rng.shuffle(shapes)
    placements: list[set[tuple[int, int]]] = []
    for shape in shapes:
        sh = max(r for r, _ in shape)
        sw = max(c for _, c in shape)
        if sh >= h or sw >= w:
            continue
        for top in range(h - sh):
            for left in range(w - sw):
                cells = _cells_at(top, left, shape)
                if _can_place(grid, cells, color, allow_mixed_touch=allow_mixed_touch):
                    placements.append(cells)
    if not placements:
        return False
    cells = rng.choice(placements)
    _paint(grid, cells, color)
    return True


def _place_singleton(
    grid: list[list[int]],
    rng,
    color: int,
    *,
    allow_mixed_touch: bool,
) -> bool:
    candidates = [
        {(r, c)}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if _can_place(grid, {(r, c)}, color, allow_mixed_touch=allow_mixed_touch)
    ]
    if not candidates:
        return False
    _paint(grid, rng.choice(candidates), color)
    return True


def _max_object_size(difficulty, h: int, w: int, texture: str) -> int:
    cap = {None: 4, "easy": 3, "medium": 4, "hard": 5}[difficulty]
    if h * w <= 35:
        cap = min(cap, 3)
    if texture == "separated" and h * w <= 42:
        cap = min(cap, 2)
    return cap


def _draw_from_degenerate(name: str) -> list[list[int]]:
    g = full_grid(5, 7, 0)
    if name == "no_singletons":
        for r, c in ((1, 1), (1, 2), (2, 1)):
            g[r][c] = 4
        for r, c in ((3, 4), (3, 5)):
            g[r][c] = 6
    elif name == "no_objects":
        for r, c, color in ((0, 1, 4), (1, 5, 6), (3, 2, 3), (4, 6, 8)):
            g[r][c] = color
    elif name == "all_singletons":
        for r, c, color in ((0, 0, 1), (0, 3, 2), (2, 1, 3), (2, 5, 4), (4, 3, 5)):
            g[r][c] = color
    else:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        extras = sorted(key for key, value in overrides.items() if key != "texture" and value is not None)
        if extras:
            raise ValueError(
                "degenerate texture cannot be combined with ordinary overrides: "
                + ", ".join(extras)
            )
        return _draw_from_degenerate(requested_texture)

    profile = _DEFAULT_PROFILES[sample_index % len(_DEFAULT_PROFILES)]
    effective = dict(overrides)
    for key, value in profile.items():
        if effective.get(key) is None:
            effective[key] = value
    if effective.get("texture") is None:
        effective["texture"] = schedule_profile(seed, sample_index, difficulty)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 5, 8)
    w = ctx.draw_int("grid_w", 5, 10)
    singleton_target = ctx.draw_int("singletons", 2, 3)
    object_target = ctx.draw_int("objects", 2, 3)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    rng = ctx.draw_rng("layout")
    max_size = _max_object_size(difficulty, h, w, texture)

    for _attempt in range(120):
        grid = full_grid(h, w, 0)
        object_colors, singleton_colors = _component_colors(
            rng, palette_kind, object_target, singleton_target, texture
        )
        object_start = 0
        singleton_start = 0
        allow_mixed_touch = texture != "separated"

        if texture == "color_touch":
            motifs = list(_color_touch_motifs(h, w))
            rng.shuffle(motifs)
            survivor_cells, singleton_cells = motifs[0]
            if object_colors[0] == singleton_colors[0]:
                # Every palette has at least four colors, so a deterministic
                # different choice is always available.
                singleton_colors[0] = next(c for c in _PALETTES[palette_kind] if c != object_colors[0])
            _paint(grid, survivor_cells, object_colors[0])
            _paint(grid, singleton_cells, singleton_colors[0])
            object_start = 1
            singleton_start = 1
        elif texture == "diagonal_same_color":
            pairs = list(_diagonal_pairs(h, w))
            rng.shuffle(pairs)
            pair = pairs[0]
            cells = sorted(pair)
            _paint(grid, {cells[0]}, singleton_colors[0])
            _paint(grid, {cells[1]}, singleton_colors[1])
            singleton_start = 2

        failed = False
        for color in object_colors[object_start:]:
            if not _place_object(
                grid,
                rng,
                color,
                max_size,
                allow_mixed_touch=allow_mixed_touch,
            ):
                failed = True
                break
        if failed:
            continue
        for color in singleton_colors[singleton_start:]:
            if not _place_singleton(
                grid,
                rng,
                color,
                allow_mixed_touch=allow_mixed_touch,
            ):
                failed = True
                break
        if failed:
            continue

        observed = observe_overrides(grid)
        if observed != {"singletons": singleton_target, "objects": object_target}:
            continue
        if self_check(grid, difficulty=difficulty):
            continue
        if texture == "color_touch" and not _witness_mixed_color_contact(grid):
            continue
        if texture == "diagonal_same_color" and not _witness_same_color_diagonal_singletons(grid):
            continue
        return grid

    raise ValueError(
        "could not realize requested component counts/texture on "
        f"{h}x{w}: objects={object_target}, singletons={singleton_target}, "
        f"texture={texture!r}"
    )
