"""Generator for 3f26d45b9f51 — connect equal-color markers on a cell lattice.

The input is a K×K lattice of 2×2 cells separated by one-pixel dividers.
The divider color is a role, not a fixed value: it is the modal non-zero
lattice color.  Marker cells are uniform 2×2 blocks in other colors.
For each marker color independently, fill every coarse-cell interval whose
endpoints are same-color markers in a shared row or shared column.  Markers
that share neither row nor column with a same-color peer remain unchanged.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3f26d45b9f51"
VERSION = "4.0.0"  # exact axes + collinear-triple teaching witness
TASK_ID = "3f26d45b9f51"
RULE_HASH = "54129d31ff5b"

SUMMARY = (
    "A square (3*K-1)×(3*K-1) lattice of K×K 2x2 cells is separated by "
    "single-pixel divider rows/columns in a modal non-zero divider color. "
    "Uniform 2x2 marker cells use other colors. For each marker color, fill "
    "all coarse cells between same-color markers that share a coarse row or "
    "column. A color may connect on both axes, and singleton/off-line markers "
    "that share no row/column with a same-color peer stay unchanged."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "grid is square with side 3*K-1 for K in 7..9",
    "every r%3==2 or c%3==2 pixel is one common non-zero divider color",
    "every lattice cell is a uniform 2x2 block: empty 0 or a non-divider marker color",
    "there are 2..4 distinct marker colors and at least one same-color row/column connection",
    "different marker colors have disjoint connection spans, so rule application is order-independent",
]

AXES = {
    "K": {
        "type": "int",
        "default": "rng 7..9",
        "valid": "7..9",
        "doc": "Lattice side in 2x2 cells; canonical inputs use K=7,8,9.",
    },
    "n_colors": {
        "type": "int",
        "default": "rng 2..4",
        "valid": "2..4",
        "doc": "Exact number of distinct marker colors, excluding 0 and the divider.",
    },
}

_DIVIDER_SCHEDULE = (1, 8, 4, 5)


def _place_2x2(grid: list[list[int]], cell_r: int, cell_c: int, color: int) -> None:
    r0, c0 = 3 * cell_r, 3 * cell_c
    for dr in range(2):
        for dc in range(2):
            grid[r0 + dr][c0 + dc] = color


def _connection_spans(cells: Sequence[tuple[int, int]]) -> tuple[set[tuple[int, int]], int, int]:
    """Return filled coarse cells plus counts of horizontal/vertical line witnesses."""
    rows: dict[int, list[int]] = defaultdict(list)
    cols: dict[int, list[int]] = defaultdict(list)
    for row, col in cells:
        rows[row].append(col)
        cols[col].append(row)

    span: set[tuple[int, int]] = set()
    horizontal = 0
    vertical = 0
    for row, values in rows.items():
        uniq = sorted(set(values))
        if len(uniq) >= 2:
            horizontal += 1
            span.update((row, col) for col in range(uniq[0], uniq[-1] + 1))
    for col, values in cols.items():
        uniq = sorted(set(values))
        if len(uniq) >= 2:
            vertical += 1
            span.update((row, col) for row in range(uniq[0], uniq[-1] + 1))
    return span, horizontal, vertical


def _analyze(grid: Any) -> dict[str, Any]:
    info: dict[str, Any] = {
        "errors": [],
        "height": 0,
        "width": 0,
        "K": None,
        "divider": None,
        "markers": {},
        "spans": {},
        "horizontal_lines": 0,
        "vertical_lines": 0,
        "unconnected_markers": [],
        "dual_axis_colors": [],
    }
    errors: list[str] = info["errors"]
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        errors.append("grid must be a non-empty list of non-empty rows")
        return info
    height, width = len(grid), len(grid[0])
    info["height"], info["width"] = height, width
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        errors.append("grid must be rectangular")
        return info
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
        return info
    if (height + 1) % 3:
        errors.append(f"grid side must equal 3*K-1, got {height}")
        return info
    K = (height + 1) // 3
    info["K"] = K
    if not 7 <= K <= 9:
        errors.append(f"K must be in 7..9, got {K}")

    if height < 3:
        errors.append("grid is too small to contain divider lines")
        return info
    divider = grid[2][0]
    info["divider"] = divider
    if not isinstance(divider, int) or divider == 0:
        errors.append(f"divider color must be non-zero, got {divider!r}")
        return info

    for r in range(height):
        for c in range(width):
            value = grid[r][c]
            if not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                return info
            is_divider = r % 3 == 2 or c % 3 == 2
            if is_divider and value != divider:
                errors.append(
                    f"divider lattice broken at ({r},{c}): expected {divider}, got {value}"
                )
                return info

    markers: dict[int, list[tuple[int, int]]] = defaultdict(list)
    interior_counts: dict[int, int] = defaultdict(int)
    for cell_r in range(K):
        for cell_c in range(K):
            vals = {
                grid[3 * cell_r + dr][3 * cell_c + dc]
                for dr in range(2)
                for dc in range(2)
            }
            if len(vals) != 1:
                errors.append(f"coarse cell ({cell_r},{cell_c}) is not a uniform 2x2 block")
                continue
            value = next(iter(vals))
            interior_counts[value] += 4
            if value == divider:
                errors.append(
                    f"divider color {divider} may not appear inside coarse cell ({cell_r},{cell_c})"
                )
            elif value != 0:
                markers[value].append((cell_r, cell_c))

    info["markers"] = {color: sorted(cells) for color, cells in markers.items()}
    if not 2 <= len(markers) <= 4:
        errors.append(f"expected 2..4 marker colors, got {len(markers)}")
    for color, cells in markers.items():
        if not 1 <= len(cells) <= 4:
            errors.append(f"marker color {color} must occupy 1..4 coarse cells, got {len(cells)}")

    divider_pixels = sum(
        1
        for r in range(height)
        for c in range(width)
        if r % 3 == 2 or c % 3 == 2
    )
    zero_pixels = interior_counts.get(0, 0)
    max_marker_pixels = max((4 * len(cells) for cells in markers.values()), default=0)
    if divider_pixels <= max(zero_pixels, max_marker_pixels):
        errors.append(
            "divider must be the unique modal color so the canonical oracle can identify its role"
        )

    spans: dict[int, set[tuple[int, int]]] = {}
    horizontal_lines = 0
    vertical_lines = 0
    unconnected: list[tuple[int, tuple[int, int]]] = []
    dual_axis_colors: list[int] = []
    for color, cells in markers.items():
        span, horizontal, vertical = _connection_spans(cells)
        spans[color] = span
        horizontal_lines += horizontal
        vertical_lines += vertical
        if horizontal and vertical:
            dual_axis_colors.append(color)
        for cell in cells:
            row, col = cell
            if not any(
                other != cell and (other[0] == row or other[1] == col)
                for other in cells
            ):
                unconnected.append((color, cell))

    info["spans"] = spans
    info["horizontal_lines"] = horizontal_lines
    info["vertical_lines"] = vertical_lines
    info["unconnected_markers"] = unconnected
    info["dual_axis_colors"] = sorted(dual_axis_colors)
    if horizontal_lines + vertical_lines == 0:
        errors.append("no same-color markers share a coarse row or column; rule would be identity")

    colors = sorted(spans)
    for i, left in enumerate(colors):
        for right in colors[i + 1 :]:
            overlap = spans[left] & spans[right]
            if overlap:
                errors.append(
                    f"connection spans for colors {left} and {right} overlap at {sorted(overlap)[0]}"
                )
                break

    return info


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's structural input grammar while accepting every canonical input."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Task-linked teaching predicate matching every canonical train/test input."""
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    if info["horizontal_lines"] < 1:
        errors.append("canonical lessons contain at least one horizontal same-color connection")
    if info["vertical_lines"] < 1:
        errors.append("canonical lessons contain at least one vertical same-color connection")
    if not any(len(cells) == 3 for cells in info["markers"].values()):
        errors.append("canonical lessons contain a three-marker color")
    if not info["unconnected_markers"]:
        errors.append("canonical lessons contain at least one marker not connected to a same-color peer")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from a generated grid."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"K": int(info["K"]), "n_colors": len(info["markers"])}


def _solve_python(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent mirror used only for semantic checks; Racket remains output authority."""
    info = _analyze([list(row) for row in grid])
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [list(row) for row in grid]
    for color, span in info["spans"].items():
        for cell_r, cell_c in span:
            _place_2x2(out, cell_r, cell_c, color)
    return out


def _solve_with_axes(grid, *, horizontal: bool, vertical: bool) -> list[list[int]]:
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [list(row) for row in grid]
    for color, cells in info["markers"].items():
        rows: dict[int, list[int]] = defaultdict(list)
        cols: dict[int, list[int]] = defaultdict(list)
        for row, col in cells:
            rows[row].append(col)
            cols[col].append(row)
        if horizontal:
            for row, values in rows.items():
                values = sorted(set(values))
                if len(values) >= 2:
                    for col in range(values[0], values[-1] + 1):
                        _place_2x2(out, row, col, color)
        if vertical:
            for col, values in cols.items():
                values = sorted(set(values))
                if len(values) >= 2:
                    for row in range(values[0], values[-1] + 1):
                        _place_2x2(out, row, col, color)
    return out


def _rival_row_only(grid):
    return _solve_with_axes(grid, horizontal=True, vertical=False)


def _rival_column_only(grid):
    return _solve_with_axes(grid, horizontal=False, vertical=True)


def _rival_bbox_fill(grid):
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [list(row) for row in grid]
    for color, cells in info["markers"].items():
        if len(cells) < 2:
            continue
        r0 = min(row for row, _ in cells)
        r1 = max(row for row, _ in cells)
        c0 = min(col for _, col in cells)
        c1 = max(col for _, col in cells)
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                _place_2x2(out, row, col, color)
    return out


def _rival_drop_unconnected(grid):
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = _solve_python(grid)
    for _, (row, col) in info["unconnected_markers"]:
        _place_2x2(out, row, col, 0)
    return out


def _rival_fixed_divider_one(grid):
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    if info["divider"] != 1:
        return [list(row) for row in grid]
    return _solve_python(grid)


def _rival_nearest_pair_only(grid):
    """Connect only the nearest adjacent marker pair on each occupied axis."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    out = [list(row) for row in grid]
    for color, cells in info["markers"].items():
        rows: dict[int, list[int]] = defaultdict(list)
        cols: dict[int, list[int]] = defaultdict(list)
        for row, col in cells:
            rows[row].append(col)
            cols[col].append(row)
        for row, values in rows.items():
            uniq = sorted(set(values))
            if len(uniq) >= 2:
                left, right = min(
                    zip(uniq, uniq[1:]),
                    key=lambda pair: (pair[1] - pair[0], pair),
                )
                for col in range(left, right + 1):
                    _place_2x2(out, row, col, color)
        for col, values in cols.items():
            uniq = sorted(set(values))
            if len(uniq) >= 2:
                top, bottom = min(
                    zip(uniq, uniq[1:]),
                    key=lambda pair: (pair[1] - pair[0], pair),
                )
                for row in range(top, bottom + 1):
                    _place_2x2(out, row, col, color)
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "row_only": _rival_row_only,
    "column_only": _rival_column_only,
    "bounding_box_fill": _rival_bbox_fill,
    "drop_unconnected_markers": _rival_drop_unconnected,
    "fixed_divider_one": _rival_fixed_divider_one,
    "nearest_pair_only": _rival_nearest_pair_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _w_horizontal(grid) -> bool:
    return _analyze(grid)["horizontal_lines"] > 0


def _w_vertical(grid) -> bool:
    return _analyze(grid)["vertical_lines"] > 0


def _w_dual_axis(grid) -> bool:
    return bool(_analyze(grid)["dual_axis_colors"])


def _w_unconnected(grid) -> bool:
    return bool(_analyze(grid)["unconnected_markers"])


def _w_non_one_divider(grid) -> bool:
    info = _analyze(grid)
    return not info["errors"] and info["divider"] != 1


def _w_three_collinear(grid) -> bool:
    info = _analyze(grid)
    if info["errors"]:
        return False
    for cells in info["markers"].values():
        rows: dict[int, int] = defaultdict(int)
        cols: dict[int, int] = defaultdict(int)
        for row, col in cells:
            rows[row] += 1
            cols[col] += 1
        if max([0, *rows.values(), *cols.values()]) >= 3:
            return True
    return False


SEMANTIC_WITNESSES = {
    "horizontal_connection": _w_horizontal,
    "vertical_connection": _w_vertical,
    "same_color_dual_axis": _w_dual_axis,
    "unconnected_marker_preserved": _w_unconnected,
    "divider_role_not_fixed_to_one": _w_non_one_divider,
    "three_collinear_markers": _w_three_collinear,
}
WITNESS_RIVALS = {
    "horizontal_connection": ["column_only"],
    "vertical_connection": ["row_only"],
    "same_color_dual_axis": ["bounding_box_fill"],
    "unconnected_marker_preserved": ["drop_unconnected_markers"],
    "divider_role_not_fixed_to_one": ["fixed_divider_one"],
    "three_collinear_markers": ["nearest_pair_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named plausible rival fits all demos but changes the query."""
    errors: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} is not an input/output pair")
            continue
        scene_errors = strict_canonical_like(pair["input"])
        if scene_errors:
            errors.append(f"demo {index} is not canonical-like: {'; '.join(scene_errors)}")
            continue
        expected = _solve_python(pair["input"])
        if pair["output"] != expected:
            errors.append(f"demo {index} output disagrees with the lattice-connect rule")
            continue
        valid.append(pair)

    if len(valid) == len(demos):
        if not any(_w_non_one_divider(pair["input"]) for pair in valid):
            errors.append("demonstrations never rebut a fixed divider-color-1 shortcut")
        for name, rival in LESSON_COMPETITORS.items():
            survives = all(rival(pair["input"]) == pair["output"] for pair in valid)
            if survives and rival(query["input"]) != _solve_python(query["input"]):
                errors.append(f"competitor {name!r} survives every demo but changes the query")

    if not isinstance(query, dict) or "input" not in query:
        errors.append("query is missing an input grid")
        return errors
    query_errors = strict_canonical_like(query["input"])
    if query_errors:
        errors.append("query is not canonical-like: " + "; ".join(query_errors))
    elif query.get("output") is not None and query["output"] != _solve_python(query["input"]):
        errors.append("query output disagrees with the lattice-connect rule")
    return errors


LESSON_SCHEDULE_PERIOD = 12
SCHEDULE_PROFILES = tuple(range(LESSON_SCHEDULE_PERIOD))


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return sample_index % LESSON_SCHEDULE_PERIOD


def _all_l_candidates(K: int, max_gap: int) -> list[tuple[list[tuple[int, int]], set[tuple[int, int]]]]:
    candidates = []
    for corner_r in range(K):
        for corner_c in range(K):
            for end_c in range(K):
                if end_c == corner_c or not 2 <= abs(end_c - corner_c) <= max_gap:
                    continue
                for end_r in range(K):
                    if end_r == corner_r or not 2 <= abs(end_r - corner_r) <= max_gap:
                        continue
                    cells = [(corner_r, corner_c), (corner_r, end_c), (end_r, corner_c)]
                    span, _, _ = _connection_spans(cells)
                    candidates.append((cells, span))
    return candidates


def _all_line_candidates(K: int, horizontal: bool, max_gap: int):
    candidates = []
    if horizontal:
        for row in range(K):
            for c0 in range(K):
                for c1 in range(c0 + 2, min(K, c0 + max_gap + 1)):
                    cells = [(row, c0), (row, c1)]
                    span, _, _ = _connection_spans(cells)
                    candidates.append((cells, span))
    else:
        for col in range(K):
            for r0 in range(K):
                for r1 in range(r0 + 2, min(K, r0 + max_gap + 1)):
                    cells = [(r0, col), (r1, col)]
                    span, _, _ = _connection_spans(cells)
                    candidates.append((cells, span))
    return candidates


def _all_line_triple_candidates(K: int, horizontal: bool, max_gap: int):
    """Return collinear triples with a visible gap beyond the nearest pair."""
    candidates = []
    if horizontal:
        for row in range(K):
            for c0 in range(K):
                for c2 in range(c0 + 3, min(K, c0 + max_gap + 1)):
                    for c1 in range(c0 + 1, c2):
                        cells = [(row, c0), (row, c1), (row, c2)]
                        span, _, _ = _connection_spans(cells)
                        candidates.append((cells, span))
    else:
        for col in range(K):
            for r0 in range(K):
                for r2 in range(r0 + 3, min(K, r0 + max_gap + 1)):
                    for r1 in range(r0 + 1, r2):
                        cells = [(r0, col), (r1, col), (r2, col)]
                        span, _, _ = _connection_spans(cells)
                        candidates.append((cells, span))
    return candidates


def _choose_disjoint(rng, candidates, reserved: set[tuple[int, int]]):
    order = list(range(len(candidates)))
    rng.shuffle(order)
    for index in order:
        cells, span = candidates[index]
        if span.isdisjoint(reserved):
            return list(cells), set(span)
    raise ValueError("could not place a disjoint marker connection pattern")


def _choose_free_marker(rng, K: int, reserved: set[tuple[int, int]], forbidden_rows=(), forbidden_cols=()):
    candidates = [
        (row, col)
        for row in range(K)
        for col in range(K)
        if (row, col) not in reserved and row not in forbidden_rows and col not in forbidden_cols
    ]
    if not candidates:
        raise ValueError("could not place required unconnected marker")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    K = ctx.draw_int_strict("K", 7, 9)
    if "n_colors" in overrides:
        n_colors = ctx.draw_int_strict("n_colors", 2, 4)
    else:
        band_offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
        scheduled_n = 2 + ((sample_index + band_offset) % 3)
        n_colors = ctx.draw_choice("n_colors", [scheduled_n])
    divider = ctx.draw_choice("divider_color", [_DIVIDER_SCHEDULE[sample_index % 4]])
    rng = ctx.draw_rng("layout")

    palette = [color for color in range(1, 10) if color != divider]
    colors = rng.sample(palette, n_colors)
    max_gap = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 4)
    max_gap = min(max_gap, K - 1)

    size = 3 * K - 1
    grid = full_grid(size, size, 0)
    for r in range(size):
        if r % 3 == 2:
            for c in range(size):
                grid[r][c] = divider
    for c in range(size):
        if c % 3 == 2:
            for r in range(size):
                grid[r][c] = divider

    reserved: set[tuple[int, int]] = set()
    markers_by_color: dict[int, list[tuple[int, int]]] = {}

    # Primary color always has an L: this single color positively witnesses both
    # row and column branches, as every canonical episode does somewhere.
    primary_cells, primary_span = _choose_disjoint(
        rng, _all_l_candidates(K, max_gap), reserved
    )
    markers_by_color[colors[0]] = primary_cells
    reserved.update(primary_span)

    active_colors = colors[1:]
    singleton_color = None
    if n_colors >= 3:
        singleton_color = active_colors[-1]
        active_colors = active_colors[:-1]

    # Additional active colors alternate line direction by lesson slot. The
    # first uses three collinear markers so a nearest-pair-only shortcut leaves
    # part of the authoritative min-to-max interval blank. With four colors, a
    # second two-endpoint line supplies the opposite secondary direction.
    for offset, color in enumerate(active_colors):
        horizontal = ((sample_index + offset) % 2 == 0)
        candidates = (
            _all_line_triple_candidates(K, horizontal, max_gap)
            if offset == 0
            else _all_line_candidates(K, horizontal, max_gap)
        )
        cells, span = _choose_disjoint(rng, candidates, reserved)
        markers_by_color[color] = cells
        reserved.update(span)

    if n_colors == 2:
        # Canonical two-color scenes use a same-color off-line third marker as
        # the distractor. It must share neither row nor column with the line.
        color = colors[1]
        cells = markers_by_color[color]
        forbidden_rows = {row for row, _ in cells}
        forbidden_cols = {col for _, col in cells}
        extra = _choose_free_marker(rng, K, reserved, forbidden_rows, forbidden_cols)
        markers_by_color[color] = cells + [extra]
        reserved.add(extra)
    elif singleton_color is not None:
        singleton = _choose_free_marker(rng, K, reserved)
        markers_by_color[singleton_color] = [singleton]
        reserved.add(singleton)

    for color, cells in markers_by_color.items():
        for row, col in cells:
            _place_2x2(grid, row, col, color)

    # Fail closed if a future edit makes the teaching schedule malformed.
    errors = strict_canonical_like(grid)
    if errors:
        raise ValueError("generated scene violates task-linked contract: " + "; ".join(errors))
    observed = observe_overrides(grid)
    if observed != {"K": K, "n_colors": n_colors}:
        raise ValueError(f"axis observation mismatch: requested K={K}, n_colors={n_colors}, got {observed}")
    return grid
