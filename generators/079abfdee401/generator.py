"""Reviewed generator for ARC task 079abfdee401.

The input contains blue objects and gray distractors on a black background.
Only blue connected components that are solid 2x3 or 3x2 rectangles are
recolored red by the canonical Racket rule.  Every ordinary draw includes
shortcut-rebutting blue and gray decoys.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "079abfdee401"
TASK_ID = "079abfdee401"
VERSION = "4.0.0"
RULE_HASH = "a6a896998c77"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "On a black background, recolor to red exactly the blue 4-connected "
    "components that are filled 2x3 or 3x2 rectangles. Preserve blue bars, "
    "non-solid six-cell shapes, wrong-size blue solids, and gray shapes. "
    "Ordinary lessons stay overwhelmingly on the canonical 11x11/12x12, {0,1,5} manifold "
    "and cycle decisive decoy families so the rule cannot collapse to a "
    "color-only, count-only, size-only, solidity-only, or shape-only shortcut."
)

INVARIANTS = [
    "the grid is rectangular, 7..24 cells per side, with palette exactly {0,1,5}",
    "there are 1..6 solid blue 2x3/3x2 target components",
    "at least one blue size-six component is not a target",
    "at least one gray distractor component is present",
    "same-color components are separated and every declared exact axis is observable",
]

HELPFUL_TEXTURES = ("plain", "six_decoys", "wrong_size", "other_color")
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-linked 11 or 12",
        "valid": "7..24",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-linked 11 or 12",
        "valid": "7..24",
    },
    "n_rectangles": {
        "type": "int",
        "default": "canonical-linked 2 or 3",
        "valid": "1..6",
    },
    "texture": {
        "type": "str",
        "default": "sample-index cycle",
        "valid": "plain|six_decoys|wrong_size|other_color",
        "doc": (
            "plain: one blue bar; six_decoys: bar plus non-solid size-six "
            "shape; wrong_size: bar plus blue 2x2; other_color: non-solid "
            "blue size-six shape plus a gray exact-size rectangle"
        ),
    },
}

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

_TARGET_2X3 = tuple((row, col) for row in range(2) for col in range(3))
_TARGET_3X2 = tuple((row, col) for row in range(3) for col in range(2))
_BAR_1X6 = tuple((0, col) for col in range(6))
_BAR_6X1 = tuple((row, 0) for row in range(6))
# Connected, six cells, 3x3 bounding box, not solid.
_NON_SOLID_SIX = ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1))
_WRONG_SIZE_2X2 = ((0, 0), (0, 1), (1, 0), (1, 1))
_GRAY_T = ((0, 0), (0, 1), (0, 2), (1, 1))

_CANONICAL_DIMS = {(11, 11), (12, 12)}
_CANONICAL_GRAY_T = tuple(sorted(_GRAY_T))
_DEFAULT_PROFILES = {
    "easy": ((11, 11, 2), (12, 12, 2), (11, 11, 2), (12, 12, 3)),
    "medium": ((12, 12, 2), (11, 11, 3), (12, 12, 3), (11, 11, 2)),
    "hard": ((12, 12, 3), (11, 11, 3), (12, 12, 3), (12, 12, 2)),
    None: ((11, 11, 2), (12, 12, 2), (12, 12, 3), (11, 11, 3)),
}
_TEXTURES = HELPFUL_TEXTURES
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}


@dataclass(frozen=True)
class _ShapeSpec:
    name: str
    color: int
    cells: tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    result: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            result.append([int(value) for value in row])
        elif isinstance(row, (list, tuple)):
            result.append(list(row))
        else:
            raise ValueError("grid rows must be lists, tuples, or digit strings")
    return result


def _components(grid: Sequence[Sequence[int]], color: int) -> list[set[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        seen = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _DIR4:
                nxt = row + drow, col + dcol
                if nxt in remaining:
                    remaining.remove(nxt)
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(seen)
    return components


def _component_info(cells: set[tuple[int, int]]) -> dict[str, Any]:
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    height = row1 - row0 + 1
    width = col1 - col0 + 1
    normalized = _normalize(cells)
    solid = len(cells) == height * width
    target = solid and ((height, width) in {(2, 3), (3, 2)})
    return {
        "cells": cells,
        "size": len(cells),
        "height": height,
        "width": width,
        "solid": solid,
        "target": target,
        "normalized": normalized,
    }


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    try:
        values = _coerce_grid(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)]}
    if not values or not values[0]:
        return {"errors": ["grid must be non-empty"]}
    width = len(values[0])
    if any(len(row) != width for row in values):
        return {"errors": ["grid must be rectangular"]}
    height = len(values)
    if not 7 <= height <= 24:
        errors.append(f"grid height must be in 7..24, got {height}")
    if not 7 <= width <= 24:
        errors.append(f"grid width must be in 7..24, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in values
        for value in row
    ):
        errors.append("every cell must be an integer ARC color in 0..9")
        return {"errors": errors, "grid": values, "height": height, "width": width}

    palette = {value for row in values for value in row}
    if palette != {0, 1, 5}:
        errors.append(f"input palette must be exactly {{0,1,5}}, got {sorted(palette)}")

    blue = [_component_info(cells) for cells in _components(values, 1)]
    gray = [_component_info(cells) for cells in _components(values, 5)]
    targets = [item for item in blue if item["target"]]
    blue_decoys = [item for item in blue if not item["target"]]
    size_six_decoys = [item for item in blue_decoys if item["size"] == 6]

    if not 1 <= len(targets) <= 6:
        errors.append(f"expected 1..6 blue target rectangles, got {len(targets)}")
    if not blue_decoys:
        errors.append("at least one non-target blue component is required")
    if not size_six_decoys:
        errors.append("at least one blue size-six non-target component is required")
    if not gray:
        errors.append("at least one gray distractor component is required")

    return {
        "errors": errors,
        "grid": values,
        "height": height,
        "width": width,
        "palette": palette,
        "blue": blue,
        "gray": gray,
        "targets": targets,
        "blue_decoys": blue_decoys,
        "size_six_decoys": size_six_decoys,
    }


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in _DEFAULT_PROFILES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")
    for name in ("grid_h", "grid_w", "n_rectangles"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    texture = overrides.get("texture")
    if texture is not None and type(texture) is not str:
        raise ValueError("texture must be a string")


def _draw_exact(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)



def _draw_dimension(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    # Keep ordinary lessons overwhelmingly on the canonical square profile while
    # retaining honest nonzero support for every declared boundary.  draw_choice
    # also makes exact caller overrides observable without a second hidden axis.
    options = tuple(range(7, 25)) + (default,) * 4000
    return ctx.draw_choice(name, options)

def _draw_texture(ctx, overrides: dict[str, Any], default: str) -> str:
    if overrides.get("texture") is not None:
        return ctx.draw_choice("texture", _TEXTURES)
    return ctx.draw_choice("texture", (default,))


def _candidate_placements(
    cells: Sequence[tuple[int, int]], height: int, width: int
) -> list[tuple[tuple[int, int], ...]]:
    shape_h, shape_w = _shape_dims(cells)
    if shape_h > height or shape_w > width:
        return []
    return [
        tuple((row0 + row, col0 + col) for row, col in cells)
        for row0 in range(height - shape_h + 1)
        for col0 in range(width - shape_w + 1)
    ]


def _place_specs(
    height: int,
    width: int,
    specs: Sequence[_ShapeSpec],
    rng,
) -> list[list[int]] | None:
    """Fast randomized greedy placement with 4-separated same-color objects."""
    occupied: set[tuple[int, int]] = set()
    by_color: dict[int, set[tuple[int, int]]] = {}
    placements: list[tuple[_ShapeSpec, tuple[tuple[int, int], ...]]] = []

    ranked = []
    for index, spec in enumerate(specs):
        options = _candidate_placements(spec.cells, height, width)
        if not options:
            return None
        rng.shuffle(options)
        shape_h, shape_w = _shape_dims(spec.cells)
        ranked.append((
            -max(shape_h, shape_w),
            -len(spec.cells),
            len(options),
            index,
            spec,
            options,
        ))
    # Elongated and large shapes are least flexible, so place them first.
    ranked.sort(key=lambda item: item[:4])

    for _neg_span, _neg_area, _nopts, _index, spec, options in ranked:
        same_color = by_color.setdefault(spec.color, set())
        chosen = None
        for placement in options:
            cell_set = set(placement)
            if cell_set & occupied:
                continue
            touches_same = False
            for row, col in cell_set:
                if any((row + drow, col + dcol) in same_color for drow, dcol in _DIR4):
                    touches_same = True
                    break
            if touches_same:
                continue
            chosen = placement
            break
        if chosen is None:
            return None
        cell_set = set(chosen)
        occupied.update(cell_set)
        same_color.update(cell_set)
        placements.append((spec, chosen))

    grid = full_grid(height, width, 0)
    for spec, placement in placements:
        for row, col in placement:
            grid[row][col] = spec.color
    return grid


def _target_shapes(n_rectangles: int, sample_index: int) -> list[tuple[tuple[int, int], ...]]:
    if n_rectangles == 1:
        return [_TARGET_2X3 if sample_index % 2 == 0 else _TARGET_3X2]
    shapes = [_TARGET_2X3, _TARGET_3X2]
    for index in range(2, n_rectangles):
        shapes.append(_TARGET_2X3 if (sample_index + index) % 2 == 0 else _TARGET_3X2)
    return shapes


def _specs_for(
    n_rectangles: int,
    texture: str,
    sample_index: int,
) -> list[_ShapeSpec]:
    specs = [
        _ShapeSpec(f"target_{index}", 1, shape)
        for index, shape in enumerate(_target_shapes(n_rectangles, sample_index))
    ]
    if texture == "plain":
        bar = _BAR_1X6 if sample_index % 2 == 0 else _BAR_6X1
        specs.append(_ShapeSpec("blue_bar", 1, bar))
    elif texture == "six_decoys":
        specs.extend(
            (
                _ShapeSpec("blue_bar", 1, _BAR_1X6),
                _ShapeSpec("blue_non_solid_six", 1, _NON_SOLID_SIX),
            )
        )
    elif texture == "wrong_size":
        specs.extend(
            (
                _ShapeSpec("blue_bar", 1, _BAR_6X1),
                _ShapeSpec("blue_wrong_size", 1, _WRONG_SIZE_2X2),
            )
        )
    elif texture == "other_color":
        specs.extend(
            (
                _ShapeSpec("blue_non_solid_six", 1, _NON_SOLID_SIX),
                _ShapeSpec("gray_exact_target_shape", 5, _TARGET_2X3),
            )
        )
    else:
        raise ValueError(f"unknown texture {texture!r}")
    specs.append(_ShapeSpec("gray_canonical_t", 5, _GRAY_T))
    return specs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profiles = _DEFAULT_PROFILES[difficulty]
    profile = profiles[(sample_index + _BAND_OFFSET[difficulty]) % len(profiles)]
    height = _draw_dimension(ctx, overrides, "grid_h", profile[0])
    width = _draw_dimension(ctx, overrides, "grid_w", profile[1])
    n_rectangles = _draw_exact(ctx, overrides, "n_rectangles", profile[2], 1, 6)
    texture_default = _TEXTURES[(sample_index + _BAND_OFFSET[difficulty]) % len(_TEXTURES)]
    texture = _draw_texture(ctx, overrides, texture_default)

    specs = _specs_for(n_rectangles, texture, sample_index)
    # Multiple deterministic search orders make dense but valid boundary cases
    # reliable without silently changing a requested exact axis.
    grid = None
    for attempt in range(256):
        rng = ctx.draw_rng(
            f"placement|attempt={attempt}|dims={height}x{width}|"
            f"n={n_rectangles}|texture={texture}"
        )
        attempt_specs = list(specs)
        if attempt:
            rng.shuffle(attempt_specs)
        grid = _place_specs(height, width, attempt_specs, rng)
        if grid is not None:
            break
    if grid is None:
        explicit = sorted(name for name, value in overrides.items() if value is not None)
        raise ValueError(
            "requested combination cannot fit separated targets and decisive "
            f"distractors: dims={height}x{width}, n_rectangles={n_rectangles}, "
            f"texture={texture!r}, explicit={explicit}"
        )

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed["n_rectangles"] != n_rectangles:
        raise AssertionError(
            f"target-count drift: requested {n_rectangles}, observed "
            f"{observed['n_rectangles']}"
        )
    return grid


def _infer_texture(analysis: dict[str, Any]) -> str:
    if any(item["target"] for item in analysis["gray"]):
        return "other_color"
    if any(item["solid"] and item["size"] != 6 for item in analysis["blue_decoys"]):
        return "wrong_size"
    if any(item["size"] == 6 and not item["solid"] for item in analysis["blue_decoys"]):
        return "six_decoys"
    return "plain"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors or not isinstance(meta, dict):
        return errors
    requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rectangles": len(analysis["targets"]),
        "texture": _infer_texture(analysis),
    }
    for name, actual in observed.items():
        expected = requested.get(name)
        if expected is not None and expected != actual:
            errors.append(f"meta {name} requested {expected!r}, observed {actual!r}")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe overrides: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_rectangles": len(analysis["targets"]),
        "texture": _infer_texture(analysis),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis.get("errors", []))
    if errors:
        return errors
    dims = analysis["height"], analysis["width"]
    if dims not in _CANONICAL_DIMS:
        errors.append(f"dimensions {dims!r} are outside canonical 11x11/12x12")
    if len(analysis["targets"]) not in (2, 3):
        errors.append("canonical inputs contain exactly two or three targets")
    gray_shapes = [item["normalized"] for item in analysis["gray"]]
    if gray_shapes != [_CANONICAL_GRAY_T]:
        errors.append("canonical inputs contain exactly one gray T distractor")
    if not 1 <= len(analysis["blue_decoys"]) <= 2:
        errors.append("canonical inputs contain one or two blue decoy components")
    return errors


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror; the Racket program remains output authority."""
    analysis = _analyze(grid)
    if analysis.get("errors"):
        raise ValueError("invalid lesson: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in analysis["grid"]]
    for target in analysis["targets"]:
        for row, col in target["cells"]:
            output[row][col] = 2
    return output


def _has_target_shape(grid, dims: tuple[int, int]) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        (item["height"], item["width"]) == dims for item in analysis["targets"]
    )


def _has_bar_decoy(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        item["size"] == 6 and (item["height"], item["width"]) in {(1, 6), (6, 1)}
        for item in analysis["blue_decoys"]
    )


def _has_non_solid_six_decoy(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        item["size"] == 6 and not item["solid"]
        for item in analysis["blue_decoys"]
    )


def _has_wrong_size_solid_decoy(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(
        item["solid"] and item["size"] != 6
        for item in analysis["blue_decoys"]
    )


def _has_gray_exact_target_shape(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and any(item["target"] for item in analysis["gray"])


SEMANTIC_WITNESSES = {
    "horizontal_2x3_target": lambda grid: _has_target_shape(grid, (2, 3)),
    "vertical_3x2_target": lambda grid: _has_target_shape(grid, (3, 2)),
    "blue_size6_bar_survives": _has_bar_decoy,
    "blue_size6_non_solid_survives": _has_non_solid_six_decoy,
    "blue_wrong_size_solid_survives": _has_wrong_size_solid_decoy,
    "gray_exact_target_shape_survives": _has_gray_exact_target_shape,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject episodes that leave the strongest rival rules unresolved."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    analyses: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is missing input/output")
            continue
        analysis = _analyze(pair["input"])
        if analysis.get("errors"):
            errors.append(f"demo {index} input is malformed: {analysis['errors'][:1]}")
            continue
        try:
            expected = rule_mirror(pair["input"])
            actual = _coerce_grid(pair["output"])
        except (TypeError, ValueError) as exc:
            errors.append(f"demo {index} cannot be checked: {exc}")
            continue
        if expected != actual:
            errors.append(f"demo {index} output does not follow the exact-component rule")
        if expected == analysis["grid"]:
            errors.append(f"demo {index} is an identity transformation")
        analyses.append(analysis)

    if len(analyses) == len(demos):
        if not any(
            (item["height"], item["width"]) == (2, 3)
            for analysis in analyses
            for item in analysis["targets"]
        ):
            errors.append("demos omit horizontal 2x3 targets")
        if not any(
            (item["height"], item["width"]) == (3, 2)
            for analysis in analyses
            for item in analysis["targets"]
        ):
            errors.append("demos omit vertical 3x2 targets")
        if not any(
            item["size"] == 6 and not item["target"]
            for analysis in analyses
            for item in analysis["blue_decoys"]
        ):
            errors.append("demos do not refute the any-blue-size-six rival")
        if not any(_has_bar_decoy(analysis["grid"]) for analysis in analyses):
            errors.append("demos omit a wrong-bounding-box size-six bar")
        if not any(_has_non_solid_six_decoy(analysis["grid"]) for analysis in analyses):
            errors.append("demos omit a non-solid size-six blue decoy")
        if not any(_has_wrong_size_solid_decoy(analysis["grid"]) for analysis in analyses):
            errors.append("demos omit a wrong-size solid blue decoy")
        if not any(_has_gray_exact_target_shape(analysis["grid"]) for analysis in analyses):
            errors.append("demos do not refute recoloring target-shaped objects of any color")
        if len({(analysis["height"], analysis["width"]) for analysis in analyses}) < 2:
            errors.append("demos permit a fixed-grid-size shortcut")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing its input")
    else:
        query_analysis = _analyze(query["input"])
        if query_analysis.get("errors"):
            errors.append("query input is malformed")
    return errors


def mutation_fixtures():
    """Task-linked near-misses that a structural self_check must reject."""
    base = generate(9091, 0, difficulty="medium", texture="six_decoys")
    analysis = _analyze(base)
    fixtures = []

    no_targets = [row[:] for row in base]
    for target in analysis["targets"]:
        for row, col in target["cells"]:
            no_targets[row][col] = 0
    fixtures.append(("no_target_components", no_targets))

    no_blue_decoy = [row[:] for row in base]
    for decoy in analysis["blue_decoys"]:
        for row, col in decoy["cells"]:
            no_blue_decoy[row][col] = 5
    fixtures.append(("all_blue_components_are_targets", no_blue_decoy))

    no_gray = [row[:] for row in base]
    for gray in analysis["gray"]:
        for row, col in gray["cells"]:
            no_gray[row][col] = 0
    fixtures.append(("gray_distractor_removed", no_gray))

    no_size_six_decoy = [row[:] for row in base]
    for decoy in analysis["size_six_decoys"]:
        row, col = max(decoy["cells"])
        no_size_six_decoy[row][col] = 0
    fixtures.append(("size_six_decoys_damaged", no_size_six_decoy))

    premature_red = [row[:] for row in base]
    for row, col in analysis["targets"][0]["cells"]:
        premature_red[row][col] = 2
    fixtures.append(("target_already_recolored_in_input", premature_red))
    return fixtures
