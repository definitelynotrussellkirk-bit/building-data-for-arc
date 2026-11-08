"""Infer primitive row motifs, then continue by repeat, reverse cycle or bounce.

Python outputs are deterministic claims. Protected audits/native qualification
execute the independent Racket programs; the default source is byte-exact.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
POLICIES = ("repeat", "reverse_cycle", "bounce")
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"continuation"}:
        raise ValueError("settings must contain only continuation")
    policy = settings["continuation"]
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("unknown continuation")
    return policy


def _analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or any(type(row) is not list for row in grid)
            or not 1 <= len(grid[0]) <= 30
            or any(len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("expected a rectangular literal-integer ARC grid at most 30x30")
    facts = []
    for row in grid:
        occupied = [c for c, v in enumerate(row) if v != 0]
        if not occupied:
            facts.append({"right": None, "period": None, "phase": None, "motif": []})
            continue
        right = occupied[-1]
        period = next(p for p in range(1, right + 2)
                      if all(row[c] == row[c % p] for c in range(right + 1)))
        facts.append({"right": right, "period": period, "phase": right % period,
                      "motif": row[:period]})
    return facts


def apply_claim(grid, settings):
    policy = _settings(settings)
    facts = _analyze(grid)
    output = deepcopy(grid)
    for r, fact in enumerate(facts):
        right, period = fact["right"], fact["period"]
        if right is None:
            continue
        phase, motif = fact["phase"], fact["motif"]
        for c in range(right + 1, len(grid[0])):
            distance = c - right
            if period == 1:
                index = 0
            elif policy == "repeat":
                index = (phase + distance) % period
            elif policy == "reverse_cycle":
                index = (phase - distance) % period
            else:
                cycle = 2 * (period - 1)
                folded = (phase + distance) % cycle
                index = min(folded, cycle - folded)
            output[r][c] = motif[index]
    return output


_PRELUDE = r"""(rule! (lambda (g)
  (let ((h (rows g)) (w (cols g)))
    (define (occupied-cols r)
      (filter (lambda (c) (not (= (at g r c) 0))) (range 0 w)))
    (define (right-of r)
      (let ((xs (occupied-cols r))) (if (empty? xs) #f (apply max xs))))
    (define rights (map right-of (range 0 h)))
    (define active (filter (lambda (r) (not (equal? (list-ref rights r) #f))) (range 0 h)))
    (define (compatible? r left right p)
      (for/and ((c (range left (+ right 1))))
        (= (at g r c) (at g r (+ left (mod (- c left) p))))))
    (define (infer-period r left right)
      (find-first (lambda (p) (compatible? r left right p))
                  (range 1 (+ (- right left) 2))))
"""


def _rule(policy, *, period_mode="minimal", fixed_period=None,
          phase_mode="observed", distance_mode="relative", origin_mode="zero",
          shared_period=None, copy_first=False, global_right=False,
          fill_mode=None, overwrite=False, duplicate_endpoints=False,
          backward_bounce=False):
    """Complete programs for the actual policies and finite executable rivals.

    Wrong fixed periods are clamped to available prefix length, so the rivals
    remain executable even on tiny lawful grids. No exception is a refutation.
    """
    origin = "(apply min (occupied-cols r))" if origin_mode == "first_nonzero" else "0"
    selected = {
        "minimal": "(infer-period r left right)",
        "visible_prefix": "(+ (- right left) 1)",
        "right_as_length": "(max 1 (- right left))",
        "full_row": "(infer-period r left (- w 1))",
        "divisor_only": "(find-first (lambda (p) (and (= (mod (+ (- right left) 1) p) 0) (compatible? r left right p))) (range 1 (+ (- right left) 2)))",
    }[period_mode]
    if fixed_period is not None:
        selected = f"(min {fixed_period} (+ (- right left) 1))"
    definitions = _PRELUDE + f"""
    (define origins (map (lambda (r) (if (equal? (list-ref rights r) #f) 0 {origin})) (range 0 h)))
    (define periods
      (map (lambda (r)
        (let ((right (list-ref rights r)) (left (list-ref origins r)))
          (if (equal? right #f) 1 {selected}))) (range 0 h)))
    (define first-active (if (empty? active) 0 (first active)))
    (define active-periods (map (lambda (r) (list-ref periods r)) active))
    (define shared-p {"(if (empty? active-periods) 1 (apply "+shared_period+" active-periods))" if shared_period in ("min", "max") else "(list-ref periods first-active)"})
    (define final-right (if (empty? active) 0 (apply max (map (lambda (r) (list-ref rights r)) active))))
"""
    p = "shared-p" if shared_period is not None or copy_first else "(list-ref periods r)"
    source_row = "first-active" if copy_first else "r"
    cutoff = "final-right" if global_right else "(list-ref rights r)"
    phase = {"observed": "(mod (- right left) p)",
             "absolute": "(mod right p)",
             "zero": "0", "one": "1", "minus_one": "-1",
             "plus_one": "(+ 1 (mod (- right left) p))",
             "last": "(- p 1)"}[phase_mode]
    distance = "c" if distance_mode == "absolute" else "(- c right)"
    if policy == "repeat":
        index = "(mod (+ phase distance) p)"
    elif policy == "reverse_cycle":
        index = "(mod (- phase distance) p)"
    else:
        cycle = "(* 2 p)" if duplicate_endpoints else "(* 2 (- p 1))"
        reflection = "(- (- cycle 1) folded)" if duplicate_endpoints else "(- cycle folded)"
        directed = "(- phase distance)" if backward_bounce else "(+ phase distance)"
        index = f"(let* ((cycle {cycle}) (folded (mod {directed} cycle))) (min folded {reflection}))"
    index = f"(if (= p 1) 0 {index})"
    value = f"(at g {source_row} (+ left {index}))"
    if fill_mode == "last_color":
        value = "(at g r (list-ref rights r))"
    preserve = "#f" if overwrite else "(<= c right)"
    expression = f"""
    (grid-from-fn h w
      (lambda (r c)
        (if (equal? (list-ref rights r) #f) 0
          (let* ((right {cutoff}) (left (list-ref origins {source_row}))
                 (p {p}) (phase {phase}) (distance {distance}))
            (if {preserve} (at g r c) {value}))))))))"""
    return definitions + expression


def program(settings):
    policy = _settings(settings)
    return CANONICAL if policy == "repeat" else _rule(policy)


def rivals(settings):
    """Extra rivals; audit.py separately compares all other parameter settings."""
    policy = _settings(settings)
    result = {"identity": "(rule! (lambda (g) g))",
              "last_color_tail": _rule(policy, fill_mode="last_color"),
              "repeat_visible_prefix": _rule(policy, period_mode="visible_prefix"),
              "period_requires_divisibility": _rule(policy, period_mode="divisor_only"),
              "right_index_used_as_length": _rule(policy, period_mode="right_as_length"),
              "infer_through_trailing_blanks": _rule(policy, period_mode="full_row"),
              "shared_first_period": _rule(policy, shared_period="first"),
              "shared_min_period": _rule(policy, shared_period="min"),
              "shared_max_period": _rule(policy, shared_period="max"),
              "copy_first_pattern": _rule(policy, copy_first=True),
              "leading_zeros_treated_as_margin": _rule(policy, origin_mode="first_nonzero", phase_mode="absolute"),
              "global_rightmost_delimiter": _rule(policy, global_right=True),
              "reset_phase_zero": _rule(policy, phase_mode="zero"),
              "restart_first_motif_cell": _rule(policy, phase_mode="one" if policy == "reverse_cycle" else "minus_one"),
              "advance_phase_one_extra": _rule(policy, phase_mode="plus_one"),
              "absolute_tail_distance": _rule(policy, distance_mode="absolute")}
    result.update({f"fixed_period_{p}_clamped": _rule(policy, fixed_period=p) for p in range(1, 11)})
    if policy != "repeat":
        result.update({"rewrite_observed_prefix": _rule(policy, overwrite=True),
                       "restart_from_last_motif_cell": _rule(policy, phase_mode="last")})
    if policy == "bounce":
        result.update({"duplicate_reflection_endpoints": _rule(policy, duplicate_endpoints=True),
                       "bounce_initially_backward": _rule(policy, backward_bounce=True),
                       "bounce_absolute_column_phase": _rule(policy, phase_mode="zero", distance_mode="absolute")})
    return result


def _sampler():
    path = HERE / "sampler.py"
    name = "_80271cb9b303_inputs_" + hashlib.sha256(str(path).encode()).hexdigest()
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def generate(seed, settings, demos, queries):
    _settings(settings)
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    if type(demos) is not int or not 3 <= demos <= 6:
        raise ValueError("demos must be a literal integer in 3..6")
    if type(queries) is not int or not 1 <= queries <= 4:
        raise ValueError("queries must be a literal integer in 1..4")
    banks = _sampler().input_banks(seed)
    episode = {split: [{"input": deepcopy(grid), "output": apply_claim(grid, settings)}
                       for grid in banks[split][:count]]
               for split, count in (("train", demos), ("test", queries))}
    episode["program_solution"] = program(settings)
    return episode


def describe(grid, settings):
    policy = _settings(settings)
    facts = _analyze(grid)
    output = apply_claim(grid, settings)
    return {"continuation": policy, "input_shape": [len(grid), len(grid[0])],
            "output_shape": [len(output), len(output[0])], "rows": facts,
            "active_rows": [r for r, fact in enumerate(facts) if fact["right"] is not None],
            "periods": sorted({fact["period"] for fact in facts if fact["period"] is not None}),
            "occupied_input_cells": sum(v != 0 for row in grid for v in row),
            "occupied_output_cells": sum(v != 0 for row in output for v in row),
            "changed_cells": sum(a != b for row, other in zip(grid, output) for a, b in zip(row, other))}


def public_turn(episode, index):
    if type(index) is not int or not 0 <= index < len(episode["test"]):
        raise ValueError("query index must select exactly one existing query")
    return {"train": [{"input": deepcopy(p["input"]), "output": deepcopy(p["output"])}
                      for p in episode["train"]],
            "test": [{"input": deepcopy(episode["test"][index]["input"])}]}
