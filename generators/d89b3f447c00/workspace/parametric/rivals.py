"""Independent finite rectangle-completion rivals with matching Racket programs.

No prototype or production helper is imported.  The exact mirror uses a
three-edge path predicate at each missing cell, independently of the canonical
rectangle-enumeration implementation.  These alternatives are a finite audit
bank, not an exhaustive description of every possible rule.
"""
from __future__ import annotations


def _copy(grid):
    return [list(row) for row in grid]


def _validate(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("Expected a rectangular exact-integer ARC grid")


def _colors(grid):
    return sorted({value for row in grid for value in row if value != 0})


def _points(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == color}


def _allowed_color(mode, color, colors, cells):
    if mode == "lowest_color_only":
        return color == colors[0]
    if mode == "highest_color_only":
        return color == colors[-1]
    if mode == "two_lowest_colors":
        return color in colors[:2]
    if mode == "three_markers_only":
        return len(cells) == 3
    if mode == "at_most_four_markers":
        return len(cells) <= 4
    area = ((max(r for r, _ in cells) - min(r for r, _ in cells) + 1)
            * (max(c for _, c in cells) - min(c for _, c in cells) + 1))
    if mode == "small_bbox_only":
        return area <= 25
    if mode == "large_bbox_only":
        return area > 25
    return True


def _eligible(cells, row, col, rows, cols, mode):
    if (row, col) in cells:
        return False
    for other_row in rows:
        if other_row == row or (other_row, col) not in cells:
            continue
        for other_col in cols:
            if other_col == col:
                continue
            if mode == "nonminimal_only" and (abs(other_row - row) == 1
                                                or abs(other_col - col) == 1):
                continue
            if mode == "adjacent_rows_cols_only" and (abs(other_row - row) != 1
                                                       or abs(other_col - col) != 1):
                continue
            if (row, other_col) in cells and (other_row, other_col) in cells:
                return True
    return False


def complete_once(grid, mode="exact"):
    output = _copy(grid)
    colors = _colors(grid)
    for color in colors:
        original = _points(grid, color)
        if not _allowed_color(mode, color, colors, original):
            continue
        rows = sorted({r for r, _ in original})
        cols = sorted({c for _, c in original})
        if mode.startswith("inplace_"):
            _, major, directions = mode.split("_")
            if directions[0] == "r":
                rows.reverse()
            if directions[1] == "r":
                cols.reverse()
            candidates = ([(r, c) for c in cols for r in rows]
                          if major == "column" else [(r, c) for r in rows for c in cols])
            cells = set(original)
            for row, col in candidates:
                if _eligible(cells, row, col, rows, cols, "exact"):
                    output[row][col] = color
                    cells.add((row, col))
        else:
            targets = [(r, c) for r in rows for c in cols
                       if _eligible(original, r, c, rows, cols, mode)]
            if mode == "one_completion_per_color":
                targets = targets[:1]
            for row, col in targets:
                output[row][col] = color
    return output


_ORDERS = tuple(f"inplace_{major}_{directions}"
                for major in ("row", "column")
                for directions in ("ff", "fr", "rf", "rr"))
_FILTERS = ("lowest_color_only", "highest_color_only", "two_lowest_colors",
            "three_markers_only", "at_most_four_markers", "small_bbox_only",
            "large_bbox_only", "nonminimal_only", "adjacent_rows_cols_only",
            "one_completion_per_color")
_GATES = ("multiple_colors_only", "four_or_more_colors_only",
          "large_canvas_only", "square_canvas_only")


def names(rounds):
    if type(rounds) is not int or rounds not in (1, 2):
        raise ValueError("completion_rounds must be integer 1 or 2")
    return (tuple(f"rounds_{n}" for n in (0, 1, 2, 3) if n != rounds)
            + ("fixed_point", "global_cartesian", "bounding_box_fill",
               "bounding_box_corners", "only_new_cells") + _FILTERS + _ORDERS + _GATES)


def solve(grid, rounds=1, name="exact"):
    _validate(grid)
    if name != "exact" and name not in names(rounds):
        raise ValueError(f"Unknown rival {name!r}")
    output = _copy(grid)
    if name in _GATES:
        enabled = {"multiple_colors_only": len(_colors(grid)) >= 2,
                   "four_or_more_colors_only": len(_colors(grid)) >= 4,
                   "large_canvas_only": min(len(grid), len(grid[0])) >= 12,
                   "square_canvas_only": len(grid) == len(grid[0])}[name]
        if not enabled:
            return output
    if name in ("global_cartesian", "bounding_box_fill", "bounding_box_corners"):
        for color in _colors(grid):
            cells = _points(grid, color)
            rows = sorted({r for r, _ in cells})
            cols = sorted({c for _, c in cells})
            if name == "bounding_box_fill":
                rows = range(rows[0], rows[-1] + 1)
                cols = range(cols[0], cols[-1] + 1)
            elif name == "bounding_box_corners":
                rows = sorted({rows[0], rows[-1]})
                cols = sorted({cols[0], cols[-1]})
            for row in rows:
                for col in cols:
                    output[row][col] = color
        return output
    if name == "fixed_point":
        for _ in range(12):
            updated = complete_once(output)
            if updated == output:
                return updated
            output = updated
        return output
    count = int(name.rsplit("_", 1)[1]) if name.startswith("rounds_") else rounds
    mode = name if name in _FILTERS or name in _ORDERS else "exact"
    for _ in range(count):
        output = complete_once(output, mode)
    if name == "only_new_cells":
        return [[value if grid[r][c] == 0 else 0 for c, value in enumerate(row)]
                for r, row in enumerate(output)]
    return output


_COMMON = """(rule!
 (let ()
  (define mode MODE)
  (define (points board color) (find-color board color))
  (define (axis cells first-axis)
    (sort (remove-duplicates (map (if first-axis first second) cells)) <))
  (define (eligible? cells r c rs cs)
    (and (not (member? (list r c) cells))
      (any? (lambda (rr)
        (and (not (= rr r)) (member? (list rr c) cells)
          (any? (lambda (cc)
            (and (not (= cc c))
              (or (not (= mode 8)) (and (> (abs (- rr r)) 1) (> (abs (- cc c)) 1)))
              (or (not (= mode 9)) (and (= (abs (- rr r)) 1) (= (abs (- cc c)) 1)))
              (member? (list r cc) cells) (member? (list rr cc) cells))) cs))) rs)))
  (define (enabled? color colors cells rs cs)
    (let ((area (* (+ 1 (- (last rs) (first rs))) (+ 1 (- (last cs) (first cs))))))
      (cond ((= mode 1) (= color (first colors)))
            ((= mode 2) (= color (last colors)))
            ((= mode 3) (member? color (take colors (min 2 (length colors)))))
            ((= mode 4) (= (length cells) 3))
            ((= mode 5) (<= (length cells) 4))
            ((= mode 6) (<= area 25))
            ((= mode 7) (> area 25))
            (else #t))))
  (define (step board)
    (let ((colors (grid-colors board 0)))
      (for/fold ((out board)) ((color (in-list colors)))
        (let* ((cells (points board color))
               (rs0 (axis cells #t)) (cs0 (axis cells #f))
               (rs ROWS) (cs COLS)
               (candidates CANDIDATES))
          (if (enabled? color colors cells rs0 cs0)
            STEP_BODY
            out)))))
  (define (repeat-steps board count)
    (for/fold ((out board)) ((iteration (in-range count))) (step out)))
  FINAL))
"""


def program(name="exact", rounds=1):
    if name != "exact" and name not in names(rounds):
        raise ValueError(f"Unknown rival {name!r}")
    mode = _FILTERS.index(name) + 1 if name in _FILTERS else 0
    source = _COMMON.replace("MODE", str(mode))
    rows, cols = "rs0", "cs0"
    column_major = False
    if name in _ORDERS:
        _, major, directions = name.split("_")
        rows = "(reverse rs0)" if directions[0] == "r" else "rs0"
        cols = "(reverse cs0)" if directions[1] == "r" else "cs0"
        column_major = major == "column"
    candidates = ("(for*/list ((c (in-list cs)) (r (in-list rs))) (list r c))"
                  if column_major else
                  "(for*/list ((r (in-list rs)) (c (in-list cs))) (list r c))")
    if name in _ORDERS:
        body = """(for/fold ((acc out)) ((p (in-list candidates)))
                    (if (eligible? (points acc color) (first p) (second p) rs cs)
                        (set-cell acc (first p) (second p) color) acc))"""
    else:
        targets = "(filter (lambda (p) (eligible? cells (first p) (second p) rs cs)) candidates)"
        if name == "one_completion_per_color":
            targets = "(let ((found " + targets + ")) (take found (min 1 (length found))))"
        body = "(for/fold ((acc out)) ((p (in-list " + targets + "))) (set-cell acc (first p) (second p) color))"
    source = source.replace("ROWS", rows).replace("COLS", cols)
    source = source.replace("CANDIDATES", candidates).replace("STEP_BODY", body)
    count = int(name.rsplit("_", 1)[1]) if name.startswith("rounds_") else rounds
    final = f"(repeat-steps g {count})"
    if name == "fixed_point":
        final = "(let loop ((out g) (remaining 12)) (if (= remaining 0) out (let ((next (step out))) (if (equal? next out) next (loop next (- remaining 1))))))"
    elif name in _GATES:
        predicate = {"multiple_colors_only": "(>= (length (grid-colors g 0)) 2)",
                     "four_or_more_colors_only": "(>= (length (grid-colors g 0)) 4)",
                     "large_canvas_only": "(>= (min (rows g) (cols g)) 12)",
                     "square_canvas_only": "(= (rows g) (cols g))"}[name]
        final = f"(if {predicate} (repeat-steps g {rounds}) g)"
    elif name == "only_new_cells":
        final = f"(let ((out (repeat-steps g {rounds}))) (grid-from-fn (rows g) (cols g) (lambda (r c) (if (= (at g r c) 0) (at out r c) 0))))"
    elif name in ("global_cartesian", "bounding_box_fill", "bounding_box_corners"):
        row_axis, col_axis = "rs", "cs"
        if name == "bounding_box_fill":
            row_axis, col_axis = "(range (first rs) (+ 1 (last rs)))", "(range (first cs) (+ 1 (last cs)))"
        elif name == "bounding_box_corners":
            row_axis, col_axis = "(remove-duplicates (list (first rs) (last rs)))", "(remove-duplicates (list (first cs) (last cs)))"
        final = """(for/fold ((out g)) ((color (in-list (grid-colors g 0))))
                    (let* ((cells (points g color)) (rs (axis cells #t)) (cs (axis cells #f)))
                      (for*/fold ((acc out)) ((r (in-list ROW_AXIS)) (c (in-list COL_AXIS)))
                        (set-cell acc r c color))))""".replace("ROW_AXIS", row_axis).replace("COL_AXIS", col_axis)
    return source.replace("FINAL", final)


DESCRIPTIONS = {
    "exact": "Synchronous three-edge path completion; the source grid is frozen within each round.",
    "round_counts": "0, 1, 2 or 3 synchronous rounds, excluding the requested count; fixed-point closure stops at stability or twelve rounds.",
    "geometry": "Global used-row by used-column product, geometric bounding-box fill, or only bounding-box corners.",
    "filters": "Complete only the lowest/highest/two lowest colors, exact-three or at-most-four marker colors, bbox area at most/above 25, nonminimal rectangles, unit-distance rectangles, or one target per color per round.",
    "inplace": "Eight in-place scans: row/column major with each axis ascending or descending, repeated the requested number of rounds.",
    "preservation": "Return only newly painted cells, erasing original clues.",
    "board_gates": "Apply the requested rule only on boards with at least two/four colors, both dimensions at least twelve, or equal height and width; otherwise return the original board.",
    "scope": "Finite plausible completion alternatives with explicit numeric thresholds; no universal uniqueness claim."
}
