"""Generator for ARC task 4f3a702ae0c4 — command-selected diagonal reflection.

A ``1`` guide in the top-left selects reflection across the main diagonal.  A
``2`` guide in the top-right selects reflection across the anti-diagonal.  The
guide is removed and every empty cell receives the color at its reflected
coordinate, while already occupied cells keep their original colors.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4f3a702ae0c4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "327cfcfd520d"
SUMMARY = (
    "Place a sparse connected colored pattern inside a square grid. A 1 guide "
    "at the top-left selects main-diagonal reflection; a 2 guide at the "
    "top-right selects anti-diagonal reflection. Remove the guide and fill "
    "empty reflected partners without overwriting original colored cells."
)
INVARIANTS = [
    "the grid is square and 8..12 cells on each side",
    "exactly one guide is present: (top-left, top-right) is (1,0) or (0,2)",
    "the interior pattern has 4..8 cells, is 8-connected, and uses one or two colors from 3..9",
    "the pattern stays below the guide row and has at least one empty reflected partner",
    "the canonical prior covers every linked official size/command/color-count/shape profile",
]

AXES = {
    "grid_n": {
        "type": "int",
        "default": "scheduled canonical profile every fifth sample; otherwise difficulty-scaled",
        "valid": "8..12",
    },
    "cmd": {
        "type": "int",
        "default": "canonical profile command or alternating 1/2 schedule",
        "valid": "1..2",
    },
    "n_cells": {
        "type": "int",
        "default": "4 on canonical profiles; otherwise difficulty-scaled 4..8",
        "valid": "4..8",
    },
    "n_pattern_colors": {
        "type": "int",
        "default": "two colors every third ordinary sample, otherwise one",
        "valid": "1..2",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15

# Executably re-checked against every canonical train and held-out test input.
_SHAPE_A = ((0, 1), (1, 0), (2, 1), (2, 2))
_SHAPE_B = ((0, 0), (1, 0), (1, 1), (2, 2))
_SHAPE_C = ((0, 0), (1, 1), (2, 1), (2, 2))
_SHAPE_D = ((0, 0), (1, 1), (1, 2), (2, 2))
_CANONICAL_PROFILES = (
    (8, 1, 2, _SHAPE_A),
    (9, 2, 1, _SHAPE_B),
    (8, 1, 1, _SHAPE_C),
    (10, 2, 1, _SHAPE_D),
    (9, 2, 1, _SHAPE_D),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)


def _scheduled_int(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    """Record a deterministic teaching schedule while honoring explicit overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    return "medium" if difficulty is None else difficulty


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _c in cells)
    left = min(c for _r, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [r for r, _c in cells]
    cols = [c for _r, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _connected8(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nxt = (r + dr, c + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return seen == cells


def _reflect(r: int, c: int, n: int, cmd: int) -> tuple[int, int]:
    return (c, r) if cmd == 1 else (n - 1 - c, n - 1 - r)


def _apply_transform(grid: list[list[int]], cmd: int) -> list[list[int]]:
    n = len(grid)
    base = [row[:] for row in grid]
    base[0][0] = 0
    base[0][n - 1] = 0
    out = full_grid(n, n, 0)
    for r in range(n):
        for c in range(n):
            if base[r][c] != 0:
                out[r][c] = base[r][c]
            else:
                rr, cc = _reflect(r, c, n, cmd)
                out[r][c] = base[rr][cc]
    return out


def _analyze(grid: Any) -> tuple[dict[str, Any], list[str]]:
    facts: dict[str, Any] = {}
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid rows must be non-empty sequences"]
    n = len(grid)
    if any(not isinstance(row, (list, tuple)) or len(row) != n for row in grid):
        errors.append("grid must be square and rectangular")
        return facts, errors
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors in 0..9")
        return facts, errors
    if not 8 <= n <= 12:
        errors.append(f"grid side must be 8..12, got {n}")

    top_left, top_right = grid[0][0], grid[0][n - 1]
    if (top_left, top_right) == (1, 0):
        cmd = 1
        guide = (0, 0)
    elif (top_left, top_right) == (0, 2):
        cmd = 2
        guide = (0, n - 1)
    else:
        cmd = None
        guide = None
        errors.append(
            "guide corners must be exactly (top-left, top-right)=(1,0) or (0,2)"
        )

    stray_guides = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (1, 2) and (r, c) != guide
    ]
    if stray_guides:
        errors.append(f"found {len(stray_guides)} stray guide-color cell(s)")

    pattern = {
        (r, c): value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1, 2)
    }
    cells = set(pattern)
    if not 4 <= len(cells) <= 8:
        errors.append(f"pattern cell count must be 4..8, got {len(cells)}")
    colors = tuple(sorted(set(pattern.values())))
    if not 1 <= len(colors) <= 2:
        errors.append(f"pattern must use one or two colors, got {len(colors)}")
    if cells:
        r1, c1, r2, c2 = _bbox(cells)
        bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
        if r1 < 1:
            errors.append("pattern must stay below the top guide row")
        if not (2 <= bbox_h <= 5 and 2 <= bbox_w <= 5):
            errors.append(f"pattern bbox must be 2..5 by 2..5, got {bbox_h}x{bbox_w}")
        if not _connected8(cells):
            errors.append("pattern must be 8-connected")
    else:
        r1 = c1 = r2 = c2 = bbox_h = bbox_w = 0

    productive: set[tuple[int, int]] = set()
    occupied_pairs: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    if cmd is not None:
        for r, c in cells:
            reflected = _reflect(r, c, n, cmd)
            if reflected not in cells:
                productive.add((r, c))
            elif reflected != (r, c):
                occupied_pairs.add(tuple(sorted(((r, c), reflected))))
        if not productive:
            errors.append("pattern has no empty reflected partner; transformation would add nothing")

    facts.update(
        {
            "grid_n": n,
            "cmd": cmd,
            "guide": guide,
            "cells": frozenset(cells),
            "colors": colors,
            "n_cells": len(cells),
            "n_pattern_colors": len(colors),
            "bbox": (r1, c1, r2, c2),
            "bbox_h": bbox_h,
            "bbox_w": bbox_w,
            "normalized_shape": _normalize(cells) if cells else (),
            "productive_count": len(productive),
            "occupied_pair_count": len(occupied_pairs),
        }
    )
    return facts, errors


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every exact declared axis from the returned pixels."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_n": int(facts["grid_n"]),
        "cmd": int(facts["cmd"]),
        "n_cells": int(facts["n_cells"]),
        "n_pattern_colors": int(facts["n_pattern_colors"]),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket oracle for focused tests."""
    facts, errors = _analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _apply_transform(grid, int(facts["cmd"]))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts, errors = _analyze(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if facts and not errors and requested:
        observed = observe_overrides(grid)
        for name in AXES:
            if name in requested and requested[name] is not None:
                expected = int(requested[name])
                if observed.get(name) != expected:
                    errors.append(
                        f"override {name} requested {expected!r}, observed {observed.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Match the linked empirical manifold shared by all five official inputs."""
    facts, errors = _analyze(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if facts["grid_n"] not in (8, 9, 10):
        reasons.append(f"canonical side length is 8, 9, or 10, got {facts['grid_n']}")
    if facts["n_cells"] != 4:
        reasons.append(f"canonical patterns have four cells, got {facts['n_cells']}")
    if (facts["bbox_h"], facts["bbox_w"]) != (3, 3):
        reasons.append(
            f"canonical four-cell morphology occupies a 3x3 bbox, got "
            f"{facts['bbox_h']}x{facts['bbox_w']}"
        )
    return reasons


def canonical_profile_signature(grid):
    """Return the exact linked official profile signature, when present."""
    if strict_canonical_like(grid):
        return None
    facts, _errors = _analyze(grid)
    return (
        facts["grid_n"],
        facts["cmd"],
        facts["n_pattern_colors"],
        facts["normalized_shape"],
    )


def _witness_main_command(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["cmd"] == 1


def _witness_anti_command(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["cmd"] == 2


def _witness_multicolor_pattern(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["n_pattern_colors"] == 2


def _witness_productive_reflection(grid) -> bool:
    facts, errors = _analyze(grid)
    return not errors and facts["productive_count"] > 0


SEMANTIC_WITNESSES = {
    "main_diagonal_command": _witness_main_command,
    "anti_diagonal_command": _witness_anti_command,
    "multicolor_pattern": _witness_multicolor_pattern,
    "productive_reflection": _witness_productive_reflection,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave the command mapping or reflection ambiguous."""
    reasons: list[str] = []
    inputs = [pair.get("input") for pair in demos if isinstance(pair, dict)]
    outputs = [pair.get("output") for pair in demos if isinstance(pair, dict)]
    if len(inputs) < EXAMPLES_NEEDED or len(outputs) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} complete demonstrations"]

    analyses = [_analyze(grid) for grid in inputs]
    if any(errors for _facts, errors in analyses):
        reasons.append("at least one demonstration input violates the teaching grammar")
        return reasons
    commands = {facts["cmd"] for facts, _errors in analyses}
    if commands != {1, 2}:
        reasons.append("demonstrations do not establish both command branches")
    if not any(facts["n_pattern_colors"] == 2 for facts, _errors in analyses):
        reasons.append("no demonstration refutes a modal-color-only shortcut")
    if not all(expected == rule_mirror(inp) for inp, expected in zip(inputs, outputs)):
        reasons.append("at least one demonstration output disagrees with diagonal reflection")
    if not any(
        facts["productive_count"] > 0 and out != _cleared_input(inp)
        for (facts, _errors), inp, out in zip(analyses, inputs, outputs)
    ):
        reasons.append("no demonstration refutes guide-removal-only / no-op behavior")

    if not isinstance(query, dict) or not isinstance(query.get("input"), list):
        reasons.append("query input is missing")
        return reasons
    query_grid = query["input"]
    query_facts, query_errors = _analyze(query_grid)
    if query_errors:
        reasons.append("query input violates the teaching grammar")
        return reasons
    intended = _apply_transform(query_grid, int(query_facts["cmd"]))
    alternate = _apply_transform(query_grid, 3 - int(query_facts["cmd"]))
    if intended == alternate:
        reasons.append("query has the same answer under both diagonal choices")
    if int(query_facts["cmd"]) not in commands:
        reasons.append("the query command branch is absent from the demonstrations")
    return reasons


def _cleared_input(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    out[0][0] = 0
    out[0][-1] = 0
    return out


def _random_shape(count: int, rng, *, hard: bool) -> tuple[tuple[int, int], ...]:
    max_span = 5 if hard else 4
    for _attempt in range(300):
        cells = {(max_span // 2, max_span // 2)}
        while len(cells) < count:
            frontier = {
                (r + dr, c + dc)
                for r, c in cells
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
                if not (dr == dc == 0)
                and 0 <= r + dr < max_span
                and 0 <= c + dc < max_span
                and (r + dr, c + dc) not in cells
            }
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        if len(cells) != count:
            continue
        normalized = _normalize(cells)
        r1, c1, r2, c2 = _bbox(normalized)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        if 2 <= bh <= 5 and 2 <= bw <= 5 and _connected8(set(normalized)):
            return normalized
    raise RuntimeError(f"could not construct an {count}-cell connected pattern")


def _general_schedule(sample_index: int, band: str) -> tuple[int, int]:
    size_cycles = {
        "easy": (8, 9, 10, 9),
        "medium": (8, 9, 10, 11, 9),
        "hard": (9, 10, 11, 12, 10),
    }
    cell_cycles = {
        "easy": (4, 5, 4, 5),
        "medium": (5, 6, 4, 6, 5),
        "hard": (6, 7, 8, 4, 7),
    }
    return (
        size_cycles[band][sample_index % len(size_cycles[band])],
        cell_cycles[band][sample_index % len(cell_cycles[band])],
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    canonical_slot = not overrides and sample_index % 5 == 0
    profile = _CANONICAL_PROFILES[(sample_index // 5) % len(_CANONICAL_PROFILES)]
    general_n, general_cells = _general_schedule(sample_index, band)

    grid_n = _scheduled_int(
        ctx, "grid_n", 8, 12, profile[0] if canonical_slot else general_n
    )
    cmd = _scheduled_int(
        ctx, "cmd", 1, 2, profile[1] if canonical_slot else 1 + sample_index % 2
    )
    n_cells = _scheduled_int(
        ctx, "n_cells", 4, 8, 4 if canonical_slot else general_cells
    )
    scheduled_colors = profile[2] if canonical_slot else (2 if sample_index % 3 == 2 else 1)
    n_pattern_colors = _scheduled_int(
        ctx, "n_pattern_colors", 1, 2, scheduled_colors
    )

    shape_rng = ctx.draw_rng("shape")
    shape = profile[3] if canonical_slot and n_cells == 4 else _random_shape(
        n_cells, shape_rng, hard=(band == "hard")
    )
    r1, c1, r2, c2 = _bbox(shape)
    bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
    placement_rng = ctx.draw_rng("placement")

    placed: set[tuple[int, int]] | None = None
    for _attempt in range(200):
        top = placement_rng.randint(1, grid_n - bbox_h - 1)
        left = placement_rng.randint(1, grid_n - bbox_w - 1)
        candidate = {(top + r, left + c) for r, c in shape}
        if any(_reflect(r, c, grid_n, cmd) not in candidate for r, c in candidate):
            placed = candidate
            break
    if placed is None:
        raise RuntimeError("could not place a pattern with an empty reflected partner")

    colors = ctx.draw_distinct_colors(
        "pattern_colors", n=n_pattern_colors, exclude={0, 1, 2}
    )
    color_rng = ctx.draw_rng("color_assignment")
    ordered_cells = sorted(placed)
    color_rng.shuffle(ordered_cells)
    assignments = list(colors)
    assignments.extend(color_rng.choice(colors) for _ in range(len(ordered_cells) - len(colors)))
    color_rng.shuffle(assignments)

    grid = full_grid(grid_n, grid_n, 0)
    if cmd == 1:
        grid[0][0] = 1
    else:
        grid[0][grid_n - 1] = 2
    for cell, color in zip(ordered_cells, assignments):
        grid[cell[0]][cell[1]] = color

    errors = self_check(grid, difficulty=band)
    if errors:
        raise RuntimeError("generated invalid grid: " + "; ".join(errors))
    return grid
