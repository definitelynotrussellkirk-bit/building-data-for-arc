"""Reflected-probe route family for 329f699c3e09.

The canonical setting paints reflected magenta coordinates cyan.  The alternate
uses those reflected coordinates as ray origins, follows each ray farther away
from the divider to its first colored object, then recolors the selected object.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

MODES = ("paint_reflections", "probe_first_hit")
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def parse_settings(settings):
    if (type(settings) is not dict or set(settings) != {"mode"}
            or type(settings["mode"]) is not str or settings["mode"] not in MODES):
        raise ValueError("settings must be exactly mode=paint_reflections or probe_first_hit")
    return {"mode": settings["mode"]}


def _validate_grid(grid):
    if (type(grid) is not list or not 7 <= len(grid) <= 30 or not grid
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a rectangular ARC grid sized 7..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer colors 0..9")


def _first_hit(grid, start, direction):
    h, w = len(grid), len(grid[0])
    r, c = start[0] + direction[0], start[1] + direction[1]
    while 0 <= r < h and 0 <= c < w:
        value = grid[r][c]
        if value not in (0, 6, 7, 8):
            return value
        r += direction[0]; c += direction[1]
    return 0


def analyze(grid):
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(h) if all(grid[r][c] == 7 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 7 for r in range(h))]
    if len(full_rows) + len(full_cols) != 1:
        raise ValueError("need exactly one full color-7 divider")
    axis, div = (("row", full_rows[0]) if full_rows else ("col", full_cols[0]))
    sources = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if not sources:
        raise ValueError("need magenta source cells")
    routes = []
    for r, c in sources:
        if axis == "col":
            if c == div: raise ValueError("source cannot lie on divider")
            probe = (r, 2 * div - c)
            outward = (0, 1 if c < div else -1)
            source_outward = (0, -outward[1])
        else:
            if r == div: raise ValueError("source cannot lie on divider")
            probe = (2 * div - r, c)
            outward = (1 if r < div else -1, 0)
            source_outward = (-outward[0], 0)
        if not (0 <= probe[0] < h and 0 <= probe[1] < w):
            raise ValueError("reflected probe is out of bounds")
        routes.append({"source": (r, c), "probe": probe, "outward": outward,
                       "source_outward": source_outward})
    target_colors = sorted({_first_hit(grid, row["probe"], row["outward"]) for row in routes} - {0})
    source_side_colors = sorted({_first_hit(grid, row["source"], row["source_outward"]) for row in routes} - {0})
    if not target_colors or not source_side_colors:
        raise ValueError("each route family needs target and source-side first hits")
    return {"axis": axis, "divider": div, "sources": sources,
            "probes": [row["probe"] for row in routes], "routes": routes,
            "target_colors": target_colors, "source_side_colors": source_side_colors}


def canonical_output(grid):
    info = analyze(grid)
    out = deepcopy(grid)
    for r, c in info["probes"]:
        out[r][c] = 8
    return out


def apply_with_route(grid, *, use_reflected_probes):
    info = analyze(grid)
    if use_reflected_probes:
        colors = info["target_colors"]
    else:
        colors = info["source_side_colors"]
    return [[8 if value in colors else value for value in row] for row in grid]


def apply(grid, settings):
    mode = parse_settings(settings)["mode"]
    return canonical_output(grid) if mode == "paint_reflections" else apply_with_route(
        grid, use_reflected_probes=True)


ALTERNATE = r'''(rule! (let* ((div-row (find-first (lambda (r) (for/and ([c (range 0 w)]) (= (at g r c) 7))) (range 0 h)))
         (div-col (find-first (lambda (c) (for/and ([r (range 0 h)]) (= (at g r c) 7))) (range 0 w))))
  (define (route p)
    (let ((r (first p)) (c (second p)))
      (if div-col
          (list r (- (* 2 div-col) c) 0 (if (< c div-col) 1 -1))
          (list (- (* 2 div-row) r) c (if (< r div-row) 1 -1) 0))))
  (define (first-hit q)
    (let loop ((r (+ (first q) (third q))) (c (+ (second q) (fourth q))))
      (if (not (in-bounds? r c h w))
          0
          (let ((v (at g r c)))
            (if (member? v (list 0 6 7 8))
                (loop (+ r (third q)) (+ c (fourth q)))
                v)))))
  (define hits (remove-duplicates (filter (lambda (v) (not (= v 0)))
                                          (map first-hit (map route (find-color g 6))))))
  (grid-from-fn h w (lambda (r c)
    (let ((v (at g r c))) (if (member? v hits) 8 v))))))'''

COUNTERFACTUAL = r'''(rule! (let* ((div-row (find-first (lambda (r) (for/and ([c (range 0 w)]) (= (at g r c) 7))) (range 0 h)))
         (div-col (find-first (lambda (c) (for/and ([r (range 0 h)]) (= (at g r c) 7))) (range 0 w))))
  (define (route p)
    (let ((r (first p)) (c (second p)))
      (if div-col
          (list r c 0 (if (< c div-col) -1 1))
          (list r c (if (< r div-row) -1 1) 0))))
  (define (first-hit q)
    (let loop ((r (+ (first q) (third q))) (c (+ (second q) (fourth q))))
      (if (not (in-bounds? r c h w)) 0
          (let ((v (at g r c)))
            (if (member? v (list 0 6 7 8))
                (loop (+ r (third q)) (+ c (fourth q))) v)))))
  (define hits (remove-duplicates (filter (lambda (v) (not (= v 0)))
                                          (map first-hit (map route (find-color g 6))))))
  (grid-from-fn h w (lambda (r c)
    (let ((v (at g r c))) (if (member? v hits) 8 v))))))'''


def program(settings):
    return CANONICAL if parse_settings(settings)["mode"] == "paint_reflections" else ALTERNATE


def counterfactual_program():
    return COUNTERFACTUAL
