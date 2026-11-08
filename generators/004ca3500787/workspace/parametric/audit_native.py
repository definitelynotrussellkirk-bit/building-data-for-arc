"""Independent finite audit for singleton-D4-class selection and output pose.

The Python shape oracle and complete Racket candidates below are independent
of native_family.py. Exact canonical order is decimal-string order of the
numerically sorted normalized coordinate list, matching Racket FORMAT ~a.
Only the first two demonstrations fit candidates; all survivors are retained
and scored on every query. Errors never count as refutations.

The bookkeeping framework is an explicit source copy of this packet's first
task audit. There are no sibling-task imports, runtime or evidence dependencies.
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
TASK_ID = "004ca3500787"
ASSIGNMENT_ID = "review-d7872ecc6ba9c405"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


SETTINGS = ({"pose": "canonical"}, {"pose": "observed"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "rotation_group", "translation_group", "area_group", "bbox_group",
    "common_class", "smallest_area", "largest_area", "smallest_bbox", "largest_bbox",
    "first", "middle", "last", "leftmost", "rightmost", "connectivity8", "choose_F", "choose_P",
    "rotation_output", "numeric_output", "solid_box", "color2",
    "fixed_r90", "fixed_r180", "fixed_r270", "fixed_m0", "fixed_m90", "fixed_m180", "fixed_m270",
)
RIVAL_MEANINGS = {
    "identity": "Return the original input.",
    "rotation_group": "Group by translation and rotation only; reflection does not identify shapes.",
    "translation_group": "Group by exact normalized observed coordinates, without rotation or reflection.",
    "area_group": "Group only by number of red cells.",
    "bbox_group": "Group only by unordered tight-bounding-box dimensions.",
    "common_class": "Select the most frequent D4 class, using its first observed component.",
    "smallest_area": "Select the fewest-cell component; discovery order breaks ties.",
    "largest_area": "Select the most-cell component; discovery order breaks ties.",
    "smallest_bbox": "Select the smallest bounding-box area; discovery order breaks ties.",
    "largest_bbox": "Select the largest bounding-box area; discovery order breaks ties.",
    "first": "Select the first component in row-major discovery order.",
    "middle": "Select the lower middle component in row-major discovery order.",
    "last": "Select the last component in row-major discovery order.",
    "leftmost": "Select the minimum-left-column component; discovery order breaks ties.",
    "rightmost": "Select the maximum-left-column component; discovery order breaks ties.",
    "connectivity8": "Extract red eight-connected components before D4 grouping and selection.",
    "choose_F": "Select the first unscaled F pentomino if present; otherwise the first component.",
    "choose_P": "Select the first unscaled P pentomino if present; otherwise the first component.",
    "rotation_output": "Select the correct D4 singleton, then emit its rotation-only string-canonical pose.",
    "numeric_output": "Select the correct D4 singleton, then emit its numeric-coordinate D4 minimum.",
    "solid_box": "Select and orient correctly, but fill the entire tight bounding box with 8.",
    "color2": "Select and orient correctly, but leave the selected mask red (2).",
    **{name: "Select the correct singleton, then apply this fixed D4 transform to its observed pose: " + name
       for name in ("fixed_r90", "fixed_r180", "fixed_r270", "fixed_m0", "fixed_m90", "fixed_m180", "fixed_m270")},
}
EXCLUDED_EQUIVALENT = {
    "always_canonical_output": "Exactly the declared canonical-pose program; represented by that declared hypothesis.",
    "raw_observed_output_and_fixed_identity_transform": "Exactly the declared observed-pose program; represented by that declared hypothesis.",
    "numeric_D4_grouping_only": "A deterministic numeric D4 representative still identifies exactly the same D4 orbits; numeric output is tested separately.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "max_racket_evaluations": 800,
    "max_evaluation_requests": 1200, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "candidate_totality": "All valid ARC1..30 grids: ignore non-red cells; no red component yields [[0]]; no singleton yields first component.",
}
F_CELLS = ((0, 1), (0, 2), (1, 0), (1, 1), (2, 1))
P_CELLS = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0))


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
        raise ValueError("A grid must have exact integer ARC cells in a rectangular 1..30 shape")
    return [row[:] for row in value]


def setting(value):
    if (type(value) is not dict or set(value) != {"pose"}
            or type(value["pose"]) is not str or value["pose"] not in ("canonical", "observed")):
        raise ValueError("Expected exactly the declared canonical or observed pose setting")
    return value["pose"]


def normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    min_r, min_c = min(r for r, c in cells), min(c for r, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def shape_key(cells):
    """Racket FORMAT ~a spelling, after numeric sorting, not Python repr."""
    return "(" + " ".join(f"({r} {c})" for r, c in normalize(cells)) + ")"


def transform(cells, rotation=0, reflected=False):
    current = [(r, -c if reflected else c) for r, c in cells]
    for _ in range(rotation % 4):
        current = [(c, -r) for r, c in current]
    return normalize(current)


def canonical(cells, *, rotations_only=False, numeric=False):
    poses = {transform(cells, rotation, reflected)
             for reflected in ((False,) if rotations_only else (False, True))
             for rotation in range(4)}
    return min(poses, key=(lambda value: value) if numeric else shape_key)


def components(grid, connectivity=4):
    """Set-based flood fill, independent of native extraction and Racket objects."""
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    groups = []
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    while pending:
        first = min(pending)
        pending.remove(first)
        stack, group = [first], [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in deltas:
                following = r + dr, c + dc
                if following in pending:
                    pending.remove(following)
                    stack.append(following)
                    group.append(following)
        groups.append(tuple(sorted(group)))
    return groups


def dimensions(cells):
    cells = normalize(cells)
    return max(r for r, c in cells) + 1, max(c for r, c in cells) + 1


def mask(cells, color=8, solid=False):
    cells = normalize(cells)
    if not cells:
        return [[0]]
    height, width = dimensions(cells)
    occupied = set(cells)
    return [[color if solid or (r, c) in occupied else 0 for c in range(width)] for r in range(height)]


def rival_reference(grid, settings, name):
    pose = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity":
        return grid
    groups = components(grid, 8 if name == "connectivity8" else 4)
    if not groups:
        return [[0]]
    def signature(cells):
        if name == "translation_group":
            return normalize(cells)
        if name == "area_group":
            return len(cells)
        if name == "bbox_group":
            return tuple(sorted(dimensions(cells)))
        return canonical(cells, rotations_only=name == "rotation_group")
    keys = [signature(cells) for cells in groups]
    frequencies = Counter(keys)
    chosen = next((index for index, key in enumerate(keys) if frequencies[key] == 1), 0)
    if name == "common_class":
        chosen = max(range(len(groups)), key=lambda index: frequencies[keys[index]])
    elif name in {"smallest_area", "largest_area", "smallest_bbox", "largest_bbox", "leftmost", "rightmost"}:
        def score(index):
            if name.endswith("area"):
                return len(groups[index])
            if name.endswith("bbox"):
                height, width = dimensions(groups[index])
                return height * width
            return min(c for r, c in groups[index])
        chooser = max if name.startswith("largest") or name == "rightmost" else min
        chosen = chooser(range(len(groups)), key=score)
    elif name in {"first", "middle", "last"}:
        chosen = {"first": 0, "middle": (len(groups) - 1) // 2, "last": len(groups) - 1}[name]
    elif name in {"choose_F", "choose_P"}:
        wanted = canonical(F_CELLS if name == "choose_F" else P_CELLS)
        chosen = next((index for index, cells in enumerate(groups) if canonical(cells) == wanted), 0)
    cells = groups[chosen]
    if name.startswith("fixed_"):
        operation = name[6:]
        cells = transform(cells, int(operation[1:]) // 90, operation[0] == "m")
    elif name == "rotation_output":
        cells = canonical(cells, rotations_only=True)
    elif name == "numeric_output":
        cells = canonical(cells, numeric=True)
    elif pose == "canonical":
        cells = canonical(cells)
    else:
        cells = normalize(cells)
    return mask(cells, 2 if name == "color2" else 8, name == "solid_box")


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    """Complete Racket rival, with its own coordinate and selection functions."""
    pose = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    signature = "(shape-key (canon cells #f #f))"
    if name == "rotation_group":
        signature = "(shape-key (canon cells #t #f))"
    elif name == "translation_group":
        signature = "(shape-key cells)"
    elif name == "area_group":
        signature = "(length cells)"
    elif name == "bbox_group":
        signature = "(sort (dims cells) <)"
    selection = "(singleton-index)"
    if name == "common_class":
        selection = "(choose-index frequency #t)"
    elif name in {"smallest_area", "largest_area"}:
        selection = f"(choose-index (lambda (i) (length (list-ref pieces i))) {'#t' if name.startswith('largest') else '#f'})"
    elif name in {"smallest_bbox", "largest_bbox"}:
        selection = f"(choose-index (lambda (i) (apply * (dims (list-ref pieces i)))) {'#t' if name.startswith('largest') else '#f'})"
    elif name in {"leftmost", "rightmost"}:
        selection = f"(choose-index (lambda (i) (apply min (map second (list-ref pieces i)))) {'#t' if name == 'rightmost' else '#f'})"
    elif name in {"first", "middle", "last"}:
        selection = {"first": "0", "middle": "(quotient (- (length pieces) 1) 2)", "last": "(- (length pieces) 1)"}[name]
    elif name in {"choose_F", "choose_P"}:
        literal = "'((0 1) (0 2) (1 0) (1 1) (2 1))" if name == "choose_F" else "'((0 0) (0 1) (1 0) (1 1) (2 0))"
        selection = f"(shape-index (shape-key (canon {literal} #f #f)))"
    output_cells = "(canon chosen #f #f)" if pose == "canonical" else "(norm chosen)"
    if name.startswith("fixed_"):
        operation = name[6:]
        output_cells = "(mirror chosen)" if operation[0] == "m" else "(norm chosen)"
        for _ in range(int(operation[1:]) // 90):
            output_cells = f"(turn {output_cells})"
    elif name == "rotation_output":
        output_cells = "(canon chosen #t #f)"
    elif name == "numeric_output":
        output_cells = "(canon chosen #f #t)"
    color = 2 if name == "color2" else 8
    present = "#t" if name == "solid_box" else "(member (list r c) output-cells)"
    return f"""(rule! (lambda (g)
  (define (cell<? a b)
    (or (< (first a) (first b)) (and (= (first a) (first b)) (< (second a) (second b)))))
  (define (norm cells)
    (if (empty? cells) '()
        (let ((mr (apply min (map first cells))) (mc (apply min (map second cells))))
          (sort (map (lambda (p) (list (- (first p) mr) (- (second p) mc))) cells) cell<?))))
  (define (shape-key cells) (format "~a" (norm cells)))
  (define (turn cells) (norm (map (lambda (p) (list (second p) (- (first p)))) cells)))
  (define (mirror cells) (norm (map (lambda (p) (list (first p) (- (second p)))) cells)))
  (define (rotations cells)
    (let* ((a (norm cells)) (b (turn a)) (c (turn b)) (d (turn c))) (list a b c d)))
  (define (lex<? a b)
    (cond ((empty? a) (not (empty? b))) ((empty? b) #f)
          ((< (first a) (first b)) #t) ((> (first a) (first b)) #f)
          (else (lex<? (rest a) (rest b)))))
  (define (canon cells only-rotations numeric)
    (define poses (if only-rotations (rotations cells) (append (rotations cells) (rotations (mirror cells)))))
    (first (sort poses (lambda (a b) (if numeric (lex<? (apply append a) (apply append b))
                                      (string<? (shape-key a) (shape-key b)))))))
  (define (dims cells)
    (define n (norm cells))
    (list (+ 1 (apply max (map first n))) (+ 1 (apply max (map second n)))))
  (define pieces (map obj-cells (filter (lambda (o) (= (obj-color o) 2))
                                      ({'objects-8' if name == 'connectivity8' else 'objects'} g 0))))
  (define (signature cells) {signature})
  (define keys (map signature pieces))
  (define (frequency i) (length (filter (lambda (key) (equal? key (list-ref keys i))) keys)))
  (define (singleton-index)
    (define matches (filter (lambda (i) (= (frequency i) 1)) (range (length pieces))))
    (if (empty? matches) 0 (first matches)))
  (define (shape-index wanted)
    (define matches (filter (lambda (i) (equal? (list-ref keys i) wanted)) (range (length pieces))))
    (if (empty? matches) 0 (first matches)))
  (define (choose-index score maximum)
    (for/fold ((best 0)) ((i (in-range 1 (length pieces))))
      (if (if maximum (> (score i) (score best)) (< (score i) (score best))) i best)))
  (if (empty? pieces) '((0))
      (let* ((chosen (list-ref pieces {selection})) (output-cells {output_cells})
             (size (dims output-cells)))
        (grid-from-fn (first size) (second size) (lambda (r c) (if {present} {color} 0)))))))"""


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
    spec = importlib.util.spec_from_file_location("_004ca3500787_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid, output):
    groups = components(grid)
    keys = [shape_key(canonical(cells)) for cells in groups]
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
            "component_count": len(groups), "red_cells": sum(len(cells) for cells in groups),
            "D4_class_multiplicities": sorted(Counter(keys).values()),
            "components": [{"size": len(cells), "bbox_dimensions": list(dimensions(cells)),
                            "observed_key": shape_key(cells), "D4_key": key}
                           for cells, key in zip(groups, keys)],
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
    report = {"schema": "004ca3500787-independent-teaching-audit-v1", "status": "running",
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
                        pose = setting(settings)
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
                        candidates = [("declared:pose=" + other["pose"], family.program(other),
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
                        intended_name = "declared:pose=" + pose
                        row["extra_survivors"] = [name for name in survivors if name != intended_name]
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


