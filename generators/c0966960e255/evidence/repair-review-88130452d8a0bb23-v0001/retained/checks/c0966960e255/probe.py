#!/usr/bin/env python3
"""Bounded source-bound learnability probe for c0966960e255."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = "c0966960e255"
EXPECTED_SOURCE_SHA256 = "45df359d3e79a21762f9906ba590a6213d22741e7864924ef861939bda7e3694"


def literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)

    gen, source_path, source_sha = load_selected_generator(TASK_ID)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"peer source differs: {source_sha}")

    solution_path = Path("shared/data/base/solutions/banks/54d03287ae93/E36__c0966960e255.json")
    solution = json.loads(solution_path.read_text(encoding="utf-8"))
    canonical_program = solution["racket_target"]["target_code"]
    wrapped = wrap_rule(canonical_program)

    failures = []
    lessons = 0
    visible_inputs = 0
    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    parity_cases = []
    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for seed in range(12):
                inputs = [
                    gen.generate(1000 * band_index + seed, seed * 101 + offset, difficulty=difficulty)
                    for offset in range(4)
                ]
                visible_inputs += len(inputs)
                demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in inputs[:3]]
                query = {"input": inputs[3]}
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({"kind": "surviving_competitor", "difficulty": difficulty, "seed": seed, "reasons": reasons})
                for index, grid in enumerate(inputs):
                    analysis = gen._analyze(grid)
                    if analysis["errors"]:
                        failures.append({"kind": "invalid_generated_input", "difficulty": difficulty, "seed": seed, "index": index, "errors": analysis["errors"]})
                    firing = {name for name, predicate in gen.SEMANTIC_WITNESSES.items() if predicate(grid)}
                    for name in firing:
                        witness_counts[name] += 1
                    if firing != set(gen.SEMANTIC_WITNESSES):
                        failures.append({"kind": "missing_witness", "difficulty": difficulty, "seed": seed, "index": index, "firing": sorted(firing)})
                if seed == 0:
                    racket_output = bridge.eval_text(f"({wrapped} {literal(inputs[3])})")
                    expected = gen.rule_mirror(inputs[3])
                    if racket_output != expected:
                        failures.append({"kind": "racket_mismatch", "difficulty": difficulty})
                    parity_cases.append({
                        "difficulty": difficulty,
                        "input": inputs[3],
                        "output": racket_output,
                        "shape": [len(inputs[3]), len(inputs[3][0])],
                    })
                lessons += 1
        runtime = bridge.runtime_identity
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-peer-learnability-probe-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "finding",
        "source": {"path": str(source_path), "sha256": source_sha},
        "totals": {
            "lessons": lessons,
            "demonstrations_per_lesson": 3,
            "queries_per_lesson": 1,
            "visible_inputs": visible_inputs,
            "protected_racket_evaluations": len(parity_cases),
            "finite_competitors": 6,
        },
        "semantic_witness_firings": witness_counts,
        "racket_parity_cases": parity_cases,
        "canonical_program_sha256": hashlib.sha256(canonical_program.encode()).hexdigest(),
        "failures": failures,
        "racket": runtime,
        "finding": None if not failures else "See failures.",
        "limits": "36 generated three-demo lessons against the generator's six declared competitors plus three protected-Racket parity cases; not universal uniqueness or owner approval.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "totals": report["totals"], "failures": len(failures), "out": str(out)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
