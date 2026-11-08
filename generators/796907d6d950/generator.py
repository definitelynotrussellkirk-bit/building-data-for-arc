"""Generator for 5a5a2103: stamp one discovered template across each row.

A colored separator lattice partitions the input into equal square macro-cells.
Every macro-row has a monochrome marker in its first cell.  Exactly one other
macro-cell contains a monochrome template.  The Racket rule discovers that
shape and stamps it into every cell of each row using that row's marker color.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "796907d6d950"
VERSION = "3.0.0"
TASK_ID = "796907d6d950"
RULE_HASH = "dec54a77f94f"

SUMMARY = (
    "A one-cell-thick, uniform nonzero lattice partitions the input into a "
    "3×3 through 5×5 array of equal square cells. The first cell of every "
    "macro-row contains the same marker mask in a row-specific color. Exactly "
    "one non-marker cell contains a larger monochrome template. The answer "
    "clears every data cell and stamps that template mask into every cell of "
    "each macro-row, recolored with that row's marker color; separators stay "
    "unchanged."
)

INVARIANTS = [
    "separator rows and columns are one cell thick, periodic, and share one nonzero color",
    "the lattice contains three through five equal square cells in each dimension",
    "every first-column cell contains one connected 3- or 4-cell marker with a shared mask",
    "marker colors are distinct across macro-rows",
    "exactly one non-first-column cell contains one connected 5- through 8-cell template",
    "background, separator, marker, and template colors have unambiguous roles",
]

EXAMPLES_NEEDED = 4
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "cell_size": {
        "type": "int",
        "default": "difficulty-aware 3..5; every fourth sample anchors cell size 4",
        "valid": "3..5",
    },
    "row_count": {
        "type": "int",
        "default": "difficulty-aware 3..5 macro-rows",
        "valid": "3..5",
    },
    "col_count": {
        "type": "int",
        "default": "difficulty-aware 3..5 macro-columns",
        "valid": "3..5",
    },
    "marker_size": {
        "type": "int",
        "default": "scheduled 3- or 4-cell row marker",
        "valid": "3..4",
    },
    "template_size": {
        "type": "int",
        "default": "scheduled connected template with 5..8 cells",
        "valid": "5..8",
    },
    "template_row_index": {
        "type": "int",
        "default": "scheduled across first, middle, last, and free macro-rows",
        "valid": "0..4",
    },
    "template_col_index": {
        "type": "int",
        "default": "scheduled across non-marker macro-columns",
        "valid": "1..4",
    },
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_KING = tuple(
    (delta_row, delta_col)
    for delta_row in (-1, 0, 1)
    for delta_col in (-1, 0, 1)
    if (delta_row, delta_col) != (0, 0)
)
_CANONICAL_TEMPLATE_MASKS = {
    6: (
        frozenset({(1, 0), (1, 1), (1, 3), (2, 1), (2, 2), (3, 2)}),
    ),
    8: (
        frozenset({(0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 2)}),
        frozenset({(0, 1), (0, 2), (1, 2), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1)}),
    ),
}


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    ranges = {
        "cell_size": (3, 5),
        "row_count": (3, 5),
        "col_count": (3, 5),
        "marker_size": (3, 4),
        "template_size": (5, 8),
        "template_row_index": (0, 4),
        "template_col_index": (1, 4),
    }
    for name, (lower, upper) in ranges.items():
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lower <= value <= upper
        ):
            raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")
    if (
        overrides.get("row_count") is not None
        and overrides.get("template_row_index") is not None
        and overrides["template_row_index"] >= overrides["row_count"]
    ):
        raise ValueError("template_row_index must be smaller than row_count")
    if (
        overrides.get("col_count") is not None
        and overrides.get("template_col_index") is not None
        and overrides["template_col_index"] >= overrides["col_count"]
    ):
        raise ValueError("template_col_index must be smaller than col_count")


def _draw_axis(ctx, name: str, lo: int, hi: int, *, fixed: int | None = None) -> int:
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    if fixed is not None:
        return ctx.draw_int(name, fixed, fixed)
    return ctx.draw_int(name, lo, hi)


def _band_ranges(difficulty) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (3, 4), (3, 4), (3, 4)
    if difficulty == "hard":
        return (4, 5), (4, 5), (4, 5)
    return (3, 5), (3, 5), (3, 5)


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in _KING:
            nxt = row + delta_row, col + delta_col
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _marker_mask(cell_size: int, marker_size: int, slot: int, rng) -> frozenset[tuple[int, int]]:
    if marker_size == 4 and cell_size == 4 and slot == 0:
        return frozenset({(1, 1), (1, 2), (2, 1), (2, 2)})

    if marker_size == 3:
        forms = (
            {(0, 0), (1, 0), (1, 1)},
            {(0, 0), (0, 1), (1, 1)},
            {(0, 1), (1, 0), (1, 1)},
            {(0, 0), (0, 1), (1, 0)},
            {(0, 1), (1, 1), (2, 1)},
        )
    else:
        forms = (
            {(0, 0), (0, 1), (1, 0), (1, 1)},
            {(0, 1), (1, 0), (1, 1), (1, 2)},
            {(0, 0), (1, 0), (1, 1), (2, 1)},
            {(0, 0), (0, 1), (1, 1), (1, 2)},
        )
    base = set(rng.choice(forms))
    height = max(row for row, _ in base) + 1
    width = max(col for _, col in base) + 1
    row_offset = rng.randrange(cell_size - height + 1)
    col_offset = rng.randrange(cell_size - width + 1)
    return frozenset(
        (row + row_offset, col + col_offset) for row, col in base
    )


def _grow_shape(cell_size: int, size: int, rng) -> frozenset[tuple[int, int]]:
    for _ in range(200):
        cells = {(rng.randrange(cell_size), rng.randrange(cell_size))}
        while len(cells) < size:
            frontier = []
            for row, col in sorted(cells):
                for delta_row, delta_col in _CARDINAL:
                    nxt = row + delta_row, col + delta_col
                    if (
                        0 <= nxt[0] < cell_size
                        and 0 <= nxt[1] < cell_size
                        and nxt not in cells
                    ):
                        frontier.append(nxt)
            if not frontier:
                break
            cells.add(rng.choice(frontier))
        if len(cells) == size and _connected(cells):
            return frozenset(cells)
    raise ValueError("could not construct a connected template mask")


def _template_mask(
    cell_size: int,
    template_size: int,
    slot: int,
    rng,
) -> frozenset[tuple[int, int]]:
    if cell_size == 4 and slot == 0 and template_size in _CANONICAL_TEMPLATE_MASKS:
        return rng.choice(_CANONICAL_TEMPLATE_MASKS[template_size])
    return _grow_shape(cell_size, template_size, rng)


def _separator_geometry(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["empty grid"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return None, ["grid must be a non-empty rectangular sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["ragged grid"]
    height = len(grid)
    if height > 30 or width > 30:
        return None, [f"grid exceeds ARC bounds: {height}x{width}"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None, ["grid contains a non-integer or color outside 0..9"]

    sep_rows = [
        row
        for row in range(height)
        if grid[row][0] != 0 and len(set(grid[row])) == 1
    ]
    sep_cols = [
        col
        for col in range(width)
        if grid[0][col] != 0
        and len({grid[row][col] for row in range(height)}) == 1
    ]
    if not sep_rows or not sep_cols:
        return None, ["missing a full-width row or full-height column separator"]
    cell_size = sep_rows[0]
    if cell_size < 1 or sep_cols[0] != cell_size:
        return None, ["first row and column separators do not define equal cells"]
    expected_rows = list(range(cell_size, height, cell_size + 1))
    expected_cols = list(range(cell_size, width, cell_size + 1))
    if sep_rows != expected_rows or sep_cols != expected_cols:
        return None, ["separator rows/columns are not a complete periodic lattice"]
    row_count = len(sep_rows) + 1
    col_count = len(sep_cols) + 1
    if height != row_count * cell_size + row_count - 1:
        return None, ["height is inconsistent with the separator lattice"]
    if width != col_count * cell_size + col_count - 1:
        return None, ["width is inconsistent with the separator lattice"]
    sep_colors = {grid[row][0] for row in sep_rows} | {
        grid[0][col] for col in sep_cols
    }
    if len(sep_colors) != 1:
        return None, ["separator rows and columns use multiple colors"]
    sep_color = next(iter(sep_colors))
    for row in range(height):
        for col in range(width):
            on_separator = row in sep_rows or col in sep_cols
            if on_separator and grid[row][col] != sep_color:
                return None, ["separator lattice has an overwritten cell"]
            if not on_separator and grid[row][col] == sep_color:
                return None, ["separator color leaks into a data cell"]
    return {
        "height": height,
        "width": width,
        "cell_size": cell_size,
        "row_count": row_count,
        "col_count": col_count,
        "sep_color": sep_color,
    }, []


def _analyze_grid(grid):
    geometry, errors = _separator_geometry(grid)
    if errors:
        return {}, errors
    assert geometry is not None
    cell_size = geometry["cell_size"]
    row_count = geometry["row_count"]
    col_count = geometry["col_count"]
    sep_color = geometry["sep_color"]
    if not 3 <= cell_size <= 5:
        errors.append(f"cell_size {cell_size} outside 3..5")
    if not 3 <= row_count <= 5:
        errors.append(f"row_count {row_count} outside 3..5")
    if not 3 <= col_count <= 5:
        errors.append(f"col_count {col_count} outside 3..5")

    marker_masks = []
    marker_colors = []
    occupied_non_marker = []
    for macro_row in range(row_count):
        row0 = macro_row * (cell_size + 1)
        for macro_col in range(col_count):
            col0 = macro_col * (cell_size + 1)
            by_color = {}
            for local_row in range(cell_size):
                for local_col in range(cell_size):
                    value = grid[row0 + local_row][col0 + local_col]
                    if value == 0:
                        continue
                    if value == sep_color:
                        errors.append("separator color appears inside a data cell")
                        continue
                    by_color.setdefault(value, set()).add((local_row, local_col))
            if macro_col == 0:
                if len(by_color) != 1:
                    errors.append(
                        f"marker cell in macro-row {macro_row} has {len(by_color)} colors"
                    )
                    continue
                color, mask = next(iter(by_color.items()))
                if len(mask) not in (3, 4):
                    errors.append(
                        f"marker in macro-row {macro_row} has {len(mask)} cells, expected 3 or 4"
                    )
                if not _connected(mask):
                    errors.append(f"marker in macro-row {macro_row} is disconnected")
                marker_colors.append(color)
                marker_masks.append(frozenset(mask))
            elif by_color:
                occupied_non_marker.append((macro_row, macro_col, by_color))

    if len(marker_colors) == row_count and len(set(marker_colors)) != row_count:
        errors.append("marker colors are not distinct across macro-rows")
    if marker_masks and any(mask != marker_masks[0] for mask in marker_masks[1:]):
        errors.append("marker masks differ across macro-rows")
    if len(occupied_non_marker) != 1:
        errors.append(
            f"found {len(occupied_non_marker)} occupied non-marker cells, expected exactly one template"
        )
        return {}, errors

    template_row, template_col, by_color = occupied_non_marker[0]
    if len(by_color) != 1:
        errors.append("template cell contains multiple colors")
        return {}, errors
    template_color, template_mask = next(iter(by_color.items()))
    if template_color == sep_color or template_color in marker_colors:
        errors.append("template color is not role-distinct from separators and markers")
    if not 5 <= len(template_mask) <= 8:
        errors.append(
            f"template has {len(template_mask)} cells, expected 5 through 8"
        )
    if not _connected(template_mask):
        errors.append("template mask is disconnected")
    if marker_masks and frozenset(template_mask) == marker_masks[0]:
        errors.append("template mask is identical to the marker mask")

    observations = {
        "cell_size": cell_size,
        "row_count": row_count,
        "col_count": col_count,
        "marker_size": len(marker_masks[0]) if marker_masks else 0,
        "template_size": len(template_mask),
        "template_row_index": template_row,
        "template_col_index": template_col,
    }
    return observations, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not uniquely expose one row-stamping lesson."""
    _, errors = _analyze_grid(grid)
    return errors


def observe_overrides(grid):
    """Recover every exact declared axis from the returned input grid."""
    observations, errors = _analyze_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return observations


_CANONICAL_MARKER_MASK = frozenset({(1, 1), (1, 2), (2, 1), (2, 2)})


def _scene(grid):
    """Full parsed scene for a self_check-clean grid, else None.  Pure."""
    observations, errors = _analyze_grid(grid)
    if errors:
        return None
    geometry, geo_errors = _separator_geometry(grid)
    if geo_errors or geometry is None:
        return None
    cell_size = geometry["cell_size"]
    sep_color = geometry["sep_color"]
    row_count = geometry["row_count"]
    col_count = geometry["col_count"]

    def cell_masks(macro_row, macro_col):
        row0 = macro_row * (cell_size + 1)
        col0 = macro_col * (cell_size + 1)
        by_color = {}
        for local_row in range(cell_size):
            for local_col in range(cell_size):
                value = grid[row0 + local_row][col0 + local_col]
                if value != 0:
                    by_color.setdefault(value, set()).add((local_row, local_col))
        return by_color

    marker_colors = []
    for macro_row in range(row_count):
        by_color = cell_masks(macro_row, 0)
        color, mask = next(iter(by_color.items()))
        marker_colors.append(color)
        if macro_row == 0:
            marker_mask = frozenset(mask)
    template_row = observations["template_row_index"]
    template_col = observations["template_col_index"]
    by_color = cell_masks(template_row, template_col)
    template_color, template_mask = next(iter(by_color.items()))
    return {
        **observations,
        "sep_color": sep_color,
        "marker_colors": tuple(marker_colors),
        "marker_mask": marker_mask,
        "template_color": template_color,
        "template_mask": frozenset(template_mask),
    }


def strict_canonical_like(grid) -> list[str]:
    """Semantic-gate hook: canonical-like for THIS task.

    All six official inputs use cell size 4, a square macro layout (3x3,
    4x4, or 5x5), the inset 2x2 marker mask, and one of the canonical 6- or
    8-cell template masks.  Returns [] for such scenes, else reasons.  Pure.
    """
    errors = self_check(grid)
    if errors:
        return list(errors)
    scene = _scene(grid)
    if scene is None:
        return ["grid does not parse into a lattice scene"]
    reasons = []
    if scene["cell_size"] != 4:
        reasons.append(f"canonical cell size is 4, got {scene['cell_size']}")
    if scene["row_count"] != scene["col_count"]:
        reasons.append(
            f"canonical layouts are square, got "
            f"{scene['row_count']}x{scene['col_count']} macro-cells"
        )
    if scene["marker_mask"] != _CANONICAL_MARKER_MASK:
        reasons.append("marker is not the canonical inset 2x2 square")
    canonical_templates = frozenset().union(
        *(set(masks) for masks in _CANONICAL_TEMPLATE_MASKS.values())
    )
    if scene["template_mask"] not in canonical_templates:
        reasons.append(
            f"template mask ({len(scene['template_mask'])} cells) is not one "
            f"of the canonical 6/8-cell masks"
        )
    return reasons


def _witness(predicate):
    def check(grid):
        scene = _scene(grid)
        return scene is not None and predicate(scene)

    return check


# Semantic-gate hook: every scheduled branch the curriculum must exhibit.
# Pre-repair defect: a fixed four-cell template at one location, so most of
# these branches were documented but never generated.
SEMANTIC_WITNESSES = {
    "marker_size_3": _witness(lambda s: s["marker_size"] == 3),
    "marker_size_4": _witness(lambda s: s["marker_size"] == 4),
    "template_size_5": _witness(lambda s: s["template_size"] == 5),
    "template_size_6": _witness(lambda s: s["template_size"] == 6),
    "template_size_7": _witness(lambda s: s["template_size"] == 7),
    "template_size_8": _witness(lambda s: s["template_size"] == 8),
    "template_in_first_row": _witness(lambda s: s["template_row_index"] == 0),
    "template_in_middle_row": _witness(
        lambda s: 0 < s["template_row_index"] < s["row_count"] - 1
    ),
    "template_in_last_row": _witness(
        lambda s: s["template_row_index"] == s["row_count"] - 1
    ),
    "template_in_first_data_col": _witness(lambda s: s["template_col_index"] == 1),
    "template_in_last_col": _witness(
        lambda s: s["template_col_index"] == s["col_count"] - 1
    ),
    "square_layout": _witness(lambda s: s["row_count"] == s["col_count"]),
    "rect_layout": _witness(lambda s: s["row_count"] != s["col_count"]),
    "canonical_cell4_anchor": lambda grid: strict_canonical_like(grid) == [],
}


def _stamp_all(scene, mask, color_of_row):
    """Grid with every macro-cell holding ``mask`` in ``color_of_row(row)``."""
    cell_size = scene["cell_size"]
    row_count = scene["row_count"]
    col_count = scene["col_count"]
    height = row_count * cell_size + row_count - 1
    width = col_count * cell_size + col_count - 1
    out = [[0] * width for _ in range(height)]
    for row in range(cell_size, height, cell_size + 1):
        for col in range(width):
            out[row][col] = scene["sep_color"]
    for col in range(cell_size, width, cell_size + 1):
        for row in range(height):
            out[row][col] = scene["sep_color"]
    for macro_row in range(row_count):
        color = color_of_row(macro_row)
        for macro_col in range(col_count):
            row0 = macro_row * (cell_size + 1)
            col0 = macro_col * (cell_size + 1)
            for local_row, local_col in mask:
                out[row0 + local_row][col0 + local_col] = color
    return out


def _competing_outputs(scene, grid):
    """Named competing rules' outputs; 'true' is the canonical stamping."""
    row_color = lambda macro_row: scene["marker_colors"][macro_row]  # noqa: E731
    outputs = {
        "true": _stamp_all(scene, scene["template_mask"], row_color),
        "stamp_marker_mask": _stamp_all(scene, scene["marker_mask"], row_color),
        "stamp_in_template_color": _stamp_all(
            scene, scene["template_mask"], lambda _row: scene["template_color"]
        ),
        "identity": [list(row) for row in grid],
    }
    source_row_only = [list(row) for row in grid]
    template_row = scene["template_row_index"]
    stamped = outputs["true"]
    row0 = template_row * (scene["cell_size"] + 1)
    for row in range(row0, row0 + scene["cell_size"]):
        source_row_only[row] = list(stamped[row])
    outputs["stamp_source_row_only"] = source_row_only
    keep_markers = [list(row) for row in stamped]
    for macro_row in range(scene["row_count"]):
        base = macro_row * (scene["cell_size"] + 1)
        for local_row in range(scene["cell_size"]):
            for local_col in range(scene["cell_size"]):
                keep_markers[base + local_row][local_col] = grid[base + local_row][local_col]
    outputs["keep_marker_column"] = keep_markers
    return outputs


def lesson_identifiable(demos, query) -> list[str]:
    """Semantic-gate hook: do the demos single out the stamping rule?

    Competing rules tested: replicate the marker mask, stamp in the
    template's own color, stamp only the source macro-row, keep the marker
    column untouched, and identity.  Returns [] when every competitor
    consistent with ALL demos still yields the query's answer.  Pure.
    """
    reasons = []
    demo_scenes = []
    for index, demo in enumerate(demos):
        scene = _scene(demo.get("input"))
        if scene is None:
            reasons.append(f"demo {index} input is not a lawful lattice scene")
        else:
            demo_scenes.append((scene, demo["input"], demo.get("output")))
    query_scene = _scene(query.get("input"))
    if query_scene is None:
        reasons.append("query input is not a lawful lattice scene")
    if reasons:
        return reasons

    surviving = None
    for scene, grid, output in demo_scenes:
        outputs = _competing_outputs(scene, grid)
        consistent = {name for name, out in outputs.items() if out == output}
        if "true" not in consistent:
            reasons.append("a demo output does not match the canonical stamping")
            return reasons
        surviving = consistent if surviving is None else surviving & consistent
    query_outputs = _competing_outputs(query_scene, query["input"])
    query_answer = query.get("output")
    if query_outputs["true"] != query_answer:
        reasons.append("query output does not match the canonical stamping")
        return reasons
    for name in sorted(surviving or set()):
        if name != "true" and query_outputs[name] != query_answer:
            reasons.append(
                f"competing rule {name!r} is consistent with every demo but "
                f"gives a different query answer"
            )
    return reasons


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
    slot = sample_index % EXAMPLES_NEEDED
    cell_range, row_range, col_range = _band_ranges(difficulty)

    canonical_count = 3 + ((seed + sample_index // EXAMPLES_NEEDED) % 3)
    cell_size = _draw_axis(
        ctx,
        "cell_size",
        3,
        5,
        fixed=4 if slot == 0 and "cell_size" not in overrides else None,
    ) if "cell_size" in overrides else _draw_axis(
        ctx,
        "cell_size",
        *cell_range,
        fixed=4 if slot == 0 else None,
    )

    required_rows = (
        overrides["template_row_index"] + 1
        if overrides.get("template_row_index") is not None
        else 3
    )
    required_cols = (
        overrides["template_col_index"] + 1
        if overrides.get("template_col_index") is not None
        else 3
    )
    if overrides.get("row_count") is not None:
        row_count = ctx.draw_int("row_count", 3, 5)
    else:
        lower, upper = max(row_range[0], required_rows), row_range[1]
        if lower > upper:
            lower, upper = required_rows, 5
        row_count = ctx.draw_int(
            "row_count",
            max(canonical_count, required_rows) if slot == 0 else lower,
            max(canonical_count, required_rows) if slot == 0 else upper,
        )
    if overrides.get("col_count") is not None:
        col_count = ctx.draw_int("col_count", 3, 5)
    else:
        lower, upper = max(col_range[0], required_cols), col_range[1]
        if lower > upper:
            lower, upper = required_cols, 5
        col_count = ctx.draw_int(
            "col_count",
            max(canonical_count, required_cols) if slot == 0 else lower,
            max(canonical_count, required_cols) if slot == 0 else upper,
        )
    if overrides.get("template_row_index") is not None and overrides["template_row_index"] >= row_count:
        raise ValueError("template_row_index must be smaller than realized row_count")
    if overrides.get("template_col_index") is not None and overrides["template_col_index"] >= col_count:
        raise ValueError("template_col_index must be smaller than realized col_count")

    marker_fixed = (4, 3, None, 4)[slot]
    marker_size = _draw_axis(
        ctx,
        "marker_size",
        3,
        4,
        fixed=marker_fixed if overrides.get("marker_size") is None else None,
    )
    template_fixed = (None, 5, 7, 8)[slot]
    template_size = _draw_axis(
        ctx,
        "template_size",
        5,
        8,
        fixed=template_fixed if overrides.get("template_size") is None else None,
    )

    if overrides.get("template_row_index") is not None:
        template_row = ctx.draw_int("template_row_index", 0, 4)
    else:
        scheduled_row = (
            row_count - 1,
            0,
            row_count // 2,
            None,
        )[slot]
        template_row = ctx.draw_int(
            "template_row_index",
            scheduled_row if scheduled_row is not None else 0,
            scheduled_row if scheduled_row is not None else row_count - 1,
        )
    if overrides.get("template_col_index") is not None:
        template_col = ctx.draw_int("template_col_index", 1, 4)
    else:
        scheduled_col = (
            1,
            col_count - 1,
            min(2, col_count - 1),
            None,
        )[slot]
        template_col = ctx.draw_int(
            "template_col_index",
            scheduled_col if scheduled_col is not None else 1,
            scheduled_col if scheduled_col is not None else col_count - 1,
        )

    palette = ctx.draw_distinct_colors("role_colors", n=row_count + 2, exclude={0})
    sep_color = palette[0]
    template_color = palette[1]
    marker_colors = palette[2:]
    marker_mask = _marker_mask(
        cell_size,
        marker_size,
        slot,
        ctx.draw_rng("marker_mask"),
    )
    template_mask = _template_mask(
        cell_size,
        template_size,
        slot,
        ctx.draw_rng("template_mask"),
    )

    height = row_count * cell_size + row_count - 1
    width = col_count * cell_size + col_count - 1
    grid = full_grid(height, width, 0)
    for row in range(cell_size, height, cell_size + 1):
        for col in range(width):
            grid[row][col] = sep_color
    for col in range(cell_size, width, cell_size + 1):
        for row in range(height):
            grid[row][col] = sep_color
    for macro_row, color in enumerate(marker_colors):
        row0 = macro_row * (cell_size + 1)
        for local_row, local_col in marker_mask:
            grid[row0 + local_row][local_col] = color
    template_row0 = template_row * (cell_size + 1)
    template_col0 = template_col * (cell_size + 1)
    for local_row, local_col in template_mask:
        grid[template_row0 + local_row][template_col0 + local_col] = template_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator constructed an invalid lesson: " + "; ".join(errors))
    return grid
