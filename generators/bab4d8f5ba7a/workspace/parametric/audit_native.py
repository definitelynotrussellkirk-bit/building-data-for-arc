"""Independent finite audit of row-header recoloring and component selection.

Python geometry and complete Racket hypotheses do not import the native source.
Bookkeeping is explicitly source-copied from the completed 111848 XOR audit;
no predecessor imports, receipts, runtime or environment are dependencies.
Exactly the first two demonstrations fit candidates before any query scoring.
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
TASK_ID = "bab4d8f5ba7a"
ASSIGNMENT_ID = "review-a2fa8bcede5fa990"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"mode": "row"}, {"mode": "largest"})
SEEDS = (0, 17)
RIVALS = (
    "identity", "skip_recolor", "global_first_header", "first_marker_only", "last_marker_only",
    "zero_header_recolors", "erase_nonmarker_body", "all_nonzero_body", "drop_headers", "column_header",
    "select_before_recolor", "diagonal_components", "foreground_components", "global_color", "bbox_area",
    "smallest_component", "tie_last_anchor", "tie_low_color", "tie_high_color", "ignore_eights",
    "solid_box", "crop_box", "keep_canvas", "fixed_output2", "fixed_output8",
)
ROW_RIVALS = RIVALS[1:10]
POST_RIVALS = RIVALS[10:]
RIVAL_MEANINGS = {
    "identity": "Return the unchanged input.",
    "skip_recolor": "Skip row recoloring; row mode is identity, largest mode selects from the input.",
    "global_first_header": "Replace every body8 by the first nonzero row header, or0 if no header exists.",
    "first_marker_only": "Recolor only the first body8 in each row with a nonzero header.",
    "last_marker_only": "Recolor only the last body8 in each row with a nonzero header.",
    "zero_header_recolors": "Apply the header even when it is0, erasing those body8 cells.",
    "erase_nonmarker_body": "Erase body cells originally neither0 nor8 after recoloring.",
    "all_nonzero_body": "Recolor every occupied body cell in nonzero-header rows.",
    "drop_headers": "Erase column0 after row recoloring.",
    "column_header": "Use the top cell of the current column as the key instead of the row header.",
    "select_before_recolor": "Select the largest input component, then render only its original cells with their recolored values.",
    "diagonal_components": "Select largest same-color8-connected component after recoloring.",
    "foreground_components": "Select largest colorblind4-connected foreground component; retain its recolored cell values.",
    "global_color": "Aggregate every cell of a color irrespective of connectivity, then select largest color total.",
    "bbox_area": "Rank post-recolor components by bounding-box area instead of occupied-cell count.",
    "smallest_component": "Select the smallest post-recolor component.",
    "tie_last_anchor": "Largest ties use the lexicographically last occupied anchor.",
    "tie_low_color": "Largest ties prefer the numerically lowest color, then first occupied anchor.",
    "tie_high_color": "Largest ties prefer the numerically highest color, then first occupied anchor.",
    "ignore_eights": "Exclude all color8 components from post-recolor selection.",
    "solid_box": "Fill the selected component's entire bounding box in its color.",
    "crop_box": "Crop the full recolored grid to the selected component's bbox, preserving unrelated clutter inside it.",
    "keep_canvas": "Render the selected component at its original coordinates on the full input canvas.",
    "fixed_output2": "Render the selected component in fixed color2.",
    "fixed_output8": "Render the selected component in fixed color8.",
}
EXCLUDED_EQUIVALENT = {
    "always_row": "Already represented by the declared row hypothesis.",
    "always_correct_largest": "Already represented by the declared largest hypothesis.",
    "largest_before_without_recolor": "Exactly skip_recolor in largest mode.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "max_racket_evaluations": 650,
    "max_evaluation_requests": 1000, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "candidate_totality": "All exact rectangular ARC1..30 grids; no foreground gives[[0]] for component candidates; ties use first occupied anchor unless explicitly overridden.",
    "candidate_scope": "Row-stage rivals follow the episode's mode; post-selection rivals always emit a component result, including when tested against row mode.",
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
            or type(value["mode"]) is not str or value["mode"] not in ("row", "largest")):
        raise ValueError("Expected exactly mode=row or mode=largest")
    return value["mode"]


def equivalent_aliases(settings):
    setting(settings)
    return {}


def components(grid, *, diagonal=False, colorblind=False):
    visited, groups = set(), []
    h, w = len(grid), len(grid[0])
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in visited:
                continue
            color = grid[r][c]
            reached, stack = {(r, c)}, [(r, c)]
            visited.add((r, c))
            while stack:
                y, x = stack.pop()
                for dy, dx in steps:
                    point = yy, xx = y + dy, x + dx
                    if (0 <= yy < h and 0 <= xx < w and point not in visited
                            and grid[yy][xx] and (colorblind or grid[yy][xx] == color)):
                        visited.add(point)
                        reached.add(point)
                        stack.append(point)
            groups.append((color, tuple(sorted(reached))))
    return groups


def row_stage(grid, name="reference"):
    if name == "skip_recolor":
        return grid_copy(grid)
    first_key = next((row[0] for row in grid if row[0]), 0)
    output = grid_copy(grid)
    for r, row in enumerate(grid):
        markers = [c for c in range(1, len(row)) if row[c] == 8]
        for c, value in enumerate(row):
            key = grid[0][c] if name == "column_header" else first_key if name == "global_first_header" else row[0]
            change = c > 0 and value == 8 and key != 0
            if name in ("zero_header_recolors", "global_first_header"):
                change = c > 0 and value == 8
            elif name == "first_marker_only":
                change = change and c == markers[0]
            elif name == "last_marker_only":
                change = change and c == markers[-1]
            elif name == "all_nonzero_body":
                change = c > 0 and value != 0 and key != 0
            output[r][c] = key if change else value
            if name == "erase_nonmarker_body" and c > 0 and value not in (0, 8):
                output[r][c] = 0
            if name == "drop_headers" and c == 0:
                output[r][c] = 0
    return output


def bounds(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def rival_reference(grid, settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    grid = grid_copy(grid)
    if name == "identity":
        return grid
    stage = row_stage(grid, name)
    if mode == "row" and name not in POST_RIVALS:
        return stage
    source = grid if name == "select_before_recolor" else stage
    if name == "global_color":
        groups = [(color, tuple((r, c) for r, row in enumerate(source) for c, value in enumerate(row) if value == color))
                  for color in range(1, 10) if any(color in row for row in source)]
    else:
        groups = components(source, diagonal=name == "diagonal_components", colorblind=name == "foreground_components")
    if name == "ignore_eights":
        groups = [group for group in groups if group[0] != 8]
    if not groups:
        return [[0]]
    def key(group):
        color, cells = group
        r0, c0, r1, c1 = bounds(cells)
        score = (r1-r0+1)*(c1-c0+1) if name == "bbox_area" else len(cells)
        first = score if name == "smallest_component" else -score
        anchor = cells[0]
        tie = (-anchor[0], -anchor[1]) if name == "tie_last_anchor" else anchor
        if name == "tie_low_color":
            return first, color, tie
        if name == "tie_high_color":
            return first, -color, tie
        return first, tie
    color, selected = min(groups, key=key)
    r0, c0, r1, c1 = bounds(selected)
    if name == "keep_canvas":
        r0, c0, r1, c1 = 0, 0, len(grid)-1, len(grid[0])-1
    cells = set(selected)
    def cell(r, c):
        if name in ("solid_box", "crop_box") or (r, c) in cells:
            if name in ("select_before_recolor", "foreground_components", "crop_box"):
                return stage[r][c]
            if name == "fixed_output2":
                return 2
            if name == "fixed_output8":
                return 8
            return color
        return 0
    return [[cell(r, c) for c in range(c0, c1+1)] for r in range(r0, r1+1)]


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    mode = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    key = "(at g 0 c)" if name == "column_header" else "first-key" if name == "global_first_header" else "(at g r 0)"
    guard = "(and (> c 0) (= v 8) (!= key 0))"
    if name in ("zero_header_recolors", "global_first_header"):
        guard = "(and (> c 0) (= v 8))"
    elif name == "first_marker_only":
        guard = "(and (> c 0) (= v 8) (!= key 0) (not (ormap (lambda (j) (= (at g r j) 8)) (range 1 c))))"
    elif name == "last_marker_only":
        guard = "(and (> c 0) (= v 8) (!= key 0) (not (ormap (lambda (j) (= (at g r j) 8)) (range (+ c 1) w))))"
    elif name == "all_nonzero_body":
        guard = "(and (> c 0) (!= v 0) (!= key 0))"
    value = f"(if {guard} key v)"
    if name == "erase_nonmarker_body":
        value = f"(if (and (> c 0) (!= v 0) (!= v 8)) 0 {value})"
    elif name == "drop_headers":
        value = f"(if (= c 0) 0 {value})"
    stage = "g" if name == "skip_recolor" else f"(grid-from-fn h w (lambda (r c) (let ((key {key}) (v (at g r c))) {value})))"
    definitions = f"""(define first-key (let ((ks (filter (lambda (x) (!= x 0)) (map first g)))) (if (empty? ks) 0 (first ks))))
  (define stage {stage})"""
    if mode == "row" and name not in POST_RIVALS:
        return f"(rule! (let () {definitions} stage))"
    source = "g" if name == "select_before_recolor" else "stage"
    found = "(objects source 0)"
    if name == "diagonal_components":
        found = "(objects-8 source 0)"
    elif name == "foreground_components":
        found = "(objects (grid-from-fn h w (lambda (r c) (if (= (at source r c) 0) 0 1))) 0)"
    groups = f"(map (lambda (o) (list (obj-color o) (sort (obj-cells o) cell<))) {found})"
    if name == "global_color":
        groups = """(map (lambda (color) (list color (filter (lambda (p) (= (at source (first p) (second p)) color)) (grid-positions source))))
      (sort (remove-duplicates (filter (lambda (v) (!= v 0)) (append* source))) <))"""
    if name == "ignore_eights":
        groups = f"(filter (lambda (o) (!= (first o) 8)) {groups})"
    score = "(* (+ 1 (- (third (bbox-of-cells (second o))) (first (bbox-of-cells (second o))))) (+ 1 (- (fourth (bbox-of-cells (second o))) (second (bbox-of-cells (second o))))))" if name == "bbox_area" else "(length (second o))"
    anchor_test = "(cell< (anchor b) (anchor a))" if name == "tie_last_anchor" else "(cell< (anchor a) (anchor b))"
    tie = anchor_test
    if name in ("tie_low_color", "tie_high_color"):
        op = "<" if name == "tie_low_color" else ">"
        tie = f"(if (= (first a) (first b)) {anchor_test} ({op} (first a) (first b)))"
    op = "<" if name == "smallest_component" else ">"
    r0, c0, height, width = "(first bb)", "(second bb)", "(+ 1 (- (third bb) (first bb)))", "(+ 1 (- (fourth bb) (second bb)))"
    if name == "keep_canvas":
        r0, c0, height, width = "0", "0", "h", "w"
    present = "#t" if name in ("solid_box", "crop_box") else "(member? p cells)"
    color = "(first winner)"
    if name in ("select_before_recolor", "foreground_components", "crop_box"):
        color = "(at stage (first p) (second p))"
    elif name == "fixed_output2":
        color = "2"
    elif name == "fixed_output8":
        color = "8"
    return f"""(rule! (let ()
  {definitions}
  (define source {source})
  (define groups {groups})
  (define (anchor o) (first (second o)))
  (define (score o) {score})
  (define (better? a b) (if (= (score a) (score b)) {tie} ({op} (score a) (score b))))
  (if (empty? groups) '((0))
    (let* ((winner (first (sort groups better?))) (cells (second winner)) (bb (bbox-of-cells cells)))
      (grid-from-fn {height} {width} (lambda (r c)
        (let ((p (list (+ r {r0}) (+ c {c0})))) (if {present} {color} 0))))))))"""

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
    spec = importlib.util.spec_from_file_location("_bab4d8f5ba7a_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid, output):
    stage = row_stage(grid)
    before, after = components(grid), components(stage)
    def winner(groups):
        if not groups:
            return None
        color, cells = min(groups, key=lambda group: (-len(group[1]), group[1][0]))
        return {"color": color, "size": len(cells), "anchor": list(cells[0]), "bbox": list(bounds(cells))}
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [len(output), len(output[0])],
            "occupied_cells": sum(bool(v) for row in grid for v in row),
            "before_component_count": len(before), "after_component_count": len(after),
            "before_winner": winner(before), "after_winner": winner(after),
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
    report = {"schema": "bab4d8f5ba7a-independent-teaching-audit-v1", "status": "running",
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
                        candidates = [("declared:mode=" + other["mode"], family.program(other),
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


