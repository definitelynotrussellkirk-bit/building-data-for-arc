"""Independent semantics and falsifiable alternatives for the header family.

This module does not import the prototype or generator.  Python discovers
components by flood fill; emitted Racket discovers objects in the constructed
matrix.  These are audit predictions, never a replacement reference authority.

On a header equality matrix, monochromatic 4- and 8-connectivity coincide.
Each component is a maximal same-color row run times a maximal same-color
column run.  Its bounding-box area is therefore its cell count.  Those
equivalent algorithms are deliberately absent from the rival bank.
"""
from __future__ import annotations

from collections import Counter
from functools import partial
from itertools import groupby
from pathlib import Path


MODES = ("all_matches", "largest_blocks")


def validate(grid):
    """Require the complete admitted grammar, including exact Python types."""
    if type(grid) is not list or not 2 <= len(grid) <= 30:
        raise ValueError("input must be an exact list with 2..30 rows")
    if type(grid[0]) is not list or not 2 <= len(grid[0]) <= 30:
        raise ValueError("input must have 2..30 columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("input must be rectangular exact lists of integer colors 0..9")
    if grid[0][0] != 0:
        raise ValueError("corner must be zero")
    if any(value == 0 for value in grid[0][1:]) or any(row[0] == 0 for row in grid[1:]):
        raise ValueError("both header axes must be nonzero")
    if any(value != 0 for row in grid[1:] for value in row[1:]):
        raise ValueError("input interior must be zero")
    return grid


def _mode(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"unknown selection mode: {mode!r}")
    return mode


def headers(grid):
    validate(grid)
    return [row[0] for row in grid[1:]], list(grid[0][1:])


def from_headers(rows, cols):
    grid = [[0, *cols], *[[value, *([0] * len(cols))] for value in rows]]
    return validate(grid)


def components(matrix, *, diagonal=False, monochromatic=True):
    """Return row-major components as tuples of (row,column) coordinates."""
    height, width = len(matrix), len(matrix[0])
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen, result = set(), []
    for row in range(height):
        for col in range(width):
            if matrix[row][col] == 0 or (row, col) in seen:
                continue
            color = matrix[row][col]
            pending, cells = [(row, col)], []
            seen.add((row, col))
            while pending:
                current = pending.pop()
                cells.append(current)
                for dr, dc in deltas:
                    nr, nc = current[0] + dr, current[1] + dc
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr, nc) not in seen and matrix[nr][nc] != 0 and
                            (not monochromatic or matrix[nr][nc] == color)):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def _retain(matrix, objects):
    keep = {cell for obj in objects for cell in obj}
    return [[value if (row, col) in keep else 0 for col, value in enumerate(line)]
            for row, line in enumerate(matrix)]


def _rank(values, kind):
    if kind == "sorted":
        ordered = sorted(set(values))
        return {value: index for index, value in enumerate(ordered)}
    if kind == "first_seen":
        return {value: index for index, value in enumerate(dict.fromkeys(values))}
    counts = Counter(values)
    ranks = {count: index for index, count in enumerate(sorted(set(counts.values())))}
    return {value: ranks[count] for value, count in counts.items()}


def _run_ordinals(values):
    result, starts = [], Counter()
    for index, value in enumerate(values):
        if index == 0 or values[index - 1] != value:
            starts[value] += 1
        result.append(starts[value] - 1)
    return result


STAGE_RIVALS = (
    "ordinal_header_rank", "first_seen_header_rank", "frequency_header_rank",
    "row_rank_fallback", "col_rank_fallback", "row_headers_must_match",
    "col_headers_must_match", "boolean_match", "all_crossings",
    "shared_row_fills_row", "shared_col_fills_col", "first_matching_column",
    "last_matching_column", "first_matching_row", "last_matching_row",
    "occurrence_pairing", "zip_same_color_runs", "numeric_min_match_color",
    "numeric_max_match_color", "unequal_headers",
)

SELECTION_RIVALS = (
    "largest_color_total", "largest_color_bbox", "most_frequent_row_color",
    "most_frequent_col_color", "all_cells_of_winning_colors",
    "first_largest_component", "last_largest_component", "per_color_largest",
    "one_component_per_winning_color", "largest_height", "largest_width",
    "largest_perimeter", "largest_min_dimension", "largest_max_dimension",
    "minimum_color_winners", "maximum_color_winners", "non_singletons",
    "at_least_half_max", "top_two_distinct_sizes", "unique_max_or_empty",
    "binary_eight_connected", "include_header_frame",
)

OUTPUT_RIVALS = ("transpose_output", "reverse_output_rows", "reverse_output_columns",
                 "crop_to_foreground", "retain_header_frame")


def _matrix(rows, cols, name=None):
    shared = set(rows) & set(cols)
    if name in {"ordinal_header_rank", "row_rank_fallback", "col_rank_fallback"}:
        rr, cr = _rank(rows, "sorted"), _rank(cols, "sorted")
    elif name == "first_seen_header_rank":
        rr, cr = _rank(rows, "first_seen"), _rank(cols, "first_seen")
    elif name == "frequency_header_rank":
        rr, cr = _rank(rows, "frequency"), _rank(cols, "frequency")
    else:
        rr = cr = {}
    row_runs, col_runs = _run_ordinals(rows), _run_ordinals(cols)
    result = []
    for r, left in enumerate(rows):
        line = []
        for c, top in enumerate(cols):
            match, color = left == top, left
            if name in {"ordinal_header_rank", "first_seen_header_rank", "frequency_header_rank"}:
                match = rr[left] == cr[top]
            elif name == "row_rank_fallback":
                match = match or (left not in cols and rr[left] == cr[top])
            elif name == "col_rank_fallback":
                match = match or (top not in rows and rr[left] == cr[top])
            elif name == "row_headers_must_match":
                match = match or (left not in cols and c == r % len(cols))
            elif name == "col_headers_must_match":
                if top not in rows and r == c % len(rows):
                    match, color = True, top
            elif name == "boolean_match":
                color = 1
            elif name == "all_crossings":
                match = True
            elif name == "shared_row_fills_row":
                match = left in shared
            elif name == "shared_col_fills_col":
                match, color = top in shared, top
            elif name == "first_matching_column":
                match = match and c == cols.index(left)
            elif name == "last_matching_column":
                match = match and c == len(cols) - 1 - cols[::-1].index(left)
            elif name == "first_matching_row":
                match = match and r == rows.index(top)
            elif name == "last_matching_row":
                match = match and r == len(rows) - 1 - rows[::-1].index(top)
            elif name == "occurrence_pairing":
                match = match and rows[:r + 1].count(left) == cols[:c + 1].count(top)
            elif name == "zip_same_color_runs":
                match = match and row_runs[r] == col_runs[c]
            elif name == "numeric_min_match_color":
                match = match and left == min(shared, default=0)
            elif name == "numeric_max_match_color":
                match = match and left == max(shared, default=0)
            elif name == "unequal_headers":
                match = not match
            line.append(color if match else 0)
        result.append(line)
    return result


def _selection(matrix, rows, cols, name="largest_blocks"):
    if name == "all_matches":
        return [line[:] for line in matrix]
    if name == "include_header_frame":
        framed = [[0, *cols], *[[color, *line] for color, line in zip(rows, matrix)]]
        objects = components(framed)
        biggest = max(map(len, objects), default=0)
        kept = _retain(framed, [obj for obj in objects if len(obj) == biggest])
        return [line[1:] for line in kept[1:]]
    objects = components(matrix, diagonal=name == "binary_eight_connected",
                         monochromatic=name != "binary_eight_connected")
    if not objects:
        return [line[:] for line in matrix]
    largest = max(map(len, objects))
    winners = [obj for obj in objects if len(obj) == largest]
    color = lambda obj: matrix[obj[0][0]][obj[0][1]]
    row_span = lambda obj: max(r for r, _ in obj) - min(r for r, _ in obj) + 1
    col_span = lambda obj: max(c for _, c in obj) - min(c for _, c in obj) + 1
    by_color = {value: [cell for obj in objects if color(obj) == value for cell in obj]
                for value in {color(obj) for obj in objects}}
    if name == "largest_color_total":
        scores = {value: len(cells) for value, cells in by_color.items()}
    elif name == "largest_color_bbox":
        scores = {value: row_span(cells) * col_span(cells) for value, cells in by_color.items()}
    elif name == "most_frequent_row_color":
        counts = Counter(rows)
        scores = {value: counts[value] for value in by_color}
    elif name == "most_frequent_col_color":
        counts = Counter(cols)
        scores = {value: counts[value] for value in by_color}
    else:
        scores = None
    if scores is not None:
        maximum = max(scores.values())
        winners = [obj for obj in objects if scores[color(obj)] == maximum]
    elif name == "all_cells_of_winning_colors":
        winning_colors = {color(obj) for obj in winners}
        winners = [obj for obj in objects if color(obj) in winning_colors]
    elif name == "first_largest_component":
        winners = winners[:1]
    elif name == "last_largest_component":
        winners = winners[-1:]
    elif name == "per_color_largest":
        maxima = {value: max(len(obj) for obj in objects if color(obj) == value) for value in by_color}
        winners = [obj for obj in objects if len(obj) == maxima[color(obj)]]
    elif name == "one_component_per_winning_color":
        first = {}
        for obj in winners:
            first.setdefault(color(obj), obj)
        winners = list(first.values())
    elif name in {"largest_height", "largest_width", "largest_perimeter",
                  "largest_min_dimension", "largest_max_dimension"}:
        score = {"largest_height": row_span, "largest_width": col_span,
                 "largest_perimeter": lambda obj: 2 * (row_span(obj) + col_span(obj)),
                 "largest_min_dimension": lambda obj: min(row_span(obj), col_span(obj)),
                 "largest_max_dimension": lambda obj: max(row_span(obj), col_span(obj))}[name]
        maximum = max(map(score, objects))
        winners = [obj for obj in objects if score(obj) == maximum]
    elif name in {"minimum_color_winners", "maximum_color_winners"}:
        selected_color = (min if name == "minimum_color_winners" else max)(map(color, winners))
        winners = [obj for obj in winners if color(obj) == selected_color]
    elif name == "non_singletons":
        winners = [obj for obj in objects if len(obj) > 1]
    elif name == "at_least_half_max":
        winners = [obj for obj in objects if 2 * len(obj) >= largest]
    elif name == "top_two_distinct_sizes":
        sizes = sorted({len(obj) for obj in objects}, reverse=True)[:2]
        winners = [obj for obj in objects if len(obj) in sizes]
    elif name == "unique_max_or_empty":
        winners = winners if len(winners) == 1 else []
    return _retain(matrix, winners)


def intended(grid, mode):
    """Independent full-domain Python semantics; Racket remains authority."""
    rows, cols = headers(grid)
    return _selection(_matrix(rows, cols), rows, cols, _mode(mode))


def _predict(grid, mode, name):
    rows, cols = headers(grid)
    matrix = _matrix(rows, cols, name if name in STAGE_RIVALS else None)
    selection = mode
    if name == "opposite_selection":
        selection = MODES[1 - MODES.index(mode)]
    elif name in SELECTION_RIVALS:
        selection = name
    result = _selection(matrix, rows, cols, selection)
    if name == "transpose_output":
        result = [list(column) for column in zip(*result)]
    elif name == "reverse_output_rows":
        result = result[::-1]
    elif name == "reverse_output_columns":
        result = [line[::-1] for line in result]
    elif name == "retain_header_frame":
        result = [[0, *cols], *[[color, *line] for color, line in zip(rows, result)]]
    elif name == "crop_to_foreground":
        cells = [(r, c) for r, line in enumerate(result) for c, value in enumerate(line) if value]
        if not cells:
            return [[0]]
        r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
        c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
        result = [line[c0:c1 + 1] for line in result[r0:r1 + 1]]
    return result


def bank(mode):
    _mode(mode)
    names = (*STAGE_RIVALS, "opposite_selection", *OUTPUT_RIVALS)
    if mode == "largest_blocks":
        names += SELECTION_RIVALS
    return {name: partial(_predict, mode=mode, name=name) for name in names}


def _racket_stage(name):
    conditions = {
        None: "(= left top)",
        "ordinal_header_rank": "(= (rank rh left) (rank ch top))",
        "first_seen_header_rank": "(= (index-of (remove-duplicates rh) left) (index-of (remove-duplicates ch) top))",
        "frequency_header_rank": "(= (frank rh left) (frank ch top))",
        "row_rank_fallback": "(or (= left top) (and (not (member left ch)) (= (rank rh left) (rank ch top))))",
        "col_rank_fallback": "(or (= left top) (and (not (member top rh)) (= (rank rh left) (rank ch top))))",
        "row_headers_must_match": "(or (= left top) (and (not (member left ch)) (= c (modulo r n))))",
        "col_headers_must_match": "(or (= left top) (and (not (member top rh)) (= r (modulo c m))))",
        "boolean_match": "(= left top)",
        "all_crossings": "#t",
        "shared_row_fills_row": "(member left ch)",
        "shared_col_fills_col": "(member top rh)",
        "first_matching_column": "(and (= left top) (= c (index-of ch left)))",
        "last_matching_column": "(and (= left top) (= c (- n 1 (index-of (reverse ch) left))))",
        "first_matching_row": "(and (= left top) (= r (index-of rh top)))",
        "last_matching_row": "(and (= left top) (= r (- m 1 (index-of (reverse rh) top))))",
        "occurrence_pairing": "(and (= left top) (= (freq (take rh (+ r 1)) left) (freq (take ch (+ c 1)) top)))",
        "zip_same_color_runs": "(and (= left top) (= (run-rank rh r) (run-rank ch c)))",
        "numeric_min_match_color": "(and (= left top) (= left (apply min (cons 10 shared))))",
        "numeric_max_match_color": "(and (= left top) (= left (apply max (cons 0 shared))))",
        "unequal_headers": "(!= left top)",
    }
    color = "1" if name == "boolean_match" else "top" if name == "shared_col_fills_col" else "left"
    if name == "col_headers_must_match":
        color = "(if (= left top) left top)"
    return f"(grid-from-fn m n (lambda (r c) (let ((left (list-ref rh r)) (top (list-ref ch c))) (if {conditions[name]} {color} 0))))"


def _racket_selection(name):
    if name == "all_matches":
        return "a"
    if name == "include_header_frame":
        return """(let* ((framed (cons (cons 0 ch) (map cons rh a)))
                         (oo (objects framed 0))
                         (mx (apply max (cons 0 (map obj-size oo))))
                         (cells (append* (map obj-cells (filter (lambda (o) (= (obj-size o) mx)) oo)))))
                    (grid-from-fn m n (lambda (r c) (if (member (list (+ r 1) (+ c 1)) cells) (at a r c) 0))))"""
    object_source = "(objects-8 (grid-from-fn m n (lambda (r c) (if (= (at a r c) 0) 0 1))) 0)" if name == "binary_eight_connected" else "(objects a 0)"
    keepers = {
        "largest_blocks": "wins",
        "binary_eight_connected": "wins",
        "first_largest_component": "(if (null? wins) '() (list (first wins)))",
        "last_largest_component": "(if (null? wins) '() (list (last wins)))",
        "all_cells_of_winning_colors": "(filter (lambda (o) (member (obj-color o) (map obj-color wins))) oo)",
        "per_color_largest": "(filter (lambda (o) (= (obj-size o) (apply max (map obj-size (same-color o))))) oo)",
        "one_component_per_winning_color": "(filter (lambda (o) (equal? o (first (filter (lambda (p) (= (obj-color p) (obj-color o))) wins)))) wins)",
        "minimum_color_winners": "(filter (lambda (o) (= (obj-color o) (apply min (cons 10 (map obj-color wins))))) wins)",
        "maximum_color_winners": "(filter (lambda (o) (= (obj-color o) (apply max (cons 0 (map obj-color wins))))) wins)",
        "non_singletons": "(filter (lambda (o) (> (obj-size o) 1)) oo)",
        "at_least_half_max": "(filter (lambda (o) (>= (* 2 (obj-size o)) mx)) oo)",
        "top_two_distinct_sizes": "(filter (lambda (o) (member (obj-size o) (take (sort (remove-duplicates (map obj-size oo)) >) (min 2 (length (remove-duplicates (map obj-size oo))))))) oo)",
        "unique_max_or_empty": "(if (= (length wins) 1) wins '())",
    }
    scores = {
        "largest_color_total": "(apply + (map obj-size (same-color o)))",
        "largest_color_bbox": "(let* ((cells (append* (map obj-cells (same-color o)))) (rs (map first cells)) (cs (map second cells))) (* (+ 1 (- (apply max rs) (apply min rs))) (+ 1 (- (apply max cs) (apply min cs)))))",
        "most_frequent_row_color": "(freq rh (obj-color o))",
        "most_frequent_col_color": "(freq ch (obj-color o))",
        "largest_height": "(obj-h o)",
        "largest_width": "(obj-w o)",
        "largest_perimeter": "(* 2 (+ (obj-h o) (obj-w o)))",
        "largest_min_dimension": "(min (obj-h o) (obj-w o))",
        "largest_max_dimension": "(max (obj-h o) (obj-w o))",
    }
    score = scores.get(name, "(obj-size o)")
    selected = keepers.get(name, "(filter (lambda (o) (= (score o) (apply max (cons 0 (map score oo))))) oo)")
    return f"""(let* ((oo {object_source})
                       (same-color (lambda (o) (filter (lambda (p) (= (obj-color p) (obj-color o))) oo)))
                       (score (lambda (o) {score}))
                       (mx (apply max (cons 0 (map obj-size oo))))
                       (wins (filter (lambda (o) (= (obj-size o) mx)) oo))
                       (keep {selected})
                       (cells (append* (map obj-cells keep))))
                  (grid-from-fn m n (lambda (r c) (if (member (list r c) cells) (at a r c) 0))))"""


def racket(mode, name=None):
    """Return complete executable programs, including each named rival."""
    _mode(mode)
    if name is not None and name not in bank(mode):
        raise ValueError(f"unknown rival for {mode}: {name!r}")
    if mode == "all_matches" and name is None:
        return Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")
    selection = mode
    if name == "opposite_selection":
        selection = MODES[1 - MODES.index(mode)]
    elif name in SELECTION_RIVALS:
        selection = name
    output = "answer"
    if name == "transpose_output":
        output = "(apply map list answer)"
    elif name == "reverse_output_rows":
        output = "(reverse answer)"
    elif name == "reverse_output_columns":
        output = "(map reverse answer)"
    elif name == "retain_header_frame":
        output = "(cons (cons 0 ch) (map cons rh answer))"
    elif name == "crop_to_foreground":
        output = """(let ((cells (append* (map obj-cells (objects answer 0)))))
                      (if (null? cells) '((0))
                          (let* ((rs (map first cells)) (cs (map second cells))
                                 (r0 (apply min rs)) (c0 (apply min cs))
                                 (hh (+ 1 (- (apply max rs) r0)))
                                 (ww (+ 1 (- (apply max cs) c0))))
                            (grid-from-fn hh ww (lambda (r c) (at answer (+ r r0) (+ c c0)))))))"""
    stage = _racket_stage(name if name in STAGE_RIVALS else None)
    selected = _racket_selection(selection)
    return f"""(rule!
      (let* ((rh (map first (rest g))) (ch (rest (first g)))
             (m (length rh)) (n (length ch))
             (freq (lambda (xs x) (length (filter (lambda (v) (= v x)) xs))))
             (rank (lambda (xs x) (length (filter (lambda (v) (< v x)) (remove-duplicates xs)))))
             (frank (lambda (xs x) (length (filter (lambda (v) (< v (freq xs x))) (remove-duplicates (map (lambda (v) (freq xs v)) xs))))))
             (run-rank (lambda (xs i) (- (length (filter (lambda (j) (and (= (list-ref xs j) (list-ref xs i)) (or (= j 0) (!= (list-ref xs (- j 1)) (list-ref xs j))))) (range 0 (+ i 1)))) 1)))
             (shared (filter (lambda (v) (member v ch)) (remove-duplicates rh)))
             (a {stage})
             (answer {selected}))
        {output}))
"""


def fixtures():
    """Hand-authored structural controls, independent of the episode sampler."""
    patterns = {
        "minimum_match": ([2], [2]),
        "minimum_no_match": ([2], [9]),
        "all_same": ([9] * 3, [9] * 5),
        "no_shared_colors": ([1, 2, 1, 2], [3, 4, 5, 3, 4]),
        "fragmented_total_loses": ([1, 2, 1, 2, 1, 3, 3], [1, 4, 1, 4, 1, 3, 3]),
        "unique_max_secondary_winner": ([2, 2, 8, 2, 5, 7, 7, 5, 7, 7, 5, 7, 7],
                                        [2, 2, 2, 9, 2, 4, 7, 7, 9, 7, 7]),
        "cross_color_aspect_tie": ([2, 2, 8, 2, 5, 7, 7, 7, 5, 7],
                                   [2, 2, 2, 9, 2, 4, 7, 7, 9, 7]),
        "same_color_four_ties": ([4, 4, 1, 4, 4, 8, 7], [4, 4, 4, 9, 4, 4, 4, 2, 7]),
        "private_rank_dominance": ([2, 2, 2, 2, 4, 4, 7, 7], [3, 3, 3, 3, 4, 4, 7, 7]),
        "different_private_ranks": ([8, 8, 8, 2, 2, 5, 5, 5], [1, 1, 1, 2, 2, 5, 5]),
        "first_seen_and_numeric_rank": ([8, 2, 2, 5, 8, 2], [5, 8, 8, 1, 2, 2, 2]),
        "asymmetric_repetition": ([3, 3, 6, 3, 8], [6, 3, 3, 8, 3, 6, 9]),
        "height_is_not_area": ([2, 2, 2, 2, 8, 7, 7], [2, 9, 7, 7, 7]),
        "width_is_not_area": ([2, 9, 7, 7, 7], [2, 2, 2, 2, 8, 7, 7]),
        "perimeter_is_not_area": ([2, 8, 7, 7, 7], [2, 2, 2, 2, 2, 2, 9, 7, 7, 7]),
        "thresholds": ([2, 2, 2, 9, 7, 7, 8, 4], [2, 2, 3, 7, 7, 5, 4]),
        "diagonal_different_colors": ([1, 2, 2, 3, 3], [1, 2, 2, 3, 3]),
        "all_unit_components": ([1, 2, 1, 2, 3, 4], [2, 1, 2, 1, 3, 4]),
        "cross_run_product": ([1, 1, 2, 1], [1, 2, 1, 1, 1]),
        "header_frame_changes_winner": ([1, 2, 2], [1, 1, 1, 2, 2]),
        "whole_color_bbox": ([1, 2, 2, 1], [1, 2, 2, 1]),
        "one_output_row": ([4], [4, 4, 9, 4, 4, 4]),
        "one_output_column": ([6, 6, 1, 6, 6, 6], [6]),
        "maximum_30": ([2] * 3 + [7] * 2 + [4] * 4 + [1] * 2 + [8] * 3 + [7] +
                        [2] * 2 + [5] * 3 + [4] * 2 + [1] * 2 + [6] * 4 + [8],
                        [7] * 4 + [2] * 3 + [4] * 3 + [9] * 2 + [5] * 2 + [1] * 4 +
                        [7] * 2 + [2] + [4] * 4 + [3] * 4),
    }
    return {name: from_headers(rows, cols) for name, (rows, cols) in patterns.items()}


def feature_summary(grid):
    rows, cols = headers(grid)
    matrix = _matrix(rows, cols)
    objects = components(matrix)
    maximum = max(map(len, objects), default=0)
    winners = [obj for obj in objects if len(obj) == maximum]
    palette = sorted(set(rows) | set(cols))
    run_lengths = lambda axis: [len(list(group)) for _, group in groupby(axis)]
    color = lambda obj: matrix[obj[0][0]][obj[0][1]]
    return {
        "input_shape": [len(grid), len(grid[0])],
        "output_shape": [len(rows), len(cols)],
        "nonzero_header_cells": len(rows) + len(cols),
        "input_interior_nonzero": 0,
        "palette": palette,
        "shared_colors": sorted(set(rows) & set(cols)),
        "row_private_colors": sorted(set(rows) - set(cols)),
        "col_private_colors": sorted(set(cols) - set(rows)),
        "row_private_numeric_ranks": [palette.index(c) for c in sorted(set(rows) - set(cols))],
        "col_private_numeric_ranks": [palette.index(c) for c in sorted(set(cols) - set(rows))],
        "row_run_lengths": run_lengths(rows),
        "col_run_lengths": run_lengths(cols),
        "equality_nonzero_cells": sum(map(len, objects)),
        "equality_component_count": len(objects),
        "component_sizes": sorted(map(len, objects), reverse=True),
        "largest_component_size": maximum,
        "largest_component_count": len(winners),
        "winning_colors": sorted({color(obj) for obj in winners}),
        "retained_nonzero_cells": sum(map(len, winners)),
    }
