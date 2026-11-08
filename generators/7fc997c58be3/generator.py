"""Generator for ARC task 1e81d6f9 / content hash 7fc997c58be3.

The colour at zero-based coordinate ``(1, 1)`` is the target.  The output
replaces every *other* occurrence of that colour with background 0 and leaves
all remaining cells unchanged.

Version 4 replaces the old density/texture controls with exact, recoverable
axes.  Ordinary lessons deliberately include a target occurrence before the
marker and an adjacent target pair.  Those witnesses rule out the common
"keep the first occurrence", "erase only isolated copies", and
"erase only copies below the marker" shortcuts while two canonical-anchor
profiles retain the source task's 15x15, 9/10-colour envelope.
"""
from __future__ import annotations

import copy
from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7fc997c58be3"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "10ffeef3b427"

SUMMARY = (
    "Read target = input[1][1]. Replace every other cell equal to target with "
    "0; preserve (1,1), background, and every non-target colour exactly. "
    "Ordinary scenes schedule row, column, diagonal, connected-cluster, and "
    "disconnected-scattered target layouts, with canonical 15x15 anchors."
)

INVARIANTS = [
    "the grid is rectangular, at least 3x3, and uses integer colours 0..9",
    "the target colour at (1,1) is nonzero",
    "at least one target-colour copy occurs outside (1,1)",
    "background 0 and at least one non-target decoy colour are both present",
    "the output erases exactly the target copies outside (1,1)",
]

TARGET_LAYOUTS = ("scattered", "cluster", "row", "column", "diagonal")

# Every public axis is exact and recoverable from the returned grid through
# observe_overrides().  Boundary values are honored in every difficulty band.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile schedule with 15x15 canonical anchors",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile schedule with 15x15 canonical anchors",
        "valid": "10..18",
    },
    "target_color": {
        "type": "color",
        "default": "cyclic seeded nonzero colour",
        "valid": "1..9",
    },
    "n_target_copies": {
        "type": "int",
        "default": "scheduled 3..8 copies outside (1,1)",
        "valid": "3..8",
    },
    "palette_size": {
        "type": "int",
        "default": "scheduled 5..10 total colours including 0 and target",
        "valid": "5..10",
    },
    "decoy_count": {
        "type": "int",
        "default": "scheduled 20..48 non-target nonzero cells",
        "valid": "20..48",
    },
    "target_layout": {
        "type": "enum",
        "default": "five-profile schedule",
        "valid": "|".join(TARGET_LAYOUTS),
    },
}

# The complete declared boundary matrix fits even in a 10x10 grid:
# marker + 8 target copies + 48 decoys = 57 occupied cells.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_scattered",
    "canonical_cluster",
    "row_lesson",
    "column_lesson",
    "diagonal_lesson",
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.35


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic five-slot curriculum profile."""
    del difficulty
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            f"unknown override axis/axes: {unknown}; allowed={sorted(AXES)}"
        )


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    """Use the scheduled singleton normally and the full domain for overrides."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (int(scheduled),)))


def _draw_exact_color(ctx, label: str, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_color(label, exclude=(0,))
    return int(ctx.draw_choice(label, (int(scheduled),)))


def _draw_exact_choice(ctx, label: str, scheduled: str, options: tuple[str, ...]) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _scheduled_axes(
    profile: str, difficulty: str | None, seed: int, sample_index: int
) -> dict[str, int | str]:
    """Five profiles; the first two sit inside the canonical envelope."""
    target = 1 + ((int(seed) * 7 + int(sample_index)) % 9)
    if profile == "canonical_scattered":
        return {
            "grid_h": 15,
            "grid_w": 15,
            "target_color": target,
            "n_target_copies": 5,
            "palette_size": 9,
            "decoy_count": 29,
            "target_layout": "scattered",
        }
    if profile == "canonical_cluster":
        return {
            "grid_h": 15,
            "grid_w": 15,
            "target_color": target,
            "n_target_copies": 3,
            "palette_size": 10,
            "decoy_count": 20,
            "target_layout": "cluster",
        }

    band = difficulty or "medium"
    defaults = {
        "easy": {
            "row_lesson": (10, 12, 3, 5, 24),
            "column_lesson": (11, 10, 4, 6, 25),
            "diagonal_lesson": (12, 12, 4, 7, 28),
        },
        "medium": {
            "row_lesson": (13, 16, 5, 7, 32),
            "column_lesson": (16, 13, 6, 8, 34),
            "diagonal_lesson": (16, 16, 6, 9, 38),
        },
        "hard": {
            "row_lesson": (17, 18, 7, 8, 43),
            "column_lesson": (18, 17, 8, 9, 46),
            "diagonal_lesson": (18, 18, 8, 10, 48),
        },
    }
    h, w, copies, palette, decoys = defaults[band][profile]
    return {
        "grid_h": h,
        "grid_w": w,
        "target_color": target,
        "n_target_copies": copies,
        "palette_size": palette,
        "decoy_count": decoys,
        "target_layout": profile.removesuffix("_lesson"),
    }


def _target_positions(layout: str, h: int, w: int, n: int) -> list[tuple[int, int]]:
    """Construct an exact, unambiguously classifiable target layout.

    Every branch contains a target before (1,1) in row-major order and an
    8-neighbour target pair.  This is deliberate teaching evidence, not a
    requirement imposed on canonical inputs by self_check().
    """
    if layout == "row":
        positions = [(0, col) for col in range(n)]
    elif layout == "column":
        positions = [(row, 0) for row in range(n)]
    elif layout == "diagonal":
        positions = [(index, index + 2) for index in range(n)]
    elif layout == "cluster":
        positions = [
            (0, 3),
            (1, 3),
            (1, 4),
            (0, 4),
            (2, 3),
            (2, 4),
            (1, 5),
            (0, 5),
        ][:n]
    elif layout == "scattered":
        positions = [
            (0, 0),
            (0, 1),
            (h - 1, w - 1),
            (h - 1, 0),
            (0, w - 1),
            (h // 2, w // 2 + 2),
            (h // 2 + 2, w // 2 - 2),
            (h - 3, w // 2),
        ][:n]
    else:
        raise ValueError(f"unknown target layout {layout!r}")

    if len(positions) != n or len(set(positions)) != n:
        raise AssertionError(f"layout {layout!r} did not realize {n} unique cells")
    if any(not (0 <= row < h and 0 <= col < w) for row, col in positions):
        raise AssertionError(f"layout {layout!r} escaped the {h}x{w} grid")
    if (1, 1) in positions:
        raise AssertionError("target layout overlaps the protected marker")
    return positions


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty sequence of rows")
    rows: list[list[int]] = []
    width: int | None = None
    for row in grid:
        if isinstance(row, str):
            values = [int(ch) for ch in row.strip()]
        elif isinstance(row, (list, tuple)):
            values = []
            for value in row:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError("grid colours must be integers in 0..9")
                values.append(value)
        else:
            raise ValueError("every grid row must be a sequence")
        if width is None:
            width = len(values)
            if width == 0:
                raise ValueError("grid rows must be nonempty")
        elif len(values) != width:
            raise ValueError("grid must be rectangular")
        if any(value < 0 or value > 9 for value in values):
            raise ValueError("grid colours must be integers in 0..9")
        rows.append(values)
    return rows


def _connected8(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr, dc) == (0, 0):
                    continue
                nxt = (row + dr, col + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return seen == cells


def _classify_target_layout(cells: set[tuple[int, int]]) -> str:
    if not cells:
        raise ValueError("no target copies outside (1,1)")
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(rows) == 1:
        return "row"
    if len(cols) == 1:
        return "column"
    if len({row - col for row, col in cells}) == 1 or len(
        {row + col for row, col in cells}
    ) == 1:
        return "diagonal"
    if _connected8(cells):
        return "cluster"
    return "scattered"


def _analyze(grid: Any) -> dict[str, Any]:
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}

    h, w = len(values), len(values[0])
    errors: list[str] = []
    if h < 3 or w < 3:
        errors.append("grid must be at least 3x3")
        return {"errors": errors, "grid": values, "height": h, "width": w}

    target = values[1][1]
    if target == 0:
        errors.append("target at (1,1) must be nonzero")
    target_cells = {
        (row, col)
        for row in range(h)
        for col in range(w)
        if values[row][col] == target and (row, col) != (1, 1)
    }
    if not target_cells:
        errors.append("expected at least one target-colour copy outside (1,1)")
    decoy_cells = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if values[row][col] not in (0, target)
    ]
    if not decoy_cells:
        errors.append("expected at least one non-target decoy cell")
    if not any(value == 0 for row in values for value in row):
        errors.append("expected background colour 0")

    layout = _classify_target_layout(target_cells) if target_cells else None
    return {
        "errors": errors,
        "grid": values,
        "height": h,
        "width": w,
        "target": target,
        "target_cells": target_cells,
        "n_target_copies": len(target_cells),
        "decoy_cells": decoy_cells,
        "decoy_count": len(decoy_cells),
        "palette_size": len({value for row in values for value in row}),
        "target_layout": layout,
    }


def _analysis_or_raise(grid: Any) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid task grid: " + "; ".join(analysis["errors"]))
    return analysis


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = _scheduled_axes(profile, difficulty, seed, sample_index)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _draw_exact_int(ctx, "grid_h", int(scheduled["grid_h"]), 10, 18)
    w = _draw_exact_int(ctx, "grid_w", int(scheduled["grid_w"]), 10, 18)
    target = _draw_exact_color(ctx, "target_color", int(scheduled["target_color"]))
    copies = _draw_exact_int(
        ctx, "n_target_copies", int(scheduled["n_target_copies"]), 3, 8
    )
    palette_size = _draw_exact_int(
        ctx, "palette_size", int(scheduled["palette_size"]), 5, 10
    )
    decoy_count = _draw_exact_int(
        ctx, "decoy_count", int(scheduled["decoy_count"]), 20, 48
    )
    layout = _draw_exact_choice(
        ctx, "target_layout", str(scheduled["target_layout"]), TARGET_LAYOUTS
    )

    grid = full_grid(h, w, 0)
    grid[1][1] = target
    target_positions = _target_positions(layout, h, w, copies)
    for row, col in target_positions:
        grid[row][col] = target

    decoy_colours = list(
        ctx.draw_distinct_colors(
            "decoy_colours", n=palette_size - 2, exclude=(0, target)
        )
    )
    free = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if grid[row][col] == 0
    ]
    if decoy_count > len(free):
        raise ValueError(
            f"decoy_count={decoy_count} exceeds {len(free)} available cells"
        )
    cell_rng = ctx.draw_rng("decoy_cells")
    cell_rng.shuffle(free)
    selected = free[:decoy_count]

    # Exactly one singleton decoy refutes "erase the rarest colour".  Every
    # other non-modal decoy appears twice; the second colour takes the balance.
    assignments = [decoy_colours[0]]
    for colour in decoy_colours[2:]:
        assignments.extend((colour, colour))
    assignments.extend(
        [decoy_colours[1]] * (decoy_count - len(assignments))
    )
    if len(assignments) != decoy_count:
        raise AssertionError("decoy assignment cardinality mismatch")
    assignment_rng = ctx.draw_rng("decoy_assignments")
    assignment_rng.shuffle(assignments)
    for (row, col), colour in zip(selected, assignments):
        grid[row][col] = colour

    expected = {
        "grid_h": h,
        "grid_w": w,
        "target_color": target,
        "n_target_copies": copies,
        "palette_size": palette_size,
        "decoy_count": decoy_count,
        "target_layout": layout,
    }
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": expected},
    )
    if errors:
        raise AssertionError("generator contract failure: " + "; ".join(errors))
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = observe_overrides(grid)
    for axis, value in requested.items():
        if axis in AXES and observed.get(axis) != value:
            errors.append(
                f"meta {axis} requested {value!r}, observed {observed.get(axis)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis_or_raise(grid)
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "target_color": analysis["target"],
        "n_target_copies": analysis["n_target_copies"],
        "palette_size": analysis["palette_size"],
        "decoy_count": analysis["decoy_count"],
        "target_layout": analysis["target_layout"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    if analysis["height"] != 15 or analysis["width"] != 15:
        errors.append("canonical inputs are 15x15")
    if analysis["palette_size"] not in (9, 10):
        errors.append("canonical palette size is 9 or 10")
    if not 3 <= analysis["n_target_copies"] <= 5:
        errors.append("canonical target-copy count is 3..5 outside (1,1)")
    if not 20 <= analysis["decoy_count"] <= 34:
        errors.append("canonical decoy-cell count is 20..34")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Pure diagnostic mirror; canonical Racket remains output authority."""
    analysis = _analysis_or_raise(grid)
    target = analysis["target"]
    return [
        [
            0 if value == target and (row, col) != (1, 1) else value
            for col, value in enumerate(values)
        ]
        for row, values in enumerate(analysis["grid"])
    ]


def _target_neighbour_count(
    cells: set[tuple[int, int]], row: int, col: int
) -> int:
    return sum(
        (row + dr, col + dc) in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    )


def _rival_keep_first_target(grid):
    analysis = _analysis_or_raise(grid)
    values = copy.deepcopy(analysis["grid"])
    target = analysis["target"]
    target_cells = sorted(
        (row, col)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value == target
    )
    keep = target_cells[0]
    for row, col in target_cells[1:]:
        values[row][col] = 0
    values[keep[0]][keep[1]] = target
    return values


def _rival_erase_only_isolated_targets(grid):
    analysis = _analysis_or_raise(grid)
    values = copy.deepcopy(analysis["grid"])
    target = analysis["target"]
    all_targets = set(analysis["target_cells"]) | {(1, 1)}
    for row, col in analysis["target_cells"]:
        if _target_neighbour_count(all_targets, row, col) == 0:
            values[row][col] = 0
    values[1][1] = target
    return values


def _rival_erase_only_below_marker(grid):
    analysis = _analysis_or_raise(grid)
    target = analysis["target"]
    return [
        [0 if value == target and row > 1 else value for value in line]
        for row, line in enumerate(analysis["grid"])
    ]


def _frequency_colour_rival(grid, *, modal: bool):
    analysis = _analysis_or_raise(grid)
    values = copy.deepcopy(analysis["grid"])
    counts = Counter(value for row in values for value in row if value != 0)
    if modal:
        colour = max(counts, key=lambda value: (counts[value], -value))
    else:
        colour = min(counts, key=lambda value: (counts[value], value))
    cells = [
        (row, col)
        for row, line in enumerate(values)
        for col, value in enumerate(line)
        if value == colour
    ]
    for row, col in cells[1:]:
        values[row][col] = 0
    return values


def _rival_rarest_nonzero(grid):
    return _frequency_colour_rival(grid, modal=False)


def _rival_modal_nonzero(grid):
    return _frequency_colour_rival(grid, modal=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "keep_first_target_occurrence": _rival_keep_first_target,
    "erase_only_isolated_targets": _rival_erase_only_isolated_targets,
    "erase_only_below_marker": _rival_erase_only_below_marker,
    "erase_rarest_nonzero": _rival_rarest_nonzero,
    "erase_modal_nonzero": _rival_modal_nonzero,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis.get("errors") else analysis


def _layout_is(grid, layout: str) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["target_layout"] == layout


def _target_before_marker(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(cell < (1, 1) for cell in analysis["target_cells"])


def _adjacent_target_pair(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    cells = set(analysis["target_cells"])
    return any(_target_neighbour_count(cells, row, col) > 0 for row, col in cells)


def _unique_singleton_decoy(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    counts = Counter(
        analysis["grid"][row][col] for row, col in analysis["decoy_cells"]
    )
    return sum(count == 1 for count in counts.values()) == 1


def _non_target_modal(grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    counts = Counter(value for row in analysis["grid"] for value in row if value != 0)
    best = max(counts.values())
    return counts[analysis["target"]] < best and sum(count == best for count in counts.values()) == 1


SEMANTIC_WITNESSES = {
    "canonical_profile": lambda grid: strict_canonical_like(grid) == [],
    "scattered_target_layout": lambda grid: _layout_is(grid, "scattered"),
    "cluster_target_layout": lambda grid: _layout_is(grid, "cluster"),
    "row_target_layout": lambda grid: _layout_is(grid, "row"),
    "column_target_layout": lambda grid: _layout_is(grid, "column"),
    "diagonal_target_layout": lambda grid: _layout_is(grid, "diagonal"),
    "target_before_marker": _target_before_marker,
    "adjacent_target_pair": _adjacent_target_pair,
    "unique_singleton_decoy": _unique_singleton_decoy,
    "non_target_modal_colour": _non_target_modal,
}

# Each named witness makes a concrete, gate-verifiable disagreement claim.
WITNESS_RIVALS = {
    "canonical_profile": ["erase_only_isolated_targets"],
    "scattered_target_layout": ["erase_only_isolated_targets"],
    "cluster_target_layout": ["erase_only_isolated_targets"],
    "row_target_layout": ["erase_only_isolated_targets"],
    "column_target_layout": ["erase_only_isolated_targets"],
    "diagonal_target_layout": ["erase_only_isolated_targets"],
    "target_before_marker": [
        "keep_first_target_occurrence",
        "erase_only_below_marker",
    ],
    "adjacent_target_pair": ["erase_only_isolated_targets"],
    "unique_singleton_decoy": ["erase_rarest_nonzero"],
    "non_target_modal_colour": ["erase_modal_nonzero"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    pairs = [*demos, query]
    normalized_outputs: list[list[list[int]] | None] = []
    for index, pair in enumerate(pairs):
        label = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} is not an input/output pair")
            normalized_outputs.append(None)
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"{label} input violates teaching grammar: {structural[0]}")
            normalized_outputs.append(None)
            continue
        try:
            output = _coerce_grid(pair["output"])
        except (TypeError, ValueError) as exc:
            reasons.append(f"{label} output is invalid: {exc}")
            normalized_outputs.append(None)
            continue
        if rule_mirror(pair["input"]) != output:
            reasons.append(f"{label} output disagrees with the (1,1)-target rule")
        normalized_outputs.append(output)
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == normalized_outputs[index]
            for index, demo in enumerate(demos)
        )
        query_output = normalized_outputs[-1]
        if survives and competitor(query["input"]) != query_output:
            reasons.append(
                f"competing rule {name!r} fits every demo but answers the query differently"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed near-misses that self_check must reject."""
    base = generate(73129, 0, difficulty="medium")
    target = base[1][1]

    target_zero = copy.deepcopy(base)
    target_zero[1][1] = 0

    no_duplicates = copy.deepcopy(base)
    for row in range(len(no_duplicates)):
        for col in range(len(no_duplicates[0])):
            if (row, col) != (1, 1) and no_duplicates[row][col] == target:
                no_duplicates[row][col] = 0

    no_decoys = copy.deepcopy(base)
    for row in range(len(no_decoys)):
        for col in range(len(no_decoys[0])):
            if no_decoys[row][col] not in (0, target):
                no_decoys[row][col] = 0

    no_background = copy.deepcopy(base)
    filler = next(
        value for row in no_background for value in row if value not in (0, target)
    )
    for row in range(len(no_background)):
        for col in range(len(no_background[0])):
            if no_background[row][col] == 0:
                no_background[row][col] = filler

    invalid_colour = copy.deepcopy(base)
    invalid_colour[0][0] = 10

    ragged = copy.deepcopy(base)
    ragged[-1] = ragged[-1][:-1]

    return [
        ("zero_target_marker", target_zero),
        ("missing_target_duplicates", no_duplicates),
        ("missing_non_target_decoys", no_decoys),
        ("missing_background", no_background),
        ("colour_outside_arc_palette", invalid_colour),
        ("nonrectangular_grid", ragged),
    ]
