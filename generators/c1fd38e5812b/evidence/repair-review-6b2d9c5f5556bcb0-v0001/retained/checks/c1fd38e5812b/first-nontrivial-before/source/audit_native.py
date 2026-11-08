"""Independent, protected semantic-rival audit for logical-grid component crops.

Fit every hypothesis on demonstrations before reading query labels. Execution
errors fail closed. All-color components include zero; cropped boxes preserve
their original interior colors. The finite rivals do not establish uniqueness.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
TASK_ID = "c1fd38e5812b"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


SETTINGS = ({"view": "compressed"}, {"view": "largest_component_crop"})
JOBS = ((0, 3), (17, 3), (101, 6))
RIVALS = ("physical_area", "bbox_area", "color_total", "connectivity8",
          "ignore_zero", "solid_bbox", "isolate_component", "first_component",
          "last_component", "min_color", "max_color", "reverse_tie",
          "tie_min_color", "tie_max_color", "fixed_stride", "coupled_cols", "coupled_rows", "global_dedup")


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def setting(value):
    if (type(value) is not dict or set(value) != {"view"}
            or type(value["view"]) is not str
            or value["view"] not in ("compressed", "largest_component_crop")):
        raise ValueError("Expected exactly one declared view setting")
    return value["view"]


def compression(grid):
    grid = _grid(grid)
    rs = [0] + [r for r in range(1, len(grid)) if grid[r] != grid[r-1]]
    cs = [0] + [c for c in range(1, len(grid[0]))
                if any(row[c] != row[c-1] for row in grid)]
    heights = [b-a for a, b in zip(rs, rs[1:]+[len(grid)])]
    widths = [b-a for a, b in zip(cs, cs[1:]+[len(grid[0])])]
    return [[grid[r][c] for c in cs] for r in rs], heights, widths


def compress(grid):
    return compression(grid)[0]


def expand(logical, heights, widths):
    return [[value for value, width in zip(row, widths) for _ in range(width)]
            for row, height in zip(logical, heights) for _ in range(height)]


def components(grid, connectivity=4):
    pending = {(r, c) for r, row in enumerate(grid) for c in range(len(row))}
    result = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        pending.remove(start)
        stack, cells = [start], [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (connectivity == 4 and abs(dr)+abs(dc) != 1):
                        continue
                    point = r+dr, c+dc
                    if point in pending and grid[point[0]][point[1]] == color:
                        pending.remove(point)
                        cells.append(point)
                        stack.append(point)
        result.append(tuple(sorted(cells)))
    return result


def bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def component_key(cells, grid):
    return (*bbox(cells), grid[cells[0][0]][cells[0][1]])


def crop(grid, cells, render="original"):
    r1, c1, r2, c2 = bbox(cells)
    color = grid[cells[0][0]][cells[0][1]]
    selected = set(cells)
    return [[color if render == "solid_bbox" else
             (grid[r][c] if (render != "isolate_component" or (r, c) in selected) else 0)
             for c in range(c1, c2+1)] for r in range(r1, r2+1)]


def _logical_for(grid, name):
    logical, heights, widths = compression(grid)
    rs, cs = [0], [0]
    for span in heights[:-1]: rs.append(rs[-1]+span)
    for span in widths[:-1]: cs.append(cs[-1]+span)
    if name == "fixed_stride" or (name == "coupled_rows" and len(set(widths)) == 1):
        rs = list(range(0, len(grid), heights[0]))
    if name == "fixed_stride" or (name == "coupled_cols" and len(set(heights)) == 1):
        cs = list(range(0, len(grid[0]), widths[0]))
    if name == "global_dedup":
        rows = list(dict.fromkeys(map(tuple, grid)))
        cols = list(dict.fromkeys(zip(*rows)))
        logical = [list(row) for row in zip(*cols)]
    elif name in {"fixed_stride", "coupled_cols", "coupled_rows"}:
        logical = [[grid[r][c] for c in cs] for r in rs]
    return logical, heights, widths


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    grid = _grid(grid)
    logical, heights, widths = _logical_for(grid, name)
    if mode == "compressed":
        return logical
    groups = components(logical, 8 if name == "connectivity8" else 4)
    if name == "ignore_zero":
        groups = [cells for cells in groups if logical[cells[0][0]][cells[0][1]] != 0]
    if not groups:
        return logical
    def key(cells):
        tail = component_key(cells, logical)
        color = tail[-1]
        if name == "physical_area":
            return (-sum(heights[r]*widths[c] for r, c in cells), *tail)
        if name == "bbox_area":
            r1, c1, r2, c2 = bbox(cells)
            return (-(r2-r1+1)*(c2-c1+1), *tail)
        if name == "color_total":
            return (-sum(value == color for row in logical for value in row), -len(cells), *tail)
        if name in {"first_component", "last_component"}:
            return tuple((-value if name == "last_component" else value) for value in tail)
        if name in {"min_color", "max_color"}:
            return ((-color if name == "max_color" else color), -len(cells), *tail)
        if name in {"tie_min_color", "tie_max_color"}:
            return (-len(cells), (-color if name == "tie_max_color" else color), *tail)
        if name == "reverse_tie":
            return (-len(cells), *(-value for value in tail))
        return (-len(cells), *tail)
    chosen = min(groups, key=key)
    return crop(logical, chosen, name)


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def facts(grid):
    logical, heights, widths = compression(grid)
    groups = components(logical)
    ranked = sorted(groups, key=lambda cells: (-len(cells), *component_key(cells, logical)))
    return {"input_shape": [len(grid), len(grid[0])], "logical_shape": [len(logical), len(logical[0])],
            "row_spans": heights, "column_spans": widths,
            "row_spans_uniform": len(set(heights)) == 1, "column_spans_uniform": len(set(widths)) == 1,
            "component_count": len(groups), "components": [
                {"color": logical[cells[0][0]][cells[0][1]], "logical_area": len(cells),
                 "bbox": list(bbox(cells)),
                 "physical_area": sum(heights[r]*widths[c] for r, c in cells)} for cells in ranked],
            "winner": {"cells": [list(p) for p in ranked[0]], "bbox": list(bbox(ranked[0])),
                       "color": logical[ranked[0][0][0]][ranked[0][0][1]], "logical_area": len(ranked[0])},
            "logical_grid": logical}


def rival_program(settings, name):
    """Complete standalone Racket, with scoring independent of family helpers."""
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown rival: " + name)
    row_indices = "rs"
    col_indices = "cs"
    if name == "fixed_stride":
        row_indices, col_indices = "(range 0 (rows g) (first hs))", "(range 0 (cols g) (first ws))"
    elif name == "coupled_rows":
        row_indices = "(if (all? (lambda (v) (= v (first ws))) ws) (range 0 (rows g) (first hs)) rs)"
    elif name == "coupled_cols":
        col_indices = "(if (all? (lambda (v) (= v (first hs))) hs) (range 0 (cols g) (first ws)) cs)"
    projection = "(transpose (remove-duplicates (transpose (remove-duplicates g))))" if name == "global_dedup" else \
        "(grid-from-fn (length rpick) (length cpick) (lambda (r c) (at g (nth rpick r) (nth cpick c))))"
    tail = "(append (obj-bbox o) (list (obj-color o)))"
    key = f"(cons (- (obj-size o)) {tail})"
    if name == "physical_area":
        key = f"(cons (- (sum-list (map (lambda (p) (* (nth hs (first p)) (nth ws (second p)))) (obj-cells o)))) {tail})"
    elif name == "bbox_area":
        key = f"(cons (- (* (obj-h o) (obj-w o))) {tail})"
    elif name == "color_total":
        key = f"(append (list (- (count-if (lambda (v) (= v (obj-color o))) (apply append logical))) (- (obj-size o))) {tail})"
    elif name in {"first_component", "last_component"}:
        key = tail if name == "first_component" else f"(map - {tail})"
    elif name in {"min_color", "max_color"}:
        key = f"(append (list {'(- (obj-color o))' if name == 'max_color' else '(obj-color o)'} (- (obj-size o))) {tail})"
    elif name in {"tie_min_color", "tie_max_color"}:
        key = f"(append (list (- (obj-size o)) {'(- (obj-color o))' if name == 'tie_max_color' else '(obj-color o)'}) {tail})"
    elif name == "reverse_tie":
        key = f"(cons (- (obj-size o)) (map - {tail}))"
    groups = f"({'objects-8' if name == 'connectivity8' else 'objects'} logical {'0' if name == 'ignore_zero' else '-1'})"
    render = "(crop-object logical chosen)"
    if name == "solid_bbox":
        render = "(grid-from-fn (obj-h chosen) (obj-w chosen) (lambda (r c) (obj-color chosen)))"
    elif name == "isolate_component":
        render = "(grid-from-fn (obj-h chosen) (obj-w chosen) (lambda (r c) (let ((p (list (+ r (obj-r1 chosen)) (+ c (obj-c1 chosen))))) (if (member p (obj-cells chosen)) (obj-color chosen) 0))))"
    finish = "logical" if mode == "compressed" else f"(if (empty? os) logical (let ((chosen (first (sort os (lambda (a b) (key<? (key a) (key b))))))) {render}))"
    return f"""(rule! (lambda (g)
  (define (key<? a b)
    (cond ((empty? a) #f) ((< (first a) (first b)) #t)
          ((> (first a) (first b)) #f) (else (key<? (rest a) (rest b)))))
  (define rs (cons 0 (filter (lambda (r) (not (equal? (nth g r) (nth g (- r 1))))) (range 1 (rows g)))))
  (define cs (cons 0 (filter (lambda (c) (any? (lambda (r) (!= (at g r c) (at g r (- c 1)))) (range (rows g)))) (range 1 (cols g)))))
  (define hs (map - (append (rest rs) (list (rows g))) rs))
  (define ws (map - (append (rest cs) (list (cols g))) cs))
  (define rpick {row_indices})
  (define cpick {col_indices})
  (define logical {projection})
  (define os {groups})
  (define (key o) {key})
  {finish}))"""


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
        answer = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(answer)
        return answer


def fit_hypothesis(apply, program, train, oracle=None):
    outputs, rejected = [], []
    for index, pair in enumerate(train):
        output = apply(program, pair["input"])
        if oracle is not None and output != oracle(pair["input"]):
            raise ValueError("Independent Python/Racket candidate meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
            break
    return {"survives_demonstrations": not rejected, "rejected_by_demo_indices": rejected,
            "executed_demo_indices": list(range(len(outputs))), "demo_outputs": outputs}


def source_files():
    paths = {TASK / "generator.py"}
    paths.update(p for p in HOME.rglob("*") if p.is_file() and p.suffix in {".py", ".rkt", ".json", ".md"}
                 and not any(part in {"evidence", "__pycache__", "examples"} for part in p.relative_to(HOME).parts))
    paths.update((TASK / "tests").glob("*.py"))
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(paths)}


def prototype():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("_c1fd38e5812b_audit_family", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def uniform_teaching_witness(family, apply, identity, binding):
    """Same logical teaching roles, but uniform expansion hides physical weighting."""
    settings = {"view": "largest_component_crop"}
    query = replacement = None
    for seed in (0, 17, 101):
        episode = family.generate(seed, settings, demos=3, queries=4)
        query = next((pair for pair in episode["test"]
                      if reference(pair["input"], settings) != rival_reference(pair["input"], settings, "physical_area")), None)
        replacement = next(((index, pair) for index, pair in enumerate(episode["train"])
                            if reference(pair["input"], settings) != rival_reference(pair["input"], settings, "physical_area")), None)
        if query is not None and replacement is not None:
            break
    if query is None or replacement is None:
        return {"status": "not_available", "reason": "Seeds0/17/101 lack both a demo and query physical-area reversal"}
    weak = []
    for pair in episode["train"]:
        logical = compress(pair["input"])
        grid = expand(logical, [2]*len(logical), [2]*len(logical[0]))
        weak.append({"input": grid, "output": apply(family.program(settings), grid)})
    programs = {"reference": family.program(settings), "compressed": family.program({"view": "compressed"}),
                "physical_area": rival_program(settings, "physical_area")}
    hypotheses = {name: fit_hypothesis(apply, program, weak) for name, program in programs.items()}
    assert hypotheses["reference"]["survives_demonstrations"]
    assert hypotheses["physical_area"]["survives_demonstrations"]
    assert not hypotheses["compressed"]["survives_demonstrations"]
    outputs = {name: apply(programs[name], query["input"]) for name in ("reference", "physical_area")}
    assert outputs["reference"] != outputs["physical_area"]
    index, repair_pair = replacement
    repair_reference = apply(programs["reference"], repair_pair["input"])
    repair_rival = apply(programs["physical_area"], repair_pair["input"])
    assert repair_reference != repair_rival
    assert compress(repair_pair["input"]) == compress(weak[index]["input"])
    repaired = deepcopy(weak)
    repaired[index] = {"input": repair_pair["input"], "output": repair_reference}
    assert len({packed(p["input"]) for p in repaired+[query]}) == 4
    return {"schema": "c1fd38e5812b-physical-weight-teaching-witness-v1",
            "status": "reproduced_expected_incremental_gate_failure", "seed": seed, "settings": settings,
            "source_files_sha256": binding, "racket": identity, "programs": programs,
            "train": weak, "fit_frozen_before_query": True, "hypotheses": hypotheses,
            "query": query, "query_outputs": outputs, "query_facts": facts(query["input"]),
            "repair": {"replace_demo_index": index, "pair": repaired[index], "rival_output": repair_rival,
                       "same_logical_teaching_role": True, "demonstration_count_unchanged": 3,
                       "query_remains_novel": True},
            "scope": "Constructed uniform-expansion lesson, not emitted by the final teaching sampler. Declared settings distinguish; an extra physical-area rival does not. One nonuniform replacement repairs it.",
            "training_admitted": False, "visibility": "controller_private"}


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding = source_files()
    family = prototype()
    report = {"schema": "c1fd38e5812b-native-finite-audit-v1", "status": "running",
              "source_files_sha256": binding, "settings": SETTINGS, "jobs": JOBS,
              "extra_rivals": list(RIVALS), "episodes": [], "findings": [],
              "programs": {}, "training_admitted": False, "visibility": "controller_private"}
    out.mkdir(parents=True)
    private = out / "private"
    private.mkdir()
    evaluator = None
    try:
        with _local_imports(RUNTIME, HOME):
            apply, identity, bridge = _real_evaluator(RUNTIME)
            evaluator = CachedEvaluator(apply)
            report["racket"] = identity
            try:
                banks = {}
                label_count = 0
                for seed, demos in JOBS:
                    for settings in SETTINGS:
                        mode = setting(settings)
                        episode = family.generate(seed, settings, demos=demos, queries=4)
                        train, test = deepcopy(episode["train"]), deepcopy(episode["test"])
                        inputs = [pair["input"] for pair in train+test]
                        assert len({packed(grid) for grid in inputs}) == len(inputs)
                        if (seed, demos) in banks:
                            assert inputs == banks[seed, demos], "Inputs leak the parameter setting"
                        banks[seed, demos] = inputs
                        selected_program = family.program(settings)
                        for pair in train+test:
                            actual = evaluator(selected_program, pair["input"])
                            assert actual == pair["output"] == reference(pair["input"], settings), "Native/Python reference mismatch"
                            label_count += 1
                        hypotheses = [("declared:"+other["view"], family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        hypotheses += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        fitted = []
                        # This entire loop sees only demonstrations. Query decisions occur later.
                        for name, program, oracle in hypotheses:
                            program_hash = sha(program.encode())
                            report["programs"][program_hash] = program
                            fitted.append({"name": name, "program_sha256": program_hash,
                                           **fit_hypothesis(evaluator, program, train, oracle)})
                        for row, (_, program, oracle) in zip(fitted, hypotheses):
                            row["query_disagreement_indices"] = None
                            if row["survives_demonstrations"]:
                                outputs = []
                                for pair in test:
                                    value = evaluator(program, pair["input"])
                                    assert value == oracle(pair["input"]), "Independent query meaning mismatch"
                                    outputs.append(value)
                                row["query_outputs"] = outputs
                                disagreements = [i for i, (value, pair) in enumerate(zip(outputs, test)) if value != pair["output"]]
                                row["query_disagreement_indices"] = disagreements
                                if disagreements:
                                    report["findings"].append({"seed": seed, "demos": demos, "settings": settings,
                                                               "hypothesis": row["name"], "queries": disagreements})
                        report["episodes"].append({"seed": seed, "settings": settings, "demos": demos, "queries": 4,
                                                   "fit_frozen_before_query": True, "train": train, "test": test,
                                                   "scene_facts": {"train": [facts(p["input"]) for p in train],
                                                                   "test": [facts(p["input"]) for p in test]},
                                                   "hypotheses": fitted})
                report["reference_label_count"] = label_count
                report["matched_inputs_across_settings"] = True
                before = evaluator.evaluations
                witness = uniform_teaching_witness(family, evaluator, identity, binding)
                witness["additional_racket_evaluations"] = evaluator.evaluations-before
                (private/"before-witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True)+"\n")
                report["before_witness"] = {"path": "before-witness.json", "status": witness["status"],
                                            "sha256": sha((private/"before-witness.json").read_bytes())}
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
    report["limits"] = "Six supported episodes, eighteen extra finite interpretations; demonstration fits precede candidate query checks. Canonical full-row/full-column compression agrees with border-run sampling on the emitted exact expansion grammar. Equivalent survivors are allowed. No universal identifiability, owner acceptance or training admission."
    (private/"audit.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: report.get(key) for key in ("status", "reference_label_count", "execution", "findings", "error")}))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.out))


if __name__ == "__main__":
    main()
