"""Generator for ARC task e633a9e5 / content hash ecd1058990ce.

The Racket oracle applies a fixed non-uniform scale map to a 3x3 input:
rows and columns use scale factors ``(2, 1, 2)``.  The outer rows/columns
are duplicated while the middle row/column remains single, producing 5x5.

The generator deliberately keeps every ordinary scene answer-identifying:
adjacent input rows and adjacent input columns have different signatures, so
the four output run boundaries expose the exact row/column scale factors.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ecd1058990ce"
VERSION = "3.0.1"
TASK_ID = "ecd1058990ce"
RULE_HASH = "6c697debe9bc"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Generate a fixed 3x3 multicolor input. Apply scale-map with row scales "
    "(2, 1, 2) and column scales (2, 1, 2): duplicate the top/bottom rows "
    "and left/right columns while leaving the middle row/column single. The "
    "result is 5x5. Every ordinary scene has distinct adjacent row and column "
    "signatures so the non-uniform scale is directly identifiable."
)

INVARIANTS = [
    "input is exactly 3x3 because the Racket scale vectors each have length 3",
    "the realized palette has 2..9 distinct ARC colors and is never monochrome",
    "at least two cells differ from the modal color, excluding singleton-marker shortcuts",
    "adjacent row signatures differ, exposing row run lengths (2,1,2)",
    "adjacent column signatures differ, exposing column run lengths (2,1,2)",
]

_TEXTURE_FAMILIES = (
    "noise",
    "checker",
    "row_distinct",
    "col_distinct",
    "diagonal",
    "frame_inner",
    "blob",
    "gradient",
)

# Only true caller controls are declared. Grid size is rule-locked, and the old
# cell_distinctness knob was not recoverable from the returned grid.
AXES = {
    "palette_size": {
        "type": "int",
        "default": "difficulty-aware draw: easy 3..5, medium 4..7, hard 6..9",
        "valid": "2..9",
    },
}

# The strict predicate below accepts exactly the canonical palette envelope
# (5 or 6 colors). Default band ranges put substantial mass there.
MIN_STRICT_FRAC = 0.20

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_BAND_PALETTE_BOUNDS = {
    "easy": (3, 5),
    "medium": (4, 7),
    "hard": (6, 9),
}
_TARGET_ROW_SCALES = (2, 1, 2)
_TARGET_COL_SCALES = (2, 1, 2)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic 3x3 teaching input."""
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = "medium" if difficulty is None else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    # Explicit palette_size overrides are lawful over the complete declared
    # 2..9 domain in every difficulty band. Defaults remain band-shaped.
    if overrides.get("palette_size") is not None:
        palette_lo, palette_hi = 2, 9
    else:
        palette_lo, palette_hi = _BAND_PALETTE_BOUNDS[band]
    n_colors = ctx.draw_int("palette_size", palette_lo, palette_hi)
    palette = ctx.draw_distinct_colors("palette", n=n_colors)
    rng = ctx.draw_rng("cells")
    # Texture is intentionally internal rather than a public exact override:
    # repairs and palette realization can alter its visible signature, so it
    # cannot be truthfully reconstructed by observe_overrides.
    texture = rng.choice(_TEXTURE_FAMILIES)

    grid = _paint_texture(texture, palette, rng)
    _repair_identifiability(grid, palette, texture, rng)
    _ensure_every_palette_color(grid, palette, rng)

    errors = self_check(
        grid,
        difficulty=band,
        meta={"palette_size": n_colors, "texture": texture},
    )
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's complete teaching grammar.

    Difficulty changes the default sampling distribution, not validity. An
    explicit two-color hard example is lawful as long as both scale axes remain
    observable.
    """
    del difficulty
    errors = _basic_grid_errors(grid)
    if errors:
        return errors

    vals = [value for row in grid for value in row]
    distinct = len(set(vals))
    if distinct < 2:
        errors.append("non-uniform scaling is invisible on a monochrome input")
    counts = {value: vals.count(value) for value in set(vals)}
    if counts and 9 - max(counts.values()) < 2:
        errors.append("at least two cells must differ from the modal color")

    if grid[0] == grid[1]:
        errors.append("top and middle row signatures must differ")
    if grid[1] == grid[2]:
        errors.append("middle and bottom row signatures must differ")

    columns = _columns(grid)
    if columns[0] == columns[1]:
        errors.append("left and middle column signatures must differ")
    if columns[1] == columns[2]:
        errors.append("middle and right column signatures must differ")

    requested_palette = None
    if isinstance(meta, dict):
        requested_palette = meta.get("palette_size")
        if requested_palette is None and isinstance(meta.get("overrides"), dict):
            requested_palette = meta["overrides"].get("palette_size")
    if requested_palette is not None and distinct != int(requested_palette):
        errors.append(
            f"palette_size requested {int(requested_palette)}, realized {distinct}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Return reasons when a scene falls outside the canonical 3x3 manifold."""
    errors = self_check(grid)
    if errors:
        return errors
    distinct = len({value for row in grid for value in row})
    if distinct not in {5, 6}:
        return [f"canonical inputs use 5 or 6 distinct colors, found {distinct}"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    """Recover the exact semantic override from the returned grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {"palette_size": len({value for row in grid for value in row})}


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["input must be a non-empty list-of-lists grid"]
    if not all(isinstance(row, list) for row in grid):
        return ["input must be a list-of-lists grid"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["input grid must be rectangular and non-empty"]
    errors: list[str] = []
    if (len(grid), width) != (3, 3):
        errors.append(f"scale-map input must be exactly 3x3, found {len(grid)}x{width}")
    values = [value for row in grid for value in row]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for value in values
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    return errors


def _columns(grid: list[list[int]]) -> list[tuple[int, ...]]:
    return [tuple(row[column] for row in grid) for column in range(3)]


def _paint_texture(texture: str, palette: tuple[int, ...], rng) -> list[list[int]]:
    grid = full_grid(3, 3, palette[0])
    if texture == "noise":
        for row in range(3):
            for column in range(3):
                grid[row][column] = rng.choice(palette)
    elif texture == "checker":
        for row in range(3):
            for column in range(3):
                grid[row][column] = palette[(row + column) % min(2, len(palette))]
    elif texture == "row_distinct":
        for row in range(3):
            base = palette[row % len(palette)]
            for column in range(3):
                grid[row][column] = (
                    base if rng.random() < 0.72 else rng.choice(palette)
                )
    elif texture == "col_distinct":
        for column in range(3):
            base = palette[column % len(palette)]
            for row in range(3):
                grid[row][column] = (
                    base if rng.random() < 0.72 else rng.choice(palette)
                )
    elif texture == "diagonal":
        background = palette[-1]
        for row in range(3):
            for column in range(3):
                grid[row][column] = (
                    palette[row % len(palette)] if row == column else background
                )
    elif texture == "frame_inner":
        border = palette[0]
        inner = palette[1]
        for row in range(3):
            for column in range(3):
                grid[row][column] = (
                    inner if (row, column) == (1, 1) else border
                )
    elif texture == "blob":
        secondary = palette[1]
        for row in range(3):
            for column in range(3):
                grid[row][column] = (
                    palette[0] if rng.random() < 0.56 else secondary
                )
        grid[rng.randrange(3)][rng.randrange(3)] = palette[-1]
    elif texture == "gradient":
        for row in range(3):
            for column in range(3):
                grid[row][column] = palette[(row + column) % len(palette)]
    else:  # protected by ctx.draw_choice, retained as a fail-loud guard.
        raise ValueError(f"unsupported texture {texture!r}")
    return grid


def _repair_identifiability(
    grid: list[list[int]],
    palette: tuple[int, ...],
    texture: str,
    rng,
) -> None:
    """Make adjacent row/column signatures distinct without hiding axes."""
    if len(palette) == 2:
        # A proper checker is the only 2-color orthogonal coloring. Let the
        # texture choose one of its two phases so texture remains observable
        # even when palette_size is fixed to the lower boundary.
        phase = _TEXTURE_FAMILIES.index(texture) % 2
        for row in range(3):
            for column in range(3):
                grid[row][column] = palette[(row + column + phase) % 2]
        return

    # Repair only when a whole adjacent row/column signature collides. A fresh
    # replacement color is selected to break the collision while preserving
    # the texture elsewhere.
    for row in (1, 2):
        if grid[row] == grid[row - 1]:
            column = rng.randrange(3)
            blocked = {grid[row - 1][column]}
            grid[row][column] = rng.choice(
                [color for color in palette if color not in blocked]
            )
    for column in (1, 2):
        columns = _columns(grid)
        if columns[column] == columns[column - 1]:
            row = rng.randrange(3)
            blocked = {grid[row][column - 1]}
            grid[row][column] = rng.choice(
                [color for color in palette if color not in blocked]
            )


def _neighbors(row: int, column: int) -> Iterable[tuple[int, int]]:
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = row + dr, column + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            yield nr, nc


def _ensure_every_palette_color(
    grid: list[list[int]], palette: tuple[int, ...], rng
) -> None:
    """Make declared palette_size equal the realized distinct-color count."""
    counts = {color: 0 for color in palette}
    for row in grid:
        for value in row:
            counts[value] += 1

    for missing in [color for color in palette if counts[color] == 0]:
        candidates: list[tuple[int, int]] = []
        for row in range(3):
            for column in range(3):
                old = grid[row][column]
                if counts[old] <= 1:
                    continue
                # `missing` is absent globally at this point, so this guard is
                # normally vacuous; keep it explicit for mutation safety.
                if any(grid[nr][nc] == missing for nr, nc in _neighbors(row, column)):
                    continue
                candidates.append((row, column))
        if not candidates:
            raise AssertionError("could not realize every requested palette color")
        row, column = rng.choice(candidates)
        old = grid[row][column]
        grid[row][column] = missing
        counts[old] -= 1
        counts[missing] += 1

    # Palette insertion cannot create equality with a neighbor because each
    # inserted color was globally absent. It can, however, accidentally repair
    # a row/column collision only in our favor; assert the final grammar.
    if grid[0] == grid[1] or grid[1] == grid[2]:
        raise AssertionError("palette realization collapsed adjacent row signatures")
    columns = _columns(grid)
    if columns[0] == columns[1] or columns[1] == columns[2]:
        raise AssertionError("palette realization collapsed adjacent column signatures")


def _scale_map_python(
    grid: list[list[int]],
    row_scales: tuple[int, int, int],
    col_scales: tuple[int, int, int],
) -> list[list[int]]:
    output: list[list[int]] = []
    for row, row_scale in zip(grid, row_scales):
        expanded_row: list[int] = []
        for value, col_scale in zip(row, col_scales):
            expanded_row.extend([value] * col_scale)
        output.extend([list(expanded_row) for _ in range(row_scale)])
    return output


def _positive_compositions_5() -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (a, b, 5 - a - b)
        for a, b in product(range(1, 4), repeat=2)
        if 5 - a - b >= 1
    )


_SCALE_TRIPLES = _positive_compositions_5()


def lesson_identifiable(demos, query) -> list[str]:
    """Prove the demos identify the query answer among 3-part 5-cell scales.

    The counter-hypothesis class is every positive row-scale and column-scale
    triple of length three whose entries sum to five (36 scale maps total).
    Multiple surviving maps are accepted only when they are answer-equivalent
    on the query, matching the worker contract.
    """
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    candidates = {
        (row_scales, col_scales)
        for row_scales in _SCALE_TRIPLES
        for col_scales in _SCALE_TRIPLES
    }
    for index, pair in enumerate(demos):
        input_grid = pair.get("input") if isinstance(pair, dict) else None
        output_grid = pair.get("output") if isinstance(pair, dict) else None
        input_errors = self_check(input_grid)
        if input_errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(input_errors)}")
            continue
        expected = _scale_map_python(
            input_grid, _TARGET_ROW_SCALES, _TARGET_COL_SCALES
        )
        if output_grid != expected:
            reasons.append(f"demo {index} output disagrees with the canonical scale-map")
            continue
        candidates = {
            candidate
            for candidate in candidates
            if _scale_map_python(input_grid, *candidate) == output_grid
        }

    query_input = query.get("input") if isinstance(query, dict) else None
    query_output = query.get("output") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
        return reasons

    intended = (_TARGET_ROW_SCALES, _TARGET_COL_SCALES)
    if intended not in candidates:
        reasons.append("demonstrations eliminated the intended (2,1,2)x(2,1,2) map")
    if not candidates:
        reasons.append("no positive 3-part scale map is consistent with every demonstration")
        return reasons

    answers = {
        tuple(tuple(row) for row in _scale_map_python(query_input, *candidate))
        for candidate in candidates
    }
    expected_query = _scale_map_python(
        query_input, _TARGET_ROW_SCALES, _TARGET_COL_SCALES
    )
    if query_output is not None and query_output != expected_query:
        reasons.append("query output disagrees with the canonical scale-map")
    if len(answers) > 1:
        reasons.append(
            f"{len(candidates)} scale maps remain and yield {len(answers)} query answers"
        )
    return reasons


def _valid_scene(grid: Any) -> bool:
    return self_check(grid) == []


SEMANTIC_WITNESSES = {
    "top_middle_row_boundary": lambda grid: (
        _valid_scene(grid) and grid[0] != grid[1]
    ),
    "middle_bottom_row_boundary": lambda grid: (
        _valid_scene(grid) and grid[1] != grid[2]
    ),
    "left_middle_column_boundary": lambda grid: (
        _valid_scene(grid) and _columns(grid)[0] != _columns(grid)[1]
    ),
    "middle_right_column_boundary": lambda grid: (
        _valid_scene(grid) and _columns(grid)[1] != _columns(grid)[2]
    ),
    "canonical_palette_5_or_6": lambda grid: (
        _valid_scene(grid)
        and len({value for row in grid for value in row}) in {5, 6}
    ),
    "repeated_color_rebuts_fixed_position_code": lambda grid: (
        _valid_scene(grid)
        and len({value for row in grid for value in row}) < 9
    ),
}
