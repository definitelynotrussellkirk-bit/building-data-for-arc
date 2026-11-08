"""Generator for completing guarded down-right diagonal gaps.

The selected rule fills the zero in a ``4,0,4`` down-right diagonal only
when neither the predecessor nor the successor on that diagonal is also 4.
Helpful samples contain both positive fills and an explicit guarded non-fill,
so the tempting unguarded shortcut is visible in every ordinary lesson.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7195f447bb20"
VERSION = "2.1.0"
TASK_ID = "7195f447bb20"
RULE_HASH = "0dab15d8dfee"
SUMMARY = (
    "A 0-background grid contains several isolated down-right 4,0,4 gaps and "
    "one controlled 4,4,0,4 or 4,0,4,4 diagonal near-miss. Fill only the "
    "midpoints of isolated 4,0,4 triples; a candidate that extends a longer "
    "diagonal run is deliberately left unchanged."
)

EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0 and foreground is color 4",
    "ordinary samples contain at least two eligible down-right gaps",
    "ordinary samples contain a predecessor- or successor-guarded non-fill",
    "motifs occupy distinct down-right diagonals",
]

HELPFUL_TEXTURES = ("guarded_predecessor", "guarded_successor")
DEGENERATE_TEXTURES = ("no_pairs", "midpoints_already_filled", "ascending_diagonal")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 10..20", "valid": "10..20"},
    "n_gaps": {"type": "int", "default": "difficulty-aware rng 2..8", "valid": "2..8"},
    "texture": {"type": "str", "default": "rng guarded profile",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}
_ALLOWED_OVERRIDES = set(AXES)


def _validate_override_keys(overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")


def _rectangular(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        return None, ["empty grid"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(type(cell) is not int or cell not in (0, 4) for row in grid for cell in row):
        return None, ["expected only background 0 and foreground 4"]
    return (len(grid), width), []


def _candidate_kind(grid, r, c):
    """Return eligible/guarded/None for the pair at (r,c),(r+2,c+2)."""
    h, w = len(grid), len(grid[0])
    if not (0 <= r < h - 2 and 0 <= c < w - 2):
        return None
    if not (grid[r][c] == 4 and grid[r + 1][c + 1] == 0
            and grid[r + 2][c + 2] == 4):
        return None
    predecessor = r > 0 and c > 0 and grid[r - 1][c - 1] == 4
    successor = r + 3 < h and c + 3 < w and grid[r + 3][c + 3] == 4
    return "guarded" if predecessor or successor else "eligible"


def _eligible_midpoints(grid):
    shape, errors = _rectangular(grid)
    if errors:
        return []
    h, w = shape
    return [(r + 1, c + 1) for r in range(h - 2) for c in range(w - 2)
            if _candidate_kind(grid, r, c) == "eligible"]


def _guarded_midpoints(grid):
    shape, errors = _rectangular(grid)
    if errors:
        return []
    h, w = shape
    return [(r + 1, c + 1) for r in range(h - 2) for c in range(w - 2)
            if _candidate_kind(grid, r, c) == "guarded"]


def rule_mirror(grid):
    """Pure Python mirror of the selected source rule."""
    result = deepcopy(grid)
    for r, c in _eligible_midpoints(grid):
        result[r][c] = 4
    return result


def no_guard_rival(grid):
    """Tempting shortcut: fill every down-right 4,0,4 midpoint."""
    shape, errors = _rectangular(grid)
    if errors:
        return deepcopy(grid)
    h, w = shape
    result = deepcopy(grid)
    for r in range(h - 2):
        for c in range(w - 2):
            if grid[r][c] == 4 and grid[r + 1][c + 1] == 0 and grid[r + 2][c + 2] == 4:
                result[r + 1][c + 1] = 4
    return result


def fill_first_rival(grid):
    """Tempting shortcut: complete only the first eligible gap."""
    result = deepcopy(grid)
    centers = _eligible_midpoints(grid)
    if centers:
        r, c = centers[0]
        result[r][c] = 4
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    shape, errors = _rectangular(grid)
    if errors:
        return errors
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    eligible = _eligible_midpoints(grid)
    if not eligible and not _guarded_midpoints(grid):
        errors.append("expected at least one down-right 4,0,4 candidate")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def semantic_signature(grid):
    shape, errors = _rectangular(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = shape
    return {
        "grid_h": h,
        "grid_w": w,
        "eligible_gap_count": len(_eligible_midpoints(grid)),
        "guarded_gap_count": len(_guarded_midpoints(grid)),
        "foreground_count": sum(cell == 4 for row in grid for cell in row),
    }


def _lawful(predicate):
    def check(grid):
        try:
            facts = semantic_signature(grid)
        except ValueError:
            return False
        return bool(predicate(facts))
    return check


SEMANTIC_WITNESSES = {
    "guarded_nonfill_refutes_unguarded_rule": _lawful(lambda f: f["guarded_gap_count"] > 0),
    "multiple_fills_refute_single_gap_rule": _lawful(lambda f: f["eligible_gap_count"] >= 2),
}
LESSON_COMPETITORS = {
    "unguarded_all_pairs": no_guard_rival,
    "single_gap_only": fill_first_rival,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
WITNESS_RIVALS = {
    "guarded_nonfill_refutes_unguarded_rule": ["unguarded_all_pairs"],
    "multiple_fills_refute_single_gap_rule": ["single_gap_only"],
}
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    for index, pair in enumerate(demos):
        if self_check(pair.get("input")):
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        if rule_mirror(pair["input"]) != pair.get("output"):
            reasons.append(f"demo {index} output does not match the guarded diagonal rule")
    if self_check(query.get("input")):
        reasons.append("query input is outside the task grammar")
        return reasons
    answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != answer:
            reasons.append(f"competing rule {name!r} fits every demo but changes the query answer")
    return reasons


def _anchors_by_diagonal(h, w, *, predecessor=False, successor=False):
    rows = {}
    for r in range(h - 2):
        for c in range(w - 2):
            if predecessor and (r == 0 or c == 0):
                continue
            if successor and (r + 3 >= h or c + 3 >= w):
                continue
            rows.setdefault(c - r, []).append((r, c))
    return rows


def _place_helpful(h, w, n_gaps, texture, rng):
    grid = full_grid(h, w, 0)
    predecessor = texture == "guarded_predecessor"
    guarded = _anchors_by_diagonal(h, w, predecessor=predecessor, successor=not predecessor)
    guard_diagonals = list(guarded)
    rng.shuffle(guard_diagonals)
    guard_d = guard_diagonals[0]
    guard_anchor = rng.choice(guarded[guard_d])
    r, c = guard_anchor
    grid[r][c] = 4
    grid[r + 2][c + 2] = 4
    if predecessor:
        grid[r - 1][c - 1] = 4
    else:
        grid[r + 3][c + 3] = 4

    eligible = _anchors_by_diagonal(h, w)
    diagonals = [d for d in eligible if d != guard_d]
    rng.shuffle(diagonals)
    if len(diagonals) < n_gaps:
        raise ValueError("grid is too small for requested independent gaps")
    for d in diagonals[:n_gaps]:
        r, c = rng.choice(eligible[d])
        grid[r][c] = 4
        grid[r + 2][c + 2] = 4

    facts = semantic_signature(grid)
    if facts["eligible_gap_count"] != n_gaps or facts["guarded_gap_count"] < 1:
        raise AssertionError(f"constructed motif census drifted: {facts}")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    texture_override = overrides.get("texture")
    if texture_override in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture_override)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_int_diff("grid_h", 10, 20)
    w = ctx.draw_int_diff("grid_w", 10, 20)
    n_gaps = ctx.draw_int_diff("n_gaps", 2, 8)
    texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    return _place_helpful(h, w, n_gaps, texture, ctx.draw_rng("placement"))


def _draw_from_degenerate(name):
    grid = full_grid(10, 10, 0)
    if name == "no_pairs":
        grid[1][1] = 4
        grid[5][2] = 4
        grid[3][7] = 4
    elif name == "midpoints_already_filled":
        grid[1][1] = grid[2][2] = grid[3][3] = 4
        grid[5][6] = grid[6][7] = grid[7][8] = 4
    elif name == "ascending_diagonal":
        grid[3][1] = grid[1][3] = 4
        grid[8][3] = grid[6][5] = 4
    return grid
