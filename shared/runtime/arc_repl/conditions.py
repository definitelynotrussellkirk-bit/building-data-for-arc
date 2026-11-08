"""
Preconditions and selectors — composable predicates for grid cells, objects, and pairs.

Every condition is a function that returns True/False or a mask/list.
These compose with transforms to express rules like:
  "for each pair of objects WHERE same_color AND on_same_row, connect with draw_line"

Categories:
  Cell conditions:   is_color, is_bg, is_border, is_enclosed, has_neighbor, ...
  Object conditions:  is_largest, is_smallest, same_color_as, above, below, ...
  Pair conditions:    same_color, same_shape, aligned, adjacent, overlapping, ...
  Grid conditions:    has_symmetry, has_enclosed, has_lattice, ...
  Selectors:          objects_where, cells_where, pairs_where, ...
"""

import numpy as np
from .grid_ops import (find_objects, find_enclosed, neighbors_4, neighbors_8,
                       bounding_box, where_color, where_adjacent_to,
                       spatial_relation, object_properties)
from collections import deque


# ============================================================
# Cell conditions: (grid, r, c) -> bool
# ============================================================

def is_color(grid, r, c, color):
    return grid[r][c] == color

def is_bg(grid, r, c, bg=0):
    return grid[r][c] == bg

def is_border_cell(grid, r, c):
    h, w = len(grid), len(grid[0])
    return r == 0 or r == h - 1 or c == 0 or c == w - 1

def is_corner_cell(grid, r, c):
    h, w = len(grid), len(grid[0])
    return (r in (0, h-1)) and (c in (0, w-1))

def has_n_neighbors(grid, r, c, color, n, connectivity=4):
    h, w = len(grid), len(grid[0])
    fn = neighbors_4 if connectivity == 4 else neighbors_8
    count = sum(1 for nr, nc in fn(r, c, h, w) if grid[nr][nc] == color)
    return count == n

def is_isolated(grid, r, c, bg=0):
    """Cell has no same-color neighbors."""
    h, w = len(grid), len(grid[0])
    color = grid[r][c]
    return all(grid[nr][nc] != color for nr, nc in neighbors_4(r, c, h, w))


# ============================================================
# Object conditions: (obj) -> bool or (obj1, obj2) -> bool
# ============================================================

def obj_is_color(obj, color):
    return obj["color"] == color

def obj_is_largest(obj, all_objs):
    return obj["size"] == max(o["size"] for o in all_objs)

def obj_is_smallest(obj, all_objs):
    return obj["size"] == min(o["size"] for o in all_objs)

def obj_is_rectangular(obj):
    return object_properties(obj)["is_rectangular"]

def obj_is_line(obj):
    return object_properties(obj)["is_line"]

def obj_is_dot(obj):
    return obj["size"] == 1

def obj_on_border(obj, h, w):
    r1, c1, r2, c2 = obj["bbox"]
    return r1 == 0 or r2 == h - 1 or c1 == 0 or c2 == w - 1


# ============================================================
# Object pair conditions: (obj1, obj2) -> bool
# ============================================================

def same_color(obj1, obj2):
    return obj1["color"] == obj2["color"]

def same_shape(obj1, obj2):
    """Same bounding box dimensions and same relative pixel pattern."""
    r1a, c1a, r2a, c2a = obj1["bbox"]
    r1b, c1b, r2b, c2b = obj2["bbox"]
    if (r2a - r1a) != (r2b - r1b) or (c2a - c1a) != (c2b - c1b):
        return False
    # Compare relative positions
    cells_a = set((r - r1a, c - c1a) for r, c in obj1["cells"])
    cells_b = set((r - r1b, c - c1b) for r, c in obj2["cells"])
    return cells_a == cells_b

def same_size(obj1, obj2):
    return obj1["size"] == obj2["size"]

def on_same_row(obj1, obj2):
    return spatial_relation(obj1, obj2)["same_row"]

def on_same_col(obj1, obj2):
    return spatial_relation(obj1, obj2)["same_col"]

def are_adjacent(obj1, obj2):
    rel = spatial_relation(obj1, obj2)
    return "vertically_adjacent" in rel["relations"] or "horizontally_adjacent" in rel["relations"]

def are_aligned(obj1, obj2, axis="any"):
    """Objects share a row or column center."""
    rel = spatial_relation(obj1, obj2)
    if axis == "row":
        return rel["same_row"]
    elif axis == "col":
        return rel["same_col"]
    return rel["same_row"] or rel["same_col"]


# ============================================================
# Grid conditions: (grid) -> bool
# ============================================================

def has_enclosed_regions(grid, bg=0):
    return find_enclosed(grid, bg).any()

def has_symmetry_lr(grid):
    g = np.array(grid)
    return np.array_equal(g, np.fliplr(g))

def has_symmetry_ud(grid):
    g = np.array(grid)
    return np.array_equal(g, np.flipud(g))

def is_single_object(grid, bg=0):
    return len(find_objects(grid, bg)) == 1

def has_n_objects(grid, n, bg=0):
    return len(find_objects(grid, bg)) == n

def has_color(grid, color):
    return color in np.array(grid)


# ============================================================
# Selectors: filter objects or cells by condition
# ============================================================

def objects_where(grid, condition_fn, bg=0):
    """Return objects matching condition_fn(obj) -> bool."""
    objs = find_objects(grid, bg)
    return [o for o in objs if condition_fn(o)]

def cells_where(grid, condition_fn):
    """Return (r, c) cells where condition_fn(grid, r, c) -> True."""
    h, w = len(grid), len(grid[0])
    return [(r, c) for r in range(h) for c in range(w) if condition_fn(grid, r, c)]

def object_pairs_where(grid, condition_fn, bg=0):
    """Return (obj1, obj2) pairs where condition_fn(obj1, obj2) -> True."""
    objs = find_objects(grid, bg)
    pairs = []
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            if condition_fn(objs[i], objs[j]):
                pairs.append((objs[i], objs[j]))
    return pairs


# ============================================================
# Pathfinding
# ============================================================

def shortest_path(grid, start_r, start_c, end_r, end_c, walkable=None, bg=0, connectivity=4):
    """BFS shortest path between two points.

    walkable: function(grid, r, c) -> bool. Default: cell == bg.
    Returns: list of (r, c) coordinates (path), or [] if no path.
    """
    h, w = len(grid), len(grid[0])
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8

    if walkable is None:
        walkable = lambda g, r, c: g[r][c] == bg

    visited = set()
    parent = {}
    queue = deque([(start_r, start_c)])
    visited.add((start_r, start_c))

    while queue:
        r, c = queue.popleft()
        if r == end_r and c == end_c:
            # Reconstruct path
            path = [(r, c)]
            while (r, c) != (start_r, start_c):
                r, c = parent[(r, c)]
                path.append((r, c))
            return list(reversed(path))

        for nr, nc in neighbor_fn(r, c, h, w):
            if (nr, nc) not in visited and (walkable(grid, nr, nc) or (nr == end_r and nc == end_c)):
                visited.add((nr, nc))
                parent[(nr, nc)] = (r, c)
                queue.append((nr, nc))

    return []  # no path


def shortest_path_between_colors(grid, color1, color2, bg=0):
    """Find shortest path through bg cells connecting any cell of color1 to any cell of color2."""
    g = np.array(grid)
    starts = list(zip(*np.where(g == color1)))
    ends = set(zip(*np.where(g == color2)))
    h, w = g.shape

    if not starts or not ends:
        return []

    # Multi-source BFS from all color1 cells
    visited = set()
    parent = {}
    queue = deque()

    for r, c in starts:
        queue.append((r, c, None))
        visited.add((r, c))

    while queue:
        r, c, _ = queue.popleft()
        if (r, c) in ends:
            path = [(r, c)]
            while (r, c) in parent:
                r, c = parent[(r, c)]
                path.append((r, c))
            return list(reversed(path))

        for nr, nc in neighbors_4(r, c, h, w):
            if (nr, nc) not in visited and (g[nr, nc] == bg or (nr, nc) in ends):
                visited.add((nr, nc))
                parent[(nr, nc)] = (r, c)
                queue.append((nr, nc, None))

    return []


def draw_path(grid, path, color):
    """Draw a path (list of (r,c) tuples) onto the grid."""
    from copy import deepcopy
    g = deepcopy(grid)
    for r, c in path:
        g[r][c] = color
    return g


def connect_objects_shortest(grid, obj1, obj2, color=None, bg=0):
    """Draw shortest path between two objects through background cells."""
    if color is None:
        color = obj1["color"]

    # Find the closest pair of cells between the two objects
    best_path = None
    for r1, c1 in obj1["cells"]:
        for r2, c2 in obj2["cells"]:
            path = shortest_path(grid, r1, c1, r2, c2, bg=bg)
            if path and (best_path is None or len(path) < len(best_path)):
                best_path = path

    if best_path:
        return draw_path(grid, best_path, color)
    return grid


# ============================================================
# Composite operations (condition + action)
# ============================================================

def connect_all_same_color(grid, line_color=None, bg=0):
    """For each pair of objects with the same color, connect with shortest path."""
    from copy import deepcopy
    objs = find_objects(grid, bg)
    result = deepcopy(grid)
    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            if objs[i]["color"] == objs[j]["color"]:
                lc = line_color if line_color is not None else objs[i]["color"]
                result = connect_objects_shortest(result, objs[i], objs[j], lc, bg)
    return result


def connect_on_same_axis(grid, color=None, bg=0):
    """Connect objects that share a row or column with straight lines."""
    from copy import deepcopy
    g = np.array(grid)
    objs = find_objects(grid, bg)
    result = deepcopy(grid)

    for i in range(len(objs)):
        for j in range(i + 1, len(objs)):
            o1, o2 = objs[i], objs[j]
            rel = spatial_relation(o1, o2)
            lc = color if color is not None else o1["color"]

            if rel["same_row"]:
                # Connect horizontally
                r = round(o1["center_r"])
                c1 = max(o1["bbox"][1], o1["bbox"][3])
                c2 = min(o2["bbox"][1], o2["bbox"][3])
                if c1 > c2:
                    c1, c2 = c2, c1
                for c in range(c1, c2 + 1):
                    if result[r][c] == bg:
                        result[r][c] = lc

            elif rel["same_col"]:
                # Connect vertically
                c = round(o1["center_c"])
                r1 = max(o1["bbox"][0], o1["bbox"][2])
                r2 = min(o2["bbox"][0], o2["bbox"][2])
                if r1 > r2:
                    r1, r2 = r2, r1
                for r in range(r1, r2 + 1):
                    if result[r][c] == bg:
                        result[r][c] = lc

    return result
