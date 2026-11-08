#!/usr/bin/env python3
"""Authoring diagnostic: exhaust the selected finite witness shape-pair pools.

Labels use the generator's diagnostic set-operation helper, not Racket execution
per pair. One lawful representative placement is checked per distinct pair.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "c5a80b7a3acc"
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break
from reviewer_support import canonical_path, find_root


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check():
    root = find_root(__file__)
    source = root / "generators" / TASK / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("witness_pool_generator", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    ledger = canonical_path(root)
    rules = set()
    with ledger.open() as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK:
                    rules.add(hashlib.sha256(record["program_solution"].encode()).hexdigest())
    report = {
        "schema": "c5a80b7a3acc-witness-pools-v1", "task_id": TASK,
        "generator_sha256": sha(source), "canonical_ledger_sha256": sha(ledger),
        "canonical_rule_source_sha256": sorted(rules),
        "declared_rule_hash": gen.RULE_HASH, "probe_sha256": sha(__file__),
        "execution": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "label_basis": "diagnostic generator._intended_for_probe; no per-pair Racket execution",
        "limits": ["one representative placement per distinct shape pair",
                   "finite current declared rivals; no universal induction claim",
                   "default witness roles only; semantic overrides bypass schedule"],
        "pool_band": "medium", "overlaps": list(range(1, 7)),
        "rivals": list(gen.LESSON_COMPETITORS), "roles": {}, "errors": [],
    }
    if len(rules) != 1 or next(iter(rules), "")[:12] != gen.RULE_HASH:
        report["errors"].append("canonical authority does not match declared rule hash")
    guaranteed = set()
    for role in ("and_witness", "xor_witness"):
        if role not in gen.SCHEDULE_PROFILES:
            report["errors"].append(f"role {role} is not in actual schedule declarations")
        pools = {k: set(gen._pair_pool(k, "any", role, "medium")) for k in range(1, 7)}
        pairs = set().union(*pools.values())
        failures = dict.fromkeys(gen.LESSON_COMPETITORS, 0)
        validation_errors = []
        for a, b in sorted(pairs):
            grid = [[0] * 8 for _ in range(8)]
            for r, c in gen._mask_cells(a):
                grid[r][c] = 2
            for r, c in gen._mask_cells(b):
                grid[r + 4][c] = 3
            if role == "and_witness":
                grid[7][7] = 7
            grid[7][6] = 9
            errors = gen.self_check(grid)
            if errors:
                validation_errors.append({"masks": [a, b], "errors": errors})
            output = gen._intended_for_probe(grid)
            for name, rival in gen.LESSON_COMPETITORS.items():
                failures[name] += rival(grid) != output
        always = {name for name, count in failures.items() if pairs and count == len(pairs)}
        guaranteed.update(always)
        report["roles"][role] = {
            "distinct_pairs": len(pairs),
            "distinct_pairs_per_overlap": {str(k): len(v) for k, v in pools.items()},
            "refutations": failures, "refutation_intersection": sorted(always),
            "validation_errors": validation_errors,
        }
        if validation_errors or not all(pools.values()):
            report["errors"].append(f"{role}: invalid representative input or empty overlap pool")
    report["joint_guaranteed_refutations"] = sorted(guaranteed)
    report["uncovered_rivals"] = sorted(set(gen.LESSON_COMPETITORS) - guaranteed)
    if report["uncovered_rivals"]:
        report["errors"].append("some declared rivals lack a role-wide refutation")
    report["status"] = "pass" if not report["errors"] else "fail"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new JSON path; never overwritten")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"refusing to overwrite {args.out}")
    report = check()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(f"{report['status']}: {args.out}; "
          f"{sum(r['distinct_pairs'] for r in report['roles'].values())} distinct role pairs")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
