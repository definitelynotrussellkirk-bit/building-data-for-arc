#!/usr/bin/env python3
"""Bounded, independent teaching audit for component/quadrant native variants.

The first two demonstrations alone fix the surviving hypotheses. Four query
answers are then assessed independently; a query answer never teaches another
query. Rivals already refuted by demonstrations require no query execution.
Every retained intended and rival label is executed by protected Racket.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "196a7ec58bbc"
RIVALS = (
    "opposite_handedness", "opposite_source", "first_component",
    "last_component", "smallest_component", "largest_bbox",
    "aggregate_color", "eight_connected", "raw_crop",
    "reflection_quadrants", "repeat_quadrants", "fixed_five_crop",
)


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def components(grid, connectivity=4):
    """Independent same-color flood fill, preserving row-major object order."""
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    height, width = len(grid), len(grid[0])
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if connectivity == 8:
        deltas += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if not grid[row][col] or (row, col) in seen:
                continue
            color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in deltas:
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width
                            and (rr, cc) not in seen and grid[rr][cc] == color):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            rs, cs = zip(*cells)
            result.append({"color": color, "cells": sorted(cells), "size": len(cells),
                           "bbox": [min(rs), min(cs), max(rs), max(cs)]})
    if not result:
        raise ValueError("audit grammar requires a nonzero object")
    return result


def _extract(grid, obj, raw=False):
    r0, c0, r1, c1 = obj["bbox"]
    side = max(r1 - r0 + 1, c1 - c0 + 1)
    tile = [[0] * side for _ in range(side)]
    if raw:
        for row in range(r0, r1 + 1):
            for col in range(c0, c1 + 1):
                tile[row - r0][col - c0] = grid[row][col]
    else:
        for row, col in obj["cells"]:
            tile[row - r0][col - c0] = grid[row][col]
    return tile


def _cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _tile(tile, handedness, layout="rotation"):
    cw = _cw(tile)
    half = _cw(cw)
    ccw = _cw(half)
    if layout == "reflection":
        tr, bl = [row[::-1] for row in tile], tile[::-1]
    elif layout == "repeat":
        tr = bl = half = tile
    else:
        tr, bl = (cw, ccw) if handedness == "clockwise" else (ccw, cw)
    return [left + right for left, right in zip(tile, tr)] + [left + right for left, right in zip(bl, half)]


def python_intended(grid, settings):
    """Independent intended labels; no native-family implementation is used."""
    if settings["source_mode"] == "whole":
        source = deepcopy(grid)
    else:
        selected = max(components(grid), key=lambda obj: obj["size"])
        source = _extract(grid, selected)
    return _tile(source, settings["handedness"])


def _rival_choice(settings, name):
    if name not in RIVALS:
        raise ValueError(f"unknown rival {name!r}")
    source, hand = settings["source_mode"], settings["handedness"]
    layout, raw = "rotation", False
    selector = "largest_component"
    if name == "opposite_handedness":
        hand = "counterclockwise" if hand == "clockwise" else "clockwise"
    elif name == "opposite_source":
        source = "largest_component" if source == "whole" else "whole"
    elif name in ("reflection_quadrants", "repeat_quadrants"):
        layout = "reflection" if name == "reflection_quadrants" else "repeat"
    else:
        source = "largest_component"
        selector = name
        raw = name == "raw_crop"
    return source, hand, selector, raw, layout


def python_rival(grid, settings, name):
    source, hand, selector, raw, layout = _rival_choice(settings, name)
    if source == "whole":
        tile = deepcopy(grid)
    else:
        objects = components(grid, 8 if selector == "eight_connected" else 4)
        if selector == "first_component":
            obj = objects[0]
        elif selector == "last_component":
            obj = objects[-1]
        elif selector == "smallest_component":
            obj = min(objects, key=lambda o: o["size"])
        elif selector == "largest_bbox":
            obj = max(objects, key=lambda o: (o["bbox"][2] - o["bbox"][0] + 1) * (o["bbox"][3] - o["bbox"][1] + 1))
        elif selector == "aggregate_color":
            counts = Counter(value for row in grid for value in row if value)
            colors = list(dict.fromkeys(o["color"] for o in objects))
            color = max(colors, key=counts.get)
            obj = max((o for o in objects if o["color"] == color), key=lambda o: o["size"])
        else:
            obj = max(objects, key=lambda o: o["size"])
        tile = _extract(grid, obj, raw)
        if selector == "fixed_five_crop":
            tile = [[tile[r][c] if r < len(tile) and c < len(tile[0]) else 0
                     for c in range(5)] for r in range(5)]
    return _tile(tile, hand, layout)


def rival_program(settings, name):
    """Independent executable hypotheses, not mutations of the native program."""
    source, hand, selector, raw, layout = _rival_choice(settings, name)
    if source == "whole":
        bindings = "[tile g]"
    else:
        object_source = "(objects-8 g 0)" if selector == "eight_connected" else "(objects g 0)"
        choices = {
            "first_component": "(first os)",
            "last_component": "(last os)",
            "smallest_component": "(argmin obj-size os)",
            "largest_bbox": "(argmax (lambda (o) (* (obj-h o) (obj-w o))) os)",
            "aggregate_color": """(let* ([colors (remove-duplicates (map obj-color os))]
              [color (argmax (lambda (c) (count-color g c)) colors)])
              (argmax obj-size (filter (lambda (o) (= (obj-color o) color)) os)))""",
        }
        choice = choices.get(selector, "(argmax obj-size os)")
        content = "(crop-object g chosen)" if raw else """(crop-object
          (paint-cells (empty-grid (rows g) (cols g) 0)
            (obj-cells chosen) (obj-color chosen)) chosen)"""
        side = "5" if selector == "fixed_five_crop" else "(max (rows cropped) (cols cropped))"
        bindings = f"""[os {object_source}]
       [chosen {choice}]
       [cropped {content}]
       [side {side}]
       [tile (grid-from-fn side side
          (lambda (r c) (if (and (< r (rows cropped)) (< c (cols cropped)))
            (cell-at cropped r c) 0)))]"""
    if layout == "reflection":
        tr, bl, br = "(flip-lr tile)", "(flip-ud tile)", "(rotate-180 tile)"
    elif layout == "repeat":
        tr = bl = br = "tile"
    else:
        tr, bl = ("(rotate-cw tile)", "(rotate-ccw tile)") if hand == "clockwise" else ("(rotate-ccw tile)", "(rotate-cw tile)")
        br = "(rotate-180 tile)"
    return f"""(rule! (lambda (g)
  (let* ({bindings})
    (stack-grids 'vertical (list
      (stack-grids 'horizontal (list tile {tr}))
      (stack-grids 'horizontal (list {bl} {br})))))))"""


def score_lesson(intended_demos, intended_queries, rival_demos, rival_queries):
    """Freeze demo-consistent rivals before inspecting independent queries."""
    if not intended_demos or not intended_queries:
        raise ValueError("a lesson requires demonstrations and queries")
    for name in rival_demos:
        if len(rival_demos[name]) != len(intended_demos):
            raise ValueError("rival label count differs from the lesson")
    survivors = sorted(name for name, labels in rival_demos.items() if labels == intended_demos)
    if not set(survivors) <= set(rival_queries) <= set(rival_demos):
        raise ValueError("query labels must cover every demo survivor and no undeclared rivals")
    if any(len(labels) != len(intended_queries) for labels in rival_queries.values()):
        raise ValueError("rival label count differs from the lesson")
    query_rows = []
    for index, output in enumerate(intended_queries):
        disagreeing = [name for name in survivors if rival_queries[name][index] != output]
        query_rows.append({"query_index": index, "surviving_disagreeing_rivals": disagreeing,
                           "identified_within_declared_rivals": not disagreeing})
    return {"surviving_rivals_after_demonstrations": survivors,
            "refuted_rivals": sorted(set(rival_demos) - set(survivors)),
            "queries": query_rows,
            "ok": all(row["identified_within_declared_rivals"] for row in query_rows)}


def _load_family():
    for path in (ROOT / "src", ROOT / "shared/runtime", HERE.parent):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location("native_teaching_family_196a7ec58bbc", HERE.with_name("native_family.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load native family")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_report(seeds=(0, 1), demonstrations=2):
    if not 2 <= demonstrations <= 6:
        raise ValueError("audit demonstrations must lie in 2..6")
    if not seeds or len(seeds) > 4 or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("audit requires one to four nonnegative exact integer seeds")
    family = _load_family()
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = ROOT / "shared/runtime"
    rows, failures, witness_candidates = [], [], []
    executed = 0
    with _local_imports(runtime, HERE.parent):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for seed, source, hand in itertools.product(seeds, ("whole", "largest_component"), ("clockwise", "counterclockwise")):
                settings = {"source_mode": source, "handedness": hand}
                episode = family.generate(seed, settings, demos=demonstrations, queries=4)
                pairs = episode["train"] + episode["test"]
                program = family.program(settings)
                intended = [_grid(apply(program, pair["input"])) for pair in pairs]
                executed += len(pairs)
                if intended != [pair["output"] for pair in pairs]:
                    raise AssertionError("intended Racket label differs from generated claim")
                independent_intended = [python_intended(pair["input"], settings) for pair in pairs]
                if intended != independent_intended:
                    raise AssertionError("intended labels differ between independent Python and Racket")
                labels, programs = {}, {}
                for name in RIVALS:
                    programs[name] = rival_program(settings, name)
                    labels[name] = [_grid(apply(programs[name], pair["input"])) for pair in episode["train"]]
                    executed += demonstrations
                    independent = [python_rival(pair["input"], settings, name) for pair in episode["train"]]
                    if labels[name] != independent:
                        raise AssertionError(f"rival {name} differs between independent Python and Racket")
                demo_labels = labels
                survivors = sorted(name for name, values in demo_labels.items() if values == intended[:demonstrations])
                query_labels = {}
                for name in survivors:
                    query_labels[name] = [_grid(apply(programs[name], pair["input"])) for pair in episode["test"]]
                    executed += 4
                    independent = [python_rival(pair["input"], settings, name) for pair in episode["test"]]
                    if query_labels[name] != independent:
                        raise AssertionError(f"surviving rival {name} differs between independent Python and Racket")
                lesson = score_lesson(intended[:demonstrations], intended[demonstrations:], demo_labels, query_labels)
                rival_rows = {name: {"program": programs[name],
                    "refuting_demonstrations": [i for i in range(demonstrations) if labels[name][i] != intended[i]],
                    "query_execution": "executed" if name in query_labels else "not_run_already_refuted",
                    "disagreeing_queries": ([i for i in range(4) if query_labels[name][i] != intended[demonstrations + i]]
                                             if name in query_labels else None),
                    "demonstration_label_sha256": [_hash(value) for value in labels[name]],
                    "query_label_sha256": [_hash(value) for value in query_labels.get(name, [])]} for name in RIVALS}
                rows.append({"seed": seed, "settings": settings, "demonstrations": demonstrations,
                    "queries": 4, "program": program, "unique_inputs": len({_hash(pair["input"]) for pair in pairs}),
                    "input_sha256": [_hash(pair["input"]) for pair in pairs],
                    "intended_label_sha256": [_hash(value) for value in intended],
                    "rival_checks": rival_rows, **lesson})
                for query in lesson["queries"]:
                    for name in query["surviving_disagreeing_rivals"]:
                        index = query["query_index"]
                        failures.append({"seed": seed, "settings": settings, "program": program,
                            "train": deepcopy(episode["train"]), "query_index": index,
                            "input": episode["test"][index]["input"], "output": intended[demonstrations + index],
                            "rival": name, "rival_program": programs[name],
                            "rival_output": query_labels[name][index]})
                if source == "largest_component" and hand == "clockwise" and seed == seeds[0]:
                    grid = pairs[0]["input"]
                    chosen = max(components(grid), key=lambda obj: obj["size"])
                    name = "largest_bbox"
                    if labels[name][0] != intended[0]:
                        witness_candidates.append({"seed": seed, "settings": settings, "program": program,
                            "input": grid, "output": intended[0], "counterfactual_program": programs[name],
                            "counterfactual_output": labels[name][0], "ablation": "wrong_intermediate",
                            "intermediate_value": {**chosen, "cropped_component": _extract(grid, chosen)}})
        finally:
            bridge.close()
    source_names = ("native_family.py", "adapter.py", "promotion.json", "audit_native.py")
    inventory = {name: hashlib.sha256(HERE.with_name(name).read_bytes()).hexdigest()
                 for name in source_names if HERE.with_name(name).is_file()}
    return {"schema": "196a7ec58bbc-native-teaching-audit-v1", "task_id": TASK_ID,
            "source_sha256": inventory, "racket": identity, "executed_labels": executed,
            "seeds": list(seeds), "rivals": list(RIVALS), "episodes": rows,
            "counterexamples": failures, "causal_candidates": witness_candidates,
            "all_intended_and_rival_labels_match_independent_python": True,
            "execution_scope": "All intended labels; every rival on demonstrations; only demo-surviving rivals on queries.",
            "ok": not failures and all(row["ok"] and row["unique_inputs"] == demonstrations + 4 for row in rows),
            "limits": ["Finite declared-rival audit; no universal identification claim or native acceptance.",
                       "Each rival is totalized by zero-padding a nonsquare rival crop at its bottom/right to a square before tiling.",
                       "Fixed-five crop clips or zero-pads the selected object to a 5x5 tile anchored at its bounding-box origin.",
                       "Aggregate-color selects a color by global nonzero frequency, then its largest four-connected component.",
                       "Only demonstrations determine survivor hypotheses; each query is assessed independently."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(tuple(args.seeds), args.demos)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"ok": report["ok"], "episodes": len(report["episodes"]),
                      "rivals": len(RIVALS), "executed_labels": report["executed_labels"],
                      "counterexamples": len(report["counterexamples"]), "out": str(args.out)}, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
