#!/usr/bin/env python3
"""Reproduce and measure unchecked contact-pair placement in 102e79f0ca6d."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / "repo"
TASK_ID = "102e79f0ca6d"
GEN_PATH = REPO / "generators" / TASK_ID / "generator.py"

spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}", GEN_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {GEN_PATH}")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

probe = {"seed": 2, "sample_index": 3, "difficulty": "easy"}
grid = gen.generate(**probe)
errors = gen.self_check(grid, difficulty=probe["difficulty"])
assert errors == ["no two adjacent cells of different colors — no contact boundary"]

counts: Counter[str] = Counter()
examples = []
for difficulty in ("easy", None, "hard"):
    band = "medium" if difficulty is None else difficulty
    for seed in range(100):
        for sample_index in range(20):
            candidate = gen.generate(seed, sample_index, difficulty=difficulty)
            candidate_errors = gen.self_check(candidate, difficulty=difficulty)
            counts[f"{band}:total"] += 1
            if candidate_errors:
                counts[f"{band}:invalid"] += 1
                counts["all:invalid"] += 1
                if len(examples) < 10:
                    examples.append({
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": candidate_errors,
                        "input": candidate,
                    })
            counts["all:total"] += 1

racket = json.loads((Path(__file__).with_name("racket.json")).read_text())
report = {
    "schema": "arc-generator-audit-reproducer-v2",
    "task_id": TASK_ID,
    "generator_path": str(GEN_PATH.relative_to(ROOT)),
    "generator_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "generator_version": gen.VERSION,
    "executed_rule_hash": racket["executed_rule_hash"],
    "probe": {
        **probe,
        "overrides": {},
        "input": grid,
        "self_check_errors": errors,
        "input_passes_validator": False,
        "racket_output": racket["results"][0]["output"],
        "rival_name": None,
        "rival_output": None,
        "input_sha256": racket["results"][0]["input_sha256"],
        "output_sha256": racket["results"][0]["output_sha256"],
        "belongs_to_documented_generator_domain": True,
    },
    "census": {
        "seed_range": "0..99 inclusive",
        "sample_index_range": "0..19 inclusive",
        "bands": ["easy", "medium", "hard"],
        "counts": dict(sorted(counts.items())),
        "invalid_examples": examples,
    },
    "finding": (
        "ordinary default generation can return inputs with no differently colored "
        "adjacent cells, contradicting the rule premise and self_check"
    ),
    "root_cause": (
        "generate() ignores the boolean result from the second _try_place call. "
        "When all 80 random trials miss the newly placed A component, A remains "
        "isolated and generation continues."
    ),
    "reproduce": {
        "cwd": str(ROOT),
        "argv": ["python3", "checks/audit/102e79f0ca6d/reproduce.py"],
    },
}
Path(__file__).with_name("reproducer.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n"
)
print(json.dumps({
    "probe_errors": errors,
    "census_counts": report["census"]["counts"],
    "out": str(Path(__file__).with_name("reproducer.json")),
}, indent=2, sort_keys=True))
