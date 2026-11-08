"""Generator for arc_puzzle_bank_sixth21:E37.

Rule: transpose the complete square grid across its main diagonal.  The
canonical inputs are sparse colored partial-permutation matrices: every
non-background color occurs once and occupied rows/columns are unique.

The generator deliberately varies which side of the diagonal contains the
moving cells, whether one diagonal fixed point is present, and whether an
off-diagonal corner is occupied.  Every ordinary sample has a unique D4
interpretation for the official transpose answer.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c86f5a19e34d"
VERSION = "2.0.0"
TASK_ID = "c86f5a19e34d"
RULE_HASH = "f5d00e3992ee"
SUMMARY = (
    "Transpose a sparse square grid across the main diagonal. Normal inputs "
    "contain 3-8 uniquely colored cells with at most one cell per row and "
    "column; moving cells may lie above, below, or on both sides of the "
    "diagonal, and an optional single diagonal cell is a fixed point."
)
INVARIANTS = [
    "grid is square with side 5..10",
    "background is 0 and every nonzero color occurs exactly once",
    "occupied rows and occupied columns are unique",
    "at least two cells move under main-diagonal transpose",
    "the transpose answer is distinct from every other D4 transform",
]

PALETTE_KINDS = ("broad", "warm", "cool", "primary")
POSITION_BIASES = ("upper", "lower", "mixed")

# Pairwise derangements make palette_kind visibly effective for every sampled
# color index without changing the task's color-agnostic rule.
_PALETTES = {
    "broad": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 5, 6, 7, 8, 9, 1),
    "cool": (3, 4, 5, 6, 7, 8, 9, 1, 2),
    "primary": (4, 5, 6, 7, 8, 9, 1, 2, 3),
}

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-aware rng 5..10",
        "valid": "5..10",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-aware rng 3..8, capped by grid_n",
        "valid": "3..8",
    },
    "palette_kind": {
        "type": "enum",
        "default": "rng",
        "valid": "|".join(PALETTE_KINDS),
    },
    "position_bias": {
        "type": "enum",
        "default": "rng",
        "valid": "|".join(POSITION_BIASES),
    },
    "anchor_corner": {
        "type": "bool",
        "default": "rng",
        "valid": "true|false",
    },
    "include_diagonal": {
        "type": "bool",
        "default": "rng",
        "valid": "true|false",
    },
}


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)]


def _d4_transforms(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    n = len(grid)
    return {
        "identity": [row[:] for row in grid],
        "rotate_90": [[grid[n - 1 - c][r] for c in range(n)] for r in range(n)],
        "rotate_180": [
            [grid[n - 1 - r][n - 1 - c] for c in range(n)]
            for r in range(n)
        ],
        "rotate_270": [[grid[c][n - 1 - r] for c in range(n)] for r in range(n)],
        "flip_lr": [list(reversed(row)) for row in grid],
        "flip_ud": [row[:] for row in reversed(grid)],
        "transpose": _transpose(grid),
        "anti_transpose": [
            [grid[n - 1 - c][n - 1 - r] for c in range(n)]
            for r in range(n)
        ],
    }


def _unique_transpose_answer(grid: list[list[int]]) -> bool:
    transforms = _d4_transforms(grid)
    answer = transforms["transpose"]
    return all(
        candidate != answer
        for name, candidate in transforms.items()
        if name != "transpose"
    )


def _anchor_corners(n: int) -> set[tuple[int, int]]:
    return {(0, n - 1), (n - 1, 0)}


def _position_side(r: int, c: int) -> str:
    if r < c:
        return "upper"
    if r > c:
        return "lower"
    return "diagonal"


def _candidate_positions(
    n: int,
    position_bias: str,
    *,
    anchor_corner: bool,
    include_diagonal: bool,
) -> list[tuple[int, int]]:
    anchors = _anchor_corners(n)
    positions: list[tuple[int, int]] = []
    for r in range(n):
        for c in range(n):
            side = _position_side(r, c)
            if side == "diagonal":
                # Diagonal edge corners are excluded so anchor_corner has one
                # exact, observable meaning. Interior diagonal cells are legal.
                if not include_diagonal or r in {0, n - 1}:
                    continue
            elif position_bias != "mixed" and side != position_bias:
                continue
            if (r, c) in anchors and not anchor_corner:
                continue
            positions.append((r, c))
    return positions


def _support_is_valid(
    support: Iterable[tuple[int, int]],
    *,
    n: int,
    count: int,
    position_bias: str,
    anchor_corner: bool,
    include_diagonal: bool,
) -> bool:
    cells = list(support)
    if len(cells) != count or len(set(cells)) != count:
        return False
    if len({r for r, _ in cells}) != count:
        return False
    if len({c for _, c in cells}) != count:
        return False
    cell_set = set(cells)
    if any(r != c and (c, r) in cell_set for r, c in cells):
        return False

    diag_count = sum(r == c for r, c in cells)
    if diag_count != int(include_diagonal):
        return False
    if (bool(cell_set & _anchor_corners(n))) != anchor_corner:
        return False

    sides = {_position_side(r, c) for r, c in cells if r != c}
    if position_bias == "upper" and sides != {"upper"}:
        return False
    if position_bias == "lower" and sides != {"lower"}:
        return False
    if position_bias == "mixed" and not {"upper", "lower"} <= sides:
        return False
    return True


@lru_cache(maxsize=None)
def _support_pool(
    n: int,
    count: int,
    position_bias: str,
    anchor_corner: bool,
    include_diagonal: bool,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Build a bounded deterministic pool of lawful supports for a profile.

    The old rejection sampler could spend thousands of attempts on tight
    boundary combinations. This row-wise matching search is cached per
    profile, uses only local stable RNG for traversal order, and stops after
    256 witnesses—enough variation without making override audits expensive.
    """
    candidates = _candidate_positions(
        n,
        position_bias,
        anchor_corner=anchor_corner,
        include_diagonal=include_diagonal,
    )
    by_row: dict[int, list[tuple[int, int]]] = {r: [] for r in range(n)}
    for cell in candidates:
        by_row[cell[0]].append(cell)

    order_rng = stable_rng(
        n * 100 + count,
        f"support-pool|{position_bias}|{anchor_corner}|{include_diagonal}",
        VERSION,
    )
    rows = list(range(n))
    order_rng.shuffle(rows)
    for row in rows:
        order_rng.shuffle(by_row[row])

    out: list[tuple[tuple[int, int], ...]] = []
    selected: list[tuple[int, int]] = []
    selected_set: set[tuple[int, int]] = set()

    def visit(row_index: int, used_cols: int) -> None:
        if len(out) >= 256:
            return
        remaining_rows = len(rows) - row_index
        need = count - len(selected)
        if need < 0 or need > remaining_rows:
            return
        if row_index == len(rows):
            if _support_is_valid(
                selected,
                n=n,
                count=count,
                position_bias=position_bias,
                anchor_corner=anchor_corner,
                include_diagonal=include_diagonal,
            ):
                out.append(tuple(sorted(selected)))
            return

        row = rows[row_index]
        options = by_row[row]
        # Prefer placing a cell while cells are still needed; the explicit
        # skip branch keeps arbitrary row subsets reachable.
        for cell in options:
            r, c = cell
            if used_cols & (1 << c):
                continue
            if r != c and (c, r) in selected_set:
                continue
            selected.append(cell)
            selected_set.add(cell)
            visit(row_index + 1, used_cols | (1 << c))
            selected_set.remove(cell)
            selected.pop()
            if len(out) >= 256:
                return
        visit(row_index + 1, used_cols)

    visit(0, 0)
    # Different row traversal paths can reach the same sorted support.
    unique = tuple(dict.fromkeys(out))
    return unique


def _draw_support(
    rng,
    n: int,
    count: int,
    position_bias: str,
    anchor_corner: bool,
    include_diagonal: bool,
) -> list[tuple[int, int]]:
    pool = _support_pool(
        n,
        count,
        position_bias,
        anchor_corner,
        include_diagonal,
    )
    if not pool:
        raise ValueError(
            "no lawful sparse transpose support for requested combination: "
            f"grid_n={n}, n_cells={count}, position_bias={position_bias}, "
            f"anchor_corner={anchor_corner}, include_diagonal={include_diagonal}"
        )
    return list(rng.choice(pool))


def _validate_unknown_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_unknown_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Draw the categorical geometry first so numeric bounds describe a
    # feasible domain rather than recording a value that placement later
    # shrinks. A corner-anchored one-sided partial permutation needs two
    # unused rows/columns; every other profile needs one.
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    position_bias = ctx.draw_choice("position_bias", POSITION_BIASES)
    anchor_corner = ctx.draw_choice("anchor_corner", (False, True))
    include_diagonal = ctx.draw_choice("include_diagonal", (False, True))
    slack = 2 if position_bias in {"upper", "lower"} and anchor_corner else 1

    requested_count = overrides.get("n_cells")
    if requested_count is not None:
        requested_count = int(requested_count)
        if not 3 <= requested_count <= 8:
            raise ValueError("n_cells override must be in 3..8")

    if "grid_n" in overrides:
        n_lo, n_hi = 5, 10
    elif difficulty == "easy":
        n_lo, n_hi = 5, 7
    elif difficulty == "hard":
        n_lo, n_hi = 8, 10
    else:
        n_lo, n_hi = 6, 9
    if requested_count is not None:
        n_lo = max(n_lo, requested_count + slack)
        n_hi = max(n_hi, n_lo)
    n = ctx.draw_int("grid_n", n_lo, n_hi)

    max_count = min(8, n - slack)
    if max_count < 3:
        raise ValueError(
            "grid_n is too small for the requested position/anchor profile"
        )
    if "n_cells" in overrides:
        count_lo, count_hi = 3, max_count
    elif difficulty == "easy":
        count_lo, count_hi = 3, min(5, max_count)
    elif difficulty == "hard":
        count_lo, count_hi = max(3, min(6, max_count)), max_count
    else:
        count_lo, count_hi = max(3, min(4, max_count)), min(7, max_count)
    count = ctx.draw_int("n_cells", count_lo, count_hi)

    rng = ctx.draw_rng("layout")
    for _ in range(200):
        support = _draw_support(
            rng,
            n,
            count,
            position_bias,
            anchor_corner,
            include_diagonal,
        )
        palette = _PALETTES[palette_kind]
        colors = rng.sample(list(palette), count)
        grid = full_grid(n, n, 0)
        for (r, c), color in zip(support, colors):
            grid[r][c] = color
        if _unique_transpose_answer(grid):
            return grid

    raise ValueError("failed to draw a uniquely identifiable transpose instance")


def observe_overrides(grid) -> dict[str, int | str | bool]:
    n = len(grid)
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    offdiag_sides = {_position_side(r, c) for r, c in cells if r != c}
    if offdiag_sides == {"upper"}:
        position_bias = "upper"
    elif offdiag_sides == {"lower"}:
        position_bias = "lower"
    else:
        position_bias = "mixed"
    return {
        "grid_n": n,
        "n_cells": len(cells),
        "position_bias": position_bias,
        "anchor_corner": bool(set(cells) & _anchor_corners(n)),
        "include_diagonal": any(r == c for r, c in cells),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical sparse partial-permutation teaching grammar."""
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, list) and row for row in grid):
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid is ragged"]
    n = len(grid)
    if n != width:
        errors.append(f"grid is not square: {n}x{width}")
        return errors
    if not 5 <= n <= 10:
        errors.append(f"grid side {n} outside canonical teaching range 5..10")

    bad_values = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if bad_values:
        errors.append("grid contains non-integer or out-of-range colors")
        return errors

    cells = [
        (r, c, grid[r][c])
        for r in range(n)
        for c in range(n)
        if grid[r][c] != 0
    ]
    if not 3 <= len(cells) <= min(8, n - 1):
        errors.append(
            f"nonzero count {len(cells)} outside sparse range 3..{min(8, n - 1)}"
        )
    colors = [value for _, _, value in cells]
    if len(set(colors)) != len(colors):
        errors.append("every nonzero color must occur exactly once")
    if len({r for r, _, _ in cells}) != len(cells):
        errors.append("more than one nonzero cell occupies a row")
    if len({c for _, c, _ in cells}) != len(cells):
        errors.append("more than one nonzero cell occupies a column")

    support = {(r, c) for r, c, _ in cells}
    diagonal = [(r, c) for r, c in support if r == c]
    if len(diagonal) > 1:
        errors.append("more than one diagonal fixed point")
    offdiag = [(r, c) for r, c in support if r != c]
    if len(offdiag) < 2:
        errors.append("fewer than two cells move under transpose")
    if any((c, r) in support for r, c in offdiag):
        errors.append("input contains a pre-existing transpose partner")
    if not errors and not _unique_transpose_answer(grid):
        errors.append("transpose answer is not unique among D4 transforms")
    return errors
