"""Generator for ARC task 60c09cac — two-times nearest-neighbor upscale.

The canonical examples are small (3x3, 4x4, 5x5), sparse, zero-background
motifs with exactly two foreground colors.  Keep the teaching distribution on
that manifold: every generated foreground is one connected motif, uses both
foreground colors, and is deliberately non-degenerate under plausible wrong
"tile the whole grid" / transpose-before-scale interpretations.

Authoritative rule: ``(rule! (lambda (g) (upscale g 2)))``.
"""
from __future__ import annotations

from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d6d64e90301"
TASK_ID = "0d6d64e90301"
RULE_HASH = "511f58f5d471"
VERSION = "3.2.0"
EXAMPLES_NEEDED = 2
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = (
    "square_anchor",
    "wide_rectangle",
    "tall_rectangle",
)

# Positionally aligned with SCHEDULE_PROFILES.  Each three-example window has
# one square canonical anchor and two rectangular counterexamples.  Thus every
# two-demo rotation retains at least one example that refutes the strongest
# canonical shortcut: "only upscale square grids".
PROFILE_DIMENSIONS = {
    None: ((4, 4), (3, 4), (4, 3)),
    "easy": ((3, 3), (3, 4), (4, 3)),
    "medium": ((4, 4), (4, 5), (5, 4)),
    "hard": ((5, 5), (4, 5), (5, 4)),
}

SUMMARY = (
    "Canonical-scale 3x3..5x5 zero-background grid containing one sparse, "
    "4-connected motif in exactly two nonzero colors. Rule: replace EACH input "
    "cell by a solid 2x2 block of the same color, so an h x w input becomes a "
    "2h x 2w output. A three-step schedule supplies one square anchor and two "
    "rectangular witnesses, while rejecting scenes where whole-grid tiling or "
    "transpose-before-upscale would accidentally match the true output."
)

INVARIANTS = [
    "input dimensions are 3..5 in each axis, matching the canonical scale",
    "every three ordinary draws contain one square anchor and two rectangles",
    "background is color 0 and remains the strict majority",
    "exactly two nonzero colors are visible",
    "all nonzero cells form one 4-connected motif spanning at least 2 rows and 2 columns",
    "every ordinary draw refutes whole-row/whole-grid tiling and transpose-before-upscale rivals",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile/difficulty schedule within 3..5",
        "valid": "3..5",
        "doc": "Full input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile/difficulty schedule within 3..5",
        "valid": "3..5",
        "doc": "Full input-grid width.",
    },
}


def _upscale2(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python statement of the selected rule, used only by audit hooks."""
    out: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(2)]
        out.append(expanded[:])
        out.append(expanded[:])
    return out


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the deterministic three-step teaching schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _scheduled_shape(sample_index: int, difficulty) -> tuple[int, int]:
    band = difficulty if difficulty in PROFILE_DIMENSIONS else None
    return PROFILE_DIMENSIONS[band][sample_index % LESSON_SCHEDULE_PERIOD]


def _draw_scheduled_axis(ctx, name: str, default: int) -> int:
    """Record scheduled defaults while keeping the complete exact override domain."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 3, 5)
    return ctx.draw_int_strict(name, default, default)


def _tile_each_row(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rival: duplicate each whole row horizontally, then duplicate rows."""
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
    """Wrong rival: transpose the input first, then perform the 2x upscale."""
    transposed = [list(row) for row in zip(*grid)]
    return _upscale2(transposed)


def _square_only_upscale(grid: list[list[int]]) -> list[list[int]]:
    """Wrong canonical shortcut: apply the learned rule only to square inputs.

    Every labeled canonical input is square, so those examples cannot refute
    this domain-gated solver.  On rectangular inputs it incorrectly returns an
    unchanged copy instead of performing the 2x per-cell upscale.
    """
    if grid and grid[0] and len(grid) == len(grid[0]):
        return _upscale2(grid)
    return [list(row) for row in grid]


INSTANCE_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "tile_each_whole_row": _tile_each_row,
    "tile_whole_grid_2x2": _tile_whole_grid,
    "transpose_then_upscale": _transpose_then_upscale,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    **INSTANCE_RIVALS,
    "square_only_upscale": _square_only_upscale,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"square_only_upscale": _square_only_upscale}


def _refutes(rival_name: str, grid: list[list[int]]) -> bool:
    return SEMANTIC_RIVALS[rival_name](grid) != _upscale2(grid)


def _is_rectangular(grid: list[list[int]]) -> bool:
    return bool(grid and grid[0] and len(grid) != len(grid[0]))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "cellwise_horizontal_repeat_not_row_tile": lambda g: _refutes("tile_each_whole_row", g),
    "cellwise_vertical_repeat_not_grid_tile": lambda g: _refutes("tile_whole_grid_2x2", g),
    "orientation_preserved_not_transposed": lambda g: _refutes("transpose_then_upscale", g),
    "rectangular_input_refutes_square_only": lambda g: _is_rectangular(g)
    and _refutes("square_only_upscale", g),
}
WITNESS_RIVALS = {
    "cellwise_horizontal_repeat_not_row_tile": ["tile_each_whole_row"],
    "cellwise_vertical_repeat_not_grid_tile": ["tile_whole_grid_2x2"],
    "orientation_preserved_not_transposed": ["transpose_then_upscale"],
    "rectangular_input_refutes_square_only": ["square_only_upscale"],
}
MIN_STRICT_FRAC = 0.90


def _foreground_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }


def _is_4_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pos = (r + dr, c + dc)
            if pos in cells and pos not in seen:
                seen.add(pos)
                stack.append(pos)
    return seen == cells


def _spans_2d(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    return len(rows) >= 2 and len(cols) >= 2


def _curriculum_rivals_refuted(grid: list[list[int]]) -> bool:
    expected = _upscale2(grid)
    return all(rival(grid) != expected for rival in INSTANCE_RIVALS.values())


def _grow_connected_cells(h: int, w: int, count: int, rng) -> set[tuple[int, int]]:
    """Grow a random 4-connected polyomino of exactly ``count`` cells."""
    start = (rng.randrange(h), rng.randrange(w))
    cells = {start}
    while len(cells) < count:
        frontier = sorted({
            (r + dr, c + dc)
            for r, c in cells
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if 0 <= r + dr < h and 0 <= c + dc < w
            and (r + dr, c + dc) not in cells
        })
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return cells


def _paint_two_colors(
    h: int,
    w: int,
    cells: set[tuple[int, int]],
    colors: tuple[int, int],
    rng,
) -> list[list[int]]:
    g = full_grid(h, w, 0)
    ordered = sorted(cells)
    rng.shuffle(ordered)
    # Seed both colors explicitly; every additional cell may use either.
    g[ordered[0][0]][ordered[0][1]] = colors[0]
    g[ordered[1][0]][ordered[1][1]] = colors[1]
    for r, c in ordered[2:]:
        g[r][c] = rng.choice(colors)
    return g


def _validate_request(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool or a coercible value)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool or a coercible value)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or a coercible value)")
        lo, hi = 3, 5
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Full declared domains remain available to explicit overrides.  Ordinary
    # draws use a deterministic lesson schedule so every two-demo bundle (and
    # every held-out rotation of its three pairs) contains a rectangular
    # counterexample to the square-only canonical shortcut.
    scheduled_h, scheduled_w = _scheduled_shape(sample_index, difficulty)
    h = _draw_scheduled_axis(ctx, "grid_h", scheduled_h)
    w = _draw_scheduled_axis(ctx, "grid_w", scheduled_w)
    colors = ctx.draw_distinct_colors("palette", n=2, exclude={0})
    rng = ctx.draw_rng("motif")

    area = h * w
    base_count = max(3, round(area * 0.29))
    max_count = min(area - 1, (area - 1) // 2)
    choices = [n for n in range(max(3, base_count - 1), min(max_count, base_count + 1) + 1)]
    if not choices:
        choices = [min(max_count, 3)]

    # The loop is deterministic (one keyed RNG) and rejects only curriculum
    # aliases, never a canonical input.  With 3..5 grids it succeeds rapidly;
    # the explicit bound keeps failures loud instead of hanging.
    for _ in range(64):
        count = rng.choice(choices)
        cells = _grow_connected_cells(h, w, count, rng)
        if len(cells) != count or not _spans_2d(cells):
            continue
        grid = _paint_two_colors(h, w, cells, colors, rng)
        if self_check(grid, difficulty=difficulty):
            continue
        if not _curriculum_rivals_refuted(grid):
            continue
        return grid
    raise RuntimeError("could not construct a non-degenerate upscale lesson after 64 attempts")


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from the returned grid."""
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-anchored teaching grammar.

    The selected rule can execute many arbitrary grids; this checker is about
    the *lesson grammar*: canonical scale, zero background, two visible
    foreground colors, and a sparse connected motif rather than a shortcut-
    hiding monochrome/tiny/full-grid scene.
    """
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    if not (3 <= h <= 5 and 3 <= w <= 5):
        errors.append(f"expected canonical-scale dimensions 3..5 x 3..5, got {h}x{w}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    palette = {value for row in grid for value in row}
    fg_colors = palette - {0}
    if 0 not in palette:
        errors.append("background color 0 must be present")
    if len(fg_colors) != 2:
        errors.append(f"expected exactly two nonzero colors, got {sorted(fg_colors)}")

    fg = _foreground_cells(grid)
    bg_count = h * w - len(fg)
    if len(fg) < 3:
        errors.append(f"foreground has only {len(fg)} cells; need at least 3")
    if bg_count <= len(fg):
        errors.append("background 0 must be the strict majority")
    if fg and not _is_4_connected(fg):
        errors.append("nonzero foreground must form one 4-connected motif")
    if fg and not _spans_2d(fg):
        errors.append("foreground motif must span at least two rows and two columns")
    if len(fg_colors) == 2:
        counts = {
            color: sum(value == color for row in grid for value in row)
            for color in fg_colors
        }
        if any(count == 0 for count in counts.values()):
            errors.append("both nonzero colors must be visible")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Pin the generated lessons to the measured 60c09cac canonical manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    fg_count = len(_foreground_cells(grid))
    density = fg_count / (h * w)
    if not 0.20 <= density <= 0.45:
        errors.append(f"foreground density {density:.3f} outside canonical-like 0.20..0.45")
    return errors


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if named plausible upscale shortcuts survive its demos."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = _upscale2(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with 2x per-cell upscale")

    for name, rival in SEMANTIC_RIVALS.items():
        try:
            survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        except Exception as exc:
            reasons.append(f"rival {name} raised {exc!r}")
            continue
        if survives:
            rival_query = rival(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(f"rival remains answer-equivalent on query: {name}")
    return reasons


def mutation_fixtures():
    """Task-local must-reject impostors for self-check mutation evidence."""
    return [
        (
            "all_background",
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        ),
        (
            "single_foreground_color",
            [[0, 0, 0], [0, 2, 2], [0, 2, 0]],
        ),
        (
            "disconnected_two_color_islands",
            [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 3]],
        ),
        (
            "foreground_not_sparse",
            [[2, 2, 2], [2, 3, 3], [3, 3, 0]],
        ),
        (
            "line_only_motif",
            [[0, 0, 0, 0], [2, 2, 3, 3], [0, 0, 0, 0], [0, 0, 0, 0]],
        ),
    ]
