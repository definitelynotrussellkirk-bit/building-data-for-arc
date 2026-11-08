"""Bounded, independent audit of snapshot diagonal-completion teaching.

The Python oracle below is authored separately from the native family. Racket
rivals are complete programs, executed by this checkout's protected runtime.
Only the first two demonstrations can accept or reject a hypothesis. Once that
fit is frozen, every survivor is evaluated on every query, including survivors
that happen to be equivalent under the selected setting. Execution failures
are errors, never convenient refutations.

Run through the outer review launcher, with a fresh --out under WORK/checks.
This finite audit is neither a proof of unique inference nor owner acceptance.
"""
from __future__ import annotations

import argparse
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
TASK_ID = "01bb2cbe1309"
ASSIGNMENT_ID = "review-d7872ecc6ba9c405"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator


SETTINGS = ({"passes": 1}, {"passes": 2})
SEEDS = (0, 17)
RIVALS = (
    "identity", "snapshot3", "fixedpoint",
    "inplace_forward1", "inplace_forward2", "inplace_reverse1", "inplace_reverse2",
    "skip_A", "main_only", "anti_only", "ignore_blockers", "axis_pairs",
    "endpoint_mismatch", "reverse_snapshot", "fill8", "main_then_anti",
    "anti_then_main", "reverse_second_snapshot",
)
RIVAL_MEANINGS = {
    "identity": "Return the input unchanged.",
    "snapshot3": "Three complete consuming snapshot passes, independently of the selected count.",
    "fixedpoint": "Consume canonical snapshot passes until unchanged, bounded by the number of cells.",
    "inplace_forward1": "One row-major scan; each window reads the accumulated output.",
    "inplace_forward2": "Two row-major scans; each window reads the accumulated output.",
    "inplace_reverse1": "One reverse-row-major scan; each window reads the accumulated output.",
    "inplace_reverse2": "Two reverse-row-major scans; each window reads the accumulated output.",
    "skip_A": "Repeat the selected number of passes but always read the original input.",
    "main_only": "Selected snapshot count, recognizing only the top-left/bottom-right diagonal.",
    "anti_only": "Selected snapshot count, recognizing only the top-right/bottom-left diagonal.",
    "ignore_blockers": "Selected snapshots; fill any zero opposite corner despite a nonzero blocker.",
    "axis_pairs": "Selected snapshots; additionally complete equal adjacent horizontal or vertical pairs.",
    "endpoint_mismatch": "Selected snapshots; unequal nonzero diagonal endpoints qualify, using the top endpoint color.",
    "reverse_snapshot": "Selected consuming snapshots with reverse-row-major conflict resolution.",
    "fill8": "Selected snapshots, painting eligible zero corners color 8 instead of the diagonal color.",
    "main_then_anti": "Each selected pass is a main-only snapshot followed by a consuming anti-only snapshot.",
    "anti_then_main": "Each selected pass is an anti-only snapshot followed by a consuming main-only snapshot.",
    "reverse_second_snapshot": "The first snapshot is row-major; only a selected second snapshot reverses traversal.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 2,
    "queries_per_episode": 4, "max_racket_evaluations": 800,
    "max_evaluation_requests": 1200, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "fixedpoint_changing_passes_at_most": "input height * input width (at most 900)",
}


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def grid_copy(value):
    """Validate the complete ARC grid domain, without coercing cells or shapes."""
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("A grid must have exact integer ARC cells in a rectangular 1..30 shape")
    return [row[:] for row in value]


def setting(value):
    if (type(value) is not dict or set(value) != {"passes"}
            or type(value["passes"]) is not int or value["passes"] not in (1, 2)):
        raise ValueError("Expected exactly the declared passes setting, 1 or 2")
    return value["passes"]


def _names(name):
    if name not in ("reference", "snapshot1", "snapshot2", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))


def _snapshot(grid, *, direction="forward", live=False, variant="reference"):
    """Python oracle: collect a window's proposals, then assign them in order.

    Corners are indexed clockwise as TL, TR, BR, BL. The endpoint-pair model
    here is intentionally different from the four-cell Racket implementation.
    The stable snapshot remains separate from the accumulated output unless
    the explicitly named in-place rival is being evaluated.
    """
    out = [row[:] for row in grid]
    anchors = [(r, c) for r in range(len(grid) - 1) for c in range(len(grid[0]) - 1)]
    if direction == "reverse":
        anchors.reverse()
    pairs = [(0, 2), (1, 3)]
    if variant == "main_only":
        pairs = [(0, 2)]
    elif variant == "anti_only":
        pairs = [(1, 3)]
    elif variant == "axis_pairs":
        pairs += [(0, 1), (3, 2), (0, 3), (1, 2)]
    for r, c in anchors:
        locations = [(r, c), (r, c + 1), (r + 1, c + 1), (r + 1, c)]
        view = out if live else grid
        values = [view[y][x] for y, x in locations]
        proposals = []
        for first, second in pairs:
            if not values[first] or not values[second]:
                continue
            if variant != "endpoint_mismatch" and values[first] != values[second]:
                continue
            opposite = [index for index in range(4) if index not in (first, second)]
            if variant != "ignore_blockers" and any(values[index] != 0 for index in opposite):
                continue
            color = 8 if variant == "fill8" else values[first]
            proposals.extend((locations[index], color) for index in opposite if values[index] == 0)
        for (y, x), color in proposals:
            out[y][x] = color
    return out


def rival_reference(grid, settings, name):
    """Independent Python interpretation, used only as a checked audit oracle."""
    passes = setting(settings)
    _names(name)
    original = grid_copy(grid)
    if name == "identity":
        return original
    if name.startswith("snapshot"):
        passes = int(name[-1])
    if name == "fixedpoint":
        state = original
        # A strict pass never changes an already nonzero cell. Every changed
        # pass therefore removes at least one zero, so this bound is complete.
        for _ in range(len(original) * len(original[0])):
            following = _snapshot(state)
            if following == state:
                return following
            state = following
        return state
    if name.startswith("inplace_"):
        passes = int(name[-1])
    state = original
    for index in range(passes):
        if name in ("main_then_anti", "anti_then_main"):
            first, second = ("main_only", "anti_only") if name == "main_then_anti" else ("anti_only", "main_only")
            state = _snapshot(_snapshot(state, variant=first), variant=second)
        else:
            reverse = name.startswith("inplace_reverse") or name == "reverse_snapshot" or (
                name == "reverse_second_snapshot" and index == 1)
            variant = name if name in {"main_only", "anti_only", "ignore_blockers", "axis_pairs",
                                      "endpoint_mismatch", "fill8"} else "reference"
            state = _snapshot(original if name == "skip_A" else state,
                              direction="reverse" if reverse else "forward",
                              live=name.startswith("inplace_"), variant=variant)
    return state


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    """A complete protected-runtime program; never imports native family code."""
    passes = setting(settings)
    _names(name)
    if name == "identity":
        return "(rule! (lambda (g) g))"
    if name.startswith("snapshot") or name.startswith("inplace_"):
        passes = int(name[-1])
    equal_main = "(and (> a 0) (> d 0))" if name == "endpoint_mismatch" else "(and (> a 0) (= a d))"
    equal_anti = "(and (> b 0) (> c 0))" if name == "endpoint_mismatch" else "(and (> b 0) (= b c))"
    blank_main = "#t" if name == "ignore_blockers" else "(and (= b 0) (= c 0))"
    blank_anti = "#t" if name == "ignore_blockers" else "(and (= a 0) (= d 0))"
    main_color = "8" if name == "fill8" else "a"
    anti_color = "8" if name == "fill8" else "b"
    axial = """
          ((and (> a 0) (= a b) (= c 0) (= d 0))
           (paint (paint out src (+ r 1) c0 a) src (+ r 1) (+ c0 1) a))
          ((and (> c 0) (= c d) (= a 0) (= b 0))
           (paint (paint out src r c0 c) src r (+ c0 1) c))
          ((and (> a 0) (= a c) (= b 0) (= d 0))
           (paint (paint out src r (+ c0 1) a) src (+ r 1) (+ c0 1) a))
          ((and (> b 0) (= b d) (= a 0) (= c 0))
           (paint (paint out src r c0 b) src (+ r 1) c0 b))""" if name == "axis_pairs" else ""
    live = "#t" if name.startswith("inplace_") else "#f"
    reverse = "#t" if name == "reverse_snapshot" or name.startswith("inplace_reverse") else "#f"
    orientation = "1" if name == "main_only" else "2" if name == "anti_only" else "0"
    step = f"(scan state {reverse} {live} {orientation})"
    if name == "skip_A":
        step = "(scan g #f #f 0)"
    elif name == "main_then_anti":
        step = "(scan (scan state #f #f 1) #f #f 2)"
    elif name == "anti_then_main":
        step = "(scan (scan state #f #f 2) #f #f 1)"
    elif name == "reverse_second_snapshot":
        step = "(scan state (= pass-index 1) #f 0)"
    finish = f"(for/fold ((state g)) ((pass-index (in-range {passes}))) {step})"
    if name == "fixedpoint":
        finish = """(let loop ((state g) (remaining (* (rows g) (cols g))))
    (if (= remaining 0) state
        (let ((next (scan state #f #f 0)))
          (if (equal? next state) next (loop next (- remaining 1))))))"""
    return f"""(rule! (lambda (g)
  (define (paint out src r c color)
    (if (= (at src r c) 0) (set-cell out r c color) out))
  (define (scan input reversed live orientation)
    (define anchors
      (for*/list ((r (in-range (- (rows input) 1)))
                  (c (in-range (- (cols input) 1)))) (list r c)))
    (for/fold ((out input)) ((p (in-list (if reversed (reverse anchors) anchors))))
      (let* ((r (first p)) (c0 (second p)) (src (if live out input))
             (a (at src r c0)) (b (at src r (+ c0 1)))
             (c (at src (+ r 1) c0)) (d (at src (+ r 1) (+ c0 1))))
        (cond
          ((and (!= orientation 2) {equal_main} {blank_main})
           (paint (paint out src r (+ c0 1) {main_color}) src (+ r 1) c0 {main_color}))
          ((and (!= orientation 1) {equal_anti} {blank_anti})
           (paint (paint out src r c0 {anti_color}) src (+ r 1) (+ c0 1) {anti_color}))
          {axial}
          (else out)))))
  {finish}))"""


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
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location("_01bb2cbe1309_frozen_native_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _facts(grid, intended):
    return {"shape": [len(grid), len(grid[0])],
            "colors": sorted({value for row in grid for value in row}),
            "nonzero_input_cells": sum(value != 0 for row in grid for value in row),
            "changed_cells": sum(a != b for ra, rb in zip(grid, intended) for a, b in zip(ra, rb)),
            "input_sha256": sha(packed(grid)), "output_sha256": sha(packed(intended))}


def run(out):
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    binding = source_files()
    runtime_before = runtime_files()
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
    report = {"schema": "01bb2cbe1309-independent-teaching-audit-v1", "status": "running",
              "task_id": TASK_ID, "assignment_id": ASSIGNMENT_ID,
              "source_files_sha256_before": binding, "runtime_files_sha256_before": runtime_before,
              "limits": deepcopy(LIMITS), "rival_meanings": RIVAL_MEANINGS,
              "known_equivalence_notes": {
                  "passes=1/skip_A": "A single pass reads the original input in both programs; no intermediate exists to skip.",
                  "passes=1/reverse_second_snapshot": "There is no second pass to reverse, so both programs perform one forward snapshot."
              },
              "episodes": [], "findings": [], "reference_label_count": 0,
              "visibility": "controller_private", "training_admitted": False,
              "scope": "Four episodes only; all 6+4 intended labels checked. Exactly the first two demos determine every survivor. No universal identifiability, owner acceptance, or training admission."}
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
                        count = setting(settings)
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
                        candidates = [("declared:passes=" + str(other["passes"]), family.program(other),
                                       lambda grid, other=other: reference(grid, other)) for other in SETTINGS]
                        candidates += [(name, rival_program(settings, name),
                                        lambda grid, name=name: rival_reference(grid, settings, name)) for name in RIVALS]
                        row = {"seed": seed, "settings": deepcopy(settings), "train": train, "test": test,
                               "fit_demo_indices": [0, 1], "label_checks": [], "hypotheses": []}
                        report["episodes"].append(row)
                        # This complete fitting phase receives only first-two-demo labels.
                        # Remaining demos and all query labels are checked only afterwards.
                        for name, program, oracle in candidates:
                            evaluator.context = {"phase": "fit_first_two_demonstrations", "seed": seed,
                                                 "settings": settings, "hypothesis": name}
                            row["hypotheses"].append({"name": name, "program_sha256": sha(program.encode()),
                                                      **fit_hypothesis(evaluator, program, train[:2], oracle)})
                        survivors = [item["name"] for item in row["hypotheses"] if item["survives_demonstrations"]]
                        row["survivors_frozen_before_query"] = deepcopy(survivors)
                        row["survivor_set_sha256_before_queries"] = sha(packed(survivors))
                        intended_name = "declared:passes=" + str(count)
                        row["known_equivalent_extra_survivors"] = [name for name in survivors
                            if count == 1 and name in {"skip_A", "reverse_second_snapshot"}]
                        row["unclassified_extra_survivors"] = [name for name in survivors
                            if name != intended_name and name not in row["known_equivalent_extra_survivors"]]
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
                                         "facts": _facts(pair["input"], independent)}
                                row["label_checks"].append(check)
                                if not check["matched"]:
                                    raise ValueError("Native label, independent Python, and protected Racket disagree")
                                report["reference_label_count"] += 1
                        # Query labels score the already frozen set; no survivor can be
                        # removed merely because its query answer is inconvenient.
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
                report["racket_after"] = {key: bridge.runtime_identity[key] for key in identity}
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
                report.setdefault("racket_after", {key: bridge.runtime_identity[key]
                                                    for key in report.get("racket_before", {})})
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
        _write_json(private / "audit.json", report)
    print(json.dumps({key: report.get(key) for key in ("status", "reference_label_count", "execution", "findings", "error")}))
    return 0 if report["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    raise SystemExit(run(options.out))


if __name__ == "__main__":
    main()
