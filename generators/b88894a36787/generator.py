"""Input sampler for the header-to-side L-path task 29700607.

The pinned Racket program remains the label authority.  The Python prediction
and rivals below are diagnostics for regression and lesson-identifiability
checks; generated labels are not produced by this module.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b88894a36787"
TASK_ID = GENERATOR_ID
RULE_HASH = "94000a617419"
VERSION = "3.1.0"
SUMMARY = (
    "A contiguous row-0 header contains 2..4 distinct colors.  Each header "
    "color has either one matching dot on the left/right edge or, for at most "
    "one color, no side dot.  The rule extends each header vertically to its "
    "matching dot and then horizontally to that edge; a header without a dot "
    "extends vertically to the bottom row."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 8
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the 11..15 by 11..15 input uses integer colors 0..9",
    "row 0 has one contiguous run of 2..4 distinct nonzero colors away from the edges",
    "each nonzero body cell is a left/right-edge dot whose color occurs in the header",
    "each header color has at most one side dot and at most one header color is missing a dot",
    "the implied colored paths are pairwise disjoint, including missing-dot bottom extensions",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted by band", "valid": "11..15"},
    "grid_w": {"type": "int", "default": "canonical-weighted by band", "valid": "11..15"},
    "n_markers": {"type": "int", "default": "canonical-weighted 3", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_SCHEDULE_PROFILES = (
    "missing_left_interior_row2_a",
    "missing_right_interior_row2",
    "missing_left_interior_row2_b",
    "missing_boundary_one_side",
    "missing_left_interior_row2_c",
    "complete_split_shared_row",
    "missing_left_interior_row2_d",
    "complete_one_side",
)
SCHEDULE_PROFILES = _SCHEDULE_PROFILES


def schedule_profile(seed, sample_index, difficulty=None):
    """Public finite-period curriculum profile used by schedule census tools."""
    del seed, difficulty
    return _SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _weighted_axis(ctx, name, lo, hi, anchor):
    """Draw an exact observable axis while retaining its full domain in every band."""
    choices = list(range(lo, hi + 1)) + [anchor] * 40
    return ctx.draw_choice(name, choices)


def _validate_call(seed, sample_index, difficulty, overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    bounds = {"grid_h": (11, 15), "grid_w": (11, 15), "n_markers": (2, 4)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be within {lo}..{hi}")


def _rows(rng, count, h, *, include_two=False, exclude=()):
    """Sorted target rows; ordering is what prevents same-side path crossings."""
    if count == 0:
        return []
    blocked = set(exclude)
    chosen = []
    if include_two:
        if 2 in blocked:
            raise ValueError("row 2 cannot be both required and excluded")
        chosen.append(2)
        blocked.add(2)
    candidates = [r for r in range(2, h - 1) if r not in blocked]
    need = count - len(chosen)
    if need > len(candidates):
        raise ValueError("not enough body rows for requested marker layout")
    chosen.extend(rng.sample(candidates, need))
    return sorted(chosen)


def _assign_group(targets, indices, side, rows):
    """Assign rows from the outside header inward, making paths noncrossing."""
    order = sorted(indices) if side == 0 else sorted(indices, reverse=True)
    if len(order) != len(rows):
        raise ValueError("row assignment length mismatch")
    for index, row in zip(order, rows):
        targets[index] = (row, side)


def _split_around_missing(rng, targets, h, w, n, missing, *, include_two=True):
    """Place extant dots on the side away from one missing header marker."""
    left = list(range(0, missing))
    right = list(range(missing + 1, n))
    left_rows = _rows(rng, len(left), h, include_two=include_two and bool(left))
    right_rows = _rows(rng, len(right), h, exclude=left_rows)
    _assign_group(targets, left, 0, left_rows)
    _assign_group(targets, right, w - 1, right_rows)
    return targets


def _target_layout(ctx, h, w, n):
    """Eight-slot schedule that refutes position-based missing-dot shortcuts."""
    phase = ctx.sample_index % LESSON_SCHEDULE_PERIOD
    rng = ctx.draw_rng("target_layout")
    targets = [None] * n

    if phase in {0, 2, 4, 6}:
        # For four-header production lessons, omit the left interior marker.
        # This is the lawful horizontal reflection absent from v3.0.0 and is a
        # direct counterexample to guessing the missing position from geometry.
        return _split_around_missing(rng, targets, h, w, n, missing=1)

    if phase == 1:
        # Also retain the canonical right-interior case.  With four markers it
        # omits index 2, so both reflected interior positions are reachable.
        return _split_around_missing(rng, targets, h, w, n, missing=n - 2)

    if phase == 3:
        # Missing boundary alternates by schedule block; all extant connectors
        # safely point away from it on one edge.
        missing_left = (ctx.sample_index // LESSON_SCHEDULE_PERIOD) % 2 == 0
        missing = 0 if missing_left else n - 1
        present = [i for i in range(n) if i != missing]
        side = w - 1 if missing_left else 0
        _assign_group(targets, present, side, _rows(rng, len(present), h, include_two=True))
        return targets

    if phase == 5:
        # Complete split layout.  Matching outside-depths share a row across
        # opposite edges, reproducing the legal canonical shared-row branch.
        split = (n + 1) // 2
        left = list(range(split))
        right = list(range(split, n))
        depth = max(len(left), len(right))
        depth_rows = _rows(rng, depth, h)
        _assign_group(targets, left, 0, depth_rows[:len(left)])
        _assign_group(targets, right, w - 1, depth_rows[:len(right)])
        return targets

    # Complete all-on-one-side layout, alternating sides by schedule block.
    side = 0 if (ctx.sample_index // LESSON_SCHEDULE_PERIOD) % 2 == 0 else w - 1
    _assign_group(targets, list(range(n)), side, _rows(rng, n, h, include_two=True))
    return targets


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    overrides = {name: value for name, value in overrides.items() if value is not None}
    effective_overrides = dict(overrides)
    if sample_index % LESSON_SCHEDULE_PERIOD in {0, 1, 2, 4, 6}:
        effective_overrides.setdefault("n_markers", 4)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )

    canonical_anchor = {
        "easy": 11,
        "medium": 12,
        "hard": 15,
        None: (11, 12, 15, 12, 11, 12, 15, 12)[sample_index % LESSON_SCHEDULE_PERIOD],
    }[difficulty]
    h = _weighted_axis(ctx, "grid_h", 11, 15, canonical_anchor)
    w = _weighted_axis(ctx, "grid_w", 11, 15, canonical_anchor)
    n = _weighted_axis(ctx, "n_markers", 2, 4, 3)

    grid = full_grid(h, w, 0)
    colors = ctx.draw_distinct_colors("header_colors", n=n, exclude={0})
    start = ctx.draw_rng("header_position").randint(2, w - n - 2)
    for index, color in enumerate(colors):
        grid[0][start + index] = color

    targets = _target_layout(ctx, h, w, n)
    for color, target in zip(colors, targets):
        if target is not None:
            row, col = target
            if grid[row][col] != 0:
                raise RuntimeError("constructive side-marker collision")
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _entries(grid):
    h, w = len(grid), len(grid[0])
    body = [(r, c, grid[r][c]) for r in range(1, h) for c in range(w)
            if grid[r][c] != 0]
    entries = []
    for col, color in enumerate(grid[0]):
        if color == 0:
            continue
        dot = next((item for item in body if item[2] == color), None)
        if dot is None:
            entries.append((col, color, h - 1, None))
        else:
            entries.append((col, color, dot[0], dot[1]))
    return entries


def _path_cells(entry):
    col, _color, target_row, target_col = entry
    cells = {(row, col) for row in range(target_row + 1)}
    if target_col is not None:
        cells.update((target_row, c)
                     for c in range(min(col, target_col), max(col, target_col) + 1))
    return cells


def _prediction(grid):
    """Diagnostic mirror of the Racket authority, including first-match priority."""
    h, w = len(grid), len(grid[0])
    entries = _entries(grid)
    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            for header_col, color, target_row, target_col in entries:
                vertical = col == header_col and row <= target_row
                horizontal = (
                    target_col is not None
                    and row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                )
                if vertical or horizontal:
                    out[row][col] = color
                    break
    return out


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": sum(value != 0 for value in grid[0]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty grid rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h, w = len(grid), width
    errors = []
    if not 11 <= h <= 15 or not 11 <= w <= 15:
        errors.append("canvas must be 11..15 rows by 11..15 columns")

    header = [(col, value) for col, value in enumerate(grid[0]) if value != 0]
    if not 2 <= len(header) <= 4:
        errors.append("row 0 must contain 2..4 header markers")
        return errors
    header_cols = [col for col, _value in header]
    header_colors = [value for _col, value in header]
    if header_cols != list(range(header_cols[0], header_cols[0] + len(header_cols))):
        errors.append("row-0 header markers must form one contiguous run")
    if header_cols[0] == 0 or header_cols[-1] == w - 1:
        errors.append("header run must be separated from both side edges")
    if len(set(header_colors)) != len(header_colors):
        errors.append("header colors must be distinct")

    body = [(row, col, grid[row][col]) for row in range(1, h) for col in range(w)
            if grid[row][col] != 0]
    if any(col not in (0, w - 1) for _row, col, _value in body):
        errors.append("all body markers must lie on the left or right edge")
    if any(value not in header_colors for _row, _col, value in body):
        errors.append("body marker colors must come from the header")
    counts = {color: 0 for color in header_colors}
    for _row, _col, value in body:
        if value in counts:
            counts[value] += 1
    if any(count > 1 for count in counts.values()):
        errors.append("each header color may have at most one matching side dot")
    missing = [color for color, count in counts.items() if count == 0]
    if len(missing) > 1:
        errors.append("at most one header color may omit its side dot")

    if not errors:
        entries = _entries(grid)
        for index, left in enumerate(entries):
            for right in entries[index + 1:]:
                overlap = _path_cells(left) & _path_cells(right)
                if overlap:
                    errors.append(
                        f"implied paths for colors {left[1]} and {right[1]} overlap at "
                        f"{sorted(overlap)[:3]}"
                    )
    return errors


def strict_canonical_like(grid):
    """The full declared sampler manifold, not a superficial shape predicate."""
    return self_check(grid)


def _only_existing_pairs(grid):
    """RIVAL: incorrectly omits a header column when its side dot is absent."""
    h, w = len(grid), len(grid[0])
    entries = [entry for entry in _entries(grid) if entry[3] is not None]
    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            for header_col, color, target_row, target_col in entries:
                if (col == header_col and row <= target_row) or (
                    row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                ):
                    out[row][col] = color
                    break
    return out


def _all_columns_to_bottom(grid):
    """RIVAL: ignores every side dot and extends all header columns downward."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for col, color in enumerate(grid[0]):
        if color != 0:
            for row in range(h):
                out[row][col] = color
    return out



def _assumed_missing_position(grid):
    """RIVAL: guesses which header lacks a dot from side-layout geometry."""
    h, w = len(grid), len(grid[0])
    header = [(col, color) for col, color in enumerate(grid[0]) if color]
    dots = [(row, col, grid[row][col]) for row in range(1, h)
            for col in range(w) if grid[row][col]]
    guessed = None
    if len(dots) < len(header):
        sides = {col for _row, col, _color in dots}
        if len(sides) == 2:
            guessed = len(header) // 2
        elif sides == {0}:
            guessed = len(header) - 1
        elif sides == {w - 1}:
            guessed = 0

    entries = []
    for index, (header_col, color) in enumerate(header):
        dot = next((item for item in dots if item[2] == color), None)
        target_row, target_col = (dot[0], dot[1]) if dot else (0, None)
        vertical_end = h - 1 if index == guessed else target_row
        entries.append((header_col, color, target_row, target_col, vertical_end))

    out = full_grid(h, w, 0)
    for row in range(h):
        for col in range(w):
            for header_col, color, target_row, target_col, vertical_end in entries:
                vertical = col == header_col and row <= vertical_end
                horizontal = (
                    target_col is not None
                    and row == target_row
                    and min(header_col, target_col) <= col <= max(header_col, target_col)
                )
                if vertical or horizontal:
                    out[row][col] = color
                    break
    return out

def _has_missing_side_dot(grid):
    return any(target_col is None for _col, _color, _row, target_col in _entries(grid))


def _has_matched_side_dot(grid):
    return any(target_col is not None for _col, _color, _row, target_col in _entries(grid))


def _has_left_interior_missing_dot(grid):
    entries = _entries(grid)
    return (
        len(entries) == 4
        and entries[1][3] is None
        and all(entry[3] is not None for index, entry in enumerate(entries) if index != 1)
    )


SEMANTIC_WITNESSES = {
    "missing_side_dot": _has_missing_side_dot,
    "matched_side_dot": _has_matched_side_dot,
    "left_interior_missing_dot": _has_left_interior_missing_dot,
}
SEMANTIC_RIVALS = {
    "only_existing_pairs": _only_existing_pairs,
    "all_columns_to_bottom": _all_columns_to_bottom,
    "assumed_missing_position": _assumed_missing_position,
}
WITNESS_RIVALS = {
    "missing_side_dot": ["only_existing_pairs"],
    "matched_side_dot": ["all_columns_to_bottom"],
    "left_interior_missing_dot": ["assumed_missing_position"],
}
CANONICAL_SHORTCUTS = {
    "assumed_missing_position": _assumed_missing_position,
}
LESSON_COMPETITORS = {**SEMANTIC_RIVALS, **CANONICAL_SHORTCUTS}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query):
    """Report declared rivals that fit all demos but disagree on the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    findings = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                findings.append(f"declared rival {name} fits every demonstration")
    return findings
