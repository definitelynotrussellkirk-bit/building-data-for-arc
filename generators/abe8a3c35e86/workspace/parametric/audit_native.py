"""Independent finite audit of one or two actual hinge-reflection passes.

Python geometry and complete Racket candidates are independent of native code.
Bookkeeping and the same-color component traversal are explicit source copies
from this packet's completed row/component audit, with task identity, settings
and a four-demo fit boundary adapted. No earlier receipts, runtimes or imports
are dependencies.
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
TASK_ID = "abe8a3c35e86"
ASSIGNMENT_ID = "review-a2fa8bcede5fa990"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

SETTINGS = ({"passes": 1}, {"passes": 2})
SEEDS = (0, 17)
RIVALS = (
    "identity", "row_priority", "column_only", "row_only", "always_column", "always_row",
    "else_row", "else_column", "both_original", "geometric_fourfold", "rotate180",
    "global_center", "center_row", "center_col", "pivot_plus_row", "pivot_plus_col",
    "per_color", "per_component", "largest_component_only", "fixed_copies2", "first_color_copies",
    "drop_pivot", "move_copy", "reject_clipped", "wrap", "clamp", "erase_clipped_sources", "crop_result",
)
RIVAL_MEANINGS = {
    "identity": "Return unchanged input.",
    "row_priority": "At every pass, prefer row-side reflection over column-side reflection.",
    "column_only": "Use only the column-side branch, otherwise no-op.",
    "row_only": "Use only the row-side branch, otherwise no-op.",
    "always_column": "Reflect across the pivot column without a side predicate.",
    "always_row": "Reflect across the pivot row without a side predicate.",
    "else_row": "After both side predicates fail, incorrectly reflect across the pivot row.",
    "else_column": "After both side predicates fail, incorrectly reflect across the pivot column.",
    "both_original": "Per pass, copy along every satisfied axis from that pass's original cells, omitting composed diagonal images.",
    "geometric_fourfold": "Per pass, use original side predicates to include column, row and composed diagonal images, even when an earlier actual pass would clip entirely.",
    "rotate180": "Copy a180-degree pivot rotation instead of the selected single-axis reflection.",
    "global_center": "Use the lower integer canvas center as pivot.",
    "center_row": "Use the canvas center row and the9 pivot column.",
    "center_col": "Use the9 pivot row and canvas center column.",
    "pivot_plus_row": "Use a pivot one row below the actual9.",
    "pivot_plus_col": "Use a pivot one column right of the actual9.",
    "per_color": "Choose a branch independently for each non0/9 color at every pass.",
    "per_component": "Choose a branch independently for each same-color4-connected component.",
    "largest_component_only": "Reflect only the largest non9 component, choosing its own branch; ties use occupied-anchor order.",
    "fixed_copies2": "Paint every reflected copy in fixed color2.",
    "first_color_copies": "Paint every reflected copy in the first motif cell's color.",
    "drop_pivot": "Run correct passes, then erase all9 cells.",
    "move_copy": "Erase the source motif before drawing its reflection at every pass.",
    "reject_clipped": "Reject the entire selected reflection if even one destination is out of bounds.",
    "wrap": "Wrap reflected destinations around the canvas instead of clipping.",
    "clamp": "Clamp reflected destinations to the nearest edge instead of clipping.",
    "erase_clipped_sources": "Erase source cells whose reflected destinations are out of bounds.",
    "crop_result": "Crop the completed result to its nonzero bounding box.",
}
EXCLUDED_EQUIVALENT = {
    "always_one_pass": "Already represented by declared passes1.",
    "always_two_passes": "Already represented by declared passes2.",
    "reuse_original_axis_for_second_copy": "A single-axis clipped copy is idempotent, so this equals declared passes1.",
    "run_until_fixed_point": "On the one-pivot grammar, actual canonical iteration stabilizes within2passes; this equals declared passes2.",
}
LIMITS = {
    "seeds": list(SEEDS), "settings": list(SETTINGS), "episode_count": 4,
    "generated_demonstrations_per_episode": 6, "fit_demonstrations_per_episode": 4,
    "queries_per_episode": 4, "max_racket_evaluations": 1400,
    "max_evaluation_requests": 1800, "wall_seconds_checked_between_calls": 300,
    "racket_seconds_per_call": 10, "racket_startup_seconds": 30,
    "candidate_totality": "All exact rectangular ARC1..30 grids; no9 pivot makes each pass a no-op, multiple9 uses the first, and empty final crop yields[[0]].",
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
    if (type(value) is not dict or set(value) != {"passes"}
            or type(value["passes"]) is not int or value["passes"] not in (1, 2)):
        raise ValueError("Expected exactly passes=1 or passes=2")
    return value["passes"]


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



def axes(cells, pr, pc, name="reference"):
    if not cells:
        return []
    left_right = max(c for r, c in cells) < pc or min(c for r, c in cells) > pc
    above_below = max(r for r, c in cells) < pr or min(r for r, c in cells) > pr
    if name == "row_priority":
        return ["row"] if above_below else ["column"] if left_right else []
    if name == "column_only":
        return ["column"] if left_right else []
    if name == "row_only":
        return ["row"] if above_below else []
    if name == "always_column":
        return ["column"]
    if name == "always_row":
        return ["row"]
    if name == "rotate180":
        return ["diagonal"]
    if name in ("both_original", "geometric_fourfold"):
        return (["column"] if left_right else []) + (["row"] if above_below else []) + (["diagonal"] if name == "geometric_fourfold" and left_right and above_below else [])
    return ["column"] if left_right else ["row"] if above_below else ["row"] if name == "else_row" else ["column"] if name == "else_column" else []


def one_pass(grid, name="reference"):
    output = grid_copy(grid)
    pivots = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)]
    if not pivots or not cells:
        return output
    h, w = len(grid), len(grid[0])
    pr, pc = pivots[0]
    if name in ("global_center", "center_row"):
        pr = (h - 1) // 2
    if name in ("global_center", "center_col"):
        pc = (w - 1) // 2
    if name == "pivot_plus_row":
        pr += 1
    if name == "pivot_plus_col":
        pc += 1
    groups = [cells]
    if name == "per_color":
        groups = [[p for p in cells if grid[p[0]][p[1]] == color] for color in range(1, 9)]
        groups = [group for group in groups if group]
    elif name in ("per_component", "largest_component_only"):
        objects = [o for o in components(grid) if o[0] != 9]
        if name == "largest_component_only":
            objects = [min(objects, key=lambda o: (-len(o[1]), o[1][0]))]
        groups = [o[1] for o in objects]
    for group in groups:
        for axis in axes(group, pr, pc, name):
            destinations = [(r if axis == "column" else 2 * pr-r,
                             c if axis == "row" else 2 * pc-c) for r, c in group]
            inside = [0 <= r < h and 0 <= c < w for r, c in destinations]
            if name == "reject_clipped" and not all(inside):
                continue
            if name == "move_copy":
                for r, c in group:
                    output[r][c] = 0
            if name == "erase_clipped_sources":
                for (r, c), good in zip(group, inside):
                    if not good:
                        output[r][c] = 0
            for (r, c), (rr, cc) in zip(group, destinations):
                if name == "wrap":
                    rr, cc = rr % h, cc % w
                elif name == "clamp":
                    rr, cc = min(h-1, max(0, rr)), min(w-1, max(0, cc))
                if 0 <= rr < h and 0 <= cc < w:
                    output[rr][cc] = 2 if name == "fixed_copies2" else grid[cells[0][0]][cells[0][1]] if name == "first_color_copies" else grid[r][c]
    return output


def rival_reference(grid, settings, name):
    count = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    output = grid_copy(grid)
    if name == "identity":
        return output
    for _ in range(count):
        output = one_pass(output, name)
    if name == "drop_pivot":
        output = [[0 if v == 9 else v for v in row] for row in output]
    if name == "crop_result":
        cells = [(r, c) for r, row in enumerate(output) for c, v in enumerate(row) if v]
        if not cells:
            return [[0]]
        r0, c0 = min(r for r,c in cells), min(c for r,c in cells)
        r1, c1 = max(r for r,c in cells), max(c for r,c in cells)
        output = [row[c0:c1+1] for row in output[r0:r1+1]]
    return output


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    count = setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + str(name))
    if name == "identity":
        return "(rule! (lambda (g) g))"
    pr, pc = "(first pivot)", "(second pivot)"
    if name in ("global_center", "center_row"):
        pr = "(quotient (- h 1) 2)"
    if name in ("global_center", "center_col"):
        pc = "(quotient (- w 1) 2)"
    if name == "pivot_plus_row":
        pr = "(+ 1 (first pivot))"
    if name == "pivot_plus_col":
        pc = "(+ 1 (second pivot))"
    choose = "(cond (lr '(column)) (ab '(row)) (else '()))"
    if name == "row_priority":
        choose = "(cond (ab '(row)) (lr '(column)) (else '()))"
    elif name == "column_only":
        choose = "(if lr '(column) '())"
    elif name == "row_only":
        choose = "(if ab '(row) '())"
    elif name == "always_column":
        choose = "'(column)"
    elif name == "always_row":
        choose = "'(row)"
    elif name == "rotate180":
        choose = "'(diagonal)"
    elif name == "else_row":
        choose = "(if lr '(column) '(row))"
    elif name == "else_column":
        choose = "(cond (lr '(column)) (ab '(row)) (else '(column)))"
    elif name in ("both_original", "geometric_fourfold"):
        choose = "(append (if lr '(column) '()) (if ab '(row) '())" + (" (if (and lr ab) '(diagonal) '())" if name == "geometric_fourfold" else "") + ")"
    groups = "(list cells)"
    if name == "per_color":
        groups = "(filter (lambda (group) (not (empty? group))) (map (lambda (color) (filter (lambda (p) (= (at state (first p) (second p)) color)) cells)) (range 1 9)))"
    elif name in ("per_component", "largest_component_only"):
        objects = "(filter (lambda (o) (!= (obj-color o) 9)) (objects state 0))"
        if name == "largest_component_only":
            objects = f"(list (first (sort {objects} (lambda (a b) (if (= (obj-size a) (obj-size b)) (cell< (first (sort (obj-cells a) cell<)) (first (sort (obj-cells b) cell<))) (> (obj-size a) (obj-size b)))))))"
        groups = f"(map (lambda (o) (sort (obj-cells o) cell<)) {objects})"
    rr = "(if (equal? axis 'column) (first p) (- (* 2 pr) (first p)))"
    cc = "(if (equal? axis 'row) (second p) (- (* 2 pc) (second p)))"
    if name == "wrap":
        rr, cc = f"(modulo {rr} h)", f"(modulo {cc} w)"
    elif name == "clamp":
        rr, cc = f"(min (- h 1) (max 0 {rr}))", f"(min (- w 1) (max 0 {cc}))"
    reject = "(ormap (lambda (q) (not (in-bounds? (first q) (second q) h w))) targets)" if name == "reject_clipped" else "#f"
    cleared = "out"
    if name == "move_copy":
        cleared = "(for/fold ((acc out)) ((p (in-list group))) (set-cell acc (first p) (second p) 0))"
    elif name == "erase_clipped_sources":
        cleared = "(for/fold ((acc out)) ((p (in-list group)) (q (in-list targets))) (if (in-bounds? (first q) (second q) h w) acc (set-cell acc (first p) (second p) 0)))"
    color = "(at state (first p) (second p))"
    if name == "fixed_copies2":
        color = "2"
    elif name == "first_color_copies":
        color = "(at state (first (first cells)) (second (first cells)))"
    finish = "result"
    if name == "drop_pivot":
        finish = "(grid-from-fn h w (lambda (r c) (if (= (at result r c) 9) 0 (at result r c))))"
    elif name == "crop_result":
        finish = """(let ((nonzero (filter (lambda (p) (!= (at result (first p) (second p)) 0)) (grid-positions result))))
      (if (empty? nonzero) '((0)) (let ((bb (bbox-of-cells nonzero)))
        (subgrid result (first bb) (second bb) (third bb) (fourth bb)))))"""
    return f"""(rule! (let ()
  (define (step state)
    (let ((pivots (find-color state 9))
          (cells (filter (lambda (p) (not (member? (at state (first p) (second p)) '(0 9)))) (grid-positions state))))
      (if (or (empty? pivots) (empty? cells)) state
        (let* ((pivot (first pivots)) (pr {pr}) (pc {pc}))
          (define (axes group)
            (let ((lr (or (< (apply max (map second group)) pc) (> (apply min (map second group)) pc)))
                  (ab (or (< (apply max (map first group)) pr) (> (apply min (map first group)) pr))))
              {choose}))
          (define groups {groups})
          (define (copy-axis out group axis)
            (let ((targets (map (lambda (p) (list {rr} {cc})) group)))
              (if {reject} out
                (for/fold ((acc {cleared})) ((p (in-list group)) (q (in-list targets)))
                  (if (in-bounds? (first q) (second q) h w)
                    (set-cell acc (first q) (second q) {color}) acc)))))
          (for/fold ((out state)) ((group (in-list groups)))
            (for/fold ((acc out)) ((axis (in-list (axes group)))) (copy-axis acc group axis)))))))
  (define result (for/fold ((state g)) ((iteration (in-range {count}))) (step state)))
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
    spec = importlib.util.spec_from_file_location("_abe8a3c35e86_frozen_native_audit", HOME / "native_family.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def facts(grid, output):
    pivot = next(((r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 9), None)
    stage = one_pass(grid)
    cells = lambda g: [(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v not in (0,9)]
    return {"input_shape": [len(grid),len(grid[0])], "output_shape": [len(output),len(output[0])],
        "pivot": pivot, "input_occupied": sum(bool(v) for row in grid for v in row),
        "first_axes": axes(cells(grid), *pivot) if pivot else [],
        "second_axes": axes(cells(stage), *pivot) if pivot else [],
        "input_sha256":sha(packed(grid)), "output_sha256":sha(packed(output))}


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
    report = {"schema": "abe8a3c35e86-independent-teaching-audit-v1", "status": "running",
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
                        candidates = [("declared:passes=" + str(other["passes"]), family.program(other),
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
                        intended_name = "declared:passes=" + str(mode)
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


