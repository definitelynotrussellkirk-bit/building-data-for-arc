"""Generate lessons for recoloring corners of solid blue rectangles.

The selected Racket rule inspects monochromatic blue (1) components.  A blue
component is transformed only when it exactly fills a bounding box whose height
and width are both at least two; exactly the four corner cells of that box are
recolored red (2).  Other blue shapes and every non-blue object are unchanged.

The canonical task needs negative evidence to make both predicates observable:
one published input contains a large irregular blue component, while every
published input also contains non-blue distractors.  The curriculum below keeps
those branches explicit.  Every sliding three-profile lesson contains (a) more
than one qualifying rectangle, (b) a non-rectangular blue component, (c) a
solid non-blue rectangle, (d) an edge-touching target, and (e) a 2x2 target.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c93dc1552b3"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "3b0c50f6c708"

SUMMARY = (
    "On a zero-background grid, find each blue(1) four-connected component "
    "that is a solid filled rectangle at least 2x2. Recolor exactly that "
    "rectangle's four corner cells red(2). Leave its non-corner blue cells, "
    "irregular blue components, and all non-blue distractors unchanged."
)

INVARIANTS = [
    "background is 0 and the transformed source color is blue 1",
    "only solid blue components with height and width at least two qualify",
    "exactly four qualifying-component corner cells become red 2",
    "irregular blue components and non-blue objects remain unchanged",
    "ordinary lessons use exactly four input colors and canonical grid sizes",
]

Grid = list[list[int]]
Cell = tuple[int, int]

# B marks blue cells.  Whether a B component is a target is deliberately
# inferred from its geometry, not encoded separately.  D is a multi-cell
# distractor and M is a singleton distractor; their literal colors vary.
_PROFILE_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "easy",
        "easy_pair_8x10",
        (
            ".........M",
            ".BBB......",
            ".BBB......",
            "....BB....",
            "....B.BB..",
            "DD....BB..",
            "DD....BB..",
            "..........",
        ),
    ),
    (
        "easy",
        "easy_negative_8x9",
        (
            "BB.......",
            "BB.......",
            "DD.......",
            "DD..BBB..",
            "....BBB..",
            "....BBB..",
            ".BBBB....",
            ".BBBB...M",
        ),
    ),
    (
        "easy",
        "easy_edge_triple_9x11",
        (
            "...BBBB....",
            "...BBBB....",
            "...BBBB....",
            ".D.........",
            ".D.....BBB.",
            "BB.....BBB.",
            "BB.........",
            "...........",
            "..........M",
        ),
    ),
    (
        "medium",
        "medium_triple_9x12",
        (
            "..BBBB...DD.",
            "..BBBB...DD.",
            "............",
            "............",
            "........BB..",
            "........BB..",
            ".BBB....BB..",
            ".BBB........",
            "...........M",
        ),
    ),
    (
        "medium",
        "medium_negative_10x12",
        (
            "...........M",
            "........BB..",
            "..BB....BB..",
            "..BB........",
            "..BB........",
            "..BB........",
            "DD....BBBB..",
            "DD....BBB...",
            "............",
            "............",
        ),
    ),
    (
        "medium",
        "medium_edge_negative_8x10",
        (
            "BB........",
            "BB....BBB.",
            "......BBB.",
            "..........",
            ".BBBB.....",
            ".BBB......",
            "........DD",
            ".M.......D",
        ),
    ),
    (
        "hard",
        "hard_negative_triple_10x12",
        (
            "BB..........",
            "BB....BBBB..",
            "......BBBB..",
            "............",
            "..BBBB......",
            "..BBB...BBB.",
            "........BBB.",
            "DD......BBB.",
            "DD..........",
            "...M........",
        ),
    ),
    (
        "hard",
        "hard_edge_triple_9x12",
        (
            "...BBB......",
            "...BBB......",
            "............",
            "............",
            "BBBB........",
            "BBBB....DDD.",
            "........D.D.",
            "..BB....DDD.",
            "M.BB........",
        ),
    ),
    (
        "hard",
        "hard_dense_negative_8x9",
        (
            "..BBBB...",
            "..BBBB.DD",
            ".......DD",
            "BB.......",
            "BB..BBB..",
            "....BBB..",
            ".BBBB....",
            "MBBB.....",
        ),
    ),
)

_PROFILE_BY_NAME = {
    name: (band, template) for band, name, template in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(name for row_band, name, _template in _PROFILE_ROWS if row_band == band)
    for band in ("easy", "medium", "hard")
}
SCENE_PROFILES = tuple(name for _band_name, name, _template in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic three-profile curriculum for the difficulty band",
        "valid": (
            "easy_pair_8x10|easy_negative_8x9|easy_edge_triple_9x11|"
            "medium_triple_9x12|medium_negative_10x12|"
            "medium_edge_negative_8x10|hard_negative_triple_10x12|"
            "hard_edge_triple_9x12|hard_dense_negative_8x9"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

_CANONICAL_DIMS = {(8, 9), (8, 10), (9, 11), (9, 12), (10, 12)}
_DISTRACTOR_COLORS = tuple(range(3, 10))


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact profile at a curriculum position."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if "scene_profile" in overrides and overrides["scene_profile"] not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {overrides['scene_profile']!r}")


def _template_components(template: tuple[str, ...]) -> list[dict[str, Any]]:
    """Extract the visible objects while retaining each profile's geometry."""
    height, width = len(template), len(template[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            symbol = template[row][col]
            if symbol == "." or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[Cell] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                current_row, current_col = current
                for neighbor in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    nrow, ncol = neighbor
                    if (
                        0 <= nrow < height
                        and 0 <= ncol < width
                        and neighbor not in seen
                        and template[nrow][ncol] == symbol
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            row0 = min(r for r, _c in cells)
            row1 = max(r for r, _c in cells)
            col0 = min(c for _r, c in cells)
            col1 = max(c for _r, c in cells)
            components.append(
                {
                    "symbol": symbol,
                    "cells": tuple(sorted((r - row0, c - col0) for r, c in cells)),
                    "height": row1 - row0 + 1,
                    "width": col1 - col0 + 1,
                    "edge": row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1,
                    "origin": (row0, col0),
                }
            )
    return components


def _placement_candidates(
    component: dict[str, Any], height: int, width: int
) -> list[tuple[Cell, ...]]:
    """Enumerate translations that preserve the component's edge role."""
    candidates: list[tuple[Cell, ...]] = []
    component_height = component["height"]
    component_width = component["width"]
    for row0 in range(height - component_height + 1):
        for col0 in range(width - component_width + 1):
            touches_edge = (
                row0 == 0
                or col0 == 0
                or row0 + component_height == height
                or col0 + component_width == width
            )
            # The singleton is deliberately free to move between edge and interior;
            # it is not part of the observable profile signature.
            if component["symbol"] != "M" and touches_edge != component["edge"]:
                continue
            candidates.append(
                tuple(
                    (row0 + row, col0 + col)
                    for row, col in component["cells"]
                )
            )
    return candidates


def _blue_halo(cells: tuple[Cell, ...]) -> set[Cell]:
    """Cells whose use by another blue object would merge or visually fuse it."""
    return {
        (row + drow, col + dcol)
        for row, col in cells
        for drow in (-1, 0, 1)
        for dcol in (-1, 0, 1)
    }


def _repack_template(template: tuple[str, ...], rng) -> list[list[str]]:
    """Randomly place intact profile components with exhaustive backtracking."""
    height, width = len(template), len(template[0])
    entries = []
    for component in _template_components(template):
        candidates = _placement_candidates(component, height, width)
        rng.shuffle(candidates)
        entries.append((component, candidates))

    # Constrained and large objects first keeps the search shallow.  Candidate
    # order remains seed-dependent, so successful layouts vary across calls.
    entries.sort(
        key=lambda item: (
            len(item[1]),
            -len(item[0]["cells"]),
            item[0]["symbol"],
            item[0]["origin"],
        )
    )
    occupied: set[Cell] = set()
    blue_cells: set[Cell] = set()
    selected: list[tuple[dict[str, Any], tuple[Cell, ...]]] = []

    def place(index: int) -> bool:
        if index == len(entries):
            return True
        component, candidates = entries[index]
        for cells in candidates:
            if occupied.intersection(cells):
                continue
            if component["symbol"] == "B" and blue_cells.intersection(_blue_halo(cells)):
                continue
            occupied.update(cells)
            if component["symbol"] == "B":
                blue_cells.update(cells)
            selected.append((component, cells))
            if place(index + 1):
                return True
            selected.pop()
            occupied.difference_update(cells)
            if component["symbol"] == "B":
                blue_cells.difference_update(cells)
        return False

    if not place(0):
        raise AssertionError("declared profile components could not be repacked")

    rows = [["."] * width for _ in range(height)]
    for component, cells in selected:
        for row, col in cells:
            rows[row][col] = component["symbol"]
    return rows


def _render_template(template: tuple[str, ...], distractor: int, singleton: int, rng) -> Grid:
    rows = _repack_template(template, rng)
    mapping = {".": 0, "B": 1, "D": distractor, "M": singleton}
    return [[mapping[value] for value in row] for row in rows]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the selected Racket rule owns output."""
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    scheduled = overrides.get("scene_profile") or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", (scheduled,))
    _profile_band, template = _PROFILE_BY_NAME[profile]
    rng = ctx.draw_rng("render")
    distractor, singleton = rng.sample(_DISTRACTOR_COLORS, 2)
    grid = _render_template(template, distractor, singleton, rng)
    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise AssertionError(
            f"constructed profile {profile!r} observed as {observed.get('scene_profile')!r}"
        )
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Grid, color: int) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    todo = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[dict[str, Any]] = []
    while todo:
        start = min(todo)
        todo.remove(start)
        cells = [start]
        stack = [start]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in todo:
                    todo.remove(neighbor)
                    stack.append(neighbor)
                    cells.append(neighbor)
        cells.sort()
        row0 = min(row for row, _col in cells)
        row1 = max(row for row, _col in cells)
        col0 = min(col for _row, col in cells)
        col1 = max(col for _row, col in cells)
        box_height = row1 - row0 + 1
        box_width = col1 - col0 + 1
        solid = len(cells) == box_height * box_width
        components.append(
            {
                "cells": tuple(cells),
                "size": len(cells),
                "row0": row0,
                "row1": row1,
                "col0": col0,
                "col1": col1,
                "height": box_height,
                "width": box_width,
                "solid": solid,
                "edge": row0 == 0 or col0 == 0 or row1 == height - 1 or col1 == width - 1,
                "qualifies": solid and box_height >= 2 and box_width >= 2,
            }
        )
    components.sort(key=lambda item: (item["row0"], item["col0"], item["row1"], item["col1"]))
    return components


def _component_signature(component: dict[str, Any], *, include_solid: bool = False) -> tuple[Any, ...]:
    values: tuple[Any, ...] = (
        component["height"],
        component["width"],
        component["size"],
    )
    if include_solid:
        values += (component["solid"],)
    return values + (component["edge"],)


def _analysis(grid: Any, *, teaching: bool = False) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "targets": [], "irregular": [], "scene_profile": None}

    normalized: Grid = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    counts = Counter(value for row in normalized for value in row)
    palette = set(counts)

    if 0 not in palette:
        errors.append("expected background color 0")
    if 1 not in palette:
        errors.append("expected at least one blue component")
    if 2 in palette:
        errors.append("input must not contain output marker color red 2")
    if len(palette) != 4:
        errors.append(f"expected exactly four input colors, found {len(palette)}")

    distractor_colors = sorted(palette - {0, 1, 2})
    singleton_color: int | None = None
    main_color: int | None = None
    if len(distractor_colors) != 2:
        errors.append(
            "expected exactly two non-blue distractor colors in addition to 0 and 1"
        )
    else:
        singletons = [color for color in distractor_colors if counts[color] == 1]
        mains = [color for color in distractor_colors if counts[color] >= 2]
        if len(singletons) != 1 or len(mains) != 1:
            errors.append("distractors must comprise one singleton and one multi-cell color")
        else:
            singleton_color = singletons[0]
            main_color = mains[0]

    blue_components = _components(normalized, 1) if 1 in palette else []
    targets = [component for component in blue_components if component["qualifies"]]
    irregular = [component for component in blue_components if not component["qualifies"]]
    if not 1 <= len(targets) <= 3:
        errors.append(f"expected one to three qualifying blue rectangles, found {len(targets)}")
    if len(irregular) > 1:
        errors.append(f"expected at most one irregular blue component, found {len(irregular)}")
    for component in irregular:
        if component["height"] < 2 or component["width"] < 2 or component["size"] < 3:
            errors.append("irregular blue evidence must span at least 2x2 and contain at least three cells")
    for component in targets:
        if component["height"] > 5 or component["width"] > 5:
            errors.append("qualifying blue rectangles must be at most 5x5 on this task manifold")

    main_components = _components(normalized, main_color) if main_color is not None else []
    if main_color is not None and len(main_components) != 1:
        errors.append("multi-cell distractor color must form one four-connected object")
    if singleton_color is not None:
        singleton_components = _components(normalized, singleton_color)
        if len(singleton_components) != 1 or singleton_components[0]["size"] != 1:
            errors.append("singleton distractor must form exactly one one-cell object")

    signature = (
        height,
        width,
        tuple(sorted(_component_signature(component) for component in targets)),
        tuple(sorted(_component_signature(component) for component in irregular)),
        tuple(
            sorted(
                _component_signature(component, include_solid=True)
                for component in main_components
            )
        ),
    )
    scene_profile = _PROFILE_BY_SIGNATURE.get(signature)

    if teaching and not errors:
        if scene_profile is None:
            errors.append(
                "teaching scene must realize one declared linked geometry profile; "
                f"observed signature {signature!r}"
            )
        if (height, width) not in _CANONICAL_DIMS:
            errors.append(f"teaching dimensions must match a canonical size, found {height}x{width}")

    return {
        "errors": errors,
        "grid": normalized,
        "height": height,
        "width": width,
        "counts": counts,
        "palette": palette,
        "distractor_colors": distractor_colors,
        "singleton_color": singleton_color,
        "main_color": main_color,
        "blue_components": blue_components,
        "targets": targets,
        "irregular": irregular,
        "main_components": main_components,
        "signature": signature,
        "scene_profile": scene_profile,
    }


def _template_grid(template: tuple[str, ...]) -> Grid:
    mapping = {".": 0, "B": 1, "D": 3, "M": 4}
    return [[mapping[value] for value in row] for row in template]


def _build_profile_signature_map() -> dict[tuple[Any, ...], str]:
    mapping: dict[tuple[Any, ...], str] = {}
    for _band_name, name, template in _PROFILE_ROWS:
        analysis = _analysis_without_profile_lookup(_template_grid(template))
        signature = analysis["signature"]
        if analysis["errors"]:
            raise AssertionError(f"invalid built-in profile {name}: {analysis['errors']}")
        if signature in mapping:
            raise AssertionError(f"duplicate observable profile signature: {name} and {mapping[signature]}")
        mapping[signature] = name
    return mapping


def _analysis_without_profile_lookup(grid: Grid) -> dict[str, Any]:
    """Build the structural record before the signature table exists."""
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    blue_components = _components(grid, 1)
    targets = [component for component in blue_components if component["qualifies"]]
    irregular = [component for component in blue_components if not component["qualifies"]]
    distractor_colors = sorted(set(counts) - {0, 1, 2})
    main_color = next((color for color in distractor_colors if counts[color] >= 2), None)
    main_components = _components(grid, main_color) if main_color is not None else []
    signature = (
        height,
        width,
        tuple(sorted(_component_signature(component) for component in targets)),
        tuple(sorted(_component_signature(component) for component in irregular)),
        tuple(
            sorted(
                _component_signature(component, include_solid=True)
                for component in main_components
            )
        ),
    )
    return {"errors": [], "signature": signature}


# Initialized after the structural helpers; _analysis resolves it at call time.
_PROFILE_BY_SIGNATURE = _build_profile_signature_map()


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the broad task grammar, including canonical negative examples."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrower generated curriculum and exact observable axis."""
    del difficulty
    analysis = _analysis(grid, teaching=True)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = {"scene_profile": analysis["scene_profile"]}
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the complete declared axis from the returned geometry."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def strict_canonical_like(grid) -> list[str]:
    """Accept the canonical manifold and every ordinary generated lesson."""
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if (analysis["height"], analysis["width"]) not in _CANONICAL_DIMS:
        errors.append(
            "strict canonical-like grids must use one of the five canonical dimensions"
        )
    return errors


def canonical_profile_index(grid) -> int | None:
    """Return the exact canonical structural-profile index, if any."""
    try:
        from scripts.canonical_profile_gate import canonical_inputs
    except Exception:
        return None
    normalized = [list(row) for row in grid] if isinstance(grid, (list, tuple)) else grid
    for index, candidate in enumerate(canonical_inputs(TASK_ID)):
        if normalized == candidate:
            return index
    return None


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _corners(component: dict[str, Any]) -> tuple[Cell, Cell, Cell, Cell]:
    return (
        (component["row0"], component["col0"]),
        (component["row0"], component["col1"]),
        (component["row1"], component["col0"]),
        (component["row1"], component["col1"]),
    )


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    output = _copy_grid(grid)
    for component in _components(output, 1):
        if component["qualifies"]:
            for row, col in _corners(component):
                output[row][col] = 2
    return output


def _rival_all_blue_to_red(grid: Grid) -> Grid:
    return [[2 if value == 1 else value for value in row] for row in grid]


def _rival_bbox_corners_all_blue_components(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for component in _components(_copy_grid(grid), 1):
        if component["height"] >= 2 and component["width"] >= 2:
            for row, col in _corners(component):
                output[row][col] = 2
    return output


def _rival_all_solid_rectangles_any_color(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for color in sorted({value for row in grid for value in row} - {0, 2}):
        for component in _components(_copy_grid(grid), color):
            if component["qualifies"]:
                for row, col in _corners(component):
                    output[row][col] = 2
    return output


def _rival_first_target_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    targets = [component for component in _components(_copy_grid(grid), 1) if component["qualifies"]]
    if targets:
        for row, col in _corners(targets[0]):
            output[row][col] = 2
    return output


def _rival_paint_full_border(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for component in _components(_copy_grid(grid), 1):
        if not component["qualifies"]:
            continue
        row0, row1 = component["row0"], component["row1"]
        col0, col1 = component["col0"], component["col1"]
        for col in range(col0, col1 + 1):
            output[row0][col] = 2
            output[row1][col] = 2
        for row in range(row0, row1 + 1):
            output[row][col0] = 2
            output[row][col1] = 2
    return output


def _rival_interior_targets_only(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for component in _components(_copy_grid(grid), 1):
        if component["qualifies"] and not component["edge"]:
            for row, col in _corners(component):
                output[row][col] = 2
    return output


def _rival_skip_2x2_targets(grid: Grid) -> Grid:
    output = _copy_grid(grid)
    for component in _components(_copy_grid(grid), 1):
        if component["qualifies"] and (component["height"], component["width"]) != (2, 2):
            for row, col in _corners(component):
                output[row][col] = 2
    return output


def _rival_identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _valid_analysis(grid: Grid) -> dict[str, Any] | None:
    analysis = _analysis(grid, teaching=True)
    return None if analysis["errors"] else analysis


def _multiple_targets(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and len(analysis["targets"]) >= 2


def _blue_irregular_negative(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and bool(analysis["irregular"])


def _wrong_color_solid_rectangle(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        component["qualifies"] for component in analysis["main_components"]
    )


def _noncorner_blue_survives(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    if analysis is None:
        return False
    corner_cells = {
        cell for component in analysis["targets"] for cell in _corners(component)
    }
    return any(
        cell not in corner_cells
        for component in analysis["targets"]
        for cell in component["cells"]
    )


def _edge_touching_target(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(component["edge"] for component in analysis["targets"])


def _two_by_two_target(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and any(
        (component["height"], component["width"]) == (2, 2)
        for component in analysis["targets"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "multiple_targets": _multiple_targets,
    "blue_irregular_negative": _blue_irregular_negative,
    "wrong_color_solid_rectangle": _wrong_color_solid_rectangle,
    "noncorner_blue_survives": _noncorner_blue_survives,
    "edge_touching_target": _edge_touching_target,
    "two_by_two_target": _two_by_two_target,
}

SEMANTIC_RIVALS = {
    "all_blue_to_red": _rival_all_blue_to_red,
    "bbox_corners_all_blue_components": _rival_bbox_corners_all_blue_components,
    "all_solid_rectangles_any_color": _rival_all_solid_rectangles_any_color,
    "first_target_only": _rival_first_target_only,
    "paint_full_border": _rival_paint_full_border,
    "interior_targets_only": _rival_interior_targets_only,
    "skip_2x2_targets": _rival_skip_2x2_targets,
    "identity": _rival_identity,
}
WITNESS_RIVALS = {
    "multiple_targets": ["first_target_only"],
    "blue_irregular_negative": ["all_blue_to_red", "bbox_corners_all_blue_components"],
    "wrong_color_solid_rectangle": ["all_solid_rectangles_any_color"],
    "noncorner_blue_survives": ["all_blue_to_red", "paint_full_border"],
    "edge_touching_target": ["interior_targets_only"],
    "two_by_two_target": ["skip_2x2_targets"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to eliminate the declared task-local shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if teaching_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if teaching_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not apply the solid-blue-corners rule")
            continue
        valid_demos.append(demo)

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
