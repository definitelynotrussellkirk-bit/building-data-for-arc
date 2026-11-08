"""Bounded private teaching audit using a persistent protected Racket bridge.

Run from the packet through review.py run. Rival survival uses demonstrations
only; query labels are inspected only after that survivor set is frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "f47990415137"
REQUESTS = ((3, 2), (22, 2), (17, 3), (0, 6))


def load(name):
    path = HERE / (name + ".py")
    spec = importlib.util.spec_from_file_location("aspect_audit_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_hashes():
    paths = sorted(path for path in HERE.iterdir() if path.is_file()
                   and path.suffix in {".py", ".rkt", ".json"})
    paths.append(HERE.parents[1] / "generator.py")
    paths.extend(sorted((HERE.parents[1] / "tests").glob("test_param*.py")))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def object_program(mode, *, selector=None, groups=None, comparison="ratio", fill=False):
    if selector is None:
        selector = "(argmax obj-size objs)" if mode == "largest" else "#f"
    groups = groups or "(objects g 0)"
    if comparison == "integer_ratio":
        left, right = "(/ (obj-h obj) (obj-w obj))", "(/ rh rw)"
    elif comparison == "height_width_difference":
        left, right = "(- (obj-h obj) (obj-w obj))", "(- rh rw)"
    else:
        left, right = "(* (obj-h obj) rw)", "(* (obj-w obj) rh)"
    color = "(cond [(> left right) 2] [(< left right) 3] [else 4])"
    if comparison == "anchor_only_special":
        color = "(if (equal? obj anchor) 4 (cond [(> (obj-h obj) (obj-w obj)) 2] [(< (obj-h obj) (obj-w obj)) 3] [else 4]))"
    cells = "(obj-cells obj)"
    if fill:
        cells = """(for*/list ([r (in-range (obj-r1 obj) (+ 1 (obj-r2 obj)))]
                               [c (in-range (obj-c1 obj) (+ 1 (obj-c2 obj)))])
                       (list r c))"""
    return f"""(rule! (lambda (g)
      (let* ([objs {groups}]
             [anchor (if (empty? objs) #f {selector})]
             [rh (if anchor (obj-h anchor) 1)]
             [rw (if anchor (obj-w anchor) 1)])
        (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (in-list objs)])
          (let* ([left {left}] [right {right}] [color {color}])
            (paint-cells out {cells} color))))))"""


def rivals(settings, prototype):
    mode = settings["reference"]
    # Construct actual merged objects: reference selection also sees merged
    # foreground cell counts, rather than quietly retaining true components.
    merged = """(map (lambda (color)
                       (let ([cells (find-color g color)])
                         (hash 'color color 'cells cells 'bbox (bbox-of-cells cells)
                               'size (length cells))))
                     (grid-colors g 0))"""
    return {
        "other_setting": prototype.program({"reference": "largest" if mode == "axes" else "axes"}),
        "group_by_color": object_program(mode, groups=merged),
        "fill_bounding_boxes": object_program(mode, fill=True),
        "bbox_area_anchor": object_program(mode, selector="(argmax (lambda (o) (* (obj-h o) (obj-w o))) objs)"),
        "raster_first_anchor": object_program(mode, selector="(first objs)"),
        "integer_ratio": object_program(mode, comparison="integer_ratio"),
        "height_width_difference": object_program(mode, comparison="height_width_difference"),
        "anchor_only_special": object_program(mode, selector="(argmax obj-size objs)", comparison="anchor_only_special"),
    }


def assess_predictions(actual_train, actual_test, predicted_train, predicted_test):
    """A wrong query prediction is an ambiguity only for a demo survivor."""
    if (not actual_train or not actual_test or len(predicted_train) != len(actual_train)
            or len(predicted_test) != len(actual_test)
            or any(value is None for value in predicted_train + predicted_test)):
        raise ValueError("Missing or failed rival execution cannot count as teaching evidence")
    demo_matches = [a == b for a, b in zip(actual_train, predicted_train)]
    survivors = all(demo_matches)
    first_two_survivor = all(demo_matches[:2])
    disagreements = [i for i, (a, b) in enumerate(zip(actual_test, predicted_test)) if a != b]
    return {"demo_matches": demo_matches, "survives_demonstrations": survivors,
            "survives_first_two": first_two_survivor,
            "query_disagreements": disagreements,
            "ambiguous_queries": disagreements if survivors else [],
            "first_two_ambiguous_queries": disagreements if first_two_survivor else []}


def scene_stats(grid, prototype):
    groups = prototype.components(grid)
    occupied = [(r, c) for _, cells in groups for r, c in cells]
    anchor = max(groups, key=lambda item: len(item[1]))
    counts = sorted((len(cells) for _, cells in groups), reverse=True)
    r0, r1 = min(r for r, _ in occupied), max(r for r, _ in occupied)
    c0, c1 = min(c for _, c in occupied), max(c for _, c in occupied)
    return {"height": len(grid), "width": len(grid[0]), "components": len(groups),
            "foreground_cells": len(occupied), "occupied_bbox": [r0, c0, r1, c1],
            "row_span": r1 - r0 + 1, "column_span": c1 - c0 + 1,
            "foreground_colors": len({color for color, _ in groups}),
            "largest_unique": counts[0] > counts[1],
            "anchor_cells": len(anchor[1]), "anchor_dimensions": list(prototype.dimensions(anchor[1])),
            "edge_contacts": {"top": r0 == 0, "bottom": r1 == len(grid) - 1,
                              "left": c0 == 0, "right": c1 == len(grid[0]) - 1}}


def run_audit():
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    adapter, prototype = load("adapter"), load("prototype")
    before = source_hashes()
    report = {"schema": "f47990415137-parametric-teaching-audit-v1", "task_id": TASK,
              "status": "running", "source_hashes": before,
              "request_schedule": [{"seed": seed, "demos": demos, "queries": 4}
                                   for seed, demos in REQUESTS],
              "episodes": [], "boundaries": [], "survivor_table": [],
              "survivor_with_query_disagreement": [], "first_two_findings": [],
              "errors": [], "rival_programs": {}, "matched_inputs": [],
              "limits": ["Finite declared-rival audit; not universal identifiability or model evidence.",
                         "All rival executions must return valid grids; runtime errors are audit failures.",
                         "For axes, height-minus-width versus zero is mathematically equivalent to canonical aspect.",
                         "Eight-separated sampling does not distinguish 4-connectivity from 8-connectivity."]}
    runtime = ROOT / "shared/runtime"
    cache = {}
    executions = 0
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity
        def execute(program, grid):
            nonlocal executions
            key = (program, digest(grid))
            if key not in cache:
                cache[key] = _grid(apply(program, _grid(grid)))
                executions += 1
            return cache[key]
        try:
            input_sets = {}
            for settings in prototype.SETTINGS:
                mode = settings["reference"]
                declared = rivals(settings, prototype)
                report["rival_programs"][mode] = declared
                for seed, demos in REQUESTS:
                    episode_id = f"{mode}-seed{seed}-demos{demos}"
                    episode = adapter.generate(seed, settings, demos, 4)
                    program = adapter.program(settings)
                    if episode["program_solution"] != program:
                        raise ValueError("Adapter program and episode program differ")
                    if len(episode["train"]) != demos or len(episode["test"]) != 4:
                        raise ValueError("Adapter silently changed demonstration/query count")
                    pairs = episode["train"] + episode["test"]
                    inputs = [pair["input"] for pair in pairs]
                    if len({digest(grid) for grid in inputs}) != demos + 4:
                        raise ValueError("Duplicate demonstration/query inputs")
                    input_key = (seed, demos)
                    if input_key in input_sets:
                        matched = input_sets[input_key] == inputs
                        report["matched_inputs"].append({"seed": seed, "demos": demos, "identical": matched})
                        if not matched:
                            raise ValueError("Hidden setting changes the input grammar or ordering")
                    else:
                        input_sets[input_key] = inputs
                    labels = []
                    for index, pair in enumerate(pairs):
                        label = execute(program, pair["input"])
                        if label != _grid(pair["output"]):
                            raise ValueError(f"Python claim disagrees with protected Racket in {episode_id} pair {index}")
                        labels.append(label)
                    item = {"episode_id": episode_id, "seed": seed, "settings": dict(settings),
                            "demos": demos, "queries": 4, "program": program,
                            "train": episode["train"], "test": episode["test"],
                            "scene_stats": [scene_stats(grid, prototype) for grid in inputs],
                            "rivals": {}}
                    if not all(stats["largest_unique"] for stats in item["scene_stats"]):
                        raise ValueError(f"Nonunique cell-count anchor in {episode_id}")
                    report["episodes"].append(item)
                    for name, rival in declared.items():
                        try:
                            predictions = [execute(rival, grid) for grid in inputs]
                            result = assess_predictions(labels[:demos], labels[demos:],
                                                        predictions[:demos], predictions[demos:])
                        except Exception as exc:
                            report["errors"].append({"episode_id": episode_id, "rival": name,
                                                     "error": f"{type(exc).__name__}: {exc}"})
                            item["rivals"][name] = {"status": "execution_failed"}
                            continue
                        item["rivals"][name] = {"status": "executed", **result}
                        report["survivor_table"].append({"episode_id": episode_id, "setting": mode,
                                                        "rival": name, **result})
                        for key, destination in (("ambiguous_queries", "survivor_with_query_disagreement"),
                                                 ("first_two_ambiguous_queries", "first_two_findings")):
                            for index in result[key]:
                                report[destination].append({"episode_id": episode_id, "rival": name,
                                    "query_index": index, "settings": dict(settings), "program": program,
                                    "counterfactual_program": rival,
                                    "train": episode["train"] if key == "ambiguous_queries" else episode["train"][:2],
                                    "input": inputs[demos + index], "output": labels[demos + index],
                                    "counterfactual_output": predictions[demos + index]})
            for settings in prototype.SETTINGS:
                program = adapter.program(settings)
                for size in (8, 30):
                    grid = prototype.sample_scene(91, size, size, "tall")
                    label = execute(program, grid)
                    if label != prototype.transform(grid, settings):
                        raise ValueError("Boundary claim disagrees with protected Racket")
                    stats = scene_stats(grid, prototype)
                    if not stats["largest_unique"] or stats["components"] < 4:
                        raise ValueError("Boundary has no unique cell-count anchor or lacks substantive objects")
                    if size == 30 and (stats["foreground_cells"] < 100 or min(stats["row_span"], stats["column_span"]) < 26):
                        raise ValueError("30x30 stress is only empty padding")
                    report["boundaries"].append({"settings": dict(settings), "seed": 91,
                                                 "input": grid, "output": label, "stats": stats})
        except Exception as exc:
            report["errors"].append({"error": f"{type(exc).__name__}: {exc}"})
        finally:
            bridge.close()
    report["protected_racket_executions"] = executions
    if before != source_hashes():
        report["errors"].append({"error": "Source changed during audit; results are not source-bound"})
    report["status"] = "pass" if not any(report[key] for key in
        ("errors", "survivor_with_query_disagreement", "first_two_findings")) else "fail"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Private JSON evidence destination")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Refusing to overwrite existing evidence; select a fresh output path")
    report = run_audit()
    report["command"] = [sys.executable, *sys.argv]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "racket_executions": report["protected_racket_executions"],
                      "survivor_query_findings": len(report["survivor_with_query_disagreement"]),
                      "first_two_findings": len(report["first_two_findings"]),
                      "execution_errors": len(report["errors"]), "out": str(args.out)}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
