"""Standalone input generator and interpreter for compact contour diagrams."""
from collections import Counter, deque
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_2d0172a1"
RULE_TASK_ID = 'ee_2d0172a1'
VERSION = "1.0.0"
SUMMARY = "Classify loops and blobs, merge projected intervals, and draw a compact frame-and-point diagram."
INVARIANTS = ["two colors with strict background majority", "four-connected components",
              "at most one cavity per component", "noncollapsed frame coordinates", "output at most 30 by 30"]
AXES = {}


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def frame_policy(value):
    if type(value) is not str or value not in ("all", "outermost"):
        raise ValueError("frame_policy must be all or outermost")
    return value


def components(points):
    remaining = set(points)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        found = {start}
        todo = deque([start])
        while todo:
            r, c = todo.popleft()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in remaining:
                    remaining.remove(p)
                    found.add(p)
                    todo.append(p)
        result.append(found)
    return result


def cavities(cells, bounds):
    r0, c0, r1, c1 = bounds
    empty = {(r, c) for r in range(r0 - 1, r1 + 2)
             for c in range(c0 - 1, c1 + 2)} - cells
    outside = set()
    todo = deque([(r0 - 1, c0 - 1)])
    while todo:
        p = todo.popleft()
        if p in outside or p not in empty:
            continue
        outside.add(p)
        r, c = p
        todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return components(empty - outside)


def parse(grid):
    if type(grid) is not list or not 5 <= len(grid) <= 30:
        raise ValueError("height must be 5..30 with exact list rows")
    if type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30:
        raise ValueError("width must be 5..30")
    height, width = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("exact integer colors 0..9 required")
    counts = Counter(v for row in grid for v in row)
    if len(counts) != 2 or len(set(counts.values())) != 2:
        raise ValueError("exactly two colors with a strict majority background required")
    background = max(counts, key=counts.get)
    foreground = next(v for v in counts if v != background)
    parts = components((r, c) for r in range(height) for c in range(width)
                       if grid[r][c] == foreground)
    if not 1 <= len(parts) <= 20:
        raise ValueError("one to twenty foreground components required")
    objects = []
    for index, cells in enumerate(parts):
        bounds = [min(r for r, c in cells), min(c for r, c in cells),
                  max(r for r, c in cells), max(c for r, c in cells)]
        holes = cavities(cells, bounds)
        if len(holes) > 1:
            raise ValueError("components with multiple cavities are unsupported")
        objects.append({"id": index, "kind": "frame" if holes else "blob",
                        "bounds": bounds, "cells": sorted(cells),
                        "cavity": sorted(holes[0]) if holes else []})
    for obj in objects:
        obj["containers"] = [other["id"] for other in objects
                             if other["id"] != obj["id"] and other["kind"] == "frame"
                             and set(obj["cells"]).issubset(set(other["cavity"]))]
    return {"height": height, "width": width, "background": background,
            "foreground": foreground, "objects": objects}


def merge_intervals(events):
    groups = []
    for event in sorted(events, key=lambda e: (e["low"], e["high"], e["object_id"], e["role"])):
        if groups and event["low"] <= groups[-1]["high"]:
            groups[-1]["high"] = max(groups[-1]["high"], event["high"])
            groups[-1]["events"].append(event)
        else:
            groups.append({"low": event["low"], "high": event["high"], "events": [event]})
    return groups


def axis_groups(objects, axis):
    events = []
    for obj in objects:
        low, high = obj["bounds"][axis], obj["bounds"][axis + 2]
        if obj["kind"] == "frame":
            for role, value in (("low", low), ("high", high)):
                events.append({"low": value, "high": value, "object_id": obj["id"], "role": role})
        else:
            events.append({"low": low, "high": high, "object_id": obj["id"], "role": "point"})
    return merge_intervals(events)


def coordinate_map(groups):
    return {(event["object_id"], event["role"]): 2 * index
            for index, group in enumerate(groups) for event in group["events"]}


def first_stage(grid, policy="all"):
    frame_policy(policy)
    parsed = parse(grid)
    selected = [obj for obj in parsed["objects"]
                if policy == "all" or obj["kind"] == "blob" or not obj["containers"]]
    row_groups = axis_groups(selected, 0)
    column_groups = axis_groups(selected, 1)
    ys, xs = coordinate_map(row_groups), coordinate_map(column_groups)
    shapes = []
    for obj in selected:
        roles = ("low", "high") if obj["kind"] == "frame" else ("point", "point")
        rows = [ys[(obj["id"], role)] for role in roles]
        cols = [xs[(obj["id"], role)] for role in roles]
        if obj["kind"] == "frame" and (rows[0] == rows[1] or cols[0] == cols[1]):
            raise ValueError("projected intervals collapse a selected frame")
        shapes.append({"id": obj["id"], "kind": obj["kind"], "rows": rows, "cols": cols})
    top = min(s["rows"][0] - (s["kind"] == "blob") for s in shapes)
    left = min(s["cols"][0] - (s["kind"] == "blob") for s in shapes)
    bottom = max(s["rows"][1] + (s["kind"] == "blob") for s in shapes)
    right = max(s["cols"][1] + (s["kind"] == "blob") for s in shapes)
    if max(bottom - top + 1, right - left + 1) > 30:
        raise ValueError("compact output exceeds 30 by 30")
    return {**parsed, "frame_policy": policy, "selected": selected,
            "row_groups": row_groups, "column_groups": column_groups,
            "shapes": shapes, "extent": [top, left, bottom, right]}


def analyze(grid, policy="all"):
    stage = first_stage(grid, policy)
    top, left, bottom, right = stage["extent"]
    output = [[stage["background"]] * (right - left + 1) for _ in range(bottom - top + 1)]
    for shape in stage["shapes"]:
        r0, r1 = shape["rows"]
        c0, c1 = shape["cols"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if shape["kind"] == "blob" or r in (r0, r1) or c in (c0, c1):
                    output[r - top][c - left] = stage["foreground"]
    return {**stage, "output": output}


def solve(grid, policy="all"):
    return analyze(grid, policy)["output"]


def self_check(grid):
    try:
        first_stage(grid, "all")
        first_stage(grid, "outermost")
    except (ValueError, TypeError) as error:
        return [str(error)]
    return []


def rng_for(seed, label):
    digest = hashlib.sha256(f"2d0172a1/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def contour_cells(bounds, cut):
    r0, c0, r1, c1 = bounds
    cells = {(r0, c) for c in range(c0 + cut, c1 - cut + 1)}
    cells.update((r1, c) for c in range(c0 + cut, c1 - cut + 1))
    cells.update((r, c0) for r in range(r0 + cut, r1 - cut + 1))
    cells.update((r, c1) for r in range(r0 + cut, r1 - cut + 1))
    for r, c, dr, dc in ((r0, c0 + cut, 1, -1), (r0 + cut, c1, -1, -1),
                          (r1, c1 - cut, -1, 1), (r1 - cut, c0, 1, 1)):
        cells.add((r, c))
        for _ in range(cut):
            r += dr
            cells.add((r, c))
            c += dc
            cells.add((r, c))
    return cells


# Plans describe geometry only; labels always follow the general interpreter.
PLANS = [
    (30, 30, [(2, 2, 26, 26), (6, 6, 22, 22), (10, 9, 18, 19)],
     [(4, 10, 1, 3), (8, 11, 1, 3), (24, 13, 1, 3), (13, 4, 3, 1),
      (0, 0, 1, 1), (28, 28, 1, 1), (29, 29, 1, 1)]),
    (30, 30, [(2, 1, 25, 13), (8, 4, 18, 10), (4, 17, 22, 28), (6, 20, 8, 24)],
     [(11, 6, 3, 3), (10, 20, 3, 3), (13, 25, 3, 1), (4, 6, 2, 3), (27, 6, 2, 3)]),
    (22, 26, [(1, 1, 20, 24), (5, 5, 15, 14)],
     [(8, 8, 3, 3), (8, 18, 4, 3), (17, 8, 2, 3)]),
    (24, 28, [(2, 2, 21, 25), (6, 5, 16, 12), (6, 16, 16, 22)],
     [(10, 8, 3, 2), (10, 19, 3, 1), (4, 13, 1, 1), (18, 13, 1, 1)]),
    (30, 30, [(1, 1, 28, 28), (5, 5, 24, 24), (9, 9, 20, 20)],
     [(13, 13, 3, 3), (3, 13, 1, 3), (13, 7, 3, 1)]),
    (18, 30, [(1, 1, 15, 13), (5, 4, 11, 10), (3, 19, 13, 28)],
     [(7, 6, 3, 3), (7, 23, 3, 2), (16, 21, 1, 3)]),
    (26, 30, [(1, 1, 24, 13), (5, 4, 18, 10), (3, 17, 22, 28), (8, 20, 16, 25)],
     [(9, 6, 3, 3), (11, 22, 3, 2), (21, 6, 1, 3), (0, 15, 1, 1)]),
    (30, 30, [(0, 0, 29, 29), (4, 4, 25, 25), (8, 8, 21, 21)],
     [(12, 12, 3, 3), (17, 17, 2, 2), (6, 12, 1, 3), (12, 2, 3, 1)]),
    (24, 30, [(2, 2, 20, 20), (7, 7, 15, 15)],
     [(9, 0, 2, 1), (10, 24, 3, 3), (17, 10, 1, 3), (22, 10, 1, 2)]),
    (30, 30, [(0, 0, 28, 28), (5, 4, 22, 12), (5, 17, 22, 25), (10, 7, 16, 9)],
     [(7, 8, 1, 1), (19, 8, 1, 1), (9, 20, 3, 3), (16, 20, 3, 3), (2, 13, 1, 3), (29, 29, 1, 1)]),
]


def sample_profile(seed, label, profile):
    rng = rng_for(seed, label)
    height, width, frames, blobs = PLANS[profile]
    background, foreground = rng.sample(range(10), 2)
    grid = [[background] * width for _ in range(height)]
    occupied = set()
    for bounds in frames:
        r0, c0, r1, c1 = bounds
        # One-cell corner cuts preserve the two-cell clearance to child blobs.
        cut = rng.randrange(min(1, (min(r1 - r0 + 1, c1 - c0 + 1) - 3) // 2) + 1)
        cells = contour_cells(bounds, cut)
        if occupied & cells:
            raise ValueError("sampler contour overlap")
        occupied.update(cells)
    for r0, c0, bh, bw in blobs:
        cells = {(r, c) for r in range(r0, r0 + bh) for c in range(c0, c0 + bw)}
        variant = rng.randrange(3)
        if bh == bw == 3 and variant == 1:
            cells = {(r0 + 1, c) for c in range(c0, c0 + 3)} | {(r, c0 + 1) for r in range(r0, r0 + 3)}
        elif min(bh, bw) >= 2 and variant == 2:
            cells.remove((r0, c0))
        if occupied & cells:
            raise ValueError("sampler blob overlap")
        occupied.update(cells)
    for r, c in occupied:
        grid[r][c] = foreground
    if rng.randrange(2):
        grid.reverse()
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    if profile >= 2 and rng.randrange(2):
        grid = [list(column) for column in zip(*grid)]
    parsed = parse(grid)
    if len(parsed["objects"]) != len(frames) + len(blobs):
        raise ValueError("sampler components touched")
    if sum(o["kind"] == "frame" for o in parsed["objects"]) != len(frames):
        raise ValueError("sampler topology changed")
    for policy in ("all", "outermost"):
        first_stage(grid, policy)
    return grid


def lesson_inputs(seed):
    integer(seed, 0, 2**63 - 1, "seed")
    demos = [sample_profile(seed, f"demo-{i}", i) for i in range(6)]
    queries = [sample_profile(seed, f"query-{i}", i + 6) for i in range(4)]
    rng_for(seed, "complete-query-order").shuffle(queries)
    return demos, queries


def generate(seed, sample_index=0, *, difficulty=None, **overrides):
    integer(seed, 0, 2**63 - 1, "seed")
    integer(sample_index, 0, 2**63 - 1, "sample_index")
    if overrides:
        raise ValueError("no caller overrides are supported")
    return sample_profile(seed, f"base-{sample_index}", sample_index % len(PLANS))
