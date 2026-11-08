"""Generator for the fixed-panel Boolean gallery task.

Two connected color-1 masks occupy aligned 5x5 panels separated by one blank
column.  The unchanged Racket authority emits three 5x5 panels: union in color
2, intersection in color 3, and xor in color 4.

The default five-slot curriculum reproduces the five public occupancy
signatures while varying the actual connected shapes.  Four slots expose all
four Boolean states (00, 10, 01, 11); the fifth preserves the public query's
right-subset-of-left branch.  Any four demonstrations from a five-pair window
therefore contain multiple complete truth tables and refute the declared
shortcut rules even when the query position is rotated.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8384d9743be8"
TASK_ID = GENERATOR_ID
RULE_HASH = "859078164faa"
VERSION = "3.0.0"

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A fixed 5x11 input contains two coordinate-aligned 5x5 binary panels in "
    "color 1, separated by blank column 5. Each panel is one 4-connected "
    "shape. The output is a 5x17 gallery with union colored 2, intersection "
    "colored 3, and xor colored 4, separated by blank columns. A five-profile "
    "schedule matches every public occupancy signature; four profiles expose "
    "the complete Boolean truth table and one preserves the public subset case."
)

INVARIANTS = [
    "the input is exactly 5x11 with background 0 and blank separator column 5",
    "each 5x5 panel contains one 4-connected color-1 shape of size 3..9",
    "the aligned masks have nonempty intersection and nonempty xor",
    "the output gallery orders union(2), intersection(3), xor(4)",
]

AXES = {
    "density_l": {
        "type": "int",
        "default": "five-slot canonical occupancy schedule",
        "valid": "3..9",
    },
    "density_r": {
        "type": "int",
        "default": "five-slot canonical occupancy schedule",
        "valid": "3..9",
    },
}

# (left cells, right cells, overlap cells, relation)
_PROFILE_SPECS = {
    "partial_4x5": (4, 5, 2, "partial"),
    "partial_5x5": (5, 5, 3, "partial"),
    "partial_4x4": (4, 4, 2, "partial"),
    "partial_4x6": (4, 6, 2, "partial"),
    "right_subset_8x4": (8, 4, 4, "right_subset"),
}
SCHEDULE_PROFILES = tuple(_PROFILE_SPECS)

# Signatures are ordered as (00, 10, 01, 11).  These are exactly the four
# public demonstrations plus the public query.
_CANONICAL_SIGNATURES = {
    (18, 2, 3, 2),
    (18, 2, 2, 3),
    (19, 2, 2, 2),
    (17, 2, 4, 2),
    (17, 4, 0, 4),
}

_CELLS = tuple((row, column) for row in range(5) for column in range(5))
_CENTRAL_CELLS = tuple(
    (row, column) for row in range(1, 4) for column in range(1, 4)
)

# Guaranteed connected fallback path.  Every contiguous interval is a
# 4-connected mask; dihedral transforms preserve that property.
_SPIRAL_PATH = (
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 4), (2, 4), (3, 4), (4, 4),
    (4, 3), (4, 2), (4, 1), (4, 0),
    (3, 0), (2, 0), (1, 0),
    (1, 1), (1, 2), (1, 3),
    (2, 3), (3, 3), (3, 2), (3, 1),
    (2, 1), (2, 2),
)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _neighbors(cell):
    row, column = cell
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = row + dr, column + dc
        if 0 <= nr < 5 and 0 <= nc < 5:
            yield nr, nc


def _is_connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in _neighbors(current):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be a literal integer")
        if not 3 <= value <= 9:
            raise ValueError(f"{name} must be in 3..9")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the call-order-independent five-slot semantic profile."""
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _weighted_frontier_choice(rng, frontier):
    weighted = []
    for row, column in sorted(frontier):
        # Compact, canonical-like growth is favored without eliminating edge
        # support.  Integer repetition keeps the decision deterministic.
        center_distance = abs(row - 2) + abs(column - 2)
        weight = max(1, 6 - center_distance)
        weighted.extend([(row, column)] * weight)
    return rng.choice(weighted)


def _grow_connected(rng, target_size: int, *, initial=None, allowed=None):
    allowed_cells = set(_CELLS if allowed is None else allowed)
    cells = set(initial or ())
    if not cells:
        choices = [cell for cell in _CENTRAL_CELLS if cell in allowed_cells]
        if not choices:
            choices = sorted(allowed_cells)
        if not choices:
            return None
        cells.add(rng.choice(choices))
    if not cells <= allowed_cells or len(cells) > target_size:
        return None
    while len(cells) < target_size:
        frontier = {
            neighbor
            for cell in cells
            for neighbor in _neighbors(cell)
            if neighbor in allowed_cells and neighbor not in cells
        }
        if not frontier:
            return None
        cells.add(_weighted_frontier_choice(rng, frontier))
    return cells


def _transform_path(path, transform: int):
    def apply(cell):
        row, column = cell
        if transform >= 4:
            column = 4 - column
        for _ in range(transform % 4):
            row, column = column, 4 - row
        return row, column

    transformed = tuple(apply(cell) for cell in path)
    if len(set(transformed)) != 25:
        raise RuntimeError("invalid fallback path transform")
    return transformed


def _fallback_pair(rng, left_size: int, right_size: int, overlap: int, relation: str):
    transform = rng.randrange(8)
    path = _transform_path(_SPIRAL_PATH, transform)
    if rng.randrange(2):
        path = tuple(reversed(path))

    if relation == "right_subset":
        span = left_size
        start = rng.randint(0, len(path) - span)
        left_seq = path[start : start + left_size]
        offset = rng.randint(0, left_size - right_size)
        right_seq = left_seq[offset : offset + right_size]
        return set(left_seq), set(right_seq)

    span = left_size + right_size - overlap
    start = rng.randint(0, len(path) - span)
    left_seq = path[start : start + left_size]
    right_start = start + left_size - overlap
    right_seq = path[right_start : right_start + right_size]
    return set(left_seq), set(right_seq)


def _construct_pair(rng, left_size: int, right_size: int, overlap: int, relation: str):
    for _ in range(400):
        if relation == "right_subset":
            left = _grow_connected(rng, left_size)
            if left is None:
                continue
            right = _grow_connected(
                rng,
                right_size,
                initial={rng.choice(sorted(left))},
                allowed=left,
            )
            if right is None:
                continue
        else:
            core = _grow_connected(rng, overlap)
            if core is None:
                continue
            left = _grow_connected(rng, left_size, initial=core)
            if left is None:
                continue
            # Forbid left-exclusive cells so the intersection remains exactly
            # the requested core while the right mask grows from that core.
            allowed_right = set(_CELLS) - (left - core)
            right = _grow_connected(
                rng,
                right_size,
                initial=core,
                allowed=allowed_right,
            )
            if right is None:
                continue

        if len(left) != left_size or len(right) != right_size:
            continue
        if len(left & right) != overlap:
            continue
        if not (_is_connected(left) and _is_connected(right)):
            continue
        if relation == "right_subset":
            if not right < left:
                continue
        elif not (left - right and right - left):
            continue
        return left, right

    left, right = _fallback_pair(
        rng, left_size, right_size, overlap, relation
    )
    if not (_is_connected(left) and _is_connected(right)):
        raise RuntimeError("fallback failed to construct connected panel masks")
    return left, right


def _effective_profile(
    profile: str,
    left_size: int,
    right_size: int,
) -> tuple[int, str]:
    _, _, desired_overlap, scheduled_relation = _PROFILE_SPECS[profile]
    if scheduled_relation == "right_subset" and right_size < left_size:
        return right_size, "right_subset"
    overlap = max(1, min(desired_overlap, left_size - 1, right_size - 1))
    return overlap, "partial"


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task input; the runner applies the Racket rule."""
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    default_left, default_right, _, _ = _PROFILE_SPECS[profile]

    effective_overrides = dict(overrides)
    effective_overrides.setdefault("density_l", default_left)
    effective_overrides.setdefault("density_r", default_right)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    left_size = ctx.draw_int_strict("density_l", 3, 9)
    right_size = ctx.draw_int_strict("density_r", 3, 9)
    overlap, relation = _effective_profile(profile, left_size, right_size)

    left, right = _construct_pair(
        ctx.draw_rng(f"masks:{difficulty or 'none'}:{profile}:{relation}"),
        left_size,
        right_size,
        overlap,
        relation,
    )
    grid = full_grid(5, 11, 0)
    for row, column in left:
        grid[row][column] = 1
    for row, column in right:
        grid[row][column + 6] = 1

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid Boolean-gallery input: {errors}")
    observed = observe_overrides(grid)
    expected = {"density_l": left_size, "density_r": right_size}
    if observed != expected:
        raise RuntimeError(f"exact-axis mismatch: {observed!r} != {expected!r}")
    return _copy_grid(grid)


def _analyze(grid: Any) -> dict[str, Any]:
    if not isinstance(grid, list) or len(grid) != 5:
        return {"errors": ["grid must be exactly 5x11"]}
    if any(not isinstance(row, list) or len(row) != 11 for row in grid):
        return {"errors": ["grid must be exactly 5x11"]}
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be literal ARC integers 0..9"]}

    errors: list[str] = []
    if any(grid[row][5] != 0 for row in range(5)):
        errors.append("separator column 5 must stay background")

    panel_values = {
        grid[row][column]
        for row in range(5)
        for column in tuple(range(5)) + tuple(range(6, 11))
    }
    if not panel_values <= {0, 1}:
        errors.append(
            "both panels must use only background 0 and foreground color 1"
        )

    left = {
        (row, column)
        for row in range(5)
        for column in range(5)
        if grid[row][column] != 0
    }
    right = {
        (row, column - 6)
        for row in range(5)
        for column in range(6, 11)
        if grid[row][column] != 0
    }
    if not left:
        errors.append("left panel must contain a foreground shape")
    if not right:
        errors.append("right panel must contain a foreground shape")
    if left and not _is_connected(left):
        errors.append("left panel cells must form one 4-connected component")
    if right and not _is_connected(right):
        errors.append("right panel cells must form one 4-connected component")
    if left and not 3 <= len(left) <= 9:
        errors.append(f"left panel size must be in 3..9, got {len(left)}")
    if right and not 3 <= len(right) <= 9:
        errors.append(f"right panel size must be in 3..9, got {len(right)}")
    if left and right and not left & right:
        errors.append("intersection must be non-empty")
    if left and right and not left ^ right:
        errors.append("xor must be non-empty")

    counts = Counter({state: 0 for state in ("00", "10", "01", "11")})
    for row in range(5):
        for column in range(5):
            state = f"{int((row, column) in left)}{int((row, column) in right)}"
            counts[state] += 1
    return {
        "errors": errors,
        "left": left,
        "right": right,
        "counts": dict(counts),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the fixed two-panel input grammar."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def occupancy_counts(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return dict(analysis["counts"])


def occupancy_signature(grid) -> tuple[int, int, int, int]:
    counts = occupancy_counts(grid)
    return tuple(counts[state] for state in ("00", "10", "01", "11"))


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "density_l": len(analysis["left"]),
        "density_r": len(analysis["right"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Accept the exact public grammar and one of its occupancy signatures."""
    errors = self_check(grid)
    if errors:
        return errors
    signature = occupancy_signature(grid)
    if signature not in _CANONICAL_SIGNATURES:
        return [f"occupancy signature {signature} is not public-canonical"]
    return []


def _split_masks(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["left"], analysis["right"]


def _gallery(
    grid,
    union_predicate: Callable[[bool, bool], bool],
    intersection_predicate: Callable[[bool, bool], bool],
    xor_predicate: Callable[[bool, bool], bool],
):
    left, right = _split_masks(grid)
    output = full_grid(5, 17, 0)
    for row in range(5):
        for column in range(5):
            a = (row, column) in left
            b = (row, column) in right
            if union_predicate(a, b):
                output[row][column] = 2
            if intersection_predicate(a, b):
                output[row][column + 6] = 3
            if xor_predicate(a, b):
                output[row][column + 12] = 4
    return output


def rule_mirror(grid):
    """Independent Python mirror; the selected Racket program remains authority."""
    return _gallery(
        grid,
        lambda a, b: a or b,
        lambda a, b: a and b,
        lambda a, b: a != b,
    )


def _swap_union_intersection(grid):
    return _gallery(
        grid,
        lambda a, b: a and b,
        lambda a, b: a or b,
        lambda a, b: a != b,
    )


def _swap_intersection_xor(grid):
    return _gallery(
        grid,
        lambda a, b: a or b,
        lambda a, b: a != b,
        lambda a, b: a and b,
    )


def _recolor_left_three_times(grid):
    return _gallery(grid, lambda a, b: a, lambda a, b: a, lambda a, b: a)


def _recolor_right_three_times(grid):
    return _gallery(grid, lambda a, b: b, lambda a, b: b, lambda a, b: b)


def _xor_left_minus_right(grid):
    return _gallery(
        grid,
        lambda a, b: a or b,
        lambda a, b: a and b,
        lambda a, b: a and not b,
    )


def _xor_right_minus_left(grid):
    return _gallery(
        grid,
        lambda a, b: a or b,
        lambda a, b: a and b,
        lambda a, b: b and not a,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "swap_union_intersection": _swap_union_intersection,
    "swap_intersection_xor": _swap_intersection_xor,
    "recolor_left_three_times": _recolor_left_three_times,
    "recolor_right_three_times": _recolor_right_three_times,
    "xor_left_minus_right": _xor_left_minus_right,
    "xor_right_minus_left": _xor_right_minus_left,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "recolor_left_three_times": _recolor_left_three_times,
    "recolor_right_three_times": _recolor_right_three_times,
    "xor_left_minus_right": _xor_left_minus_right,
    "xor_right_minus_left": _xor_right_minus_left,
}


def _witness_partial_truth_table(grid) -> bool:
    try:
        counts = occupancy_counts(grid)
    except ValueError:
        return False
    return all(counts[state] > 0 for state in ("00", "10", "01", "11"))


def _witness_right_subset(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["right"] < analysis["left"]


def _witness_refutes(grid, *, rival: Callable[[Any], list[list[int]]]) -> bool:
    try:
        return rule_mirror(grid) != rival(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "partial_truth_table": _witness_partial_truth_table,
    "right_subset_branch": _witness_right_subset,
}
WITNESS_RIVALS = {
    "partial_truth_table": list(SEMANTIC_RIVALS),
    "right_subset_branch": [
        "swap_union_intersection",
        "swap_intersection_xor",
        "recolor_left_three_times",
        "recolor_right_three_times",
        "xor_right_minus_left",
    ],
}
BRANCH_WITNESSES = set(SEMANTIC_WITNESSES)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if labels are wrong or any named rival survives demos."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    all_pairs = list(demos) + [query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(pair["input"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"pair {index} is outside the rule domain: {exc}")
            continue
        if expected != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the Boolean gallery")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(deepcopy(demo["input"])) == demo["output"]
                for demo in demos
            )
        except Exception as exc:
            reasons.append(
                f"competitor {name} crashed: {type(exc).__name__}: {exc}"
            )
            continue
        if survives:
            reasons.append(f"demonstrations fail to refute rival {name}")
    return reasons
