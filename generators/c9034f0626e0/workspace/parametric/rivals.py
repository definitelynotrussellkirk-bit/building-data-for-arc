"""Independent finite rivals for marker-anchored lattice lessons.

These functions do not import the sampler, its mirror, or its rule builder.
They are diagnostics over valid one-marker ARC inputs, not label authorities.
The intended setting is omitted from ``rival_predictions``. Identical rival
outputs may share a grid object; callers should treat predictions as values.
"""
from __future__ import annotations

from copy import deepcopy

MODES = ("period2", "period3", "ray_size")
INTENDED_NAMES = {
    "period2": "fixed_period_2",
    "period3": "fixed_period_3",
    "ray_size": "ray_size_even_2_odd_3",
}

# These produced fit-demos/disagree-query counterexamples in the bounded
# seeds 0,17,44 / demos 2,3 audit. They are a selection-gate starting point;
# the complete predictor set below also retains no-findings hypotheses.
EMPIRICAL_RISK_RIVALS = (
    "component_count_parity",
    "east_gray_total_parity",
    "first_scan_size_parity",
    "gray_total_parity",
    "largest_size_parity",
    "last_east_size_parity",
    "nearest_size_parity",
    "origin_residues",
    "row_gray_total_parity",
    "selected_bbox_area_parity",
    "selected_height_parity",
    "selected_size_8_parity",
    "selected_width_parity",
    "west_first_size_parity",
)


def _marker(grid):
    markers = [(r, c, value) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value not in (0, 5)]
    if len(markers) != 1:
        raise ValueError("rival inputs require exactly one nonzero, non-gray marker")
    return markers[0]


def _components(grid, diagonal=False):
    unseen = {(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value == 5}
    directions = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                  if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        points, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in unseen:
                    unseen.remove(point)
                    points.add(point)
                    todo.append(point)
        found.append(points)
    return found


def rival_features(grid):
    """Return independently measured component and ray features."""
    mr, mc, color = _marker(grid)
    parts = _components(grid)
    east = [c for c in range(mc + 1, len(grid[0])) if grid[mr][c] == 5]
    west = [c for c in range(mc - 1, -1, -1) if grid[mr][c] == 5]

    def part_at(r, c):
        return next(part for part in parts if (r, c) in part)

    selected = part_at(mr, east[0]) if east else set()
    selected8 = next((part for part in _components(grid, diagonal=True)
                      if east and (mr, east[0]) in part), set())
    rows = [r for r, c in selected]
    cols = [c for r, c in selected]
    height, width = ((max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)
                     if selected else (0, 0))
    run = 0
    if east:
        while east[0] + run < len(grid[0]) and grid[mr][east[0] + run] == 5:
            run += 1
    nearest = (min(parts, key=lambda part: (
        min(abs(r - mr) + abs(c - mc) for r, c in part), min(part)))
        if parts else set())
    return {
        "marker": [mr, mc, color],
        "selected_size": len(selected),
        "selected_size_8": len(selected8),
        "selected_height": height,
        "selected_width": width,
        "selected_bbox_area": height * width,
        "ray_run": run,
        "east_gray_total": len(east),
        "row_gray_total": sum(value == 5 for value in grid[mr]),
        "gray_total": sum(map(len, parts)),
        "component_count": len(parts),
        "first_scan_size": len(parts[0]) if parts else 0,
        "largest_size": max(map(len, parts), default=0),
        "smallest_size": min(map(len, parts), default=0),
        "nearest_size": len(nearest),
        "last_east_size": len(part_at(mr, east[-1])) if east else 0,
        "west_first_size": len(part_at(mr, west[0])) if west else 0,
    }


def _paint(grid, period, *, origin=False, coverage="ordered", overwrite=False):
    mr, mc, color = _marker(grid)
    if origin:
        mr, mc = 0, 0
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            row_match = r % period == mr % period
            col_match = c % period == mc % period
            match = row_match and col_match
            if coverage == "row":
                match = row_match
            elif coverage == "column":
                match = col_match
            elif coverage == "sum":
                match = (r + c) % period == (mr + mc) % period
            elif coverage == "all":
                match = True
            if match and (overwrite or value == 0):
                output[r][c] = color
    return output


def rival_predictions(grid, mode):
    """Return the audit's finite counter-rule name -> predicted output mapping."""
    if type(mode) is not str or mode not in MODES:
        raise ValueError("unknown lattice rule for rival predictions")
    info = rival_features(grid)
    period = (2 if mode == "period2" else 3 if mode == "period3"
              else 2 + info["selected_size"] % 2)
    lattice = {2: _paint(grid, 2), 3: _paint(grid, 3)}
    predictions = {
        "fixed_period_2": lattice[2],
        "fixed_period_3": lattice[3],
        "ray_size_even_2_odd_3": lattice[2 + info["selected_size"] % 2],
        "ray_size_reversed": lattice[3 - info["selected_size"] % 2],
        "origin_residues": _paint(grid, period, origin=True),
        "row_only": _paint(grid, period, coverage="row"),
        "column_only": _paint(grid, period, coverage="column"),
        "sum_residue": _paint(grid, period, coverage="sum"),
        "fill_all": _paint(grid, period, coverage="all"),
        "overwrite_gray": _paint(grid, period, overwrite=True),
        "identity": deepcopy(grid),
    }
    for feature in (
        "selected_size_8", "selected_height", "selected_width", "selected_bbox_area",
        "ray_run", "east_gray_total", "row_gray_total", "gray_total", "component_count",
        "first_scan_size", "largest_size", "smallest_size", "nearest_size",
        "last_east_size", "west_first_size",
    ):
        predictions[feature + "_parity"] = lattice[2 + info[feature] % 2]
    del predictions[INTENDED_NAMES[mode]]
    return predictions


def fitting_rivals(demos, mode):
    """List counter-rules fitting every supplied, labeled demonstration."""
    if not demos:
        raise ValueError("at least one labeled demonstration is required")
    survivors = None
    for pair in demos:
        fitting = {name for name, output in rival_predictions(pair["input"], mode).items()
                   if output == pair["output"]}
        survivors = fitting if survivors is None else survivors & fitting
        if not survivors:
            break
    return sorted(survivors)
