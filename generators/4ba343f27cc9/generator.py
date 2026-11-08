"""Generator for ``4ba343f27cc9``: rotate the whole grid by 180 degrees.

Four of every six scheduled draws use one of the task's exact canonical
``(height, width, palette-size)`` profiles.  The other two draws vary shape
while preserving the same global rule.  Every normal input is constructed so
identity, a single flip, a quarter turn, and either diagonal reflection all
predict a different output from the authoritative 180-degree rotation.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "4ba343f27cc9"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"  # distribution rewrite: canonical anchors + rival-killing scenes
RULE_HASH = "9703e0ed7747"  # normalized canonical (rule! (rotate-180 g))

SUMMARY = (
    "Rotate the complete input grid by 180 degrees: cell (r,c) moves to "
    "(h-1-r,w-1-c), with dimensions and colors unchanged. Four of each six "
    "scheduled draws exactly match a canonical shape/palette profile; every "
    "ordinary scene distinguishes the rule from identity, one-axis flips, "
    "quarter turns, and diagonal reflections."
)

INVARIANTS = [
    "grid is rectangular with height and width in 4..8",
    "the realized palette has exactly 7..10 ARC colors",
    "the modal-color support is neither a line nor a solid rectangle",
    "the input differs from its 180-degree rotation",
    "the 180-degree output differs from every other D4 transform",
    "the Racket oracle alone owns output construction",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus 4..8 generalization",
        "valid": "4..8",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus 4..8 generalization",
        "valid": "4..8",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled canonical 7/9/10-color profiles",
        "valid": "7..10",
    },
}

# Every Cartesian combination of the declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CANONICAL_PROFILES = (
    (4, 4, 7),
    (5, 5, 9),
    (5, 5, 10),
    (6, 6, 10),
)
_PROFILE_NAMES = (
    "canonical_4x4_palette7",
    "canonical_5x5_palette9",
    "canonical_5x5_palette10",
    "canonical_6x6_palette10",
    "rectangular_generalization",
    "larger_square_generalization",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.60


def schedule_profile(seed, sample_index, difficulty=None):
    """Every six-draw window contains all four exact canonical profiles."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rot90(grid):
    return [list(row) for row in zip(*reversed(grid))]


def _rot270(grid):
    return [list(row) for row in reversed(list(zip(*grid)))]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid):
    return _transpose(_rot180(grid))


SEMANTIC_RIVALS = {
    "identity": lambda grid: [list(row) for row in grid],
    "horizontal_flip_only": _flip_lr,
    "vertical_flip_only": _flip_ud,
    "rotate_90": _rot90,
    "rotate_270": _rot270,
    "main_diagonal_reflection": _transpose,
    "anti_diagonal_reflection": _anti_transpose,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_disagreements(grid) -> dict[str, bool]:
    expected = _rot180(grid)
    return {name: rival(grid) != expected for name, rival in SEMANTIC_RIVALS.items()}


def _modal_support(grid) -> tuple[int, set[tuple[int, int]]]:
    counts = Counter(value for row in grid for value in row)
    modal = min(counts, key=lambda value: (-counts[value], value))
    support = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != modal
    }
    return modal, support


def _is_solid_rectangle(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return area == len(cells)


def _validate_grid(grid) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"
                ]
    return len(grid), width, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, rule-hiding, and shortcut-compatible scenes."""
    del difficulty, meta
    height, width, errors = _validate_grid(grid)
    if errors:
        return errors
    if not (4 <= height <= 8):
        errors.append(f"height {height} outside 4..8")
    if not (4 <= width <= 8):
        errors.append(f"width {width} outside 4..8")

    palette_size = len({value for row in grid for value in row})
    if not (7 <= palette_size <= 10):
        errors.append(f"expected exactly 7..10 colors, found {palette_size}")

    _, support = _modal_support(grid)
    if len(support) < palette_size - 1:
        errors.append(
            f"need at least one non-modal witness per other color; found {len(support)}"
        )
    if support and len({r for r, _ in support}) == 1:
        errors.append("non-modal support may not be a single horizontal line")
    if support and len({c for _, c in support}) == 1:
        errors.append("non-modal support may not be a single vertical line")
    if _is_solid_rectangle(support):
        errors.append("non-modal support may not be a solid rectangle")

    if grid == _rot180(grid):
        errors.append("input must not be 180-degree symmetric")
    for name, differs in _rival_disagreements(grid).items():
        if not differs:
            errors.append(f"input does not distinguish 180-degree rotation from {name}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact canonical shape/palette manifold, after structural validation."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(
            f"profile {profile} is outside canonical profiles {_CANONICAL_PROFILES}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
    }


def _witness_identity(grid) -> bool:
    return not self_check(grid) and grid != _rot180(grid)


def _witness_single_flips(grid) -> bool:
    expected = _rot180(grid)
    return not self_check(grid) and expected != _flip_lr(grid) and expected != _flip_ud(grid)


def _witness_quarter_turns(grid) -> bool:
    expected = _rot180(grid)
    return not self_check(grid) and expected != _rot90(grid) and expected != _rot270(grid)


def _witness_diagonal_reflections(grid) -> bool:
    expected = _rot180(grid)
    return not self_check(grid) and expected != _transpose(grid) and expected != _anti_transpose(grid)


SEMANTIC_WITNESSES = {
    "asymmetry_refutes_identity": _witness_identity,
    "row_and_column_structure_refutes_single_flips": _witness_single_flips,
    "orientation_structure_refutes_quarter_turns": _witness_quarter_turns,
    "diagonal_structure_refutes_transposes": _witness_diagonal_reflections,
}

WITNESS_RIVALS = {
    "asymmetry_refutes_identity": ["identity"],
    "row_and_column_structure_refutes_single_flips": [
        "horizontal_flip_only",
        "vertical_flip_only",
    ],
    "orientation_structure_refutes_quarter_turns": ["rotate_90", "rotate_270"],
    "diagonal_structure_refutes_transposes": [
        "main_diagonal_reflection",
        "anti_diagonal_reflection",
    ],
}


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket remains authority."""
    return _rot180(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively refute every named rival."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact 180-degree rotation")
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    if profile == "canonical_4x4_palette7":
        return 4, 4, 7
    if profile == "canonical_5x5_palette9":
        return 5, 5, 9
    if profile == "canonical_5x5_palette10":
        return 5, 5, 10
    if profile == "canonical_6x6_palette10":
        return 6, 6, 10
    if profile == "rectangular_generalization":
        return {
            "easy": (4, 5, 7),
            "medium": (5, 6, 9),
            "hard": (6, 7, 10),
        }.get(difficulty, (5, 6, 9))
    return {
        "easy": (7, 7, 8),
        "medium": (8, 8, 9),
        "hard": (8, 8, 10),
    }.get(difficulty, (7, 7, 9))


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _candidate_grid(
    height: int,
    width: int,
    palette: tuple[int, ...],
    rng,
    difficulty,
) -> list[list[int]]:
    area = height * width
    minimum_marks = len(palette) - 1
    density = {"easy": 0.35, "medium": 0.48, "hard": 0.62}.get(difficulty, 0.45)
    target_marks = max(minimum_marks, round(area * density))
    # Keep the chosen background modal. With >=7 colors, distributing marks
    # round-robin makes this cap conservative even on the 4x4 / 10-color edge.
    target_marks = min(target_marks, area - 1)

    positions = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(positions)
    non_background = list(palette[1:])
    values = [non_background[index % len(non_background)] for index in range(target_marks)]
    rng.shuffle(values)

    grid = [[palette[0] for _ in range(width)] for _ in range(height)]
    for (r, c), value in zip(positions, values):
        grid[r][c] = value
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_palette = _profile_defaults(sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 4, 8)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 4, 8)
    palette_size = _scheduled_int(ctx, overrides, "palette_size", default_palette, 7, 10)
    palette = ctx.draw_distinct_colors("palette", n=palette_size)
    rng = ctx.draw_rng("cells")

    # Rejection sampling is deterministic because only the keyed RNG advances.
    for _ in range(256):
        grid = _candidate_grid(height, width, palette, rng, difficulty)
        if not self_check(grid):
            return grid
    raise RuntimeError(
        "could not construct a shortcut-disambiguating grid after 256 deterministic attempts"
    )
