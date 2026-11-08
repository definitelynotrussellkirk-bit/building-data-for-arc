"""Finite, independent lookup rivals for the private MAIN self-review.

These functions do not import the generator or its parsing/matching helpers.
Every declared rival has a standalone Racket program so a Python prediction is
never mistaken for an authoritative label.  This bank is deliberately finite.
"""
from __future__ import annotations

from typing import Any


def _copy(grid):
    return [list(row) for row in grid]


def _crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    if not cells:
        return [[0]]
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def parse(grid):
    """Independent five-panel parser, following the canonical delimiter rule."""
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or any(type(row) is not list or len(row) != len(grid[0])
                                 for row in grid)):
        raise ValueError("Expected a rectangular list grid")
    if any(type(cell) is not int or not 0 <= cell <= 9
           for row in grid for cell in row):
        raise ValueError("Expected exact integer ARC cells")
    height, width = len(grid), len(grid[0])
    panels, start, col = [], 0, 0
    while col < width:
        if all(grid[row][col] == 9 for row in range(height)):
            if start < col:
                panels.append([row[start:col] for row in grid])
            while col < width and all(grid[row][col] == 9 for row in range(height)):
                col += 1
            start = col
        else:
            col += 1
    if start < width:
        panels.append([row[start:width] for row in grid])
    if len(panels) != 5:
        raise ValueError(f"Expected five panels, found {len(panels)}")
    return dict(zip(("key1", "value1", "key2", "value2", "query"),
                    [_crop(panel) for panel in panels[:4]] + [panels[4]]))


def _rotate(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _variants(template, transformations):
    values = [_copy(template)]
    if transformations in ("rotations", "dihedral"):
        for _ in range(3):
            values.append(_rotate(values[-1]))
    if transformations in ("dihedral", "reflections"):
        flipped = [list(reversed(row)) for row in template]
        values.append(flipped)
        for _ in range(3):
            flipped = _rotate(flipped)
            values.append(flipped)
    unique = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def has_match(board, template, *, wildcard=True, transformations="identity",
              missing=0, colorblind=False, color_present=False):
    """Independent placement search; missing counts required-cell disagreements."""
    if color_present:
        colors = {value for row in template for value in row if value != 0}
        return any(value in colors for row in board for value in row)
    for shape in _variants(template, transformations):
        for row in range(len(board) - len(shape) + 1):
            for col in range(len(board[0]) - len(shape[0]) + 1):
                mismatches = 0
                for dr, line in enumerate(shape):
                    for dc, target in enumerate(line):
                        actual = board[row + dr][col + dc]
                        if target == 0:
                            equal = wildcard or actual == 0
                        else:
                            equal = actual != 0 if colorblind else actual == target
                        mismatches += not equal
                if mismatches <= missing:
                    return True
    return False


_MATCH_OPTIONS = {
    "rotations": {"transformations": "rotations"},
    "reflections": {"transformations": "reflections"},
    "dihedral": {"transformations": "dihedral"},
    "one_missing": {"missing": 1},
    "zero_strict": {"wildcard": False},
    "colorblind": {"colorblind": True},
    "key_color_presence": {"color_present": True},
    "minority_key_color": {"frequency": "minority"},
    "majority_key_color": {"frequency": "majority"},
    "either_key": {},
}


def names(depth):
    if type(depth) is not int or depth not in (1, 2):
        raise ValueError("lookup_depth must be exact integer 1 or 2")
    result = ["constant_value1", "constant_value2", "other_lookup_depth",
              "invert_initial", "fixed_intermediate_value1",
              "fixed_intermediate_value2", "wrong_intermediate",
              "any_panel_key1", "larger_value_area", "smaller_value_area",
              "larger_foreground_count", "smaller_foreground_count"]
    for kind in _MATCH_OPTIONS:
        result.append(kind + "_both")
        if depth == 2:
            result.extend((kind + "_first", kind + "_second"))
    return tuple(result)


def _decode(name, depth):
    if name == "exact":
        return "lookup", depth, {}, {}
    if name == "other_lookup_depth":
        return "lookup", 3 - depth, {}, {}
    for kind, options in _MATCH_OPTIONS.items():
        for suffix in ("both", "first", "second"):
            if name == kind + "_" + suffix:
                chosen = dict(options)
                if kind == "either_key":
                    chosen["either_key"] = True
                return ("lookup", depth,
                        chosen if suffix in ("both", "first") else {},
                        chosen if suffix in ("both", "second") else {})
    if name not in names(depth):
        raise ValueError(f"Unknown rival {name!r}")
    return name, depth, {}, {}


def solve(grid, depth=1, name="exact"):
    facts = parse(grid)
    key1, key2 = facts["key1"], facts["key2"]
    value1, value2, query = facts["value1"], facts["value2"], facts["query"]
    operation, iterations, first_options, second_options = _decode(name, depth)

    def lookup(board, options=None):
        options = dict(options or {})
        either_key = options.pop("either_key", False)
        frequency = options.pop("frequency", None)
        if frequency is not None:
            colors = [{value for row in key for value in row if value != 0}
                      for key in (key1, key2)]
            count1, count2 = [sum(value in palette for row in board for value in row)
                              for palette in colors]
            if count1 == 0:
                found = False
            elif count2 == 0:
                found = True
            else:
                found = count1 <= count2 if frequency == "minority" else count1 >= count2
        else:
            found = has_match(board, key1, **options)
            if either_key:
                found = found or has_match(board, key2, **options)
        return value1 if found else value2

    if operation == "constant_value1":
        result = value1
    elif operation == "constant_value2":
        result = value2
    elif operation == "invert_initial":
        result = value2 if has_match(query, key1) else value1
    elif operation == "fixed_intermediate_value1":
        result = lookup(value1)
    elif operation == "fixed_intermediate_value2":
        result = lookup(value2)
    elif operation == "wrong_intermediate":
        result = lookup(value2 if has_match(query, key1) else value1)
    elif operation == "any_panel_key1":
        result = value1 if any(has_match(board, key1)
                               for board in (query, value1, value2)) else value2
    elif operation in ("larger_value_area", "smaller_value_area",
                       "larger_foreground_count", "smaller_foreground_count"):
        if operation.endswith("value_area"):
            scores = [len(value) * len(value[0]) for value in (value1, value2)]
        else:
            scores = [sum(cell != 0 for row in value for cell in row)
                      for value in (value1, value2)]
        choose_first = scores[0] >= scores[1] if operation.startswith("larger") else scores[0] <= scores[1]
        result = value1 if choose_first else value2
    else:
        result = lookup(query, first_options)
        if iterations == 2:
            result = lookup(result, second_options)
    return _copy(result)


_RACKET_COMMON = """(rule!
  (let ()
    (define (split-panels board)
      (let loop ((col 0) (start 0) (acc (list)))
        (cond
          ((>= col (cols board))
           (reverse (if (< start (cols board))
                        (cons (subgrid board 0 start (- (rows board) 1) (- (cols board) 1)) acc)
                        acc)))
          ((all? (lambda (row) (= (at board row col) 9)) (range 0 (rows board)))
           (let scan ((next col))
             (if (and (< next (cols board))
                      (all? (lambda (row) (= (at board row next) 9)) (range 0 (rows board))))
                 (scan (+ next 1))
                 (loop next next
                       (if (< start col)
                           (cons (subgrid board 0 start (- (rows board) 1) (- col 1)) acc)
                           acc)))))
          (else (loop (+ col 1) start acc)))))
    (define (crop board)
      (let ((cells (filter (lambda (p)
                            (let ((value (at board (first p) (second p))))
                              (and (not (= value 0)) (not (= value 9)))))
                          (grid-positions board))))
        (if (empty? cells)
            (grid (list 0))
            (let ((bb (bbox-of-cells cells)))
              (subgrid board (first bb) (second bb) (third bb) (fourth bb))))))
    (define (rotate3 board) (rotate-cw (rotate-180 board)))
    (define (variants template mode)
      (cond ((= mode 0) (list template))
            ((= mode 1) (list template (rotate-cw template) (rotate-180 template) (rotate3 template)))
            ((= mode 3) (list template (flip-lr template) (rotate-cw (flip-lr template))
                             (rotate-180 (flip-lr template)) (rotate3 (flip-lr template))))
            (else (list template (rotate-cw template) (rotate-180 template) (rotate3 template)
                        (flip-lr template) (rotate-cw (flip-lr template))
                        (rotate-180 (flip-lr template)) (rotate3 (flip-lr template))))))
    (define (color-present? board template)
      (let ((colors (map (lambda (p) (at template (first p) (second p)))
                         (filter (lambda (p) (not (= (at template (first p) (second p)) 0)))
                                 (grid-positions template)))))
        (not (empty? (filter (lambda (p) (member? (at board (first p) (second p)) colors))
                             (grid-positions board))))))
    (define (color-count board template)
      (let ((colors (map (lambda (p) (at template (first p) (second p)))
                         (filter (lambda (p) (not (= (at template (first p) (second p)) 0)))
                                 (grid-positions template)))))
        (length (filter (lambda (p) (member? (at board (first p) (second p)) colors))
                        (grid-positions board)))))
    (define (frequency-first? board key1 key2 most)
      (let ((count1 (color-count board key1)) (count2 (color-count board key2)))
        (cond ((= count1 0) #f)
              ((= count2 0) #t)
              (else (if most (>= count1 count2) (<= count1 count2))))))
    (define (match? board template mode wild blind missing)
      (not (empty?
        (flatmap
          (lambda (shape)
            (for*/list ((row (in-range 0 (+ 1 (- (rows board) (rows shape)))))
                        (col (in-range 0 (+ 1 (- (cols board) (cols shape)))))
              #:when
              (<= (length
                    (filter
                      (lambda (p)
                        (let ((target (at shape (first p) (second p)))
                              (actual (at board (+ row (first p)) (+ col (second p)))))
                          (not (if (= target 0)
                                   (or wild (= actual 0))
                                   (if blind (not (= actual 0)) (= actual target))))))
                      (grid-positions shape)))
                  missing))
              (list row col)))
          (variants template mode)))))
    (let* ((panels (split-panels g))
           (k1 (crop (first panels)))
           (v1 (crop (second panels)))
           (k2 (crop (third panels)))
           (v2 (crop (fourth panels)))
           (query (list-ref panels 4)))
      __RESULT__)))"""


def _match_expression(board, options=None):
    options = dict(options or {})
    if options.get("frequency"):
        most = "#t" if options["frequency"] == "majority" else "#f"
        return f"(frequency-first? {board} k1 k2 {most})"
    if options.get("color_present", False):
        return f"(color-present? {board} k1)"
    mode = {"identity": 0, "rotations": 1, "dihedral": 2, "reflections": 3}[options.get("transformations", "identity")]
    wildcard = "#t" if options.get("wildcard", True) else "#f"
    blind = "#t" if options.get("colorblind", False) else "#f"
    missing = options.get("missing", 0)
    first = f"(match? {board} k1 {mode} {wildcard} {blind} {missing})"
    if options.get("either_key", False):
        second = f"(match? {board} k2 {mode} {wildcard} {blind} {missing})"
        return f"(or {first} {second})"
    return first


def program(name, depth=1):
    """Return one complete protected-runtime-compatible Racket expression."""
    operation, iterations, first_options, second_options = _decode(name, depth)
    exact_query = _match_expression("query")

    def lookup(board, options=None):
        return f"(if {_match_expression(board, options)} v1 v2)"

    if operation == "constant_value1":
        expression = "v1"
    elif operation == "constant_value2":
        expression = "v2"
    elif operation == "invert_initial":
        expression = f"(if {exact_query} v2 v1)"
    elif operation == "fixed_intermediate_value1":
        expression = lookup("v1")
    elif operation == "fixed_intermediate_value2":
        expression = lookup("v2")
    elif operation == "wrong_intermediate":
        expression = f"(let ((wrong (if {exact_query} v2 v1))) {lookup('wrong')})"
    elif operation == "any_panel_key1":
        predicate = "(or " + " ".join(_match_expression(board) for board in ("query", "v1", "v2")) + ")"
        expression = f"(if {predicate} v1 v2)"
    elif operation in ("larger_value_area", "smaller_value_area",
                       "larger_foreground_count", "smaller_foreground_count"):
        if operation.endswith("value_area"):
            scores = [f"(* (rows {value}) (cols {value}))" for value in ("v1", "v2")]
        else:
            scores = [f"(length (filter (lambda (p) (not (= (at {value} (first p) (second p)) 0))) (grid-positions {value})))"
                      for value in ("v1", "v2")]
        comparison = ">=" if operation.startswith("larger") else "<="
        expression = f"(if ({comparison} {scores[0]} {scores[1]}) v1 v2)"
    elif iterations == 1:
        expression = lookup("query", first_options)
    else:
        expression = f"(let ((intermediate {lookup('query', first_options)})) {lookup('intermediate', second_options)})"
    return _RACKET_COMMON.replace("__RESULT__", expression)


DESCRIPTIONS: dict[str, Any] = {
    "scope": "Finite plausible template-search and lookup-composition alternatives; no universal uniqueness claim.",
    "matching": "Rotations, reflections, dihedral transforms, one required-cell disagreement, strict template zeros, colorblind occupied-cell matching, mere key-color presence, and either-key dispatch are tested at both hops and separately at each active hop.",
    "composition": "Constant output panel, other lookup depth, inverted initial branch, fixed value1/value2 intermediate, opposite selected intermediate, and an any-panel shortcut.",
    "size": "Always choose the larger/smaller cropped value area or nonzero foreground count; ties choose value1.",
    "frequency": "Choose the less/more frequent present key color without inspecting shape, at each active hop. A present color beats an absent color, positive ties select value1, and both colors absent selects value2.",
}
