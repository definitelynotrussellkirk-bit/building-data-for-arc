"""Matched-input repeated-shape selection episodes for ``fb7c915894d6``.

The private episode setting chooses one of two repeated normalized-shape
classes.  The selected class's measured frequency is then consumed as the
upscaling factor, so selection and rendering form a genuine sequential rule.
Python outputs are deterministic claims; native qualification independently
executes every label with protected Racket.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK_ID = "fb7c915894d6"
POLICIES = ("most_frequent", "least_repeated")
SETTINGS = tuple({"class_policy": value} for value in POLICIES)
CARDINAL = ((1, 0), (-1, 0), (0, 1), (0, -1))

# h, w, dominant count, secondary count, dominant area, secondary area,
# singleton areas, class owning the earliest object.
DEMO_SPECS = (
    (16, 18, 4, 2, 4, 9, (5,), "dominant"),
    (20, 22, 5, 3, 8, 4, (), "secondary"),
    (14, 16, 3, 2, 6, 5, (4,), "dominant"),
    (24, 26, 5, 2, 5, 8, (6,), "secondary"),
    (27, 29, 4, 3, 9, 6, (7,), "dominant"),
    (30, 30, 5, 4, 7, 5, (), "secondary"),
)
QUERY_SPECS = (
    (15, 17, 3, 2, 4, 6, (5,), "secondary"),
    (21, 23, 4, 3, 8, 5, (6,), "dominant"),
    (27, 28, 5, 2, 6, 9, (7,), "secondary"),
    (30, 30, 5, 3, 9, 8, (7,), "dominant"),
)
TARGETS = (
    (0.00, 0.00), (0.06, 0.50), (0.06, 0.94),
    (0.50, 0.06), (0.50, 0.94),
    (0.94, 0.06), (0.94, 0.50), (0.94, 0.94),
    (0.50, 0.50),
)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings):
    if (
        type(settings) is not dict
        or set(settings) != {"class_policy"}
        or type(settings["class_policy"]) is not str
        or settings["class_policy"] not in POLICIES
    ):
        raise ValueError(
            "settings must be exactly {'class_policy': "
            "'most_frequent'|'least_repeated'}"
        )
    return settings["class_policy"]


def program(settings):
    value = _policy(settings)
    name = "canonical.rkt" if value == "most_frequent" else "least_repeated.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed, split, index, attempt=0):
    payload = json.dumps(
        [TASK_ID, seed, split, index, attempt], separators=(",", ":")
    ).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _normalize(cells):
    row0 = min(r for r, _ in cells)
    col0 = min(c for _, c in cells)
    return tuple(sorted((r - row0, c - col0) for r, c in cells))


def _bbox(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _random_polyomino(rng, size, *, used):
    for _ in range(512):
        cells = {(0, 0)}
        while len(cells) < size:
            row, col = rng.choice(tuple(cells))
            dr, dc = rng.choice(CARDINAL)
            cells.add((row + dr, col + dc))
        shape = _normalize(cells)
        height, width = _bbox(shape)
        if (
            shape not in used
            and height <= 5
            and width <= 5
            and len(shape) < height * width
        ):
            return shape
    raise ValueError(f"unable to construct distinct non-solid polyomino of area {size}")


def _translated(shape, top, left):
    return {(top + r, left + c) for r, c in shape}


def _clear_of(cells, occupied):
    if cells & occupied:
        return False
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr, dc in CARDINAL
    )


def _place_object(grid, occupied, shape, color, target, rng):
    height, width = len(grid), len(grid[0])
    shape_h, shape_w = _bbox(shape)
    desired_r = target[0] * (height - 1)
    desired_c = target[1] * (width - 1)
    candidates = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            cells = _translated(shape, top, left)
            if not _clear_of(cells, occupied):
                continue
            center_r = top + (shape_h - 1) / 2
            center_c = left + (shape_w - 1) / 2
            score = (center_r - desired_r) ** 2 + (center_c - desired_c) ** 2
            candidates.append((score, rng.random(), top, left, cells))
    if not candidates:
        return False
    _score, _tie, _top, _left, cells = min(candidates)
    for row, col in cells:
        grid[row][col] = color
    occupied.update(cells)
    return True


def _object_order(dominant_count, secondary_count, singleton_count, first_class):
    remaining = {
        "dominant": dominant_count,
        "secondary": secondary_count,
        **{f"single_{i}": 1 for i in range(singleton_count)},
    }
    order = []
    order.append(first_class)
    remaining[first_class] -= 1
    preferred = [
        "secondary" if first_class == "dominant" else "dominant",
        "dominant" if first_class == "dominant" else "secondary",
        *[f"single_{i}" for i in range(singleton_count)],
    ]
    while sum(remaining.values()):
        progressed = False
        for name in preferred:
            if remaining.get(name, 0):
                order.append(name)
                remaining[name] -= 1
                progressed = True
        if not progressed:
            raise AssertionError("object schedule stalled")
    return order


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    objects = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            todo = [(row, col)]
            seen.add((row, col))
            cells = set()
            while todo:
                point = todo.pop()
                cells.add(point)
                for dr, dc in CARDINAL:
                    neighbor = (point[0] + dr, point[1] + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        todo.append(neighbor)
            objects.append(cells)
    return objects


def _shape_classes(grid):
    grouped = defaultdict(list)
    for cells in _components(grid):
        grouped[_normalize(cells)].append(cells)
    return dict(grouped)


def _class_anchor(items):
    return min((min(r for r, _ in cells), min(c for _, c in cells)) for cells in items)


def select_class(grid, policy):
    if policy not in POLICIES:
        raise ValueError(f"unknown class policy {policy!r}")
    classes = _shape_classes(grid)
    repeated = [(shape, items) for shape, items in classes.items() if len(items) >= 2]
    if len(repeated) < 2:
        raise ValueError("input needs at least two repeated shape classes")
    if policy == "most_frequent":
        return min(repeated, key=lambda item: (-len(item[1]), _class_anchor(item[1])))
    return min(repeated, key=lambda item: (len(item[1]), _class_anchor(item[1])))


def render_shape(shape, scale):
    if type(scale) is not int or scale < 1:
        raise ValueError("scale must be a positive exact integer")
    height, width = _bbox(shape)
    output = [[0] * (width * scale) for _ in range(height * scale)]
    for row, col in shape:
        for dr in range(scale):
            for dc in range(scale):
                output[row * scale + dr][col * scale + dc] = 8
    return output


def claimed_output(grid, settings):
    policy = _policy(settings)
    shape, items = select_class(grid, policy)
    return render_shape(shape, len(items))


def validate_input(grid):
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        raise ValueError("grid must be a nonempty list of rows")
    height, width = len(grid), len(grid[0])
    if not 10 <= height <= 30 or not 10 <= width <= 30 or any(len(row) != width for row in grid):
        raise ValueError("grid dimensions must be rectangular and in 10..30")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact ARC colors")
    objects = _components(grid)
    if not 5 <= len(objects) <= 9:
        raise ValueError("input must contain 5..9 separated objects")
    classes = _shape_classes(grid)
    repeated = sorted(len(items) for items in classes.values() if len(items) >= 2)
    singles = [items for items in classes.values() if len(items) == 1]
    if len(repeated) != 2 or repeated[0] >= repeated[1]:
        raise ValueError("input needs exactly two repeated classes with distinct frequencies")
    if any(len(shape) == _bbox(shape)[0] * _bbox(shape)[1] for shape, items in classes.items() if len(items) >= 2):
        raise ValueError("selected repeated shapes must expose background in their bounding boxes")
    colors = []
    for cells in objects:
        values = {grid[r][c] for r, c in cells}
        if len(values) != 1:
            raise ValueError("objects must be monochrome")
        colors.extend(values)
    if len(colors) != len(set(colors)):
        raise ValueError("objects must use distinct colors")
    if claimed_output(grid, SETTINGS[0]) == claimed_output(grid, SETTINGS[1]):
        raise ValueError("settings must disagree on every admitted input")
    return {
        "height": height,
        "width": width,
        "objects": len(objects),
        "repeated_counts": repeated,
        "singleton_classes": len(singles),
    }


def sample_input(seed, index, *, split):
    _integer(seed, 0, 2**63 - 1, "seed")
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    specs = DEMO_SPECS if split == "train" else QUERY_SPECS
    _integer(index, 0, len(specs) - 1, "index")
    spec = specs[index]
    height, width, dominant_count, secondary_count, dominant_size, secondary_size, singleton_sizes, first_class = spec
    for attempt in range(128):
        rng = _rng(seed, split, index, attempt)
        used = set()
        try:
            dominant = _random_polyomino(rng, dominant_size, used=used)
            used.add(dominant)
            secondary = _random_polyomino(rng, secondary_size, used=used)
            used.add(secondary)
            singleton_shapes = []
            for size in singleton_sizes:
                shape = _random_polyomino(rng, size, used=used)
                used.add(shape)
                singleton_shapes.append(shape)
        except ValueError:
            continue
        shapes = {"dominant": dominant, "secondary": secondary}
        shapes.update({f"single_{i}": shape for i, shape in enumerate(singleton_shapes)})
        order = _object_order(dominant_count, secondary_count, len(singleton_shapes), first_class)
        colors = list(range(1, 10))
        rng.shuffle(colors)
        grid = [[0] * width for _ in range(height)]
        occupied = set()
        ok = True
        for object_index, class_name in enumerate(order):
            if not _place_object(
                grid,
                occupied,
                shapes[class_name],
                colors[object_index],
                TARGETS[object_index],
                rng,
            ):
                ok = False
                break
        if not ok:
            continue
        try:
            validate_input(grid)
        except ValueError:
            continue
        return grid
    raise ValueError(f"unable to realize {split}[{index}] after 128 attempts")


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _policy(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    episode = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        source_split = "train" if split == "train" else "test"
        for index in range(count):
            grid = sample_input(seed, index, split=source_split)
            signature = json.dumps(grid, separators=(",", ":"))
            if signature in seen:
                raise ValueError(f"duplicate input at {split}[{index}]")
            seen.add(signature)
            episode[split].append({"input": grid, "output": claimed_output(grid, settings)})
    return episode
