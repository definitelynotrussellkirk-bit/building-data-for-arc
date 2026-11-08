"""Generator for 71e2e99645f4 — classify three sections by hole geometry.

The selected Racket rule reads three fixed 4×4 sections, separated by zero
columns, and maps each section's zero pattern to one output color.  This module
samples inputs only; ``rule_mirror`` is a Python oracle used by review and
lesson checks.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71e2e99645f4"
TASK_ID = GENERATOR_ID
RULE_HASH = "d38a7d9b0fc4"
VERSION = "3.0.0"
SUMMARY = (
    "A fixed 4×14 input contains three 4×4 same-color sections at columns "
    "0..3, 5..8, and 10..13, separated by zero columns 4 and 9. Each section "
    "has exactly one of four zero patterns: none→2, centered 2×2→8, bottom "
    "2×2→4, or the four middle left/right edge cells→3. The output is 3×3; "
    "row i repeats the class color of section i."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
# The ordinary curriculum emits exactly 18 ordered class grids: three
# scheduled choices of the omitted hole class times all six section orders.
# Exact overrides intentionally expose the authority's wider 4^3 space, but
# the default finite teaching alphabet is the one the diversity gates sample.
EXPECTED_OUTPUT_CODOMAIN = 18

HOLE_PATTERNS = ("no_hole", "center_hole", "bottom_hole", "edge_hole")
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_SECTION_STARTS = (0, 5, 10)
_DIVIDER_COLUMNS = (4, 9)

_PATTERN_HOLES: dict[str, frozenset[tuple[int, int]]] = {
    "no_hole": frozenset(),
    "center_hole": frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}),
    "bottom_hole": frozenset({(2, 1), (2, 2), (3, 1), (3, 2)}),
    "edge_hole": frozenset({(1, 0), (1, 3), (2, 0), (2, 3)}),
}
_PATTERN_FROM_HOLES = {holes: name for name, holes in _PATTERN_HOLES.items()}
_PATTERN_CLASS = {
    "no_hole": 2,
    "center_hole": 8,
    "bottom_hole": 4,
    "edge_hole": 3,
}

INVARIANTS = [
    "input is exactly 4×14 with zero divider columns 4 and 9",
    "all nonzero cells share one fill color in 1..9",
    "each 4×4 section has one exact canonical hole pattern",
    "edge_hole removes only rows 1 and 2 at local columns 0 and 3",
]

AXES = {
    "fill_color": {
        "type": "color",
        "default": "keyed draw from 1..9",
        "valid": "1..9",
    },
    "hole_patterns": {
        "type": "list",
        "default": "three scheduled canonical pattern names",
        "valid": "length 3; entries in no_hole|center_hole|bottom_hole|edge_hole",
        "probe": "diagnostic",
    },
}

# No texture alias or invalid bypass is part of this task's public domain.
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "omit_center_hole",
    "omit_bottom_hole",
    "omit_edge_hole",
)


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))


def _validate_pattern_list(value: Any) -> list[str]:
    if type(value) is not list:
        raise TypeError("hole_patterns override must be a list")
    if len(value) != 3:
        raise ValueError("hole_patterns must contain exactly three entries")
    if any(type(item) is not str for item in value):
        raise TypeError("hole_patterns entries must be strings")
    unknown = [item for item in value if item not in HOLE_PATTERNS]
    if unknown:
        raise ValueError(
            f"hole_patterns entries {unknown!r} are not in {list(HOLE_PATTERNS)!r}"
        )
    return list(value)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the three-step curriculum profile selected by ``sample_index``."""
    del seed, difficulty
    omitted = ("center_hole", "bottom_hole", "edge_hole")[sample_index % 3]
    return f"omit_{omitted}"


def _default_patterns(ctx, sample_index: int, difficulty: str | None) -> list[str]:
    omitted = schedule_profile(ctx.seed, sample_index, difficulty).removeprefix("omit_")
    patterns = [name for name in HOLE_PATTERNS if name != omitted]
    # There are exactly three distinct patterns, including no_hole.  Shuffle by
    # a keyed internal draw, then rotate by band so difficulty is observable
    # without changing the semantic coverage guarantee.
    ctx.draw_rng("pattern_order").shuffle(patterns)
    offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return patterns[offset:] + patterns[:offset]


def _apply_pattern(grid: list[list[int]], section_start: int, pattern: str) -> None:
    for row, col in _PATTERN_HOLES[pattern]:
        grid[row][section_start + col] = 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input and honor every advertised override."""
    _validate_call(seed, sample_index, difficulty, overrides)
    if overrides.get("hole_patterns") is not None:
        requested_patterns = _validate_pattern_list(overrides["hole_patterns"])
    else:
        requested_patterns = None

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    fill_color = ctx.draw_color_strict("fill_color", exclude={0})
    if requested_patterns is None:
        requested_patterns = _default_patterns(ctx, sample_index, difficulty)
    # Structured list axes use a one-option keyed choice. This records exact
    # provenance and lets GenCtx independently enforce override equality.
    patterns = list(ctx.draw_choice("hole_patterns", [requested_patterns]))

    grid = full_grid(4, 14, fill_color)
    for row in range(4):
        for col in _DIVIDER_COLUMNS:
            grid[row][col] = 0
    for section_start, pattern in zip(_SECTION_STARTS, patterns):
        _apply_pattern(grid, section_start, pattern)

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError("generator produced an invalid grid: " + "; ".join(findings))
    return grid


def _grid_shape(grid: Any) -> tuple[int, int] | None:
    if type(grid) is not list or not grid:
        return None
    if any(type(row) is not list or not row for row in grid):
        return None
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None
    return len(grid), width


def _decode(grid: Any) -> tuple[int, list[str]]:
    """Return fill color and section patterns; raise on an invalid task input."""
    findings = self_check(grid)
    if findings:
        raise ValueError("input is outside the task grammar: " + "; ".join(findings))
    fill_color = next(value for row in grid for value in row if value != 0)
    patterns = []
    for start in _SECTION_STARTS:
        holes = frozenset(
            (row, col)
            for row in range(4)
            for col in range(4)
            if grid[row][start + col] == 0
        )
        patterns.append(_PATTERN_FROM_HOLES[holes])
    return fill_color, patterns


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concise reasons when ``grid`` is outside the exact task grammar."""
    del difficulty, meta
    shape = _grid_shape(grid)
    if shape is None:
        return ["grid must be a non-empty rectangular list of non-empty rows"]
    height, width = shape
    if (height, width) != (4, 14):
        return [f"expected a 4×14 grid, got {height}×{width}"]

    bad_cell = next(
        (
            (row, col, value)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if type(value) is not int or not 0 <= value <= 9
        ),
        None,
    )
    if bad_cell is not None:
        row, col, value = bad_cell
        return [f"cell ({row},{col}) is not an integer ARC color: {value!r}"]

    reasons: list[str] = []
    for col in _DIVIDER_COLUMNS:
        if any(grid[row][col] != 0 for row in range(4)):
            reasons.append(f"divider column {col} must be all zero")

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 1:
        reasons.append(
            "all section fill cells must share exactly one nonzero color; "
            f"found {sorted(colors)}"
        )

    for section_index, start in enumerate(_SECTION_STARTS):
        holes = frozenset(
            (row, col)
            for row in range(4)
            for col in range(4)
            if grid[row][start + col] == 0
        )
        if holes not in _PATTERN_FROM_HOLES:
            reasons.append(
                f"section {section_index} has noncanonical holes {sorted(holes)}"
            )
    return reasons


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover both exact public axes from returned pixels."""
    fill_color, patterns = _decode(grid)
    return {"fill_color": fill_color, "hole_patterns": patterns}


def _rows_from_classes(classes: list[int]) -> list[list[int]]:
    return [[color, color, color] for color in classes]


def rule_mirror(grid):
    """Pure-Python mirror of the selected Racket rule on the task grammar."""
    _, patterns = _decode(grid)
    return _rows_from_classes([_PATTERN_CLASS[pattern] for pattern in patterns])


def _raw_section_holes(grid: list[list[int]]) -> list[frozenset[tuple[int, int]]]:
    return [
        frozenset(
            (row, col)
            for row in range(4)
            for col in range(4)
            if grid[row][start + col] == 0
        )
        for start in _SECTION_STARTS
    ]


def _rival_full_edge_columns(grid):
    """Wrong shortcut: class 3 only when both whole outer columns are holes."""
    if self_check(grid):
        raise ValueError("rival input is outside the task grammar")
    classes = []
    full_edges = frozenset(
        {(row, col) for row in range(4) for col in (0, 3)}
    )
    for holes in _raw_section_holes(grid):
        if not holes:
            classes.append(2)
        elif holes == full_edges:
            classes.append(3)
        elif holes == _PATTERN_HOLES["center_hole"]:
            classes.append(8)
        elif holes == _PATTERN_HOLES["bottom_hole"]:
            classes.append(4)
        else:
            classes.append(2)
    return _rows_from_classes(classes)


def _rival_four_zeros_means_center(grid):
    """Wrong shortcut: every four-zero section is the centered class 8."""
    if self_check(grid):
        raise ValueError("rival input is outside the task grammar")
    return _rows_from_classes([2 if not holes else 8 for holes in _raw_section_holes(grid)])


def _contains_pattern(name: str) -> Callable[[Any], bool]:
    def predicate(grid: Any) -> bool:
        try:
            return name in observe_overrides(grid)["hole_patterns"]
        except (TypeError, ValueError, IndexError):
            return False

    return predicate


SEMANTIC_RIVALS = {
    "full_edge_columns": _rival_full_edge_columns,
    "four_zeros_means_center": _rival_four_zeros_means_center,
}
SEMANTIC_WITNESSES = {
    "canonical_edge_geometry": _contains_pattern("edge_hole"),
    "vertical_position_matters": _contains_pattern("bottom_hole"),
}
WITNESS_RIVALS = {
    "canonical_edge_geometry": ["full_edge_columns"],
    "vertical_position_matters": ["four_zeros_means_center"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Validate a lesson and identify any declared rival left alive."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]

    reasons: list[str] = []
    validated_demos: list[dict[str, Any]] = []
    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"pair {index} is outside the grammar: {findings[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with the selected rule")
            continue
        if index < len(demos):
            validated_demos.append(pair)
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in validated_demos):
                reasons.append(f"demonstrations do not falsify rival: {name}")
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
    return reasons
