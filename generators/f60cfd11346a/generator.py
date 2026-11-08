"""Generator for f60cfd11346a: flood-fill the seed's zero chamber.

The input contains one red (2) seed, black (0) floor, gray (5) walls, and one
additional wall-colored cell.  The authoritative rule traverses cardinally from
the seed through {0, 2} only and recolors every reached 0 to cyan (8).  Every
ordinary generated instance contains a critical wall cell colored 1 or 9.  Those
colors never occur in the canonical demonstrations, so the instance explicitly
refutes the plausible shortcut "only the demonstrated blocker palette
{3,4,5,6,7} is impassable".
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f60cfd11346a"
VERSION = "3.1.0"
TASK_ID = "f60cfd11346a"
RULE_HASH = "23823efe5a14"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "A gray-bordered floor is split by a full vertical wall, a full horizontal "
    "wall, or both, plus a partial internal branch that hides a same-side pocket. "
    "Exactly one wall cell has an accent color and one adjacent chamber contains "
    "the red seed. Flood cardinally from the seed through colors 0 and 2, "
    "recoloring reached zeros to 8. Ordinary draws use an unseen accent wall "
    "color (1 or 9) and an internal pocket, rejecting both palette memorization "
    "and coarse half/quadrant filling."
)

INVARIANTS = [
    "grid is 7..15 by 8..22 with a solid gray(5) border",
    "palette is exactly {0,2,5,accent}; accent is one cell from 1|3|4|6|7|9",
    "exactly one red(2) seed and at least one reachable black(0) cell",
    "a full wall separates at least one zero chamber from the seeded chamber",
    "a partial branch hides an additional zero pocket inside the seed's coarse region",
    "ordinary draws make color 1 or 9 a critical impassable wall witness",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale weighted, with full-domain support",
        "valid": "7..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale weighted, with full-domain support",
        "valid": "8..22",
    },
    "layout_style": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "vertical|horizontal|cross",
    },
    "accent_color": {
        "type": "color",
        "default": "1|9 (canonical-gap witnesses); all values overrideable",
        "valid": "1|3|4|6|7|9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_ACCENT_COLORS = (1, 3, 4, 6, 7, 9)
_UNSEEN_ACCENTS = (1, 9)
_CANONICAL_BLOCKERS = frozenset({3, 4, 5, 6, 7})

# Include every documented value while heavily anchoring the exact canonical
# shape profiles (8x10, 9x10, 10x12, 9x11).  Repetition is only a sampling
# weight; exact overrides remain observable from returned pixels.
_HEIGHT_OPTIONS = tuple(range(7, 16)) + (8,) * 12 + (9,) * 16 + (10,) * 12
_WIDTH_OPTIONS = tuple(range(8, 23)) + (10,) * 18 + (11,) * 12 + (12,) * 14
_LAYOUT_OPTIONS = {
    None: ("vertical", "horizontal", "cross"),
    "easy": ("vertical", "vertical", "horizontal", "horizontal", "cross"),
    "medium": ("vertical", "horizontal", "cross", "cross"),
    "hard": ("vertical", "horizontal", "cross", "cross", "cross"),
}


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "accent_color"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise ValueError(f"{name} must be an integer (not bool, float, or string)")
    if ("layout_style" in overrides and overrides["layout_style"] is not None
            and type(overrides["layout_style"]) is not str):
        raise ValueError("layout_style must be a string")


def _region_zeros(grid, start, *, passable: Callable[[int], bool]) -> set[tuple[int, int]]:
    """Return zero-valued cells reachable from start through ``passable`` cells."""
    h, w = len(grid), len(grid[0])
    seen = {start}
    stack = [start]
    zeros: set[tuple[int, int]] = set()
    while stack:
        row, col = stack.pop()
        if grid[row][col] == 0:
            zeros.add((row, col))
        for dr, dc in _CARDINAL:
            nr, nc = row + dr, col + dc
            if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                    and passable(grid[nr][nc])):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return zeros


def _single_seed(grid) -> tuple[int, int]:
    seeds = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(seeds) != 1:
        raise ValueError(f"expected exactly one red seed, found {len(seeds)}")
    return seeds[0]


def _apply_flood(grid, *, passable: Callable[[int], bool]):
    seed = _single_seed(grid)
    reached = _region_zeros(grid, seed, passable=passable)
    output = deepcopy(grid)
    for row, col in reached:
        output[row][col] = 8
    return output


def rule_mirror(grid):
    """Pure independent-facing mirror of the selected Racket rule."""
    return _apply_flood(grid, passable=lambda value: value in (0, 2))


def _canonical_blocker_palette_only(grid):
    """Plausible wrong rule: only colors seen blocking canonically are walls."""
    return _apply_flood(grid, passable=lambda value: value not in _CANONICAL_BLOCKERS)


def _coarse_partition_only(grid):
    """Wrong lesson heuristic: fill the seed's box between full wall axes."""
    seed_row, seed_col = _single_seed(grid)
    h, w = len(grid), len(grid[0])
    row_edges = [0, *_full_interior_rows(grid), h - 1]
    col_edges = [0, *_full_interior_cols(grid), w - 1]
    row_lo = max(edge for edge in row_edges if edge < seed_row)
    row_hi = min(edge for edge in row_edges if edge > seed_row)
    col_lo = max(edge for edge in col_edges if edge < seed_col)
    col_hi = min(edge for edge in col_edges if edge > seed_col)
    output = deepcopy(grid)
    for row in range(row_lo + 1, row_hi):
        for col in range(col_lo + 1, col_hi):
            if grid[row][col] == 0:
                output[row][col] = 8
    return output


def _critical_unseen_blocker(grid) -> bool:
    colors = {value for row in grid for value in row}
    return bool(colors & set(_UNSEEN_ACCENTS)) and rule_mirror(grid) != _canonical_blocker_palette_only(grid)


def _internal_branch_pocket(grid) -> bool:
    return rule_mirror(grid) != _coarse_partition_only(grid)


def _bordered_grid(height: int, width: int):
    grid = full_grid(height, width, 0)
    for row in range(height):
        grid[row][0] = 5
        grid[row][width - 1] = 5
    for col in range(width):
        grid[0][col] = 5
        grid[height - 1][col] = 5
    return grid


def _draw_vertical(ctx, grid, accent: int) -> None:
    h, w = len(grid), len(grid[0])
    divider = ctx.draw_rng("vertical_divider").randint(2, w - 3)
    candidates: list[tuple[int, int, int]] = []
    for branch_row in range(2, h - 2):
        for gate_row in range(1, h - 1):
            if gate_row == branch_row:
                continue
            for side in (-1, 1):
                chamber_width = divider - 1 if side == -1 else w - divider - 2
                seed_height = (
                    branch_row - 1
                    if gate_row < branch_row
                    else h - branch_row - 2
                )
                pocket_height = (
                    h - branch_row - 2
                    if gate_row < branch_row
                    else branch_row - 1
                )
                if seed_height * chamber_width >= 2 and pocket_height * chamber_width >= 1:
                    candidates.append((branch_row, gate_row, side))
    if not candidates:
        raise RuntimeError("legal vertical layout has no branch-separated seed chamber")
    branch_row, gate_row, side = ctx.draw_rng("vertical_geometry").choice(candidates)

    for row in range(1, h - 1):
        grid[row][divider] = 5
    branch_cols = range(1, divider) if side == -1 else range(divider + 1, w - 1)
    for col in branch_cols:
        grid[branch_row][col] = 5
    grid[gate_row][divider] = accent
    grid[gate_row][divider + side] = 2


def _draw_horizontal(ctx, grid, accent: int) -> None:
    h, w = len(grid), len(grid[0])
    divider = ctx.draw_rng("horizontal_divider").randint(2, h - 3)
    candidates: list[tuple[int, int, int]] = []
    for branch_col in range(2, w - 2):
        for gate_col in range(1, w - 1):
            if gate_col == branch_col:
                continue
            for side in (-1, 1):
                chamber_height = divider - 1 if side == -1 else h - divider - 2
                seed_width = (
                    branch_col - 1
                    if gate_col < branch_col
                    else w - branch_col - 2
                )
                pocket_width = (
                    w - branch_col - 2
                    if gate_col < branch_col
                    else branch_col - 1
                )
                if chamber_height * seed_width >= 2 and chamber_height * pocket_width >= 1:
                    candidates.append((branch_col, gate_col, side))
    if not candidates:
        raise RuntimeError("legal horizontal layout has no branch-separated seed chamber")
    branch_col, gate_col, side = ctx.draw_rng("horizontal_geometry").choice(candidates)

    for col in range(1, w - 1):
        grid[divider][col] = 5
    branch_rows = range(1, divider) if side == -1 else range(divider + 1, h - 1)
    for row in branch_rows:
        grid[row][branch_col] = 5
    grid[divider][gate_col] = accent
    grid[divider + side][gate_col] = 2


def _draw_cross(ctx, grid, accent: int) -> None:
    h, w = len(grid), len(grid[0])
    row_divider = ctx.draw_rng("cross_row_divider").randint(2, h - 3)
    col_divider = ctx.draw_rng("cross_col_divider").randint(2, w - 3)

    # Candidate = (gate_row, horizontal_side, branch_orientation, branch_coord,
    #              row_lo, row_hi, col_lo, col_hi).  The branch splits the
    # seed's quadrant into a reachable component with at least one zero and a
    # disconnected same-quadrant pocket.
    candidates: list[tuple[int, int, str, int, int, int, int, int]] = []
    row_ranges = ((1, row_divider - 1), (row_divider + 1, h - 2))
    col_ranges = ((1, col_divider - 1, -1), (col_divider + 1, w - 2, 1))
    for row_lo, row_hi in row_ranges:
        q_height = row_hi - row_lo + 1
        for col_lo, col_hi, side in col_ranges:
            q_width = col_hi - col_lo + 1
            if q_height >= 3:
                for branch_row in range(row_lo + 1, row_hi):
                    for gate_row in range(row_lo, row_hi + 1):
                        if gate_row == branch_row:
                            continue
                        seed_height = (
                            branch_row - row_lo
                            if gate_row < branch_row
                            else row_hi - branch_row
                        )
                        pocket_height = (
                            row_hi - branch_row
                            if gate_row < branch_row
                            else branch_row - row_lo
                        )
                        if seed_height * q_width >= 2 and pocket_height * q_width >= 1:
                            candidates.append((
                                gate_row, side, "horizontal", branch_row,
                                row_lo, row_hi, col_lo, col_hi,
                            ))
            if q_width >= 3:
                for branch_col in range(col_lo + 1, col_hi):
                    seed_width = (
                        col_hi - branch_col
                        if side == -1
                        else branch_col - col_lo
                    )
                    pocket_width = (
                        branch_col - col_lo
                        if side == -1
                        else col_hi - branch_col
                    )
                    if q_height * seed_width < 2 or q_height * pocket_width < 1:
                        continue
                    for gate_row in range(row_lo, row_hi + 1):
                        candidates.append((
                            gate_row, side, "vertical", branch_col,
                            row_lo, row_hi, col_lo, col_hi,
                        ))
    if not candidates:
        raise RuntimeError("legal cross layout has no branch-separated seed chamber")

    (gate_row, side, orientation, branch_coord,
     row_lo, row_hi, col_lo, col_hi) = ctx.draw_rng("cross_geometry").choice(candidates)
    for col in range(1, w - 1):
        grid[row_divider][col] = 5
    for row in range(1, h - 1):
        grid[row][col_divider] = 5
    if orientation == "horizontal":
        for col in range(col_lo, col_hi + 1):
            grid[branch_coord][col] = 5
    else:
        for row in range(row_lo, row_hi + 1):
            grid[row][branch_coord] = 5
    grid[gate_row][col_divider] = accent
    grid[gate_row][col_divider + side] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_choice("grid_h", _HEIGHT_OPTIONS)
    width = ctx.draw_choice("grid_w", _WIDTH_OPTIONS)
    layout = ctx.draw_choice(
        "layout_style",
        _LAYOUT_OPTIONS.get(difficulty, _LAYOUT_OPTIONS[None]),
    )
    # Default lessons always expose the canonical palette gap. An exact
    # override may select every lawful canonical or unseen accent color.
    accent_options = _ACCENT_COLORS if overrides.get("accent_color") is not None else _UNSEEN_ACCENTS
    accent = ctx.draw_choice("accent_color", accent_options)

    grid = _bordered_grid(height, width)
    if layout == "vertical":
        _draw_vertical(ctx, grid, accent)
    elif layout == "horizontal":
        _draw_horizontal(ctx, grid, accent)
    elif layout == "cross":
        _draw_cross(ctx, grid, accent)
    else:  # draw_choice protects this, but fail loudly if metadata/code drift.
        raise RuntimeError(f"unsupported layout_style {layout!r}")
    return grid


def _full_interior_rows(grid) -> list[int]:
    h, w = len(grid), len(grid[0])
    return [
        row
        for row in range(1, h - 1)
        if all(grid[row][col] not in (0, 2) for col in range(1, w - 1))
    ]


def _full_interior_cols(grid) -> list[int]:
    h, w = len(grid), len(grid[0])
    return [
        col
        for col in range(1, w - 1)
        if all(grid[row][col] not in (0, 2) for row in range(1, h - 1))
    ]


def observe_overrides(grid) -> dict:
    """Recover every exact axis from returned pixels, never RNG bookkeeping."""
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed grid: {errors}")
    row_walls = _full_interior_rows(grid)
    col_walls = _full_interior_cols(grid)
    if len(row_walls) == 0 and len(col_walls) == 1:
        layout = "vertical"
    elif len(row_walls) == 1 and len(col_walls) == 0:
        layout = "horizontal"
    elif len(row_walls) == 1 and len(col_walls) == 1:
        layout = "cross"
    else:
        raise ValueError(
            f"cannot identify layout: full interior rows={row_walls}, cols={col_walls}"
        )
    accents = {value for row in grid for value in row if value not in (0, 2, 5)}
    if len(accents) != 1:
        raise ValueError(f"expected one accent color, found {sorted(accents)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout_style": layout,
        "accent_color": next(iter(accents)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical input grammar without requiring a disconnected zero."""
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (booleans are not colors)"]

    height = len(grid)
    errors: list[str] = []
    if not 7 <= height <= 15 or not 8 <= width <= 22:
        errors.append(f"grid shape {height}x{width} outside 7..15 by 8..22")

    palette = {value for row in grid for value in row}
    if 8 in palette:
        errors.append("input already contains output fill color 8")
    if not {0, 2, 5} <= palette:
        errors.append("input must contain floor 0, seed 2, and gray wall 5")
    accents = palette - {0, 2, 5}
    if len(accents) != 1 or not accents <= set(_ACCENT_COLORS):
        errors.append(
            f"expected one accent color from {_ACCENT_COLORS}, found {sorted(accents)}"
        )
    elif sum(value in accents for row in grid for value in row) != 1:
        errors.append("accent color must occupy exactly one cell")

    border = (
        list(grid[0]) + list(grid[-1])
        + [row[0] for row in grid[1:-1]]
        + [row[-1] for row in grid[1:-1]]
    )
    if any(value != 5 for value in border):
        errors.append("outer border must be solid gray(5)")

    seeds = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(seeds) != 1:
        errors.append(f"expected exactly one red seed, found {len(seeds)}")
    elif 0 in palette:
        reached = _region_zeros(
            grid,
            seeds[0],
            passable=lambda value: value in (0, 2),
        )
        if not reached:
            errors.append("seed chamber contains no reachable zero to transform")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "unseen_blocker_color": _critical_unseen_blocker,
    "internal_branch_pocket": _internal_branch_pocket,
}
SEMANTIC_RIVALS = {
    "canonical_blocker_palette_only": _canonical_blocker_palette_only,
    "coarse_partition_only": _coarse_partition_only,
}
WITNESS_RIVALS = {
    "unseen_blocker_color": ["canonical_blocker_palette_only"],
    "internal_branch_pocket": ["coarse_partition_only"],
}
CANONICAL_SHORTCUTS = {
    "canonical_blocker_palette_only": _canonical_blocker_palette_only,
}
LESSON_COMPETITORS = {
    "canonical_blocker_palette_only": _canonical_blocker_palette_only,
    "coarse_partition_only": _coarse_partition_only,
}
