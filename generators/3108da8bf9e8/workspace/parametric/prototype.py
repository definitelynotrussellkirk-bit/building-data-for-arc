"""Proposed whole-block sorting by cell count or four-neighbor components.

The canonical setting preserves the exact selected eleven-by-eleven rule.
The alternate first measures each block's topology, then uses that intermediate
to choose a whole-block permutation. Its size extension retains nine equal
square blocks and full zero separator bands, including substantive 30x30 input.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random


TASK_ID = "3108da8bf9e8"
SETTINGS = ("cells", "components_then_cells")
DEFAULT = {"rank_basis": "cells"}
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
TARGETS = (6, 7, 8, 3, 4, 5, 0, 1, 2)
MAX_ATTEMPTS = 4096
CANONICAL_PROGRAM = Path(__file__).with_name("canonical.rkt").read_text(encoding="utf-8")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"rank_basis"}:
        raise ValueError("settings must contain exactly rank_basis")
    basis = settings["rank_basis"]
    if type(basis) is not str or basis not in SETTINGS:
        raise ValueError(f"rank_basis must be one of {SETTINGS}")
    return basis


def _runs(indices):
    groups = []
    for index in indices:
        if groups and index == groups[-1][-1] + 1:
            groups[-1].append(index)
        else:
            groups.append([index])
    return groups


def geometry(grid):
    """Return occupied row bands and column bands; validate_grid owns checks."""
    row_bands = _runs([r for r, row in enumerate(grid) if any(row)])
    col_bands = _runs([c for c in range(len(grid[0])) if any(row[c] for row in grid)])
    return row_bands, col_bands


def validate_grid(grid, canonical=False):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty list matrix within 30x30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or v not in (0, 1, 2) for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with literal integer colors 0,1,2")
    rows, cols = geometry(grid)
    if len(rows) != 3 or len(cols) != 3:
        raise ValueError("expected three occupied bands on each axis")
    side = len(rows[0])
    if not 3 <= side <= 9 or any(len(b) != side for b in rows + cols):
        raise ValueError("nine blocks must be equal squares with side 3..9")
    if rows[0][0] != 0 or cols[0][0] != 0 or rows[-1][-1] != len(grid) - 1 or cols[-1][-1] != width - 1:
        raise ValueError("outer padding is outside this grammar")
    active_rows, active_cols = set(sum(rows, [])), set(sum(cols, []))
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (r in active_rows and c in active_cols) != (value in (1, 2)):
                raise ValueError("blocks contain only 1/2 and all separators are zero")
    counts = [sum(grid[r][c] == 1 for r in rb for c in cb) for rb in rows for cb in cols]
    if len(set(counts)) != 9:
        raise ValueError("nine color-1 cell counts must be distinct")
    if canonical and (len(grid) != 11 or width != 11 or rows != [list(range(i, i + 3)) for i in (0, 4, 8)] or cols != rows):
        raise ValueError("canonical cells setting requires exact 11x11 geometry")
    return True


def extract_blocks(grid):
    validate_grid(grid)
    rows, cols = geometry(grid)
    return [[[grid[r][c] for c in cb] for r in rb] for rb in rows for cb in cols]


def component_count(block, color=1, connectivity=4):
    if type(color) is not int or color not in (1, 2) or type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("component color is 1 or 2; connectivity is 4 or 8")
    pending = {(r, c) for r, row in enumerate(block) for c, value in enumerate(row) if value == color}
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        directions += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    result = 0
    while pending:
        result += 1
        frontier = [pending.pop()]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in directions:
                neighbor = r + dr, c + dc
                if neighbor in pending:
                    pending.remove(neighbor)
                    frontier.append(neighbor)
    return result


def block_keys(grid, rank_basis):
    validate_settings({"rank_basis": rank_basis})
    blocks = extract_blocks(grid)
    counts = [sum(v == 1 for row in b for v in row) for b in blocks]
    if rank_basis == "cells":
        return counts
    return [(component_count(b), count) for b, count in zip(blocks, counts)]


def rank_order(grid, rank_basis):
    keys = block_keys(grid, rank_basis)
    return sorted(range(9), key=lambda i: keys[i])


def place_order(grid, order):
    """Place source indices in bottom-first target order without repainting."""
    if type(order) not in (list, tuple) or len(order) != 9 or any(type(i) is not int for i in order) or sorted(order) != list(range(9)):
        raise ValueError("order must be a permutation of nine literal indices")
    blocks = extract_blocks(grid)
    rows, cols = geometry(grid)
    output = [[0] * len(grid[0]) for _ in grid]
    for target, source in zip(TARGETS, order):
        rb, cb = rows[target // 3], cols[target % 3]
        for dr, r in enumerate(rb):
            for dc, c in enumerate(cb):
                output[r][c] = blocks[source][dr][dc]
    return output


def solve(grid, *, rank_basis="cells"):
    validate_settings({"rank_basis": rank_basis})
    validate_grid(grid, canonical=rank_basis == "cells")
    return place_order(grid, rank_order(grid, rank_basis))


def rule_program(rank_basis="components_then_cells", *, connectivity=4, color=1, tie_break="cells", descending=False, target="bottom"):
    """Render a complete general-geometry rule, also useful for counterfactuals.

    program(settings), rather than this helper, returns the exact canonical
    authority for cells. This bounded renderer changes only named sort choices.
    """
    validate_settings({"rank_basis": rank_basis})
    if type(connectivity) is not int or connectivity not in (4, 8) or type(color) is not int or color not in (1, 2):
        raise ValueError("invalid component color/connectivity")
    if tie_break not in ("cells", "reverse_cells", "none") or type(descending) is not bool or target not in ("bottom", "top"):
        raise ValueError("invalid tie, direction or target option")
    component_function = "objects" if connectivity == 4 else "objects-8"
    cells = f"(for/sum ((row b)) (for/sum ((v row)) (if (= v {color}) 1 0)))"
    tie = cells if tie_break == "cells" else (f"(- (* side side) {cells})" if tie_break == "reverse_cells" else "0")
    key = cells if rank_basis == "cells" else f"(+ (* (+ (* side side) 1) (length ({component_function} b {3-color}))) {tie})"
    if descending:
        key = f"(- {key})"
    rank_index = "(+ (* (- 2 br) 3) bc)" if target == "bottom" else "(+ (* br 3) bc)"
    return f"""(rule! (lambda (g)
  (let* ((rstarts (filter (lambda (r) (and (!= (at g r 0) 0)
                    (or (= r 0) (= (at g (- r 1) 0) 0)))) (range 0 (rows g))))
         (cstarts (filter (lambda (c) (and (!= (at g 0 c) 0)
                    (or (= c 0) (= (at g 0 (- c 1)) 0)))) (range 0 (cols g))))
         (side (find-first (lambda (r) (= (at g r 0) 0)) (range 0 (rows g))))
         (records (for/list ((i (range 0 9)))
           (let* ((r (nth rstarts (quotient i 3)))
                  (c (nth cstarts (remainder i 3)))
                  (b (subgrid g r c (+ r side -1) (+ c side -1))))
             (list i {key}))))
         (ordered (sort-by records (lambda (record) (second record)))))
    (grid-from-fn (rows g) (cols g) (lambda (r c)
      (if (= (at g r c) 0) 0
        (let* ((br (find-first (lambda (i) (and (<= (nth rstarts i) r)
                              (< r (+ (nth rstarts i) side)))) (range 0 3)))
               (bc (find-first (lambda (i) (and (<= (nth cstarts i) c)
                              (< c (+ (nth cstarts i) side)))) (range 0 3)))
               (source (first (nth ordered {rank_index})))
               (sr (nth rstarts (quotient source 3)))
               (sc (nth cstarts (remainder source 3))))
          (at g (+ sr (- r (nth rstarts br)))
                (+ sc (- c (nth cstarts bc)))))))))))"""


def program(settings):
    basis = validate_settings(settings)
    return CANONICAL_PROGRAM if basis == "cells" else rule_program(basis)


def _rng(seed, split, index, attempt):
    text = f"{TASK_ID}/topology-v1/{seed}/{split}/{index}/{attempt}"
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest(), "big"))


def _draw_grid(rng, side, gaps=(1, 1)):
    starts = (0, side + gaps[0], 2 * side + sum(gaps))
    extent = 3 * side + sum(gaps)
    grid = [[0] * extent for _ in range(extent)]
    for i, count in enumerate(rng.sample(range(side * side + 1), 9)):
        blue = set(rng.sample(range(side * side), count))
        for dr in range(side):
            for dc in range(side):
                grid[starts[i // 3] + dr][starts[i % 3] + dc] = 1 if dr * side + dc in blue else 2
    return grid


def _has_long_move_cycle(order):
    movement = dict(zip(TARGETS, order))
    remaining = set(range(9))
    while remaining:
        start = min(remaining)
        node, length = start, 0
        while node in remaining:
            remaining.remove(node)
            length += 1
            node = movement[node]
        if length >= 4:
            return True
    return False


def _teaching_orders(grid):
    """Reject finite semantic collapses using Python claims only, not queries."""
    blocks = extract_blocks(grid)
    ones = [sum(v == 1 for row in b for v in row) for b in blocks]
    size = len(blocks[0]) ** 2
    c4 = [component_count(b) for b in blocks]
    c8 = [component_count(b, connectivity=8) for b in blocks]
    red = [component_count(b, color=2) for b in blocks]
    keys = {
        "cells": ones,
        "components_then_cells": list(zip(c4, ones)),
        "eight": list(zip(c8, ones)),
        "only": c4,
        "tie_reverse": list(zip(c4, [-v for v in ones])),
        "red": list(zip(red, [size-v for v in ones])),
        "primary_reverse": list(zip([-v for v in c4], ones)),
    }
    orders = {name: sorted(range(9), key=lambda i: values[i]) for name, values in keys.items()}
    for basis in SETTINGS:
        chosen = orders[basis]
        if not _has_long_move_cycle(chosen):
            return None
        if any(chosen == other for name, other in orders.items() if name != basis):
            return None
        # Identity, row reversal and within-row/column sorting are explicit;
        # a >=4 movement cycle also excludes every independent-triple partition.
        row_sorted = sum([sorted(range(3*r, 3*r+3), key=lambda i: keys[basis][i]) for r in (2, 1, 0)], [])
        col_output = [None] * 9
        for col in range(3):
            for row, source in zip((2, 1, 0), sorted((col, col+3, col+6), key=lambda i: keys[basis][i])):
                col_output[3 * row + col] = source
        if chosen in (list(TARGETS), list(range(9)), row_sorted, [col_output[t] for t in TARGETS]):
            return None
    if all([v for row in b for v in row] == [1] * count + [2] * (size-count) for b, count in zip(blocks, ones)):
        return None
    return {basis: tuple(orders[basis]) for basis in SETTINGS}


def _sample(seed, split, index, side, gaps, seen, prior_orders):
    for attempt in range(MAX_ATTEMPTS):
        grid = _draw_grid(_rng(seed, split, index, attempt), side, gaps)
        fingerprint = json.dumps(grid, separators=(",", ":"))
        if fingerprint in seen:
            continue
        orders = _teaching_orders(grid)
        if orders is None or any(orders[basis] in prior_orders[basis] for basis in SETTINGS):
            continue
        seen.add(fingerprint)
        for basis in SETTINGS:
            prior_orders[basis].add(orders[basis])
        return grid, attempt + 1
    raise RuntimeError(f"bounded teaching sampler exhausted {MAX_ATTEMPTS} attempts at {split}[{index}]")


def input_bank(seed, rank_basis):
    """Build the complete bank before count slicing; return private draw costs."""
    validate_settings({"rank_basis": rank_basis})
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative literal Python integer")
    seen, prior = set(), {basis: set() for basis in SETTINGS}
    demos, queries, attempts = [], [], []
    for index in range(6):
        grid, cost = _sample(seed, "demo", index, 3, (1, 1), seen, prior)
        demos.append(grid)
        attempts.append({"split": "train", "index": index, "attempts": cost})
    for index in range(4):
        side = 3 if rank_basis == "cells" else (4, 6, 8, 9)[index]
        gaps = (1, 2) if side == 9 else (1, 1)
        grid, cost = _sample(seed, f"query-{rank_basis}", index, side, gaps, seen, prior)
        queries.append(grid)
        attempts.append({"split": "test", "index": index, "attempts": cost})
    return demos, queries, attempts


def generate(seed, settings, demos=3, queries=4):
    basis = validate_settings(settings)
    if type(demos) is not int or not 2 <= demos <= 6 or type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("supported counts: 2..6 demos and 1..4 queries")
    train_inputs, query_inputs, costs = input_bank(seed, basis)
    return {
        "train": [{"input": deepcopy(grid), "output": solve(grid, rank_basis=basis)} for grid in train_inputs[:demos]],
        "test": [{"input": deepcopy(grid), "output": solve(grid, rank_basis=basis)} for grid in query_inputs[:queries]],
        "program_solution": program(settings),
        "settings": deepcopy(settings),
        "sampler": {"max_attempts_per_pair": MAX_ATTEMPTS, "full_bank_attempts": costs},
    }
