"""Canonical majority fill and a selection that consumes the filled topology.

The Python evaluator is a transparent sampler/audit mirror. Exported labels are
verified through the protected Racket runtime; the canonical default is read
verbatim from the same-checkout authority ledger.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
import json
from pathlib import Path


TASK_ID = "25e78410d5bb"
ROOT = Path(__file__).resolve().parents[4]
RETENTIONS = ("all", "largest_filled_component")
RIVALS = (
    "side_only",
    "row_copy",
    "global_indicator_majority",
    "minority",
    "marker_components",
    "largest_room",
    "largest_color_total",
    "original_components",
    "bbox_size",
)
_VOTE_RIVALS = RIVALS[:5]
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _retention(value):
    if type(value) is not str or value not in RETENTIONS:
        raise ValueError("retention must be all or largest_filled_component")
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"retention"}:
        raise ValueError("settings must name exactly retention")
    return _retention(settings["retention"])


def _grid(grid):
    if (
        type(grid) is not list or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
        or any(type(row) is not list or len(row) != len(grid[0])
               or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
               for row in grid)
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return grid


@lru_cache(maxsize=1)
def canonical_program():
    """Return the exact selected ledger bytes, including original whitespace."""
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical authority")
    return programs.pop()


def _canonical_lambda():
    # Use the shared wrapper parser instead of maintaining a second parser.
    from puzzle_generators.rule_wrap import strip_rule_wrapper
    return strip_rule_wrapper(canonical_program())


def _components(grid, accepted):
    """Same-color components in the Racket prelude's row-major/BFS order."""
    h, w = len(grid), len(grid[0])
    seen, result = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if (r, c) in seen or not accepted(color):
                continue
            seen.add((r, c))
            queue, cells = deque([(r, c)]), []
            while queue:
                cr, cc = queue.popleft()
                cells.append((cr, cc))
                for dr, dc in _DIRS:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({
                "cells": cells,
                "color": color,
                "size": len(cells),
                "bbox": (
                    min(p[0] for p in cells), min(p[1] for p in cells),
                    max(p[0] for p in cells), max(p[1] for p in cells),
                ),
            })
    return result


def _votes(grid, cells, directions=_DIRS):
    h, w = len(grid), len(grid[0])
    votes = []
    for r, c in cells:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, 5):
                votes.append(grid[nr][nc])
    return votes


def _winner(votes, *, minority=False):
    counts = Counter(votes)
    if not counts:
        return None
    # Canonical counts are accumulated in reverse encounter order and each
    # updated color moves to the front. Thus a tied maximum favors the first
    # color encountered by the prelude's component BFS, then U/D/L/R contacts.
    return (min if minority else max)(counts, key=counts.get)


def region_data(grid):
    """Zero-room cells, bounds, cardinal contact counts, and canonical winner."""
    _grid(grid)
    result = _components(grid, lambda color: color == 0)
    for record in result:
        votes = _votes(grid, record["cells"])
        record["counts"] = dict(Counter(votes))
        record["winner"] = _winner(votes)
    return result


def filled_components(grid):
    """Same-color 4-connected objects excluding background 0 and wall 5."""
    return _components(_grid(grid), lambda color: color not in (0, 5))


def rivals_for(retention):
    return _VOTE_RIVALS if _retention(retention) == "all" else RIVALS


def _check_rival(rival, retention):
    if rival is not None and (type(rival) is not str or rival not in rivals_for(retention)):
        raise ValueError("rival must be declared for the selected retention")


def evaluate(grid, retention="all", rival=None):
    """Evaluate the rule or one named audit rival without mutating the input.

    Vote rivals alter A and then honor the selected retention. Retention rivals
    preserve canonical A and substitute B's ranking. Every policy preserves all
    original nonzero cells; tied maxima are all retained.
    """
    _grid(grid)
    _retention(retention)
    _check_rival(rival, retention)
    rooms = region_data(grid)
    filled = [row[:] for row in grid]
    global_winner = _winner([v for row in grid for v in row if v not in (0, 5)])
    marker_index = (
        {p: (index, item["color"])
         for index, item in enumerate(filled_components(grid)) for p in item["cells"]}
        if rival == "marker_components" else {}
    )
    for room in rooms:
        winner = room["winner"]
        if rival == "side_only":
            side = Counter(_votes(grid, room["cells"], ((0, -1), (0, 1))))
            if side:
                best = max(side.values())
                if sum(value == best for value in side.values()) == 1:
                    winner = max(side, key=side.get)
        elif rival == "row_copy":
            row_bounds = room["bbox"][0], room["bbox"][2]
            leftmost = next(item for item in rooms
                            if (item["bbox"][0], item["bbox"][2]) == row_bounds)
            winner = leftmost["winner"]
        elif rival == "global_indicator_majority":
            winner = global_winner
        elif rival == "minority":
            winner = _winner(_votes(grid, room["cells"]), minority=True)
        elif rival == "marker_components":
            seen, votes = set(), []
            for r, c in room["cells"]:
                for dr, dc in _DIRS:
                    marker = marker_index.get((r + dr, c + dc))
                    if marker is not None and marker[0] not in seen:
                        seen.add(marker[0])
                        votes.append(marker[1])
            winner = _winner(votes)
        if winner is not None:
            for r, c in room["cells"]:
                filled[r][c] = winner
    if retention == "all":
        return filled

    candidates = rooms if rival == "largest_room" else filled_components(filled)
    color_totals = Counter(v for row in filled for v in row if v not in (0, 5))
    originals = filled_components(grid) if rival == "original_components" else []

    def score(component):
        if rival == "largest_color_total":
            return color_totals[component["color"]]
        if rival == "bbox_size":
            r0, c0, r1, c1 = component["bbox"]
            return (r1 - r0 + 1) * (c1 - c0 + 1)
        if rival == "original_components":
            cells = set(component["cells"])
            return max((len(item["cells"]) for item in originals
                        if any(p in cells for p in item["cells"])), default=0)
        return len(component["cells"])

    maximum = max((score(component) for component in candidates), default=0)
    kept = {p for component in candidates if score(component) == maximum
            for p in component["cells"]}
    return [[filled[r][c] if grid[r][c] == 0 and (r, c) in kept else grid[r][c]
             for c in range(len(grid[0]))] for r in range(len(grid))]


_RACKET_VOTE_HELPERS = r"""
    (define zero-objects (objects (cellmap g (r c v) (if (= v 0) 1 0)) 0))
    (define (votes cells directions)
      (apply append
        (map (lambda (p)
          (filter (lambda (v) (and (!= v 0) (!= v 5)))
            (map (lambda (d)
              (let ((r (+ (first p) (first d)))
                    (c (+ (second p) (second d))))
                (if (and (>= r 0) (< r (rows g)) (>= c 0) (< c (cols g)))
                    (at g r c) 0))) directions))) cells)))
    (define (count-value values v) (length (filter (lambda (x) (= x v)) values)))
    (define (choose values least)
      (if (null? values) #f
        (for/fold ((best (first values))) ((v (in-list values)))
          (if (if least (< (count-value values v) (count-value values best))
                        (> (count-value values v) (count-value values best)))
              v best))))
    (define cardinal (list (list -1 0) (list 1 0) (list 0 -1) (list 0 1)))
    (define (ordinary obj) (choose (votes (obj-cells obj) cardinal) #f))
"""


def _rival_fill_lambda(name):
    extra = ""
    if name == "side_only":
        choice = r"""(let* ((side (votes (obj-cells obj) (list (list 0 -1) (list 0 1))))
                            (best (choose side #f))
                            (tied (if best
                              (filter (lambda (v) (= (count-value side v) (count-value side best)))
                                      (remove-duplicates side)) (list))))
                       (if (= (length tied) 1) best (ordinary obj)))"""
    elif name == "row_copy":
        choice = r"""(ordinary (first (filter (lambda (other)
                        (and (= (first (obj-bbox other)) (first (obj-bbox obj)))
                             (= (third (obj-bbox other)) (third (obj-bbox obj))))) zero-objects)))"""
    elif name == "global_indicator_majority":
        choice = r"""(choose (filter (lambda (v) (and (!= v 0) (!= v 5)))
                                     (apply append g)) #f)"""
    elif name == "minority":
        choice = "(choose (votes (obj-cells obj) cardinal) #t)"
    elif name == "marker_components":
        extra = r"""
    (define marker-objects
      (filter (lambda (obj) (!= (obj-color obj) 5)) (objects g 0)))
    (define (marker-votes cells)
      (let* ((neighbors (apply append (map (lambda (p)
                          (map (lambda (d) (list (+ (first p) (first d))
                                                 (+ (second p) (second d)))) cardinal)) cells)))
             (touching (map (lambda (p)
                         (find-first (lambda (obj) (member? p (obj-cells obj))) marker-objects))
                       neighbors)))
        (map obj-color (remove-duplicates (filter (lambda (obj) obj) touching)))))
"""
        choice = "(choose (marker-votes (obj-cells obj)) #f)"
    else:
        raise ValueError("unknown vote rival")
    return "(lambda (g)\n" + _RACKET_VOTE_HELPERS + extra + f"""
    (for/fold ((out g)) ((obj (in-list zero-objects)))
      (let ((winner {choice}))
        (if winner
          (for/fold ((acc out)) ((p (in-list (obj-cells obj))))
            (set-cell acc (first p) (second p) winner))
          out))))"""


def _retain_program(fill_lambda, rival=None):
    candidates = (
        "(objects (cellmap g (r c v) (if (= v 0) 1 0)) 0)"
        if rival == "largest_room"
        else "(filter (lambda (obj) (!= (obj-color obj) 5)) (objects filled 0))"
    )
    if rival == "largest_color_total":
        score = "(count-color filled (obj-color obj))"
    elif rival == "bbox_size":
        score = """(let ((bb (obj-bbox obj)))
                       (* (+ 1 (- (third bb) (first bb)))
                          (+ 1 (- (fourth bb) (second bb)))))"""
    elif rival == "original_components":
        score = """(let ((old (filter (lambda (source)
                           (any? (lambda (p) (member? p (obj-cells obj))) (obj-cells source)))
                         (filter (lambda (source) (!= (obj-color source) 5)) (objects g 0)))))
                       (if (null? old) 0 (apply max (map obj-size old))))"""
    else:
        score = "(obj-size obj)"
    return f"""(rule! (lambda (g)
      (let* ((filled ({fill_lambda} g))
             (candidates {candidates})
             (score (lambda (obj) {score}))
             (maximum (if (null? candidates) 0 (apply max (map score candidates))))
             (selected (filter (lambda (obj) (= (score obj) maximum)) candidates))
             (kept (apply append (map obj-cells selected))))
        (cellmap g (r c v)
          (if (= v 0)
              (if (member? (list r c) kept) (at filled r c) 0)
              v)))))"""


def program(settings):
    """One complete Racket rule; canonical all is byte-identical to authority."""
    retention = _settings(settings)
    if retention == "all":
        return canonical_program()
    return _retain_program(_canonical_lambda())


def rival_program(name, retention="all"):
    """Materialize an audit rival with precisely the Python mirror's semantics."""
    _retention(retention)
    _check_rival(name, retention)
    if name is None:
        raise ValueError("rival name is required")
    fill = _rival_fill_lambda(name) if name in _VOTE_RIVALS else _canonical_lambda()
    if retention == "all":
        return "(rule! " + fill + ")"
    return _retain_program(fill, name if name not in _VOTE_RIVALS else None)
