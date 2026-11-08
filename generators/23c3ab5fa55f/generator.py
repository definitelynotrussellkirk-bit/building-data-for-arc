"""Generator for ARC task 23c3ab5fa55f: compact each row left.

The lesson is row-local and order-sensitive: delete zeroes from each row,
retain the nonzero sequence exactly, and pad the right side with zeroes.  The
default distribution mixes a substantial linked prior over the five canonical
row-count/color-count profiles with broader calibrated scenes.  Every returned
draw contains a singleton row, a shifted contiguous row, an internally-gapped
row, and a descending color sequence, so the transformation is visible and a
count-only or color-sorting shortcut is contradicted inside the same grid.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "23c3ab5fa55f"
TASK_ID = "23c3ab5fa55f"
VERSION = "2.0.0"
RULE_HASH = "8cd149b15ecf"
SUMMARY = (
    "Independently compact every row's nonzero cells to the left, preserving "
    "their exact left-to-right color order and padding the remainder with 0."
)

INVARIANTS = [
    "background is 0 and the grid remains the same shape",
    "rows are transformed independently",
    "the nonzero sequence of each row is preserved exactly",
    "every generated lesson has a singleton row, a shifted contiguous row, and an internally-gapped row",
    "every generated lesson includes a descending color pair, rebutting color-sorting shortcuts",
    "at least one row changes under left compaction",
]

# Exact, observable controls only.  Nuisance choices such as row locations,
# palette identities, and gap patterns vary deterministically but are not
# exposed as per-draw override promises.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked canonical prior or difficulty-aware rng 6..10",
        "valid": "6..10",
    },
    "grid_w": {
        "type": "int",
        "default": "linked canonical prior or difficulty-aware rng 8..13",
        "valid": "8..13",
    },
    "active_rows": {
        "type": "int",
        "default": "linked canonical prior or difficulty-aware rng 3..8",
        "valid": "3..8",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "linked canonical prior or difficulty-aware rng 2..8",
        "valid": "2..8",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Executable linked profiles extracted from all four train inputs and the held-
# out test input.  Coordinates and literal color identities are nuisance
# factors; the linked row occupancy multiset and palette cardinality are not.
# Each tuple is: (height, width, sorted active-row nonzero counts, color count).
_CANONICAL_PROFILES = {
    (8, 9, (1, 2, 3, 3), 7),
    (8, 9, (1, 2, 3), 3),
    (8, 9, (1, 2, 2, 2, 3, 3, 3, 4), 7),
    (8, 9, (1, 1, 2, 2, 2, 3, 3, 4), 7),
    (8, 9, (1, 1, 1, 3, 4), 8),
}
_CANONICAL_PROFILE_LIST = tuple(sorted(_CANONICAL_PROFILES))

_DEFAULT_BOUNDS = {
    "easy": {
        "grid_h": (6, 8),
        "grid_w": (8, 10),
        "active_rows": (3, 5),
        "n_distinct_colors": (2, 5),
    },
    "medium": {
        "grid_h": (7, 9),
        "grid_w": (9, 11),
        "active_rows": (4, 7),
        "n_distinct_colors": (3, 7),
    },
    "hard": {
        "grid_h": (8, 10),
        "grid_w": (10, 13),
        "active_rows": (5, 8),
        "n_distinct_colors": (4, 8),
    },
}
_PRIOR_RATE = {"easy": 0.70, "medium": 0.55, "hard": 0.40}


def _valid_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC color integers 0 through 9"]
    return []


def _row_facts(row: list[int] | tuple[int, ...]) -> dict[str, Any]:
    columns = [index for index, value in enumerate(row) if value != 0]
    values = [row[index] for index in columns]
    contiguous = bool(columns) and columns == list(
        range(columns[0], columns[0] + len(columns))
    )
    return {
        "columns": tuple(columns),
        "values": tuple(values),
        "count": len(columns),
        "singleton": len(columns) == 1,
        "shifted_contiguous": contiguous and columns[0] > 0,
        "internally_gapped": any(
            right - left > 1 for left, right in zip(columns, columns[1:])
        ),
        "descending": any(
            left > right for left, right in zip(values, values[1:])
        ),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "facts": {}}

    height, width = len(grid), len(grid[0])
    rows = [_row_facts(row) for row in grid]
    active = [item for item in rows if item["count"]]
    palette = sorted({value for row in grid for value in row if value != 0})
    row_counts = tuple(sorted(item["count"] for item in active))

    if not 6 <= height <= 10:
        errors.append("calibrated height must be 6 through 10")
    if not 8 <= width <= 13:
        errors.append("calibrated width must be 8 through 13")
    if not 3 <= len(active) <= 8:
        errors.append("calibrated lessons need 3 through 8 active rows")
    if not 2 <= len(palette) <= 8:
        errors.append("calibrated lessons need 2 through 8 distinct nonzero colors")
    if any(not 1 <= item["count"] <= 5 for item in active):
        errors.append("each active row must contain 1 through 5 nonzero cells")
    if len(set(row_counts)) < 2:
        errors.append("active rows must use at least two different occupancy counts")
    if not any(item["singleton"] for item in active):
        errors.append("lesson needs a singleton active row")
    if not any(item["shifted_contiguous"] for item in active):
        errors.append("lesson needs a shifted contiguous row")
    if not any(item["internally_gapped"] for item in active):
        errors.append("lesson needs an internally-gapped row")
    if not any(item["descending"] for item in active):
        errors.append("lesson needs a descending nonzero color pair")

    facts = {
        "height": height,
        "width": width,
        "active_rows": len(active),
        "n_distinct_colors": len(palette),
        "palette": tuple(palette),
        "row_counts": row_counts,
        "total_nonzero": sum(item["count"] for item in active),
        "singleton_rows": sum(item["singleton"] for item in active),
        "shifted_contiguous_rows": sum(
            item["shifted_contiguous"] for item in active
        ),
        "internally_gapped_rows": sum(item["internally_gapped"] for item in active),
        "descending_rows": sum(item["descending"] for item in active),
        "row_facts": tuple(active),
    }
    return {"errors": errors, "facts": facts}


def profile_signature(grid: Any):
    """Coarse linked morphology used for both canonical and generated grids."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    facts = analysis["facts"]
    return (
        facts["height"],
        facts["width"],
        facts["row_counts"],
        facts["n_distinct_colors"],
    )


def canonical_profile_signature(grid: Any):
    signature = profile_signature(grid)
    return signature if signature in _CANONICAL_PROFILES else None


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact AXES value from the returned grid itself."""
    analysis = _analysis(grid)
    facts = analysis.get("facts") or {}
    if not facts:
        return {}
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "active_rows": facts["active_rows"],
        "n_distinct_colors": facts["n_distinct_colors"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the calibrated teaching grammar without mutating ``grid``."""
    del difficulty, meta
    return _analysis(grid)["errors"]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Input-pure Python mirror for tests; the canonical Racket rule is authority."""
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    width = len(grid[0])
    output = []
    for row in grid:
        values = [value for value in row if value != 0]
        output.append(values + [0] * (width - len(values)))
    return output


def _draw_global_or_default(ctx, name: str, default: tuple[int, int], global_: tuple[int, int]):
    bounds = global_ if name in ctx.overrides else default
    return ctx.draw_int(name, *bounds)


def _general_counts(active_rows: int, n_colors: int, width: int, rng) -> list[int]:
    """Create exact active-row counts with mandatory 1/2/3-cell branches."""
    counts = [1, 2, 3]
    counts.extend(rng.randint(1, min(4, width - 1)) for _ in range(active_rows - 3))
    max_count = min(5, width - 1)
    while sum(counts) < n_colors:
        candidates = [index for index, count in enumerate(counts) if count < max_count]
        if not candidates:
            raise ValueError(
                "incompatible active_rows/n_distinct_colors/grid_w combination"
            )
        # Preserve at least one singleton while expanding other rows first.
        non_singletons = [index for index in candidates if counts[index] > 1]
        index = rng.choice(non_singletons or candidates)
        counts[index] += 1
    rng.shuffle(counts)
    return counts


def _gapped_positions(count: int, width: int, rng) -> list[int]:
    for _ in range(128):
        columns = sorted(rng.sample(range(width), count))
        if any(right - left > 1 for left, right in zip(columns, columns[1:])):
            return columns
    # Deterministic fallback; width >= 8 and count <= 5 make this reachable.
    return list(range(count - 1)) + [count]


def _row_positions(count: int, width: int, role: str, rng) -> list[int]:
    if role == "shifted_contiguous":
        start = rng.randint(1, width - count)
        return list(range(start, start + count))
    if role == "gapped":
        return _gapped_positions(count, width, rng)
    if role == "left_packed":
        return list(range(count))

    choice = rng.randrange(4)
    if choice == 0:
        return list(range(count))
    if choice == 1:
        start = rng.randint(1, width - count)
        return list(range(start, start + count))
    return _gapped_positions(count, width, rng)


def _color_sequences(counts: list[int], gapped_index: int, palette: tuple[int, ...], rng):
    """Assign every palette color and force a stable-order sorting counterexample."""
    sequences = [[None] * count for count in counts]
    high, low = max(palette), min(palette)
    sequences[gapped_index][0] = high
    sequences[gapped_index][1] = low

    open_slots = [
        (row_index, cell_index)
        for row_index, count in enumerate(counts)
        for cell_index in range(count)
        if sequences[row_index][cell_index] is None
    ]
    mandatory = [color for color in palette if color not in {high, low}]
    filler_count = len(open_slots) - len(mandatory)
    if filler_count < 0:
        raise ValueError("not enough cells to realize n_distinct_colors exactly")
    values = mandatory + [rng.choice(palette) for _ in range(filler_count)]
    rng.shuffle(values)
    for (row_index, cell_index), value in zip(open_slots, values):
        sequences[row_index][cell_index] = value
    return [[int(value) for value in sequence] for sequence in sequences]


def _draw_scene(
    ctx,
    height: int,
    width: int,
    counts: list[int],
    n_colors: int,
    *,
    scene_label: str,
):
    rng = ctx.draw_rng(scene_label)
    active_rows = len(counts)
    row_indices = sorted(rng.sample(range(height), active_rows))

    singleton_candidates = [index for index, count in enumerate(counts) if count == 1]
    gapped_candidates = [index for index, count in enumerate(counts) if count >= 2]
    if not singleton_candidates or not gapped_candidates:
        raise ValueError("scene counts must include singleton and multi-cell rows")
    singleton_index = rng.choice(singleton_candidates)
    gapped_index = rng.choice(gapped_candidates)

    palette = tuple(rng.sample(range(1, 10), n_colors))
    sequences = _color_sequences(counts, gapped_index, palette, rng)
    grid = full_grid(height, width, 0)

    for local_index, (row_index, count, colors) in enumerate(
        zip(row_indices, counts, sequences)
    ):
        if local_index == singleton_index:
            role = "shifted_contiguous"
        elif local_index == gapped_index:
            role = "gapped"
        else:
            role = "mixed"
        columns = _row_positions(count, width, role, rng)
        for column, color in zip(columns, colors):
            grid[row_index][column] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = difficulty if difficulty in _DEFAULT_BOUNDS else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # A linked canonical-profile prior is used only for ordinary draws.  Exact
    # caller controls bypass it so no early-return path can ignore an override.
    use_profile = (
        not overrides
        and ctx.draw_rng("canonical_prior").random() < _PRIOR_RATE[band]
    )
    if use_profile:
        profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILE_LIST)
        height, width, row_counts, n_colors = profile
        height = ctx.draw_int("grid_h", height, height)
        width = ctx.draw_int("grid_w", width, width)
        active_rows = ctx.draw_int("active_rows", len(row_counts), len(row_counts))
        n_colors = ctx.draw_int("n_distinct_colors", n_colors, n_colors)
        counts = list(row_counts)
        ctx.draw_rng("count_permutation").shuffle(counts)
        return _draw_scene(
            ctx,
            height,
            width,
            counts,
            n_colors,
            scene_label=f"scene_layout_{band}",
        )

    defaults = _DEFAULT_BOUNDS[band]
    active_override = (
        int(overrides["active_rows"])
        if overrides.get("active_rows") is not None
        else None
    )
    height_override = (
        int(overrides["grid_h"])
        if overrides.get("grid_h") is not None
        else None
    )
    if (
        active_override is not None
        and height_override is not None
        and active_override > height_override
    ):
        raise ValueError("incompatible: active_rows cannot exceed grid_h")

    height_default = defaults["grid_h"]
    if active_override is not None:
        height_default = (
            max(height_default[0], active_override),
            max(height_default[1], active_override),
        )
    height = _draw_global_or_default(ctx, "grid_h", height_default, (6, 10))
    width = _draw_global_or_default(
        ctx, "grid_w", defaults["grid_w"], (8, 13)
    )

    active_default = (
        defaults["active_rows"][0],
        min(defaults["active_rows"][1], height, 8),
    )
    active_rows = _draw_global_or_default(
        ctx, "active_rows", active_default, (3, 8)
    )
    if active_rows > height:
        raise ValueError("incompatible: active_rows cannot exceed grid_h")

    n_colors = _draw_global_or_default(
        ctx,
        "n_distinct_colors",
        defaults["n_distinct_colors"],
        (2, 8),
    )
    counts = _general_counts(
        active_rows,
        n_colors,
        width,
        ctx.draw_rng("row_counts"),
    )
    grid = _draw_scene(
        ctx,
        height,
        width,
        counts,
        n_colors,
        scene_label=f"scene_layout_{band}",
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator constructed an invalid lesson: " + "; ".join(errors))
    return grid
