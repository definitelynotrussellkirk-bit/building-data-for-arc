"""Bounded, rerunnable Racket-label and demonstration-only teaching audit.

Run through review.py run; --out must be a new directory. This authoring tool
does not qualify, accept, or admit the family to training.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import random

from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator
from reviewer_support import find_root

HERE = Path(__file__).resolve().parent
TASK = "8d2cfdfec79c"


def _load(name):
    path = HERE / (name + ".py")
    spec = importlib.util.spec_from_file_location("_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RIVALS = (
    "identity", "fill_all_boxes", "fixed_color_8", "reverse_order", "completion_order",
    "numeric_order", "restore_clues", "first_two_only", "skip_thin", "outline_only",
    "fill_all", "first", "last", "numeric_min", "numeric_max", "numeric_median",
    "raw_perimeter", "bbox_area", "min_visible", "tie_last", "fillable_only",
    "smallest_fillable", "visible_fraction_fillable", "before_last", "overwrite_interior",
    "winner_only", "visible_bbox", "largest_zero_interior", "fill_whole_box",
)


def rival_output(grid, mode, rival):
    """Independent finite wrong-rule implementations, with no query-label access."""
    if rival not in RIVALS:
        raise ValueError("undeclared rival")
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, []).append((r, c))
    colors = list(groups)
    boxes = {color: (min(r for r, c in cells), min(c for r, c in cells),
                     max(r for r, c in cells), max(c for r, c in cells))
             for color, cells in groups.items()}
    def perimeter(color):
        r0, c0, r1, c1 = boxes[color]
        return 2 * (r1 - r0 + c1 - c0)
    def area(color):
        r0, c0, r1, c1 = boxes[color]
        return (r1 - r0 + 1) * (c1 - c0 + 1)
    def fillable(color):
        r0, c0, r1, c1 = boxes[color]
        return min(r1 - r0, c1 - c0) > 1
    def render(order, fill=False):
        out = [[0] * len(grid[0]) for _ in grid]
        for color in order:
            r0, c0, r1, c1 = boxes[color]
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    if fill or r in (r0, r1) or c in (c0, c1):
                        out[r][c] = color
        return out
    if rival == "identity":
        return [row[:] for row in grid]
    order = colors[:]
    if rival == "reverse_order":
        order.reverse()
    elif rival == "completion_order":
        order.sort(key=lambda color: groups[color][-1])
    elif rival == "numeric_order":
        order.sort()
    elif rival == "first_two_only":
        order = order[:2]
    elif rival == "skip_thin":
        order = [color for color in order if fillable(color)]
    out = render(order, fill=(rival == "fill_all_boxes"))
    if rival == "restore_clues":
        for color, cells in groups.items():
            for r, c in cells:
                out[r][c] = color
    if mode == "outline" or rival == "outline_only":
        return [[8 if v else 0 for v in row] for row in out] if rival == "fixed_color_8" else out
    scoring = render(colors[:-1]) if rival == "before_last" else out
    counts = Counter(cell for row in scoring for cell in row if cell)
    eligible = [color for color in colors if fillable(color)] or colors
    winner = max(colors, key=lambda color: counts[color])
    if rival == "first":
        winner = colors[0]
    elif rival == "last":
        winner = colors[-1]
    elif rival in ("numeric_min", "numeric_max", "numeric_median"):
        winner = {"numeric_min": min(colors), "numeric_max": max(colors),
                  "numeric_median": sorted(colors)[len(colors) // 2]}[rival]
    elif rival == "raw_perimeter":
        winner = max(colors, key=perimeter)
    elif rival == "bbox_area":
        winner = max(colors, key=area)
    elif rival == "min_visible":
        winner = min(colors, key=lambda color: counts[color])
    elif rival == "tie_last":
        winner = max(reversed(colors), key=lambda color: counts[color])
    elif rival == "fillable_only":
        winner = max(eligible, key=lambda color: counts[color])
    elif rival == "smallest_fillable":
        winner = min(eligible, key=area)
    elif rival == "visible_fraction_fillable":
        winner = max(eligible, key=lambda color: Fraction(counts[color], perimeter(color)))
    elif rival == "largest_zero_interior":
        def zeros(color):
            r0, c0, r1, c1 = boxes[color]
            return sum(out[r][c] == 0 for r in range(r0 + 1, r1)
                       for c in range(c0 + 1, c1))
        winner = max(colors, key=zeros)
    chosen = colors if rival == "fill_all" else [winner]
    if rival == "visible_bbox":
        cells = [(r, c) for r, row in enumerate(out) for c, v in enumerate(row) if v == winner]
        boxes[winner] = (min(r for r, c in cells), min(c for r, c in cells),
                         max(r for r, c in cells), max(c for r, c in cells))
    if rival == "winner_only":
        out = [[0] * len(grid[0]) for _ in grid]
    for color in chosen:
        r0, c0, r1, c1 = boxes[color]
        delta = 0 if rival == "fill_whole_box" else 1
        for r in range(r0 + delta, r1 + 1 - delta):
            for c in range(c0 + delta, c1 + 1 - delta):
                if out[r][c] == 0 or rival in ("overwrite_interior", "fill_whole_box"):
                    out[r][c] = color
    return [[8 if v else 0 for v in row] for row in out] if rival == "fixed_color_8" else out


def racket_rival(name, prototype=None):
    """Protected-executable counterfactuals for the repaired teaching holes."""
    p = prototype or _load("prototype")
    text = p.FILL_PROGRAM
    if name == "overwrite_interior":
        return text.replace("#:when (= (at outlines r c) 0)", "#:when #t")
    if name == "raw_perimeter":
        return text.replace("(length (find-color outlines color))",
            "(let ((b (box color))) (* 2 (+ (- (third b) (first b)) (- (fourth b) (second b)))))")
    if name not in ("fillable_only", "smallest_fillable", "visible_fraction_fillable"):
        raise ValueError("no Racket counterfactual for this rival")
    original = """    (define winner
      (for/fold ((best (first colors))) ((color (in-list (rest colors))))
        (if (> (score color) (score best)) color best)))"""
    selector = "(> (score color) (score best))"
    if name == "smallest_fillable":
        selector = "(< (area color) (area best))"
    elif name == "visible_fraction_fillable":
        selector = "(> (/ (score color) (raw color)) (/ (score best) (raw best)))"
    replacement = """    (define (raw color)
      (let ((b (box color))) (* 2 (+ (- (third b) (first b)) (- (fourth b) (second b))))))
    (define (area color)
      (let ((b (box color))) (* (+ 1 (- (third b) (first b))) (+ 1 (- (fourth b) (second b))))))
    (define eligible
      (filter (lambda (color) (let ((b (box color)))
        (and (> (- (third b) (first b)) 1) (> (- (fourth b) (second b)) 1)))) colors))
    (define candidates (if (null? eligible) colors eligible))
    (define winner
      (for/fold ((best (first candidates))) ((color (in-list (rest candidates))))
        (if SELECTOR color best)))""".replace("SELECTOR", selector)
    if original not in text:
        raise ValueError("current program no longer matches the counterfactual builder")
    return text.replace(original, replacement)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("--out must be a new directory")
    root = find_root(HERE)
    prototype, exporter = _load("prototype"), _load("public_export")
    sources = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.iterdir()) if p.is_file() and p.suffix in (".py", ".rkt", ".json")}
    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [{"seed": seed, "settings": {"mode": mode}, "demos": demos, "queries": 4}
            for seed in (0, 17, 33) for demos in (2, 3, 6) for mode in prototype.MODES]
    execution = evaluate_contract(root, TASK, contract, jobs)
    rows, failures = [], []
    for episode in execution["episodes"]:
        mode = episode["settings"]["mode"]
        survivors = [name for name in RIVALS if all(
            rival_output(pair["input"], mode, name) == pair["output"]
            for pair in episode["train"])]
        disagreements = [{"rival": name, "query_index": index}
                         for name in survivors for index, pair in enumerate(episode["test"])
                         if rival_output(pair["input"], mode, name) != pair["output"]]
        row = {"seed": episode["seed"], "settings": episode["settings"],
               "demos": len(episode["train"]), "queries": len(episode["test"]),
               "demo_consistent_rivals": survivors, "query_disagreements": disagreements}
        rows.append(row)
        failures.extend({**row, "input": episode["test"][d["query_index"]]["input"],
                         "failure": d} for d in disagreements)
    examples = [e for e in execution["episodes"] if e["seed"] == 0 and len(e["train"]) == 3]
    boundaries, repair_cases = [], []
    with _local_imports(root / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(root / "shared/runtime")
        try:
            for index, (h, w, kind) in enumerate(((8, 10, "inversion"), (8, 30, "crossing"),
                                                  (30, 10, "nested"), (30, 30, "crossing"))):
                grid = prototype.varied_scene(random.Random(109 + index), h, w, kind)
                for mode in prototype.MODES:
                    output = apply(prototype.program({"mode": mode}), grid)
                    if output != prototype.predict(grid, mode):
                        raise ValueError("boundary Python claim differs from Racket")
                    boundaries.append({"shape": [h, w], "kind": kind, "settings": {"mode": mode},
                                       "input": grid, "output": output,
                                       "colors": len({v for row in grid for v in row if v}),
                                       "output_nonzero": sum(bool(v) for row in output for v in row)})
            fixed = next(e for e in execution["episodes"]
                         if e["seed"] == 0 and len(e["train"]) == 2
                         and e["settings"]["mode"] == "fill_most_visible")
            for name in ("overwrite_interior", "fillable_only", "smallest_fillable",
                         "visible_fraction_fillable", "raw_perimeter"):
                wrong = racket_rival(name, prototype)
                outputs = [apply(wrong, p["input"]) for p in fixed["train"]]
                for pair, output in zip(fixed["train"], outputs):
                    if output != rival_output(pair["input"], "fill_most_visible", name):
                        raise ValueError("Racket rival and Python rival disagree: " + name)
                indices = [i for i, (p, output) in enumerate(zip(fixed["train"], outputs))
                           if output != p["output"]]
                if not indices:
                    raise ValueError("repaired demos fail to distinguish " + name)
                i = indices[0]
                repair_cases.append({"rival": name, "demo_index": i, "program": fixed["program"],
                    "rival_program": wrong, "input": fixed["train"][i]["input"],
                    "output": fixed["train"][i]["output"], "rival_output": outputs[i]})
        finally:
            bridge.close()
    report = {"schema": "rectangle-parametric-audit-v1", "task_id": TASK,
              "status": "pass" if not failures else "fail", "sources": sources,
              "jobs": jobs, "completed_jobs": len(execution["episodes"]), "failed_jobs": 0,
              "racket": execution["racket"], "native_job_evaluations": execution["racket_evaluations"],
              "extra_racket_evaluations": len(boundaries) + 10,
              "rivals": list(RIVALS), "teaching": rows, "failures": failures,
              "protected_repair_cases": repair_cases, "boundary_cases": boundaries,
              "limits": "Finite declared-rival check using demonstrations only; no universal uniqueness or measured learning gain. No acceptance or training admission."}
    args.out.mkdir(parents=True)
    (args.out / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.out / "examples.private.json").write_text(json.dumps(examples, indent=2, sort_keys=True) + "\n")
    exporter.write_public_turns(examples, args.out / "public")
    print(json.dumps({"status": report["status"], "episodes": len(rows), "rivals": len(RIVALS),
                      "query_disagreements": len(failures), "racket_evaluations":
                      execution["racket_evaluations"] + report["extra_racket_evaluations"],
                      "evidence": str(args.out / "audit.json")}, sort_keys=True))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
