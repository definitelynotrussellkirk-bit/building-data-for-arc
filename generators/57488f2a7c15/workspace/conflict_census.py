#!/usr/bin/env python3
"""Census ordinary draws with independent grid checks and source-bound witnesses.

From the packet root:
  python3 run_with_racket.py python3 generators/57488f2a7c15/workspace/conflict_census.py \
    --seeds 10000 --out ../checks/conflicts-after.json

Use --expect-violations only to retain an intentionally failing baseline. It
requires at least one measured violation and never converts the report to a pass.
The first retained conflict in each band is also executed through Catalog.apply.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_path, find_root


TASK_ID = "57488f2a7c15"
BANDS = ("easy", "medium", "hard")


def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_digest(grid):
    return digest_bytes(json.dumps(grid, separators=(",", ":")).encode())


def selected_source(root):
    paths = (root / "generators" / TASK_ID / "generator.py",
             root / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py")
    return next(path for path in paths if path.is_file())


def import_generator(source):
    spec = importlib.util.spec_from_file_location("symmetry_census_generator", source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inspect_grid(grid):
    """Return independent domain failures; never call generator helper code."""
    if not isinstance(grid, list) or not grid:
        return {"malformed": "grid is not a nonempty list"}
    if any(not isinstance(row, list) or not row for row in grid):
        return {"malformed": "rows are not nonempty lists"}
    if len({len(row) for row in grid}) != 1:
        return {"malformed": "ragged rows"}
    if len(grid) > 30 or len(grid[0]) > 30:
        return {"malformed": "grid dimensions exceed 30"}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"malformed": "cells are not integer colors 0..9"}
    if len(grid) != len(grid[0]):
        return {"non_square": [len(grid), len(grid[0])]}
    conflicts = [
        {"positions": [[r, c], [c, r]], "colors": [grid[r][c], grid[c][r]]}
        for r in range(len(grid)) for c in range(r + 1, len(grid))
        if grid[r][c] != 0 and grid[c][r] != 0 and grid[r][c] != grid[c][r]
    ]
    findings = {"conflicts": conflicts} if conflicts else {}
    if all(grid[r][c] == grid[c][r]
           for r in range(len(grid)) for c in range(r + 1, len(grid))):
        findings["no_op"] = True
    return findings


def source_identity(root, source):
    ledger = canonical_path(root)
    rows = [json.loads(line) for line in ledger.read_text().splitlines()
            if line.strip() and json.loads(line).get("task_id") == TASK_ID]
    rules = {row["program_solution"] for row in rows}
    if len(rules) != 1:
        raise ValueError(f"Expected one exact canonical rule, found {len(rules)}")
    rule = rules.pop()
    return {
        "generator_path": source.relative_to(root).as_posix(),
        "generator_sha256": digest_bytes(source.read_bytes()),
        "census_path": Path(__file__).resolve().relative_to(root).as_posix(),
        "census_sha256": digest_bytes(Path(__file__).read_bytes()),
        "canonical_path": ledger.relative_to(root).as_posix(),
        "canonical_ledger_sha256": digest_bytes(ledger.read_bytes()),
        "canonical_task_rows_sha256": digest_bytes(json.dumps(rows, sort_keys=True,
                                                              separators=(",", ":")).encode()),
        "rule_text": rule,
        "rule_text_sha256": digest_bytes(rule.encode()),
        "rule_hash": digest_bytes(" ".join(rule.split()).encode())[:12],
        "loaded_generator_dependencies": [
            {"path": path.relative_to(root).as_posix(), "sha256": digest_bytes(path.read_bytes())}
            for path in sorted({Path(module.__file__).resolve()
                                for name, module in tuple(sys.modules.items())
                                if name.startswith("puzzle_generators") and getattr(module, "__file__", None)
                                and Path(module.__file__).resolve().is_relative_to(root)})
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=10000,
                        help="draw seeds 0..N-1 in each band, with sample_index=seed")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--witnesses", type=int, default=3,
                        help="maximum exact witnesses of each kind per band")
    parser.add_argument("--expect-violations", action="store_true")
    args = parser.parse_args(argv)
    if args.seeds < 1 or not 1 <= args.witnesses <= 10:
        parser.error("seeds must be positive and witnesses must be 1..10")
    if args.out.exists():
        parser.error("output already exists; use a new path to retain earlier evidence")

    root = find_root(__file__)
    source = selected_source(root)
    generator = import_generator(source)
    identity = source_identity(root, source)
    report = {
        "schema": "main-diagonal-conflict-census-v1",
        "task_id": TASK_ID,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, *sys.argv],
        "cwd": str(Path.cwd()),
        "library_root": str(root),
        "source_identity": identity,
        "sampling": {"bands": list(BANDS), "seed_start": 0, "seed_stop_exclusive": args.seeds,
                     "sample_index": "seed", "overrides": {}, "seeds_per_band": args.seeds},
        "expect_violations": args.expect_violations,
        "per_band": {},
        "status": "running",
    }
    reference_witnesses = []
    all_input_hashes = set()
    count_names = ("attempted", "generated", "generation_errors", "malformed", "non_square",
                   "no_op", "conflict_draws", "conflict_orbits", "accepted_conflict_draws",
                   "self_check_rejections", "self_check_errors", "malformed_self_check_returns",
                   "violation_draws", "unique_inputs")
    for band in BANDS:
        counts = Counter({name: 0 for name in count_names})
        witnesses = {}
        input_hashes = set()
        for seed in range(args.seeds):
            counts["attempted"] += 1
            witness = {"difficulty": band, "seed": seed, "sample_index": seed, "overrides": {}}
            try:
                grid = generator.generate(seed=seed, sample_index=seed, difficulty=band)
            except Exception as exc:
                counts["generation_errors"] += 1
                findings = {"generation_errors": f"{type(exc).__name__}: {exc}"}
            else:
                counts["generated"] += 1
                findings = inspect_grid(grid)
                witness["input"] = grid
                try:
                    witness["input_sha256"] = grid_digest(grid)
                    input_hashes.add(witness["input_sha256"])
                except (TypeError, ValueError):
                    witness["input"] = repr(grid)
                try:
                    errors = generator.self_check(grid, difficulty=band)
                    witness["self_check"] = errors
                    if not isinstance(errors, list) or any(not isinstance(error, str) for error in errors):
                        findings["malformed_self_check_returns"] = repr(errors)
                        counts["malformed_self_check_returns"] += 1
                    elif errors:
                        counts["self_check_rejections"] += 1
                        findings["self_check_rejections"] = errors
                    elif findings.get("conflicts"):
                        counts["accepted_conflict_draws"] += 1
                except Exception as exc:
                    findings["self_check_errors"] = f"{type(exc).__name__}: {exc}"
                    counts["self_check_errors"] += 1
                for name in ("malformed", "non_square", "no_op"):
                    counts[name] += int(name in findings)
                if findings.get("conflicts"):
                    counts["conflict_draws"] += 1
                    counts["conflict_orbits"] += len(findings["conflicts"])
            if findings:
                counts["violation_draws"] += 1
                witness["findings"] = findings
                for kind in findings:
                    if len(witnesses.setdefault(kind, [])) < args.witnesses:
                        witnesses[kind].append(witness)
        counts["unique_inputs"] = len(input_hashes)
        all_input_hashes.update(input_hashes)
        report["per_band"][band] = {"counts": dict(counts), "witnesses": witnesses}
        if witnesses.get("conflicts"):
            reference_witnesses.append(witnesses["conflicts"][0])

    report["totals"] = {name: sum(item["counts"][name] for item in report["per_band"].values())
                        for name in count_names}
    report["totals"]["unique_inputs"] = len(all_input_hashes)
    report["reference_witnesses"] = None
    report["errors"] = []
    if reference_witnesses:
        try:
            applied = Catalog(root=root).apply(TASK_ID, [item["input"] for item in reference_witnesses],
                                               timeout=120)
            report["reference_witnesses"] = {
                "inputs": reference_witnesses, "application": applied,
                "hash_note": "source_identity.rule_text_sha256 hashes exact canonical source; "
                             "application.rule_text_sha256 hashes the runtime's wrapped callable",
            }
            if (applied["generator_sha256"] != identity["generator_sha256"]
                    or applied["executed_rule_hash"] != identity["rule_hash"]
                    or not applied["rule_hash_matches_catalog"]):
                raise RuntimeError("Reference witness execution source identity does not match census")
            if (len(applied["results"]) != len(reference_witnesses)
                    or any(not item["valid_output"] for item in applied["results"])):
                raise RuntimeError("Reference witness execution did not return every valid output")
        except Exception as exc:
            report["errors"].append(f"reference witness execution: {type(exc).__name__}: {exc}")
    if digest_bytes(source.read_bytes()) != identity["generator_sha256"]:
        report["errors"].append("generator source changed during census")
    if digest_bytes(canonical_path(root).read_bytes()) != identity["canonical_ledger_sha256"]:
        report["errors"].append("canonical ledger changed during census")
    violations = report["totals"]["violation_draws"]
    report["status"] = "error" if report["errors"] else ("violations_found" if violations else "no_violations_found")
    report["exit_code"] = 2 if report["errors"] else int(bool(violations) != args.expect_violations)
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "status": report["status"], "exit_code": report["exit_code"],
                      "generator_sha256": identity["generator_sha256"], "totals": report["totals"]},
                     sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
