"""Generator for 17829a00 — move border-colored interior objects vertically.

The first and last rows are solid, distinct marker colors.  Interior objects
matching the top marker move upward until their bounding boxes start at row 1.
Interior objects matching the bottom marker normally move downward until their
bounding boxes end at row ``h - 2``.  The one exceptional branch is a bottom
object whose bounding box is at least three rows tall and touches the right
edge: each occupied column is extruded downward from the object's top row to
``h - 2``.

Normal draws include shortcut-rebutting controls: a tall top object touching
the right edge (still moves upward), a tall bottom object away from the right
edge (still slides normally), and a scheduled right-edge bottom case whose
height cycles through tall-special, short-control, and absent.  Any three
consecutive sample indexes therefore expose the conjunction behind the special
branch.  Generated scenes also keep same-color object destinations disjoint so
the painted output cannot silently merge two source objects or erase cells by
overdraw.
"""
from __future__ import annotations

from collections import Counter
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b320eba4cfd5"
TASK_ID = "b320eba4cfd5"
VERSION = "3.1.0"  # reject projected destination collisions in training draws
RULE_HASH = "85019913700d"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "A rectangular grid has a solid TOP-COLOR first row, a solid BOTTOM-COLOR "
    "last row, and a third modal BACKGROUND color. Interior 8-connected "
    "objects use only the two marker colors. Every TOP-COLOR object is erased "
    "and shifted vertically so its top edge becomes row 1. Every ordinary "
    "BOTTOM-COLOR object is erased and shifted so its bottom edge becomes row "
    "h-2. A BOTTOM-COLOR object that both touches the right edge and is at "
    "least three rows tall is instead extruded downward: every column occupied "
    "by that object is filled from the object's original top row through row "
    "h-2. Generated lessons keep same-color object destinations disjoint so "
    "every source object's effect remains visible. Object shapes, counts, "
    "positions, dimensions, and colors vary."
)

INVARIANTS = [
    "the first and last rows are solid, distinct marker colors",
    "the modal background is distinct from both marker colors",
    "all interior non-background cells use one of the marker colors",
    "top-color objects begin below row 1 and therefore move upward",
    "ordinary bottom-color objects end above row h-2 and therefore move downward",
    "only tall right-edge bottom objects take the extrusion branch",
    "same-color source objects never overlap at their projected destinations",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted with frequent canonical 16",
        "valid": "14..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted with frequent canonical 16",
        "valid": "14..20",
    },
    "n_top_objs": {
        "type": "int",
        "default": "difficulty-weighted",
        "valid": "2..4",
    },
    "n_bot_objs": {
        "type": "int",
        "default": "difficulty-weighted",
        "valid": "3..5",
    },
    "edge_mode": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "tall_special|short_control|none",
    },
    "shape_style": {
        "type": "str",
        "default": "sample_index alternation",
        "valid": "rectangles|mixed",
    },
}

DEGENERATE_TEXTURES = ("no_objects", "no_borders", "full_grid")
_EDGE_MODES = ("tall_special", "short_control", "none")
_SHAPE_STYLES = ("rectangles", "mixed")
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_COLORS = tuple(range(1, 10))

# Normalized coordinate templates.  Every template is 8-connected.  The
# irregular set intentionally contains diagonal links, matching the canonical
# task's sparse shapes and preventing rectangle-only shortcuts.
_RECT_SHAPES = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
)
_IRREGULAR_SHAPES = (
    ((0, 0), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
    ((0, 1), (1, 0), (1, 2), (2, 1)),
)


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return (
        max(row for row, _ in cells) + 1,
        max(column for _, column in cells) + 1,
    )


def _is_rectangle(cells: list[tuple[int, int]]) -> bool:
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return len(cells) == (
        (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)
    )


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    """8-connected components of ``color`` in the interior, in global coords."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(1, height - 1):
        for column in range(width):
            if grid[row][column] != color or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_column = stack.pop()
                cells.append((current_row, current_column))
                for delta_row in (-1, 0, 1):
                    for delta_column in (-1, 0, 1):
                        if delta_row == 0 and delta_column == 0:
                            continue
                        neighbor = (
                            current_row + delta_row,
                            current_column + delta_column,
                        )
                        nr, nc = neighbor
                        if not (1 <= nr < height - 1 and 0 <= nc < width):
                            continue
                        if neighbor in seen or grid[nr][nc] != color:
                            continue
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(sorted(cells))
    return components


def _bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    columns = [column for _, column in cells]
    return min(rows), min(columns), max(rows), max(columns)


def _projected_destination_sets(facts: dict) -> list[dict]:
    """Return each object's destination cells under the pinned Racket rule."""
    height = facts["height"]
    width = facts["width"]
    top_color = facts["top_color"]
    bottom_color = facts["bottom_color"]
    projected: list[dict] = []
    for kind, color, components in (
        ("top", top_color, facts["top_objects"]),
        ("bottom", bottom_color, facts["bottom_objects"]),
    ):
        for index, cells in enumerate(components):
            row1, _, row2, column2 = _bbox(cells)
            if kind == "bottom" and column2 == width - 1 and row2 - row1 + 1 >= 3:
                destination = {
                    (row, column)
                    for column in {column for _, column in cells}
                    for row in range(row1, height - 1)
                }
                branch = "extrude"
            elif kind == "top":
                delta = 1 - row1
                destination = {(row + delta, column) for row, column in cells}
                branch = "slide_up"
            else:
                delta = (height - 2) - row2
                destination = {(row + delta, column) for row, column in cells}
                branch = "slide_down"
            projected.append(
                {
                    "kind": kind,
                    "index": index,
                    "color": color,
                    "branch": branch,
                    "cells": destination,
                }
            )
    return projected


def projected_destination_collisions(grid: list[list[int]]) -> list[dict]:
    """Observe same-color overdraw that would hide part of a source object."""
    facts = _scene_facts(grid)
    if facts["errors"]:
        return []
    projected = _projected_destination_sets(facts)
    collisions: list[dict] = []
    for left_index, left in enumerate(projected):
        for right_index in range(left_index + 1, len(projected)):
            right = projected[right_index]
            if left["color"] != right["color"]:
                continue
            shared = sorted(left["cells"] & right["cells"])
            if shared:
                collisions.append(
                    {
                        "left": (left["kind"], left["index"], left["branch"]),
                        "right": (right["kind"], right["index"], right["branch"]),
                        "color": left["color"],
                        "shared": shared,
                    }
                )
    return collisions


def _scene_facts(grid: list[list[int]]) -> dict:
    facts: dict = {"errors": []}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        facts["errors"].append("grid must be a non-empty list of rows")
        return facts
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        facts["errors"].append("grid must be rectangular with non-zero width")
        return facts
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        facts["errors"].append("grid colors must be integer values in 0..9")
        return facts

    height = len(grid)
    facts.update({"height": height, "width": width})
    if height < 6 or width < 6:
        facts["errors"].append("grid must be at least 6x6")
        return facts

    top_color = grid[0][0]
    bottom_color = grid[-1][0]
    facts.update({"top_color": top_color, "bottom_color": bottom_color})
    if any(value != top_color for value in grid[0]):
        facts["errors"].append("first row must be a solid top marker band")
    if any(value != bottom_color for value in grid[-1]):
        facts["errors"].append("last row must be a solid bottom marker band")
    if top_color == bottom_color:
        facts["errors"].append("top and bottom marker colors must be distinct")

    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    palette = set(counts)
    facts.update({"background": background, "palette": palette})
    if background in (top_color, bottom_color):
        facts["errors"].append("the modal background must differ from marker colors")
    if palette != {background, top_color, bottom_color}:
        facts["errors"].append(
            "the scene must use exactly background, top-marker, and bottom-marker colors"
        )

    top_objects = _components(grid, top_color)
    bottom_objects = _components(grid, bottom_color)
    facts.update({"top_objects": top_objects, "bottom_objects": bottom_objects})
    if len(top_objects) < 2:
        facts["errors"].append("need at least two interior top-color objects")
    if len(bottom_objects) < 2:
        facts["errors"].append("need at least two interior bottom-color objects")

    for index, cells in enumerate(top_objects):
        row1, _, _, _ = _bbox(cells)
        if row1 <= 1:
            facts["errors"].append(
                f"top object {index} is already aligned to row 1 and would not move"
            )
    for index, cells in enumerate(bottom_objects):
        _, _, row2, _ = _bbox(cells)
        if row2 >= height - 2:
            facts["errors"].append(
                f"bottom object {index} is already aligned to row h-2 and would not move"
            )

    right_tall = []
    right_short = []
    tall_nonedge = []
    for cells in bottom_objects:
        row1, column1, row2, column2 = _bbox(cells)
        object_height = row2 - row1 + 1
        if column2 == width - 1 and object_height >= 3:
            right_tall.append(cells)
        elif column2 == width - 1:
            right_short.append(cells)
        elif object_height >= 3:
            tall_nonedge.append(cells)
    top_right_tall = [
        cells
        for cells in top_objects
        if _bbox(cells)[3] == width - 1
        and _bbox(cells)[2] - _bbox(cells)[0] + 1 >= 3
    ]
    facts.update(
        {
            "right_tall_bottom": right_tall,
            "right_short_bottom": right_short,
            "tall_nonedge_bottom": tall_nonedge,
            "top_right_tall": top_right_tall,
            "all_objects": top_objects + bottom_objects,
        }
    )
    return facts


def _edge_mode_from_facts(facts: dict) -> str:
    if facts.get("right_tall_bottom"):
        return "tall_special"
    if facts.get("right_short_bottom"):
        return "short_control"
    return "none"


def _shape_style_from_facts(facts: dict) -> str:
    components = facts.get("all_objects", [])
    return (
        "rectangles"
        if components and all(_is_rectangle(component) for component in components)
        else "mixed"
    )


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact semantic axis from the returned input grid."""
    facts = _scene_facts(grid)
    return {
        "grid_h": facts.get("height", len(grid) if isinstance(grid, list) else 0),
        "grid_w": facts.get(
            "width",
            len(grid[0]) if isinstance(grid, list) and grid and isinstance(grid[0], list) else 0,
        ),
        "n_top_objs": len(facts.get("top_objects", [])),
        "n_bot_objs": len(facts.get("bottom_objects", [])),
        "edge_mode": _edge_mode_from_facts(facts),
        "shape_style": _shape_style_from_facts(facts),
    }


def _record_int(ctx, label: str, value: int) -> int:
    return ctx.draw_int(label, value, value)


def _record_choice(ctx, label: str, value: str) -> str:
    return ctx.draw_choice(label, [value])


def _draw_int_axis(
    ctx,
    label: str,
    full_bounds: tuple[int, int],
    default_options: tuple[int, ...],
    default_value: int | None = None,
) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, *full_bounds)
    if default_value is None:
        default_value = ctx.draw_rng(f"default|{label}").choice(default_options)
    return _record_int(ctx, label, default_value)


def _draw_choice_axis(
    ctx,
    label: str,
    full_options: tuple[str, ...],
    default_value: str,
) -> str:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, full_options)
    return _record_choice(ctx, label, default_value)


def _band_defaults(difficulty: str | None) -> dict[str, tuple[int, ...]]:
    if difficulty == "easy":
        return {
            "grid_h": (14, 16),
            "grid_w": (14, 16),
            "n_top_objs": (2, 3),
            "n_bot_objs": (3, 4),
        }
    if difficulty == "hard":
        return {
            "grid_h": (16, 18, 20),
            "grid_w": (16, 18, 20),
            "n_top_objs": (3, 4),
            "n_bot_objs": (4, 5),
        }
    return {
        "grid_h": (14, 16, 18),
        "grid_w": (14, 16, 18),
        "n_top_objs": (2, 3, 4),
        "n_bot_objs": (3, 4, 5),
    }


def _translated(
    shape: Iterable[tuple[int, int]], row0: int, column0: int
) -> list[tuple[int, int]]:
    return [(row0 + row, column0 + column) for row, column in shape]


def _blocked_cells(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    blocked: set[tuple[int, int]] = set()
    for row, column in cells:
        for delta_row in (-1, 0, 1):
            for delta_column in (-1, 0, 1):
                blocked.add((row + delta_row, column + delta_column))
    return blocked


def _place_at(
    grid: list[list[int]],
    occupied_blocked: set[tuple[int, int]],
    shape: Iterable[tuple[int, int]],
    row0: int,
    column0: int,
    color: int,
) -> bool:
    height = len(grid)
    width = len(grid[0])
    cells = _translated(shape, row0, column0)
    if any(not (1 <= row < height - 1 and 0 <= column < width) for row, column in cells):
        return False
    if any(cell in occupied_blocked for cell in cells):
        return False
    for row, column in cells:
        grid[row][column] = color
    occupied_blocked.update(_blocked_cells(cells))
    return True


def _try_place(
    grid: list[list[int]],
    occupied_blocked: set[tuple[int, int]],
    shape: Iterable[tuple[int, int]],
    color: int,
    rng,
    *,
    row_bounds: tuple[int, int] | None = None,
    right_edge: bool = False,
    forbid_right_edge: bool = False,
) -> bool:
    height = len(grid)
    width = len(grid[0])
    shape_h, shape_w = _shape_size(shape)
    row_low = 2
    row_high = height - shape_h - 2
    if row_bounds is not None:
        row_low = max(row_low, row_bounds[0])
        row_high = min(row_high, row_bounds[1])
    if row_high < row_low:
        return False
    rows = list(range(row_low, row_high + 1))
    rng.shuffle(rows)
    if right_edge:
        columns = [width - shape_w]
    else:
        column_high = width - shape_w - (1 if forbid_right_edge else 0)
        if column_high < 0:
            return False
        columns = list(range(0, column_high + 1))
        rng.shuffle(columns)
    for row0 in rows:
        for column0 in columns:
            if _place_at(
                grid,
                occupied_blocked,
                shape,
                row0,
                column0,
                color,
            ):
                return True
    return False


def _random_shape(rng, style: str, *, tall: bool | None = None):
    if style == "rectangles":
        pool = list(_RECT_SHAPES)
    else:
        pool = list(_RECT_SHAPES) + list(_IRREGULAR_SHAPES)
    if tall is True:
        pool = [shape for shape in pool if _shape_size(shape)[0] >= 3]
    elif tall is False:
        pool = [shape for shape in pool if _shape_size(shape)[0] <= 2]
    if not pool:
        raise RuntimeError("shape pool unexpectedly empty")
    return rng.choice(pool)


def _build_scene(
    height: int,
    width: int,
    top_color: int,
    bottom_color: int,
    background: int,
    n_top: int,
    n_bottom: int,
    edge_mode: str,
    shape_style: str,
    rng,
) -> list[list[int]]:
    """Construct one exact-axis scene or raise when the combination is infeasible."""
    if n_top < 2 or n_bottom < 3:
        raise ValueError("the semantic controls require n_top_objs>=2 and n_bot_objs>=3")
    for _attempt in range(128):
        grid = full_grid(height, width, background)
        grid[0] = [top_color] * width
        grid[-1] = [bottom_color] * width
        blocked: set[tuple[int, int]] = set()

        # Top-color conjunction control: tall + right edge, but the rule must
        # still choose the top-object slide branch rather than extrusion.
        top_right_shape = ((0, 0), (1, 0), (2, 0))
        if not _try_place(
            grid,
            blocked,
            top_right_shape,
            top_color,
            rng,
            row_bounds=(2, max(2, height // 3)),
            right_edge=True,
        ):
            continue

        # Bottom-color right-edge-condition control: tall but NOT at the right
        # edge, so it must slide normally.  In mixed scenes this is deliberately
        # diagonal/irregular, bringing generated object morphology toward the
        # canonical examples.
        bottom_tall_control = (
            ((0, 0), (1, 1), (2, 2))
            if shape_style == "mixed"
            else ((0, 0), (1, 0), (2, 0))
        )
        if not _try_place(
            grid,
            blocked,
            bottom_tall_control,
            bottom_color,
            rng,
            row_bounds=(2, max(2, height // 3)),
            forbid_right_edge=True,
        ):
            continue

        placed_top = 1
        placed_bottom = 1

        if edge_mode == "tall_special":
            edge_shape = (
                ((0, 0), (1, 0), (2, 0))
                if shape_style == "rectangles"
                else ((0, 0), (1, 0), (2, 0), (2, 1))
            )
            if not _try_place(
                grid,
                blocked,
                edge_shape,
                bottom_color,
                rng,
                row_bounds=(height // 2, height - 5),
                right_edge=True,
            ):
                continue
            placed_bottom += 1
        elif edge_mode == "short_control":
            edge_shape = ((0, 0), (1, 0))
            if not _try_place(
                grid,
                blocked,
                edge_shape,
                bottom_color,
                rng,
                row_bounds=(height // 2, height - 4),
                right_edge=True,
            ):
                continue
            placed_bottom += 1
        elif edge_mode != "none":
            raise ValueError(f"unknown edge_mode {edge_mode!r}")

        # Fill the remaining exact object counts.  Non-edge objects are kept
        # away from the right wall so edge_mode is unambiguous from the grid.
        while placed_top < n_top:
            shape = _random_shape(rng, shape_style)
            if not _try_place(
                grid,
                blocked,
                shape,
                top_color,
                rng,
                forbid_right_edge=True,
            ):
                break
            placed_top += 1
        if placed_top != n_top:
            continue

        while placed_bottom < n_bottom:
            shape = _random_shape(rng, shape_style)
            if not _try_place(
                grid,
                blocked,
                shape,
                bottom_color,
                rng,
                forbid_right_edge=True,
            ):
                break
            placed_bottom += 1
        if placed_bottom != n_bottom:
            continue

        observed = observe_overrides(grid)
        expected = {
            "grid_h": height,
            "grid_w": width,
            "n_top_objs": n_top,
            "n_bot_objs": n_bottom,
            "edge_mode": edge_mode,
            "shape_style": shape_style,
        }
        if observed != expected:
            continue
        if self_check(grid):
            continue
        return grid
    raise ValueError(
        "could not place the requested exact-axis scene; choose larger dimensions "
        "or fewer objects"
    )


def _draw_degenerate(name: str) -> list[list[int]]:
    height = width = 16
    if name == "no_objects":
        grid = full_grid(height, width, 7)
        grid[0] = [1] * width
        grid[-1] = [4] * width
        return grid
    if name == "no_borders":
        grid = full_grid(height, width, 7)
        grid[4][4] = 1
        grid[10][10] = 4
        return grid
    if name == "full_grid":
        return full_grid(height, width, 1)
    raise ValueError(f"unknown degenerate texture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")

    texture = overrides.get("texture")
    if texture is not None:
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(
                f"unknown texture {texture!r}; valid diagnostics are {DEGENERATE_TEXTURES}"
            )
        conflicting = [
            name
            for name, value in overrides.items()
            if name != "texture" and value is not None
        ]
        if conflicting:
            raise ValueError(
                f"diagnostic texture {texture!r} cannot be combined with {conflicting}"
            )
        return _draw_degenerate(texture)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _band_defaults(difficulty)

    # Every second default draw anchors the exact canonical 16x16 profile.
    canonical_anchor = sample_index % 2 == 0
    height = _draw_int_axis(
        ctx,
        "grid_h",
        (14, 20),
        defaults["grid_h"],
        16 if canonical_anchor else None,
    )
    width = _draw_int_axis(
        ctx,
        "grid_w",
        (14, 20),
        defaults["grid_w"],
        16 if canonical_anchor else None,
    )
    n_top = _draw_int_axis(ctx, "n_top_objs", (2, 4), defaults["n_top_objs"])
    n_bottom = _draw_int_axis(ctx, "n_bot_objs", (3, 5), defaults["n_bot_objs"])
    edge_mode = _draw_choice_axis(
        ctx,
        "edge_mode",
        _EDGE_MODES,
        _EDGE_MODES[sample_index % len(_EDGE_MODES)],
    )
    shape_style = _draw_choice_axis(
        ctx,
        "shape_style",
        _SHAPE_STYLES,
        _SHAPE_STYLES[sample_index % len(_SHAPE_STYLES)],
    )

    palette_rng = ctx.draw_rng("palette")
    top_color, bottom_color, background = palette_rng.sample(_COLORS, 3)
    layout_rng = ctx.draw_rng("layout")
    return _build_scene(
        height,
        width,
        top_color,
        bottom_color,
        background,
        n_top,
        n_bottom,
        edge_mode,
        shape_style,
        layout_rng,
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural teaching-grammar gate; accepts every canonical input."""
    facts = _scene_facts(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    for collision in projected_destination_collisions(grid):
        errors.append(
            "same-color objects overlap after projection: "
            f"{collision['left']} and {collision['right']} share "
            f"{collision['shared']}"
        )

    # Exact override requests, when supplied by harness metadata, must be
    # visible in the returned scene rather than silently clamped/fallen back.
    requested: dict = {}
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        if isinstance(nested, dict):
            requested.update(nested)
        requested.update({name: meta[name] for name in AXES if name in meta})
    if requested:
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and value is not None and observed.get(name) != value:
                errors.append(
                    f"override {name} requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic manifold, broader only in size/palette identity."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _witness_top_right_tall(grid) -> bool:
    facts = _scene_facts(grid)
    return not facts["errors"] and bool(facts["top_right_tall"])


def _witness_bottom_tall_nonedge(grid) -> bool:
    facts = _scene_facts(grid)
    return not facts["errors"] and bool(facts["tall_nonedge_bottom"])


def _witness_edge_mode(expected: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        facts = _scene_facts(grid)
        return not facts["errors"] and _edge_mode_from_facts(facts) == expected

    return predicate


def _witness_shape_style(expected: str) -> Callable[[list[list[int]]], bool]:
    def predicate(grid: list[list[int]]) -> bool:
        facts = _scene_facts(grid)
        return not facts["errors"] and _shape_style_from_facts(facts) == expected

    return predicate


def _witness_canonical_profile(grid) -> bool:
    facts = _scene_facts(grid)
    return (
        not facts["errors"]
        and facts["height"] == 16
        and facts["width"] == 16
        and len(facts["palette"]) == 3
    )


def _witness_disjoint_destinations(grid) -> bool:
    facts = _scene_facts(grid)
    return not facts["errors"] and not projected_destination_collisions(grid)


SEMANTIC_WITNESSES = {
    "top_tall_right_edge_still_slides_up": _witness_top_right_tall,
    "bottom_tall_nonedge_still_slides_down": _witness_bottom_tall_nonedge,
    "bottom_tall_right_edge_extrudes": _witness_edge_mode("tall_special"),
    "bottom_short_right_edge_still_slides": _witness_edge_mode("short_control"),
    "bottom_without_right_edge_control": _witness_edge_mode("none"),
    "rectangle_only_scene": _witness_shape_style("rectangles"),
    "irregular_eight_connected_scene": _witness_shape_style("mixed"),
    "canonical_16x16_profile": _witness_canonical_profile,
    "projected_destinations_disjoint": _witness_disjoint_destinations,
}


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _transform(
    grid: list[list[int]],
    *,
    move_top: bool = True,
    move_bottom: bool = True,
    special_policy: str = "correct",
) -> list[list[int]]:
    """Python test mirror.  Racket remains the sole production output authority."""
    source = _copy_grid(grid)
    facts = _scene_facts(source)
    if facts["errors"]:
        raise ValueError("invalid lesson input: " + "; ".join(facts["errors"]))
    height = facts["height"]
    width = facts["width"]
    top_color = facts["top_color"]
    bottom_color = facts["bottom_color"]
    background = facts["background"]
    output = _copy_grid(source)
    for row in range(1, height - 1):
        for column in range(width):
            if output[row][column] in (top_color, bottom_color):
                output[row][column] = background

    def special_for(color: int, cells: list[tuple[int, int]]) -> bool:
        row1, _, row2, column2 = _bbox(cells)
        object_height = row2 - row1 + 1
        if special_policy == "correct":
            return color == bottom_color and column2 == width - 1 and object_height >= 3
        if special_policy == "never":
            return False
        if special_policy == "right_any_height":
            return color == bottom_color and column2 == width - 1
        if special_policy == "tall_anywhere":
            return color == bottom_color and object_height >= 3
        if special_policy == "any_color_tall_right":
            return column2 == width - 1 and object_height >= 3
        raise ValueError(f"unknown special policy {special_policy!r}")

    if move_top:
        for cells in facts["top_objects"]:
            if special_for(top_color, cells):
                row1, _, _, _ = _bbox(cells)
                for column in sorted({column for _, column in cells}):
                    for row in range(row1, height - 1):
                        output[row][column] = top_color
            else:
                row1, _, _, _ = _bbox(cells)
                delta = 1 - row1
                for row, column in cells:
                    output[row + delta][column] = top_color

    if move_bottom:
        for cells in facts["bottom_objects"]:
            if special_for(bottom_color, cells):
                row1, _, _, _ = _bbox(cells)
                for column in sorted({column for _, column in cells}):
                    for row in range(row1, height - 1):
                        output[row][column] = bottom_color
            else:
                _, _, row2, _ = _bbox(cells)
                delta = (height - 2) - row2
                for row, column in cells:
                    output[row + delta][column] = bottom_color
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return _transform(grid, special_policy="correct")


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where plausible near-miss rules disagree on the query."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    candidates = {
        "correct": lambda grid: _transform(grid, special_policy="correct"),
        "slide_all_bottom": lambda grid: _transform(grid, special_policy="never"),
        "extrude_any_right_bottom": lambda grid: _transform(
            grid, special_policy="right_any_height"
        ),
        "extrude_any_tall_bottom": lambda grid: _transform(
            grid, special_policy="tall_anywhere"
        ),
        "extrude_tall_right_any_color": lambda grid: _transform(
            grid, special_policy="any_color_tall_right"
        ),
        "top_only": lambda grid: _transform(
            grid, move_bottom=False, special_policy="correct"
        ),
        "bottom_only": lambda grid: _transform(
            grid, move_top=False, special_policy="correct"
        ),
        "identity": _copy_grid,
    }
    consistent: list[str] = []
    for name, candidate in candidates.items():
        try:
            if all(
                isinstance(pair, dict)
                and "input" in pair
                and "output" in pair
                and candidate(_copy_grid(pair["input"])) == _copy_grid(pair["output"])
                for pair in demos
            ):
                consistent.append(name)
        except (TypeError, ValueError):
            continue
    if "correct" not in consistent:
        return [f"official demonstrations do not match the pinned rule; matches={consistent}"]
    if not consistent:
        return ["no candidate operation matches every demonstration"]

    query_grid = _copy_grid(query["input"])
    answer_groups: dict[str, list[str]] = {}
    for name in consistent:
        answer = candidates[name](query_grid)
        answer_groups.setdefault(repr(answer), []).append(name)
    if len(answer_groups) != 1:
        groups = "; ".join(str(names) for names in answer_groups.values())
        return [f"demo-consistent near-miss rules disagree on query answer: {groups}"]
    return []
