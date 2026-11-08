"""Constructive two-setting layer-flip family for ``89a9a629c544``.

``vertical`` is the exact selected canonical program. ``anchor_bbox`` first
selects the uniquely most populous color, derives an axis from that color's
bounding-box aspect ratio, then flips every color layer along the derived axis.
Inputs are sampled independently of the hidden setting inside four disjoint
quadrants, so both vertical and horizontal layer transforms are total and cannot
clobber another color.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random


TASK_ID = "89a9a629c544"
HERE = Path(__file__).resolve().parent
SETTINGS = ("vertical", "anchor_bbox")
DEMO_SHAPES = ((15, 11), (11, 15), (13, 13), (17, 15), (19, 17), (21, 19))
QUERY_SHAPES = ((7, 7), (18, 22), (23, 19), (30, 30))
DEMO_AXES = ("lr", "ud", "lr", "ud", "lr", "ud")
QUERY_AXES = ("lr", "ud", "lr", "ud")


def _integer(value, name, low=None, high=None):
    if type(value) is not int or (low is not None and value < low) or (
        high is not None and value > high
    ):
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _setting(settings):
    if type(settings) is not dict or set(settings) != {"axis_policy"}:
        raise ValueError("settings must contain exactly axis_policy")
    value = settings["axis_policy"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("axis_policy must be vertical or anchor_bbox")
    return value


def _grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return grid


def program(settings):
    name = _setting(settings)
    filename = "vertical.rkt" if name == "vertical" else "anchor_bbox.rkt"
    return (HERE / filename).read_text(encoding="utf-8")


def _colors(grid):
    seen = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.append(value)
    return seen


def _mask(grid, color):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def _bbox(mask):
    rows = [r for r, _ in mask]
    cols = [c for _, c in mask]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_axis(mask):
    r1, c1, r2, c2 = _bbox(mask)
    return "lr" if c2 - c1 + 1 > r2 - r1 + 1 else "ud"


def _flip(mask, axis):
    r1, c1, r2, c2 = _bbox(mask)
    if axis == "ud":
        return {(r1 + r2 - r, c) for r, c in mask}
    if axis == "lr":
        return {(r, c1 + c2 - c) for r, c in mask}
    raise ValueError("axis must be ud or lr")


def _apply_axis(grid, axis):
    result = deepcopy(_grid(grid))
    for color in _colors(grid):
        current = _mask(result, color)
        target = _flip(current, axis)
        for r, row in enumerate(result):
            for c, value in enumerate(row):
                if value == color:
                    result[r][c] = 0
        for r, c in target:
            result[r][c] = color
    return result


def _apply_per_color_axes(grid):
    result = deepcopy(_grid(grid))
    original = {color: _mask(grid, color) for color in _colors(grid)}
    for color in _colors(grid):
        current = _mask(result, color)
        target = _flip(current, _bbox_axis(original[color]))
        for r, row in enumerate(result):
            for c, value in enumerate(row):
                if value == color:
                    result[r][c] = 0
        for r, c in target:
            result[r][c] = color
    return result


def scene_facts(grid):
    _grid(grid)
    colors = _colors(grid)
    masks = {color: _mask(grid, color) for color in colors}
    counts = {color: len(mask) for color, mask in masks.items()}
    maximum = max(counts.values()) if counts else 0
    anchors = [color for color in colors if counts[color] == maximum]
    anchor = anchors[0] if len(anchors) == 1 else None

    def safe(axis):
        occupied = set()
        expected = [[0] * len(grid[0]) for _ in grid]
        for color in colors:
            target = _flip(masks[color], axis)
            if occupied & target:
                return False
            occupied |= target
            for r, c in target:
                expected[r][c] = color
        return _apply_axis(grid, axis) == expected

    return {
        "colors": colors,
        "counts": counts,
        "anchor": anchor,
        "unique_anchor": anchor is not None,
        "anchor_axis": _bbox_axis(masks[anchor]) if anchor is not None else None,
        "all_layers_ud_safe": bool(colors) and safe("ud"),
        "all_layers_lr_safe": bool(colors) and safe("lr"),
    }


def validate_input(grid):
    try:
        _grid(grid)
    except ValueError as error:
        return [str(error)]
    errors = []
    h, w = len(grid), len(grid[0])
    if not 7 <= h <= 30 or not 7 <= w <= 30:
        errors.append("parametric layer scenes must be 7..30 on each side")
    facts = scene_facts(grid)
    if len(facts["colors"]) != 4:
        errors.append("scene must contain exactly four non-background colors")
    if not facts["unique_anchor"]:
        errors.append("scene must have one uniquely most populous anchor color")
    if facts["anchor_axis"] not in ("ud", "lr"):
        errors.append("anchor bounding box must determine an axis")
    if not facts["all_layers_ud_safe"] or not facts["all_layers_lr_safe"]:
        errors.append("both vertical and horizontal layer transforms must be collision-safe")
    for color in facts["colors"]:
        mask = _mask(grid, color)
        if _flip(mask, "ud") == mask or _flip(mask, "lr") == mask:
            errors.append(f"color {color} must be asymmetric under both axes")
    return errors


def transform(grid, settings):
    policy = _setting(settings)
    errors = validate_input(grid)
    if errors:
        raise ValueError("invalid parametric input: " + "; ".join(errors))
    axis = "ud" if policy == "vertical" else scene_facts(grid)["anchor_axis"]
    return _apply_axis(grid, axis)


def _rng(seed, stream, index):
    payload = json.dumps([seed, stream, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _quadrants(height, width):
    split_r, split_c = height // 2, width // 2
    return (
        (0, split_r, 0, split_c),
        (0, split_r, split_c + 1, width),
        (split_r + 1, height, 0, split_c),
        (split_r + 1, height, split_c + 1, width),
    )


def _box_dimensions(tile, axis):
    r0, r1, c0, c1 = tile
    th, tw = r1 - r0, c1 - c0
    if axis == "lr":
        bh = max(2, min(th, max(2, th // 2)))
        bw = max(bh + 1, min(tw, max(3, tw - (1 if tw > 3 else 0))))
        if bw > tw:
            bh, bw = 2, tw
    else:
        bw = max(2, min(tw, max(2, tw // 2)))
        bh = max(bw + 1, min(th, max(3, th - (1 if th > 3 else 0))))
        if bh > th:
            bh, bw = th, 2
    if not (2 <= bh <= th and 2 <= bw <= tw):
        raise ValueError("tile cannot hold an oriented bounding box")
    if axis == "lr" and not bw > bh:
        bh, bw = 2, min(tw, 3)
    if axis == "ud" and not bh >= bw:
        bh, bw = min(th, 3), 2
    return bh, bw


def _oriented_mask(tile, axis, count, rng):
    r0, r1, c0, c1 = tile
    bh, bw = _box_dimensions(tile, axis)
    top = rng.randint(r0, r1 - bh)
    left = rng.randint(c0, c1 - bw)
    positions = [(top + r, left + c) for r in range(bh) for c in range(bw)]
    # Two opposite corners already span the oriented bbox and are
    # asymmetric under both horizontal and vertical reflection.
    base = {(top, left), (top + bh - 1, left + bw - 1)}
    count = max(2, min(count, len(positions) - 1))
    extras = [cell for cell in positions if cell not in base]
    for _ in range(128):
        rng.shuffle(extras)
        mask = base | set(extras[: count - len(base)])
        if _bbox_axis(mask) == axis and _flip(mask, "ud") != mask and _flip(mask, "lr") != mask:
            return mask
    raise RuntimeError("failed to construct a two-axis-asymmetric mask")


def sample_input(seed, stream, index, height, width, anchor_axis):
    _integer(seed, "seed")
    _integer(index, "index", 0)
    _integer(height, "height", 7, 30)
    _integer(width, "width", 7, 30)
    if type(stream) is not str or not stream:
        raise ValueError("stream must be a nonempty string")
    if anchor_axis not in ("ud", "lr"):
        raise ValueError("anchor_axis must be ud or lr")
    rng = _rng(seed, stream, index)
    palette = rng.sample(range(1, 10), 4)
    tiles = _quadrants(height, width)
    axes = (
        "ud" if anchor_axis == "lr" else "lr",
        anchor_axis,
        "ud" if anchor_axis == "lr" else "lr",
        anchor_axis,
    )
    capacities = []
    for tile, axis in zip(tiles, axes):
        bh, bw = _box_dimensions(tile, axis)
        capacities.append(bh * bw)
    anchor_count = max(5, min(capacities[3] - 1, round(capacities[3] * 0.56)))
    counts = [
        max(2, min(capacities[0] - 1, anchor_count - 3)),
        max(2, min(capacities[1] - 1, anchor_count - 2)),
        max(2, min(capacities[2] - 1, anchor_count - 1)),
        anchor_count,
    ]
    if len(set(counts)) != 4 or max(counts[:-1]) >= anchor_count:
        counts = [2, 3, max(4, anchor_count - 1), anchor_count]
        counts = [min(value, capacities[i] - 1) for i, value in enumerate(counts)]
    if len(set(counts)) != 4 or max(counts[:-1]) >= counts[3]:
        raise ValueError("canvas is too small for a unique four-layer anchor lesson")

    grid = [[0] * width for _ in range(height)]
    for color, tile, axis, count in zip(palette, tiles, axes, counts):
        for r, c in _oriented_mask(tile, axis, count, rng):
            grid[r][c] = color
    errors = validate_input(grid)
    if errors:
        raise RuntimeError("constructive layer sampler failed: " + "; ".join(errors))
    return grid


def generate(seed, settings, demos, queries):
    _integer(seed, "seed", 0, 2**63 - 1)
    _setting(settings)
    _integer(demos, "demos", 2, 6)
    _integer(queries, "queries", 1, 4)
    result = {
        "train": [],
        "test": [],
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
        "prototype": True,
    }
    seen = set()
    for split, shapes, axes in (
        ("train", DEMO_SHAPES[:demos], DEMO_AXES[:demos]),
        ("test", QUERY_SHAPES[:queries], QUERY_AXES[:queries]),
    ):
        for index, ((height, width), axis) in enumerate(zip(shapes, axes)):
            grid = sample_input(seed, split, index, height, width, axis)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise RuntimeError("sampler produced duplicate visible inputs")
            seen.add(key)
            result[split].append({"input": grid, "output": transform(grid, settings)})
    return result


def _selected_axis(grid, settings):
    return "ud" if _setting(settings) == "vertical" else scene_facts(grid)["anchor_axis"]


def _apply_anchor_only(grid, axis):
    result = deepcopy(grid)
    anchor = scene_facts(grid)["anchor"]
    current = _mask(result, anchor)
    target = _flip(current, axis)
    for r, row in enumerate(result):
        for c, value in enumerate(row):
            if value == anchor:
                result[r][c] = 0
    for r, c in target:
        result[r][c] = anchor
    return result


def rival_outputs(grid, settings):
    facts = scene_facts(grid)
    colors = facts["colors"]
    first = colors[0]
    least = min(colors, key=lambda color: facts["counts"][color])
    overall = "lr" if len(grid[0]) > len(grid) else "ud"
    selected_axis = _selected_axis(grid, settings)
    return {
        "fixed_vertical": _apply_axis(grid, "ud"),
        "fixed_horizontal": _apply_axis(grid, "lr"),
        "overall_grid_aspect": _apply_axis(grid, overall),
        "first_color_bbox": _apply_axis(grid, _bbox_axis(_mask(grid, first))),
        "least_populous_bbox": _apply_axis(grid, _bbox_axis(_mask(grid, least))),
        "each_color_uses_own_bbox": _apply_per_color_axes(grid),
        "flip_only_anchor": _apply_anchor_only(grid, selected_axis),
    }


def teaching_failures(demos, queries, settings):
    selected = _setting(settings)
    if type(demos) is not list or type(queries) is not list or not demos or not queries:
        return ["demos and queries must be nonempty lists"]
    prepared = []
    for label, pairs in (("demo", demos), ("query", queries)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or not {"input", "output"} <= set(pair):
                return [f"{label} {index} is malformed"]
            errors = validate_input(pair["input"])
            if errors:
                return [f"{label} {index} input invalid: {'; '.join(errors)}"]
            expected = transform(pair["input"], settings)
            if pair["output"] != expected:
                return [f"{label} {index} label disagrees with {selected}"]
            prepared.append((label, pair, rival_outputs(pair["input"], settings)))

    names = sorted(prepared[0][2])
    if selected == "vertical":
        names.remove("fixed_vertical")
    failures = []
    demo_rows = [row for row in prepared if row[0] == "demo"]
    query_rows = [row for row in prepared if row[0] == "query"]
    for name in names:
        survives = all(rivals[name] == pair["output"] for _, pair, rivals in demo_rows)
        disagrees = any(rivals[name] != pair["output"] for _, pair, rivals in query_rows)
        if survives and disagrees:
            failures.append(f"plausible rival {name!r} fits every demo but changes a query")
    return failures
