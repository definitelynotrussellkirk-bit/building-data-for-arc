"""Input generator for ARC task 9c50790b939c.

A mixed vertical SOURCE rail contains a contiguous color-9 block at one end.
The intended rule clears that block to color 8, finds the unique all-8 TARGET
rail exactly two cells longer than the source, and paints ``input_nines + 1``
color-9 cells at the matching end of the target.

The canonical demonstrations also admit a tempting rival: paint exactly half
of the target rail.  They cannot distinguish it because every public source
block occupies half of its source rail.  This generator deliberately emits
non-half source blocks and declares that rival to the semantic gate.
"""
from __future__ import annotations

from typing import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9c50790b939c"
TASK_ID = "9c50790b939c"
VERSION = "3.1.0"
RULE_HASH = "846ddca6645d"
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a color-7 field, one vertical 8/9 source rail has an end-aligned "
    "color-9 block and one unique all-8 target rail is exactly two cells "
    "longer. Several additional all-8 vertical rails reproduce the canonical "
    "rail field. Move the block to the target's matching end and grow it by "
    "one cell. Non-half source blocks refute the canonical-only shortcut of "
    "painting half the target."
)

INVARIANTS = [
    "all non-background cells belong to vertical rails of length at least two",
    "exactly one mixed source rail contains a contiguous end-aligned 9 block",
    "exactly one all-8 rail has length source_length + 2",
    "the output clears the source and paints input_nines + 1 target cells",
    "generated support includes cases where input_nines + 1 is not half the target",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "16 often; otherwise difficulty band",
        "valid": "12..20",
        "doc": "Canvas height. Exact overrides work in every difficulty band.",
    },
    "grid_w": {
        "type": "int",
        "default": "16 often; otherwise difficulty band",
        "valid": "12..20",
        "doc": "Canvas width. Exact overrides work in every difficulty band.",
    },
    "source_length": {
        "type": "int",
        "default": "difficulty-dependent choice",
        "valid": "2|4|6|8",
        "doc": "Total length of the mixed 8/9 source rail.",
    },
    "block_position": {
        "type": "str",
        "default": "rng",
        "valid": "top|bottom",
        "doc": "End of the source and target rails occupied by color 9.",
    },
    "distractor_rails": {
        "type": "int",
        "default": "difficulty band",
        "valid": "8..13",
        "doc": "Number of additional pure color-8 rails besides the target.",
    },
}

# Every Cartesian boundary combination is feasible: h >= 12 fits the longest
# ten-cell rail. Multiple separated short rails may share a column, matching
# canonical scenes with more rails than distinct occupied columns.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[object] = []

_SOURCE_LENGTHS = (2, 4, 6, 8)
_BLOCK_POSITIONS = ("top", "bottom")
_DISTRACTOR_LENGTHS = (2, 4, 6, 8, 10)


def _is_int(value: object) -> bool:
    return type(value) is int


def _validate_controls(difficulty: object, overrides: dict[str, object]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, 'easy', 'medium', 'hard'")
    for key in ("grid_h", "grid_w", "source_length", "distractor_rails"):
        value = overrides.get(key)
        if value is not None and not _is_int(value):
            raise TypeError(f"override {key} must be an integer")
    position = overrides.get("block_position")
    if position is not None and type(position) is not str:
        raise TypeError("override block_position must be a string")


def _dimension_bounds(
    difficulty: str | None,
    *,
    compact: bool,
    overridden: bool,
) -> tuple[int, int]:
    if overridden:
        return (12, 20)
    if compact:
        return (16, 16)
    return {
        "easy": (12, 16),
        "medium": (14, 18),
        "hard": (16, 20),
    }.get(difficulty, (12, 20))


def _source_options(difficulty: str | None, overridden: bool) -> tuple[int, ...]:
    if overridden:
        return _SOURCE_LENGTHS
    return {
        "easy": (2, 4, 6),
        "medium": _SOURCE_LENGTHS,
        "hard": (4, 6, 8),
    }.get(difficulty, _SOURCE_LENGTHS)


def _distractor_bounds(difficulty: str | None, overridden: bool) -> tuple[int, int]:
    if overridden:
        return (8, 13)
    return {
        "easy": (8, 11),
        "medium": (9, 12),
        "hard": (10, 13),
    }.get(difficulty, (8, 13))


def _choose_block_length(ctx, source_length: int) -> int:
    """Choose a proper end block, usually breaking the half-target shortcut."""
    rng = ctx.draw_rng("block_length")
    canonical_half = source_length // 2
    counterexamples = [
        length
        for length in range(1, source_length)
        if length != canonical_half
    ]
    # Source length two has only the canonical one-cell block.  At longer
    # lengths, four fifths of draws are explicit shortcut counterexamples,
    # while the remaining fifth preserves public-demo-like half blocks.
    if counterexamples and rng.random() < 0.80:
        return rng.choice(counterexamples)
    return canonical_half


def _can_place_short_rail(grid, start: int, column: int, *, isolated: bool) -> bool:
    """Whether rows ``start:start+2`` form a new maximal two-cell rail."""
    height, width = len(grid), len(grid[0])
    stop = start + 2
    if stop > height:
        return False
    if grid[start][column] != 7 or grid[start + 1][column] != 7:
        return False
    if start > 0 and grid[start - 1][column] in (8, 9):
        return False
    if stop < height and grid[stop][column] in (8, 9):
        return False
    if isolated:
        for row in (start, start + 1):
            for neighbor_column in (column - 1, column + 1):
                if (
                    0 <= neighbor_column < width
                    and grid[row][neighbor_column] in (8, 9)
                ):
                    return False
    return True


def _add_short_rails(base_grid, count: int, rng, *, isolated: bool):
    """Greedily add ``count`` separated two-cell runs, or return ``None``."""
    grid = [row[:] for row in base_grid]
    height, width = len(grid), len(grid[0])
    candidates = [
        (start, column)
        for column in range(width)
        for start in range(height - 1)
    ]
    rng.shuffle(candidates)
    placed = 0
    for start, column in candidates:
        if not _can_place_short_rail(grid, start, column, isolated=isolated):
            continue
        grid[start][column] = 8
        grid[start + 1][column] = 8
        placed += 1
        if placed == count:
            return grid
    return None


def _pack_rails(height: int, width: int, segments, rng):
    """Pack the five length-ladder rails plus extra two-cell rails in O(hw).

    The 2/4/6/8/10 ladder always occupies five nonadjacent columns, so those
    canonical-scale objects cannot merge horizontally. Remaining segments are
    all length two and are greedily inserted with a one-cell moat when possible;
    a vertical-gap-only fallback guarantees every valid override combination.
    """
    if len(segments) < 5:
        raise ValueError("rail scaffold requires the five canonical ladder rungs")
    by_length = {length: name for name, length in segments if length != 2}
    two_names = [name for name, length in segments if length == 2]
    # Exactly one named segment represents each ladder length.  Additional
    # two-cell segments are indistinguishable texture and are counted below.
    source_or_target_two = next(
        (name for name, length in segments if length == 2 and name in ("source", "target")),
        None,
    )
    ladder_names = {}
    for length in _DISTRACTOR_LENGTHS:
        if length == 2:
            if source_or_target_two is not None:
                ladder_names[length] = source_or_target_two
            else:
                ladder_names[length] = next(
                    name for name, item_length in segments
                    if item_length == 2 and name.startswith("ladder_")
                )
        else:
            ladder_names[length] = by_length[length]

    parity = rng.randrange(2)
    nonadjacent_columns = list(range(parity, width, 2))
    if len(nonadjacent_columns) < 5:
        parity = 1 - parity
        nonadjacent_columns = list(range(parity, width, 2))
    columns = rng.sample(nonadjacent_columns, 5)
    rng.shuffle(columns)

    grid = full_grid(height, width, 7)
    placements = {}
    for length, column in zip(_DISTRACTOR_LENGTHS, columns):
        name = ladder_names[length]
        start = rng.randint(0, height - length)
        placements[name] = (start, column, length)
        for row in range(start, start + length):
            grid[row][column] = 8

    # Remove the one two-cell ladder segment already placed. Every remaining
    # length-two descriptor is an extra canonical texture rail.
    remaining_two = len(two_names) - 1
    packed = _add_short_rails(grid, remaining_two, rng, isolated=True)
    if packed is None:
        packed = _add_short_rails(grid, remaining_two, rng, isolated=False)
    if packed is None:
        raise ValueError(
            f"could not pack {len(segments)} rails on {height}x{width} canvas"
        )
    return packed, placements


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input grid; labels remain the canonical Racket rule's job."""
    _validate_controls(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_rng = ctx.draw_rng("canonical_profile_prior")
    compact = profile_rng.random() < 0.60
    h_lo, h_hi = _dimension_bounds(
        difficulty,
        compact=compact,
        overridden=overrides.get("grid_h") is not None,
    )
    w_lo, w_hi = _dimension_bounds(
        difficulty,
        compact=compact,
        overridden=overrides.get("grid_w") is not None,
    )
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    source_length = ctx.draw_choice(
        "source_length",
        _source_options(difficulty, overrides.get("source_length") is not None),
    )
    block_position = ctx.draw_choice("block_position", _BLOCK_POSITIONS)
    d_lo, d_hi = _distractor_bounds(
        difficulty, overrides.get("distractor_rails") is not None
    )
    distractor_count = ctx.draw_int("distractor_rails", d_lo, d_hi)
    block_length = _choose_block_length(ctx, source_length)

    target_length = source_length + 2
    # Every canonical input has the complete 2/4/6/8/10 length ladder: the
    # source and target supply two rungs, three mandatory distractors supply
    # the rest, and all additional rails are two-cell texture.
    missing_ladder = [
        length
        for length in _DISTRACTOR_LENGTHS
        if length not in (source_length, target_length)
    ]
    segments = [("source", source_length), ("target", target_length)]
    segments.extend(
        (f"ladder_{length}", length) for length in missing_ladder
    )
    extra_count = distractor_count - len(missing_ladder)
    segments.extend((f"short_{index}", 2) for index in range(extra_count))

    layout_rng = ctx.draw_rng("rail_layout")
    grid, placements = _pack_rails(h, w, segments, layout_rng)
    source_start, source_col, _ = placements["source"]
    if block_position == "top":
        block_rows = range(source_start, source_start + block_length)
    else:
        block_rows = range(
            source_start + source_length - block_length,
            source_start + source_length,
        )
    for row in block_rows:
        grid[row][source_col] = 9

    # This is an internal assertion, not a second construction path.  It turns
    # any future layout regression into a deterministic generation failure.
    findings = self_check(grid, difficulty=difficulty, meta=ctx.recorded_draws())
    if findings:
        raise AssertionError("constructed invalid 9c50790b939c grid: " + "; ".join(findings))
    return grid


def _vertical_runs(grid: Sequence[Sequence[int]]):
    """Return every maximal vertical run of colors 8/9 as (column, rows, values)."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    runs = []
    for column in range(w):
        row = 0
        while row < h:
            if grid[row][column] not in (8, 9):
                row += 1
                continue
            start = row
            values = []
            while row < h and grid[row][column] in (8, 9):
                values.append(grid[row][column])
                row += 1
            runs.append((column, list(range(start, row)), values))
    return runs


def _scene(grid: Sequence[Sequence[int]]):
    runs = _vertical_runs(grid)
    sources = [run for run in runs if 9 in run[2]]
    if len(sources) != 1:
        raise ValueError(f"expected one source rail, found {len(sources)}")
    source = sources[0]
    source_length = len(source[1])
    targets = [
        run
        for run in runs
        if len(run[1]) == source_length + 2 and all(value == 8 for value in run[2])
    ]
    if len(targets) != 1:
        raise ValueError(f"expected one target rail, found {len(targets)}")
    nines = [
        (row, source[0])
        for row, value in zip(source[1], source[2])
        if value == 9
    ]
    position = "top" if source[2][0] == 9 else "bottom"
    return {
        "runs": runs,
        "source": source,
        "target": targets[0],
        "nines": nines,
        "block_position": position,
    }


def _apply_with_block_length(grid: Sequence[Sequence[int]], block_length: int):
    scene = _scene(grid)
    output = [list(row) for row in grid]
    for row, column in scene["nines"]:
        output[row][column] = 8
    target_column, target_rows, _target_values = scene["target"]
    if scene["block_position"] == "top":
        paint_rows = target_rows[:block_length]
    else:
        paint_rows = target_rows[-block_length:]
    for row in paint_rows:
        output[row][target_column] = 9
    return output


def rule_mirror(grid: Sequence[Sequence[int]]):
    """Pure Python mirror used only for tests and rival analysis, never labeling."""
    scene = _scene(grid)
    return _apply_with_block_length(grid, len(scene["nines"]) + 1)


def _paint_half_target(grid: Sequence[Sequence[int]]):
    """Plausible wrong rule fitting all four canonical demonstrations."""
    scene = _scene(grid)
    return _apply_with_block_length(grid, len(scene["target"][1]) // 2)


def _half_target_shortcut_rebutted(grid: Sequence[Sequence[int]]) -> bool:
    try:
        scene = _scene(grid)
    except (IndexError, TypeError, ValueError):
        return False
    intended = len(scene["nines"]) + 1
    shortcut = len(scene["target"][1]) // 2
    return intended != shortcut


SEMANTIC_RIVALS = {"paint_half_target": _paint_half_target}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "half_target_shortcut_rebutted": _half_target_shortcut_rebutted,
}
WITNESS_RIVALS = {
    "half_target_shortcut_rebutted": ["paint_half_target"],
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's rail-field input grammar without running the label rule."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list/tuple of rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be lists or tuples"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    errors: list[str] = []
    if not (12 <= height <= 20 and 12 <= width <= 20):
        errors.append("grid dimensions must each lie in 12..20")
    if any(
        type(value) is not int or value not in (7, 8, 9)
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer colors in {7,8,9}")
        return errors
    if not any(value == 7 for row in grid for value in row):
        errors.append("color 7 background must remain visible")

    runs = _vertical_runs(grid)
    if not (10 <= len(runs) <= 15):
        errors.append(f"expected 10..15 vertical rails, found {len(runs)}")
    singleton_runs = [run for run in runs if len(run[1]) < 2]
    if singleton_runs:
        errors.append(f"all 8/9 rails must have length at least two; found {len(singleton_runs)} singleton(s)")

    sources = [run for run in runs if 9 in run[2]]
    if len(sources) != 1:
        errors.append(f"expected exactly one source rail with color 9, found {len(sources)}")
        return errors
    source = sources[0]
    source_values = source[2]
    nine_indexes = [index for index, value in enumerate(source_values) if value == 9]
    if not nine_indexes:
        errors.append("source rail has no color-9 block")
    elif nine_indexes != list(range(min(nine_indexes), max(nine_indexes) + 1)):
        errors.append("source color-9 block must be contiguous")
    elif min(nine_indexes) != 0 and max(nine_indexes) != len(source_values) - 1:
        errors.append("source color-9 block must touch the top or bottom end")
    if len(nine_indexes) >= len(source_values):
        errors.append("source rail must retain at least one color-8 cell")
    if len(source_values) not in _SOURCE_LENGTHS:
        errors.append(f"source rail length must be one of {_SOURCE_LENGTHS}")

    target_length = len(source[1]) + 2
    targets = [
        run
        for run in runs
        if len(run[1]) == target_length and all(value == 8 for value in run[2])
    ]
    if len(targets) != 1:
        errors.append(
            f"expected exactly one all-8 target rail of length {target_length}, found {len(targets)}"
        )
    pure_runs = [run for run in runs if all(value == 8 for value in run[2])]
    distractor_count = len(pure_runs) - len(targets)
    if not (8 <= distractor_count <= 13):
        errors.append(
            f"expected 8..13 pure all-8 distractor rails, found {distractor_count}"
        )
    lengths = {len(run[1]) for run in runs}
    if not set(_DISTRACTOR_LENGTHS) <= lengths:
        errors.append("rail lengths must include the canonical 2/4/6/8/10 ladder")
    return errors


def strict_canonical_like(grid):
    """The declared teaching manifold; all generated and canonical inputs lie here."""
    return self_check(grid)


def observe_overrides(grid):
    scene = _scene(grid)
    pure_runs = [
        run for run in scene["runs"] if all(value == 8 for value in run[2])
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "source_length": len(scene["source"][1]),
        "block_position": scene["block_position"],
        "distractor_rails": len(pure_runs) - 1,
    }
