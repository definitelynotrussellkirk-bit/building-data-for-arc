"""Generator for arc_additional_puzzle_bank_volume4:E27.

Builds sparse green-on-black scenes containing several exact diagonal triggers
for the canonical 2x2-square completion rule, plus lawful non-trigger green
cells that rule out broad "grow every green object" shortcuts.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "60d5b73ff222"
VERSION = "3.0.0"
TASK_ID = "60d5b73ff222"
RULE_HASH = "041ed405f52e"
SUMMARY = (
    "Sparse 0-background grids contain 3-6 non-overlapping 2x2 windows with "
    "two green(3) cells on exactly one diagonal; the rule fills the opposite "
    "diagonal, while a three-green blocked-diagonal decoy and other green "
    "distractors remain unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the only colors are background 0 and green 3",
    "there are exactly 3-6 active diagonal-pair windows and both diagonal orientations occur",
    "active 2x2 windows do not overlap; at least one touches the border and one is interior",
    "normal generated draws include a three-green 2x2 decoy whose occupied third corner blocks completion",
    "there are 1-5 green distractor cells outside all active diagonal pairs, and no 2x2 is already full",
    "the canonical rule changes every active pair into a filled green 2x2 square and leaves distractors unchanged",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 7..9; medium 9..11; hard 11..14",
        "valid": "7..14",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 7..9; medium 9..11; hard 11..14",
        "valid": "7..14",
        "doc": "Returned grid width.",
    },
    "n_pairs": {
        "type": "int",
        "default": "easy 3..4; medium 4..5; hard 5..6",
        "valid": "3..6",
        "doc": "Exact number of active diagonal-pair 2x2 windows.",
    },
}

_VALID_BOUNDS = {
    "grid_h": (7, 14),
    "grid_w": (7, 14),
    "n_pairs": (3, 6),
}
_BAND_BOUNDS = {
    "easy": {"grid_h": (7, 9), "grid_w": (7, 9), "n_pairs": (3, 4)},
    "medium": {"grid_h": (9, 11), "grid_w": (9, 11), "n_pairs": (4, 5)},
    "hard": {"grid_h": (11, 14), "grid_w": (11, 14), "n_pairs": (5, 6)},
}

Target = tuple[int, int, str]
Cell = tuple[int, int]


def _target_at(grid: list[list[int]], r: int, c: int) -> str | None:
    """Return the active orientation at one 2x2 anchor, if any."""
    a = grid[r][c]
    b = grid[r][c + 1]
    d = grid[r + 1][c]
    e = grid[r + 1][c + 1]
    if (a, b, d, e) == (3, 0, 0, 3):
        return "main"
    if (a, b, d, e) == (0, 3, 3, 0):
        return "anti"
    return None


def _find_targets(grid: list[list[int]]) -> list[Target]:
    h, w = len(grid), len(grid[0])
    return [
        (r, c, orientation)
        for r in range(h - 1)
        for c in range(w - 1)
        if (orientation := _target_at(grid, r, c)) is not None
    ]


def _window_cells(r: int, c: int) -> set[Cell]:
    return {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}


def _pair_cells(r: int, c: int, orientation: str) -> tuple[Cell, Cell]:
    if orientation == "main":
        return (r, c), (r + 1, c + 1)
    return (r, c + 1), (r + 1, c)


def _affected_anchors(cells: Iterable[Cell], h: int, w: int) -> set[Cell]:
    anchors: set[Cell] = set()
    for r, c in cells:
        for rr in (r - 1, r):
            for cc in (c - 1, c):
                if 0 <= rr < h - 1 and 0 <= cc < w - 1:
                    anchors.add((rr, cc))
    return anchors


def _green_count(grid: list[list[int]], r: int, c: int) -> int:
    return sum(
        grid[rr][cc] == 3
        for rr in (r, r + 1)
        for cc in (c, c + 1)
    )


def _is_edge_anchor(r: int, c: int, h: int, w: int) -> bool:
    return r in (0, h - 2) or c in (0, w - 2)


def _is_close_anchor(r: int, c: int, targets: list[Target]) -> bool:
    """Canonical-like proximity without overlapping 2x2 windows."""
    return any(
        max(abs(r - rr), abs(c - cc)) <= 2
        for rr, cc, _ in targets
    )


def _can_place_target(
    grid: list[list[int]],
    r: int,
    c: int,
    orientation: str,
    occupied_windows: set[Cell],
) -> bool:
    h, w = len(grid), len(grid[0])
    window = _window_cells(r, c)
    if occupied_windows & window:
        return False
    if any(grid[rr][cc] != 0 for rr, cc in window):
        return False

    pair = _pair_cells(r, c, orientation)
    for rr, cc in pair:
        grid[rr][cc] = 3
    try:
        for rr, cc in _affected_anchors(pair, h, w):
            if _green_count(grid, rr, cc) > 2:
                return False
        active = {
            (rr, cc, found)
            for rr, cc in _affected_anchors(pair, h, w)
            if (found := _target_at(grid, rr, cc)) is not None
        }
        return active == {(r, c, orientation)}
    finally:
        for rr, cc in pair:
            grid[rr][cc] = 0


def _place_targets(
    grid: list[list[int]], n_pairs: int, rng: Any
) -> list[Target]:
    h, w = len(grid), len(grid[0])
    orientations = ["main", "anti"] + [
        rng.choice(("main", "anti")) for _ in range(n_pairs - 2)
    ]
    rng.shuffle(orientations)

    # Roughly half the scenes force a close-but-disjoint pair. The other half
    # leave spacing unconstrained, spanning both compact and dispersed layouts.
    compact = rng.random() < 0.5
    roles = ["edge", "interior", "close" if compact else "any"]
    roles.extend("any" for _ in range(n_pairs - len(roles)))

    targets: list[Target] = []
    occupied_windows: set[Cell] = set()
    anchors = [(r, c) for r in range(h - 1) for c in range(w - 1)]

    def search(index: int) -> bool:
        if index == n_pairs:
            return True
        orientation = orientations[index]
        role = roles[index]
        candidates = anchors[:]
        rng.shuffle(candidates)
        for r, c in candidates:
            edge = _is_edge_anchor(r, c, h, w)
            if role == "edge" and not edge:
                continue
            if role == "interior" and edge:
                continue
            if role == "close" and not _is_close_anchor(r, c, targets):
                continue
            if not _can_place_target(
                grid, r, c, orientation, occupied_windows
            ):
                continue

            pair = _pair_cells(r, c, orientation)
            window = _window_cells(r, c)
            for rr, cc in pair:
                grid[rr][cc] = 3
            targets.append((r, c, orientation))
            occupied_windows.update(window)
            if search(index + 1):
                return True
            occupied_windows.difference_update(window)
            targets.pop()
            for rr, cc in pair:
                grid[rr][cc] = 0
        return False

    if not search(0):
        raise ValueError(
            f"could not place {n_pairs} lawful diagonal pairs in {h}x{w}"
        )
    return targets


def _safe_add_distractor(
    grid: list[list[int]],
    cells: tuple[Cell, ...],
    protected: set[Cell],
    target_keys: set[Target],
) -> bool:
    h, w = len(grid), len(grid[0])
    if len(set(cells)) != len(cells):
        return False
    if any(
        not (0 <= r < h and 0 <= c < w)
        or (r, c) in protected
        or grid[r][c] != 0
        for r, c in cells
    ):
        return False

    for r, c in cells:
        grid[r][c] = 3
    affected = _affected_anchors(cells, h, w)
    try:
        if any(_green_count(grid, r, c) > 3 for r, c in affected):
            return False
        for r, c in affected:
            orientation = _target_at(grid, r, c)
            if orientation is not None and (r, c, orientation) not in target_keys:
                return False
        return True
    finally:
        if any(
            _green_count(grid, r, c) > 3
            or (
                (orientation := _target_at(grid, r, c)) is not None
                and (r, c, orientation) not in target_keys
            )
            for r, c in affected
        ):
            for rr, cc in cells:
                grid[rr][cc] = 0


def _try_pattern_family(
    grid: list[list[int]],
    family: str,
    rng: Any,
    protected: set[Cell],
    target_keys: set[Target],
) -> tuple[Cell, ...] | None:
    h, w = len(grid), len(grid[0])
    if family == "blocked":
        patterns = []
        for r in range(h - 1):
            for c in range(w - 1):
                square = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
                if any(cell in protected for cell in square):
                    continue
                patterns.extend(tuple(cell for i, cell in enumerate(square) if i != missing)
                                for missing in range(4))
    elif family == "horizontal":
        patterns = [((r, c), (r, c + 1)) for r in range(h) for c in range(w - 1)]
    elif family == "vertical":
        patterns = [((r, c), (r + 1, c)) for r in range(h - 1) for c in range(w)]
    else:
        patterns = [((r, c),) for r in range(h) for c in range(w)]
    rng.shuffle(patterns)
    for cells in patterns:
        if _safe_add_distractor(grid, cells, protected, target_keys):
            return cells
    return None


def _place_distractors(
    grid: list[list[int]], targets: list[Target], difficulty: str, rng: Any
) -> list[Cell]:
    if difficulty == "easy":
        desired = rng.randint(3, 4)
    elif difficulty == "hard":
        desired = rng.randint(4, 5)
    else:
        desired = rng.randint(3, 5)

    protected = set().union(
        *(_window_cells(r, c) for r, c, _ in targets)
    )
    target_keys = set(targets)
    added: list[Cell] = []

    # Every normal draw contains an explicit else-branch witness: a 2x2
    # with three green cells. It contains a diagonal pair, but the occupied
    # third corner means the canonical zero-precondition is false, so the rule
    # must leave the missing fourth corner empty.
    first = _try_pattern_family(
        grid, "blocked", rng, protected, target_keys
    )
    if first is None:
        first = _try_pattern_family(
            grid, "singleton", rng, protected, target_keys
        )
    if first is None:
        raise ValueError("could not place a lawful green distractor")
    added.extend(first)

    while len(added) < desired:
        cell = _try_pattern_family(
            grid, "singleton", rng, protected, target_keys
        )
        if cell is None:
            break
        added.extend(cell)

    return added[:5]


def _draw_axis(ctx: Any, label: str, difficulty: str, overrides: dict[str, Any]) -> int:
    lo, hi = (
        _VALID_BOUNDS[label]
        if label in overrides and overrides[label] is not None
        else _BAND_BOUNDS[difficulty][label]
    )
    return ctx.draw_int(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = "medium" if difficulty is None else difficulty
    if band not in _BAND_BOUNDS:
        raise ValueError("difficulty must be one of easy, medium, hard, or None")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    h = _draw_axis(ctx, "grid_h", band, overrides)
    w = _draw_axis(ctx, "grid_w", band, overrides)
    n_pairs = _draw_axis(ctx, "n_pairs", band, overrides)
    rng = ctx.draw_rng("layout")

    grid = full_grid(h, w, 0)
    targets = _place_targets(grid, n_pairs, rng)
    _place_distractors(grid, targets, band, rng)

    analysis = _analysis(grid)
    if analysis["blocked_count"] == 0:
        raise AssertionError("internal generator invariant failure: missing blocked-diagonal decoy")
    errors = list(analysis["errors"])
    if errors:
        raise AssertionError(f"internal generator invariant failure: {errors}")
    return grid


def _analysis(grid: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "errors": [],
        "targets": [],
        "main_count": 0,
        "anti_count": 0,
        "edge_count": 0,
        "interior_count": 0,
        "distractor_cells": [],
        "max_green_2x2": 0,
        "blocked_count": 0,
    }
    errors: list[str] = result["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid must be a non-empty list of non-empty rows")
        return result
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        errors.append("grid is ragged")
        return result
    h = len(grid)
    if not (7 <= h <= 14 and 7 <= w <= 14):
        errors.append(f"expected dimensions in 7..14, got {h}x{w}")
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if not isinstance(value, int)
            or isinstance(value, bool)
            or value not in (0, 3)
        },
        key=repr,
    )
    if bad:
        errors.append(f"expected only integer colors 0 and 3, found {bad}")
        return result
    palette = {value for row in grid for value in row}
    if palette != {0, 3}:
        errors.append(f"expected both colors 0 and 3, found {sorted(palette)}")

    targets = _find_targets(grid)
    result["targets"] = targets
    result["main_count"] = sum(orientation == "main" for _, _, orientation in targets)
    result["anti_count"] = sum(orientation == "anti" for _, _, orientation in targets)
    result["edge_count"] = sum(
        _is_edge_anchor(r, c, h, w) for r, c, _ in targets
    )
    result["interior_count"] = len(targets) - result["edge_count"]

    if not (3 <= len(targets) <= 6):
        errors.append(f"expected 3..6 active diagonal pairs, got {len(targets)}")
    if result["main_count"] == 0 or result["anti_count"] == 0:
        errors.append(
            "expected both diagonal orientations, got "
            f"main={result['main_count']} anti={result['anti_count']}"
        )

    windows = [_window_cells(r, c) for r, c, _ in targets]
    if any(
        windows[i] & windows[j]
        for i in range(len(windows))
        for j in range(i)
    ):
        errors.append("active 2x2 target windows overlap")
    if result["edge_count"] == 0:
        errors.append("expected at least one border-touching target window")
    if result["interior_count"] == 0:
        errors.append("expected at least one interior target window")

    green_counts = [
        _green_count(grid, r, c)
        for r in range(h - 1)
        for c in range(w - 1)
    ]
    max_green = max(green_counts, default=0)
    result["max_green_2x2"] = max_green
    result["blocked_count"] = sum(count == 3 for count in green_counts)
    if max_green > 3:
        errors.append(f"a 2x2 window contains {max_green} green cells; full green squares are not input cues")

    pair_cells: set[Cell] = set()
    for r, c, orientation in targets:
        pair_cells.update(_pair_cells(r, c, orientation))
    green_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    }
    distractors = sorted(green_cells - pair_cells)
    result["distractor_cells"] = distractors
    if not (1 <= len(distractors) <= 5):
        errors.append(
            f"expected 1..5 green distractor cells outside target pairs, got {len(distractors)}"
        )
    return result


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"n_pairs": len(analysis["targets"])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not encode the canonical lesson structure."""
    return list(_analysis(grid)["errors"])
