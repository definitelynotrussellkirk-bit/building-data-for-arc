"""Generator for ARC task 348efda982ab: room marker count vs. door degree.

Colors 1 and 9 are walls.  Color 7 is a door cut into a wall and therefore an
edge between the two adjacent rectangular rooms.  Color 3 marks tokens inside
rooms.  The Racket oracle paints a room cyan (8) exactly when its token count
equals its graph degree; unmatched room interiors become background (0), while
all wall and door cells are preserved.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "348efda982ab"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "abbcb1f89b47"

SUMMARY = (
    "Walls partition the input into rooms. Doors (7) induce adjacency edges; "
    "green markers (3) are counted per room. Paint a whole room cyan (8) iff "
    "its marker count equals its number of neighboring rooms."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "colors 1 and 9 are walls; color 7 is a door on exactly one internal wall",
    "every door joins exactly two adjacent rooms and each room pair has at most one door",
    "color-3 markers occur only inside rooms",
    "at least one positive-degree room matches and at least one positive-degree room mismatches",
    "generated inputs contain at least one door and produce a non-identity output",
]

# These are the only caller-facing exact controls. Grid dimensions and room
# sizes are derived; fixed semantic colors are not palette-remappable because
# the pinned Racket rule names them literally.
AXES = {
    "room_rows": {
        "type": "int",
        "default": "difficulty-skewed mixture over 1..4",
        "valid": "1..4 (incompatible with room_cols=1)",
    },
    "room_cols": {
        "type": "int",
        "default": "difficulty-skewed mixture over 1..4",
        "valid": "1..4 (incompatible with room_rows=1)",
    },
}

_DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
_WALLS = {1, 7, 9}
_INPUT_COLORS = {0, 1, 3, 7, 9}


def _draw_room_count(ctx, label: str, lo: int, hi: int) -> int:
    """Mostly difficulty-skewed, with a stable tail that keeps all values live."""
    if ctx.draw_rng(f"{label}_full_range_tail").random() < 0.20:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int_diff(label, lo, hi)


def _room_counts(ctx, overrides: dict[str, Any]) -> tuple[int, int]:
    for axis in ("room_rows", "room_cols"):
        if axis in overrides and overrides[axis] is not None:
            value = overrides[axis]
            if isinstance(value, bool):
                raise ValueError(f"{axis} must be an integer in 1..4, not bool")
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{axis} must be an integer in 1..4") from exc
            if not 1 <= value <= 4:
                raise ValueError(f"{axis}={value} is outside 1..4")

    if overrides.get("room_rows") == 1 and overrides.get("room_cols") == 1:
        raise ValueError("room_rows=1 and room_cols=1 would create only one room")

    # A single strip override must succeed for every seed and difficulty, so
    # draw the other dimension from 2..4. Otherwise retain the complete 1..4
    # support and prevent only the derived 1x1 combination.
    row_lo = 2 if overrides.get("room_cols") == 1 else 1
    room_rows = _draw_room_count(ctx, "room_rows", row_lo, 4)
    col_lo = 2 if room_rows == 1 else 1
    room_cols = _draw_room_count(ctx, "room_cols", col_lo, 4)
    return room_rows, room_cols


def _size_bounds(difficulty: str | None) -> tuple[int, int]:
    if difficulty == "easy":
        return 3, 5
    if difficulty == "hard":
        return 2, 6
    return 2, 5


def _vary_sizes(values: list[int], lo: int, hi: int, rng) -> list[int]:
    """Keep independently drawn sizes, but avoid a fixed-size corpus."""
    if len(values) > 1 and len(set(values)) == 1 and lo < hi and rng.random() < 0.70:
        index = rng.randrange(len(values))
        values[index] = lo if values[index] != lo else hi
    return values


def _spanning_tree(nodes, edges, rng):
    parent = {node: node for node in nodes}

    def find(node):
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    selected = []
    shuffled = list(edges)
    rng.shuffle(shuffled)
    for edge in shuffled:
        a, b, _ = edge
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        parent[ra] = rb
        selected.append(edge)
    return selected


def _choose_edges(room_rows: int, room_cols: int, difficulty: str | None, rng):
    nodes = [(row, col) for row in range(room_rows) for col in range(room_cols)]
    edges = []
    for row, col in nodes:
        if col + 1 < room_cols:
            edges.append(((row, col), (row, col + 1), "vertical"))
        if row + 1 < room_rows:
            edges.append(((row, col), (row + 1, col), "horizontal"))

    mode_roll = rng.random()
    if len(nodes) >= 3 and mode_roll < 0.24:
        mode = "isolated"
    elif mode_roll < 0.62:
        mode = "connected"
    else:
        mode = "sparse"

    if mode == "isolated":
        corners = [
            (0, 0),
            (0, room_cols - 1),
            (room_rows - 1, 0),
            (room_rows - 1, room_cols - 1),
        ]
        isolated = rng.choice(sorted(set(corners)))
        remaining_nodes = [node for node in nodes if node != isolated]
        remaining_edges = [
            edge for edge in edges if isolated not in edge[:2]
        ]
        selected = _spanning_tree(remaining_nodes, remaining_edges, rng)
        chosen = set(selected)
        extra_probability = {
            "easy": 0.05,
            "medium": 0.18,
            "hard": 0.35,
        }.get(difficulty, 0.18)
        for edge in remaining_edges:
            if edge not in chosen and rng.random() < extra_probability:
                selected.append(edge)
        # Corner removal leaves a connected grid graph for every supported
        # shape except two rooms, which never enters this branch.
        return selected, mode

    if mode == "connected":
        selected = _spanning_tree(nodes, edges, rng)
        chosen = set(selected)
        extra_probability = {
            "easy": 0.08,
            "medium": 0.24,
            "hard": 0.48,
        }.get(difficulty, 0.24)
        for edge in edges:
            if edge not in chosen and rng.random() < extra_probability:
                selected.append(edge)
        return selected, mode

    shuffled = list(edges)
    rng.shuffle(shuffled)
    upper = max(1, min(len(shuffled), len(nodes) - 1))
    count = rng.randint(1, upper)
    return shuffled[:count], mode


def _separator_positions(sizes: list[int]) -> list[int]:
    separators = [0]
    cursor = 0
    for size in sizes:
        cursor += size + 1
        separators.append(cursor)
    return separators


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            f"difficulty must be easy, medium, hard, default, or None; got {difficulty!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    normalized_difficulty = None if difficulty == "default" else difficulty
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=normalized_difficulty,
        overrides=overrides,
    )

    room_rows, room_cols = _room_counts(ctx, overrides)
    size_lo, size_hi = _size_bounds(normalized_difficulty)
    size_rng = ctx.draw_rng("room_sizes")
    row_heights = _vary_sizes(
        [size_rng.randint(size_lo, size_hi) for _ in range(room_rows)],
        size_lo,
        size_hi,
        size_rng,
    )
    col_widths = _vary_sizes(
        [size_rng.randint(size_lo, size_hi) for _ in range(room_cols)],
        size_lo,
        size_hi,
        size_rng,
    )

    row_separators = _separator_positions(row_heights)
    col_separators = _separator_positions(col_widths)
    height = row_separators[-1] + 1
    width = col_separators[-1] + 1
    grid = full_grid(height, width, 1)

    rooms = {}
    for room_row in range(room_rows):
        for room_col in range(room_cols):
            cells = []
            for row in range(row_separators[room_row] + 1, row_separators[room_row + 1]):
                for col in range(col_separators[room_col] + 1, col_separators[room_col + 1]):
                    grid[row][col] = 0
                    cells.append((row, col))
            rooms[(room_row, room_col)] = {
                "cells": cells,
                "degree": 0,
                "neighbors": set(),
            }

    # The oracle explicitly treats 9 as a wall. A minority of scenes show that
    # branch as contiguous internal wall segments; most retain the canonical
    # 1/7/3 palette.
    wall_rng = ctx.draw_rng("wall_variant")
    if wall_rng.random() < 0.18:
        segments = []
        for separator in row_separators[1:-1]:
            for col_index in range(room_cols):
                segments.append(
                    [(separator, col) for col in range(col_separators[col_index] + 1,
                                                       col_separators[col_index + 1])]
                )
        for separator in col_separators[1:-1]:
            for row_index in range(room_rows):
                segments.append(
                    [(row, separator) for row in range(row_separators[row_index] + 1,
                                                       row_separators[row_index + 1])]
                )
        wall_rng.shuffle(segments)
        for segment in segments[: max(1, len(segments) // 3)]:
            for row, col in segment:
                grid[row][col] = 9

    edge_rng = ctx.draw_rng("door_graph")
    selected_edges, graph_mode = _choose_edges(
        room_rows, room_cols, normalized_difficulty, edge_rng
    )
    door_rng = ctx.draw_rng("door_positions")
    for first, second, orientation in selected_edges:
        first_row, first_col = first
        second_row, second_col = second
        if orientation == "vertical":
            wall_col = col_separators[max(first_col, second_col)]
            door_row = door_rng.randint(
                row_separators[first_row] + 1,
                row_separators[first_row + 1] - 1,
            )
            grid[door_row][wall_col] = 7
        else:
            wall_row = row_separators[max(first_row, second_row)]
            door_col = door_rng.randint(
                col_separators[first_col] + 1,
                col_separators[first_col + 1] - 1,
            )
            grid[wall_row][door_col] = 7
        rooms[first]["neighbors"].add(second)
        rooms[second]["neighbors"].add(first)

    for room in rooms.values():
        room["degree"] = len(room["neighbors"])

    positive = [key for key, room in rooms.items() if room["degree"] > 0]
    if len(positive) < 2:  # Defensive: a real edge always gives two endpoints.
        raise RuntimeError("internal error: generated graph lacks two positive-degree rooms")

    marker_rng = ctx.draw_rng("marker_plan")
    keys = sorted(rooms)
    match_flags = {key: marker_rng.random() < 0.55 for key in keys}
    forced_match = marker_rng.choice(positive)
    positive_mismatch_candidates = [key for key in positive if key != forced_match]
    forced_mismatch = marker_rng.choice(positive_mismatch_candidates)
    match_flags[forced_match] = True
    match_flags[forced_mismatch] = False

    isolated = [key for key in keys if rooms[key]["degree"] == 0]
    if isolated:
        isolated_key = marker_rng.choice(isolated)
        # Alternate both degree-zero branches without tying them to position,
        # room size, or graph mode.
        match_flags[isolated_key] = marker_rng.random() < 0.50

    marker_positions_rng = ctx.draw_rng("marker_positions")
    for key in keys:
        room = rooms[key]
        degree = room["degree"]
        capacity = len(room["cells"])
        if match_flags[key]:
            marker_count = degree
        else:
            upper = min(capacity, 4)
            choices = [count for count in range(upper + 1) if count != degree]
            marker_count = marker_rng.choice(choices)
        positions = list(room["cells"])
        marker_positions_rng.shuffle(positions)
        for row, col in positions[:marker_count]:
            grid[row][col] = 3

    analysis = _analysis(grid)
    if analysis["errors"]:
        raise RuntimeError(
            f"internal generator invariant failed ({graph_mode}): "
            + "; ".join(analysis["errors"])
        )
    return grid


def _invalid(errors: list[str], message: str) -> None:
    if message not in errors:
        errors.append(message)


def _analysis(grid) -> dict[str, Any]:
    """Parse a lawful lesson grid, derive graph facts, and mirror the oracle."""
    errors: list[str] = []
    result: dict[str, Any] = {
        "errors": errors,
        "output": None,
        "room_rows": None,
        "room_cols": None,
        "row_heights": [],
        "col_widths": [],
        "rooms": [],
        "doors": [],
        "connected": False,
        "has_wall_9": False,
    }

    if not isinstance(grid, list) or not grid:
        return {**result, "errors": ["grid must be a non-empty list of rows"]}
    if not all(isinstance(row, list) for row in grid):
        return {**result, "errors": ["every row must be a list"]}
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return {**result, "errors": ["grid must be rectangular and non-empty"]}
    height = len(grid)
    if height > 30 or width > 30:
        _invalid(errors, f"grid exceeds ARC 30x30 limit: {height}x{width}")
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in _INPUT_COLORS
            ):
                _invalid(errors, "grid contains an invalid input color or non-integer")
                return result

    result["has_wall_9"] = any(value == 9 for row in grid for value in row)
    separator_rows = [
        row for row in range(height) if all(grid[row][col] in _WALLS for col in range(width))
    ]
    separator_cols = [
        col for col in range(width) if all(grid[row][col] in _WALLS for row in range(height))
    ]
    if len(separator_rows) < 2 or separator_rows[0] != 0 or separator_rows[-1] != height - 1:
        _invalid(errors, "top and bottom borders must be complete wall separators")
    if len(separator_cols) < 2 or separator_cols[0] != 0 or separator_cols[-1] != width - 1:
        _invalid(errors, "left and right borders must be complete wall separators")
    if errors:
        return result

    row_heights = [b - a - 1 for a, b in zip(separator_rows, separator_rows[1:])]
    col_widths = [b - a - 1 for a, b in zip(separator_cols, separator_cols[1:])]
    if any(size < 2 for size in row_heights):
        _invalid(errors, "each room row must have at least two interior cells")
    if any(size < 2 for size in col_widths):
        _invalid(errors, "each room column must have at least two interior cells")
    if errors:
        return result

    separator_row_set = set(separator_rows)
    separator_col_set = set(separator_cols)
    for row in range(height):
        for col in range(width):
            on_separator = row in separator_row_set or col in separator_col_set
            if on_separator and grid[row][col] not in _WALLS:
                _invalid(errors, "a wall separator contains a non-wall breach")
            if not on_separator and grid[row][col] not in {0, 3}:
                _invalid(errors, "a room interior contains a wall or door cell")
            if row in separator_row_set and col in separator_col_set and grid[row][col] == 7:
                _invalid(errors, "a door cannot occupy a wall intersection")
    if errors:
        return result

    room_rows = len(row_heights)
    room_cols = len(col_widths)
    room_by_cell = {}
    rooms = []
    for room_row in range(room_rows):
        for room_col in range(room_cols):
            room_id = room_row * room_cols + room_col
            cells = []
            marker_count = 0
            for row in range(separator_rows[room_row] + 1, separator_rows[room_row + 1]):
                for col in range(separator_cols[room_col] + 1, separator_cols[room_col + 1]):
                    cells.append((row, col))
                    room_by_cell[(row, col)] = room_id
                    marker_count += grid[row][col] == 3
            rooms.append(
                {
                    "id": room_id,
                    "row": room_row,
                    "col": room_col,
                    "cells": cells,
                    "marker_count": marker_count,
                    "neighbors": set(),
                }
            )

    door_pairs = set()
    doors = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 7:
                continue
            on_row = row in separator_row_set
            on_col = col in separator_col_set
            if on_row == on_col:
                _invalid(errors, "each door must lie on exactly one separator")
                continue
            if row in {0, height - 1} or col in {0, width - 1}:
                _invalid(errors, "doors may not occur on the outer border")
                continue
            adjacent_cells = (
                [(row - 1, col), (row + 1, col)]
                if on_row
                else [(row, col - 1), (row, col + 1)]
            )
            adjacent_ids = [room_by_cell.get(cell) for cell in adjacent_cells]
            if any(room_id is None for room_id in adjacent_ids) or adjacent_ids[0] == adjacent_ids[1]:
                _invalid(errors, "a door must join exactly two distinct adjacent rooms")
                continue
            pair = tuple(sorted(adjacent_ids))
            if pair in door_pairs:
                _invalid(errors, "each adjacent room pair may have at most one door")
                continue
            door_pairs.add(pair)
            rooms[pair[0]]["neighbors"].add(pair[1])
            rooms[pair[1]]["neighbors"].add(pair[0])
            doors.append({"cell": (row, col), "rooms": pair})
    if not doors:
        _invalid(errors, "at least one valid internal door is required")
    if errors:
        return result

    for room in rooms:
        room["degree"] = len(room["neighbors"])
        room["matches"] = room["marker_count"] == room["degree"]
        room["neighbors"] = tuple(sorted(room["neighbors"]))

    positive_matches = [room for room in rooms if room["degree"] > 0 and room["matches"]]
    positive_mismatches = [room for room in rooms if room["degree"] > 0 and not room["matches"]]
    if not positive_matches:
        _invalid(errors, "at least one positive-degree room must match")
    if not positive_mismatches:
        _invalid(errors, "at least one positive-degree room must mismatch")
    if errors:
        return result

    adjacency = {room["id"]: set(room["neighbors"]) for room in rooms}
    seen = set()
    frontier = [0]
    while frontier:
        room_id = frontier.pop()
        if room_id in seen:
            continue
        seen.add(room_id)
        frontier.extend(adjacency[room_id] - seen)

    output = [row[:] for row in grid]
    for room in rooms:
        fill = 8 if room["matches"] else 0
        for row, col in room["cells"]:
            output[row][col] = fill

    result.update(
        {
            "output": output,
            "room_rows": room_rows,
            "room_cols": room_cols,
            "row_heights": row_heights,
            "col_widths": col_widths,
            "rooms": rooms,
            "doors": doors,
            "connected": len(seen) == len(rooms),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or weak teaching scenes using the full room graph."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "room_rows": analysis["room_rows"],
        "room_cols": analysis["room_cols"],
    }


def rule_mirror(grid):
    """Input-pure Python mirror; the pinned Racket program remains authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis["output"]
