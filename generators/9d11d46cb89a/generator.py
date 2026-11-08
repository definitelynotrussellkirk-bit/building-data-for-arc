"""Generator for 9d11d46cb89a — five-room key/value lookup.

The five enclosed rooms are ordered left to right as
``key1, value1, key2, value2, query``.  The query room exactly repeats one
key's colored cells at the same room-relative coordinates, and the answer is
the complete interior crop of that key's associated value room.

Ordinary samples follow a four-slot lesson schedule.  Every four consecutive
samples contain both answer branches plus three discriminators: keys that
require shape, exact position, and color respectively.  The schedule therefore
refutes fixed-answer, cell-count-only, translation-invariant, and color-blind
shortcuts without relying on chance.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d11d46cb89a"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"  # lookup grammar + observable schedule + <=30 canonical-area envelope
RULE_HASH = "3c5efa300447"

SUMMARY = (
    "Read the five wall-enclosed rooms from left to right as key1, value1, "
    "key2, value2, and query. Compare the query's nonzero colored cells with "
    "the two keys at exact room-relative coordinates, including color. Return "
    "the entire interior grid of the value room paired with the unique match."
)

INVARIANTS = [
    "exactly five equal-size rooms are enclosed by a uniform wall color from {1,7,9}",
    "every room contains one non-wall monochrome pattern on background 0",
    "the two key patterns contain the same number of cells but are not identical",
    "the query exactly matches one and only one key, including color and room-relative position",
    "the two value-room interiors are distinct, so the selected branch changes the answer",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

WALL_COLORS = (1, 7, 9)
CONTENT_COLORS = (2, 3, 4, 5, 6, 8)
ROOM_PROFILES = ("compact", "medium", "tall")
QUERY_MATCHES = ("key1", "key2")
KEY_DISCRIMINATORS = ("shape", "position", "color")
MOTIF_SIZES = (3, 4, 5)

# Generated examples must fit the repository's ARC 30x30 materialization
# envelope.  The recognizer below remains broader and accepts the linked
# canonical 5x5 and 5x7 rooms, whose source examples are 31/41 columns wide.
_PROFILE_DIMS = {
    "compact": (3, 3),  # 5x21 input; also a linked canonical profile
    "medium": (4, 4),   # 6x26 input
    "tall": (6, 4),     # 8x26 input; reaches canonical-area tolerance
}
_CANONICAL_ROOM_DIMS = frozenset({(3, 3), (5, 5), (5, 7)})
_STRICT_ROOM_DIMS = frozenset(_PROFILE_DIMS.values()) | _CANONICAL_ROOM_DIMS

# Four consecutive sample indexes always contain all three discriminator
# branches and both possible query answers.  The position/color cases select
# key2 so the natural choose-first rival is observably wrong.
_SCHEDULE = (
    ("shape", "key1", 3),
    ("shape", "key2", 4),
    ("position", "key2", 5),
    ("color", "key2", 3),
)
SCHEDULE_PROFILES = (
    "shape_key1",
    "shape_key2",
    "position_key2",
    "color_key2",
)

AXES = {
    "room_profile": {
        "type": "str",
        "default": "sample-index cycle with a difficulty phase shift",
        "valid": "|".join(ROOM_PROFILES),
    },
    "wall_color": {
        "type": "color",
        "default": "keyed rng",
        "valid": "1|7|9",
    },
    "query_match": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "|".join(QUERY_MATCHES),
    },
    "key_discriminator": {
        "type": "str",
        "default": "four-slot lesson schedule",
        "valid": "|".join(KEY_DISCRIMINATORS),
    },
    "motif_size": {
        "type": "int",
        "default": "four-slot lesson schedule",
        "valid": "3..5",
    },
}

# Every Cartesian combination of declared exact axes is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Same-size, connected pairs with equal bounding boxes.  Equal cell counts make
# count-only matching useless; the pair geometry provides the shape branch.
_BASE_SHAPE_PAIRS: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ),
}


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the semantic schedule slot; seed/difficulty are nuisance inputs."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _default_room_profile(sample_index: int, difficulty: str | None) -> str:
    # Cycle every profile in every band so each band contains linked compact
    # canonical geometry, while a phase shift keeps the band parameter
    # observable without ever generating an input wider than 30 cells.
    phase = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return ROOM_PROFILES[(int(sample_index) + phase) % len(ROOM_PROFILES)]


def _effective_axes(
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    _validate_overrides(overrides)
    slot = _SCHEDULE[int(sample_index) % len(_SCHEDULE)]
    effective = dict(overrides)
    effective.setdefault("room_profile", _default_room_profile(sample_index, difficulty))
    effective.setdefault("query_match", slot[1])
    effective.setdefault("key_discriminator", slot[0])
    effective.setdefault("motif_size", slot[2])
    return effective


def _normalize_cells(cells: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _transform_cells(
    cells: Sequence[tuple[int, int]], transform: int
) -> tuple[tuple[int, int], ...]:
    normalized = _normalize_cells(cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1

    def apply(row: int, col: int) -> tuple[int, int]:
        if transform == 0:   # identity
            return row, col
        if transform == 1:   # horizontal reflection
            return row, width - 1 - col
        if transform == 2:   # vertical reflection
            return height - 1 - row, col
        if transform == 3:   # 180 rotation
            return height - 1 - row, width - 1 - col
        if transform == 4:   # transpose
            return col, row
        if transform == 5:   # transpose + horizontal reflection
            return col, height - 1 - row
        if transform == 6:   # transpose + vertical reflection
            return width - 1 - col, row
        if transform == 7:   # transpose + 180 rotation
            return width - 1 - col, height - 1 - row
        raise ValueError(f"unsupported transform {transform}")

    return _normalize_cells(tuple(apply(row, col) for row, col in normalized))


def _shape_dims(cells: Sequence[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize_cells(cells)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _placements(
    cells: Sequence[tuple[int, int]], room_h: int, room_w: int
) -> list[tuple[int, int]]:
    shape_h, shape_w = _shape_dims(cells)
    return [
        (top, left)
        for top in range(room_h - shape_h + 1)
        for left in range(room_w - shape_w + 1)
    ]


def _shift_cells(
    cells: Sequence[tuple[int, int]], offset: tuple[int, int]
) -> tuple[tuple[int, int], ...]:
    top, left = offset
    return tuple(sorted((top + row, left + col) for row, col in cells))


def _colored_motif(
    cells: Sequence[tuple[int, int]], color: int
) -> dict[tuple[int, int], int]:
    return {tuple(cell): int(color) for cell in cells}


def _choose_key_motifs(
    *,
    discriminator: str,
    motif_size: int,
    room_h: int,
    room_w: int,
    colors: tuple[int, int, int],
    rng: Any,
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int], tuple[int, int]]:
    pair = _BASE_SHAPE_PAIRS[motif_size]
    transform = rng.randrange(8)
    shape_a = _transform_cells(pair[0], transform)
    shape_b = _transform_cells(pair[1], transform)
    placements = _placements(shape_a, room_h, room_w)
    if not placements:
        raise ValueError("motif cannot fit the requested room profile")

    key_color_a, key_color_b, shared_value_color = colors
    if discriminator == "shape":
        offset = rng.choice(placements)
        key1 = _colored_motif(_shift_cells(shape_a, offset), key_color_a)
        key2 = _colored_motif(_shift_cells(shape_b, offset), key_color_a)
        return key1, key2, (key_color_b, shared_value_color)

    if discriminator == "position":
        if len(placements) < 2:
            raise ValueError("position discriminator needs two legal motif placements")
        offset1, offset2 = rng.sample(placements, 2)
        key1 = _colored_motif(_shift_cells(shape_a, offset1), key_color_a)
        key2 = _colored_motif(_shift_cells(shape_a, offset2), key_color_a)
        return key1, key2, (key_color_b, shared_value_color)

    if discriminator == "color":
        offset = rng.choice(placements)
        shifted = _shift_cells(shape_a, offset)
        key1 = _colored_motif(shifted, key_color_a)
        key2 = _colored_motif(shifted, key_color_b)
        # One shared value color keeps the complete input palette at the
        # canonical size of five even though the two key colors differ.
        return key1, key2, (shared_value_color, shared_value_color)

    raise ValueError(f"unsupported key_discriminator {discriminator!r}")


def _choose_value_motifs(
    *,
    room_h: int,
    room_w: int,
    value_colors: tuple[int, int],
    rng: Any,
) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    value_size = rng.choice(MOTIF_SIZES)
    pair = _BASE_SHAPE_PAIRS[value_size]
    transform = rng.randrange(8)
    shape_a = _transform_cells(pair[0], transform)
    shape_b = _transform_cells(pair[1], transform)
    placements_a = _placements(shape_a, room_h, room_w)
    placements_b = _placements(shape_b, room_h, room_w)
    if not placements_a or not placements_b:
        raise ValueError("value motif cannot fit the requested room profile")
    cells_a = _shift_cells(shape_a, rng.choice(placements_a))
    cells_b = _shift_cells(shape_b, rng.choice(placements_b))
    return (
        _colored_motif(cells_a, value_colors[0]),
        _colored_motif(cells_b, value_colors[1]),
    )


def _room_left(room_index: int, room_w: int) -> int:
    return 1 + room_index * (room_w + 1)


def _paint_room(
    grid: list[list[int]],
    room_index: int,
    room_w: int,
    motif: dict[tuple[int, int], int],
) -> None:
    left = _room_left(room_index, room_w)
    for (row, col), color in motif.items():
        grid[1 + row][left + col] = color


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    effective = _effective_axes(sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    room_profile = ctx.draw_choice("room_profile", ROOM_PROFILES)
    wall_color = ctx.draw_choice("wall_color", WALL_COLORS)
    query_match = ctx.draw_choice("query_match", QUERY_MATCHES)
    key_discriminator = ctx.draw_choice("key_discriminator", KEY_DISCRIMINATORS)
    motif_size = ctx.draw_int("motif_size", min(MOTIF_SIZES), max(MOTIF_SIZES))

    room_h, room_w = _PROFILE_DIMS[room_profile]
    color_rng = ctx.draw_rng("content-colors")
    colors = tuple(color_rng.sample(list(CONTENT_COLORS), 3))
    key1, key2, value_colors = _choose_key_motifs(
        discriminator=key_discriminator,
        motif_size=motif_size,
        room_h=room_h,
        room_w=room_w,
        colors=colors,
        rng=ctx.draw_rng("key-motifs"),
    )
    value1, value2 = _choose_value_motifs(
        room_h=room_h,
        room_w=room_w,
        value_colors=value_colors,
        rng=ctx.draw_rng("value-motifs"),
    )
    query = dict(key1 if query_match == "key1" else key2)

    total_h = room_h + 2
    total_w = 5 * room_w + 6
    grid = full_grid(total_h, total_w, wall_color)
    for room_index in range(5):
        left = _room_left(room_index, room_w)
        for row in range(1, total_h - 1):
            for col in range(left, left + room_w):
                grid[row][col] = 0

    for room_index, motif in enumerate((key1, value1, key2, value2, query)):
        _paint_room(grid, room_index, room_w, motif)
    return grid


def _grid_errors(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    converted = [list(row) for row in grid]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in converted
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"], None
    return [], converted


def _room_grid(
    grid: list[list[int]], room_index: int, room_h: int, room_w: int
) -> list[list[int]]:
    left = _room_left(room_index, room_w)
    return [row[left:left + room_w] for row in grid[1:1 + room_h]]


def _motif_map(room: Sequence[Sequence[int]]) -> dict[tuple[int, int], int]:
    return {
        (row, col): int(value)
        for row, values in enumerate(room)
        for col, value in enumerate(values)
        if int(value) != 0
    }


def _normalized_positions(motif: dict[tuple[int, int], int]) -> tuple[tuple[int, int], ...]:
    return _normalize_cells(tuple(motif))


def _monochrome_color(motif: dict[tuple[int, int], int]) -> int | None:
    colors = set(motif.values())
    return next(iter(colors)) if len(colors) == 1 else None


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, converted = _grid_errors(grid)
    if converted is None:
        return {"errors": errors}
    total_h, total_w = len(converted), len(converted[0])
    if total_h < 5 or total_w < 21:
        errors.append(f"grid {total_h}x{total_w} is too small for five enclosed rooms")

    wall_color = converted[0][0]
    if wall_color not in WALL_COLORS:
        errors.append(f"top-left wall color {wall_color} is not one of {WALL_COLORS}")

    if any(value != wall_color for value in converted[0]):
        errors.append("top border is not a uniform wall row")
    if any(value != wall_color for value in converted[-1]):
        errors.append("bottom border is not a uniform wall row")

    wall_columns = [
        col
        for col in range(total_w)
        if all(converted[row][col] == wall_color for row in range(total_h))
    ]
    room_w = None
    if len(wall_columns) != 6:
        errors.append(f"expected exactly six full-height wall columns, found {len(wall_columns)}")
    elif wall_columns[0] != 0 or wall_columns[-1] != total_w - 1:
        errors.append("outer left/right borders must be full-height wall columns")
    else:
        widths = [right - left - 1 for left, right in zip(wall_columns, wall_columns[1:])]
        if len(set(widths)) != 1 or widths[0] < 3:
            errors.append(f"five room widths must be equal and at least 3, found {widths}")
        else:
            room_w = widths[0]

    stray_wall_colors = [
        (row, col, value)
        for row, values in enumerate(converted)
        for col, value in enumerate(values)
        if value in WALL_COLORS and value != wall_color
    ]
    if stray_wall_colors:
        errors.append("mixed wall colors or wall-valued cells appear inside the room system")

    room_h = total_h - 2
    if room_h < 3:
        errors.append(f"room height {room_h} must be at least 3")

    expected_profile = None
    if room_w is not None:
        for name, dims in _PROFILE_DIMS.items():
            if dims == (room_h, room_w):
                expected_profile = name
                break

    rooms: list[list[list[int]]] = []
    motifs: list[dict[tuple[int, int], int]] = []
    room_colors: list[int | None] = []
    if room_w is not None:
        expected_total_w = 5 * room_w + 6
        if total_w != expected_total_w:
            errors.append(
                f"five-room width formula expected {expected_total_w}, found {total_w}"
            )
        for room_index in range(5):
            room = _room_grid(converted, room_index, room_h, room_w)
            rooms.append(room)
            motif = _motif_map(room)
            motifs.append(motif)
            if not motif:
                errors.append(f"room {room_index + 1} has an empty pattern")
                room_colors.append(None)
                continue
            color = _monochrome_color(motif)
            if color is None:
                errors.append(f"room {room_index + 1} pattern is not monochrome")
            elif color in WALL_COLORS:
                errors.append(f"room {room_index + 1} uses wall color {color} as content")
            room_colors.append(color)

    query_match = None
    key_discriminator = None
    motif_size = None
    if len(motifs) == 5 and all(motifs):
        key1, _value1, key2, _value2, query = motifs
        if len(key1) != len(key2):
            errors.append(
                f"key patterns must have equal cell counts, found {len(key1)} and {len(key2)}"
            )
        else:
            motif_size = len(key1)
        if key1 == key2:
            errors.append("key1 and key2 must be distinct")
        matches = [query == key1, query == key2]
        if sum(matches) != 1:
            errors.append(
                f"query must exactly match one key, found {sum(matches)} matching keys"
            )
        else:
            query_match = "key1" if matches[0] else "key2"

        key1_color = _monochrome_color(key1)
        key2_color = _monochrome_color(key2)
        coords1 = set(key1)
        coords2 = set(key2)
        normalized1 = _normalized_positions(key1)
        normalized2 = _normalized_positions(key2)
        if coords1 == coords2 and key1_color != key2_color:
            key_discriminator = "color"
        elif (
            key1_color == key2_color
            and normalized1 == normalized2
            and coords1 != coords2
        ):
            key_discriminator = "position"
        elif (
            key1_color == key2_color
            and len(key1) == len(key2)
            and normalized1 != normalized2
        ):
            key_discriminator = "shape"
        else:
            errors.append(
                "key relation is not one of the declared shape/position/color discriminators"
            )

        if rooms[1] == rooms[3]:
            errors.append("value1 and value2 room interiors must be distinct")
        selected_room = rooms[1] if query_match == "key1" else rooms[3] if query_match == "key2" else None
        if selected_room is not None and selected_room == rooms[4]:
            errors.append("selected value room must not be identical to the query room")

    palette = {value for row in converted for value in row}
    return {
        "errors": errors,
        "grid": converted,
        "total_h": total_h,
        "total_w": total_w,
        "room_h": room_h,
        "room_w": room_w,
        "room_profile": expected_profile,
        "wall_color": wall_color,
        "rooms": rooms,
        "motifs": motifs,
        "room_colors": tuple(room_colors),
        "query_match": query_match,
        "key_discriminator": key_discriminator,
        "motif_size": motif_size,
        "palette": palette,
        "palette_size": len(palette),
    }


def self_check(
    grid: Any,
    *,
    difficulty: str | None = None,
    meta: Any = None,
) -> list[str]:
    """Recognize the complete five-room teaching grammar and reject impostors."""
    del difficulty, meta
    return list(semantic_observables(grid).get("errors", []))


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("room_profile") not in ROOM_PROFILES:
        raise ValueError("returned grid does not encode a declared room_profile")
    if facts.get("motif_size") not in MOTIF_SIZES:
        raise ValueError("returned grid does not encode a declared motif_size")
    return {
        "room_profile": facts["room_profile"],
        "wall_color": facts["wall_color"],
        "query_match": facts["query_match"],
        "key_discriminator": facts["key_discriminator"],
        "motif_size": facts["motif_size"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    """Require linked geometry/palette, including the oversize source pairs."""
    facts = semantic_observables(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    room_dims = (facts.get("room_h"), facts.get("room_w"))
    if room_dims not in _STRICT_ROOM_DIMS:
        reasons.append(
            "room dimensions are outside the generated 3x3/4x4/6x4 envelope "
            "and linked canonical 5x5/5x7 source profiles"
        )
    if facts.get("palette_size") != 5:
        reasons.append(
            f"canonical linked palette has five colors, found {facts.get('palette_size')}"
        )
    if facts.get("motif_size") not in MOTIF_SIZES:
        reasons.append("key motif cell count is outside the canonical-linked 3..5 range")
    return reasons


def _copy_grid(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror; the canonical Racket rule remains output authority."""
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    index = 1 if facts["query_match"] == "key1" else 3
    return _copy_grid(facts["rooms"][index])


def _fixed_value(index: int) -> Callable[[Any], list[list[int]]]:
    def apply(grid: Any) -> list[list[int]]:
        facts = semantic_observables(grid)
        return _copy_grid(facts["rooms"][index])

    return apply


def _choose_by_translation_invariant_pattern(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    motifs = facts["motifs"]
    query = motifs[4]

    def normalized_colored(motif: dict[tuple[int, int], int]) -> tuple[tuple[int, int, int], ...]:
        min_row = min(row for row, _ in motif)
        min_col = min(col for _, col in motif)
        return tuple(
            sorted((row - min_row, col - min_col, color) for (row, col), color in motif.items())
        )

    query_key = normalized_colored(query)
    chosen = 1 if normalized_colored(motifs[0]) == query_key else 3
    return _copy_grid(facts["rooms"][chosen])


def _choose_ignoring_key_color(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    motifs = facts["motifs"]
    query_coords = set(motifs[4])
    chosen = 1 if set(motifs[0]) == query_coords else 3
    return _copy_grid(facts["rooms"][chosen])


def _choose_by_key_cell_count(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    motifs = facts["motifs"]
    query_count = len(motifs[4])
    chosen = 1 if len(motifs[0]) == query_count else 3
    return _copy_grid(facts["rooms"][chosen])


def _crop_nonzero_bbox(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return [[]]
    top = min(row for row, _ in cells)
    bottom = max(row for row, _ in cells)
    left = min(col for _, col in cells)
    right = max(col for _, col in cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def _crop_selected_value_bbox(grid: Any) -> list[list[int]]:
    return _crop_nonzero_bbox(rule_mirror(grid))


def _copy_query_room(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    return _copy_grid(facts["rooms"][4])


SEMANTIC_RIVALS = {
    "fixed_value1": _fixed_value(1),
    "fixed_value2": _fixed_value(3),
    "translation_invariant": _choose_by_translation_invariant_pattern,
    "ignore_key_color": _choose_ignoring_key_color,
    "key_cell_count": _choose_by_key_cell_count,
    "crop_value_bbox": _crop_selected_value_bbox,
    "copy_query_room": _copy_query_room,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "translation_invariant": _choose_by_translation_invariant_pattern,
    "ignore_key_color": _choose_ignoring_key_color,
}


def _facts(grid: Any) -> dict[str, Any]:
    return semantic_observables(grid)


def _selected_value_has_padding(grid: Any) -> bool:
    official = rule_mirror(grid)
    return _crop_nonzero_bbox(official) != official


SEMANTIC_WITNESSES = {
    "query_selects_key1": lambda grid: _facts(grid).get("query_match") == "key1",
    "query_selects_key2": lambda grid: _facts(grid).get("query_match") == "key2",
    "shape_count_tie_selects_key2": lambda grid: (
        _facts(grid).get("key_discriminator") == "shape"
        and _facts(grid).get("query_match") == "key2"
    ),
    "exact_position_selects_key2": lambda grid: (
        _facts(grid).get("key_discriminator") == "position"
        and _facts(grid).get("query_match") == "key2"
    ),
    "exact_color_selects_key2": lambda grid: (
        _facts(grid).get("key_discriminator") == "color"
        and _facts(grid).get("query_match") == "key2"
    ),
    "selected_value_keeps_room_padding": _selected_value_has_padding,
    "query_room_is_not_the_answer": lambda grid: _copy_query_room(grid) != rule_mirror(grid),
}

WITNESS_RIVALS = {
    "query_selects_key1": ["fixed_value2"],
    "query_selects_key2": ["fixed_value1"],
    "shape_count_tie_selects_key2": ["key_cell_count"],
    "exact_position_selects_key2": ["translation_invariant"],
    "exact_color_selects_key2": ["ignore_key_color"],
    "selected_value_keeps_room_padding": ["crop_value_bbox"],
    "query_room_is_not_the_answer": ["copy_query_room"],
}


def _grid_tuple(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require each four-demo window to refute every declared shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    surviving = set(LESSON_COMPETITORS)
    branches: set[str] = set()
    discriminators: set[str] = set()
    saw_shape_key2 = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        facts = semantic_observables(pair["input"])
        if facts.get("errors"):
            return [f"demo {index} input invalid: {facts['errors'][0]}"]
        official = _grid_tuple(pair["output"])
        if _grid_tuple(rule_mirror(pair["input"])) != official:
            reasons.append(f"demo {index} does not match the selected lookup rule")
        branches.add(facts["query_match"])
        discriminators.add(facts["key_discriminator"])
        saw_shape_key2 |= (
            facts["key_discriminator"] == "shape"
            and facts["query_match"] == "key2"
        )
        surviving &= {
            name
            for name in surviving
            if _grid_tuple(LESSON_COMPETITORS[name](pair["input"])) == official
        }

    if branches != set(QUERY_MATCHES):
        reasons.append("demos do not show both key1 and key2 answer branches")
    missing_discriminators = set(KEY_DISCRIMINATORS) - discriminators
    if missing_discriminators:
        reasons.append(
            "demos omit key discriminator(s): " + ", ".join(sorted(missing_discriminators))
        )
    if not saw_shape_key2:
        reasons.append("demos never refute the equal-cell-count choose-first shortcut")
    if surviving:
        reasons.append("demos leave shortcut(s) unrefuted: " + ", ".join(sorted(surviving)))

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_facts = semantic_observables(query["input"])
    if query_facts.get("errors"):
        reasons.append(f"query input invalid: {query_facts['errors'][0]}")
        return reasons
    if _grid_tuple(rule_mirror(query["input"])) != _grid_tuple(query["output"]):
        reasons.append("query does not match the selected lookup rule")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-semantic near-misses that the structural checker must reject."""
    base = generate(314159, 0, difficulty="medium")
    facts = semantic_observables(base)
    room_w = int(facts["room_w"])
    fixtures: list[tuple[str, list[list[int]]]] = []

    broken_border = _copy_grid(base)
    broken_border[0][1] = 0
    fixtures.append(("broken_outer_wall", broken_border))

    empty_query = _copy_grid(base)
    query_left = _room_left(4, room_w)
    for row in range(1, len(empty_query) - 1):
        for col in range(query_left, query_left + room_w):
            empty_query[row][col] = 0
    fixtures.append(("empty_query", empty_query))

    both_keys_match = _copy_grid(base)
    key1 = facts["rooms"][0]
    key2_left = _room_left(2, room_w)
    for row in range(facts["room_h"]):
        both_keys_match[1 + row][key2_left:key2_left + room_w] = list(key1[row])
    fixtures.append(("query_matches_both_keys", both_keys_match))

    extra_query_color = _copy_grid(base)
    query_motif = facts["motifs"][4]
    spare = next(
        (row, col)
        for row in range(facts["room_h"])
        for col in range(room_w)
        if (row, col) not in query_motif
    )
    replacement_color = next(
        color for color in CONTENT_COLORS if color not in set(query_motif.values())
    )
    extra_query_color[1 + spare[0]][query_left + spare[1]] = replacement_color
    fixtures.append(("multicolor_query", extra_query_color))

    unequal_key_count = _copy_grid(base)
    key1_cell = next(iter(facts["motifs"][0]))
    key1_left = _room_left(0, room_w)
    unequal_key_count[1 + key1_cell[0]][key1_left + key1_cell[1]] = 0
    fixtures.append(("unequal_key_counts", unequal_key_count))

    equal_values = _copy_grid(base)
    value1 = facts["rooms"][1]
    value2_left = _room_left(3, room_w)
    for row in range(facts["room_h"]):
        equal_values[1 + row][value2_left:value2_left + room_w] = list(value1[row])
    fixtures.append(("identical_value_rooms", equal_values))

    interior_wall = _copy_grid(base)
    interior_wall[1][1] = next(color for color in WALL_COLORS if color != facts["wall_color"])
    fixtures.append(("wall_color_inside_room", interior_wall))
    return fixtures
