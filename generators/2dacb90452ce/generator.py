"""Generator for 2dacb90452ce — two-times nearest-neighbor upscale.

The selected rule replaces every input cell by a solid 2x2 block of the same
color.  The canonical task progresses through 2x2, 3x3, 4x4 and 5x5 square
inputs with respectively 3, 4, 5 and 8 visible colors.  This generator keeps
that 2..5 scale, regularly emits the exact profiles, and interleaves adjacent
palette counts so a learner cannot solve by recognizing only public profiles.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "2dacb90452ce"
TASK_ID = "2dacb90452ce"
RULE_HASH = "511f58f5d471"
VERSION = "3.1.0"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.25

CANONICAL_PALETTE_BY_SIZE = {2: 3, 3: 4, 4: 5, 5: 8}
ALLOWED_PALETTE_COUNTS_BY_SIZE = {
    2: (2, 3, 4),
    3: (3, 4, 5),
    4: (4, 5, 6),
    5: (7, 8, 9),
}

SUMMARY = (
    "Canonical-scale square input (2x2 through 5x5), with every third sample "
    "on the exact public size/palette profile and intervening samples using "
    "one fewer or one more visible color. Every color is visible, the "
    "arrangement varies in both axes and is not transpose-symmetric. Rule: "
    "replace EACH input cell with a solid 2x2 block of the same color."
)

INVARIANTS = [
    "input is square with side 2..5, matching the canonical scale",
    "palette cardinality is the canonical count or an adjacent lawful count",
    "every three-sample window contains one exact and two off-profile palettes",
    "every declared palette color is visible",
    "the grid varies horizontally and vertically",
    "the grid is not invariant under transpose",
]

AXES = {
    "grid_size": {
        "type": "int",
        "default": "difficulty-skewed 2..5",
        "valid": "2..5",
        "doc": "Square input side length; palette profile follows the canonical task.",
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[object] = []


def _upscale2(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of ``(upscale g 2)``."""
    out: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(2)]
        out.append(expanded[:])
        out.append(expanded[:])
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Public task-local statement of the selected authority."""
    return _upscale2(grid)


def _tile_each_whole_row(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: append each whole row to itself, then duplicate the row."""
    out: list[list[int]] = []
    for row in grid:
        tiled = list(row) + list(row)
        out.append(tiled[:])
        out.append(tiled[:])
    return out


def _tile_whole_grid(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: tile the complete input in a 2x2 arrangement."""
    rows = [list(row) + list(row) for row in grid]
    return [row[:] for row in rows] + [row[:] for row in rows]


def _transpose_then_upscale(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: transpose first, then upscale each transposed cell."""
    transposed = [list(row) for row in zip(*grid)]
    return _upscale2(transposed)


def _canonical_profile_only_else_grid_tile(
    grid: list[list[int]],
) -> list[list[int]]:
    """Wrong rival that memorizes the public size/palette manifold.

    It reproduces every canonical pair, but tiles the whole grid whenever the
    palette count is adjacent to (rather than exactly on) the public profile.
    """
    size = len(grid)
    palette_count = len({value for row in grid for value in row})
    if CANONICAL_PALETTE_BY_SIZE.get(size) == palette_count:
        return _upscale2(grid)
    return _tile_whole_grid(grid)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "tile_each_whole_row": _tile_each_whole_row,
    "tile_whole_grid_2x2": _tile_whole_grid,
    "transpose_then_upscale": _transpose_then_upscale,
    "canonical_profile_only_else_grid_tile": _canonical_profile_only_else_grid_tile,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "canonical_profile_only_else_grid_tile": _canonical_profile_only_else_grid_tile,
}
PER_INSTANCE_RIVALS = {
    name: rival
    for name, rival in SEMANTIC_RIVALS.items()
    if name not in CANONICAL_SHORTCUTS
}


def _refutes(rival_name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != _upscale2(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "cellwise_horizontal_repeat_not_row_tile": lambda grid: _refutes(
        "tile_each_whole_row", grid
    ),
    "cellwise_vertical_repeat_not_grid_tile": lambda grid: _refutes(
        "tile_whole_grid_2x2", grid
    ),
    "orientation_preserved_not_transposed": lambda grid: _refutes(
        "transpose_then_upscale", grid
    ),
    "off_profile_refutes_public_profile_gate": lambda grid: _refutes(
        "canonical_profile_only_else_grid_tile", grid
    ),
}
WITNESS_RIVALS = {
    "cellwise_horizontal_repeat_not_row_tile": ["tile_each_whole_row"],
    "cellwise_vertical_repeat_not_grid_tile": ["tile_whole_grid_2x2"],
    "orientation_preserved_not_transposed": ["transpose_then_upscale"],
    "off_profile_refutes_public_profile_gate": [
        "canonical_profile_only_else_grid_tile"
    ],
}


def _has_horizontal_variation(grid) -> bool:
    return any(
        row[c] != row[c + 1]
        for row in grid
        for c in range(len(row) - 1)
    )


def _has_vertical_variation(grid) -> bool:
    return any(
        grid[r][c] != grid[r + 1][c]
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]))
    )


def _is_transpose_symmetric(grid) -> bool:
    n = len(grid)
    return all(grid[r][c] == grid[c][r] for r in range(n) for c in range(n))


def _curriculum_rivals_refuted(grid: list[list[int]]) -> bool:
    expected = _upscale2(grid)
    return all(rival(grid) != expected for rival in PER_INSTANCE_RIVALS.values())


def _scheduled_palette_count(size: int, sample_index: int) -> int:
    """Cycle exact, lower-neighbor, upper-neighbor palette counts."""
    canonical = CANONICAL_PALETTE_BY_SIZE[size]
    residue = sample_index % 3
    if residue == 0:
        return canonical
    return canonical - 1 if residue == 1 else canonical + 1


def _palette(ctx, size: int, count: int) -> tuple[int, ...]:
    if size == 2:
        # The canonical 2x2 input has no zero; nearby profiles keep the same
        # object-free visual grammar while varying only palette cardinality.
        return ctx.draw_distinct_colors("palette", n=count, exclude={0})
    foreground = ctx.draw_distinct_colors("palette", n=count - 1, exclude={0})
    return (0, *foreground)


def _candidate_values(size: int, palette: tuple[int, ...], difficulty, rng) -> list[int]:
    """Return one multiset containing every palette color at least once."""
    area = size * size
    values = list(palette)
    remaining = area - len(values)
    dominant = rng.choice(palette)

    if difficulty == "easy":
        # A clear repeated-color region, while all palette colors remain visible.
        values.extend([dominant] * remaining)
    elif difficulty == "hard":
        # More balanced, visually dense use of the larger canonical palettes.
        values.extend(rng.choice(palette) for _ in range(remaining))
    else:
        dominant_repeats = remaining // 2
        values.extend([dominant] * dominant_repeats)
        values.extend(rng.choice(palette) for _ in range(remaining - dominant_repeats))
    rng.shuffle(values)
    return values


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size = ctx.draw_int_diff("grid_size", 2, 5)
    palette_count = _scheduled_palette_count(size, sample_index)
    palette = _palette(ctx, size, palette_count)
    rng = ctx.draw_rng("cells")

    # Reject only teaching aliases.  Every attempt preserves the exact declared
    # size/palette profile, and the finite cap makes an unexpected construction
    # failure loud rather than silently returning a degenerate lesson.
    for _ in range(128):
        values = _candidate_values(size, palette, difficulty, rng)
        grid = [values[r * size : (r + 1) * size] for r in range(size)]
        if self_check(grid, difficulty=difficulty):
            continue
        if not _curriculum_rivals_refuted(grid):
            continue
        return [row[:] for row in grid]
    raise RuntimeError("could not construct a non-degenerate upscale lesson after 128 attempts")


def observe_overrides(grid) -> dict[str, int]:
    """Recover the sole exact axis directly from returned pixels."""
    return {"grid_size": len(grid)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate this task's canonical-scale teaching grammar."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty 2D sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]

    size = len(grid)
    width = len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid rows must be rectangular"]
    if width != size:
        errors.append(f"expected a square input, got {size}x{width}")
    if size not in CANONICAL_PALETTE_BY_SIZE:
        errors.append(f"expected canonical side length 2..5, got {size}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    colors = {value for row in grid for value in row}
    allowed_colors = ALLOWED_PALETTE_COUNTS_BY_SIZE[size]
    if len(colors) not in allowed_colors:
        errors.append(
            f"size {size} expects one of {allowed_colors} visible colors, got {len(colors)}"
        )
    if not _has_horizontal_variation(grid):
        errors.append("grid must vary horizontally")
    if not _has_vertical_variation(grid):
        errors.append("grid must vary vertically")
    if size >= 3:
        varying_rows = sum(len(set(row)) >= 2 for row in grid)
        varying_cols = sum(
            len({grid[r][c] for r in range(size)}) >= 2 for c in range(size)
        )
        if varying_rows < 2:
            errors.append("sizes 3..5 require at least two varying rows")
        if varying_cols < 2:
            errors.append("sizes 3..5 require at least two varying columns")
    if _is_transpose_symmetric(grid):
        errors.append("grid must not be transpose-symmetric")
    if not errors and not _curriculum_rivals_refuted([list(row) for row in grid]):
        errors.append("grid does not distinguish per-cell upscale from declared rivals")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accept only the exact four public size/palette profiles."""
    errors = self_check(grid)
    if errors:
        return errors
    size = len(grid)
    palette_count = len({value for row in grid for value in row})
    expected = CANONICAL_PALETTE_BY_SIZE[size]
    if palette_count != expected:
        return [
            f"size {size} strict profile expects {expected} colors, got {palette_count}"
        ]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared upscale rival alive."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing input"]

    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"pair {index} is missing input")
            continue
        expected = _upscale2(pair["input"])
        if "output" in pair and pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with 2x per-cell upscale")

    for name, rival in SEMANTIC_RIVALS.items():
        try:
            survives = all(
                rival(demo["input"]) == demo.get("output", _upscale2(demo["input"]))
                for demo in demos
            )
        except Exception as exc:  # diagnostic contract: report, never hide
            reasons.append(f"rival {name} raised {exc!r}")
            continue
        if survives:
            rival_query = rival(query["input"])
            expected_query = query.get("output", _upscale2(query["input"]))
            if rival_query != expected_query:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(f"rival remains answer-equivalent on query: {name}")
    return reasons


def mutation_fixtures():
    """Named must-reject impostors used by the shared mutation-power check."""
    return [
        ("all_background", [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        ("singleton", [[0, 0, 0], [0, 2, 0], [0, 0, 0]]),
        ("solid_2x2", [[4, 4], [4, 4]]),
        ("short_line", [[0, 0, 0], [1, 2, 3], [0, 0, 0]]),
        ("transpose_symmetric", [[1, 2], [2, 3]]),
        (
            "wrong_5x5_palette",
            [
                [0, 1, 2, 3, 4],
                [1, 2, 3, 4, 5],
                [2, 3, 4, 5, 6],
                [3, 4, 5, 6, 0],
                [4, 5, 6, 0, 1],
            ],
        ),
    ]
