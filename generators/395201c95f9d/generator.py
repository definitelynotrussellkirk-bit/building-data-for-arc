"""Generator for ``arc_puzzle_bank_eighth21:H55``.

Two labeled prototype panels precede a query panel.  The query is a translated,
rotated, or reflected copy of exactly one prototype.  The answer preserves the
query's displayed pose and recolors it with the matching prototype's top-left
label.

Version 3.1 repairs semantic sampling defects in the imported generator: the
query used to be copied at exactly the prototype coordinates in every sampled
example, so no rotation/reflection reasoning was required.  The new curriculum
uses all eight D4 transforms, independently places the query, makes the two
prototypes D4-distinct, and exposes every declared override as an observable
property of the generated grid.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "395201c95f9d"
TASK_ID = "395201c95f9d"
VERSION = "3.1.0"
RULE_HASH = "a99b04260a01"

SUMMARY = (
    "Split the input at the two solid color-9 columns.  The first two equal "
    "panels contain a label at local (0,0) and a monochrome prototype.  The "
    "third panel contains a translated D4 transform (rotation or reflection) "
    "of exactly one prototype.  Return a blank panel of the same size with "
    "the query cells kept in their displayed positions and recolored with "
    "the matching prototype's label."
)

INVARIANTS = [
    "three equal panels are separated by exactly two full-height color-9 columns",
    "prototype labels occupy local (0,0), and prototype shapes exclude that cell",
    "the two connected prototype supports are D4-distinct",
    "the connected query support matches exactly one prototype under D4",
    "the output preserves query coordinates and uses the winning label color",
]

_CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
_ROTATION_CODES = ("id", "r1", "r2", "r3")
_REFLECTION_CODES = frozenset(("fh", "fv", "tr", "atr"))
# The 16-step schedule crosses every D4 transform with both possible matching
# panels.  Its repeating four semantic roles are panel-0 reflection,
# panel-1 rotation, panel-0 rotation, panel-1 reflection; therefore every four
# consecutive examples demonstrates both labels and both transform classes for
# each label.  This blocks the narrower canonical-fitting shortcut "recognize
# panel 1 only under rotations; otherwise choose panel 0."
_SCHEDULE_CODES = (
    "fh", "r1", "r1", "fh",
    "fv", "r2", "r2", "fv",
    "tr", "r3", "r3", "tr",
    "atr", "id", "id", "atr",
)
_BAND_CELL_COUNTS = {None: 5, "easy": 4, "medium": 5, "hard": 6}
_BAND_VARIANT_SIZES = {
    None: ((5, 6), (6, 5), (6, 6)),
    "easy": ((4, 4), (4, 5), (5, 4)),
    "medium": ((5, 6), (6, 5), (6, 6)),
    "hard": ((6, 7), (7, 6), (8, 7)),
}

AXES = {
    "panel_h": {
        "type": "int",
        "default": "canonical 5 most draws; scheduled band-specific variants",
        "valid": "4..8",
    },
    "panel_w": {
        "type": "int",
        "default": "canonical 5 most draws; scheduled band-specific variants",
        "valid": "4..7",
    },
    "cell_count": {
        "type": "int",
        "default": "4 easy, 5 medium/default, 6 hard",
        "valid": "4..6",
    },
    "match_panel": {
        "type": "int",
        "default": "sample_index mod 2",
        "valid": "0..1",
    },
    "transform": {
        "type": "enum",
        "default": "8-step D4 curriculum",
        "valid": "id|r1|r2|r3|fh|fv|tr|atr",
    },
}
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def _normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    if not cells:
        return []
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return sorted((r - min_r, c - min_c) for r, c in cells)


def _dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    if not cells:
        return (0, 0)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _xform(cells: Iterable[tuple[int, int]], code: str) -> list[tuple[int, int]]:
    cells = _normalize(cells)
    if code not in _CODES:
        raise ValueError(f"unknown transform: {code!r}")
    h, w = _dims(cells)
    if code == "id":
        raw = cells
    elif code == "r1":
        raw = [(c, h - 1 - r) for r, c in cells]
    elif code == "r2":
        raw = [(h - 1 - r, w - 1 - c) for r, c in cells]
    elif code == "r3":
        raw = [(w - 1 - c, r) for r, c in cells]
    elif code == "fh":
        raw = [(r, w - 1 - c) for r, c in cells]
    elif code == "fv":
        raw = [(h - 1 - r, c) for r, c in cells]
    elif code == "tr":
        raw = [(c, r) for r, c in cells]
    else:  # anti-transpose = rotate-180(transpose(cells))
        raw = [(w - 1 - c, h - 1 - r) for r, c in cells]
    return _normalize(raw)


def _orbit(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(sorted({tuple(_xform(cells, code)) for code in _CODES}))


def _dihedral_canon(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    return min(_orbit(cells))


def _connected(cells: Iterable[tuple[int, int]]) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    stack = [next(iter(remaining))]
    seen: set[tuple[int, int]] = set()
    while stack:
        cell = stack.pop()
        if cell in seen:
            continue
        seen.add(cell)
        r, c = cell
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in remaining and neighbor not in seen:
                stack.append(neighbor)
    return seen == remaining


def _enumerate_families(cell_count: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All connected D4 classes of ``cell_count`` cells in a 3x3 box."""
    by_canon: dict[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]] = {}
    positions = tuple((r, c) for r in range(3) for c in range(3))
    for subset in combinations(positions, cell_count):
        if not _connected(subset):
            continue
        normalized = tuple(_normalize(subset))
        canon = _dihedral_canon(normalized)
        by_canon.setdefault(canon, normalized)
    return tuple(sorted(by_canon))


_FAMILIES = {count: _enumerate_families(count) for count in (4, 5, 6)}
_FULL_ORBIT_FAMILIES = {
    count: tuple(shape for shape in families if len(_orbit(shape)) == 8)
    for count, families in _FAMILIES.items()
}
if any(len(_FAMILIES[count]) < 2 or not _FULL_ORBIT_FAMILIES[count] for count in (4, 5, 6)):
    raise AssertionError("3x3 shape census cannot support the declared curriculum")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> tuple[int, str]:
    """Return the deterministic semantic curriculum point for one example."""
    del seed, difficulty
    return sample_index % 2, _SCHEDULE_CODES[sample_index % len(_SCHEDULE_CODES)]


SCHEDULE_PROFILES = tuple(
    (sample_index % 2, _SCHEDULE_CODES[sample_index])
    for sample_index in range(len(_SCHEDULE_CODES))
)


def _scheduled_size(sample_index: int, difficulty: str | None) -> tuple[int, int]:
    # Two thirds of natural draws have the canonical 5x17 / seven-color input
    # profile in every band; the remaining third broadens panel scale.
    if sample_index % 3 != 2:
        return (5, 5)
    variants = _BAND_VARIANT_SIZES[difficulty]
    return variants[(sample_index // 3) % len(variants)]


def _choose_prototypes(rng, cell_count: int, match_panel: int) -> list[list[tuple[int, int]]]:
    matched_family = rng.choice(_FULL_ORBIT_FAMILIES[cell_count])
    distractor_pool = [
        shape
        for shape in _FAMILIES[cell_count]
        if _dihedral_canon(shape) != _dihedral_canon(matched_family)
    ]
    distractor = rng.choice(distractor_pool)
    families = [matched_family, distractor]
    if match_panel == 1:
        families.reverse()
    return [_xform(shape, rng.choice(_CODES)) for shape in families]


def _placements(
    cells: Iterable[tuple[int, int]],
    panel_h: int,
    panel_w: int,
    *,
    reserved: Iterable[tuple[int, int]] = (),
    excluded: Iterable[tuple[tuple[int, int], ...]] = (),
) -> list[tuple[tuple[int, int], ...]]:
    normalized = _normalize(cells)
    shape_h, shape_w = _dims(normalized)
    reserved_set = set(reserved)
    excluded_set = set(excluded)
    out: list[tuple[tuple[int, int], ...]] = []
    for dr in range(panel_h - shape_h + 1):
        for dc in range(panel_w - shape_w + 1):
            placed = tuple(sorted((r + dr, c + dc) for r, c in normalized))
            if reserved_set.intersection(placed) or placed in excluded_set:
                continue
            out.append(placed)
    return out


def _choose_placement(
    rng,
    cells: Iterable[tuple[int, int]],
    panel_h: int,
    panel_w: int,
    *,
    reserved: Iterable[tuple[int, int]] = (),
    excluded: Iterable[tuple[tuple[int, int], ...]] = (),
) -> tuple[tuple[int, int], ...]:
    candidates = _placements(
        cells,
        panel_h,
        panel_w,
        reserved=reserved,
        excluded=excluded,
    )
    if not candidates:
        raise ValueError("shape has no legal panel placement")
    return rng.choice(candidates)


def _paint_local(
    grid: list[list[int]],
    panel_left: int,
    cells: Iterable[tuple[int, int]],
    color: int,
) -> None:
    for r, c in cells:
        grid[r][panel_left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _BAND_CELL_COUNTS:
        raise ValueError(
            f"unknown difficulty: {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    scheduled_match, scheduled_transform = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w = _scheduled_size(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if "panel_h" in overrides:
        panel_h = ctx.draw_int("panel_h", 4, 8)
    else:
        panel_h = ctx.draw_choice("panel_h", (scheduled_h,))
    if "panel_w" in overrides:
        panel_w = ctx.draw_int("panel_w", 4, 7)
    else:
        panel_w = ctx.draw_choice("panel_w", (scheduled_w,))
    if "cell_count" in overrides:
        cell_count = ctx.draw_int("cell_count", 4, 6)
    else:
        cell_count = ctx.draw_choice("cell_count", (_BAND_CELL_COUNTS[difficulty],))
    if "match_panel" in overrides:
        match_panel = ctx.draw_int("match_panel", 0, 1)
    else:
        match_panel = ctx.draw_choice("match_panel", (scheduled_match,))
    if "transform" in overrides:
        transform = ctx.draw_choice("transform", _CODES)
    else:
        transform = ctx.draw_choice("transform", (scheduled_transform,))

    shape_rng = ctx.draw_rng("prototype_families")
    placement_rng = ctx.draw_rng("placements")
    prototypes = _choose_prototypes(shape_rng, cell_count, match_panel)
    prototype_cells = [
        _choose_placement(
            placement_rng,
            shape,
            panel_h,
            panel_w,
            reserved=((0, 0),),
        )
        for shape in prototypes
    ]
    query_shape = _xform(prototype_cells[match_panel], transform)
    query_cells = _choose_placement(
        placement_rng,
        query_shape,
        panel_h,
        panel_w,
        excluded=(prototype_cells[match_panel],),
    )

    label0, label1, shape0_color, shape1_color, query_color = ctx.draw_distinct_colors(
        "role_colors", n=5, exclude=(0, 9)
    )

    full_w = 3 * panel_w + 2
    sep0 = panel_w
    sep1 = 2 * panel_w + 1
    grid = full_grid(panel_h, full_w, 0)
    for row in range(panel_h):
        grid[row][sep0] = 9
        grid[row][sep1] = 9

    lefts = (0, panel_w + 1, 2 * panel_w + 2)
    grid[0][lefts[0]] = label0
    grid[0][lefts[1]] = label1
    _paint_local(grid, lefts[0], prototype_cells[0], shape0_color)
    _paint_local(grid, lefts[1], prototype_cells[1], shape1_color)
    _paint_local(grid, lefts[2], query_cells, query_color)

    requested = {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "cell_count": cell_count,
        "match_panel": match_panel,
        "transform": transform,
    }
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": requested})
    if errors:
        raise AssertionError(f"internal invalid generation: {errors}")
    return grid


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"]
    errors: list[str] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color integer")
    return errors


def _shape_data(
    grid: Any,
    *,
    left: int,
    panel_w: int,
    exclude_label: bool,
) -> dict[str, Any]:
    raw_cells: list[tuple[int, int]] = []
    colors: set[int] = set()
    for r in range(len(grid)):
        for c in range(panel_w):
            if exclude_label and (r, c) == (0, 0):
                continue
            value = grid[r][left + c]
            if value != 0:
                raw_cells.append((r, c))
                colors.add(value)
    normalized = _normalize(raw_cells)
    return {
        "raw_cells": tuple(sorted(raw_cells)),
        "cells": tuple(normalized),
        "colors": tuple(sorted(colors)),
        "color": next(iter(colors)) if len(colors) == 1 else None,
        "count": len(raw_cells),
        "connected": _connected(normalized),
    }


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    panel_h = len(grid)
    full_w = len(grid[0])
    if panel_h < 3:
        errors.append(f"expected at least 3 rows, found {panel_h}")
    separator_columns = [
        c for c in range(full_w) if all(grid[r][c] == 9 for r in range(panel_h))
    ]
    if len(separator_columns) != 2:
        errors.append(
            f"expected exactly 2 full-height color-9 separators, found {len(separator_columns)}"
        )
        return result

    sep0, sep1 = separator_columns
    widths = (sep0, sep1 - sep0 - 1, full_w - sep1 - 1)
    if widths[0] <= 0 or len(set(widths)) != 1:
        errors.append(f"expected three equal nonempty panel widths, found {widths}")
        return result
    panel_w = widths[0]
    lefts = (0, sep0 + 1, sep1 + 1)
    if (sep0, sep1) != (panel_w, 2 * panel_w + 1):
        errors.append("separator positions are inconsistent with equal-width panels")

    for r in range(panel_h):
        for c in range(full_w):
            if c not in separator_columns and grid[r][c] == 9:
                errors.append(f"color 9 leaked into panel cell ({r},{c})")

    labels = (grid[0][lefts[0]], grid[0][lefts[1]])
    for index, label in enumerate(labels):
        if label in (0, 9):
            errors.append(f"prototype panel {index} has invalid label {label} at local (0,0)")
    if labels[0] == labels[1]:
        errors.append("prototype labels must be distinct")

    prototypes = [
        _shape_data(grid, left=lefts[index], panel_w=panel_w, exclude_label=True)
        for index in range(2)
    ]
    query = _shape_data(grid, left=lefts[2], panel_w=panel_w, exclude_label=False)

    for index, data in enumerate(prototypes):
        if not data["raw_cells"]:
            errors.append(f"prototype panel {index} shape is empty")
        if len(data["colors"]) != 1:
            errors.append(
                f"prototype panel {index} shape has {len(data['colors'])} colors, expected 1"
            )
        if data["raw_cells"] and not data["connected"]:
            errors.append(f"prototype panel {index} shape is not 4-connected")
        if data["raw_cells"] and not 3 <= data["count"] <= 6:
            errors.append(
                f"prototype panel {index} has {data['count']} cells, expected 3..6"
            )
    if not query["raw_cells"]:
        errors.append("query shape is empty")
    if len(query["colors"]) != 1:
        errors.append(f"query shape has {len(query['colors'])} colors, expected 1")
    if query["raw_cells"] and not query["connected"]:
        errors.append("query shape is not 4-connected")
    if query["raw_cells"] and not 3 <= query["count"] <= 6:
        errors.append(f"query has {query['count']} cells, expected 3..6")

    if all(proto["cells"] for proto in prototypes):
        canons = [_dihedral_canon(proto["cells"]) for proto in prototypes]
        if len(set(canons)) != 2:
            errors.append("prototype shapes are not D4-distinct")

    matches: list[tuple[int, tuple[str, ...]]] = []
    if query["cells"]:
        for index, prototype in enumerate(prototypes):
            codes = tuple(
                code for code in _CODES if tuple(_xform(prototype["cells"], code)) == query["cells"]
            )
            if codes:
                matches.append((index, codes))
    if len(matches) != 1:
        errors.append(f"query shape matches {len(matches)} prototypes under D4, expected 1")

    prototype_counts = tuple(int(proto["count"]) for proto in prototypes)
    matched_panel = matches[0][0] if len(matches) == 1 else None
    matched_codes = matches[0][1] if len(matches) == 1 else ()
    common_count = (
        prototype_counts[0]
        if len(set(prototype_counts + (int(query["count"]),))) == 1
        else None
    )
    result.update(
        {
            "errors": errors,
            "panel_h": panel_h,
            "panel_w": panel_w,
            "separator_columns": tuple(separator_columns),
            "label_colors": tuple(labels),
            "prototype_cells": tuple(proto["cells"] for proto in prototypes),
            "prototype_raw_cells": tuple(proto["raw_cells"] for proto in prototypes),
            "prototype_counts": prototype_counts,
            "prototype_colors": tuple(proto["color"] for proto in prototypes),
            "query_cells": query["cells"],
            "query_raw_cells": query["raw_cells"],
            "query_count": int(query["count"]),
            "query_color": query["color"],
            "matched_panel": matched_panel,
            "matched_codes": matched_codes,
            "matched_transform_count": len(matched_codes),
            "transform": matched_codes[0] if len(matched_codes) == 1 else None,
            "cell_count": common_count,
        }
    )
    return result


def semantic_observables(grid: Any) -> dict[str, Any]:
    """Expose selected-rule facts derived only from the visible grid."""
    return _analysis(grid)


def observe_overrides(grid: Any) -> dict[str, int | str]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["cell_count"] is None:
        raise ValueError("cell_count is not uniquely observable")
    if facts["matched_panel"] is None:
        raise ValueError("match_panel is not uniquely observable")
    if facts["transform"] is None:
        raise ValueError("transform is not uniquely observable")
    return {
        "panel_h": int(facts["panel_h"]),
        "panel_w": int(facts["panel_w"]),
        "cell_count": int(facts["cell_count"]),
        "match_panel": int(facts["matched_panel"]),
        "transform": str(facts["transform"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    facts = _analysis(grid)
    errors = list(facts["errors"])
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        requested = meta["overrides"]
        try:
            observed = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for key, expected in requested.items():
                if key in AXES and observed.get(key) != expected:
                    errors.append(
                        f"override {key}={expected!r} realized as {observed.get(key)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Validate the selected rule's panel, label, and D4-match grammar."""
    return self_check(grid)


def _output_from_cells(
    panel_h: int,
    panel_w: int,
    cells: Iterable[tuple[int, int]],
    color: int,
) -> list[list[int]]:
    output = full_grid(panel_h, panel_w, 0)
    for r, c in cells:
        output[r][c] = color
    return output


def rule_mirror(grid: Any) -> list[list[int]]:
    """Pure Python mirror of the selected Racket authority."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    matched = int(facts["matched_panel"])
    return _output_from_cells(
        int(facts["panel_h"]),
        int(facts["panel_w"]),
        facts["query_raw_cells"],
        int(facts["label_colors"][matched]),
    )


def _rival_output_for_panel(
    grid: Any,
    panel: int,
    *,
    cells: Iterable[tuple[int, int]] | None = None,
    color: int | None = None,
) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    chosen_cells = facts["query_raw_cells"] if cells is None else cells
    chosen_color = facts["label_colors"][panel] if color is None else color
    return _output_from_cells(
        int(facts["panel_h"]), int(facts["panel_w"]), chosen_cells, int(chosen_color)
    )


def _rival_panel(panel: int) -> Callable[[Any], list[list[int]]]:
    return lambda grid: _rival_output_for_panel(grid, panel)


def _rival_same_count_leftmost(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query_count = int(facts["query_count"])
    panel = next(
        (i for i, count in enumerate(facts["prototype_counts"]) if count == query_count),
        0,
    )
    return _rival_output_for_panel(grid, panel)


def _rival_exact_coordinates_else_panel_1(grid: Any) -> list[list[int]]:
    """The imported generator's accidental rule: exact local coordinates only."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query = facts["query_raw_cells"]
    if query == facts["prototype_raw_cells"][0]:
        panel = 0
    elif query == facts["prototype_raw_cells"][1]:
        panel = 1
    else:
        panel = 1
    return _rival_output_for_panel(grid, panel)


def _rival_rotations_only_else_panel_1(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query = facts["query_cells"]
    panel = 1
    for index, prototype in enumerate(facts["prototype_cells"]):
        if any(tuple(_xform(prototype, code)) == query for code in _ROTATION_CODES):
            panel = index
            break
    return _rival_output_for_panel(grid, panel)


def _rival_one_panel_transform_class(
    grid: Any,
    *,
    inspected_panel: int,
    allowed_codes: Iterable[str],
    fallback_panel: int,
) -> list[list[int]]:
    """Match one panel under only one transform class, otherwise default."""
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    query = facts["query_cells"]
    prototype = facts["prototype_cells"][inspected_panel]
    panel = (
        inspected_panel
        if any(tuple(_xform(prototype, code)) == query for code in allowed_codes)
        else fallback_panel
    )
    return _rival_output_for_panel(grid, panel)


def _rival_panel1_rotations_else_panel0(grid: Any) -> list[list[int]]:
    return _rival_one_panel_transform_class(
        grid,
        inspected_panel=1,
        allowed_codes=_ROTATION_CODES,
        fallback_panel=0,
    )


def _rival_panel1_reflections_else_panel0(grid: Any) -> list[list[int]]:
    return _rival_one_panel_transform_class(
        grid,
        inspected_panel=1,
        allowed_codes=_REFLECTION_CODES,
        fallback_panel=0,
    )


def _rival_panel0_rotations_else_panel1(grid: Any) -> list[list[int]]:
    return _rival_one_panel_transform_class(
        grid,
        inspected_panel=0,
        allowed_codes=_ROTATION_CODES,
        fallback_panel=1,
    )


def _rival_panel0_reflections_else_panel1(grid: Any) -> list[list[int]]:
    return _rival_one_panel_transform_class(
        grid,
        inspected_panel=0,
        allowed_codes=_REFLECTION_CODES,
        fallback_panel=1,
    )


def _rival_copy_query_color(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return _output_from_cells(
        int(facts["panel_h"]),
        int(facts["panel_w"]),
        facts["query_raw_cells"],
        int(facts["query_color"]),
    )


def _rival_paint_prototype_pose(grid: Any) -> list[list[int]]:
    facts = _analysis(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    panel = int(facts["matched_panel"])
    return _rival_output_for_panel(
        grid,
        panel,
        cells=facts["prototype_raw_cells"][panel],
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_panel_0": _rival_panel(0),
    "always_panel_1": _rival_panel(1),
    "same_count_leftmost": _rival_same_count_leftmost,
    "exact_coordinates_else_panel_1": _rival_exact_coordinates_else_panel_1,
    "rotations_only_else_panel_1": _rival_rotations_only_else_panel_1,
    "panel1_rotations_else_panel0": _rival_panel1_rotations_else_panel0,
    "panel1_reflections_else_panel0": _rival_panel1_reflections_else_panel0,
    "panel0_rotations_else_panel1": _rival_panel0_rotations_else_panel1,
    "panel0_reflections_else_panel1": _rival_panel0_reflections_else_panel1,
    "copy_query_color": _rival_copy_query_color,
    "paint_prototype_pose": _rival_paint_prototype_pose,
}
CANONICAL_SHORTCUTS = {
    "exact_coordinates_else_panel_1": _rival_exact_coordinates_else_panel_1,
    "panel1_rotations_else_panel0": _rival_panel1_rotations_else_panel0,
    "panel1_reflections_else_panel0": _rival_panel1_reflections_else_panel0,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _fact(grid: Any, key: str, default: Any = None) -> Any:
    return semantic_observables(grid).get(key, default)


def _valid(grid: Any) -> bool:
    return not bool(_fact(grid, "errors", ["invalid"]))


def _pose_differs(grid: Any) -> bool:
    facts = semantic_observables(grid)
    panel = facts.get("matched_panel")
    return (
        not facts.get("errors")
        and panel in (0, 1)
        and facts.get("query_raw_cells") != facts.get("prototype_raw_cells", ((), ()))[panel]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "panel_zero_selected": lambda grid: _valid(grid) and _fact(grid, "matched_panel") == 0,
    "panel_one_selected": lambda grid: _valid(grid) and _fact(grid, "matched_panel") == 1,
    "old_exact_coordinate_shortcut_refuted": lambda grid: (
        _valid(grid) and _fact(grid, "matched_panel") == 0 and _pose_differs(grid)
    ),
    "reflection_required": lambda grid: (
        _valid(grid)
        and _fact(grid, "matched_panel") == 0
        and _fact(grid, "transform") in _REFLECTION_CODES
    ),
    "panel_zero_rotation": lambda grid: (
        _valid(grid)
        and _fact(grid, "matched_panel") == 0
        and _fact(grid, "transform") in _ROTATION_CODES
    ),
    "panel_zero_reflection": lambda grid: (
        _valid(grid)
        and _fact(grid, "matched_panel") == 0
        and _fact(grid, "transform") in _REFLECTION_CODES
    ),
    "panel_one_rotation": lambda grid: (
        _valid(grid)
        and _fact(grid, "matched_panel") == 1
        and _fact(grid, "transform") in _ROTATION_CODES
    ),
    "panel_one_reflection": lambda grid: (
        _valid(grid)
        and _fact(grid, "matched_panel") == 1
        and _fact(grid, "transform") in _REFLECTION_CODES
    ),
    "query_repaint_required": lambda grid: (
        _valid(grid)
        and _fact(grid, "query_color")
        != _fact(grid, "label_colors", (None, None))[_fact(grid, "matched_panel")]
    ),
    "query_pose_required": _pose_differs,
}
WITNESS_RIVALS = {
    "panel_zero_selected": ("always_panel_1",),
    "panel_one_selected": ("always_panel_0", "same_count_leftmost"),
    "old_exact_coordinate_shortcut_refuted": ("exact_coordinates_else_panel_1",),
    "reflection_required": ("rotations_only_else_panel_1",),
    "panel_zero_rotation": ("panel0_reflections_else_panel1",),
    "panel_zero_reflection": ("panel0_rotations_else_panel1",),
    "panel_one_rotation": ("panel1_reflections_else_panel0",),
    "panel_one_reflection": ("panel1_rotations_else_panel0",),
    "query_repaint_required": ("copy_query_color",),
    "query_pose_required": ("paint_prototype_pose",),
}

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} is malformed"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input invalid: {errors[0]}"]
    try:
        official = rule_mirror(pair["input"])
    except ValueError as exc:
        return [f"{label} mirror failed: {exc}"]
    if official != pair["output"]:
        return [f"{label} output does not follow the selected rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to falsify every declared shortcut."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        errors.extend(_pair_errors(pair, f"demo {index}"))
    errors.extend(_pair_errors(query, "query"))
    if errors:
        return errors

    matched_panels = {
        int(semantic_observables(pair["input"])["matched_panel"]) for pair in demos
    }
    if matched_panels != {0, 1}:
        errors.append("demonstrations must cover both prototype labels")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"surviving lesson shortcut: {name}")
    return errors


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local near-misses that the validator must reject."""
    grid = generate(991, 0, difficulty="easy")
    facts = semantic_observables(grid)
    panel_w = int(facts["panel_w"])
    lefts = (0, panel_w + 1, 2 * panel_w + 2)

    broken_separator = [list(row) for row in grid]
    broken_separator[0][panel_w] = 0

    duplicate_prototype = [list(row) for row in grid]
    for r in range(len(grid)):
        for c in range(panel_w):
            if (r, c) != (0, 0):
                duplicate_prototype[r][lefts[1] + c] = 0
    duplicate_color = int(facts["prototype_colors"][1])
    for r, c in facts["prototype_raw_cells"][0]:
        duplicate_prototype[r][lefts[1] + c] = duplicate_color

    empty_query = [list(row) for row in grid]
    for r in range(len(grid)):
        for c in range(panel_w):
            empty_query[r][lefts[2] + c] = 0

    multicolor_query = [list(row) for row in grid]
    qr, qc = facts["query_raw_cells"][0]
    replacement = next(
        color
        for color in range(1, 9)
        if color != facts["query_color"] and color != 9
    )
    multicolor_query[qr][lefts[2] + qc] = replacement

    erased_label = [list(row) for row in grid]
    erased_label[0][0] = 0

    return [
        ("broken_separator", broken_separator),
        ("d4_duplicate_prototype", duplicate_prototype),
        ("empty_query", empty_query),
        ("multicolor_query", multicolor_query),
        ("erased_label", erased_label),
    ]
