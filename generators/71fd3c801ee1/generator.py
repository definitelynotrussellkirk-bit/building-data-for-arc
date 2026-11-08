"""Generator for ARC task 71fd3c801ee1 — repeated feature classes.

Each nonzero 4-connected object is described by

    (area, number of enclosed holes, reflection-symmetry class)

where symmetry class is 0=neither, 1=row reflection only, 2=column
reflection only, and 3=both.  Every object whose complete triple occurs at
least twice is recolored cyan (8); objects with a unique triple are unchanged.

The curriculum is deliberately counterfactual.  Every generated grid contains
(1) two different outlines with one shared complete triple, (2) a unique
object with the same area and hole count but different symmetry, and (3) a
unique object with the same area and symmetry but different hole count.  Thus
exact-outline, area-only, area+holes, and area+symmetry shortcuts all make an
observable mistake on every ordinary sample.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "71fd3c801ee1"
TASK_ID = "71fd3c801ee1"
RULE_HASH = "12f0cca6ed07"
VERSION = "3.0.0"
SUMMARY = (
    "Five separated, distinctly colored objects on the canonical 12x18 / "
    "6-color profile.  Group objects by (area, enclosed-hole count, row/column "
    "reflection-symmetry class) and recolor every member of a repeated class "
    "cyan (8).  The v3 curriculum always uses different-outline feature twins "
    "plus same-area one-feature decoys, directly refuting exact-shape, "
    "area-only, area+holes, and area+symmetry shortcuts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "input is 12x18 with background 0 and exactly five separated objects",
    "the five objects use five distinct nonzero colors and input color 8 is absent",
    "exactly one complete (area, holes, symmetry-class) triple occurs twice",
    "the repeated class contains two different normalized outlines",
    "unique same-area decoys make holes and symmetry independently load-bearing",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ()

TARGET_FAMILIES: dict[str, tuple[int, int, int]] = {
    "plain_asym8": (8, 0, 0),
    "hole_asym8": (8, 1, 0),
    "plain_row9": (9, 0, 1),
    "hole_row9": (9, 1, 1),
    "hole_col9": (9, 1, 2),
}
_TRIPLE_TO_FAMILY = {triple: name for name, triple in TARGET_FAMILIES.items()}

AXES = {
    "target_family": {
        "type": "str",
        "default": "cyclic semantic curriculum",
        "valid": "plain_asym8|hole_asym8|plain_row9|hole_row9|hole_col9",
        "doc": (
            "The sole repeated complete feature triple; exactly observable "
            "from the returned grid."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Shape = tuple[tuple[int, int], ...]
Triple = tuple[int, int, int]

# Compact, hand-audited polyomino banks.  Every shape fits a 4x4 lesson slot.
# Multiple entries for target triples are intentionally different normalized
# outlines, not translated copies.
_SHAPES: dict[Triple, tuple[Shape, ...]] = {
    (4, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
    ),
    (8, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (8, 0, 3): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2)),
    ),
    (8, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (3, 0)),
    ),
    (8, 1, 3): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 0, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 0, 1): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 0, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 2), (3, 0), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0), (3, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
    ),
    (9, 1, 0): (
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
    (9, 1, 1): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (2, 3)),
    ),
    (9, 1, 2): (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
    ),
}

# For each target: first decoy shares (area, holes) but has different symmetry;
# second shares (area, symmetry) but has a different hole count.
_FAMILY_DECOYS: dict[str, tuple[Triple, Triple]] = {
    "plain_asym8": ((8, 0, 3), (8, 1, 0)),
    "hole_asym8": ((8, 1, 3), (8, 0, 0)),
    "plain_row9": ((9, 0, 0), (9, 1, 1)),
    "hole_row9": ((9, 1, 0), (9, 0, 1)),
    "hole_col9": ((9, 1, 0), (9, 0, 2)),
}

# Inclusive interior rectangles.  They are separated by at least one complete
# background row/column, so every placement is unambiguously a separate object.
_SLOT_REGIONS = (
    (1, 4, 1, 5),
    (1, 4, 7, 11),
    (1, 4, 13, 16),
    (7, 10, 2, 6),
    (7, 10, 10, 14),
)


def _norm(cells: Iterable[tuple[int, int]]) -> Shape:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _feature_triple(cells: Iterable[tuple[int, int]]) -> Triple:
    shape = set(_norm(cells))
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1

    holes = 0
    seen: set[tuple[int, int]] = set()
    for row0 in range(height):
        for col0 in range(width):
            if (row0, col0) in shape or (row0, col0) in seen:
                continue
            region: list[tuple[int, int]] = []
            stack = [(row0, col0)]
            seen.add((row0, col0))
            while stack:
                row, col = stack.pop()
                region.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in shape
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if all(
                0 < row < height - 1 and 0 < col < width - 1
                for row, col in region
            ):
                holes += 1

    row_sym = all((height - 1 - row, col) in shape for row, col in shape)
    col_sym = all((row, width - 1 - col) in shape for row, col in shape)
    symmetry = 3 if row_sym and col_sym else 1 if row_sym else 2 if col_sym else 0
    return (len(shape), holes, symmetry)


def _flip(shape: Shape, code: int) -> Shape:
    """Identity / vertical / horizontal / 180-degree flip, preserving class."""
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    cells = []
    for row, col in shape:
        if code & 1:
            row = height - 1 - row
        if code & 2:
            col = width - 1 - col
        cells.append((row, col))
    return _norm(cells)


def _shape_size(shape: Shape) -> tuple[int, int]:
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return "ragged grid"
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            return "cells must be integer ARC colors 0..9"
    return None


def _components(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            if grid[row0][col0] == 0 or (row0, col0) in seen:
                continue
            stack = [(row0, col0)]
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                colors.add(int(grid[row][col]))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (row + dr, col + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            shape = _norm(cells)
            components.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": frozenset(colors),
                    "color": next(iter(colors)) if len(colors) == 1 else None,
                    "shape": shape,
                    "triple": _feature_triple(shape),
                }
            )
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    structural = _grid_error(grid)
    if structural is not None:
        return {"errors": [structural], "components": []}

    height = len(grid)
    width = len(grid[0])
    components = _components(grid)
    errors: list[str] = []

    if len(components) != 5:
        errors.append(f"expected exactly five objects, found {len(components)}")
    if any(component["color"] is None for component in components):
        errors.append("each object must be monochromatic")
    colors = [component["color"] for component in components if component["color"] is not None]
    if len(set(colors)) != len(colors):
        errors.append("each object must use a distinct nonzero color")
    if 8 in colors:
        errors.append("input color 8 is reserved for the recolored output")

    for component in components:
        size = len(component["cells"])
        if not 3 <= size <= 12:
            errors.append(f"object area {size} outside canonical range 3..12")
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in component["cells"]
        ):
            errors.append("objects must not touch the grid border")
            break

    # A one-cell Chebyshev halo prevents diagonal or cardinal contact from
    # turning object segmentation into an incidental convention.
    for left_index, left in enumerate(components):
        for right in components[left_index + 1 :]:
            if any(
                max(abs(r1 - r2), abs(c1 - c2)) <= 1
                for r1, c1 in left["cells"]
                for r2, c2 in right["cells"]
            ):
                errors.append("objects must be separated by a one-cell background halo")
                break
        if errors and errors[-1].startswith("objects must be separated"):
            break

    triples = [component["triple"] for component in components]
    counts = Counter(triples)
    if components and not any(count > 1 for count in counts.values()):
        errors.append("at least one complete feature triple must repeat")
    if components and not any(count == 1 for count in counts.values()):
        errors.append("at least one complete feature triple must remain unique")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": frozenset(value for row in grid for value in row),
        "components": components,
        "triple_counts": counts,
    }


def _strict_errors(grid: Any) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if (analysis["height"], analysis["width"]) != (12, 18):
        errors.append("strict profile is exactly 12x18")
    if len(analysis["palette"]) != 6:
        errors.append("strict profile uses background plus five object colors")

    components = analysis["components"]
    counts: Counter[Triple] = analysis["triple_counts"]
    repeated = [triple for triple, count in counts.items() if count > 1]
    if len(repeated) != 1 or counts[repeated[0]] != 2:
        errors.append("strict profile has exactly one repeated pair")
    elif len({component["shape"] for component in components if component["triple"] == repeated[0]}) < 2:
        errors.append("strict repeated pair must use different normalized outlines")

    projection_specs: tuple[tuple[str, Callable[[Triple], Any]], ...] = (
        ("area", lambda triple: triple[0]),
        ("area+holes", lambda triple: triple[:2]),
        ("area+symmetry", lambda triple: (triple[0], triple[2])),
    )
    for label, project in projection_specs:
        projected = Counter(project(component["triple"]) for component in components)
        if not any(
            counts[component["triple"]] == 1 and projected[project(component["triple"])] > 1
            for component in components
        ):
            errors.append(f"strict profile lacks a unique-triple {label} collision")
    return errors


def _family_for_grid(grid: Any) -> str | None:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    repeated = [triple for triple, count in analysis["triple_counts"].items() if count > 1]
    if len(repeated) != 1:
        return None
    return _TRIPLE_TO_FAMILY.get(repeated[0])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    families = tuple(TARGET_FAMILIES)
    if overrides.get("target_family") is not None:
        family = ctx.draw_choice("target_family", families)
    else:
        band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
        scheduled = families[(int(sample_index) + band_offset) % len(families)]
        family = ctx.draw_choice("target_family", (scheduled,))

    target = TARGET_FAMILIES[family]
    decoy_holes, decoy_symmetry = _FAMILY_DECOYS[family]
    shape_rng = ctx.draw_rng("shape_selection")
    target_shapes = shape_rng.sample(list(_SHAPES[target]), 2)
    shapes = [
        target_shapes[0],
        target_shapes[1],
        shape_rng.choice(_SHAPES[decoy_holes]),
        shape_rng.choice(_SHAPES[decoy_symmetry]),
        shape_rng.choice(_SHAPES[(4, 0, 0)]),
    ]
    flip_code = ctx.draw_rng("shape_flip").randrange(4)
    shapes = [_flip(shape, flip_code) for shape in shapes]

    layout_rng = ctx.draw_rng("layout")
    specs = list(shapes)
    layout_rng.shuffle(specs)
    colors = ctx.draw_rng("colors").sample([1, 2, 3, 4, 5, 6, 7, 9], 5)

    grid = full_grid(12, 18, 0)
    for shape, color, region in zip(specs, colors, _SLOT_REGIONS):
        row_lo, row_hi, col_lo, col_hi = region
        shape_h, shape_w = _shape_size(shape)
        if shape_h > row_hi - row_lo + 1 or shape_w > col_hi - col_lo + 1:
            raise RuntimeError(f"shape {shape!r} does not fit its constructive slot")
        row0 = layout_rng.randint(row_lo, row_hi - shape_h + 1)
        col0 = layout_rng.randint(col_lo, col_hi - shape_w + 1)
        for row, col in shape:
            grid[row0 + row][col0 + col] = color

    errors = _strict_errors(grid)
    if errors:
        raise RuntimeError("internal constructive error: " + "; ".join(errors))
    if _family_for_grid(grid) != family:
        raise RuntimeError("constructed repeated class does not match target_family")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the documented five-object teaching grammar and canonical pairs."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Canonical task manifold; production-only curriculum checks stay internal."""
    return self_check(grid)


def _recolor_by_key(grid: Any, key: Callable[[dict[str, Any]], Any]):
    if _grid_error(grid) is not None:
        return None
    components = _components(grid)
    keys = [key(component) for component in components]
    counts = Counter(keys)
    output = [list(row) for row in grid]
    for component, value in zip(components, keys):
        if counts[value] > 1:
            for row, col in component["cells"]:
                output[row][col] = 8
    return output


def rule_mirror(grid):
    """Pure Python mirror for tests; the selected Racket program remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = _recolor_by_key(grid, lambda component: component["triple"])
    assert output is not None
    return output


def observe_overrides(grid) -> dict[str, str]:
    family = _family_for_grid(grid)
    if family is None:
        errors = self_check(grid)
        detail = "; ".join(errors) if errors else "repeated triple is not a declared family"
        raise ValueError(detail)
    return {"target_family": family}


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_shape": [analysis["height"], analysis["width"]],
        "palette_size": len(analysis["palette"]),
        "target_family": _family_for_grid(grid),
        "triples": [list(component["triple"]) for component in analysis["components"]],
        "shapes": [
            [list(cell) for cell in component["shape"]]
            for component in analysis["components"]
        ],
    }


def _rival_exact_shape(grid):
    return _recolor_by_key(grid, lambda component: component["shape"])


def _rival_same_area(grid):
    return _recolor_by_key(grid, lambda component: component["triple"][0])


def _rival_same_area_and_holes(grid):
    return _recolor_by_key(grid, lambda component: component["triple"][:2])


def _rival_same_area_and_symmetry(grid):
    return _recolor_by_key(
        grid,
        lambda component: (component["triple"][0], component["triple"][2]),
    )


SEMANTIC_RIVALS = {
    "exact_shape": _rival_exact_shape,
    "same_area": _rival_same_area,
    "same_area_and_holes": _rival_same_area_and_holes,
    "same_area_and_symmetry": _rival_same_area_and_symmetry,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "same_area": _rival_same_area,
    "same_area_and_holes": _rival_same_area_and_holes,
    "same_area_and_symmetry": _rival_same_area_and_symmetry,
}


def _different_outline_twins(grid) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    for triple, count in analysis["triple_counts"].items():
        if count > 1:
            shapes = {
                component["shape"]
                for component in analysis["components"]
                if component["triple"] == triple
            }
            if len(shapes) > 1:
                return True
    return False


def _unique_projection_collision(grid, project: Callable[[Triple], Any]) -> bool:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return False
    projected = Counter(project(component["triple"]) for component in analysis["components"])
    return any(
        analysis["triple_counts"][component["triple"]] == 1
        and projected[project(component["triple"])] > 1
        for component in analysis["components"]
    )


SEMANTIC_WITNESSES = {
    "different_outline_equal_triple": _different_outline_twins,
    "same_area_unique_triple": lambda grid: _unique_projection_collision(
        grid, lambda triple: triple[0]
    ),
    "same_area_holes_unique_triple": lambda grid: _unique_projection_collision(
        grid, lambda triple: triple[:2]
    ),
    "same_area_symmetry_unique_triple": lambda grid: _unique_projection_collision(
        grid, lambda triple: (triple[0], triple[2])
    ),
}
WITNESS_RIVALS = {
    "different_outline_equal_triple": ["exact_shape"],
    "same_area_unique_triple": ["same_area"],
    "same_area_holes_unique_triple": ["same_area_and_holes"],
    "same_area_symmetry_unique_triple": ["same_area_and_symmetry"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report a documented rival that fits every demo but differs on query."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            truth = rule_mirror(demo.get("input"))
        except (TypeError, ValueError) as exc:
            reasons.append(f"demo {index}: invalid input: {exc}")
            continue
        if demo.get("output") != truth:
            reasons.append(f"demo {index}: output disagrees with complete feature triple")
    try:
        query_truth = rule_mirror(query.get("input"))
    except (TypeError, ValueError) as exc:
        reasons.append(f"query: invalid input: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_truth:
        reasons.append("query: output disagrees with complete feature triple")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} fits every demonstration but changes the query"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small structural impostors that exercise self_check diagnostics."""
    base = generate(71_003, 2, difficulty="medium")
    analysis = _analyze(base)
    components = analysis["components"]

    blank = [[0 for _ in row] for row in base]

    four_objects = [row[:] for row in base]
    for row, col in components[0]["cells"]:
        four_objects[row][col] = 0

    input_cyan = [row[:] for row in base]
    row, col = components[0]["cells"][0]
    for rr, cc in components[0]["cells"]:
        input_cyan[rr][cc] = 8

    mixed_component = [row[:] for row in base]
    row, col = components[1]["cells"][0]
    mixed_component[row][col] = components[0]["color"]

    border_component = [row[:] for row in base]
    border_component[0][0] = 9 if 9 not in analysis["palette"] else 8

    reused_color = [row[:] for row in base]
    for row, col in components[2]["cells"]:
        reused_color[row][col] = components[0]["color"]

    return [
        ("blank", blank),
        ("four_objects", four_objects),
        ("input_cyan", input_cyan),
        ("mixed_component", mixed_component),
        ("border_component", border_component),
        ("reused_color", reused_color),
    ]
