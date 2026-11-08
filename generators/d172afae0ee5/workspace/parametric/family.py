"""Cue-normalized move-to-marker family for d172afae0ee5.

The canonical setting pastes the crop as found.  The alternate first identifies
the unique singleton-colored corner cue, then flips the crop so that cue becomes
the crop's top-left before pasting.  Qualification re-executes both Racket rules.
"""
from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

ORIENTATIONS = ("as_found", "cue_to_top_left")
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
if not CANONICAL.startswith("(rule! ") or not CANONICAL.endswith(")"):
    raise ValueError("canonical.rkt must contain the exact selected rule expression")


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {"orientation"}
            or type(settings["orientation"]) is not str
            or settings["orientation"] not in ORIENTATIONS):
        raise ValueError("settings must be exactly orientation=as_found or cue_to_top_left")
    return {"orientation": settings["orientation"]}


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _rotate_180(grid):
    return _flip_ud(_flip_lr(grid))


def _transform_for_corner(crop, corner):
    if corner == "top_left":
        return [list(row) for row in crop]
    if corner == "top_right":
        return _flip_lr(crop)
    if corner == "bottom_left":
        return _flip_ud(crop)
    if corner == "bottom_right":
        return _rotate_180(crop)
    raise ValueError("unknown cue corner")


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen == cells


def analyze(grid):
    if (type(grid) is not list or not 6 <= len(grid) <= 30
            or type(grid[0]) is not list or not 6 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a rectangular 6..30 ARC grid")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        raise ValueError("cells must be exact integer ARC colors 0..9")
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if len(markers) != 1 or len(cells) < 4 or not _connected(cells):
        raise ValueError("need one marker and one connected object of at least four cells")
    counts = Counter(grid[r][c] for r, c in cells)
    singleton = [color for color, count in counts.items() if count == 1]
    if len(counts) != 2 or len(singleton) != 1:
        raise ValueError("object needs exactly two colors and one singleton cue color")
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    r1, c1 = max(r for r, _ in cells), max(c for _, c in cells)
    marker = markers[0]
    if r0 <= marker[0] <= r1 and c0 <= marker[1] <= c1:
        raise ValueError("marker must be outside the source bounding box")
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    cue_color = singleton[0]
    cue = next((r, c) for r, row in enumerate(crop) for c, v in enumerate(row) if v == cue_color)
    corners = {(0, 0): "top_left", (0, len(crop[0]) - 1): "top_right",
               (len(crop) - 1, 0): "bottom_left",
               (len(crop) - 1, len(crop[0]) - 1): "bottom_right"}
    if cue not in corners:
        raise ValueError("singleton cue must occupy a crop corner")
    if marker[0] + len(crop) > len(grid) or marker[1] + len(crop[0]) > width:
        raise ValueError("marker cannot anchor the crop in bounds")
    return {"marker": marker, "crop": [list(row) for row in crop],
            "cue_color": cue_color, "cue_corner": corners[cue],
            "bbox": (r0, c0, r1, c1)}


def _paste(crop, marker, h, w):
    out = [[0] * w for _ in range(h)]
    top, left = marker
    for r, row in enumerate(crop):
        for c, value in enumerate(row):
            if value:
                out[top + r][left + c] = value
    return out


def apply_with_corner(grid, corner):
    info = analyze(grid)
    crop = _transform_for_corner(info["crop"], corner)
    return _paste(crop, info["marker"], len(grid), len(grid[0]))


def apply(grid, settings):
    setting = parse_settings(settings)["orientation"]
    info = analyze(grid)
    corner = "top_left" if setting == "as_found" else info["cue_corner"]
    return apply_with_corner(grid, corner)


def output_bbox_top_left(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return min(r for r, _ in cells), min(c for _, c in cells)


ALTERNATE = r'''(rule! (let ((dummy 0))
  (define (d172-paste grid pat top left)
    (for*/fold ((out grid)) ((r (in-range (rows pat))) (c (in-range (cols pat))))
      (let ((v (at pat r c)) (rr (+ top r)) (cc (+ left c)))
        (if (and (not (= v 0)) (in-bounds? rr cc (rows out) (cols out)))
            (set-cell out rr cc v) out))))
  (let* ((marker (first (find-color g 9)))
         (cells (filter (lambda (p)
                  (let ((v (at g (first p) (second p))))
                    (not (member? v (list 0 9)))))
                (grid-positions g)))
         (bb (bbox-of-cells cells))
         (obj (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (vals (map (lambda (p) (at g (first p) (second p))) cells))
         (cue-color (first (filter (lambda (v)
                         (= 1 (length (filter (lambda (x) (= x v)) vals))))
                       vals)))
         (cue (first (find-color obj cue-color)))
         (cr (first cue)) (cc (second cue))
         (oriented
           (cond ((and (= cr 0) (= cc 0)) obj)
                 ((and (= cr 0) (= cc (- (cols obj) 1))) (flip-lr obj))
                 ((and (= cr (- (rows obj) 1)) (= cc 0)) (flip-ud obj))
                 (else (rotate-180 obj)))))
    (d172-paste (empty-grid (rows g) (cols g) 0) oriented
                (first marker) (second marker)))))'''


def program(settings):
    return CANONICAL if parse_settings(settings)["orientation"] == "as_found" else ALTERNATE


def counterfactual_program():
    """Skip cue inference and paste the source crop unchanged."""
    return CANONICAL
