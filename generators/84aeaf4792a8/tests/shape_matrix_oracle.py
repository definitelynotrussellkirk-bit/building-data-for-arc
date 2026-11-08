"""Independent pixel oracle for the shape-similarity repair regressions.

No generator helpers or workspace probes are imported. Expected shape classes
are enumerated directly from connected subsets of a 3 by 3 lattice.
"""
from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from functools import lru_cache
from importlib import util
from itertools import combinations
from pathlib import Path
import sys


try:
    from reviewer_support import canonical_pairs, find_root
except ModuleNotFoundError as exc:
    if exc.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, find_root


TASK_ID = "84aeaf4792a8"
ROOT = find_root(__file__)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator():
    candidates = (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"No selected generator under {ROOT}")
    name = "shape_matrix_generator_under_review"
    spec = util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def normalize(cells):
    top = min(row for row, col in cells)
    left = min(col for row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def rotation_key(cells):
    shape = normalize(cells)
    rotations = []
    for _ in range(4):
        rotations.append(shape)
        shape = normalize(tuple((col, -row) for row, col in shape))
    return min(rotations)


def reflection_key(cells):
    return min(rotation_key(cells), rotation_key([(row, -col) for row, col in cells]))


@dataclass(frozen=True)
class Component:
    color: int
    cells: tuple
    bbox: tuple

    @property
    def shape(self):
        return normalize(self.cells)


def components(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            queue = deque([(row, col)])
            visited.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in CARDINAL:
                    neighbor = (r + dr, c + dc)
                    nr, nc = neighbor
                    if (0 <= nr < height and 0 <= nc < width
                            and neighbor not in visited and grid[nr][nc] == color):
                        visited.add(neighbor)
                        queue.append(neighbor)
            bbox = (min(r for r, c in cells), min(c for r, c in cells),
                    max(r for r, c in cells), max(c for r, c in cells))
            found.append(Component(color, tuple(sorted(cells)), bbox))
    return sorted(found, key=lambda obj: obj.bbox[:2])


def relation_matrix(objects, key=rotation_key):
    keys = [key(obj.cells) for obj in objects]
    return [[5 if r == c else 8 if keys[r] == keys[c] else 0
             for c in range(len(objects))] for r in range(len(objects))]


def solve(grid):
    return relation_matrix(components(grid))


def area_bbox(cells):
    shape = normalize(cells)
    sides = sorted((1 + max(r for r, c in shape), 1 + max(c for r, c in shape)))
    return len(shape), tuple(sides)


def rival_color_order(grid):
    ordered = sorted(components(grid), key=lambda obj: (obj.color, *obj.bbox[:2]))
    return relation_matrix(ordered)


def rival_fixed_four(grid):
    actual = solve(grid)
    return [[5 if r == c else actual[r][c] if r < len(actual) and c < len(actual) else 0
             for c in range(4)] for r in range(4)]


def rival_first_pair(grid):
    result = solve(grid)
    if len(result) >= 2:
        result[0][1] = result[1][0] = 8
    return result


INDEPENDENT_RIVALS = {
    "area_bbox": lambda grid: relation_matrix(components(grid), area_bbox),
    "reflections": lambda grid: relation_matrix(components(grid), reflection_key),
    "translation_only": lambda grid: relation_matrix(components(grid), normalize),
    "color_order": rival_color_order,
    "fixed_four": rival_fixed_four,
    "first_pair": rival_first_pair,
}


def observed(grid):
    objects = components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_components": len(objects),
        "n_families": len({rotation_key(obj.cells) for obj in objects}),
        "n_distinct_colors": len({obj.color for obj in objects}),
    }


def partition(grid):
    counts = Counter(rotation_key(obj.cells) for obj in components(grid))
    return tuple(sorted(counts.values(), reverse=True))


def assert_domain(grid):
    assert isinstance(grid, list) and 8 <= len(grid) <= 18
    assert all(isinstance(row, list) and 12 <= len(row) <= 22 for row in grid)
    assert len({len(row) for row in grid}) == 1
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    objects = components(grid)
    assert 2 <= len(objects) <= 6
    owners = {cell: index for index, obj in enumerate(objects) for cell in obj.cells}
    for index, obj in enumerate(objects):
        assert 3 <= len(obj.cells) <= 5
        assert obj.bbox[2] - obj.bbox[0] < 3 and obj.bbox[3] - obj.bbox[1] < 3
        for r, c in obj.cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    assert owners.get((r + dr, c + dc), index) == index


def draw(specs, height=12, width=14):
    grid = [[0] * width for _ in range(height)]
    for color, (top, left), cells in specs:
        for r, c in cells:
            assert grid[top + r][left + c] == 0
            grid[top + r][left + c] = color
    return grid


L3 = ((0, 0), (0, 1), (1, 0))
L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
J4 = ((0, 1), (1, 1), (2, 0), (2, 1))
L4_ROTATED = ((0, 0), (0, 1), (0, 2), (1, 0))
T4 = ((0, 0), (0, 1), (0, 2), (1, 1))


def distinguishing_grid():
    return draw(((5, (1, 1), L4), (2, (1, 8), J4),
                 (4, (7, 2), L4_ROTATED), (3, (7, 8), T4)))


@lru_cache(maxsize=1)
def supported_shape_classes():
    classes = set()
    lattice = [(r, c) for r in range(3) for c in range(3)]
    for size in (3, 4, 5):
        for selected in combinations(lattice, size):
            cells = set(selected)
            reached = {selected[0]}
            frontier = [selected[0]]
            while frontier:
                r, c = frontier.pop()
                neighbors = {(r + dr, c + dc) for dr, dc in CARDINAL}
                new = (neighbors & cells) - reached
                reached.update(new)
                frontier.extend(new)
            if reached == cells:
                classes.add(rotation_key(cells))
    return frozenset(classes)
