"""Generator for ``f7072db3091a``: mark blue-line endpoints orange.

The ordinary distribution mirrors the canonical grammar: two to four isolated
straight blue lines, both orientations represented, plus one or two color-5
distractor cells that the rule must preserve.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f7072db3091a"
TASK_ID = "f7072db3091a"
VERSION = "4.0.0"  # exact overrides, canonical distractors, semantic contract
RULE_HASH = "9d3911a05c45"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "An 8..20 by 8..20 black grid contains 2..4 mutually separated straight "
    "blue(1) lines, with at least one horizontal and one vertical line, plus "
    "1..2 color-5 distractor cells. Recolor exactly the two endpoint cells of "
    "each blue line to orange(7). Preserve every blue interior cell, every "
    "color-5 distractor, and the background."
)

INVARIANTS = [
    "background is 0; line cells are 1; endpoint caps become 7",
    "there are 2..4 straight contiguous blue components of length at least two",
    "both horizontal and vertical blue lines occur in every ordinary instance",
    "generated blue components are placed in separated bands and never touch or cross",
    "one or two color-5 distractor cells are preserved by the rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/sample schedule with canonical profiles",
        "valid": "8..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/sample schedule with canonical profiles",
        "valid": "8..20",
    },
    "n_lines": {
        "type": "int",
        "default": "3 canonical-like; 2..4 scheduled elsewhere",
        "valid": "2..4",
    },
    "marker_count": {
        "type": "int",
        "default": "1 or 2 color-5 distractors",
        "valid": "1..2",
    },
}

_AXIS_RANGES = {
    "grid_h": (8, 20),
    "grid_w": (8, 20),
    "n_lines": (2, 4),
    "marker_count": (1, 2),
}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_CANONICAL_PROFILES = ((9, 10), (10, 11), (8, 12), (11, 10), (9, 12))
_MEDIUM_PROFILES = ((12, 13), (13, 15), (15, 12), (14, 16))
_HARD_PROFILES = ((16, 18), (18, 16), (20, 20), (17, 19))
_NEIGHBORS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside declared range {lo}..{hi}")


def _default_profile(sample_index: int, difficulty: Any) -> tuple[int, int]:
    # Every third draw uses a canonical profile in every band, keeping the
    # curriculum anchored while still exposing larger canvases.
    if sample_index % 3 == 0 or difficulty == "easy":
        return _CANONICAL_PROFILES[sample_index % len(_CANONICAL_PROFILES)]
    profiles = _HARD_PROFILES if difficulty == "hard" else _MEDIUM_PROFILES
    return profiles[sample_index % len(profiles)]


def _draw_scheduled_int(ctx, name: str, scheduled: int) -> int:
    lo, hi = _AXIS_RANGES[name]
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _line_cells_horizontal(row: int, start: int, length: int):
    return [(row, start + offset) for offset in range(length)]


def _line_cells_vertical(col: int, start: int, length: int):
    return [(start + offset, col) for offset in range(length)]


def _place_lines(grid, ctx, n_lines: int) -> list[list[tuple[int, int]]]:
    """Place an exact mixed set in separated upper/lower bands.

    Horizontal lines live above a two-row separator; vertical lines live below
    it. Within each band, selected rows/columns differ by at least two, so the
    promised Chebyshev halo is guaranteed without retry-dependent count drift.
    """
    h, w = len(grid), len(grid[0])
    split = h // 2
    top_rows = list(range(0, split, 2))
    bottom_start = split + 1
    vertical_cols = list(range(0, w, 2))
    if len(top_rows) < 2 or h - bottom_start < 2 or len(vertical_cols) < 2:
        raise ValueError(f"grid {h}x{w} is too small for the mixed-line grammar")

    if n_lines == 2:
        n_horizontal = 1
    elif n_lines == 3:
        n_horizontal = 1 + ((ctx.seed + ctx.sample_index) % 2)
    else:
        n_horizontal = 2
    n_vertical = n_lines - n_horizontal

    rng = ctx.draw_rng("line_layout")
    rng.shuffle(top_rows)
    rng.shuffle(vertical_cols)
    lines: list[list[tuple[int, int]]] = []

    used_lengths: set[int] = set()
    for index, row in enumerate(top_rows[:n_horizontal]):
        min_length = 3 if index == 0 else 2
        length = rng.randint(min_length, w)
        if length in used_lengths and length < w:
            length += 1
        used_lengths.add(length)
        start = rng.randint(0, w - length)
        cells = _line_cells_horizontal(row, start, length)
        lines.append(cells)

    vertical_height = h - bottom_start
    for index, col in enumerate(vertical_cols[:n_vertical]):
        min_length = 3 if not used_lengths and index == 0 else 2
        length = rng.randint(min_length, vertical_height)
        if length in used_lengths and length < vertical_height:
            length += 1
        used_lengths.add(length)
        start = rng.randint(bottom_start, h - length)
        cells = _line_cells_vertical(col, start, length)
        lines.append(cells)

    if len(lines) != n_lines:
        raise AssertionError(f"placed {len(lines)} lines, expected {n_lines}")
    for cells in lines:
        for row, col in cells:
            grid[row][col] = 1
    return lines


def _place_markers(grid, ctx, marker_count: int) -> None:
    h, w = len(grid), len(grid[0])
    candidates = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 0
    ]
    rng = ctx.draw_rng("marker_positions")
    rng.shuffle(candidates)
    chosen: list[tuple[int, int]] = []
    for row, col in candidates:
        # Prefer isolated distractors for visual clarity, but do not make
        # adjacency to blue illegal: one canonical marker touches a blue end.
        if any(max(abs(row - rr), abs(col - cc)) <= 1 for rr, cc in chosen):
            continue
        chosen.append((row, col))
        if len(chosen) == marker_count:
            break
    if len(chosen) != marker_count:
        raise AssertionError("not enough empty cells for exact marker_count")
    for row, col in chosen:
        grid[row][col] = 5


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_profile(sample_index, difficulty)
    default_lines = 3 if difficulty in (None, "easy") else 2 + (sample_index % 3)
    default_markers = 1 + ((seed + sample_index) % 2)

    h = _draw_scheduled_int(ctx, "grid_h", default_h)
    w = _draw_scheduled_int(ctx, "grid_w", default_w)
    n_lines = _draw_scheduled_int(ctx, "n_lines", default_lines)
    marker_count = _draw_scheduled_int(ctx, "marker_count", default_markers)

    grid = full_grid(h, w, 0)
    _place_lines(grid, ctx, n_lines)
    _place_markers(grid, ctx, marker_count)
    return grid


def _components(grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _NEIGHBORS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _analyze(grid) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {}, ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {}, ["grid must be rectangular"]
    h, w = len(grid), width
    if not 8 <= h <= 20 or not 8 <= w <= 20:
        errors.append(f"grid dimensions must be 8..20, got {h}x{w}")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 1, 5}:
        errors.append(f"input palette must be a subset of {{0,1,5}}, got {sorted(palette)}")

    lines = _components(grid, 1)
    orientations: list[str] = []
    lengths: list[int] = []
    for cells in lines:
        rows = sorted({row for row, _col in cells})
        cols = sorted({col for _row, col in cells})
        lengths.append(len(cells))
        if len(cells) < 2:
            errors.append("blue line components must have length at least two")
        elif len(rows) == 1 and cols == list(range(cols[0], cols[-1] + 1)):
            orientations.append("horizontal")
        elif len(cols) == 1 and rows == list(range(rows[0], rows[-1] + 1)):
            orientations.append("vertical")
        else:
            errors.append("every blue component must be one straight contiguous line")
    if not 2 <= len(lines) <= 4:
        errors.append(f"expected 2..4 blue line components, found {len(lines)}")
    if lines and set(orientations) != {"horizontal", "vertical"}:
        errors.append("ordinary/canonical-like scenes must contain both line orientations")

    marker_count = sum(value == 5 for row in grid for value in row)
    if not 1 <= marker_count <= 2:
        errors.append(f"expected 1..2 color-5 distractors, found {marker_count}")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "n_lines": len(lines),
        "marker_count": marker_count,
        "orientations": frozenset(orientations),
        "line_lengths": tuple(sorted(lengths)),
    }
    return facts, errors


def observe_overrides(grid) -> dict[str, int]:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {name: int(facts[name]) for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return _analyze(grid)[1]


def _oracle(grid):
    out = [row[:] for row in grid]
    for cells in _components(grid, 1):
        rows = {row for row, _col in cells}
        cols = {col for _row, col in cells}
        if len(rows) == 1:
            row = next(iter(rows))
            out[row][min(cols)] = 7
            out[row][max(cols)] = 7
        elif len(cols) == 1:
            col = next(iter(cols))
            out[min(rows)][col] = 7
            out[max(rows)][col] = 7
    return out


def _rival_recolor_all_blue(grid):
    return [[7 if value == 1 else value for value in row] for row in grid]


def _rival_recolor_all_nonzero(grid):
    return [[7 if value != 0 else 0 for value in row] for row in grid]


def _rival_horizontal_only(grid):
    out = [row[:] for row in grid]
    for cells in _components(grid, 1):
        rows = {row for row, _col in cells}
        cols = {col for _row, col in cells}
        if len(rows) == 1:
            row = next(iter(rows))
            out[row][min(cols)] = 7
            out[row][max(cols)] = 7
    return out


LESSON_COMPETITORS: dict[str, Callable] = {
    "recolor_all_blue": _rival_recolor_all_blue,
    "recolor_all_nonzero": _rival_recolor_all_nonzero,
    "horizontal_only": _rival_horizontal_only,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
CANONICAL_SHORTCUTS = dict(LESSON_COMPETITORS)


def _witness_blue_interior(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and any(length >= 3 for length in facts["line_lengths"])


def _witness_distractor_preserved(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["marker_count"] >= 1


def _witness_mixed_orientations(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["orientations"] == {"horizontal", "vertical"}


SEMANTIC_WITNESSES = {
    "blue_interiors_exist": _witness_blue_interior,
    "color5_distractor_present": _witness_distractor_preserved,
    "mixed_orientations": _witness_mixed_orientations,
}
WITNESS_RIVALS = {
    "blue_interiors_exist": ["recolor_all_blue"],
    "color5_distractor_present": ["recolor_all_nonzero"],
    "mixed_orientations": ["horizontal_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    del query
    if len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    parsed: list[tuple[Any, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict):
            reasons.append(f"demo {index} is not a pair dictionary")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        errors = strict_canonical_like(grid)
        if errors:
            reasons.append(f"demo {index} input violates grammar: {errors[0]}")
        elif output != _oracle(grid):
            reasons.append(f"demo {index} output is not the endpoint transform")
        else:
            parsed.append((grid, output))
    if len(parsed) < EXAMPLES_NEEDED:
        return reasons or ["too few complete demonstrations"]
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(grid) == output for grid, output in parsed):
            reasons.append(f"competitor {name!r} survives every demonstration")
    return reasons
