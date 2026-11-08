"""Generator for arc_additional_puzzle_bank_volume2:E13.

The canonical rule recolors every yellow (4) 4-connected component that is
*exactly* a three-cell L in blue (1).  Ordinary generated lessons include both
shape and color counterexamples so that "recolor every yellow cell", "recolor
every yellow size-three component", and "recolor every L regardless of color"
do not survive the demonstrations.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "4de2bae05c7d"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "12b3f52c8e05"

SUMMARY = (
    "On a black background, recolor only yellow (4) components that are exact "
    "three-cell 2x2 L-triominoes to blue (1). Yellow non-L components and "
    "same-shaped L-triominoes in other colors remain unchanged."
)

INVARIANTS = [
    "background is 0 and blue 1 is absent from every input",
    "at least one yellow component is an exact size-3 2x2 L-triomino",
    "yellow shape decoys, when present, are isolated lawful non-L components",
    "non-yellow distractors, when present, are isolated exact L-triominoes",
    "ordinary five-example curricula expose every L orientation and refute shape-only and color-only shortcuts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked five-profile schedule",
        "valid": "7..18",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked five-profile schedule",
        "valid": "7..18",
        "doc": "Input grid width.",
    },
    "n_target_l": {
        "type": "int",
        "default": "2 canonical anchor / 3 contrast profiles",
        "valid": "1..3",
        "doc": "Number of yellow exact L-triomino target components.",
    },
    "n_yellow_decoys": {
        "type": "int",
        "default": "0 canonical anchor / 1 contrast profiles",
        "valid": "0..1",
        "doc": "Number of yellow components that are deliberately not L-triominoes.",
    },
    "n_colored_l_decoys": {
        "type": "int",
        "default": "0 canonical anchor / 1 contrast profiles",
        "valid": "0..1",
        "doc": "Number of exact L-triominoes whose color is not yellow.",
    },
    "target_position": {
        "type": "enum",
        "default": "linked five-profile schedule",
        "valid": ["interior", "edge"],
        "doc": "Whether every target is interior or at least one target touches an edge.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)


# Normalized 2x2 L-triominoes, named by the missing corner.
_L_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "missing_nw": ((0, 1), (1, 0), (1, 1)),
    "missing_ne": ((0, 0), (1, 0), (1, 1)),
    "missing_sw": ((0, 0), (0, 1), (1, 1)),
    "missing_se": ((0, 0), (0, 1), (1, 0)),
}
_L_BY_CELLS = {cells: name for name, cells in _L_SHAPES.items()}
_ORIENTATIONS = tuple(_L_SHAPES)

# Every five consecutive generated samples contain all five profiles.  This is
# deliberately aligned with EXAMPLES_NEEDED so any materialized lesson gets a
# canonical anchor plus four shortcut-rebutting demonstrations.
_PROFILE_ORIENTATIONS = (
    ("missing_se", "missing_sw"),
    ("missing_nw", "missing_ne", "missing_sw"),
    ("missing_ne", "missing_sw", "missing_se"),
    ("missing_sw", "missing_se", "missing_nw"),
    ("missing_se", "missing_nw", "missing_ne"),
)
_YELLOW_DECOY_BASES = (
    ((0, 0), (0, 1), (0, 2)),  # straight triomino for explicit overrides on profile 0
    ((0, 0), (0, 1), (0, 2)),  # straight triomino: refutes size-3 shortcut
    ((0, 0), (0, 1), (1, 0), (1, 1)),  # solid 2x2 square
    ((0, 0), (1, 0), (2, 0), (2, 1)),  # length-4 L tetromino
    ((0, 0), (0, 1)),  # domino
)
_NON_YELLOW_COLORS = (2, 3, 5, 6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the linked curriculum profile; independent of seed and band."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _rotate(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in shape)


def _reflect(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return _normalize((row, -col) for row, col in shape)


def _orbit(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = _normalize(shape)
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


_DECOY_ORBITS = {
    "singleton": set(_orbit(((0, 0),))),
    "domino": set(_orbit(((0, 0), (0, 1)))),
    "straight_triomino": set(_orbit(((0, 0), (0, 1), (0, 2)))),
    "square": set(_orbit(((0, 0), (0, 1), (1, 0), (1, 1)))),
    "long_l_tetromino": set(_orbit(((0, 0), (1, 0), (2, 0), (2, 1)))),
}


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Pin the linked profile normally, but honor the whole declared override range."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _profile_defaults(ctx, profile: int, difficulty: str | None) -> dict[str, Any]:
    if profile == 0:
        # The official rows are 7x7 and 8x8 with two yellow targets and no
        # distractors. Both canonical dimensions remain present in every band.
        side = ctx.draw_rng("canonical-side").choice((7, 8))
        return {
            "grid_h": side,
            "grid_w": side,
            "n_target_l": 2,
            "n_yellow_decoys": 0,
            "n_colored_l_decoys": 0,
            "target_position": "interior",
        }

    base_dims = ((10, 10), (11, 10), (12, 12), (13, 11))
    h, w = base_dims[profile - 1]
    bump = {None: 1, "easy": 0, "medium": 1, "hard": 3}[difficulty]
    return {
        "grid_h": h + bump,
        "grid_w": w + bump,
        "n_target_l": 3,
        "n_yellow_decoys": 1,
        "n_colored_l_decoys": 1,
        "target_position": "edge" if profile in (2, 3) else "interior",
    }


def _translated_candidates(
    shape: tuple[tuple[int, int], ...],
    h: int,
    w: int,
    *,
    require_edge: bool = False,
    require_interior: bool = False,
) -> list[tuple[tuple[int, int], ...]]:
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    candidates = []
    for row0 in range(h - height + 1):
        for col0 in range(w - width + 1):
            cells = tuple((row0 + row, col0 + col) for row, col in shape)
            touches_edge = any(
                row in (0, h - 1) or col in (0, w - 1) for row, col in cells
            )
            if require_edge and not touches_edge:
                continue
            if require_interior and touches_edge:
                continue
            candidates.append(cells)
    return candidates


def _can_place(cells: tuple[tuple[int, int], ...], occupied: set[tuple[int, int]]) -> bool:
    if any(cell in occupied for cell in cells):
        return False
    # A one-cell cardinal moat keeps same-color components distinct and avoids
    # visually fused multicolor objects. Diagonal contact remains lawful.
    for row, col in cells:
        for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if (row + drow, col + dcol) in occupied:
                return False
    return True


def _place_specs(
    h: int,
    w: int,
    specs: list[dict[str, Any]],
    rng,
) -> list[tuple[dict[str, Any], tuple[tuple[int, int], ...]]]:
    candidate_lists: list[list[tuple[tuple[int, int], ...]]] = []
    for spec in specs:
        candidates = _translated_candidates(
            spec["shape"],
            h,
            w,
            require_edge=bool(spec.get("require_edge")),
            require_interior=bool(spec.get("require_interior")),
        )
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    # Put the most constrained objects first while retaining stable tie order.
    order = sorted(
        range(len(specs)),
        key=lambda index: (
            len(candidate_lists[index]),
            -len(specs[index]["shape"]),
            index,
        ),
    )
    placed: list[tuple[dict[str, Any], tuple[tuple[int, int], ...]] | None] = [None] * len(specs)
    occupied: set[tuple[int, int]] = set()
    nodes = 0

    def search(depth: int) -> bool:
        nonlocal nodes
        if depth == len(order):
            return True
        index = order[depth]
        spec = specs[index]
        for cells in candidate_lists[index]:
            nodes += 1
            if nodes > 250_000:
                return False
            if not _can_place(cells, occupied):
                continue
            occupied.update(cells)
            placed[index] = (spec, cells)
            if search(depth + 1):
                return True
            for cell in cells:
                occupied.remove(cell)
            placed[index] = None
        return False

    if not search(0):
        raise ValueError(
            f"could not place {len(specs)} separated components on {h}x{w} grid"
        )
    return [item for item in placed if item is not None]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; the canonical Racket rule owns output."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _profile_defaults(ctx, profile, difficulty)

    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 7, 18)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 7, 18)
    n_target = _draw_int_axis(
        ctx, overrides, "n_target_l", defaults["n_target_l"], 1, 3
    )
    n_yellow_decoys = _draw_int_axis(
        ctx, overrides, "n_yellow_decoys", defaults["n_yellow_decoys"], 0, 1
    )
    n_colored_decoys = _draw_int_axis(
        ctx,
        overrides,
        "n_colored_l_decoys",
        defaults["n_colored_l_decoys"],
        0,
        1,
    )
    target_position = _draw_choice_axis(
        ctx,
        overrides,
        "target_position",
        defaults["target_position"],
        ("interior", "edge"),
    )

    shape_rng = ctx.draw_rng("shape-selection")
    layout_rng = ctx.draw_rng("layout")
    orientation_schedule = _PROFILE_ORIENTATIONS[profile]
    specs: list[dict[str, Any]] = []
    for index in range(n_target):
        orientation = orientation_schedule[index % len(orientation_schedule)]
        specs.append(
            {
                "role": "target",
                "color": 4,
                "shape": _L_SHAPES[orientation],
                "require_edge": target_position == "edge" and index == 0,
                "require_interior": target_position == "interior",
            }
        )

    for _ in range(n_yellow_decoys):
        base = _YELLOW_DECOY_BASES[profile]
        variants = _orbit(base)
        specs.append(
            {
                "role": "yellow_decoy",
                "color": 4,
                "shape": shape_rng.choice(variants),
            }
        )

    for index in range(n_colored_decoys):
        orientation = orientation_schedule[(n_target + index) % len(orientation_schedule)]
        specs.append(
            {
                "role": "colored_l_decoy",
                "color": shape_rng.choice(_NON_YELLOW_COLORS),
                "shape": _L_SHAPES[orientation],
            }
        )

    grid = full_grid(h, w, 0)
    for spec, cells in _place_specs(h, w, specs, layout_rng):
        for row, col in cells:
            grid[row][col] = spec["color"]

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_target_l": n_target,
        "n_yellow_decoys": n_yellow_decoys,
        "n_colored_l_decoys": n_colored_decoys,
        "target_position": target_position,
    }
    if observed != expected:
        raise ValueError(f"constructed axes are not observable: expected {expected}, got {observed}")
    return [row[:] for row in grid]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                rr, cc = current
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (rr + drow, cc + dcol)
                    if (
                        0 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            normalized = _normalize(cells)
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "normalized": normalized,
                    "orientation": _L_BY_CELLS.get(normalized),
                }
            )
    return components


def _yellow_decoy_kind(normalized: tuple[tuple[int, int], ...]) -> str | None:
    for name, orbit in _DECOY_ORBITS.items():
        if normalized in orbit:
            return name
    return None


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 18:
        errors.append(f"grid height {h} outside 7..18")
    if not 7 <= w <= 18:
        errors.append(f"grid width {w} outside 7..18")

    colors = {value for row in grid for value in row}
    if 1 in colors:
        errors.append("blue 1 is an output color and must not appear in an input")

    # Different-colored pieces are also required to have a cardinal background
    # moat; otherwise a multicolor blob visually obscures the object grammar.
    for row in range(h):
        for col in range(w):
            value = grid[row][col]
            if value == 0:
                continue
            for drow, dcol in ((1, 0), (0, 1)):
                rr, cc = row + drow, col + dcol
                if 0 <= rr < h and 0 <= cc < w:
                    other = grid[rr][cc]
                    if other not in (0, value):
                        errors.append("nonzero components must be separated by background")
                        break
            if errors and errors[-1] == "nonzero components must be separated by background":
                break
        if errors and errors[-1] == "nonzero components must be separated by background":
            break

    components = _components(grid)
    targets = [comp for comp in components if comp["color"] == 4 and comp["orientation"]]
    yellow_decoys = [comp for comp in components if comp["color"] == 4 and not comp["orientation"]]
    colored_l_decoys = [comp for comp in components if comp["color"] != 4 and comp["orientation"]]
    colored_non_l = [comp for comp in components if comp["color"] != 4 and not comp["orientation"]]

    if not 1 <= len(targets) <= 3:
        errors.append(f"expected 1..3 yellow exact L-triominoes, found {len(targets)}")
    if len(yellow_decoys) > 1:
        errors.append(f"expected at most one yellow non-L decoy, found {len(yellow_decoys)}")
    if len(colored_l_decoys) > 1:
        errors.append(f"expected at most one non-yellow L decoy, found {len(colored_l_decoys)}")
    if colored_non_l:
        errors.append("every non-yellow component must be an exact L-triomino")

    yellow_decoy_kinds = []
    for component in yellow_decoys:
        kind = _yellow_decoy_kind(component["normalized"])
        if kind is None:
            errors.append(
                "yellow decoys must be singleton, domino, straight triomino, square, or length-4 L"
            )
        else:
            yellow_decoy_kinds.append(kind)

    target_touches_edge = any(
        row in (0, h - 1) or col in (0, w - 1)
        for component in targets
        for row, col in component["cells"]
    )
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "colors": colors,
        "components": components,
        "targets": targets,
        "yellow_decoys": yellow_decoys,
        "yellow_decoy_kinds": yellow_decoy_kinds,
        "colored_l_decoys": colored_l_decoys,
        "target_position": "edge" if target_touches_edge else "interior",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and task-hiding impostors."""
    del difficulty, meta
    return list(_analyze(grid).get("errors", []))


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_target_l": len(analysis["targets"]),
        "n_yellow_decoys": len(analysis["yellow_decoys"]),
        "n_colored_l_decoys": len(analysis["colored_l_decoys"]),
        "target_position": analysis["target_position"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    orientations = sorted(component["orientation"] for component in analysis["targets"])
    return {
        **observe_overrides(grid),
        "target_orientations": orientations,
        "yellow_decoy_kinds": sorted(analysis["yellow_decoy_kinds"]),
        "palette": sorted(analysis["colors"]),
        "canonical_anchor": not strict_canonical_like(grid),
    }


def strict_canonical_like(grid) -> list[str]:
    """Official structural family: canonical dimensions, palette, and counts."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    reasons = []
    if (analysis["grid_h"], analysis["grid_w"]) not in {(7, 7), (8, 8)}:
        reasons.append("canonical inputs are 7x7 or 8x8")
    if analysis["colors"] - {0, 4}:
        reasons.append("canonical inputs use only background 0 and yellow 4")
    if len(analysis["targets"]) != 2:
        reasons.append("canonical inputs contain exactly two target L-triominoes")
    if analysis["yellow_decoys"] or analysis["colored_l_decoys"]:
        reasons.append("canonical inputs contain no distractor components")
    if analysis["target_position"] != "interior":
        reasons.append("canonical target components do not touch the border")
    return reasons


def _witness(grid, predicate) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "canonical_anchor": lambda grid: _witness(grid, lambda _: not strict_canonical_like(grid)),
    "target_missing_nw": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_nw" for c in a["targets"])
    ),
    "target_missing_ne": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_ne" for c in a["targets"])
    ),
    "target_missing_sw": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_sw" for c in a["targets"])
    ),
    "target_missing_se": lambda grid: _witness(
        grid, lambda a: any(c["orientation"] == "missing_se" for c in a["targets"])
    ),
    "yellow_non_l_decoy": lambda grid: _witness(grid, lambda a: bool(a["yellow_decoys"])),
    "yellow_straight_triomino_decoy": lambda grid: _witness(
        grid, lambda a: "straight_triomino" in a["yellow_decoy_kinds"]
    ),
    "yellow_square_decoy": lambda grid: _witness(
        grid, lambda a: "square" in a["yellow_decoy_kinds"]
    ),
    "yellow_long_l_decoy": lambda grid: _witness(
        grid, lambda a: "long_l_tetromino" in a["yellow_decoy_kinds"]
    ),
    "nonyellow_l_decoy": lambda grid: _witness(grid, lambda a: bool(a["colored_l_decoys"])),
    "target_touches_edge": lambda grid: _witness(
        grid, lambda a: a["target_position"] == "edge"
    ),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def rule_mirror(grid):
    """Pure Python mirror for tests only; Racket remains the output authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        for row, col in component["cells"]:
            out[row][col] = 1
    return out


def _recolor_all_yellow(grid):
    return [[1 if value == 4 else value for value in row] for row in grid]


def _recolor_yellow_size3(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["color"] == 4 and len(component["cells"]) == 3:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _recolor_all_l_any_color(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["orientation"]:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def _recolor_only_missing_se(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        if component["orientation"] == "missing_se":
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


SEMANTIC_RIVALS = {
    "recolor every yellow cell": _recolor_all_yellow,
    "recolor every yellow size-three component": _recolor_yellow_size3,
    "recolor every L-triomino regardless of color": _recolor_all_l_any_color,
}
WITNESS_RIVALS = {
    "yellow_non_l_decoy": ["recolor every yellow cell"],
    "yellow_straight_triomino_decoy": [
        "recolor every yellow cell",
        "recolor every yellow size-three component",
    ],
    "nonyellow_l_decoy": ["recolor every L-triomino regardless of color"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = {
    **SEMANTIC_RIVALS,
    "recolor only the missing-SE orientation": _recolor_only_missing_se,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that determine the exact yellow-L query answer."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    orientations: set[str] = set()
    saw_yellow_decoy = False
    saw_straight_yellow = False
    saw_colored_l = False
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _analyze(demo["input"])
        if analysis.get("errors"):
            reasons.append(f"demo {index} input is not lawful: {analysis['errors'][0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the exact yellow-L rule")
        orientations.update(component["orientation"] for component in analysis["targets"])
        saw_yellow_decoy |= bool(analysis["yellow_decoys"])
        saw_straight_yellow |= "straight_triomino" in analysis["yellow_decoy_kinds"]
        saw_colored_l |= bool(analysis["colored_l_decoys"])

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    if reasons:
        return reasons

    missing = sorted(set(_ORIENTATIONS) - orientations)
    if missing:
        reasons.append(f"demonstrations omit target L orientations {missing}")
    if not saw_yellow_decoy:
        reasons.append("demonstrations never show a yellow non-L component that must stay yellow")
    if not saw_straight_yellow:
        reasons.append("demonstrations never show a yellow straight triomino that must stay yellow")
    if not saw_colored_l:
        reasons.append("demonstrations never show a non-yellow L-triomino that must retain its color")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            alternative = competitor(query["input"])
            if alternative != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
