#!/usr/bin/env python3
"""Probe an undeclared D4-invariance shortcut for 70c33a3391ac."""
from __future__ import annotations

from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = "70c33a3391ac"
SOURCE_PATH = ROOT / "repo" / "generators" / TASK / "generator.py"
spec = importlib.util.spec_from_file_location(f"audit_{TASK}_generator", SOURCE_PATH)
assert spec is not None and spec.loader is not None
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def as_tuple(grid):
    return tuple(tuple(row) for row in grid)


def rotate_cw(grid):
    return tuple(tuple(grid[len(grid) - 1 - r][c] for r in range(len(grid))) for c in range(len(grid[0])))


def mirror_lr(grid):
    return tuple(tuple(reversed(row)) for row in grid)


def d4_key(grid):
    current = as_tuple(grid)
    variants = []
    for seed in (current, mirror_lr(current)):
        item = seed
        for _ in range(4):
            variants.append(item)
            item = rotate_cw(item)
    return min(variants)


def d4_rival(grid):
    """Wrong rule: compare component crops up to rotation/reflection, output first match."""
    components = GEN._components(grid)
    groups = defaultdict(list)
    first_order = []
    for component in components:
        key = d4_key(component["crop"])
        if key not in groups:
            first_order.append(key)
        groups[key].append(component)
    for key in first_order:
        if len(groups[key]) >= 2:
            return [list(row) for row in groups[key][0]["crop"]]
    raise ValueError("no repeated D4 crop")


def exact_output(grid):
    return [list(row) for row in GEN._analysis(grid)["duplicate"]["crop"]]


input_path = ROOT / "checks" / "audit" / TASK / "input.json"
racket_path = ROOT / "checks" / "audit" / TASK / "racket.json"
hand = json.loads(input_path.read_text())
racket = json.loads(racket_path.read_text())
actual = racket["results"][0]["output"]
rival = d4_rival(hand)
validator_errors = GEN.self_check(hand, difficulty=None)
observed = GEN.observe_overrides(hand)

canonical_total = 0
canonical_fit = 0
canonical_failures = []
seen = set()
with (ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl").open(encoding="utf-8") as handle:
    for line in handle:
        row = json.loads(line)
        if row.get("task_id") != TASK:
            continue
        for split in ("train", "test"):
            for index, pair in enumerate(row.get(split, [])):
                fingerprint = json.dumps(pair["input"], separators=(",", ":"))
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                canonical_total += 1
                got = d4_rival(pair["input"])
                if got == pair["output"]:
                    canonical_fit += 1
                else:
                    canonical_failures.append({"source": row.get("source"), "split": split, "index": index})

generated_total = 0
generated_fit = 0
generated_failures = []
for band_index, difficulty in enumerate(("easy", "medium", "hard")):
    for offset in range(200):
        seed = 80_000 + band_index * 10_000 + offset
        sample_index = band_index * 1000 + offset
        grid = GEN.generate(seed, sample_index, difficulty=difficulty)
        generated_total += 1
        got = d4_rival(grid)
        expected = exact_output(grid)
        if got == expected:
            generated_fit += 1
        elif len(generated_failures) < 12:
            generated_failures.append({
                "difficulty": difficulty,
                "seed": seed,
                "sample_index": sample_index,
                "observed": GEN.observe_overrides(grid),
            })

source_hash = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
result = {
    "schema": "arcpuzzles-audit-counterexample-v1",
    "task_id": TASK,
    "finding_kind": "reproduced undeclared D4-invariance shortcut",
    "documented_domain": True,
    "domain_reason": (
        "Hand-made grid passes self_check and realizes declared axes: five components, "
        "middle duplicate rank, shared palette, non-canonical prior."
    ),
    "generator_sha256": source_hash,
    "rule_hash": racket["executed_rule_hash"],
    "rule_hash_matches_catalog": racket["rule_hash_matches_catalog"],
    "input": hand,
    "actual_racket_output": actual,
    "rival_output": rival,
    "validator": {
        "self_check_errors": validator_errors,
        "passes_self_check": not validator_errors,
        "observed_overrides": observed,
    },
    "rival": {
        "name": "d4_equivalent_crop_first",
        "description": (
            "Treat rotated/reflected component crops as equal and return the first "
            "component belonging to the first repeated D4 class."
        ),
        "canonical_fit": {
            "fit": canonical_fit,
            "total_unique_pairs": canonical_total,
            "failures": canonical_failures,
        },
        "generated_fit": {
            "fit": generated_fit,
            "total": generated_total,
            "sample_policy": "200 ordinary draws per band; seeds 80000..80199, 90000..90199, 100000..100199",
            "failures": generated_failures,
        },
        "counterexample_disagrees": rival != actual,
    },
    "reproducer": {
        "cwd": racket["cwd"],
        "apply_command": racket["command"],
        "probe_command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/70c33a3391ac/probe.py",
        ],
    },
    "battery_summary": "checks/audit/70c33a3391ac/battery/checks/70c33a3391ac_after_battery_summary.json",
}
assert not validator_errors, validator_errors
assert actual != rival, (actual, rival)
assert canonical_fit == canonical_total, canonical_failures
out = ROOT / "checks" / "audit" / TASK / "counterexample.json"
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({
    "generator_sha256": source_hash,
    "rule_hash": result["rule_hash"],
    "passes_self_check": not validator_errors,
    "observed_overrides": observed,
    "canonical_fit": f"{canonical_fit}/{canonical_total}",
    "generated_fit": f"{generated_fit}/{generated_total}",
    "actual_racket_output": actual,
    "rival_output": rival,
    "counterexample": str(out.relative_to(ROOT)),
}, indent=2))
