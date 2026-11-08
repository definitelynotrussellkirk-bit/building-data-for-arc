"""Input sampler for ``arc_additional_puzzle_bank_volume4:E25``.

The selected Racket authority owns labels.  This module samples lawful inputs
for the task: every magenta (6) singleton moves one cell down and one cell to
the right, its source cell is erased, and every gray (5) cell stays fixed.

The four declared controls are deliberately recoverable from returned pixels.
No texture/palette aliases or diagnostic degenerates are accepted.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "95b47c355ae4"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "76edf9516933"
SUMMARY = "Move isolated magenta cells one step down-right while gray cells remain fixed."
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "8..10 rows and columns; colors are exactly drawn from {0, 5, 6}",
    "3..7 isolated color-6 source cells, each with an empty in-bounds down-right target",
    "3..12 color-5 decoration cells disjoint from every source and target",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 8|9|10", "valid": "8..10"},
    "grid_w": {"type": "int", "default": "scheduled 8|9|10", "valid": "8..10"},
    "n_6_cells": {"type": "int", "default": "scheduled 3..7", "valid": "3..7"},
    "n_5_cells": {"type": "int", "default": "scheduled 3..12", "valid": "3..12"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []

_DIMENSIONS = (8, 9, 10)
_N6_VALUES = tuple(range(3, 8))
_N5_VALUES = tuple(range(3, 13))
_N6_SCHEDULE = (3, 5, 4, 6, 7, 5)
_N5_SCHEDULE = (3, 7, 8, 9, 11, 12, 5, 10, 6, 4)
_BAND_PHASE = {None: 0, "easy": 0, "medium": 1, "hard": 2}
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _controls(overrides: dict) -> dict[str, int]:
    """Validate the complete public override surface without coercion."""
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    active = {name: value for name, value in overrides.items() if value is not None}
    domains = {
        "grid_h": _DIMENSIONS,
        "grid_w": _DIMENSIONS,
        "n_6_cells": _N6_VALUES,
        "n_5_cells": _N5_VALUES,
    }
    for name, value in active.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or a coercible value)")
        if value not in domains[name]:
            lo, hi = min(domains[name]), max(domains[name])
            raise ValueError(f"{name} must be in {lo}..{hi}; got {value}")
    return active


def _draw_scheduled(ctx, name: str, domain: tuple[int, ...], preferred: int) -> int:
    """Use a keyed draw while making the default curriculum deterministic.

    Explicit controls see the entire declared domain, so every legal boundary
    and every legal joint combination retains normal GenCtx provenance.
    """
    options: Iterable[int]
    options = domain if name in ctx.overrides else (preferred,)
    return ctx.draw_choice(name, tuple(options))


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in _NEIGHBORS4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
    return count


def _scattered_cells(
    free: set[tuple[int, int]], n: int, rng
) -> set[tuple[int, int]]:
    """Prefer separated gray cells, then fill any remaining quota."""
    order = list(free)
    rng.shuffle(order)
    chosen: set[tuple[int, int]] = set()
    for cell in order:
        if all((cell[0] + dr, cell[1] + dc) not in chosen for dr, dc in _NEIGHBORS4):
            chosen.add(cell)
            if len(chosen) == n:
                return chosen
    remainder = [cell for cell in order if cell not in chosen]
    chosen.update(remainder[: n - len(chosen)])
    return chosen


def _grown_cells(
    free: set[tuple[int, int]], n: int, rng, seed_count: int
) -> set[tuple[int, int]]:
    """Grow one or more connected gray components inside the free canvas."""
    order = list(free)
    rng.shuffle(order)
    chosen: set[tuple[int, int]] = set(order[: min(seed_count, n)])
    while len(chosen) < n:
        frontier = {
            (r + dr, c + dc)
            for r, c in chosen
            for dr, dc in _NEIGHBORS4
            if (r + dr, c + dc) in free and (r + dr, c + dc) not in chosen
        }
        if frontier:
            options = sorted(frontier)
            chosen.add(options[rng.randrange(len(options))])
            continue
        remainder = sorted(free - chosen)
        chosen.add(remainder[rng.randrange(len(remainder))])
    return chosen


def _gray_cells(
    free: set[tuple[int, int]], n: int, mode: int, rng
) -> set[tuple[int, int]]:
    """Sample varied but exact gray topology; all branches have a safe fallback."""
    if n > len(free):
        raise ValueError(f"cannot place {n} gray cells in {len(free)} free positions")
    if mode == 0:
        return _scattered_cells(free, n, rng)
    if mode == 1:
        return _grown_cells(free, n, rng, seed_count=1)
    if mode == 2:
        return _grown_cells(free, n, rng, seed_count=2)
    if mode == 3:
        return _grown_cells(free, n, rng, seed_count=min(3, n))
    if mode == 4:
        # Compare random candidates and keep one with an intermediate number
        # of components.  This creates small blobs plus singletons without
        # making a brittle hand-authored placement template.
        best: set[tuple[int, int]] | None = None
        best_score: tuple[int, tuple[tuple[int, int], ...]] | None = None
        target = max(2, min(n - 1, n // 2))
        ordered = list(free)
        for _ in range(24):
            candidate = set(rng.sample(ordered, n))
            score = (abs(_component_count(candidate) - target), tuple(sorted(candidate)))
            if best_score is None or score < best_score:
                best, best_score = candidate, score
        return best or set(rng.sample(ordered, n))
    return set(rng.sample(sorted(free), n))



def _source_compatible(
    cell: tuple[int, int], selected: set[tuple[int, int]]
) -> bool:
    """Whether a source and its target remain disjoint from chosen sources."""
    r, c = cell
    target = (r + 1, c + 1)
    selected_targets = {(rr + 1, cc + 1) for rr, cc in selected}
    if cell in selected_targets or target in selected:
        return False
    return all(abs(r - rr) + abs(c - cc) != 1 for rr, cc in selected)


def _source_cells(h: int, w: int, n: int, rng) -> set[tuple[int, int]]:
    """Choose scattered lawful sources with visible row/column parity variation.

    One left-edge source keeps clipping/direction alternatives observable.  A
    second forced source uses the opposite row parity and an odd column, which
    rules out the accidental one-lattice curriculum of the legacy repair.
    Remaining cells are selected greedily under source/target disjointness; the
    bounded retries are deterministic under the keyed RNG.
    """
    pool = [(r, c) for r in range(h - 1) for c in range(w - 1)]
    anchors = [cell for cell in pool if cell[1] == 0]
    rng.shuffle(anchors)
    for anchor in anchors:
        diversifiers = [
            cell
            for cell in pool
            if cell[1] % 2 == 1
            and cell[0] % 2 != anchor[0] % 2
            and _source_compatible(cell, {anchor})
        ]
        rng.shuffle(diversifiers)
        for diversifier in diversifiers:
            for _ in range(24):
                order = [cell for cell in pool if cell not in (anchor, diversifier)]
                rng.shuffle(order)
                selected = {anchor, diversifier}
                for cell in order:
                    if _source_compatible(cell, selected):
                        selected.add(cell)
                        if len(selected) == n:
                            return selected
    raise RuntimeError(f"unable to place {n} lawful source cells on {h}x{w}")

def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )

    phase = _BAND_PHASE.get(difficulty, 0)
    h_pref = _DIMENSIONS[(sample_index + phase) % len(_DIMENSIONS)]
    # Defaults stay square to recur on every canonical exact profile.  The two
    # dimensions remain independent under explicit controls.
    w_pref = h_pref
    n6_pref = _N6_SCHEDULE[(sample_index + phase) % len(_N6_SCHEDULE)]
    n5_pref = _N5_SCHEDULE[(sample_index + 2 * phase) % len(_N5_SCHEDULE)]

    h = _draw_scheduled(ctx, "grid_h", _DIMENSIONS, h_pref)
    w = _draw_scheduled(ctx, "grid_w", _DIMENSIONS, w_pref)
    n6 = _draw_scheduled(ctx, "n_6_cells", _N6_VALUES, n6_pref)
    n5 = _draw_scheduled(ctx, "n_5_cells", _N5_VALUES, n5_pref)

    grid = full_grid(h, w, 0)

    # Sources are 4-isolated and disjoint from every (+1,+1) target.  Each
    # scene contains both row parities and both column parities, plus a c=0
    # source, so parity-filtered and down-left/clipping shortcuts are visible.
    source_rng = ctx.draw_rng("source_positions")
    sources = _source_cells(h, w, n6, source_rng)
    targets = {(r + 1, c + 1) for r, c in sources}

    free = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in sources and (r, c) not in targets
    }
    gray_rng = ctx.draw_rng("gray_positions")
    gray = _gray_cells(free, n5, (sample_index + phase) % 6, gray_rng)

    for r, c in gray:
        grid[r][c] = 5
    for r, c in sources:
        grid[r][c] = 6
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared control from rendered pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_6_cells": sum(value == 6 for row in grid for value in row),
        "n_5_cells": sum(value == 5 for row in grid for value in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return reasons when a grid falls outside the actual task domain."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["grid must be a nonempty rectangular sequence"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or value not in (0, 5, 6) for row in grid for value in row):
        return ["cells must be integer colors from {0,5,6} (not booleans)"]

    h, w = len(grid), width
    errors: list[str] = []
    if h not in _DIMENSIONS or w not in _DIMENSIONS:
        errors.append("dimensions must each be in 8..10")

    sixes = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6}
    n5 = sum(value == 5 for row in grid for value in row)
    if not 3 <= len(sixes) <= 7:
        errors.append(f"expected 3..7 color-6 source cells; got {len(sixes)}")
    if not 3 <= n5 <= 12:
        errors.append(f"expected 3..12 color-5 decoration cells; got {n5}")

    touching = [
        (r, c)
        for r, c in sixes
        if any((r + dr, c + dc) in sixes for dr, dc in _NEIGHBORS4)
    ]
    if touching:
        errors.append("color-6 source cells must be 4-neighbor isolated")

    for r, c in sorted(sixes):
        nr, nc = r + 1, c + 1
        if nr >= h or nc >= w:
            errors.append(f"color-6 source {(r, c)} has an out-of-bounds target")
        elif grid[nr][nc] != 0:
            errors.append(f"color-6 source {(r, c)} has a nonempty target {(nr, nc)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-domain membership, separate from exact canonical profile scoring."""
    return self_check(grid)


def _reference_output(grid):
    """Independent Python oracle used only by tests and semantic rivals."""
    output = [list(row) for row in grid]
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    for r, c in sources:
        output[r][c] = 0
    h, w = len(output), len(output[0])
    for r, c in sources:
        if r + 1 < h and c + 1 < w:
            output[r + 1][c + 1] = 6
    return output


def _identity(grid):
    return [list(row) for row in grid]


def _copy_down_right(grid):
    """Wrong shortcut: add targets but forget to erase sources."""
    output = [list(row) for row in grid]
    h, w = len(output), len(output[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 6 and r + 1 < h and c + 1 < w:
                output[r + 1][c + 1] = 6
    return output


def _move_down_left(grid):
    """Wrong diagonal direction; left-edge sources make clipping observable."""
    output = [list(row) for row in grid]
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    for r, c in sources:
        output[r][c] = 0
    h = len(output)
    for r, c in sources:
        if r + 1 < h and c - 1 >= 0:
            output[r + 1][c - 1] = 6
    return output


def _move_all_nonzero_down_right(grid):
    """Wrong scope: move gray decorations as well as magenta sources."""
    h, w = len(grid), len(grid[0])
    output = full_grid(h, w, 0)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value and r + 1 < h and c + 1 < w:
                output[r + 1][c + 1] = value
    return output



def _move_selected_sources(grid, predicate):
    """Wrong-family helper: transform only sources accepted by predicate."""
    output = [list(row) for row in grid]
    sources = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    ]
    selected = [(r, c) for r, c in sources if predicate(r, c)]
    for r, c in selected:
        output[r][c] = 0
    h, w = len(output), len(output[0])
    for r, c in selected:
        if r + 1 < h and c + 1 < w:
            output[r + 1][c + 1] = 6
    return output


def _move_even_columns_only(grid):
    return _move_selected_sources(grid, lambda _r, c: c % 2 == 0)


def _move_even_rows_only(grid):
    return _move_selected_sources(grid, lambda r, _c: r % 2 == 0)

def _lawful_with_sources(grid) -> bool:
    return not self_check(grid) and any(value == 6 for row in grid for value in row)


def _left_edge_direction_witness(grid) -> bool:
    return not self_check(grid) and any(row[0] == 6 for row in grid)


def _static_gray_witness(grid) -> bool:
    return not self_check(grid) and any(value == 5 for row in grid for value in row)


def _both_source_column_parities(grid) -> bool:
    if self_check(grid):
        return False
    columns = {c % 2 for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6}
    return columns == {0, 1}


def _both_source_row_parities(grid) -> bool:
    if self_check(grid):
        return False
    rows = {r % 2 for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6}
    return rows == {0, 1}


SEMANTIC_WITNESSES = {
    "source_erasure_is_visible": _lawful_with_sources,
    "down_right_direction_is_visible": _left_edge_direction_witness,
    "gray_cells_are_static": _static_gray_witness,
    "both_source_column_parities": _both_source_column_parities,
    "both_source_row_parities": _both_source_row_parities,
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "copy_without_erasing": _copy_down_right,
    "move_down_left": _move_down_left,
    "move_all_nonzero": _move_all_nonzero_down_right,
    "move_even_columns_only": _move_even_columns_only,
    "move_even_rows_only": _move_even_rows_only,
}
WITNESS_RIVALS = {
    "source_erasure_is_visible": ["identity", "copy_without_erasing"],
    "down_right_direction_is_visible": ["move_down_left"],
    "gray_cells_are_static": ["move_all_nonzero"],
    "both_source_column_parities": ["move_even_columns_only"],
    "both_source_row_parities": ["move_even_rows_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Finite named-rival lesson check; no universal uniqueness claim."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
