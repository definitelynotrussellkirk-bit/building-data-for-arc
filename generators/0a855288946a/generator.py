"""Generator for ARC task ``0a855288946a`` (slug ``3c9b0459``).

The authoritative rule rotates the entire grid by 180 degrees.  Generated
inputs are deliberately asymmetric under every other D4 transform, so a
lesson cannot be solved by identity, a single flip, a quarter turn, or a
diagonal reflection.  Two of every four scheduled draws stay on the exact
canonical 3x3 / 2-or-3-color manifold; the remaining draws vary shape and
palette without changing the rule.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "0a855288946a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d4b6baaa86e7"

SUMMARY = (
    "Rotate the complete input grid by 180 degrees: cell (r,c) moves to "
    "(h-1-r,w-1-c), with dimensions and colors unchanged.  Every ordinary "
    "generated input is asymmetric and distinguishes this rule from identity, "
    "horizontal/vertical flips, 90/270-degree rotations, and both diagonal "
    "reflections.  A fixed four-draw schedule includes two canonical 3x3 "
    "anchors plus rectangular and larger-square generalization witnesses."
)

INVARIANTS = [
    "grid is rectangular with height and width in 3..8",
    "the realized palette has exactly 2..4 ARC colors",
    "at least four cells differ from the modal color and are not a line or solid rectangle",
    "the input differs from its 180-degree rotation",
    "the 180-degree output differs from every other D4 transform",
    "the Racket oracle alone owns output construction",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 3..6", "valid": "3..8"},
    "grid_w": {"type": "int", "default": "scheduled 3..6", "valid": "3..8"},
    "palette_size": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}

# Every Cartesian combination of the declared exact axes is constructible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "canonical_binary",
    "canonical_ternary",
    "rectangular_generalization",
    "larger_square_generalization",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive draws cover both canonical profiles and shape variation."""
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
    # Reflection across the anti-diagonal: rotate 180, then transpose.
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
    return {name: fn(grid) != expected for name, fn in SEMANTIC_RIVALS.items()}


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
    if not (3 <= height <= 8):
        errors.append(f"height {height} outside 3..8")
    if not (3 <= width <= 8):
        errors.append(f"width {width} outside 3..8")

    palette_size = len({value for row in grid for value in row})
    if not (2 <= palette_size <= 4):
        errors.append(f"expected exactly 2..4 colors, found {palette_size}")

    _, support = _modal_support(grid)
    if len(support) < 4:
        errors.append(f"need at least four non-modal cells, found {len(support)}")
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
    """Exact empirical manifold shared by all five canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    if len(grid) != 3 or len(grid[0]) != 3:
        reasons.append(f"canonical dimensions are exactly 3x3, found {len(grid)}x{len(grid[0])}")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (2, 3):
        reasons.append(f"canonical palette size is 2 or 3, found {palette_size}")
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
        "horizontal_flip_only", "vertical_flip_only"
    ],
    "orientation_structure_refutes_quarter_turns": ["rotate_90", "rotate_270"],
    "diagonal_structure_refutes_transposes": [
        "main_diagonal_reflection", "anti_diagonal_reflection"
    ],
}


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket remains authority."""
    return _rot180(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid exact demos that collectively refute every named rival."""
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
    if profile == "canonical_binary":
        return 3, 3, 2
    if profile == "canonical_ternary":
        return 3, 3, 3
    if profile == "rectangular_generalization":
        return {
            "easy": (3, 4, 2),
            "medium": (4, 5, 3),
            "hard": (5, 6, 4),
        }.get(difficulty, (4, 5, 3))
    return {
        "easy": (4, 4, 3),
        "medium": (5, 5, 3),
        "hard": (6, 6, 4),
    }.get(difficulty, (5, 5, 3))


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _candidate_grid(height: int, width: int, palette: tuple[int, ...], rng) -> list[list[int]]:
    positions = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(positions)
    values = [palette[index] for index in range(len(palette))]
    values.extend(rng.choice(palette) for _ in range(height * width - len(palette)))
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
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 3, 8)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 3, 8)
    palette_size = _scheduled_int(ctx, overrides, "palette_size", default_palette, 2, 4)
    palette = ctx.draw_distinct_colors("palette", n=palette_size)
    rng = ctx.draw_rng("cells")

    # Rejection sampling is deterministic because it uses only this keyed RNG.
    # The fallback below is defensive; the accepted rate is high for all axes.
    for _ in range(256):
        grid = _candidate_grid(height, width, palette, rng)
        if not self_check(grid):
            return grid
    raise RuntimeError(
        "could not construct a shortcut-disambiguating grid after 256 deterministic attempts"
    )
