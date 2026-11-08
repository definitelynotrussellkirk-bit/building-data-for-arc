"""Generator for 57df2ac388cd — normalize and overlay two colored motifs.

The input contains exactly two isolated monochrome 4-connected objects.  Crop
both objects to their own bounding boxes and align the crops at top-left.  The
output is their normalized union: overlap cells become 8, first-object-only
cells keep the first object's color, and second-object-only cells keep the
second object's color.

Generated lessons deliberately exercise all three semantic branches on every
lawful input.  Negative ``texture`` fixtures remain available for validators,
but are not advertised as ordinary training-domain values.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57df2ac388cd"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "a668b763669f"

SUMMARY = (
    "A 0-background grid contains exactly two separated 4-connected motifs in "
    "distinct non-{0,8} colors. Normalize each motif to its bounding-box "
    "top-left and overlay the first two scan-order objects: shared cells become "
    "8, first-only cells keep the first color, and second-only cells keep the "
    "second color. Every generated lesson contains all three supports."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the grid is rectangular ARC data",
    "exactly two monochrome 4-connected motifs, each 3..6 cells",
    "motifs use distinct colors other than 0 and 8 and have a background moat",
    "normalized motifs have overlap, first-only, and second-only cells",
]

TEXTURE_PALETTES = {
    "default": (2, 3),
    "warm": (4, 7),
    "cool": (1, 5),
    "varied": (6, 9),
}
HELPFUL_TEXTURES = tuple(TEXTURE_PALETTES)
PALETTE_KINDS = HELPFUL_TEXTURES
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "difficulty-aware; canonical prior", "valid": "9..18"},
    "motif_a_cells": {"type": "int", "default": "difficulty-aware", "valid": "3..6"},
    "motif_b_cells": {"type": "int", "default": "difficulty-aware", "valid": "3..6"},
    "texture": {"type": "str", "default": "rng helpful", "valid": "default|warm|cool|varied"},
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize_shape(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


@lru_cache(maxsize=None)
def _polyominoes(size: int):
    """All fixed 4-connected polyominoes of ``size``, translation-normalized."""
    if type(size) is not int or not 1 <= size <= 6:
        raise ValueError("polyomino size must be an integer in 1..6")
    shapes = {((0, 0),)}
    for _ in range(1, size):
        grown = set()
        for shape in shapes:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in _NEIGHBORS:
                    point = (r + dr, c + dc)
                    if point not in occupied:
                        grown.add(_normalize_shape((*shape, point)))
        shapes = grown
    return tuple(sorted(shapes))


def _partial_overlap(a, b) -> bool:
    aset, bset = set(a), set(b)
    return bool(aset & bset and aset - bset and bset - aset)


def _shape_extent(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _origins(grid_h: int, grid_w: int, shape):
    sh, sw = _shape_extent(shape)
    if sh > grid_h or sw > grid_w:
        return ()
    return tuple(
        (r, c)
        for r in range(grid_h - sh + 1)
        for c in range(grid_w - sw + 1)
    )


def _separated(a, origin_a, b, origin_b) -> bool:
    ar, ac = origin_a
    br, bc = origin_b
    for r1, c1 in a:
        rr1, cc1 = ar + r1, ac + c1
        for r2, c2 in b:
            if max(abs(rr1 - (br + r2)), abs(cc1 - (bc + c2))) <= 1:
                return False
    return True


def _choose_origins(rng, grid_h: int, grid_w: int, a, b, *, exhaustive=False):
    origins_a = _origins(grid_h, grid_w, a)
    origins_b = _origins(grid_h, grid_w, b)
    if not origins_a or not origins_b:
        return None
    if not exhaustive:
        for _ in range(128):
            oa = rng.choice(origins_a)
            ob = rng.choice(origins_b)
            if _separated(a, oa, b, ob):
                return oa, ob
        return None
    for oa in origins_a:
        for ob in origins_b:
            if _separated(a, oa, b, ob):
                return oa, ob
    return None


def _choose_shapes_and_origins(rng, grid_h: int, grid_w: int, size_a: int, size_b: int):
    shapes_a = _polyominoes(size_a)
    shapes_b = _polyominoes(size_b)

    # The normal path samples the complete fixed-polyomino support without
    # constructing a quadratic pair table.  Every accepted pair has all three
    # normalized overlay branches by construction.
    for _ in range(192):
        a = rng.choice(shapes_a)
        b = rng.choice(shapes_b)
        if not _partial_overlap(a, b):
            continue
        origins = _choose_origins(rng, grid_h, grid_w, a, b)
        if origins is not None:
            return a, b, origins[0], origins[1]

    # Deterministic total fallback.  This is only reachable for an unusually
    # unlucky sample, and ensures every advertised override combination is
    # realizable rather than failing by rejection-sampling chance.
    ranked_a = sorted(shapes_a, key=lambda s: (_shape_extent(s)[0] * _shape_extent(s)[1], s))
    ranked_b = sorted(shapes_b, key=lambda s: (_shape_extent(s)[0] * _shape_extent(s)[1], s))
    for a in ranked_a:
        for b in ranked_b:
            if not _partial_overlap(a, b):
                continue
            origins = _choose_origins(rng, grid_h, grid_w, a, b, exhaustive=True)
            if origins is not None:
                return a, b, origins[0], origins[1]
    raise ValueError(
        f"could not place partial-overlap motifs of sizes {size_a},{size_b} "
        f"in {grid_h}x{grid_w}"
    )


def _validate_override_keys(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")


def _draw_axis_int(ctx, overrides, label, full_bounds, default_bounds):
    lo, hi = full_bounds if overrides.get(label) is not None else default_bounds
    return ctx.draw_int_strict(label, lo, hi)


def _band_ranges(difficulty):
    if difficulty == "easy":
        return (9, 11), (9, 12), (3, 6), (3, 6)
    if difficulty == "hard":
        return (10, 16), (11, 18), (3, 6), (3, 6)
    return (9, 13), (9, 15), (3, 6), (3, 6)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)

    texture_override = overrides.get("texture")
    if texture_override in DEGENERATE_TEXTURES:
        extra = sorted(k for k, v in overrides.items() if k != "texture" and v is not None)
        if extra:
            raise ValueError(
                "negative texture fixtures do not accept ordinary axis overrides: "
                f"{extra}"
            )
        return _draw_from_degenerate(texture_override)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h_range, w_range, a_range, b_range = _band_ranges(difficulty)
    canonical_scale = ctx.draw_rng("canonical_profile_prior").random() < 0.45
    default_h = (9, 9) if canonical_scale else h_range
    default_w = (9, 9) if canonical_scale else w_range

    grid_h = _draw_axis_int(ctx, overrides, "grid_h", (9, 16), default_h)
    grid_w = _draw_axis_int(ctx, overrides, "grid_w", (9, 18), default_w)
    size_a = _draw_axis_int(ctx, overrides, "motif_a_cells", (3, 6), a_range)
    size_b = _draw_axis_int(ctx, overrides, "motif_b_cells", (3, 6), b_range)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    color_a, color_b = TEXTURE_PALETTES[texture]

    rng = ctx.draw_rng("motif_geometry_and_placement")
    shape_a, shape_b, origin_a, origin_b = _choose_shapes_and_origins(
        rng, grid_h, grid_w, size_a, size_b
    )
    grid = full_grid(grid_h, grid_w, 0)
    for r, c in shape_a:
        grid[origin_a[0] + r][origin_a[1] + c] = color_a
    for r, c in shape_b:
        grid[origin_b[0] + r][origin_b[1] + c] = color_b
    return grid


def _draw_from_degenerate(name):
    grid = full_grid(9, 9, 0)
    if name == "no_motifs":
        return grid
    if name == "single_motif":
        for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
            grid[r][c] = 2
        return grid
    if name == "all_same_color":
        for r, c in ((1, 1), (1, 2), (2, 1)):
            grid[r][c] = 4
        for r, c in ((6, 6), (6, 7), (7, 6), (7, 7)):
            grid[r][c] = 4
        return grid
    raise ValueError(f"unknown degenerate texture {name!r}")


def _grid_errors(grid):
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return ["grid dimensions must be in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colors 0..9 (not bool)"]
    return []


def _components_by_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _NEIGHBORS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, tuple(sorted(cells))))
    return components


def _normalized_set(cells):
    return frozenset(_normalize_shape(cells))


def _branch_sets(grid):
    components = _components_by_color(grid)
    if len(components) != 2:
        raise ValueError("expected exactly two motifs")
    first = _normalized_set(components[0][1])
    second = _normalized_set(components[1][1])
    return first & second, first - second, second - first


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors

    components = _components_by_color(grid)
    if len(components) != 2:
        return [f"expected exactly 2 motifs, found {len(components)}"]

    colors = [color for color, _ in components]
    if len(set(colors)) != 2:
        errors.append("motif colors must be distinct")
    if any(color in (0, 8) for color in colors):
        errors.append("motif colors must exclude background 0 and overlap color 8")

    for index, (_, cells) in enumerate(components, start=1):
        if not 3 <= len(cells) <= 6:
            errors.append(f"motif {index} must contain 3..6 cells, found {len(cells)}")

    cells_a, cells_b = components[0][1], components[1][1]
    if any(
        max(abs(ar - br), abs(ac - bc)) <= 1
        for ar, ac in cells_a
        for br, bc in cells_b
    ):
        errors.append("motifs must be separated by at least one background cell")

    first = _normalized_set(cells_a)
    second = _normalized_set(cells_b)
    if not first & second:
        errors.append("normalized motifs need an overlap cell")
    if not first - second:
        errors.append("normalized motifs need a first-only cell")
    if not second - first:
        errors.append("normalized motifs need a second-only cell")
    return errors


def strict_canonical_like(grid):
    """The strict task manifold equals the executable generator contract."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact control from a lawful returned grid."""
    findings = self_check(grid)
    if findings:
        raise ValueError(f"cannot observe malformed grid: {findings}")
    components = _components_by_color(grid)
    colors = frozenset(color for color, _ in components)
    matches = [
        name for name, pair in TEXTURE_PALETTES.items()
        if frozenset(pair) == colors
    ]
    if len(matches) != 1:
        raise ValueError(f"unrecognized texture colors: {sorted(colors)}")
    texture = matches[0]
    by_color = {color: len(cells) for color, cells in components}
    color_a, color_b = TEXTURE_PALETTES[texture]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_a_cells": by_color[color_a],
        "motif_b_cells": by_color[color_b],
        "texture": texture,
    }


def _overlay(grid, *, overlap_mode="cyan", erase_first=False, erase_second=False):
    components = _components_by_color(grid)
    if len(components) < 2:
        return [list(row) for row in grid]
    (color_a, cells_a), (color_b, cells_b) = components[:2]
    first = _normalized_set(cells_a)
    second = _normalized_set(cells_b)
    height = max(max(r for r, _ in first), max(r for r, _ in second)) + 1
    width = max(max(c for _, c in first), max(c for _, c in second)) + 1
    output = full_grid(height, width, 0)
    for r in range(height):
        for c in range(width):
            in_first = (r, c) in first
            in_second = (r, c) in second
            if in_first and in_second:
                output[r][c] = 8 if overlap_mode == "cyan" else color_a
            elif in_first and not erase_first:
                output[r][c] = color_a
            elif in_second and not erase_second:
                output[r][c] = color_b
    return output


def _paint_overlap_first(grid):
    return _overlay(grid, overlap_mode="first")


def _erase_first_only(grid):
    return _overlay(grid, erase_first=True)


def _erase_second_only(grid):
    return _overlay(grid, erase_second=True)


def _has_overlap(grid):
    try:
        return bool(_branch_sets(grid)[0])
    except Exception:
        return False


def _has_first_only(grid):
    try:
        return bool(_branch_sets(grid)[1])
    except Exception:
        return False


def _has_second_only(grid):
    try:
        return bool(_branch_sets(grid)[2])
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "paint_overlap_first": _paint_overlap_first,
    "erase_first_only": _erase_first_only,
    "erase_second_only": _erase_second_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)

SEMANTIC_WITNESSES = {
    "overlap_branch": _has_overlap,
    "first_only_branch": _has_first_only,
    "second_only_branch": _has_second_only,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "overlap_branch": ["paint_overlap_first"],
    "first_only_branch": ["erase_first_only"],
    "second_only_branch": ["erase_second_only"],
}


def lesson_identifiable(demos, query):
    """Finite-rival teaching check for the three independent output branches."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    if self_check(query["input"]):
        reasons.append("query input is outside the lawful motif-overlay grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demo {index} input is unlawful: {findings[0]}")
            continue
        if demo["output"] != _overlay(demo["input"]):
            reasons.append(f"demo {index} output is not the normalized overlay")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair["input"]) == pair["output"] for pair in valid_demos):
            reasons.append(f"declared rival survives all demonstrations: {name}")
    return reasons
