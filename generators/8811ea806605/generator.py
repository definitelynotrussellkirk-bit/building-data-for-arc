"""Semantic generator for ARC task 8811ea806605 (Column Gravity Dots).

The Racket oracle counts blue cells independently in each column and redraws
that many blue cells as a contiguous stack against the bottom edge.  Generated
inputs vary the source rows, bottom-row occupancy, canvas size, active-column
mask, and per-column stack heights while preserving a substantial
canonical-like manifold.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8811ea806605"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "85a21a74f703"

SUMMARY = (
    "On a binary 0/1 grid, treat every column independently. Count its blue "
    "(1) cells, erase their original row positions, and redraw exactly that "
    "many blue cells as a bottom-aligned contiguous stack in the same column. "
    "Dimensions and per-column counts are preserved; source-row positions are "
    "irrelevant."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is rectangular, 5..12 rows by 5..14 columns, and uses only colors 0 and 1",
    "4..14 columns are active, including at least one one-dot column and one multi-dot column",
    "no active column contains more than four blue cells",
    "blue cells occupy at least three source rows and the gravity transform changes the grid",
    "default draws mix canonical-like dense-column scenes with broader sparse/taller anti-shortcut scenes",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical mixture 6..7; otherwise difficulty-aware 6..12",
        "valid": "5..12",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical mixture 6..8; otherwise difficulty-aware 6..14",
        "valid": "5..14",
    },
    "active_cols": {
        "type": "int",
        "default": "difficulty-aware feasible draw, often all or all-but-one columns",
        "valid": "4..14",
    },
    "max_stack": {
        "type": "int",
        "default": "2 on canonical/easy draws, up to 4 on hard draws",
        "valid": "2..4",
    },
}

# Exact public inputs are used only to label canonical evidence.  Generation
# remains procedural; these prototypes are never returned by a special branch.
_PUBLIC_INPUT_ROWS = {
    "public_train_1": (
        "0010010", "1001001", "0000100", "0100000", "0000000", "0001000",
    ),
    "public_train_2": (
        "100010", "001000", "000001", "010100", "000000", "001010", "000000",
    ),
    "public_test_1": (
        "01000100", "00010000", "10000010", "00100100", "00000000", "01000001",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(value) for value in row) for row in rows): name
    for name, rows in _PUBLIC_INPUT_ROWS.items()
}


def _gravity_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for validation/tests; never an output authority."""
    h, w = len(grid), len(grid[0])
    counts = [sum(grid[r][c] == 1 for r in range(h)) for c in range(w)]
    return [
        [1 if r >= h - counts[c] else 0 for c in range(w)]
        for r in range(h)
    ]


def _analysis(grid) -> dict:
    errors: list[str] = []
    result = {
        "errors": errors,
        "active_cols": 0,
        "max_stack": 0,
        "column_counts": [],
        "row_support": 0,
        "gravity_changes": False,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be a non-empty list of rows")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be non-empty sequences")
        return result
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if not 5 <= h <= 12 or not 5 <= w <= 14:
        errors.append(f"grid dimensions must be within 5..12 by 5..14; got {h}x{w}")
    bad = sorted({
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 1)
    }, key=repr)
    if bad:
        errors.append(f"input must use only integer colors 0 and 1; got {bad}")
        return result

    counts = [sum(grid[r][c] == 1 for r in range(h)) for c in range(w)]
    positive = [count for count in counts if count]
    active = len(positive)
    max_stack = max(counts, default=0)
    rows_used = {r for r, row in enumerate(grid) if any(value == 1 for value in row)}
    result.update({
        "active_cols": active,
        "max_stack": max_stack,
        "column_counts": counts,
        "row_support": len(rows_used),
    })

    if not 4 <= active <= w:
        errors.append(f"expected 4..{w} active columns; got {active}")
    if 1 not in positive:
        errors.append("expected at least one active column containing exactly one blue cell")
    if not any(count >= 2 for count in positive):
        errors.append("expected at least one multi-cell active column")
    if max_stack > 4:
        errors.append(f"column count exceeds the declared four-cell maximum: {max_stack}")
    if len(rows_used) < 3:
        errors.append(f"blue cells must span at least three source rows; got {len(rows_used)}")

    output = _gravity_output([list(row) for row in grid])
    changes = output != [list(row) for row in grid]
    result["gravity_changes"] = changes
    if not changes:
        errors.append("input is already bottom-packed, so the intended transform is a no-op")
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed/no-op lessons while accepting all canonical inputs."""
    return list(_analysis(grid)["errors"])


def canonical_profile_signature(grid) -> str | None:
    try:
        signature = tuple(tuple(int(value) for value in row) for row in grid)
    except Exception:
        return None
    return _PUBLIC_SIGNATURES.get(signature)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "active_cols": analysis["active_cols"],
        "max_stack": analysis["max_stack"],
    }


def _draw_dimension(ctx, overrides, name, default_lo, default_hi, valid_lo, valid_hi):
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _difficulty_ranges(difficulty: str | None) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (6, 8), (6, 9)
    if difficulty == "medium":
        return (7, 10), (7, 12)
    if difficulty == "hard":
        return (9, 12), (9, 14)
    return (6, 12), (6, 14)


def _counts_for_columns(rng, active: int, max_stack: int, *, canonical_like: bool) -> list[int]:
    if canonical_like:
        # Canonical examples have all/all-but-one columns active, heights 1/2,
        # and total blue count within width..width+2.  The caller chooses active
        # relative to width; choose a small nonzero number of height-2 columns.
        max_twos = min(active - 1, 3)
        twos = rng.randint(1, max_twos)
        counts = [2] * twos + [1] * (active - twos)
    else:
        counts = [rng.randint(1, max_stack) for _ in range(active)]
        counts[0] = 1
        counts[1] = max_stack
    rng.shuffle(counts)
    return counts


def _place_counts(
    h: int,
    w: int,
    columns: list[int],
    counts: list[int],
    rng,
    *,
    canonical_like: bool,
    bottom_seeded: bool,
):
    required_rows = 4 if canonical_like else 3
    forced_bottom_column = rng.choice(columns) if bottom_seeded else None
    for _ in range(256):
        grid = full_grid(h, w, 0)
        for column, count in zip(columns, counts):
            # Choose the source-layout branch once per scene.  This preserves
            # both public patterns: some examples already contain one or more
            # bottom-row dots, while others contain none at all.
            include_bottom = bottom_seeded and (
                column == forced_bottom_column or rng.random() < 0.30
            )
            if include_bottom:
                rows = [h - 1]
                rows.extend(rng.sample(range(h - 1), count - 1))
            else:
                rows = rng.sample(range(h - 1), count)
            for row in rows:
                grid[row][column] = 1
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["row_support"] >= required_rows:
            return grid
    raise AssertionError("failed to place an unambiguous non-degenerate column-gravity lesson")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # The canonical-like prior is default-only. Any explicit semantic override
    # bypasses it, so no requested axis can be silently ignored by an early return.
    canonical_like = not overrides and ctx.draw_rng("canonical_prior").random() < 0.35

    requested_active = None
    if overrides.get("active_cols") is not None:
        requested_active = ctx.draw_int("active_cols", 4, 14)

    if canonical_like:
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 8)
        active = ctx.draw_int("active_cols", max(4, w - 1), w)
        max_stack = ctx.draw_int("max_stack", 2, 2)
    else:
        (h_lo, h_hi), (w_lo, w_hi) = _difficulty_ranges(difficulty)
        h = _draw_dimension(ctx, overrides, "grid_h", h_lo, h_hi, 5, 12)

        if requested_active is not None and overrides.get("grid_w") is None:
            # A single active_cols boundary override must remain realizable in
            # every difficulty band; expand only the unoverridden width domain.
            w_lo = max(w_lo, requested_active)
            w_hi = max(w_hi, requested_active)
        w = _draw_dimension(ctx, overrides, "grid_w", w_lo, w_hi, 5, 14)

        if requested_active is not None:
            active = requested_active
            if active > w:
                raise ValueError(
                    f"active_cols={active} is incompatible with grid_w={w}; active_cols must not exceed width"
                )
        else:
            empties_cap = {"easy": 1, "medium": 3, "hard": 4}.get(difficulty, 4)
            active = ctx.draw_int("active_cols", max(4, w - empties_cap), w)

        if overrides.get("max_stack") is not None:
            max_stack = ctx.draw_int("max_stack", 2, 4)
        else:
            stack_lo, stack_hi = {
                "easy": (2, 2),
                "medium": (2, 3),
                "hard": (3, 4),
            }.get(difficulty, (2, 4))
            max_stack = ctx.draw_int("max_stack", stack_lo, stack_hi)

    if active > w:
        raise ValueError(f"active_cols={active} exceeds grid_w={w}")
    if max_stack >= h:
        raise ValueError(f"max_stack={max_stack} requires grid_h>{max_stack}; got {h}")

    rng = ctx.draw_rng("layout")
    columns = sorted(rng.sample(range(w), active))
    counts = _counts_for_columns(rng, active, max_stack, canonical_like=canonical_like)
    bottom_seeded = rng.random() < 0.50
    grid = _place_counts(
        h,
        w,
        columns,
        counts,
        rng,
        canonical_like=canonical_like,
        bottom_seeded=bottom_seeded,
    )

    analysis = _analysis(grid)
    if analysis["errors"]:
        raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["active_cols"] != active or analysis["max_stack"] != max_stack:
        raise AssertionError(
            "realized override drift: "
            f"active {analysis['active_cols']} != {active} or max_stack {analysis['max_stack']} != {max_stack}"
        )
    return grid
