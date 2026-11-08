"""Independent semantic oracle and finite rival bank for 033db13a9d37.

Authored from canonical.rkt and the stated relay specification. This module
never imports the prototype, adapter, sampler, or production generator. The
domain deliberately includes arbitrary marker counts and bottom-row origins.
Racket variants are complete independently authored rules for protected replay.
"""
from __future__ import annotations

from functools import partial

MODES = ("first", "parity_relay")
COLORS = (0, 1, 2, 3, 5, 6, 7, 8, 9)
COMMON = (
    "last_origin", "column_major_origin", "rightmost_first_row_origin",
    "minimum_color_origin", "maximum_color_origin", "opposite_canopy_parity",
    "fixed_even_canopy", "single_column_canopy", "all_columns_canopy",
    "exclude_seed_row", "canopy_in_seed_color", "preserve_other_input",
    "no_echo", "echo_at_seed", "echo_two_rows_down",
)
RELAY = (
    "ignore_lane_mask", "ignore_lane_parity", "opposite_lane_parity",
    "same_column_only", "next_row_only", "last_eligible",
    "column_major_eligible", "repeat_relay", "origin_canopy_row",
    "origin_echo_row", "origin_echo_column", "origin_echo_color",
    "no_hit_blank", "no_hit_last", "no_hit_input",
    "rightward_only", "echo_visible_only", "echo_wrap", "echo_clamp",
    "target_min_color", "target_max_color",
    "nearest_eligible",
)


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a rectangular list with dimensions 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or value not in COLORS for value in row)
           for row in grid):
        raise ValueError("grid must contain exact integer colors 0..9 except 4")
    if not any(value for row in grid for value in row):
        raise ValueError("grid requires at least one nonzero marker")
    return grid


def _mode(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError("seed_mode must be first or parity_relay")


def _cells(grid):
    return [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]


def stage_a(grid):
    """Read the first original marker; project a strict-below parity lane."""
    validate_grid(grid)
    origin = _cells(grid)[0]
    row, col, _ = origin
    return origin, [[int(r > row and c % 2 == col % 2)
                     for c in range(len(grid[0]))] for r in range(len(grid))]


def stage_b(grid, origin, lane_mask):
    """Select from original nonzero cells using the supplied A-stage mask."""
    return next((cell for cell in _cells(grid) if lane_mask[cell[0]][cell[1]]), origin)


def _render(grid, target, origin, name=None):
    h, w = len(grid), len(grid[0])
    r, c, color = target
    canopy_row = origin[0] if name == "origin_canopy_row" else r
    if name == "exclude_seed_row":
        canopy_row -= 1
    parity = (c + int(name == "opposite_canopy_parity")) % 2
    if name == "fixed_even_canopy":
        parity = 0
    out = [row[:] for row in grid] if name == "preserve_other_input" else [[0] * w for _ in range(h)]
    for rr in range(canopy_row + 1):
        for cc in range(w):
            lane = (cc == c if name == "single_column_canopy" else
                    True if name == "all_columns_canopy" else cc % 2 == parity)
            if lane:
                out[rr][cc] = color if name == "canopy_in_seed_color" else 4
    er = (r if name == "echo_at_seed" else r + 2 if name == "echo_two_rows_down"
          else origin[0] + 1 if name == "origin_echo_row" else r + 1)
    if name == "echo_wrap":
        er %= h
    elif name == "echo_clamp":
        er = min(er, h - 1)
    ec = origin[1] if name == "origin_echo_column" else c
    ev = origin[2] if name == "origin_echo_color" else color
    if name != "no_echo" and er < h:
        out[er][ec] = ev
    return out


def intended(grid, mode):
    _mode(mode)
    origin, mask = stage_a(grid)
    target = stage_b(grid, origin, mask) if mode == "parity_relay" else origin
    return _render(grid, target, origin)


def _rival(grid, mode, name):
    _mode(mode)
    validate_grid(grid)
    cells = _cells(grid)
    origin = cells[0]
    if name == "last_origin":
        origin = cells[-1]
    elif name == "column_major_origin":
        origin = min(cells, key=lambda p: (p[1], p[0]))
    elif name == "rightmost_first_row_origin":
        origin = [cell for cell in cells if cell[0] == cells[0][0]][-1]
    elif name == "minimum_color_origin":
        origin = min(cells, key=lambda p: (p[2], p[0], p[1]))
    elif name == "maximum_color_origin":
        origin = min(cells, key=lambda p: (-p[2], p[0], p[1]))
    target = origin
    if mode == "parity_relay":
        row, col, _ = origin
        def permitted(cell):
            r, c, _ = cell
            if name == "ignore_lane_mask":
                return True
            if name == "ignore_lane_parity":
                return r > row
            if name == "same_column_only":
                return r > row and c == col
            if name == "next_row_only":
                return r == row + 1 and c % 2 == col % 2
            if name == "rightward_only":
                return r > row and c % 2 == col % 2 and c >= col
            if name == "echo_visible_only":
                return row < r < len(grid) - 1 and c % 2 == col % 2
            return r > row and c % 2 == (col + int(name == "opposite_lane_parity")) % 2
        eligible = [cell for cell in cells if permitted(cell)]
        if eligible:
            if name == "last_eligible":
                target = eligible[-1]
            elif name == "column_major_eligible":
                target = min(eligible, key=lambda p: (p[1], p[0]))
            elif name == "repeat_relay":
                # Repeated strict-below relays end at the first marker on the
                # deepest eligible row, not the last cell on that row.
                target = next(cell for cell in eligible if cell[0] == eligible[-1][0])
            elif name == "target_min_color":
                target = min(eligible, key=lambda p: (p[2], p[0], p[1]))
            elif name == "target_max_color":
                target = min(eligible, key=lambda p: (-p[2], p[0], p[1]))
            elif name == "nearest_eligible":
                target = min(eligible, key=lambda p: ((p[0] - row) ** 2 + (p[1] - col) ** 2,
                                                     p[0], p[1]))
            else:
                target = eligible[0]
        elif name == "no_hit_blank":
            return [[0] * len(grid[0]) for _ in grid]
        elif name == "no_hit_input":
            return [row[:] for row in grid]
        elif name == "no_hit_last":
            target = cells[-1]
    return _render(grid, target, origin, name)


def bank(mode):
    """One callable per semantically distinct named mistake, with no aliases."""
    _mode(mode)
    return {name: partial(_rival, mode=mode, name=name)
            for name in COMMON + (RELAY if mode == "parity_relay" else ())}


def racket(mode, name=None):
    """Complete independently authored Racket rule, including both stages."""
    _mode(mode)
    if name is not None and name not in bank(mode):
        raise ValueError("unknown rival")
    origins = {
        "last_origin": "(last cells)",
        "column_major_origin": "(first column-cells)",
        "rightmost_first_row_origin": "(last (filter (lambda (p) (= (first p) (first (first cells)))) cells))",
        "minimum_color_origin": "(find (lambda (p) (= (third p) (apply min (map third cells)))) cells)",
        "maximum_color_origin": "(find (lambda (p) (= (third p) (apply max (map third cells)))) cells)",
    }
    origin = origins.get(name, "(first cells)")
    row_check = "(= r (+ (first origin) 1))" if name == "next_row_only" else "(> r (first origin))"
    col_check = ("(= c (second origin))" if name == "same_column_only" else
                 "#t" if name == "ignore_lane_parity" else
                 f"(= (remainder c 2) (remainder (+ (second origin) {int(name == 'opposite_lane_parity')}) 2))")
    mask_check = "#t" if name == "ignore_lane_mask" else f"(and {row_check} {col_check})"
    if name == "rightward_only":
        mask_check = f"(and {mask_check} (>= c (second origin)))"
    elif name == "echo_visible_only":
        mask_check = f"(and {mask_check} (< r (- h 1)))"
    candidate = {
        "last_eligible": "(last eligible)",
        "column_major_eligible": "(find (lambda (p) (= (at lane-mask (first p) (second p)) 1)) column-cells)",
        "repeat_relay": "(find (lambda (p) (= (first p) (first (last eligible)))) eligible)",
        "target_min_color": "(find (lambda (p) (= (third p) (apply min (map third eligible)))) eligible)",
        "target_max_color": "(find (lambda (p) (= (third p) (apply max (map third eligible)))) eligible)",
        "nearest_eligible": """(let ((cost (lambda (p)
                                  (let ((dr (- (first p) (first origin)))
                                        (dc (- (second p) (second origin))))
                                    (+ (* dr dr) (* dc dc))))))
                              (let ((best (apply min (map cost eligible))))
                                (find (lambda (p) (= (cost p) best)) eligible)))""",
    }.get(name, "(first eligible)")
    fallback = "(last cells)" if name == "no_hit_last" else "origin"
    target = f"(if (null? eligible) {fallback} {candidate})" if mode == "parity_relay" else "origin"
    canopy_row = "(first origin)" if name == "origin_canopy_row" else "tr"
    if name == "exclude_seed_row":
        canopy_row = f"(- {canopy_row} 1)"
    canopy_col = ("(= c tc)" if name == "single_column_canopy" else "#t" if name == "all_columns_canopy"
                  else "(= (remainder c 2) 0)" if name == "fixed_even_canopy"
                  else f"(= (remainder c 2) (remainder (+ tc {int(name == 'opposite_canopy_parity')}) 2))")
    er = ("tr" if name == "echo_at_seed" else "(+ tr 2)" if name == "echo_two_rows_down"
          else "(+ (first origin) 1)" if name == "origin_echo_row" else "(+ tr 1)")
    if name == "echo_wrap":
        er = f"(remainder {er} h)"
    elif name == "echo_clamp":
        er = f"(min {er} (- h 1))"
    ec = "(second origin)" if name == "origin_echo_column" else "tc"
    ev = "(third origin)" if name == "origin_echo_color" else "tv"
    echo = "#f" if name == "no_echo" else f"(and (= r {er}) (= c {ec}))"
    canopy_color = "tv" if name == "canopy_in_seed_color" else "4"
    base = "v" if name == "preserve_other_input" else "0"
    fallback_clause = ("((null? eligible) 0)" if name == "no_hit_blank" else
                       "((null? eligible) v)" if name == "no_hit_input" else "")
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (cells (filter (lambda (p) p)
                  (for*/list ((r (range 0 h)) (c (range 0 w)))
                    (and (!= (at g r c) 0) (list r c (at g r c))))))
         (column-cells (filter (lambda (p) p)
                  (for*/list ((c (range 0 w)) (r (range 0 h)))
                    (and (!= (at g r c) 0) (list r c (at g r c))))))
         (origin {origin})
         (lane-mask (for/list ((r (range 0 h)))
                      (for/list ((c (range 0 w))) (if {mask_check} 1 0))))
         (eligible (filter (lambda (p) (= (at lane-mask (first p) (second p)) 1)) cells))
         (target {target})
         (tr (first target)) (tc (second target)) (tv (third target)))
    (cellmap g (r c v)
      (cond {fallback_clause}
            ({echo} {ev})
            ((and (<= r {canopy_row}) {canopy_col}) {canopy_color})
            (else {base}))))))"""


def _grid(height, width, markers):
    grid = [[0] * width for _ in range(height)]
    for row, col, color in markers:
        grid[row][col] = color
    return grid


def fixtures():
    """Finite literal edges and discriminators; never sampler-derived."""
    return {
        "unit_bottom": [[9]],
        "single_row": [[0, 0, 5, 0, 1, 0, 8]],
        "single_column": _grid(8, 1, [(1, 0, 3), (3, 0, 7), (7, 0, 1)]),
        "odd_active": _grid(8, 9, [(1, 5, 7), (1, 8, 2), (2, 0, 1), (3, 3, 6),
                                           (5, 1, 9), (6, 1, 2), (6, 3, 8), (7, 8, 5)]),
        "even_active": _grid(10, 12, [(2, 6, 3), (2, 8, 8), (3, 1, 5), (4, 4, 7),
                                              (5, 6, 6), (6, 0, 2), (8, 2, 1), (8, 10, 9), (9, 11, 8)]),
        "even_fallback": _grid(6, 9, [(1, 4, 6), (1, 6, 7), (2, 1, 1), (5, 7, 9)]),
        "odd_fallback": _grid(7, 8, [(2, 3, 2), (2, 7, 5), (3, 0, 8), (6, 6, 1)]),
        "bottom_target": _grid(5, 6, [(0, 3, 2), (1, 0, 7), (4, 1, 9), (4, 5, 3)]),
        "bottom_origin": _grid(4, 7, [(3, 2, 8), (3, 5, 1)]),
        "same_row_exclusion": _grid(5, 8, [(1, 2, 5), (1, 4, 2), (2, 1, 9), (3, 6, 7)]),
        "same_column_hit": _grid(7, 7, [(0, 4, 3), (1, 4, 8), (2, 2, 1), (5, 0, 6)]),
        "last_opposite": _grid(6, 8, [(0, 2, 9), (2, 6, 1), (3, 0, 8), (5, 7, 5)]),
        "wide_30": _grid(2, 30, [(0, 29, 6), (1, 1, 2), (1, 27, 9)]),
        "tall_30": _grid(30, 2, [(0, 1, 8), (18, 0, 1), (29, 1, 3)]),
        "dense_30": [[COLORS[1 + (r * 7 + c * 3) % 8] if (r + c) % 3 else 0
                      for c in range(30)] for r in range(30)],
        "sparse_30": _grid(30, 30, [(4, 20, 7), (4, 24, 1), (6, 1, 2), (13, 28, 6),
                                             (17, 20, 9), (25, 0, 5), (29, 22, 3)]),
    }


def feature_summary(grid):
    origin, mask = stage_a(grid)
    cells = _cells(grid)
    target = stage_b(grid, origin, mask)
    eligible = [cell for cell in cells if mask[cell[0]][cell[1]]]
    return {
        "shape": [len(grid), len(grid[0])], "markers": len(cells),
        "origin": list(origin), "relay_target": list(target),
        "origin_parity": origin[1] % 2, "eligible_count": len(eligible),
        "relay_active": bool(eligible), "relay_fallback": not eligible,
        "origin_bottom": origin[0] == len(grid) - 1,
        "target_bottom": target[0] == len(grid) - 1,
        "different_color": origin[2] != target[2],
        "different_column": origin[1] != target[1],
        "same_row_decoys": sum(cell[0] == origin[0] for cell in cells[1:]),
        "skipped_wrong_parity": any(origin[0] < cell[0] < target[0]
                                     and cell[1] % 2 != origin[1] % 2 for cell in cells),
        "column_major_origin_changes": min(cells, key=lambda p: (p[1], p[0])) != origin,
        "mode_changes_output": intended(grid, "first") != intended(grid, "parity_relay"),
    }
