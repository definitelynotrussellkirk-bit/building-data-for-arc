"""Deterministic authoring prototype for center-nearest green-object scope.

The canonical setting repaints only the Manhattan-center-nearest color-3
component.  The alternative first selects that component, binds its occupied
cell count, then repaints every color-3 component with that count.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
from typing import Iterable

HOME = Path(__file__).resolve().parent
PROGRAM_FILES = {
    "nearest_only": HOME / "canonical.rkt",
    "nearest_size_class": HOME / "size_class.rkt",
}
SETTINGS = tuple(PROGRAM_FILES)
RIVALS = (
    "euclidean_nearest",
    "centroid_euclidean",
    "first_green",
    "last_green",
    "largest_green",
    "smallest_green",
    "nearest_cell",
    "paint_all_green",
    "fixed_size_five",
    "bbox_area_class",
    "bbox_dimensions_class",
    "selected_shape_class",
    "at_least_selected_size",
    "at_most_selected_size",
)

# These selectors are intentionally retained for query-aware audit.  On the
# current generated support they fit the two demonstrations only when they also
# agree with the canonical selector on every query, so they are not declared
# ambiguity rivals.  Tests pin that property so future sampler drift is caught.
SHADOW_SELECTORS = ("centroid_manhattan", "bbox_edge_nearest")


def _exact_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _scope(settings: object) -> str:
    if not isinstance(settings, dict) or set(settings) != {"paint_scope"}:
        raise ValueError("settings must contain exactly paint_scope")
    value = settings["paint_scope"]
    if type(value) is not str or value not in SETTINGS:
        raise ValueError("unknown paint_scope")
    return value


def program(settings: dict) -> str:
    return PROGRAM_FILES[_scope(settings)].read_text(encoding="utf-8")


def _validate_grid(grid: object) -> list[list[int]]:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        raise ValueError("grid must be rectangular and 1..30")
    width = len(grid[0])
    out: list[list[int]] = []
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        new_row = []
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("grid cells must be exact ARC integers")
            new_row.append(cell)
        out.append(new_row)
    return out


def _components(grid: list[list[int]], color: int = 3) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            rows = [x[0] for x in cells]
            cols = [x[1] for x in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            result.append({"cells": cells, "bbox": bbox, "size": len(cells)})
    return result


def _metric_key(obj: dict, h: int, w: int, metric: str) -> tuple:
    r1, c1, r2, c2 = obj["bbox"]
    dr = (r1 + r2) - (h - 1)
    dc = (c1 + c2) - (w - 1)
    if metric == "manhattan":
        distance = abs(dr) + abs(dc)
    elif metric == "euclidean":
        distance = dr * dr + dc * dc
    elif metric in {"centroid_manhattan", "centroid_euclidean"}:
        size = obj["size"]
        row_delta = 2 * sum(r for r, _ in obj["cells"]) - size * (h - 1)
        col_delta = 2 * sum(c for _, c in obj["cells"]) - size * (w - 1)
        if metric == "centroid_manhattan":
            # All terms share this object's positive denominator; compare the
            # exact rational distances by cross multiplication in the key.
            distance = Fraction(abs(row_delta) + abs(col_delta), size)
        else:
            distance = Fraction(row_delta * row_delta + col_delta * col_delta, size * size)
    elif metric == "bbox_edge_nearest":
        center_r2, center_c2 = h - 1, w - 1
        dr_edge = 0 if 2 * r1 <= center_r2 <= 2 * r2 else min(abs(2 * r1 - center_r2), abs(2 * r2 - center_r2))
        dc_edge = 0 if 2 * c1 <= center_c2 <= 2 * c2 else min(abs(2 * c1 - center_c2), abs(2 * c2 - center_c2))
        distance = dr_edge + dc_edge
    elif metric == "nearest_cell":
        distance = min(abs(2 * r - (h - 1)) + abs(2 * c - (w - 1)) for r, c in obj["cells"])
    else:
        raise ValueError("unknown metric")
    return (distance, obj["bbox"])


def _selected(components: list[dict], h: int, w: int, kind: str) -> dict:
    if not components:
        raise ValueError("at least one green component is required")
    if kind == "first_green":
        return min(components, key=lambda obj: obj["bbox"])
    if kind == "last_green":
        return max(components, key=lambda obj: obj["bbox"])
    if kind == "largest_green":
        return min(components, key=lambda obj: (-obj["size"], obj["bbox"]))
    if kind == "smallest_green":
        return min(components, key=lambda obj: (obj["size"], obj["bbox"]))
    metric_by_kind = {
        "euclidean_nearest": "euclidean",
        "centroid_manhattan": "centroid_manhattan",
        "centroid_euclidean": "centroid_euclidean",
        "bbox_edge_nearest": "bbox_edge_nearest",
        "nearest_cell": "nearest_cell",
    }
    metric = metric_by_kind.get(kind, "manhattan")
    return min(components, key=lambda obj: _metric_key(obj, h, w, metric))


def _paint(grid: list[list[int]], objects: Iterable[dict]) -> list[list[int]]:
    out = deepcopy(grid)
    for obj in objects:
        for r, c in obj["cells"]:
            out[r][c] = 7
    return out


def _apply_with_selector(grid: list[list[int]], scope: str, selector: str) -> list[list[int]]:
    checked = _validate_grid(grid)
    objects = _components(checked)
    target = _selected(objects, len(checked), len(checked[0]), selector)
    if scope == "nearest_only":
        chosen = [target]
    else:
        chosen = [obj for obj in objects if obj["size"] == target["size"]]
    return _paint(checked, chosen)


def apply_python(grid: list[list[int]], settings: dict) -> list[list[int]]:
    return _apply_with_selector(grid, _scope(settings), "manhattan")


def _normalized_shape(obj: dict) -> tuple[tuple[int, int], ...]:
    min_row = min(r for r, _ in obj["cells"])
    min_col = min(c for _, c in obj["cells"])
    return tuple(sorted((r - min_row, c - min_col) for r, c in obj["cells"]))


def _bbox_dimensions(obj: dict) -> tuple[int, int]:
    r1, c1, r2, c2 = obj["bbox"]
    return r2 - r1 + 1, c2 - c1 + 1


def apply_rival(grid: list[list[int]], rival: str, scope: str) -> list[list[int]]:
    if scope not in SETTINGS:
        raise ValueError("unknown scope")
    checked = _validate_grid(grid)
    objects = _components(checked)
    selector_rivals = {
        "euclidean_nearest",
        "centroid_manhattan",
        "centroid_euclidean",
        "bbox_edge_nearest",
        "first_green",
        "last_green",
        "largest_green",
        "smallest_green",
        "nearest_cell",
    }
    if rival in selector_rivals:
        return _apply_with_selector(checked, scope, rival)
    if rival == "paint_all_green":
        return _paint(checked, objects)
    if rival == "fixed_size_five":
        return _paint(checked, [obj for obj in objects if obj["size"] == 5])
    target = _selected(objects, len(checked), len(checked[0]), "manhattan")
    if rival == "bbox_area_class":
        target_dims = _bbox_dimensions(target)
        area = target_dims[0] * target_dims[1]
        return _paint(checked, [obj for obj in objects if _bbox_dimensions(obj)[0] * _bbox_dimensions(obj)[1] == area])
    if rival == "bbox_dimensions_class":
        dimensions = _bbox_dimensions(target)
        return _paint(checked, [obj for obj in objects if _bbox_dimensions(obj) == dimensions])
    if rival == "selected_shape_class":
        shape = _normalized_shape(target)
        return _paint(checked, [obj for obj in objects if _normalized_shape(obj) == shape])
    if rival == "at_least_selected_size":
        return _paint(checked, [obj for obj in objects if obj["size"] >= target["size"]])
    if rival == "at_most_selected_size":
        return _paint(checked, [obj for obj in objects if obj["size"] <= target["size"]])
    raise ValueError("unknown rival")


def _seed(seed: int, split: str, index: int) -> int:
    raw = f"e9cd770abc01|{seed}|{split}|{index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _blank(h: int, w: int) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint_cells(grid: list[list[int]], cells: Iterable[tuple[int, int]], color: int) -> None:
    for r, c in cells:
        if grid[r][c] != 0:
            raise ValueError("teaching scene overlap")
        grid[r][c] = color


def _flip(grid: list[list[int]], rng: random.Random) -> list[list[int]]:
    out = deepcopy(grid)
    if rng.randrange(2):
        out.reverse()
    if rng.randrange(2):
        out = [list(reversed(row)) for row in out]
    return out


def _teaching_metric_scope(seed: int) -> list[list[int]]:
    """One scene separates L1/L2, nearest/same-size, and bbox-area rivals."""
    grid = _blank(13, 11)
    # Euclidean winner (size 4), but not Manhattan winner.
    _paint_cells(grid, [(1, 8), (1, 9), (2, 8), (3, 8)], 3)
    # Manhattan winner: occupied size 5 in a 3x3 bbox.
    _paint_cells(grid, [(10, 3), (11, 2), (11, 3), (12, 3), (12, 4)], 3)
    # Equal occupied size, different bbox area.
    _paint_cells(grid, [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)], 3)
    # Equal occupied size and equal bbox area, still far from center.
    _paint_cells(grid, [(9, 8), (10, 8), (11, 8), (11, 9), (11, 10)], 3)
    _paint_cells(grid, [(6, 3), (6, 4), (7, 3)], 9)
    _paint_cells(grid, [(6, 9), (7, 8), (7, 9)], 6)
    # This lesson is deliberately not reflected: nearest-cell has a distance
    # tie here, and reflection would let bbox ordering erase the contrast.
    return grid


def _ring(top: int, left: int, side: int = 5) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(top, top + side)
        for c in range(left, left + side)
        if r in {top, top + side - 1} or c in {left, left + side - 1}
    ]


def _teaching_center_cell_contrast(seed: int) -> list[list[int]]:
    """Separate bbox-center selection from nearest-cell and size shortcuts."""
    grid = _blank(21, 21)
    # Earliest component makes row-major/first-object selection observably wrong.
    _paint_cells(grid, [(0, 0), (0, 1)], 3)
    # Remote occupied-size companion for the canonical center ring.
    _paint_cells(grid, _ring(0, 16), 3)
    # Its bbox is centered exactly on the grid, but no occupied cell is central.
    _paint_cells(grid, _ring(8, 8), 3)
    # This singleton has the same bbox-center distance (zero) and loses the
    # canonical bbox tie, while winning the nearest-occupied-cell shortcut.
    _paint_cells(grid, [(10, 10)], 3)
    # A larger 5x5 object defeats largest-object and bbox-area shortcuts.
    _paint_cells(grid, [(r, c) for r in range(16, 21) for c in range(0, 5)], 3)
    _paint_cells(grid, [(5, 2), (5, 3), (6, 2)], 4)
    _paint_cells(grid, [(14, 14), (14, 15), (15, 15)], 8)
    return grid


SHAPES = {
    2: [[(0, 0), (0, 1)], [(0, 0), (1, 0)]],
    3: [[(0, 0), (1, 0), (1, 1)], [(0, 0), (0, 1), (0, 2)]],
    4: [[(0, 0), (0, 1), (1, 0), (1, 1)], [(0, 1), (1, 0), (1, 1), (1, 2)]],
    5: [[(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)], [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]],
    6: [[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)], [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)]],
}


def _shape(size: int, rng: random.Random) -> list[tuple[int, int]]:
    cells = list(rng.choice(SHAPES[size]))
    if rng.randrange(2):
        cells = [(r, -c) for r, c in cells]
    if rng.randrange(2):
        cells = [(-r, c) for r, c in cells]
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _place(
    grid: list[list[int]],
    occupied_halo: set[tuple[int, int]],
    shape: list[tuple[int, int]],
    top: int,
    left: int,
    color: int,
) -> bool:
    h, w = len(grid), len(grid[0])
    cells = {(top + r, left + c) for r, c in shape}
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    if cells & occupied_halo:
        return False
    for r, c in cells:
        grid[r][c] = color
    occupied_halo.update(
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= r + dr < h and 0 <= c + dc < w
    )
    return True


def _scene(seed: int, split: str, index: int, h: int, w: int) -> list[list[int]]:
    rng = random.Random(_seed(seed, split, index))
    grid = _blank(h, w)
    halo: set[tuple[int, int]] = set()
    target_size = 3 + ((seed + index) % 4)
    anchor = _shape(target_size, rng)
    ah = max(r for r, _ in anchor) + 1
    aw = max(c for _, c in anchor) + 1
    # Keep the selected anchor centered enough to beat every corner object.
    assert _place(grid, halo, anchor, max(0, h // 2 - ah // 2), max(0, w // 2 - aw // 2), 3)
    companion = _shape(target_size, rng)
    assert _place(grid, halo, companion, 1, 1, 3)

    green_specs = [
        (2 + ((target_size + 0) % 5), 1, max(1, w - 6)),
        (2 + ((target_size + 1) % 5), max(1, h - 6), 1),
        (2 + ((target_size + 2) % 5), max(1, h - 6), max(1, w - 6)),
    ]
    for size, top, left in green_specs:
        size = max(2, min(6, size))
        _place(grid, halo, _shape(size, rng), top, left, 3)

    positions = [
        (max(1, h // 4 - 1), max(1, w // 4 - 1)),
        (max(1, h // 4 - 1), max(1, (3 * w) // 4 - 2)),
        (max(1, (3 * h) // 4 - 2), max(1, w // 4 - 1)),
        (max(1, (3 * h) // 4 - 2), max(1, (3 * w) // 4 - 2)),
    ]
    colors = [1, 4, 6, 8, 9]
    for j, (top, left) in enumerate(positions):
        placed = _place(grid, halo, _shape(3 + (j % 3), rng), top, left, colors[(j + seed) % len(colors)])
        if not placed:
            # Search a bounded local neighborhood, preserving deterministic content.
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if _place(grid, halo, _shape(2 + (j % 2), rng), top + dr, left + dc, colors[(j + seed) % len(colors)]):
                        placed = True
                        break
                if placed:
                    break
    return grid


def _all_train_inputs(seed: int) -> list[list[list[int]]]:
    values = [_teaching_metric_scope(seed), _teaching_center_cell_contrast(seed)]
    for index, dims in enumerate(((13, 17), (17, 13), (19, 19), (21, 17)), start=2):
        values.append(_scene(seed, "train", index, *dims))
    return values


def _all_query_inputs(seed: int) -> list[list[list[int]]]:
    dims = ((13, 19), (18, 22), (24, 29), (30, 30))
    return [_scene(seed, "test", index, *shape) for index, shape in enumerate(dims)]


def teaching_report(train: list[dict], settings: dict) -> dict:
    scope = _scope(settings)
    if type(train) is not list or not train:
        raise ValueError("train must be a nonempty pair list")
    pairs = []
    for pair in train:
        if not isinstance(pair, dict) or set(pair) < {"input", "output"}:
            raise ValueError("invalid teaching pair")
        pairs.append((_validate_grid(pair["input"]), _validate_grid(pair["output"])))
    setting_survivors = [
        candidate
        for candidate in SETTINGS
        if all(apply_python(grid, {"paint_scope": candidate}) == output for grid, output in pairs)
    ]
    rival_survivors = [
        rival
        for rival in RIVALS
        if all(apply_rival(grid, rival, scope) == output for grid, output in pairs)
    ]
    return {
        "fit_scope": "demonstrations_only",
        "setting_survivors": setting_survivors,
        "plausible_rival_survivors": rival_survivors,
        "rivals_checked": list(RIVALS),
    }


def generate(seed: int, settings: dict, demos: int, queries: int) -> dict:
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 2, 6)
    _exact_int("queries", queries, 1, 4)
    scope = _scope(settings)
    train_inputs = _all_train_inputs(seed)[:demos]
    test_inputs = _all_query_inputs(seed)[:queries]
    all_inputs = train_inputs + test_inputs
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs]
    if len(serialized) != len(set(serialized)):
        raise ValueError("all demonstration/query inputs must be distinct")
    chosen = {"paint_scope": scope}
    train = [{"input": grid, "output": apply_python(grid, chosen)} for grid in train_inputs]
    test = [{"input": grid, "output": apply_python(grid, chosen)} for grid in test_inputs]
    report = teaching_report(train, chosen)
    if report["setting_survivors"] != [scope] or report["plausible_rival_survivors"]:
        raise ValueError("constructive demonstrations failed to identify the intended rule")
    return {"train": train, "test": test, "program_solution": program(chosen)}
