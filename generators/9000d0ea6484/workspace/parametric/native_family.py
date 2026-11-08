"""Native cyclic panel scans, including input-derived density anchors.

The eight fixed scans reuse the retained prototype's guarded exact programs.
Four density scans count panel cells before choosing a cyclic scan. Python
labels are claims; protected Racket qualification independently checks them.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from itertools import permutations
from pathlib import Path
import sys

TASK_ID = "9000d0ea6484"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
START_SECTIONS = (0, 1, 2, 3, "densest", "sparsest")
SCAN_DIRECTIONS = ("forward", "reverse")
DEFAULT = {"start_section": 2, "scan_direction": "forward"}
SETTINGS = tuple({"start_section": start, "scan_direction": direction}
                 for start in START_SECTIONS for direction in SCAN_DIRECTIONS)
TIE_PRIORITY = (2, 3, 0, 1)
SECTION_STARTS = (0, 5, 10, 15)
CANONICAL_SHA256 = "3bec9ede53940dce7bdf0aa83666b99ea3fb754cb6c4d356406e7eab30dade8c"
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
if hashlib.sha256(CANONICAL.encode()).hexdigest() != CANONICAL_SHA256:
    raise ValueError("canonical.rkt does not match the pinned exact source")


def _adjacent(filename):
    path = HERE / filename
    name = "_9000d0ea6484_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
    return sys.modules[name]


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"start_section", "scan_direction"}:
        raise ValueError("settings must contain only start_section and scan_direction")
    start, direction = settings["start_section"], settings["scan_direction"]
    if not ((type(start) is int and start in (0, 1, 2, 3))
            or (type(start) is str and start in ("densest", "sparsest"))):
        raise ValueError("start_section must be 0..3, densest, or sparsest")
    if type(direction) is not str or direction not in SCAN_DIRECTIONS:
        raise ValueError("scan_direction must be forward or reverse")
    return start, direction


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list or len(row) != 19 for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("expected a literal-integer ARC grid with 1..30 rows and 19 columns")
    if any(row[c] != 3 for row in grid for c in (4, 9, 14)):
        raise ValueError("columns 4, 9, and 14 must be color-3 dividers")
    if any(row[c] == 3 for row in grid for c in range(19) if c not in (4, 9, 14)):
        raise ValueError("color 3 is reserved for divider columns")
    return grid


def _counts(grid):
    return [sum(grid[r][start + c] != 0 for r in range(len(grid)) for c in range(4))
            for start in SECTION_STARTS]


def _order(counts, settings):
    start, direction = _settings(settings)
    if type(start) is str:
        target = (max if start == "densest" else min)(counts)
        start = next(i for i in TIE_PRIORITY if counts[i] == target)
    step = 1 if direction == "forward" else -1
    return tuple((start + step * offset) % 4 for offset in range(4))


def apply_claim(grid, settings):
    """Independent Python claim; no Racket process is started by the adapter."""
    _settings(settings)
    _grid(grid)
    order = _order(_counts(grid), settings)
    return [[next((grid[r][SECTION_STARTS[s] + c] for s in order
                   if grid[r][SECTION_STARTS[s] + c] != 0), 0)
             for c in range(4)] for r in range(len(grid))]


_PRELUDE = r"""(rule! (lambda (g)
  (let ((h (rows g)))
    (define indices (list 0 1 2 3))
    (define (sec si r c) (at g r (+ (* si 5) c)))
    (define (panel si) (build-grid h 4 (r c) (sec si r c)))
    (define (count-cells si)
      (length (filter (lambda (v) (!= v 0))
        (for*/list ((r (range 0 h)) (c (range 0 4))) (sec si r c)))))
    (define (count-rows si)
      (length (filter (lambda (r)
        (find (lambda (c) (!= (sec si r c) 0)) (range 0 4))) (range 0 h))))
    (define (count-columns si)
      (length (filter (lambda (c)
        (find (lambda (r) (!= (sec si r c) 0)) (range 0 h))) (range 0 4))))
    (define (count-components si) (length (objects (panel si) 0)))
    (define (panel-color si)
      (apply max (for*/list ((r (range 0 h)) (c (range 0 4))) (sec si r c))))
"""


def _density_program(start, direction, *, metric="cells", ties=TIE_PRIORITY,
                     sorted_scan=False, only_anchor=False, ignored=None):
    if start not in ("densest", "sparsest") or direction not in SCAN_DIRECTIONS:
        raise ValueError("density rule needs a density start and scan direction")
    metrics = {"cells": "count-cells", "rows": "count-rows", "columns": "count-columns",
               "components": "count-components", "color": "panel-color"}
    metric_name = metrics[metric]
    maximum = start == "densest"
    extreme = "max" if maximum else "min"
    step = 1 if direction == "forward" else -1
    priority = f"(map (lambda (k) (modulo (+ start (* {step} k)) 4)) (range 0 4))"
    if sorted_scan:
        comparator = ">" if maximum else "<"
        priority = f"(sort tie-priority (lambda (a b) ({comparator} (list-ref scores a) (list-ref scores b))))"
    if only_anchor:
        priority = "(list start)"
    if ignored is not None:
        if type(ignored) is not int or ignored not in (0, 1, 2, 3):
            raise ValueError("ignored section must be 0..3")
        ties = tuple(i for i in ties if i != ignored)
    tie_text = " ".join(map(str, ties))
    target_scores = "scores" if ignored is None else "(map (lambda (si) (list-ref scores si)) tie-priority)"
    return _PRELUDE + f"""    (define tie-priority (list {tie_text}))
    (define scores (map {metric_name} indices))
    (define target (apply {extreme} {target_scores}))
    (define start (find (lambda (si) (= (list-ref scores si) target)) tie-priority))
    (define priority {priority})
    (build-grid h 4 (r c)
      (let ((hit (find (lambda (si) (!= (sec si r c) 0)) priority)))
        (if hit (sec hit r c) 0))))))"""


def program(settings):
    start, direction = _settings(settings)
    if type(start) is int:
        # Reuse the retained guarded rule materializer; load by exact path.
        return _adjacent("prototype.py").materialize_rule(start, direction, root=ROOT)
    return _density_program(start, direction)


def _fixed_program(order):
    old = "(priority (list 2 3 0 1))"
    assert CANONICAL.count(old) == 1
    return CANONICAL.replace(old, "(priority (list " + " ".join(map(str, order)) + "))", 1)


def _cell_program(selector):
    return r"""(rule! (lambda (g)
      (build-grid (rows g) 4 (r c)
        (let ((vals (filter (lambda (v) (!= v 0))
                (map (lambda (s) (at g r (+ (* s 5) c))) (list 0 1 2 3)))))
          (if (empty? vals) 0 """ + selector + ")))))"


def rivals(settings):
    """Finite, executable teaching alternatives; not a uniqueness claim."""
    start, direction = _settings(settings)
    selected = program(settings)
    result = {"fixed_order_" + "".join(map(str, order)): _fixed_program(order)
              for order in permutations(range(4)) if _fixed_program(order) != selected}
    result.update({"numeric_max": _cell_program("(apply max vals)"),
                   "numeric_min_nonzero": _cell_program("(apply min vals)"),
                   "fixed_canonical_color_priority": _cell_program(r"""(first
                     (sort vals (lambda (a b)
                       (< (cond ((= a 9) 0) ((= a 4) 1) ((= a 8) 2) ((= a 5) 3) (else (+ 100 a)))
                          (cond ((= b 9) 0) ((= b 4) 1) ((= b 8) 2) ((= b 5) 3) (else (+ 100 b)))))))""")})
    if type(start) is str:
        result.update({"rank_by_" + metric: _density_program(start, direction, metric=metric)
                       for metric in ("rows", "columns", "components", "color")})
        result.update({"ignore_anchor_candidate_" + str(i): _density_program(start, direction, ignored=i)
                       for i in range(4)})
        result.update({"ties_smallest_index": _density_program(start, direction, ties=(0, 1, 2, 3)),
                       "ties_largest_index": _density_program(start, direction, ties=(3, 2, 1, 0)),
                       "ties_reverse_canonical": _density_program(start, direction, ties=(1, 0, 3, 2)),
                       "sort_all_by_count": _density_program(start, direction, sorted_scan=True),
                       "use_anchor_only": _density_program(start, direction, only_anchor=True)})
    else:
        order = _order([0, 0, 0, 0], settings)
        result["omit_last_priority_section"] = _fixed_program(order[:-1])
        result["use_first_section_only"] = _fixed_program(order[:1])
    return result


def generate(seed, settings=None, demos=4, queries=4):
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    if type(demos) is not int or not 4 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 4..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    if settings is None:
        settings = SETTINGS[seed % len(SETTINGS)]
    _settings(settings)
    bank = _adjacent("sampler.py").build_bank(seed)
    episode = {split: [{"input": deepcopy(grid), "output": apply_claim(grid, settings)}
                       for grid in bank[split][:count]]
               for split, count in (("train", demos), ("test", queries))}
    episode["program_solution"] = program(settings)
    episode["private_metadata"] = {"settings": deepcopy(settings), "seed": seed,
                                   "profiles": deepcopy(bank["specs"])}
    return episode


def describe(grid, settings):
    _settings(settings)
    _grid(grid)
    counts = _counts(grid)
    order = _order(counts, settings)
    output = apply_claim(grid, settings)
    return {"input_shape": [len(grid), 19], "output_shape": [len(grid), 4],
            "counts": counts, "selected_start": order[0], "priority_order": list(order),
            "panel_colors": [sorted({row[start+c] for row in grid for c in range(4)} - {0})
                             for start in SECTION_STARTS],
            "occupied_input_cells": sum(v != 0 for row in grid for v in row),
            "occupied_output_cells": sum(v != 0 for row in output for v in row),
            "payload_cells": sum(counts), "divider_cells": 3 * len(grid)}


def public_turn(episode, index=0):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index must select exactly one existing query")
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}
