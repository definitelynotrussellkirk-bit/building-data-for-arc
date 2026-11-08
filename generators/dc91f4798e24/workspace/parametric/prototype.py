"""Matched-input component-count and count-conditioned area prototype.

The production generator is unchanged. Its exact local placement and component
helpers are reused here; Python labels are claims for protected Racket replay.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

from reviewer_support import load_selected_generator


TASK_ID = "dc91f4798e24"
MODES = ("all", "blue_count_threshold")
ROOT = Path(__file__).resolve().parents[4]
_BASE, _BASE_PATH, _BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_MAX_ATTEMPTS = 256


def validate_settings(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must be exactly {'mode': 'all' or 'blue_count_threshold'}")
    return settings["mode"]


def _integer(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 nonempty list rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")


def _connectivity(connectivity):
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("connectivity must be the exact integer 4 or 8")


def components(grid, color, connectivity=4):
    """Return monochromatic components as lists of (row, column) pairs."""
    _grid(grid)
    _integer("color", color, 0, 9)
    _connectivity(connectivity)
    return _BASE._components(grid, color, connectivity)


def component_areas(grid, connectivity=4):
    """Return sorted target-component areas, keyed by integer colors 1/2/3."""
    _grid(grid)
    _connectivity(connectivity)
    return {color: sorted(map(len, _BASE._components(grid, color, connectivity)))
            for color in (1, 2, 3)}


def bars(counts):
    """Paint the shared three-row histogram, including the zero-count case."""
    if (type(counts) not in (tuple, list) or len(counts) != 3
            or any(type(n) is not int or n < 0 for n in counts)):
        raise ValueError("counts must be three nonnegative exact integers")
    width = max(1, *counts)
    return [[color if c < count else 0 for c in range(width)]
            for color, count in zip((1, 2, 3), counts)]


def solve(grid, mode="all"):
    """Diagnostic Python claim: A counts blue bodies; B filters by that count."""
    validate_settings({"mode": mode})
    by_color = component_areas(grid)
    threshold = len(by_color[1])
    counts = [len(by_color[c]) if mode == "all"
              else sum(area >= threshold for area in by_color[c]) for c in (1, 2, 3)]
    return bars(counts)


def _binary_objects(grid):
    binary = [[int(v != 0) for v in row] for row in grid]
    return _BASE._components(binary, 1)


def rival_outputs(grid, mode="blue_count_threshold"):
    """Explicit finite teaching rivals; these are diagnostic Python claims.

    Fixed cutoffs 1..31 cover all distinct cutoff behavior on the admitted
    component areas (at most 12). Values <=1 and >12 are equivalent there.
    Binary B counts one foreground island for each target color it contains.
    """
    validate_settings({"mode": mode})
    by_color = component_areas(grid)
    by_eight = component_areas(grid, 8)
    k = len(by_color[1])
    islands = _binary_objects(grid)
    island_colors = [{grid[r][c] for r, c in island} for island in islands]
    binary_blue = sum(1 in colors for colors in island_colors)

    def selected(areas, threshold, compare=lambda area, cutoff: area >= cutoff):
        return bars([sum(compare(area, threshold) for area in areas[c]) for c in (1, 2, 3)])

    def binary_selected(threshold):
        return bars([sum(color in colors and len(island) >= threshold
                         for island, colors in zip(islands, island_colors)) for color in (1, 2, 3)])

    counts = [len(by_color[c]) if mode == "all"
              else sum(area >= k for area in by_color[c]) for c in (1, 2, 3)]
    rivals = {
        "other_mode": solve(grid, "blue_count_threshold" if mode == "all" else "all"),
        "raw_pixel_histogram": bars([sum(by_color[c]) for c in (1, 2, 3)]),
        "sorted_counts_ascending": bars(sorted(counts)),
        "sorted_counts_descending": bars(sorted(counts, reverse=True)),
        "replicate_blue_count": bars([counts[0]] * 3),
    }
    if mode == "all":
        rivals["eight_components"] = bars([len(by_eight[c]) for c in (1, 2, 3)])
        rivals["binary_foreground"] = binary_selected(1)
        for cutoff in range(2, 32):
            rivals[f"fixed_area_cutoff_{cutoff}"] = selected(by_color, cutoff)
        return rivals

    for cutoff in range(1, 32):
        rivals[f"fixed_area_cutoff_{cutoff}"] = selected(by_color, cutoff)
    rivals.update({
        "blue_pixel_threshold": selected(by_color, sum(by_color[1])),
        "red_count_threshold": selected(by_color, len(by_color[2])),
        "green_count_threshold": selected(by_color, len(by_color[3])),
        "largest_blue_area_threshold": selected(by_color, max(by_color[1], default=0)),
        "less_equal_threshold": selected(by_color, k, lambda area, cutoff: area <= cutoff),
        "strict_greater_threshold": selected(by_color, k, lambda area, cutoff: area > cutoff),
        "exact_threshold": selected(by_color, k, lambda area, cutoff: area == cutoff),
        "eight_A": selected(by_color, len(by_eight[1])),
        "eight_B": selected(by_eight, k),
        "eight_both": selected(by_eight, len(by_eight[1])),
        "binary_A": selected(by_color, binary_blue),
        "binary_B": binary_selected(k),
        "binary_both": binary_selected(binary_blue),
        "retained_pixel_area": bars([sum(area for area in by_color[c] if area >= k)
                                      for c in (1, 2, 3)]),
    })
    bbox_areas = {c: [_bbox_area(body) for body in _BASE._components(grid, c)] for c in (1, 2, 3)}
    rivals["bounding_box_area"] = selected(bbox_areas, k)
    return rivals


def _bbox_area(body):
    rows, columns = zip(*body)
    return (max(rows) - min(rows) + 1) * (max(columns) - min(columns) + 1)


def grid_stats(grid):
    """JSON-safe geometry metrics; target arrays follow blue, red, green order."""
    by_color = component_areas(grid)
    by_eight = component_areas(grid, 8)
    h, w = len(grid), len(grid[0])
    k = len(by_color[1])
    target_bodies = [body for color in (1, 2, 3) for body in _BASE._components(grid, color)]
    foreground = sum(v != 0 for row in grid for v in row)
    edges = {"top": grid[0], "bottom": grid[-1],
             "left": [row[0] for row in grid], "right": [row[-1] for row in grid]}
    return {
        "height": h, "width": w,
        "counts4": [len(by_color[c]) for c in (1, 2, 3)],
        "counts8": [len(by_eight[c]) for c in (1, 2, 3)],
        "areas": {str(c): by_color[c] for c in (1, 2, 3)},
        "threshold": k,
        "eligible_counts": [sum(area >= k for area in by_color[c]) for c in (1, 2, 3)],
        "foreground_cells": foreground,
        "target_cells": sum(sum(a) for a in by_color.values()),
        "density": foreground / (h * w),
        "border_components": sum(any(r in (0, h - 1) or c in (0, w - 1) for r, c in body)
                                 for body in target_bodies),
        "border_sides": [side for side, values in edges.items() if any(v in (1, 2, 3) for v in values)],
        "distractor_cells": sum(v >= 4 for row in grid for v in row),
        "distractor_colors": sorted({v for row in grid for v in row if v >= 4}),
    }


def _rng(seed, split, index, stream, attempt=0):
    key = f"{TASK_ID}|parametric-v1|{seed}|{split}|{index}|{stream}|{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _profile(seed, split, index):
    """Areas are chosen once; a failed placement never shrinks the requested job."""
    rng = _rng(seed, split, index, "areas")
    if split == "train":
        profiles = (
            (7, 8, ([2, 3], [1, 1, 3], [2, 3])),
            (9, 10, ([1, 2, 3, 4], [3, 4], [1, 4])),
            (10, 12, ([1, 3, 5], [1, 2, 3, 4], [3, 6])),
            (11, 13, ([1, 3, 4, 6], [2, 4, 6], [1, 2, 4, 5, 6])),
            (14, 16, ([1, 4, 5, 6, 8], [rng.randint(1, 9) for _ in range(8)],
                      [rng.randint(1, 9) for _ in range(6)])),
            (16, 18, ([1, 3, 5, 6, 8, 10], [rng.randint(1, 10) for _ in range(9)],
                      [rng.randint(1, 10) for _ in range(7)])),
        )
    else:
        profiles = (
            (7, 8, ([1, 3], [2, 4], [1, 2, 3])),
            (12, 16, ([2, 3, 5], [rng.randint(1, 7) for _ in range(7)],
                      [rng.randint(1, 7) for _ in range(5)])),
            (24, 24, ([1, 4, 5, 6, 9], [rng.randint(2, 11) for _ in range(13)],
                      [rng.randint(2, 11) for _ in range(17)])),
            (30, 30, ([1, 5, 6, 7, 9, 12], [rng.randint(3, 12) for _ in range(18)],
                      [rng.randint(3, 12) for _ in range(21)])),
        )
    return profiles[index]


def _bridge_diagonal_blue(grid, rng):
    """Join two diagonal blue bodies in binary foreground using a foreign cell."""
    bodies = _BASE._components(grid, 1)
    for left in bodies:
        left_set = set(left)
        for right in bodies:
            if right is left:
                continue
            for r, c in right:
                for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                    if (r + dr, c + dc) in left_set:
                        bridges = [(r + dr, c), (r, c + dc)]
                        rng.shuffle(bridges)
                        rr, cc = bridges[0]
                        if grid[rr][cc] == 0:
                            grid[rr][cc] = rng.randint(4, 9)
                        return True
    return False


def _geometry_ok(grid, split, index):
    if split == "train" and index == 0:
        return len(_BASE._components(grid, 1, 8)) == 1
    if split == "train" and index == 1:
        return any(len(body) == 3 and _bbox_area(body) == 4
                   for color in (1, 2, 3) for body in _BASE._components(grid, color))
    if split == "test" and index == 3:
        edges = (grid[0], grid[-1], [row[0] for row in grid], [row[-1] for row in grid])
        if not all(any(v in (1, 2, 3) for v in edge) for edge in edges):
            return False
        return all(sum(v in (1, 2, 3) for row in rows for v in row[start:start + 15]) >= 25
                   for rows in (grid[:15], grid[15:]) for start in (0, 15))
    return True


def _draw(seed, split, index):
    h, w, by_color = _profile(seed, split, index)
    counts = tuple(map(len, by_color))
    sizes = [size for group in by_color for size in group]
    for attempt in range(_MAX_ATTEMPTS):
        grid = _BASE._place(h, w, counts, sizes, True,
                            _rng(seed, split, index, "placement", attempt))
        if grid is None or not _geometry_ok(grid, split, index):
            continue
        noise_rng = _rng(seed, split, index, "noise", attempt)
        if split == "train" and index == 0 and not _bridge_diagonal_blue(grid, noise_rng):
            continue
        free = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0]
        noise_rng.shuffle(free)
        noise_count = max(3, h * w // 18)
        for r, c in free[:noise_count]:
            grid[r][c] = noise_rng.randint(4, 9)
        actual = component_areas(grid)
        if any(actual[color] != sorted(expected) for color, expected in zip((1, 2, 3), by_color)):
            raise RuntimeError(f"Placement violated requested areas: seed={seed}, split={split}, index={index}")
        return grid
    raise RuntimeError(f"Placement exhausted after {_MAX_ATTEMPTS} attempts: seed={seed}, "
                       f"split={split}, index={index}, shape={(h, w)}, counts={counts}, areas={sizes}")


def generate(seed, settings, demos=3, queries=4):
    """Build one episode with independent split/index RNGs and fixed count limits."""
    mode = validate_settings(settings)
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, 6)
    _integer("queries", queries, 1, 4)
    train = [_draw(seed, "train", i) for i in range(demos)]
    test = [_draw(seed, "test", i) for i in range(queries)]
    signatures = [tuple(map(tuple, grid)) for grid in train + test]
    if len(set(signatures)) != len(signatures):
        raise RuntimeError(f"Duplicate generated input: seed={seed}")
    return {"train": [{"input": grid, "output": solve(grid, mode)} for grid in train],
            "test": [{"input": grid, "output": solve(grid, mode)} for grid in test]}

