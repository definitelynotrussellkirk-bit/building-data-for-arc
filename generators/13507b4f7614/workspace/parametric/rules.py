"""Episode-fixed rectangle joining followed by the unchanged canonical rule.

All bridge eligibility is computed from the original components. The canonical
operation then finds objects afresh in the joined grid. The Python implementation
is an independent diagnostic mirror; protected Racket supplies episode labels.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path


JOIN_AXES = ("none", "horizontal", "vertical")


def _axis(join_axis):
    if type(join_axis) is not str or join_axis not in JOIN_AXES:
        raise ValueError("join_axis must be none, horizontal, or vertical")
    return join_axis


def _checked_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in (0, 4) for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0 and 4")
    return [row[:] for row in grid]


def _objects(grid):
    """Return original color-4 cardinal components and their bounding boxes."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4}
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for candidate in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if candidate in remaining:
                    remaining.remove(candidate)
                    cells.add(candidate)
                    queue.append(candidate)
        rs, cs = zip(*cells)
        bounds = min(rs), min(cs), max(rs), max(cs)
        found.append((bounds, cells))
    return found


def _solid(bounds, cells):
    top, left, bottom, right = bounds
    return len(cells) == (bottom - top + 1) * (right - left + 1)


def joined_grid(grid, join_axis):
    """Fill eligible one-cell gaps simultaneously; do not reuse updated objects."""
    _axis(join_axis)
    output = _checked_grid(grid)
    if join_axis == "none":
        return output
    rectangles = [bounds for bounds, cells in _objects(grid) if _solid(bounds, cells)]
    bridges = set()
    for at, al, ab, ar in rectangles:
        for bt, bl, bb, br in rectangles:
            if join_axis == "horizontal" and at == bt and ab == bb and ar + 2 == bl:
                candidate = {(row, ar + 1) for row in range(at, ab + 1)}
            elif join_axis == "vertical" and al == bl and ar == br and ab + 2 == bt:
                candidate = {(ab + 1, col) for col in range(al, ar + 1)}
            else:
                continue
            if all(grid[row][col] == 0 for row, col in candidate):
                bridges.update(candidate)
    for row, col in bridges:
        output[row][col] = 4
    return output


def transform(grid, join_axis):
    """Diagnostic mirror: join, recompute components, reduce odd solid rectangles."""
    intermediate = joined_grid(grid, join_axis)
    output = [row[:] for row in intermediate]
    for bounds, cells in _objects(intermediate):
        top, left, bottom, right = bounds
        height, width = bottom - top + 1, right - left + 1
        if not _solid(bounds, cells) or height % 2 != 1 or width % 2 != 1:
            continue
        middle_row, middle_col = (top + bottom) // 2, (left + right) // 2
        for row, col in cells:
            output[row][col] = 4 if row == middle_row or col == middle_col else 0
    return output


def canonical_program():
    """Return the exact registered program, including its original whitespace."""
    return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def _joined_program(join_axis, *, operation="join_then_reduce", parity="both"):
    allow_horizontal = "#t" if join_axis in ("horizontal", "both") else "#f"
    allow_vertical = "#t" if join_axis in ("vertical", "both") else "#f"
    original = canonical_program()
    if not original.startswith("(rule! ") or not original.endswith(")"):
        raise ValueError("canonical resource must contain the exact selected rule expression")
    canonical_body = original[len("(rule! "):-1]
    if parity != "both":
        guard = "(and (= (modulo h 2) 1) (= (modulo w 2) 1) (solid-rect? obj))"
        if canonical_body.count(guard) != 1:
            raise ValueError("canonical odd-dimension guard is missing or ambiguous")
        replacement = {
            "ignore": "(solid-rect? obj)",
            "height_only": "(and (= (modulo h 2) 1) (solid-rect? obj))",
            "width_only": "(and (= (modulo w 2) 1) (solid-rect? obj))",
        }[parity]
        canonical_body = canonical_body.replace(guard, replacement)
    final = {
        "join_then_reduce": "(canonical (join-grid g))",
        "reduce_then_join": "(join-grid (canonical g))",
        "join_only": "(join-grid g)",
    }[operation]
    return f"""(rule!
  (let ()
    (define (join-grid source)
      (define rects
        (filter (lambda (obj) (and (= (obj-color obj) 4) (solid-rect? obj)))
                (objects source 0)))
      (for*/fold ((out source)) ((a (in-list rects)) (b (in-list rects)))
        (let ((bridge
          (cond
            ((and {allow_horizontal}
                  (= (obj-r1 a) (obj-r1 b)) (= (obj-r2 a) (obj-r2 b))
                  (= (+ (obj-c2 a) 2) (obj-c1 b)))
             (for/list ((r (in-range (obj-r1 a) (+ (obj-r2 a) 1))))
               (list r (+ (obj-c2 a) 1))))
            ((and {allow_vertical}
                  (= (obj-c1 a) (obj-c1 b)) (= (obj-c2 a) (obj-c2 b))
                  (= (+ (obj-r2 a) 2) (obj-r1 b)))
             (for/list ((c (in-range (obj-c1 a) (+ (obj-c2 a) 1))))
               (list (+ (obj-r2 a) 1) c)))
            (else (list)))))
          (if (all? (lambda (p) (= (at source (first p) (second p)) 0)) bridge)
              (paint-cells out bridge 4)
              out))))
    (define (canonical source)
      (let ((g source)) {canonical_body}))
    {final}))"""


def program(settings):
    """Materialize a fixed program; reject missing, extra, or mistyped settings."""
    if type(settings) is not dict or set(settings) != {"join_axis"}:
        raise ValueError("settings must contain exactly join_axis")
    join_axis = _axis(settings["join_axis"])
    if join_axis == "none":
        return canonical_program()
    return _joined_program(join_axis)


def counterfactual_program(join_axis, mode):
    """Private finite rivals and causal ablations; never public challenge content."""
    _axis(join_axis)
    if type(mode) is not str or mode not in (
            "skip_a", "wrong_order", "ignore_parity", "both_axes", "join_only",
            "height_only", "width_only", "first_bridge", "first_group"):
        raise ValueError("unsupported counterfactual mode")
    if mode == "skip_a":
        return canonical_program()
    if mode == "wrong_order":
        return _joined_program(join_axis, operation="reduce_then_join")
    if mode == "ignore_parity":
        return _joined_program(join_axis, parity="ignore")
    if mode in ("height_only", "width_only"):
        return _joined_program(join_axis, parity=mode)
    if mode == "both_axes":
        return _joined_program("both")
    if mode in ("first_bridge", "first_group"):
        source = _joined_program(join_axis)
        action = "(paint-cells out bridge 4)"
        if source.count(action) != 1:
            raise ValueError("bridge action is missing or ambiguous")
        if mode == "first_bridge":
            replacement = "(if (equal? out source) (paint-cells out bridge 4) out)"
        else:
            # All eligibility still reads the original rectangles. After the
            # first bridge, permit only bridges adjoining the component that
            # contains a newly painted (originally zero) cell. Thus a chain is
            # completed, but independent groups are deliberately omitted.
            replacement = """(if
                (or (equal? out source)
                    (any?
                      (lambda (component)
                        (and (= (obj-color component) 4)
                             (any? (lambda (p) (= (at source (first p) (second p)) 0))
                                   (obj-cells component))
                             (any?
                               (lambda (p)
                                 (any?
                                   (lambda (q)
                                     (= (+ (abs (- (first p) (first q)))
                                           (abs (- (second p) (second q)))) 1))
                                   (obj-cells component)))
                               bridge)))
                      (objects out 0)))
                (paint-cells out bridge 4)
                out)"""
        return source.replace(action, replacement)
    return _joined_program(join_axis, operation="join_only")
