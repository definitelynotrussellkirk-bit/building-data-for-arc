"""Generator for ``8862a204ce3a`` (left-header row flood).

The selected rule is exact and row-local: a nonzero value in column zero is a
row header, so the output replaces that entire row with the header color.
Rows whose header is zero become all-zero rows.  Ordinary lessons alternate
clean canonical-profile anchors with controlled counterexamples that disprove
two canonical-fitting shortcuts: preserving noise in zero-header rows and
preserving conflicting nonzero cells in marked rows.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8862a204ce3a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "067caed98cc7"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "A color-0 grid has two or three distinct nonzero row headers in column 0. "
    "The output floods each marked row with its header color and clears every "
    "zero-header row.  Ordinary lessons alternate clean canonical-size anchors "
    "with scenes containing both zero-header noise and a conflicting colored "
    "cell inside a marked row, so demonstrations identify overwrite/clear "
    "semantics rather than merely extending sparse rows."
)

INVARIANTS = [
    "background is color 0 and all nonzero cells use one of the distinct header colors",
    "every declared scene_profile fixes height, width, and exactly two or three headers",
    "row_layout exactly records whether the top and/or bottom row is marked",
    "contrast scenes contain zero-header noise and marker-row conflicts; anchors contain neither",
    "every advertised override is constructive and exactly recoverable from returned pixels",
    "the canonical Racket program, not the Python mirror, is output authority",
]

# Five exact source profiles plus five non-overlapping broad profiles.  Unique
# (height, width, marker-count) signatures make scene_profile pixel-observable.
_PROFILE_SPECS: dict[str, tuple[int, int, int]] = {
    "canonical_7x8_2": (7, 8, 2),
    "canonical_8x7_3": (8, 7, 3),
    "canonical_6x9_2": (6, 9, 2),
    "canonical_9x6_2": (9, 6, 2),
    "canonical_8x8_3": (8, 8, 3),
    "broad_6x6_2": (6, 6, 2),
    "broad_6x8_3": (6, 8, 3),
    "broad_7x9_3": (7, 9, 3),
    "broad_9x9_2": (9, 9, 2),
    "broad_7x7_2": (7, 7, 2),
}
SCENE_PROFILES = tuple(_PROFILE_SPECS)
_CANONICAL_PROFILES = tuple(name for name in SCENE_PROFILES if name.startswith("canonical_"))
_BROAD_PROFILES = tuple(name for name in SCENE_PROFILES if name.startswith("broad_"))
_PROFILE_BY_SIGNATURE = {spec: name for name, spec in _PROFILE_SPECS.items()}

ROW_LAYOUTS = ("interior", "top", "bottom", "both")
SCHEDULE_PROFILES = ("canonical", "contrast")

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "scheduled canonical/broad profile",
        "valid": "canonical_7x8_2|canonical_8x7_3|canonical_6x9_2|canonical_9x6_2|canonical_8x8_3|broad_6x6_2|broad_6x8_3|broad_7x9_3|broad_9x9_2|broad_7x7_2",
    },
    "row_layout": {
        "type": "enum",
        "default": "scheduled across all boundary layouts",
        "valid": "interior|top|bottom|both",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("scene_profile", "row_layout"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Return the pedagogical branch; every four consecutive slots are A/C/A/C."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_scene(seed: int, sample_index: int, branch: str,
                     difficulty: Any) -> str:
    group = _CANONICAL_PROFILES if branch == "canonical" else _BROAD_PROFILES
    # Pair index advances through all profiles while A/C alternation stays fixed.
    # A band offset keeps the public difficulty control live without changing
    # branch semantics or narrowing any exact override domain.
    band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    pair_index = int(sample_index) // 2
    return group[(pair_index + int(seed) + band_offset) % len(group)]


def _scheduled_layout(seed: int, sample_index: int) -> str:
    return ROW_LAYOUTS[(int(sample_index) + int(seed)) % len(ROW_LAYOUTS)]


def _draw_exact_choice(ctx, overrides: dict[str, Any], name: str, default: str,
                       options: tuple[str, ...]) -> str:
    allowed = options if overrides.get(name) is not None else (default,)
    return ctx.draw_choice(name, allowed)


def _marker_rows(h: int, count: int, layout: str, rng) -> list[int]:
    interior = list(range(1, h - 1))
    if layout == "interior":
        rows = rng.sample(interior, count)
    elif layout == "top":
        rows = [0, *rng.sample(interior, count - 1)]
    elif layout == "bottom":
        rows = [*rng.sample(interior, count - 1), h - 1]
    elif layout == "both":
        rows = [0, h - 1]
        if count == 3:
            rows.append(rng.choice(interior))
    else:  # guarded by draw_choice, retained as defense in depth
        raise ValueError(f"unknown row_layout {layout!r}")
    return sorted(rows)


def _put_contrast_noise(grid: list[list[int]], marker_rows: list[int],
                        marker_colors: tuple[int, ...], rng) -> None:
    """Construct both shortcut-killing witness classes without extra colors."""
    h, w = len(grid), len(grid[0])
    marked = set(marker_rows)

    zero_candidates = [(r, c) for r in range(h) if r not in marked for c in range(1, w)]
    zero_count = rng.randint(1, min(3, len(zero_candidates)))
    for r, c in rng.sample(zero_candidates, zero_count):
        grid[r][c] = rng.choice(marker_colors)

    conflict_candidates = [(r, c) for r in marker_rows for c in range(1, w)]
    conflict_count = rng.randint(1, min(3, len(conflict_candidates)))
    for r, c in rng.sample(conflict_candidates, conflict_count):
        header = grid[r][0]
        alternatives = [color for color in marker_colors if color != header]
        grid[r][c] = rng.choice(alternatives)


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides):
    _validate_call(difficulty, overrides)
    branch = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scene_profile = _draw_exact_choice(
        ctx,
        overrides,
        "scene_profile",
        _scheduled_scene(seed, sample_index, branch, difficulty),
        SCENE_PROFILES,
    )
    row_layout = _draw_exact_choice(
        ctx,
        overrides,
        "row_layout",
        _scheduled_layout(seed, sample_index),
        ROW_LAYOUTS,
    )
    h, w, marker_count = _PROFILE_SPECS[scene_profile]
    rows = _marker_rows(h, marker_count, row_layout, ctx.draw_rng("marker_rows"))
    colors = ctx.draw_distinct_colors("marker_colors", n=marker_count, exclude=(0,))

    grid = full_grid(h, w, 0)
    for row, color in zip(rows, colors):
        grid[row][0] = color
    if branch == "contrast":
        _put_contrast_noise(grid, rows, colors, ctx.draw_rng("contrast_noise"))
    return grid


def _grid_shape_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty sequence of rows"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "grid rows must be nonempty sequences"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return "grid must be rectangular"
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid values must be integers in 0..9"
    return None


def _marker_info(grid: list[list[int]] | tuple[tuple[int, ...], ...]):
    markers = [(r, row[0]) for r, row in enumerate(grid) if row[0] != 0]
    return markers, [color for _, color in markers]


def _profile_name(grid: Any) -> str | None:
    if _grid_shape_error(grid):
        return None
    markers, _ = _marker_info(grid)
    return _PROFILE_BY_SIGNATURE.get((len(grid), len(grid[0]), len(markers)))


def _layout_name(grid: Any) -> str | None:
    if _grid_shape_error(grid):
        return None
    markers, _ = _marker_info(grid)
    rows = {row for row, _ in markers}
    top = 0 in rows
    bottom = len(grid) - 1 in rows
    if top and bottom:
        return "both"
    if top:
        return "top"
    if bottom:
        return "bottom"
    return "interior"


def _noise_counts(grid: Any) -> tuple[int, int]:
    zero_header_noise = 0
    marker_row_conflicts = 0
    for row in grid:
        header = row[0]
        for value in row[1:]:
            if value == 0:
                continue
            if header == 0:
                zero_header_noise += 1
            elif value != header:
                marker_row_conflicts += 1
    return zero_header_noise, marker_row_conflicts


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    shape_error = _grid_shape_error(grid)
    if shape_error:
        return [shape_error]

    errors: list[str] = []
    profile = _profile_name(grid)
    if profile is None:
        errors.append(
            "height, width, and first-column marker count must match one declared scene_profile"
        )
        return errors

    markers, colors = _marker_info(grid)
    expected_count = _PROFILE_SPECS[profile][2]
    if len(markers) != expected_count:
        errors.append(f"expected {expected_count} first-column markers")
    if len(set(colors)) != len(colors):
        errors.append("first-column marker colors must be distinct")

    marker_colors = set(colors)
    present_nonzero = {value for row in grid for value in row if value != 0}
    unknown = sorted(present_nonzero - marker_colors)
    if unknown:
        errors.append(f"non-header colors are not allowed: {unknown}")

    for r, row in enumerate(grid):
        header = row[0]
        if header != 0 and any(value == header for value in row[1:]):
            errors.append(
                f"row {r} repeats its header color outside column 0; only conflicting controls are lawful"
            )

    zero_noise, conflicts = _noise_counts(grid)
    if zero_noise > 3:
        errors.append(f"zero-header noise count must be at most 3, found {zero_noise}")
    if conflicts > 3:
        errors.append(f"marker-row conflict count must be at most 3, found {conflicts}")
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """Require the exact source-profile grammar: source signature and no noise."""
    errors = list(self_check(grid))
    if errors:
        return errors
    profile = _profile_name(grid)
    if profile not in _CANONICAL_PROFILES:
        errors.append("grid does not have one of the five canonical profile signatures")
    if any(value != 0 for row in grid for value in row[1:]):
        errors.append("canonical-profile inputs contain only first-column markers")
    return errors


def observe_overrides(grid: Any) -> dict[str, str]:
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    profile = _profile_name(grid)
    layout = _layout_name(grid)
    assert profile is not None and layout is not None
    return {"scene_profile": profile, "row_layout": layout}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the selected canonical authority; never mutates input."""
    shape_error = _grid_shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    width = len(grid[0])
    return [[row[0]] * width if row[0] != 0 else [0] * width for row in grid]


def _preserve_zero_header_rows(grid: list[list[int]]) -> list[list[int]]:
    """Wrong canonical-fitting rule: fill headers but retain unmarked rows."""
    shape_error = _grid_shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    width = len(grid[0])
    return [[row[0]] * width if row[0] != 0 else list(row) for row in grid]


def _preserve_marker_conflicts(grid: list[list[int]]) -> list[list[int]]:
    """Wrong canonical-fitting rule: fill only blank cells of marked rows."""
    shape_error = _grid_shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    width = len(grid[0])
    output = full_grid(len(grid), width, 0)
    for r, row in enumerate(grid):
        header = row[0]
        if header == 0:
            continue
        output[r] = [header] + [value if value != 0 else header for value in row[1:]]
    return output


def _zero_header_noise_witness(grid: Any) -> bool:
    try:
        return _noise_counts(grid)[0] > 0 and _preserve_zero_header_rows(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _marker_row_conflict_witness(grid: Any) -> bool:
    try:
        return _noise_counts(grid)[1] > 0 and _preserve_marker_conflicts(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "preserve_zero_header_rows": _preserve_zero_header_rows,
    "preserve_marker_conflicts": _preserve_marker_conflicts,
}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "zero_header_noise": _zero_header_noise_witness,
    "marker_row_conflict": _marker_row_conflict_witness,
}
WITNESS_RIVALS = {
    "zero_header_noise": ["preserve_zero_header_rows"],
    "marker_row_conflict": ["preserve_marker_conflicts"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Report declared competitors not refuted by the demonstrations."""
    del query
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    reasons: list[str] = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        survives = True
        for pair in demos:
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                return ["lesson demonstrations must contain input and output grids"]
            try:
                candidate = rival(deepcopy(pair["input"]))
            except (TypeError, ValueError) as exc:
                return [f"invalid demonstration for {name}: {exc}"]
            if candidate != pair["output"]:
                survives = False
                break
        if survives:
            reasons.append(f"declared competitor {name!r} fits every demonstration")
    return reasons
