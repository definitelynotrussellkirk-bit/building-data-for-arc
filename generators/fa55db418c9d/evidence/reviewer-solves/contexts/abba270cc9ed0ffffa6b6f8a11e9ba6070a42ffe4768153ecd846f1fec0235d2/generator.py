"""Generator for arc_additional_puzzle_bank_volume21:M141.

The canonical rule operates on same-color four-connected components.  Every
blue (1) component that is *exactly* a three-cell L in a 2x2 bounding box is
recolored by the missing corner; every other component remains unchanged.

Ordinary five-example curricula deliberately include blue non-L components,
including a blue straight triomino, and non-blue L-triominoes.  Those examples
separate the intended rule from the strongest canonical-fitting size-only
shortcut and from broader color-only / shape-only rivals.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "fa55db418c9d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "eeee12543bcc"

SUMMARY = (
    "On a black background, recolor only blue (1) components that are exact "
    "three-cell 2x2 L-triominoes. The replacement color is determined by the "
    "missing corner: missing southeast -> 2, southwest -> 3, northeast -> 4, "
    "northwest -> 8. Blue non-L components and non-blue components remain "
    "unchanged. Five linked profiles expose every orientation plus size, "
    "color, and border counterexamples."
)

INVARIANTS = [
    "background is 0 and generated inputs do not use output colors 2, 3, 4, or 8",
    "every input has 1..4 blue exact L-triomino targets",
    "blue non-L components, when present, remain blue",
    "non-blue L-triominoes, when present, retain their original color",
    "ordinary five-example curricula contain all four target orientations and explicit rival-rule counterexamples",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked five-profile schedule",
        "valid": "9..20",
        "doc": "Input grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "linked five-profile schedule",
        "valid": "10..22",
        "doc": "Input grid width.",
    },
    "n_target_l": {
        "type": "int",
        "default": "3 canonical/contrast profiles; 4 advanced profiles",
        "valid": "1..4",
        "doc": "Number of blue exact L-triomino target components.",
    },
    "n_blue_decoys": {
        "type": "int",
        "default": "1",
        "valid": "0..1",
        "doc": "Number of blue components that are deliberately not L-triominoes.",
    },
    "n_colored_l_decoys": {
        "type": "int",
        "default": "0 canonical anchor / 1 contrast profiles",
        "valid": "0..1",
        "doc": "Number of exact L-triominoes whose color is not blue.",
    },
    "target_position": {
        "type": "enum",
        "default": "linked five-profile schedule",
        "valid": ["interior", "edge"],
        "doc": "Whether all targets are interior or at least one target touches an edge.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)


# Normalized 2x2 L-triominoes, named by their missing corner.
_L_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "missing_nw": ((0, 1), (1, 0), (1, 1)),
    "missing_ne": ((0, 0), (1, 0), (1, 1)),
    "missing_sw": ((0, 0), (0, 1), (1, 1)),
    "missing_se": ((0, 0), (0, 1), (1, 0)),
}
_L_BY_CELLS = {cells: name for name, cells in _L_SHAPES.items()}
_ORIENTATIONS = tuple(_L_SHAPES)
_OUTPUT_BY_ORIENTATION = {
    "missing_se": 2,
    "missing_sw": 3,
    "missing_ne": 4,
    "missing_nw": 8,
}

_PROFILE_TARGET_ORIENTATIONS = (
    ("missing_sw", "missing_ne", "missing_se", "missing_nw"),
    ("missing_nw", "missing_ne", "missing_sw", "missing_se"),
    ("missing_ne", "missing_sw", "missing_se", "missing_nw"),
    ("missing_sw", "missing_se", "missing_nw", "missing_ne"),
    ("missing_se", "missing_nw", "missing_ne", "missing_sw"),
)

_STRAIGHT_TRIOMINO = ((0, 0), (0, 1), (0, 2))
_SQUARE = ((0, 0), (0, 1), (1, 0), (1, 1))
_LONG_L_TETROMINO = ((0, 0), (1, 0), (2, 0), (2, 1))
_SIZE6_RECTANGLE = (
    (0, 0), (0, 1), (0, 2),
    (1, 0), (1, 1), (1, 2),
)
_PROFILE_BLUE_DECOY_BASES = (
    _SIZE6_RECTANGLE,
    _STRAIGHT_TRIOMINO,
    _SQUARE,
    _SIZE6_RECTANGLE,
    _LONG_L_TETROMINO,
)
_NON_BLUE_COLORS = (5, 6, 7, 9)
_ALLOWED_INPUT_COLORS = {0, 1, *_NON_BLUE_COLORS}
_CANONICAL_DIMS = {(10, 11), (9, 11), (9, 12), (9, 10)}
_CANONICAL_PALETTES = ({0, 1, 7}, {0, 1, 6}, {0, 1, 6, 7})


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
    "straight_triomino": set(_orbit(_STRAIGHT_TRIOMINO)),
    "square": set(_orbit(_SQUARE)),
    "long_l_tetromino": set(_orbit(_LONG_L_TETROMINO)),
    "size6_blob": set(_orbit(_SIZE6_RECTANGLE)),
}


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Pin profile defaults normally while honoring the full exact override range."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _profile_defaults(ctx, profile: int, difficulty: str | None) -> dict[str, Any]:
    if profile == 0:
        # Every band receives an exact canonical (height, width, palette-size)
        # anchor. The fixed decorations below make the default palette {0,1,6,7}.
        h, w = ctx.draw_rng("canonical-dimensions").choice(sorted(_CANONICAL_DIMS))
        return {
            "grid_h": h,
            "grid_w": w,
            "n_target_l": 3,
            "n_blue_decoys": 1,
            "n_colored_l_decoys": 0,
            "target_position": "interior",
        }

    base_h, base_w = ((10, 13), (11, 14), (12, 15), (13, 16))[profile - 1]
    bump = {None: 2, "easy": 0, "medium": 2, "hard": 4}[difficulty]
    return {
        "grid_h": base_h + bump,
        "grid_w": base_w + bump,
        "n_target_l": 3 if profile in (1, 2) else 4,
        "n_blue_decoys": 1,
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
    # Generated scenes use a cardinal moat for visual clarity. This is a
    # generation policy, not a validator requirement: canonical examples may
    # lawfully have different-colored components touching.
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

    order = sorted(
        range(len(specs)),
        key=lambda index: (
            len(candidate_lists[index]),
            -len(specs[index]["shape"]),
            index,
        ),
    )
    placed: list[
        tuple[dict[str, Any], tuple[tuple[int, int], ...]] | None
    ] = [None] * len(specs)
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
            if nodes > 500_000:
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
    """Build one deterministic lawful input; canonical Racket owns the output."""
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

    h = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 9, 20)
    w = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 10, 22)
    n_target = _draw_int_axis(
        ctx, overrides, "n_target_l", defaults["n_target_l"], 1, 4
    )
    n_blue_decoys = _draw_int_axis(
        ctx, overrides, "n_blue_decoys", defaults["n_blue_decoys"], 0, 1
    )
    n_colored_l = _draw_int_axis(
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
    orientation_schedule = _PROFILE_TARGET_ORIENTATIONS[profile]
    specs: list[dict[str, Any]] = []

    for index in range(n_target):
        orientation = orientation_schedule[index % len(orientation_schedule)]
        specs.append(
            {
                "role": "target",
                "color": 1,
                "shape": _L_SHAPES[orientation],
                "require_edge": target_position == "edge" and index == 0,
                "require_interior": target_position == "interior",
            }
        )

    for _ in range(n_blue_decoys):
        base = _PROFILE_BLUE_DECOY_BASES[profile]
        specs.append(
            {
                "role": "blue_decoy",
                "color": 1,
                "shape": shape_rng.choice(_orbit(base)),
            }
        )

    for index in range(n_colored_l):
        orientation = orientation_schedule[(n_target + index) % len(orientation_schedule)]
        specs.append(
            {
                "role": "colored_l_decoy",
                "color": shape_rng.choice(_NON_BLUE_COLORS),
                "shape": _L_SHAPES[orientation],
            }
        )

    # The default anchor mirrors the canonical scale and reaches the largest
    # canonical palette with color-6 and color-7 line decorations. Explicit
    # override matrices omit these hidden
    # profile decorations so every advertised axis remains independently
    # realizable even at the smallest 9x10 boundary.
    if profile == 0 and not overrides:
        specs.extend(
            [
                {
                    "role": "canonical_decoration",
                    "color": 7,
                    "shape": _STRAIGHT_TRIOMINO,
                },
                {
                    "role": "canonical_decoration",
                    "color": 6,
                    "shape": ((0, 0), (0, 1), (0, 2), (0, 3)),
                },
            ]
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
        "n_blue_decoys": n_blue_decoys,
        "n_colored_l_decoys": n_colored_l,
        "target_position": target_position,
    }
    if observed != expected:
        raise ValueError(
            f"constructed axes are not observable: expected {expected}, got {observed}"
        )
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


def _decoy_kind(normalized: tuple[tuple[int, int], ...]) -> str:
    for name, orbit in _DECOY_ORBITS.items():
        if normalized in orbit:
            return name
    if len(normalized) == 6:
        return "size6_blob"
    return f"other_size_{len(normalized)}"


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    h, w = len(grid), len(grid[0])
    if not 9 <= h <= 20:
        errors.append(f"grid height {h} outside 9..20")
    if not 10 <= w <= 22:
        errors.append(f"grid width {w} outside 10..22")

    colors = {value for row in grid for value in row}
    if 0 not in colors:
        errors.append("input must contain black background 0")
    illegal = sorted(colors - _ALLOWED_INPUT_COLORS)
    if illegal:
        errors.append(
            f"input colors {illegal} are outside the declared input palette; output colors 2,3,4,8 are reserved"
        )

    components = _components(grid)
    targets = [comp for comp in components if comp["color"] == 1 and comp["orientation"]]
    blue_decoys = [comp for comp in components if comp["color"] == 1 and not comp["orientation"]]
    colored_l_decoys = [
        comp for comp in components if comp["color"] != 1 and comp["orientation"]
    ]
    colored_non_l = [
        comp for comp in components if comp["color"] != 1 and not comp["orientation"]
    ]

    if not 1 <= len(targets) <= 4:
        errors.append(f"expected 1..4 blue exact L-triominoes, found {len(targets)}")
    if len(blue_decoys) > 1:
        errors.append(f"expected at most one blue non-L decoy, found {len(blue_decoys)}")
    if len(colored_l_decoys) > 1:
        errors.append(
            f"expected at most one non-blue L decoy, found {len(colored_l_decoys)}"
        )
    if len(colored_l_decoys) + len(colored_non_l) > 2:
        errors.append("expected at most two non-blue components")

    for component in blue_decoys + colored_non_l:
        size = len(component["cells"])
        if not 1 <= size <= 7:
            errors.append(
                f"non-target component size {size} is outside the admitted 1..7 range"
            )

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
        "blue_decoys": blue_decoys,
        "blue_decoy_kinds": [_decoy_kind(comp["normalized"]) for comp in blue_decoys],
        "colored_l_decoys": colored_l_decoys,
        "colored_non_l": colored_non_l,
        "target_position": "edge" if target_touches_edge else "interior",
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the task's lawful domain, including official cross-color contact."""
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
        "n_blue_decoys": len(analysis["blue_decoys"]),
        "n_colored_l_decoys": len(analysis["colored_l_decoys"]),
        "target_position": analysis["target_position"],
    }


def strict_canonical_like(grid) -> list[str]:
    """Official structural family: canonical dimensions, palettes, and counts."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return list(analysis["errors"])
    reasons = []
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_DIMS:
        reasons.append("canonical inputs use one of the four official dimensions")
    if analysis["colors"] not in _CANONICAL_PALETTES:
        reasons.append("canonical inputs use palette {0,1,7}, {0,1,6}, or {0,1,6,7}")
    if len(analysis["blue_decoys"]) > 1 or any(
        len(component["cells"]) != 6 for component in analysis["blue_decoys"]
    ):
        reasons.append("canonical blue non-L support is absent or one size-six component")
    nonblue = analysis["colored_l_decoys"] + analysis["colored_non_l"]
    if len(nonblue) != 2:
        reasons.append("canonical inputs contain exactly two non-blue components")
    if any(component["color"] not in (6, 7) for component in nonblue):
        reasons.append("canonical decoration colors are 6 and/or 7")
    return reasons


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return {"errors": list(analysis["errors"])}
    return {
        **observe_overrides(grid),
        "errors": [],
        "target_orientations": sorted(
            component["orientation"] for component in analysis["targets"]
        ),
        "blue_decoy_kinds": sorted(analysis["blue_decoy_kinds"]),
        "n_nonblue_components": len(analysis["colored_l_decoys"])
        + len(analysis["colored_non_l"]),
        "palette": sorted(analysis["colors"]),
        "canonical_anchor": not strict_canonical_like(grid),
    }


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _analyze(grid)
    return not analysis.get("errors") and bool(predicate(analysis))


SEMANTIC_WITNESSES = {
    "strict_anchor_rebutting_all_blue": lambda grid: _witness(
        grid,
        lambda a: not strict_canonical_like(grid) and bool(a["blue_decoys"]),
    ),
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
    "blue_straight_triomino_decoy": lambda grid: _witness(
        grid, lambda a: "straight_triomino" in a["blue_decoy_kinds"]
    ),
    "blue_large_non_l_decoy": lambda grid: _witness(
        grid, lambda a: any(len(c["cells"]) > 3 for c in a["blue_decoys"])
    ),
    "nonblue_l_decoy": lambda grid: _witness(
        grid, lambda a: bool(a["colored_l_decoys"])
    ),
    "target_touches_edge": lambda grid: _witness(
        grid, lambda a: a["target_position"] == "edge"
    ),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def rule_mirror(grid):
    """Pure Python mirror for tests/probes only; Racket remains authoritative."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("; ".join(analysis["errors"]))
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        color = _OUTPUT_BY_ORIENTATION[component["orientation"]]
        for row, col in component["cells"]:
            out[row][col] = color
    return out


def _recolor_every_blue_size3(grid):
    """Canonical-fitting shortcut: size three is treated as sufficient."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["color"] != 1 or len(component["cells"]) != 3:
            continue
        color = _OUTPUT_BY_ORIENTATION.get(component["orientation"], 2)
        for row, col in component["cells"]:
            out[row][col] = color
    return out


def _recolor_every_blue_component(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if component["color"] != 1:
            continue
        color = _OUTPUT_BY_ORIENTATION.get(component["orientation"], 2)
        for row, col in component["cells"]:
            out[row][col] = color
    return out


def _recolor_every_l_any_color(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    out = _copy_grid(grid)
    for component in analysis["components"]:
        if not component["orientation"]:
            continue
        color = _OUTPUT_BY_ORIENTATION[component["orientation"]]
        for row, col in component["cells"]:
            out[row][col] = color
    return out


def _leave_orientation_blue(orientation: str):
    def competitor(grid):
        analysis = _analyze(grid)
        if analysis.get("errors"):
            return None
        out = _copy_grid(grid)
        for component in analysis["targets"]:
            if component["orientation"] == orientation:
                continue
            color = _OUTPUT_BY_ORIENTATION[component["orientation"]]
            for row, col in component["cells"]:
                out[row][col] = color
        return out

    return competitor


def _ignore_edge_targets(grid):
    analysis = _analyze(grid)
    if analysis.get("errors"):
        return None
    h, w = analysis["grid_h"], analysis["grid_w"]
    out = _copy_grid(grid)
    for component in analysis["targets"]:
        if any(
            row in (0, h - 1) or col in (0, w - 1)
            for row, col in component["cells"]
        ):
            continue
        color = _OUTPUT_BY_ORIENTATION[component["orientation"]]
        for row, col in component["cells"]:
            out[row][col] = color
    return out


SEMANTIC_RIVALS = {
    "recolor every blue size-three component": _recolor_every_blue_size3,
    "recolor every blue component": _recolor_every_blue_component,
    "recolor every L-triomino regardless of color": _recolor_every_l_any_color,
    "leave missing-NW targets blue": _leave_orientation_blue("missing_nw"),
    "leave missing-NE targets blue": _leave_orientation_blue("missing_ne"),
    "leave missing-SW targets blue": _leave_orientation_blue("missing_sw"),
    "leave missing-SE targets blue": _leave_orientation_blue("missing_se"),
    "ignore edge-touching targets": _ignore_edge_targets,
}
WITNESS_RIVALS = {
    "strict_anchor_rebutting_all_blue": ["recolor every blue component"],
    "target_missing_nw": ["leave missing-NW targets blue"],
    "target_missing_ne": ["leave missing-NE targets blue"],
    "target_missing_sw": ["leave missing-SW targets blue"],
    "target_missing_se": ["leave missing-SE targets blue"],
    "blue_straight_triomino_decoy": [
        "recolor every blue size-three component",
        "recolor every blue component",
    ],
    "blue_large_non_l_decoy": ["recolor every blue component"],
    "nonblue_l_decoy": ["recolor every L-triomino regardless of color"],
    "target_touches_edge": ["ignore edge-touching targets"],
}
CANONICAL_SHORTCUTS = {
    "recolor every blue size-three component": _recolor_every_blue_size3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations that determine the exact blue-L query answer."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    orientations: set[str] = set()
    saw_straight_blue = False
    saw_large_blue = False
    saw_colored_l = False
    saw_edge = False
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
            reasons.append(
                f"demo {index} output disagrees with the exact blue-L orientation rule"
            )
        orientations.update(component["orientation"] for component in analysis["targets"])
        saw_straight_blue |= "straight_triomino" in analysis["blue_decoy_kinds"]
        saw_large_blue |= any(len(c["cells"]) > 3 for c in analysis["blue_decoys"])
        saw_colored_l |= bool(analysis["colored_l_decoys"])
        saw_edge |= analysis["target_position"] == "edge"

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    if reasons:
        return reasons

    missing = sorted(set(_ORIENTATIONS) - orientations)
    if missing:
        reasons.append(f"demonstrations omit target L orientations {missing}")
    if not saw_straight_blue:
        reasons.append(
            "demonstrations never show a blue straight triomino that must stay blue"
        )
    if not saw_large_blue:
        reasons.append(
            "demonstrations never show a blue component larger than three that must stay blue"
        )
    if not saw_colored_l:
        reasons.append(
            "demonstrations never show a non-blue L-triomino that must retain its color"
        )
    if not saw_edge:
        reasons.append("demonstrations never show a target L touching a grid edge")

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            alternative = competitor(query["input"])
            if alternative != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons
