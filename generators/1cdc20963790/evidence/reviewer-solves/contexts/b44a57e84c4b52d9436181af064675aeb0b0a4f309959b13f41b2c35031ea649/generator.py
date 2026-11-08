"""Generator for 1cdc20963790 — dispatch markers from row/column headers.

The top row and left column are copied color headers.  In the interior, a
blue marker (1) inherits the color at the left edge of its row, a red marker
(2) inherits the color at the top of its column, and background (0) stays 0.

The selected Racket program remains the label authority.  ``rule_mirror`` is
a deterministic Python mirror used only by review contracts and tests.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1cdc20963790"
TASK_ID = GENERATOR_ID
RULE_HASH = "2d0911ecb918"
VERSION = "4.0.0"
SUMMARY = (
    "The top row and left column are color headers. Interior 1 markers take "
    "their row header, interior 2 markers take their column header, and zeros "
    "remain background."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "balanced",
    "row_heavy",
    "column_heavy",
    "edge_mix",
)

INVARIANTS = [
    "shape is one of the three canonical profiles: 6x6, 7x7, or 7x8",
    "top-left is 0 and both headers contain unique keys from colors 2..8",
    "the union of the two headers is exactly colors 2..8 and both include 2",
    "interior cells are only 0, 1, or 2",
    "there are 2..6 markers of each type",
    "row and column dispatch each expose identity and non-identity evidence",
]

AXES = {
    "shape_profile": {
        "type": "str",
        "default": "profile-weighted canonical shape",
        "valid": "6x6|7x7|7x8",
    },
    "row_markers": {
        "type": "int",
        "default": "profile-weighted 2..6",
        "valid": "2..6",
    },
    "column_markers": {
        "type": "int",
        "default": "profile-weighted 2..6",
        "valid": "2..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_SHAPE_OPTIONS = ("6x6", "7x7", "7x8")
_SHAPE_DIMS = {
    "6x6": (6, 6),
    "7x7": (7, 7),
    "7x8": (7, 8),
}
_DIMS_SHAPE = {dims: name for name, dims in _SHAPE_DIMS.items()}
_KEYS = tuple(range(2, 9))

_PROFILE_COUNTS = {
    "balanced": (4, 4),
    "row_heavy": (6, 3),
    "column_heavy": (3, 6),
    "edge_mix": (5, 5),
}
_PROFILE_SHAPES = {
    "easy": {
        "balanced": "6x6",
        "row_heavy": "6x6",
        "column_heavy": "6x6",
        "edge_mix": "7x7",
    },
    "medium": {
        "balanced": "7x7",
        "row_heavy": "7x8",
        "column_heavy": "7x7",
        "edge_mix": "6x6",
    },
    "hard": {
        "balanced": "7x8",
        "row_heavy": "7x8",
        "column_heavy": "7x7",
        "edge_mix": "6x6",
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle all four teaching profiles in every consecutive four examples."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    if "shape_profile" in overrides and overrides["shape_profile"] is not None:
        value = overrides["shape_profile"]
        if type(value) is not str:
            raise TypeError("shape_profile must be a string")
        if value not in _SHAPE_OPTIONS:
            raise ValueError(
                f"shape_profile={value!r} outside {list(_SHAPE_OPTIONS)!r}"
            )

    for name in ("row_markers", "column_markers"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
        if not 2 <= value <= 6:
            raise ValueError(f"{name}={value} outside [2, 6]")


def _weighted_choice(ctx, name: str, options: tuple[Any, ...], preferred: Any):
    """Retain the full exact domain while strongly favoring a teaching anchor."""
    return ctx.draw_choice(name, options + (preferred,) * 64)


def _header_sequences(ctx, h: int, w: int) -> tuple[list[int], list[int]]:
    """Build unique canonical headers whose union is exactly colors 2..8."""
    rng = ctx.draw_rng("header_sequences")
    non_two = list(range(3, 9))
    rng.shuffle(non_two)

    top_missing_count = len(_KEYS) - (w - 1)
    left_missing_count = len(_KEYS) - (h - 1)
    top_missing = set(non_two[:top_missing_count])
    left_missing = set(
        non_two[top_missing_count : top_missing_count + left_missing_count]
    )

    top = [color for color in _KEYS if color not in top_missing]
    left = [color for color in _KEYS if color not in left_missing]
    rng.shuffle(top)
    rng.shuffle(left)
    return top, left


def _choose(rng, candidates, used: set[tuple[int, int]]) -> tuple[int, int]:
    options = [cell for cell in candidates if cell not in used]
    if not options:
        raise RuntimeError("constructive marker placement exhausted its candidates")
    return rng.choice(options)


def _marker_cells(
    grid: list[list[int]],
    row_count: int,
    column_count: int,
    rng,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """Place exact counts with branch, identity, and rival-refuting evidence."""
    h, w = len(grid), len(grid[0])
    row_two = next(r for r in range(1, h) if grid[r][0] == 2)
    col_two = next(c for c in range(1, w) if grid[0][c] == 2)
    used: set[tuple[int, int]] = set()

    # A row-dispatch identity case (1 -> row key 2), deliberately under a
    # different column key so the swapped/all-column rivals disagree.
    one_identity = _choose(
        rng,
        [(row_two, c) for c in range(1, w) if c != col_two],
        used,
    )
    used.add(one_identity)

    # A second row branch on another row key, also at a mismatched crossing.
    one_nonidentity = _choose(
        rng,
        [
            (r, c)
            for r in range(1, h)
            for c in range(1, w)
            if r != row_two and grid[r][0] != grid[0][c]
        ],
        used,
    )
    used.add(one_nonidentity)
    ones = [one_identity, one_nonidentity]

    # A column-dispatch identity case (2 -> column key 2), away from row key 2.
    two_identity = _choose(
        rng,
        [(r, col_two) for r in range(1, h) if r != row_two],
        used,
    )
    used.add(two_identity)

    # A second column branch on another column key and mismatched row crossing.
    two_nonidentity = _choose(
        rng,
        [
            (r, c)
            for r in range(1, h)
            for c in range(1, w)
            if c != col_two and grid[r][0] != grid[0][c]
        ],
        used,
    )
    used.add(two_nonidentity)
    twos = [two_identity, two_nonidentity]

    remaining = [
        (r, c)
        for r in range(1, h)
        for c in range(1, w)
        if (r, c) not in used
    ]
    rng.shuffle(remaining)
    need_ones = row_count - len(ones)
    ones.extend(remaining[:need_ones])
    used.update(remaining[:need_ones])

    remaining = [cell for cell in remaining[need_ones:] if cell not in used]
    need_twos = column_count - len(twos)
    twos.extend(remaining[:need_twos])
    if len(ones) != row_count or len(twos) != column_count:
        raise RuntimeError("failed to realize exact marker counts")
    return ones, twos


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    preferred_shape = _PROFILE_SHAPES[band][profile]
    preferred_rows, preferred_columns = _PROFILE_COUNTS[profile]

    shape = _weighted_choice(ctx, "shape_profile", _SHAPE_OPTIONS, preferred_shape)
    row_count = int(
        _weighted_choice(ctx, "row_markers", tuple(range(2, 7)), preferred_rows)
    )
    column_count = int(
        _weighted_choice(
            ctx,
            "column_markers",
            tuple(range(2, 7)),
            preferred_columns,
        )
    )

    h, w = _SHAPE_DIMS[shape]
    grid = full_grid(h, w, 0)
    top_keys, left_keys = _header_sequences(ctx, h, w)
    grid[0][0] = 0
    for c, color in enumerate(top_keys, start=1):
        grid[0][c] = color
    for r, color in enumerate(left_keys, start=1):
        grid[r][0] = color

    ones, twos = _marker_cells(
        grid,
        row_count,
        column_count,
        ctx.draw_rng("marker_layout"),
    )
    for r, c in ones:
        grid[r][c] = 1
    for r, c in twos:
        grid[r][c] = 2
    return grid


def _grid_shape(grid) -> tuple[int, int] | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return None
    return len(grid), w


def _marker_positions(grid, value: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(1, len(grid))
        for c in range(1, len(grid[0]))
        if grid[r][c] == value
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete canonical-shaped input grammar."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    h, w = shape
    errors: list[str] = []

    if shape not in _DIMS_SHAPE:
        errors.append(f"shape {h}x{w} is not one of 6x6, 7x7, or 7x8")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors
    if grid[0][0] != 0:
        errors.append("top-left cell must be background 0")

    top = list(grid[0][1:])
    left = [grid[r][0] for r in range(1, h)]
    if any(color not in _KEYS for color in top):
        errors.append("top header keys must all be colors 2..8")
    if len(set(top)) != len(top):
        errors.append("top header keys must be unique")
    if any(color not in _KEYS for color in left):
        errors.append("left header keys must all be colors 2..8")
    if len(set(left)) != len(left):
        errors.append("left header keys must be unique")
    if set(top) | set(left) != set(_KEYS):
        errors.append("header-key union must be exactly colors 2..8")
    if 2 not in top or 2 not in left:
        errors.append("both headers must contain color key 2")

    bad_interior = [
        (r, c, grid[r][c])
        for r in range(1, h)
        for c in range(1, w)
        if grid[r][c] not in (0, 1, 2)
    ]
    if bad_interior:
        errors.append(
            "interior cells must be only 0, 1, or 2; "
            f"first bad cell={bad_interior[0]}"
        )

    ones = _marker_positions(grid, 1)
    twos = _marker_positions(grid, 2)
    if not 2 <= len(ones) <= 6:
        errors.append(f"row markers (1) must number 2..6, found {len(ones)}")
    if not 2 <= len(twos) <= 6:
        errors.append(f"column markers (2) must number 2..6, found {len(twos)}")

    if ones and len({r for r, _c in ones}) < 2:
        errors.append("row markers must exercise at least two row keys")
    if twos and len({c for _r, c in twos}) < 2:
        errors.append("column markers must exercise at least two column keys")
    if ones and not any(grid[r][0] != grid[0][c] for r, c in ones):
        errors.append("row markers need a row/column-key mismatch witness")
    if twos and not any(grid[r][0] != grid[0][c] for r, c in twos):
        errors.append("column markers need a row/column-key mismatch witness")
    if ones and not any(grid[r][0] == 2 for r, _c in ones):
        errors.append("row markers need an identity witness under row key 2")
    if twos and not any(grid[0][c] == 2 for _r, c in twos):
        errors.append("column markers need an identity witness under column key 2")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All generated instances and all public canonical inputs use this manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised exact axis directly from returned pixels."""
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe malformed grid: " + "; ".join(findings[:3]))
    shape = _DIMS_SHAPE[(len(grid), len(grid[0]))]
    return {
        "shape_profile": shape,
        "row_markers": len(_marker_positions(grid, 1)),
        "column_markers": len(_marker_positions(grid, 2)),
    }


def _blank_with_headers(grid) -> list[list[int]]:
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    out[0] = list(grid[0])
    for r in range(1, h):
        out[r][0] = grid[r][0]
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected Racket row/column dispatch rule."""
    out = _blank_with_headers(grid)
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            if grid[r][c] == 1:
                out[r][c] = grid[r][0]
            elif grid[r][c] == 2:
                out[r][c] = grid[0][c]
    return out


# --- Explicit plausible wrong rules for semantic and lesson checks. ---

def _swapped_dispatch(grid):
    out = _blank_with_headers(grid)
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            if grid[r][c] == 1:
                out[r][c] = grid[0][c]
            elif grid[r][c] == 2:
                out[r][c] = grid[r][0]
    return out


def _all_row_dispatch(grid):
    out = _blank_with_headers(grid)
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            if grid[r][c] in (1, 2):
                out[r][c] = grid[r][0]
    return out


def _all_column_dispatch(grid):
    out = _blank_with_headers(grid)
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            if grid[r][c] in (1, 2):
                out[r][c] = grid[0][c]
    return out


def _preserve_markers(grid):
    return deepcopy(grid)


def _fixed_first_headers(grid):
    out = _blank_with_headers(grid)
    first_row_key = grid[1][0]
    first_column_key = grid[0][1]
    for r in range(1, len(grid)):
        for c in range(1, len(grid[0])):
            if grid[r][c] == 1:
                out[r][c] = first_row_key
            elif grid[r][c] == 2:
                out[r][c] = first_column_key
    return out


def _row_dispatch_mismatch(grid) -> bool:
    return any(grid[r][0] != grid[0][c] for r, c in _marker_positions(grid, 1))


def _column_dispatch_mismatch(grid) -> bool:
    return any(grid[r][0] != grid[0][c] for r, c in _marker_positions(grid, 2))


def _row_key_two_branch(grid) -> bool:
    return any(grid[r][0] == 2 for r, _c in _marker_positions(grid, 1))


def _column_key_two_branch(grid) -> bool:
    return any(grid[0][c] == 2 for _r, c in _marker_positions(grid, 2))


def _multiple_row_keys(grid) -> bool:
    return len({grid[r][0] for r, _c in _marker_positions(grid, 1)}) >= 2


def _multiple_column_keys(grid) -> bool:
    return len({grid[0][c] for _r, c in _marker_positions(grid, 2)}) >= 2


SEMANTIC_RIVALS: dict[str, Callable] = {
    "swapped_dispatch": _swapped_dispatch,
    "all_markers_use_row": _all_row_dispatch,
    "all_markers_use_column": _all_column_dispatch,
    "preserve_marker_colors": _preserve_markers,
    "fixed_first_headers": _fixed_first_headers,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "row_dispatch_mismatch": _row_dispatch_mismatch,
    "column_dispatch_mismatch": _column_dispatch_mismatch,
    "row_key_two_branch": _row_key_two_branch,
    "column_key_two_branch": _column_key_two_branch,
    "multiple_row_keys": _multiple_row_keys,
    "multiple_column_keys": _multiple_column_keys,
}
WITNESS_RIVALS = {
    "row_dispatch_mismatch": ["swapped_dispatch", "all_markers_use_column"],
    "column_dispatch_mismatch": ["swapped_dispatch", "all_markers_use_row"],
    "multiple_row_keys": ["fixed_first_headers"],
    "multiple_column_keys": ["fixed_first_headers"],
}
BRANCH_WITNESSES = (
    "row_key_two_branch",
    "column_key_two_branch",
)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared rival that fits all demos but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    normalized = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labeled pair")
            continue
        findings = strict_canonical_like(pair["input"])
        if findings:
            reasons.append(f"demo {index} is outside the strict manifold: {findings[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} label disagrees with the rule mirror")
            continue
        normalized.append(pair)
    if reasons:
        return reasons

    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]
    findings = strict_canonical_like(query["input"])
    if findings:
        return [f"query is outside the strict manifold: {findings[0]}"]
    query_truth = query.get("output", rule_mirror(query["input"]))
    if query_truth != rule_mirror(query["input"]):
        return ["query label disagrees with the rule mirror"]

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in normalized)
            changes_query = rival(query["input"]) != query_truth
        except Exception as exc:  # pragma: no cover - defensive diagnostics
            reasons.append(f"competitor {name} crashed: {exc!r}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
