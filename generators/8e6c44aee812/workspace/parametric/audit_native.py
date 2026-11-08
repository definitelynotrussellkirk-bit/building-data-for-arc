"""Finite protected-Racket audit of short-context staircase continuation.

Fit hypotheses to visible demonstrations before checking their query answers.
Keep full programs, inputs, outputs and source bindings in private evidence.
This bounded authoring gate grants neither acceptance nor training admission.
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
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


SETTINGS = ({"output_scale": 2}, {"output_scale": 3})
JOBS = ((0, 2), (17, 3), (22, 6))
RIVALS = ("tile_whole_input", "row_only", "column_only", "min_axis",
          "keep_terminal_zero", "always_drop_last", "deduplicate_active",
          "first_run_per_color", "first_color_exempt_first_run",
          "other_colors_exempt_first_run", "collapse_contiguous_runs",
          "fixed_period_four", "color_count_period", "first_repeat_period",
          "fixed_output_ten", "stop_at_last_band")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"output_scale"}
            or type(settings["output_scale"]) is not int
            or settings["output_scale"] not in (2, 3)):
        raise ValueError("Expected one exact output_scale setting")
    return settings["output_scale"]


def _active(grid):
    values = [grid[i][i] for i in range(min(len(grid), len(grid[0])))]
    while values and values[-1] == 0:
        values.pop()
    if not values:
        raise ValueError("No active staircase period")
    return values


def _runs(values):
    groups = []
    for value in values:
        if groups and groups[-1][0] == value:
            groups[-1].append(value)
        else:
            groups.append([value])
    return groups


def rival_reference(grid, settings, name):
    """Independent list/array meaning; does not call the production mirror."""
    scale = _setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    grid = _grid(grid)
    active = _active(grid)
    sequence = active[:]
    if name == "keep_terminal_zero":
        sequence = [grid[i][i] for i in range(len(grid))]
    elif name == "always_drop_last":
        sequence = [grid[i][i] for i in range(len(grid) - 1)]
    elif name == "deduplicate_active":
        sequence = list(dict.fromkeys(active))
    elif name == "collapse_contiguous_runs":
        sequence = [run[0] for run in _runs(active)]
    elif name in ("first_run_per_color", "first_color_exempt_first_run", "other_colors_exempt_first_run"):
        seen, sequence = set(), []
        for run in _runs(active):
            value = run[0]
            exempt = ((name == "first_color_exempt_first_run" and value == active[0])
                      or (name == "other_colors_exempt_first_run" and value != active[0]))
            if exempt or value not in seen:
                sequence.extend(run)
            seen.add(value)
    elif name == "fixed_period_four":
        sequence = active[:4]
    elif name == "color_count_period":
        sequence = active[:len(set(active))]
    elif name == "first_repeat_period":
        following = [i for i, value in enumerate(active[1:], 1) if value == active[0]]
        sequence = active[:following[0]] if following else active[:]
    height = width = 10 if name == "fixed_output_ten" else scale * len(grid)
    if name == "tile_whole_input":
        return [[grid[r % len(grid)][c % len(grid[0])] for c in range(width)]
                for r in range(height)]
    def color(r, c):
        index = r if name == "row_only" else c if name == "column_only" else min(r, c) if name == "min_axis" else max(r, c)
        index = min(index, len(sequence) - 1) if name == "stop_at_last_band" else index % len(sequence)
        return sequence[index]
    return [[color(r, c) for c in range(width)] for r in range(height)]


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    """Complete executable programs, including the color-role run hypotheses."""
    scale = _setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    sequence = {
        "keep_terminal_zero": "raw",
        "always_drop_last": "(take raw (- (length raw) 1))",
        "deduplicate_active": "(remove-duplicates active)",
        "collapse_contiguous_runs": "(squash active)",
        "first_run_per_color": "(keep-runs active 0)",
        "first_color_exempt_first_run": "(keep-runs active 1)",
        "other_colors_exempt_first_run": "(keep-runs active 2)",
        "fixed_period_four": "(take active (min 4 (length active)))",
        "color_count_period": "(take active (length (remove-duplicates active)))",
        "first_repeat_period": "(take active (first-return active))",
    }.get(name, "active")
    metric = {"row_only": "r", "column_only": "c", "min_axis": "(min r c)"}.get(name, "(max r c)")
    index = f"(min {metric} (- (length sequence) 1))" if name == "stop_at_last_band" else f"(remainder {metric} (length sequence))"
    cell = "(at g (remainder r (rows g)) (remainder c (cols g)))" if name == "tile_whole_input" else f"(list-ref sequence {index})"
    height = "10" if name == "fixed_output_ten" else f"(* (rows g) {scale})"
    width = "10" if name == "fixed_output_ten" else f"(* (cols g) {scale})"
    return f"""(rule! (lambda (g)
  (define raw (for/list ((i (range 0 (min (rows g) (cols g))))) (at g i i)))
  (define active (let trim ((xs raw))
    (if (or (empty? xs) (!= (last xs) 0)) xs (trim (take xs (- (length xs) 1))))))
  (define (keep-runs xs mode)
    (let loop ((left xs) (previous -1) (seen (list)) (keep #t) (result (list)))
      (if (empty? left) (reverse result)
        (let* ((v (first left))
               (exempt (or (and (= mode 1) (= v (first xs)))
                           (and (= mode 2) (!= v (first xs)))))
               (chosen (if (= v previous) keep (or exempt (not (member v seen))))))
          (loop (rest left) v (cons v seen) chosen (if chosen (cons v result) result))))))
  (define (squash xs)
    (let loop ((left xs) (previous -1) (result (list)))
      (if (empty? left) (reverse result)
        (loop (rest left) (first left)
              (if (= (first left) previous) result (cons (first left) result))))))
  (define (first-return xs)
    (let loop ((left (rest xs)) (index 1))
      (if (empty? left) (length xs)
        (if (= (first left) (first xs)) index (loop (rest left) (+ index 1))))))
  (let ((sequence {sequence}))
    (grid-from-fn {height} {width} (lambda (r c) {cell})))))"""


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


def assess(name, program, train, test, execute):
    outputs = [execute(program, pair["input"]) for pair in train]
    rejected = [i for i, (out, pair) in enumerate(zip(outputs, train)) if out != pair["output"]]
    survives, prefix = not rejected, not any(i < 2 for i in rejected)
    checked_for = (["all_demonstrations"] if survives else []) + (["first_two_prefix"] if prefix else [])
    queries = [execute(program, pair["input"]) for pair in test] if checked_for else None
    differences = ([i for i, (out, pair) in enumerate(zip(queries, test)) if out != pair["output"]]
                   if queries is not None else None)
    return {"name": name, "program_sha256": sha(program.encode()), "demo_outputs": outputs,
            "rejected_by_demo_indices": rejected, "survives_demonstrations": survives,
            "survives_first_two": prefix, "query_checked_for": checked_for,
            "query_outputs": queries, "query_disagreement_indices": differences}


def scene_facts(grid, settings):
    grid = _grid(grid)
    output = reference(grid, settings)
    active = _active(grid)
    h, w = len(output), len(output[0])
    points = [(r, c) for r, row in enumerate(output) for c, color in enumerate(row) if color]
    diagonal = [output[i][i] for i in range(h)]
    return {"input_shape": [len(grid), len(grid[0])], "output_shape": [h, w],
            "active_diagonal": active, "period": len(active),
            "padding_cells": len(grid) - len(active), "colors": sorted(set(active)),
            "output_foreground_cells": len(points),
            "occupied_rows": len({r for r, c in points}),
            "occupied_columns": len({c for r, c in points}),
            "diagonal_color_transitions": sum(a != b for a, b in zip(diagonal, diagonal[1:])),
            "quadrant_foreground": [sum((r >= h // 2) == bottom and (c >= w // 2) == right for r, c in points)
                                    for bottom, right in ((False, False), (False, True), (True, False), (True, True))]}


def _load(path):
    name = "_staircase_audit_" + sha(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_binding():
    paths = list(HOME.glob("*.py")) + list((TASK / "tests").glob("*.py")) + list(HOME.glob("*.rkt"))
    paths += [TASK / "generator.py", HOME / "promotion.json", ROOT / "shared/data/canonical/puzzles.jsonl",
              ROOT / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths)) if p.is_file()}


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    private.mkdir()
    report = {"schema": "8e6c44aee812-native-finite-audit-v1", "status": "running",
              "visibility": "controller_private", "training_admitted": False,
              "source_files_sha256": source_binding(), "settings": deepcopy(SETTINGS),
              "jobs": [{"seed": seed, "demos": demos, "queries": 4} for seed, demos in JOBS],
              "extra_rivals": list(RIVALS), "programs": {}, "episodes": [],
              "findings": [], "first_two_prefix_findings": [],
              "limits": "Six episodes, two declared settings and sixteen extra executable rules. Demonstration survivors are frozen before queries. No universal identifiability, owner acceptance or training admission."}
    bridge, engine, phase = None, None, "setup"
    try:
        with _local_imports(RUNTIME, HOME):
            from arcpuzzles import Catalog
            adapter = _load(HOME / "adapter.py")
            apply, identity, bridge = _real_evaluator(RUNTIME)
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise ValueError("Protected Racket is required")
            report["racket"] = identity
            engine = CachedEvaluator(apply)
            programs = {s["output_scale"]: adapter.program(deepcopy(s)) for s in SETTINGS}
            canonical = {v["program_solution"] for v in Catalog(ROOT).get("8e6c44aee812")["variants"]
                         if isinstance(v.get("program_solution"), str)}
            if canonical != {programs[2]}:
                raise AssertionError("Native default differs from exact canonical source")
            def retain(program):
                identifier = sha(program.encode())
                report["programs"][identifier] = program
                return identifier
            for seed, demos in JOBS:
                shared = None
                for settings in SETTINGS:
                    scale = settings["output_scale"]
                    phase = f"generate:{seed}:{demos}:{scale}"
                    episode = adapter.generate(seed, deepcopy(settings), demos, 4)
                    if episode["program_solution"] != programs[scale]:
                        raise AssertionError("Episode does not retain its exact setting program")
                    pairs = {}
                    for split, count in (("train", demos), ("test", 4)):
                        if type(episode[split]) is not list or len(episode[split]) != count:
                            raise ValueError("Incorrect demonstration/query count")
                        pairs[split] = [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in episode[split]]
                    inputs = [p["input"] for p in pairs["train"] + pairs["test"]]
                    if len({packed(g) for g in inputs}) != len(inputs):
                        raise AssertionError("Episode inputs are not distinct")
                    if shared is not None and shared != inputs:
                        raise AssertionError("Input draws differ across settings")
                    shared = inputs
                    phase = f"reference:{seed}:{demos}:{scale}"
                    for pair in pairs["train"] + pairs["test"]:
                        actual = engine(programs[scale], pair["input"])
                        if actual != pair["output"] or actual != reference(pair["input"], settings):
                            raise AssertionError("Claimed label or independent reference differs from Racket")
                    facts = [scene_facts(g, settings) for g in inputs]
                    record = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                              "program_sha256": retain(programs[scale]), **pairs, "hypotheses": [],
                              "scene_facts": {"train": facts[:demos], "test": facts[demos:]}}
                    report["episodes"].append(record)
                    hypotheses = [("declared:" + str(s["output_scale"]), programs[s["output_scale"]], s) for s in SETTINGS]
                    hypotheses += [(name, rival_program(settings, name), None) for name in RIVALS]
                    survivors = []
                    for name, program, declared in hypotheses:
                        phase = f"hypothesis:{seed}:{demos}:{scale}:{name}"
                        retain(program)
                        def execute(source, grid, name=name, declared=declared):
                            actual = engine(source, grid)
                            expected = reference(grid, declared) if declared is not None else rival_reference(grid, settings, name)
                            if actual != expected:
                                raise AssertionError("Racket hypothesis differs from independent meaning: " + name)
                            return actual
                        row = assess(name, program, pairs["train"], pairs["test"], execute)
                        record["hypotheses"].append(row)
                        if declared is not None and row["survives_demonstrations"]:
                            survivors.append(declared["output_scale"])
                        finding = {"episode_index": len(report["episodes"]) - 1, "seed": seed,
                                   "settings": deepcopy(settings), "rival": name, "query_indices": row["query_disagreement_indices"]}
                        if row["survives_demonstrations"] and row["query_disagreement_indices"]:
                            report["findings"].append(dict(finding, kind="demo_survivor_query_disagreement"))
                        if row["survives_first_two"] and row["query_disagreement_indices"]:
                            report["first_two_prefix_findings"].append(dict(finding, kind="prefix_survivor_query_disagreement"))
                    record["declared_survivors"] = survivors
                    record["extra_survivors"] = [r["name"] for r in record["hypotheses"] if not r["name"].startswith("declared:") and r["survives_demonstrations"]]
                    if survivors != [scale]:
                        report["findings"].append({"kind": "declared_setting_not_identified", "episode_index": len(report["episodes"]) - 1})
                    stress = facts[-1]
                    side = 10 * scale
                    stress_ok = (stress["input_shape"] == [10, 10] and stress["output_shape"] == [side, side]
                                 and stress["period"] == 9 and stress["padding_cells"] == 1
                                 and stress["output_foreground_cells"] == side * side
                                 and stress["diagonal_color_transitions"] >= 8 and len(stress["colors"]) >= 3)
                    record["stress_check"] = {"passed": stress_ok,
                        "scope": "10x10 input, nine active bands plus zero padding, full foreground 20x20 or30x30 output, at least eight color transitions and three colors."}
                    if not stress_ok:
                        report["findings"].append({"kind": "insufficient_large_continuation", "episode_index": len(report["episodes"]) - 1, "facts": stress})
                    print(json.dumps({"seed": seed, "demos": demos, "output_scale": scale,
                                      "racket_evaluations": engine.evaluations,
                                      "extra_survivors": record["extra_survivors"],
                                      "findings": len(report["findings"]),
                                      "prefix_findings": len(report["first_two_prefix_findings"])}), flush=True)
            if source_binding() != report["source_files_sha256"]:
                raise AssertionError("Source bytes changed during audit")
            report["reference_label_count"] = sum(demos + 4 for seed, demos in JOBS) * 2
            report["matched_inputs_across_settings"] = True
            report["status"] = "failed" if report["findings"] or report["first_two_prefix_findings"] else "passed"
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error),
                                       "last_native_request": engine.last_request if engine else None}
    finally:
        if bridge is not None:
            bridge.close()
        if engine is not None:
            report["execution"] = {"requests": engine.requests, "racket_evaluations": engine.evaluations,
                "cache_hits": engine.cache_hits, "successful_cached_results": len(engine.cache),
                "cache_key": "exact complete program and exact validated grid"}
        target = private / "audit.json"
        target.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "report": str(target), "findings": len(report["findings"]),
                      "prefix_findings": len(report["first_two_prefix_findings"]),
                      "execution_failure": report.get("execution_failure")}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    result = run(parser.parse_args().out)
    raise SystemExit(0 if result["status"] == "passed" else 1)
