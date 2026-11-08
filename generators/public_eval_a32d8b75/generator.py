"""Public a32d8b75 sidebar-stamp family.

A magenta (6) full-height divider separates a central field from one or two
sidebars.  Each sidebar contains a filled two-color texture swatch, a
monochrome glyph, a corner dot (4), and a two-cell rotation pointer (7).  Swap
the swatch colors, rotate the glyph, replace each retained glyph cell by the
swatch, and dock the resulting sparse stamp at the indicated field corner.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = GENERATOR_ID = "public_eval_a32d8b75"
RULE_TASK_ID = "ee_a32d8b75"
VERSION = "1.0.0"
EXAMPLES_NEEDED = 2
HOME = Path(__file__).resolve().parent
PROGRAM = (HOME / "reference.rkt").read_text() if (HOME / "reference.rkt").is_file() else ""
RULE_HASH = hashlib.sha256(" ".join(PROGRAM.split()).encode()).hexdigest()[:12]
SUMMARY = "Swap each sidebar swatch, rotate its glyph from the bar cue, and corner-dock the textured stamp on the central field."
INVARIANTS = [
    "one widest central field separated by full-height color-6 columns",
    "each sidebar has one two-color swatch, a monochrome glyph, a corner dot and a rotation bar",
    "all input dimensions are at most 30 by 30",
]
AXES = {}
SETTINGS = ("all", "texture_indexed_component")
RIVALS = (
    "opposite_scope",
    "unswapped_texture",
    "solid_texture",
    "no_rotation",
    "fixed_clockwise",
    "fixed_180",
    "anchor_nw",
    "anchor_se",
    "first_component",
    "last_component",
    "largest_component",
    "first_sidebar_only",
)


def _integer(value: object, lo: int, hi: int, name: str) -> int:
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"invalid {name}")
    return value


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{label}:sidebar-stamp-v1".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def check_grid(grid: object) -> list[list[int]]:
    if type(grid) is not list or not grid or len(grid) > 30:
        raise ValueError("grid must have 1..30 rows")
    width = len(grid[0]) if type(grid[0]) is list else 0
    if not 1 <= width <= 30:
        raise ValueError("grid must have 1..30 columns")
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(v) is not int or not 0 <= v <= 9 for v in row):
            raise ValueError("grid colors must be integers 0..9")
    return grid


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not cells:
        raise ValueError("empty cells")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0, c0, _, _ = _bbox(cells)
    return {(r - r0, c - c0) for r, c in cells}


def _components(cells: set[tuple[int, int]], connectivity: int = 4) -> list[set[tuple[int, int]]]:
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    deltas = [
        (dr, dc)
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if (dr or dc) and (connectivity == 8 or abs(dr) + abs(dc) == 1)
    ]
    todo = set(cells)
    result: list[set[tuple[int, int]]] = []
    while todo:
        first = min(todo)
        todo.remove(first)
        component = {first}
        queue = [first]
        while queue:
            r, c = queue.pop()
            for dr, dc in deltas:
                nxt = (r + dr, c + dc)
                if nxt in todo:
                    todo.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def _rotate_cells(cells: set[tuple[int, int]], turns: int) -> set[tuple[int, int]]:
    current = _normalize(cells)
    for _ in range(turns % 4):
        _, _, r1, _ = _bbox(current)
        height = r1 + 1
        current = _normalize({(c, height - 1 - r) for r, c in current})
    return current


def _segments(separator_columns: list[int], width: int) -> list[tuple[int, int]]:
    bounds = [-1, *separator_columns, width]
    return [
        (bounds[i] + 1, bounds[i + 1] - 1)
        for i in range(len(bounds) - 1)
        if bounds[i] + 1 <= bounds[i + 1] - 1
    ]


def _parse_sidebar(sidebar: list[list[int]], source_columns: tuple[int, int]) -> dict:
    height = len(sidebar)
    width = len(sidebar[0])
    horizontal = [r for r, row in enumerate(sidebar) if all(v == 6 for v in row)]
    if len(horizontal) != 2:
        raise ValueError("sidebar requires exactly two full color-6 separator rows")
    top_end, control_split = horizontal
    if top_end < 5 or control_split - top_end != 4 or height - control_split != 4:
        raise ValueError("sidebar control geometry is malformed")
    top = [row[:] for row in sidebar[:top_end]]
    ink = {(r, c) for r, row in enumerate(top) for c, value in enumerate(row) if value not in (0, 6)}
    objects = _components(ink, 8)
    textured = [
        component
        for component in objects
        if len({top[r][c] for r, c in component}) == 2
    ]
    if len(textured) != 1:
        raise ValueError("sidebar needs one connected two-color swatch")
    swatch_cells = textured[0]
    r0, c0, r1, c1 = _bbox(swatch_cells)
    swatch = [row[c0 : c1 + 1] for row in top[r0 : r1 + 1]]
    colors = sorted({value for row in swatch for value in row})
    if len(colors) != 2 or any(value in (0, 6) for value in colors):
        raise ValueError("swatch must be a filled two-color rectangle")
    if any(value not in colors for row in swatch for value in row):
        raise ValueError("swatch bounding box contains background")
    swapped = [
        [colors[1] if value == colors[0] else colors[0] for value in row]
        for row in swatch
    ]
    glyph = ink - swatch_cells
    if not glyph:
        raise ValueError("sidebar glyph is missing")
    glyph_colors = {top[r][c] for r, c in glyph}
    if len(glyph_colors) != 1:
        raise ValueError("glyph must be monochrome")
    glyph = _normalize(glyph)

    dot_box = sidebar[top_end + 1 : control_split]
    bar_box = sidebar[control_split + 1 :]
    dot_positions = [(r, c) for r, row in enumerate(dot_box) for c, value in enumerate(row) if value == 4]
    bar_positions = [(r, c) for r, row in enumerate(bar_box) for c, value in enumerate(row) if value == 7]
    if len(dot_positions) != 1 or len(bar_positions) != 2:
        raise ValueError("sidebar needs one dot and one two-cell bar")
    dot_columns = [c for c in range(width) if any(row[c] != 6 for row in dot_box)]
    bar_columns = [c for c in range(width) if any(row[c] != 6 for row in bar_box)]
    if len(dot_columns) != 3 or len(bar_columns) != 3:
        raise ValueError("control boxes require three interior columns")
    dr, dc = dot_positions[0]
    dc -= min(dot_columns)
    if dr not in (0, 2) or dc not in (0, 2):
        raise ValueError("dot must occupy a control-box corner")
    corner = ("N" if dr == 0 else "S") + ("W" if dc == 0 else "E")
    relative_bar = [(r, c - min(bar_columns)) for r, c in bar_positions]
    if relative_bar[0][1] == relative_bar[1][1]:
        turns = 0 if min(r for r, _ in relative_bar) == 0 else 2
    elif relative_bar[0][0] == relative_bar[1][0]:
        turns = 1 if max(c for _, c in relative_bar) == 2 else 3
    else:
        raise ValueError("bar must be horizontal or vertical")
    return {
        "source_columns": source_columns,
        "swatch": swatch,
        "swapped": swapped,
        "glyph": glyph,
        "components": _components(glyph, 4),
        "corner": corner,
        "turns": turns,
    }


def analyze(grid: list[list[int]]) -> dict:
    check_grid(grid)
    height = len(grid)
    width = len(grid[0])
    separator_columns = [c for c in range(width) if all(grid[r][c] == 6 for r in range(height))]
    if not separator_columns:
        raise ValueError("missing full-height color-6 separator")
    segments = _segments(separator_columns, width)
    if len(segments) not in (2, 3):
        raise ValueError("expected one central field and one or two sidebars")
    field_segment = max(segments, key=lambda part: part[1] - part[0] + 1)
    if sum((b - a) == (field_segment[1] - field_segment[0]) for a, b in segments) != 1:
        raise ValueError("central field must be uniquely widest")
    field = [row[field_segment[0] : field_segment[1] + 1] for row in grid]
    recipes = []
    for segment in segments:
        if segment == field_segment:
            continue
        c0, c1 = segment
        recipes.append(_parse_sidebar([row[c0 : c1 + 1] for row in grid], segment))
    return {"field": field, "field_columns": field_segment, "recipes": recipes}


def _selected_component(recipe: dict, mode: str, rival: str | None) -> set[tuple[int, int]]:
    components = recipe["components"]
    if not components:
        raise ValueError("glyph has no components")
    requested = mode
    if rival == "opposite_scope":
        requested = "texture_indexed_component" if mode == "all" else "all"
    if rival == "first_component":
        return components[0]
    if rival == "last_component":
        return components[-1]
    if rival == "largest_component":
        return max(enumerate(components), key=lambda item: (len(item[1]), -item[0]))[1]
    if requested == "all":
        return recipe["glyph"]
    tile = recipe["swapped"]
    count = sum(value == tile[0][0] for row in tile for value in row)
    if rival == "wrong_texture_count":
        original = recipe["swatch"]
        count = sum(value == original[0][0] for row in original for value in row)
    return components[(count - 1) % len(components)]


def render(info: dict, mode: str = "all", rival: str | None = None) -> list[list[int]]:
    if mode not in SETTINGS:
        raise ValueError("unknown scope")
    if rival is not None and rival not in RIVALS:
        raise ValueError("unknown rival")
    output = deepcopy(info["field"])
    recipes = info["recipes"][:1] if rival == "first_sidebar_only" else info["recipes"]
    field_height = len(output)
    field_width = len(output[0])
    for recipe in recipes:
        tile = recipe["swatch"] if rival == "unswapped_texture" else recipe["swapped"]
        if rival == "solid_texture":
            tile = [[tile[0][0] for _ in row] for row in tile]
        cells = _selected_component(recipe, mode, rival)
        turns = recipe["turns"]
        if rival == "no_rotation":
            turns = 0
        elif rival == "fixed_clockwise":
            turns = 1
        elif rival == "fixed_180":
            turns = 2
        cells = _rotate_cells(cells, turns)
        corner = recipe["corner"]
        if rival == "anchor_nw":
            corner = "NW"
        elif rival == "anchor_se":
            corner = "SE"
        _, _, gr1, gc1 = _bbox(cells)
        glyph_height = gr1 + 1
        glyph_width = gc1 + 1
        tile_height = len(tile)
        tile_width = len(tile[0])
        stamp_height = glyph_height * tile_height
        stamp_width = glyph_width * tile_width
        anchor_row = 0 if corner[0] == "N" else field_height - stamp_height
        anchor_col = 0 if corner[1] == "W" else field_width - stamp_width
        if anchor_row < 0 or anchor_col < 0:
            raise ValueError("stamp does not fit field")
        for glyph_row, glyph_col in cells:
            for tile_row, row in enumerate(tile):
                for tile_col, value in enumerate(row):
                    output[anchor_row + glyph_row * tile_height + tile_row][
                        anchor_col + glyph_col * tile_width + tile_col
                    ] = value
    return output


def solve(grid: list[list[int]], mode: str = "all", rival: str | None = None) -> list[list[int]]:
    return render(analyze(grid), mode, rival)


def _texture(size: int, color_a: int, color_b: int, selected_index: int) -> list[list[int]]:
    # The alternate counts the swapped top-left color, i.e. color_b in this source tile.
    count_b = selected_index + 1
    if count_b >= size * size:
        raise ValueError("texture count exceeds tile")
    flat = [color_a] * (size * size)
    positions = list(range(1, size * size))
    # Spread the second color rather than making an accidental object cue.
    order = positions[::2] + positions[1::2]
    for index in order[:count_b]:
        flat[index] = color_b
    return [flat[r * size : (r + 1) * size] for r in range(size)]


GLYPHS = (
    {(0, 0), (0, 1), (1, 0), (0, 3), (1, 3), (1, 2), (3, 1), (3, 2), (4, 2)},
    {(0, 0), (1, 0), (0, 3), (0, 4), (2, 2), (3, 2), (4, 0), (4, 1)},
    {(0, 1), (1, 1), (0, 4), (1, 4), (2, 3), (3, 3), (4, 0), (4, 1)},
    {(0, 0), (0, 1), (2, 0), (3, 0), (1, 3), (2, 3), (3, 3)},
)


def _paint_object(canvas: list[list[int]], cells: set[tuple[int, int]], top: int, left: int, color: int) -> None:
    for r, c in cells:
        canvas[top + r][left + c] = color


def _sidebar(
    height: int,
    width: int,
    tile: list[list[int]],
    glyph: set[tuple[int, int]],
    glyph_color: int,
    corner: str,
    turns: int,
) -> list[list[int]]:
    top_height = height - 8
    if top_height < 8 or width < 5:
        raise ValueError("sidebar profile too small")
    canvas = [[0] * width for _ in range(height)]
    tile_top = 1
    tile_left = (width - len(tile[0])) // 2
    for r, row in enumerate(tile):
        for c, value in enumerate(row):
            canvas[tile_top + r][tile_left + c] = value
    _, _, gr1, gc1 = _bbox(glyph)
    glyph_height, glyph_width = gr1 + 1, gc1 + 1
    glyph_top = top_height - glyph_height - 1
    glyph_left = (width - glyph_width) // 2
    if glyph_top <= tile_top + len(tile):
        raise ValueError("tile and glyph overlap")
    _paint_object(canvas, glyph, glyph_top, glyph_left, glyph_color)
    for c in range(width):
        canvas[top_height][c] = 6
        canvas[top_height + 4][c] = 6
    interior_left = (width - 3) // 2
    for r in range(top_height + 1, top_height + 4):
        canvas[r] = [6] * width
        for c in range(interior_left, interior_left + 3):
            canvas[r][c] = 0
    for r in range(top_height + 5, height):
        canvas[r] = [6] * width
        for c in range(interior_left, interior_left + 3):
            canvas[r][c] = 0
    dot_r = top_height + 1 + (0 if corner[0] == "N" else 2)
    dot_c = interior_left + (0 if corner[1] == "W" else 2)
    canvas[dot_r][dot_c] = 4
    if turns == 0:
        bar = ((0, 1), (1, 1))
    elif turns == 1:
        bar = ((1, 1), (1, 2))
    elif turns == 2:
        bar = ((1, 1), (2, 1))
    elif turns == 3:
        bar = ((1, 0), (1, 1))
    else:
        raise ValueError("turns must be 0..3")
    for r, c in bar:
        canvas[top_height + 5 + r][interior_left + c] = 7
    return canvas


def _field(seed: int, label: str, height: int, width: int, forbidden: set[int]) -> list[list[int]]:
    rng = _rng(seed, label + ":field")
    palette = [color for color in range(10) if color not in forbidden]
    colors = rng.sample(palette, 3)
    row_band = rng.choice((2, 3, 4, 5))
    col_band = rng.choice((3, 4, 5, 6))
    phase = rng.randrange(3)
    field = [
        [colors[((r // row_band) + (c // col_band) + phase) % 3] for c in range(width)]
        for r in range(height)
    ]
    # Add one preserved rectangular island so empty glyph blocks are visibly transparent.
    rh = max(2, height // 5)
    rw = max(2, width // 5)
    r0 = rng.randrange(0, height - rh + 1)
    c0 = rng.randrange(0, width - rw + 1)
    island = colors[(phase + 1) % 3]
    for r in range(r0, r0 + rh):
        for c in range(c0, c0 + rw):
            field[r][c] = island
    return field


def _scene(seed: int, label: str, profile: dict) -> list[list[int]]:
    rng = _rng(seed, label)
    height = profile["height"]
    total_width = profile["width"]
    sides = profile["sides"]
    sidebar_width = 5
    field_width = total_width - len(sides) * (sidebar_width + 1)
    if field_width < 10:
        raise ValueError("field too narrow")
    used = {0, 6}
    recipes = []
    for side_index, side in enumerate(sides):
        colors = [c for c in range(1, 10) if c != 6 and c not in used]
        color_a, color_b, glyph_color = rng.sample(colors, 3)
        used.update((color_a, color_b, glyph_color))
        size = profile.get("tile_sizes", (2,))[side_index % len(profile.get("tile_sizes", (2,)))]
        selected = profile.get("selected", (0,))[side_index % len(profile.get("selected", (0,)))]
        tile = _texture(size, color_a, color_b, selected)
        glyph = set(GLYPHS[profile.get("glyphs", (0,))[side_index % len(profile.get("glyphs", (0,)))]] )
        corners = profile.get("corners", ("NW",))
        turns = profile.get("turns", (0,))
        corner = corners[side_index % len(corners)]
        turn = turns[side_index % len(turns)]
        recipes.append((side, _sidebar(height, sidebar_width, tile, glyph, glyph_color, corner, turn)))
    field = _field(seed, label, height, field_width, {6})
    left = next((panel for side, panel in recipes if side == "L"), None)
    right = next((panel for side, panel in recipes if side == "R"), None)
    rows = []
    for r in range(height):
        row = []
        if left is not None:
            row.extend(left[r]); row.append(6)
        row.extend(field[r])
        if right is not None:
            row.append(6); row.extend(right[r])
        rows.append(row)
    info = analyze(rows)
    if len(rows) != height or len(rows[0]) != total_width:
        raise RuntimeError("profile dimensions changed")
    for mode in SETTINGS:
        correct = render(info, mode)
        if correct == field:
            raise RuntimeError("stamp has no effect")
        for rival in RIVALS:
            render(info, mode, rival)
    return rows


DEMO_PROFILES = (
    {"height": 20, "width": 28, "sides": ("L",), "tile_sizes": (2,), "selected": (0,), "glyphs": (0,), "corners": ("NW",), "turns": (0,)},
    {"height": 24, "width": 30, "sides": ("L", "R"), "tile_sizes": (2, 2), "selected": (1, 2), "glyphs": (1, 2), "corners": ("NE", "SW"), "turns": (1, 3)},
    {"height": 18, "width": 26, "sides": ("R",), "tile_sizes": (3,), "selected": (2,), "glyphs": (3,), "corners": ("SE",), "turns": (2,)},
    {"height": 22, "width": 29, "sides": ("L",), "tile_sizes": (3,), "selected": (1,), "glyphs": (2,), "corners": ("SW",), "turns": (3,)},
    {"height": 26, "width": 30, "sides": ("R",), "tile_sizes": (2,), "selected": (0,), "glyphs": (1,), "corners": ("NE",), "turns": (1,)},
    {"height": 21, "width": 27, "sides": ("L",), "tile_sizes": (2,), "selected": (2,), "glyphs": (3,), "corners": ("SE",), "turns": (2,)},
)
QUERY_PROFILES = (
    {"height": 19, "width": 27, "sides": ("R",), "tile_sizes": (3,), "selected": (0,), "glyphs": (0,), "corners": ("NW",), "turns": (3,)},
    {"height": 23, "width": 30, "sides": ("L", "R"), "tile_sizes": (2, 2), "selected": (2, 1), "glyphs": (3, 0), "corners": ("NW", "SE"), "turns": (2, 0)},
    {"height": 27, "width": 30, "sides": ("L",), "tile_sizes": (3,), "selected": (1,), "glyphs": (1,), "corners": ("SW",), "turns": (1,)},
    {"height": 30, "width": 30, "sides": ("L", "R"), "tile_sizes": (2, 2), "selected": (0, 2), "glyphs": (2, 3), "corners": ("NE", "SW"), "turns": (0, 3)},
)


@lru_cache(maxsize=128)
def inputs(seed: int) -> tuple[list[list[int]], ...]:
    _integer(seed, 0, 2**63 - 1, "seed")
    demos = [_scene(seed, f"demo.{i}", profile) for i, profile in enumerate(DEMO_PROFILES)]
    order = list(range(4))
    _rng(seed, "query-profile-order").shuffle(order)
    queries = [_scene(seed, f"query.{slot}", QUERY_PROFILES[index]) for slot, index in enumerate(order)]
    bank = demos + queries
    if len({repr(grid) for grid in bank}) != 10:
        raise RuntimeError("duplicate generated input")
    # The first two examples must teach both settings and all declared shortcuts.
    for mode in SETTINGS:
        wanted = [solve(grid, mode) for grid in bank[:2]]
        for rival in RIVALS:
            if all(solve(grid, mode, rival) == output for grid, output in zip(bank[:2], wanted)):
                raise RuntimeError(f"teaching collision: {mode}/{rival}")
    return tuple(deepcopy(bank))


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides) -> list[list[int]]:
    if overrides:
        raise TypeError("no override axes")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("invalid difficulty")
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(sample_index, 0, 2**31 - 1, "sample_index")
    bank_seed = seed + sample_index // 10
    return deepcopy(inputs(bank_seed)[sample_index % 10])


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    return solve(grid, "all")


def self_check(grid: list[list[int]]) -> list[str]:
    try:
        analyze(grid)
        return []
    except (ValueError, IndexError) as exc:
        return [str(exc)]
