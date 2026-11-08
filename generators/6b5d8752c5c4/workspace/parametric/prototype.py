"""Deterministic divider-source family for ARC task 6b5d8752c5c4.

The exact canonical default uses each object's bounding-box midpoint.  The
nearby setting uses the colored marker in each short-axis lane.  Generated
markers are deliberately off-center so visible demonstrations identify the
selected setting instead of leaving the nuisance stripe causally ambiguous.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Any, Iterable

TASK_ID = "6b5d8752c5c4"
SCHEMA = "6b5d8752c5c4-divider-source-parametric-v1"
DIVIDER_SOURCES = ("bbox_midpoint", "lane_marker")
DEFAULT_DIVIDER_SOURCE = "bbox_midpoint"
MIN_DEMOS = 2
MAX_DEMOS = 6
QUERY_COUNT = 4
MAX_SEED = 2**63 - 1
CANONICAL_PROGRAM = '(rule! (lambda (g)\n         (let* ((h (rows g))\n                (w (cols g)))\n           (begin\n             (define comps (objects-multicolor g 0))\n             (foldl (lambda (obj acc)\n                      (let* ((r1 (obj-r1 obj))\n                             (c1 (obj-c1 obj))\n                             (r2 (obj-r2 obj))\n                             (c2 (obj-c2 obj))\n                             (oh (+ 1 (- r2 r1)))\n                             (ow (+ 1 (- c2 c1)))\n                             (split-horizontal (> oh ow))\n                             (cut (quotient (if split-horizontal oh ow) 2)))\n                        (foldl (lambda (p out)\n                                 (if (!= (at g (first p) (second p)) 9)\n                                     out\n                                     (let* ((lr (- (first p) r1))\n                                            (lc (- (second p) c1))\n                                            (dr (if split-horizontal\n                                                    (if (< lr cut) -1 1)\n                                                    0))\n                                            (dc (if split-horizontal\n                                                    0\n                                                    (if (< lc cut) -1 1)))\n                                            (nr (+ (first p) dr))\n                                            (nc (+ (second p) dc)))\n                                       (if (in-bounds? nr nc h w)\n                                           (set-cell out nr nc 9)\n                                           out))))\n                               acc\n                               (obj-cells obj))))\n                    (empty-grid h w 0)\n                    comps)))))'

LANE_MARKER_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (begin
             (define comps (objects-multicolor g 0))
             (foldl (lambda (obj acc)
                      (let* ((r1 (obj-r1 obj))
                             (c1 (obj-c1 obj))
                             (r2 (obj-r2 obj))
                             (c2 (obj-c2 obj))
                             (oh (+ 1 (- r2 r1)))
                             (ow (+ 1 (- c2 c1)))
                             (split-horizontal (> oh ow)))
                        (foldl (lambda (p out)
                                 (if (!= (at g (first p) (second p)) 9)
                                     out
                                     (let* ((marker
                                             (first
                                              (filter
                                               (lambda (q)
                                                 (and
                                                  (if split-horizontal
                                                      (= (second q) (second p))
                                                      (= (first q) (first p)))
                                                  (!= (at g (first q) (second q)) 9)))
                                               (obj-cells obj))))
                                            (dr (if split-horizontal
                                                    (if (< (first p) (first marker)) -1 1)
                                                    0))
                                            (dc (if split-horizontal
                                                    0
                                                    (if (< (second p) (second marker)) -1 1)))
                                            (nr (+ (first p) dr))
                                            (nc (+ (second p) dc)))
                                       (if (in-bounds? nr nc h w)
                                           (set-cell out nr nc 9)
                                           out))))
                               acc
                               (obj-cells obj))))
                    (empty-grid h w 0)
                    comps)))))"""
PROGRAMS = {
    "bbox_midpoint": CANONICAL_PROGRAM,
    "lane_marker": LANE_MARKER_PROGRAM,
}

# Each shape is (height, width, must touch a non-movement canvas edge).
_DEMO_PROFILES = (
    (8, ((2, 4, True),)),
    (12, ((4, 2, True), (2, 4, True))),
    (16, ((4, 8, True), (8, 4, False), (3, 6, False))),
    (20, ((5, 10, True), (10, 5, True), (3, 6, False), (6, 3, False))),
    (24, ((6, 12, True), (12, 6, True), (4, 8, False), (8, 4, False), (2, 4, False))),
    (28, ((6, 12, True), (12, 6, True), (5, 10, False), (10, 5, False), (4, 8, False))),
)
_QUERY_PROFILES = (
    (30, ((6, 12, True), (12, 6, True), (5, 10, True), (10, 5, True), (4, 8, False), (8, 4, False))),
    (22, ((5, 10, True), (10, 5, True), (4, 8, False), (8, 4, False))),
    (18, ((4, 8, True), (8, 4, True), (3, 6, False), (6, 3, False))),
    (26, ((6, 12, True), (12, 6, True), (4, 8, False), (8, 4, False), (3, 6, False))),
)

Grid = list[list[int]]
Box = tuple[int, int, int, int]
Shape = tuple[int, int, bool]


def _literal_int(name: str, value: Any, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _source(value: Any) -> str:
    if not isinstance(value, str) or value not in DIVIDER_SOURCES:
        raise ValueError(f"divider_source must be one of {DIVIDER_SOURCES}")
    return value


def validate_settings(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"divider_source"}:
        raise ValueError("settings must contain exactly divider_source")
    return {"divider_source": _source(settings["divider_source"])}


def program(settings: Any) -> str:
    return PROGRAMS[validate_settings(settings)["divider_source"]]


def _rng(seed: int, slot: int, namespace: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:divider-source-v1:{seed}:{slot}:{namespace}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _grid(grid: Any) -> Grid:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty sequence")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be non-empty")
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        raise ValueError("grid dimensions must not exceed 30x30")
    result: Grid = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        copied: list[int] = []
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9:
                raise ValueError("grid cells must be literal ARC colors 0..9")
            copied.append(cell)
        result.append(copied)
    return result


def _components8(grid: Grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                point = stack.pop()
                cells.append(point)
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if not (dr or dc):
                            continue
                        nxt = (point[0] + dr, point[1] + dc)
                        if (
                            0 <= nxt[0] < height
                            and 0 <= nxt[1] < width
                            and grid[nxt[0]][nxt[1]] != 0
                            and nxt not in seen
                        ):
                            seen.add(nxt)
                            stack.append(nxt)
            result.append(sorted(cells))
    return result


def _box_cells(box: Box) -> set[tuple[int, int]]:
    row, col, height, width = box
    return {(r, c) for r in range(row, row + height) for c in range(col, col + width)}


def _halo(canvas: int, box: Box) -> set[tuple[int, int]]:
    row, col, height, width = box
    return {
        (r, c)
        for r in range(max(0, row - 1), min(canvas, row + height + 1))
        for c in range(max(0, col - 1), min(canvas, col + width + 1))
    }


def _envelope(box: Box) -> set[tuple[int, int]]:
    row, col, height, width = box
    if width > height:
        return {(r, c) for r in range(row, row + height) for c in range(col - 1, col + width + 1)}
    return {(r, c) for r in range(row - 1, row + height + 1) for c in range(col, col + width)}


def _candidates(canvas: int, shape: Shape) -> list[Box]:
    height, width, edge = shape
    if width > height:
        rows: Iterable[int] = sorted({0, canvas - height}) if edge else range(1, canvas - height)
        cols: Iterable[int] = range(1, canvas - width)
    else:
        rows = range(1, canvas - height)
        cols = sorted({0, canvas - width}) if edge else range(1, canvas - width)
    return [(row, col, height, width) for row in rows for col in cols]


def _place(canvas: int, shapes: tuple[Shape, ...], rng: random.Random) -> list[Box]:
    ordered = sorted(enumerate(shapes), key=lambda item: item[1][0] * item[1][1], reverse=True)
    candidate_lists: list[tuple[int, list[Box]]] = []
    for index, shape in ordered:
        options = _candidates(canvas, shape)
        rng.shuffle(options)
        candidate_lists.append((index, options))
    selected: dict[int, Box] = {}

    def search(index: int, forbidden: set[tuple[int, int]], envelopes: set[tuple[int, int]]) -> bool:
        if index == len(candidate_lists):
            return True
        original, options = candidate_lists[index]
        for box in options:
            cells = _box_cells(box)
            envelope = _envelope(box)
            if cells & forbidden or envelope & envelopes:
                continue
            selected[original] = box
            if search(index + 1, forbidden | _halo(canvas, box), envelopes | envelope):
                return True
            selected.pop(original, None)
        return False

    if not search(0, set(), set()):
        raise RuntimeError(f"cannot place {len(shapes)} bars on {canvas}x{canvas}")
    return [selected[index] for index in range(len(shapes))]


def _transform(grid: Grid, code: int) -> Grid:
    result = [list(row) for row in grid]
    rotations = code
    if code >= 4:
        result = [list(reversed(row)) for row in result]
        rotations -= 4
    for _ in range(rotations):
        result = [list(row) for row in zip(*reversed(result))]
    return result


def _marker_positions(long_side: int, lanes: int, rng: random.Random) -> list[int]:
    centers = {long_side // 2 - 1, long_side // 2}
    outer = [index for index in range(long_side) if index not in centers]
    if len(outer) < 2:
        raise RuntimeError("bar too short for an off-center marker lesson")
    positions = [0, long_side - 1]
    while len(positions) < lanes:
        positions.append(rng.choice(outer))
    rng.shuffle(positions)
    return positions[:lanes]


def _draw_bar(grid: Grid, box: Box, marker_color: int, rng: random.Random) -> None:
    row, col, height, width = box
    for r, c in _box_cells(box):
        grid[r][c] = 9
    if width > height:
        for lane, position in enumerate(_marker_positions(width, height, rng)):
            grid[row + lane][col + position] = marker_color
    else:
        for lane, position in enumerate(_marker_positions(height, width, rng)):
            grid[row + position][col + lane] = marker_color


def _build_input(seed: int, slot: int, profile: tuple[int, tuple[Shape, ...]]) -> Grid:
    canvas, shapes = profile
    boxes = _place(canvas, shapes, _rng(seed, slot, "layout"))
    marker_color = 1 + ((seed + 3 * slot) % 8)
    grid = [[0 for _ in range(canvas)] for _ in range(canvas)]
    for index, box in enumerate(boxes):
        _draw_bar(grid, box, marker_color, _rng(seed, slot * 1000 + index, "markers"))
    grid = _transform(grid, _rng(seed, slot, "transform").randrange(8))
    analyze_input(grid)
    return grid


def episode_inputs(seed: Any, demos: Any = 3, queries: Any = 4) -> list[Grid]:
    seed = _literal_int("seed", seed, 0, MAX_SEED)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    schedule = list(enumerate(_DEMO_PROFILES[:demos])) + [
        (100 + index, profile) for index, profile in enumerate(_QUERY_PROFILES[:queries])
    ]
    grids = [_build_input(seed, slot, profile) for slot, profile in schedule]
    if len({tuple(map(tuple, grid)) for grid in grids}) != len(grids):
        raise RuntimeError("input schedule produced a duplicate grid")
    return grids


def _record(grid: Grid, cells: list[tuple[int, int]]) -> dict[str, Any]:
    canvas = len(grid)
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    if len(cells) != height * width:
        raise ValueError("component must fill its bounding box")
    short, long = min(height, width), max(height, width)
    if short < 2 or long != 2 * short:
        raise ValueError("component must be a 2:1 bar")
    colors = {grid[r][c] for r, c in cells}
    others = colors - {9}
    if 9 not in colors or len(others) != 1:
        raise ValueError("bar must contain 9 and one marker color")
    marker_color = next(iter(others))
    if not 1 <= marker_color <= 8:
        raise ValueError("marker color must be 1..8")
    orientation = "wide" if width > height else "tall"
    positions: list[int] = []
    if orientation == "wide":
        for row in range(r0, r1 + 1):
            found = [col - c0 for col in range(c0, c1 + 1) if grid[row][col] == marker_color]
            if len(found) != 1:
                raise ValueError("wide bar needs one marker per row")
            positions.append(found[0])
    else:
        for col in range(c0, c1 + 1):
            found = [row - r0 for row in range(r0, r1 + 1) if grid[row][col] == marker_color]
            if len(found) != 1:
                raise ValueError("tall bar needs one marker per column")
            positions.append(found[0])
    touches = sorted(
        side
        for side, condition in (
            ("top", r0 == 0), ("bottom", r1 == canvas - 1),
            ("left", c0 == 0), ("right", c1 == canvas - 1),
        )
        if condition
    )
    if orientation == "wide" and {"left", "right"} & set(touches):
        raise ValueError("wide bar touches a movement boundary")
    if orientation == "tall" and {"top", "bottom"} & set(touches):
        raise ValueError("tall bar touches a movement boundary")
    centers = {long // 2 - 1, long // 2}
    return {
        "bbox": [r0, c0, r1, c1],
        "shape": [height, width],
        "orientation": orientation,
        "marker_color": marker_color,
        "marker_positions": positions,
        "off_center_marker_count": sum(position not in centers for position in positions),
        "touches": touches,
    }


def analyze_input(grid: Any) -> dict[str, Any]:
    checked = _grid(grid)
    if len(checked) != len(checked[0]) or not 8 <= len(checked) <= 30:
        raise ValueError("family inputs must be square 8..30")
    components = _components8(checked)
    if not components:
        raise ValueError("input needs at least one bar")
    records = [_record(checked, cells) for cells in components]
    marker_colors = {record["marker_color"] for record in records}
    if len(marker_colors) != 1:
        raise ValueError("all bars must share one marker color")
    marker_color = next(iter(marker_colors))
    return {
        "canvas": len(checked),
        "object_count": len(records),
        "marker_color": marker_color,
        "colors": [0, 9, marker_color],
        "orientations": sorted({record["orientation"] for record in records}),
        "edge_contact_count": sum(bool(record["touches"]) for record in records),
        "off_center_marker_count": sum(record["off_center_marker_count"] for record in records),
        "bars": records,
    }


def _lane_markers(grid: Grid, cells: list[tuple[int, int]], orientation: str) -> dict[int, int]:
    result: dict[int, int] = {}
    for row, col in cells:
        if grid[row][col] == 9:
            continue
        lane, divider = (col, row) if orientation == "tall" else (row, col)
        if lane in result:
            raise ValueError("lane has multiple markers")
        result[lane] = divider
    return result


def apply_setting(grid: Any, divider_source: Any) -> Grid:
    source = _source(divider_source)
    checked = _grid(grid)
    analyze_input(checked)
    height, width = len(checked), len(checked[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for cells in _components8(checked):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        object_height, object_width = r1 - r0 + 1, c1 - c0 + 1
        orientation = "tall" if object_height > object_width else "wide"
        markers = _lane_markers(checked, cells, orientation)
        midpoint = r0 + object_height // 2 if orientation == "tall" else c0 + object_width // 2
        for row, col in cells:
            if checked[row][col] != 9:
                continue
            coordinate = row if orientation == "tall" else col
            divider = midpoint
            if source == "lane_marker":
                divider = markers[col if orientation == "tall" else row]
            delta = -1 if coordinate < divider else 1
            nr = row + (delta if orientation == "tall" else 0)
            nc = col + (delta if orientation == "wide" else 0)
            if not (0 <= nr < height and 0 <= nc < width):
                raise ValueError("shifted cell left the grid")
            if (nr, nc) in occupied:
                raise ValueError("shifted cells collided")
            occupied.add((nr, nc))
            output[nr][nc] = 9
    return output


def _rival_output(grid: Any, rival: str) -> Grid:
    checked = _grid(grid)
    analyze_input(checked)
    height, width = len(checked), len(checked[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    global_marker = min(
        (r, c)
        for r, row in enumerate(checked)
        for c, value in enumerate(row)
        if value not in (0, 9)
    )
    for cells in _components8(checked):
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        object_height, object_width = r1 - r0 + 1, c1 - c0 + 1
        orientation = "tall" if object_height > object_width else "wide"
        markers = _lane_markers(checked, cells, orientation)
        for row, col in cells:
            if checked[row][col] != 9:
                continue
            if rival == "wrong_axis":
                if orientation == "tall":
                    coordinate, divider, axis = col, c0 + object_width // 2, "wide"
                else:
                    coordinate, divider, axis = row, r0 + object_height // 2, "tall"
                delta = -1 if coordinate < divider else 1
            else:
                axis = orientation
                coordinate = row if orientation == "tall" else col
                if rival == "global_first_marker":
                    divider = global_marker[0] if orientation == "tall" else global_marker[1]
                    delta = -1 if coordinate < divider else 1
                elif rival == "canvas_midpoint":
                    divider = height // 2 if orientation == "tall" else width // 2
                    delta = -1 if coordinate < divider else 1
                elif rival == "toward_marker":
                    divider = markers[col if orientation == "tall" else row]
                    delta = 1 if coordinate < divider else -1
                else:
                    raise ValueError(f"unknown rival: {rival}")
            nr = row + (delta if axis == "tall" else 0)
            nc = col + (delta if axis == "wide" else 0)
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = 9
    return output


def assess_demos(train: Any, chosen: Any) -> dict[str, Any]:
    chosen = _source(chosen)
    if not isinstance(train, list) or not train:
        raise ValueError("train must be a non-empty pair list")
    for pair in train:
        if not isinstance(pair, dict) or not {"input", "output"} <= set(pair):
            raise ValueError("each pair needs input and output")
    declared: dict[str, dict[str, Any]] = {}
    survivors: list[str] = []
    for source in DIVIDER_SOURCES:
        fits = [apply_setting(pair["input"], source) == pair["output"] for pair in train]
        declared[source] = {
            "fits_all_demos": all(fits),
            "first_eliminating_demo": next((i for i, fit in enumerate(fits) if not fit), None),
        }
        if all(fits):
            survivors.append(source)
    shortcuts: dict[str, dict[str, Any]] = {}
    for rival in ("global_first_marker", "wrong_axis", "toward_marker", "canvas_midpoint"):
        fits = [_rival_output(pair["input"], rival) == pair["output"] for pair in train]
        shortcuts[rival] = {
            "fits_all_demos": all(fits),
            "first_eliminating_demo": next((i for i, fit in enumerate(fits) if not fit), None),
        }
    return {
        "chosen": chosen,
        "declared_survivors": survivors,
        "declared": declared,
        "shortcuts": shortcuts,
        "all_named_shortcuts_rejected": all(not row["fits_all_demos"] for row in shortcuts.values()),
        "scope": "Finite two-setting and four named-rival audit on visible demonstrations only.",
    }


def generate(seed: Any, settings: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    checked_settings = validate_settings(settings)
    seed = _literal_int("seed", seed, 0, MAX_SEED)
    demos = _literal_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _literal_int("queries", queries, QUERY_COUNT, QUERY_COUNT)
    source = checked_settings["divider_source"]
    inputs = episode_inputs(seed, demos, queries)
    pairs = [
        {"input": copy.deepcopy(grid), "output": apply_setting(grid, source)}
        for grid in inputs
    ]
    episode = {
        "schema": SCHEMA,
        "status": "proposed",
        "task_id": TASK_ID,
        "seed": seed,
        "settings": copy.deepcopy(checked_settings),
        "train": pairs[:demos],
        "test": pairs[demos : demos + queries],
        "program_solution": PROGRAMS[source],
    }
    if assess_demos(episode["train"], source)["declared_survivors"] != [source]:
        raise RuntimeError("demonstrations do not identify the chosen setting")
    return episode


def public_payload(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def first_turn_payload(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "train": copy.deepcopy(episode["train"]),
        "test": [{"input": copy.deepcopy(episode["test"][0]["input"])}],
    }


def _main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--divider-source", choices=DIVIDER_SOURCES, default=DEFAULT_DIVIDER_SOURCE)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--public", action="store_true")
    args = parser.parse_args()
    episode = generate(args.seed, {"divider_source": args.divider_source}, args.demos, args.queries)
    print(json.dumps(public_payload(episode) if args.public else episode, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
