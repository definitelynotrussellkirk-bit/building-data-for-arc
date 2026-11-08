"""Generator for ``arc_additional_puzzles_21_set11_bundle:E71``.

For every non-background color that occurs exactly twice, connect its two
markers when they share a row or a column.  Colors with one marker, three
markers, or two diagonal markers are deliberate controls and remain unchanged.

The sampler keeps the canonical scale in every difficulty band.  Four
consecutive samples form a compact teaching cycle: a canonical-profile scene,
a diagonal-pair control, a three-marker count control, and a singleton control.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c83b29b14c16"
TASK_ID = "c83b29b14c16"
VERSION = "2.0.0"
RULE_HASH = "d264380c5850"

SUMMARY = (
    "On a 0-background grid, each color occurring exactly twice is joined "
    "inclusively when its two cells share a row or column. Singleton colors, "
    "three-cell colors, and diagonal pairs are unchanged controls."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid dimensions are 7..10 in each direction",
    "there are exactly two or three aligned exact-two color pairs",
    "aligned pairs use both horizontal and vertical orientations",
    "aligned endpoints have at least one blank cell between them",
    "at most one singleton, diagonal pair, and aligned triple are present",
    "all active connector spans are disjoint and have blank interiors",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "7..10"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "7..10"},
    "n_pairs": {"type": "int", "default": "difficulty-aware 2..3", "valid": "2..3"},
    "n_singletons": {"type": "int", "default": "teaching-cycle 0..1", "valid": "0..1"},
    "n_diagonal_pairs": {"type": "int", "default": "teaching-cycle 0..1", "valid": "0..1"},
    "n_triples": {"type": "int", "default": "teaching-cycle 0..1", "valid": "0..1"},
    "n_short_pairs": {"type": "int", "default": "1", "valid": "0..1"},
}

# Every cross product of the advertised domains is constructively supported,
# including the maximum combination on a 7x7 grid.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_CANONICAL_SIZES = ((7, 7), (8, 8), (9, 9), (8, 9), (9, 10))
_AXIS_RANGES = {
    "grid_h": (7, 10),
    "grid_w": (7, 10),
    "n_pairs": (2, 3),
    "n_singletons": (0, 1),
    "n_diagonal_pairs": (0, 1),
    "n_triples": (0, 1),
    "n_short_pairs": (0, 1),
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _draw_axis_int(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    """Draw an exact axis, using its full domain for caller overrides."""
    lo, hi = _AXIS_RANGES[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _default_size(ctx, overrides: dict[str, Any]) -> tuple[int, int]:
    """Anchor ordinary draws to one of the five exact canonical profiles."""
    if "grid_h" in overrides or "grid_w" in overrides:
        # A partial dimension override still gets an independently lawful
        # counterpart; exact-profile scheduling is only an ordinary-draw goal.
        default_h, default_w = _CANONICAL_SIZES[
            ctx.draw_rng("size_profile").randrange(len(_CANONICAL_SIZES))
        ]
    else:
        default_h, default_w = ctx.draw_rng("size_profile").choice(_CANONICAL_SIZES)
    return (
        _draw_axis_int(ctx, overrides, "grid_h", default_h),
        _draw_axis_int(ctx, overrides, "grid_w", default_w),
    )


def _default_pair_count(difficulty: Any, sample_index: int) -> int:
    if difficulty == "easy":
        return 2
    if difficulty == "hard":
        return 3
    return 2 + (sample_index % 2)


def _transform_cell(cell: tuple[int, int], transform: int) -> tuple[int, int]:
    """Apply one of the eight D4 transforms to a coordinate in a 7x7 tile."""
    r, c = cell
    if transform >= 4:
        c = 6 - c
    for _ in range(transform % 4):
        r, c = c, 6 - r
    return r, c


def _layout_groups(
    n_pairs: int,
    n_singletons: int,
    n_diagonal_pairs: int,
    n_triples: int,
    n_short_pairs: int,
) -> list[tuple[tuple[int, int], ...]]:
    """Return disjoint marker groups in a universal 7x7 teaching tile.

    Full connector spans and the distractor control regions are disjoint even
    for the maximum advertised combination.  Subsets therefore remain valid
    without rejection sampling or silently shortened counts.
    """
    first_end = 2 if n_short_pairs else 4
    aligned = [
        ((0, 0), (0, first_end)),   # horizontal; the only optional short pair
        ((0, 6), (3, 6)),           # vertical; odd span defeats parity shortcut
        ((6, 0), (6, 4)),           # horizontal
    ][:n_pairs]
    groups: list[tuple[tuple[int, int], ...]] = list(aligned)
    if n_singletons:
        groups.append(((4, 5),))
    if n_diagonal_pairs:
        groups.append(((3, 1), (5, 4)))  # skew, not only a 45-degree diagonal
    if n_triples:
        groups.append(((2, 0), (2, 2), (2, 4)))
    return groups


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h, w = _default_size(ctx, overrides)
    mode = sample_index % 4
    n_pairs = _draw_axis_int(
        ctx, overrides, "n_pairs", _default_pair_count(difficulty, sample_index)
    )
    n_singletons = _draw_axis_int(ctx, overrides, "n_singletons", int(mode == 3))
    n_diagonal_pairs = _draw_axis_int(
        ctx, overrides, "n_diagonal_pairs", int(mode == 1)
    )
    n_triples = _draw_axis_int(ctx, overrides, "n_triples", int(mode == 2))
    n_short_pairs = _draw_axis_int(ctx, overrides, "n_short_pairs", 1)

    groups = _layout_groups(
        n_pairs,
        n_singletons,
        n_diagonal_pairs,
        n_triples,
        n_short_pairs,
    )
    colors = ctx.draw_rng("colors").sample(range(1, 10), len(groups))
    transform = ctx.draw_rng("layout_transform").randrange(8)
    row_offset = ctx.draw_rng("row_offset").randrange(h - 7 + 1)
    col_offset = ctx.draw_rng("col_offset").randrange(w - 7 + 1)

    grid = full_grid(h, w, 0)
    for color, group in zip(colors, groups):
        for cell in group:
            r, c = _transform_cell(cell, transform)
            grid[row_offset + r][col_offset + c] = color

    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_pairs": n_pairs,
        "n_singletons": n_singletons,
        "n_diagonal_pairs": n_diagonal_pairs,
        "n_triples": n_triples,
        "n_short_pairs": n_short_pairs,
    }
    observed = observe_overrides(grid)
    if observed != expected:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError(
            f"generated scene lost exact axes: expected {expected}, observed {observed}"
        )
    errors = self_check(grid)
    if errors:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError("generated invalid terminal-link scene: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"], len(grid), 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"], len(grid), width
    errors: list[str] = []
    if not 7 <= len(grid) <= 10 or not 7 <= width <= 10:
        errors.append(f"grid dimensions {len(grid)}x{width} outside 7..10")
    bad = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if type(value) is not int or not 0 <= value <= 9
        }
    )
    if bad:
        errors.append("cells must be integer ARC colors 0..9; found " + ", ".join(bad[:5]))
    return errors, len(grid), width


def _line_cells(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    (r1, c1), (r2, c2) = a, b
    if r1 == r2:
        return tuple((r1, c) for c in range(min(c1, c2), max(c1, c2) + 1))
    if c1 == c2:
        return tuple((r, c1) for r in range(min(r1, r2), max(r1, r2) + 1))
    return ()


def semantic_observables(grid) -> dict[str, Any]:
    errors, h, w = _basic_grid_errors(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n_pairs": 0,
        "n_singletons": 0,
        "n_diagonal_pairs": 0,
        "n_triples": 0,
        "n_short_pairs": 0,
        "orientations": set(),
        "active_spans": [],
    }
    if errors and (not h or not w or any("ragged" in error for error in errors)):
        return result
    if errors and any("cells must" in error for error in errors):
        return result

    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    if not positions:
        errors.append("no non-background colors")
        return result

    active: list[tuple[int, tuple[int, int], tuple[int, int], tuple[tuple[int, int], ...]]] = []
    for color, cells in sorted(positions.items()):
        if len(cells) == 1:
            result["n_singletons"] += 1
            continue
        if len(cells) == 2:
            a, b = cells
            span = _line_cells(a, b)
            if not span:
                result["n_diagonal_pairs"] += 1
                continue
            distance = len(span) - 1
            if distance < 2:
                errors.append(f"color {color} aligned endpoints are adjacent")
                continue
            result["n_pairs"] += 1
            if distance == 2:
                result["n_short_pairs"] += 1
            orientation = "horizontal" if a[0] == b[0] else "vertical"
            result["orientations"].add(orientation)
            active.append((color, a, b, span))
            continue
        if len(cells) == 3:
            same_row = len({r for r, _ in cells}) == 1
            same_col = len({c for _, c in cells}) == 1
            if not (same_row or same_col):
                errors.append(f"color {color} has three non-collinear cells")
                continue
            coordinates = sorted(c for _, c in cells) if same_row else sorted(r for r, _ in cells)
            if coordinates[-1] - coordinates[0] < 4:
                errors.append(f"color {color} triple has no visible interior gaps")
                continue
            result["n_triples"] += 1
            continue
        errors.append(f"color {color} has {len(cells)} cells; expected 1, 2, or 3")

    limits = {
        "n_pairs": (2, 3),
        "n_singletons": (0, 1),
        "n_diagonal_pairs": (0, 1),
        "n_triples": (0, 1),
        "n_short_pairs": (0, 1),
    }
    for name, (lo, hi) in limits.items():
        value = result[name]
        if not lo <= value <= hi:
            errors.append(f"{name}={value} outside [{lo}, {hi}]")
    if result["orientations"] != {"horizontal", "vertical"}:
        errors.append("aligned pairs must cover both horizontal and vertical orientations")

    spans: list[set[tuple[int, int]]] = []
    for color, a, b, span_tuple in active:
        span = set(span_tuple)
        endpoints = {a, b}
        for r, c in span - endpoints:
            if grid[r][c] != 0:
                errors.append(f"color {color} connector interior is not blank at {(r, c)}")
        if any(span & other for other in spans):
            errors.append(f"color {color} connector span intersects another connector span")
        spans.append(span)
    result["active_spans"] = [tuple(sorted(span)) for span in spans]
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked input grammar and any requested exact axes."""
    observations = semantic_observables(grid)
    errors = list(observations["errors"])
    requested = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    for name, wanted in requested.items():
        if name in AXES and wanted is not None and observations.get(name) != wanted:
            errors.append(
                f"requested {name}={wanted}, observed {observations.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws stay on the declared task manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    observations = semantic_observables(grid)
    if observations["errors"]:
        raise ValueError(
            "cannot observe axes from invalid scene: " + "; ".join(observations["errors"])
        )
    return {name: int(observations[name]) for name in AXES}


def _positions_by_color(grid) -> dict[int, list[tuple[int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))
    return positions


def _paint_line(out, color: int, a: tuple[int, int], b: tuple[int, int]) -> None:
    for r, c in _line_cells(a, b):
        out[r][c] = color


def rule_mirror(grid):
    """Test-only Python mirror; canonical Racket remains output authority."""
    if self_check(grid):
        raise ValueError("rule_mirror requires a lawful terminal-link input")
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) == 2 and _line_cells(cells[0], cells[1]):
            _paint_line(out, color, cells[0], cells[1])
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _skip_short_pairs(grid):
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        span = _line_cells(cells[0], cells[1])
        if span and len(span) - 1 >= 3:
            _paint_line(out, color, cells[0], cells[1])
    return out


def _connect_aligned_extrema_any_count(grid):
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) < 2:
            continue
        if len({r for r, _ in cells}) == 1:
            row = cells[0][0]
            _paint_line(out, color, (row, min(c for _, c in cells)), (row, max(c for _, c in cells)))
        elif len({c for _, c in cells}) == 1:
            col = cells[0][1]
            _paint_line(out, color, (min(r for r, _ in cells), col), (max(r for r, _ in cells), col))
    return out


def _connect_exact_pair_bbox(grid):
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r][c] = color
    return out


def _skip_45_degree_pairs_box_other_pairs(grid):
    """Wrong rule retained from review: only 45-degree pairs are ignored."""
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        if abs(r1 - r2) == abs(c1 - c2):
            continue
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r][c] = color
    return out


def _horizontal_only(grid):
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) == 2 and cells[0][0] == cells[1][0]:
            _paint_line(out, color, cells[0], cells[1])
    return out


def _vertical_only(grid):
    out = [list(row) for row in grid]
    for color, cells in _positions_by_color(grid).items():
        if len(cells) == 2 and cells[0][1] == cells[1][1]:
            _paint_line(out, color, cells[0], cells[1])
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _identity,
    "skip one-gap pairs": _skip_short_pairs,
    "connect aligned extrema regardless of count": _connect_aligned_extrema_any_count,
    "connect every exact pair bounding box": _connect_exact_pair_bbox,
    "skip 45-degree pairs, box-fill other exact pairs": _skip_45_degree_pairs_box_other_pairs,
    "horizontal pairs only": _horizontal_only,
    "vertical pairs only": _vertical_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# These two wrong rules reproduce all five canonical pairs.  Generated controls
# are therefore necessary to distinguish them from the selected authority.
CANONICAL_SHORTCUTS = {
    "connect aligned extrema regardless of count": _connect_aligned_extrema_any_count,
    "connect every exact pair bounding box": _connect_exact_pair_bbox,
}


def _valid_observations(grid) -> dict[str, Any] | None:
    observations = semantic_observables(grid)
    return None if observations["errors"] else observations


def _connection_fires(grid) -> bool:
    return _valid_observations(grid) is not None and rule_mirror(grid) != _identity(grid)


def _has_short_pair(grid) -> bool:
    observations = _valid_observations(grid)
    return bool(observations and observations["n_short_pairs"])


def _has_triple_control(grid) -> bool:
    observations = _valid_observations(grid)
    return bool(observations and observations["n_triples"])


def _has_diagonal_control(grid) -> bool:
    observations = _valid_observations(grid)
    return bool(observations and observations["n_diagonal_pairs"])


def _has_skew_diagonal_control(grid) -> bool:
    for cells in _positions_by_color(grid).values():
        if len(cells) != 2:
            continue
        (r1, c1), (r2, c2) = cells
        dr, dc = abs(r1 - r2), abs(c1 - c2)
        if dr and dc and dr != dc:
            return True
    return False


def _has_both_orientations(grid) -> bool:
    observations = _valid_observations(grid)
    return bool(observations and observations["orientations"] == {"horizontal", "vertical"})


SEMANTIC_WITNESSES = {
    "connection_fires": _connection_fires,
    "one-gap_pair": _has_short_pair,
    "exactly_two_count_control": _has_triple_control,
    "row_or_column_alignment_control": _has_diagonal_control,
    "skew_nonalignment_control": _has_skew_diagonal_control,
    "both_orientations": _has_both_orientations,
}
WITNESS_RIVALS = {
    "connection_fires": ["identity"],
    "one-gap_pair": ["skip one-gap pairs"],
    "exactly_two_count_control": ["connect aligned extrema regardless of count"],
    "row_or_column_alignment_control": ["connect every exact pair bounding box"],
    "skew_nonalignment_control": ["skip 45-degree pairs, box-fill other exact pairs"],
    "both_orientations": ["horizontal pairs only", "vertical pairs only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a named rival viable."""
    errors: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is unlawful: " + "; ".join(query_errors)]
    truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        demo_errors = self_check(demo_input)
        if demo_errors:
            errors.append(f"demo {index} input is unlawful: {'; '.join(demo_errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            errors.append(f"demo {index} output disagrees with the exact-two alignment rule")
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != truth:
                errors.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return errors
