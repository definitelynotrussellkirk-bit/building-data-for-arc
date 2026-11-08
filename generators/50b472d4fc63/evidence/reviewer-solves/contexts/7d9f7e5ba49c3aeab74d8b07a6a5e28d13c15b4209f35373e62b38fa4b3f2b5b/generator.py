"""Task-local sampler for 50b472d4fc63.

The selected Racket authority finds maximal *same-color* vertical runs and
recolors only the two endpoints of runs whose length is exactly three.  This
sampler preserves canonical-sized examples while deliberately adding three
teaching negatives:

* a three-cell nonzero occupancy block whose colors change (do nothing),
* a same-color run of length two (do nothing), and
* a same-color run of length four (do nothing).

Defaults alternate the length-two and length-four negatives.  Therefore every
four-pair sequential lesson contains two of each, so any one pair can be moved
to the query position while the other three demonstrations still teach both
exact-length boundaries.

The mixed-color block is the essential repair: the public examples cannot
separate the real rule from the shortcut "mark every three occupied cells in a
column regardless of their colors."  Outputs remain owned by the unchanged
Racket authority; Python oracles below exist only for semantic audits.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "50b472d4fc63"
TASK_ID = GENERATOR_ID
RULE_HASH = "9af5ed1251ca"
VERSION = "3.2.0"

SUMMARY = (
    "A 0-background grid contains isolated vertical occupancy blocks. Exact "
    "same-color runs of length 3 are targets; the authority recolors only "
    "their top and bottom cells to 8. Every default example also contains a "
    "mixed-color occupied block of length 3. Defaults alternate same-color "
    "length-2 and length-4 distractors, so every three consecutive examples "
    "show both boundaries and every four-pair lesson remains identifiable under "
    "all query rotations. Three quarters "
    "of default draws use one of the canonical (height,width,palette) profiles."
)

INVARIANTS = [
    "input cells are ARC colors 0..9 and input color 8 is reserved for output",
    "every occupied column has one contiguous block of length 2, 3, or 4",
    "at least one block is a same-color vertical run of length exactly 3",
    "every default input has one mixed-length-3 negative and exactly one alternating length-2/length-4 negative",
    "every three-example window has both length boundaries; every four-pair lesson keeps both under any query rotation",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 8|9 on 3/4 draws; otherwise difficulty-aware 6..16",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 6|7|9 on 3/4 draws; otherwise difficulty-aware 6..16",
        "valid": "6..16",
    },
    "n_targets": {
        "type": "int",
        "default": "1 on canonical-profile draws; 2 on the broad branch",
        "valid": "1..2",
    },
    "n_mixed": {
        "type": "int",
        "default": "1 on canonical-profile draws; 2 on the broad branch",
        "valid": "1..2",
    },
    "n_short": {
        "type": "int",
        "default": "alternating lesson schedule: 0,1,0,1,...",
        "valid": "0..1",
    },
    "n_long": {
        "type": "int",
        "default": "alternating lesson schedule: 1,0,1,0,...",
        "valid": "0..1",
    },
    "palette_size": {
        "type": "int",
        "default": "2 on canonical-profile draws; scheduled 2..4 otherwise",
        "valid": "2..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CANONICAL_SHAPES = ((9, 6), (8, 7), (9, 9))
_AXIS_BOUNDS = {
    "grid_h": (6, 16),
    "grid_w": (6, 16),
    "n_targets": (1, 2),
    "n_mixed": (1, 2),
    "n_short": (0, 1),
    "n_long": (0, 1),
    "palette_size": (2, 4),
}


def _validate_overrides(overrides: dict[str, object]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        lo, hi = _AXIS_BOUNDS[name]
        if type(value) is not int:
            raise ValueError(f"{name} override must be an integer, got {value!r}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_scheduled_int(ctx, label: str, scheduled: int) -> int:
    """Consume an exact axis override or record a deterministic default."""
    lo, hi = _AXIS_BOUNDS[label]
    if label in ctx.overrides:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, (scheduled,))


def _broad_bounds(label: str, difficulty) -> tuple[int, int]:
    if label == "grid_h":
        return {
            "easy": (6, 10),
            "medium": (8, 13),
            "hard": (10, 16),
        }.get(difficulty, (6, 16))
    return {
        "easy": (6, 10),
        "medium": (7, 13),
        "hard": (9, 16),
    }.get(difficulty, (6, 16))


def _draw_dimension(ctx, label: str, *, canonical: bool, scheduled: int, difficulty) -> int:
    lo, hi = _AXIS_BOUNDS[label]
    if label in ctx.overrides:
        return ctx.draw_int(label, lo, hi)
    if canonical:
        return ctx.draw_choice(label, (scheduled,))
    draw_lo, draw_hi = _broad_bounds(label, difficulty)
    return ctx.draw_int(label, draw_lo, draw_hi)


def _default_count(label: str, sample_index: int, difficulty) -> int:
    del difficulty
    if label in {"n_targets", "n_mixed"}:
        # Canonical-profile branches stay visually close to the two-object
        # public lessons.  The 1/4 broad branch exercises the upper count bound
        # without moving the median beyond the corpus drift gate.
        return 2 if sample_index % 4 == 3 else 1
    return 1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input; the shared runner applies the Racket rule."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Three scheduled branches anchor the exact canonical profiles.  The fourth
    # broad branch explores dimensions and palettes without starving any band.
    canonical = sample_index % 4 != 3
    canonical_h, canonical_w = _CANONICAL_SHAPES[sample_index % len(_CANONICAL_SHAPES)]
    grid_h = _draw_dimension(
        ctx, "grid_h", canonical=canonical, scheduled=canonical_h, difficulty=difficulty
    )
    grid_w = _draw_dimension(
        ctx, "grid_w", canonical=canonical, scheduled=canonical_w, difficulty=difficulty
    )

    n_targets = _draw_scheduled_int(
        ctx, "n_targets", _default_count("n_targets", sample_index, difficulty)
    )
    n_mixed = _draw_scheduled_int(
        ctx, "n_mixed", _default_count("n_mixed", sample_index, difficulty)
    )
    # Alternate the two exact-length boundary negatives.  Every consecutive
    # three examples includes both, and every four-pair lesson has two of each;
    # removing any one pair as the query therefore leaves both in the demos.
    n_short = _draw_scheduled_int(ctx, "n_short", 1 if sample_index % 2 == 1 else 0)
    n_long = _draw_scheduled_int(ctx, "n_long", 1 if sample_index % 2 == 0 else 0)

    if "palette_size" in overrides:
        palette_size = ctx.draw_int("palette_size", 2, 4)
    elif canonical:
        palette_size = ctx.draw_choice("palette_size", (2,))
    else:
        # Guarantee all advertised palette sizes appear in each 80-example
        # sequential census rather than relying on probabilistic coverage.
        palette_size = ctx.draw_choice("palette_size", (2 + ((sample_index // 4) % 3),))

    feature_count = n_targets + n_mixed + n_short + n_long
    if feature_count > grid_w:  # impossible under the declared ranges, kept defensive
        raise RuntimeError(
            f"internal feature count {feature_count} exceeds grid width {grid_w}"
        )

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(list(_COLORS), palette_size)

    features: list[tuple[str, tuple[int, ...]]] = []
    for index in range(n_targets):
        color = palette[index % palette_size]
        features.append(("target", (color, color, color)))

    for index in range(n_mixed):
        if index == 0:
            if palette_size == 2:
                values = (palette[0], palette[1], palette[0])
            elif palette_size == 3:
                values = (palette[0], palette[1], palette[2])
            else:
                # The first target uses palette[0], so this one block exposes
                # every remaining color even when all optional decoys are off.
                values = (palette[1], palette[2], palette[3])
        else:
            values = tuple(
                palette[(index + offset + 1) % palette_size] for offset in range(3)
            )
            if len(set(values)) == 1:  # defensive; palette_size is at least two
                values = (palette[0], palette[1], palette[0])
        features.append(("mixed", values))

    for index in range(n_short):
        color = palette[(n_targets + index) % palette_size]
        features.append(("short", (color, color)))
    for index in range(n_long):
        color = palette[(n_targets + n_short + index) % palette_size]
        features.append(("long", (color, color, color, color)))

    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(features)
    columns = layout_rng.sample(range(grid_w), feature_count)
    grid = full_grid(grid_h, grid_w, 0)
    for column, (_, values) in zip(columns, features):
        start = layout_rng.randint(0, grid_h - len(values))
        for offset, value in enumerate(values):
            grid[start + offset][column] = value
    return grid


def _occupancy_segments(grid) -> list[dict[str, object]]:
    height, width = len(grid), len(grid[0])
    result: list[dict[str, object]] = []
    for column in range(width):
        row = 0
        while row < height:
            if grid[row][column] == 0:
                row += 1
                continue
            start = row
            values: list[int] = []
            while row < height and grid[row][column] != 0:
                values.append(grid[row][column])
                row += 1
            result.append(
                {
                    "col": column,
                    "start": start,
                    "end": row - 1,
                    "values": tuple(values),
                    "length": len(values),
                    "uniform": len(set(values)) == 1,
                }
            )
    return result


def _same_color_runs(grid):
    height, width = len(grid), len(grid[0])
    for column in range(width):
        row = 0
        while row < height:
            value = grid[row][column]
            if value == 0:
                row += 1
                continue
            start = row
            while row < height and grid[row][column] == value:
                row += 1
            yield column, start, row - 1, value


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared public axis from the returned pixels."""
    segments = _occupancy_segments(grid)
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": sum(s["length"] == 3 and s["uniform"] for s in segments),
        "n_mixed": sum(s["length"] == 3 and not s["uniform"] for s in segments),
        "n_short": sum(s["length"] == 2 and s["uniform"] for s in segments),
        "n_long": sum(s["length"] == 4 and s["uniform"] for s in segments),
        "palette_size": len(colors),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task manifold while accepting every canonical input."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 16 or not 6 <= width <= 16:
        errors.append(f"grid dimensions {height}x{width} outside 6..16")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors
    if any(value == 8 for row in grid for value in row):
        errors.append("input color 8 is reserved for highlighted output endpoints")

    segments = _occupancy_segments(grid)
    by_column: dict[int, int] = {}
    target_count = 0
    for segment in segments:
        column = int(segment["col"])
        by_column[column] = by_column.get(column, 0) + 1
        length = int(segment["length"])
        uniform = bool(segment["uniform"])
        if length not in (2, 3, 4):
            errors.append(f"column {column} has unsupported occupancy length {length}")
        if length in (2, 4) and not uniform:
            errors.append(f"column {column} length-{length} distractor must be same-color")
        if length == 3 and uniform:
            target_count += 1
    repeated = sorted(column for column, count in by_column.items() if count > 1)
    if repeated:
        errors.append(f"columns contain multiple separated occupancy blocks: {repeated}")
    if target_count < 1:
        errors.append("no exact same-color vertical run of length 3")

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) < 2:
        errors.append(f"expected at least two nonzero input colors, found {len(colors)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require a canonical shape and canonical two-color foreground palette."""
    errors = list(self_check(grid))
    if not errors and (len(grid), len(grid[0])) not in set(_CANONICAL_SHAPES):
        errors.append(
            f"shape {len(grid)}x{len(grid[0])} is not one of {_CANONICAL_SHAPES}"
        )
    colors = {value for row in grid for value in row if value != 0}
    if not errors and len(colors) != 2:
        errors.append(f"strict canonical profile requires two nonzero colors, found {len(colors)}")
    return errors


def _exact_same_color_output(grid):
    out = deepcopy(grid)
    for column, start, end, _ in _same_color_runs(grid):
        if end - start + 1 == 3:
            out[start][column] = 8
            out[end][column] = 8
    return out


def _occupancy_exact_three(grid):
    """Wrong: treat any three occupied cells as a target, ignoring color."""
    out = deepcopy(grid)
    for segment in _occupancy_segments(grid):
        if segment["length"] == 3:
            out[segment["start"]][segment["col"]] = 8
            out[segment["end"]][segment["col"]] = 8
    return out


def _all_non_singleton_runs(grid):
    """Wrong: mark endpoints of every same-color run of length at least two."""
    out = deepcopy(grid)
    for column, start, end, _ in _same_color_runs(grid):
        if end - start + 1 >= 2:
            out[start][column] = 8
            out[end][column] = 8
    return out


def _at_least_three_runs(grid):
    """Wrong: mark same-color runs of length three or more, not exactly three."""
    out = deepcopy(grid)
    for column, start, end, _ in _same_color_runs(grid):
        if end - start + 1 >= 3:
            out[start][column] = 8
            out[end][column] = 8
    return out


def _mixed_color_exact_three_witness(grid) -> bool:
    return self_check(grid) == [] and any(
        segment["length"] == 3 and not segment["uniform"]
        for segment in _occupancy_segments(grid)
    ) and _occupancy_exact_three(grid) != _exact_same_color_output(grid)


def _short_same_color_witness(grid) -> bool:
    return self_check(grid) == [] and any(
        segment["length"] == 2 and segment["uniform"]
        for segment in _occupancy_segments(grid)
    ) and _all_non_singleton_runs(grid) != _exact_same_color_output(grid)


def _long_same_color_witness(grid) -> bool:
    return self_check(grid) == [] and any(
        segment["length"] == 4 and segment["uniform"]
        for segment in _occupancy_segments(grid)
    ) and _at_least_three_runs(grid) != _exact_same_color_output(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Return [] only when the demos refute every declared plausible rival."""
    del query
    findings: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            refuted = any(rival(pair["input"]) != pair["output"] for pair in demos)
        except Exception as exc:
            findings.append(f"{name} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if not refuted:
            findings.append(f"{name} still fits every demonstration")
    return findings


SEMANTIC_WITNESSES = {
    "mixed_color_exact_three": _mixed_color_exact_three_witness,
    "short_same_color_run": _short_same_color_witness,
    "long_same_color_run": _long_same_color_witness,
}
SEMANTIC_RIVALS = {
    "occupancy_exact_three": _occupancy_exact_three,
    "all_non_singleton_runs": _all_non_singleton_runs,
    "at_least_three_runs": _at_least_three_runs,
}
WITNESS_RIVALS = {
    "mixed_color_exact_three": ["occupancy_exact_three"],
    "short_same_color_run": ["all_non_singleton_runs"],
    "long_same_color_run": ["at_least_three_runs"],
}
# Only the color-blind occupancy shortcut fits all three public pairs.  The
# length-threshold rivals are still useful lesson competitors and witnesses.
CANONICAL_SHORTCUTS = {"occupancy_exact_three": _occupancy_exact_three}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def mutation_fixtures():
    """Small invalid grids used by the strict defect-lint mutation stage."""
    blank = full_grid(6, 6, 0)

    singleton = full_grid(6, 6, 0)
    singleton[1][1] = 1

    length_five = full_grid(6, 6, 0)
    for row in range(5):
        length_five[row][1] = 1
    length_five[1][4] = 2

    split_column = full_grid(6, 6, 0)
    split_column[0][0] = 1
    split_column[2][0] = 1
    for row in range(1, 4):
        split_column[row][3] = 2

    input_eight = full_grid(6, 6, 0)
    for row in range(3):
        input_eight[row][1] = 1
    input_eight[4][4] = 8
    input_eight[5][4] = 2

    return [
        ("blank", blank),
        ("singleton", singleton),
        ("length_five", length_five),
        ("split_column", split_column),
        ("input_eight", input_eight),
    ]
