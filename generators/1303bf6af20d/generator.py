"""Generator for the rotation-only template-selection task ``1303bf6af20d``.

A connected color-4 template appears above one full color-9 divider.  Below the
separator are isolated color-6 objects.  The canonical Racket rule recolors to
2 exactly the objects whose normalized shape is a rotation of the template;
reflection-only and unrelated distractors remain color 6.

Ordinary draws deliberately contain both branches, a same-cell-count
reflection distractor, and a non-trivially rotated match.  One quarter of the
``sample_index`` schedule stays on the exact empirical canonical manifold.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1303bf6af20d"
TASK_ID = "1303bf6af20d"
VERSION = "3.0.0"
RULE_HASH = "a52f81e5e18b"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A zero-background grid contains one connected color-4 template above a "
    "full color-9 divider. Below it are isolated color-6 objects. Recolor to "
    "2 exactly the objects whose normalized shape equals one of the four "
    "rotations of the template; preserve reflection-only and unrelated "
    "objects. Ordinary lessons contain at least one match, at least one "
    "non-match, a non-trivially rotated match, and a same-size reflected "
    "distractor."
)

INVARIANTS = [
    "exactly one connected color-4 template lies strictly above one full color-9 divider",
    "at least one color-6 object below the divider is rotation-equivalent to the template",
    "at least one color-6 object below the divider is not rotation-equivalent to the template",
    "ordinary generated objects are 8-neighbor separated and include a same-size reflection-only distractor",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty/profile linked", "valid": "8..16"},
    "grid_w": {"type": "int", "default": "difficulty/profile linked", "valid": "8..16"},
    "template_size": {"type": "int", "default": "difficulty linked", "valid": "4..6"},
    "n_blobs": {"type": "int", "default": "difficulty linked", "valid": "2..6"},
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_CANON_DIMS = ((8, 9), (8, 8), (9, 9), (8, 9))
_CANON_TEMPLATE = ((0, 0), (1, 0), (2, 0), (2, 1))
_CANON_TEMPLATE_CANON = ((0, 0), (0, 1), (0, 2), (1, 0))
_CANON_NONMATCH_CANONS = {
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
}


def _norm(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _norm(cells)
    height = max(r for r, _ in cells) + 1
    return _norm((c, height - 1 - r) for r, c in cells)


def _rotations(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    forms: list[tuple[tuple[int, int], ...]] = []
    current = _norm(cells)
    for _ in range(4):
        if current not in forms:
            forms.append(current)
        current = _rotate(current)
    return tuple(forms)


def _canonical(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_rotations(cells))


def _mirror(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = _norm(cells)
    width = max(c for _, c in cells) + 1
    return _norm((r, width - 1 - c) for r, c in cells)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = _norm(cells)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _rotation_classes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate connected fixed polyominoes, quotiented by rotation only."""
    shapes: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    for _ in range(1, size):
        expanded: set[tuple[tuple[int, int], ...]] = set()
        for shape in shapes:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    candidate = (r + dr, c + dc)
                    if candidate not in occupied:
                        expanded.add(_canonical((*shape, candidate)))
        shapes = expanded
    return tuple(sorted(shapes))


# Chiral templates make the no-reflection clause observable.  These banks are
# derived from connectivity rather than hand-labelled as "canonical" shapes.
_CHIRAL_BY_SIZE = {
    size: tuple(
        shape
        for shape in _rotation_classes(size)
        if _canonical(_mirror(shape)) != _canonical(shape)
    )
    for size in range(4, 7)
}
_ALL_CLASSES_BY_SIZE = {size: _rotation_classes(size) for size in range(3, 7)}


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid must be a non-empty list of non-empty rows"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} exceed ARC bounds")
    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int) or isinstance(value, bool) or value not in {0, 4, 6, 9}
    ]
    if bad_values:
        errors.append("input palette must be exactly a subset of {0,4,6,9}")
        return {"errors": errors, "height": height, "width": width}

    divider_rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    if len(divider_rows) != 1:
        errors.append(f"expected exactly one full color-9 divider row, found {len(divider_rows)}")
        return {"errors": errors, "height": height, "width": width}
    divider_row = divider_rows[0]
    stray_nines = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9 and r != divider_row
    ]
    if stray_nines:
        errors.append("color 9 may appear only in the full divider row")

    template_components = _components(grid, 4)
    if len(template_components) != 1:
        errors.append(f"expected exactly one connected color-4 template, found {len(template_components)}")
        template = set()
    else:
        template = template_components[0]
        if any(r >= divider_row for r, _ in template):
            errors.append("the color-4 template must lie strictly above the divider")

    blobs = _components(grid, 6)
    if len(blobs) < 2:
        errors.append(f"expected at least two color-6 objects, found {len(blobs)}")
    if any(r <= divider_row for blob in blobs for r, _ in blob):
        errors.append("all color-6 objects must lie strictly below the divider")

    for r in range(divider_row):
        if any(value not in {0, 4} for value in grid[r]):
            errors.append("only background and the template may appear above the divider")
            break
    for r in range(divider_row + 1, height):
        if any(value not in {0, 6} for value in grid[r]):
            errors.append("only background and candidate objects may appear below the divider")
            break

    template_norm = _norm(template)
    template_canon = _canonical(template) if template else ()
    blob_infos: list[dict[str, Any]] = []
    for blob in blobs:
        normalized = _norm(blob)
        blob_infos.append(
            {
                "cells": blob,
                "norm": normalized,
                "canon": _canonical(blob),
                "size": len(blob),
                "bbox": _bbox(blob),
                "matches": bool(template and _canonical(blob) == template_canon),
            }
        )
    matching = [info for info in blob_infos if info["matches"]]
    nonmatching = [info for info in blob_infos if not info["matches"]]
    if template and not matching:
        errors.append("at least one color-6 object must match the template up to rotation")
    if template and not nonmatching:
        errors.append("at least one color-6 object must be a non-matching distractor")

    if template:
        rows = [r for r, _ in template]
        cols = [c for _, c in template]
        template_bbox = (
            min(rows), min(cols), max(rows) - min(rows) + 1, max(cols) - min(cols) + 1
        )
        template_edge = min(cols) == 0 or max(cols) == width - 1
        mirror_canon = _canonical(_mirror(template_norm))
    else:
        template_bbox = None
        template_edge = False
        mirror_canon = ()

    same_size_nonmatch = bool(
        template and any(info["size"] == len(template) for info in nonmatching)
    )
    transformed_match = bool(
        template and any(info["norm"] != template_norm for info in matching)
    )
    reflection_only = bool(
        template
        and mirror_canon != template_canon
        and any(info["canon"] == mirror_canon for info in nonmatching)
    )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "divider_row": divider_row,
        "template": template,
        "template_norm": template_norm,
        "template_canon": template_canon,
        "template_bbox": template_bbox,
        "template_size": len(template),
        "template_edge": template_edge,
        "blobs": blobs,
        "blob_infos": blob_infos,
        "n_blobs": len(blobs),
        "matching": matching,
        "nonmatching": nonmatching,
        "n_matching": len(matching),
        "same_size_nonmatch": same_size_nonmatch,
        "transformed_match": transformed_match,
        "reflection_only": reflection_only,
        "palette": {value for row in grid for value in row},
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar gate shared by generated and canonical inputs."""
    return list(_analysis(grid)["errors"])


def _axis_int(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _difficulty_defaults(difficulty: str | None, rng, overrides: dict[str, Any]) -> dict[str, Any]:
    pinned_h = int(overrides["grid_h"]) if overrides.get("grid_h") is not None else None
    pinned_w = int(overrides["grid_w"]) if overrides.get("grid_w") is not None else None
    tight = min(value for value in (pinned_h, pinned_w, 16) if value is not None)

    if overrides.get("template_size") is not None:
        template_size = int(overrides["template_size"])
    elif tight <= 9:
        template_size = 4
    elif difficulty == "hard":
        template_size = rng.choice((5, 6))
    else:
        template_size = rng.choice((4, 5))

    if overrides.get("n_blobs") is not None:
        n_blobs = int(overrides["n_blobs"])
    else:
        capacity_cap = 2 if tight <= 9 else 3 if tight <= 11 else 4 if tight <= 13 else 6
        if difficulty == "easy":
            choices = (2, 3)
        elif difficulty == "hard":
            choices = (4, 5, 6)
        else:
            choices = (3, 4)
        lawful = tuple(value for value in choices if value <= capacity_cap)
        n_blobs = rng.choice(lawful or (2,))

    n_matching = rng.randint(1, min(n_blobs - 1, 1 if difficulty == "easy" else 3))
    divider_hi = min(6, (pinned_h - 5) if pinned_h is not None else 6)
    divider_row = rng.randint(3, max(3, divider_hi))

    load_min = {2: 8, 3: 10, 4: 12, 5: 14, 6: 16}[n_blobs]
    base_h = max(load_min, divider_row + 5, 8 + max(0, template_size - 4))
    base_w = max(load_min, 8 + max(0, template_size - 4))
    grid_h = pinned_h if pinned_h is not None else rng.randint(min(base_h, 16), min(16, base_h + 2))
    grid_w = pinned_w if pinned_w is not None else rng.randint(min(base_w, 16), min(16, base_w + 2))
    template_edge = bool(rng.randint(0, 1))
    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "divider_row": divider_row,
        "template_size": template_size,
        "n_blobs": n_blobs,
        "n_matching": n_matching,
        "template_edge": template_edge,
    }

def _resolve_axes(ctx, difficulty: str | None, overrides: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")

    canonical_profile = not overrides and ctx.sample_index % 4 == 0
    profile_rng = ctx.draw_rng("profile")
    if canonical_profile:
        grid_h, grid_w = profile_rng.choice(_CANON_DIMS)
        defaults = {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "divider_row": 3,
            "template_size": 4,
            "n_blobs": 2,
            "n_matching": 1,
            "template_edge": False,
        }
    else:
        defaults = _difficulty_defaults(difficulty, profile_rng, overrides)

    values = {
        "grid_h": _axis_int(ctx, overrides, "grid_h", defaults["grid_h"], 8, 16),
        "grid_w": _axis_int(ctx, overrides, "grid_w", defaults["grid_w"], 8, 16),
        "template_size": _axis_int(ctx, overrides, "template_size", defaults["template_size"], 4, 6),
        "n_blobs": _axis_int(ctx, overrides, "n_blobs", defaults["n_blobs"], 2, 6),
        "divider_row": defaults["divider_row"],
        "n_matching": defaults["n_matching"],
        "template_edge": defaults["template_edge"],
    }
    if values["n_matching"] >= values["n_blobs"]:
        raise ValueError(
            f"n_matching={values['n_matching']} requires n_blobs >= {values['n_matching'] + 1}"
        )
    if values["divider_row"] >= values["grid_h"] - 1:
        raise ValueError("divider_row leaves no usable region below the separator")
    return values, canonical_profile


def _paint(grid: list[list[int]], cells: Iterable[tuple[int, int]], top: int, left: int, color: int) -> None:
    for r, c in cells:
        grid[top + r][left + c] = color


def _template_candidates(values: dict[str, Any], canonical_profile: bool, rng) -> list[tuple[tuple[int, int], ...]]:
    if canonical_profile:
        return [_CANON_TEMPLATE]
    candidates: list[tuple[tuple[int, int], ...]] = []
    for base in _CHIRAL_BY_SIZE[values["template_size"]]:
        for orientation in _rotations(base):
            height, width = _bbox(orientation)
            horizontal_space = values["grid_w"] if values["template_edge"] else values["grid_w"] - 2
            if height <= values["divider_row"] and width <= horizontal_space:
                candidates.append(orientation)
    rng.shuffle(candidates)
    return candidates


def _template_position(values: dict[str, Any], shape: tuple[tuple[int, int], ...], canonical_profile: bool, rng) -> tuple[int, int]:
    shape_h, shape_w = _bbox(shape)
    if canonical_profile:
        left = rng.randint(1, values["grid_w"] - shape_w - 1)
        return 0, left
    top = rng.randint(0, values["divider_row"] - shape_h)
    if values["template_edge"]:
        left = 0 if rng.randint(0, 1) == 0 else values["grid_w"] - shape_w
    else:
        left = rng.randint(1, values["grid_w"] - shape_w - 1)
    return top, left


def _canonical_blob_shapes(template: tuple[tuple[int, int], ...], rng) -> list[tuple[tuple[int, int], ...]]:
    matching_choices = [shape for shape in _rotations(template) if shape != _norm(template)]
    match = rng.choice(matching_choices or list(_rotations(template)))
    nonmatch = rng.choice(
        [
            ((0, 0), (0, 1), (1, 1)),
            ((0, 0), (0, 1), (1, 0), (1, 1)),
        ]
    )
    return [match, nonmatch]


def _general_blob_shapes(values: dict[str, Any], template: tuple[tuple[int, int], ...], rng) -> list[tuple[tuple[int, int], ...]]:
    rotations = list(_rotations(template))
    nontrivial = [shape for shape in rotations if shape != _norm(template)]
    matching: list[tuple[tuple[int, int], ...]] = [rng.choice(nontrivial or rotations)]
    while len(matching) < values["n_matching"]:
        matching.append(rng.choice(rotations))

    template_canon = _canonical(template)
    distractors: list[tuple[tuple[int, int], ...]] = [_mirror(template)]
    while len(distractors) < values["n_blobs"] - values["n_matching"]:
        size = rng.randint(3, 6)
        choices = [shape for shape in _ALL_CLASSES_BY_SIZE[size] if _canonical(shape) != template_canon]
        shape = rng.choice(choices)
        distractors.append(rng.choice(_rotations(shape)))

    specs = matching + distractors
    rng.shuffle(specs)
    return specs


def _candidate_positions(shape: tuple[tuple[int, int], ...], values: dict[str, Any], rng) -> list[tuple[int, int]]:
    shape_h, shape_w = _bbox(shape)
    positions = [
        (top, left)
        for top in range(values["divider_row"] + 1, values["grid_h"] - shape_h + 1)
        for left in range(0, values["grid_w"] - shape_w + 1)
    ]
    rng.shuffle(positions)
    return positions


def _separated(candidate: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    for r, c in candidate:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    return True


def _place_blobs(
    grid: list[list[int]],
    shapes: list[tuple[tuple[int, int], ...]],
    values: dict[str, Any],
    rng,
) -> bool:
    occupied: set[tuple[int, int]] = set()
    placements: list[tuple[tuple[tuple[int, int], ...], int, int]] = []

    # Largest-first search reduces backtracking on tight valid overrides.
    order = sorted(range(len(shapes)), key=lambda index: _bbox(shapes[index])[0] * _bbox(shapes[index])[1], reverse=True)

    def search(depth: int) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        shape = shapes[index]
        for top, left in _candidate_positions(shape, values, rng):
            cells = {(top + r, left + c) for r, c in shape}
            if not _separated(cells, occupied):
                continue
            occupied.update(cells)
            placements.append((shape, top, left))
            if search(depth + 1):
                return True
            placements.pop()
            occupied.difference_update(cells)
        return False

    if not search(0):
        return False
    for shape, top, left in placements:
        _paint(grid, shape, top, left, 6)
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    values, canonical_profile = _resolve_axes(ctx, difficulty, overrides)
    layout_rng = ctx.draw_rng("layout")

    for template in _template_candidates(values, canonical_profile, layout_rng):
        grid = full_grid(values["grid_h"], values["grid_w"], 0)
        top, left = _template_position(values, template, canonical_profile, layout_rng)
        _paint(grid, template, top, left, 4)
        for c in range(values["grid_w"]):
            grid[values["divider_row"]][c] = 9

        shapes = (
            _canonical_blob_shapes(template, layout_rng)
            if canonical_profile
            else _general_blob_shapes(values, template, layout_rng)
        )
        if not _place_blobs(grid, shapes, values, layout_rng):
            continue
        info = _analysis(grid)
        if info["errors"]:
            continue
        if not canonical_profile and not (
            info["same_size_nonmatch"]
            and info["transformed_match"]
            and info["reflection_only"]
        ):
            continue
        observed = observe_overrides(grid)
        for axis in AXES:
            requested = values[axis]
            if observed[axis] != requested:
                raise AssertionError(
                    f"constructed axis drift for {axis}: requested {requested!r}, observed {observed[axis]!r}"
                )
        return grid

    raise ValueError(
        "requested axis combination cannot place a chiral template and the "
        f"required isolated objects: {values}"
    )


def observe_overrides(grid) -> dict[str, int | bool]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(info["errors"]))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "template_size": info["template_size"],
        "n_blobs": info["n_blobs"],
    }


def strict_canonical_like(grid) -> list[str]:
    info = _analysis(grid)
    if info["errors"]:
        return list(info["errors"])
    reasons: list[str] = []
    if (info["height"], info["width"]) not in {(8, 8), (8, 9), (9, 9)}:
        reasons.append("dimensions are outside the observed canonical (h,w) set")
    if info["divider_row"] != 3:
        reasons.append("canonical divider row is exactly 3")
    if info["palette"] != {0, 4, 6, 9}:
        reasons.append("canonical input palette is exactly {0,4,6,9}")
    if info["template_norm"] != _CANON_TEMPLATE:
        reasons.append("canonical template is the demonstrated oriented L tetromino")
    elif info["template_bbox"][0] != 0:
        reasons.append("canonical template touches the top row")
    if info["n_blobs"] != 2 or info["n_matching"] != 1:
        reasons.append("canonical scenes contain exactly one match and one non-match")
    elif info["matching"][0]["size"] != 4:
        reasons.append("canonical matching object has four cells")
    if info["nonmatching"] and info["nonmatching"][0]["canon"] not in _CANON_NONMATCH_CANONS:
        reasons.append("non-match morphology is outside the demonstrated triomino/square set")
    return reasons


# The default sample-index schedule is exactly one canonical profile in four.
MIN_STRICT_FRAC = 0.20


def _lawful_info(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _witness(predicate: Callable[[dict[str, Any]], bool], grid) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


SEMANTIC_WITNESSES = {
    "rotation_match_present": lambda grid: _witness(lambda info: info["n_matching"] >= 1, grid),
    "preserved_nonmatch_present": lambda grid: _witness(lambda info: len(info["nonmatching"]) >= 1, grid),
    "nontrivially_rotated_match": lambda grid: _witness(lambda info: info["transformed_match"], grid),
    "same_size_count_shortcut_rebuttal": lambda grid: _witness(lambda info: info["same_size_nonmatch"], grid),
    "reflection_only_distractor": lambda grid: _witness(lambda info: info["reflection_only"], grid),
    "template_on_side_edge": lambda grid: _witness(lambda info: info["template_edge"], grid),
    "template_interior_horizontally": lambda grid: _witness(lambda info: not info["template_edge"], grid),
    "strict_empirical_profile": lambda grid: strict_canonical_like(grid) == [],
}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python test mirror; canonical Racket remains authoritative."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("malformed task input: " + "; ".join(info["errors"]))
    out = [row[:] for row in grid]
    for blob in info["matching"]:
        for r, c in blob["cells"]:
            out[r][c] = 2
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _recolor_selected(grid, predicate: Callable[[dict[str, Any], dict[str, Any]], bool]):
    info = _analysis(grid)
    if info["errors"]:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for blob in info["blob_infos"]:
        if predicate(info, blob):
            for r, c in blob["cells"]:
                out[r][c] = 2
    return out


def _recolor_all_blobs(grid):
    return _recolor_selected(grid, lambda info, blob: True)


def _recolor_same_cell_count(grid):
    return _recolor_selected(grid, lambda info, blob: blob["size"] == info["template_size"])


def _recolor_exact_orientation(grid):
    return _recolor_selected(grid, lambda info, blob: blob["norm"] == info["template_norm"])


def _recolor_rotations_or_reflections(grid):
    return _recolor_selected(
        grid,
        lambda info, blob: blob["canon"]
        in {info["template_canon"], _canonical(_mirror(info["template_norm"]))},
    )


_LESSON_COMPETITORS = {
    "copy the input unchanged": _identity,
    "recolor every color-6 object": _recolor_all_blobs,
    "select by cell count only": _recolor_same_cell_count,
    "require exact orientation": _recolor_exact_orientation,
    "allow reflections as well as rotations": _recolor_rotations_or_reflections,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{role} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"{role} is not lawful: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{role} output disagrees with rotation-only selection")
    if reasons:
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify shortcut '{name}', which changes the query")
    return reasons
