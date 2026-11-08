"""Generator for S21_H7 — learn a room-relative motif-to-fill mapping.

Walls (1/7/9) partition the board into four rectangular rooms.  Two EXAMPLE
rooms are majority-filled with distinct colors and expose a magenta(6) motif;
two QUERY rooms contain only those motifs on black.  The answer fills each
query room with the color of the example whose motif occupies the same
room-relative cells.

Ordinary draws vary layout, example/query ordering, motif-to-query ordering,
and whether the two motifs have different shapes or the same shape at distinct
room-relative offsets.  An eight-profile schedule guarantees that consecutive
lessons contain counterexamples to reading-order, same-column/nearest-room, and
translation-invariant motif shortcuts.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "2496d7db1883"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0c6fcbc89830"

SUMMARY = (
    "Four wall-separated rooms contain two majority-filled examples and two "
    "motif-only queries.  Exact magenta(6) coordinates relative to each room "
    "map a query to its example fill color.  Scheduled row/grid layouts, "
    "grouped/interleaved roles, same/reverse query order, and offset-sensitive "
    "motifs rebut spatial and reading-order shortcuts."
)

INVARIANTS = [
    "colors 1/7/9 are walls and separate exactly four equal rectangular rooms",
    "exactly two rooms are examples and two are motif-only queries",
    "the examples use distinct fill colors and distinct room-relative motifs",
    "the query motifs are a permutation of the two example motifs",
    "generated grids are at most 30x30 and the transform changes both queries",
]

AXES = {
    "room_h": {
        "type": "int",
        "default": "easy/hard difficulty-skewed; medium uniform 3..5",
        "valid": "3..5",
    },
    "room_w": {
        "type": "int",
        "default": "difficulty-skewed 4..6",
        "valid": "4..6",
    },
    "motif_size": {
        "type": "int",
        "default": "difficulty-skewed 3..5",
        "valid": "3..5",
    },
    "layout": {
        "type": "str",
        "default": "scheduled",
        "valid": "row|grid",
    },
    "role_order": {
        "type": "str",
        "default": "scheduled",
        "valid": "grouped|interleaved",
    },
    "mapping_order": {
        "type": "str",
        "default": "scheduled",
        "valid": "same|reverse",
    },
    "motif_relation": {
        "type": "str",
        "default": "scheduled",
        "valid": "different_shapes|same_shape_shifted",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

WALL = 1
WALL_COLORS = frozenset((1, 7, 9))
MOTIF_COLOR = 6
FILL_COLORS = (2, 3, 4, 5, 8)
LAYOUTS = ("row", "grid")
ROLE_ORDERS = ("grouped", "interleaved")
MAPPING_ORDERS = ("same", "reverse")
MOTIF_RELATIONS = ("different_shapes", "same_shape_shifted")

# Every four consecutive profiles include both values of every scheduled axis.
# Thus a four-demo lesson cannot collapse to one reading order or one geometry.
_PROFILE_TABLE = (
    ("row",  "grouped",     "reverse", "different_shapes"),
    ("grid", "grouped",     "same",    "same_shape_shifted"),
    ("row",  "interleaved", "same",    "different_shapes"),
    ("grid", "interleaved", "reverse", "same_shape_shifted"),
    ("row",  "grouped",     "same",    "same_shape_shifted"),
    ("grid", "grouped",     "reverse", "different_shapes"),
    ("row",  "interleaved", "reverse", "same_shape_shifted"),
    ("grid", "interleaved", "same",    "different_shapes"),
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILE_TABLE)))

# Connected normalized motifs.  Every entry fits the minimum 3x4 room and has
# at least two legal translations there, which is needed by the offset branch.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (0, 3)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ),
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Stable eight-way teaching schedule; seed/difficulty are nuisance inputs."""
    del seed, difficulty
    return int(sample_index) % len(_PROFILE_TABLE)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    """Record a full-domain keyed draw while deterministically selecting a profile.

    ``draw_choice`` must see the full domain so every override remains lawful.
    We place the scheduled value at the index that this label's fresh keyed RNG
    will choose; the subsequent draw therefore records the scheduled value and
    honest full-domain provenance without touching process-global randomness.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    probe = ctx.draw_rng(label)
    chosen_index = probe.randrange(len(options))
    arranged = list(options)
    scheduled_index = arranged.index(scheduled)
    arranged[chosen_index], arranged[scheduled_index] = (
        arranged[scheduled_index],
        arranged[chosen_index],
    )
    return ctx.draw_choice(label, tuple(arranged))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    row0 = min(row for row, _col in cells)
    col0 = min(col for _row, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _placements(
    shape: tuple[tuple[int, int], ...], room_h: int, room_w: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    height = max(row for row, _col in shape) + 1
    width = max(col for _row, col in shape) + 1
    return tuple(
        tuple(sorted((top + row, left + col) for row, col in shape))
        for top in range(room_h - height + 1)
        for left in range(room_w - width + 1)
    )


def _make_motifs(rng, room_h: int, room_w: int, size: int, relation: str):
    shapes = tuple(
        shape
        for shape in _SHAPES[size]
        if _placements(shape, room_h, room_w)
    )
    if relation == "same_shape_shifted":
        shape = rng.choice(shapes)
        placements = _placements(shape, room_h, room_w)
        if len(placements) < 2:
            raise ValueError("selected motif has fewer than two room translations")
        return tuple(rng.sample(list(placements), 2))
    if relation == "different_shapes":
        first_shape, second_shape = rng.sample(list(shapes), 2)
        return (
            rng.choice(_placements(first_shape, room_h, room_w)),
            rng.choice(_placements(second_shape, room_h, room_w)),
        )
    raise ValueError(f"unsupported motif relation: {relation!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Medium must span the canonical 7/9-row profiles instead of collapsing
    # to the center height under the difficulty-skewed draw.  Easy and hard
    # retain their useful boundary emphasis.
    room_h = (
        ctx.draw_int("room_h", 3, 5)
        if difficulty == "medium"
        else ctx.draw_int_diff("room_h", 3, 5)
    )
    room_w = ctx.draw_int_diff("room_w", 4, 6)
    motif_size = ctx.draw_int_diff("motif_size", 3, 5)

    profile = _PROFILE_TABLE[schedule_profile(seed, sample_index, difficulty)]
    layout = _scheduled_choice(ctx, "layout", LAYOUTS, profile[0])
    role_order = _scheduled_choice(ctx, "role_order", ROLE_ORDERS, profile[1])
    mapping_order = _scheduled_choice(ctx, "mapping_order", MAPPING_ORDERS, profile[2])
    motif_relation = _scheduled_choice(
        ctx, "motif_relation", MOTIF_RELATIONS, profile[3]
    )

    if layout == "row":
        n_rows, n_cols = 1, 4
    else:
        n_rows, n_cols = 2, 2
    height = n_rows * room_h + n_rows + 1
    width = n_cols * room_w + n_cols + 1
    if height > 30 or width > 30:
        raise ValueError(f"constructed generated grid exceeds 30x30: {height}x{width}")

    fills = tuple(ctx.draw_rng("fills").sample(list(FILL_COLORS), 2))
    motifs = _make_motifs(
        ctx.draw_rng("motifs"), room_h, room_w, motif_size, motif_relation
    )
    query_indices = (0, 1) if mapping_order == "same" else (1, 0)
    roles = (
        ("key", "key", "query", "query")
        if role_order == "grouped"
        else ("key", "query", "key", "query")
    )

    grid = full_grid(height, width, WALL)
    positions = (
        tuple((0, col) for col in range(4))
        if layout == "row"
        else ((0, 0), (0, 1), (1, 0), (1, 1))
    )
    key_index = 0
    query_index = 0
    for slot, role in enumerate(roles):
        room_row, room_col = positions[slot]
        row0 = 1 + room_row * (room_h + 1)
        col0 = 1 + room_col * (room_w + 1)
        if role == "key":
            motif_index = key_index
            base = fills[key_index]
            key_index += 1
        else:
            motif_index = query_indices[query_index]
            base = 0
            query_index += 1
        for row in range(room_h):
            for col in range(room_w):
                grid[row0 + row][col0 + col] = base
        for row, col in motifs[motif_index]:
            grid[row0 + row][col0 + col] = MOTIF_COLOR

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def _coerce_grid(grid) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    converted: list[list[int]] = []
    errors: list[str] = []
    for index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {index} must have width {width}")
            continue
        converted_row: list[int] = []
        for value in row:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                converted_row.append(0)
            else:
                converted_row.append(value)
        converted.append(converted_row)
    return (None, errors) if errors else (converted, [])


def _analyze(grid) -> dict[str, Any]:
    converted, errors = _coerce_grid(grid)
    if errors or converted is None:
        raise ValueError("; ".join(errors))
    height = len(converted)
    width = len(converted[0])
    seen: set[tuple[int, int]] = set()
    rooms: list[dict[str, Any]] = []

    for start_row in range(height):
        for start_col in range(width):
            if (
                (start_row, start_col) in seen
                or converted[start_row][start_col] in WALL_COLORS
            ):
                continue
            queue = deque(((start_row, start_col),))
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _CARDINAL:
                    candidate = (row + drow, col + dcol)
                    if (
                        0 <= candidate[0] < height
                        and 0 <= candidate[1] < width
                        and candidate not in seen
                        and converted[candidate[0]][candidate[1]] not in WALL_COLORS
                    ):
                        seen.add(candidate)
                        queue.append(candidate)

            row0 = min(row for row, _col in cells)
            col0 = min(col for _row, col in cells)
            row1 = max(row for row, _col in cells)
            col1 = max(col for _row, col in cells)
            cell_set = set(cells)
            rectangle = {
                (row, col)
                for row in range(row0, row1 + 1)
                for col in range(col0, col1 + 1)
            }
            motif_abs = tuple(
                sorted((row, col) for row, col in cells if converted[row][col] == MOTIF_COLOR)
            )
            motif = tuple(sorted((row - row0, col - col0) for row, col in motif_abs))
            counts = Counter(
                converted[row][col]
                for row, col in cells
                if converted[row][col] not in (0, MOTIF_COLOR)
                and converted[row][col] not in WALL_COLORS
            )
            ranked = sorted(counts, key=lambda color: (-counts[color], -color))
            fill = (
                ranked[0]
                if ranked and counts[ranked[0]] > len(cells) // 2
                else None
            )
            rooms.append(
                {
                    "bbox": (row0, col0, row1, col1),
                    "cells": tuple(sorted(cells)),
                    "rectangular": cell_set == rectangle,
                    "height": row1 - row0 + 1,
                    "width": col1 - col0 + 1,
                    "motif": motif,
                    "motif_abs": motif_abs,
                    "fill": fill,
                    "counts": counts,
                    "values": frozenset(converted[row][col] for row, col in cells),
                    "role": "key" if fill is not None else "query",
                }
            )

    rooms.sort(key=lambda room: (room["bbox"][0], room["bbox"][1]))
    keys = [room for room in rooms if room["role"] == "key"]
    queries = [room for room in rooms if room["role"] == "query"]
    row_starts = sorted({room["bbox"][0] for room in rooms})
    col_starts = sorted({room["bbox"][1] for room in rooms})
    if len(row_starts) == 1 and len(col_starts) == 4:
        layout = "row"
    elif len(row_starts) == 2 and len(col_starts) == 2:
        layout = "grid"
    else:
        layout = None
    role_signature = tuple(room["role"] for room in rooms)
    role_order = {
        ("key", "key", "query", "query"): "grouped",
        ("key", "query", "key", "query"): "interleaved",
    }.get(role_signature)
    key_motifs = tuple(room["motif"] for room in keys)
    query_motifs = tuple(room["motif"] for room in queries)
    if query_motifs == key_motifs:
        mapping_order = "same"
    elif query_motifs == tuple(reversed(key_motifs)):
        mapping_order = "reverse"
    else:
        mapping_order = None
    if len(keys) == 2 and key_motifs[0] != key_motifs[1]:
        motif_relation = (
            "same_shape_shifted"
            if _normalize(key_motifs[0]) == _normalize(key_motifs[1])
            else "different_shapes"
        )
    else:
        motif_relation = None

    return {
        "grid": converted,
        "height": height,
        "width": width,
        "rooms": rooms,
        "keys": keys,
        "queries": queries,
        "layout": layout,
        "role_order": role_order,
        "mapping_order": mapping_order,
        "motif_relation": motif_relation,
        "wall_values": frozenset(
            converted[row][col]
            for row in range(height)
            for col in range(width)
            if converted[row][col] in WALL_COLORS
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    converted, basic_errors = _coerce_grid(grid)
    if basic_errors or converted is None:
        return basic_errors
    errors: list[str] = []
    info = _analyze(converted)

    if not all(
        converted[row][col] in WALL_COLORS
        for row, col in (
            *((0, col) for col in range(info["width"])),
            *((info["height"] - 1, col) for col in range(info["width"])),
            *((row, 0) for row in range(info["height"])),
            *((row, info["width"] - 1) for row in range(info["height"])),
        )
    ):
        errors.append("the outer border must be wall-colored")
    if len(info["rooms"]) != 4:
        errors.append(f"expected exactly four wall-separated rooms, found {len(info['rooms'])}")
        return errors
    if any(not room["rectangular"] for room in info["rooms"]):
        errors.append("every room must be a complete rectangle without internal wall holes")
    dimensions = {(room["height"], room["width"]) for room in info["rooms"]}
    if len(dimensions) != 1:
        errors.append("all four rooms must have equal dimensions")
    if info["layout"] not in LAYOUTS:
        errors.append("rooms must form either a 1x4 row or a 2x2 grid")
    if len(info["keys"]) != 2 or len(info["queries"]) != 2:
        errors.append(
            f"expected two example rooms and two query rooms, found "
            f"{len(info['keys'])} and {len(info['queries'])}"
        )
        return errors
    if info["role_order"] not in ROLE_ORDERS:
        errors.append("room roles must be grouped K,K,Q,Q or interleaved K,Q,K,Q")

    motif_sizes = {len(room["motif"]) for room in info["rooms"]}
    if len(motif_sizes) != 1 or not motif_sizes or next(iter(motif_sizes)) not in range(3, 6):
        errors.append("all rooms must expose the same 3..5-cell magenta motif size")
    for key in info["keys"]:
        if not key["motif"]:
            errors.append("every example room needs a magenta motif")
        allowed = {key["fill"], MOTIF_COLOR}
        if not key["values"] <= allowed:
            errors.append("example rooms may contain only their fill and motif color 6")
    for query in info["queries"]:
        if not query["motif"]:
            errors.append("every query room needs a magenta motif")
        if not query["values"] <= {0, MOTIF_COLOR}:
            errors.append("query rooms may contain only background 0 and motif color 6")

    fills = [room["fill"] for room in info["keys"]]
    if len(set(fills)) != 2:
        errors.append("the two example fill colors must be distinct")
    key_motifs = [room["motif"] for room in info["keys"]]
    query_motifs = [room["motif"] for room in info["queries"]]
    if len(set(key_motifs)) != 2:
        errors.append("the two example motifs must be distinct in room-relative coordinates")
    if Counter(query_motifs) != Counter(key_motifs):
        errors.append("each query motif must match exactly one example motif")
    if info["mapping_order"] not in MAPPING_ORDERS:
        errors.append("query motifs must be the same or reverse permutation of example motifs")
    if info["motif_relation"] not in MOTIF_RELATIONS:
        errors.append("example motifs must differ by shape or by room-relative offset")
    if not any(0 in query["values"] for query in info["queries"]):
        errors.append("query rooms need background cells so the transform is visible")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(converted)
        for axis, value in requested.items():
            if observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic manifold, including every published canonical input."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    info = _analyze(grid)
    room_h = info["rooms"][0]["height"]
    room_w = info["rooms"][0]["width"]
    if not (3 <= room_h <= 6 and 4 <= room_w <= 7):
        reasons.append(
            f"canonical-scale rooms are 3..6 by 4..7, found {room_h}x{room_w}"
        )
    if info["wall_values"] - WALL_COLORS:
        reasons.append("walls must use only colors 1/7/9")
    if any(key["fill"] not in FILL_COLORS for key in info["keys"]):
        reasons.append("example fills must use the demonstrated fill-color family")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    reasons = self_check(grid)
    if reasons:
        raise ValueError(f"cannot observe axes from invalid grid: {reasons}")
    info = _analyze(grid)
    room = info["rooms"][0]
    return {
        "room_h": room["height"],
        "room_w": room["width"],
        "motif_size": len(room["motif"]),
        "layout": info["layout"],
        "role_order": info["role_order"],
        "mapping_order": info["mapping_order"],
        "motif_relation": info["motif_relation"],
    }


def expected_output(grid) -> list[list[int]]:
    reasons = self_check(grid)
    if reasons:
        raise ValueError(f"cannot solve invalid motif-room grid: {reasons}")
    info = _analyze(grid)
    mapping = {room["motif"]: room["fill"] for room in info["keys"]}
    output = [row[:] for row in info["grid"]]
    for query in info["queries"]:
        color = mapping[query["motif"]]
        for row, col in query["cells"]:
            output[row][col] = color
    return output


def _paint_queries(grid, colors: Iterable[int]) -> list[list[int]]:
    try:
        info = _analyze(grid)
    except ValueError:
        return []
    output = [row[:] for row in info["grid"]]
    colors = tuple(colors)
    if len(colors) != len(info["queries"]):
        return output
    for query, color in zip(info["queries"], colors):
        for row, col in query["cells"]:
            output[row][col] = color
    return output


def _rival_same_reading_order(grid):
    try:
        info = _analyze(grid)
    except ValueError:
        return []
    return _paint_queries(grid, (room["fill"] for room in info["keys"]))


def _rival_reverse_reading_order(grid):
    try:
        info = _analyze(grid)
    except ValueError:
        return []
    return _paint_queries(grid, (room["fill"] for room in reversed(info["keys"])))


def _room_center(room) -> tuple[float, float]:
    row0, col0, row1, col1 = room["bbox"]
    return ((row0 + row1) / 2.0, (col0 + col1) / 2.0)


def _rival_nearest_example(grid):
    try:
        info = _analyze(grid)
    except ValueError:
        return []
    colors = []
    for query in info["queries"]:
        query_center = _room_center(query)
        nearest = min(
            enumerate(info["keys"]),
            key=lambda item: (
                abs(_room_center(item[1])[0] - query_center[0])
                + abs(_room_center(item[1])[1] - query_center[1]),
                item[0],
            ),
        )[1]
        colors.append(nearest["fill"])
    return _paint_queries(grid, colors)


def _rival_motif_shape_ignores_room_offset(grid):
    try:
        info = _analyze(grid)
    except ValueError:
        return []
    mapping: dict[tuple[tuple[int, int], ...], int] = {}
    for key in info["keys"]:
        mapping.setdefault(_normalize(key["motif"]), key["fill"])
    colors = [mapping.get(_normalize(query["motif"]), info["keys"][0]["fill"])
              for query in info["queries"]]
    return _paint_queries(grid, colors)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "same_reading_order": _rival_same_reading_order,
    "reverse_reading_order": _rival_reverse_reading_order,
    "nearest_example": _rival_nearest_example,
    "motif_shape_ignores_room_offset": _rival_motif_shape_ignores_room_offset,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "reverse_reading_order": _rival_reverse_reading_order,
    "same_reading_order": _rival_same_reading_order,
}


def _valid(grid) -> bool:
    return not self_check(grid)


def _observed_is(grid, axis: str, value: str) -> bool:
    return _valid(grid) and observe_overrides(grid)[axis] == value


def _rival_differs(grid, name: str) -> bool:
    if not _valid(grid):
        return False
    return SEMANTIC_RIVALS[name](grid) != expected_output(grid)


SEMANTIC_WITNESSES = {
    "same_order_mapping": lambda grid: _observed_is(grid, "mapping_order", "same"),
    "reverse_order_mapping": lambda grid: _observed_is(grid, "mapping_order", "reverse"),
    "room_offset_is_semantic": lambda grid: (
        _observed_is(grid, "motif_relation", "same_shape_shifted")
        and _rival_differs(grid, "motif_shape_ignores_room_offset")
    ),
    "spatial_alignment_is_wrong": lambda grid: _rival_differs(grid, "nearest_example"),
    "interleaved_spatial_counterexample": lambda grid: (
        _observed_is(grid, "role_order", "interleaved")
        and _rival_differs(grid, "nearest_example")
    ),
}

WITNESS_RIVALS = {
    "same_order_mapping": ["reverse_reading_order"],
    "reverse_order_mapping": ["same_reading_order"],
    "room_offset_is_semantic": ["motif_shape_ignores_room_offset"],
    "spatial_alignment_is_wrong": ["nearest_example"],
    "interleaved_spatial_counterexample": ["nearest_example"],
}


def lesson_identifiable(demos, query) -> list[str]:
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        if not all(competitor(pair["input"]) == pair["output"] for pair in demos):
            continue
        if competitor(query["input"]) == query["output"]:
            reasons.append(f"{name} survives every demo and the query")
        else:
            reasons.append(f"{name} fits every demo but changes the query answer")
    return reasons


def mutation_fixtures():
    base = generate(
        101,
        0,
        room_h=4,
        room_w=5,
        motif_size=4,
        layout="grid",
        role_order="grouped",
        mapping_order="reverse",
        motif_relation="different_shapes",
    )
    info = _analyze(base)

    missing_wall = [row[:] for row in base]
    missing_wall[0][0] = 0

    unmatched = [row[:] for row in base]
    query = info["queries"][0]
    for row, col in query["motif_abs"]:
        unmatched[row][col] = 0
    row0, col0, _row1, _col1 = query["bbox"]
    unmatched[row0][col0] = MOTIF_COLOR

    duplicate_fills = [row[:] for row in base]
    first_fill = info["keys"][0]["fill"]
    for row, col in info["keys"][1]["cells"]:
        if duplicate_fills[row][col] != MOTIF_COLOR:
            duplicate_fills[row][col] = first_fill

    return [
        ("outer_wall_broken", missing_wall),
        ("query_motif_has_no_example", unmatched),
        ("example_fill_colors_not_distinct", duplicate_fills),
    ]
