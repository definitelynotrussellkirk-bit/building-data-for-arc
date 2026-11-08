#!/usr/bin/env python3
"""Read-only, source-bound curriculum diagnostics; all retained labels use Racket.

From the outer packet directory, pass an absolute interpreter to review.py run:
  WORK/.venv/bin/python review.py run /ABS/WORK/.venv/bin/python \
    generators/832404dc8a5c/workspace/probe_curriculum.py \
    --out ../checks/curriculum-probe.json
The output is PRIVATE authoring evidence containing reference answers.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from arcpuzzles.grids import compare_grids
from reviewer_support import canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = "832404dc8a5c"
BANDS = ("easy", "medium", "hard")
NAMESPACES = ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS")


def sha256(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def declared_rivals(generator):
    result = {}
    for namespace in NAMESPACES:
        declarations = getattr(generator, namespace, {})
        if not isinstance(declarations, dict):
            raise TypeError(f"{namespace} must be a name-to-callable mapping")
        for name, predict in declarations.items():
            if not isinstance(name, str) or not callable(predict):
                raise TypeError(f"invalid rival declaration in {namespace}")
            result[f"{namespace}.{name}"] = predict
    return result


def difference(expected, actual):
    result = compare_grids(expected, actual)
    differences = [dict(cell, kind=kind) for kind in ("changed", "missing", "extra")
                   for cell in result[f"{kind}_cells"]]
    differences.sort(key=lambda cell: (cell["row"], cell["column"]))
    return {"differing_cells": len(differences),
            "first_mismatch": differences[0] if differences else None}


def canonical_program(root):
    with canonical_path(root).open(encoding="utf-8") as handle:
        programs = {row["program_solution"] for line in handle if line.strip()
                    for row in [json.loads(line)] if row.get("task_id") == TASK_ID}
    if len(programs) != 1:
        raise ValueError("expected one exact selected canonical program")
    return programs.pop()


def execute_rule(bridge, program, grid):
    source = program.strip()
    if not source.startswith("(rule! (lambda (g)") or not source.endswith(")"):
        raise ValueError("expected this task's rule! wrapper around a grid lambda")
    bridge.define_grid("g", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({source[len('(rule!'):-1].strip()} g)"))


def case_specs(generator):
    cases = [(f"default-{band}-{index}", 17, index, band, {})
             for band in BANDS for index in (0, 1)]
    cases += [(f"canonical-profile-medium-{index}", 17, index, "medium", {})
              for index in (2, 4, 6)]
    large = {"grid_h": 30, "grid_w": 30, "n_anchored_rows": 4, "n_anchored_cols": 4}
    cases += [(f"boundary-30x30-{band}", 29, 3, band, large) for band in BANDS]
    textures = getattr(generator, "LAWFUL_DEGENERATE_TEXTURES", getattr(generator, "DEGENERATE_TEXTURES", ()))
    cases += [(f"lawful-texture-{texture}", 29, 3, "hard",
               {"grid_h": 30, "grid_w": 30, "texture": texture}) for texture in textures]
    return cases


def size_census(generator, seeds, indices):
    bands = {}
    for band in BANDS:
        sizes, invalid = Counter(), []
        for seed in seeds:
            for index in indices:
                grid = generator.generate(seed, index, difficulty=band)
                sizes[(len(grid), len(grid[0]))] += 1
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    invalid.append({"seed": seed, "sample_index": index, "errors": errors})
        bands[band] = {"inputs": sum(sizes.values()), "unique_sizes": len(sizes),
                       "height_range": [min(h for h, _ in sizes), max(h for h, _ in sizes)],
                       "width_range": [min(w for _, w in sizes), max(w for _, w in sizes)],
                       "size_histogram": {f"{h}x{w}": n for (h, w), n in sorted(sizes.items())},
                       "invalid_inputs": invalid}
    return {"label_policy": "input-only; no Racket outputs generated", "seeds": seeds,
            "sample_indices": indices, "overrides": {}, "bands": bands,
            "total_inputs": sum(row["inputs"] for row in bands.values())}


def collect_report(*, root=None, census_seeds=range(8), census_indices=range(16)):
    root = find_root(__file__) if root is None else Path(root)
    seeds, indices = list(census_seeds), list(census_indices)
    if not seeds or not indices:
        raise ValueError("census seeds and indices must be nonempty")
    generator, source, source_hash = load_selected_generator(TASK_ID, root=root)
    program, rivals = canonical_program(root), declared_rivals(generator)
    cases, rival_errors = [], []
    with RacketBridge(timeout=20) as bridge:
        for case_id, seed, index, band, overrides in case_specs(generator):
            grid = generator.generate(seed, index, difficulty=band, **overrides)
            output = execute_rule(bridge, program, grid)
            predictions = {}
            for name, predict in rivals.items():
                try:
                    predictions[name] = difference(output, predict(deepcopy(grid)))
                except Exception as error:
                    predictions[name] = {"error": f"{type(error).__name__}: {error}"}
                    rival_errors.append({"case_id": case_id, "rival": name, **predictions[name]})
            cases.append({"case_id": case_id,
                          "replay": {"seed": seed, "sample_index": index, "difficulty": band, "overrides": overrides},
                          "height": len(grid), "width": len(grid[0]), "input": grid, "output": output,
                          "label_source": "live RacketBridge",
                          "self_check": generator.self_check(grid, difficulty=band), "rivals": predictions})
    census = size_census(generator, seeds, indices)
    unchanged = sha256(source.read_bytes()) == source_hash
    findings = bool(rival_errors or not unchanged or not rivals or any(c["self_check"] for c in cases)
                    or any(b["invalid_inputs"] for b in census["bands"].values()))
    return {"schema": "832404dc8a5c-curriculum-probe-v1", "status": "findings" if findings else "complete",
            "task_id": TASK_ID, "generator_source": str(source.relative_to(root)),
            "generator_sha256": source_hash, "generator_source_unchanged": unchanged,
            "tool_sha256": sha256(Path(__file__).read_bytes()), "rule": program,
            "rule_sha256": sha256(program), "declared_rule_hash": getattr(generator, "RULE_HASH", None),
            "runtime": racket_runtime_status(), "rival_inventory": sorted(rivals), "rival_errors": rival_errors,
            "rival_witnesses": {name: next((case["case_id"] for case in cases
                                           if case["rivals"][name].get("differing_cells", 0) > 0), None)
                                for name in rivals},
            "cases": cases, "input_size_census": census,
            "coordinates": "zero-based row, column from top-left",
            "limitations": ["Private authoring evidence, not public challenge material.",
                            "Finite selected examples; no lesson or rotation identifiability verdict.",
                            "The larger size census generates and validates inputs only.",
                            "Rival predictions use declared Python callables; authoritative labels execute in Racket."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--index-count", type=int, default=16)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("fresh output required: destination already exists")
    if args.seed_count < 1 or args.index_count < 1:
        parser.error("census counts must be positive")
    report = collect_report(census_seeds=range(args.seed_count), census_indices=range(args.index_count))
    report["command"] = {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, separators=(",", ":"), sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status": report["status"], "racket_labeled_cases": len(report["cases"]),
                      "input_only_census": report["input_size_census"]["total_inputs"],
                      "generator_sha256": report["generator_sha256"], "out": str(args.out)}, sort_keys=True))
    return int(report["status"] != "complete")


if __name__ == "__main__":
    raise SystemExit(main())
