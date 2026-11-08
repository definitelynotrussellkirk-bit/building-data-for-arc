"""Generator for 7bba59d92716 — recolor the middle of exact vertical 1-lines.

Selected rule
-------------
For every 4-connected color-1 component that is a *straight vertical line of
exactly five cells*, recolor its middle cell to 2.  Other color-1 components do
not change.

The ordinary curriculum is deliberately counterexample-rich.  Every generated
input contains exact targets plus all of the following non-targets:

* a five-cell vertical run with one or two non-midpoint side branches;
* one straight vertical line of length 3, 4, or 6;
* one horizontal line of length 5.

Those objects distinguish the component-aware rule from canonical-fitting
shortcuts such as "mark every vertical run of five" and "mark every five-cell
component".  Public axes are exact and recoverable from the returned pixels.
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7bba59d92716"
TASK_ID = GENERATOR_ID
RULE_HASH = "0f19aed9b60e"
VERSION = "2.1.0"
SUMMARY = (
    "Exact vertical color-1 components of length 5 are targets; ordinary grids "
    "also contain branched-run, wrong-length, and horizontal counterexamples."
)

PROFILE_SPECS = {
    "p8x10c4": (8, 10, 4),
    "p8x13c3": (8, 13, 3),
    "p9x12c4": (9, 12, 4),
    "p10x11c3": (10, 11, 3),
    "p10x13c3": (10, 13, 3),
}
PROFILES = tuple(PROFILE_SPECS)
TARGET_COUNTS = (2, 3)
DECOY_LENGTHS = (3, 4, 6)
# Two long decoys per four consecutive pairs make every query rotation
# retain at least one counterexample to the >=5 shortcut.
DECOY_SCHEDULE = (6, 3, 6, 4)
# Alternating six- and seven-cell branch components prevents a learner from
# memorizing one branch size; all arms are off the midpoint so the narrower
# "skip only a midpoint side-neighbor" shortcut is directly contradicted.
BRANCH_PATTERNS = ((0,), (1, 3), (4,), (0, 4))
DISTRACTOR_COUNTS = (2, 3, 4)

AXES = {
    "profile": {
        "type": "str",
        "default": "sample_index cycle over canonical profiles",
        "valid": "p8x10c4|p8x13c3|p9x12c4|p10x11c3|p10x13c3",
    },
    "n_targets": {
        "type": "int",
        "default": "sample_index cycle 2..3",
        "valid": "2..3",
    },
    "decoy_length": {
        "type": "int",
        "default": "rotation-safe 6|3|6|4 cycle",
        "valid": "3|4|6",
    },
    "n_distractors": {
        "type": "int",
        "default": "three-block cycle 2..4",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

INVARIANTS = [
    "2 or 3 exact vertical color-1 components of length 5",
    "one 6- or 7-cell branched color-1 component containing a vertical run of length 5",
    "one straight vertical color-1 decoy of length 3, 4, or 6",
    "one horizontal color-1 component of length 5",
    "2 to 4 color-6/7 distractor cells",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _difficulty_offset(difficulty) -> int:
    return {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the canonical profile scheduled for a default draw."""
    del seed  # The profile schedule is intentionally index-based and auditable.
    return PROFILES[(int(sample_index) + _difficulty_offset(difficulty)) % len(PROFILES)]


SCHEDULE_PROFILES = PROFILES


def _scheduled_choice(ctx, label: str, options: tuple, scheduled):
    """Draw an exact axis, retaining deterministic cyclic defaults.

    A caller override is checked against the complete domain.  On the default
    path the schedule supplies a singleton choice; across the declared cycle the
    full domain is visited.  In both cases GenCtx records the value used to build
    the returned grid, so default-draw provenance remains exact.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name, value in overrides.items():
        if value is None:
            continue
        if name == "profile":
            if type(value) is not str:
                raise TypeError("profile override must be a string")
            if value not in PROFILE_SPECS:
                raise ValueError(f"profile override {value!r} is not one of {PROFILES}")
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
        legal = {
            "n_targets": TARGET_COUNTS,
            "decoy_length": DECOY_LENGTHS,
            "n_distractors": DISTRACTOR_COUNTS,
        }[name]
        if value not in legal:
            raise ValueError(f"{name} override {value!r} is not one of {legal}")


def _column_layout(rng, width: int, count: int):
    """Choose separated vertical columns and an outward-pointing branch arm.

    The branch spine is always an extreme selected column.  Its arm points
    toward the nearer free edge, so it cannot bridge into another blue object.
    """
    candidates: list[tuple[tuple[int, ...], int, int]] = []
    for cols in combinations(range(width), count):
        if any(b - a < 2 for a, b in zip(cols, cols[1:])):
            continue
        if cols[0] > 0:
            candidates.append((cols, cols[0], -1))
        if cols[-1] < width - 1:
            candidates.append((cols, cols[-1], 1))
    if not candidates:
        raise ValueError(
            f"cannot place {count} separated vertical objects in width {width}"
        )
    cols, branch_col, arm_dc = rng.choice(candidates)
    remaining = [col for col in cols if col != branch_col]
    rng.shuffle(remaining)
    return branch_col, arm_dc, remaining


def _vertical_start(rng, height: int, length: int, horizontal_row: int) -> int:
    """Choose a vertical start with a full blank buffer row from the horizontal."""
    if horizontal_row == 0:
        choices = list(range(2, height - length + 1))
    else:
        choices = list(range(0, height - length - 1))
    if not choices:
        raise ValueError(
            f"height {height} cannot fit length {length} with horizontal buffer"
        )
    return rng.choice(choices)


def _paint_vertical(grid, start: int, col: int, length: int) -> None:
    for row in range(start, start + length):
        if grid[row][col] != 0:
            raise RuntimeError("constructive vertical placement collided")
        grid[row][col] = 1


def _put_distractors(grid, count: int, palette_size: int, rng) -> None:
    candidates = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    ]
    if len(candidates) < count:
        raise RuntimeError("not enough empty cells for declared distractors")
    chosen = rng.sample(candidates, count)

    if palette_size == 4:
        # Two distractors are always available, so both accent colors can be
        # guaranteed rather than left to chance.
        colors = [6, 7] + [rng.choice((6, 7)) for _ in range(count - 2)]
        rng.shuffle(colors)
    elif palette_size == 3:
        colors = [rng.choice((6, 7))] * count
    else:  # PROFILE_SPECS is closed, but keep failures loud if edited later.
        raise ValueError(f"unsupported profile palette size {palette_size}")

    for (row, col), color in zip(chosen, colors):
        grid[row][col] = color


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

    offset = _difficulty_offset(difficulty)
    profile = _scheduled_choice(
        ctx,
        "profile",
        PROFILES,
        schedule_profile(seed, sample_index, difficulty),
    )
    n_targets = _scheduled_choice(
        ctx,
        "n_targets",
        TARGET_COUNTS,
        TARGET_COUNTS[(int(sample_index) + offset) % len(TARGET_COUNTS)],
    )
    decoy_length = _scheduled_choice(
        ctx,
        "decoy_length",
        DECOY_LENGTHS,
        DECOY_SCHEDULE[int(sample_index) % len(DECOY_SCHEDULE)],
    )
    n_distractors = _scheduled_choice(
        ctx,
        "n_distractors",
        DISTRACTOR_COUNTS,
        DISTRACTOR_COUNTS[(int(sample_index) // 3 + offset) % len(DISTRACTOR_COUNTS)],
    )

    height, width, palette_size = PROFILE_SPECS[profile]
    grid = full_grid(height, width, 0)

    side_rng = ctx.draw_rng("horizontal_side")
    horizontal_row = side_rng.choice((0, height - 1))
    horizontal_start = ctx.draw_rng("horizontal_position").randint(0, width - 5)
    for col in range(horizontal_start, horizontal_start + 5):
        grid[horizontal_row][col] = 1

    branch_col, arm_dc, other_cols = _column_layout(
        ctx.draw_rng("vertical_columns"), width, n_targets + 2
    )
    target_cols = other_cols[:n_targets]
    decoy_col = other_cols[n_targets]
    starts_rng = ctx.draw_rng("vertical_starts")

    target_starts: list[int] = []
    for col in target_cols:
        start = _vertical_start(starts_rng, height, 5, horizontal_row)
        target_starts.append(start)
        _paint_vertical(grid, start, col, 5)

    branch_start = _vertical_start(starts_rng, height, 5, horizontal_row)
    _paint_vertical(grid, branch_start, branch_col, 5)
    arm_col = branch_col + arm_dc
    branch_offsets = BRANCH_PATTERNS[int(sample_index) % len(BRANCH_PATTERNS)]
    for offset in branch_offsets:
        arm_row = branch_start + offset
        if grid[arm_row][arm_col] != 0:
            raise RuntimeError("constructive branch arm placement collided")
        grid[arm_row][arm_col] = 1

    decoy_start = _vertical_start(
        starts_rng, height, decoy_length, horizontal_row
    )
    _paint_vertical(grid, decoy_start, decoy_col, decoy_length)

    _put_distractors(
        grid,
        n_distractors,
        palette_size,
        ctx.draw_rng("distractor_layout"),
    )

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and exact-axis observation
# ---------------------------------------------------------------------------


def _shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int for row in grid for value in row):
        return ["all cells must be integer ARC colors"]
    return []


def _components(grid, color: int = 1) -> list[list[tuple[int, int]]]:
    if _shape_errors(grid):
        return []
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for sr in range(height):
        for sc in range(width):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(sorted(cells))
    return result


def _is_vertical_line(cells: Iterable[tuple[int, int]], length=None) -> bool:
    cells = list(cells)
    if not cells or (length is not None and len(cells) != length):
        return False
    rows = sorted(row for row, _ in cells)
    cols = {col for _, col in cells}
    return len(cols) == 1 and rows == list(range(rows[0], rows[0] + len(rows)))


def _is_horizontal_line(cells: Iterable[tuple[int, int]], length=None) -> bool:
    cells = list(cells)
    if not cells or (length is not None and len(cells) != length):
        return False
    rows = {row for row, _ in cells}
    cols = sorted(col for _, col in cells)
    return len(rows) == 1 and cols == list(range(cols[0], cols[0] + len(cols)))


def _has_branched_run5(grid) -> bool:
    for cells in _components(grid, 1):
        if len(cells) <= 5:
            continue
        cell_set = set(cells)
        for col in {c for _, c in cells}:
            rows = sorted(row for row, c in cells if c == col)
            if rows and len(rows) == 5 and rows == list(range(rows[0], rows[0] + 5)):
                if any(c != col for _, c in cell_set):
                    return True
    return False


def observe_overrides(grid):
    """Recover every exact public axis from pixels; raise on ambiguity."""
    errors = _shape_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    palette = {value for row in grid for value in row}
    profile_matches = [
        name
        for name, dims in PROFILE_SPECS.items()
        if dims == (len(grid), len(grid[0]), len(palette))
    ]
    if len(profile_matches) != 1:
        raise ValueError(
            "grid does not realize exactly one declared canonical profile: "
            f"shape={len(grid)}x{len(grid[0])}, palette={sorted(palette)}"
        )

    components = _components(grid, 1)
    target_count = sum(_is_vertical_line(cells, 5) for cells in components)
    wrong_lengths = sorted(
        len(cells)
        for cells in components
        if _is_vertical_line(cells) and len(cells) in DECOY_LENGTHS
    )
    if len(wrong_lengths) != 1:
        raise ValueError(
            f"expected exactly one observable wrong-length vertical decoy, got {wrong_lengths}"
        )
    return {
        "profile": profile_matches[0],
        "n_targets": target_count,
        "decoy_length": wrong_lengths[0],
        "n_distractors": sum(
            value in (6, 7) for row in grid for value in row
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's accepted input grammar, not just generator internals."""
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    allowed_shapes = {(h, w) for h, w, _ in PROFILE_SPECS.values()}
    if (height, width) not in allowed_shapes:
        errors.append(
            f"shape {height}x{width} is outside the canonical profile manifold"
        )
    bad = sorted(
        {
            value
            for row in grid
            for value in row
            if value not in (0, 1, 6, 7)
        }
    )
    if bad:
        errors.append(
            f"input colors must be drawn from 0,1,6,7; found {bad}"
        )
    if not any(_is_vertical_line(cells, 5) for cells in _components(grid, 1)):
        errors.append(
            "no exact vertical color-1 component of length 5; the selected rule has no answer"
        )
    return errors


def strict_canonical_like(grid):
    """Accept canonical-profile inputs on which the selected rule has a target."""
    return self_check(grid)


# ---------------------------------------------------------------------------
# Rule mirror, plausible rivals, witnesses, and lesson contract
# ---------------------------------------------------------------------------


def _copy_grid(grid):
    return [list(row) for row in grid]


def rule_mirror(grid):
    out = _copy_grid(grid)
    for cells in _components(grid, 1):
        if _is_vertical_line(cells, 5):
            rows = sorted(row for row, _ in cells)
            out[rows[2]][cells[0][1]] = 2
    return out


def _run5_ignores_branches(grid):
    out = _copy_grid(grid)
    if _shape_errors(grid):
        return out
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 1:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 1:
                row += 1
            if row - start == 5:
                out[start + 2][col] = 2
    return out


def _run5_skips_midpoint_side_neighbor(grid):
    """Rival: recognize a branch only when its arm touches the midpoint."""
    out = _copy_grid(grid)
    if _shape_errors(grid):
        return out
    height, width = len(grid), len(grid[0])
    for col in range(width):
        row = 0
        while row < height:
            if grid[row][col] != 1:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == 1:
                row += 1
            if row - start != 5:
                continue
            middle = start + 2
            has_midpoint_arm = (
                (col > 0 and grid[middle][col - 1] == 1)
                or (col + 1 < width and grid[middle][col + 1] == 1)
            )
            if not has_midpoint_arm:
                out[middle][col] = 2
    return out


def _run5_skips_six_cell_branch(grid):
    """Rival: exempt only six-cell components containing a five-cell run."""
    out = _copy_grid(grid)
    for cells in _components(grid, 1):
        by_col: dict[int, list[int]] = {}
        for row, col in cells:
            by_col.setdefault(col, []).append(row)
        for col, rows in by_col.items():
            rows = sorted(rows)
            if len(rows) == 5 and rows == list(range(rows[0], rows[0] + 5)):
                if len(cells) != 6:
                    out[rows[2]][col] = 2
    return out


def _component_size5_any_shape(grid):
    out = _copy_grid(grid)
    for cells in _components(grid, 1):
        if len(cells) == 5:
            row, col = sorted(cells)[2]
            out[row][col] = 2
    return out


def _all_vertical_components(grid):
    out = _copy_grid(grid)
    for cells in _components(grid, 1):
        if _is_vertical_line(cells):
            rows = sorted(row for row, _ in cells)
            out[rows[(len(rows) - 1) // 2]][cells[0][1]] = 2
    return out


def _vertical_length_at_least5(grid):
    out = _copy_grid(grid)
    for cells in _components(grid, 1):
        if len(cells) >= 5 and _is_vertical_line(cells):
            rows = sorted(row for row, _ in cells)
            out[rows[(len(rows) - 1) // 2]][cells[0][1]] = 2
    return out


def _branched_run5_signatures(grid) -> list[tuple[int, tuple[int, ...]]]:
    result: list[tuple[int, tuple[int, ...]]] = []
    for cells in _components(grid, 1):
        if len(cells) <= 5:
            continue
        for col in sorted({c for _, c in cells}):
            rows = sorted(row for row, c in cells if c == col)
            if len(rows) != 5 or rows != list(range(rows[0], rows[0] + 5)):
                continue
            offsets = tuple(sorted(row - rows[0] for row, c in cells if c != col))
            if offsets:
                result.append((len(cells), offsets))
    return result


def _has_off_midpoint_branched_run5(grid) -> bool:
    return any(2 not in offsets for _, offsets in _branched_run5_signatures(grid))


def _has_branched_size7_run5(grid) -> bool:
    return any(size == 7 for size, _ in _branched_run5_signatures(grid))


def _has_horizontal5(grid) -> bool:
    return any(_is_horizontal_line(cells, 5) for cells in _components(grid, 1))


def _has_wrong_vertical(grid) -> bool:
    return any(
        _is_vertical_line(cells) and len(cells) in DECOY_LENGTHS
        for cells in _components(grid, 1)
    )


def _has_long_vertical(grid) -> bool:
    return any(_is_vertical_line(cells, 6) for cells in _components(grid, 1))


def _has_counterexample_bundle(grid) -> bool:
    """Ordinary-grid bundle used for one authoritative rival comparison."""
    return (
        _has_branched_run5(grid)
        and _has_horizontal5(grid)
        and _has_wrong_vertical(grid)
    )


SEMANTIC_WITNESSES: dict[str, Callable] = {
    "ordinary_counterexample_bundle": _has_counterexample_bundle,
    "branched_run5_decoy": _has_branched_run5,
    "off_midpoint_branched_run5": _has_off_midpoint_branched_run5,
    "branched_size7_run5": _has_branched_size7_run5,
    "horizontal_size5_decoy": _has_horizontal5,
    "wrong_length_vertical_decoy": _has_wrong_vertical,
    "long_vertical_decoy": _has_long_vertical,
}
SEMANTIC_RIVALS: dict[str, Callable] = {
    "run5_ignores_branches": _run5_ignores_branches,
    "run5_skips_midpoint_side_neighbor": _run5_skips_midpoint_side_neighbor,
    "run5_skips_six_cell_branch": _run5_skips_six_cell_branch,
    "component_size5_any_shape": _component_size5_any_shape,
    "all_vertical_components": _all_vertical_components,
    "vertical_length_at_least5": _vertical_length_at_least5,
}
WITNESS_RIVALS = {
    # All three counterexamples occur in the same ordinary grid, so one Racket
    # authority call can verify all three rival disagreements.  The individual
    # predicates remain first-class positive branch coverage below.
    "ordinary_counterexample_bundle": [
        "run5_ignores_branches",
        "run5_skips_midpoint_side_neighbor",
        "component_size5_any_shape",
        "all_vertical_components",
    ],
    "branched_size7_run5": ["run5_skips_six_cell_branch"],
}
BRANCH_WITNESSES = (
    "branched_run5_decoy",
    "off_midpoint_branched_run5",
    "branched_size7_run5",
    "horizontal_size5_decoy",
    "wrong_length_vertical_decoy",
    "long_vertical_decoy",
)
CANONICAL_SHORTCUTS = {
    "run5_ignores_branches": _run5_ignores_branches,
    "run5_skips_midpoint_side_neighbor": _run5_skips_midpoint_side_neighbor,
    "run5_skips_six_cell_branch": _run5_skips_six_cell_branch,
    "component_size5_any_shape": _component_size5_any_shape,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons when labeled demonstrations do not determine the query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} labeled demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled input/output pair"]

    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is not a labeled input/output pair")
            continue
        expected = rule_mirror(pair["input"])
        if expected != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and rival(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
