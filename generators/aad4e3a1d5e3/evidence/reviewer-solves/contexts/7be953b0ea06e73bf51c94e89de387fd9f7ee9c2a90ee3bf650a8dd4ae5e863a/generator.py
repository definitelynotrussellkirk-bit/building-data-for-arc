"""Task-linked generator for ``aad4e3a1d5e3``.

A near-full color-5 vertical guide and a near-full color-6 horizontal guide
cross at one cell.  A two-color motif lies wholly in one quadrant.  The
selected rule preserves the input and mirrors every motif cell across the
vertical guide, the horizontal guide, and both guides.

The canonical demonstrations always leave the vertical guide unbroken at the
intersection.  This sampler deliberately alternates which guide owns that
cell; horizontal-owned intersections are exact counterexamples to the
canonical-fitting shortcut "only mirror when the vertical 5-guide is full".
"""
from __future__ import annotations

from collections import deque
import copy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aad4e3a1d5e3"
VERSION = "2.0.1"
TASK_ID = "aad4e3a1d5e3"
RULE_HASH = "3fcc1761aea7"  # sha256[:12] of normalized canonical program_solution

SUMMARY = (
    "A 10..12 by 11..14 grid contains crossing near-full 5/6 guides and a "
    "6..9-cell, two-color motif in one quadrant. Reflect the motif across "
    "both guide axes into all four quadrants."
)

EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))

INVARIANTS = [
    "rectangular 10..12 by 11..14 grid using background 0",
    "exactly one near-full color-5 vertical guide and color-6 horizontal guide",
    "the guide intersection is either 5 or 6 and no guide colors occur elsewhere",
    "exactly 6..9 motif cells use exactly two non-guide colors",
    "all motif cells lie in one quadrant and all three reflections are empty and in bounds",
    "the motif union has exactly one or two 4-connected components",
]

DEGENERATE_TEXTURES = (
    "no_guides",
    "multiple_guide_rows",
    "no_motif",
    "motif_on_axis",
    "mixed_quadrants",
    "clipped_reflection",
    "single_color",
    "stray_guide",
    "too_few_cells",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "10..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "11..14",
    },
    "n_cells": {
        "type": "int",
        "default": "scheduled 6..9",
        "valid": "6..9",
    },
    "source_quadrant": {
        "type": "str",
        "default": "scheduled all quadrants",
        "valid": "top_left|top_right|bottom_left|bottom_right",
    },
    "layout": {
        "type": "str",
        "default": "scheduled connected|split",
        "valid": "connected|split",
    },
    "row_axis_position": {
        "type": "str",
        "default": "scheduled center|off_center",
        "valid": "center|off_center",
    },
    "col_axis_position": {
        "type": "str",
        "default": "scheduled center|off_center",
        "valid": "center|off_center",
    },
    "intersection_owner": {
        "type": "str",
        "default": "alternating vertical|horizontal",
        "valid": "vertical|horizontal",
    },
}

_CANONICAL_DIMENSIONS = (
    (11, 13),
    (10, 12),
    (12, 14),
    (11, 11),
    (12, 12),
)

# Any five consecutive samples contain at least two horizontal-owned
# intersections.  Therefore rotating any one sample into the query still
# leaves a demonstration that refutes the named full-vertical-guide shortcut.
_SCHEDULE: tuple[dict[str, Any], ...] = (
    dict(grid_h=11, grid_w=13, n_cells=6, source_quadrant="top_left",     layout="connected", row_axis_position="center",     col_axis_position="center",     intersection_owner="vertical"),
    dict(grid_h=10, grid_w=12, n_cells=7, source_quadrant="top_right",    layout="connected", row_axis_position="off_center", col_axis_position="center",     intersection_owner="horizontal"),
    dict(grid_h=12, grid_w=14, n_cells=8, source_quadrant="bottom_left",  layout="split",     row_axis_position="center",     col_axis_position="off_center", intersection_owner="vertical"),
    dict(grid_h=11, grid_w=11, n_cells=9, source_quadrant="bottom_right", layout="connected", row_axis_position="off_center", col_axis_position="off_center", intersection_owner="horizontal"),
    dict(grid_h=12, grid_w=12, n_cells=7, source_quadrant="top_left",     layout="connected", row_axis_position="center",     col_axis_position="center",     intersection_owner="vertical"),
    dict(grid_h=11, grid_w=13, n_cells=6, source_quadrant="top_right",    layout="split",     row_axis_position="off_center", col_axis_position="center",     intersection_owner="horizontal"),
    dict(grid_h=10, grid_w=12, n_cells=9, source_quadrant="bottom_left",  layout="connected", row_axis_position="center",     col_axis_position="off_center", intersection_owner="vertical"),
    dict(grid_h=12, grid_w=14, n_cells=8, source_quadrant="bottom_right", layout="split",     row_axis_position="off_center", col_axis_position="off_center", intersection_owner="horizontal"),
)

_INT_DOMAINS = {
    "grid_h": tuple(range(10, 13)),
    "grid_w": tuple(range(11, 15)),
    "n_cells": tuple(range(6, 10)),
}
_STR_DOMAINS = {
    "source_quadrant": ("top_left", "top_right", "bottom_left", "bottom_right"),
    "layout": ("connected", "split"),
    "row_axis_position": ("center", "off_center"),
    "col_axis_position": ("center", "off_center"),
    "intersection_owner": ("vertical", "horizontal"),
}


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _component_count(cells: Iterable[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        queue = deque([remaining.pop()])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
    return count


def _guide_rows(grid: list[list[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    w = len(grid[0])
    return [
        r
        for r, row in enumerate(grid)
        if all(value in (5, 6) for value in row)
        and sum(value == 6 for value in row) >= w - 1
    ]


def _guide_cols(grid: list[list[int]]) -> list[int]:
    if not grid or not grid[0]:
        return []
    h, w = len(grid), len(grid[0])
    return [
        c
        for c in range(w)
        if all(grid[r][c] in (5, 6) for r in range(h))
        and sum(grid[r][c] == 5 for r in range(h)) >= h - 1
    ]


def _guide_axes(grid: list[list[int]]) -> tuple[int, int]:
    rows = _guide_rows(grid)
    cols = _guide_cols(grid)
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(
            f"expected one near-full 6-row and one near-full 5-column; found {len(rows)} and {len(cols)}"
        )
    return rows[0], cols[0]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python expression of the selected two-pass mirror rule."""
    row_axis, col_axis = _guide_axes(grid)
    h, w = len(grid), len(grid[0])
    out = _copy_grid(grid)
    interesting = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in interesting:
        mirror_c = 2 * col_axis - c
        if 0 <= mirror_c < w:
            out[r][mirror_c] = value
    second_pass = [
        (r, c, value)
        for r, row in enumerate(out)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    ]
    for r, c, value in second_pass:
        mirror_r = 2 * row_axis - r
        if 0 <= mirror_r < h:
            out[mirror_r][c] = value
    return out


def _scheduled_choice(ctx, name: str, scheduled: Any, overrides: dict[str, Any]) -> Any:
    if name in overrides:
        if name in _INT_DOMAINS:
            options = _INT_DOMAINS[name]
        else:
            options = _STR_DOMAINS[name]
    else:
        options = (scheduled,)
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    allowed = set(AXES) | {"texture"}
    unknown = sorted(set(overrides) - allowed)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, domain in _INT_DOMAINS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if value not in domain:
            raise ValueError(f"override {name!r}={value!r} outside {domain[0]}..{domain[-1]}")
    for name, domain in _STR_DOMAINS.items():
        if name in overrides and overrides[name] is not None and overrides[name] not in domain:
            raise ValueError(f"override {name!r}={overrides[name]!r} not in {domain!r}")
    if "texture" in overrides and overrides["texture"] is not None:
        texture = overrides["texture"]
        if texture not in DEGENERATE_TEXTURES:
            raise ValueError(f"unknown texture {texture!r}")
        extras = sorted(key for key in overrides if key != "texture")
        if extras:
            raise ValueError("degenerate texture cannot be combined with exact-axis overrides")


def _axis_index(size: int, position: str, rng) -> int:
    center = size // 2
    if position == "center":
        return center
    if position != "off_center":
        raise ValueError(f"unknown axis position {position!r}")
    candidates = [
        index
        for index in range(size)
        if index != center and min(index, size - 1 - index) >= 4
    ]
    if not candidates:
        raise ValueError(f"no off-center axis with four-cell reflection span for size {size}")
    return rng.choice(candidates)


def _transform_local_shape(
    cells: set[tuple[int, int]], transform_index: int
) -> set[tuple[int, int]]:
    """Apply one of eight dihedral transforms inside a 4x4 local square."""
    transformed: set[tuple[int, int]] = set()
    for r, c in cells:
        rr, cc = r - 1, c - 1
        if transform_index >= 4:
            cc = 3 - cc
        for _ in range(transform_index % 4):
            rr, cc = cc, 3 - rr
        transformed.add((rr + 1, cc + 1))
    return transformed


def _local_shape(n_cells: int, layout: str, rng) -> set[tuple[int, int]]:
    if layout == "connected":
        path = [
            (1, 1), (1, 2), (1, 3),
            (2, 3), (2, 2), (2, 1),
            (3, 1), (3, 2), (3, 3),
        ]
        cells = set(path[:n_cells])
    elif layout == "split":
        first = [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3)]
        second = [(4, 1), (4, 2), (4, 3), (4, 4)]
        cells = set(first[: n_cells - 4] + second)
    else:
        raise ValueError(f"unknown layout {layout!r}")
    cells = _transform_local_shape(cells, rng.randrange(8))
    expected_components = 1 if layout == "connected" else 2
    if len(cells) != n_cells or _component_count(cells) != expected_components:
        raise AssertionError("local motif template violated its declared layout")
    return cells


def _map_shape_to_quadrant(
    local: set[tuple[int, int]],
    *,
    h: int,
    w: int,
    row_axis: int,
    col_axis: int,
    quadrant: str,
    rng,
) -> set[tuple[int, int]]:
    row_span = min(row_axis, h - 1 - row_axis)
    col_span = min(col_axis, w - 1 - col_axis)
    if row_span < 4 or col_span < 4:
        raise ValueError("guide positions leave less than a 4x4 mirrorable quadrant")
    row_shift = rng.randint(0, row_span - 4)
    col_shift = rng.randint(0, col_span - 4)
    row_sign = -1 if quadrant.startswith("top_") else 1
    col_sign = -1 if quadrant.endswith("_left") else 1
    return {
        (
            row_axis + row_sign * (local_r + row_shift),
            col_axis + col_sign * (local_c + col_shift),
        )
        for local_r, local_c in local
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    del seed, difficulty
    return int(sample_index) % LESSON_SCHEDULE_PERIOD


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    texture = overrides.get("texture")
    if texture is not None:
        return _draw_from_degenerate(texture, ctx)

    profile_index = schedule_profile(seed, sample_index, difficulty)
    profile = dict(_SCHEDULE[profile_index])
    if "n_cells" not in overrides:
        band_base = {"easy": 6, "medium": 7, "hard": 8}.get(difficulty)
        if band_base is not None:
            profile["n_cells"] = band_base + (profile_index % 2)
    values = {
        name: _scheduled_choice(ctx, name, profile[name], overrides)
        for name in AXES
    }
    h = int(values["grid_h"])
    w = int(values["grid_w"])
    n_cells = int(values["n_cells"])
    quadrant = str(values["source_quadrant"])
    layout = str(values["layout"])
    intersection_owner = str(values["intersection_owner"])

    row_axis = _axis_index(
        h, str(values["row_axis_position"]), ctx.draw_rng("row_axis_geometry")
    )
    col_axis = _axis_index(
        w, str(values["col_axis_position"]), ctx.draw_rng("col_axis_geometry")
    )
    local = _local_shape(n_cells, layout, ctx.draw_rng("motif_shape"))
    motif_cells = _map_shape_to_quadrant(
        local,
        h=h,
        w=w,
        row_axis=row_axis,
        col_axis=col_axis,
        quadrant=quadrant,
        rng=ctx.draw_rng("motif_position"),
    )

    colors = tuple(ctx.draw_rng("motif_colors").sample([1, 2, 3, 4, 7, 8, 9], 2))
    ordered_cells = sorted(motif_cells)
    color_rng = ctx.draw_rng("motif_color_assignment")
    color_rng.shuffle(ordered_cells)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[row_axis][c] = 6
    for r in range(h):
        grid[r][col_axis] = 5
    grid[row_axis][col_axis] = 5 if intersection_owner == "vertical" else 6
    for index, (r, c) in enumerate(ordered_cells):
        grid[r][c] = colors[index % 2]

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": values})
    if errors:
        raise AssertionError(f"constructed invalid generator instance: {errors}")
    observed = observe_overrides(grid)
    if observed != values:
        raise AssertionError(f"constructed scene did not realize axes: {observed!r} != {values!r}")
    return _copy_grid(grid)


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    h = len(grid) if isinstance(grid, list) else 0
    w = len(grid[0]) if h and isinstance(grid[0], list) else 0
    result: dict[str, int | str] = {"grid_h": h, "grid_w": w}
    try:
        row_axis, col_axis = _guide_axes(grid)
    except Exception:
        return result

    motif = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    }
    row_signs = {"top" if r < row_axis else "bottom" if r > row_axis else "axis" for r, _ in motif}
    col_signs = {"left" if c < col_axis else "right" if c > col_axis else "axis" for _, c in motif}
    if len(row_signs) == 1 and len(col_signs) == 1 and "axis" not in row_signs | col_signs:
        quadrant = f"{next(iter(row_signs))}_{next(iter(col_signs))}"
    else:
        quadrant = "mixed"
    components = _component_count(motif) if motif else 0
    layout = "connected" if components == 1 else "split" if components == 2 else "other"
    intersection = grid[row_axis][col_axis]
    owner = "vertical" if intersection == 5 else "horizontal" if intersection == 6 else "other"
    result.update(
        {
            "n_cells": len(motif),
            "source_quadrant": quadrant,
            "layout": layout,
            "row_axis_position": "center" if row_axis == h // 2 else "off_center",
            "col_axis_position": "center" if col_axis == w // 2 else "off_center",
            "intersection_owner": owner,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the full lawful input grammar and any requested exact axes."""
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular and nonempty"]
    h = len(grid)
    if not (10 <= h <= 12 and 11 <= w <= 14):
        errors.append(f"grid dimensions {h}x{w} outside 10..12 by 11..14")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    rows = _guide_rows(grid)
    cols = _guide_cols(grid)
    if len(rows) != 1:
        errors.append(f"expected exactly one near-full color-6 guide row, found {len(rows)}")
    if len(cols) != 1:
        errors.append(f"expected exactly one near-full color-5 guide column, found {len(cols)}")
    if len(rows) != 1 or len(cols) != 1:
        return errors
    row_axis, col_axis = rows[0], cols[0]

    intersection = grid[row_axis][col_axis]
    if intersection not in (5, 6):
        errors.append("guide intersection must be color 5 or 6")
    bad_row = [
        (row_axis, c, grid[row_axis][c])
        for c in range(w)
        if c != col_axis and grid[row_axis][c] != 6
    ]
    bad_col = [
        (r, col_axis, grid[r][col_axis])
        for r in range(h)
        if r != row_axis and grid[r][col_axis] != 5
    ]
    if bad_row:
        errors.append(f"horizontal guide has {len(bad_row)} non-6 cells outside the intersection")
    if bad_col:
        errors.append(f"vertical guide has {len(bad_col)} non-5 cells outside the intersection")
    stray_guides = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in (5, 6) and r != row_axis and c != col_axis
    ]
    if stray_guides:
        errors.append(f"found {len(stray_guides)} stray guide-color cells outside the axes")

    motif = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5, 6)
    }
    if not (6 <= len(motif) <= 9):
        errors.append(f"expected 6..9 motif cells, found {len(motif)}")
    motif_colors = {grid[r][c] for r, c in motif}
    if len(motif_colors) != 2:
        errors.append(f"expected exactly two motif colors, found {len(motif_colors)}")
    else:
        counts = {color: sum(grid[r][c] == color for r, c in motif) for color in motif_colors}
        if min(counts.values()) < 2:
            errors.append("each motif color must occur at least twice")
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must remain present")

    row_sides = {-1 if r < row_axis else 1 if r > row_axis else 0 for r, _ in motif}
    col_sides = {-1 if c < col_axis else 1 if c > col_axis else 0 for _, c in motif}
    if len(row_sides) != 1 or 0 in row_sides or len(col_sides) != 1 or 0 in col_sides:
        errors.append("motif cells must lie wholly in exactly one guide-defined quadrant")

    clipped: list[tuple[int, int]] = []
    occupied: list[tuple[tuple[int, int], tuple[int, int], int]] = []
    motif_set = set(motif)
    for r, c in motif:
        destinations = (
            (r, 2 * col_axis - c),
            (2 * row_axis - r, c),
            (2 * row_axis - r, 2 * col_axis - c),
        )
        for nr, nc in destinations:
            if not (0 <= nr < h and 0 <= nc < w):
                clipped.append((nr, nc))
            elif (nr, nc) not in motif_set and grid[nr][nc] != 0:
                occupied.append(((r, c), (nr, nc), grid[nr][nc]))
    if clipped:
        errors.append(f"{len(clipped)} reflected motif destinations are out of bounds")
    if occupied:
        errors.append(f"{len(occupied)} reflected motif destinations are not background")

    if motif:
        components = _component_count(motif)
        if components not in (1, 2):
            errors.append(f"motif union must have one or two components, found {components}")

    observed = observe_overrides(grid)
    requested: dict[str, Any] = {}
    if isinstance(meta, dict):
        candidate = meta.get("overrides", meta)
        if isinstance(candidate, dict):
            requested = candidate
    for name, value in requested.items():
        if name in AXES and observed.get(name) != value:
            errors.append(
                f"override {name} requested {value!r}, observed {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful instances of the exact selected dual-guide mirror rule."""
    return self_check(grid)


def _has_broken_vertical_guide(grid) -> bool:
    """Witness: the horizontal guide owns the intersection, breaking full 5s."""
    try:
        row_axis, col_axis = _guide_axes(grid)
    except Exception:
        return False
    return grid[row_axis][col_axis] == 6 and not all(
        grid[r][col_axis] == 5 for r in range(len(grid))
    )


def _require_unbroken_vertical_guide(grid):
    """RIVAL: mirror only when a literally full color-5 column exists."""
    if not grid or not grid[0]:
        return _copy_grid(grid)
    h, w = len(grid), len(grid[0])
    full_five_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(full_five_cols) != 1:
        return _copy_grid(grid)
    try:
        return rule_mirror(grid)
    except Exception:
        return _copy_grid(grid)


SEMANTIC_WITNESSES = {"broken_vertical_guide": _has_broken_vertical_guide}
SEMANTIC_RIVALS = {"require_unbroken_vertical_guide": _require_unbroken_vertical_guide}
WITNESS_RIVALS = {
    "broken_vertical_guide": ["require_unbroken_vertical_guide"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named wrong rule survives all demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demo {index} input is unlawful: {findings[0]}")
        elif demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the selected rule")
    query_findings = self_check(query["input"])
    if query_findings:
        reasons.append(f"query input is unlawful: {query_findings[0]}")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, which changes the query answer"
                )
    return reasons


def _mutation_base() -> list[list[int]]:
    return generate(
        991,
        0,
        grid_h=10,
        grid_w=11,
        n_cells=7,
        source_quadrant="bottom_right",
        layout="connected",
        row_axis_position="off_center",
        col_axis_position="off_center",
        intersection_owner="vertical",
    )


def mutation_fixtures():
    """Task-linked malformed near-misses that the structural validator rejects."""
    base = _mutation_base()
    row_axis, col_axis = _guide_axes(base)
    motif = [(r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value not in (0, 5, 6)]

    no_guides = _copy_grid(base)
    for r in range(len(no_guides)):
        for c in range(len(no_guides[0])):
            if no_guides[r][c] in (5, 6):
                no_guides[r][c] = 0

    multiple_rows = _copy_grid(base)
    other_row = 0 if row_axis != 0 else len(base) - 1
    for c in range(len(base[0])):
        multiple_rows[other_row][c] = 6
    multiple_rows[other_row][col_axis] = 5

    no_motif = _copy_grid(base)
    for r, c in motif:
        no_motif[r][c] = 0

    motif_on_axis = _copy_grid(base)
    source_r, source_c = motif[0]
    source_color = motif_on_axis[source_r][source_c]
    motif_on_axis[source_r][source_c] = 0
    motif_on_axis[row_axis][source_c] = source_color

    mixed = _copy_grid(base)
    source_r, source_c = motif[0]
    source_color = mixed[source_r][source_c]
    mixed[source_r][source_c] = 0
    mixed[2 * row_axis - source_r][source_c] = source_color

    clipped = _copy_grid(base)
    source_r, source_c = motif[0]
    source_color = clipped[source_r][source_c]
    clipped[source_r][source_c] = 0
    clipped[-1][source_c] = source_color

    single_color = _copy_grid(base)
    colors = sorted({single_color[r][c] for r, c in motif})
    single_color = [
        [colors[0] if value == colors[1] else value for value in row]
        for row in single_color
    ]

    stray_guide = _copy_grid(base)
    target = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if r != row_axis and c != col_axis and stray_guide[r][c] == 0
    )
    stray_guide[target[0]][target[1]] = 5

    too_few = _copy_grid(base)
    for r, c in motif[:2]:
        too_few[r][c] = 0

    return [
        ("no_guides", no_guides),
        ("multiple_guide_rows", multiple_rows),
        ("no_motif", no_motif),
        ("motif_on_axis", motif_on_axis),
        ("mixed_quadrants", mixed),
        ("clipped_reflection", clipped),
        ("single_color", single_color),
        ("stray_guide", stray_guide),
        ("too_few_cells", too_few),
    ]


def _draw_from_degenerate(name: str, ctx):
    del ctx
    fixtures = dict(mutation_fixtures())
    if name not in fixtures:
        raise ValueError(f"unknown degenerate texture {name!r}")
    return _copy_grid(fixtures[name])
