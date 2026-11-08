#!/usr/bin/env python3
"""Audit every requested lesson start and holdout against DECLARED rivals.

Run from a packet with run_with_racket.py; e.g.:
  python3 run_with_racket.py python3 generators/5430502683a1/workspace/probe_lesson_windows.py --out ../checks/cyclic-windows.json

This reusable authoring tool obtains all labels via Catalog.apply, retains exact
inputs/outputs and receipts, reads current rival dictionaries, checks canonical
shortcut claims, and records source hashes. It is NOT a blind-solve tool.
The start count is explicit: a schedule claim must include every relevant phase.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_generator(root, task):
    candidates = (root / "generators" / task / "generator.py",
                  root / "puzzle_generators" / "per_puzzle" / task / "generator.py")
    path = next(path for path in candidates if path.is_file())
    spec = importlib.util.spec_from_file_location("window_probe_generator", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return path, module


def write_checkpoint(path, report):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", default="5430502683a1")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--demos", type=int)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if min(args.seeds, args.starts) < 1:
        parser.error("seeds and starts must be positive")
    if args.out.exists():
        parser.error("output already exists; retain earlier evidence and use a new path")
    root = find_root(__file__)
    path, generator = load_generator(root, args.task)
    n_demos = args.demos if args.demos is not None else getattr(generator, "EXAMPLES_NEEDED", 3)
    if not 1 <= n_demos <= 32:
        parser.error("demos must be in 1..32")
    # Always inspect actual dictionaries; no copied rival-name list can drift.
    competitors = dict(getattr(generator, "LESSON_COMPETITORS", {}))
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    competitors.update(shortcuts)
    if not competitors:
        parser.error("no declared competitors; an empty rival set is not a pass")
    catalog = Catalog(root)
    description = catalog.describe(args.task)
    canonical = canonical_pairs(args.task, root=root, labeled_only=True)
    canonical_checks = {
        name: {"matched": sum(rival(pair["input"]) == pair["output"] for pair in canonical),
               "total": len(canonical)}
        for name, rival in shortcuts.items()
    }
    report = {
        "schema": "arcpuzzles-task-window-probe-v1", "status": "running",
        "task_id": args.task, "generator_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "canonical_file_sha256": hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
        "rule_hash": description["rule_hash"], "n_demos": n_demos, "n_queries": 1,
        "seed_range": [args.seed_start, args.seed_start + args.seeds - 1],
        "start_indices": list(range(args.starts)),
        "bands": ["easy", "medium", "hard"], "rivals": sorted(competitors),
        "canonical_shortcuts": canonical_checks, "command": [sys.executable, *sys.argv],
        "working_directory": str(Path.cwd()), "requested_windows": args.seeds * args.starts * 3,
        "completed_windows": 0, "completed_rotations": 0, "unique_input_hashes": [],
        "ambiguous_production": [], "ambiguous_rotations": [], "errors": [],
        "sources": [], "windows": [],
        "scope": "finite named-rival evaluation; no universal identifiability or training admission claim",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_checkpoint(args.out, report)
    hashes = set()
    try:
        for band in report["bands"]:
            for seed in range(args.seed_start, args.seed_start + args.seeds):
                records = []
                count = args.starts + n_demos
                for index in range(count):
                    grid = generator.generate(seed, index, difficulty=band)
                    reasons = generator.self_check(grid, difficulty=band)
                    if reasons:
                        raise ValueError(f"invalid input {band}/{seed}/{index}: {reasons}")
                    records.append({"sample_index": index, "input": grid, "input_sha256": digest(grid)})
                source_index = len(report["sources"])
                receipts = []
                for offset in range(0, len(records), 64):
                    batch = records[offset:offset + 64]
                    receipt = catalog.apply(args.task, [r["input"] for r in batch], timeout=120)
                    if not receipt["rule_hash_matches_catalog"]:
                        raise ValueError("executed rule hash differs from catalog")
                    for record, result in zip(batch, receipt["results"], strict=True):
                        if result["output"] is None or result.get("error"):
                            raise ValueError(f"reference execution failure: {result}")
                        record["output"] = result["output"]
                        record["output_sha256"] = result["output_sha256"]
                        record["input_sha256"] = result["input_sha256"]
                        hashes.add(record["input_sha256"])
                    receipts.append({key: value for key, value in receipt.items() if key != "results"})
                report["sources"].append({"band": band, "seed": seed, "pairs": records, "receipts": receipts})
                predictions = {name: [rival(record["input"]) for record in records]
                               for name, rival in competitors.items()}
                for start in range(args.starts):
                    indices = list(range(start, start + n_demos + 1))
                    witness = {name: [i for i in indices if values[i] != records[i]["output"]]
                               for name, values in predictions.items()}
                    production_query = indices[-1]
                    ambiguities = [name for name, refuting in witness.items() if refuting == [production_query]]
                    if ambiguities:
                        report["ambiguous_production"].append({"source": source_index, "start": start,
                                                              "query_index": production_query, "rivals": ambiguities})
                    rotations = []
                    for query_index in indices:
                        rivals = [name for name, refuting in witness.items() if refuting == [query_index]]
                        if rivals:
                            item = {"source": source_index, "start": start, "query_index": query_index, "rivals": rivals}
                            report["ambiguous_rotations"].append(item)
                            rotations.append(item)
                        report["completed_rotations"] += 1
                    report["windows"].append({"source": source_index, "start": start, "pair_indices": indices,
                                              "refuting_pair_indices": witness,
                                              "production_ambiguities": ambiguities, "rotation_ambiguities": rotations})
                    report["completed_windows"] += 1
                report["unique_input_hashes"] = sorted(hashes)
                write_checkpoint(args.out, report)
                print(f"{band} seed={seed}: {report['completed_windows']} windows, {report['completed_rotations']} rotations", flush=True)
        report["canonical_shortcut_claims_valid"] = all(
            result["matched"] == result["total"] for result in canonical_checks.values())
        report["status"] = ("passed" if report["canonical_shortcut_claims_valid"]
                            and not report["ambiguous_production"] and not report["ambiguous_rotations"] else "failed")
    except Exception as exc:
        report["status"] = "error"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    report["unique_inputs"] = len(hashes)
    write_checkpoint(args.out, report)
    print(json.dumps({key: report[key] for key in ("status", "completed_windows", "completed_rotations", "unique_inputs")}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
