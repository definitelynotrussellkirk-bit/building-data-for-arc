"""Independent, protected finite audit of stable row-ranking lessons.

Demonstrations determine every fit before candidate queries are compared.
Execution errors fail closed. Exact-ratio rivals use integer cross products
in Racket and rational arithmetic in Python. This audit cannot prove uniqueness.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


PARAMETRIC = Path(__file__).resolve().parent
TASK = PARAMETRIC.parents[1]
ROOT = PARAMETRIC.parents[3]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


TASK_ID = "323fded12174"
SETTINGS = ({"rank_by": "occupancy"}, {"rank_by": "anchor_color"})
JOBS = ((0, 3), (17, 3), (101, 6))
RIVALS = ("dominant_count", "mixed_then_dominant", "diversity_then_dominant",
          "ascending", "first_row_anchor", "last_row_anchor",
          "second_occupancy_anchor", "dominant_anchor", "global_color",
          "anchor_first_color", "anchor_min_color", "anchor_max_color",
          "anchor_mode_including_zero", "presence", "fraction", "reverse_ties",
          "lexicographic_ties", "occupancy_tiebreak", "left_justify", "sort_cells")


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def setting(value):
    if (type(value) is not dict or set(value) != {"rank_by"}
            or value["rank_by"] not in ("occupancy", "anchor_color")):
        raise ValueError("Expected exactly one declared rank_by setting")
    return value["rank_by"]


def occupancy(row):
    return sum(value != 0 for value in row)


def modal(values, include_zero=False):
    counts = Counter(value for value in values if include_zero or value != 0)
    if not counts:
        raise ValueError("A modal cue requires at least one eligible cell")
    return min(counts, key=lambda color: (-counts[color], color))


def dominant(row):
    return max(Counter(value for value in row if value != 0).values(), default=0)


def diversity(row):
    return len(set(row)-{0})


def anchor_index(grid):
    return max(range(len(grid)), key=lambda i: (occupancy(grid[i]), -i))


def selected_color(grid, name="reference"):
    anchor = anchor_index(grid)
    if name == "first_row_anchor":
        anchor = 0
    elif name == "last_row_anchor":
        anchor = len(grid)-1
    elif name == "second_occupancy_anchor":
        anchor = sorted(range(len(grid)), key=lambda i: (-occupancy(grid[i]), i))[1]
    elif name == "dominant_anchor":
        anchor = max(range(len(grid)), key=lambda i: (dominant(grid[i]), -i))
    values = grid[anchor]
    if name == "global_color":
        return modal([value for row in grid for value in row])
    if name == "anchor_first_color":
        return next(value for value in values if value)
    if name == "anchor_min_color":
        return min(value for value in values if value)
    if name == "anchor_max_color":
        return max(value for value in values if value)
    return modal(values, include_zero=name == "anchor_mode_including_zero")


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    grid = _grid(grid)
    occupancies = list(map(occupancy, grid))
    color = selected_color(grid, name) if mode == "anchor_color" else None
    active = occupancies if mode == "occupancy" else [row.count(color) for row in grid]
    def key(index):
        row = grid[index]
        if name == "dominant_count":
            score = (-dominant(row),)
        elif name == "mixed_then_dominant":
            score = (-int(diversity(row) > 1), -dominant(row))
        elif name == "diversity_then_dominant":
            score = (-diversity(row), -dominant(row))
        elif name == "ascending":
            score = (active[index],)
        elif name == "presence":
            score = (-int(active[index] > 0),)
        elif name == "fraction":
            denominator = occupancies[index] if mode == "anchor_color" else len(row)
            score = (-Fraction(active[index], denominator),)
        else:
            score = (-active[index],)
        if name == "reverse_ties":
            return (*score, -index)
        if name == "lexicographic_ties":
            return (*score, *row, index)
        if name == "occupancy_tiebreak":
            return (*score, -occupancies[index], index)
        return (*score, index)
    ordered = [list(grid[i]) for i in sorted(range(len(grid)), key=key)]
    if name == "left_justify":
        return [[value for value in row if value] + [0] * row.count(0) for row in ordered]
    if name == "sort_cells":
        return [sorted(row) for row in ordered]
    return ordered


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def facts(grid):
    grid = _grid(grid)
    occ = list(map(occupancy, grid))
    anchor = anchor_index(grid)
    color = modal(grid[anchor])
    counts = Counter(value for value in grid[anchor] if value)
    target = [row.count(color) for row in grid]
    return {"shape": [len(grid), len(grid[0])], "anchor_index": anchor,
            "anchor_color": color, "unique_anchor": occ.count(max(occ)) == 1,
            "unique_nonzero_anchor_mode": list(counts.values()).count(max(counts.values())) == 1,
            "anchor_distinct_colors": diversity(grid[anchor]), "occupancies": occ,
            "target_counts": target, "global_color": modal([v for row in grid for v in row]),
            "palette": sorted(set(v for row in grid for v in row)-{0}),
            "occupancy_order": sorted(range(len(grid)), key=lambda i: (-occ[i], i)),
            "anchor_color_order": sorted(range(len(grid)), key=lambda i: (-target[i], i)),
            "rows": [{"index": i, "occupancy": occ[i], "target_count": target[i],
                      "dominant_count": dominant(row), "distinct_colors": diversity(row),
                      "nonzero_mode": modal(row), "counts": dict(sorted(Counter(row).items()))}
                     for i, row in enumerate(grid)]}


def rival_program(settings, name):
    """Return a complete Racket interpretation, independent of the family code."""
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    cue_index = "anchor"
    if name == "first_row_anchor":
        cue_index = "0"
    elif name == "last_row_anchor":
        cue_index = "(- (rows g) 1)"
    elif name == "second_occupancy_anchor":
        cue_index = "(second occupancy-order)"
    elif name == "dominant_anchor":
        cue_index = "(first (sort indices (lambda (i j) (> (dom (nth g i)) (dom (nth g j))))))"
    color = f"(mode (nth g {cue_index}) 1)"
    if name == "global_color":
        color = "(mode (apply append g) 1)"
    elif name == "anchor_first_color":
        color = "(first (filter (lambda (v) (!= v 0)) (nth g anchor)))"
    elif name in {"anchor_min_color", "anchor_max_color"}:
        color = f"(apply {'min' if name == 'anchor_min_color' else 'max'} (filter (lambda (v) (!= v 0)) (nth g anchor)))"
    elif name == "anchor_mode_including_zero":
        color = "(mode (nth g anchor) 0)"
    active = "(occ (nth g i))" if mode == "occupancy" else "(freq (nth g i) chosen-color)"
    score = "(list (- (active i)))"
    if name == "dominant_count":
        score = "(list (- (dom (nth g i))))"
    elif name == "mixed_then_dominant":
        score = "(list (- (if (> (diversity (nth g i)) 1) 1 0)) (- (dom (nth g i))))"
    elif name == "diversity_then_dominant":
        score = "(list (- (diversity (nth g i))) (- (dom (nth g i))))"
    elif name == "ascending":
        score = "(list (active i))"
    elif name == "presence":
        score = "(list (- (if (> (active i) 0) 1 0)))"
    tail = "(list i)"
    if name == "reverse_ties":
        tail = "(list (- i))"
    elif name == "lexicographic_ties":
        tail = "(append (nth g i) (list i))"
    elif name == "occupancy_tiebreak":
        tail = "(list (- (occ (nth g i))) i)"
    comparator = "(key<? (key i) (key j))"
    if name == "fraction":
        denominator = "(occ (nth g i))" if mode == "anchor_color" else "(cols g)"
        comparator = "(let ((left (* (active i) (denominator j))) (right (* (active j) (denominator i)))) (cond ((> left right) #t) ((< left right) #f) (else (< i j))))"
    else:
        denominator = "1"
    render = "(nth g i)"
    if name == "left_justify":
        render = "(append (filter (lambda (v) (!= v 0)) (nth g i)) (make-list (- (cols g) (occ (nth g i))) 0))"
    elif name == "sort_cells":
        render = "(sort (nth g i) <)"
    return f"""(rule! (lambda (g)
  (define (freq values color) (count-if (lambda (v) (= v color)) values))
  (define (occ values) (count-if (lambda (v) (!= v 0)) values))
  (define (dom values) (apply max (map (lambda (c) (freq values c)) (range 1 10))))
  (define (diversity values) (count-if (lambda (c) (> (freq values c) 0)) (range 1 10)))
  (define (mode values start) (first (sort (range start 10) (lambda (a b) (> (freq values a) (freq values b))))))
  (define (key<? a b) (cond ((empty? a) #f) ((< (first a) (first b)) #t)
    ((> (first a) (first b)) #f) (else (key<? (rest a) (rest b)))))
  (define indices (range (rows g)))
  (define occupancy-order (sort indices (lambda (i j) (> (occ (nth g i)) (occ (nth g j))))))
  (define anchor (first occupancy-order))
  (define chosen-color {color})
  (define (active i) {active})
  (define (denominator i) {denominator})
  (define (key i) (append {score} {tail}))
  (define ordered (sort indices (lambda (i j) {comparator})))
  (map (lambda (i) {render}) ordered)))"""


class CachedEvaluator:
    def __init__(self, apply):
        self.apply, self.cache = apply, {}
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None

    def __call__(self, program, grid):
        self.requests += 1
        key = program, packed(grid)
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.last_request = {"program_sha256": sha(program.encode()), "input_sha256": sha(key[1])}
        self.evaluations += 1
        result = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(result)
        return result


def fit_hypothesis(apply, program, train, oracle=None):
    outputs, rejected = [], []
    for index, pair in enumerate(train):
        output = apply(program, pair["input"])
        if oracle is not None and output != oracle(pair["input"]):
            raise ValueError("Independent Python/Racket interpretation mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
            break
    return {"survives_demonstrations": not rejected, "rejected_by_demo_indices": rejected,
            "executed_demo_indices": list(range(len(outputs))), "demo_outputs": outputs}


def source_files():
    paths = {TASK / "generator.py"}
    paths.update(p for p in PARAMETRIC.rglob("*") if p.is_file() and p.suffix in {".py", ".rkt", ".json", ".md"}
                 and not any(part in {"evidence", "__pycache__", "examples"} for part in p.relative_to(PARAMETRIC).parts))
    paths.update((TASK / "tests").glob("*.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def prototype():
    spec = importlib.util.spec_from_file_location("_323fded12174_audit_family", PARAMETRIC / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding = source_files()
    family = prototype()
    report = {"schema": "323fded12174-native-finite-audit-v1", "status": "running",
              "source_files_sha256": binding, "settings": SETTINGS, "jobs": JOBS,
              "extra_rivals": list(RIVALS), "episodes": [], "findings": [],
              "programs": {}, "training_admitted": False, "visibility": "controller_private"}
    out.mkdir(parents=True)
    private = out / "private"
    private.mkdir()
    evaluator = None
    try:
        with _local_imports(RUNTIME, PARAMETRIC):
            apply, identity, bridge = _real_evaluator(RUNTIME)
            evaluator = CachedEvaluator(apply)
            report["racket"] = identity
            try:
                banks, labels = {}, 0
                for seed, demos in JOBS:
                    for settings in SETTINGS:
                        episode = family.generate(seed, settings, demos=demos, queries=4)
                        train, test = deepcopy(episode["train"]), deepcopy(episode["test"])
                        inputs = [pair["input"] for pair in train+test]
                        assert len({packed(grid) for grid in inputs}) == len(inputs), "Repeated episode input"
                        if (seed, demos) in banks:
                            assert inputs == banks[seed, demos], "Input bank leaks parameter setting"
                        banks[seed, demos] = inputs
                        for pair in train+test:
                            info = facts(pair["input"])
                            assert info["unique_anchor"] and info["unique_nonzero_anchor_mode"]
                            assert info["anchor_distinct_colors"] >= 2 and len(info["palette"]) >= 3
                            assert 3 <= info["shape"][0] <= 30 and 5 <= info["shape"][1] <= 30
                            assert all(0 < value < info["shape"][1] for value in info["occupancies"])
                            actual = evaluator(family.program(settings), pair["input"])
                            assert actual == pair["output"] == reference(pair["input"], settings), "Reference meaning mismatch"
                            labels += 1
                        hypotheses = [("declared:"+other["rank_by"], family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        hypotheses += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        fitted = []
                        # No candidate query result contributes to this fitting loop.
                        for name, program, oracle in hypotheses:
                            key = sha(program.encode())
                            report["programs"][key] = program
                            fitted.append({"name": name, "program_sha256": key,
                                           **fit_hypothesis(evaluator, program, train, oracle)})
                        for row, (_, program, oracle) in zip(fitted, hypotheses):
                            row["query_disagreement_indices"] = None
                            if row["survives_demonstrations"]:
                                outputs = [evaluator(program, pair["input"]) for pair in test]
                                assert outputs == [oracle(pair["input"]) for pair in test], "Query interpretation mismatch"
                                disagreements = [i for i, (value, pair) in enumerate(zip(outputs, test)) if value != pair["output"]]
                                row.update(query_outputs=outputs, query_disagreement_indices=disagreements)
                                if disagreements:
                                    report["findings"].append({"seed": seed, "demos": demos, "settings": settings,
                                                               "hypothesis": row["name"], "queries": disagreements})
                        report["episodes"].append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                                                   "fit_frozen_before_query": True, "train": train, "test": test,
                                                   "scene_facts": {"train": [facts(p["input"]) for p in train],
                                                                   "test": [facts(p["input"]) for p in test]},
                                                   "hypotheses": fitted})
                report["reference_label_count"] = labels
                report["matched_inputs_across_settings"] = True
                assert binding == source_files(), "Source changed during audit"
                report["status"] = "passed" if not report["findings"] else "failed"
            finally:
                bridge.close()
    except Exception as error:
        report["status"] = "error"
        report["error"] = f"{type(error).__name__}: {error}"
        if evaluator is not None:
            report["failed_request"] = evaluator.last_request
    if evaluator is not None:
        report["execution"] = {"requests": evaluator.requests, "racket_evaluations": evaluator.evaluations,
                               "cache_hits": evaluator.cache_hits, "successful_cached_results": len(evaluator.cache)}
    report["limits"] = "Six supported episodes and twenty predeclared extra interpretations. Demonstration fits precede candidate query checks; default-equivalent survivors are allowed. Exact fraction semantics use cross products. No universal identifiability, owner acceptance, or training admission."
    (private / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: report.get(key) for key in ("status", "reference_label_count", "execution", "findings", "error")}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    raise SystemExit(run(parser.parse_args().out))
