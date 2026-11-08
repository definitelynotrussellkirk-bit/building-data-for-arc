"""Opt-in point reflection and an echo selected from its clipped intermediate.

Python outputs are sampling claims, never independent reference labels. Native
qualification and probe.py execute the exact Racket programs. The default
resource is copied byte-for-byte from the selected canonical authority.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import random

SETTINGS = ({"rule": "point"}, {"rule": "visible_span_echo"})
_HOME = Path(__file__).resolve().parent
_BASE_RIVALS = (
    "other_setting", "identity", "fixed_anchor", "grid_center", "all_or_nothing",
    "outline_only", "left_of_anchor_only", "horizontal_axis", "vertical_axis",
    "reflection_only", "anchor_color_copy", "translate_only",
)
_ECHO_RIVALS = (
    "source_span", "unclipped_echo", "always_row", "always_column",
    "tie_columns", "opposite_axis", "echo_source", "omit_first_copy",
)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"rule"}
            or type(settings["rule"]) is not str
            or settings["rule"] not in ("point", "visible_span_echo")):
        raise ValueError("settings must be exactly {'rule': 'point'|'visible_span_echo'}")
    return settings["rule"]


def _integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")


def _parts(grid):
    anchor = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    shape = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    return anchor, shape


def _inside(p, h, w):
    return 0 <= p[0] < h and 0 <= p[1] < w


def _spans(cells):
    if not cells:
        return 0, 0
    return (max(p[0] for p in cells) - min(p[0] for p in cells) + 1,
            max(p[1] for p in cells) - min(p[1] for p in cells) + 1)


def validate_grid(grid):
    """The extended family grammar; the canonical sampler remains untouched."""
    if (type(grid) is not list or not 4 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 5 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)):
        return ["expected a rectangular 4..30 by 5..30 list grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["expected exact integer colors 0..9"]
    if sum(v == 9 for row in grid for v in row) != 1:
        return ["expected exactly one color-9 anchor"]
    anchor, cells = _parts(grid)
    shape = {(r, c) for r, c, _ in cells}
    if not 2 <= len(shape) <= 240 or len({v for _, _, v in cells}) != 1:
        return ["expected one monochromatic 2..240-cell shape"]
    reached = {min(shape)}
    todo = list(reached)
    while todo:
        r, c = todo.pop()
        for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if p in shape and p not in reached:
                reached.add(p)
                todo.append(p)
    if reached != shape:
        return ["shape must be 4-connected"]
    targets = {(2*anchor[0]-r, 2*anchor[1]-c) for r, c in shape}
    if targets & shape:
        return ["source and first reflection must be disjoint"]
    if not any(_inside(p, len(grid), len(grid[0])) for p in targets):
        return ["first reflection must have visible cells"]
    return []


def intermediate(grid):
    anchor, shape = _parts(grid)
    reflected = [(2*anchor[0]-r, 2*anchor[1]-c, v) for r, c, v in shape]
    visible = [p for p in reflected if _inside(p, len(grid), len(grid[0]))]
    height, width = _spans(visible)
    return {"anchor": list(anchor), "visible_cells": [list(p) for p in visible],
            "height": height, "width": width,
            "axis": "row" if height >= width else "column",
            "source_span": list(_spans(shape)), "clipped_cells": len(shape)-len(visible)}


def predict(grid, settings, rival=None):
    """Independent geometry used to select teaching examples, not to certify labels."""
    mode = _setting(settings)
    allowed = _BASE_RIVALS + (_ECHO_RIVALS if mode == "visible_span_echo" else ())
    if rival is not None and rival not in allowed:
        raise ValueError(f"unknown rival {rival!r}")
    if rival == "identity":
        return [row[:] for row in grid]
    if rival == "other_setting":
        mode = "visible_span_echo" if mode == "point" else "point"
    anchor, original = _parts(grid)
    h, w = len(grid), len(grid[0])
    ar, ac = ((2, 3) if rival == "fixed_anchor" else
              (h//2, (w-1)//2) if rival == "grid_center" else anchor)
    selected = original
    if rival == "outline_only":
        positions = {(r, c) for r, c, _ in original}
        selected = [p for p in original if any(q not in positions for q in
                    ((p[0]-1, p[1]), (p[0]+1, p[1]), (p[0], p[1]-1), (p[0], p[1]+1)))]
    if rival == "left_of_anchor_only":
        selected = [p for p in original if p[1] <= ac]
    rsum = min(p[0] for p in original) + max(p[0] for p in original)
    csum = min(p[1] for p in original) + max(p[1] for p in original)
    reflected = []
    for r, c, v in selected:
        if rival == "horizontal_axis":
            rr, cc = 2*ar-r, c
        elif rival == "vertical_axis":
            rr, cc = r, 2*ac-c
        elif rival == "translate_only":
            rr, cc = r+2*ar-rsum, c+2*ac-csum
        else:
            rr, cc = 2*ar-r, 2*ac-c
        reflected.append((rr, cc, 9 if rival == "anchor_color_copy" else v))
    visible = [p for p in reflected if _inside(p, h, w)]
    if rival == "all_or_nothing" and len(visible) != len(reflected):
        visible = []
    reference = original if rival == "source_span" else visible
    vh, vw = _spans(reference)
    row_axis = vh >= vw
    if rival == "always_row": row_axis = True
    if rival == "always_column": row_axis = False
    if rival == "tie_columns": row_axis = vh > vw
    if rival == "opposite_axis": row_axis = not row_axis
    echo_source = reflected if rival == "unclipped_echo" else original if rival == "echo_source" else visible
    echo = []
    if mode == "visible_span_echo":
        echo = [(2*ar-r, c, v) if row_axis else (r, 2*ac-c, v) for r, c, v in echo_source]
    output = [row[:] for row in grid]
    if rival == "reflection_only":
        output = [[0]*w for _ in range(h)]
        output[anchor[0]][anchor[1]] = 9
    for r, c, v in ([] if rival == "omit_first_copy" else visible) + echo:
        if _inside((r, c), h, w):
            output[r][c] = v
    return output


@lru_cache(maxsize=64)
def _racket(mode, rival):
    if rival == "identity":
        return "(rule! (lambda (g) g))"
    if rival == "other_setting":
        mode = "visible_span_echo" if mode == "point" else "point"
    if mode == "point" and rival in (None, "other_setting"):
        return (_HOME / "canonical.rkt").read_text()
    center = "(list 2 3)" if rival == "fixed_anchor" else "(list (/ hh 2) (/ (- ww 1) 2))" if rival == "grid_center" else "anchor"
    selection = "source"
    if rival == "outline_only":
        selection = """(filter (lambda (p) (ormap (lambda (d)
          (not (ormap (lambda (q) (and (= (first q) (+ (first p) (first d)))
              (= (second q) (+ (second p) (second d))))) source)))
          (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))) source)"""
    elif rival == "left_of_anchor_only":
        selection = "(filter (lambda (p) (<= (second p) ac)) source)"
    rr, cc = "(- (* 2 ar) (first p))", "(- (* 2 ac) (second p))"
    if rival == "horizontal_axis": cc = "(second p)"
    if rival == "vertical_axis": rr = "(first p)"
    if rival == "translate_only":
        rr = "(- (+ (first p) (* 2 ar)) (+ (apply min (map first source)) (apply max (map first source))))"
        cc = "(- (+ (second p) (* 2 ac)) (+ (apply min (map second source)) (apply max (map second source))))"
    color = "9" if rival == "anchor_color_copy" else "(third p)"
    visible = "(if (= (length in-grid) (length reflected)) in-grid (list))" if rival == "all_or_nothing" else "in-grid"
    reference = "source" if rival == "source_span" else "visible"
    axis = {"always_row": "#t", "always_column": "#f", "tie_columns": "(> vh vw)",
            "opposite_axis": "(< vh vw)"}.get(rival, "(>= vh vw)")
    echo_source = "reflected" if rival == "unclipped_echo" else "source" if rival == "echo_source" else "visible"
    echo = f"""(map (lambda (p) (if row-axis
          (list (- (* 2 ar) (first p)) (second p) (third p))
          (list (first p) (- (* 2 ac) (second p)) (third p)))) {echo_source})""" if mode == "visible_span_echo" else "(list)"
    initial = "(set-cell (empty-grid hh ww 0) (first anchor) (second anchor) 9)" if rival == "reflection_only" else "g"
    drawn = "(list)" if rival == "omit_first_copy" else "visible"
    return f"""(rule!
 (let* ((hh (rows g)) (ww (cols g))
        (anchor (first (find-color g 9))) (center {center})
        (ar (first center)) (ac (second center))
        (source (for*/list ((r (in-range hh)) (c (in-range ww))
                 #:unless (member? (at g r c) (list 0 9))) (list r c (at g r c))))
        (selected {selection})
        (reflected (map (lambda (p) (list {rr} {cc} {color})) selected))
        (in-grid (filter (lambda (p) (in-bounds? (first p) (second p) hh ww)) reflected))
        (visible {visible}) (reference {reference})
        (vh (if (empty? reference) 0 (+ 1 (- (apply max (map first reference)) (apply min (map first reference))))))
        (vw (if (empty? reference) 0 (+ 1 (- (apply max (map second reference)) (apply min (map second reference))))))
        (row-axis {axis}) (echo {echo}))
   (for/fold ((out {initial})) ((p (in-list (append {drawn} echo))))
     (if (in-bounds? (first p) (second p) hh ww)
         (set-cell out (first p) (second p) (third p)) out))))"""


def program(settings):
    return _racket(_setting(settings), None)


def rival_programs(settings):
    mode = _setting(settings)
    return {name: _racket(mode, name) for name in
            _BASE_RIVALS + (_ECHO_RIVALS if mode == "visible_span_echo" else ())}


# Three constructive witnesses: clipped plus, complete tied-span L, clipped
# tall L. The last refutes echoing invisible first-stage cells back onto canvas.
_FIXTURES = (
    ((1, 2), ((1, 1), (2, 0), (2, 1), (2, 2), (3, 1))),
    ((2, 2), ((1, 3), (1, 4), (2, 4))),
    ((1, 1), ((1, 2), (2, 2), (3, 2), (3, 3))),
)


def _paint(h, w, anchor, cells, color):
    grid = [[0]*w for _ in range(h)]
    for r, c in cells:
        grid[r][c] = color
    grid[anchor[0]][anchor[1]] = 9
    return grid


def _flip(grid, lr, ud):
    if lr: grid = [list(reversed(row)) for row in grid]
    if ud: grid = list(reversed(grid))
    return grid


def _fixture(index, color, scale, h, w, lr, ud):
    anchor, cells = _FIXTURES[index]
    # Odd block scales preserve the exact cell-centered reflection geometry.
    cells = [(scale*r+dr, scale*c+dc) for r, c in cells
             for dr in range(scale) for dc in range(scale)]
    anchor = tuple(scale*x + scale//2 for x in anchor)
    return _flip(_paint(h*scale, w*scale, anchor, cells, color), lr, ud)


def _teaches(grids):
    for setting in SETTINGS:
        expected = [predict(grid, setting) for grid in grids]
        for name in rival_programs(setting):
            if all(predict(grid, setting, name) == output for grid, output in zip(grids, expected)):
                return False
    return True


def _large(rng, h, w, color):
    sh = rng.randint(8, min(13, h//2))
    sw = rng.randint(8, min(13, w//2))
    # Connected perimeter/spine plus variable filled interior, holes and bays.
    # This uses a substantial shape, not a tiny padded canonical example.
    cells = {(r, c) for r in range(sh) for c in range(sw)
             if r in (0, sh-1) or c in (0, sw-1) or r % 3 == 0 or c % 3 == 0 or rng.random() < .58}
    # Every retained interior pixel touches the grid of solid row/column ribs.
    pending = {(0, 0)}
    connected = set()
    while pending:
        p = pending.pop()
        if p in connected: continue
        connected.add(p)
        r, c = p
        pending.update(q for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if q in cells and q not in connected)
    grid = _paint(h, w, (h//2, w//2), connected, color)
    return _flip(grid, bool(rng.getrandbits(1)), bool(rng.getrandbits(1)))


def sample_inputs(seed, demos=3, queries=4):
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 4, "queries")
    rng = random.Random(seed ^ 0xB1972482CB43)
    # Settings never enter this RNG or any input-selection predicate.
    for attempt in range(16):
        lr, ud = bool(rng.getrandbits(1)), bool(rng.getrandbits(1))
        scaled = rng.randrange(3)
        grids = [_fixture(i, 1+(seed+i)%8, 3 if i == scaled else 1,
                          4+rng.randrange(2), 5+rng.randrange(3), lr, ud) for i in range(3)]
        if _teaches(grids):
            break
    else:
        grids = [_fixture(i, 1+(seed+i)%8, 3 if i == 1 else 1, 4, 5, False, False) for i in range(3)]
        if not _teaches(grids):
            raise RuntimeError("constructive witnesses failed the declared rival contract")
    for index in range(3, demos):
        grids.append(_fixture(index%3, 1+(seed+index)%8, 1, 6+index, 8+index,
                              bool(rng.getrandbits(1)), bool(rng.getrandbits(1))))
    # A separate stream preserves one-query/four-query first-turn identity.
    qrng = random.Random(seed ^ 0xEC404A17)
    candidates = [
        _fixture(qrng.randrange(3), 1+(seed+5)%8, 1, 4, 5,
                 bool(qrng.getrandbits(1)), bool(qrng.getrandbits(1))),
        _fixture(qrng.randrange(3), 1+(seed+6)%8, 3, 6, 8,
                 bool(qrng.getrandbits(1)), bool(qrng.getrandbits(1))),
        _large(qrng, 22, 26, 1+(seed+7)%8),
        _large(qrng, 30, 30, 1+(seed+4)%8),
    ]
    # The first/second queries use colors absent from all possible same-geometry
    # demonstrations; the two large queries have distinct dimensions.
    chosen = grids + candidates[:queries]
    if len({repr(grid) for grid in chosen}) != len(chosen):
        raise RuntimeError("constructive sampling produced duplicate inputs")
    if any(validate_grid(grid) for grid in chosen):
        raise RuntimeError("constructive sampling violated the family grammar")
    return grids, candidates[:queries]


def generate(seed, settings, demos=3, queries=4):
    _setting(settings)
    train, test = sample_inputs(seed, demos, queries)
    return {"train": [{"input": grid, "output": predict(grid, settings)} for grid in train],
            "test": [{"input": grid, "output": predict(grid, settings)} for grid in test],
            "program_solution": program(settings)}
