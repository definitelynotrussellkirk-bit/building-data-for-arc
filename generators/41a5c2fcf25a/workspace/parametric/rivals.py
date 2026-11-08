"""Twelve explicit, total shortcut hypotheses for this family's input grammar.

These are finite audit hypotheses, not a claim of unique human interpretation.
Perimeters here cancel lattice edges independently of adapter.py's neighbor count.
"""
from collections import deque


CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
RIVALS = ("other_metric", "position_only", "ascending", "sorted_legend",
          "reverse_ties", "column_first_ties", "source_color_first",
          "source_color_last", "capped_metric", "eight_neighbors",
          "bounding_box", "filled_holes")


def components(grid, diagonal=False):
    steps = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c) if diagonal else CARDINAL
    visited = set()
    result = []
    for r in range(1, len(grid)):
        for c in range(len(grid[0])):
            if not grid[r][c] or (r, c) in visited:
                continue
            cells = {(r, c)}
            visited.add((r, c))
            queue = deque([(r, c)])
            while queue:
                a, b = queue.popleft()
                for dr, dc in steps:
                    nr, nc = a + dr, b + dc
                    if (1 <= nr < len(grid) and 0 <= nc < len(grid[0])
                            and grid[nr][nc] and (nr, nc) not in visited):
                        visited.add((nr, nc))
                        cells.add((nr, nc))
                        queue.append((nr, nc))
            result.append(cells)
    return result


def edge_perimeter(cells):
    edges = set()
    for r, c in cells:
        edges.symmetric_difference_update({((r, c), (r, c + 1)),
            ((r + 1, c), (r + 1, c + 1)), ((r, c), (r + 1, c)),
            ((r, c + 1), (r + 1, c + 1))})
    return len(edges)


def fill_holes(cells):
    top, bottom = min(r for r, c in cells) - 1, max(r for r, c in cells) + 1
    left, right = min(c for r, c in cells) - 1, max(c for r, c in cells) + 1
    outside = {(top, left)}
    queue = deque(outside)
    while queue:
        r, c = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = r + dr, c + dc
            if (top <= nr <= bottom and left <= nc <= right
                    and (nr, nc) not in cells and (nr, nc) not in outside):
                outside.add((nr, nc))
                queue.append((nr, nc))
    return {(r, c) for r in range(top + 1, bottom) for c in range(left + 1, right)
            if (r, c) not in outside}


def predict(grid, metric, rival):
    if rival not in RIVALS or metric not in ("area", "perimeter"):
        raise ValueError("unknown rival or metric")
    colors = [v for v in grid[0] if v]
    comps = components(grid, diagonal=rival == "eight_neighbors")
    if rival == "sorted_legend":
        colors = sorted(colors)
    elif rival == "source_color_first" and 8 in colors:
        colors = [8] + [v for v in colors if v != 8]
    elif rival == "source_color_last" and 8 in colors:
        colors = [v for v in colors if v != 8] + [8]
    chosen = ("perimeter" if metric == "area" else "area") if rival == "other_metric" else metric

    def key(cells):
        top, left = min(r for r, c in cells), min(c for r, c in cells)
        measure = fill_holes(cells) if rival == "filled_holes" else cells
        score = len(measure) if chosen == "area" else edge_perimeter(measure)
        if rival == "bounding_box":
            height = max(r for r, c in cells) - top + 1
            width = max(c for r, c in cells) - left + 1
            score = height * width if chosen == "area" else 2 * (height + width)
        if rival == "capped_metric":
            score = min(score, 5 if chosen == "area" else 8)
        if rival == "position_only":
            return top, left
        if rival == "ascending":
            return score, top, left
        if rival == "reverse_ties":
            return -score, -top, -left
        if rival == "column_first_ties":
            return -score, left, top
        return -score, top, left

    out = [row[:] for row in grid]
    for color, cells in zip(colors, sorted(reversed(comps), key=key)):
        for r, c in cells:
            out[r][c] = color
    return out


def check_episode(episode):
    metric = episode["settings"]["rank_by"]
    rows = []
    for rival in RIVALS:
        mismatches = [i for i, pair in enumerate(episode["train"])
                      if predict(pair["input"], metric, rival) != pair["output"]]
        disagreements = [i for i, pair in enumerate(episode["test"])
                         if predict(pair["input"], metric, rival) != pair["output"]]
        rows.append({"rival": rival, "demo_mismatch_indices": mismatches,
                     "query_disagreement_indices": disagreements,
                     "survives_demos": not mismatches})
    return rows
