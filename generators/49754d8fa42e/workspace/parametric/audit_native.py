"""Finite same-checkout protected-Racket audit for mode-selected glyph policies.

Run through the packet launcher from its outer directory, using a fresh output::

    python review.py run python3 \
      generators/49754d8fa42e/workspace/parametric/audit_native.py \
      --out generators/49754d8fa42e/workspace/parametric/evidence/native-current

The audit retains controller-private programs, inputs, labels and rival results.
It neither changes public examples nor grants native acceptance or training use.
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


HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK = HOME.parents[1]
RUNTIME = ROOT / "shared/runtime"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


SETTINGS = ({"orientation": "canonical"}, {"orientation": "modal_components"})
JOBS = ((0, 2), (17, 3), (22, 6))
SELECTORS = (
    "first_nonzero", "last_nonzero", "smallest_nonzero", "largest_nonzero",
    "least_frequent_nonzero", "endpoint_complement", "endpoint_limited_mode",
    "largest_component_4", "largest_component_8", "largest_color_bbox",
)
TOPOLOGY = (
    "count_modal_8", "count_all_objects", "count_modal_cells", "parity_only",
    "fragmented_once", "opposite_rotation", "off_by_one",
)
COLOR_GATED = ("rotate_only_color_2", "rotate_only_color_3")
GLYPHS = {
    1: [[0, 5, 0], [5, 5, 5], [0, 5, 0]],
    2: [[5, 5, 5], [0, 5, 0], [0, 5, 0]],
    3: [[0, 0, 5], [0, 0, 5], [5, 5, 5]],
}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _load(path):
    name = "_mode_glyph_audit_" + digest(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load current task source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _orientation(settings):
    if (type(settings) is not dict or set(settings) != {"orientation"}
            or type(settings["orientation"]) is not str
            or settings["orientation"] not in ("canonical", "modal_components")):
        raise ValueError("Expected exactly one declared orientation setting")
    return settings["orientation"]


def _objects(grid, diagonal=False):
    """Independent pixel flood fill; does not trust sampler metadata/helpers."""
    height, width = len(grid), len(grid[0])
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        steps += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    seen, result = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if not color or (r, c) in seen:
                continue
            seen.add((r, c))
            pending, cells = [(r, c)], []
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for dr, dc in steps:
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < height and 0 <= nc < width and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append({"color": color, "cells": cells, "size": len(cells)})
    return result


def _counts_and_mode(grid):
    counts = Counter(value for row in grid for value in row if value)
    if not counts:
        raise ValueError("Scene must have a unique nonzero mode")
    largest = max(counts.values())
    winners = [color for color, count in counts.items() if count == largest]
    if len(winners) != 1 or winners[0] not in (1, 2, 3):
        raise ValueError("Scene must have a unique nonzero mode in colors 1, 2, 3")
    return counts, winners[0]


def _bbox(points):
    return [min(r for r, _ in points), min(c for _, c in points),
            max(r for r, _ in points), max(c for _, c in points)]


def _bbox_area(points):
    r1, c1, r2, c2 = _bbox(points)
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def scene_facts(grid):
    grid = _grid(grid)
    height, width = len(grid), len(grid[0])
    if min(height, width) < 8:
        raise ValueError("Composition scenes must be 8..30 on both dimensions")
    counts, mode = _counts_and_mode(grid)
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    objects4, objects8 = _objects(grid), _objects(grid, True)
    modal4 = [obj for obj in objects4 if obj["color"] == mode]
    modal8 = [obj for obj in objects8 if obj["color"] == mode]
    areas = {color: _bbox_area([(r, c) for r, row in enumerate(grid)
                              for c, value in enumerate(row) if value == color])
             for color in counts}
    return {
        "shape": [height, width], "nonzero_cells": len(points),
        "density": len(points) / (height * width),
        "mode_color": mode, "mode_count": counts[mode],
        "runner_up_count": max((n for c, n in counts.items() if c != mode), default=0),
        "counts_by_color": {str(c): counts[c] for c in sorted(counts)},
        "objects_4": len(objects4), "objects_8": len(objects8),
        "modal_components_4": len(modal4), "modal_components_8": len(modal8),
        "modal_component_sizes_4": sorted((obj["size"] for obj in modal4), reverse=True),
        "modal_component_sizes_8": sorted((obj["size"] for obj in modal8), reverse=True),
        "modal_component_quarter_turns": (len(modal4) - 1) % 4,
        "occupied_rows": len({r for r, _ in points}),
        "occupied_columns": len({c for _, c in points}),
        "nonzero_bbox": _bbox(points),
        "modal_bbox": _bbox([(r, c) for r, row in enumerate(grid)
                             for c, value in enumerate(row) if value == mode]),
        "color_bbox_areas": {str(c): areas[c] for c in sorted(areas)},
        "contacts": {"top": any(r == 0 for r, _ in points),
                     "bottom": any(r == height - 1 for r, _ in points),
                     "left": any(c == 0 for _, c in points),
                     "right": any(c == width - 1 for _, c in points)},
        "quadrant_nonzero": [sum((r >= height // 2) == bottom and
                                  (c >= width // 2) == right for r, c in points)
                             for bottom, right in ((False, False), (False, True),
                                                   (True, False), (True, True))],
    }


def _glyph(color, turns):
    result = deepcopy(GLYPHS.get(color, [[0] * 3 for _ in range(3)]))
    for _ in range(turns % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def reference(grid, settings):
    counts, color = _counts_and_mode(grid)
    turns = 0
    if _orientation(settings) == "modal_components":
        turns = (sum(obj["color"] == color for obj in _objects(grid)) - 1) % 4
    return _glyph(color, turns)


def rival_names():
    return SELECTORS + TOPOLOGY + COLOR_GATED + tuple(f"fixed_rotation_{n}" for n in range(4))


def _selected_color(grid, name):
    values = [value for row in grid for value in row if value]
    counts = Counter(values)
    if name == "first_nonzero":
        return values[0]
    if name == "last_nonzero":
        return values[-1]
    if name == "smallest_nonzero":
        return min(values)
    if name == "largest_nonzero":
        return max(values)
    if name == "least_frequent_nonzero":
        return min(counts, key=lambda c: (counts[c], c))
    if name == "endpoint_complement":
        return values[0] if values[0] == values[-1] else min({1, 2, 3} - {values[0], values[-1]})
    if name == "endpoint_limited_mode":
        return max({values[0], values[-1]}, key=lambda c: (counts[c], -c))
    if name in ("largest_component_4", "largest_component_8"):
        return max(_objects(grid, name.endswith("_8")), key=lambda o: (o["size"], -o["color"]))["color"]
    if name == "largest_color_bbox":
        points = {color: [(r, c) for r, row in enumerate(grid)
                          for c, value in enumerate(row) if value == color] for color in counts}
        return max(points, key=lambda c: (_bbox_area(points[c]), -c))
    raise ValueError("Unknown selector: " + name)


def rival_reference(grid, settings, name):
    orientation = _orientation(settings)
    if name not in rival_names():
        raise ValueError("Unknown rival: " + name)
    counts, modal_color = _counts_and_mode(grid)
    color = _selected_color(grid, name) if name in SELECTORS else modal_color
    objects = _objects(grid)
    k = sum(obj["color"] == color for obj in objects)
    if name in SELECTORS:
        turns = (k - 1) % 4 if orientation == "modal_components" else 0
    elif name == "count_modal_8":
        turns = (sum(obj["color"] == color for obj in _objects(grid, True)) - 1) % 4
    elif name == "count_all_objects":
        turns = (len(objects) - 1) % 4
    elif name == "count_modal_cells":
        turns = (counts[color] - 1) % 4
    elif name == "parity_only":
        turns = (k - 1) % 2
    elif name == "fragmented_once":
        turns = int(k > 1)
    elif name == "opposite_rotation":
        turns = (1 - k) % 4
    elif name == "off_by_one":
        turns = k % 4
    elif name in COLOR_GATED:
        turns = (k - 1) % 4 if color == int(name.rsplit("_", 1)[1]) else 0
    else:
        turns = int(name.rsplit("_", 1)[1])
    return _glyph(color, turns)


def _racket_grid(grid):
    return "(list " + " ".join("(list " + " ".join(map(str, row)) + ")" for row in grid) + ")"


def rival_program(settings, name):
    """Executable rivals: selectors feed both glyph lookup and object counting."""
    orientation = _orientation(settings)
    if name not in rival_names():
        raise ValueError("Unknown rival: " + name)
    selectors = {
        "first_nonzero": "(first values)", "last_nonzero": "(last values)",
        "smallest_nonzero": "(first colors)", "largest_nonzero": "(last colors)",
        "least_frequent_nonzero": "(pick-min colors count-value)",
        "endpoint_complement": "(if (= (first values) (last values)) (first values) "
            "(first (filter (lambda (c) (and (not (= c (first values))) "
            "(not (= c (last values))))) (list 1 2 3))))",
        "endpoint_limited_mode": "(pick-max (sort (remove-duplicates (list (first values) (last values))) <) count-value)",
        "largest_component_4": "(largest-object-color objs4)",
        "largest_component_8": "(largest-object-color objs8)",
        "largest_color_bbox": "(pick-max colors color-box-area)",
    }
    turns = {
        "count_modal_8": "(modulo (- k8 1) 4)",
        "count_all_objects": "(modulo (- (length objs4) 1) 4)",
        "count_modal_cells": "(modulo (- (count-value color) 1) 4)",
        "parity_only": "(modulo (- k4 1) 2)",
        "fragmented_once": "(if (> k4 1) 1 0)",
        "opposite_rotation": "(modulo (- 1 k4) 4)", "off_by_one": "(modulo k4 4)",
        **{f"rotate_only_color_{c}": f"(if (= color {c}) (modulo (- k4 1) 4) 0)" for c in (2, 3)},
        **{f"fixed_rotation_{n}": str(n) for n in range(4)},
    }
    selected = selectors.get(name, "(mode g 0)")
    turn = ("(modulo (- k4 1) 4)" if orientation == "modal_components" else "0") if name in SELECTORS else turns[name]
    glyph = "(cond " + " ".join(f"((= color {c}) {_racket_grid(g)})" for c, g in GLYPHS.items())
    glyph += " (else " + _racket_grid([[0] * 3 for _ in range(3)]) + "))"
    return f"""(rule! (lambda (g)
      (let* ((values (filter (lambda (v) (not (= v 0))) (apply append g)))
             (colors (sort (remove-duplicates values) <))
             (count-value (lambda (c) (length (filter (lambda (v) (= v c)) values))))
             (objs4 (objects g 0))
             (objs8 (objects-8 g 0))
             (largest-object-color
               (lambda (objs)
                 (obj-color (first (sort objs
                   (lambda (a b) (or (> (obj-size a) (obj-size b))
                     (and (= (obj-size a) (obj-size b)) (< (obj-color a) (obj-color b))))))))))
             (color-box-area
               (lambda (c) (let ((box (bbox-of-cells (cells-of-color g c))))
                 (* (+ 1 (- (third box) (first box))) (+ 1 (- (fourth box) (second box)))))))
             (color {selected})
             (k4 (length (filter (lambda (o) (= (obj-color o) color)) objs4)))
             (k8 (length (filter (lambda (o) (= (obj-color o) color)) objs8)))
             (turns {turn})
             (glyph {glyph}))
        (cond ((= turns 0) glyph)
              ((= turns 1) (rotate-cw glyph))
              ((= turns 2) (rotate-cw (rotate-cw glyph)))
              (else (rotate-cw (rotate-cw (rotate-cw glyph))))))))"""


class CachedEvaluator:
    """Successful exact program/input results only; any execution error escapes."""
    def __init__(self, apply):
        self.apply = apply
        self.cache = {}
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None

    def __call__(self, program, grid):
        grid = _grid(grid)
        if type(program) is not str or not program.strip():
            raise ValueError("Program must be nonempty exact Racket text")
        self.requests += 1
        key = (program, json_bytes(grid))
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.last_request = {"program_sha256": digest(program.encode()), "input_sha256": digest(key[1])}
        self.evaluations += 1
        result = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(result)
        return result


def assess_hypothesis(name, program, train, test, execute):
    """Freeze demo-only survivor decisions before evaluating any query."""
    outputs = [execute(program, pair["input"]) for pair in train]
    rejected = [i for i, (output, pair) in enumerate(zip(outputs, train)) if output != pair["output"]]
    survives = not rejected
    prefix_survives = not any(i < 2 for i in rejected)
    checked_for = (["all_demonstrations"] if survives else []) + (["first_two_prefix"] if prefix_survives else [])
    query_outputs = [execute(program, pair["input"]) for pair in test] if checked_for else None
    disagreement = ([i for i, (output, pair) in enumerate(zip(query_outputs, test)) if output != pair["output"]]
                    if query_outputs is not None else None)
    return {"name": name, "program_sha256": digest(program.encode()), "demo_outputs": outputs,
            "rejected_by_demo_indices": rejected, "survives_demonstrations": survives,
            "survives_first_two": prefix_survives, "query_checked_for": checked_for,
            "query_outputs": query_outputs, "query_disagreement_indices": disagreement}


def _episode(episode, demos, queries):
    if type(episode) is not dict or type(episode.get("program_solution")) is not str:
        raise ValueError("Native episode requires exact program_solution text")
    result = {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = episode.get(split)
        if type(pairs) is not list or len(pairs) != count:
            raise ValueError(f"Incorrect {split} count")
        result[split] = []
        for pair in pairs:
            if type(pair) is not dict or not {"input", "output"} <= pair.keys():
                raise ValueError("Every private pair needs input and output")
            result[split].append({"input": _grid(pair["input"]), "output": _grid(pair["output"])})
    keys = [json_bytes(pair["input"]) for split in result.values() for pair in split]
    if len(keys) != len(set(keys)):
        raise ValueError("All demonstration/query inputs must differ")
    return result


def source_binding():
    paths = list(HOME.glob("*.py")) + list((TASK / "tests").glob("*.py"))
    paths += [TASK / "generator.py", HOME / "promotion.json",
              ROOT / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    return {path.relative_to(ROOT).as_posix(): digest(path.read_bytes()) for path in sorted(set(paths))}


def _write(path, report):
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    private.mkdir()
    target = private / "audit.json"
    report = {
        "schema": "49754d8fa42e-native-finite-audit-v1", "status": "running",
        "visibility": "controller_private", "source_files_sha256": source_binding(),
        "jobs": [{"seed": seed, "demos": demos, "queries": 4} for seed, demos in JOBS],
        "settings": deepcopy(SETTINGS), "extra_rivals": list(rival_names()),
        "scope": "Six episodes; two declared policies; 23 explicit extra hypotheses. "
                 "Demo-only survivor selection precedes query comparisons. Finite authoring evidence "
                 "only; no universal identifiability, owner acceptance or training admission.",
        "programs": {}, "episodes": [], "findings": [], "first_two_prefix_findings": [],
    }
    engine, bridge = None, None
    phase = "load_current_adapter"
    try:
        with _local_imports(RUNTIME, HOME):
            adapter = _load(HOME / "adapter.py")
            apply, identity, bridge = _real_evaluator(RUNTIME)
            engine = CachedEvaluator(apply)
            report["racket"] = identity
            programs = {s["orientation"]: adapter.program(deepcopy(s)) for s in SETTINGS}
            canonical = _load(HOME / "prototype.py")._canonical_program()
            if programs["canonical"] != canonical:
                raise AssertionError("Default native program is not the exact canonical authority")
            report["canonical_program_sha256"] = digest(canonical.encode())

            def retain(program):
                identifier = digest(program.encode())
                report["programs"][identifier] = program
                return identifier

            for seed, demos in JOBS:
                shared_inputs = None
                for settings in SETTINGS:
                    orientation = settings["orientation"]
                    phase = f"generate:{seed}:{demos}:{orientation}"
                    generated = adapter.generate(seed, deepcopy(settings), demos, 4)
                    ep = _episode(generated, demos, 4)
                    if generated["program_solution"] != programs[orientation]:
                        raise AssertionError("Generated program_solution differs from adapter.program")
                    inputs = [pair["input"] for pair in ep["train"] + ep["test"]]
                    if shared_inputs is None:
                        shared_inputs = inputs
                    elif inputs != shared_inputs:
                        raise AssertionError("Inputs changed across declared settings")
                    facts = [scene_facts(grid) for grid in inputs]
                    phase = f"reference_labels:{seed}:{demos}:{orientation}"
                    selected_program = programs[orientation]
                    for pair in ep["train"] + ep["test"]:
                        actual = engine(selected_program, pair["input"])
                        if actual != pair["output"] or actual != reference(pair["input"], settings):
                            raise AssertionError("Protected Racket label disagrees with generated/independent claim")
                    record = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                              "program_sha256": retain(selected_program), **ep,
                              "scene_facts": {"train": facts[:demos], "test": facts[demos:]},
                              "hypotheses": []}
                    taught_modes = {f["mode_color"] for f in facts[:demos]}
                    queried_modes = {f["mode_color"] for f in facts[demos:]}
                    record["demonstrated_mode_colors"] = sorted(taught_modes)
                    record["query_mode_colors"] = sorted(queried_modes)
                    record["demonstrated_nonzero_rotation_mode_colors"] = sorted({f["mode_color"] for f in facts[:demos]
                                                                                  if f["modal_component_quarter_turns"]})
                    report["episodes"].append(record)
                    if not queried_modes <= taught_modes:
                        report["findings"].append({"episode_index": len(report["episodes"]) - 1,
                            "kind": "query_modal_class_not_demonstrated", "unseen_modes": sorted(queried_modes - taught_modes)})
                    declared_survivors = []
                    hypotheses = [("declared:" + s["orientation"], programs[s["orientation"]], s)
                                  for s in SETTINGS]
                    hypotheses += [(name, rival_program(settings, name), None) for name in rival_names()]
                    for name, program, declared in hypotheses:
                        phase = f"hypothesis:{seed}:{demos}:{orientation}:{name}"
                        retain(program)
                        def execute(source, grid, declared=declared, name=name):
                            actual = engine(source, grid)
                            expected = reference(grid, declared) if declared is not None else rival_reference(grid, settings, name)
                            if actual != expected:
                                raise AssertionError(f"Executable hypothesis disagrees with its independent mirror: {name}")
                            return actual
                        assessed = assess_hypothesis(name, program, ep["train"], ep["test"], execute)
                        record["hypotheses"].append(assessed)
                        if declared is not None and assessed["survives_demonstrations"]:
                            declared_survivors.append(declared["orientation"])
                        finding = {"episode_index": len(report["episodes"]) - 1,
                                   "seed": seed, "settings": deepcopy(settings), "rival": name,
                                   "query_indices": assessed["query_disagreement_indices"]}
                        if assessed["survives_demonstrations"] and assessed["query_disagreement_indices"]:
                            report["findings"].append(dict(finding, kind="demo_survivor_query_disagreement"))
                        if assessed["survives_first_two"] and assessed["query_disagreement_indices"]:
                            report["first_two_prefix_findings"].append(dict(finding, kind="prefix_survivor_query_disagreement"))
                    record["declared_survivors"] = declared_survivors
                    record["extra_survivors"] = [r["name"] for r in record["hypotheses"]
                                                  if not r["name"].startswith("declared:") and r["survives_demonstrations"]]
                    if declared_survivors != [orientation]:
                        report["findings"].append({"episode_index": len(report["episodes"]) - 1,
                            "kind": "declared_policy_not_identified", "survivors": declared_survivors})
                    stress = facts[-1]
                    stress_passed = (stress["shape"] == [30, 30] and stress["nonzero_cells"] >= 300
                                     and stress["mode_count"] >= 150
                                     and stress["occupied_rows"] >= 24 and stress["occupied_columns"] >= 24
                                     and min(stress["quadrant_nonzero"]) >= 30
                                     and stress["nonzero_bbox"] == [0, 0, 29, 29])
                    record["stress_check"] = {"passed": stress_passed,
                        "requirements": {"shape": [30, 30], "nonzero_cells_min": 300,
                                         "mode_count_min": 150, "occupied_rows_columns_min": 24,
                                         "quadrant_nonzero_min": 30, "full_canvas_bbox": True}}
                    if not stress_passed:
                        report["findings"].append({"episode_index": len(report["episodes"]) - 1,
                                                  "kind": "insufficient_30x30_scene_content", "facts": stress})
                    print(json.dumps({"seed": seed, "demos": demos, "orientation": orientation,
                        "native_evaluations": engine.evaluations, "extra_survivors": record["extra_survivors"],
                        "findings": len(report["findings"]), "prefix_findings": len(report["first_two_prefix_findings"])}), flush=True)
            phase = "source_binding_after_execution"
            after = source_binding()
            if after != report["source_files_sha256"]:
                changed = sorted(k for k in set(after) | set(report["source_files_sha256"])
                                 if after.get(k) != report["source_files_sha256"].get(k))
                raise AssertionError("Sources changed during audit: " + ", ".join(changed))
            report["status"] = "failed" if report["findings"] else "passed"
            report["matched_inputs_across_settings"] = True
            report["reference_label_count"] = sum(j["demos"] + j["queries"] for j in report["jobs"]) * len(SETTINGS)
            report["prefix_scope"] = ("Unsupported diagnostic truncation of larger episodes: their queries may use a modal class "
                "first taught in demo three. Reported separately, not an acceptance gate. The valid two-demo contract is the "
                "separately generated demos=2 job, whose queries must use its demonstrated modal class.")
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error),
                                       "last_native_request": engine.last_request if engine else None}
    finally:
        if bridge is not None:
            bridge.close()
        if engine is not None:
            report["execution"] = {"backend": "live protected Racket", "requests": engine.requests,
                "racket_evaluations": engine.evaluations, "successful_cached_results": len(engine.cache),
                "cache_hits": engine.cache_hits,
                "cache_key": "exact complete program text and exact validated input grid"}
        _write(target, report)
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "findings": len(report["findings"]), "prefix_findings": len(report["first_two_prefix_findings"]),
                      "report": str(target), "execution_failure": report.get("execution_failure")}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New controller-private evidence directory")
    result = run(parser.parse_args().out)
    raise SystemExit(0 if result["status"] == "passed" else 1)
