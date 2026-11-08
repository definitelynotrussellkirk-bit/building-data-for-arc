"""Generator for ``fe54bfae4cee`` — fill equal-color straight midpoints.

The canonical lesson contains exactly two color motifs on a zero background.
A motif is active when its two equal endpoints are two cells apart in a row or
column and the midpoint is zero.  The output fills only those active
midpoints.  When a draw has one active motif, its second motif is a canonical
near miss (longer straight span, diagonal pair, or blocked midpoint).
"""
from __future__ import annotations

from typing import Iterable, NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fe54bfae4cee"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "92b2f2721622"

SUMMARY = (
    "On a sparse zero-background grid, fill a zero midpoint only when equal "
    "nonzero endpoints are exactly two cells apart horizontally or vertically. "
    "Every draw has two color motifs: one or two active pairs, and—when only "
    "one is active—a longer-span, diagonal, or blocked near miss that stays "
    "unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and the input contains exactly two nonzero colors",
    "there are exactly one or two active equal-endpoint midpoint pairs",
    "two-active-pair scenes contain one horizontal and one vertical pair",
    "one-active-pair scenes contain one structurally explicit near miss",
    "the canonical rule changes only zero midpoints of active pairs",
]

COUNTER_HYPOTHESES = [
    "copy the input unchanged",
    "fill the midpoint of any equal-color pair regardless of gap",
    "fill diagonal midpoints",
    "overwrite a nonzero midpoint",
    "use a fixed fill color instead of the endpoint color",
]

# These are the only caller-visible controls.  Every declared axis is consumed
# by GenCtx, exactly realized in the returned grid, and recoverable by
# observe_overrides().  Layout, colors, orientations, and near-miss type remain
# deterministic nuisance variation rather than misleading pseudo-axes.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed within 7..12",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed within 7..12",
        "valid": "7..12",
    },
    "pairs": {
        "type": "int",
        "default": "uniform within 1..2",
        "valid": "1..2",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


class _Pair(NamedTuple):
    color: int
    a: tuple[int, int]
    b: tuple[int, int]
    midpoint: tuple[int, int]
    orientation: str


class _Candidate(NamedTuple):
    kind: str
    orientation: str
    endpoints: tuple[tuple[int, int], tuple[int, int]]
    midpoint: tuple[int, int] | None
    occupied: tuple[tuple[int, int], ...]
    reserved: frozenset[tuple[int, int]]


def _valid_grid_shape(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and isinstance(grid[0], list)
        and bool(grid[0])
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
    )


def _fillable_pairs(grid: list[list[int]]) -> list[_Pair]:
    """Return every branch witness seen by the canonical Racket rule."""
    h, w = len(grid), len(grid[0])
    pairs: list[_Pair] = []
    for r in range(h):
        for c in range(w - 2):
            color = grid[r][c]
            if color != 0 and color == grid[r][c + 2] and grid[r][c + 1] == 0:
                pairs.append(
                    _Pair(color, (r, c), (r, c + 2), (r, c + 1), "horizontal")
                )
    for r in range(h - 2):
        for c in range(w):
            color = grid[r][c]
            if color != 0 and color == grid[r + 2][c] and grid[r + 1][c] == 0:
                pairs.append(
                    _Pair(color, (r, c), (r + 2, c), (r + 1, c), "vertical")
                )
    return pairs


def _rule_fills(grid: list[list[int]]) -> set[tuple[int, int]]:
    """Python mirror of the canonical rule's changed-cell set."""
    return {pair.midpoint for pair in _fillable_pairs(grid)}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Test-only mirror; the canonical Racket program remains authoritative."""
    if not _valid_grid_shape(grid):
        raise ValueError("rule_mirror expects a rectangular non-empty grid")
    out = [row[:] for row in grid]
    # _fillable_pairs follows the Racket program's horizontal-then-vertical
    # scan order, including the same last-write behavior for a crossed midpoint.
    for pair in _fillable_pairs(grid):
        r, c = pair.midpoint
        out[r][c] = pair.color
    return out


def _expanded(cells: Iterable[tuple[int, int]], h: int, w: int) -> frozenset[tuple[int, int]]:
    """One-cell halo used to keep the two motifs visually separable."""
    out: set[tuple[int, int]] = set()
    for r, c in cells:
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                out.add((rr, cc))
    return frozenset(out)


def _line_cells(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    ar, ac = a
    br, bc = b
    if ar == br:
        lo, hi = sorted((ac, bc))
        return [(ar, c) for c in range(lo, hi + 1)]
    if ac == bc:
        lo, hi = sorted((ar, br))
        return [(r, ac) for r in range(lo, hi + 1)]
    raise ValueError("line endpoints must share a row or column")


def _active_candidates(orientation: str, h: int, w: int) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    if orientation == "horizontal":
        for r in range(h):
            for c in range(w - 2):
                a, b, mid = (r, c), (r, c + 2), (r, c + 1)
                path = _line_cells(a, b)
                candidates.append(
                    _Candidate(
                        "active",
                        orientation,
                        (a, b),
                        mid,
                        (a, b),
                        _expanded(path, h, w),
                    )
                )
    else:
        for r in range(h - 2):
            for c in range(w):
                a, b, mid = (r, c), (r + 2, c), (r + 1, c)
                path = _line_cells(a, b)
                candidates.append(
                    _Candidate(
                        "active",
                        orientation,
                        (a, b),
                        mid,
                        (a, b),
                        _expanded(path, h, w),
                    )
                )
    return candidates


def _near_miss_candidates(
    kind: str,
    target_orientation: str,
    h: int,
    w: int,
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    opposite = "vertical" if target_orientation == "horizontal" else "horizontal"

    if kind == "longspan":
        gap = 3
        if opposite == "horizontal":
            for r in range(h):
                for c in range(w - gap):
                    a, b = (r, c), (r, c + gap)
                    candidates.append(
                        _Candidate(
                            kind,
                            opposite,
                            (a, b),
                            None,
                            (a, b),
                            _expanded(_line_cells(a, b), h, w),
                        )
                    )
        else:
            for r in range(h - gap):
                for c in range(w):
                    a, b = (r, c), (r + gap, c)
                    candidates.append(
                        _Candidate(
                            kind,
                            opposite,
                            (a, b),
                            None,
                            (a, b),
                            _expanded(_line_cells(a, b), h, w),
                        )
                    )
        return candidates

    if kind == "blocked":
        # Same geometry as an active pair, but its midpoint is occupied by the
        # other motif's color and therefore must not be overwritten.
        for active in _active_candidates(opposite, h, w):
            assert active.midpoint is not None
            occupied = active.endpoints + (active.midpoint,)
            candidates.append(
                _Candidate(
                    kind,
                    opposite,
                    active.endpoints,
                    active.midpoint,
                    occupied,
                    active.reserved,
                )
            )
        return candidates

    if kind == "diagonal":
        # A clear two-by-two diagonal displacement: equal colors, but not a
        # straight row/column relation recognized by the rule.
        for r in range(h):
            for c in range(w):
                for dr, dc in ((2, 2), (2, -2)):
                    r2, c2 = r + dr, c + dc
                    if not (0 <= r2 < h and 0 <= c2 < w):
                        continue
                    a, b = (r, c), (r2, c2)
                    rlo, rhi = sorted((r, r2))
                    clo, chi = sorted((c, c2))
                    footprint = [
                        (rr, cc)
                        for rr in range(rlo, rhi + 1)
                        for cc in range(clo, chi + 1)
                    ]
                    candidates.append(
                        _Candidate(
                            kind,
                            "diagonal",
                            (a, b),
                            None,
                            (a, b),
                            _expanded(footprint, h, w),
                        )
                    )
        return candidates

    raise ValueError(f"unknown near-miss kind: {kind}")


def _write_candidate(
    grid: list[list[int]],
    candidate: _Candidate,
    endpoint_color: int,
    *,
    blocker_color: int | None = None,
) -> None:
    for r, c in candidate.endpoints:
        grid[r][c] = endpoint_color
    if candidate.kind == "blocked":
        if blocker_color is None or candidate.midpoint is None:
            raise ValueError("blocked motif requires a midpoint blocker color")
        r, c = candidate.midpoint
        grid[r][c] = blocker_color


def _nonzero_components(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    stack.append((rr, cc))
    return count


def _scene_errors(grid: list[list[int]]) -> list[str]:
    """Strict canonical-shape recognizer shared by self_check and tests."""
    errors: list[str] = []
    if not _valid_grid_shape(grid):
        return ["expected a non-empty rectangular list-of-lists grid"]

    h, w = len(grid), len(grid[0])
    if not (7 <= h <= 12 and 7 <= w <= 12):
        errors.append(f"expected dimensions in 7..12, got {h}x{w}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))

    if len(positions) != 2:
        errors.append(f"expected exactly two nonzero colors, got {len(positions)}")
        return errors

    nonzero_count = sum(len(cells) for cells in positions.values())
    if nonzero_count not in (4, 5):
        errors.append(f"expected 4 or 5 nonzero cells, got {nonzero_count}")

    pairs = _fillable_pairs(grid)
    if len(pairs) not in (1, 2):
        errors.append(f"expected one or two active midpoint pairs, got {len(pairs)}")
        return errors
    if len({pair.midpoint for pair in pairs}) != len(pairs):
        errors.append("multiple active pairs share one midpoint")
        return errors

    if len(pairs) == 2:
        if nonzero_count != 4:
            errors.append("two-active-pair scenes must contain exactly four endpoints")
        if {pair.orientation for pair in pairs} != {"horizontal", "vertical"}:
            errors.append("two-active-pair scenes need one horizontal and one vertical pair")
        if len({pair.color for pair in pairs}) != 2:
            errors.append("the two active pairs must use distinct colors")
        if sorted(len(cells) for cells in positions.values()) != [2, 2]:
            errors.append("each active-pair color must occur exactly twice")
        if _nonzero_components(grid) != 4:
            errors.append("the four canonical endpoints must be isolated input objects")
        return errors

    pair = pairs[0]
    target_color = pair.color
    other_colors = [color for color in positions if color != target_color]
    if len(other_colors) != 1:
        errors.append("one-active-pair scene must have one distinct near-miss color")
        return errors
    decoy_color = other_colors[0]
    target_cells = positions[target_color]
    decoy_cells = positions[decoy_color]
    if len(decoy_cells) != 2:
        errors.append("near-miss endpoint color must occur exactly twice")
        return errors

    (r1, c1), (r2, c2) = decoy_cells
    dr, dc = abs(r1 - r2), abs(c1 - c2)
    opposite = "vertical" if pair.orientation == "horizontal" else "horizontal"

    is_longspan = (
        len(target_cells) == 2
        and (
            (opposite == "horizontal" and dr == 0 and dc == 3)
            or (opposite == "vertical" and dc == 0 and dr == 3)
        )
    )
    is_diagonal = len(target_cells) == 2 and dr == 2 and dc == 2

    is_blocked = False
    if len(target_cells) == 3:
        if opposite == "horizontal" and dr == 0 and dc == 2:
            midpoint = (r1, min(c1, c2) + 1)
            is_blocked = grid[midpoint[0]][midpoint[1]] == target_color
        elif opposite == "vertical" and dc == 0 and dr == 2:
            midpoint = (min(r1, r2) + 1, c1)
            is_blocked = grid[midpoint[0]][midpoint[1]] == target_color

    if not (is_longspan or is_diagonal or is_blocked):
        errors.append(
            "second motif is not a valid long-span, diagonal, or blocked near miss"
        )
    expected_components = 3 if is_blocked else 4
    if _nonzero_components(grid) != expected_components:
        errors.append(
            f"expected {expected_components} isolated/blocked input objects for this scene"
        )
    return errors


def _near_miss_kind(difficulty, rng) -> str:
    if difficulty == "easy":
        return "longspan"
    if difficulty == "hard":
        return rng.choice(("longspan", "diagonal", "blocked"))
    return rng.choice(("longspan", "diagonal"))


def _build_scene(
    h: int,
    w: int,
    pair_count: int,
    colors: tuple[int, int],
    difficulty,
    rng,
) -> list[list[int]]:
    orientations = ["horizontal", "vertical"]
    rng.shuffle(orientations)

    if pair_count == 2:
        first = _active_candidates(orientations[0], h, w)
        second = _active_candidates(orientations[1], h, w)
        rng.shuffle(first)
        rng.shuffle(second)
        for left in first:
            for right in second:
                if left.reserved & right.reserved:
                    continue
                grid = full_grid(h, w, 0)
                _write_candidate(grid, left, colors[0])
                _write_candidate(grid, right, colors[1])
                if not _scene_errors(grid):
                    return grid
        raise RuntimeError(f"could not place two active motifs in {h}x{w}")

    target_orientation = orientations[0]
    near_kind = _near_miss_kind(difficulty, rng)
    targets = _active_candidates(target_orientation, h, w)
    decoys = _near_miss_candidates(near_kind, target_orientation, h, w)
    rng.shuffle(targets)
    rng.shuffle(decoys)
    for target in targets:
        for decoy in decoys:
            if target.reserved & decoy.reserved:
                continue
            grid = full_grid(h, w, 0)
            _write_candidate(grid, target, colors[0])
            _write_candidate(
                grid,
                decoy,
                colors[1],
                blocker_color=colors[0],
            )
            # In blocked scenes the blocker reuses the target color.  This gate
            # prevents that cell from accidentally introducing another active
            # pair with either target endpoint.
            if len(_fillable_pairs(grid)) != 1:
                continue
            if not _scene_errors(grid):
                return grid
    raise RuntimeError(
        f"could not place active + {near_kind} motifs in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Full declared bounds are valid in every difficulty band; draw_int_diff
    # changes only the default prior and never makes a legal override illegal.
    h = ctx.draw_int_diff("grid_h", 7, 12)
    w = ctx.draw_int_diff("grid_w", 7, 12)
    pair_count = ctx.draw_int("pairs", 1, 2)
    colors = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    rng = ctx.draw_rng("layout")
    return _build_scene(h, w, pair_count, colors, difficulty, rng)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from a returned grid."""
    if not _valid_grid_shape(grid):
        raise ValueError("cannot observe overrides on a ragged/non-grid value")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "pairs": len(_fillable_pairs(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject grids that do not encode the canonical two-motif lesson."""
    del difficulty, meta
    return _scene_errors(grid)
