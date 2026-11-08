"""Independent finite audit of D4 prototype matching and transformation transfer.

Python point geometry and complete Racket hypotheses are independent of the
native implementation. Bookkeeping is an explicit source copy of this packet's
completed XOR audit, with a four-demo fit boundary. No sibling imports, prior
evidence, borrowed runtime or environment are used.
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
TASK_ID = "a51a8e285ce9"
ASSIGNMENT_ID = "review-db65cf48f1dddb72"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

NAMES = ("id", "rot90", "rot180", "rot270", "flip-h", "flip-v", "transpose", "anti-transpose")
SETTINGS = ({"mode": "prototype"}, {"mode": "transfer"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "fixed_match0", "fixed_match1", "rotations_match0", "rotations_match1",
    "reflections_match0", "reflections_match1", "query_display", "other_display", "inverse_transfer",
    "fixed_rot90", "fixed_rot180", "fixed_rot270", "fixed_flip-h", "fixed_flip-v",
    "fixed_transpose", "fixed_anti-transpose", "prototype_color", "color8", "color2",
    "ignore_color8", "area_match0", "area_match1", "bbox_match0", "bbox_match1",
    "full_panel", "canonical_output",
)
RIVAL_MEANINGS = {
    "identity": "Return the original input.",
    "fixed_match0": "Always identify prototype0 as matched; transfer uses an inferred code or identity fallback.",
    "fixed_match1": "Always identify prototype1 as matched; transfer uses an inferred code or identity fallback.",
    **{f"{kind}_match{fallback}": f"Identify and infer using {kind} only; if no match choose prototype{fallback}, and if no code choose identity."
       for kind in ("rotations", "reflections") for fallback in (0, 1)},
    "query_display": "Emit the query's observed tight crop.",
    "other_display": "Emit the unmatched prototype's displayed crop, with no inferred transform.",
    "inverse_transfer": "Apply the inverse inferred matching transform to the unmatched prototype.",
    **{"fixed_" + name: "Apply fixed transform " + name + " to the unmatched prototype." for name in NAMES[1:]},
    "prototype_color": "Use the rendered prototype's input color rather than the query color.",
    "color8": "Use fixed output color8.",
    "color2": "Use fixed output color2.",
    "ignore_color8": "Discard color8 inside the panels as though it were separator/background.",
    **{f"{kind}_match{fallback}": f"Match by {kind} only; ambiguous or absent matches select prototype{fallback}."
       for kind in ("area", "bbox") for fallback in (0, 1)},
    "full_panel": "Render in the full source panel dimensions rather than a tight support crop.",
    "canonical_output": "Replace the correct output support by its numeric-coordinate D4 minimum.",
}
EXCLUDED_EQUIVALENT = {
    "always_prototype": "Already represented by the declared prototype hypothesis.",
    "always_correct_transfer": "Already represented by the declared transfer hypothesis.",
    "fixed_identity_to_other": "Exactly other_display.",
    "correct_transform_to_matched": "Exactly query_display on the admitted unique-match grammar.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 4,
    "queries_per_episode": 4, "max_racket_evaluations": 1400,
    "max_evaluation_requests": 1800, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "candidate_totality": "All valid ARC1..30 grids; width<5 returns[[0]], missing matches/codes use declared fallback/identity, empty support yields[[0]].",
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
        raise ValueError("Expected an exact-integer rectangular ARC1..30 grid")
    return [row[:] for row in value]


def setting(value):
    if (type(value) is not dict or set(value) != {"mode"}
            or type(value["mode"]) is not str or value["mode"] not in ("prototype", "transfer")):
        raise ValueError("Expected exactly mode=prototype or mode=transfer")
    return value["mode"]


def equivalent_aliases(settings):
    setting(settings)
    return {}


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transform(cells, name):
    maps = {
        "id": lambda r, c: (r, c), "rot90": lambda r, c: (c, -r),
        "rot180": lambda r, c: (-r, -c), "rot270": lambda r, c: (-c, r),
        "flip-h": lambda r, c: (r, -c), "flip-v": lambda r, c: (-r, c),
        "transpose": lambda r, c: (c, r), "anti-transpose": lambda r, c: (-c, -r),
    }
    return normalize(maps[name](r, c) for r, c in cells)


def inverse(name):
    return {"rot90": "rot270", "rot270": "rot90"}.get(name, name)


def dimensions(cells):
    return (max(r for r, c in cells) + 1, max(c for r, c in cells) + 1) if cells else (0, 0)


def panel_data(grid, ignore8=False):
    width = (len(grid[0]) - 2) // 3
    result = []
    for i in range(3):
        left = i * (width + 1)
        occupied = [(r, c, grid[r][left + c]) for r in range(len(grid)) for c in range(width)
                    if grid[r][left + c] and not (ignore8 and grid[r][left + c] == 8)]
        result.append((normalize((r, c) for r, c, color in occupied), occupied[0][2] if occupied else 0))
    return result, width


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity": return grid
    if len(grid[0]) < 5: return [[0]]
    panels, pw = panel_data(grid, name == "ignore_color8")
    prototypes, query = [p[0] for p in panels[:2]], panels[2][0]
    names = NAMES[:4] if name.startswith("rotations_") else NAMES[4:] if name.startswith("reflections_") else NAMES
    fallback = int(name[-1]) if name.endswith(("match0", "match1")) else 0
    if name.startswith("area_"):
        matches = [i for i, p in enumerate(prototypes) if len(p) == len(query)]
    elif name.startswith("bbox_"):
        matches = [i for i, p in enumerate(prototypes) if sorted(dimensions(p)) == sorted(dimensions(query))]
    else:
        matches = [i for i, p in enumerate(prototypes) if query in [transform(p, code) for code in names]]
    ambiguous_heuristic = name.startswith(("area_", "bbox_")) and len(matches) != 1
    matched = fallback if name.startswith("fixed_match") or not matches or ambiguous_heuristic else matches[0]
    code = next((code for code in names if transform(prototypes[matched], code) == query), "id")
    source_index = matched if mode == "prototype" else 1 - matched
    output = prototypes[matched] if mode == "prototype" else transform(prototypes[1 - matched], code)
    if name == "query_display": output = query
    if name == "other_display": output = prototypes[1 - matched]
    if name == "inverse_transfer": output = transform(prototypes[1 - matched], inverse(code))
    if name.startswith("fixed_") and not name.startswith("fixed_match"):
        output = transform(prototypes[1 - matched], name[len("fixed_"):])
    if name == "canonical_output": output = min(transform(output, code) for code in NAMES)
    color = panels[source_index][1] if name == "prototype_color" else 8 if name == "color8" else 2 if name == "color2" else panels[2][1]
    if not output: return [[0]]
    h, w = (len(grid), pw) if name == "full_panel" else dimensions(output)
    return [[color if (r, c) in output else 0 for c in range(w)] for r in range(h)]


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity": return "(rule! (lambda (g) g))"
    names = NAMES[:4] if name.startswith("rotations_") else NAMES[4:] if name.startswith("reflections_") else NAMES
    code_list = "'( " + " ".join(names) + ")"
    fallback = int(name[-1]) if name.endswith(("match0", "match1")) else 0
    valid_cell = "(and (not (= v 0)) (not (= v 8)))" if name == "ignore_color8" else "(not (= v 0))"
    condition = "(member? q (map (lambda (code) (tf (list-ref protos i) code)) names))"
    if name.startswith("area_"): condition = "(= (length (list-ref protos i)) (length q))"
    if name.startswith("bbox_"): condition = "(equal? (sort (dims (list-ref protos i)) <) (sort (dims q) <))"
    matched = f"(if (empty? matches) {fallback} (first matches))"
    if name.startswith(("area_", "bbox_")): matched = f"(if (= (length matches) 1) (first matches) {fallback})"
    if name.startswith("fixed_match"): matched = str(fallback)
    output = "selected" if mode == "prototype" else "(tf other code)"
    if name == "query_display": output = "q"
    if name == "other_display": output = "other"
    if name == "inverse_transfer": output = "(tf other (inverse code))"
    if name.startswith("fixed_") and not name.startswith("fixed_match"): output = f"(tf other '{name[6:]})"
    if name == "canonical_output": output = f"(first (sort (map (lambda (n) (tf {output} n)) all-names) shape<?))"
    color = "q-color"
    if name == "prototype_color": color = "(list-ref colors matched)" if mode == "prototype" else "(list-ref colors (- 1 matched))"
    if name == "color8": color = "8"
    if name == "color2": color = "2"
    output_dims = "(list (rows g) pw)" if name == "full_panel" else "(dims output)"
    return f"""(rule! (if (< (cols g) 5) '((0)) (let ()
  (define all-names '(id rot90 rot180 rot270 flip-h flip-v transpose anti-transpose))
  (define names {code_list})
  (define (norm cells) (if (empty? cells) '() (sort (normalize-cells cells) cell<)))
  (define (tf cells code)
    (norm (map (lambda (p) (let ((r (first p)) (c (second p)))
      (cond ((equal? code 'id) (list r c)) ((equal? code 'rot90) (list c (- r)))
            ((equal? code 'rot180) (list (- r) (- c))) ((equal? code 'rot270) (list (- c) r))
            ((equal? code 'flip-h) (list r (- c))) ((equal? code 'flip-v) (list (- r) c))
            ((equal? code 'transpose) (list c r)) (else (list (- c) (- r)))))) cells)))
  (define (inverse code) (cond ((equal? code 'rot90) 'rot270) ((equal? code 'rot270) 'rot90) (else code)))
  (define (dims cells) (if (empty? cells) '(0 0)
      (list (+ 1 (apply max (map first cells))) (+ 1 (apply max (map second cells))))))
  (define (shape<? a b)
    (cond ((empty? a) (not (empty? b))) ((empty? b) #f)
          ((equal? (first a) (first b)) (shape<? (rest a) (rest b)))
          (else (cell< (first a) (first b)))))
  (define pw (quotient (- (cols g) 2) 3))
  (define (panel i) (let ((left (* i (+ pw 1)))) (subgrid g 0 left (- (rows g) 1) (+ left pw -1))))
  (define (valid? v) {valid_cell})
  (define (support p) (norm (filter (lambda (rc) (valid? (at p (first rc) (second rc)))) (grid-positions p))))
  (define (color p) (let ((values (filter valid? (apply append p)))) (if (empty? values) 0 (first values))))
  (define panels (map panel '(0 1 2)))
  (define supports (map support panels))
  (define protos (list (first supports) (second supports)))
  (define colors (map color panels))
  (define q (third supports))
  (define q-color (third colors))
  (define matches (filter (lambda (i) {condition}) '(0 1)))
  (define matched {matched})
  (define selected (list-ref protos matched))
  (define other (list-ref protos (- 1 matched)))
  (define codes (filter (lambda (n) (equal? (tf selected n) q)) names))
  (define code (if (empty? codes) 'id (first codes)))
  (define output {output})
  (if (empty? output) '((0))
    (let ((size {output_dims}))
      (grid-from-fn (first size) (second size)
        (lambda (r c) (if (member? (list r c) output) {color} 0))))))))"""

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
    """Use exactly the first four demonstrations, never later demonstrations."""
    if len(demonstrations) < 4:
        raise ValueError("Teaching audit requires four demonstrations")
    outputs, rejected = [], []
    for index, pair in enumerate(demonstrations[:4]):
        output = grid_copy(apply(program, pair["input"]))
        if oracle is not None and output != oracle(pair["input"]):
            raise ValueError("Independent Python/Racket candidate meaning mismatch")
        outputs.append(output)
        if output != pair["output"]:
            rejected.append(index)
    return {"survives_demonstrations": not rejected,
            "executed_demo_indices": [0, 1, 2, 3], "rejected_by_demo_indices": rejected,
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
    spec = importlib.util.spec_from_file_location("_a51a8e285ce9_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid, output):
    panels, width = panel_data(grid)
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
            "panel_width": width, "ignored_right_tail": len(grid[0]) - (3 * width + 2),
            "panels": [{"color": color, "cells": list(cells), "size": len(cells),
                        "D4_distinct_poses": len({transform(cells, name) for name in NAMES})} for cells, color in panels],
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
    report = {"schema": "a51a8e285ce9-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "excluded_equivalent_hypotheses": EXCLUDED_EQUIVALENT,
              "episodes": [], "findings": [], "reference_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Four episodes only; all6+4 intended labels checked independently. Exactly first4 demos determine survivors, then every survivor receives all4 query scores. No universal identifiability, owner acceptance, or training admission."}
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
                        candidates = [("declared:mode=" + other["mode"], family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        candidates += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        row = {"seed": seed, "settings": deepcopy(settings), "train": train, "test": test,
                               "fit_demo_indices": [0, 1, 2, 3], "label_checks": [], "hypotheses": []}
                        report["episodes"].append(row)
                        # Fit receives no later-demo or query labels.
                        for name, program, oracle in candidates:
                            evaluator.context = {"phase": "fit_first_four_demonstrations", "seed": seed,
                                                 "settings": settings, "hypothesis": name}
                            row["hypotheses"].append({"name": name, "program_sha256": sha(program.encode()),
                                                      **fit_hypothesis(evaluator, program, train[:4], oracle)})
                        survivors = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivors_frozen_before_query"] = deepcopy(survivors)
                        row["survivor_set_sha256_before_queries"] = sha(packed(survivors))
                        intended_name = "declared:mode=" + mode
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


