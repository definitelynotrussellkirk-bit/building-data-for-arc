"""Generator for arc_puzzle_bank_twentythird21:E161.

Canonical rule: each row is handled independently.  When a row contains one
maroon (9) anchor, every other nonzero cell in that row is copied to its
reflection across the anchor; originals remain.  Rows without a 9 are left
unchanged.

The curriculum deliberately includes sources on both sides of row-local
anchors, non-full-height anchor patterns, varied anchor columns, and occasional
colored rows without anchors.  These witnesses refute the old full-column,
left-to-right-only interpretation while remaining exactly executable by the
canonical Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71f7823f30a3"
VERSION = "3.0.0"  # row-local bidirectional semantics + exact observable axes
TASK_ID = "71f7823f30a3"
RULE_HASH = "2f1f3e5388a0"

SUMMARY = (
    "A 0-background grid has two or more rows containing exactly one maroon "
    "(9) anchor and at least one colored source. Each anchored row is solved "
    "independently: every nonzero non-9 source is copied to the equally distant "
    "cell on the opposite side of that row's 9, preserving the source. Sources "
    "occur on both sides across every generated grid. At least one row has no "
    "anchor, so the 9s never form a full-height divider; some such rows contain "
    "colored pass-through distractors that must remain unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and colors are integers 0..9",
    "each anchored row contains exactly one color-9 anchor",
    "at least two anchored rows and at least one unanchored row are present",
    "every anchored row has a source whose reflected target is in-bounds and empty",
    "the grid contains anchored sources on both the left and right of row-local anchors",
    "the color-9 anchors do not form a full-height divider column",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 4..10",
        "valid": "4..10",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 7..15",
        "valid": "7..15",
    },
    "n_anchor_rows": {
        "type": "int",
        "default": "difficulty-weighted, leaving >=1 unanchored row",
        "valid": "2..3",
    },
    "source_count": {
        "type": "int",
        "default": "difficulty/profile/capacity constrained",
        "valid": "4..5",
    },
    "anchor_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "shared|varied",
    },
    "side_balance": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "left_heavy|right_heavy",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "warm|cool|mixed",
    },
    "orphan_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "empty|colored",
    },
}

_ANCHOR_PROFILES = ("varied", "shared", "varied")
_SIDE_BALANCES = ("left_heavy", "right_heavy", "left_heavy")
_PALETTE_KINDS = ("warm", "cool", "mixed")
_ORPHAN_PROFILES = ("colored", "empty", "colored")
_WARM = (1, 2, 4, 7)
_COOL = (3, 5, 6, 8)
_DIFFICULTIES = (None, "easy", "medium", "hard")


def _grid_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list"
    if isinstance(grid[0], str):
        width = len(grid[0])
        if width == 0 or any(not isinstance(row, str) or len(row) != width for row in grid):
            return "grid must be rectangular"
        if any(not value.isdigit() for row in grid for value in row):
            return "string rows must contain digits only"
        return None
    if not isinstance(grid[0], list) or not grid[0]:
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid colors must be integers in 0..9"
    return None


def _as_int_grid(grid) -> list[list[int]]:
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _palette_kind(colors: set[int]) -> str | None:
    if not colors:
        return None
    if colors <= set(_WARM):
        return "warm"
    if colors <= set(_COOL):
        return "cool"
    if colors <= set(_WARM + _COOL) and colors & set(_WARM) and colors & set(_COOL):
        return "mixed"
    return None


def _analyze_grid(grid) -> dict:
    analysis: dict = {"errors": []}
    error = _grid_error(grid)
    if error:
        analysis["errors"].append(error)
        return analysis

    grid = _as_int_grid(grid)
    height, width = len(grid), len(grid[0])
    analysis.update({"grid": grid, "grid_h": height, "grid_w": width})
    if not (4 <= height <= 10 and 7 <= width <= 15):
        analysis["errors"].append("grid dimensions must be h=4..10 and w=7..15")

    anchored: list[dict] = []
    orphan_colors: set[int] = set()
    left_count = 0
    right_count = 0
    all_source_colors: set[int] = set()

    for row_index, row in enumerate(grid):
        anchors = [column for column, value in enumerate(row) if value == 9]
        if len(anchors) > 1:
            analysis["errors"].append(
                f"row {row_index} has {len(anchors)} color-9 anchors; expected at most one"
            )
            continue
        if not anchors:
            orphan_colors.update(value for value in row if value not in (0, 9))
            continue

        anchor = anchors[0]
        sources = []
        row_left = 0
        row_right = 0
        for column, value in enumerate(row):
            if value in (0, 9):
                continue
            mirror_column = 2 * anchor - column
            sources.append((column, value, mirror_column))
            all_source_colors.add(value)
            if column < anchor:
                row_left += 1
                left_count += 1
            else:
                row_right += 1
                right_count += 1
            if not 0 <= mirror_column < width:
                analysis["errors"].append(
                    f"row {row_index} source at column {column} mirrors out of bounds"
                )
            elif row[mirror_column] != 0:
                analysis["errors"].append(
                    f"row {row_index} source at column {column} has nonempty mirror target"
                )
        if not sources:
            analysis["errors"].append(f"anchored row {row_index} has no colored source")
        anchored.append(
            {
                "row": row_index,
                "anchor": anchor,
                "sources": tuple(sources),
                "left": row_left,
                "right": row_right,
            }
        )

    if len(anchored) < 2:
        analysis["errors"].append("expected at least two anchored rows")
    if len(anchored) >= height:
        analysis["errors"].append("expected at least one row without a color-9 anchor")
    source_count = left_count + right_count
    if source_count < 4:
        analysis["errors"].append("expected at least four anchored source cells")
    if left_count == 0 or right_count == 0:
        analysis["errors"].append(
            "expected anchored source cells on both sides of row-local anchors"
        )
    if len(all_source_colors) < 2:
        analysis["errors"].append("expected at least two distinct anchored source colors")

    anchor_columns = [item["anchor"] for item in anchored]
    anchor_profile = None
    if anchor_columns:
        anchor_profile = "shared" if len(set(anchor_columns)) == 1 else "varied"

    side_balance = None
    if source_count:
        if left_count > right_count:
            side_balance = "left_heavy"
        elif right_count > left_count:
            side_balance = "right_heavy"
        else:
            side_balance = "balanced"

    palette_kind = _palette_kind(all_source_colors | orphan_colors)
    if palette_kind is None and (all_source_colors or orphan_colors):
        analysis["errors"].append("nonzero non-9 colors must come from palette 1..8")

    analysis.update(
        {
            "anchored": tuple(anchored),
            "n_anchor_rows": len(anchored),
            "source_count": source_count,
            "left_count": left_count,
            "right_count": right_count,
            "anchor_profile": anchor_profile,
            "side_balance": side_balance,
            "palette_kind": palette_kind,
            "orphan_profile": "colored" if orphan_colors else "empty",
            "source_colors": tuple(sorted(all_source_colors)),
            "orphan_colors": tuple(sorted(orphan_colors)),
        }
    )
    return analysis


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed/shortcut-hiding lessons."""
    return list(_analyze_grid(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared semantic axis from the returned input grid."""
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError(
            "cannot observe overrides on invalid grid: " + "; ".join(analysis["errors"])
        )
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_anchor_rows": analysis["n_anchor_rows"],
        "source_count": analysis["source_count"],
        "anchor_profile": analysis["anchor_profile"],
        "side_balance": analysis["side_balance"],
        "palette_kind": analysis["palette_kind"],
        "orphan_profile": analysis["orphan_profile"],
    }


def _draw_int(ctx, label: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]):
    bounds = full_bounds if ctx.overrides.get(label) is not None else default_bounds
    return ctx.draw_int(label, *bounds)


def _scheduled_choice(ctx, label: str, schedule: tuple[str, ...], all_options: tuple[str, ...]):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, all_options)
    value = schedule[ctx.sample_index % len(schedule)]
    return ctx.draw_choice(label, (value,))


def _band_bounds(difficulty):
    if difficulty == "easy":
        return {
            "grid_h": (4, 6),
            "grid_w": (7, 9),
            "n_anchor_rows": (2, 2),
            "source_count": (4, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (7, 10),
            "grid_w": (11, 15),
            "n_anchor_rows": (3, 3),
            "source_count": (5, 5),
        }
    return {
        "grid_h": (5, 8),
        "grid_w": (9, 12),
        "n_anchor_rows": (2, 3),
        "source_count": (4, 5),
    }


def _choose_anchor_columns(width: int, count: int, profile: str, rng) -> list[int]:
    # Avoid edge anchors on normal draws so each row has multiple pair slots;
    # width>=7 guarantees at least columns 2..w-3.
    candidates = list(range(2, width - 2))
    if not candidates:
        raise ValueError(f"grid width {width} has no supported anchor columns")
    ranked = sorted(
        candidates,
        key=lambda column: (min(column, width - 1 - column), rng.random()),
        reverse=True,
    )
    if profile == "shared":
        return [ranked[0]] * count
    if profile != "varied":
        raise ValueError(f"unknown anchor_profile {profile!r}")
    if count < 2 or len(candidates) < 2:
        raise ValueError("varied anchor_profile requires >=2 rows and >=2 anchor columns")
    columns = [ranked[0], ranked[1]]
    columns.extend(rng.choice(ranked) for _ in range(count - 2))
    rng.shuffle(columns)
    return columns


def _source_side_counts(profile: str, count: int) -> tuple[int, int]:
    if count < 4:
        raise ValueError(f"{profile} side_balance requires source_count >= 4")
    if profile == "left_heavy":
        left = count // 2 + 1
        return left, count - left
    if profile == "right_heavy":
        right = count // 2 + 1
        return count - right, right
    raise ValueError(f"unknown side_balance {profile!r}")


def _source_colors(kind: str, count: int, rng) -> list[int]:
    if kind == "warm":
        colors = [rng.choice(_WARM) for _ in range(count)]
        colors[0], colors[1] = rng.sample(_WARM, 2)
        return colors
    if kind == "cool":
        colors = [rng.choice(_COOL) for _ in range(count)]
        colors[0], colors[1] = rng.sample(_COOL, 2)
        return colors
    if kind == "mixed":
        colors = [rng.choice(_WARM + _COOL) for _ in range(count)]
        colors[0] = rng.choice(_WARM)
        colors[1] = rng.choice(_COOL)
        rng.shuffle(colors)
        return colors
    raise ValueError(f"unknown palette_kind {kind!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    bounds = _band_bounds(difficulty)
    height = _draw_int(ctx, "grid_h", bounds["grid_h"], (4, 10))
    width = _draw_int(ctx, "grid_w", bounds["grid_w"], (7, 15))

    anchor_hi = min(3, height - 1)
    default_anchor_hi = min(bounds["n_anchor_rows"][1], anchor_hi)
    default_anchor_lo = min(bounds["n_anchor_rows"][0], default_anchor_hi)
    n_anchor_rows = _draw_int(
        ctx,
        "n_anchor_rows",
        (default_anchor_lo, default_anchor_hi),
        (2, anchor_hi),
    )

    anchor_profile = _scheduled_choice(
        ctx, "anchor_profile", _ANCHOR_PROFILES, ("shared", "varied")
    )
    side_balance = _scheduled_choice(
        ctx,
        "side_balance",
        _SIDE_BALANCES,
        ("left_heavy", "right_heavy"),
    )
    palette_kind = _scheduled_choice(
        ctx, "palette_kind", _PALETTE_KINDS, ("warm", "cool", "mixed")
    )
    orphan_profile = _scheduled_choice(
        ctx, "orphan_profile", _ORPHAN_PROFILES, ("empty", "colored")
    )

    row_rng = ctx.draw_rng("anchor_rows")
    anchor_rows = sorted(row_rng.sample(range(height), n_anchor_rows))
    anchor_columns = _choose_anchor_columns(
        width, n_anchor_rows, anchor_profile, ctx.draw_rng("anchor_columns")
    )
    anchors = dict(zip(anchor_rows, anchor_columns))

    pair_slots: list[tuple[int, int]] = []
    slots_by_row: dict[int, list[tuple[int, int]]] = {}
    for row in anchor_rows:
        anchor = anchors[row]
        span = min(anchor, width - 1 - anchor)
        row_slots = [(row, distance) for distance in range(1, span + 1)]
        if not row_slots:
            raise ValueError(f"row {row} anchor {anchor} has no in-bounds mirror pair")
        slots_by_row[row] = row_slots
        pair_slots.extend(row_slots)

    source_lo = max(4, n_anchor_rows, bounds["source_count"][0])
    source_hi = min(5, len(pair_slots), bounds["source_count"][1])
    if ctx.overrides.get("source_count") is not None:
        source_lo = max(4, n_anchor_rows)
        source_hi = min(5, len(pair_slots))
    allowed_counts = list(range(source_lo, source_hi + 1))
    if not allowed_counts:
        raise ValueError(
            "no source_count satisfies grid capacity, anchor coverage, and side_balance"
        )
    source_count = ctx.draw_choice("source_count", tuple(allowed_counts))
    left_count, right_count = _source_side_counts(side_balance, source_count)

    slot_rng = ctx.draw_rng("source_slots")
    selected_slots = [slot_rng.choice(slots_by_row[row]) for row in anchor_rows]
    remaining_slots = [slot for slot in pair_slots if slot not in set(selected_slots)]
    selected_slots.extend(slot_rng.sample(remaining_slots, source_count - len(selected_slots)))
    slot_rng.shuffle(selected_slots)

    sides = ["left"] * left_count + ["right"] * right_count
    side_rng = ctx.draw_rng("source_sides")
    side_rng.shuffle(sides)
    colors = _source_colors(palette_kind, source_count, ctx.draw_rng("source_colors"))

    grid = full_grid(height, width, 0)
    for row, anchor in anchors.items():
        grid[row][anchor] = 9
    for (row, distance), side, color in zip(selected_slots, sides, colors):
        anchor = anchors[row]
        column = anchor - distance if side == "left" else anchor + distance
        grid[row][column] = color

    if orphan_profile == "colored":
        orphan_rows = [row for row in range(height) if row not in anchors]
        orphan_rng = ctx.draw_rng("orphans")
        orphan_count = min(len(orphan_rows) + 1, 3)
        orphan_palette = _WARM if palette_kind == "warm" else _COOL if palette_kind == "cool" else _WARM + _COOL
        for index in range(orphan_count):
            row = orphan_rows[index % len(orphan_rows)]
            empty_columns = [column for column, value in enumerate(grid[row]) if value == 0]
            column = orphan_rng.choice(empty_columns)
            grid[row][column] = orphan_rng.choice(orphan_palette)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_anchor_rows": n_anchor_rows,
        "source_count": source_count,
        "anchor_profile": anchor_profile,
        "side_balance": side_balance,
        "palette_kind": palette_kind,
        "orphan_profile": orphan_profile,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid
