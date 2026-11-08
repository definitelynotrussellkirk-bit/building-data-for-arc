"""Independent coordinate-event semantics and a finite executable rival bank.

This module imports neither the family, its retained mirror, nor the production
generator. Each painted cell is resolved by the greatest event timestamp; this
also makes simultaneous versus marker-ordered interpretation explicit. Racket
programs are independently authored and are checked against these meanings by
the protected audit before they support any learnability claim.
"""
from __future__ import annotations

from collections import defaultdict


LEGAL_BACKGROUNDS = (0, 4, 5, 6, 7, 8, 9)
DESCRIPTIONS = {
    "skip_a": "Run the final sweep from original input blue markers, bypassing A and its surviving-green intermediate.",
    "nominal_diagonals": "Propagate the union of nominal original diagonal targets, including stamps erased by later crosses.",
    "reverse_sweep": "Process markers in reverse row-major order in every executed sweep.",
    "simultaneous_sweep": "Paint every cross, then every center, then every diagonal, in each sweep.",
    "retain_intermediate": "Use surviving-green seeds for B but paint on A's output instead of a fresh original-background grid.",
    "repeat_same_grid": "Apply the single-sweep transform again to A's grid, reading its remaining blue cross cells as markers.",
    "intermediate_blue": "Seed the fresh B grid from surviving blue cells of A instead of surviving green cells.",
    "interior_only": "Ignore markers whose four diagonal targets do not all fit inside the canvas.",
    "full_stamp_only": "Paint edge-marker crosses and centers but suppress their entire diagonal stamp when any corner clips.",
    "wrap_diagonals": "Wrap out-of-bounds diagonal targets onto the opposite edge.",
    "clamp_diagonals": "Clamp out-of-bounds diagonal targets to the closest boundary cell.",
    "first_marker": "Use only the first row-major marker in every sweep.",
    "last_marker": "Use only the last row-major marker in every sweep.",
    "rows_only": "Paint horizontal blue lines, omitting the vertical lines.",
    "columns_only": "Paint vertical blue lines, omitting the horizontal lines.",
    "north_diagonals": "Paint only the two diagonal targets above each marker.",
    "south_diagonals": "Paint only the two diagonal targets below each marker.",
    "main_diagonal": "Paint only northwest and southeast diagonal targets.",
    "anti_diagonal": "Paint only northeast and southwest diagonal targets.",
    "positive_rays": "Paint blue rays right and down from each marker instead of complete rows and columns.",
    "restore_centers": "Run the ordered sweep, then restore every selected marker center to red.",
    "dynamic_markers": "Skip a queued original marker if an earlier write has changed its current cell from blue.",
}
RIVALS = tuple(DESCRIPTIONS)


def settings_values(settings):
    if type(settings) is not dict or set(settings) != {"diagonal_radius", "propagation_passes"}:
        raise ValueError("settings must name diagonal_radius and propagation_passes exactly")
    values = settings["diagonal_radius"], settings["propagation_passes"]
    if any(type(v) is not int or v not in (1, 2) for v in values):
        raise ValueError("both settings must be literal integers in {1,2}")
    return values


def _shape(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row) for row in grid)):
        raise ValueError("grid must be a rectangular typed ARC grid of size 1..30")
    return len(grid), len(grid[0])


def coordinates(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell == color]


def background(grid):
    _shape(grid)
    other = {cell for row in grid for cell in row if cell != 1}
    if len(other) != 1 or next(iter(other)) not in LEGAL_BACKGROUNDS:
        raise ValueError("input needs one legal uniform background plus blue markers")
    return next(iter(other))


def seeded(grid, points):
    h, w = _shape(grid)
    bg = background(grid)
    points = set(points)
    return [[1 if (r, c) in points else bg for c in range(w)] for r in range(h)]


def diagonal_targets(point, radius, shape, kind="reference"):
    h, w = shape
    r, c = point
    offsets = [(-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius)]
    if kind == "north_diagonals":
        offsets = offsets[:2]
    elif kind == "south_diagonals":
        offsets = offsets[2:]
    elif kind == "main_diagonal":
        offsets = [offsets[0], offsets[3]]
    elif kind == "anti_diagonal":
        offsets = [offsets[1], offsets[2]]
    targets = [(r + dr, c + dc) for dr, dc in offsets]
    if kind == "wrap_diagonals":
        return {(r % h, c % w) for r, c in targets}
    if kind == "clamp_diagonals":
        return {(max(0, min(h - 1, r)), max(0, min(w - 1, c))) for r, c in targets}
    inside = {(r, c) for r, c in targets if 0 <= r < h and 0 <= c < w}
    return set() if kind == "full_stamp_only" and len(inside) != 4 else inside


def event_sweep(grid, points, radius, kind="reference"):
    """Resolve independent (marker,phase) coordinate events by last timestamp."""
    h, w = _shape(grid)
    points = sorted(set(points))
    if kind == "reverse_sweep":
        points.reverse()
    elif kind == "first_marker":
        points = points[:1]
    elif kind == "last_marker":
        points = points[-1:]
    elif kind == "interior_only":
        points = [(r, c) for r, c in points if radius <= r < h - radius and radius <= c < w - radius]
    events = defaultdict(list)
    for marker_index, (r, c) in enumerate(points):
        if kind == "dynamic_markers":
            current = max(events[r, c])[1] if (r, c) in events else grid[r][c]
            if current != 1:
                continue
        horizontal = {(r, cc) for cc in range(c if kind == "positive_rays" else 0, w)}
        vertical = {(rr, c) for rr in range(r if kind == "positive_rays" else 0, h)}
        cross = (horizontal if kind == "rows_only" else vertical if kind == "columns_only"
                 else horizontal | vertical)
        groups = ((cross, 1), ({(r, c)}, 2), (diagonal_targets((r, c), radius, (h, w), kind), 3))
        for phase, (cells, color) in enumerate(groups):
            timestamp = (phase, marker_index) if kind == "simultaneous_sweep" else (marker_index, phase)
            for cell in cells:
                events[cell].append((timestamp, color))
    if kind == "restore_centers":
        for cell in points:
            events[cell].append(((len(points), 3), 2))
    return [[max(events[r, c])[1] if (r, c) in events else grid[r][c]
             for c in range(w)] for r in range(h)]


def first_stage(grid, radius):
    background(grid)
    return event_sweep(grid, coordinates(grid, 1), radius)


def reference(grid, settings):
    return predict(grid, settings, "reference")


def predict(grid, settings, kind):
    radius, passes = settings_values(settings)
    if kind != "reference" and kind not in RIVALS:
        raise ValueError(f"unknown rival: {kind}")
    background(grid)
    original = coordinates(grid, 1)
    stage = event_sweep(grid, original, radius, kind)
    if passes == 1 or kind == "skip_a":
        return stage
    if kind == "nominal_diagonals":
        derived = set().union(*(diagonal_targets(p, radius, _shape(grid)) for p in original))
    else:
        derived = coordinates(stage, 1 if kind in ("repeat_same_grid", "intermediate_blue") else 3)
    base = stage if kind in ("retain_intermediate", "repeat_same_grid") else seeded(grid, derived)
    return event_sweep(base, derived, radius, kind)


def program(settings, kind="reference"):
    """Return a standalone protected-Racket candidate with the declared meaning."""
    radius, passes = settings_values(settings)
    if kind != "reference" and kind not in RIVALS:
        raise ValueError(f"unknown rival: {kind}")
    offsets = [(-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius)]
    if kind == "north_diagonals":
        offsets = offsets[:2]
    elif kind == "south_diagonals":
        offsets = offsets[2:]
    elif kind == "main_diagonal":
        offsets = [offsets[0], offsets[3]]
    elif kind == "anti_diagonal":
        offsets = [offsets[1], offsets[2]]
    offset_text = "(list " + " ".join(f"(list {r} {c})" for r, c in offsets) + ")"
    inside = f"(and (>= r {radius}) (< r (- h {radius})) (>= c {radius}) (< c (- w {radius})))"
    if kind == "wrap_diagonals":
        painting = "(set-cell acc (modulo rr h) (modulo cc w) 3)"
    elif kind == "clamp_diagonals":
        painting = "(set-cell acc (max 0 (min (- h 1) rr)) (max 0 (min (- w 1) cc)) 3)"
    else:
        painting = "(if (and (>= rr 0) (< rr h) (>= cc 0) (< cc w)) (set-cell acc rr cc 3) acc)"
    stamp = f"(reduce (lambda (acc d) (let ((rr (+ r (fst d))) (cc (+ c (snd d)))) {painting})) base {offset_text})"
    if kind == "full_stamp_only":
        stamp = f"(if {inside} {stamp} base)"
    cross_condition = "(or (= rr r) (= cc c))"
    if kind == "rows_only":
        cross_condition = "(= rr r)"
    elif kind == "columns_only":
        cross_condition = "(= cc c)"
    elif kind == "positive_rays":
        cross_condition = "(or (and (= rr r) (>= cc c)) (and (= cc c) (>= rr r)))"
    points = "raw"
    if kind == "reverse_sweep":
        points = "(reverse raw)"
    elif kind == "first_marker":
        points = "(if (empty? raw) raw (list (first raw)))"
    elif kind == "last_marker":
        points = "(if (empty? raw) raw (list (last raw)))"
    elif kind == "interior_only":
        points = f"(filter (lambda (p) (let ((r (fst p)) (c (snd p))) {inside})) raw)"
    sweep = "(reduce (lambda (acc p) (stamp (center (cross acc p) p) p)) base points)"
    if kind == "simultaneous_sweep":
        sweep = "(reduce stamp (reduce center (reduce cross base points) points) points)"
    elif kind == "restore_centers":
        sweep = f"(reduce center {sweep} points)"
    elif kind == "dynamic_markers":
        sweep = "(reduce (lambda (acc p) (if (= (cell-at acc (fst p) (snd p)) 1) (stamp (center (cross acc p) p) p) acc)) base points)"
    derived = "(find-color stage 3)"
    if kind in ("repeat_same_grid", "intermediate_blue"):
        derived = "(find-color stage 1)"
    elif kind == "nominal_diagonals":
        # The scratch color-3 canvas records the union of nominal stamps;
        # no crosses or centers can erase them before the seed extraction.
        derived = "(find-color (reduce stamp blank original) 3)"
    final = "stage"
    if passes == 2 and kind != "skip_a":
        base = "stage" if kind in ("retain_intermediate", "repeat_same_grid") else "(reduce (lambda (acc p) (set-cell acc (fst p) (snd p) 1)) blank seeds)"
        final = f"(let* ((seeds {derived}) (base {base})) (sweep base seeds))"
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (bg (first (filter (lambda (v) (not (= v 1))) (grid-colors g))))
         (original (find-color g 1)) (blank (empty-grid h w bg))
         (cross (lambda (base p)
           (let ((r (fst p)) (c (snd p)))
             (grid-from-fn h w (lambda (rr cc)
               (if {cross_condition} 1 (cell-at base rr cc)))))))
         (center (lambda (base p) (set-cell base (fst p) (snd p) 2)))
         (stamp (lambda (base p)
           (let ((r (fst p)) (c (snd p))) {stamp})))
         (sweep (lambda (base raw) (let ((points {points})) {sweep})))
         (stage (sweep g original)))
    {final})))"""


def scene(height, width, points, bg=7):
    points = set(points)
    return [[1 if (r, c) in points else bg for c in range(width)] for r in range(height)]


def fixtures():
    return {
        "erased_diagonals_both_radii": scene(9, 11, [(2, 2), (3, 6), (4, 8)]),
        "shared_rows_columns_and_edges": scene(7, 10, [(0, 0), (0, 7), (3, 7), (6, 9)], 4),
        "clipped_four_sides": scene(8, 9, [(0, 3), (3, 0), (4, 8), (7, 5)], 0),
        "original_markers_overwritten_before_their_turn": scene(9, 10, [(1, 1), (2, 2), (3, 3)], 8),
    }


def facts(grid):
    h, w = _shape(grid)
    markers = coordinates(grid, 1)
    result = {"shape": [h, w], "background": background(grid), "markers": [list(p) for p in markers],
              "marker_count": len(markers), "shared_rows": len({r for r, c in markers}) < len(markers),
              "shared_columns": len({c for r, c in markers}) < len(markers), "radii": {}}
    if markers:
        result["marker_span"] = [max(r for r, c in markers) - min(r for r, c in markers) + 1,
                                 max(c for r, c in markers) - min(c for r, c in markers) + 1]
    for radius in (1, 2):
        nominal = set().union(*(diagonal_targets(p, radius, (h, w)) for p in markers))
        stage = first_stage(grid, radius)
        survived = set(coordinates(stage, 3))
        result["radii"][str(radius)] = {
            "nominal_diagonal_count": len(nominal), "surviving_green_count": len(survived),
            "erased_diagonal_cells": [list(p) for p in sorted(nominal - survived)],
            "surviving_green_cells": [list(p) for p in sorted(survived)],
            "overwritten_original_centers": [list(p) for p in markers if stage[p[0]][p[1]] != 2],
            "clipped_marker_count": sum(len(diagonal_targets(p, radius, (h, w))) < 4 for p in markers),
        }
    return result
