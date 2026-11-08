"""Exact Python claims and Racket programs for the rotation relay family."""
from __future__ import annotations

import copy

CANONICAL_PROGRAM = "(rule! (rotate-cw g))"
VALUES = ("none", "marker_relay")
EDGE_CODES = {"top": 0, "bottom": 1, "left": 2, "right": 3}


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"post_rotation"}
            or type(settings["post_rotation"]) is not str
            or settings["post_rotation"] not in VALUES):
        raise ValueError("settings must contain exactly one supported post_rotation value")
    return settings["post_rotation"]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _marker_edge(grid):
    marker = [(r, c) for r, row in enumerate(grid)
              for c, value in enumerate(row) if value == 9]
    if len(marker) != 1:
        return None, None
    r, c = marker[0]
    h, w = len(grid), len(grid[0])
    if r == 0:
        return "top", (r, c)
    if r == h - 1:
        return "bottom", (r, c)
    if c == 0:
        return "left", (r, c)
    if c == w - 1:
        return "right", (r, c)
    return None, (r, c)


def _pack(grid, edge=None, marker=None):
    if edge is None or marker is None:
        edge, marker = _marker_edge(grid)
    if edge is None:
        return copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    output = [[9 if (r, c) == marker else 0 for c in range(w)] for r in range(h)]
    line_count = w if edge in {"top", "bottom"} else h
    for line in range(line_count):
        if edge == "top":
            coords = [(r, line) for r in range(h)]
        elif edge == "bottom":
            coords = [(r, line) for r in range(h - 1, -1, -1)]
        elif edge == "left":
            coords = [(line, c) for c in range(w)]
        else:
            coords = [(line, c) for c in range(w - 1, -1, -1)]
        values = [grid[r][c] for r, c in coords if grid[r][c] not in (0, 9)]
        destinations = [(r, c) for r, c in coords if (r, c) != marker]
        for value, (r, c) in zip(values, destinations):
            output[r][c] = value
    return output


def _contact(grid, edge, marker):
    r, c = marker
    point = {
        "top": (r + 1, c),
        "bottom": (r - 1, c),
        "left": (r, c + 1),
        "right": (r, c - 1),
    }.get(edge)
    return 0 if point is None else grid[point[0]][point[1]]


def _second_edge(cue):
    return "top" if cue == 1 else "left" if cue == 2 else None


def relay_trace(grid):
    after_a = _rotate_cw(grid)
    first_edge, marker = _marker_edge(after_a)
    if first_edge is None:
        return {
            "after_rotation": after_a,
            "first_settled": copy.deepcopy(after_a),
            "first_edge": None,
            "marker": None,
            "contact_color": 0,
            "second_edge": None,
            "output": copy.deepcopy(after_a),
        }
    first_settled = _pack(after_a, first_edge, marker)
    cue = _contact(first_settled, first_edge, marker)
    second_edge = _second_edge(cue)
    output = first_settled if second_edge is None else _pack(first_settled, second_edge, marker)
    return {
        "after_rotation": after_a,
        "first_settled": first_settled,
        "first_edge": first_edge,
        "marker": list(marker),
        "contact_color": cue,
        "second_edge": second_edge,
        "output": output,
    }


def python_apply(grid, mode):
    if mode not in VALUES:
        raise ValueError("unsupported post_rotation mode")
    return _rotate_cw(grid) if mode == "none" else relay_trace(grid)["output"]


def python_counterfactual(grid, kind):
    if kind == "skip_b":
        return relay_trace(grid)["first_settled"]
    if kind == "skip_a":
        edge, marker = _marker_edge(grid)
        first = _pack(grid, edge, marker)
        cue = _contact(first, edge, marker) if edge is not None else 0
        second = _second_edge(cue)
        return first if second is None else _pack(first, second, marker)
    if kind == "wrong_order":
        return _rotate_cw(python_counterfactual(grid, "skip_a"))
    trace = relay_trace(grid)
    if kind == "wrong_intermediate":
        swapped = 2 if trace["contact_color"] == 1 else 1 if trace["contact_color"] == 2 else 0
        edge = _second_edge(swapped)
        return trace["first_settled"] if edge is None else _pack(
            trace["first_settled"], edge, tuple(trace["marker"]))
    if kind == "opposite_second_edge":
        opposite = "bottom" if trace["second_edge"] == "top" else "right" if trace["second_edge"] == "left" else None
        return trace["first_settled"] if opposite is None else _pack(
            trace["first_settled"], opposite, tuple(trace["marker"]))
    if kind in {"always_top", "always_left"}:
        forced = "top" if kind == "always_top" else "left"
        return trace["first_settled"] if trace["marker"] is None else _pack(
            trace["first_settled"], forced, tuple(trace["marker"]))
    raise ValueError("unknown counterfactual kind")


_RACKET_HELPERS = r"""
    (define (edge-of grid marker)
      (let ((r (first marker)) (c (second marker))
            (hh (rows grid)) (ww (cols grid)))
        (cond ((= r 0) 0)
              ((= r (- hh 1)) 1)
              ((= c 0) 2)
              ((= c (- ww 1)) 3)
              (else -1))))
    (define (payload? value) (and (not (= value 0)) (not (= value 9))))
    (define (pack grid edge marker)
      (if (= edge -1)
          grid
          (let* ((hh (rows grid)) (ww (cols grid))
                 (line-count (if (< edge 2) ww hh))
                 (cleared
                  (for*/fold ((out grid))
                             ((r (in-range hh)) (c (in-range ww)))
                    (if (payload? (at grid r c))
                        (set-cell out r c 0)
                        out))))
            (define (coords line)
              (cond ((= edge 0)
                     (for/list ((r (in-range hh))) (list r line)))
                    ((= edge 1)
                     (for/list ((r (in-range (- hh 1) -1 -1))) (list r line)))
                    ((= edge 2)
                     (for/list ((c (in-range ww))) (list line c)))
                    (else
                     (for/list ((c (in-range (- ww 1) -1 -1))) (list line c)))))
            (for/fold ((out cleared)) ((line (in-range line-count)))
              (let* ((cells (coords line))
                     (values
                      (filter payload?
                              (map (lambda (p) (at grid (first p) (second p))) cells)))
                     (destinations
                      (filter (lambda (p) (not (equal? p marker))) cells)))
                (for/fold ((acc out)) ((i (in-range (length values))))
                  (let ((p (list-ref destinations i)))
                    (set-cell acc (first p) (second p) (list-ref values i)))))))))
    (define (contact grid edge marker)
      (let ((r (first marker)) (c (second marker)))
        (cond ((= edge 0) (at grid (+ r 1) c))
              ((= edge 1) (at grid (- r 1) c))
              ((= edge 2) (at grid r (+ c 1)))
              ((= edge 3) (at grid r (- c 1)))
              (else 0))))
    (define (second-edge cue)
      (cond ((= cue 1) 0) ((= cue 2) 2) (else -1)))
"""


def _compose(final_expression):
    return "(rule!\n  (let ()\n" + _RACKET_HELPERS + "\n    " + final_expression + "))"


MARKER_RELAY_PROGRAM = _compose(
    "(let* ((after-a (rotate-cw g))\n"
    "           (markers (find-color after-a 9)))\n"
    "      (if (= (length markers) 1)\n"
    "          (let* ((marker (first markers))\n"
    "                 (first-edge (edge-of after-a marker))\n"
    "                 (first-settled (pack after-a first-edge marker))\n"
    "                 (cue (contact first-settled first-edge marker))\n"
    "                 (second (second-edge cue)))\n"
    "            (if (= second -1) first-settled\n"
    "                (pack first-settled second marker)))\n"
    "          after-a))"
)


def program(settings):
    return CANONICAL_PROGRAM if _mode(settings) == "none" else MARKER_RELAY_PROGRAM


def counterfactual_program(kind):
    if kind == "skip_b":
        return _compose(
            "(let* ((after-a (rotate-cw g)) (markers (find-color after-a 9)))\n"
            "      (if (= (length markers) 1)\n"
            "          (let* ((marker (first markers)) (edge (edge-of after-a marker)))\n"
            "            (pack after-a edge marker))\n"
            "          after-a))"
        )
    if kind == "skip_a":
        return _compose(
            "(let ((markers (find-color g 9)))\n"
            "      (if (= (length markers) 1)\n"
            "          (let* ((marker (first markers)) (edge (edge-of g marker))\n"
            "                 (first-settled (pack g edge marker))\n"
            "                 (cue (contact first-settled edge marker))\n"
            "                 (second (second-edge cue)))\n"
            "            (if (= second -1) first-settled\n"
            "                (pack first-settled second marker)))\n"
            "          g))"
        )
    if kind == "wrong_order":
        inner = counterfactual_program("skip_a")
        body = inner[len("(rule!"): -1].strip()
        return f"(rule! (rotate-cw {body}))"
    if kind == "wrong_intermediate":
        return _compose(
            "(let* ((after-a (rotate-cw g)) (markers (find-color after-a 9)))\n"
            "      (if (= (length markers) 1)\n"
            "          (let* ((marker (first markers)) (first-edge (edge-of after-a marker))\n"
            "                 (first-settled (pack after-a first-edge marker))\n"
            "                 (cue (contact first-settled first-edge marker))\n"
            "                 (wrong-cue (cond ((= cue 1) 2) ((= cue 2) 1) (else 0)))\n"
            "                 (second (second-edge wrong-cue)))\n"
            "            (if (= second -1) first-settled\n"
            "                (pack first-settled second marker)))\n"
            "          after-a))"
        )
    if kind == "opposite_second_edge":
        return _compose(
            "(let* ((after-a (rotate-cw g)) (markers (find-color after-a 9)))\n"
            "      (if (= (length markers) 1)\n"
            "          (let* ((marker (first markers)) (first-edge (edge-of after-a marker))\n"
            "                 (first-settled (pack after-a first-edge marker))\n"
            "                 (cue (contact first-settled first-edge marker))\n"
            "                 (second (cond ((= cue 1) 1) ((= cue 2) 3) (else -1))))\n"
            "            (if (= second -1) first-settled\n"
            "                (pack first-settled second marker)))\n"
            "          after-a))"
        )
    if kind in {"always_top", "always_left"}:
        forced = 0 if kind == "always_top" else 2
        return _compose(
            "(let* ((after-a (rotate-cw g)) (markers (find-color after-a 9)))\n"
            "      (if (= (length markers) 1)\n"
            "          (let* ((marker (first markers)) (first-edge (edge-of after-a marker))\n"
            "                 (first-settled (pack after-a first-edge marker)))\n"
            f"            (pack first-settled {forced} marker))\n"
            "          after-a))"
        )
    raise ValueError("unknown counterfactual kind")
