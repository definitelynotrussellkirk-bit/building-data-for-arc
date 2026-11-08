#!/usr/bin/env python3
"""Build source-bound audit evidence without importing private runner code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

WORK = Path(__file__).resolve().parents[3]
TASK = "2282d057d92e"
AUDIT = WORK / "checks" / "audit" / TASK
CANONICAL = WORK / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
GENERATOR = WORK / "repo" / "generators" / TASK / "generator.py"


def first_grid_occurrence_per_color(grid: list[list[int]]) -> list[list[int]]:
    """Wrong but canonical-compatible rule: only the first seed of each color casts."""
    out = [row[:] for row in grid]
    seen: set[int] = set()
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or color in seen:
                continue
            seen.add(color)
            cc = c + 1
            while cc < len(row) and grid[r][cc] == 0:
                out[r][cc] = color
                cc += 1
    return out


def load_task() -> dict:
    for line in CANONICAL.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK:
            return record
    raise RuntimeError(f"missing canonical task {TASK}")


def main() -> None:
    canonical = load_task()
    canonical_fit = [
        first_grid_occurrence_per_color(pair["input"]) == pair["output"]
        for pair in canonical["train"]
    ]
    assert all(canonical_fit)

    episode = json.loads((AUDIT / "episode-seed0.jsonl").read_text().splitlines()[0])
    pair = episode["train"][0]
    racket = json.loads((AUDIT / "racket.json").read_text())
    actual = racket["results"][0]["output"]
    rival = first_grid_occurrence_per_color(pair["input"])
    assert pair["input"] == racket["results"][0]["input"]
    assert pair["output"] == actual
    assert rival != actual

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "finding": (
            "All three canonical demonstrations use every color once, so the rival "
            "'only the first row-major occurrence of each color casts rightward' fits them. "
            "Production seed 0/sample 0 repeats color 6 on three rows and refutes it."
        ),
        "generator_sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest(),
        "rule_hash": racket["executed_rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "generation": {
            "seed": episode["seed"],
            "sample_index": episode["sample_indices"][0],
            "difficulty": episode["provenance"]["difficulty"],
            "overrides": episode["provenance"]["overrides"],
        },
        "canonical_demonstrations_checked": len(canonical_fit),
        "canonical_rival_fit": canonical_fit,
        "documented_generator_domain": racket["results"][0]["generator_domain"]["status"] == "valid",
        "self_check_errors": racket["results"][0]["generator_domain"]["errors"],
        "input": pair["input"],
        "actual_racket_output": actual,
        "rival_name": "first_grid_occurrence_per_color",
        "rival_output": rival,
        "commands": [
            {
                "cwd": "WORK",
                "argv": [
                    "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "generate", TASK,
                    "--count", "1", "--seed", "0", "--sample-index", "0", "--difficulty", "medium",
                    "--train", "3", "--test", "1", "--allow-unapproved", "--out",
                    "../checks/audit/2282d057d92e/episode-seed0.jsonl",
                ],
            },
            {
                "cwd": "WORK",
                "argv": [
                    "python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                    "--input", "../checks/audit/2282d057d92e/input.json", "--check-generator-domain",
                    "--out", "../checks/audit/2282d057d92e/racket.json",
                ],
            },
        ],
    }
    (AUDIT / "counterexample.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
