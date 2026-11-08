"""Digit-valued erosion-shell histograms of connected, hole-free polyominoes.

Generate inputs only. The unchanged canonical Racket rule supplies labels.
Local shell calculations validate the domain and diagnose rivals; they do not
replace the reference authority for exported answers.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "12ace26107fd"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "3e24db6285e1"
SUMMARY = (
    "One connected, hole-free shape in a single color 1..8 on background 0. "
    "The unchanged rule counts cells REMOVED at each successive cardinal "
    "erosion step, writing the counts outer-to-inner in a one-row strip. "
    "Each shell count is 1..9; total area may exceed 9. Default lessons cycle "
    "axial-detour, dual-concavity, and broad/core examples: five demonstrations "
    "plus one query contain two examples of each role."
)
INVARIANTS = [
    "zero background and one cardinal-connected monochrome shape in color 1..8",
    "the shape has no enclosed background hole and contains at least 3 cells",
    "each nonempty erosion shell contains 1..9 cells; total area is not the output bound",
    "default canvases span 7..16 per axis, favoring canonical 7x7 and 9x9 profiles",
]
AXES = {
    "grid_h": {"type": "int", "default": "7..16, weighted toward 7 and 9", "valid": "5..16"},
    "grid_w": {"type": "int", "default": "7..16, weighted toward 7 and 9", "valid": "5..16"},
    "shape_size": {"type": "int", "default": "scheduled or broad 3..14", "valid": "3..14"},
    "color": {"type": "int", "default": "uniform 1..8", "valid": "1..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("axial", "concavity", "core")
MIN_STRICT_FRAC = 0.05
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_AXIAL = frozenset({(2, c) for c in range(5)} | {(r, 2) for r in range(5)})
_CONCAVITY = frozenset((r, c) for r, row in enumerate(("101", "111", "100", "110"))
                       for c, value in enumerate(row) if value == "1")


def _cells(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value not in (0, 9)}


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return {(r - top, c - left) for r, c in cells}


def _shell_counts(cells):
    """Diagnostic exact-shell counts, not cumulative remaining-area counts."""
    cur = set(cells)
    counts = []
    while cur:
        remaining = {p for p in cur
                     if all((p[0] + dr, p[1] + dc) in cur for dr, dc in _DELTAS)}
        counts.append(len(cur) - len(remaining))
        cur = remaining
    return counts


def _connected(cells):
    if not cells:
        return False
    seen = {min(cells)}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _DELTAS:
            point = r + dr, c + dc
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def _hole_free(cells):
    """Flood the complement in a one-cell padded bounding box."""
    if not cells:
        return False
    top, bottom = min(r for r, _ in cells) - 1, max(r for r, _ in cells) + 1
    left, right = min(c for _, c in cells) - 1, max(c for _, c in cells) + 1
    outside = {(top, left)}
    stack = [(top, left)]
    while stack:
        r, c = stack.pop()
        for dr, dc in _DELTAS:
            point = r + dr, c + dc
            if (top <= point[0] <= bottom and left <= point[1] <= right
                    and point not in cells and point not in outside):
                outside.add(point)
                stack.append(point)
    return len(outside) + len(cells) == (bottom - top + 1) * (right - left + 1)


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["rows must be integer sequences"]
    w = len(grid[0])
    if not w or any(len(row) != w for row in grid):
        return ["empty or ragged rows"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integers in 0..9"]
    palette = {value for row in grid for value in row}
    if 0 not in palette or 9 in palette or len(palette - {0}) != 1:
        return ["require background 0 and exactly one foreground color in 1..8"]
    cells = _cells(grid)
    if len(cells) < 3:
        return ["the shape must contain at least 3 cells"]
    if not _connected(cells):
        return ["require exactly one cardinal-connected shape"]
    if not _hole_free(cells):
        return ["enclosed background holes are outside this solid-shape manifold"]
    counts = _shell_counts(cells)
    if any(not 1 <= count <= 9 for count in counts):
        return [f"erosion shell counts must each fit digits 1..9; got {counts}"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) not in ((7, 7), (9, 9)):
        return ["outside the two canonical canvas profiles"]
    return []


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _diamond(radius):
    return {(r, c) for r in range(2 * radius + 1) for c in range(2 * radius + 1)
            if abs(r - radius) + abs(c - radius) <= radius}


def _fallback(size):
    """Construct every exact supported area inside 5x5 with digit-valid shells."""
    if size <= 9:
        return {(i // 3, i % 3) for i in range(size)}
    cells = _diamond(2)
    if size == 14:
        cells.add((0, 1))
    else:
        for point in ((0, 2), (4, 2), (2, 0))[:13 - size]:
            cells.remove(point)
    return _normalize(cells)


def _transform(cells, orientation):
    transformed = set(cells)
    if orientation >= 4:
        transformed = {(r, -c) for r, c in transformed}
    for _ in range(orientation % 4):
        transformed = {(c, -r) for r, c in transformed}
    return _normalize(transformed)


def _is_scheduled_witness_shape(cells):
    normalized = _normalize(cells)
    return any(normalized == _transform(template, orientation)
               for template in (_AXIAL, _CONCAVITY) for orientation in range(8))


def _random_shape(rng, size, h, w):
    """Rejection is internal and bounded; the exact-size fallback always fits."""
    for _ in range(16):
        cells = {(0, 0)}
        while len(cells) < size:
            frontier = set()
            for r, c in sorted(cells):
                for dr, dc in _DELTAS:
                    point = r + dr, c + dc
                    if point not in cells:
                        candidate = cells | {point}
                        if (max(r for r, _ in candidate) - min(r for r, _ in candidate) < h
                                and max(c for _, c in candidate) - min(c for _, c in candidate) < w):
                            frontier.add(point)
            if not frontier:
                break
            options = sorted(frontier)
            weights = [(1 + sum((r + dr, c + dc) in cells for dr, dc in _DELTAS)) ** 3
                       for r, c in options]
            cells.add(rng.choices(options, weights=weights)[0])
        if (len(cells) == size and _hole_free(cells)
                and all(count <= 9 for count in _shell_counts(cells))):
            return _normalize(cells)
    return _fallback(size)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be a literal integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Small canvases remain exact override options; ordinary lessons have room
    # to place repeated witness shapes differently without rejecting a draw.
    favored = (7,) * 20 + (9,) * 10 if difficulty == "easy" else (
        (9,) * 20 + (7,) * 10 if difficulty == "hard" else (7, 9) * 15)
    dimensions = tuple(range(7, 17)) + favored
    h = ctx.draw_int_strict("grid_h", 5, 16) if overrides.get("grid_h") is not None else ctx.draw_choice("grid_h", dimensions)
    w = ctx.draw_int_strict("grid_w", 5, 16) if overrides.get("grid_w") is not None else ctx.draw_choice("grid_w", dimensions)
    color = ctx.draw_color_strict("color", exclude={0, 9})
    rng = ctx.draw_rng("shape")
    role = schedule_profile(seed, sample_index, difficulty)
    # Explicit area control requests a lawful exact-size sample, not a lesson.
    if overrides.get("shape_size") is not None:
        size = ctx.draw_int_strict("shape_size", 3, 14)
        cells = _random_shape(rng, size, min(h, w), min(h, w))
    elif role == "axial":
        size = ctx.draw_choice("shape_size", (9,))
        cells = set(_AXIAL)
    elif role == "concavity":
        size = ctx.draw_choice("shape_size", (8,))
        cells = set(_CONCAVITY)
    else:
        choices = tuple(range(3, 15)) + (5, 9, 13, 13, 14, 14)
        size = ctx.draw_choice("shape_size", choices)
        if size in (13, 14) and rng.randrange(2) == 0:
            cells = _fallback(size)
        else:
            cells = _random_shape(rng, size, min(h, w), min(h, w))
        if _is_scheduled_witness_shape(cells):
            cells = _fallback(size)
    cells = _transform(cells, ctx.draw_rng("orientation").randrange(8))
    sh, sw = max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1
    if sh > h or sw > w:
        raise RuntimeError("constructed exact-size shape did not fit")
    # Consecutive copies of a role have different positions whenever their
    # normalized geometry and canvas match. Different roles have disjoint
    # default mask support. Explicit tiny-canvas overrides are not lessons.
    slots = (h - sh + 1) * (w - sw + 1)
    slot = (seed + sample_index // LESSON_SCHEDULE_PERIOD) % slots
    top, left = divmod(slot, w - sw + 1)
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[top + r][left + c] = color
    return grid


def observe_overrides(grid):
    cells = _cells(grid)
    foreground = {grid[r][c] for r, c in cells}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "shape_size": len(cells),
            "color": next(iter(foreground)) if len(foreground) == 1 else None}


def _axial_ray_depth(grid):
    cells = _cells(grid)
    counts = Counter()
    for r, c in cells:
        lengths = []
        for dr, dc in _DELTAS:
            length = 1
            while (r + length * dr, c + length * dc) in cells:
                length += 1
            lengths.append(length)
        counts[min(lengths)] += 1
    return [[counts[d] for d in range(1, max(counts, default=0) + 1)]]


def _row_fill_then_peel(grid):
    cells = _cells(grid)
    filled = set(cells)
    for r in {r for r, _ in cells}:
        cols = [c for rr, c in cells if rr == r]
        filled.update((r, c) for c in range(min(cols), max(cols) + 1))
    return [_shell_counts(filled)]


def _column_fill_then_peel(grid):
    cells = _cells(grid)
    filled = set(cells)
    for c in {c for _, c in cells}:
        rows = [r for r, cc in cells if cc == c]
        filled.update((r, c) for r in range(min(rows), max(rows) + 1))
    return [_shell_counts(filled)]


SEMANTIC_RIVALS = {
    "axial_ray_depth": _axial_ray_depth,
    "row_fill_then_peel": _row_fill_then_peel,
    "column_fill_then_peel": _column_fill_then_peel,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "axial_detour": lambda grid: _axial_ray_depth(grid) != [_shell_counts(_cells(grid))],
    "row_gap": lambda grid: _row_fill_then_peel(grid) != [_shell_counts(_cells(grid))],
    "column_gap": lambda grid: _column_fill_then_peel(grid) != [_shell_counts(_cells(grid))],
    "depth_three": lambda grid: len(_shell_counts(_cells(grid))) == 3,
}
WITNESS_RIVALS = {
    "axial_detour": ["axial_ray_depth"],
    "row_gap": ["row_fill_then_peel"],
    "column_gap": ["column_fill_then_peel"],
}
BRANCH_WITNESSES = ("depth_three",)


def lesson_identifiable(demos, query):
    reasons = []
    for name, solve in LESSON_COMPETITORS.items():
        if all(solve(pair["input"]) == pair["output"] for pair in demos):
            if solve(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons

LAWFUL_MINIMAL_PROBES = {'solid_2x2': {'justification': 'The selected onion rule accepts connected solid shapes; four cells form one nonempty shell and produce a single count of four.', 'rule_hash': '3e24db6285e1', 'expected_output': [[4]]}, 'short_line': {'justification': 'The selected onion rule accepts connected solid shapes; four cells form one nonempty shell and produce a single count of four.', 'rule_hash': '3e24db6285e1', 'expected_output': [[4]]}}
