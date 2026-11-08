"""Bounded protected-Racket self-review of the closure-rounds prototype.

Run from this checkout through the packet's review.py run wrapper. Reports are
private evidence: exact programs, counterfactual answers, and settings must not
be supplied to a learner. This script changes no acceptance state.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "699479899861"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(value):
    if type(value) is str:
        value = value.encode("utf-8")
    elif type(value) is not bytes:
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _sources():
    paths = [HERE.parents[1] / "generator.py"]
    paths.extend(sorted(path for path in HERE.iterdir() if path.suffix in (".py", ".rkt", ".json") and path.is_file()))
    return {str(path.relative_to(ROOT)): _sha(path.read_bytes()) for path in paths if path.is_file()}


def _dump(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def replay_retained_case(case_path: Path, prior_review_path: Path, out: Path) -> dict:
    """Execute an earlier demo-fitting live-scan counterexample without resampling."""
    if out.exists():
        raise ValueError("Use a new evidence directory for each replay")
    case = json.loads(case_path.read_text(encoding="utf-8"))
    prior_review = json.loads(prior_review_path.read_text(encoding="utf-8"))
    settings = case["settings"]
    source_hash = next(
        row["program_sha256"] for row in prior_review["protected"]["rows"]
        if row["settings"] == settings
    )
    source = prior_review["programs"][source_hash]
    canonical = prior_review["programs"][prior_review["canonical_program_sha256"]]
    rivals = _load(HERE / "rivals.py", "_closure_rounds_replay_rivals")
    rival = rivals.build(settings, canonical)["live_second_pass_ascending"]
    report = {
        "schema": "arcpuzzles-closure-rounds-live-scan-counterexample-v1",
        "task_id": TASK_ID,
        "case_path": str(case_path),
        "case_sha256": _sha(case_path.read_bytes()),
        "prior_review_path": str(prior_review_path),
        "prior_review_sha256": _sha(prior_review_path.read_bytes()),
        "audited_source_files": prior_review["source_files"],
        "rival_source_files": {
            str(path.relative_to(ROOT)): _sha(path.read_bytes())
            for path in (HERE / "rivals.py", HERE / "audit.py")
        },
        "settings": settings,
        "seed": case["seed"],
        "demos": case["demos"],
        "query_index": case["query_index"],
        "program": source,
        "program_sha256": source_hash,
        "rival_program": rival["program"],
        "rival_description": rival["description"],
        "train": [],
    }
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            for split, pairs in (("train", case["train"]), ("query", [case["query"]])):
                for pair in pairs:
                    grid = _grid(pair["input"])
                    intended = _grid(apply(source, grid))
                    altered = _grid(apply(rival["program"], grid))
                    if intended != pair["output"]:
                        raise AssertionError("Protected replay changed an original intended label")
                    if altered != rival["predict"](grid):
                        raise AssertionError("Live-scan Python/Racket disagreement")
                    row = {"input": grid, "output": intended, "rival_output": altered, "agrees": intended == altered}
                    if split == "train":
                        report["train"].append(row)
                    else:
                        report["query"] = row
                        if altered != case["rival_query_output"]:
                            raise AssertionError("Protected replay disagrees with retained rival prediction")
            report["racket"] = identity
        finally:
            bridge.close()
    if not all(row["agrees"] for row in report["train"]) or report["query"]["agrees"]:
        raise AssertionError("Retained case no longer demonstrates the alleged teaching hole")
    report["status"] = "protected_demo_fitting_query_disagreement"
    report["protected_executions"] = 2 * (len(report["train"]) + 1)
    report["resolution"] = "The sampler must teach both relative scan orders; a later source-bound review establishes the repair."
    out.mkdir(parents=True)
    _dump(out / "live-scan-counterexample.json", report)
    return {"status": report["status"], "protected_executions": report["protected_executions"], "report": str(out / "live-scan-counterexample.json")}


def run(out: Path) -> dict:
    if out.exists():
        raise ValueError("Use a new evidence directory for each source revision")
    before = _sources()
    prototype = _load(HERE / "prototype.py", "_closure_rounds_audit_prototype")
    rivals = _load(HERE / "rivals.py", "_closure_rounds_audit_rivals")
    canonical = prototype.program({"closure_rounds": 1})
    selected_programs = {
        variant["program_solution"] for variant in Catalog(ROOT).get(TASK_ID)["variants"]
        if type(variant.get("program_solution")) is str
    }
    if selected_programs != {canonical}:
        raise AssertionError("Default setting is not the exact selected canonical source")

    report = {
        "schema": "arcpuzzles-closure-rounds-self-review-v1",
        "task_id": TASK_ID,
        "source_files": before,
        "canonical_program_sha256": _sha(canonical),
        "scope": "Finite declared executable rivals; no claim of universal uniqueness or training admission.",
        "rival_count": len(rivals.build({"closure_rounds": 2}, canonical)),
        "failures": [],
        "ambiguities": [],
        "programs": {},
    }
    sample_pairs = 0
    shapes = set()
    red_counts = set()
    changed_counts = []
    large_foreground = []
    seen_inputs = set()
    matched_inputs = {}
    request_count = 0
    # 20 seeds × two settings × two independent demonstration counts = 80 requests.
    for seed in range(20):
        for demos in (2, 6):
            for count in (1, 2):
                settings = {"closure_rounds": count}
                request_count += 1
                episode = prototype.generate(seed, settings, demos=demos, queries=4)
                if len(episode["train"]) != demos or len(episode["test"]) != 4:
                    raise AssertionError("Generator shortened a requested demonstration/query count")
                if episode["program_solution"] != prototype.program(settings):
                    raise AssertionError("Episode carries a different program from its fixed setting")
                fingerprints = []
                for pair in episode["train"] + episode["test"]:
                    grid, answer = _grid(pair["input"]), _grid(pair["output"])
                    if answer != rivals._rounds(grid, count):
                        raise AssertionError("Independent closure walk disagrees with a claimed label")
                    fingerprints.append(_sha(grid))
                    seen_inputs.add(_sha(grid))
                    shapes.add((len(grid), len(grid[0])))
                    red_counts.add(len(rivals._components(grid, 2)))
                    changed_counts.append(sum(a != b for row_a, row_b in zip(grid, answer) for a, b in zip(row_a, row_b)))
                    if len(grid) == len(grid[0]) == 30:
                        positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
                        large_foreground.append({
                            "cells": len(positions),
                            "bbox": list(rivals._bbox(positions)),
                            "occupied_quadrants": len({(r >= 15, c >= 15) for r, c in positions}),
                        })
                    sample_pairs += 1
                if len(set(fingerprints)) != len(fingerprints):
                    raise AssertionError("Repeated inputs within an episode")
                key = (seed, demos)
                if key in matched_inputs and matched_inputs[key] != fingerprints:
                    raise AssertionError("Inputs change when only the episode setting changes")
                matched_inputs[key] = fingerprints
                teaching = rivals.lesson_check(episode, settings, canonical)
                for row in teaching["ambiguities"]:
                    report["ambiguities"].append({"scope": "sampler", "seed": seed, "settings": settings, "demos": demos, **row})
    report["sampler"] = {
        "requests": request_count,
        "seeds": list(range(20)),
        "demo_counts": [2, 6],
        "queries_per_episode": 4,
        "pairs": sample_pairs,
        "unique_inputs": len(seen_inputs),
        "shapes": [list(shape) for shape in sorted(shapes)],
        "red_component_counts": sorted(red_counts),
        "changed_cell_range": [min(changed_counts), max(changed_counts)],
        "matched_inputs_across_settings": True,
        "exact_30x30_pairs": len(large_foreground),
        "exact_30x30_min_foreground_cells": min(row["cells"] for row in large_foreground) if large_foreground else None,
        "exact_30x30_min_occupied_quadrants": min(row["occupied_quadrants"] for row in large_foreground) if large_foreground else None,
        "exact_30x30_foreground_bboxes": sorted({tuple(row["bbox"]) for row in large_foreground}),
    }

    executions = 0
    protected_cache = {}
    rows = []
    witness = None
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        try:
            def execute(source, grid):
                nonlocal executions
                source_hash = _sha(source)
                report["programs"][source_hash] = source
                key = (source_hash, _sha(grid))
                if key not in protected_cache:
                    output = _grid(apply(source, grid))
                    protected_cache[key] = output
                    executions += 1
                return protected_cache[key]

            for seed in (0, 17):
                for demos in (2, 6):
                    for count in (1, 2):
                        settings = {"closure_rounds": count}
                        episode = prototype.generate(seed, settings, demos=demos, queries=4)
                        source = prototype.program(settings)
                        all_pairs = episode["train"] + episode["test"]
                        for pair in all_pairs:
                            actual = execute(source, pair["input"])
                            if actual != pair["output"]:
                                raise AssertionError("Protected Racket disagrees with a claimed native label")
                        result = {
                            "seed": seed,
                            "settings": settings,
                            "demos": demos,
                            "queries": 4,
                            "program_sha256": _sha(source),
                            "input_sha256": [_sha(pair["input"]) for pair in all_pairs],
                            "rivals": [],
                        }
                        for name, rival in rivals.build(settings, canonical).items():
                            disagreements = []
                            for index, pair in enumerate(all_pairs):
                                actual = execute(rival["program"], pair["input"])
                                predicted = rival["predict"](pair["input"])
                                if actual != predicted:
                                    raise AssertionError(f"Racket/Python rival mismatch: {name}")
                                if actual != pair["output"]:
                                    disagreements.append(index)
                            demo_disagreements = [i for i in disagreements if i < demos]
                            query_disagreements = [i - demos for i in disagreements if i >= demos]
                            row = {
                                "name": name,
                                "program_sha256": _sha(rival["program"]),
                                "demo_disagreements": demo_disagreements,
                                "query_disagreements": query_disagreements,
                                "ambiguous": not demo_disagreements and bool(query_disagreements),
                            }
                            result["rivals"].append(row)
                            if row["ambiguous"]:
                                report["ambiguities"].append({"scope": "protected", "seed": seed, "settings": settings, "demos": demos, **row})
                        rows.append(result)
                        if witness is None and count == 2:
                            pair = episode["train"][0]
                            grid = pair["input"]
                            counterfactual = rivals.build(settings, canonical)["stale_red_components"]["program"]
                            original = execute(source, grid)
                            altered = execute(counterfactual, grid)
                            intermediate = execute(canonical, grid)
                            if original == altered:
                                raise AssertionError("First alternative demonstration does not witness updated-state dependency")
                            witness = {
                                "settings": settings,
                                "input": grid,
                                "output": original,
                                "program": source,
                                "counterfactual_program": counterfactual,
                                "counterfactual_output": altered,
                                "ablation": "wrong_intermediate",
                                "generation": {"seed": seed, "demos": demos, "queries": 4, "split": "train", "pair_index": 0},
                                "intermediate_value": {
                                    "first_pass_grid": intermediate,
                                    "original_red_component_count": len(rivals._components(grid, 2)),
                                    "first_pass_green_component_boxes": [list(rivals._bbox(cells)) for cells in rivals._components(intermediate, 3)],
                                    "new_green_cells_in_second_pass": [[r, c] for r, row in enumerate(original) for c, value in enumerate(row) if value == 3 and intermediate[r][c] != 3],
                                },
                                "racket": identity,
                            }
            report["racket"] = identity
        finally:
            bridge.close()
    after = _sources()
    if before != after:
        raise AssertionError("Source files changed during the self-review")
    report["protected"] = {"episodes": len(rows), "executions": executions, "rows": rows, "rival_execution_errors": 0, "label_mismatches": 0}
    report["status"] = "passed" if not report["ambiguities"] else "failed"
    report["causal_case"] = "audited-case.json"
    out.mkdir(parents=True)
    _dump(out / "self-review.json", report)
    _dump(out / "audited-case.json", witness)
    return {
        "status": report["status"],
        "rival_count": report["rival_count"],
        "sampler_requests": request_count,
        "sampler_pairs": sample_pairs,
        "protected_episodes": len(rows),
        "protected_executions": executions,
        "ambiguities": len(report["ambiguities"]),
        "report": str(out / "self-review.json"),
        "causal_case": str(out / "audited-case.json"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--replay-case", type=Path)
    parser.add_argument("--prior-review", type=Path)
    args = parser.parse_args()
    if args.replay_case:
        if args.prior_review is None:
            parser.error("--replay-case requires --prior-review")
        result = replay_retained_case(args.replay_case.resolve(), args.prior_review.resolve(), args.out.resolve())
    else:
        result = run(args.out.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in ("passed", "protected_demo_fitting_query_disagreement") else 1


if __name__ == "__main__":
    raise SystemExit(main())
