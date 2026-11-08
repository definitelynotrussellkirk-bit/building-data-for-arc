"""Generator for M7 / ``show_holes_only``.

The authoritative rule is broader than the canonical 3x3 examples: for every
monochrome object, find background regions enclosed inside that object's local
bounding box, paint those hole cells with the object's color, and erase every
other cell.  Ordinary draws therefore include non-rectangular enclosures,
multiple-cell holes, multiple holes in one object, multiple enclosing objects
(in both same- and different-color cases), and open/solid distractors that must
not appear in the output.

The seven default scene profiles are scheduled by ``sample_index % 7``.
Consequently every seven consecutive examples contain all decisive branches,
which makes the intended rule identifiable against the declared shortcut
solvers rather than merely producing diverse-looking grids.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "37aaf7d1e52e"
TASK_ID = "37aaf7d1e52e"
VERSION = "3.0.0"
RULE_HASH = "7429f4268659"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 0-background grid contains one or more monochrome 4-connected objects. "
    "For EACH object, identify every 4-connected background region enclosed "
    "inside that object's bounding box. Output only those enclosed cells, "
    "colored with the enclosing object's color; erase all object walls, open "
    "cavities, solid objects, and other distractors to 0. The curriculum "
    "covers rectangular and irregular enclosures, one- and multi-cell holes, "
    "multiple holes in one object, multiple enclosing objects with equal or "
    "different colors, and non-enclosing distractors."
)

INVARIANTS = [
    "background is 0",
    "ordinary draws contain at least one monochrome object with an enclosed hole",
    "objects are interpreted independently as same-color 4-connected components",
    "open cavities and solid objects contribute no output cells",
    "every seven consecutive default examples cover all seven scene profiles",
]

SCENE_PROFILES = (
    "single_rect",
    "single_irregular",
    "wide_hole",
    "multi_hole",
    "multi_object_distinct",
    "multi_object_same",
    "with_distractor",
)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted with periodic canonical 5",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with periodic canonical 7",
        "valid": "7..14",
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index modulo 7",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

DEGENERATE_TEXTURES = (
    "no_objects",
    "solid_only",
    "open_only",
    "filled_hole",
    "mixed_color_wall",
)

# Local object templates.  A value of 1 is an object cell and omitted cells are
# background.  Templates are transformed by rotations/reflections before
# placement, so these are semantic skeletons rather than fixed positions.
_RING_3 = frozenset(
    (r, c)
    for r in range(3)
    for c in range(3)
    if not (r == 1 and c == 1)
)
_IRREGULAR_RING = frozenset(
    {(0, 1)}
    | {
        (r + 1, c)
        for r in range(4)
        for c in range(4)
        if r in (0, 3) or c in (0, 3)
    }
)
_WIDE_RING = frozenset(
    (r, c)
    for r in range(3)
    for c in range(4)
    if r in (0, 2) or c in (0, 3)
)
_TWO_HOLE_FRAME = frozenset(
    (r, c)
    for r in range(3)
    for c in range(5)
    if r in (0, 2) or c in (0, 2, 4)
)
_OPEN_U = frozenset(
    {
        (0, 0), (1, 0), (2, 0),
        (2, 1),
        (0, 2), (1, 2), (2, 2),
    }
)

_TEMPLATES = {
    "ring": _RING_3,
    "irregular": _IRREGULAR_RING,
    "wide": _WIDE_RING,
    "two_hole": _TWO_HOLE_FRAME,
    "open_u": _OPEN_U,
}


def _normalize(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return frozenset((r - min_r, c - min_c) for r, c in cells)


def _rotate(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    normalized = _normalize(cells)
    h = max(r for r, _ in normalized) + 1
    return _normalize((c, h - 1 - r) for r, c in normalized)


def _reflect(cells: Iterable[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    normalized = _normalize(cells)
    w = max(c for _, c in normalized) + 1
    return _normalize((r, w - 1 - c) for r, c in normalized)


def _variants(cells: Iterable[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], ...]:
    variants: set[frozenset[tuple[int, int]]] = set()
    current = _normalize(cells)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants, key=lambda v: (max(r for r, _ in v), max(c for _, c in v), sorted(v))))


_TEMPLATE_VARIANTS = {name: _variants(cells) for name, cells in _TEMPLATES.items()}


def _shape_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _guard(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _place_objects(
    h: int,
    w: int,
    specs: list[tuple[str, int]],
    rng,
) -> list[list[int]]:
    """Backtrack over all fitting placements; object cells stay one cell apart."""
    grid = full_grid(h, w, 0)

    def recurse(index: int, blocked: set[tuple[int, int]]) -> bool:
        if index == len(specs):
            return True
        template_name, color = specs[index]
        variants = list(_TEMPLATE_VARIANTS[template_name])
        rng.shuffle(variants)
        for shape in variants:
            sh, sw = _shape_size(shape)
            if sh > h or sw > w:
                continue
            positions = [(r0, c0) for r0 in range(h - sh + 1) for c0 in range(w - sw + 1)]
            rng.shuffle(positions)
            for r0, c0 in positions:
                cells = {(r0 + r, c0 + c) for r, c in shape}
                if cells & blocked:
                    continue
                for r, c in cells:
                    grid[r][c] = color
                if recurse(index + 1, blocked | _guard(cells)):
                    return True
                for r, c in cells:
                    grid[r][c] = 0
        return False

    if not recurse(0, set()):
        raise ValueError(
            f"could not place scene profile in exact requested grid {h}x{w}"
        )
    return grid


def _profile_specs(profile: str, colors: tuple[int, ...]) -> list[tuple[str, int]]:
    if profile == "single_rect":
        return [("ring", colors[0])]
    if profile == "single_irregular":
        return [("irregular", colors[0])]
    if profile == "wide_hole":
        return [("wide", colors[0])]
    if profile == "multi_hole":
        return [("two_hole", colors[0])]
    if profile == "multi_object_distinct":
        return [("ring", colors[0]), ("ring", colors[1])]
    if profile == "multi_object_same":
        return [("ring", colors[0]), ("ring", colors[0])]
    if profile == "with_distractor":
        return [("ring", colors[0]), ("open_u", colors[1])]
    raise ValueError(f"unknown scene_profile {profile!r}")


def _needed_color_count(profile: str) -> int:
    return 2 if profile in {"multi_object_distinct", "with_distractor"} else 1


def _draw_int_axis(ctx, name: str, bounds: tuple[int, int], defaults: tuple[int, int], forced: int | None = None) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, *bounds)
    if forced is None:
        forced = ctx.draw_rng(f"default|{name}").randint(*defaults)
    return ctx.draw_int(name, forced, forced)


def _draw_profile(ctx, sample_index: int) -> str:
    if ctx.overrides.get("scene_profile") is not None:
        return ctx.draw_choice("scene_profile", SCENE_PROFILES)
    profile = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
    return ctx.draw_choice("scene_profile", (profile,))


def _band_defaults(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (5, 7), (7, 9)
    if difficulty == "hard":
        return (8, 12), (10, 14)
    return (6, 10), (8, 12)


def _draw_degenerate(name: str) -> list[list[int]]:
    grid = full_grid(7, 9, 0)
    if name == "no_objects":
        return grid
    if name == "solid_only":
        for r in range(2, 5):
            for c in range(3, 6):
                grid[r][c] = 4
        return grid
    if name == "open_only":
        for r, c in _OPEN_U:
            grid[r + 2][c + 3] = 5
        return grid
    if name == "filled_hole":
        for r, c in _RING_3:
            grid[r + 2][c + 3] = 6
        grid[3][4] = 6
        return grid
    if name == "mixed_color_wall":
        for r, c in _RING_3:
            grid[r + 2][c + 3] = 7
        grid[2][4] = 8
        return grid
    raise ValueError(f"unknown diagnostic texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"unknown texture {texture!r}; valid diagnostics are {DEGENERATE_TEXTURES}"
            )
        conflicts = sorted(k for k, v in overrides.items() if k != "texture" and v is not None)
        if conflicts:
            raise ValueError(f"diagnostic texture {texture!r} conflicts with {conflicts}")
        return _draw_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_profile(ctx, sample_index)
    h_defaults, w_defaults = _band_defaults(difficulty)

    # Periodic exact canonical anchor in every band.  Explicit overrides always
    # win and still use the full declared range rather than a band-local range.
    canonical_anchor = sample_index % (2 * len(SCENE_PROFILES)) == 0
    h = _draw_int_axis(ctx, "grid_h", (5, 12), h_defaults, 5 if canonical_anchor else None)
    w = _draw_int_axis(ctx, "grid_w", (7, 14), w_defaults, 7 if canonical_anchor else None)

    palette_rng = ctx.draw_rng("palette")
    n_colors = _needed_color_count(profile)
    colors = tuple(palette_rng.sample(range(1, 10), n_colors))
    layout_rng = ctx.draw_rng("layout")
    grid = _place_objects(h, w, _profile_specs(profile, colors), layout_rng)

    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "scene_profile": profile}
    if observed != expected:
        raise RuntimeError(f"internal profile realization mismatch: {observed!r} != {expected!r}")
    return grid


def _neighbors4(r: int, c: int, h: int, w: int) -> Iterable[tuple[int, int]]:
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _components_by_color(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells: set[tuple[int, int]] = set()
            while queue:
                cr, cc = queue.pop()
                cells.add((cr, cc))
                for nr, nc in _neighbors4(cr, cc, h, w):
                    if (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            components.append({"color": color, "cells": cells, "bbox": bbox})
    components.sort(key=lambda obj: (obj["bbox"], obj["color"]))
    return components


def _holes_for_object(obj: dict[str, Any]) -> list[set[tuple[int, int]]]:
    r0, c0, r1, c1 = obj["bbox"]
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    occupied = {(r - r0, c - c0) for r, c in obj["cells"]}
    unseen = {(r, c) for r in range(bh) for c in range(bw) if (r, c) not in occupied}
    holes: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        region = {start}
        queue = deque([start])
        touches_border = start[0] in (0, bh - 1) or start[1] in (0, bw - 1)
        while queue:
            r, c = queue.popleft()
            for nr, nc in _neighbors4(r, c, bh, bw):
                if (nr, nc) not in unseen:
                    continue
                unseen.remove((nr, nc))
                region.add((nr, nc))
                queue.append((nr, nc))
                if nr in (0, bh - 1) or nc in (0, bw - 1):
                    touches_border = True
        if not touches_border:
            holes.append({(r0 + r, c0 + c) for r, c in region})
    holes.sort(key=lambda region: min(region))
    return holes


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["grid values must be integer ARC colors 0..9"]}
    h = len(grid)
    if not (5 <= h <= 12 and 7 <= w <= 14):
        errors.append(f"grid dimensions outside teaching contract: {h}x{w}")
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must be present")

    components = _components_by_color(grid)
    for obj in components:
        obj["holes"] = _holes_for_object(obj)
    hole_objects = [obj for obj in components if obj["holes"]]
    distractors = [obj for obj in components if not obj["holes"]]
    if not hole_objects:
        errors.append("at least one object must enclose a background hole")

    # No other nonzero component may sit inside a hole-bearing object's bbox;
    # such nesting is legal for the broad Racket program but would make the
    # intended color ownership ambiguous in this teaching grammar.
    for owner in hole_objects:
        r0, c0, r1, c1 = owner["bbox"]
        for other in components:
            if other is owner:
                continue
            if any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in other["cells"]):
                errors.append("objects may not be nested inside another object's bounding box")
                break

    profile = _classify_profile(hole_objects, distractors)
    if profile is None:
        errors.append("scene does not match any declared teaching profile")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "components": components,
        "hole_objects": hole_objects,
        "distractors": distractors,
        "scene_profile": profile,
    }


def _classify_profile(hole_objects: list[dict[str, Any]], distractors: list[dict[str, Any]]) -> str | None:
    if len(hole_objects) == 2 and not distractors:
        colors = {obj["color"] for obj in hole_objects}
        return "multi_object_same" if len(colors) == 1 else "multi_object_distinct"
    if len(hole_objects) != 1:
        return None
    obj = hole_objects[0]
    holes = obj["holes"]
    if distractors:
        return "with_distractor" if len(distractors) == 1 and len(holes) == 1 else None
    if len(holes) == 2 and all(len(region) == 1 for region in holes):
        return "multi_hole"
    if len(holes) != 1:
        return None
    hole_size = len(holes[0])
    r0, c0, r1, c1 = obj["bbox"]
    bh, bw = r1 - r0 + 1, c1 - c0 + 1
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    if obj["cells"] == border:
        if (bh, bw) == (3, 3) and len(obj["cells"]) == 8:
            return "single_rect"
        if hole_size >= 2:
            return "wide_hole"
    return "single_irregular"


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    return {
        "grid_h": analysis.get("grid_h", len(grid) if isinstance(grid, list) else 0),
        "grid_w": analysis.get(
            "grid_w",
            len(grid[0]) if isinstance(grid, list) and grid and isinstance(grid[0], list) else 0,
        ),
        "scene_profile": analysis.get("scene_profile") or "invalid",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if requested and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"requested override {name}={value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked manifold: the explicit seven-profile hole curriculum."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python audit mirror; canonical Racket remains the output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid lesson input: " + "; ".join(analysis["errors"]))
    out = full_grid(len(grid), len(grid[0]), 0)
    for obj in analysis["hole_objects"]:
        for region in obj["holes"]:
            for r, c in region:
                out[r][c] = obj["color"]
    return out


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    hole_sizes = [len(region) for obj in analysis["hole_objects"] for region in obj["holes"]]
    return {
        **observe_overrides(grid),
        "n_hole_objects": len(analysis["hole_objects"]),
        "n_distractors": len(analysis["distractors"]),
        "n_hole_regions": len(hole_sizes),
        "max_hole_size": max(hole_sizes),
        "same_color_hole_objects": (
            len(analysis["hole_objects"]) > 1
            and len({obj["color"] for obj in analysis["hole_objects"]}) == 1
        ),
        "canonical_anchor": (
            analysis["grid_h"] == 5
            and analysis["grid_w"] == 7
            and analysis["scene_profile"] == "single_rect"
        ),
    }


def _valid_obs(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


def _blank_like(grid: list[list[int]]) -> list[list[int]]:
    return full_grid(len(grid), len(grid[0]), 0)


def _rival_ring_centers_only(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    h, w = len(grid), len(grid[0])
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            border = [
                grid[r0 + dr][c0 + dc]
                for dr in range(3)
                for dc in range(3)
                if (dr, dc) != (1, 1)
            ]
            color = border[0]
            if color and all(v == color for v in border) and grid[r0 + 1][c0 + 1] == 0:
                out[r0 + 1][c0 + 1] = color
    return out


def _rival_bbox_center_each_object(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    for obj in _components_by_color(grid):
        r0, c0, r1, c1 = obj["bbox"]
        out[(r0 + r1) // 2][(c0 + c1) // 2] = obj["color"]
    return out


def _rival_first_hole_per_object(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    for obj in _components_by_color(grid):
        holes = _holes_for_object(obj)
        if holes:
            r, c = min(min(region) for region in holes)
            out[r][c] = obj["color"]
    return out


def _rival_first_object_only(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    for obj in _components_by_color(grid):
        holes = _holes_for_object(obj)
        if holes:
            for region in holes:
                for r, c in region:
                    out[r][c] = obj["color"]
            break
    return out


def _rival_all_bbox_zeros(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    for obj in _components_by_color(grid):
        r0, c0, r1, c1 = obj["bbox"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if grid[r][c] == 0:
                    out[r][c] = obj["color"]
    return out


def _rival_one_component_per_color(grid: list[list[int]]) -> list[list[int]]:
    out = _blank_like(grid)
    seen_colors: set[int] = set()
    for obj in _components_by_color(grid):
        if obj["color"] in seen_colors:
            continue
        seen_colors.add(obj["color"])
        for region in _holes_for_object(obj):
            for r, c in region:
                out[r][c] = obj["color"]
    return out


def _rival_copy_input(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


SEMANTIC_RIVALS = {
    "ring_centers_only": _rival_ring_centers_only,
    "bbox_center_each_object": _rival_bbox_center_each_object,
    "first_hole_per_object": _rival_first_hole_per_object,
    "first_object_only": _rival_first_object_only,
    "all_bbox_zeros": _rival_all_bbox_zeros,
    "one_component_per_color": _rival_one_component_per_color,
    "copy_input": _rival_copy_input,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ring_centers_only": _rival_ring_centers_only,
    "bbox_center_each_object": _rival_bbox_center_each_object,
    "first_hole_per_object": _rival_first_hole_per_object,
    "all_bbox_zeros": _rival_all_bbox_zeros,
    "one_component_per_color": _rival_one_component_per_color,
}

SEMANTIC_WITNESSES = {
    "canonical_ring_anchor": lambda grid: _valid_obs(grid, lambda obs: obs["canonical_anchor"]),
    "irregular_enclosure": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "single_irregular"
    ),
    "multi_cell_hole": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "wide_hole" and obs["max_hole_size"] >= 2
    ),
    "multiple_holes_one_object": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "multi_hole" and obs["n_hole_regions"] == 2
    ),
    "multiple_objects_distinct_colors": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "multi_object_distinct"
    ),
    "multiple_objects_same_color": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "multi_object_same" and obs["same_color_hole_objects"]
    ),
    "non_enclosing_distractor_ignored": lambda grid: _valid_obs(
        grid, lambda obs: obs["scene_profile"] == "with_distractor" and obs["n_distractors"] == 1
    ),
}
WITNESS_RIVALS = {
    "canonical_ring_anchor": ["copy_input"],
    "irregular_enclosure": ["ring_centers_only", "all_bbox_zeros"],
    "multi_cell_hole": ["bbox_center_each_object", "first_hole_per_object"],
    "multiple_holes_one_object": ["bbox_center_each_object", "first_hole_per_object"],
    "multiple_objects_distinct_colors": ["first_object_only"],
    "multiple_objects_same_color": ["one_component_per_color", "first_object_only"],
    "non_enclosing_distractor_ignored": ["bbox_center_each_object", "all_bbox_zeros"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def lesson_identifiable(demos, query) -> list[str]:
    """Require every named plausible shortcut to be refuted by the demos."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) != EXAMPLES_NEEDED:
        reasons.append(f"expected exactly {EXAMPLES_NEEDED} demonstrations")
        return reasons
    profiles = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        profile = observe_overrides(demo["input"])["scene_profile"]
        profiles.append(profile)
    if set(profiles) != set(SCENE_PROFILES):
        reasons.append(f"demonstrations cover profiles {sorted(set(profiles))}, expected all seven")

    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            if rival(demo["input"]) != demo["output"]:
                survived = False
                break
        if survived:
            reasons.append(f"shortcut {name!r} fits every demonstration")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    return reasons
