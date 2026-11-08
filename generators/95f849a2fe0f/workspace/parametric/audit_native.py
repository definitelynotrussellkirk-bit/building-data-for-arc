"""Independent finite audit of normalized XOR and ordered shape subtraction.

The Python oracle and complete Racket candidates are independent of the native
implementation. The bookkeeping framework is an explicit source-only adaptation
of the completed 104734 shape audit; no predecessor imports, evidence, runtime,
environment, or cached module is used. Only first-two-demo labels fit candidates.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
TASK_ID = "95f849a2fe0f"
ASSIGNMENT_ID = "review-db65cf48f1dddb72"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"combine": "xor"}, {"combine": "difference"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "recrop_all", "recrop_rows", "recrop_cols", "union_frame",
    "union", "intersection", "reverse_operands", "observed_coordinates",
    "joint_normalize", "normalize_first_only", "normalize_second_only",
    "position_order", "area_order", "area_descending", "first_shape", "second_shape",
    "solid_box", "color2", "input_colors", "reflect_second", "rotate_second",
    "transpose_second", "bbox_shapes",
)
RIVAL_MEANINGS = {
    "identity": "Return the unchanged input.",
    "recrop_all": "Crop leading blank rows and columns after the selected operation.",
    "recrop_rows": "Crop only leading blank rows after the selected operation.",
    "recrop_cols": "Crop only leading blank columns after the selected operation.",
    "union_frame": "Keep the full normalized union extent, including trailing canceled coordinates.",
    "union": "Emit the normalized union instead of the selected operation.",
    "intersection": "Emit the normalized intersection instead of the selected operation.",
    "reverse_operands": "Swap the lower- and higher-color normalized operands.",
    "observed_coordinates": "Combine observed coordinates without either normalization.",
    "joint_normalize": "Translate both observed shapes by one common origin instead of aligning independently.",
    "normalize_first_only": "Normalize the first shape but leave the second in observed coordinates.",
    "normalize_second_only": "Normalize the second shape but leave the first in observed coordinates.",
    "position_order": "Order the two components by row-major discovery instead of color.",
    "area_order": "Order components by ascending cell count, with discovery-order ties.",
    "area_descending": "Order components by descending cell count, with discovery-order ties.",
    "first_shape": "Return only the normalized lower-color shape.",
    "second_shape": "Return only the normalized higher-color shape.",
    "solid_box": "Fill the entire origin-anchored output rectangle instead of its occupied cells.",
    "color2": "Use fixed output color2 instead of8.",
    "input_colors": "Preserve the contributing operand's input color instead of output color8.",
    "reflect_second": "Reflect the normalized higher-color operand vertically before combining.",
    "rotate_second": "Rotate the normalized higher-color operand clockwise before combining.",
    "transpose_second": "Transpose the normalized higher-color operand before combining.",
    "bbox_shapes": "Replace each normalized operand by its filled bounding rectangle before combining.",
}
EXCLUDED_EQUIVALENT = {
    "always_xor": "Already represented by the declared XOR hypothesis.",
    "always_lower_minus_higher": "Already represented by the declared difference hypothesis.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "max_racket_evaluations": 650,
    "max_evaluation_requests": 1000, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "candidate_totality": "All valid ARC1..30 grids; use the first two ordered nonzero same-color4cc, missing operands are empty, an empty frame returns[[0]].",
}


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def grid_copy(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("Expected a rectangular exact-integer ARC1..30 grid")
    return [row[:] for row in value]


def setting(value):
    if (type(value) is not dict or set(value) != {"combine"}
            or type(value["combine"]) is not str or value["combine"] not in ("xor", "difference")):
        raise ValueError("Expected exactly combine=xor or combine=difference")
    return value["combine"]


def equivalent_aliases(settings):
    return ({name: "XOR is commutative on the admitted exactly-two-component grammar."
             for name in ("reverse_operands", "position_order", "area_order", "area_descending")}
            if setting(settings) == "xor" else {})


def normalize(cells):
    cells = set(cells)
    if not cells:
        return set()
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = []
    while pending:
        start = min(pending)
        pending.remove(start)
        color = grid[start[0]][start[1]]
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in pending and grid[q[0]][q[1]] == color:
                    pending.remove(q)
                    cells.add(q)
                    stack.append(q)
        result.append((color, cells))
    return result


def rectangle(cells):
    return ({(r, c) for r in range(max(r for r, c in cells) + 1)
             for c in range(max(c for r, c in cells) + 1)} if cells else set())


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity":
        return grid
    groups = components(grid)
    if name == "area_order":
        groups.sort(key=lambda item: len(item[1]))
    elif name == "area_descending":
        groups.sort(key=lambda item: -len(item[1]))
    elif name != "position_order":
        groups.sort(key=lambda item: item[0])
    color_a, raw_a = groups[0] if groups else (0, set())
    color_b, raw_b = groups[1] if len(groups) > 1 else (0, set())
    a, b = normalize(raw_a), normalize(raw_b)
    if name == "observed_coordinates":
        a, b = raw_a, raw_b
    elif name == "joint_normalize":
        both = raw_a | raw_b
        if both:
            r0, c0 = min(r for r, c in both), min(c for r, c in both)
            a, b = ({(r - r0, c - c0) for r, c in raw_a}, {(r - r0, c - c0) for r, c in raw_b})
    elif name == "normalize_first_only":
        b = raw_b
    elif name == "normalize_second_only":
        a = raw_a
    elif name == "reverse_operands":
        a, b = b, a
    elif name == "reflect_second":
        b = normalize((r, -c) for r, c in b)
    elif name == "rotate_second":
        b = normalize((c, -r) for r, c in b)
    elif name == "transpose_second":
        b = normalize((c, r) for r, c in b)
    elif name == "bbox_shapes":
        a, b = rectangle(a), rectangle(b)
    cells = a ^ b if mode == "xor" else a - b
    if name == "union": cells = a | b
    if name == "intersection": cells = a & b
    if name == "first_shape": cells = a
    if name == "second_shape": cells = b
    frame = a | b if name == "union_frame" else cells
    if not frame:
        return [[0]]
    r0 = min(r for r, c in frame) if name in ("recrop_all", "recrop_rows") else 0
    c0 = min(c for r, c in frame) if name in ("recrop_all", "recrop_cols") else 0
    def value(r, c):
        if name != "solid_box" and (r, c) not in cells:
            return 0
        if name == "color2": return 2
        if name == "input_colors": return color_a if (r, c) in a else color_b
        return 8
    return [[value(r, c) for c in range(c0, max(c for r, c in frame) + 1)]
            for r in range(r0, max(r for r, c in frame) + 1)]


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    ordered = "(sort found (lambda (x y) (< (obj-color x) (obj-color y))))"
    if name == "position_order": ordered = "found"
    if name in ("area_order", "area_descending"):
        compare = "<" if name == "area_order" else ">"
        ordered = f"(sort found (lambda (x y) ({compare} (length (obj-cells x)) (length (obj-cells y)))))"
    a_expr, b_expr = "(norm raw-a)", "(norm raw-b)"
    if name == "observed_coordinates": a_expr, b_expr = "raw-a", "raw-b"
    elif name == "joint_normalize": a_expr, b_expr = "(shift raw-a) ", "(shift raw-b)"
    elif name == "normalize_first_only": b_expr = "raw-b"
    elif name == "normalize_second_only": a_expr = "raw-a"
    elif name == "reverse_operands": a_expr, b_expr = "(norm raw-b)", "(norm raw-a)"
    elif name == "reflect_second": b_expr = "(norm (map (lambda (p) (list (first p) (- (second p)))) raw-b))"
    elif name == "rotate_second": b_expr = "(norm (map (lambda (p) (list (second p) (- (first p)))) raw-b))"
    elif name == "transpose_second": b_expr = "(norm (map (lambda (p) (list (second p) (first p))) raw-b))"
    elif name == "bbox_shapes": a_expr, b_expr = "(box (norm raw-a))", "(box (norm raw-b))"
    cells = ("(append (filter (lambda (p) (not (member? p b))) a) (filter (lambda (p) (not (member? p a))) b))"
             if mode == "xor" else "(filter (lambda (p) (not (member? p b))) a)")
    if name == "union": cells = "(remove-duplicates (append a b))"
    if name == "intersection": cells = "(filter (lambda (p) (member? p b)) a)"
    if name == "first_shape": cells = "a"
    if name == "second_shape": cells = "b"
    frame = "(append a b)" if name == "union_frame" else "cells"
    r0 = "(apply min (map first frame))" if name in ("recrop_all", "recrop_rows") else "0"
    c0 = "(apply min (map second frame))" if name in ("recrop_all", "recrop_cols") else "0"
    present = "#t" if name == "solid_box" else "(member? p cells)"
    color = "2" if name == "color2" else "8"
    if name == "input_colors": color = "(if (member? p a) color-a color-b)"
    return f"""(rule! (let ()
  (define (norm cells) (if (empty? cells) '() (sort (normalize-cells cells) cell<)))
  (define (box cells)
    (if (empty? cells) '()
      (append* (map (lambda (r) (map (lambda (c) (list r c))
          (range (+ 1 (apply max (map second cells))))))
          (range (+ 1 (apply max (map first cells))))))))
  (define found (objects g 0))
  (define ordered {ordered})
  (define raw-a (if (empty? ordered) '() (obj-cells (first ordered))))
  (define raw-b (if (< (length ordered) 2) '() (obj-cells (second ordered))))
  (define color-a (if (empty? ordered) 0 (obj-color (first ordered))))
  (define color-b (if (< (length ordered) 2) 0 (obj-color (second ordered))))
  (define all-cells (append raw-a raw-b))
  (define (shift cells)
    (if (empty? all-cells) '()
      (let ((r0 (apply min (map first all-cells))) (c0 (apply min (map second all-cells))))
        (map (lambda (p) (list (- (first p) r0) (- (second p) c0))) cells))))
  (define a {a_expr})
  (define b {b_expr})
  (define cells {cells})
  (define frame {frame})
  (if (empty? frame) '((0))
    (let* ((r0 {r0}) (c0 {c0})
           (h (- (+ 1 (apply max (map first frame))) r0))
           (w (- (+ 1 (apply max (map second frame))) c0)))
      (grid-from-fn h w (lambda (r c)
        (let ((p (list (+ r r0) (+ c c0)))) (if {present} {color} 0))))))))"""

class CachedEvaluator:
    """Exact executable/input cache with an append-only request/execution ledger."""
    def __init__(self, apply, *, ledger=None):
        self.apply, self.ledger = apply, ledger
        self.cache, self.programs, self.records = {}, {}, []
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None
        self.context = {}
        self.started = time.monotonic()

    def __call__(self, program, grid):
        if self.requests >= LIMITS["max_evaluation_requests"]:
            raise RuntimeError("Finite evaluation request budget exhausted")
        if time.monotonic() - self.started > LIMITS["wall_seconds_checked_between_calls"]:
            raise TimeoutError("Finite audit wall budget exhausted between calls")
        value = grid_copy(grid)
        program_hash = sha(program.encode())
        self.programs[program_hash] = program
        self.requests += 1
        key = program, packed(value)
        row = {"request_index": self.requests, "program_sha256": program_hash,
               "input_sha256": sha(key[1]), "input": value,
               "context": deepcopy(self.context), "cache_hit": key in self.cache}
        self.last_request = deepcopy(row)
        try:
            if key in self.cache:
                self.cache_hits += 1
                output, execution_index = self.cache[key]
            else:
                if self.evaluations >= LIMITS["max_racket_evaluations"]:
                    raise RuntimeError("Finite protected evaluation budget exhausted")
                self.evaluations += 1
                execution_index = self.evaluations
                row["execution_index"] = execution_index
                output = grid_copy(self.apply(program, deepcopy(value)))
                self.cache[key] = deepcopy(output), execution_index
            row.update(status="ok", execution_index=execution_index,
                       output=deepcopy(output), output_sha256=sha(packed(output)))
            return deepcopy(output)
        except Exception as error:
            row.update(status="error", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            self.records.append(row)
            if self.ledger is not None:
                self.ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
                self.ledger.flush()


def fit_hypothesis(apply, program, demonstrations, oracle=None):
    """Use exactly the first two demonstrations, never later demonstrations."""
    if len(demonstrations) < 2:
        raise ValueError("Teaching audit requires two demonstrations")
    outputs, rejected = [], []
    for index, pair in enumerate(demonstrations[:2]):
        output = grid_copy(apply(program, pair["input"]))
        if oracle is not None and output != oracle(pair["input"]):
            raise ValueError("Independent Python/Racket candidate meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
    return {"survives_demonstrations": not rejected,
            "executed_demo_indices": [0, 1], "rejected_by_demo_indices": rejected,
            "demo_outputs": outputs}


def source_files():
    paths = {TASK / "generator.py"}
    paths.update(path for path in HOME.iterdir() if path.is_file()
                 and path.suffix in {".py", ".rkt", ".json", ".md"})
    paths.update((TASK / "tests").glob("*.py"))
    return {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sorted(paths)}


def runtime_files():
    paths = {ROOT / "src/arcpuzzles/parametric_worker.py", ROOT / "shared/tools/comment_solutions.py",
             RUNTIME / "puzzle_generators/rule_wrap.py"}
    paths.update(path for path in (RUNTIME / "arc_repl").rglob("*")
                 if path.is_file() and path.suffix in {".py", ".rkt"})
    return {path.relative_to(ROOT).as_posix(): sha(path.read_bytes()) for path in sorted(paths)}


def load_family():
    spec = importlib.util.spec_from_file_location("_95f849a2fe0f_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid, output):
    groups = sorted(components(grid), key=lambda item: item[0])
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
            "component_count": len(groups), "occupied_cells": sum(len(cells) for _, cells in groups),
            "components": [{"color": color, "size": len(cells), "normalized_cells": sorted(normalize(cells))}
                           for color, cells in groups],
            "input_sha256": sha(packed(grid)), "output_sha256": sha(packed(output))}


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding, runtime_before = source_files(), runtime_files()
    out.mkdir(parents=True)
    private = out / "private"
    private.mkdir()
    for name, digest in binding.items():
        content = (ROOT / name).read_bytes()
        if sha(content) != digest:
            raise RuntimeError("Source changed while taking the initial snapshot: " + name)
        destination = out / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    report = {"schema": "95f849a2fe0f-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Four episodes only; all6+4 intended labels checked independently. Exactly first2 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
    evaluator = bridge = None
    started = time.monotonic()
    try:
        family = load_family()
        with (private / "executions.jsonl").open("x") as ledger:
            with _local_imports(RUNTIME, HOME):
                apply, identity, bridge = _real_evaluator(RUNTIME)
                report["racket_before"] = identity
                evaluator = CachedEvaluator(apply, ledger=ledger)
                banks = {}
                for seed in SEEDS:
                    for settings in SETTINGS:
                        mode = setting(settings)
                        episode = family.generate(seed, deepcopy(settings), demos=6, queries=4)
                        selected_program = family.program(settings)
                        if episode.get("program_solution") != selected_program:
                            raise ValueError("Episode program_solution differs from selected program")
                        train, test = deepcopy(episode["train"]), deepcopy(episode["test"])
                        if len(train) != 6 or len(test) != 4:
                            raise ValueError("Episode omitted requested demonstrations or queries")
                        for pair in train + test:
                            grid_copy(pair["input"])
                            grid_copy(pair["output"])
                        inputs = [pair["input"] for pair in train + test]
                        if len({packed(grid) for grid in inputs}) != 10:
                            raise ValueError("Repeated input inside an episode")
                        if seed in banks and inputs != banks[seed]:
                            raise ValueError("Input bank depends on the semantic setting")
                        banks[seed] = deepcopy(inputs)
                        candidates = [("declared:combine=" + other["combine"], family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        candidates += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        row = {"seed": seed, "settings": deepcopy(settings), "train": train, "test": test,
                               "fit_demo_indices": [0, 1], "label_checks": [], "hypotheses": []}
                        report["episodes"].append(row)
                        # Fit receives no later-demo or query labels.
                        for name, program, oracle in candidates:
                            evaluator.context = {"phase": "fit_first_two_demonstrations", "seed": seed,
                                                 "settings": settings, "hypothesis": name}
                            row["hypotheses"].append({"name": name, "program_sha256": sha(program.encode()),
                                                      **fit_hypothesis(evaluator, program, train[:2], oracle)})
                        survivors = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivors_frozen_before_query"] = deepcopy(survivors)
                        row["survivor_set_sha256_before_queries"] = sha(packed(survivors))
                        intended_name = "declared:combine=" + mode
                        row["extra_survivors"] = [name for name in survivors if name != intended_name]
                        aliases = equivalent_aliases(settings)
                        row["equivalent_survivor_aliases"] = {name: aliases[name] for name in row["extra_survivors"] if name in aliases}
                        row["unclassified_extra_survivors"] = [name for name in row["extra_survivors"] if name not in aliases]
                        if intended_name not in survivors:
                            raise ValueError("The intended program was refuted by its own teaching labels")
                        for split, pairs in (("train", train), ("test", test)):
                            for index, pair in enumerate(pairs):
                                evaluator.context = {"phase": "verify_all_intended_labels", "seed": seed,
                                                     "settings": settings, "split": split, "index": index}
                                actual = evaluator(selected_program, pair["input"])
                                independent = reference(pair["input"], settings)
                                check = {"split": split, "index": index,
                                         "racket_output": actual, "python_output": independent,
                                         "provided_output": pair["output"],
                                         "matched": actual == independent == pair["output"],
                                         "facts": facts(pair["input"], independent)}
                                row["label_checks"].append(check)
                                if not check["matched"]:
                                    raise ValueError("Native label, independent Python, and protected Racket disagree")
                                report["reference_label_count"] += 1
                        # Query labels score every frozen survivor and can never refit it.
                        for fitted, (name, program, oracle) in zip(row["hypotheses"], candidates):
                            fitted["query_outputs"] = None
                            fitted["query_disagreement_indices"] = None
                            if not fitted["survives_demonstrations"]:
                                continue
                            outputs = []
                            for index, pair in enumerate(test):
                                evaluator.context = {"phase": "score_frozen_survivor_queries", "seed": seed,
                                                     "settings": settings, "hypothesis": name, "index": index}
                                actual = evaluator(program, pair["input"])
                                if actual != oracle(pair["input"]):
                                    raise ValueError("Independent Python/Racket survivor query meaning mismatch")
                                outputs.append(actual)
                            disagreements = [index for index, (actual, pair) in enumerate(zip(outputs, test))
                                             if actual != pair["output"]]
                            fitted["query_outputs"] = outputs
                            fitted["query_disagreement_indices"] = disagreements
                            if disagreements:
                                report["findings"].append({"seed": seed, "settings": deepcopy(settings),
                                                           "hypothesis": name,
                                                           "query_disagreement_indices": disagreements,
                                                           "first_witness": deepcopy(test[disagreements[0]]),
                                                           "rival_output": outputs[disagreements[0]]})
                        after = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivor_set_sha256_after_queries"] = sha(packed(after))
                        if after != survivors:
                            raise ValueError("Query scoring altered the teaching survivor set")
                report["matched_inputs_across_settings"] = True
                after_identity = bridge.runtime_identity
                report["racket_after"] = {key: after_identity[key] for key in identity}
                if report["racket_after"] != report["racket_before"]:
                    raise ValueError("Protected runtime identity changed during the audit")
                report["status"] = "passed" if not report["findings"] else "failed"
    except Exception as error:
        report["status"] = "error"
        report["error"] = f"{type(error).__name__}: {error}"
        if evaluator is not None:
            report["failed_request"] = evaluator.last_request
    finally:
        if bridge is not None:
            try:
                final_identity = bridge.runtime_identity
                report.setdefault("racket_after", {key: final_identity[key] for key in report.get("racket_before", {})})
            finally:
                bridge.close()
        report["source_files_sha256_after"] = source_files()
        report["runtime_files_sha256_after"] = runtime_files()
        report["source_unchanged"] = report["source_files_sha256_after"] == binding
        report["runtime_sources_unchanged"] = report["runtime_files_sha256_after"] == runtime_before
        if not report["source_unchanged"] or not report["runtime_sources_unchanged"]:
            report["status"] = "error"
            report["source_binding_error"] = "Source or runtime files changed during the audit"
        if evaluator is not None:
            report["programs"] = evaluator.programs
            report["execution"] = {"requests": evaluator.requests, "racket_evaluations": evaluator.evaluations,
                                   "cache_hits": evaluator.cache_hits, "successful_cached_results": len(evaluator.cache),
                                   "request_records": len(evaluator.records), "ledger": "executions.jsonl",
                                   "ledger_sha256": sha((private / "executions.jsonl").read_bytes())}
        report["elapsed_seconds"] = time.monotonic() - started
        (private / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({key: report.get(key) for key in ("status", "reference_label_count", "execution", "findings", "error")}))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    raise SystemExit(run(options.out))


if __name__ == "__main__":
    main()


