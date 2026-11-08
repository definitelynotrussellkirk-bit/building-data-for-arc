"""Generator for ARC task a8c38be5 / content hash 5a85abd1e231.

The input contains nine solid 3x3 tiles on a zero background. Eight tiles are
canonical directional glyphs made from gray(5) plus one signal color; the ninth
is an all-gray blank tile. The glyph shape, not the tile's input position or
color, chooses one of the eight perimeter slots of a 9x9 compass. The output is
an all-gray 9x9 canvas with every directional tile stamped into its matching
slot; the blank tile leaves the center slot gray.
"""
from __future__ import annotations

from typing import Any, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "5a85abd1e231"
TASK_ID = "5a85abd1e231"
VERSION = "4.0.0"
RULE_HASH = "2b7620b38386"

SUMMARY = (
    "Nine scattered solid 3x3 tiles sit on background 0: eight gray(5) "
    "direction glyphs and one all-gray blank. Each direction glyph has the "
    "canonical arrow/corner shape and one signal color. Pack the eight glyphs "
    "into the matching perimeter blocks of a 9x9 gray compass while the blank "
    "tile corresponds to the untouched gray center. Input positions and color "
    "assignments are randomized; one canonical profile also permits a single "
    "safe touching pair."
)

INVARIANTS = [
    "there are exactly nine non-overlapping solid 3x3 tile windows and no other nonzero cells",
    "exactly one tile is all gray(5); the other eight realize the eight canonical direction glyphs once each",
    "direction is encoded by signal-cell geometry, never by input position or signal color",
    "the eight signal glyphs use either seven or eight distinct non-gray colors, matching canonical palettes 9 or 10",
    "the authoritative output is a 9x9 gray canvas with the eight source tiles stamped into their compass slots",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# The three exact (height, width, palette-size) profiles present in canonical
# train/test data. They are intentionally scheduled in every difficulty band so
# the canonical-profile floor measures real support rather than a lucky tail.
_PROFILE_ROWS = (
    ("14x14_palette9", 14, 14, 7),
    ("16x14_palette10", 16, 14, 8),
    ("16x15_palette9", 16, 15, 7),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {(row[1], row[2], row[3] + 2): row[0] for row in _PROFILE_ROWS}
CONTACT_MODES = ("separated", "touching_pair")

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "scheduled across the three canonical shape/palette profiles",
        "valid": "14x14_palette9|16x14_palette10|16x15_palette9",
    },
    "contact_mode": {
        "type": "str",
        "default": "alternates separated tiles and one safe touching pair",
        "valid": "separated|touching_pair",
    },
}

# Perimeter macro blocks in reading order. The center (1, 1) is represented by
# the blank all-gray input tile and therefore has no signal glyph.
_DIRECTION_ORDER = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),         (1, 2),
    (2, 0), (2, 1), (2, 2),
)

# Exact signal-cell geometry observed in the canonical examples. Each tuple is
# expressed in local 3x3 coordinates and maps directly to its compass block.
_GLYPHS = {
    (0, 0): ((0, 0), (0, 1), (1, 0)),
    (0, 1): ((0, 0), (0, 1), (0, 2), (1, 1)),
    (0, 2): ((0, 1), (0, 2), (1, 2)),
    (1, 0): ((0, 0), (1, 0), (1, 1), (2, 0)),
    (1, 2): ((0, 2), (1, 1), (1, 2), (2, 2)),
    (2, 0): ((1, 0), (2, 0), (2, 1)),
    (2, 1): ((1, 1), (2, 0), (2, 1), (2, 2)),
    (2, 2): ((1, 2), (2, 1), (2, 2)),
}
_GLYPH_TO_DIRECTION = {frozenset(cells): direction for direction, cells in _GLYPHS.items()}
_SIGNAL_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty in _BAND_OFFSETS:
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle through every canonical profile in every difficulty band."""
    del seed
    band = _band(difficulty)
    offset = _BAND_OFFSETS[band]
    return SCENE_PROFILES[(int(sample_index) + offset) % len(SCENE_PROFILES)]


def _scheduled_contact(sample_index: int, band: str) -> str:
    offset = _BAND_OFFSETS[band]
    return CONTACT_MODES[(int(sample_index) + offset) % len(CONTACT_MODES)]


def _rectangles_separated(a: tuple[int, int], b: tuple[int, int], margin: int) -> bool:
    ar, ac = a
    br, bc = b
    return (
        ar + 3 + margin <= br
        or br + 3 + margin <= ar
        or ac + 3 + margin <= bc
        or bc + 3 + margin <= ac
    )


def _tile_cells(origin: tuple[int, int]) -> set[tuple[int, int]]:
    top, left = origin
    return {(top + dr, left + dc) for dr in range(3) for dc in range(3)}


def _solid_origins_from_cells(
    height: int, width: int, occupied: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(height - 2)
        for col in range(width - 2)
        if all((row + dr, col + dc) in occupied for dr in range(3) for dc in range(3))
    }


def _positions_separated(height: int, width: int, rng) -> list[tuple[int, int]]:
    """Place nine tiles with at least one zero row/column between each pair."""
    candidates = [(r, c) for r in range(height - 2) for c in range(width - 2)]
    for _attempt in range(120):
        order = list(candidates)
        rng.shuffle(order)
        selected: list[tuple[int, int]] = []
        for candidate in order:
            if all(_rectangles_separated(candidate, other, 1) for other in selected):
                selected.append(candidate)
                if len(selected) == 9:
                    return selected
    raise RuntimeError(f"could not place nine separated tiles in {height}x{width}")


def _touching_pair_candidates(height: int, width: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Pairs that touch by exactly one cardinal edge cell, as in canonical train."""
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row in range(height - 5):
        for col in range(width - 4):
            pairs.append(((row, col), (row + 3, col + 2)))
            pairs.append(((row, col + 2), (row + 3, col)))
    for row in range(height - 4):
        for col in range(width - 5):
            pairs.append(((row, col), (row + 2, col + 3)))
            pairs.append(((row + 2, col), (row, col + 3)))
    return pairs


def _positions_touching_pair(height: int, width: int, rng) -> list[tuple[int, int]]:
    """Place exactly one touching pair while keeping all other tiles separated."""
    pairs = _touching_pair_candidates(height, width)
    candidates = [(r, c) for r in range(height - 2) for c in range(width - 2)]
    for _attempt in range(120):
        first, second = rng.choice(pairs)
        selected = [first, second]
        order = list(candidates)
        rng.shuffle(order)
        for candidate in order:
            if any(not _rectangles_separated(candidate, other, 0) for other in selected):
                continue
            if any(not _rectangles_separated(candidate, other, 1) for other in selected):
                continue
            selected.append(candidate)
            if len(selected) == 9:
                break
        if len(selected) != 9:
            continue
        occupied = set().union(*(_tile_cells(origin) for origin in selected))
        if _solid_origins_from_cells(height, width, occupied) != set(selected):
            continue
        if _count_components(occupied) != 8:
            continue
        return selected
    raise RuntimeError(f"could not place canonical touching-pair layout in {height}x{width}")


def _count_components(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _stamp_tile(
    grid: list[list[int]],
    top: int,
    left: int,
    direction: tuple[int, int] | None,
    color: int | None,
) -> None:
    for dr in range(3):
        for dc in range(3):
            grid[top + dr][left + dc] = 5
    if direction is None:
        return
    if color not in _SIGNAL_COLORS:
        raise ValueError(f"illegal signal color: {color!r}")
    for dr, dc in _GLYPHS[direction]:
        grid[top + dr][left + dc] = int(color)


def _signal_assignment(distinct_count: int, rng) -> list[int]:
    if distinct_count == 8:
        colors = list(_SIGNAL_COLORS)
        rng.shuffle(colors)
        return colors
    if distinct_count == 7:
        colors = rng.sample(list(_SIGNAL_COLORS), 7)
        colors.append(rng.choice(colors))
        rng.shuffle(colors)
        return colors
    raise ValueError(f"unsupported distinct signal-color count: {distinct_count}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    band = _band(difficulty)
    requested_profile = overrides.get("scene_profile")
    if requested_profile is not None and requested_profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested_profile!r}")
    requested_contact = overrides.get("contact_mode")
    if requested_contact is not None and requested_contact not in CONTACT_MODES:
        raise ValueError(f"unknown contact_mode: {requested_contact!r}")

    scheduled_profile = requested_profile or schedule_profile(seed, sample_index, band)
    scheduled_contact = requested_contact or _scheduled_contact(sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scene_profile = ctx.draw_choice("scene_profile", [scheduled_profile])
    contact_mode = ctx.draw_choice("contact_mode", [scheduled_contact])
    height, width, distinct_color_count = _PROFILE_BY_NAME[scene_profile]
    rng = ctx.draw_rng("layout")

    if contact_mode == "separated":
        positions = _positions_separated(height, width, rng)
    else:
        positions = _positions_touching_pair(height, width, rng)
    rng.shuffle(positions)

    colors = _signal_assignment(distinct_color_count, rng)
    grid = full_grid(height, width, 0)
    for origin, direction, color in zip(positions[:8], _DIRECTION_ORDER, colors):
        _stamp_tile(grid, origin[0], origin[1], direction, color)
    blank = positions[8]
    _stamp_tile(grid, blank[0], blank[1], None, None)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator produced invalid grid: " + "; ".join(errors[:4]))
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    nonzero = {(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0}
    origins = sorted(_solid_origins_from_cells(height, width, nonzero))
    if len(origins) != 9:
        errors.append(f"expected exactly nine solid 3x3 windows, found {len(origins)}")

    tile_cell_sets = [_tile_cells(origin) for origin in origins]
    covered: set[tuple[int, int]] = set()
    overlap = False
    for cells in tile_cell_sets:
        if cells & covered:
            overlap = True
        covered |= cells
    if overlap:
        errors.append("solid 3x3 tile windows must not overlap")
    if covered != nonzero:
        extras = len(nonzero - covered)
        errors.append(f"every nonzero cell must belong to a solid 3x3 tile; extra={extras}")

    tiles = []
    directions: dict[tuple[int, int], dict[str, Any]] = {}
    blank_count = 0
    signal_colors: list[int] = []
    for origin in origins:
        top, left = origin
        signal_positions = []
        tile_colors = set()
        cells = []
        for dr in range(3):
            row_values = []
            for dc in range(3):
                value = grid[top + dr][left + dc]
                row_values.append(value)
                if value != 5:
                    signal_positions.append((dr, dc))
                    tile_colors.add(value)
            cells.append(row_values)

        if not signal_positions:
            blank_count += 1
            tiles.append({"origin": origin, "direction": None, "color": None, "cells": cells})
            continue
        if len(tile_colors) != 1:
            errors.append(f"tile at {origin} must use one signal color, found {sorted(tile_colors)}")
            direction = None
            color = None
        else:
            color = next(iter(tile_colors))
            if color not in _SIGNAL_COLORS:
                errors.append(f"tile at {origin} uses illegal signal color {color}")
            direction = _GLYPH_TO_DIRECTION.get(frozenset(signal_positions))
            if direction is None:
                errors.append(f"tile at {origin} has non-canonical signal geometry {signal_positions}")
            elif direction in directions:
                errors.append(f"direction {direction} appears more than once")
            else:
                directions[direction] = {
                    "origin": origin,
                    "direction": direction,
                    "color": color,
                    "cells": cells,
                }
            signal_colors.append(color)
        tiles.append({"origin": origin, "direction": direction, "color": color, "cells": cells})

    if blank_count != 1:
        errors.append(f"expected exactly one all-gray blank tile, found {blank_count}")
    missing = sorted(set(_DIRECTION_ORDER) - set(directions))
    extra = sorted(set(directions) - set(_DIRECTION_ORDER))
    if missing or extra or len(directions) != 8:
        errors.append(f"direction coverage must be exactly the eight perimeter slots; missing={missing}, extra={extra}")

    palette = sorted({value for row in grid for value in row})
    distinct_signal_colors = len(set(signal_colors))
    if distinct_signal_colors not in (7, 8):
        errors.append(
            f"direction glyphs must use seven or eight distinct signal colors, found {distinct_signal_colors}"
        )
    if 0 not in palette or 5 not in palette:
        errors.append("palette must include background 0 and tile gray 5")
    if len(palette) not in (9, 10):
        errors.append(f"palette size must be 9 or 10, found {len(palette)}")

    components = _count_components(nonzero) if nonzero else 0
    if components not in (8, 9):
        errors.append(f"nonzero tile field must have 8 or 9 components, found {components}")

    profile = _PROFILE_BY_SIGNATURE.get((height, width, len(palette)))
    if profile is None:
        errors.append(
            f"shape/palette profile {(height, width, len(palette))} is outside canonical profiles"
        )
    contact_mode = "touching_pair" if components == 8 else "separated" if components == 9 else None

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "palette_size": len(palette),
        "profile": profile,
        "contact_mode": contact_mode,
        "components": components,
        "origins": origins,
        "tiles": tiles,
        "directions": directions,
        "blank_count": blank_count,
        "signal_colors": signal_colors,
        "distinct_signal_colors": distinct_signal_colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject scenes that do not express the canonical nine-tile compass grammar."""
    del difficulty, meta
    return list(_analysis(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    """The generated manifold is deliberately the exact canonical profile family."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover every exact declared axis from the realized grid."""
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return {}
    return {
        "scene_profile": analysis["profile"],
        "contact_mode": analysis["contact_mode"],
    }


def _stamp_analysis_tile(
    output: list[list[int]], target: tuple[int, int], tile: dict[str, Any]
) -> None:
    row0, col0 = 3 * target[0], 3 * target[1]
    for dr in range(3):
        for dc in range(3):
            output[row0 + dr][col0 + dc] = tile["cells"][dr][dc]


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror of the synchronized canonical Racket rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid compass input: " + "; ".join(analysis["errors"][:4]))
    output = full_grid(9, 9, 5)
    for direction in _DIRECTION_ORDER:
        _stamp_analysis_tile(output, direction, analysis["directions"][direction])
    return output


def _rival_by_reading_order(grid) -> list[list[int]]:
    """Wrong shortcut: scan glyph tiles and assign slots by input reading order."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid compass input")
    output = full_grid(9, 9, 5)
    tiles = sorted(
        (tile for tile in analysis["tiles"] if tile["direction"] is not None),
        key=lambda tile: tile["origin"],
    )
    for target, tile in zip(_DIRECTION_ORDER, tiles):
        _stamp_analysis_tile(output, target, tile)
    return output


def _rival_by_color_order(grid) -> list[list[int]]:
    """Wrong shortcut: sort glyphs by signal color instead of reading geometry."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid compass input")
    output = full_grid(9, 9, 5)
    tiles = sorted(
        (tile for tile in analysis["tiles"] if tile["direction"] is not None),
        key=lambda tile: (tile["color"], tile["origin"]),
    )
    for target, tile in zip(_DIRECTION_ORDER, tiles):
        _stamp_analysis_tile(output, target, tile)
    return output


def _rival_by_first_signal_cell(grid) -> list[list[int]]:
    """Wrong shortcut: use only the first colored cell's local coordinate."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid compass input")
    output = full_grid(9, 9, 5)
    tiles = sorted(
        (tile for tile in analysis["tiles"] if tile["direction"] is not None),
        key=lambda tile: tile["origin"],
    )
    for tile in tiles:
        signal = [
            (dr, dc)
            for dr in range(3)
            for dc in range(3)
            if tile["cells"][dr][dc] != 5
        ]
        target = min(signal)
        _stamp_analysis_tile(output, target, tile)
    return output


SEMANTIC_RIVALS = {
    "reading_order_slots": _rival_by_reading_order,
    "color_order_slots": _rival_by_color_order,
    "first_signal_cell_slots": _rival_by_first_signal_cell,
}
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _rival_differs(grid, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


def _palette9(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["palette_size"] == 9


def _palette10(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["palette_size"] == 10


def _touching_layout(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["contact_mode"] == "touching_pair"


def _separated_layout(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["contact_mode"] == "separated"


SEMANTIC_WITNESSES = {
    "reading_order_is_not_direction": lambda grid: _rival_differs(grid, "reading_order_slots"),
    "signal_color_is_not_direction": lambda grid: _rival_differs(grid, "color_order_slots"),
    "whole_glyph_not_first_cell": lambda grid: _rival_differs(grid, "first_signal_cell_slots"),
    "palette9_duplicate_signal": _palette9,
    "palette10_unique_signals": _palette10,
    "touching_pair_layout": _touching_layout,
    "separated_layout": _separated_layout,
}
WITNESS_RIVALS = {
    "reading_order_is_not_direction": ["reading_order_slots"],
    "signal_color_is_not_direction": ["color_order_slots"],
    "whole_glyph_not_first_cell": ["first_signal_cell_slots"],
}
BRANCH_WITNESSES = (
    "palette9_duplicate_signal",
    "palette10_unique_signals",
    "touching_pair_layout",
    "separated_layout",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Require a three-demo lesson that covers profiles and kills named rivals."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    profiles = set()
    contacts = set()
    surviving = set(LESSON_COMPETITORS)
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        analysis = _analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} is outside the teaching grammar: {analysis['errors'][:2]}")
            continue
        expected = rule_mirror(demo["input"])
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with the authority mirror")
        profiles.add(analysis["profile"])
        contacts.add(analysis["contact_mode"])
        for name in list(surviving):
            if LESSON_COMPETITORS[name](demo["input"]) != demo["output"]:
                surviving.remove(name)

    if profiles != set(SCENE_PROFILES):
        reasons.append(f"demonstrations miss canonical scene profiles: {sorted(set(SCENE_PROFILES) - profiles)}")
    if contacts != set(CONTACT_MODES):
        reasons.append(f"demonstrations miss contact modes: {sorted(set(CONTACT_MODES) - contacts)}")
    if surviving:
        reasons.append(f"named rival rules survive every demonstration: {sorted(surviving)}")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output")
    else:
        query_errors = self_check(query["input"])
        if query_errors:
            reasons.append(f"query is outside the teaching grammar: {query_errors[:2]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the authority mirror")
    return reasons
