"""Count blue markers, select a monochrome area match, crop, and scale.

The Python outputs are claims until the native worker checks protected Racket.
Input RNG streams never depend on the setting or requested pair counts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

SCALES = (1, 2, 3)
DEMO_SIZES = ((10, 12), (14, 16), (12, 14), (16, 18), (18, 20), (20, 22))
QUERY_SIZES = ((13, 15), (21, 24), (24, 27), (30, 30))
NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))
RIVALS = (
    "count_all_header_nonzero", "color_agnostic_components", "isolated_object",
    "largest_object", "smallest_object", "first_object", "last_object",
    "bbox_area", "header_runs", "flip_lr", "flip_ud", "transpose",
    "largest_multicolor_group", "area_rank_2", "area_rank_3",
    *(f"fixed_color_{color}" for color in range(2, 10)),
    *(f"scale_{scale}" for scale in SCALES),
)


def _integer(value, lower, upper, name):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def _scale(settings):
    if type(settings) is not dict or set(settings) != {"scale"}:
        raise ValueError("settings must contain only scale")
    return _integer(settings["scale"], 1, 3, "scale")


def program(settings):
    scale = _scale(settings)
    canonical = Path(__file__).with_name("canonical.rkt").read_text()
    if scale == 2:
        return canonical
    needle = "(upscale (s17b-object-crop work target) 2)"
    if canonical.count(needle) != 1:
        raise ValueError("canonical resource has drifted")
    return canonical.replace(needle, f"(upscale (s17b-object-crop work target) {scale})")


def _rng(seed, *parts):
    raw = json.dumps([seed, *parts], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def objects(grid, *, color_sensitive=True):
    """Monochrome four-neighbor components below, but never in, row zero."""
    seen, result = set(), []
    for row in range(1, len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color, cells, todo = grid[row][col], [], [(row, col)]
            seen.add((row, col))
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in NEIGHBORS:
                    nr, nc = r + dr, c + dc
                    if (1 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and (nr, nc) not in seen and grid[nr][nc] != 0
                            and (not color_sensitive or grid[nr][nc] == color)):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return sorted(result, key=bbox)


def _crop(grid, obj, scale, *, isolate=False):
    if obj is None:
        return [[0]]  # Totalized wrong-rule predictions; no errors count as teaching.
    r0, c0, r1, c1 = bbox(obj)
    selected = set(obj)
    result = []
    for r in range(r0, r1 + 1):
        row = [grid[r][c] if not isolate or (r, c) in selected else 0
               for c in range(c0, c1 + 1)]
        expanded = [value for value in row for _ in range(scale)]
        result.extend([expanded[:] for _ in range(scale)])
    return result


def _match(grid, count, *, color_sensitive=True, use_bbox=False):
    candidates = objects(grid, color_sensitive=color_sensitive)
    for obj in candidates:
        r0, c0, r1, c1 = bbox(obj)
        measure = (r1 - r0 + 1) * (c1 - c0 + 1) if use_bbox else len(obj)
        if measure == count:
            return obj
    return None


def solve(grid, scale):
    _integer(scale, 1, 3, "scale")
    target = _match(grid, sum(value == 1 for value in grid[0]))
    if target is None:
        raise ValueError("input is outside the area-match grammar")
    return _crop(grid, target, scale)


def rival_output(grid, scale, name):
    count = sum(value == 1 for value in grid[0])
    target = _match(grid, count)
    all_objects = objects(grid)
    if name == "count_all_header_nonzero":
        target = _match(grid, sum(value != 0 for value in grid[0]))
    elif name == "header_runs":
        target = _match(grid, sum(value == 1 and (i == 0 or grid[0][i - 1] != 1)
                                  for i, value in enumerate(grid[0])))
    elif name == "color_agnostic_components":
        target = _match(grid, count, color_sensitive=False)
    elif name == "bbox_area":
        target = _match(grid, count, use_bbox=True)
    elif name in ("largest_object", "smallest_object"):
        target = (max if name == "largest_object" else min)(all_objects, key=len)
    elif name in ("first_object", "last_object"):
        target = all_objects[0 if name == "first_object" else -1]
    elif name.startswith("area_rank_"):
        rank = int(name.rsplit("_", 1)[1])
        ranked = sorted(all_objects, key=lambda obj: (-len(obj), bbox(obj)))
        target = ranked[rank - 1] if len(ranked) >= rank else None
    elif name == "largest_multicolor_group":
        groups = [group for group in objects(grid, color_sensitive=False)
                  if len({grid[r][c] for r, c in group}) > 1]
        if groups:
            group = set(max(groups, key=len))
            target = max((obj for obj in all_objects if set(obj) <= group), key=len)
        else:
            target = None
    elif name.startswith("fixed_color_"):
        color = int(name.rsplit("_", 1)[1])
        target = next((obj for obj in all_objects if grid[obj[0][0]][obj[0][1]] == color), None)
    elif name.startswith("scale_"):
        scale = int(name.rsplit("_", 1)[1])
    elif name not in ("isolated_object", "flip_lr", "flip_ud", "transpose"):
        raise ValueError(f"undeclared rival: {name}")
    answer = _crop(grid, target, scale, isolate=name == "isolated_object")
    if name == "flip_lr":
        return [row[::-1] for row in answer]
    if name == "flip_ud":
        return answer[::-1]
    if name == "transpose":
        return [list(row) for row in zip(*answer)]
    return answer


def teaching_check(demos, queries, scale):
    survivors = [name for name in RIVALS if all(
        rival_output(pair["input"], scale, name) == pair["output"] for pair in demos)]
    ambiguities = [{"rival": name, "query_index": i} for name in survivors
                   for i, pair in enumerate(queries)
                   if rival_output(pair["input"], scale, name) != pair["output"]]
    return {"declared_rivals": list(RIVALS), "survivors": survivors,
            "refuted": [name for name in RIVALS if name not in survivors],
            "ambiguities": ambiguities,
            "scope": "finite declared totalized Python rivals; no universal uniqueness claim"}


def _partitions(start, length, count):
    usable = length - (count - 1)
    small, extra = divmod(usable, count)
    result = []
    for i in range(count):
        width = small + (i < extra)
        result.append((start, width))
        start += width + 1
    return result


def _poly(rng, size, height, width, *, open_bbox=False):
    """Connected random growth, retaining order so the final cell is removable."""
    for _ in range(64):
        first = (rng.randrange(height), rng.randrange(width))
        cells, order = {first}, [first]
        while len(cells) < size:
            frontier = sorted({(r + dr, c + dc) for r, c in cells for dr, dc in NEIGHBORS
                               if 0 <= r + dr < height and 0 <= c + dc < width} - cells)
            cell = rng.choice(frontier)
            cells.add(cell)
            order.append(cell)
        r0, c0, r1, c1 = bbox(cells)
        if not open_bbox or (r1 - r0 + 1) * (c1 - c0 + 1) > size:
            return [(r - r0, c - c0) for r, c in order]
    raise RuntimeError("bounded shape search could not make an open bounding box")


def sample_scene(seed, index, *, height, width, attempt=0):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, 10000, "index")
    _integer(height, 8, 30, "height")
    _integer(width, 9, 30, "width")
    _integer(attempt, 0, 31, "attempt")
    rng = _rng(seed, "scene", index, height, width, attempt)
    palette = list(range(2, 10))
    _rng(seed, "palette").shuffle(palette)
    palette = palette[index % 8:] + palette[:index % 8]
    row_parts = _partitions(1, height - 1, 3 if height >= 21 else 2)
    col_parts = _partitions(0, width, 3 if width >= 21 else 2)
    slots = [(r, c, min(h, 10), min(w, 10)) for r, h in row_parts for c, w in col_parts]
    capacity = min(h * w for _, _, h, w in slots)
    max_k = min(width - 2, capacity - 2, 26)
    min_k = max(4, max_k - 6) if max(height, width) >= 21 else 4
    k = rng.randint(min_k, max_k)
    grid = [[0] * width for _ in range(height)]
    # First two demonstrations occupy different interior slots. Other draws
    # include boundary targets. Slot placement is independent of the scale.
    target_slot = (1 + index) if index < 2 else rng.randrange(len(slots))
    other_slots = [i for i in range(len(slots)) if i != target_slot]
    rng.shuffle(other_slots)
    header_slot, split_slot, *ordinary_slots = other_slots

    def paint(slot_index, shape, colors):
        top, left, sh, sw = slots[slot_index]
        ph = max(r for r, _ in shape) + 1
        pw = max(c for _, c in shape) + 1
        # Occupy the outer scene edges: large cases add objects/area and spread,
        # rather than enclosing a small puzzle in an empty border.
        row_offset = sh - ph if top == row_parts[-1][0] else (0 if top == 1 else rng.randrange(sh - ph + 1))
        col_offset = sw - pw if left == col_parts[-1][0] else (0 if left == 0 else rng.randrange(sw - pw + 1))
        translated = [(top + row_offset + r, left + col_offset + c) for r, c in shape]
        for (r, c), color in zip(translated, colors):
            if grid[r][c] != 0:
                raise RuntimeError("scene construction overlapped cells")
            grid[r][c] = color
        return translated

    _, _, th, tw = slots[target_slot]
    target = _poly(rng, k, th, tw, open_bbox=True)
    target_cells = paint(target_slot, target, [palette[0]] * k)
    r0, c0, r1, c1 = bbox(target_cells)
    target_set = set(target_cells)
    holes = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
             if (r, c) not in target_set and any((r + dr, c + dc) in target_set for dr, dc in NEIGHBORS)]
    # Teach both kinds of crop within the first two demos. If every visible
    # target contained another color, largest-multicolor-group could bypass K.
    if index % 4 in (0, 2):
        hr, hc = rng.choice(holes)
        grid[hr][hc] = palette[1]

    _, _, hh, hw = slots[header_slot]
    shape = _poly(rng, k + 1, hh, hw)
    # A second disconnected object may share the target color; color alone
    # does not identify the answer.
    paint(header_slot, shape, [palette[0] if index % 2 else palette[2]] * len(shape))
    _, _, sh, sw = slots[split_slot]
    shape = _poly(rng, k, sh, sw)
    paint(split_slot, shape, [palette[3]] * (k - 1) + [palette[4]])
    for i, slot_index in enumerate(ordinary_slots):
        _, _, oh, ow = slots[slot_index]
        size = rng.choice([value for value in (k - 2, k + 2, k + 3)
                           if 2 <= value <= oh * ow and value != k])
        shape = _poly(rng, size, oh, ow)
        paint(slot_index, shape, [palette[(5 + i) % 8]] * size)

    extras = 0 if index % 4 == 3 else 1
    columns = [0, 1] + rng.sample(range(2, width), k + extras - 2)
    rng.shuffle(columns)
    # Reserve the adjacent columns as actual blue markers to teach cells,
    # not runs; the colored distractor goes elsewhere.
    if extras:
        non_blue = next(col for col in reversed(columns) if col not in (0, 1))
        columns.remove(non_blue)
        grid[0][non_blue] = palette[2]
    for col in columns:
        grid[0][col] = 1
    if sum(len(obj) == k for obj in objects(grid)) != 1:
        raise RuntimeError("constructed scene does not have a unique area match")
    return grid


def inspect_scene(grid):
    count = sum(value == 1 for value in grid[0])
    all_objects = objects(grid)
    target = _match(grid, count)
    if target is None:
        raise ValueError("no selected object")
    r0, c0, r1, c1 = bbox(target)
    cells = [(r, c) for r in range(1, len(grid)) for c in range(len(grid[0])) if grid[r][c]]
    br0, bc0, br1, bc1 = bbox(cells)
    selected = set(target)
    return {"height": len(grid), "width": len(grid[0]), "header_count": count,
            "area_matches": sum(len(obj) == count for obj in all_objects),
            "body_objects": len(all_objects), "target_bbox": [r0, c0, r1, c1],
            "target_color": grid[target[0][0]][target[0][1]],
            "target_has_foreign_crop_cell": any(grid[r][c] and (r, c) not in selected
                for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)),
            "occupied_body_cells": len(cells), "occupied_row_span": br1 - br0 + 1,
            "occupied_col_span": bc1 - bc0 + 1}


def generate(seed, settings, demos=3, queries=4):
    scale = _scale(settings)
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    teaching_attempts = 0
    for index in range(demos):
        height, width = DEMO_SIZES[index]
        for attempt in range(32):
            grid = sample_scene(seed, index, height=height, width=width, attempt=attempt)
            pair = {"input": grid, "output": solve(grid, scale)}
            if index == 1:
                check = teaching_check(train + [pair], [], scale)
                if check["survivors"] != [f"scale_{scale}"]:
                    continue
            train.append(pair)
            teaching_attempts += attempt + 1
            break
        else:
            raise RuntimeError("two-demo teaching budget exhausted")
    test = []
    for index in range(queries):
        height, width = QUERY_SIZES[index]
        grid = sample_scene(seed, 100 + index, height=height, width=width)
        test.append({"input": grid, "output": solve(grid, scale)})
    return {"train": train, "test": test, "program_solution": program(settings),
            "private_sampling": {"demonstration_attempts": teaching_attempts,
                                 "teaching_uses_queries": False}}
