"""Generator for ARC task b5af3d6b3cd5 — gravity inside walled rooms.

Color 5 forms a rectangular outer frame and complete interior divider rows and
columns.  Every non-wall connected room is solved independently: in each room
column, nonzero marker cells fall to the lowest available room cells while
preserving their top-to-bottom order.

The curriculum deliberately includes two counterexamples on every generated
input.  First, at least one marker outside the canonical 1..4 palette must move,
so the canonical-fitting shortcut "only colors 1..4 fall" cannot survive a
demonstration.  Second, a two-marker stack is deliberately out of numerical
order, so sorting colors during gravity is visibly wrong.  Periodic anchors use
canonical grid profiles and marker counts; intervening draws broaden room
layouts and scale without exposing dishonest exact controls.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b5af3d6b3cd5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "f37a4766f778"

SUMMARY = (
    "Color-5 walls form an outer frame plus complete interior divider rows and "
    "columns. Treat every wall-separated room independently. In each room "
    "column, move all nonzero markers downward into the lowest available cells "
    "while preserving their top-to-bottom order; keep every wall fixed."
)

INVARIANTS = [
    "background is color 0 and walls are color 5",
    "the outer frame and every interior divider are solid color 5",
    "each rectangular room contains markers and background",
    "gravity is observable in at least one room column",
    "generated lessons move an extended-palette marker and preserve stack order",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

# Only genuinely exact, pixel-recoverable controls are public.  Room topology,
# marker density and palette are curriculum choices, not caller promises.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 8..16 with periodic canonical anchors",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 9..18 with periodic canonical anchors",
        "valid": "9..18",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_sparse",
    "broad_sparse",
    "canonical_dense",
    "broad_dense",
)
_CANONICAL_SHAPES = ((8, 9), (9, 9), (9, 10), (9, 11), (9, 12))
_CANONICAL_SHAPES_BY_BAND = {
    "easy": ((8, 9), (9, 9), (9, 10)),
    "medium": _CANONICAL_SHAPES,
    "hard": ((9, 10), (9, 11), (9, 12)),
    None: _CANONICAL_SHAPES,
}
_CANONICAL_MARKERS = (1, 2, 3, 4)
_EXTENDED_MARKERS = (6, 7, 8, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (8, 16), "grid_w": (9, 18)}
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool or coercible)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _canonical_shape(seed: int, sample_index: int, difficulty: Any) -> tuple[int, int]:
    choices = _CANONICAL_SHAPES_BY_BAND[difficulty]
    rng = stable_rng(
        seed,
        f"{TASK_ID}|{sample_index}|canonical-shape|{difficulty}",
        VERSION,
    )
    return choices[rng.randrange(len(choices))]


def _max_rooms_for_dimension(size: int, *, require_tall_segment: bool = False) -> int:
    """Maximum room count with >=2 cells per segment.

    Vertical partitions additionally reserve one extra cell so at least one
    room is three cells tall and can carry a moving two-marker stack.
    """
    interior_span = size - 2
    for room_count in range(3, 0, -1):
        cell_count = interior_span - (room_count - 1)
        required = 2 * room_count + (1 if require_tall_segment else 0)
        if cell_count >= required:
            return room_count
    return 1


def _partition_axis(size: int, room_count: int, rng) -> tuple[list[tuple[int, int]], list[int]]:
    """Partition the framed interior into ``room_count`` segments of size >=2."""
    interior_span = size - 2
    divider_count = room_count - 1
    cell_count = interior_span - divider_count
    if room_count < 1 or cell_count < 2 * room_count:
        raise ValueError(
            f"cannot partition dimension {size} into {room_count} rooms of size >=2"
        )
    lengths = [2] * room_count
    for _ in range(cell_count - 2 * room_count):
        lengths[rng.randrange(room_count)] += 1
    rng.shuffle(lengths)

    segments: list[tuple[int, int]] = []
    dividers: list[int] = []
    cursor = 1
    for index, length in enumerate(lengths):
        segments.append((cursor, cursor + length - 1))
        cursor += length
        if index + 1 < room_count:
            dividers.append(cursor)
            cursor += 1
    if cursor != size - 1:
        raise RuntimeError("partition accounting error")
    return segments, dividers


def _rooms_from_segments(row_segments, col_segments):
    return [
        (r0, r1, c0, c1)
        for r0, r1 in row_segments
        for c0, c1 in col_segments
    ]


def _choose_room_counts(h: int, w: int, profile: str, sample_index: int, rng):
    max_rows = min(3, _max_rooms_for_dimension(h, require_tall_segment=True))
    max_cols = min(3, _max_rooms_for_dimension(w))
    row_rooms = 2 if max_rows >= 2 else 1
    col_rooms = 2 if max_cols >= 2 else 1

    # Canonical anchors mostly resemble the observed 2x2 layouts, with a 2x3
    # branch where the canvas can support it.  Broad draws also exercise 3x2
    # and 3x3 layouts at larger sizes.
    if profile.startswith("canonical"):
        if max_cols >= 3 and (sample_index % 3 == 2 or w == 12):
            col_rooms = 3
    else:
        if max_rows >= 3 and rng.random() < 0.45:
            row_rooms = 3
        if max_cols >= 3 and rng.random() < 0.55:
            col_rooms = 3
    return row_rooms, col_rooms


def _target_marker_count(
    h: int,
    w: int,
    profile: str,
    difficulty: Any,
    capacity: int,
    rng,
) -> int:
    dense = profile.endswith("dense")
    if (h, w) in _CANONICAL_SHAPES:
        lo, hi = ((14, 16) if dense else (11, 13))
    elif difficulty == "easy":
        lo, hi = ((14, 18) if dense else (11, 14))
    elif difficulty == "hard":
        lo, hi = ((20, 28) if dense else (15, 21))
    else:
        lo, hi = ((17, 23) if dense else (12, 18))
    hi = min(hi, capacity)
    lo = min(lo, hi)
    return rng.randint(lo, hi)


def _pick_nonadjacent_color(grid, r: int, c: int, palette, rng) -> int:
    neighbours = {
        grid[nr][nc]
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0])
    }
    choices = [color for color in palette if color not in neighbours]
    return rng.choice(choices or list(palette))


def _populate_markers(grid, rooms, target: int, palette, extended: int, rng) -> None:
    """Populate exactly ``target`` cells while preserving two hard witnesses."""
    room_cells = {
        room: [
            (r, c)
            for r in range(room[0], room[1] + 1)
            for c in range(room[2], room[3] + 1)
        ]
        for room in rooms
    }
    witness_room = max(
        (room for room in rooms if room[1] - room[0] + 1 >= 3),
        key=lambda room: ((room[1] - room[0] + 1) * (room[3] - room[2] + 1), room),
    )
    wr0, wr1, wc0, wc1 = witness_room
    witness_col = rng.randint(wc0, wc1)
    basic_stack_color = palette[0]

    # [extended, basic, ..., empty] is movable and deliberately not ascending.
    grid[wr0][witness_col] = extended
    grid[wr0 + 1][witness_col] = basic_stack_color
    occupied = {(wr0, witness_col), (wr0 + 1, witness_col)}

    # Keep the rest of this column empty so its two-marker order is unambiguous.
    forbidden = {
        (r, witness_col)
        for r in range(wr0 + 2, wr1 + 1)
    }
    # Leave one explicit background cell in every other room as well.
    for room in rooms:
        if room == witness_room:
            continue
        cells = room_cells[room]
        forbidden.add(cells[rng.randrange(len(cells))])

    candidates = [
        cell
        for room in rooms
        for cell in room_cells[room]
        if cell not in occupied and cell not in forbidden
    ]
    rng.shuffle(candidates)
    room_of = {
        cell: room
        for room in rooms
        for cell in room_cells[room]
    }

    def place(cell, color=None):
        r, c = cell
        if color is None:
            color = _pick_nonadjacent_color(grid, r, c, palette, rng)
        grid[r][c] = color
        occupied.add(cell)

    # Every room must contain at least one marker.
    for room in rooms:
        if room == witness_room:
            continue
        cell = next(cell for cell in candidates if room_of[cell] == room and cell not in occupied)
        place(cell)

    # Every selected palette color must be visible; this keeps profile palette
    # size exact and prevents a nominal palette choice from becoming dead.
    present = {grid[r][c] for r, c in occupied}
    for color in palette:
        if color in present:
            continue
        cell = next(cell for cell in candidates if cell not in occupied)
        place(cell, color)
        present.add(color)

    target = min(target, len(candidates) + 2)
    for cell in candidates:
        if len(occupied) >= target:
            break
        if cell not in occupied:
            place(cell)
    if len(occupied) != target:
        raise RuntimeError(f"placed {len(occupied)} markers, expected {target}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    effective = dict(overrides)
    if profile.startswith("canonical"):
        anchor_h, anchor_w = _canonical_shape(seed, sample_index, difficulty)
        effective.setdefault("grid_h", anchor_h)
        effective.setdefault("grid_w", anchor_w)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_diff("grid_h", 8, 16)
    w = ctx.draw_int_diff("grid_w", 9, 18)
    rng = ctx.draw_rng("layout-palette-and-markers")

    row_rooms, col_rooms = _choose_room_counts(h, w, profile, sample_index, rng)
    row_segments, divider_rows = _partition_axis(h, row_rooms, rng)
    col_segments, divider_cols = _partition_axis(w, col_rooms, rng)
    rooms = _rooms_from_segments(row_segments, col_segments)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = grid[r][w - 1] = 5
    for r in divider_rows:
        for c in range(w):
            grid[r][c] = 5
    for c in divider_cols:
        for r in range(h):
            grid[r][c] = 5

    canonical = rng.sample(list(_CANONICAL_MARKERS), 3)
    extended = rng.choice(_EXTENDED_MARKERS)
    palette = canonical + [extended]
    # The first canonical color must be numerically below every extended color,
    # making [extended, canonical] a decisive order-preservation witness.
    palette.sort()
    palette.remove(extended)
    palette.append(extended)
    basic = palette[:-1]
    rng.shuffle(basic)
    palette = basic + [extended]

    # One background cell per room and the witness-column tail stay empty.
    raw_capacity = sum((r1 - r0 + 1) * (c1 - c0 + 1) for r0, r1, c0, c1 in rooms)
    capacity = raw_capacity - len(rooms)
    target = _target_marker_count(h, w, profile, difficulty, capacity, rng)
    _populate_markers(grid, rooms, target, palette, extended, rng)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid chamber puzzle: " + "; ".join(errors))
    return grid


def _interior_segments(lo: int, hi: int, dividers) -> list[tuple[int, int]]:
    segments = []
    cursor = lo
    for divider in sorted(dividers) + [hi + 1]:
        if cursor <= divider - 1:
            segments.append((cursor, divider - 1))
        cursor = divider + 1
    return segments


def _analyze(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["expected a nonempty grid"], "facts": {}}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["expected nonempty rows"], "facts": {}}
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return {"errors": ["ragged or non-sequence row"], "facts": {}}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9 (not bool)"], "facts": {}}
    h = len(grid)
    if not 8 <= h <= 16:
        errors.append(f"grid height {h} outside generator domain 8..16")
    if not 9 <= w <= 18:
        errors.append(f"grid width {w} outside generator domain 9..18")

    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errors.append("top and bottom frame rows must be solid color 5")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("left and right frame columns must be solid color 5")

    divider_rows = [r for r in range(1, h - 1) if all(grid[r][c] == 5 for c in range(w))]
    divider_cols = [c for c in range(1, w - 1) if all(grid[r][c] == 5 for r in range(h))]
    if not divider_rows:
        errors.append("expected at least one interior horizontal divider")
    if not divider_cols:
        errors.append("expected at least one interior vertical divider")

    divider_row_set = set(divider_rows)
    divider_col_set = set(divider_cols)
    stray_walls = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 5 and r not in divider_row_set and c not in divider_col_set
    ]
    if stray_walls:
        errors.append(f"color-5 wall cells must belong to complete dividers: {stray_walls[:3]}")

    row_segments = _interior_segments(1, h - 2, divider_rows)
    col_segments = _interior_segments(1, w - 2, divider_cols)
    if any(end - start + 1 < 2 for start, end in row_segments):
        errors.append("every room must be at least two cells tall")
    if any(end - start + 1 < 2 for start, end in col_segments):
        errors.append("every room must be at least two cells wide")
    rooms = _rooms_from_segments(row_segments, col_segments)

    marker_colors: set[int] = set()
    marker_count = 0
    movable = False
    for room in rooms:
        r0, r1, c0, c1 = room
        values = [grid[r][c] for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        markers = [value for value in values if value != 0]
        marker_colors.update(markers)
        marker_count += len(markers)
        if not markers:
            errors.append(f"room {room} has no marker")
        if 0 not in values:
            errors.append(f"room {room} has no background cell")
        for c in range(c0, c1 + 1):
            rows = list(range(r0, r1 + 1))
            occupied_rows = [r for r in rows if grid[r][c] != 0]
            if occupied_rows and occupied_rows != rows[-len(occupied_rows):]:
                movable = True

    if len(marker_colors) < 2:
        errors.append("expected at least two distinct marker colors")
    if marker_count == 0:
        errors.append("expected at least one marker")
    if not movable:
        errors.append("gravity must change at least one room column")

    facts = {
        "grid_h": h,
        "grid_w": w,
        "divider_rows": divider_rows,
        "divider_cols": divider_cols,
        "row_segments": row_segments,
        "col_segments": col_segments,
        "rooms": rooms,
        "marker_colors": sorted(marker_colors),
        "marker_count": marker_count,
        "palette": sorted({value for row in grid for value in row}),
        "movable": movable,
    }
    return {"errors": sorted(set(errors)), "facts": facts}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-linked chamber grammar, not curriculum extras."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["facts"]["grid_h"],
        "grid_w": analysis["facts"]["grid_w"],
    }


def _nonwall_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(component)
    return result


def _gravity(grid, *, sort_values: bool = False):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for room in _nonwall_components(grid):
        for c in sorted({cc for _r, cc in room}):
            cells = sorted(r for r, cc in room if cc == c)
            values = [grid[r][c] for r in cells if grid[r][c] != 0]
            if sort_values:
                values = sorted(values)
            for r, value in zip(cells[-len(values):] if values else (), values):
                out[r][c] = value
    return out


def rule_mirror(grid):
    """Independent Python mirror; the selected Racket rule remains authority."""
    return _gravity(grid)


def _sorted_stack_rival(grid):
    return _gravity(grid, sort_values=True)


def _canonical_colors_only_rival(grid):
    """Wrong but canonical-fitting rule: only colors 1..4 participate."""
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for room in _nonwall_components(grid):
        for c in sorted({cc for _r, cc in room}):
            cells = sorted(r for r, cc in room if cc == c)
            fixed_indexes = [
                index
                for index, r in enumerate(cells)
                if grid[r][c] not in (0, 1, 2, 3, 4, 5)
            ]
            for index in fixed_indexes:
                r = cells[index]
                out[r][c] = grid[r][c]
            boundaries = [-1, *fixed_indexes, len(cells)]
            for left, right in zip(boundaries, boundaries[1:]):
                indexes = list(range(left + 1, right))
                values = [
                    grid[cells[index]][c]
                    for index in indexes
                    if grid[cells[index]][c] in _CANONICAL_MARKERS
                ]
                for index, value in zip(indexes[-len(values):] if values else (), values):
                    out[cells[index]][c] = value
    return out


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = _analyze(grid)["facts"]
    if (facts["grid_h"], facts["grid_w"]) not in _CANONICAL_SHAPES:
        reasons.append(
            f"shape {(facts['grid_h'], facts['grid_w'])} is outside exact canonical profiles"
        )
    if len(facts["palette"]) != 6:
        reasons.append(f"canonical palette cardinality is 6, found {len(facts['palette'])}")
    if len(facts["rooms"]) not in (4, 6):
        reasons.append(f"canonical examples have 4 or 6 rooms, found {len(facts['rooms'])}")
    if not 11 <= facts["marker_count"] <= 16:
        reasons.append(
            f"canonical marker count is 11..16, found {facts['marker_count']}"
        )
    return reasons


def _lawful_rival_difference(rival: Callable[[Any], Any]):
    def witness(grid):
        return not self_check(grid) and rival(grid) != rule_mirror(grid)

    return witness


SEMANTIC_RIVALS = {
    "canonical_colors_only": _canonical_colors_only_rival,
    "sort_each_stack_by_color": _sorted_stack_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_colors_only": _canonical_colors_only_rival,
}
SEMANTIC_WITNESSES = {
    "extended_palette_marker_must_move": _lawful_rival_difference(
        _canonical_colors_only_rival
    ),
    "top_to_bottom_stack_order_is_preserved": _lawful_rival_difference(
        _sorted_stack_rival
    ),
}
WITNESS_RIVALS = {
    "extended_palette_marker_must_move": ["canonical_colors_only"],
    "top_to_bottom_stack_order_is_preserved": ["sort_each_stack_by_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo:
            reasons.append(f"demo {index} is missing an input")
            continue
        problems = self_check(demo["input"])
        if problems:
            reasons.append(f"demo {index} input is outside the task grammar: {problems[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output does not match per-room column gravity")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input")
        return reasons
    query_problems = self_check(query["input"])
    if query_problems:
        reasons.append(f"query input is outside the task grammar: {query_problems[0]}")
        return reasons
    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            isinstance(demo, dict)
            and "input" in demo
            and competitor(demo["input"]) == demo.get("output")
            for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "room_count": len(facts["rooms"]),
        "marker_count": facts["marker_count"],
        "marker_colors": facts["marker_colors"],
        "strict_canonical_like": not strict_canonical_like(grid),
        "schedule_profile": None,
    }
