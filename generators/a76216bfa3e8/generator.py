"""Generator for ARC task 92e50de0.

A single marker pattern appears inside one cell of a line-separated lattice.
The output stamps that exact pattern into every cell whose lattice-row parity
AND lattice-column parity match the source cell.  A terminal partial cell is a
lawful destination, so stamping is clipped at the outer grid boundary.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a76216bfa3e8"
TASK_ID = GENERATOR_ID
RULE_HASH = "33baf0d7ad4c"
# 2.1.0 retains the observable grammar and canonical anchors from 2.0.0,
# while decoupling marker morphology from both source-parity axes across every
# four-demo lesson window and enforcing that counterfactual in validation.
VERSION = "2.1.0"
SUMMARY = (
    "Stamp the unique marker-cell pattern into every lattice cell sharing "
    "both source row parity and source column parity, clipping at partial edges."
)

INVARIANTS = [
    "background is color 0",
    "one dominant nonzero color forms complete separator rows and columns",
    "separator rows and columns occur every four cells after a 3-cell prefix",
    "exactly one full 3x3 lattice cell contains a supported marker pattern",
    "marker and separator colors are distinct",
    "the source parity class contains multiple destination cells",
    "terminal lattice cells may be 1, 2, or 3 cells wide/high and are clipped",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

# Every pattern is an exact 3x3 offset set.  The first four are the four
# canonical marker morphologies; the remaining four broaden surface form while
# preserving the same copy-by-parity operation.
_PATTERNS: dict[str, tuple[tuple[int, int], ...]] = {
    "canonical_diamond4": ((0, 1), (1, 0), (1, 2), (2, 1)),
    "canonical_fork6": ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "canonical_stair5": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    "canonical_hook4": ((0, 1), (1, 0), (1, 1), (2, 2)),
    "x5": ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
    "tee5": ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    "elbow5": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    "skew4": ((0, 0), (1, 0), (1, 1), (2, 2)),
}
_PATTERN_NAMES = tuple(_PATTERNS)
_PATTERN_BY_OFFSETS = {tuple(sorted(value)): name for name, value in _PATTERNS.items()}

AXES = {
    "n_cell_rows": {
        "type": "int",
        "default": "canonical anchors plus banded 6..8-cell exploration",
        "valid": "6..8",
    },
    "n_cell_cols": {
        "type": "int",
        "default": "canonical anchors plus banded 6..8-cell exploration",
        "valid": "6..8",
    },
    "tail_h": {
        "type": "int",
        "default": "8-slot schedule covering full and clipped terminal rows",
        "valid": "1..3",
    },
    "tail_w": {
        "type": "int",
        "default": "8-slot schedule covering full and clipped terminal columns",
        "valid": "1..3",
    },
    "line_color": {
        "type": "color",
        "default": "keyed nonzero draw distinct from marker_color",
        "valid": "1..9",
    },
    "marker_color": {
        "type": "color",
        "default": "keyed nonzero draw distinct from line_color",
        "valid": "1..9",
    },
    "marker_row_parity": {
        "type": "int",
        "default": "sample_index cycles 0,0,1,1",
        "valid": "0..1",
    },
    "marker_col_parity": {
        "type": "int",
        "default": "sample_index cycles 0,1,0,1",
        "valid": "0..1",
    },
    "marker_pattern": {
        "type": "str",
        "default": "8-slot seed-rotated schedule; repeated morphologies cross both parity axes",
        "valid": "canonical_diamond4|canonical_fork6|canonical_stair5|canonical_hook4|x5|tee5|elbow5|skew4",
    },
}
_ALLOWED_OVERRIDES = frozenset(AXES)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[()] = ()

# Slots 0..3 are exact canonical-profile anchors.  Slots 4..7 retain the same
# four-parity schedule but add rectangular and one-axis-only clipping forms.
# Every four consecutive sample indexes therefore cover all source parities;
# every four-index window also contains at least one clipped destination.
_CANONICAL_PROFILE_SCHEDULE = {
    0: (6, 6, 3, 3),  # 23x23
    1: (7, 7, 3, 3),  # 27x27
    2: (7, 7, 1, 1),  # 25x25
    3: (8, 8, 1, 1),  # 29x29
}
# Pin only the exploratory dimension needed to guarantee an output-visible
# clipped destination for that slot's scheduled source parity.
_EXPLORATORY_DIMENSION_SCHEDULE = {
    5: (7, None),  # parity 01 selects terminal row index 6
    6: (None, 7),  # parity 10 selects terminal col index 6
    7: (8, 8),     # parity 11 selects terminal row/col index 7
}
_TAIL_SCHEDULE = {
    0: (3, 3),
    1: (3, 3),
    2: (1, 1),
    3: (1, 1),
    4: (3, 3),
    5: (1, 3),
    6: (3, 1),
    7: (1, 1),
}
_PARITY_SCHEDULE = ((0, 0), (0, 1), (1, 0), (1, 1))
# The four local morphology roles occur at parity-opposite positions:
# 00<->11 or 01<->10.  Thus every four-demo window repeats a morphology while
# changing both parity coordinates.  Rotating the four-role block by seed keeps
# all eight supported morphologies in production without lengthening the
# existing eight-slot geometry/tail teaching period.
_PATTERN_ROLE_SCHEDULE = (0, 1, 1, 2, 2, 3, 3, 0)
LESSON_SCHEDULE_PERIOD = len(_PATTERN_ROLE_SCHEDULE)
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Return the deterministic eight-slot lesson-teaching profile."""
    del seed, difficulty
    return int(sample_index) % LESSON_SCHEDULE_PERIOD


def _scheduled_marker_pattern(seed: int, slot: int) -> str:
    start = int(seed) % len(_PATTERN_NAMES)
    role = _PATTERN_ROLE_SCHEDULE[slot]
    return _PATTERN_NAMES[(start + role) % len(_PATTERN_NAMES)]


def _crosses_both_parity_axes(parities: Iterable[tuple[int, int]]) -> bool:
    values = tuple(parities)
    return any(
        row_a != row_b and col_a != col_b
        for row_a, col_a in values
        for row_b, col_b in values
    )


def _normalize_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    normalized: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                normalized.append([int(value) for value in row])
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            normalized.append(list(row))
        else:
            return []
    return normalized


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_axis_int(
    ctx,
    label: str,
    valid_lo: int,
    valid_hi: int,
    default_lo: int,
    default_hi: int,
) -> int:
    """Honor the full declared override range while banding free draws."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _raise_incompatible(message: str, *axes: str) -> None:
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)  # checker-recognized structured veto
    raise error


def _draw_colors(ctx) -> tuple[int, int]:
    line_override = ctx.overrides.get("line_color")
    marker_override = ctx.overrides.get("marker_color")
    if line_override is not None and marker_override is not None:
        if int(line_override) == int(marker_override):
            _raise_incompatible(
                "line_color and marker_color must be distinct",
                "line_color",
                "marker_color",
            )
        line = ctx.draw_color("line_color", exclude={0, int(marker_override)})
        marker = ctx.draw_color("marker_color", exclude={0, line})
        return line, marker
    if marker_override is not None:
        marker = ctx.draw_color("marker_color", exclude={0})
        line = ctx.draw_color("line_color", exclude={0, marker})
        return line, marker
    line = ctx.draw_color("line_color", exclude={0})
    marker = ctx.draw_color("marker_color", exclude={0, line})
    return line, marker


def _cell_bounds(length: int, separators: Iterable[int]) -> list[tuple[int, int]]:
    boundaries = [-1, *separators, length]
    return [
        (boundaries[index] + 1, boundaries[index + 1] - 1)
        for index in range(len(boundaries) - 1)
    ]


def _analysis(grid: Any) -> dict[str, Any]:
    """Return exact lattice facts and structural errors for one input grid."""
    g = _normalize_grid(grid)
    errors: list[str] = []
    if not g or not g[0]:
        return {"errors": ["grid must be a nonempty rectangular sequence"]}
    width = len(g[0])
    if any(len(row) != width for row in g):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        return {"errors": ["cells must be integer ARC colors 0..9"]}

    height = len(g)
    if not (21 <= height <= 30 and 21 <= width <= 30):
        errors.append(f"dimensions {height}x{width} outside lawful 21..30 envelope")

    counts = Counter(value for row in g for value in row)
    nonzero = sorted(value for value in counts if value != 0)
    if len(nonzero) != 2:
        errors.append(f"expected exactly two nonzero colors, found {nonzero}")
        return {"errors": errors, "grid": g}

    line_candidates: list[tuple[int, list[int], list[int]]] = []
    for color in nonzero:
        rows = [
            row
            for row in range(height)
            if all(g[row][col] == color for col in range(width))
        ]
        cols = [
            col
            for col in range(width)
            if all(g[row][col] == color for row in range(height))
        ]
        if rows and cols:
            line_candidates.append((color, rows, cols))
    if len(line_candidates) != 1:
        errors.append(
            "expected exactly one nonzero color with both full separator rows "
            f"and columns, found {len(line_candidates)}"
        )
        return {"errors": errors, "grid": g}

    line_color, line_rows, line_cols = line_candidates[0]
    marker_color = next(color for color in nonzero if color != line_color)
    expected_rows = list(range(3, height, 4))
    expected_cols = list(range(3, width, 4))
    if line_rows != expected_rows:
        errors.append(
            f"separator rows must be {expected_rows}, found {line_rows}"
        )
    if line_cols != expected_cols:
        errors.append(
            f"separator columns must be {expected_cols}, found {line_cols}"
        )

    separator_cells = {
        (row, col)
        for row in line_rows
        for col in range(width)
    } | {
        (row, col)
        for col in line_cols
        for row in range(height)
    }
    stray_line = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if g[row][col] == line_color and (row, col) not in separator_cells
    ]
    if stray_line:
        errors.append(
            f"line color appears inside lattice cells at {stray_line[:3]}"
        )
    missing_line = [
        (row, col)
        for row, col in separator_cells
        if g[row][col] != line_color
    ]
    if missing_line:
        errors.append(
            f"separator lattice has non-line cells at {missing_line[:3]}"
        )
    if counts[line_color] <= counts[marker_color]:
        errors.append("separator color must be the dominant nonzero color")

    row_bounds = _cell_bounds(height, line_rows)
    col_bounds = _cell_bounds(width, line_cols)
    n_cell_rows, n_cell_cols = len(row_bounds), len(col_bounds)
    if not 6 <= n_cell_rows <= 8:
        errors.append(f"expected 6..8 lattice rows, found {n_cell_rows}")
    if not 6 <= n_cell_cols <= 8:
        errors.append(f"expected 6..8 lattice columns, found {n_cell_cols}")
    row_sizes = [end - start + 1 for start, end in row_bounds]
    col_sizes = [end - start + 1 for start, end in col_bounds]
    if any(size != 3 for size in row_sizes[:-1]) or row_sizes[-1] not in (1, 2, 3):
        errors.append(f"lattice row sizes must be 3,...,3,tail(1..3), found {row_sizes}")
    if any(size != 3 for size in col_sizes[:-1]) or col_sizes[-1] not in (1, 2, 3):
        errors.append(f"lattice column sizes must be 3,...,3,tail(1..3), found {col_sizes}")

    marker_positions = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if g[row][col] == marker_color
    ]
    occupied_cells: set[tuple[int, int]] = set()
    for row, col in marker_positions:
        row_index = next(
            (index for index, (start, end) in enumerate(row_bounds) if start <= row <= end),
            None,
        )
        col_index = next(
            (index for index, (start, end) in enumerate(col_bounds) if start <= col <= end),
            None,
        )
        if row_index is None or col_index is None:
            errors.append(f"marker lies on a separator at {(row, col)}")
        else:
            occupied_cells.add((row_index, col_index))
    if len(occupied_cells) != 1:
        errors.append(
            f"marker color must occupy exactly one lattice cell, found {sorted(occupied_cells)}"
        )
        marker_row = marker_col = -1
        offsets: tuple[tuple[int, int], ...] = ()
    else:
        marker_row, marker_col = next(iter(occupied_cells))
        row_start, row_end = row_bounds[marker_row]
        col_start, col_end = col_bounds[marker_col]
        if row_end - row_start + 1 != 3 or col_end - col_start + 1 != 3:
            errors.append("source marker cell must be a full 3x3 cell")
        offsets = tuple(
            sorted((row - row_start, col - col_start) for row, col in marker_positions)
        )

    marker_pattern = _PATTERN_BY_OFFSETS.get(offsets)
    if marker_pattern is None:
        errors.append(f"unsupported marker offsets {offsets}")

    if marker_row >= 0 and marker_col >= 0:
        parity_size = sum(
            row % 2 == marker_row % 2 and col % 2 == marker_col % 2
            for row in range(n_cell_rows)
            for col in range(n_cell_cols)
        )
        if parity_size < 2:
            errors.append("source parity class must contain at least two lattice cells")
    else:
        parity_size = 0

    return {
        "errors": errors,
        "grid": g,
        "height": height,
        "width": width,
        "line_color": line_color,
        "marker_color": marker_color,
        "line_rows": line_rows,
        "line_cols": line_cols,
        "row_bounds": row_bounds,
        "col_bounds": col_bounds,
        "n_cell_rows": n_cell_rows,
        "n_cell_cols": n_cell_cols,
        "tail_h": row_sizes[-1],
        "tail_w": col_sizes[-1],
        "marker_row": marker_row,
        "marker_col": marker_col,
        "marker_row_parity": marker_row % 2 if marker_row >= 0 else None,
        "marker_col_parity": marker_col % 2 if marker_col >= 0 else None,
        "marker_pattern": marker_pattern,
        "marker_offsets": offsets,
        "marker_positions": marker_positions,
        "parity_size": parity_size,
    }


def _stamp_with_selector(
    grid: Any,
    selector: Callable[[int, int, dict[str, Any]], bool],
    *,
    skip_partial: bool = False,
    fill_cells: bool = False,
) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [row[:] for row in info["grid"]]
    for row_index, (row_start, row_end) in enumerate(info["row_bounds"]):
        for col_index, (col_start, col_end) in enumerate(info["col_bounds"]):
            if not selector(row_index, col_index, info):
                continue
            if skip_partial and (
                row_end - row_start + 1 != 3 or col_end - col_start + 1 != 3
            ):
                continue
            if fill_cells:
                for row in range(row_start, row_end + 1):
                    for col in range(col_start, col_end + 1):
                        out[row][col] = info["marker_color"]
                continue
            for dr, dc in info["marker_offsets"]:
                row, col = row_start + dr, col_start + dc
                if row <= row_end and col <= col_end:
                    out[row][col] = info["marker_color"]
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror; the canonical Racket program remains authority."""
    return _stamp_with_selector(
        grid,
        lambda row, col, info: (
            row % 2 == info["marker_row_parity"]
            and col % 2 == info["marker_col_parity"]
        ),
    )


# Backward-compatible helper name used by older focused probes.
def _apply_rule(grid: Any) -> list[list[int]]:
    return rule_mirror(grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding lattice scenes."""
    del difficulty, meta
    info = _analysis(grid)
    errors = list(info["errors"])
    if not errors and rule_mirror(info["grid"]) == info["grid"]:
        errors.append("same-parity stamping must change at least one destination cell")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated grammar is a direct expansion of the canonical manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact declared axis from the returned input grid."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {
        "n_cell_rows": info["n_cell_rows"],
        "n_cell_cols": info["n_cell_cols"],
        "tail_h": info["tail_h"],
        "tail_w": info["tail_w"],
        "line_color": info["line_color"],
        "marker_color": info["marker_color"],
        "marker_row_parity": info["marker_row_parity"],
        "marker_col_parity": info["marker_col_parity"],
        "marker_pattern": info["marker_pattern"],
    }


def canonical_profile_signature(grid) -> str | None:
    info = _analysis(grid)
    if info["errors"] or info["height"] != info["width"]:
        return None
    profile = (
        info["n_cell_rows"],
        info["n_cell_cols"],
        info["tail_h"],
        info["tail_w"],
    )
    names = {
        (6, 6, 3, 3): "canonical_23",
        (7, 7, 3, 3): "canonical_27",
        (7, 7, 1, 1): "canonical_25",
        (8, 8, 1, 1): "canonical_29",
    }
    return names.get(profile)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    band = _band(difficulty)
    slot = schedule_profile(seed, sample_index, difficulty)
    geometry_slot = slot % len(_TAIL_SCHEDULE)

    # Caller overrides win.  Scheduled defaults are inserted before GenCtx is
    # constructed so every exact value has public keyed-draw provenance.
    effective = dict(overrides)
    row_parity, col_parity = _PARITY_SCHEDULE[int(sample_index) % 4]
    effective.setdefault("marker_row_parity", row_parity)
    effective.setdefault("marker_col_parity", col_parity)
    effective.setdefault("marker_pattern", _scheduled_marker_pattern(seed, slot))
    tail_h, tail_w = _TAIL_SCHEDULE[geometry_slot]
    effective.setdefault("tail_h", tail_h)
    effective.setdefault("tail_w", tail_w)
    if geometry_slot in _CANONICAL_PROFILE_SCHEDULE:
        n_rows, n_cols, canonical_tail_h, canonical_tail_w = _CANONICAL_PROFILE_SCHEDULE[geometry_slot]
        effective.setdefault("n_cell_rows", n_rows)
        effective.setdefault("n_cell_cols", n_cols)
        effective.setdefault("tail_h", canonical_tail_h)
        effective.setdefault("tail_w", canonical_tail_w)
    if geometry_slot in _EXPLORATORY_DIMENSION_SCHEDULE:
        scheduled_rows, scheduled_cols = _EXPLORATORY_DIMENSION_SCHEDULE[geometry_slot]
        if scheduled_rows is not None:
            effective.setdefault("n_cell_rows", scheduled_rows)
        if scheduled_cols is not None:
            effective.setdefault("n_cell_cols", scheduled_cols)

    # The ARC canvas is at most 30x30.  Make every *single* valid override
    # total by adapting only its unrequested partner.  Refuse only the two
    # genuinely impossible explicit tuples, where both involved axes are in
    # the caller's case and therefore form a structured incompatibility.
    if overrides.get("n_cell_rows") == 8 and overrides.get("tail_h") == 3:
        _raise_incompatible(
            "n_cell_rows=8 with tail_h=3 would exceed the 30-row ARC limit",
            "n_cell_rows",
            "tail_h",
        )
    if overrides.get("n_cell_cols") == 8 and overrides.get("tail_w") == 3:
        _raise_incompatible(
            "n_cell_cols=8 with tail_w=3 would exceed the 30-column ARC limit",
            "n_cell_cols",
            "tail_w",
        )
    if overrides.get("n_cell_rows") == 8 and "tail_h" not in overrides:
        effective["tail_h"] = min(int(effective.get("tail_h", 2)), 2)
    if overrides.get("tail_h") == 3 and "n_cell_rows" not in overrides:
        effective["n_cell_rows"] = min(int(effective.get("n_cell_rows", 7)), 7)
    if overrides.get("n_cell_cols") == 8 and "tail_w" not in overrides:
        effective["tail_w"] = min(int(effective.get("tail_w", 2)), 2)
    if overrides.get("tail_w") == 3 and "n_cell_cols" not in overrides:
        effective["n_cell_cols"] = min(int(effective.get("n_cell_cols", 7)), 7)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    default_ranges = {
        "easy": (6, 7),
        "medium": (6, 8),
        "hard": (7, 8),
    }
    lo, hi = default_ranges[band]
    tail_h = _draw_axis_int(ctx, "tail_h", 1, 3, 1, 3)
    tail_w = _draw_axis_int(ctx, "tail_w", 1, 3, 1, 3)
    # ARC grids are capped at 30x30.  Eight lattice cells are lawful only
    # when the terminal cell is one or two cells wide/high.  Free draws use
    # the compatible bound; an incompatible explicit tuple is rejected with
    # structured axis names so the override checker can distinguish it from
    # an accidental crash.
    row_default_hi = min(hi, 8 if tail_h <= 2 else 7)
    col_default_hi = min(hi, 8 if tail_w <= 2 else 7)
    n_cell_rows = _draw_axis_int(ctx, "n_cell_rows", 6, 8, lo, row_default_hi)
    n_cell_cols = _draw_axis_int(ctx, "n_cell_cols", 6, 8, lo, col_default_hi)
    if n_cell_rows == 8 and tail_h == 3:
        _raise_incompatible(
            "n_cell_rows=8 with tail_h=3 would exceed the 30-row ARC limit",
            "n_cell_rows",
            "tail_h",
        )
    if n_cell_cols == 8 and tail_w == 3:
        _raise_incompatible(
            "n_cell_cols=8 with tail_w=3 would exceed the 30-column ARC limit",
            "n_cell_cols",
            "tail_w",
        )
    line_color, marker_color = _draw_colors(ctx)
    marker_row_parity = ctx.draw_int("marker_row_parity", 0, 1)
    marker_col_parity = ctx.draw_int("marker_col_parity", 0, 1)
    marker_pattern = ctx.draw_choice("marker_pattern", _PATTERN_NAMES)

    height = (n_cell_rows - 1) * 4 + tail_h
    width = (n_cell_cols - 1) * 4 + tail_w
    grid = full_grid(height, width, 0)
    for row in range(3, height, 4):
        for col in range(width):
            grid[row][col] = line_color
    for col in range(3, width, 4):
        for row in range(height):
            grid[row][col] = line_color

    row_bounds = _cell_bounds(height, range(3, height, 4))
    col_bounds = _cell_bounds(width, range(3, width, 4))
    source_cells = [
        (row_index, col_index)
        for row_index, (row_start, row_end) in enumerate(row_bounds)
        for col_index, (col_start, col_end) in enumerate(col_bounds)
        if row_end - row_start + 1 == 3
        and col_end - col_start + 1 == 3
        and row_index % 2 == marker_row_parity
        and col_index % 2 == marker_col_parity
    ]
    if not source_cells:
        raise AssertionError("scheduled parity has no full 3x3 source cell")
    marker_row, marker_col = ctx.draw_rng("marker_cell").choice(source_cells)
    row_start = row_bounds[marker_row][0]
    col_start = col_bounds[marker_col][0]
    for dr, dc in _PATTERNS[marker_pattern]:
        grid[row_start + dr][col_start + dc] = marker_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator invariant failed: " + "; ".join(errors))
    return grid


# Plausible rival rules.  Each is executable on every lawful generated scene.
def rival_all_cells(grid):
    return _stamp_with_selector(grid, lambda row, col, info: True)


def rival_same_row_parity_only(grid):
    return _stamp_with_selector(
        grid,
        lambda row, col, info: row % 2 == info["marker_row_parity"],
    )


def rival_same_col_parity_only(grid):
    return _stamp_with_selector(
        grid,
        lambda row, col, info: col % 2 == info["marker_col_parity"],
    )


def rival_skip_partial_cells(grid):
    return _stamp_with_selector(
        grid,
        lambda row, col, info: (
            row % 2 == info["marker_row_parity"]
            and col % 2 == info["marker_col_parity"]
        ),
        skip_partial=True,
    )


def rival_fixed_even_even(grid):
    return _stamp_with_selector(grid, lambda row, col, info: row % 2 == 0 and col % 2 == 0)


def rival_fixed_odd_odd(grid):
    return _stamp_with_selector(grid, lambda row, col, info: row % 2 == 1 and col % 2 == 1)


def rival_fill_selected_cells(grid):
    return _stamp_with_selector(
        grid,
        lambda row, col, info: (
            row % 2 == info["marker_row_parity"]
            and col % 2 == info["marker_col_parity"]
        ),
        fill_cells=True,
    )


SEMANTIC_RIVALS = {
    "all_cells": rival_all_cells,
    "same_row_parity_only": rival_same_row_parity_only,
    "same_col_parity_only": rival_same_col_parity_only,
    "skip_partial_cells": rival_skip_partial_cells,
    "fixed_even_even": rival_fixed_even_even,
    "fixed_odd_odd": rival_fixed_odd_odd,
    "fill_selected_cells": rival_fill_selected_cells,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _lawful_info(grid) -> dict[str, Any] | None:
    info = _analysis(grid)
    return None if info["errors"] else info


def _rival_differs(grid, rival_name: str) -> bool:
    info = _lawful_info(grid)
    if info is None:
        return False
    return SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)


def _source_parity(grid, row_parity: int, col_parity: int) -> bool:
    info = _lawful_info(grid)
    return bool(
        info
        and info["marker_row_parity"] == row_parity
        and info["marker_col_parity"] == col_parity
    )


SEMANTIC_WITNESSES = {
    "source_parity_00": lambda grid: _source_parity(grid, 0, 0),
    "source_parity_01": lambda grid: _source_parity(grid, 0, 1),
    "source_parity_10": lambda grid: _source_parity(grid, 1, 0),
    "source_parity_11": lambda grid: _source_parity(grid, 1, 1),
    "and_not_row_only": lambda grid: _rival_differs(grid, "same_row_parity_only"),
    "and_not_col_only": lambda grid: _rival_differs(grid, "same_col_parity_only"),
    "not_all_cells": lambda grid: _rival_differs(grid, "all_cells"),
    "clipped_partial_destination": lambda grid: _rival_differs(grid, "skip_partial_cells"),
    "pattern_not_solid_fill": lambda grid: _rival_differs(grid, "fill_selected_cells"),
    "canonical_profile_anchor": lambda grid: canonical_profile_signature(grid) is not None,
}
WITNESS_RIVALS = {
    "source_parity_00": ["fixed_odd_odd"],
    "source_parity_01": ["fixed_even_even"],
    "source_parity_10": ["fixed_even_even"],
    "source_parity_11": ["fixed_even_even"],
    "and_not_row_only": ["same_row_parity_only"],
    "and_not_col_only": ["same_col_parity_only"],
    "not_all_cells": ["all_cells"],
    "clipped_partial_destination": ["skip_partial_cells"],
    "pattern_not_solid_fill": ["fill_selected_cells"],
    "canonical_profile_anchor": ["all_cells"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut survives all demonstrations."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query lacks an authoritative input/output pair"]

    errors: list[str] = []
    seen_parities: set[tuple[int, int]] = set()
    parities_by_morphology: dict[str, set[tuple[int, int]]] = {}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} lacks input/output")
            continue
        info = _analysis(demo["input"])
        if info["errors"]:
            errors.append(f"demo {index} is outside the lattice grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            errors.append(f"demo {index} output disagrees with the parity-stamp rule")
        parity = (info["marker_row_parity"], info["marker_col_parity"])
        seen_parities.add(parity)
        parities_by_morphology.setdefault(info["marker_pattern"], set()).add(parity)
    if seen_parities != {(0, 0), (0, 1), (1, 0), (1, 1)}:
        errors.append(f"demonstrations do not cover all four source parities: {sorted(seen_parities)}")
    if not any(
        _crosses_both_parity_axes(parities)
        for parities in parities_by_morphology.values()
    ):
        errors.append(
            "demonstrations never repeat a marker morphology across both source-parity axes"
        )
    if not any(_rival_differs(demo["input"], "skip_partial_cells") for demo in demos):
        errors.append("demonstrations contain no output-visible clipped partial destination")
    if errors:
        return sorted(set(errors))

    query_truth = query["output"]
    if query_truth != rule_mirror(query["input"]):
        return ["query output disagrees with the parity-stamp rule"]
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                errors.append(
                    f"competing rule {name!r} fits every demo but changes the query"
                )
    return sorted(set(errors))


# Handwritten inventories should fail at import rather than drift silently.
if tuple(_PATTERNS) != _PATTERN_NAMES:
    raise AssertionError("marker pattern order drifted")
if set(_PATTERN_BY_OFFSETS.values()) != set(_PATTERN_NAMES):
    raise AssertionError("marker patterns must have unique exact offset sets")
