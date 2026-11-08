"""Independent finite hypotheses for marker selection and component cropping."""
from collections import deque
from fractions import Fraction


CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
RIVALS = ("other_metric", "euclidean", "bbox_origin", "bbox_region", "centroid",
          "mean_distance", "farthest", "first", "last", "smallest", "largest",
          "lowest_color", "highest_color", "reverse_ties", "column_first_ties",
          "discovery_ties", "eight_neighbors", "color_groups", "ignore_colors",
          "raw_crop", "solid_bbox", "fill_holes")


def objects(grid, mode="canonical"):
    foreground = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if mode == "color_groups":
        groups = {}
        for r, c in foreground:
            groups.setdefault(grid[r][c], set()).add((r, c))
        return list(groups.values())
    steps = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c) if mode == "eight_neighbors" else CARDINAL
    visited, groups = set(), []
    for start in foreground:
        if start in visited:
            continue
        cells = {start}
        visited.add(start)
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in steps:
                nr, nc = r + dr, c + dc
                if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                        and grid[nr][nc] not in (0, 9) and (nr, nc) not in visited
                        and (mode == "ignore_colors" or grid[nr][nc] == grid[start[0]][start[1]])):
                    visited.add((nr, nc)); cells.add((nr, nc)); queue.append((nr, nc))
        groups.append(cells)
    return groups


def bbox(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def norm(dr, dc, metric):
    return abs(dr) + abs(dc) if metric == "manhattan" else max(abs(dr), abs(dc))


def _filled_holes(grid, color):
    h, w = len(grid), len(grid[0])
    outside = {(r, c) for r in range(h) for c in range(w)
               if (r in (0, h - 1) or c in (0, w - 1)) and grid[r][c] == 0}
    queue = deque(outside)
    while queue:
        r, c = queue.popleft()
        for dr, dc in CARDINAL:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0 and (nr, nc) not in outside:
                outside.add((nr, nc)); queue.append((nr, nc))
    return [[0 if (r, c) in outside else color for c in range(w)] for r in range(h)]


def predict(grid, metric, rival):
    if metric not in ("manhattan", "chebyshev") or rival not in RIVALS:
        raise ValueError("unknown metric or rival")
    marker = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    groups = objects(grid, rival)
    selected_metric = ("chebyshev" if metric == "manhattan" else "manhattan") if rival == "other_metric" else metric

    def key(cells):
        top, left, bottom, right = bbox(cells)
        values = [norm(r - marker[0], c - marker[1], selected_metric) for r, c in cells]
        score = min(values)
        if rival == "euclidean":
            score = min((r - marker[0])**2 + (c - marker[1])**2 for r, c in cells)
        elif rival == "bbox_origin":
            score = norm(top - marker[0], left - marker[1], metric)
        elif rival == "bbox_region":
            dr = max(top - marker[0], 0, marker[0] - bottom)
            dc = max(left - marker[1], 0, marker[1] - right)
            score = norm(dr, dc, metric)
        elif rival == "centroid":
            score = norm(Fraction(sum(r for r, c in cells), len(cells)) - marker[0],
                         Fraction(sum(c for r, c in cells), len(cells)) - marker[1], metric)
        elif rival == "mean_distance":
            score = Fraction(sum(values), len(values))
        elif rival == "farthest": score = -score
        elif rival == "smallest": score = len(cells)
        elif rival == "largest": score = -len(cells)
        elif rival == "lowest_color": score = grid[min(cells)[0]][min(cells)[1]]
        elif rival == "highest_color": score = -grid[min(cells)[0]][min(cells)[1]]
        if rival == "reverse_ties": return score, -top, -left
        if rival == "column_first_ties": return score, left, top
        if rival == "discovery_ties": return (score,)
        return score, top, left

    chosen = groups[0] if rival == "first" else groups[-1] if rival == "last" else min(groups, key=key)
    top, left, bottom, right = bbox(chosen)
    color = grid[min(chosen)[0]][min(chosen)[1]]
    if rival == "raw_crop":
        return [row[left:right + 1] for row in grid[top:bottom + 1]]
    if rival == "solid_bbox":
        return [[color] * (right - left + 1) for _ in range(bottom - top + 1)]
    output = [[0] * (right - left + 1) for _ in range(bottom - top + 1)]
    for r, c in chosen:
        output[r - top][c - left] = grid[r][c]
    return _filled_holes(output, color) if rival == "fill_holes" else output


def check_episode(episode):
    rows = []
    for rival in RIVALS:
        mismatches = [i for i, pair in enumerate(episode["train"])
                      if predict(pair["input"], episode["settings"]["metric"], rival) != pair["output"]]
        disagreements = [i for i, pair in enumerate(episode["test"])
                         if predict(pair["input"], episode["settings"]["metric"], rival) != pair["output"]]
        rows.append({"rival": rival, "demo_mismatch_indices": mismatches,
                     "query_disagreement_indices": disagreements, "survives_demos": not mismatches})
    return rows
