#!/usr/bin/env python3
"""Bounded protected-Racket audit of the native gravity family's teaching.

Run through review.py, with --out pointing to a fresh checks directory. This
script owns only its evidence output. Every executed rule is a rule! form.
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

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


TASK = "2a43e4f3a796"
HOME = Path(__file__).resolve().parent
SEEDS = (0, 17)
KINDS = ("reverse", "sort_ascending", "sort_descending", "deduplicate",
         "gray_barrier", "cap_five", "zero_modal_cap_five", "modal_background",
         "drop_destination_edge", "rigid_translation", "identity")


def digest(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def independent(grid, direction, kind="stable"):
    """Independent list implementation used to validate rival program meaning."""
    vertical, end = direction in ("down", "up"), direction in ("down", "right")
    counts = Counter(value for row in grid for value in row)
    modal = min(counts, key=lambda value: (-counts[value], value))
    background = modal if kind == "modal_background" else 0
    lines = [list(line) for line in zip(*grid)] if vertical else deepcopy(grid)

    def packed(values, length, bg=0):
        padding = [bg] * (length - len(values))
        return padding + values if end else values + padding

    def plain(line):
        return packed([value for value in line if value != 0], len(line))

    result = []
    for original in lines:
        line = list(original)
        if kind == "identity":
            result.append(line)
            continue
        if kind == "gray_barrier":
            previous, out = -1, []
            for stop in [i for i, value in enumerate(line) if value == 5] + [len(line)]:
                out.extend(plain(line[previous + 1:stop]))
                if stop < len(line):
                    out.append(5)
                previous = stop
            result.append(out)
            continue
        if kind == "rigid_translation":
            occupied = [i for i, value in enumerate(line) if value != 0]
            out = [0] * len(line)
            if occupied:
                shift = len(line) - 1 - occupied[-1] if end else -occupied[0]
                for index in occupied:
                    out[index + shift] = line[index]
            result.append(out)
            continue
        if kind == "drop_destination_edge":
            line[-1 if end else 0] = 0
        values = [value for value in line if value != background]
        if kind == "reverse":
            values.reverse()
        elif kind == "sort_ascending":
            values.sort()
        elif kind == "sort_descending":
            values.sort(reverse=True)
        elif kind == "deduplicate":
            values = list(dict.fromkeys(values))
        elif kind == "cap_five" or (kind == "zero_modal_cap_five" and modal == 0):
            values = values[-5:] if end else values[:5]
        result.append(packed(values, len(line), background))
    return [list(line) for line in zip(*result)] if vertical else result


def rival_program(direction, kind):
    """Return one complete executable rival, with the chosen gravity fixed."""
    vertical = "#t" if direction in ("down", "up") else "#f"
    end = "#t" if direction in ("down", "right") else "#f"
    mode_bindings = "(global-mode 0)"
    if kind in ("zero_modal_cap_five", "modal_background"):
        mode_bindings = """(flat (apply append g))
         (counts (for/list ((color (in-range 10)))
                   (length (filter (lambda (value) (= value color)) flat))))
         (global-mode (for/fold ((best 0)) ((color (in-range 1 10)))
                        (if (> (list-ref counts color) (list-ref counts best)) color best)))"""
    values = "(filter (lambda (value) (not (= value 0))) line)"
    trims = """(if (> (length values) 5)
                    (if end? (drop values (- (length values) 5)) (take values 5))
                    values)"""
    transformations = {
        "reverse": "(reverse values)",
        "sort_ascending": "(sort values <)",
        "sort_descending": "(sort values >)",
        "deduplicate": "(remove-duplicates values)",
        "cap_five": trims,
        "zero_modal_cap_five": f"(if (= global-mode 0) {trims} values)",
    }
    if kind in transformations:
        operation = f"(let ((values {values})) (pack-values (length line) {transformations[kind]} 0))"
    elif kind == "modal_background":
        operation = "(base-pack line global-mode)"
    elif kind == "identity":
        operation = "line"
    elif kind == "drop_destination_edge":
        operation = """(base-pack
          (if end? (append (take line (- (length line) 1)) (list 0))
                   (cons 0 (rest line))) 0)"""
    elif kind == "gray_barrier":
        operation = """(let loop ((remaining line) (chunk (list)) (out (list)))
          (cond ((null? remaining) (append out (base-pack (reverse chunk) 0)))
                ((= (first remaining) 5)
                 (loop (rest remaining) (list)
                       (append out (base-pack (reverse chunk) 0) (list 5))))
                (else (loop (rest remaining) (cons (first remaining) chunk) out))))"""
    elif kind == "rigid_translation":
        operation = """(let ((occupied (filter (lambda (i) (not (= (list-ref line i) 0)))
                                                (range (length line)))))
          (if (null? occupied) line
              (let ((shift (if end? (- (- (length line) 1) (last occupied))
                                   (- (first occupied)))))
                (for/list ((i (in-range (length line))))
                  (let ((source (- i shift)))
                    (if (and (>= source 0) (< source (length line)))
                        (list-ref line source) 0))))))"""
    else:
        raise ValueError(f"Unknown rival kind: {kind}")
    return f"""(rule! (lambda (g)
  (let* ((height (length g)) (width (length (car g)))
         (vertical? {vertical}) (end? {end})
         {mode_bindings})
    (define (pack-values size values background)
      (let ((padding (make-list (- size (length values)) background)))
        (if end? (append padding values) (append values padding))))
    (define (base-pack line background)
      (pack-values (length line)
        (filter (lambda (value) (not (= value background))) line) background))
    (define (process line) {operation})
    (let* ((lines (if vertical?
                     (for/list ((c (in-range width)))
                       (for/list ((r (in-range height))) (list-ref (list-ref g r) c)))
                     g))
           (packed (map process lines)))
      (if vertical?
          (for/list ((r (in-range height)))
            (for/list ((c (in-range width))) (list-ref (list-ref packed c) r)))
          packed)))))
"""


def first_difference(expected, actual):
    if [len(expected), len(expected[0])] != [len(actual), len(actual[0])]:
        return {"kind": "shape", "expected": [len(expected), len(expected[0])],
                "actual": [len(actual), len(actual[0])]}
    for row in range(len(expected)):
        for col in range(len(expected[0])):
            if expected[row][col] != actual[row][col]:
                return {"kind": "cell", "row": row, "col": col,
                        "expected": expected[row][col], "actual": actual[row][col]}
    return None


class Executor:
    def __init__(self, runtime):
        self.apply, self.identity, self.bridge = _real_evaluator(runtime)
        self.cache, self.programs, self.errors = {}, {}, []
        self.evaluations = 0

    def execute(self, program, grid):
        key = digest(program), digest(grid)
        self.programs[key[0]] = program
        if key not in self.cache:
            self.evaluations += 1
            try:
                self.cache[key] = _grid(self.apply(program, deepcopy(grid)))
            except Exception as exc:
                self.errors.append({"program_sha256": key[0], "input_sha256": key[1],
                                    "type": type(exc).__name__, "message": str(exc)})
                raise
        return deepcopy(self.cache[key])


def audit_episode(executor, adapter, gravity, exporter, seed, direction, output):
    settings = {"gravity": direction}
    generated = adapter.generate(seed, settings, 2, 4)
    program = adapter.program(settings)
    if generated["program_solution"] != program:
        raise ValueError("Native episode changes the exact setting program")
    for split in ("train", "test"):
        for pair in generated[split]:
            actual = executor.execute(program, pair["input"])
            if actual != pair["output"] or actual != independent(pair["input"], direction):
                raise ValueError("Protected label differs from a Python claim or independent packing")
            pair["output"] = actual
    inventory = [("direction:" + other, adapter.program({"gravity": other}), other, "stable")
                 for other in gravity.DIRECTIONS if other != direction]
    inventory += [(kind, rival_program(direction, kind), direction, kind) for kind in KINDS]
    checks = []
    for name, source, rival_direction, kind in inventory:
        demo_checks = []
        for index, pair in enumerate(generated["train"]):
            prediction = executor.execute(source, pair["input"])
            if prediction != independent(pair["input"], rival_direction, kind):
                raise ValueError(f"Rival program does not implement its declared Python meaning: {name}")
            mismatch = first_difference(pair["output"], prediction)
            demo_checks.append({"demo_index": index, "matches": mismatch is None,
                                "output_sha256": digest(prediction), "first_difference": mismatch})
            if mismatch is not None:
                break
        survives = len(demo_checks) == 2 and all(check["matches"] for check in demo_checks)
        queries = []
        if survives:
            for index, pair in enumerate(generated["test"]):
                prediction = executor.execute(source, pair["input"])
                if prediction != independent(pair["input"], rival_direction, kind):
                    raise ValueError(f"Query rival encoding mismatch: {name}")
                mismatch = first_difference(pair["output"], prediction)
                queries.append({"query_index": index, "matches": mismatch is None,
                                "output_sha256": digest(prediction), "first_difference": mismatch})
        checks.append({"name": name, "program_sha256": digest(source), "demo_checks": demo_checks,
                       "survives_both_demos": survives, "query_checks": queries})
    ambiguous = [check["name"] for check in checks if check["survives_both_demos"]
                 and any(not query["matches"] for query in check["query_checks"])]
    short = adapter.generate(seed, settings, 2, 1)
    if (short["program_solution"] != program or short["train"] != generated["train"]
            or short["test"] != generated["test"][:1]):
        raise ValueError("One-query claims differ from the protected four-query prefix")
    episode = {"task_id": TASK, "seed": seed, "settings": settings,
               "program": program, "program_sha256": digest(program),
               "pairs": {"train": generated["train"], "test": generated["test"]},
               "racket": executor.identity, "labels": "protected_racket_execution"}
    short_episode = deepcopy(episode)
    short_episode["pairs"]["test"] = short_episode["pairs"]["test"][:1]
    full_export = exporter.export_episode(output / "exports", episode)
    short_export = exporter.export_episode(output / "exports", short_episode)
    if (full_export["turn_ids"][0] != short_export["turn_ids"][0]
            or exporter.public_first_turn(episode) != exporter.public_first_turn(short_episode)):
        raise ValueError("First public solver turn changes with total query count")
    turn_path = output / "exports" / full_export["turns"][0]["path"]
    visible = json.loads(turn_path.read_bytes())
    if (set(visible) != {"train", "test"} or len(visible["test"]) != 1
            or set(visible["test"][0]) != {"input"}):
        raise ValueError("First solver turn contains query labels, future queries or metadata")
    return {"seed": seed, "settings": settings, "program_sha256": digest(program),
            "input_shapes": [[len(pair["input"]), len(pair["input"][0])]
                             for pair in generated["train"] + generated["test"]],
            "rivals": checks, "ambiguous_rivals": ambiguous,
            "demo_survivors": [check["name"] for check in checks if check["survives_both_demos"]],
            "python_claims_equal_racket": True, "independent_labels_equal_racket": True,
            "single_turn_invariance": True, "full_export": full_export, "short_export": short_export}


def audit_edges(executor, adapter, gravity):
    tape = [3, 7, 0, 5, 3, 0, 5, 3, 0, 7] * 3
    edges = {"blank_1x1": [[0]], "foreground_1x1": [[5]],
             "full_2x3": [[5, 3, 7], [3, 5, 3]],
             "row_1x30": [tape], "column_30x1": [[value] for value in tape]}
    result = []
    for name, grid in edges.items():
        for direction in gravity.DIRECTIONS:
            program = adapter.program({"gravity": direction})
            actual = executor.execute(program, grid)
            if actual != gravity.transform(grid, direction) or actual != independent(grid, direction):
                raise ValueError(f"Edge label mismatch: {name}/{direction}")
            result.append({"name": name, "gravity": direction, "input": grid, "output": actual,
                           "program_sha256": digest(program)})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root, output = Path.cwd().resolve(), args.out.resolve()
    if output.exists():
        raise ValueError("Choose a fresh audit output directory")
    adapter = load(HOME / "adapter.py", "_gravity_adapter_audit")
    gravity = load(HOME / "gravity.py", "_gravity_family_audit")
    exporter = load(HOME / "exporter.py", "_gravity_exporter_audit")
    selected = Catalog(root).get(TASK)
    sources = {variant["program_solution"] for variant in selected["variants"]}
    if len(sources) != 1 or adapter.program({"gravity": "down"}) != next(iter(sources)):
        raise ValueError("Down is not the exact unique selected canonical program")
    paths = [root / selected["generator"], HOME / "adapter.py", HOME / "gravity.py",
             HOME / "exporter.py", HOME / "canonical.rkt", Path(__file__).resolve()]
    hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    result = {"schema": "arcpuzzles-bounded-gravity-teaching-audit-v1", "task_id": TASK,
              "status": "running", "private": True, "source_hashes": hashes,
              "generator_sha256": selected["generator_sha256"], "rule_hash": selected["rule_hash"],
              "scope": {"seeds": list(SEEDS), "settings": 4, "demos": 2, "queries": 4,
                        "rivals_per_setting": 14, "edge_cases_per_setting": 5},
              "episodes": [],
              "limits": "Bounded source-specific evidence against named rivals only. Queries are checked only for demo-surviving rivals. Runtime errors and rival-encoding mismatches fail; they never count as refutations. No owner acceptance or training admission."}
    executor = None
    output.mkdir(parents=True)
    try:
        runtime = root / "shared/runtime"
        with _local_imports(runtime, HOME):
            executor = Executor(runtime)
            result["racket"] = executor.identity
            try:
                for seed in SEEDS:
                    for direction in gravity.DIRECTIONS:
                        episode = audit_episode(executor, adapter, gravity, exporter,
                                                seed, direction, output)
                        result["episodes"].append(episode)
                        if episode["ambiguous_rivals"]:
                            print(json.dumps({"finding": "surviving_rival_query_disagreement",
                                              "seed": seed, "gravity": direction,
                                              "rivals": episode["ambiguous_rivals"]}), flush=True)
                result["edge_cases"] = audit_edges(executor, adapter, gravity)
            finally:
                executor.bridge.close()
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != hashes[str(path.relative_to(root))]
               for path in paths):
            raise ValueError("Audited source changed during execution; rerun on frozen source")
        result["status"] = ("failed" if executor.errors or any(e["ambiguous_rivals"] for e in result["episodes"])
                            else "passed_finite_rivals")
    except Exception as exc:
        result["status"] = "failed"
        result["fatal_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if executor is not None:
            result["actual_racket_evaluations"] = executor.evaluations
            result["execution_errors"] = executor.errors
            rules = output / "private/rules"
            rules.mkdir(parents=True)
            for identity, source in executor.programs.items():
                (rules / (identity + ".rkt")).write_text(source)
            result["program_paths"] = {identity: "private/rules/" + identity + ".rkt"
                                       for identity in executor.programs}
        (output / "audit.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"status": result["status"], "episodes": len(result["episodes"]),
                      "edge_cases": len(result.get("edge_cases", [])),
                      "racket_evaluations": result.get("actual_racket_evaluations", 0),
                      "execution_errors": len(result.get("execution_errors", [])),
                      "fatal_error": result.get("fatal_error"), "out": str(output)}, indent=2))
    return 0 if result["status"] == "passed_finite_rivals" else 1


if __name__ == "__main__":
    raise SystemExit(main())
