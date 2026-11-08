"""Proposed threshold variant of 661dffbdf39a; not a production generator.

The episode fixes one strict gray-density threshold. Rows and columns above
that threshold are completed in gray, with their crossings in the unique
non-black/non-gray color. Every emitted label is computed in real Racket;
``solve_python`` is an additional check, never a labeling fallback.

The sampler deliberately covers three exact boundaries on each axis in
18/24-cell dimensions. It is a teaching domain, not full ARC-grid coverage.
"""
from __future__ import annotations

import hashlib
import random


THRESHOLDS = ("1/3", "1/2", "2/3")
DEFAULT_THRESHOLD = "1/2"
GENERATOR_ID = "661dffbdf39a"

# Exact canonical reference bytes, retained separately from proposed settings.
_CANONICAL_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((marker (fst (filter (lambda (v) (and (!= v 0) (!= v 5)))
                                       (grid-colors g))))
                  (rline? (lambda (r)
                            (> (count-if (lambda (c) (= (at g r c) 5)) (range 0 w))
                               (quotient w 2))))
                  (cline? (lambda (c)
                            (> (count-if (lambda (r) (= (at g r c) 5)) (range 0 h))
                               (quotient h 2))))
                  (rset (filter rline? (range 0 h)))
                  (cset (filter cline? (range 0 w))))
             (cellmap g
                      (r c v)
                      (cond
                        ((and (member? r rset) (member? c cset)) marker)
                        ((or (member? r rset) (member? c cset)) 5)
                        (else 0)))))))"""


def _threshold(value):
    if not isinstance(value, str) or value not in THRESHOLDS:
        raise ValueError(f"threshold must be one of {THRESHOLDS}")
    return tuple(map(int, value.split("/")))


def _integer(value, name, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        bound = f"{minimum}..{maximum}" if maximum is not None else f">={minimum}"
        raise ValueError(f"{name} must be an integer {bound}, excluding bool")


def _grid_shape(grid):
    if not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if not isinstance(grid[0], (list, tuple)) or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be integer ARC colors 0..9, excluding bool")
    return h, w


def rule_program(threshold=DEFAULT_THRESHOLD):
    """Return the exact materialized rule, preserving canonical default bytes."""
    _threshold(threshold)
    if threshold == DEFAULT_THRESHOLD:
        return _CANONICAL_PROGRAM
    # Racket's fraction literals are exact rationals, avoiding rounding.
    return (_CANONICAL_PROGRAM
            .replace("(quotient w 2)", f"(* w {threshold})")
            .replace("(quotient h 2)", f"(* h {threshold})"))


def _inclusive_program(threshold):
    # This rival uses >= the exact fraction, including on odd dimensions.
    _threshold(threshold)
    return (_CANONICAL_PROGRAM
            .replace("(> (count-if", "(>= (count-if")
            .replace("(quotient w 2)", f"(* w {threshold})")
            .replace("(quotient h 2)", f"(* h {threshold})"))


def solve_python(grid, threshold=DEFAULT_THRESHOLD):
    """Independent integer-arithmetic mirror on the unique-marker domain."""
    numerator, denominator = _threshold(threshold)
    h, w = _grid_shape(grid)
    markers = {cell for row in grid for cell in row} - {0, 5}
    if len(markers) != 1:
        raise ValueError("exactly one non-black/non-gray marker color is required")
    marker = next(iter(markers))
    rows = {r for r in range(h) if denominator * sum(cell == 5 for cell in grid[r]) > numerator * w}
    cols = {c for c in range(w) if denominator * sum(grid[r][c] == 5 for r in range(h)) > numerator * h}
    return [[marker if r in rows and c in cols else 5 if r in rows or c in cols else 0
             for c in range(w)] for r in range(h)]


def sample_input(seed, sample_index):
    """Draw a threshold-independent, deterministic scene without global RNG use.

    Three candidate rows/columns have exactly 1/3, 1/2 and 2/3 gray density.
    Candidate rows only add cells in ordinary columns and vice versa, so each
    candidate's count remains exact. Ordinary lines receive at most six gray
    cells, never exceeding 1/3. Every strong line has at least one noisy hole.
    """
    _integer(seed, "seed")
    _integer(sample_index, "sample_index")
    token = f"{GENERATOR_ID}/threshold-v1/{seed}/{sample_index}".encode()
    rng = random.Random(int.from_bytes(hashlib.sha256(token).digest(), "big"))
    h, w = rng.choice((18, 24)), rng.choice((18, 24))
    marker = rng.choice((1, 2, 3, 4, 6, 7, 8, 9))
    # Vary counts over successive demos independently of the hidden threshold.
    row_count = 2 + (seed + sample_index) % 2
    col_count = 2 + (seed // 2 + sample_index // 2) % 2
    selected_rows = rng.sample(range(h), row_count + 3)
    selected_cols = rng.sample(range(w), col_count + 3)
    strong_rows, partial_rows = selected_rows[:row_count], selected_rows[row_count:]
    strong_cols, partial_cols = selected_cols[:col_count], selected_cols[col_count:]
    ordinary_rows = [r for r in range(h) if r not in selected_rows]
    ordinary_cols = [c for c in range(w) if c not in selected_cols]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r in strong_rows:
        for c in range(w):
            grid[r][c] = 5
    for c in strong_cols:
        for r in range(h):
            grid[r][c] = 5
    for r, count in zip(partial_rows, (w // 3, w // 2, 2 * w // 3)):
        for c in rng.sample(ordinary_cols, count - col_count):
            grid[r][c] = 5
    for c, count in zip(partial_cols, (h // 3, h // 2, 2 * h // 3)):
        for r in rng.sample(ordinary_rows, count - row_count):
            grid[r][c] = 5
    for r in strong_rows:
        for c in rng.sample(ordinary_cols, rng.randint(1, w // 6)):
            grid[r][c] = marker
    for c in strong_cols:
        for r in rng.sample(ordinary_rows, rng.randint(1, h // 6)):
            grid[r][c] = marker
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 and rng.random() < 0.06:
                grid[r][c] = marker
    return grid


def _checked_inputs(program, grids):
    if not isinstance(program, str) or not program.strip():
        raise ValueError("program must be a nonempty Racket string")
    if not isinstance(grids, (list, tuple)):
        raise ValueError("grids must be a list or tuple of ARC grids")
    for grid in grids:
        _grid_shape(grid)
    return [[list(row) for row in grid] for grid in grids]


def _run_on_bridge(bridge, program, grids):
    # rule! is an authoring wrapper; the exact supplied rule returns its lambda.
    bridge.eval_text(f"(define __threshold_rule (let ((rule! (lambda (fn) fn))) {program}))")
    bridge.define_value("__threshold_inputs", grids)
    outputs = bridge.eval_text("(map __threshold_rule __threshold_inputs)")
    if not isinstance(outputs, list) or len(outputs) != len(grids):
        raise RuntimeError("Racket returned the wrong number of output grids")
    for output in outputs:
        _grid_shape(output)
    return outputs


def run_racket(program, grids):
    """Execute the supplied program through the included protected bridge.

    Run via WORK/run_with_racket.py so the bridge and local Racket are selected.
    Runtime failures are surfaced; Python output is never substituted.
    """
    inputs = _checked_inputs(program, grids)
    if not inputs:
        return []
    from arc_repl.racket_bridge import RacketBridge
    bridge = RacketBridge()
    try:
        return _run_on_bridge(bridge, program, inputs)
    finally:
        bridge.shutdown()


def make_episode(seed, threshold=DEFAULT_THRESHOLD, train_count=3, query_count=4):
    """Build a fully labeled private episode with a demonstration-only certificate.

    Supported counts are 1..12 demonstrations and 1..16 distinct queries. The
    certificate covers the other two allowed thresholds and the >= boundary
    rival, not all possible ARC transformations. One demo identifies this finite
    rule family; three demos additionally vary the number of strong lines.
    """
    _integer(seed, "seed")
    _threshold(threshold)
    _integer(train_count, "train_count", 1, 12)
    _integer(query_count, "query_count", 1, 16)
    program = rule_program(threshold)
    total = train_count + query_count
    inputs, seen, indices = [], set(), []
    for index in range(total * 10):
        value = sample_input(seed, index)
        signature = tuple(map(tuple, value))
        if signature not in seen:
            inputs.append(value)
            seen.add(signature)
            indices.append(index)
        if len(inputs) == total:
            break
    if len(inputs) != total:
        raise RuntimeError(f"could not draw {total} distinct inputs within {total * 10} attempts")
    rivals = {f"strict>{other}": rule_program(other) for other in THRESHOLDS if other != threshold}
    rivals[f"inclusive>={threshold}"] = _inclusive_program(threshold)
    from arc_repl.racket_bridge import RacketBridge
    bridge = RacketBridge()
    try:
        outputs = _run_on_bridge(bridge, program, inputs)
        for index, (value, output) in enumerate(zip(inputs, outputs)):
            if output != solve_python(value, threshold):
                raise RuntimeError(f"Racket/Python disagreement at pair {index}")
        witnesses = {}
        # Deliberately pass only demonstration inputs to the rival programs.
        for name, rival_program in rivals.items():
            predictions = _run_on_bridge(bridge, rival_program, inputs[:train_count])
            witnesses[name] = [i for i in range(train_count) if predictions[i] != outputs[i]]
            if not witnesses[name]:
                raise RuntimeError(f"demonstrations do not distinguish rival {name}")
    finally:
        bridge.shutdown()
    pairs = [{"input": value, "output": output} for value, output in zip(inputs, outputs)]
    teaching = {
        "scope": "two alternative strict thresholds and the chosen inclusive boundary rival",
        "demo_witnesses": witnesses,
        "surviving_hypotheses": [f"strict>{threshold}"],
        "query_answers_used_for_identifiability": False,
        "query_certificates": [
            {"query_index": i, "eliminated_by_demonstrations": list(witnesses)}
            for i in range(query_count)
        ],
    }
    return {
        "train": pairs[:train_count],
        "test": pairs[train_count:],
        "metadata": {
            "status": "proposed_prototype",
            "generator_id": GENERATOR_ID,
            "seed": seed,
            "threshold": threshold,
            "train_count": train_count,
            "query_count": query_count,
            "sample_indices": indices,
            "program": program,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "label_backend": "arc_repl.racket_bridge.RacketBridge",
            "teaching": teaching,
        },
    }
