"""Independent Python semantics and intermediate inspection for 5ccd parametrics."""
from __future__ import annotations

import copy

FINISHES = ("outline", "fill_most_occluded")


def _grid(value):
    if (type(value) is not list or not value or type(value[0]) is not list or not value[0]
            or len(value) > 30 or len(value[0]) > 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("grid must be a rectangular 1..30 exact-integer ARC grid")
    return copy.deepcopy(value)


def positions(grid):
    grid = _grid(grid)
    found = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color != 0:
                found.setdefault(color, []).append((r, c))
    return found


def reading_order(grid):
    return list(positions(grid))


def bbox(cells):
    if not cells:
        raise ValueError("bbox needs cells")
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def border_cells(box):
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)]


def interior_cells(box):
    r0, c0, r1, c1 = box
    return [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]


def _kind(cells):
    first, second = sorted(cells)
    if first[0] == second[0]:
        return "horizontal"
    if first[1] == second[1]:
        return "vertical"
    return "down_right" if first[1] < second[1] else "down_left"


def render_outline(grid, *, order="reading", fill_all=False, keep_markers=False,
                   skip_lines=False, skip_negative=False):
    source = _grid(grid)
    groups = positions(source)
    colors = list(groups)
    if order == "ascending":
        colors.sort()
    elif order == "descending":
        colors.sort(reverse=True)
    elif order != "reading":
        raise ValueError("unknown order")
    out = [[0] * len(source[0]) for _ in source]
    for color in colors:
        cells = groups[color]
        ignored = (len(cells) != 2
                   or (skip_lines and _kind(cells) in {"horizontal", "vertical"})
                   or (skip_negative and _kind(cells) == "down_left"))
        points = cells if ignored else (
            [(r, c) for r in range(bbox(cells)[0], bbox(cells)[2] + 1)
             for c in range(bbox(cells)[1], bbox(cells)[3] + 1)]
            if fill_all else border_cells(bbox(cells)))
        for r, c in points:
            out[r][c] = color
    if keep_markers:
        for color, cells in groups.items():
            for r, c in cells:
                out[r][c] = color
    return out


def validate_pair_grid(grid):
    try:
        source = _grid(grid)
    except ValueError as exc:
        return [str(exc)]
    groups = positions(source)
    errors = []
    if len(groups) != 3:
        errors.append(f"expected exactly 3 nonzero colors, found {len(groups)}")
    for color, cells in groups.items():
        if len(cells) != 2:
            errors.append(f"color {color} has {len(cells)} markers")
    if not any(cell == 0 for row in source for cell in row):
        errors.append("background 0 is absent")
    return errors


def occlusion_intermediate(grid):
    source = _grid(grid)
    groups = positions(source)
    order = list(groups)
    outlined = render_outline(source)
    rows = []
    for index, color in enumerate(order):
        cells = groups[color]
        if len(cells) != 2:
            continue
        box = bbox(cells)
        border = border_cells(box)
        surviving = sum(outlined[r][c] == color for r, c in border)
        rows.append({
            "index": index,
            "color": color,
            "bbox": list(box),
            "perimeter": len(border),
            "area": (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
            "surviving": surviving,
            "loss": len(border) - surviving,
        })
    if not rows:
        return {"reading_order": order, "outlined": outlined, "colors": [],
                "selected_color": None, "selected_index": None}
    selected = max(range(len(rows)), key=lambda i: (rows[i]["loss"], -i))
    return {"reading_order": order, "outlined": outlined, "colors": rows,
            "selected_color": rows[selected]["color"], "selected_index": selected}


def counterfactual_intermediate(grid, selector):
    intermediate = occlusion_intermediate(grid)
    rows = copy.deepcopy(intermediate["colors"])
    if not rows:
        return intermediate
    if selector == "first":
        selected = 0
    elif selector == "second":
        selected = min(1, len(rows) - 1)
    elif selector == "largest_perimeter":
        selected = max(range(len(rows)), key=lambda i: (rows[i]["perimeter"], -i))
    elif selector == "smallest_perimeter":
        selected = min(range(len(rows)), key=lambda i: (rows[i]["perimeter"], i))
    elif selector == "largest_area":
        selected = max(range(len(rows)), key=lambda i: (rows[i]["area"], -i))
    elif selector == "smallest_area":
        selected = min(range(len(rows)), key=lambda i: (rows[i]["area"], i))
    elif selector == "most_surviving":
        selected = max(range(len(rows)), key=lambda i: (rows[i]["surviving"], -i))
    elif selector == "least_surviving":
        selected = min(range(len(rows)), key=lambda i: (rows[i]["surviving"], i))
    elif selector == "latest_max_loss":
        selected = max(range(len(rows)), key=lambda i: (rows[i]["loss"], i))
    else:
        raise ValueError(f"unknown selector: {selector}")
    return {**intermediate, "colors": rows, "selected_color": rows[selected]["color"],
            "selected_index": selected, "selector": selector}


def _finish(intermediate):
    out = copy.deepcopy(intermediate["outlined"])
    color = intermediate["selected_color"]
    if color is None:
        return out
    row = next(item for item in intermediate["colors"] if item["color"] == color)
    for r, c in interior_cells(tuple(row["bbox"])):
        out[r][c] = color
    return out


def solve(grid, finish):
    if finish not in FINISHES:
        raise ValueError(f"unknown finish: {finish}")
    return render_outline(grid) if finish == "outline" else _finish(occlusion_intermediate(grid))


def solve_counterfactual(grid, selector):
    return _finish(counterfactual_intermediate(grid, selector))
