"""Semantic generator for task 2a928a0f8378: compact nonzero rows upward.

Every all-zero row is removed from its original position.  The complete
nonzero rows keep their exact contents and top-to-bottom order, then enough
all-zero rows are appended to preserve the input dimensions.

Normal draws always contain a leading blank region and at least one internal
blank row, so the rule visibly fires.  Every draw also contains distinct row
textures, including one monochrome row and one multicolor row.  Sequential
sample indices alternate a low-density/high-density row ordering so a lesson
with ordinary consecutive demonstrations cannot be explained by sorting rows
by density instead of preserving their source order.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2a928a0f8378"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "12cdce90baa1"

SUMMARY = (
    "Keep every row containing at least one nonzero cell, preserve each row "
    "exactly and preserve their top-to-bottom order, move those rows to the "
    "top, then append all-zero rows to retain the original height and width."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "0 is the background and at least two rows are entirely zero",
    "at least two rows contain nonzero cells",
    "normal draws have both a leading blank row and an internal blank row",
    "normal draws visibly change under upward row compaction",
    "the complete contents and relative order of all nonzero rows are preserved",
    "normal draws contain distinct monochrome and multicolor row witnesses",
]

# These are the only public controls.  Every value is exact, recoverable from
# the returned grid, and consumed through GenCtx.  Layout/textural nuisance
# variation remains deterministic but is deliberately not advertised as an
# exact override axis.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 6..16",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 6..16",
        "valid": "6..16",
    },
    "active_rows": {
        "type": "int",
        "default": "difficulty-aware rng 2..min(8, grid_h-2)",
        "valid": "2..8",
    },
    "palette_size": {
        "type": "int",
        "default": "difficulty-aware rng 2..6",
        "valid": "2..6",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    if errors:
        return None, errors
    return converted, []


def _active_rows(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid if any(value != 0 for value in row)]


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror; the canonical Racket rule remains authority."""
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    kept = _active_rows(converted)
    blank = [0] * len(converted[0])
    return kept + [blank[:] for _ in range(len(converted) - len(kept))]


def _analysis(grid) -> dict:
    converted, errors = _coerce_grid(grid)
    result = {
        "errors": list(errors),
        "grid_h": None,
        "grid_w": None,
        "active_rows": None,
        "palette_size": None,
        "active_indices": (),
        "blank_indices": (),
        "solid_rows": 0,
        "mixed_rows": 0,
        "distinct_row_count": 0,
        "changed": False,
        "output": None,
    }
    if errors or converted is None:
        return result

    h, w = len(converted), len(converted[0])
    active_indices = tuple(
        index for index, row in enumerate(converted) if any(value != 0 for value in row)
    )
    blank_indices = tuple(index for index in range(h) if index not in active_indices)
    active = [converted[index] for index in active_indices]
    palette = {value for row in converted for value in row if value != 0}
    row_color_counts = [len({value for value in row if value != 0}) for row in active]
    output = rule_mirror(converted)

    result.update(
        {
            "grid_h": h,
            "grid_w": w,
            "active_rows": len(active),
            "palette_size": len(palette),
            "active_indices": active_indices,
            "blank_indices": blank_indices,
            "solid_rows": sum(count == 1 for count in row_color_counts),
            "mixed_rows": sum(count >= 2 for count in row_color_counts),
            "distinct_row_count": len({tuple(row) for row in active}),
            "changed": output != converted,
            "output": output,
            "foreground_counts": Counter(
                value for row in converted for value in row if value != 0
            ),
        }
    )
    return result


def observe_overrides(grid) -> dict[str, int]:
    """Return every exact public axis as realized in ``grid``."""
    facts = _analysis(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "active_rows": facts["active_rows"],
        "palette_size": facts["palette_size"],
    }


def _choose_active_positions(h: int, k: int, rng) -> list[int]:
    """Choose positions with leading, internal, and variable trailing blanks."""
    blank_count = h - k
    if k < 2 or blank_count < 2:
        raise ValueError("normal draws require at least two active and two blank rows")

    # Split the blank rows into a nonempty leading region, a nonempty internal
    # set, and an optional trailing region.  Endpoints of the active span stay
    # active, so every sampled internal blank is genuinely between kept rows.
    trailing = rng.randint(0, blank_count - 2)
    leading = rng.randint(1, blank_count - trailing - 1)
    internal_count = blank_count - leading - trailing
    interior_candidates = list(range(leading + 1, h - trailing - 1))
    if internal_count > len(interior_candidates):
        raise ValueError(
            f"cannot place {internal_count} internal blanks in {h} rows with "
            f"leading={leading}, trailing={trailing}, active_rows={k}"
        )
    internal = set(rng.sample(interior_candidates, internal_count))
    blanks = set(range(leading)) | internal
    if trailing:
        blanks.update(range(h - trailing, h))
    positions = [index for index in range(h) if index not in blanks]
    if len(positions) != k:
        raise RuntimeError("active-row placement did not realize the requested count")
    return positions


def _row_from_requirements(
    w: int,
    required_colors: Sequence[int],
    palette: Sequence[int],
    rng,
    *,
    min_count: int,
    max_count: int,
    allowed_columns: Sequence[int] | None = None,
) -> list[int]:
    required = list(dict.fromkeys(int(color) for color in required_colors))
    columns_pool = list(range(w)) if allowed_columns is None else list(allowed_columns)
    if not columns_pool or any(not 0 <= column < w for column in columns_pool):
        raise ValueError("allowed_columns must be nonempty valid grid columns")
    lo = max(min_count, len(required))
    hi = min(max_count, w - 1, len(columns_pool))
    if hi < lo:
        raise ValueError(
            f"cannot place {len(required)} required colors in width {w} "
            f"with count range {min_count}..{max_count}"
        )
    count = rng.randint(lo, hi)
    columns = sorted(rng.sample(columns_pool, count))
    row = [0] * w
    assigned = required + [rng.choice(list(palette)) for _ in range(count - len(required))]
    rng.shuffle(assigned)
    for column, color in zip(columns, assigned):
        row[column] = color
    return row


def _build_active_row_contents(
    k: int,
    w: int,
    palette: Sequence[int],
    sample_index: int,
    rng,
) -> list[list[int]]:
    """Build exact, distinct row witnesses with a scheduled order contrast."""
    rows: list[list[int] | None] = [None] * k
    ascending_density = sample_index % 2 == 0
    solid_slot, mixed_slot = ((0, 1) if ascending_density else (1, 0))

    # One one-cell monochrome row and one multicolor row give an unambiguous
    # density-order witness.  Their order alternates with consecutive
    # sample_index values, so row sorting cannot explain a normal lesson.
    solid_color = palette[-1]
    # Column 0 is colored only in the solid witness.  Combined with the
    # alternating solid/mixed row order, every ordinary 3-demo lesson falsifies
    # both lexicographic sorting and sorting by first nonzero column, in addition
    # to the low/high-density sorting shortcuts.
    solid_col = 0
    solid = [0] * w
    solid[solid_col] = solid_color
    rows[solid_slot] = solid

    mixed_required = list(palette) if len(palette) == 2 else list(palette[:-1])
    rows[mixed_slot] = _row_from_requirements(
        w,
        mixed_required,
        palette,
        rng,
        min_count=max(2, len(mixed_required)),
        max_count=min(5, w - 1),
        allowed_columns=range(1, w),
    )

    seen = {tuple(solid), tuple(rows[mixed_slot])}
    for index in range(k):
        if rows[index] is not None:
            continue
        for _ in range(128):
            # Additional rows vary between monochrome and multicolor textures,
            # but remain sparse enough that each complete row has visible zeros.
            color_count = rng.randint(1, min(len(palette), 3))
            required = rng.sample(list(palette), color_count)
            candidate = _row_from_requirements(
                w,
                required,
                palette,
                rng,
                min_count=max(1, color_count),
                max_count=min(5, w - 1),
            )
            signature = tuple(candidate)
            if signature not in seen:
                rows[index] = candidate
                seen.add(signature)
                break
        if rows[index] is None:
            raise RuntimeError("could not construct distinct active-row textures")

    return [list(row) for row in rows if row is not None]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    requested_active = overrides.get("active_rows")
    if requested_active is not None:
        requested_active = int(requested_active)
        if not 2 <= requested_active <= 8:
            raise ValueError("active_rows override must be in 2..8")
        min_h = max(6, requested_active + 2)
    else:
        min_h = 6

    h = ctx.draw_int_diff("grid_h", min_h, 16)
    w = ctx.draw_int_diff("grid_w", 6, 16)
    max_active = min(8, h - 2)
    k = ctx.draw_int_diff("active_rows", 2, max_active)
    palette_size = ctx.draw_int_diff("palette_size", 2, 6)

    rng = ctx.draw_rng("layout")
    positions = _choose_active_positions(h, k, rng)
    palette = tuple(sorted(ctx.draw_distinct_colors("colors", n=palette_size, exclude={0})))
    contents = _build_active_row_contents(k, w, palette, sample_index, rng)

    grid = full_grid(h, w, 0)
    for row_index, row in zip(positions, contents):
        grid[row_index] = row[:]
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural checker for canonical inputs and the stronger generated grammar."""
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    h = facts["grid_h"]
    w = facts["grid_w"]
    active_indices = facts["active_indices"]
    blank_indices = facts["blank_indices"]
    active_count = facts["active_rows"]

    if active_count < 1:
        errors.append("at least one nonzero row is required")
    if not blank_indices:
        errors.append("at least one all-zero row is required")
    if not facts["changed"]:
        errors.append("active rows are already top-packed; the rule is a whole-grid identity")

    # Canonical rows are authoritative and intentionally use only monochrome
    # active rows.  Generated draws carry stronger anti-shortcut witnesses.
    canonical = bool(isinstance(meta, dict) and meta.get("canonical"))
    if canonical:
        return errors

    if not 6 <= h <= 16:
        errors.append(f"generated height must be in 6..16, found {h}")
    if not 6 <= w <= 16:
        errors.append(f"generated width must be in 6..16, found {w}")
    if not 2 <= active_count <= 8:
        errors.append(f"generated active-row count must be in 2..8, found {active_count}")
    if not 2 <= facts["palette_size"] <= 6:
        errors.append(
            f"generated nonzero palette size must be in 2..6, found {facts['palette_size']}"
        )
    if not active_indices or active_indices[0] == 0:
        errors.append("generated grid must have at least one leading blank row")
    if not any(right - left > 1 for left, right in zip(active_indices, active_indices[1:])):
        errors.append("generated grid must have at least one internal blank row")
    if facts["solid_rows"] < 1:
        errors.append("generated grid needs a monochrome active-row witness")
    if facts["mixed_rows"] < 1:
        errors.append("generated grid needs a multicolor active-row witness")
    if facts["distinct_row_count"] != active_count:
        errors.append("generated active rows must be pairwise distinct")

    converted, _ = _coerce_grid(grid)
    assert converted is not None
    for row_index in active_indices:
        row = converted[row_index]
        if all(value != 0 for value in row):
            errors.append(f"active row {row_index} must retain at least one zero cell")

    # When the override harness supplies exact requests, verify them here too;
    # observe_overrides performs the independent contract comparison.
    if isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(converted)
            for axis in AXES:
                if axis in requested and requested[axis] != observed[axis]:
                    errors.append(
                        f"override {axis}={requested[axis]!r} realized as {observed[axis]!r}"
                    )
    return errors
