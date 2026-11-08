"""Generator for ARC task b3750af4dac1 — room-signature matching.

Colors 1, 7, and 9 are walls.  The non-wall connected regions are rooms;
a color-7 wall cell is a doorway and creates a graph edge between the two
rooms on its opposite sides.  A room signature is

    (cell count, graph degree, count of color 2, count of color 3).

Rooms are ordered row-major by their top-left cell.  The first room is the
query and the output is a one-row strip containing color 8 exactly at the
candidate whose complete signature equals the query's.

The generator builds a one-cell wall lattice with variable row/column spans.
The declared ``room_h`` and ``room_w`` axes are the query chamber's observable
height and width.  Every ordinary lesson has exactly one answer and a
controlled distractor that differs in one signature field, so area, degree,
red-count, and green-count cannot be replaced by a fixed-position shortcut.
"""
from __future__ import annotations

from itertools import product
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "b3750af4dac1"
TASK_ID = "b3750af4dac1"
VERSION = "3.0.0"
RULE_HASH = "674e022a164b"

SUMMARY = (
    "A 1/7/9 wall lattice contains row-major rooms. Color 7 is a doorway; "
    "match the first room's exact (area, door-degree, #2, #3) signature and "
    "mark the unique matching candidate in a one-row color-8 strip."
)

INVARIANTS = [
    "colors 1, 7, and 9 are walls; every color-7 cell is one doorway between exactly two adjacent rooms",
    "the outer boundary and one-cell separators form one through five chamber rows and two through six chamber columns",
    "room_h and room_w are the exact height and width of the first (query) chamber; other chamber spans may vary",
    "the first row-major room is the query and exactly one later room has the same (area, degree, #2, #3) signature",
    "every generated lesson includes a non-answer distractor sharing at least two signature fields with the query",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "macro_r": {
        "type": "int",
        "default": "difficulty-aware chamber-row count",
        "valid": "1..5",
    },
    "macro_c": {
        "type": "int",
        "default": "difficulty-aware chamber-column count",
        "valid": "2..6",
    },
    "room_h": {
        "type": "int",
        "default": "difficulty-aware query-room height",
        "valid": "2..9",
    },
    "room_w": {
        "type": "int",
        "default": "difficulty-aware query-room width",
        "valid": "2..9",
    },
}

_WALLS = frozenset((1, 7, 9))
_ROOM_VALUES = frozenset((0, 2, 3))
_ALLOWED_VALUES = _WALLS | _ROOM_VALUES
_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_FOCUSES = ("area", "degree", "red_count", "green_count")

_BAND_AXIS_RANGES = {
    None: {
        "macro_r": (1, 5),
        "macro_c": (2, 6),
        "room_h": (2, 9),
        "room_w": (2, 9),
    },
    "easy": {
        "macro_r": (1, 2),
        "macro_c": (3, 4),
        "room_h": (2, 4),
        "room_w": (2, 4),
    },
    "medium": {
        "macro_r": (2, 4),
        "macro_c": (3, 5),
        "room_h": (3, 7),
        "room_w": (3, 7),
    },
    "hard": {
        "macro_r": (2, 5),
        "macro_c": (4, 6),
        "room_h": (5, 9),
        "room_w": (5, 9),
    },
}

_OTHER_SPAN_HIGH = {None: 9, "easy": 4, "medium": 7, "hard": 9}
_EXTRA_DOOR_RATE = {None: 0.42, "easy": 0.20, "medium": 0.42, "hard": 0.62}
_WALL9_RATE = {None: 0.55, "easy": 0.35, "medium": 0.55, "hard": 0.75}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    bounds = {
        "macro_r": (1, 5),
        "macro_c": (2, 6),
        "room_h": (2, 9),
        "room_w": (2, 9),
    }
    for label, (lo, hi) in bounds.items():
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"{label} must be between {lo} and {hi}")

    macro_r = overrides.get("macro_r")
    macro_c = overrides.get("macro_c")
    if macro_r == 1 and macro_c == 2:
        raise ValueError(
            "macro_r=1 and macro_c=2 leave only one candidate; at least "
            "three rooms are required for a match and a distractor"
        )
    room_w = overrides.get("room_w")
    if macro_r == 1 and macro_c == 6 and room_w in (8, 9):
        raise ValueError(
            "a 1x6 lattice with query width 8 or 9 cannot fit a second "
            "equal-area room inside ARC's 30-column limit"
        )
    if macro_r == 1 and macro_c == 3 and room_w == 9:
        raise ValueError(
            "a 1x3 lattice with query width 9 cannot fit both an exact "
            "match and a one-feature distractor inside 30 columns"
        )


def _draw_axis(ctx, label, full_bounds, default_bounds):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        lo, hi = full_bounds
    else:
        lo, hi = default_bounds
    return ctx.draw_int(label, lo, hi)


def _draw_axes(ctx):
    ranges = _BAND_AXIS_RANGES[ctx.difficulty]
    macro_c_override = ctx.overrides.get("macro_c")
    room_w_override = ctx.overrides.get("room_w")

    mr_lo, mr_hi = ranges["macro_r"]
    if macro_c_override == 2:
        mr_lo = max(mr_lo, 2)
    if macro_c_override == 6 and room_w_override in (8, 9):
        mr_lo = max(mr_lo, 2)
    if macro_c_override == 3 and room_w_override == 9:
        mr_lo = max(mr_lo, 2)
    macro_r = _draw_axis(ctx, "macro_r", (1, 5), (mr_lo, mr_hi))

    mc_lo, mc_hi = ranges["macro_c"]
    if macro_r == 1:
        mc_lo = max(mc_lo, 3)
        if room_w_override in (8, 9):
            mc_hi = min(mc_hi, 5)
        if room_w_override == 9:
            mc_lo = max(mc_lo, 4)
    if mc_hi < mc_lo:
        raise ValueError(
            "the requested macro_r/room_w combination leaves no feasible "
            "default macro_c inside the 30-column limit"
        )
    macro_c = _draw_axis(ctx, "macro_c", (2, 6), (mc_lo, mc_hi))
    if macro_r * macro_c < 3:
        raise ValueError("the lattice must contain at least three rooms")

    room_h = _draw_axis(
        ctx, "room_h", (2, 9), ranges["room_h"]
    )
    rw_lo, rw_hi = ranges["room_w"]
    if macro_r == 1 and macro_c == 3:
        rw_hi = min(rw_hi, 8)
    if macro_r == 1 and macro_c == 6:
        rw_hi = min(rw_hi, 7)
    if rw_hi < rw_lo:
        raise ValueError(
            "the requested one-row lattice has no feasible query-room width"
        )
    room_w = _draw_axis(ctx, "room_w", (2, 9), (rw_lo, rw_hi))
    if macro_r == 1 and macro_c == 6 and room_w in (8, 9):
        raise ValueError(
            "a 1x6 lattice with query width 8 or 9 cannot fit a second "
            "equal-area room inside ARC's 30-column limit"
        )
    return macro_r, macro_c, room_h, room_w


def _room_id(row, col, macro_c):
    return row * macro_c + col


def _room_coord(room_id, macro_c):
    return divmod(room_id, macro_c)


def _candidate_coords(macro_r, macro_c):
    return [
        (row, col)
        for row in range(macro_r)
        for col in range(macro_c)
        if (row, col) != (0, 0)
    ]


def _factor_pairs(area):
    return tuple(
        (height, width)
        for height in range(2, 10)
        for width in range(2, 10)
        if height * width == area
    )


def _specs_for_room(coord, query_h, query_w, *, equal_area):
    row, col = coord
    query_area = query_h * query_w
    pairs: Iterable[tuple[int, int]]
    if equal_area:
        pairs = _factor_pairs(query_area)
    else:
        # A compact but complete 2..9 domain is cheap (64 choices) and makes
        # area-focused distractors feasible even at override boundaries.
        pairs = product(range(2, 10), repeat=2)
    specs = []
    for height, width in pairs:
        if row == 0 and height != query_h:
            continue
        if col == 0 and width != query_w:
            continue
        if equal_area != (height * width == query_area):
            continue
        specs.append((coord, height, width))
    return specs


def _merge_fixed(query_h, query_w, room_specs):
    row_fixed = {0: query_h}
    col_fixed = {0: query_w}
    for (row, col), height, width in room_specs:
        if row in row_fixed and row_fixed[row] != height:
            return None
        if col in col_fixed and col_fixed[col] != width:
            return None
        row_fixed[row] = height
        col_fixed[col] = width
    return row_fixed, col_fixed


def _minimum_dimension(count, fixed):
    return sum(fixed.get(index, 2) for index in range(count)) + count + 1


def _fill_spans(count, fixed, *, difficulty, rng):
    max_sum = 29 - count
    spans = [fixed.get(index, 2) for index in range(count)]
    if sum(spans) > max_sum:
        return None
    free = [index for index in range(count) if index not in fixed]
    rng.shuffle(free)
    high_hint = _OTHER_SPAN_HIGH[difficulty]
    for index in free:
        # Every not-yet-filled span is already represented by its legal
        # minimum value 2, so the remaining capacity is exact.
        current_without = sum(spans) - spans[index]
        high = min(9, high_hint, max_sum - current_without)
        if high < 2:
            return None
        if difficulty == "hard" and high >= 4:
            low = max(2, (high + 1) // 2)
        elif difficulty == "medium" and high >= 3:
            low = 3
        else:
            low = 2
        spans[index] = rng.randint(low, high)
    return spans


def _potential_edges(macro_r, macro_c):
    edges = []
    for row in range(macro_r):
        for col in range(macro_c):
            here = _room_id(row, col, macro_c)
            if col + 1 < macro_c:
                edges.append((here, _room_id(row, col + 1, macro_c)))
            if row + 1 < macro_r:
                edges.append((here, _room_id(row + 1, col, macro_c)))
    return tuple(edges)


def _room_capacity(room, macro_r, macro_c):
    row, col = _room_coord(room, macro_c)
    return (
        int(row > 0)
        + int(row + 1 < macro_r)
        + int(col > 0)
        + int(col + 1 < macro_c)
    )


def _degree_constrained_edges(
    macro_r, macro_c, desired, difficulty, rng
):
    edges = _potential_edges(macro_r, macro_c)
    protected = set(desired)
    relevant = [
        edge for edge in edges if edge[0] in protected or edge[1] in protected
    ]
    solutions = []
    for mask in range(1 << len(relevant)):
        degrees = {room: 0 for room in protected}
        selected = set()
        for index, edge in enumerate(relevant):
            if mask & (1 << index):
                selected.add(edge)
                if edge[0] in degrees:
                    degrees[edge[0]] += 1
                if edge[1] in degrees:
                    degrees[edge[1]] += 1
        if degrees == desired:
            solutions.append(selected)
    if not solutions:
        return None
    selected = set(rng.choice(solutions))
    extra_rate = _EXTRA_DOOR_RATE[difficulty]
    for edge in edges:
        if edge in relevant:
            continue
        if rng.random() < extra_rate:
            selected.add(edge)
    return tuple(sorted(selected))


def _alternate_degree(query_degree, capacity):
    preferred = (
        (2, 0, 3, 4) if query_degree == 1 else (1, 3, 0, 4)
    )
    return next(
        (value for value in preferred if value <= capacity),
        None,
    )


def _focus_order(requested):
    return (requested,) + tuple(
        focus for focus in _FOCUSES if focus != requested
    )


def _build_plan(macro_r, macro_c, query_h, query_w, difficulty, rng):
    coords = _candidate_coords(macro_r, macro_c)
    target_specs = []
    for coord in coords:
        target_specs.extend(
            _specs_for_room(
                coord, query_h, query_w, equal_area=True
            )
        )
    rng.shuffle(target_specs)
    requested_focus = rng.choice(_FOCUSES)

    # Each focus gets a bounded random search before falling through to the
    # next semantically valid focus.  The domain is tiny, and the deterministic
    # fallback keeps exact overrides fail-loud rather than silently clamping.
    for focus in _focus_order(requested_focus):
        equal_aux = focus != "area"
        for target_spec in target_specs:
            target_coord = target_spec[0]
            aux_coords = [coord for coord in coords if coord != target_coord]
            rng.shuffle(aux_coords)
            for aux_coord in aux_coords:
                aux_specs = _specs_for_room(
                    aux_coord,
                    query_h,
                    query_w,
                    equal_area=equal_aux,
                )
                rng.shuffle(aux_specs)
                for aux_spec in aux_specs:
                    merged = _merge_fixed(
                        query_h, query_w, (target_spec, aux_spec)
                    )
                    if merged is None:
                        continue
                    row_fixed, col_fixed = merged
                    if _minimum_dimension(macro_r, row_fixed) > 30:
                        continue
                    if _minimum_dimension(macro_c, col_fixed) > 30:
                        continue

                    row_spans = _fill_spans(
                        macro_r,
                        row_fixed,
                        difficulty=difficulty,
                        rng=rng,
                    )
                    col_spans = _fill_spans(
                        macro_c,
                        col_fixed,
                        difficulty=difficulty,
                        rng=rng,
                    )
                    if row_spans is None or col_spans is None:
                        continue

                    query = 0
                    target = _room_id(*target_coord, macro_c)
                    aux = _room_id(*aux_coord, macro_c)
                    common_max = min(
                        _room_capacity(query, macro_r, macro_c),
                        _room_capacity(target, macro_r, macro_c),
                    )
                    degree_options = list(range(1, min(2, common_max) + 1))
                    if difficulty == "hard":
                        degree_options.reverse()
                    elif len(degree_options) > 1 and rng.random() < 0.5:
                        degree_options.reverse()

                    for query_degree in degree_options:
                        desired = {
                            query: query_degree,
                            target: query_degree,
                        }
                        if focus == "degree":
                            aux_degree = _alternate_degree(
                                query_degree,
                                _room_capacity(aux, macro_r, macro_c),
                            )
                            if aux_degree is None:
                                continue
                            desired[aux] = aux_degree
                        else:
                            desired[aux] = query_degree

                        selected_edges = _degree_constrained_edges(
                            macro_r, macro_c, desired, difficulty, rng
                        )
                        if selected_edges is None:
                            continue
                        return {
                            "requested_focus": requested_focus,
                            "focus": focus,
                            "row_spans": row_spans,
                            "col_spans": col_spans,
                            "target": target,
                            "aux": aux,
                            "query_degree": query_degree,
                            "edges": selected_edges,
                        }
    raise ValueError(
        "the requested geometry cannot fit one exact match plus a controlled "
        "distractor inside the 30x30 ARC limit"
    )


def _boundaries(spans):
    walls = [0]
    cursor = 0
    for span in spans:
        cursor += span + 1
        walls.append(cursor)
    return tuple(walls)


def _room_cells(row_walls, col_walls, row, col):
    return [
        (r, c)
        for r in range(row_walls[row] + 1, row_walls[row + 1])
        for c in range(col_walls[col] + 1, col_walls[col + 1])
    ]


def _edge_door_cell(edge, macro_c, row_walls, col_walls):
    left, right = edge
    left_row, left_col = _room_coord(left, macro_c)
    right_row, right_col = _room_coord(right, macro_c)
    if left_row == right_row:
        row = left_row
        separator_col = col_walls[max(left_col, right_col)]
        top, bottom = row_walls[row], row_walls[row + 1]
        return ((top + bottom) // 2, separator_col)
    col = left_col
    separator_row = row_walls[max(left_row, right_row)]
    left_wall, right_wall = col_walls[col], col_walls[col + 1]
    return (separator_row, (left_wall + right_wall) // 2)


def _alternate_count(value, other, area):
    if value + 1 + other <= area - 1:
        return value + 1
    if value > 0:
        return value - 1
    raise ValueError("no alternate marker count fits the room")


def _marker_counts(plan, areas, degrees, difficulty, rng):
    query_area = areas[0]
    count_capacity = (
        min(query_area, areas[plan["aux"]])
        if plan["focus"] == "area"
        else query_area
    )
    q2_hi = min(3, count_capacity - 2)
    q2 = rng.randint(1, q2_hi)
    q3 = rng.randint(1, min(3, count_capacity - q2 - 1))
    counts = {}
    counts[0] = (q2, q3)
    counts[plan["target"]] = (q2, q3)

    aux = plan["aux"]
    if plan["focus"] in ("area", "degree"):
        counts[aux] = (q2, q3)
    elif plan["focus"] == "red_count":
        counts[aux] = (
            _alternate_count(q2, q3, areas[aux]),
            q3,
        )
    else:
        counts[aux] = (
            q2,
            _alternate_count(q3, q2, areas[aux]),
        )

    marker_high = {None: 3, "easy": 2, "medium": 3, "hard": 3}[difficulty]
    for room, area in enumerate(areas):
        if room in counts:
            continue
        max_total = min(2 * marker_high, area - 1)
        n2 = rng.randint(0, min(marker_high, max_total))
        n3 = rng.randint(0, min(marker_high, max_total - n2))
        if (
            area == query_area
            and degrees[room] == plan["query_degree"]
            and (n2, n3) == (q2, q3)
        ):
            n2 = _alternate_count(n2, n3, area)
        counts[room] = (n2, n3)
    return counts


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a non-empty list or tuple of rows"]
    rows = []
    for row in grid:
        if isinstance(row, str):
            if not row:
                return None, ["grid rows must be non-empty"]
            try:
                rows.append([int(value) for value in row])
            except ValueError:
                return None, ["string rows must contain decimal digits"]
        elif isinstance(row, (list, tuple)) and row:
            rows.append(list(row))
        else:
            return None, ["grid rows must be non-empty lists, tuples, or strings"]
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        return rows, ["grid must be rectangular"]
    return rows, []


def _rule_facts(grid):
    coerced, errors = _coerce_grid(grid)
    if errors:
        return {"grid": coerced, "errors": errors}
    height, width = len(coerced), len(coerced[0])
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in coerced
        for value in row
    ):
        return {
            "grid": coerced,
            "errors": ["cells must be integer ARC colors 0 through 9"],
        }

    seen = set()
    rooms = []
    cell_to_room = {}
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in seen or coerced[start_row][start_col] in _WALLS:
                continue
            pending = [start]
            seen.add(start)
            cells = []
            while pending:
                row, col = pending.pop()
                cells.append((row, col))
                for dr, dc in _DELTAS:
                    neighbor = row + dr, col + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and coerced[neighbor[0]][neighbor[1]] not in _WALLS
                    ):
                        seen.add(neighbor)
                        pending.append(neighbor)
            room_id = len(rooms)
            cells = tuple(sorted(cells))
            for cell in cells:
                cell_to_room[cell] = room_id
            rooms.append(
                {
                    "id": room_id,
                    "cells": cells,
                    "top": min(row for row, _col in cells),
                    "left": min(col for _row, col in cells),
                }
            )

    adjacency = [set() for _room in rooms]
    for row in range(height):
        for col in range(width):
            if coerced[row][col] != 7:
                continue
            neighboring = {
                cell_to_room.get((row + dr, col + dc))
                for dr, dc in _DELTAS
            }
            neighboring.discard(None)
            for first in neighboring:
                for second in neighboring:
                    if first < second:
                        adjacency[first].add(second)
                        adjacency[second].add(first)

    order = sorted(
        range(len(rooms)),
        key=lambda room: (rooms[room]["top"], rooms[room]["left"]),
    )
    signatures = []
    for room in order:
        cells = rooms[room]["cells"]
        signatures.append(
            (
                len(cells),
                len(adjacency[room]),
                sum(coerced[row][col] == 2 for row, col in cells),
                sum(coerced[row][col] == 3 for row, col in cells),
            )
        )
    matches = []
    output = None
    if signatures:
        matches = [
            index
            for index, signature in enumerate(signatures[1:])
            if signature == signatures[0]
        ]
        output = [[
            8 if index in matches else 0
            for index in range(len(signatures) - 1)
        ]]
    return {
        "grid": coerced,
        "errors": [],
        "rooms": rooms,
        "adjacency": adjacency,
        "order": order,
        "signatures": tuple(signatures),
        "matches": tuple(matches),
        "output": output,
    }


def rule_mirror(grid):
    """Independent Python mirror used only for tests; Racket stays authoritative."""
    facts = _rule_facts(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if not facts["signatures"]:
        raise ValueError("the rule requires at least one non-wall room")
    return [row[:] for row in facts["output"]]


def _near_miss_roles(signatures):
    if not signatures:
        return {}
    query = signatures[0]
    roles = {
        "area": [],
        "degree": [],
        "red_count": [],
        "green_count": [],
    }
    for index, signature in enumerate(signatures[1:]):
        if signature == query:
            continue
        if signature[1:] == query[1:] and signature[0] != query[0]:
            roles["area"].append(index)
        if (
            signature[0] == query[0]
            and signature[2:] == query[2:]
            and signature[1] != query[1]
        ):
            roles["degree"].append(index)
        if (
            signature[0] == query[0]
            and signature[1] == query[1]
            and signature[3] == query[3]
            and signature[2] != query[2]
        ):
            roles["red_count"].append(index)
        if (
            signature[0] == query[0]
            and signature[1] == query[1]
            and signature[2] == query[2]
            and signature[3] != query[3]
        ):
            roles["green_count"].append(index)
    return {name: tuple(indices) for name, indices in roles.items()}


def _scene_analysis(grid, *, enforce_lesson=True):
    coerced, errors = _coerce_grid(grid)
    if errors:
        return {"grid": coerced, "errors": errors, "geometry": None}
    height, width = len(coerced), len(coerced[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        errors.append("grid dimensions must be between 1 and 30")
    bad_values = sorted({
        value
        for row in coerced
        for value in row
        if type(value) is not int or value not in _ALLOWED_VALUES
    }, key=repr)
    if bad_values:
        errors.append(
            "generated lessons may use only colors 0,1,2,3,7,9; got "
            + ", ".join(map(str, bad_values))
        )
    if errors:
        return {"grid": coerced, "errors": errors, "geometry": None}

    wall_rows = tuple(
        row
        for row, values in enumerate(coerced)
        if all(value in _WALLS for value in values)
    )
    wall_cols = tuple(
        col
        for col in range(width)
        if all(coerced[row][col] in _WALLS for row in range(height))
    )
    if (
        not 2 <= len(wall_rows) <= 6
        or wall_rows[0] != 0
        or wall_rows[-1] != height - 1
    ):
        errors.append(
            "full wall rows must bound one through five chamber rows"
        )
    if (
        not 3 <= len(wall_cols) <= 7
        or wall_cols[0] != 0
        or wall_cols[-1] != width - 1
    ):
        errors.append(
            "full wall columns must bound two through six chamber columns"
        )
    if errors:
        return {"grid": coerced, "errors": errors, "geometry": None}

    row_spans = tuple(
        bottom - top - 1
        for top, bottom in zip(wall_rows, wall_rows[1:])
    )
    col_spans = tuple(
        right - left - 1
        for left, right in zip(wall_cols, wall_cols[1:])
    )
    if any(not 2 <= span <= 9 for span in row_spans):
        errors.append("every chamber-row height must be between 2 and 9")
    if any(not 2 <= span <= 9 for span in col_spans):
        errors.append("every chamber-column width must be between 2 and 9")

    wall_row_set, wall_col_set = set(wall_rows), set(wall_cols)
    for row in range(height):
        for col in range(width):
            on_lattice = row in wall_row_set or col in wall_col_set
            is_wall = coerced[row][col] in _WALLS
            if on_lattice and not is_wall:
                errors.append(
                    f"separator lattice is broken at ({row},{col})"
                )
            if not on_lattice and is_wall:
                errors.append(
                    f"wall color inside a room at ({row},{col})"
                )
    if errors:
        return {"grid": coerced, "errors": errors, "geometry": None}

    macro_r, macro_c = len(row_spans), len(col_spans)
    if macro_r * macro_c < 3:
        errors.append("the lesson must contain at least three rooms")

    door_pairs = {}
    internal_rows = {value: index for index, value in enumerate(wall_rows[1:-1], 1)}
    internal_cols = {value: index for index, value in enumerate(wall_cols[1:-1], 1)}
    for row in range(height):
        for col in range(width):
            if coerced[row][col] != 7:
                continue
            on_row = row in internal_rows
            on_col = col in internal_cols
            if row in (0, height - 1) or col in (0, width - 1):
                errors.append(f"doorway on the outer boundary at ({row},{col})")
                continue
            if on_row == on_col:
                errors.append(
                    f"doorway at ({row},{col}) must lie on exactly one internal separator"
                )
                continue
            if on_col:
                if (
                    coerced[row][col - 1] in _WALLS
                    or coerced[row][col + 1] in _WALLS
                    or coerced[row - 1][col] not in _WALLS
                    or coerced[row + 1][col] not in _WALLS
                ):
                    errors.append(
                        f"vertical doorway at ({row},{col}) does not connect exactly two opposite rooms"
                    )
                    continue
                row_band = next(
                    index
                    for index, (top, bottom) in enumerate(
                        zip(wall_rows, wall_rows[1:])
                    )
                    if top < row < bottom
                )
                sep = internal_cols[col]
                pair = (
                    _room_id(row_band, sep - 1, macro_c),
                    _room_id(row_band, sep, macro_c),
                )
            else:
                if (
                    coerced[row - 1][col] in _WALLS
                    or coerced[row + 1][col] in _WALLS
                    or coerced[row][col - 1] not in _WALLS
                    or coerced[row][col + 1] not in _WALLS
                ):
                    errors.append(
                        f"horizontal doorway at ({row},{col}) does not connect exactly two opposite rooms"
                    )
                    continue
                col_band = next(
                    index
                    for index, (left, right) in enumerate(
                        zip(wall_cols, wall_cols[1:])
                    )
                    if left < col < right
                )
                sep = internal_rows[row]
                pair = (
                    _room_id(sep - 1, col_band, macro_c),
                    _room_id(sep, col_band, macro_c),
                )
            pair = tuple(sorted(pair))
            if pair in door_pairs:
                errors.append(
                    f"multiple doorway cells connect room pair {pair}"
                )
            door_pairs[pair] = (row, col)

    if errors:
        return {"grid": coerced, "errors": errors, "geometry": None}

    facts = _rule_facts(coerced)
    if facts["errors"]:
        errors.extend(facts["errors"])
    signatures = facts.get("signatures", ())
    expected_rooms = macro_r * macro_c
    if len(signatures) != expected_rooms:
        errors.append(
            f"wall lattice declares {expected_rooms} rooms but the rule sees {len(signatures)}"
        )

    roles = _near_miss_roles(signatures)
    if enforce_lesson and signatures:
        query = signatures[0]
        if query[1] < 1:
            errors.append("the query room must have at least one doorway")
        if query[2] < 1 or query[3] < 1:
            errors.append("the query room must contain both color-2 and color-3 markers")
        if len(facts["matches"]) != 1:
            errors.append(
                "the lesson must have exactly one candidate with the complete query signature"
            )
        nonmatch_shared = [
            sum(left == right for left, right in zip(signatures[0], signature))
            for signature in signatures[1:]
            if signature != signatures[0]
        ]
        if not nonmatch_shared or max(nonmatch_shared) < 2:
            errors.append(
                "at least one distractor must share two or more signature fields with the query"
            )

    geometry = {
        "macro_r": macro_r,
        "macro_c": macro_c,
        "room_h": row_spans[0],
        "room_w": col_spans[0],
        "row_spans": row_spans,
        "col_spans": col_spans,
        "wall_rows": wall_rows,
        "wall_cols": wall_cols,
        "door_pairs": tuple(sorted(door_pairs)),
        "signatures": signatures,
        "matches": facts.get("matches", ()),
        "near_miss_roles": roles,
        "output": facts.get("output"),
        "wall9_count": sum(value == 9 for row in coerced for value in row),
    }
    return {"grid": coerced, "errors": errors, "geometry": geometry}


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed lattices, invalid door topology, and ambiguous lessons."""
    return _scene_analysis(grid, enforce_lesson=True)["errors"]


def observe_overrides(grid):
    analysis = _scene_analysis(grid, enforce_lesson=False)
    geometry = analysis.get("geometry")
    if geometry is None:
        return {}
    return {
        "macro_r": geometry["macro_r"],
        "macro_c": geometry["macro_c"],
        "room_h": geometry["room_h"],
        "room_w": geometry["room_w"],
    }


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
    macro_r, macro_c, query_h, query_w = _draw_axes(ctx)
    layout_rng = ctx.draw_rng("semantic_layout")
    plan = _build_plan(
        macro_r,
        macro_c,
        query_h,
        query_w,
        difficulty,
        layout_rng,
    )

    row_spans = plan["row_spans"]
    col_spans = plan["col_spans"]
    row_walls = _boundaries(row_spans)
    col_walls = _boundaries(col_spans)
    height, width = row_walls[-1] + 1, col_walls[-1] + 1
    grid = full_grid(height, width, 1)

    room_cells = []
    for row in range(macro_r):
        for col in range(macro_c):
            cells = _room_cells(row_walls, col_walls, row, col)
            room_cells.append(cells)
            for cell_row, cell_col in cells:
                grid[cell_row][cell_col] = 0

    for edge in plan["edges"]:
        row, col = _edge_door_cell(
            edge, macro_c, row_walls, col_walls
        )
        grid[row][col] = 7

    # Color 9 is an equivalent wall value in the canonical rule. Sparse,
    # answer-independent accents make that branch visible without encoding the
    # target. Intersections are chosen so no accent can masquerade as a door.
    wall_rng = ctx.draw_rng("wall_accents")
    wall_candidates = [
        (row, col)
        for row in row_walls
        for col in col_walls
        if grid[row][col] == 1
    ]
    wall_rng.shuffle(wall_candidates)
    if wall_candidates and wall_rng.random() < _WALL9_RATE[difficulty]:
        accent_count = min(
            len(wall_candidates),
            1 + int(difficulty == "hard") + wall_rng.randint(0, 1),
        )
        for row, col in wall_candidates[:accent_count]:
            grid[row][col] = 9

    degrees = [0] * (macro_r * macro_c)
    for first, second in plan["edges"]:
        degrees[first] += 1
        degrees[second] += 1
    areas = [len(cells) for cells in room_cells]
    marker_rng = ctx.draw_rng("room_markers")
    counts = _marker_counts(
        plan, areas, degrees, difficulty, marker_rng
    )
    for room, cells in enumerate(room_cells):
        shuffled = list(cells)
        marker_rng.shuffle(shuffled)
        n2, n3 = counts[room]
        for row, col in shuffled[:n2]:
            grid[row][col] = 2
        for row, col in shuffled[n2:n2 + n3]:
            grid[row][col] = 3

    analysis = _scene_analysis(grid, enforce_lesson=True)
    if analysis["errors"]:
        raise RuntimeError(
            "internal generator invariant failed: "
            + "; ".join(analysis["errors"])
        )
    focus = plan["focus"]
    if not analysis["geometry"]["near_miss_roles"][focus]:
        raise RuntimeError(
            f"internal generator invariant failed: missing {focus} near-miss"
        )
    return [row[:] for row in grid]
