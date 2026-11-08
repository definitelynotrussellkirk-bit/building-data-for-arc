"""Generator for ARC task 7deedd72e091 — rotation-congruence relation matrix.

The input is a 3x11 strip of three 3x3 tiles separated by full-height color-9
columns, exactly matching the canonical grammar.  Foreground colors are ignored:
two tiles are related when their occupancy masks agree after a 0/90/180/270°
rotation.  The output is the 3x3 relation matrix with 8 for related pairs and 0
otherwise.

Every generated lesson contains exactly one off-diagonal related pair.  Its two
members use different colors and different orientations, while the unrelated
tile shares a color and the same occupied-cell count.  Those witnesses rule out
position, foreground-color, and count-only shortcuts.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7deedd72e091"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8202ef2f7a10"
EXPECTED_OUTPUT_CODOMAIN = 3

SUMMARY = (
    "Split the canonical 3x11 strip at its two color-9 columns, reduce each "
    "3x3 tile to a nonzero occupancy mask, compare masks up to quarter-turn "
    "rotation, and emit a 3x3 matrix with 8 for equivalent pairs and 0 "
    "otherwise. Each lesson includes explicit count and color counterexamples."
)

INVARIANTS = [
    "the grid is a 3x11 strip of three 3x3 tiles",
    "single full-height color-9 columns separate adjacent tiles",
    "each tile is nonempty, nonfull, and monochrome on background color 0",
    "exactly one off-diagonal tile pair is rotation-congruent",
    "the congruent pair appears in visibly different orientations",
]

LESSON_GUARANTEES = [
    "all three tiles share an occupied-cell count from 3 to 5, so count alone cannot identify the pair",
    "the congruent pair has different colors and a noncongruent pair shares a color",
    "all three possible pair positions occur across the finite output codomain",
    "every four consecutive sample indices cover all three pair positions",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

MATCH_PAIRS = {
    "left": (0, 1),
    "outer": (0, 2),
    "right": (1, 2),
}
AXES = {
    "match_pair": {
        "type": "str",
        "default": "keyed draw over all three pair positions",
        "valid": "left|outer|right",
    },
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _rot90(cells, size=3):
    return frozenset((column, size - 1 - row) for row, column in cells)


def _orbit(cells, size=3):
    forms = []
    current = frozenset(cells)
    for _ in range(4):
        if current not in forms:
            forms.append(current)
        current = _rot90(current, size)
    return tuple(forms)


def _bits(cells, size=3):
    return tuple(
        1 if (row, column) in cells else 0
        for row in range(size)
        for column in range(size)
    )


def _canonical_key(cells, size=3):
    return min(_bits(form, size) for form in _orbit(cells, size))


def _connected(cells):
    remaining = set(cells)
    start = min(remaining)
    seen = {start}
    stack = [start]
    while stack:
        row, column = stack.pop()
        for neighbor in (
            (row - 1, column),
            (row + 1, column),
            (row, column - 1),
            (row, column + 1),
        ):
            if neighbor in remaining and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(remaining)


def _profile(cells):
    row_counts = tuple(sorted(sum((row, column) in cells for column in range(3)) for row in range(3)))
    col_counts = tuple(sorted(sum((row, column) in cells for row in range(3)) for column in range(3)))
    height = max(row for row, _ in cells) - min(row for row, _ in cells) + 1
    width = max(column for _, column in cells) - min(column for _, column in cells) + 1
    return tuple(sorted((row_counts, col_counts))), tuple(sorted((height, width)))


def _build_shape_classes():
    by_count = {}
    positions = [(row, column) for row in range(3) for column in range(3)]
    for occupied_count in (3, 4, 5):
        classes = {}
        for raw in combinations(positions, occupied_count):
            cells = frozenset(raw)
            orbit = _orbit(cells)
            if len(orbit) < 2:
                continue
            key = _canonical_key(cells)
            classes.setdefault(
                key,
                {
                    "key": key,
                    "orbit": orbit,
                    "connected": _connected(cells),
                    "profile": _profile(cells),
                },
            )
        by_count[occupied_count] = tuple(classes.values())
    return by_count


_SHAPE_CLASSES = _build_shape_classes()
_EASY_CLASSES = {
    occupied_count: tuple(record for record in records if record["connected"])
    for occupied_count, records in _SHAPE_CLASSES.items()
}
_HARD_PAIRS = {
    occupied_count: tuple(
        (left, right)
        for index, left in enumerate(records)
        for right in records[index + 1 :]
        if left["connected"]
        and right["connected"]
        and left["profile"] == right["profile"]
    )
    for occupied_count, records in _SHAPE_CLASSES.items()
}


def _choose_classes(rng, band):
    if band == "easy":
        occupied_count = rng.choice((3, 4))
        return tuple(rng.sample(list(_EASY_CLASSES[occupied_count]), 2))
    if band == "hard":
        occupied_count = rng.choice((4, 5))
        return rng.choice(_HARD_PAIRS[occupied_count])
    occupied_count = rng.choice((3, 4, 5))
    return tuple(rng.sample(list(_SHAPE_CLASSES[occupied_count]), 2))


def _paint_tile(grid, mask, tile_index, color):
    left = tile_index * 4
    for row, column in mask:
        grid[row][left + column] = color


def _make_grid(rng, match_pair, band):
    repeated_class, other_class = _choose_classes(rng, band)
    repeated_positions = MATCH_PAIRS[match_pair]
    other_position = next(index for index in range(3) if index not in repeated_positions)

    first_orientation, second_orientation = rng.sample(list(repeated_class["orbit"]), 2)
    other_orientation = rng.choice(list(other_class["orbit"]))
    tiles = [None, None, None]
    tiles[repeated_positions[0]] = first_orientation
    tiles[repeated_positions[1]] = second_orientation
    tiles[other_position] = other_orientation

    shared_color, second_color = rng.sample(range(1, 9), 2)
    colors = [shared_color, shared_color, shared_color]
    colors[repeated_positions[1]] = second_color

    grid = full_grid(3, 11, 0)
    for row in range(3):
        grid[row][3] = 9
        grid[row][7] = 9
    for tile_index, (mask, color) in enumerate(zip(tiles, colors)):
        _paint_tile(grid, mask, tile_index, color)
    return grid


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid):
    errors = _validate_grid(grid)
    result = {"errors": errors}
    if errors:
        return result
    if len(grid) != 3 or len(grid[0]) != 11:
        errors.append("grid must have canonical shape 3x11")
        return result

    expected_dividers = {3, 7}
    actual_dividers = {
        column
        for column in range(11)
        if all(grid[row][column] == 9 for row in range(3))
    }
    if actual_dividers != expected_dividers:
        errors.append("exactly columns 3 and 7 must be full-height color-9 dividers")
    for row in range(3):
        for column in range(11):
            if column not in expected_dividers and grid[row][column] == 9:
                errors.append("separator color 9 cannot occur inside a tile")
                break
    if errors:
        return result

    tiles = []
    for tile_index, left in enumerate((0, 4, 8)):
        values = [grid[row][column] for row in range(3) for column in range(left, left + 3)]
        foreground = sorted({value for value in values if value != 0})
        if len(foreground) != 1:
            errors.append(f"tile {tile_index} must use exactly one foreground color")
        mask = frozenset(
            (row, column - left)
            for row in range(3)
            for column in range(left, left + 3)
            if grid[row][column] != 0
        )
        if not mask:
            errors.append(f"tile {tile_index} is empty")
        if len(mask) == 9:
            errors.append(f"tile {tile_index} is full")
        tiles.append(
            {
                "mask": mask,
                "canonical": _canonical_key(mask) if mask else (),
                "count": len(mask),
                "color": foreground[0] if len(foreground) == 1 else None,
            }
        )
    if errors:
        result["tiles"] = tiles
        return result

    canonical_forms = []
    class_ids = []
    for tile in tiles:
        if tile["canonical"] not in canonical_forms:
            canonical_forms.append(tile["canonical"])
        class_ids.append(canonical_forms.index(tile["canonical"]))

    positive_pairs = [
        (left, right)
        for left in range(3)
        for right in range(left + 1, 3)
        if class_ids[left] == class_ids[right]
    ]
    negative_pairs = [
        (left, right)
        for left in range(3)
        for right in range(left + 1, 3)
        if class_ids[left] != class_ids[right]
    ]
    positive_name = next(
        (name for name, pair in MATCH_PAIRS.items() if pair in positive_pairs),
        None,
    )
    features = {
        "has_positive_relation": bool(positive_pairs),
        "has_negative_relation": bool(negative_pairs),
        "exactly_one_positive_pair": len(positive_pairs) == 1,
        "nontrivial_rotation": any(
            tiles[left]["mask"] != tiles[right]["mask"]
            for left, right in positive_pairs
        ),
        "count_shortcut_rebuttal": any(
            tiles[left]["count"] == tiles[right]["count"]
            for left, right in negative_pairs
        ),
        "congruent_different_colors": any(
            tiles[left]["color"] != tiles[right]["color"]
            for left, right in positive_pairs
        ),
        "noncongruent_same_color": any(
            tiles[left]["color"] == tiles[right]["color"]
            for left, right in negative_pairs
        ),
    }
    result.update(
        {
            "tile_s": 3,
            "n_tiles": 3,
            "n_classes": len(canonical_forms),
            "tiles": tiles,
            "class_ids": class_ids,
            "occupied_counts": [tile["count"] for tile in tiles],
            "positive_pairs": positive_pairs,
            "negative_pairs": negative_pairs,
            "match_pair": positive_name,
            "lesson_features": features,
            "errors": errors,
        }
    )
    return result


def observe_overrides(grid):
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"match_pair": info["match_pair"]}


def rule_mirror(grid):
    """Pure Python mirror used only for tests; Racket remains output authority."""
    info = _analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    classes = info["class_ids"]
    return [
        [8 if classes[row] == classes[column] else 0 for column in range(3)]
        for row in range(3)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    info = _analyze(grid)
    errors = list(info["errors"])
    if errors:
        return errors
    features = info["lesson_features"]
    if not features["exactly_one_positive_pair"]:
        errors.append("lesson must contain exactly one off-diagonal congruent pair")
    if not features["has_negative_relation"]:
        errors.append("lesson must contain a noncongruent tile pair")
    if not features["nontrivial_rotation"]:
        errors.append("the congruent pair must use visibly different orientations")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    if "match_pair" in overrides and overrides["match_pair"] is not None:
        match_pair = ctx.draw_choice("match_pair", tuple(MATCH_PAIRS))
    else:
        scheduled_pair = tuple(MATCH_PAIRS)[sample_index % len(MATCH_PAIRS)]
        match_pair = ctx.draw_choice("match_pair", (scheduled_pair,))
    return _make_grid(ctx.draw_rng(f"layout_{band}"), match_pair, band)
