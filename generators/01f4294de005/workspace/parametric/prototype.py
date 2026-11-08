"""Native size-palette family with an input-derived matching-marker echo.

The canonical setting recolors orange body components in place by area.  The
alternative first performs the same size-to-legend lookup, then consumes the
selected legend color to locate a unique singleton body marker and echoes the
component's normalized shape at that marker.  Input sampling is independent of
the private setting.
"""
from __future__ import annotations

from collections import deque
import hashlib
import itertools
import json
import random
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "01f4294de005"
PARAMETER = "echo_mode"
SETTINGS = ("none", "matching_marker")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "none": _HOME / "none.rkt",
    "matching_marker": _HOME / "matching_marker.rkt",
}
_TRAIN_PROFILES = (
    (13, 16, 4),
    (14, 17, 4),
    (17, 20, 5),
    (20, 24, 5),
    (24, 28, 6),
    (28, 30, 6),
)
_QUERY_PROFILES = (
    (9, 12, 3),
    (16, 20, 4),
    (23, 27, 5),
    (30, 30, 6),
)
_COLORS = (1, 2, 3, 4, 5, 6, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

_SHAPES = {
    1: (
        ((0, 0),),
    ),
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    ),
}
_EDGE_SHAPE_6 = ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2))

RIVAL_NAMES = (
    "no_echo",
    "source_left_to_right",
    "source_top_to_bottom",
    "nearest_marker",
    "width_measure",
    "height_measure",
    "bbox_area_measure",
    "reverse_palette",
    "first_marker",
    "marker_position_rank",
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _setting(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    value = settings[PARAMETER]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return value


def program(settings: dict[str, str]) -> str:
    return _PROGRAMS[_setting(settings)].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int, purpose: str) -> random.Random:
    payload = f"{TASK_ID}|inputs-v3|{seed}|{split}|{index}|{purpose}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _rotate(shape):
    width = max(col for _, col in shape) + 1
    return _normalize((col, width - 1 - row) for row, col in shape)


def _flip(shape):
    width = max(col for _, col in shape) + 1
    return _normalize((row, width - 1 - col) for row, col in shape)


def _variants(shape):
    found = []
    current = _normalize(shape)
    for _ in range(4):
        for candidate in (current, _flip(current)):
            if candidate not in found:
                found.append(candidate)
        current = _rotate(current)
    return tuple(found)


def _shape(size: int, rng: random.Random, *, edge: bool = False):
    if edge and size == 6:
        return _EDGE_SHAPE_6
    base = rng.choice(_SHAPES[size])
    return rng.choice(_variants(base))


def _axis_origins(start: int, end: int) -> list[int]:
    values = list(range(start, end + 1, 4))
    if not values:
        return [start]
    if values[-1] != end:
        if len(values) == 1 or end - values[-2] >= 4:
            values[-1] = end
        elif end - values[-1] >= 4:
            values.append(end)
    return sorted(set(values))


def _slot_order(height: int, width: int, tag: str) -> list[tuple[int, int]]:
    rows = _axis_origins(1, height - 3)
    cols = _axis_origins(0, width - 3)
    slots = [(row, col) for row in rows for col in cols]
    corners = [
        (rows[0], cols[0]),
        (rows[-1], cols[-1]),
        (rows[0], cols[-1]),
        (rows[-1], cols[0]),
    ]
    ordered = []
    for slot in corners:
        if slot not in ordered:
            ordered.append(slot)
    remaining = [slot for slot in slots if slot not in ordered]
    while remaining:
        def score(slot):
            distance = min(abs(slot[0] - row) + abs(slot[1] - col) for row, col in ordered)
            tie = int.from_bytes(hashlib.sha256(f"{tag}|{slot}".encode()).digest()[:8], "big")
            return distance, tie
        choice = max(remaining, key=score)
        ordered.append(choice)
        remaining.remove(choice)
    return ordered


def _source_assignment(slots: list[tuple[int, int]], n: int, rng: random.Random,
                       *, force_edge: bool) -> dict[int, tuple[int, int]]:
    sizes = list(range(1, n + 1))
    candidates = []
    edge_index = slots.index(max(slots)) if force_edge else None
    for perm in itertools.permutations(sizes):
        if edge_index is not None and perm[edge_index] != n:
            continue
        lr = [size for _, size in sorted(zip(slots, perm), key=lambda item: (item[0][1], item[0][0]))]
        tb = [size for _, size in sorted(zip(slots, perm), key=lambda item: item[0])]
        disorder = sum(a != b for a, b in zip(lr, sizes)) + sum(a != b for a, b in zip(tb, sizes))
        if disorder >= n and lr != sizes and tb != sizes:
            candidates.append(perm)
    if not candidates:
        raise RuntimeError("no source-slot assignment defeats rank shortcuts")
    chosen = rng.choice(candidates)
    return {size: slot for slot, size in zip(slots, chosen)}


def _center(slot: tuple[int, int]) -> tuple[int, int]:
    return slot[0] + 1, slot[1] + 1


def _marker_assignment(source_by_size, marker_slots, n, rng):
    sizes = list(range(1, n + 1))
    source_lr = [size for size, _ in sorted(source_by_size.items(), key=lambda item: (item[1][1], item[1][0]))]
    source_tb = [size for size, _ in sorted(source_by_size.items(), key=lambda item: item[1])]
    best = None
    for perm in itertools.permutations(sizes):
        by_size = {size: slot for slot, size in zip(marker_slots, perm)}
        marker_lr = [size for size, _ in sorted(by_size.items(), key=lambda item: (item[1][1], item[1][0]))]
        marker_tb = [size for size, _ in sorted(by_size.items(), key=lambda item: item[1])]
        rank_mismatches = sum(a != b for a, b in zip(source_lr, marker_lr))
        rank_mismatches += sum(a != b for a, b in zip(source_tb, marker_tb))
        nearest_wrong = 0
        for size, source in source_by_size.items():
            nearest = min(
                sizes,
                key=lambda other: (
                    abs(_center(source)[0] - _center(by_size[other])[0])
                    + abs(_center(source)[1] - _center(by_size[other])[1]),
                    other,
                ),
            )
            nearest_wrong += nearest != size
        positional_disorder = sum(a != b for a, b in zip(marker_lr, sizes))
        score = (nearest_wrong, rank_mismatches, positional_disorder, rng.random(), perm)
        if best is None or score > best:
            best = score
    assert best is not None
    return {size: slot for slot, size in zip(marker_slots, best[-1])}


def _paint(grid, shape, origin, color):
    row0, col0 = origin
    for row, col in shape:
        rr, cc = row0 + row, col0 + col
        if not (0 <= rr < len(grid) and 0 <= cc < len(grid[0])):
            raise RuntimeError("shape escaped the scene")
        if grid[rr][cc] != 0:
            raise RuntimeError("scene objects overlap")
        grid[rr][cc] = color


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    if split not in ("train", "test"):
        raise ValueError("split must be train or test")
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    index = _strict_int("index", index, 0, len(profiles) - 1)
    height, width, n = profiles[index]
    grid = [[0 for _ in range(width)] for _ in range(height)]

    palette_rng = _rng(seed, split, index, "palette")
    palette = palette_rng.sample(list(_COLORS), n)
    legend_cols = sorted(palette_rng.sample(range(width), n))
    for col, color in zip(legend_cols, palette):
        grid[0][col] = color

    slots = _slot_order(height, width, f"{seed}|{split}|{index}")
    needed = 2 * n
    if len(slots) < needed:
        raise RuntimeError(f"profile {height}x{width} has only {len(slots)} safe slots for {needed} roles")
    source_slots = slots[:n]
    marker_slots = slots[n:needed]
    layout_rng = _rng(seed, split, index, "layout")
    source_by_size = _source_assignment(
        source_slots, n, layout_rng,
        force_edge=(height, width) == (30, 30),
    )
    marker_by_size = _marker_assignment(source_by_size, marker_slots, n, layout_rng)

    shape_rng = _rng(seed, split, index, "shape")
    for size in range(1, n + 1):
        if split == "train" and index < 2 and size == 3:
            # Constructive witness against bbox-area and straight-bar shortcuts:
            # area=3, but the 2x2 bounding box has area 4.
            shape = ((0, 0), (0, 1), (1, 0))
        else:
            shape = _shape(size, shape_rng, edge=(height, width) == (30, 30) and size == n)
        _paint(grid, shape, source_by_size[size], 7)
        row, col = marker_by_size[size]
        if grid[row][col] != 0:
            raise RuntimeError("marker overlaps scene content")
        grid[row][col] = palette[size - 1]

    # On profiles with spare slots, add a same-palette multi-cell decoy so the
    # second stage must select the unique singleton marker, not merely any cell
    # of the selected color.
    if len(slots) > needed:
        decoy_slot = slots[needed]
        decoy_color = palette[(index + seed) % n]
        _paint(grid, ((0, 0), (0, 1)), decoy_slot, decoy_color)
    spare_colors = [color for color in _COLORS if color not in palette] or list(palette)
    for offset, slot in enumerate(slots[needed + 1:needed + 5]):
        color = spare_colors[offset % len(spare_colors)]
        shape = (
            ((0, 0), (1, 0), (1, 1)),
            ((0, 0), (0, 1), (1, 1)),
            ((0, 1), (1, 0), (1, 1)),
            ((0, 0), (0, 1), (1, 0)),
        )[offset % 4]
        _paint(grid, shape, slot, color)

    analyze_scene(grid)
    return grid


def _validate_grid(value: Any) -> tuple[int, int]:
    if type(value) is not list or not value or type(value[0]) is not list or not value[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(value[0])
    if not 2 <= len(value) <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be within 1..30 and include a body")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer ARC colors")
    return len(value), width


def _components(grid, color, *, row_start=1):
    height, width = _validate_grid(grid)
    unseen = {
        (row, col)
        for row in range(row_start, height)
        for col in range(width)
        if grid[row][col] == color
    }
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = row + dr, col + dc
                if nxt in unseen:
                    unseen.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        found.append(component)
    return found


def _bbox(cells):
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    palette = [value for value in grid[0] if value != 0]
    if not 3 <= len(palette) <= 6 or len(set(palette)) != len(palette) or 7 in palette:
        raise ValueError("legend must contain 3..6 distinct non-orange colors")
    orange = _components(grid, 7)
    if sorted(len(component) for component in orange) != list(range(1, len(palette) + 1)):
        raise ValueError("orange components must have exactly the areas 1..N")
    markers = []
    palette_decoys = []
    for color in palette:
        comps = _components(grid, color)
        singleton = [component for component in comps if len(component) == 1]
        if len(singleton) != 1:
            raise ValueError(f"color {color} needs exactly one singleton body marker")
        markers.append({"color": color, "cells": singleton[0]})
        palette_decoys.extend({"color": color, "cells": component} for component in comps if len(component) > 1)
    facts = {
        "height": height,
        "width": width,
        "palette": palette,
        "orange_components": orange,
        "markers": markers,
        "palette_decoys": palette_decoys,
    }
    marker_by_color = {marker["color"]: next(iter(marker["cells"])) for marker in markers}
    for component in orange:
        color = palette[len(component) - 1]
        anchor = marker_by_color[color]
        for dr, dc in _normalize(component):
            row, col = anchor[0] + dr, anchor[1] + dc
            if not (1 <= row < height and 0 <= col < width):
                raise ValueError("echo shape would leave the grid")
    return facts


def _render(grid, choices, *, include_echo=True):
    output = [row[:] for row in grid]
    for component, color, anchor in choices:
        for row, col in component:
            output[row][col] = color
        if include_echo:
            for dr, dc in _normalize(component):
                output[anchor[0] + dr][anchor[1] + dc] = color
    return output


def apply_rule(grid: list[list[int]], mode: str) -> list[list[int]]:
    if type(mode) is not str or mode not in SETTINGS:
        raise ValueError(f"mode must be one of {SETTINGS!r}")
    facts = analyze_scene(grid)
    marker_by_color = {
        marker["color"]: next(iter(marker["cells"])) for marker in facts["markers"]
    }
    choices = []
    for component in facts["orange_components"]:
        color = facts["palette"][len(component) - 1]
        choices.append((component, color, marker_by_color[color]))
    return _render(grid, choices, include_echo=mode == "matching_marker")


def _ordered(items, key):
    return sorted(items, key=key)


def _component_center(component):
    row0, col0, row1, col1 = _bbox(component)
    return (row0 + row1) / 2, (col0 + col1) / 2


def _measure_choice(facts, component, measure):
    row0, col0, row1, col1 = _bbox(component)
    value = {
        "width": col1 - col0 + 1,
        "height": row1 - row0 + 1,
        "bbox_area": (row1 - row0 + 1) * (col1 - col0 + 1),
    }[measure]
    index = max(1, min(len(facts["palette"]), value)) - 1
    color = facts["palette"][index]
    marker = next(marker for marker in facts["markers"] if marker["color"] == color)
    return color, next(iter(marker["cells"]))


def apply_rival(grid: list[list[int]], name: str) -> list[list[int]]:
    if name not in RIVAL_NAMES:
        raise ValueError(f"unknown rival {name!r}")
    facts = analyze_scene(grid)
    orange = facts["orange_components"]
    markers = facts["markers"]
    intended_by_color = {m["color"]: next(iter(m["cells"])) for m in markers}
    if name == "no_echo":
        return apply_rule(grid, "none")
    if name in ("source_left_to_right", "source_top_to_bottom"):
        key = (
            (lambda comp: (_bbox(comp)[1], _bbox(comp)[0]))
            if name.endswith("left_to_right")
            else (lambda comp: (_bbox(comp)[0], _bbox(comp)[1]))
        )
        mkey = (
            (lambda marker: (next(iter(marker["cells"]))[1], next(iter(marker["cells"]))[0]))
            if name.endswith("left_to_right")
            else (lambda marker: next(iter(marker["cells"])))
        )
        choices = []
        for component, marker in zip(_ordered(orange, key), _ordered(markers, mkey)):
            choices.append((component, marker["color"], next(iter(marker["cells"]))))
        return _render(grid, choices)
    if name == "nearest_marker":
        choices = []
        for component in orange:
            center = _component_center(component)
            marker = min(
                markers,
                key=lambda item: (
                    abs(center[0] - next(iter(item["cells"]))[0])
                    + abs(center[1] - next(iter(item["cells"]))[1]),
                    item["color"],
                ),
            )
            choices.append((component, marker["color"], next(iter(marker["cells"]))))
        return _render(grid, choices)
    if name in ("width_measure", "height_measure", "bbox_area_measure"):
        measure = name.removesuffix("_measure")
        return _render(
            grid,
            [(component, *_measure_choice(facts, component, measure)) for component in orange],
        )
    if name == "reverse_palette":
        choices = []
        for component in orange:
            color = facts["palette"][-len(component)]
            choices.append((component, color, intended_by_color[color]))
        return _render(grid, choices)
    if name == "first_marker":
        marker = min(markers, key=lambda item: next(iter(item["cells"])))
        return _render(
            grid,
            [(component, marker["color"], next(iter(marker["cells"]))) for component in orange],
        )
    if name == "marker_position_rank":
        ordered_markers = _ordered(markers, lambda item: (next(iter(item["cells"]))[1], next(iter(item["cells"]))[0]))
        choices = []
        for component in orange:
            marker = ordered_markers[len(component) - 1]
            choices.append((component, marker["color"], next(iter(marker["cells"]))))
        return _render(grid, choices)
    raise AssertionError(name)


def generate(seed: int, settings: dict[str, str], demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    mode = _setting(settings)
    result = {"train": [], "test": [], "program_solution": program(settings)}
    seen = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, split, index)
            encoded = json.dumps(grid, separators=(",", ":"))
            if encoded in seen:
                raise RuntimeError(f"duplicate generated input at {split}[{index}]")
            seen.add(encoded)
            result[split].append({"input": grid, "output": apply_rule(grid, mode)})
    return result
