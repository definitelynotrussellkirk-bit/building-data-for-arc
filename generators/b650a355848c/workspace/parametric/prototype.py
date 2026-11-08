"""Parametric marker assignment for b650a355848c.

The canonical setting independently gives each pink shape its nearest marker,
allowing marker reuse.  The alternative computes the minimum-total-distance
one-to-one assignment before stacking the recolored shape crops.  Inputs are
matched across settings; Python outputs are claims until protected Racket
qualification re-executes the exact programs.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import random
from typing import Iterable

TASK_ID = "b650a355848c"
POLICIES = ("independent_nearest", "minimum_bijection")
HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")

# The alternate keeps the canonical extraction/cropping rule, but inserts a
# global search over marker permutations.  Search order only breaks exact cost
# ties; admitted samples require a unique optimum.
MINIMUM_BIJECTION = r"""(rule! (lambda (g) (let* ((h (rows g)) (w (cols g))) (let* ((all-objs (objects g 0)) (shapes (filter (lambda (o) (= (obj-color o) 6)) all-objs)) (markers (let ((s (list))) (for* ((r (range 0 h)) (c (range 0 w))) (let ((v (at g r c))) (when (and (!= v 0) (!= v 6)) (set! s (cons (list r c v) s))))) s)) (dist-to-bbox (lambda (mr mc r1 r2 c1 c2) (let ((dr (if (and (<= r1 mr) (<= mr r2)) 0 (min (abs (- mr r1)) (abs (- mr r2))))) (dc (if (and (<= c1 mc) (<= mc c2)) 0 (min (abs (- mc c1)) (abs (- mc c2)))))) (+ dr dc)))) (is-vertical (> h w)) (shape-key (lambda (shape) (with-bbox shape (r1 c1 r2 c2) (if is-vertical r1 c1)))) (sorted-shapes (sort shapes (lambda (a b) (< (shape-key a) (shape-key b))))) (best-result (letrec ((remove-marker (lambda (target xs) (cond ((null? xs) (list)) ((equal? (car xs) target) (cdr xs)) (else (cons (car xs) (remove-marker target (cdr xs))))))) (search (lambda (ss ms assignment total best) (if (null? ss) (if (< total (first best)) (list total (reverse assignment)) best) (let loop ((choices ms) (current-best best)) (if (null? choices) current-best (let* ((m (car choices)) (shape (car ss)) (d (with-bbox shape (r1 c1 r2 c2) (dist-to-bbox (first m) (second m) r1 r2 c1 c2))) (candidate (search (cdr ss) (remove-marker m ms) (cons m assignment) (+ total d) current-best))) (loop (cdr choices) candidate)))))))) (search sorted-shapes markers (list) 0 (list 999999 (list))))) (assigned-markers (second best-result)) (shape-info (let loop ((ss sorted-shapes) (ms assigned-markers) (out (list))) (if (null? ss) (reverse out) (let* ((shape (car ss)) (marker (car ms)) (cells (obj-cells shape))) (with-bbox shape (r1 c1 r2 c2) (loop (cdr ss) (cdr ms) (cons (list cells r1 r2 c1 c2 (third marker)) out))))))) (n (length shape-info)) (out-h (if is-vertical (* n 4) 4)) (out-w (if is-vertical 4 (* n 4)))) (build-grid out-h out-w (gr gc) (let* ((idx (if is-vertical (quotient gr 4) (quotient gc 4))) (base-r (if is-vertical (* idx 4) 0)) (base-c (if is-vertical 0 (* idx 4))) (lr (- gr base-r)) (lc (- gc base-c)) (shape (list-ref shape-info idx)) (cells (first shape)) (sr1 (second shape)) (sc1 (fourth shape)) (color (sixth shape))) (let check ((cs cells)) (cond ((null? cs) 0) ((and (= (first (car cs)) (+ sr1 lr)) (= (second (car cs)) (+ sc1 lc))) color) (else (check (cdr cs)))))))))))"""

# Connected shapes, each 6..10 cells with a <=4x4 bounding box.
_PATTERNS = (
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2), (3, 1), (3, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
)

# The first two demonstrations use complementary 2-D teaching scenes.  The
# first separates bbox-nearest from nearest-cell and separates the global
# optimum from greedy/axis pairing.  The second makes nearest-cell equal the
# independent rule, so it also refutes that shortcut for the global setting.
# Transposing the second scene exercises the vertical output branch at no extra
# demonstration cost.
_TEACHING_LAYOUTS = (
    {
        "patterns": (
            ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (2, 0), (3, 0)),
            ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)),
            ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
        ),
        "anchors": ((8, 1), (3, 6), (8, 14)),
        "markers": ((6, 3), (2, 9), (10, 5)),
    },
    {
        "patterns": (
            ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
            ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (3, 2), (3, 1), (3, 0)),
            ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)),
        ),
        "anchors": ((3, 0), (4, 9), (8, 15)),
        "markers": ((0, 7), (11, 8), (0, 2)),
    },
)

# (height, width, shape count, transpose after construction)
_DEMO_PROFILES = (
    (12, 18, 3, False),
    (12, 18, 3, True),
    (14, 22, 4, False),
    (14, 22, 4, True),
    (18, 27, 5, False),
    (18, 27, 5, True),
)
_QUERY_PROFILES = (
    (11, 17, 3, False),
    (12, 17, 3, True),
    (24, 27, 4, False),
    (30, 30, 5, False),
)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _exact_int(name: str, value, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings) -> str:
    if (type(settings) is not dict or set(settings) != {"assignment_policy"}
            or type(settings["assignment_policy"]) is not str
            or settings["assignment_policy"] not in POLICIES):
        raise ValueError("settings must contain exactly one declared assignment_policy")
    return settings["assignment_policy"]


def program(settings) -> str:
    return CANONICAL if _policy(settings) == "independent_nearest" else MINIMUM_BIJECTION


def _validate_grid(grid) -> tuple[int, int]:
    if (type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]
            or not 1 <= len(grid) <= 30 or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty rectangular grid no larger than 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must contain exact integer colors 0..9")
    return len(grid), width


def _components(grid):
    height, width = _validate_grid(grid)
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
                current = stack.pop()
                cells.append(current)
                for dr, dc in _DIRS4:
                    neighbor = (current[0] + dr, current[1] + dc)
                    if (0 <= neighbor[0] < height and 0 <= neighbor[1] < width
                            and neighbor not in seen and grid[neighbor[0]][neighbor[1]] != 0):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(cells)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(cells)
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _distance(marker: tuple[int, int, int], bbox: tuple[int, int, int, int]) -> int:
    row, col, _color = marker
    top, left, bottom, right = bbox
    dr = 0 if top <= row <= bottom else min(abs(row - top), abs(row - bottom))
    dc = 0 if left <= col <= right else min(abs(col - left), abs(col - right))
    return dr + dc


def _scene_parts(grid):
    height, width = _validate_grid(grid)
    shapes = []
    for cells in _components(grid):
        row, col = cells[0]
        if grid[row][col] == 6:
            shapes.append({"cells": sorted(cells), "bbox": _bbox(cells)})
    # Canonical source conses while scanning row-major, so ties prefer reverse row-major.
    markers = [(row, col, grid[row][col]) for row in range(height) for col in range(width)
               if grid[row][col] not in (0, 6)]
    markers.reverse()
    if not shapes or len(shapes) != len(markers):
        raise ValueError("input needs equal nonzero counts of color-6 shapes and singleton markers")
    vertical = height > width
    shapes.sort(key=lambda item: item["bbox"][0] if vertical else item["bbox"][1])
    return height, width, vertical, shapes, markers


def _distance_matrix(shapes, markers):
    return [[_distance(marker, shape["bbox"]) for marker in markers] for shape in shapes]


def _minimum_assignment(matrix):
    count = len(matrix)
    ranked = []
    for permutation in itertools.permutations(range(count)):
        ranked.append((sum(matrix[i][permutation[i]] for i in range(count)), permutation))
    ranked.sort(key=lambda item: item[0])  # stable: permutation order breaks equal totals
    if not ranked:
        raise ValueError("empty assignment")
    unique = len(ranked) == 1 or ranked[0][0] < ranked[1][0]
    return list(ranked[0][1]), ranked[0][0], unique


def observables(grid):
    _height, _width, _vertical, shapes, markers = _scene_parts(grid)
    matrix = _distance_matrix(shapes, markers)
    independent = [min(range(len(markers)), key=lambda index: matrix[row][index])
                   for row in range(len(shapes))]
    bijection, total, unique = _minimum_assignment(matrix)
    distance_rows = []
    for row, distances in enumerate(matrix):
        best = min(distances)
        distance_rows.append({
            "shape_index": row,
            "distances": distances,
            "nearest_marker_indices": [i for i, value in enumerate(distances) if value == best],
        })
    return {
        "shape_count": len(shapes),
        "marker_count": len(markers),
        "distance_rows": distance_rows,
        "independent_marker_indices": independent,
        "minimum_bijection_marker_indices": bijection,
        "minimum_bijection_total": total,
        "minimum_bijection_unique": unique,
        "marker_colors": [marker[2] for marker in markers],
    }


def solve(grid, settings):
    policy = _policy(settings)
    _height, _width, vertical, shapes, markers = _scene_parts(grid)
    matrix = _distance_matrix(shapes, markers)
    if policy == "independent_nearest":
        assignment = [min(range(len(markers)), key=lambda index: matrix[row][index])
                      for row in range(len(shapes))]
    else:
        assignment, _total, _unique = _minimum_assignment(matrix)
    output_height = 4 * len(shapes) if vertical else 4
    output_width = 4 if vertical else 4 * len(shapes)
    output = [[0] * output_width for _ in range(output_height)]
    for index, (shape, marker_index) in enumerate(zip(shapes, assignment, strict=True)):
        top, left, _bottom, _right = shape["bbox"]
        base_row = 4 * index if vertical else 0
        base_col = 0 if vertical else 4 * index
        color = markers[marker_index][2]
        for row, col in shape["cells"]:
            output[base_row + row - top][base_col + col - left] = color
    return output


def _rng(seed: int, stream: str, index: int = 0) -> random.Random:
    material = f"b650-parametric-v1:{seed}:{stream}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _pattern_size(pattern):
    return max(row for row, _ in pattern) + 1, max(col for _, col in pattern) + 1


def _transform_pattern(pattern, rng):
    points = list(pattern)
    height, width = _pattern_size(points)
    if rng.randrange(2):
        points = [(row, width - 1 - col) for row, col in points]
    if rng.randrange(2):
        points = [(height - 1 - row, col) for row, col in points]
    return tuple(sorted(points))


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _reflect(grid, horizontal: bool, vertical: bool):
    result = [row[:] for row in grid]
    if horizontal:
        result = [row[::-1] for row in result]
    if vertical:
        result.reverse()
    return result


def _isolated(grid, row, col) -> bool:
    if grid[row][col] != 0:
        return False
    return all(not (0 <= row + dr < len(grid) and 0 <= col + dc < len(grid[0])
                    and grid[row + dr][col + dc] != 0) for dr, dc in _DIRS4)


def _marker_candidates(grid, bbox, distance):
    top, left, bottom, right = bbox
    result = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if not _isolated(grid, row, col):
                continue
            if _distance((row, col, 1), bbox) == distance:
                result.append((row, col))
    return result


def _marker_layout_valid(boxes, positions) -> bool:
    """Check the full assignment contrast before committing marker colors.

    Local distance-to-own-shape placement is insufficient: a marker can tie or
    steal another shape's nearest slot.  This finite global check is invariant
    under the later reflection/transpose and avoids seed-dependent retries.
    """
    matrix = [
        [_distance((row, col, 1), bbox) for row, col in positions]
        for bbox in boxes
    ]
    if any(distances.count(min(distances)) != 1 for distances in matrix):
        return False
    independent = [min(range(len(positions)), key=lambda index: distances[index])
                   for distances in matrix]
    bijection, _total, unique = _minimum_assignment(matrix)
    return unique and len(set(independent)) < len(boxes) and independent != bijection


def _choose_marker_positions(grid, boxes, initial, rng):
    """Construct a complete globally valid marker layout by bounded search."""
    height, width = len(grid), len(grid[0])
    candidate_lists = []
    for bbox in boxes[len(initial):]:
        candidates = [
            cell for cell in _marker_candidates(grid, bbox, 2)
            if cell not in initial
            and all(abs(cell[0] - row) + abs(cell[1] - col) > 1
                    for row, col in initial)
        ]
        # Boundary contacts are useful stress, while seeded tie order preserves
        # content diversity without relying on probabilistic retry loops.
        rng.shuffle(candidates)
        candidates.sort(key=lambda cell: min(
            cell[0], height - 1 - cell[0], cell[1], width - 1 - cell[1]
        ))
        if not candidates:
            raise RuntimeError("profile cannot place an isolated marker")
        candidate_lists.append(candidates)

    def search(index, selected):
        if index == len(candidate_lists):
            positions = list(initial) + selected
            return positions if _marker_layout_valid(boxes, positions) else None
        occupied = list(initial) + selected
        for candidate in candidate_lists[index]:
            if any(abs(candidate[0] - row) + abs(candidate[1] - col) <= 1
                   for row, col in occupied):
                continue
            result = search(index + 1, selected + [candidate])
            if result is not None:
                return result
        return None

    result = search(0, [])
    if result is None:
        raise RuntimeError("profile has no globally valid marker layout")
    return result


def _build_scene(seed: int, stream: str, index: int, profile):
    height, width, count, transpose = profile
    rng = _rng(seed, stream, index)
    teaching = stream == "demos" and index < 2 and profile in _DEMO_PROFILES[:2]
    if teaching:
        layout = _TEACHING_LAYOUTS[index]
        patterns = list(layout["patterns"])
        anchors = list(layout["anchors"])
        row0 = col0 = right0 = None
    else:
        pool = tuple(pattern for pattern in _PATTERNS if count < 5 or len(pattern) >= 7)
        patterns = [_transform_pattern(pool[rng.randrange(len(pool))], rng)
                    for _ in range(count)]
        sizes = [_pattern_size(pattern) for pattern in patterns]
        # The first pair is deliberately close.  The shared marker is closer to both;
        # the spare marker makes a globally cheaper bijection by serving shape zero.
        row0 = 3
        col0 = 2
        right0 = col0 + sizes[0][1] - 1
        anchors = [(row0, col0), (row0, right0 + 3)]
        if count == 3:
            anchors.append((height - sizes[2][0], width - sizes[2][1]))
        elif count == 4:
            anchors.extend([
                (height - sizes[2][0], max(2, width // 2 - sizes[2][1] // 2)),
                (height - sizes[3][0], width - sizes[3][1]),
            ])
        elif count == 5:
            # Spread the last three over the canvas, retaining a bottom/right contact.
            anchors.extend([
                (max(row0 + 5, height // 2 - sizes[2][0] // 2),
                 max(2, width // 2 - sizes[2][1] // 2)),
                (height - sizes[3][0], max(2, width // 3 - sizes[3][1] // 2)),
                (height - sizes[4][0], width - sizes[4][1]),
            ])
    grid = [[0] * width for _ in range(height)]
    boxes = []
    for pattern, (top, left) in zip(patterns, anchors, strict=True):
        cells = [(top + row, left + col) for row, col in pattern]
        if any(not (0 <= row < height and 0 <= col < width) or grid[row][col] != 0
               for row, col in cells):
            raise RuntimeError("profile cannot place shape")
        for row, col in cells:
            grid[row][col] = 6
        boxes.append(_bbox(cells))
    if teaching:
        marker_positions = list(layout["markers"])
        if (not all(_isolated(grid, row, col) for row, col in marker_positions)
                or not _marker_layout_valid(boxes, marker_positions)):
            raise RuntimeError("fixed teaching marker layout is invalid")
    else:
        initial_markers = [(row0 - 1, right0 + 1), (row0 - 1, 0)]
        if not all(_isolated(grid, row, col) for row, col in initial_markers):
            raise RuntimeError("teaching markers are not isolated")
        marker_positions = _choose_marker_positions(grid, boxes, initial_markers, rng)
    colors = rng.sample([1, 2, 3, 4, 5, 7, 8, 9], count)
    if teaching:
        matrix = [
            [_distance((row, col, 1), bbox) for row, col in marker_positions]
            for bbox in boxes
        ]
        global_assignment, _total, _unique = _minimum_assignment(matrix)
        if sorted(range(count), key=lambda marker: colors[marker]) == global_assignment:
            colors[0], colors[1] = colors[1], colors[0]
    for (row, col), color in zip(marker_positions, colors, strict=True):
        if not _isolated(grid, row, col):
            raise RuntimeError("marker collision after placement")
        grid[row][col] = color
    grid = _reflect(grid, False if teaching else bool(rng.randrange(2)),
                    bool(rng.randrange(2)))
    if transpose:
        grid = _transpose(grid)
    facts = observables(grid)
    if (facts["shape_count"] != count or facts["marker_count"] != count
            or not facts["minimum_bijection_unique"]
            or len(set(facts["independent_marker_indices"])) >= count
            or any(len(row["nearest_marker_indices"]) != 1 for row in facts["distance_rows"])
            or solve(grid, {"assignment_policy": POLICIES[0]})
               == solve(grid, {"assignment_policy": POLICIES[1]})):
        raise RuntimeError(f"constructed profile lost its assignment contrast: {facts}")
    return grid


def generate(seed, settings, demos=3, queries=4):
    _exact_int("seed", seed, 0, 2**63 - 1)
    _exact_int("demos", demos, 2, 6)
    _exact_int("queries", queries, 1, 4)
    _policy(settings)
    training = [_build_scene(seed, "demos", index, _DEMO_PROFILES[index])
                for index in range(demos)]
    query_profiles = list(_QUERY_PROFILES)
    _rng(seed, "query-order").shuffle(query_profiles)
    tests = [_build_scene(seed, "queries", index, query_profiles[index])
             for index in range(queries)]
    grids = training + tests
    if len({_grid_bytes(grid) for grid in grids}) != len(grids):
        raise RuntimeError("sampler produced duplicate inputs")
    def pairs(inputs):
        return [{"input": grid, "output": solve(grid, settings)} for grid in inputs]
    return {
        "train": pairs(training),
        "test": pairs(tests),
        "program_solution": program(settings),
        "settings": dict(settings),
        "seed": seed,
    }


def _grid_bytes(grid) -> bytes:
    return json.dumps(grid, separators=(",", ":")).encode("utf-8")


def _public_helpers():
    path = HERE.parents[3] / "shared" / "runtime" / "reviewer_support.py"
    name = "_b650_public_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_challenge(episode, query_index=0):
    _exact_int("query_index", query_index, 0, len(episode["test"]) - 1)
    projection = {
        "train": episode["train"],
        "test": [{"input": episode["test"][query_index]["input"]}],
    }
    return json.loads(_public_helpers().public_challenge_bytes(projection))


def public_id(episode, query_index=0):
    return _public_helpers().public_challenge_id(public_challenge(episode, query_index))
