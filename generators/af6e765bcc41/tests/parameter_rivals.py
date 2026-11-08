"""Independent finite semantic bank for af6e765bcc41.

This module deliberately imports neither the production generator nor its
parametric prototype.  Coordinates, connected components and masks are built
directly from the public rule description.  The bank is finite evidence, not a
claim that all conceivable hypotheses have been excluded.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable

Cell = tuple[int, int]
Grid = list[list[int]]


def copy_grid(grid: Grid) -> Grid:
    return [row[:] for row in grid]


def strict_grid(grid) -> Grid:
    if type(grid) is not list or not 3 <= len(grid) <= 30:
        raise ValueError("grid height must be an exact list of length 3..30")
    if type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be an exact list of length 3..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return copy_grid(grid)


def strict_settings(settings) -> str:
    if type(settings) is not dict or set(settings) != {"completion"}:
        raise ValueError("expected exactly completion")
    value = settings["completion"]
    if type(value) is not str or value not in ("none", "single_gap"):
        raise ValueError("completion must be none or single_gap")
    return value


def components(grid: Grid, *, color: int = 7, connectivity: int = 4) -> list[frozenset[Cell]]:
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
               if value == color}
    offsets = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if connectivity == 8:
        offsets += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    found = []
    while pending:
        start = min(pending)
        pending.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in offsets:
                neighbor = (r + dr, c + dc)
                if neighbor in pending:
                    pending.remove(neighbor)
                    queue.append(neighbor)
                    cells.add(neighbor)
        found.append(frozenset(cells))
    return found


def bounds(cells) -> tuple[int, int, int, int]:
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def border(box) -> frozenset[Cell]:
    top, left, bottom, right = box
    return frozenset((r, c) for r in range(top, bottom + 1)
                     for c in range(left, right + 1)
                     if r in (top, bottom) or c in (left, right))


def interior(box) -> frozenset[Cell]:
    top, left, bottom, right = box
    return frozenset((r, c) for r in range(top + 1, bottom)
                     for c in range(left + 1, right))


def dimensions(box):
    return box[2] - box[0] + 1, box[3] - box[1] + 1


def touches_board(box, grid):
    return box[0] == 0 or box[1] == 0 or box[2] == len(grid) - 1 or box[3] == len(grid[0]) - 1


def gap_kind(box, point):
    r, c = point
    top, left, bottom, right = box
    if r in (top, bottom) and c in (left, right):
        return "corner"
    if r == top:
        return "top"
    if r == bottom:
        return "bottom"
    if c == left:
        return "left"
    return "right"


def repair_candidates(grid, *, connectivity=4, zero_only=True, max_missing=1):
    found = []
    for cells in components(grid, connectivity=connectivity):
        box = bounds(cells)
        h, w = dimensions(box)
        if h < 3 or w < 3:
            continue
        rim = border(box)
        absent = rim - cells
        if cells <= rim and 1 <= len(absent) <= max_missing:
            if not zero_only or all(grid[r][c] == 0 for r, c in absent):
                found.append({"cells": cells, "bbox": box, "gaps": absent})
    return found


def repair(grid, completion="single_gap", *, connectivity=4, zero_only=True,
           max_missing=1, select=None):
    out = copy_grid(grid)
    if completion == "none":
        return out
    candidates = repair_candidates(grid, connectivity=connectivity,
                                   zero_only=zero_only, max_missing=max_missing)
    if select is not None:
        candidates = select(candidates)
    for candidate in candidates:
        for r, c in candidate["gaps"]:
            out[r][c] = 7
    return out


def exact_frames(grid, *, connectivity=4, colors=(7,)):
    result = []
    for color in colors:
        for cells in components(grid, color=color, connectivity=connectivity):
            box = bounds(cells)
            h, w = dimensions(box)
            if h >= 3 and w >= 3 and cells == border(box):
                result.append({"cells": cells, "bbox": box, "color": color})
    return result


def fill(grid, *, connectivity=4, colors=(7,), overwrite=False,
         empty_only=False, select=None, bboxes=False):
    out = copy_grid(grid)
    if bboxes:
        frames = [{"cells": cells, "bbox": bounds(cells), "color": 7}
                  for cells in components(grid, connectivity=connectivity)]
    else:
        frames = exact_frames(grid, connectivity=connectivity, colors=colors)
    if select is not None:
        frames = select(frames)
    for frame in frames:
        inside = interior(frame["bbox"])
        if empty_only and any(grid[r][c] != 0 for r, c in inside):
            continue
        for r, c in inside:
            if overwrite or grid[r][c] == 0:
                out[r][c] = 8
    return out


def first_stage(grid, settings):
    return repair(strict_grid(grid), strict_settings(settings))


def model(grid, settings):
    return fill(first_stage(grid, settings))


def intermediate_support(grid, settings):
    original = strict_grid(grid)
    completion = strict_settings(settings)
    candidates = repair_candidates(original) if completion == "single_gap" else []
    middle = repair(original, completion)
    frames = exact_frames(middle)
    fill_mask = sorted({cell for f in frames for cell in interior(f["bbox"])
                        if middle[cell[0]][cell[1]] == 0})
    repair_mask = sorted({cell for c in candidates for cell in c["gaps"]})
    return {"middle": middle, "output": fill(middle), "repair_mask": repair_mask,
            "fill_mask": fill_mask, "repair_candidates": candidates, "frames": frames}


def _gate_repair(grid, completion, predicate):
    return fill(repair(grid, completion, select=lambda rows: [x for x in rows if predicate(x)]))


def _gate_fill(grid, completion, predicate):
    middle = repair(grid, completion)
    return fill(middle, select=lambda rows: [x for x in rows if predicate(x)])


def _original_boxes(grid, completion):
    middle = repair(grid, completion)
    boxes = [row["bbox"] for row in exact_frames(grid)]
    if completion == "single_gap":
        boxes += [row["bbox"] for row in repair_candidates(grid)]
    out = copy_grid(middle)
    for box in boxes:
        for r, c in interior(box):
            if middle[r][c] == 0:
                out[r][c] = 8
    return out


def _until_stable(grid, completion):
    middle = copy_grid(grid)
    # Every pass adds >=1 orange cell if it changes anything, hence total.
    for _ in range(len(grid) * len(grid[0]) + 1):
        changed = repair(middle, completion)
        if changed == middle:
            return fill(middle)
        middle = changed
    raise AssertionError("monotone repair exceeded the finite grid bound")


def _enclosed_regions(grid, completion):
    middle = repair(grid, completion)
    # Orange is a wall; an enclosed region may also hold other nonorange colors.
    reachable = set()
    queue = deque((r, c) for r, row in enumerate(middle) for c, val in enumerate(row)
                  if val != 7 and (r in (0, len(middle)-1) or c in (0, len(row)-1)))
    reachable.update(queue)
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if (0 <= rr < len(middle) and 0 <= cc < len(middle[0])
                    and middle[rr][cc] != 7 and (rr, cc) not in reachable):
                reachable.add((rr, cc))
                queue.append((rr, cc))
    return [[8 if val == 0 and (r, c) not in reachable else val
             for c, val in enumerate(row)] for r, row in enumerate(middle)]


@dataclass(frozen=True)
class Rival:
    name: str
    description: str
    predict: Callable[[Grid, str], Grid]
    scope: str = "plausible_wrong_rule"


RIVALS = [
    Rival("identity", "Leave every cell unchanged.", lambda g, c: copy_grid(g)),
    Rival("setting_none", "Use canonical completion=none for every episode.", lambda g, c: fill(g)),
    Rival("setting_single_gap", "Always complete single gaps.", lambda g, c: fill(repair(g))),
    Rival("fill_before_repair", "Reverse the composition: repair after canonical fill.", lambda g, c: repair(fill(g), c)),
    Rival("fill_original_boxes", "Fill original exact and repair-candidate boxes without redetecting merged objects.", _original_boxes),
    Rival("repair_until_stable", "Repeat gap repair until a fixed point, then fill.", _until_stable,
          "provably_equivalent_one_step_idempotence"),
    Rival("repair_noncorner", "Repair side gaps but leave missing corners.",
          lambda g, c: _gate_repair(g, c, lambda x: gap_kind(x["bbox"], next(iter(x["gaps"]))) != "corner")),
    Rival("repair_corner_only", "Repair only missing corners.",
          lambda g, c: _gate_repair(g, c, lambda x: gap_kind(x["bbox"], next(iter(x["gaps"]))) == "corner")),
    Rival("repair_horizontal_edges", "Repair only gaps on top or bottom edges.",
          lambda g, c: _gate_repair(g, c, lambda x: next(iter(x["gaps"]))[0] in (x["bbox"][0], x["bbox"][2]))),
    Rival("repair_vertical_edges", "Repair only gaps on left or right edges.",
          lambda g, c: _gate_repair(g, c, lambda x: next(iter(x["gaps"]))[1] in (x["bbox"][1], x["bbox"][3]))),
    Rival("repair_square_only", "Only complete square near-frames.",
          lambda g, c: _gate_repair(g, c, lambda x: dimensions(x["bbox"])[0] == dimensions(x["bbox"])[1])),
    Rival("repair_nonsquare_only", "Only complete nonsquare near-frames.",
          lambda g, c: _gate_repair(g, c, lambda x: dimensions(x["bbox"])[0] != dimensions(x["bbox"])[1])),
    Rival("repair_min_side4", "Only complete near-frames at least four cells in both axes.",
          lambda g, c: _gate_repair(g, c, lambda x: min(dimensions(x["bbox"])) >= 4)),
    Rival("repair_max_side5", "Only complete near-frames at most five cells in each axis.",
          lambda g, c: _gate_repair(g, c, lambda x: max(dimensions(x["bbox"])) <= 5)),
    Rival("repair_largest_only", "Complete only candidates with the largest bbox area.",
          lambda g, c: fill(repair(g, c, select=lambda xs: [x for x in xs if
              dimensions(x["bbox"])[0] * dimensions(x["bbox"])[1] == max(
                  (dimensions(y["bbox"])[0] * dimensions(y["bbox"])[1] for y in xs), default=0)]))),
    Rival("skip_border_repair", "Do not repair objects touching the grid boundary.",
          lambda g, c: _gate_repair(g, c, lambda x: not touches_board(x["bbox"], g))),
    Rival("skip_border_fill", "Do not fill exact frames touching the grid boundary.",
          lambda g, c: _gate_fill(g, c, lambda x: not touches_board(x["bbox"], g))),
    Rival("repair_nonzero_gaps", "Repair a missing orange border cell even when occupied by another color.",
          lambda g, c: fill(repair(g, c, zero_only=False))),
    Rival("repair_two_gaps", "Repair connected border components missing one or two zero cells.",
          lambda g, c: fill(repair(g, c, max_missing=2))),
    Rival("fill_only_empty", "Fill an exact orange frame only when its entire interior is zero.",
          lambda g, c: fill(repair(g, c), empty_only=True)),
    Rival("overwrite_interior", "Overwrite every interior cell of exact orange frames with cyan.",
          lambda g, c: fill(repair(g, c), overwrite=True)),
    Rival("all_color_frames", "After orange repair, fill exact frames of every nonzero color.",
          lambda g, c: fill(repair(g, c), colors=tuple(range(1, 10)))),
    Rival("orange_bboxes", "After repair, fill every orange component bbox regardless of its shape.",
          lambda g, c: fill(repair(g, c), bboxes=True)),
    Rival("generic_enclosed_holes", "Fill any zero cells enclosed by orange walls, regardless of object shape.", _enclosed_regions),
    Rival("eight_connectivity", "Use eight-neighbor orange components for repair and filling.",
          lambda g, c: fill(repair(g, c, connectivity=8), connectivity=8)),
    Rival("largest_frame_only", "Fill only exact frames tied for largest bbox area.",
          lambda g, c: fill(repair(g, c), select=lambda xs: [x for x in xs if
              dimensions(x["bbox"])[0] * dimensions(x["bbox"])[1] == max(
                  (dimensions(y["bbox"])[0] * dimensions(y["bbox"])[1] for y in xs), default=0)])),
    Rival("first_frame_only", "Fill the lexicographically first exact orange frame.",
          lambda g, c: fill(repair(g, c), select=lambda xs: sorted(xs, key=lambda x: x["bbox"])[:1])),
    Rival("fill_square_only", "Fill only square exact orange frames.",
          lambda g, c: _gate_fill(g, c, lambda x: dimensions(x["bbox"])[0] == dimensions(x["bbox"])[1])),
    Rival("fill_nonsquare_only", "Fill only nonsquare exact orange frames.",
          lambda g, c: _gate_fill(g, c, lambda x: dimensions(x["bbox"])[0] != dimensions(x["bbox"])[1])),
    Rival("fill_min_side4", "Only fill frames at least four cells in both axes.",
          lambda g, c: _gate_fill(g, c, lambda x: min(dimensions(x["bbox"])) >= 4)),
    Rival("fill_max_side5", "Only fill frames at most five cells in each axis.",
          lambda g, c: _gate_fill(g, c, lambda x: max(dimensions(x["bbox"])) <= 5)),
]

for _side in ("top", "bottom", "left", "right"):
    RIVALS.append(Rival("repair_" + _side + "_only", "Repair only " + _side + " side gaps.",
        lambda g, c, side=_side: _gate_repair(g, c, lambda x:
            gap_kind(x["bbox"], next(iter(x["gaps"]))) == side)))
    RIVALS.append(Rival("repair_except_" + _side, "Repair all eligible gaps except those on the " + _side + " side.",
        lambda g, c, side=_side: _gate_repair(g, c, lambda x:
            gap_kind(x["bbox"], next(iter(x["gaps"]))) != side)))

RIVAL_BY_NAME = {rival.name: rival for rival in RIVALS}


def fit_demos(train, settings):
    """Choose survivors using demonstration pairs only; no query is accepted."""
    completion = strict_settings(settings)
    survivors, rejected, errors = [], {}, {}
    for rival in RIVALS:
        try:
            mismatch = next((i for i, pair in enumerate(train)
                             if rival.predict(copy_grid(pair["input"]), completion) != pair["output"]), None)
            if mismatch is None:
                survivors.append(rival.name)
            else:
                rejected[rival.name] = mismatch
        except Exception as exc:
            errors[rival.name] = type(exc).__name__ + ": " + str(exc)
    return {"survivors": survivors, "rejected_at_demo": rejected, "execution_errors": errors}


def assess_queries(test, settings, fitted):
    """Only after demo fitting, expose query disagreement of frozen survivors."""
    completion = strict_settings(settings)
    divergent, errors = {}, {}
    for name in fitted["survivors"]:
        rival = RIVAL_BY_NAME[name]
        try:
            indexes = [i for i, pair in enumerate(test)
                       if rival.predict(copy_grid(pair["input"]), completion) != pair["output"]]
            if indexes:
                divergent[name] = indexes
        except Exception as exc:
            errors[name] = type(exc).__name__ + ": " + str(exc)
    return {"query_disagreeing_survivors": divergent, "execution_errors": errors}
