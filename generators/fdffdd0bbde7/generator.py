"""Generator for the color-keyed stencil-library ARC task.

The top library contains 2--4 panels separated by full-height color-9
columns.  Each panel has one color-9 anchor and one colored stencil.  A blank
row separates the library from body seeds.  The unchanged canonical Racket
rule stamps the matching color's anchor-relative offsets at every body seed,
clipping at the grid boundary and emitting the stamps on a blank output.

The six advertised controls are exact and recoverable from returned pixels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fdffdd0bbde7"
TASK_ID = GENERATOR_ID
RULE_HASH = "66637f26ea98"
VERSION = "4.0.0"
SUMMARY = (
    "A 3--6 row top library holds 2--4 color-keyed stencils, each "
    "defined relative to its visible color-9 anchor and separated by full-height "
    "9-columns.  A blank row precedes 4--8 body seeds.  On a blank output, "
    "stamp each seed's matching anchor-relative stencil, clipping in-bounds."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "the first blank row separates a 3..6-row library from the body",
    "2..4 panels are separated by single full-library-height color-9 columns",
    "each panel has one 9 anchor, one unique non-9 color, and 1..5 stencil cells",
    "the body has 4..8 seeds, uses every library color, and uses no unknown color",
    "every body seed contributes at least one in-bounds output cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted toward canonical 12..13", "valid": "10..16"},
    "grid_w": {"type": "int", "default": "weighted toward canonical 17", "valid": "13..21"},
    "lib_h": {"type": "int", "default": "weighted toward canonical 5", "valid": "3..6"},
    "n_entries": {"type": "int", "default": "weighted toward canonical 3", "valid": "2..4"},
    "stencil_size": {"type": "int", "default": "difficulty-weighted 1..5", "valid": "1..5"},
    "n_body": {"type": "int", "default": "difficulty-weighted 4..8", "valid": "4..8"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_BOUNDS = {
    "grid_h": (10, 16),
    "grid_w": (13, 21),
    "lib_h": (3, 6),
    "n_entries": (2, 4),
    "stencil_size": (1, 5),
    "n_body": (4, 8),
}


def _weighted_int(ctx, name, preferred):
    lo, hi = _BOUNDS[name]
    options = list(range(lo, hi + 1))
    for value, weight in preferred:
        options.extend([value] * weight)
    return ctx.draw_choice(name, options)


def _panel_spans(width, count, rng):
    usable = width - (count - 1)
    base, remainder = divmod(usable, count)
    widths = [base + (index < remainder) for index in range(count)]
    rng.shuffle(widths)
    if min(widths) < 2:
        raise ValueError("grid_w cannot fit the requested number of panels")
    spans = []
    dividers = []
    col = 0
    for index, panel_width in enumerate(widths):
        spans.append((col, col + panel_width - 1))
        col += panel_width
        if index < count - 1:
            dividers.append(col)
            col += 1
    if col != width:
        raise RuntimeError("panel partition did not consume the requested width")
    return spans, dividers


def _center(span, lib_h):
    return lib_h // 2, (span[0] + span[1]) // 2


def _off_center_anchor(span, lib_h, rng, *, lower_row=False):
    center_row, center_col = _center(span, lib_h)
    rows = [row for row in range(lib_h) if row != center_row]
    if lower_row:
        rows = [row for row in rows if row > center_row] or rows
    cols = [col for col in range(span[0], span[1] + 1) if col != center_col]
    if not rows or not cols:
        raise ValueError("panel is too small to place a bi-axially off-center anchor")
    return rng.choice(rows), rng.choice(cols)


def _stencil_cells(anchor, span, lib_h):
    return [(row, col) for row in range(lib_h)
            for col in range(span[0], span[1] + 1)
            if (row, col) != anchor]


def _parse_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be literal integer ARC colors 0..9")
    separator = next((row for row, values in enumerate(grid) if all(value == 0 for value in values)), None)
    if separator is None:
        raise ValueError("missing blank separator row")
    dividers = [col for col in range(width) if all(grid[row][col] == 9 for row in range(separator))]
    spans = []
    start = 0
    for divider in dividers + [width]:
        if divider > start:
            spans.append((start, divider - 1))
        start = divider + 1
    entries = []
    for c1, c2 in spans:
        anchors = [(row, col) for row in range(separator) for col in range(c1, c2 + 1)
                   if grid[row][col] == 9]
        colors = sorted({grid[row][col] for row in range(separator) for col in range(c1, c2 + 1)
                         if grid[row][col] not in (0, 9)})
        if len(anchors) != 1:
            raise ValueError(f"panel {c1}-{c2} has {len(anchors)} anchors")
        if len(colors) != 1:
            raise ValueError(f"panel {c1}-{c2} has {len(colors)} stencil colors")
        anchor = anchors[0]
        color = colors[0]
        offsets = tuple(sorted((row - anchor[0], col - anchor[1])
                               for row in range(separator) for col in range(c1, c2 + 1)
                               if grid[row][col] == color))
        entries.append({"span": (c1, c2), "anchor": anchor,
                        "color": color, "offsets": offsets})
    body = tuple((row, col, grid[row][col]) for row in range(separator + 1, len(grid))
                 for col in range(width) if grid[row][col] != 0)
    return {"height": len(grid), "width": width, "separator": separator,
            "dividers": tuple(dividers), "spans": tuple(spans),
            "entries": tuple(entries), "body": body}


def _paint(parsed, offsets_by_color):
    output = full_grid(parsed["height"], parsed["width"], 0)
    for row, col, color in parsed["body"]:
        for dr, dc in offsets_by_color[color]:
            rr, cc = row + dr, col + dc
            if 0 <= rr < parsed["height"] and 0 <= cc < parsed["width"]:
                output[rr][cc] = color
    return output


def _assumed_anchor_output(grid, *, use_actual_row, use_actual_col):
    parsed = _parse_grid(grid)
    offsets = {}
    for entry in parsed["entries"]:
        center = _center(entry["span"], parsed["separator"])
        anchor = (
            entry["anchor"][0] if use_actual_row else center[0],
            entry["anchor"][1] if use_actual_col else center[1],
        )
        c1, c2 = entry["span"]
        offsets[entry["color"]] = tuple(sorted(
            (row - anchor[0], col - anchor[1])
            for row in range(parsed["separator"])
            for col in range(c1, c2 + 1)
            if grid[row][col] == entry["color"]
        ))
    return _paint(parsed, offsets)


def _panel_center_anchor_output(grid):
    """Rival: ignore both visible anchor coordinates."""
    return _assumed_anchor_output(grid, use_actual_row=False, use_actual_col=False)


def _center_row_anchor_output(grid):
    """Rival: use the visible anchor column but assume a centered row."""
    return _assumed_anchor_output(grid, use_actual_row=False, use_actual_col=True)


def _center_col_anchor_output(grid):
    """Rival: use the visible anchor row but assume a centered column."""
    return _assumed_anchor_output(grid, use_actual_row=True, use_actual_col=False)


def _has_biaxial_off_center_anchors(grid):
    parsed = _parse_grid(grid)
    return all(
        entry["anchor"][0] != _center(entry["span"], parsed["separator"])[0]
        and entry["anchor"][1] != _center(entry["span"], parsed["separator"])[1]
        for entry in parsed["entries"]
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be a literal integer, not {type(value).__name__}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    grid_h = _weighted_int(ctx, "grid_h", ((12, 18), (13, 18)))
    grid_w = _weighted_int(ctx, "grid_w", ((17, 36),))
    lib_h = _weighted_int(ctx, "lib_h", ((5, 32),))
    n_entries = _weighted_int(ctx, "n_entries", ((3, 32),))
    if difficulty == "easy":
        stencil_pref = ((2, 22), (1, 8))
        body_pref = ((4, 22), (5, 8))
    elif difficulty == "hard":
        stencil_pref = ((4, 22), (5, 8))
        body_pref = ((7, 18), (8, 12))
    else:
        stencil_pref = ((3, 22), (2, 6), (4, 6))
        body_pref = ((5, 18), (6, 12))
    stencil_size = _weighted_int(ctx, "stencil_size", stencil_pref)
    n_body = _weighted_int(ctx, "n_body", body_pref)

    spans, dividers = _panel_spans(grid_w, n_entries, ctx.draw_rng("panel_width_order"))
    grid = full_grid(grid_h, grid_w, 0)
    for divider in dividers:
        for row in range(lib_h):
            grid[row][divider] = 9

    colors = ctx.draw_rng("palette").sample(list(range(1, 9)), n_entries)
    entries = {}
    rival_entries = {
        "panel_center_anchor": {},
        "center_row_anchor": {},
        "center_col_anchor": {},
    }
    for index, (span, color) in enumerate(zip(spans, colors)):
        anchor = _off_center_anchor(
            span, lib_h, ctx.draw_rng(f"anchor_{index}"), lower_row=(index == 0)
        )
        ar, ac = anchor
        grid[ar][ac] = 9
        candidates = _stencil_cells(anchor, span, lib_h)
        if len(candidates) < stencil_size:
            raise RuntimeError("panel cannot fit the requested stencil size")
        # Every library color is exercised in the body.  Reserve one offset that
        # can land in-bounds from the shallowest legal body, then draw the rest
        # from the full panel so broad stencils remain represented.
        max_downward = grid_h - lib_h - 2
        placeable = [cell for cell in candidates if cell[0] - ar <= max_downward]
        if not placeable:
            raise RuntimeError("panel has no body-placeable stencil cell")
        stencil_rng = ctx.draw_rng(f"stencil_{index}")
        first_cell = stencil_rng.choice(placeable)
        remaining = [cell for cell in candidates if cell != first_cell]
        cells = [first_cell]
        cells.extend(stencil_rng.sample(remaining, stencil_size - 1))
        offsets = []
        for row, col in cells:
            grid[row][col] = color
            offsets.append((row - ar, col - ac))
        entries[color] = tuple(sorted(offsets))
        center_row, center_col = _center(span, lib_h)
        rival_entries["panel_center_anchor"][color] = tuple(sorted(
            (row - center_row, col - center_col) for row, col in cells
        ))
        rival_entries["center_row_anchor"][color] = tuple(sorted(
            (row - center_row, col - ac) for row, col in cells
        ))
        rival_entries["center_col_anchor"][color] = tuple(sorted(
            (row - ar, col - center_col) for row, col in cells
        ))

    body_colors = list(colors)
    color_rng = ctx.draw_rng("body_colors")
    while len(body_colors) < n_body:
        body_colors.append(color_rng.choice(colors))
    tail = body_colors[1:]
    color_rng.shuffle(tail)
    body_colors = [body_colors[0]] + tail

    body_rows = range(lib_h + 1, grid_h)
    witness = (lib_h + 1, grid_w // 2)
    all_spots = [(row, col) for row in body_rows for col in range(grid_w)]

    def stamp_cells(spot, offsets):
        row, col = spot
        return {
            (row + dr, col + dc)
            for dr, dc in offsets
            if 0 <= row + dr < grid_h and 0 <= col + dc < grid_w
        }

    witness_color = body_colors[0]
    witness_true = stamp_cells(witness, entries[witness_color])
    protected_witness_cells = {}
    for rival_name, offsets_by_color in rival_entries.items():
        witness_rival = stamp_cells(witness, offsets_by_color[witness_color])
        disagreement = witness_true ^ witness_rival
        if not disagreement:
            raise RuntimeError(f"off-center witness does not distinguish {rival_name}")
        protected_witness_cells[rival_name] = min(disagreement)

    spot_rng = ctx.draw_rng("body_positions")
    positions = [witness]
    used = {witness}
    for color in body_colors[1:]:
        valid = []
        for spot in all_spots:
            if spot in used:
                continue
            true_cells = stamp_cells(spot, entries[color])
            if not true_cells:
                continue
            contaminated = False
            for rival_name, offsets_by_color in rival_entries.items():
                rival_cells = stamp_cells(spot, offsets_by_color[color])
                if protected_witness_cells[rival_name] in (true_cells | rival_cells):
                    contaminated = True
                    break
            if contaminated:
                continue
            valid.append(spot)
        if not valid:
            raise RuntimeError(
                f"no lawful body position preserves the isolated witness for color {color}"
            )
        chosen = spot_rng.choice(valid)
        positions.append(chosen)
        used.add(chosen)

    for (row, col), color in zip(positions, body_colors):
        grid[row][col] = color

    issues = self_check(grid)
    if issues:
        raise RuntimeError(f"constructive generator emitted an invalid grid: {issues}")
    return grid


def observe_overrides(grid):
    """Recover every exact axis from returned pixels."""
    parsed = _parse_grid(grid)
    sizes = {len(entry["offsets"]) for entry in parsed["entries"]}
    if len(sizes) != 1:
        raise ValueError(f"generated stencil sizes are not uniform: {sorted(sizes)}")
    return {
        "grid_h": parsed["height"],
        "grid_w": parsed["width"],
        "lib_h": parsed["separator"],
        "n_entries": len(parsed["entries"]),
        "stencil_size": sizes.pop(),
        "n_body": len(parsed["body"]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    try:
        parsed = _parse_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors = []
    height, width = parsed["height"], parsed["width"]
    if not _BOUNDS["grid_h"][0] <= height <= _BOUNDS["grid_h"][1]:
        errors.append(f"grid_h={height} outside 10..16")
    if not _BOUNDS["grid_w"][0] <= width <= _BOUNDS["grid_w"][1]:
        errors.append(f"grid_w={width} outside 13..21")
    separator = parsed["separator"]
    if not _BOUNDS["lib_h"][0] <= separator <= _BOUNDS["lib_h"][1]:
        errors.append(f"lib_h={separator} outside 3..6")
    if separator >= height - 1:
        errors.append("missing body below separator")
    if any(all(value == 0 for value in grid[row]) for row in range(separator)):
        errors.append("blank row inside library")
    if len(parsed["dividers"]) != len(parsed["entries"]) - 1:
        errors.append("library must use one divider between adjacent panels")
    if any(c2 - c1 + 1 < 2 for c1, c2 in parsed["spans"]):
        errors.append("each panel must be at least two columns wide")
    if not _BOUNDS["n_entries"][0] <= len(parsed["entries"]) <= _BOUNDS["n_entries"][1]:
        errors.append(f"n_entries={len(parsed['entries'])} outside 2..4")

    colors = [entry["color"] for entry in parsed["entries"]]
    if len(colors) != len(set(colors)):
        errors.append("panel colors must be unique")
    for entry in parsed["entries"]:
        size = len(entry["offsets"])
        if not _BOUNDS["stencil_size"][0] <= size <= _BOUNDS["stencil_size"][1]:
            errors.append(f"color {entry['color']} stencil size {size} outside 1..5")

    body = parsed["body"]
    if not _BOUNDS["n_body"][0] <= len(body) <= _BOUNDS["n_body"][1]:
        errors.append(f"n_body={len(body)} outside 4..8")
    body_colors = {color for _, _, color in body}
    entry_colors = set(colors)
    unknown = sorted(body_colors - entry_colors)
    if unknown:
        errors.append(f"body uses colors without library entries: {unknown}")
    missing = sorted(entry_colors - body_colors)
    if missing:
        errors.append(f"library colors absent from body: {missing}")
    offsets_by_color = {entry["color"]: entry["offsets"] for entry in parsed["entries"]}
    for row, col, color in body:
        if color not in offsets_by_color:
            continue
        if not any(0 <= row + dr < height and 0 <= col + dc < width
                   for dr, dc in offsets_by_color[color]):
            errors.append(f"body seed {(row, col)} contributes no in-bounds stamp")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the lawful generator manifold, including canonical pairs."""
    return self_check(grid)


SEMANTIC_WITNESSES = {"biaxial_off_center_anchors": _has_biaxial_off_center_anchors}
SEMANTIC_RIVALS = {
    "panel_center_anchor": _panel_center_anchor_output,
    "center_row_anchor": _center_row_anchor_output,
    "center_col_anchor": _center_col_anchor_output,
}
WITNESS_RIVALS = {
    "biaxial_off_center_anchors": [
        "panel_center_anchor", "center_row_anchor", "center_col_anchor"
    ]
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
