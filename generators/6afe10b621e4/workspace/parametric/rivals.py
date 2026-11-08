"""Independent component semantics and a finite executable rival bank.

This module never imports the sampler, its mirror, or the production generator.
The reference is only a Python audit oracle: protected Racket labels remain
authoritative. Rival names describe actual algorithms, including their ties.
All selections break equal scores by original row-major component discovery.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass


RIVALS = (
    "bbox_area", "longest_span", "shortest_span", "bbox_perimeter", "cell_perimeter",
    "global_target_top_two", "global_all_top_two",
    "connectivity8", "first_component", "last_component", "leftmost",
    "rightmost", "topmost", "bottommost", "smallest_component",
    "keep_all_targets", "solid_bbox", "ignore_8", "connected_8_only",
    "select_before_merge", "exclude_8_from_size", "erase_bridge_pixels",
)

DESCRIPTIONS = {
    "bbox_area": "Largest bounding-box area per source color, stable scan-order ties.",
    "longest_span": "Largest bounding-box width or height per source color.",
    "shortest_span": "Largest shorter bounding-box side per source color.",
    "bbox_perimeter": "Largest bounding-box perimeter per source color (height + width score).",
    "cell_perimeter": "Largest count of exposed orthogonal cell edges per source color.",
    "global_target_top_two": "Two globally largest red/green components, regardless of color balance.",
    "global_all_top_two": "Two globally largest nonzero components; only selected red/green cells paint.",
    "connectivity8": "Largest 8-connected component per source color.",
    "first_component": "First component of each source color in row-major discovery order.",
    "last_component": "Last component of each source color in row-major discovery order.",
    "leftmost": "Component with smallest minimum column per source color.",
    "rightmost": "Component with largest maximum column per source color.",
    "topmost": "Component with smallest minimum row per source color.",
    "bottommost": "Component with largest maximum row per source color.",
    "smallest_component": "Smallest component per source color.",
    "keep_all_targets": "Recolor every red/green cell after the setting's preprocessing.",
    "solid_bbox": "Choose by correct cell count, but fill each winner's bounding box.",
    "ignore_8": "Always rank original red/green components; ignore all color 8.",
    "connected_8_only": "In merge mode, exclude transformed components containing no original red.",
    "select_before_merge": "In merge mode, select the original red winner, then retain its merged component.",
    "exclude_8_from_size": "Merge connectivity, but rank red components by original red cell count only.",
    "erase_bridge_pixels": "Merge and rank correctly, then erase originally color-8 pixels from the output.",
}


def setting(settings):
    if (type(settings) is not dict or set(settings) != {"bridge_mode"}
            or type(settings["bridge_mode"]) is not str
            or settings["bridge_mode"] not in ("ignore", "merge")):
        raise ValueError("Expected exactly bridge_mode='ignore' or 'merge'")
    return settings["bridge_mode"]


def checked_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("Expected an exact-integer rectangular 1..30 ARC grid")
    return [row[:] for row in grid]


@dataclass(frozen=True)
class Component:
    color: int
    cells: tuple[tuple[int, int], ...]

    @property
    def size(self):
        return len(self.cells)

    @property
    def bbox(self):
        rr, cc = zip(*self.cells)
        return min(rr), min(cc), max(rr), max(cc)

    @property
    def box_area(self):
        r0, c0, r1, c1 = self.bbox
        return (r1 - r0 + 1) * (c1 - c0 + 1)


def components(grid, connectivity=4):
    """Flood-fill same-color nonzero cells, independently of the family code."""
    if connectivity not in (4, 8):
        raise ValueError("Connectivity must be 4 or 8")
    h, w = len(grid), len(grid[0])
    visited = set()
    result = []
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        deltas += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in visited:
                continue
            queue, cells = deque([(r, c)]), []
            visited.add((r, c))
            while queue:
                point = queue.popleft()
                cells.append(point)
                for dr, dc in deltas:
                    nr, nc = point[0] + dr, point[1] + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in visited
                            and grid[nr][nc] == color):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            result.append(Component(color, tuple(cells)))
    return result


def preprocess(grid, mode):
    return [[2 if mode == "merge" and cell == 8 else cell for cell in row]
            for row in grid]


def _largest(groups, color):
    selected = [obj for obj in groups if obj.color == color]
    if not selected:
        raise ValueError(f"Both source colors must be present: missing {color}")
    return max(selected, key=lambda obj: obj.size)


def _paint(grid, selected, name="reference"):
    out = [[0] * len(grid[0]) for _ in grid]
    for obj in selected:
        if obj.color not in (2, 3):
            continue
        cells = obj.cells
        if name == "solid_bbox":
            r0, c0, r1, c1 = obj.bbox
            cells = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]
        for r, c in cells:
            if name != "erase_bridge_pixels" or grid[r][c] != 8:
                out[r][c] = 4 if obj.color == 2 else 1
    return out


def predict(grid, settings, name="reference"):
    """Evaluate one precisely declared candidate without consulting examples."""
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    grid = checked_grid(grid)
    working = preprocess(grid, "ignore" if name == "ignore_8" else mode)
    groups = components(working, 8 if name == "connectivity8" else 4)
    if name == "keep_all_targets":
        return _paint(grid, groups)
    if name in ("global_target_top_two", "global_all_top_two"):
        candidates = groups if name == "global_all_top_two" else [
            obj for obj in groups if obj.color in (2, 3)]
        return _paint(grid, sorted(candidates, key=lambda obj: -obj.size)[:2])
    chosen = []
    for color in (2, 3):
        candidates = [obj for obj in groups if obj.color == color]
        if mode == "merge" and color == 2 and name == "connected_8_only":
            candidates = [obj for obj in candidates
                          if any(grid[r][c] == 2 for r, c in obj.cells)]
        if not candidates:
            raise ValueError(f"Candidate lacks required color {color}")
        if mode == "merge" and color == 2 and name == "select_before_merge":
            anchor = _largest(components(grid), 2).cells[0]
            obj = next(obj for obj in candidates if anchor in obj.cells)
        elif name == "first_component":
            obj = candidates[0]
        elif name == "last_component":
            obj = candidates[-1]
        else:
            score = lambda obj: obj.size
            if name == "bbox_area":
                score = lambda obj: obj.box_area
            elif name == "longest_span":
                score = lambda obj: max(obj.bbox[2] - obj.bbox[0] + 1,
                                        obj.bbox[3] - obj.bbox[1] + 1)
            elif name == "shortest_span":
                score = lambda obj: min(obj.bbox[2] - obj.bbox[0] + 1,
                                        obj.bbox[3] - obj.bbox[1] + 1)
            elif name == "bbox_perimeter":
                score = lambda obj: obj.bbox[2] - obj.bbox[0] + obj.bbox[3] - obj.bbox[1] + 2
            elif name == "cell_perimeter":
                score = lambda obj: sum((r + dr, c + dc) not in set(obj.cells)
                                        for r, c in obj.cells
                                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            elif name == "smallest_component":
                score = lambda obj: -obj.size
            elif name == "leftmost":
                score = lambda obj: -obj.bbox[1]
            elif name == "rightmost":
                score = lambda obj: obj.bbox[3]
            elif name == "topmost":
                score = lambda obj: -obj.bbox[0]
            elif name == "bottommost":
                score = lambda obj: obj.bbox[2]
            elif mode == "merge" and color == 2 and name == "exclude_8_from_size":
                score = lambda obj: sum(grid[r][c] == 2 for r, c in obj.cells)
            obj = max(candidates, key=score)
        chosen.append(obj)
    return _paint(grid, chosen, name)


def reference(grid, settings):
    return predict(grid, settings)


def facts(grid):
    """Compact independent scene facts; no sampler internals are trusted."""
    original, merged = components(grid), components(preprocess(grid, "merge"))
    active = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    def groups(objs):
        return [{"color": o.color, "size": o.size, "bbox": list(o.bbox),
                 "bbox_area": o.box_area} for o in objs]
    original_red = _largest(original, 2)
    merged_red = _largest(merged, 2)
    source_red_parts = [o for o in original if o.color == 2
                        and set(o.cells).issubset(merged_red.cells)]
    return {
        "shape": [len(grid), len(grid[0])],
        "palette": sorted({v for row in grid for v in row}),
        "nonzero_cells": len(active),
        "content_span": [max(r for r, c in active) - min(r for r, c in active) + 1,
                         max(c for r, c in active) - min(c for r, c in active) + 1],
        "original_components": groups(original), "merged_components": groups(merged),
        "original_red_winner_size": original_red.size,
        "merged_red_winner_size": merged_red.size,
        "merged_winner_original_red_fragment_count": len(source_red_parts),
        "merged_winner_original_8_count": sum(grid[r][c] == 8 for r, c in merged_red.cells),
        "red_winner_changes": set(original_red.cells) != set(merged_red.cells),
        "two_red_fragments_overtake_original_winner": (
            len(source_red_parts) >= 2
            and all(o.size < original_red.size for o in source_red_parts)
            and not set(original_red.cells).intersection(merged_red.cells)),
        "standalone_8_wins_after_merge": all(grid[r][c] == 8 for r, c in merged_red.cells),
    }


def program(settings, name):
    """Standalone executable Racket for each candidate's declared meaning."""
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    working = "(recolor g 8 2)" if mode == "merge" and name != "ignore_8" else "g"
    object_function = "objects-8" if name == "connectivity8" else "objects"
    score = "(obj-size obj)"
    if name == "bbox_area":
        score = "(* (+ 1 (- (third (obj-bbox obj)) (first (obj-bbox obj)))) (+ 1 (- (fourth (obj-bbox obj)) (second (obj-bbox obj)))))"
    elif name == "longest_span":
        score = "(max (+ 1 (- (third (obj-bbox obj)) (first (obj-bbox obj)))) (+ 1 (- (fourth (obj-bbox obj)) (second (obj-bbox obj)))))"
    elif name == "shortest_span":
        score = "(min (+ 1 (- (third (obj-bbox obj)) (first (obj-bbox obj)))) (+ 1 (- (fourth (obj-bbox obj)) (second (obj-bbox obj)))))"
    elif name == "bbox_perimeter":
        score = "(+ 2 (- (third (obj-bbox obj)) (first (obj-bbox obj))) (- (fourth (obj-bbox obj)) (second (obj-bbox obj))))"
    elif name == "cell_perimeter":
        score = "(apply + (map (lambda (p) (length (filter (lambda (d) (not (member (list (+ (first p) (first d)) (+ (second p) (second d))) (obj-cells obj)))) '((1 0) (-1 0) (0 1) (0 -1))))) (obj-cells obj)))"
    elif name == "smallest_component":
        score = "(- (obj-size obj))"
    elif name in ("leftmost", "rightmost", "topmost", "bottommost"):
        selector = {"leftmost": "second", "rightmost": "fourth", "topmost": "first", "bottommost": "third"}[name]
        score = f"({selector} (obj-bbox obj))"
        if name in ("leftmost", "topmost"):
            score = f"(- {score})"
    elif name == "exclude_8_from_size" and mode == "merge":
        score = "(if (= (obj-color obj) 2) (length (filter (lambda (p) (= (at g (first p) (second p)) 2)) (obj-cells obj))) (obj-size obj))"
    candidates = "(filter (lambda (obj) (= (obj-color obj) color)) all-os)"
    if name == "connected_8_only" and mode == "merge":
        candidates = "(filter (lambda (obj) (and (= (obj-color obj) color) (or (= color 3) (ormap (lambda (p) (= (at g (first p) (second p)) 2)) (obj-cells obj))))) all-os)"
    choose = "(first (sort candidates (lambda (a b) (> (score a) (score b)))))"
    if name == "first_component":
        choose = "(first candidates)"
    elif name == "last_component":
        choose = "(last candidates)"
    elif name == "select_before_merge" and mode == "merge":
        choose = """(if (= color 2)
      (let* ((originals (filter (lambda (obj) (= (obj-color obj) 2)) (objects g 0)))
             (winner (first (sort originals (lambda (a b) (> (obj-size a) (obj-size b))))))
             (anchor (first (obj-cells winner))))
        (first (filter (lambda (obj) (member anchor (obj-cells obj))) candidates)))
      (first (sort candidates (lambda (a b) (> (score a) (score b))))))"""
    selected = "(list (choose 2) (choose 3))"
    if name == "keep_all_targets":
        selected = "all-os"
    elif name in ("global_target_top_two", "global_all_top_two"):
        pool = "all-os" if name == "global_all_top_two" else "(filter (lambda (obj) (member (obj-color obj) '(2 3))) all-os)"
        selected = f"(take (sort {pool} (lambda (a b) (> (obj-size a) (obj-size b)))) 2)"
    cells = "(obj-cells obj)"
    if name == "solid_bbox":
        cells = "(apply append (map (lambda (r) (map (lambda (c) (list r c)) (range (second (obj-bbox obj)) (+ 1 (fourth (obj-bbox obj)))))) (range (first (obj-bbox obj)) (+ 1 (third (obj-bbox obj))))))"
    elif name == "erase_bridge_pixels":
        cells = "(filter (lambda (p) (not (= (at g (first p) (second p)) 8))) (obj-cells obj))"
    return f"""(rule! (lambda (g)
  (define working {working})
  (define all-os ({object_function} working 0))
  (define (score obj) {score})
  (define (choose color)
    (define candidates {candidates})
    {choose})
  (define selected {selected})
  (foldl (lambda (obj out)
    (if (member (obj-color obj) '(2 3))
      (recolor-cells out {cells} (if (= (obj-color obj) 2) 4 1))
      out))
    (empty-grid (rows g) (cols g) 0) selected)))"""


def fixtures():
    """Small independent semantic controls, including ties and a genuine bridge."""
    # The lower red fragments have 3 cells each, below the 4-cell original
    # winner. A one-cell bridge creates a 7-cell component and reverses rank.
    bridge = [
        [2, 2, 0, 0, 3, 3, 3, 0, 0],
        [2, 2, 0, 0, 3, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 2, 8, 2, 2, 2, 0, 5],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 3, 0, 0, 3, 0, 0, 0, 0],
    ]
    # A standalone 8-region must become a legitimate red candidate. Sparse
    # L-shapes and diagonally touching components exercise bbox/connectivity.
    standalone = [
        [2, 2, 2, 0, 3, 0, 0, 0, 0, 0],
        [2, 2, 2, 0, 3, 0, 0, 3, 3, 0],
        [0, 0, 0, 0, 3, 3, 3, 0, 0, 3],
        [2, 0, 0, 0, 0, 0, 0, 0, 0, 3],
        [2, 0, 0, 0, 8, 8, 8, 8, 0, 0],
        [2, 2, 2, 0, 8, 8, 8, 8, 0, 0],
    ]
    tie = [[2, 0, 2, 0, 3], [0, 0, 0, 0, 0], [3, 0, 8, 0, 8]]
    return {"red_fragments_overtake": bridge, "standalone_8_and_sparse_bbox": standalone,
            "stable_scan_order_ties": tie}
