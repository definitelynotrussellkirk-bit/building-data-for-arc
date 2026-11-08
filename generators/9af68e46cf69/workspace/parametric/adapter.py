"""Opt-in enclosure ranking with an unchanged canonical default.

Python labels are diagnostic claims. Native qualification executes the exact
adjacent Racket programs independently. Input slots never depend on settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, load_selected_generator, public_challenge_bytes

TASK_ID = "9af68e46cf69"
VERSION = "largest-enclosed-region-v1"
_HOME = Path(__file__).resolve().parent
_BASE, _BASE_SOURCE, _BASE_SHA256 = load_selected_generator(TASK_ID, root=find_root(__file__))
_ALL = "all_enclosed"
_LARGEST = "largest_enclosed_region"


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"selection"}
            or type(settings["selection"]) is not str
            or settings["selection"] not in (_ALL, _LARGEST)):
        raise ValueError("settings must contain only selection=all_enclosed or largest_enclosed_region")
    return settings["selection"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    selection = _setting(settings)
    return (_HOME / ("canonical.rkt" if selection == _ALL else "largest.rkt")).read_text(encoding="utf-8")


def _strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty list of rows with dimensions at most 30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in (1, 9) for cell in row) for row in grid):
        raise ValueError("grid must be rectangular with literal colors 1 and 9")


def _contained(region, box):
    t, l, b, r = box
    return bool(region) and all(t < y < b and l < x < r for y, x in region)


def analyze(grid):
    """Recover complete region geometry, including original canonical inputs."""
    _strict_grid(grid)
    backgrounds = _BASE._components(grid, 9)
    records = []
    for component in _BASE._components(grid, 1):
        box = _BASE._bbox(component)
        areas = sorted(len(region) for region in backgrounds if _contained(region, box))
        records.append({"cells": sorted(component), "bbox": box,
                        "hole_areas": areas, "score": max(areas, default=0)})
    return {"objects": records, "maximum_score": max((obj["score"] for obj in records), default=0),
            "height": len(grid), "width": len(grid[0])}


def _bbox_background_count(grid, obj):
    t, l, b, r = obj["bbox"]
    return sum(grid[y][x] == 9 for y in range(t + 1, b) for x in range(l + 1, r))


def validate_input(grid):
    """Check the shared prototype grammar, separately from canonical parity."""
    try:
        info = analyze(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    errors = []
    if not 9 <= info["height"] <= 30 or not 11 <= info["width"] <= 30:
        errors.append("prototype canvas must be 9..30 rows by 11..30 columns")
    positive = [obj for obj in info["objects"] if obj["score"] > 0]
    negative = [obj for obj in info["objects"] if obj["score"] == 0]
    if not 2 <= len(positive) <= 3:
        errors.append("prototype requires 2..3 hole-bearing objects")
    if not 1 <= len(negative) <= 4:
        errors.append("prototype requires 1..4 no-hole objects")
    if not any(not _BASE._is_rectangular_outline(set(obj["cells"])) for obj in positive):
        errors.append("an irregular true-hole positive is required")
    if not any(_bbox_background_count(grid, obj) > 0 for obj in negative):
        errors.append("an open-bbox no-hole decoy is required")
    boxes = [obj["bbox"] for obj in info["objects"]]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if not (a[2] + 1 < b[0] or b[2] + 1 < a[0]
                    or a[3] + 1 < b[1] or b[3] + 1 < a[1]):
                errors.append("object bounding boxes require separation by at least one blank row or column")
    return errors


def _selected(scores, selection, *, minimum=False):
    positive = [i for i, score in enumerate(scores) if score > 0]
    if selection == _ALL or not positive:
        return positive
    target = (min if minimum else max)(scores[i] for i in positive)
    return [i for i in positive if scores[i] == target]


def _paint_objects(grid, info, indices):
    out = deepcopy(grid)
    for i in indices:
        for r, c in info["objects"][i]["cells"]:
            out[r][c] = 8
    return out


def mirror(grid, settings):
    selection = _setting(settings)
    info = analyze(grid)
    return _paint_objects(grid, info, _selected([obj["score"] for obj in info["objects"]], selection))


def _rng(seed, slot):
    encoded = f"{TASK_ID}/{VERSION}/inputs/{seed}/{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(encoded).digest(), "big"))


def _ring(h, w):
    return {(r, c) for r in range(h) for c in range(w)
            if r in (0, h - 1) or c in (0, w - 1)}


def _irregular_ring(h, w):
    return _ring(h, w) | {(max(1, h // 2), w)}


def _divided_ring(h, w, divider):
    return _ring(h, w) | {(r, divider) for r in range(1, h - 1)}


def _open_ring(h, w, gap=None):
    return _ring(h, w) - {(h - 1, w // 2 if gap is None else gap)}


def _canvas(h, w, shapes, rng):
    """Translate a constructive layout, then apply a shared reflection."""
    cells = {(r + y, c + x) for shape, y, x in shapes for r, c in shape}
    top, left = min(r for r, c in cells), min(c for r, c in cells)
    cells = {(r - top, c - left) for r, c in cells}
    used_h, used_w = max(r for r, c in cells) + 1, max(c for r, c in cells) + 1
    if used_h > h or used_w > w:
        raise AssertionError("constructive layout exceeds its canvas")
    dy, dx = rng.randrange(h - used_h + 1), rng.randrange(w - used_w + 1)
    flip_y, flip_x = bool(rng.randrange(2)), bool(rng.randrange(2))
    out = [[9] * w for _ in range(h)]
    for y, x in cells:
        y, x = y + dy, x + dx
        out[h - 1 - y if flip_y else y][w - 1 - x if flip_x else x] = 1
    return out


def _teaching_input(seed, index):
    rng = _rng(seed, f"demo-{index}")
    if index == 0:
        # Single cavity 4 beats either cavity 3, while the two cavities sum to6.
        shapes = [(_irregular_ring(4, 4), 1, 1),
                  (_divided_ring(3, 9, 4), 1, 9),
                  (_open_ring(5, 12), 10, 4)]
        return _canvas(18, 20, shapes, rng)
    # A missing CORNER leaves a four-connected unit hole but leaks diagonally.
    # Its score1 ties the divided object's max1, although that object's sum is2.
    shapes = [(_ring(3, 3) - {(0, 0)}, 1, 2),
              (_divided_ring(3, 5, 2), 1, 11),
              (_open_ring(5, 10), 9, 4)]
    return _canvas(16, 19, shapes, rng)


def _small_input(seed, slot, h, w, *, minimum=False, middle=False):
    rng = _rng(seed, slot)
    if minimum:
        shapes = [(_irregular_ring(3, 4), 0, 0),
                  (_ring(3, 3), 0, 7), (_open_ring(3, 5), 5, 2)]
    elif middle:
        shapes = [(_irregular_ring(4, 5), 0, 0),
                  (_divided_ring(3, 7, 3), 0, 9), (_open_ring(5, 10), 6, 3)]
    else:
        ah, aw = rng.randint(3, 4), rng.randint(4, 6)
        shapes = [(_irregular_ring(ah, aw), 0, 0),
                  (_divided_ring(3, 5, 2), 0, w - 5),
                  (_open_ring(rng.randint(3, 4), rng.randint(5, w - 2)), h - 4, 1)]
    return _canvas(h, w, shapes, rng)


def _large_input(seed, slot, *, stress=False):
    rng = _rng(seed, slot)
    if not stress:
        shapes = [(_irregular_ring(8, 9), 1, 1),
                  (_divided_ring(6, 11, 5), 12, 1),
                  (_irregular_ring(3, 4), 19, 12),
                  (_open_ring(10, 11, rng.randint(1, 9)), 1, 14),
                  ({(r, c) for r in range(2) for c in range(3)}, 14, 20)]
        return _canvas(22, 26, shapes, rng)
    # Full-canvas geometry: three positive objects, a huge exterior-connected
    # decoy, and0..3 solid objects. All scores are derived, never stored hints.
    shapes = [(_irregular_ring(10, rng.randint(9, 10)), 0, 0),
              (_divided_ring(9, 14, rng.randint(5, 8)), 13, 0),
              (_irregular_ring(rng.randint(5, 6), rng.randint(8, 9)), 24, 0),
              (_open_ring(11, 16, rng.randint(1, 14)), 0, 14)]
    extras = [({(r, c) for r in range(2) for c in range(3)}, 14 + rng.randrange(2), 18 + rng.randrange(3)),
              ({(r, c) for r in range(3) for c in range(2)}, 20, 24),
              ({(0, c) for c in range(3)}, 27, 25)]
    shapes.extend(extras[:rng.randint(0, 3)])
    return _canvas(30, 30, shapes, rng)


def _background_eight(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9}
    regions = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        region, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        region.add(point)
                        todo.append(point)
        regions.append(region)
    return regions


def _rival_outputs(grid, selection):
    info = analyze(grid)
    objects = info["objects"]
    scores = [obj["score"] for obj in objects]
    chosen = _selected(scores, selection)
    positive = _selected(scores, _ALL)
    other = _LARGEST if selection == _ALL else _ALL
    total = [sum(obj["hole_areas"]) for obj in objects]
    count = [len(obj["hole_areas"]) for obj in objects]
    fg = [len(obj["cells"]) if obj["score"] else 0 for obj in objects]
    bbox = [((obj["bbox"][2] - obj["bbox"][0] + 1)
             * (obj["bbox"][3] - obj["bbox"][1] + 1)) if obj["score"] else 0 for obj in objects]
    raw_background = [_bbox_background_count(grid, obj) for obj in objects]
    rectangle = [obj["score"] if _BASE._is_rectangular_outline(set(obj["cells"])) else 0 for obj in objects]
    eight_regions = _background_eight(grid)
    eight = [max((len(region) for region in eight_regions if _contained(region, obj["bbox"])), default=0)
             for obj in objects]
    outputs = {
        "opposite_setting": _paint_objects(grid, info, _selected(scores, other)),
        "total_hole_area": _paint_objects(grid, info, _selected(total, _LARGEST)),
        "hole_count": _paint_objects(grid, info, _selected(count, _LARGEST)),
        "largest_foreground": _paint_objects(grid, info, _selected(fg, _LARGEST)),
        "largest_bbox": _paint_objects(grid, info, _selected(bbox, _LARGEST)),
        "any_bbox_background": _paint_objects(grid, info, _selected(raw_background, selection)),
        "rectangular_frames_only": _paint_objects(grid, info, _selected(rectangle, selection)),
        "background_eight_connected": _paint_objects(grid, info, _selected(eight, selection)),
        "smallest_score": _paint_objects(grid, info, _selected(scores, _LARGEST, minimum=True)),
        "first_tie_only": _paint_objects(grid, info, chosen[:1]),
        "last_tie_only": _paint_objects(grid, info, chosen[-1:]),
        "first_hole_object": _paint_objects(grid, info, positive[:1]),
        "unchanged_input": deepcopy(grid),
    }
    holes, boxes = deepcopy(grid), deepcopy(grid)
    regions = _BASE._components(grid, 9)
    for i in chosen:
        obj = objects[i]
        for region in regions:
            if _contained(region, obj["bbox"]):
                for r, c in region:
                    holes[r][c] = 8
        t, l, b, r = obj["bbox"]
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                boxes[y][x] = 8
    outputs["fill_holes_instead_of_objects"] = holes
    outputs["fill_bounding_boxes"] = boxes
    return outputs


def teaching_check(episode, settings):
    """Fit rivals only to demonstrations; private query labels are ignored."""
    selection = _setting(settings)
    train, test = episode["train"], episode["test"]
    if not train or not test:
        raise ValueError("at least one demonstration and query are required")
    predictions = [_rival_outputs(pair["input"], selection) for pair in train]
    for pair in train:
        if pair["output"] != mirror(pair["input"], settings):
            raise ValueError("demonstration label disagrees with the diagnostic rule")
    eliminated = {name: [i for i, pair in enumerate(train) if predictions[i][name] != pair["output"]]
                  for name in predictions[0]}
    survivors = [name for name, witnesses in eliminated.items() if not witnesses]
    harmful = []
    if survivors:
        query_predictions = [_rival_outputs(pair["input"], selection) for pair in test]
        query_truth = [mirror(pair["input"], settings) for pair in test]
        harmful = [name for name in survivors if any(pred[name] != truth
                   for pred, truth in zip(query_predictions, query_truth))]
    return {"survivors": survivors, "harmful_survivors": harmful,
            "eliminated": {name: rows for name, rows in eliminated.items() if rows},
            "rivals_tested": len(eliminated), "fit_uses": "demonstrations_only"}


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _setting(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    inputs = [_teaching_input(seed, 0), _teaching_input(seed, 1)]
    extra_sizes = [(11, 17), (15, 22), (24, 25), (26, 21)]
    for i in range(2, demos):
        h, w = extra_sizes[i - 2]
        inputs.append(_small_input(seed, f"demo-{i}", h, w))
    test_inputs = []
    for i in range(queries):
        if i == 0:
            grid = _small_input(seed, "query-0", 9, 11, minimum=True)
        elif i == 1:
            grid = _small_input(seed, "query-1", 12, 16, middle=True)
        else:
            grid = _large_input(seed, f"query-{i}", stress=i == 3)
        test_inputs.append(grid)
    for grid in inputs + test_inputs:
        errors = validate_input(grid)
        if errors:
            raise AssertionError("constructive sampler violated its domain: " + "; ".join(errors))
    episode = {"train": [{"input": grid, "output": mirror(grid, settings)} for grid in inputs],
               "test": [{"input": grid, "output": mirror(grid, settings)} for grid in test_inputs],
               "program_solution": program(settings), "settings": dict(settings), "seed": seed}
    if teaching_check(episode, settings)["harmful_survivors"]:
        raise AssertionError("constructed demonstrations leave a query-changing rival")
    return episode


def public_view(episode, query_index=0):
    """Return only demos and one current query; the caller owns reveal timing."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                            "test": [episode["test"][query_index]]}))
