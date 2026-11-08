"""Semantic generator for ARC task 7185b8225f1c (source b27ca6d3).

Find cardinally connected red (2) components.  Singletons stay unchanged.
For every component of at least two cells, expand its bounding box by one cell
in each direction, clip it to the canvas, and paint every zero in that expanded
rectangle green (3).  Existing red and previously painted green cells remain.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7185b8225f1c"
TASK_ID = "7185b8225f1c"
VERSION = "3.0.0"
RULE_HASH = "df2d840acdd1"
SUMMARY = "Paint every zero in the clipped one-cell-expanded bounding rectangle of each multi-cell red component green; preserve red cells and red singletons."
INVARIANTS = [
    "inputs contain only black (0) background and red (2) cells",
    "red objects are cardinally connected components",
    "red singleton components remain unchanged and receive no halo",
    "each component of size at least two selects its full bounding rectangle expanded by one cell and clipped to the canvas",
    "every selected zero becomes green (3), including holes inside concave component bounding boxes",
    "red cells are never overwritten and overlapping expanded rectangles form a green union",
    "at least one multi-cell component and one singleton occur in every accepted lesson",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3")
GENERAL_PROFILES = (
    "domino_interior_h",
    "domino_interior_v",
    "domino_edge_h",
    "domino_edge_v",
    "domino_mixed",
    "domino_overlap",
    "polyomino_concave",
    "polyomino_rectangle",
    "polyomino_mixed",
    "singleton_dense",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "three official component families and ten topology/boundary/overlap lessons",
        "valid": "public_1|public_2|public_3|domino_interior_h|domino_interior_v|domino_edge_h|domino_edge_v|domino_mixed|domino_overlap|polyomino_concave|polyomino_rectangle|polyomino_mixed|singleton_dense",
    }
}

_PUBLIC_ROWS = (
    "0000000022000200/2000000000000200/0000000000000000/0000000020000000/0020000000200202/0000000000000002/0000000000200000/0200000000000000/0000000000000000/0000000000000000/0000000000000000/0000000000000000/0200000000000000/0000000000000020/0020000000200000",
    "000000000000000000/000000000000000000/002000020000000000/000000020000000000/000000000000020000/000000000000000000/000000000000000000/000000000000000000/000000000000000002/000000000000000000/000000000000000000/000020002000000000/200000000000000000/000000000000000000/200000000000000002",
    "0000000000000002/0000200000000000/0000000000000000/0000000000000202/0000000022000000/0000000000002000/0000000000000000/0022000000000000/0000000000000020/0000002000000020/2000000200000000/0000000002020000/0020200002000000/0200002200020200/0002000000000002/0000000200000000/0000000020000000",
)
_ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_HORIZONTAL = ((0, 0), (0, 1))
_VERTICAL = ((0, 0), (1, 0))
_CONCAVE_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
)
_RECTANGLE_SHAPES = (
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 8 <= len(grid) <= 30:
        return ["input must contain eight through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 8 <= len(grid[0]) <= 30:
        return ["input must contain eight through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2) for row in grid for value in row):
        return ["input cells must be literal black (0) or red (2) integers"]
    return []


def _red_components(grid):
    height, width = len(grid), len(grid[0])
    remaining = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2}
    components = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        frontier = [start]
        while frontier:
            row, col = frontier.pop()
            for dr, dc in _ORTHOGONAL:
                neighbour = row + dr, col + dc
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    reached.add(neighbour)
                    frontier.append(neighbour)
        components.append(frozenset(reached))
    return tuple(sorted(components, key=lambda cells: (min(cells), len(cells))))


def _component_facts(grid, cells):
    height, width = len(grid), len(grid[0])
    row0, row1 = min(row for row, _ in cells), max(row for row, _ in cells)
    col0, col1 = min(col for _, col in cells), max(col for _, col in cells)
    expanded = {
        (row, col)
        for row in range(max(0, row0 - 1), min(height, row1 + 2))
        for col in range(max(0, col0 - 1), min(width, col1 + 2))
    }
    rectangle = len(cells) == (row1 - row0 + 1) * (col1 - col0 + 1)
    orientation = (
        "h" if len(cells) == 2 and row0 == row1
        else "v" if len(cells) == 2 and col0 == col1
        else "other"
    )
    return {
        "cells": cells,
        "size": len(cells),
        "bbox": (row0, col0, row1, col1),
        "rectangle": rectangle,
        "concave": len(cells) >= 3 and not rectangle,
        "edge": row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1,
        "orientation": orientation,
        "expanded": frozenset(expanded),
        "paintable": frozenset(cell for cell in expanded if grid[cell[0]][cell[1]] == 0) if len(cells) >= 2 else frozenset(),
    }


def rule_mirror(grid):
    """Exact Python mirror of the canonical component/bounding-box rule."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [list(row) for row in grid]
    for cells in _red_components(grid):
        if len(cells) < 2:
            continue
        facts = _component_facts(grid, cells)
        for row, col in facts["expanded"]:
            if output[row][col] == 0:
                output[row][col] = 3
    return output


def _family_key(grid):
    components = _red_components(grid)
    multis = tuple(sorted(tuple(sorted(cells)) for cells in components if len(cells) >= 2))
    singles = sum(len(cells) == 1 for cells in components)
    return len(grid), len(grid[0]), multis, singles


_PUBLIC_FAMILIES = {_family_key(grid): name for name, grid in _PUBLIC_INPUTS.items()}


def _general_profile(facts, overlap_pairs):
    multis = [item for item in facts if item["size"] >= 2]
    singles = sum(item["size"] == 1 for item in facts)
    if len(multis) == 1 and singles >= 8:
        return "singleton_dense"
    if all(item["size"] == 2 for item in multis):
        orientations = {item["orientation"] for item in multis}
        if overlap_pairs:
            return "domino_overlap"
        if orientations == {"h", "v"}:
            return "domino_mixed"
        if orientations == {"h"}:
            return "domino_edge_h" if any(item["edge"] for item in multis) else "domino_interior_h"
        if orientations == {"v"}:
            return "domino_edge_v" if any(item["edge"] for item in multis) else "domino_interior_v"
    concaves = [item for item in multis if item["concave"]]
    rectangles = [item for item in multis if item["rectangle"]]
    if concaves and rectangles:
        return "polyomino_mixed"
    if concaves and len(concaves) == len(multis):
        return "polyomino_concave"
    if rectangles and len(rectangles) == len(multis):
        return "polyomino_rectangle"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    components = _red_components(grid)
    facts = tuple(_component_facts(grid, cells) for cells in components)
    multis = tuple(item for item in facts if item["size"] >= 2)
    singles = tuple(item for item in facts if item["size"] == 1)
    if not multis:
        errors.append("at least one multi-cell red component is required")
    if not singles:
        errors.append("at least one red singleton is required")
    overlap_pairs = sum(bool(a["paintable"] & b["paintable"]) for index, a in enumerate(multis) for b in multis[index + 1:])
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _PUBLIC_FAMILIES.get(_family_key(grid))
    if not profile:
        profile = _general_profile(facts, overlap_pairs)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared component topology/boundary profile")
    output = None
    if not errors:
        output = rule_mirror(grid)
        changed = {(row, col) for row in range(len(grid)) for col in range(len(grid[0])) if output[row][col] == 3}
        expected = {cell for item in multis for cell in item["paintable"]}
        if changed != expected:
            errors.append("green cells must exactly equal the union of paintable expanded bounding rectangles")
        if not changed:
            errors.append("every accepted lesson must visibly change")
    summary = {
        "components": facts,
        "multi_count": len(multis),
        "singleton_count": len(singles),
        "overlap_pairs": overlap_pairs,
        "edge_multis": sum(item["edge"] for item in multis),
        "concave_multis": sum(item["concave"] for item in multis),
        "rectangle_multis": sum(item["rectangle"] for item in multis),
        "changed": sum(value == 3 for row in output for value in row) if output else 0,
        "scene_profile": profile,
    }
    return {"errors": errors, "scene_profile": profile, "facts": summary, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_family_key(grid)) if not _valid_grid(grid) else None


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 10, 14
    if difficulty == "medium":
        return 13, 18
    if difficulty == "hard":
        return 17, 24
    return 12, 21


def _translated(shape, top, left):
    return {(top + row, left + col) for row, col in shape}


def _expanded_box(cells, height, width):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return {
        (row, col)
        for row in range(max(0, min(rows) - 1), min(height, max(rows) + 2))
        for col in range(max(0, min(cols) - 1), min(width, max(cols) + 2))
    }


def _can_add(cells, occupied):
    if cells & occupied:
        return False
    return not any((row + dr, col + dc) in occupied for row, col in cells for dr, dc in _ORTHOGONAL)


def _place_shape(grid, shape, rng, *, edge=False, avoid_halo_overlap=False):
    height, width = len(grid), len(grid[0])
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    occupied = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2}
    existing_multis = [cells for cells in _red_components(grid) if len(cells) >= 2]
    candidates = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            cells = _translated(shape, top, left)
            touches_edge = top == 0 or left == 0 or top + shape_h == height or left + shape_w == width
            if touches_edge != edge or not _can_add(cells, occupied):
                continue
            if avoid_halo_overlap:
                halo = _expanded_box(cells, height, width)
                if any(halo & _expanded_box(other, height, width) for other in existing_multis):
                    continue
            candidates.append(cells)
    if not candidates:
        return False
    for row, col in rng.choice(candidates):
        grid[row][col] = 2
    return True


def _place_singletons(grid, count, rng):
    height, width = len(grid), len(grid[0])
    for _ in range(count):
        occupied = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == 2}
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == 0 and _can_add({(row, col)}, occupied)
        ]
        if not candidates:
            return False
        row, col = rng.choice(candidates)
        grid[row][col] = 2
    return True


def _public_nuisance(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    grid = [[0] * len(source[0]) for _ in source]
    components = _red_components(source)
    for cells in components:
        if len(cells) >= 2:
            for row, col in cells:
                grid[row][col] = 2
    singleton_count = sum(len(cells) == 1 for cells in components)
    if not _place_singletons(grid, singleton_count, rng):
        raise AssertionError("could not place public-family singleton nuisance")
    return grid


def _general_scene_once(profile, difficulty, rng):
    lo, hi = _limits(difficulty)
    height, width = rng.randint(lo, hi), rng.randint(lo, hi)
    grid = [[0] * width for _ in range(height)]
    count = rng.randint(1, 2 if difficulty == "easy" else 4)
    avoid_overlap = profile != "domino_overlap"

    if profile == "domino_overlap":
        row, col = height // 2 - 2, width // 2 - 2
        for r, c in _translated(_HORIZONTAL, row, col) | _translated(_VERTICAL, row + 2, col + 2):
            grid[r][c] = 2
    else:
        if profile in ("domino_interior_h", "domino_edge_h"):
            shapes = [_HORIZONTAL] * count
        elif profile in ("domino_interior_v", "domino_edge_v"):
            shapes = [_VERTICAL] * count
        elif profile == "domino_mixed":
            shapes = [_HORIZONTAL, _VERTICAL] + [_HORIZONTAL if index % 2 == 0 else _VERTICAL for index in range(max(0, count - 2))]
        elif profile == "polyomino_concave":
            shapes = [rng.choice(_CONCAVE_SHAPES) for _ in range(count)]
        elif profile == "polyomino_rectangle":
            shapes = [rng.choice(_RECTANGLE_SHAPES) for _ in range(count)]
        elif profile == "polyomino_mixed":
            shapes = [rng.choice(_CONCAVE_SHAPES), rng.choice(_RECTANGLE_SHAPES)]
        elif profile == "singleton_dense":
            shapes = [_HORIZONTAL]
        else:
            raise ValueError(f"unknown general profile: {profile!r}")
        for index, shape in enumerate(shapes):
            edge = index == 0 and profile in ("domino_edge_h", "domino_edge_v")
            if not _place_shape(grid, shape, rng, edge=edge, avoid_halo_overlap=avoid_overlap):
                raise AssertionError(f"could not place shape for {profile}")

    singleton_count = rng.randint(8, min(14, height * width // 8)) if profile == "singleton_dense" else rng.randint(1, 7)
    if not _place_singletons(grid, singleton_count, rng):
        raise AssertionError("could not place singleton contrast objects")
    return grid


def _general_scene(profile, difficulty, rng):
    for _ in range(40):
        try:
            return _general_scene_once(profile, difficulty, rng)
        except AssertionError:
            continue
    raise AssertionError(f"could not construct a valid scene for {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES * 4 + GENERAL_PROFILES * 3)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_singletons"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid component-halo lesson: " + "; ".join(errors))
    return grid
