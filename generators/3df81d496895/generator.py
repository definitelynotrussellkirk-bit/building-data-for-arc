"""Generate lessons for ``3df81d496895`` (recolor via a top legend).

Rows 0 and 1 form aligned source/target color pairs.  The output removes those
legend rows and recolors every body cell whose color appears in row 0.  The
canonical Racket rule leaves an unmapped nonzero body color unchanged, although
ordinary teaching scenes deliberately use only mapped source colors so every
legend entry is exercised and the intended operation is identifiable.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3df81d496895"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "313add7d0e0d"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read aligned nonzero pairs from the first two rows: row 0 is the source "
    "color and row 1 is its replacement. Remove those two rows, then recolor "
    "each remaining source-colored cell with its paired target color. "
    "Background remains 0; an unmapped nonzero color would remain unchanged."
)

INVARIANTS = [
    "background is literal color 0",
    "each legend column is either empty in both top rows or contains one source/target pair",
    "the legend has 2..4 distinct sources and equally many distinct targets",
    "source and target color sets are disjoint, so every exercised mapping changes color",
    "ordinary body cells use only legend source colors and exercise every mapping",
    "every ordinary draw places mapped body content in row 2, the first output row",
    "every declared override is exactly recoverable from the returned input grid",
    "the canonical Racket rule, not the Python mirror below, is output authority",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-biased draws",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-biased draws",
        "valid": "9..14",
    },
    "n_pairs": {
        "type": "int",
        "default": "scheduled canonical anchors plus difficulty-biased draws",
        "valid": "2..4",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Compact connected shapes.  All fit in the minimum 6-row body and 9-column grid.
_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in AXES:
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")


def _band_ranges(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 10), (9, 11), (2, 3)
    if difficulty == "hard":
        return (10, 14), (11, 14), (3, 4)
    return (9, 12), (10, 13), (2, 4)


def _draw_int_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: tuple[int, int],
    valid: tuple[int, int],
) -> int:
    """Use the full declared domain for an exact override in every band."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid[0], valid[1])
    return ctx.draw_int(name, default[0], default[1])


def _analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be non-empty"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be non-empty"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"errors": ["cells must be ARC integers 0..9"]}

    height = len(grid)
    if not 3 <= height <= 30 or not 1 <= width <= 30:
        errors.append(f"grid dimensions must be within ARC bounds, got {height}x{width}")
    if height < 3:
        return {"errors": errors}

    half_pairs = [
        col
        for col in range(width)
        if (grid[0][col] == 0) != (grid[1][col] == 0)
    ]
    if half_pairs:
        errors.append(f"legend has unpaired nonzero cells at columns {half_pairs}")

    legend_cols = [
        col
        for col in range(width)
        if grid[0][col] != 0 and grid[1][col] != 0
    ]
    sources = [grid[0][col] for col in legend_cols]
    targets = [grid[1][col] for col in legend_cols]
    if not 2 <= len(legend_cols) <= 4:
        errors.append(f"legend must contain 2..4 pairs, got {len(legend_cols)}")
    if len(set(sources)) != len(sources):
        errors.append("legend source colors must be distinct")
    if len(set(targets)) != len(targets):
        errors.append("legend target colors must be distinct")
    if set(sources) & set(targets):
        errors.append("legend source and target color sets must be disjoint")

    body_values = [value for row in grid[2:] for value in row if value != 0]
    body_colors = set(body_values)
    if not body_values:
        errors.append("body must contain nonzero cells")
    unknown = body_colors - set(sources)
    if unknown:
        errors.append(f"body contains unmapped color(s): {sorted(unknown)}")
    missing = set(sources) - body_colors
    if missing:
        errors.append(f"body does not exercise source color(s): {sorted(missing)}")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "legend_cols": legend_cols,
        "sources": sources,
        "targets": targets,
        "mapping": dict(zip(sources, targets)),
        "body_colors": body_colors,
        "body_values": body_values,
    }


def observe_overrides(grid: Any) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_pairs": len(analysis["legend_cols"]),
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Reject malformed, ambiguous, no-op, and rule-hiding teaching scenes."""
    errors = list(_analysis(grid)["errors"])
    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if not errors and requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and requested[name] != observed[name]:
                errors.append(
                    f"{name} drifted from requested {requested[name]!r} "
                    f"to {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    """The canonical manifold is exactly the clean paired-legend grammar."""
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests and rival analysis."""
    mapping: dict[int, int] = {}
    for source, target in zip(grid[0], grid[1]):
        if source != 0 and target != 0 and source not in mapping:
            mapping[source] = target
    return [
        [0 if value == 0 else mapping.get(value, value) for value in row]
        for row in grid[2:]
    ]


def _identity_crop(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid[2:]]


def _sorted_palette_map(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    sources = sorted(analysis.get("sources", []))
    targets = sorted(analysis.get("targets", []))
    mapping = dict(zip(sources, targets))
    return [
        [0 if value == 0 else mapping.get(value, value) for value in row]
        for row in grid[2:]
    ]


def _first_pair_only(grid: list[list[int]]) -> list[list[int]]:
    mapping: dict[int, int] = {}
    for source, target in zip(grid[0], grid[1]):
        if source != 0 and target != 0:
            mapping[source] = target
            break
    return [
        [0 if value == 0 else mapping.get(value, value) for value in row]
        for row in grid[2:]
    ]


def _skip_first_body_row(grid: list[list[int]]) -> list[list[int]]:
    return rule_mirror(grid)[1:]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_crop": _identity_crop,
    "sorted_palette_map": _sorted_palette_map,
    "first_pair_only": _first_pair_only,
    "skip_first_body_row": _skip_first_body_row,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness_non_identity(grid: list[list[int]]) -> bool:
    return rule_mirror(grid) != _identity_crop(grid)


def _witness_column_pairing(grid: list[list[int]]) -> bool:
    return rule_mirror(grid) != _sorted_palette_map(grid)


def _witness_all_mappings(grid: list[list[int]]) -> bool:
    return rule_mirror(grid) != _first_pair_only(grid)


def _witness_row_two_is_body(grid: list[list[int]]) -> bool:
    return bool(grid[2]) and any(value != 0 for value in grid[2])


SEMANTIC_WITNESSES = {
    "non_identity_recolor": _witness_non_identity,
    "column_pairing_required": _witness_column_pairing,
    "all_mappings_required": _witness_all_mappings,
    "row_two_is_body": _witness_row_two_is_body,
}
WITNESS_RIVALS = {
    "non_identity_recolor": ["identity_crop"],
    "column_pairing_required": ["sorted_palette_map"],
    "all_mappings_required": ["first_pair_only"],
    "row_two_is_body": ["skip_first_body_row"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject a lesson when a named wrong rule fits all demos but changes query."""
    reasons: list[str] = []
    all_pairs = [("demo", index, pair) for index, pair in enumerate(demos)] + [
        ("query", 0, query)
    ]
    for kind, index, pair in all_pairs:
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{kind} {index}: pair must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.extend(f"{kind} {index}: {error}" for error in errors)
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"{kind} {index}: output disagrees with the legend rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"competing rule survives demos: {name}")
    return reasons


def _legend_columns(rng, width: int, n_pairs: int) -> list[int]:
    """Choose non-contiguous legend columns so position is not a shortcut."""
    for _ in range(100):
        columns = sorted(rng.sample(range(width), n_pairs))
        if any(b - a > 1 for a, b in zip(columns, columns[1:])):
            return columns
    # The declared domains always make this fallback reachable and non-contiguous.
    return [round(index * (width - 1) / (n_pairs - 1)) for index in range(n_pairs)]


def _shape_cells(
    shape: tuple[tuple[int, int], ...], top: int, left: int
) -> tuple[tuple[int, int], ...]:
    return tuple((top + dr, left + dc) for dr, dc in shape)


def _can_place(
    grid: list[list[int]], cells: tuple[tuple[int, int], ...], *, gap: bool
) -> bool:
    height, width = len(grid), len(grid[0])
    for row, col in cells:
        if not (2 <= row < height and 0 <= col < width) or grid[row][col] != 0:
            return False
        if not gap:
            continue
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                neighbor_row, neighbor_col = row + dr, col + dc
                if not (2 <= neighbor_row < height and 0 <= neighbor_col < width):
                    continue
                if grid[neighbor_row][neighbor_col] != 0:
                    return False
    return True


def _place_shape(
    grid: list[list[int]], color: int, shape, rng, *, force_row_two: bool = False
) -> bool:
    height, width = len(grid), len(grid[0])
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    rows = [2] if force_row_two else list(range(2, height - shape_h + 1))
    columns = list(range(0, width - shape_w + 1))
    candidates = [(row, col) for row in rows for col in columns]
    rng.shuffle(candidates)
    for require_gap in (True, False):
        for top, left in candidates:
            cells = _shape_cells(shape, top, left)
            if not _can_place(grid, cells, gap=require_gap):
                continue
            for row, col in cells:
                grid[row][col] = color
            return True
    return False


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng(f"layout|{difficulty or 'medium'}")

    # Half of ordinary draws are exact public-profile anchors in every band.
    if not overrides and int(sample_index) % 4 in (0, 3):
        defaults = ((9, 9), (10, 10), (3, 3))
    else:
        defaults = _band_ranges(difficulty)

    height = _draw_int_axis(ctx, overrides, "grid_h", defaults[0], (8, 14))
    width = _draw_int_axis(ctx, overrides, "grid_w", defaults[1], (9, 14))
    n_pairs = _draw_int_axis(ctx, overrides, "n_pairs", defaults[2], (2, 4))

    grid = full_grid(height, width, 0)
    colors = rng.sample(range(1, 10), 2 * n_pairs)
    sources = sorted(colors[:n_pairs])
    target_pool = sorted(colors[n_pairs:])
    shift = 1 + rng.randrange(n_pairs - 1)
    mapping = {
        source: target_pool[(index + shift) % n_pairs]
        for index, source in enumerate(sources)
    }

    columns = _legend_columns(rng, width, n_pairs)
    source_order = rng.sample(sources, n_pairs)
    for col, source in zip(columns, source_order):
        grid[0][col] = source
        grid[1][col] = mapping[source]

    body_order = rng.sample(sources, n_pairs)
    for index, source in enumerate(body_order):
        shape = rng.choice(_SHAPES)
        if not _place_shape(
            grid,
            source,
            shape,
            rng,
            force_row_two=(index == 0),
        ):
            raise RuntimeError(f"unable to place required body shape for source {source}")

    extra_shapes = 0 if difficulty == "easy" else 2 if difficulty == "hard" else 1
    for _ in range(extra_shapes):
        source = rng.choice(sources)
        _place_shape(grid, source, rng.choice(_SHAPES), rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid scene: " + "; ".join(errors))
    return grid
