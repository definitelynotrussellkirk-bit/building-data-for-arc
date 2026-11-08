"""Input sampler for rotating every L-triomino 90 degrees clockwise.

The selected Racket rule remains the label authority.  This module samples only
lawful inputs, exposes four exact observable controls, and declares the strongest
canonical shortcut found during review: "rotate color 6 only".  Canonical examples
use only color 6, while every generated input contains a non-6 object so ordinary
lessons refute that shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "371eb0221101"
TASK_ID = GENERATOR_ID
RULE_HASH = "27c74d38508a"
VERSION = "3.0.0"
SUMMARY = (
    "A 7..14 by 7..14 zero-background grid contains 2..4 isolated monochrome "
    "L-triominoes.  There are 1..2 distinct nonzero colors.  Rotate every object "
    "90 degrees clockwise inside its own tight 2x2 bounding box, preserving color "
    "and the bounding-box anchor."
)

INVARIANTS = [
    "background is color 0 and all nonzero cells belong to 2..4 components",
    "every component is exactly three cells occupying three corners of a tight 2x2 box",
    "components are separated by at least one background cell in all eight directions",
    "generated inputs use 1..2 colors and always include a non-6 object",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile weighted", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "canonical-profile weighted", "valid": "7..14"},
    "n_blobs": {"type": "int", "default": "difficulty-weighted 2..4", "valid": "2..4"},
    "n_colors": {"type": "int", "default": "weighted toward 1", "valid": "1..2"},
}
# Every Cartesian combination above is constructive, including 4 objects in 7x7.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Local coordinates of the four 3-of-4 corners of a 2x2 square.
_L_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_CANONICAL_PROFILES = ((8, 10), (9, 9), (7, 11))
_NON_SIX_COLORS = (1, 2, 3, 4, 5, 7, 8, 9)
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _axis_choices(lo, hi, *, anchor=None, weight=0):
    values = list(range(lo, hi + 1))
    if anchor is not None:
        values.extend([anchor] * weight)
    return tuple(values)


def _draw_dimensions(ctx):
    # The profile draw jointly favors every canonical (h,w) pair.  Exact axis
    # draws remain independent keyed controls and retain their entire domains.
    profile_options = _CANONICAL_PROFILES * 6 + ((None, None),) * 3
    anchor_h, anchor_w = ctx.draw_choice("curriculum_profile", profile_options)
    h = ctx.draw_choice(
        "grid_h", _axis_choices(7, 14, anchor=anchor_h, weight=18 if anchor_h else 0)
    )
    w = ctx.draw_choice(
        "grid_w", _axis_choices(7, 14, anchor=anchor_w, weight=18 if anchor_w else 0)
    )
    return h, w


def _draw_counts(ctx, difficulty):
    anchor = {None: 3, "easy": 2, "medium": 3, "hard": 4}[difficulty]
    n_blobs = ctx.draw_choice("n_blobs", _axis_choices(2, 4, anchor=anchor, weight=6))
    n_colors = ctx.draw_choice("n_colors", (1,) * 9 + (2,) * 2)
    return n_blobs, n_colors


def _placement_origins(ctx, h, w, n_blobs):
    # A stride-3 lattice gives every 2x2 object a full one-cell moat.  Every
    # advertised canvas has at least four slots, so selection never truncates.
    row_offset = ctx.draw_rng("row_lattice_offset").randrange(3)
    col_offset = ctx.draw_rng("col_lattice_offset").randrange(3)
    rows = list(range(row_offset, h - 1, 3))
    cols = list(range(col_offset, w - 1, 3))
    # Some offsets on a 7-cell dimension have only one slot (offset 2 would be
    # legal but insufficient).  Choose the first congruent offset with max slots
    # deterministically, without a rejection loop or dropping requested objects.
    if len(rows) < 2:
        rows = list(range(0, h - 1, 3))
    if len(cols) < 2:
        cols = list(range(0, w - 1, 3))
    candidates = [(r, c) for r in rows for c in cols]
    if len(candidates) < n_blobs:
        raise RuntimeError("constructive placement invariant failed")
    return ctx.draw_rng("object_positions").sample(candidates, n_blobs)


def _draw_colors(ctx, n_colors):
    rng = ctx.draw_rng("object_colors")
    if n_colors == 1:
        # Deliberately exclude the canonical-only color so every generated
        # example refutes the strongest canonical shortcut.
        return (rng.choice(_NON_SIX_COLORS),)
    return tuple(rng.sample(range(1, 10), 2))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w = _draw_dimensions(ctx)
    n_blobs, n_colors = _draw_counts(ctx, difficulty)
    origins = _placement_origins(ctx, h, w, n_blobs)
    colors = _draw_colors(ctx, n_colors)
    orientation_rng = ctx.draw_rng("object_orientations")
    color_rng = ctx.draw_rng("color_assignment")
    color_order = list(colors)
    color_rng.shuffle(color_order)

    grid = [[0] * w for _ in range(h)]
    for index, (r0, c0) in enumerate(origins):
        shape = _L_SHAPES[orientation_rng.randrange(len(_L_SHAPES))]
        color = color_order[index % len(color_order)]
        for dr, dc in shape:
            if grid[r0 + dr][c0 + dc] != 0:
                raise RuntimeError("constructive placement collision")
            grid[r0 + dr][c0 + dc] = color
    return grid


def _components(grid):
    """Return (color, sorted cells) for monochrome 4-connected components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, tuple(sorted(cells))))
    return components


def observe_overrides(grid):
    """Recover all exact controls from returned pixels."""
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(components),
        "n_colors": len({color for color, _ in components}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete documented sampler manifold, not just cell range."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (bool is not a color)"]

    h, w = len(grid), width
    errors = []
    if not 7 <= h <= 14:
        errors.append(f"grid height {h} outside 7..14")
    if not 7 <= w <= 14:
        errors.append(f"grid width {w} outside 7..14")

    components = _components(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 components, found {len(components)}")
    colors = {color for color, _ in components}
    if not 1 <= len(colors) <= 2:
        errors.append(f"expected 1..2 nonzero colors, found {len(colors)}")

    for index, (_, cells) in enumerate(components):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        box_h = max(rows) - min(rows) + 1
        box_w = max(cols) - min(cols) + 1
        if len(cells) != 3 or box_h != 2 or box_w != 2:
            errors.append(
                f"component {index} must be a 3-cell L in a tight 2x2 box; "
                f"got {len(cells)} cells in {box_h}x{box_w}"
            )

    for i, (_, left) in enumerate(components):
        for j, (_, right) in enumerate(components[i + 1:], start=i + 1):
            if min(max(abs(r1-r2), abs(c1-c2))
                   for r1, c1 in left for r2, c2 in right) <= 1:
                errors.append(f"components {i} and {j} lack one-cell separation")
    return errors


def strict_canonical_like(grid):
    """Canonical support is exactly the lawful manifold accepted above."""
    return self_check(grid)


def _rotate_cells_cw(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    r1 = max(r for r, _ in cells)
    box_h = r1 - r0 + 1
    raw = [(c-c0, box_h-1-(r-r0)) for r, c in cells]
    min_r = min(r for r, _ in raw)
    min_c = min(c for _, c in raw)
    return tuple(sorted((r0+r-min_r, c0+c-min_c) for r, c in raw))


def _rotate_all_objects_cw(grid):
    """Independent Python mirror used only for tests and rival construction."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in _components(grid):
        for r, c in _rotate_cells_cw(cells):
            out[r][c] = color
    return out


def _rotate_color_six_only(grid):
    """RIVAL: rotate color-6 objects and leave every other object unchanged."""
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in _components(grid):
        target = _rotate_cells_cw(cells) if color == 6 else cells
        for r, c in target:
            out[r][c] = color
    return out


def _has_non_six_object(grid):
    return any(color != 6 for color, _ in _components(grid))


SEMANTIC_WITNESSES = {"non_six_object": _has_non_six_object}
SEMANTIC_RIVALS = {"rotate_color_six_only": _rotate_color_six_only}
WITNESS_RIVALS = {"non_six_object": ["rotate_color_six_only"]}
CANONICAL_SHORTCUTS = {"rotate_color_six_only": _rotate_color_six_only}
LESSON_COMPETITORS = {"rotate_color_six_only": _rotate_color_six_only}
