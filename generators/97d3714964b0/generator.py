"""Generator for task 97d3714964b0.

The selected Racket rule recolors each 4-connected color-7 component from its
own bounding-box occupancy: a component with a zero-valued bbox interior becomes
4, while a completely filled bbox becomes 2.  This sampler stays on a clean
rectangular subdomain (hollow frames and solid rectangles) and deliberately
pairs at least one hollow and one solid object with identical bbox dimensions,
so size, height, and position are not valid shortcuts for the topology test.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "97d3714964b0"
TASK_ID = GENERATOR_ID
RULE_HASH = "3c6d01646411"
VERSION = "3.0.0"
SUMMARY = (
    "A 7-14 by 9-14 zero-background grid contains one or two hollow color-7 "
    "rectangular frames and one or two solid color-7 rectangles, separated by "
    "blank rows/columns.  At least one hollow/solid pair has the same bbox "
    "dimensions.  Recolor each 7-component independently: a bbox with an empty "
    "interior cell becomes yellow (4); a fully filled bbox becomes red (2)."
)

INVARIANTS = [
    "one or two hollow color-7 rectangular frames",
    "one or two solid color-7 rectangles",
    "distinct 7-components are separated by a blank row or column",
    "at least one hollow and solid component share bbox dimensions",
    "only colors 0 and 7 occur in generated inputs",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted to canonical height 8", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "weighted to canonical width 9", "valid": "9..14"},
    "n_hollow": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
    "n_solid": {"type": "int", "default": "difficulty-weighted 1..2", "valid": "1..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, int]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def _weighted_axis(ctx, name: str, lo: int, hi: int, favored: tuple[int, ...]) -> int:
    """Draw every declared value in every band while strongly anchoring a core."""
    options = list(range(lo, hi + 1)) + list(favored)
    return ctx.draw_choice(name, options)


def _draw_frame(grid, r0: int, c0: int, height: int, width: int) -> None:
    r1, c1 = r0 + height - 1, c0 + width - 1
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if r in (r0, r1) or c in (c0, c1):
                grid[r][c] = 7


def _draw_solid(grid, r0: int, c0: int, height: int, width: int) -> None:
    for r in range(r0, r0 + height):
        for c in range(c0, c0 + width):
            grid[r][c] = 7


def _regions(height: int, width: int, split_r: int, split_c: int):
    """Four disjoint slots separated by one full blank row and column."""
    return (
        (0, split_r - 1, 0, split_c - 1),
        (0, split_r - 1, split_c + 1, width - 1),
        (split_r + 1, height - 1, 0, split_c - 1),
        (split_r + 1, height - 1, split_c + 1, width - 1),
    )


def _region_dims(region):
    r0, r1, c0, c1 = region
    return r1 - r0 + 1, c1 - c0 + 1


def _place_bbox(ctx, grid, region, size, label: str, kind: str) -> None:
    rr0, rr1, cc0, cc1 = region
    height, width = size
    rng = ctx.draw_rng(f"position:{label}")
    r0 = rng.randint(rr0, rr1 - height + 1)
    c0 = rng.randint(cc0, cc1 - width + 1)
    if kind == "hollow":
        _draw_frame(grid, r0, c0, height, width)
    else:
        _draw_solid(grid, r0, c0, height, width)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Every band retains every documented value.  Repeated anchors make exact
    # canonical profiles common without hiding the broad support.
    height = _weighted_axis(ctx, "grid_h", 7, 14, (8,) * 12 + (7,) * 3 + (11,) * 3)
    width = _weighted_axis(ctx, "grid_w", 9, 14, (9,) * 14 + (10,) * 4)
    count_favored = (1,) * 8 if difficulty == "easy" else ((2,) * 8 if difficulty == "hard" else (1, 2) * 4)
    n_hollow = _weighted_axis(ctx, "n_hollow", 1, 2, count_favored)
    n_solid = _weighted_axis(ctx, "n_solid", 1, 2, count_favored)

    split_r = ctx.draw_rng("row_split").randint(3, height - 4)
    split_c = ctx.draw_rng("column_split").randint(3, width - 4)
    regions = _regions(height, width, split_r, split_c)

    kinds = ["hollow"] * n_hollow + ["solid"] * n_solid
    assignment_rng = ctx.draw_rng("slot_assignment")
    slots = assignment_rng.sample(range(4), len(kinds))
    assignment_rng.shuffle(kinds)
    placements = [{"kind": kind, "slot": slot} for kind, slot in zip(kinds, slots)]

    hollow_index = next(i for i, obj in enumerate(placements) if obj["kind"] == "hollow")
    solid_index = next(i for i, obj in enumerate(placements) if obj["kind"] == "solid")
    hollow_region = regions[placements[hollow_index]["slot"]]
    solid_region = regions[placements[solid_index]["slot"]]
    common_h = min(5, _region_dims(hollow_region)[0], _region_dims(solid_region)[0])
    common_w = min(5, _region_dims(hollow_region)[1], _region_dims(solid_region)[1])
    pair_rng = ctx.draw_rng("paired_bbox_size")
    paired_size = (pair_rng.randint(3, common_h), pair_rng.randint(3, common_w))

    grid = full_grid(height, width, 0)
    for index, obj in enumerate(placements):
        region = regions[obj["slot"]]
        region_h, region_w = _region_dims(region)
        if index in (hollow_index, solid_index):
            size = paired_size
        else:
            size_rng = ctx.draw_rng(f"bbox_size:{index}:{obj['kind']}")
            minimum = 3 if obj["kind"] == "hollow" else 2
            size = (
                size_rng.randint(minimum, min(5, region_h)),
                size_rng.randint(minimum, min(5, region_w)),
            )
        _place_bbox(ctx, grid, region, size, f"{index}:{obj['kind']}:{obj['slot']}", obj["kind"])
    return grid


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 7) for row in grid for value in row):
        return ["cells must be integer colors 0 or 7"]
    if not 7 <= len(grid) <= 14 or not 9 <= width <= 14:
        return [f"grid dimensions {len(grid)}x{width} outside 7..14 by 9..14"]
    return []


def _solid_rectangle(comp) -> bool:
    r0, c0, r1, c1 = comp["bbox"]
    return len(comp["cells"]) == (r1 - r0 + 1) * (c1 - c0 + 1)


def _hollow_frame(grid, comp) -> bool:
    r0, c0, r1, c1 = comp["bbox"]
    if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
        return False
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
    return set(comp["cells"]) == perimeter and all(grid[r][c] == 0 for r, c in interior)


def _classified_components(grid):
    classified = []
    for comp in components(grid, colors={7}):
        if _solid_rectangle(comp):
            kind = "solid"
        elif _hollow_frame(grid, comp):
            kind = "hollow"
        else:
            kind = "invalid"
        classified.append((kind, comp))
    return classified


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _grid_errors(grid)
    if errors:
        return errors

    classified = _classified_components(grid)
    invalid = [comp["bbox"] for kind, comp in classified if kind == "invalid"]
    if invalid:
        errors.append(f"7-components are neither solid rectangles nor empty-interior frames: {invalid}")
    n_hollow = sum(kind == "hollow" for kind, _ in classified)
    n_solid = sum(kind == "solid" for kind, _ in classified)
    if not 1 <= n_hollow <= 2:
        errors.append(f"expected 1..2 hollow 7-frames, got {n_hollow}")
    if not 1 <= n_solid <= 2:
        errors.append(f"expected 1..2 solid 7-rectangles, got {n_solid}")

    hollow_dims = {
        (comp["bbox"][2] - comp["bbox"][0] + 1, comp["bbox"][3] - comp["bbox"][1] + 1)
        for kind, comp in classified
        if kind == "hollow"
    }
    solid_dims = {
        (comp["bbox"][2] - comp["bbox"][0] + 1, comp["bbox"][3] - comp["bbox"][1] + 1)
        for kind, comp in classified
        if kind == "solid"
    }
    # Canonical examples need not carry this teaching witness; generated inputs
    # do, and observe_overrides/tests verify it there.  Do not reject canonical
    # task inputs merely because their shapes differ.
    if meta and meta.get("require_teaching_witness") and not (hollow_dims & solid_dims):
        errors.append("missing same-bbox hollow/solid teaching witness")
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    classified = _classified_components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_hollow": sum(kind == "hollow" for kind, _ in classified),
        "n_solid": sum(kind == "solid" for kind, _ in classified),
    }


def strict_canonical_like(grid):
    """The declared sampler manifold: lawful frame/rectangle topology inputs."""
    return self_check(grid)


def _paint_by(grid, predicate):
    out = deepcopy(grid)
    for comp in components(grid, colors={7}):
        color = 4 if predicate(comp) else 2
        for r, c in comp["cells"]:
            out[r][c] = color
    return out


def _bbox_area_gt4(grid):
    return _paint_by(
        grid,
        lambda comp: (comp["bbox"][2] - comp["bbox"][0] + 1)
        * (comp["bbox"][3] - comp["bbox"][1] + 1)
        > 4,
    )


def _component_size_ge8(grid):
    return _paint_by(grid, lambda comp: len(comp["cells"]) >= 8)


def _bbox_height_ge3(grid):
    return _paint_by(grid, lambda comp: comp["bbox"][2] - comp["bbox"][0] + 1 >= 3)


def _same_bbox_hollow_and_solid(grid) -> bool:
    if self_check(grid):
        return False
    classified = _classified_components(grid)
    hollow_dims = {
        (comp["bbox"][2] - comp["bbox"][0] + 1, comp["bbox"][3] - comp["bbox"][1] + 1)
        for kind, comp in classified
        if kind == "hollow"
    }
    solid_dims = {
        (comp["bbox"][2] - comp["bbox"][0] + 1, comp["bbox"][3] - comp["bbox"][1] + 1)
        for kind, comp in classified
        if kind == "solid"
    }
    return bool(hollow_dims & solid_dims)


SEMANTIC_RIVALS = {
    "bbox_area_gt4": _bbox_area_gt4,
    "component_size_ge8": _component_size_ge8,
    "bbox_height_ge3": _bbox_height_ge3,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"same_bbox_hollow_and_solid": _same_bbox_hollow_and_solid}
WITNESS_RIVALS = {"same_bbox_hollow_and_solid": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a declared canonical-fitting rival survives."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
