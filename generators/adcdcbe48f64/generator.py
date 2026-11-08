"""Input generator for ARC task adcdcbe48f64 (bc4146bd).

The unchanged authority emits five horizontal copies of the input, alternating
original and left-right mirror:

    input | mirror | input | mirror | input

The sampler keeps the reflection visible, regularly reproduces the canonical
4x4/two-or-three-color profile, and exposes only controls that can be recovered
exactly from the returned pixels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "adcdcbe48f64"
TASK_ID = GENERATOR_ID
RULE_HASH = "5ed1759c50b3"
VERSION = "3.3.0"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A 4..15 by 4..6 dense nonzero multicolor tile with a visible left-right "
    "asymmetry. The output is five horizontal tiles alternating original and "
    "left-right mirror, beginning and ending with the original. Canonical 4x4 "
    "two/three-color inputs are a dominant curriculum profile; broader sizes "
    "and four-color textures remain represented in every difficulty band."
)

INVARIANTS = [
    "input height is 4..15 and width is 4..6, so the 5w output is at most 30 columns",
    "all cells are nonzero ARC colors and exactly 2..4 distinct colors are present",
    "each color appears at least three times and no color exceeds 70% of the tile",
    "the input is not left-right symmetric, so the mirrored tiles are observable",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-weighted full-domain draw; difficulty changes only the bias",
        "valid": "4..15",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-weighted full-domain draw; difficulty changes only the bias",
        "valid": "4..6",
    },
    "palette_size": {
        "type": "int",
        "default": "canonical-weighted 2..4",
        "valid": "2..4",
    },
}

# Every cross-product of the advertised controls is constructive: the smallest
# 4x4 grid has enough cells to realize four colors at least three times each.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []

_PATTERN_MODES = (
    "noise",
    "row_stripes",
    "column_stripes",
    "diagonal",
    "blocks",
    "sparse",
)


_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    bounds = {
        "grid_h": (4, 15),
        "grid_w": (4, 6),
        "palette_size": (2, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_values(lo: int, hi: int, canonical: int, difficulty, *, axis: str) -> list[int]:
    """Return a full-domain choice list with canonical and band-specific bias."""
    values = list(range(lo, hi + 1))
    values.extend([canonical] * 80)
    if axis == "grid_h":
        if difficulty == "easy":
            values.extend([4, 5, 6] * 4)
        elif difficulty == "hard":
            values.extend(list(range(8, 16)) * 2)
        else:
            values.extend(list(range(4, 16)))
    elif axis == "grid_w":
        if difficulty == "easy":
            values.extend([4] * 12)
        elif difficulty == "hard":
            values.extend([4, 5, 6] * 4)
        else:
            values.extend(list(range(4, 7)) * 2)
    return values


def _palette_values(difficulty) -> list[int]:
    values = [2, 3, 4]
    # Both canonical palette counts remain dominant in every band.
    values.extend([2, 3] * 40)
    if difficulty == "easy":
        values.extend([2] * 8)
    elif difficulty == "hard":
        values.extend([4] * 8)
    else:
        values.extend([2, 3, 4] * 2)
    return values


def _draw_pattern(mode: str, height: int, width: int, palette, rng) -> list[list[int]]:
    count = len(palette)
    if mode == "noise":
        grid = [[rng.choice(palette) for _ in range(width)] for _ in range(height)]
    elif mode == "row_stripes":
        offset = rng.randrange(count)
        grid = [[palette[(row + offset) % count] for _ in range(width)]
                for row in range(height)]
    elif mode == "column_stripes":
        offset = rng.randrange(count)
        grid = [[palette[(col + offset) % count] for col in range(width)]
                for _ in range(height)]
    elif mode == "diagonal":
        offset = rng.randrange(count)
        grid = [[palette[(row + 2 * col + offset) % count] for col in range(width)]
                for row in range(height)]
    elif mode == "blocks":
        row_step = max(1, height // max(2, count))
        col_step = max(1, width // 2)
        offset = rng.randrange(count)
        grid = [[palette[((row // row_step) + (col // col_step) + offset) % count]
                 for col in range(width)] for row in range(height)]
    elif mode == "sparse":
        grid = [[palette[0] for _ in range(width)] for _ in range(height)]
        cells = [(row, col) for row in range(height) for col in range(width)]
        rng.shuffle(cells)
        touches = max(count - 1, (height * width) // 4)
        for index, (row, col) in enumerate(cells[:touches]):
            grid[row][col] = palette[1 + index % (count - 1)]
    else:  # pragma: no cover - private mode list is closed above
        raise ValueError(f"unknown pattern mode: {mode}")

    # Reserve two mirrored positions for different colors. This simultaneously
    # guarantees colors 0/1 appear and makes LR reflection visible for every
    # width, including the 2-column boundary.
    reserved = {(0, 0), (0, width - 1)}
    grid[0][0] = palette[0]
    grid[0][width - 1] = palette[1]

    # Reserve one distinct cell for each additional palette color. The smallest
    # legal canvas is 4x4, leaving room to enforce a dense color-balance grammar.
    available = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in reserved
    ]
    for color, (row, col) in zip(palette[2:], available):
        grid[row][col] = color

    # This task is a transformation of a dense symbolic tile, not object-on-
    # background extraction. Keep every color materially represented and prevent
    # one modal color from turning the input into a tiny foreground impostor.
    locked = reserved
    counts = {color: sum(value == color for row in grid for value in row)
              for color in palette}

    def replace_one(donor, recipient):
        candidates = [
            (row, col)
            for row in range(height)
            for col in range(width)
            if (row, col) not in locked and grid[row][col] == donor
        ]
        if not candidates:
            raise RuntimeError("unable to rebalance generated color counts")
        row, col = rng.choice(candidates)
        grid[row][col] = recipient
        counts[donor] -= 1
        counts[recipient] += 1

    for recipient in palette:
        while counts[recipient] < 3:
            donor = max(palette, key=lambda color: counts[color])
            if counts[donor] <= 3:
                raise RuntimeError("canvas cannot realize the declared palette balance")
            replace_one(donor, recipient)

    max_count = (height * width * 7) // 10
    while max(counts.values()) > max_count:
        donor = max(palette, key=lambda color: counts[color])
        recipient = min(palette, key=lambda color: counts[color])
        replace_one(donor, recipient)

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # A four-pair lesson (three demonstrations plus one query) must remain
    # identifiable under every query rotation.  The canonical training examples
    # are all width four, so an unconstrained draw can accidentally put the only
    # width-five/six witness in the query.  This three-slot schedule gives every
    # four consecutive samples at least two variable-width examples while keeping
    # a deterministic 4x4 canonical profile in every third slot.  Explicit axis
    # overrides still take precedence and are validated over the full domain.
    canonical_slot = sample_index % 3 == 0
    if overrides.get("grid_h") is not None:
        height_options = _weighted_values(4, 15, 4, difficulty, axis="grid_h")
    elif canonical_slot:
        height_options = [4]
    else:
        height_options = _weighted_values(4, 15, 4, difficulty, axis="grid_h")

    if overrides.get("grid_w") is not None:
        width_options = _weighted_values(4, 6, 4, difficulty, axis="grid_w")
    elif canonical_slot:
        width_options = [4]
    else:
        width_options = [5, 6]

    if overrides.get("palette_size") is not None:
        palette_options = _palette_values(difficulty)
    elif canonical_slot:
        palette_options = [2, 3]
    else:
        palette_options = _palette_values(difficulty)

    height = ctx.draw_choice("grid_h", height_options)
    width = ctx.draw_choice("grid_w", width_options)
    palette_size = ctx.draw_choice("palette_size", palette_options)
    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude={0})

    modes = list(_PATTERN_MODES)
    if difficulty == "easy":
        modes += ["row_stripes", "column_stripes", "diagonal"] * 2
    elif difficulty == "hard":
        modes += ["noise", "blocks", "sparse"] * 2
    mode = ctx.draw_choice("pattern_mode", modes)
    return _draw_pattern(mode, height, width, palette, ctx.draw_rng("cells"))


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be nonzero integer ARC colors 1..9"]
    return []


def _is_lr_sym(grid) -> bool:
    return all(row == row[::-1] for row in grid)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the sampler's lawful, reflection-teaching input manifold."""
    del meta
    if difficulty not in _VALID_DIFFICULTIES:
        return ["difficulty must be None, 'easy', 'medium', or 'hard'"]
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    errors = []
    if not 4 <= height <= 15:
        errors.append(f"height {height} outside [4, 15]")
    if not 4 <= width <= 6:
        errors.append(f"width {width} outside [4, 6]")
    counts = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    if not 2 <= len(counts) <= 4:
        errors.append(f"expected 2..4 distinct colors; found {len(counts)}")
    elif min(counts.values()) < 3:
        errors.append("every color must appear at least three times")
    if counts and max(counts.values()) * 10 > height * width * 7:
        errors.append("no color may occupy more than 70% of the tile")
    if _is_lr_sym(grid):
        errors.append("left-right symmetric input hides the mirrored tiles")
    return errors


def strict_canonical_like(grid):
    """Recognize the selected canonical 4x4, two/three-color input profile."""
    errors = self_check(grid)
    if errors:
        return errors
    colors = {value for row in grid for value in row}
    if (len(grid), len(grid[0])) != (4, 4):
        return ["canonical inputs are 4x4"]
    if len(colors) not in {2, 3}:
        return ["canonical inputs use two or three colors"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe controls from invalid grid: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "palette_size": len({value for row in grid for value in row}),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority."""
    return [list(row) + list(reversed(row)) + list(row) + list(reversed(row)) + list(row)
            for row in grid]


def _plain_repeat(grid) -> list[list[int]]:
    return [list(row) * 5 for row in grid]


def _mirror_first(grid) -> list[list[int]]:
    return [list(reversed(row)) + list(row) + list(reversed(row)) + list(row) + list(reversed(row))
            for row in grid]


def _fixed_width_4(grid) -> list[list[int]]:
    """Canonical-fitting shortcut that wrongly hard-codes the tile width."""
    output = []
    for row in grid:
        tile = list(row[:4])
        mirror = list(reversed(tile))
        output.append(tile + mirror + tile + mirror + tile)
    return output


def _visible_lr_mirror(grid) -> bool:
    return not _grid_errors(grid) and not _is_lr_sym(grid)


def lesson_identifiable(demos, query):
    """Reject lessons where a named wrong rule survives demos but flips query."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with alternating reflection")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with alternating reflection")
    if reasons:
        return reasons

    if not any(_visible_lr_mirror(pair["input"]) for pair in demos):
        reasons.append(
            "demonstrations must include a non-left-right-symmetric input "
            "that visibly distinguishes reflection from repetition"
        )

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


SEMANTIC_WITNESSES = {"visible_lr_mirror": _visible_lr_mirror}
SEMANTIC_RIVALS = {
    "plain_repeat": _plain_repeat,
    "mirror_first": _mirror_first,
}
WITNESS_RIVALS = {
    "visible_lr_mirror": ["plain_repeat", "mirror_first"],
}
# The selected task's frozen semantic-registry fixture requires the legacy
# SEMANTIC_WITNESSES / SEMANTIC_RIVALS surface exactly.  The width-four rule is
# nevertheless an executable, canonical-fitting training competitor, so keep it
# explicit in lesson scoring and cover its canonical fit with task-local tests.
CANONICAL_SHORTCUTS = {}
LESSON_COMPETITORS = {"fixed_width_4": _fixed_width_4}
