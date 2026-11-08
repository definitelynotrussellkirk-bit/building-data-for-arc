"""Finite, independently executable rivals for the closure-rounds prototype.

These are private authoring hypotheses, not alternative official answers.
Their Python predictions use a separate component walk; their exact Racket
programs are replayed by audit.py through the protected same-checkout runtime.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Callable


def _components(grid, color, connectivity=4):
    pending = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value == color
    }
    offsets = ((-1, 0), (0, -1), (0, 1), (1, 0))
    if connectivity == 8:
        offsets += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    groups = []
    while pending:
        start = min(pending)
        pending.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in offsets:
                point = (r + dr, c + dc)
                if point in pending:
                    pending.remove(point)
                    queue.append(point)
                    cells.add(point)
        groups.append(cells)
    return groups


def _bbox(cells):
    return (
        min(r for r, _ in cells), min(c for _, c in cells),
        max(r for r, _ in cells), max(c for _, c in cells),
    )


def _paint_boxes(grid, groups, *, fixed_extent=False):
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for cells in groups:
        top, left, bottom, right = _bbox(cells)
        if fixed_extent:
            tall = bottom - top >= right - left
            bottom, right = top + (2 if tall else 1), left + (1 if tall else 2)
        for r in range(top, min(height - 1, bottom) + 1):
            for c in range(left, min(width - 1, right) + 1):
                output[r][c] = 3
    return output


def _closure(grid, color=2, connectivity=4, *, selected=None, fixed_extent=False):
    groups = _components(grid, color, connectivity)
    if selected == "first":
        groups = groups[:1]
    elif selected == "largest" and groups:
        groups = [max(groups, key=len)]
    elif selected == "global" and groups:
        groups = [set().union(*groups)]
    return _paint_boxes(grid, groups, fixed_extent=fixed_extent)


def _rounds(grid, count, *, first_connectivity=4, later_connectivity=4):
    output = _closure(grid, 2, first_connectivity)
    for _ in range(count - 1):
        output = _closure(output, 3, later_connectivity)
    return output


def _fixed_point(grid):
    output = _closure(grid)
    # Closure is monotone in green cells; a strict change adds at least one.
    for _ in range(len(grid) * len(grid[0]) + 1):
        updated = _closure(output, 3)
        if updated == output:
            return output
        output = updated
    raise AssertionError("monotone closure did not converge within grid area")


def _live_second_pass(grid, count=2, *, reverse=False):
    """Re-fetch live green components at snapshot representatives, in scan order."""
    output = _closure(grid)
    if count == 1:
        return output
    representatives = sorted((min(cells) for cells in _components(output, 3)), reverse=reverse)
    for representative in representatives:
        current = next(cells for cells in _components(output, 3) if representative in cells)
        output = _paint_boxes(output, [current])
    return output


_HELPERS = """
    (define (colored state target)
      (filter (lambda (o) (= (obj-color o) target)) (objects state 0)))
    (define (colored8 state target)
      (filter (lambda (o) (= (obj-color o) target)) (objects-8 state 0)))
    (define (fill-objects state objs)
      (for/fold ([out state]) ([obj (in-list objs)])
        (paint-cells out
          (positions-in-rect (obj-r1 obj) (obj-c1 obj)
                             (obj-r2 obj) (obj-c2 obj)) 3)))
    (define (close4 state target) (fill-objects state (colored state target)))
    (define (close8 state target) (fill-objects state (colored8 state target)))
"""


def _program(body, helpers=""):
    return "(rule! (lambda (g)\n" + _HELPERS + helpers + "\n    " + body + "))"


def _correct_body(count):
    return "(close4 g 2)" if count == 1 else "(close4 (close4 g 2) 3)"


def build(settings: dict, canonical_program: str) -> dict[str, dict]:
    """Return name → description/predict/program for an exact declared setting."""
    count = settings["closure_rounds"]
    if type(count) is not int or count not in (1, 2):
        raise ValueError("closure_rounds must be exactly integer 1 or 2")
    entries: dict[str, dict] = {}

    def add(name: str, description: str, predict: Callable, source: str):
        entries[name] = {"description": description, "predict": predict, "program": source}

    opposite = 3 - count
    add(
        "opposite_rounds", "Use the other declared number of closure rounds.",
        lambda grid: _rounds(grid, opposite),
        canonical_program if opposite == 1 else _program(_correct_body(2)),
    )
    add(
        "stale_red_components",
        "Close red once, then fill only boxes of the original red components again.",
        lambda grid: _paint_boxes(_closure(grid), _components(grid, 2)),
        _program("(fill-objects (close4 g 2) (colored g 2))"),
    )
    add(
        "three_rounds", "Perform exactly three closures with recomputation.",
        lambda grid: _rounds(grid, 3),
        _program("(close4 (close4 (close4 g 2) 3) 3)"),
    )
    add(
        "fixed_point", "Continue recomputing and filling until no green cell changes.",
        _fixed_point,
        _program("""(let loop ([state (close4 g 2)] [fuel 901])
      (let ([next (close4 state 3)])
        (if (or (equal? state next) (= fuel 0)) next
            (loop next (- fuel 1)))))"""),
    )
    live_helpers = """
    (define (point-before? left right)
      (or (< (first left) (first right))
          (and (= (first left) (first right)) (< (second left) (second right)))))
    (define (representative obj)
      (car (sort (obj-cells obj) point-before?)))
"""
    for reverse in (False, True):
        order = "descending" if reverse else "ascending"
        representatives = "(reverse reps)" if reverse else "reps"
        body = f"""(let* ([stage1 (close4 g 2)]
                   [reps (sort (map representative (colored stage1 3)) point-before?)])
      (for/fold ([out stage1]) ([p (in-list {representatives})])
        (let ([live (filter (lambda (o) (member p (obj-cells o))) (colored out 3))])
          (fill-objects out live))))"""
        add(
            f"live_second_pass_{order}",
            f"Visit first-pass green-component representatives in {order} row-major order; before each fill, recompute its component from the live second-pass grid.",
            lambda grid, reverse=reverse: _live_second_pass(grid, count, reverse=reverse),
            canonical_program if count == 1 else _program(body, live_helpers),
        )
    add(
        "eight_connected_first",
        "Use eight-neighbor red components in the first closure only.",
        lambda grid: _rounds(grid, count, first_connectivity=8),
        _program("(close8 g 2)" if count == 1 else "(close4 (close8 g 2) 3)"),
    )
    add(
        "eight_connected_second",
        "Use eight-neighbor green components in the second closure when present.",
        lambda grid: _rounds(grid, count, later_connectivity=8),
        _program("(close4 g 2)" if count == 1 else "(close8 (close4 g 2) 3)"),
    )
    add(
        "one_global_box", "Fill one bounding box around every red cell.",
        lambda grid: _closure(grid, selected="global"),
        _program("""(let ([cells (apply append (map obj-cells (colored g 2)))])
      (if (null? cells) g
          (paint-cells g
            (positions-in-rect (apply min (map first cells))
                               (apply min (map second cells))
                               (apply max (map first cells))
                               (apply max (map second cells))) 3)))"""),
    )
    for selector in ("first", "largest"):
        def selected(grid, selector=selector):
            if count == 1:
                return _closure(grid, selected=selector)
            return _closure(_closure(grid), 3, selected=selector)

        state = "g" if count == 1 else "(close4 g 2)"
        target = 2 if count == 1 else 3
        choice = "(car objs)" if selector == "first" else "(pick-max objs obj-size)"
        add(
            f"{selector}_component_only",
            f"Apply the final closure only to the {selector} component.",
            selected,
            _program(f"""(let* ([state {state}] [objs (colored state {target})])
      (if (null? objs) state (fill-objects state (list {choice}))))"""),
        )

    def fixed_extent(grid):
        output = _closure(grid, fixed_extent=True)
        return output if count == 1 else _closure(output, 3)

    fixed_helpers = """
    (define (fixed-close state)
      (for/fold ([out state]) ([obj (in-list (colored state 2))])
        (let ([tall (>= (obj-h obj) (obj-w obj))])
          (paint-cells out
            (positions-in-rect (obj-r1 obj) (obj-c1 obj)
              (+ (obj-r1 obj) (if tall 2 1))
              (+ (obj-c1 obj) (if tall 1 2))) 3))))
"""
    add(
        "fixed_canonical_extent", "Replace each first-pass bbox by a fixed 3×2 or 2×3 stamp.",
        fixed_extent,
        _program("(fixed-close g)" if count == 1 else "(close4 (fixed-close g) 3)", fixed_helpers),
    )

    def retain_red(grid):
        output = _rounds(grid, count)
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 2:
                    output[r][c] = 2
        return output

    add(
        "retain_original_red", "Fill the intended cells but retain every original red cell.",
        retain_red,
        _program(f"(let ([out {_correct_body(count)}]) (cellmap out (r c v) (if (= (at g r c) 2) 2 v)))"),
    )
    add(
        "erase_decorations", "Execute the intended closures and erase all unrelated colors.",
        lambda grid: [[v if v in (0, 2, 3) else 0 for v in row] for row in _rounds(grid, count)],
        _program(f"(let ([out {_correct_body(count)}]) (cellmap out (r c v) (if (member v '(0 2 3)) v 0)))"),
    )
    add(
        "skip_first_closure", "Skip red closure and try green closure on the original grid.",
        lambda grid: _closure(grid, 3),
        _program("(close4 g 3)"),
    )
    return entries


def lesson_check(episode: dict, settings: dict, canonical_program: str) -> dict:
    """Check original demonstrations alone against every query, without label fitting."""
    rows = []
    for name, rival in build(settings, canonical_program).items():
        demo_disagreements = [
            index for index, pair in enumerate(episode["train"])
            if rival["predict"](pair["input"]) != pair["output"]
        ]
        query_disagreements = [
            index for index, pair in enumerate(episode["test"])
            if rival["predict"](pair["input"]) != pair["output"]
        ]
        rows.append({
            "rival": name,
            "demo_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "ambiguous": not demo_disagreements and bool(query_disagreements),
        })
    return {"rivals": rows, "ambiguities": [row for row in rows if row["ambiguous"]]}
