"""Replay every cyclic lesson start with real Racket labels and live rivals.

From the extracted packet root:
  python3 run_with_racket.py python3 generators/e937c5b85cdd/workspace/probe_lessons.py --out ../checks/cycles.json

The ordinary public lesson census additionally checks materializer rejections.
This complementary probe enumerates the small deterministic schedule directly.
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

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK = "e937c5b85cdd"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seeds", type=int, default=12)
    args = parser.parse_args()
    if args.seeds < 1 or args.out.exists():
        parser.error("--seeds must be positive and --out must be a new path")
    root = find_root(__file__)
    source = root / "generators" / TASK / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("live_cross_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rivals, declarations = {}, {}
    # Preserve the contract's explicit lesson override precedence. New rivals
    # participate automatically; the probe contains no copied rival-name list.
    for namespace in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declared = getattr(gen, namespace, {})
        declarations[namespace] = list(declared)
        rivals.update(declared)
    if not rivals:
        raise ValueError("No live declared rivals; cannot establish a rival pass")
    period, n_train = len(gen.SCHEDULE_PROFILES), gen.EXAMPLES_NEEDED
    report = {
        "schema": "cross-cycle-probe-v1", "task_id": TASK,
        "generator_sha256": source_hash, "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH, "declarations": declarations,
        "period": period, "train_pairs": n_train,
        "seed_range_inclusive": [0, args.seeds - 1],
        "sample_index_range_inclusive": [0, period + n_train - 1],
        "command": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "authority_batches": [], "inputs": [], "windows": [], "failures": [],
        "limits": "Finite declared-rival evidence; direct draws have no materializer rejection layer.",
    }
    records, unique = [], {}
    for band in ("easy", "medium", "hard"):
        for seed in range(args.seeds):
            for index in range(period + n_train):
                grid = gen.generate(seed, index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    raise ValueError((band, seed, index, errors))
                key = digest(grid)
                unique[key] = grid
                records.append({"band": band, "seed": seed, "sample_index": index,
                                "profile": gen.schedule_profile(seed, index, band), "input_hash": key})
    # Complementary boundary: a length-three single cross painting the nearer
    # edge remains available under exact overrides, outside ordinary scheduling.
    control_overrides = {"grid_h": 11, "grid_w": 11, "cross_count": 1, "max_arm_len": 3}
    control = gen.generate(0, 0, difficulty="easy", **control_overrides)
    control_hash = digest(control)
    unique[control_hash] = control
    report["exact_override_control"] = {"seed": 0, "sample_index": 0, "difficulty": "easy",
                                        "overrides": control_overrides, "input_hash": control_hash,
                                        "self_check": gen.self_check(control)}
    canonical = canonical_pairs(TASK, root=root)
    report["canonical_fit"] = {
        name: {"matched": sum(rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical),
               "total": len(canonical)} for name, rival in rivals.items()
    }
    report["canonical_unique_pairs"] = len({digest([p["input"], p["output"]]) for p in canonical})
    outputs, items = {}, list(unique.items())
    catalog = Catalog(root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(items), 64):
        batch = items[start:start + 64]
        receipt = catalog.apply(TASK, [grid for _, grid in batch], reference="canonical", timeout=180)
        report["authority_batches"].append({k: v for k, v in receipt.items() if k != "results"})
        if receipt["generator_sha256"] != source_hash or receipt["executed_rule_hash"] != gen.RULE_HASH:
            raise ValueError("source or reference changed during the probe")
        if len(receipt["results"]) != len(batch):
            raise ValueError("reference returned a short batch")
        for (key, grid), result in zip(batch, receipt["results"]):
            if result.get("error") or result.get("output") is None:
                report["failures"].append({"input_hash": key, "reference_error": result.get("error")})
                continue
            output = result["output"]
            outputs[key] = output
            fits = {name: rival(deepcopy(grid)) == output for name, rival in rivals.items()}
            report["inputs"].append({"input_hash": key, "input": grid, "output_racket": output,
                                      "rival_fits": fits})
        args.out.write_text(json.dumps({**report, "status": "running"}, separators=(",", ":")) + "\n")
    fits_by_hash = {record["input_hash"]: record["rival_fits"] for record in report["inputs"]}
    by_identity = {(r["band"], r["seed"], r["sample_index"]): r for r in records}
    ambiguity = Counter()
    for band in ("easy", "medium", "hard"):
        for seed in range(args.seeds):
            for start in range(period):
                members = [by_identity[band, seed, start + j] for j in range(n_train + 1)]
                rotation_results = []
                for query in range(n_train + 1):
                    demo_indices = [j for j in range(n_train + 1) if j != query]
                    for name in rivals:
                        fit = [fits_by_hash[m["input_hash"]][name] for m in members]
                        if all(fit[j] for j in demo_indices) and not fit[query]:
                            ambiguity[name] += 1
                            report["failures"].append({"band": band, "seed": seed, "start": start,
                                                       "query_position": query, "rival": name})
                    pairs = [{"input": unique[m["input_hash"]], "output": outputs[m["input_hash"]]}
                             for m in members]
                    reasons = gen.lesson_identifiable([pairs[j] for j in demo_indices], pairs[query])
                    if reasons:
                        report["failures"].append({"band": band, "seed": seed, "start": start,
                                                   "query_position": query, "hook_reasons": reasons})
                    rotation_results.append({"query_sample_index": start + query,
                                             "demo_sample_indices": [start + j for j in demo_indices],
                                             "hook_reasons": reasons})
                report["windows"].append({"band": band, "seed": seed, "start": start,
                                           "members": members, "rotations": rotation_results})
    report["summary"] = {"generated_draws": len(records), "unique_labeled_inputs_including_control": len(outputs),
                           "cyclic_windows": len(report["windows"]),
                           "query_rotations": len(report["windows"]) * (n_train + 1),
                           "ambiguous_by_rival": dict(ambiguity), "failures": len(report["failures"])}
    report["source_unchanged"] = hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    report["status"] = "pass" if not report["failures"] and report["source_unchanged"] else "fail"
    args.out.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "generator_sha256": source_hash, **report["summary"]}))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
