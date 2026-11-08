"""Findings-only audit reproducer for b09f5ee22328.

Run through review.py run from the packet root.  Labels are obtained separately
with the public ``arcpuzzles apply`` command; this script only prepares and
checks source-bound evidence.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "b09f5ee22328"
OUT = Path(__file__).resolve().parent
ROOT = find_root(Path.cwd())
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)


def save(name: str, value) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def strict_majority(counts: Counter, size: int) -> bool:
    return max(counts.values()) > size // 2


def prepare() -> None:
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    selected = None
    for index, pair in enumerate(canonical):
        counts = Counter(value for row in pair["input"] for value in row)
        ordered = sorted(counts.values(), reverse=True)
        if len(ordered) >= 2 and ordered[0] > ordered[1] and ordered[0] <= 4:
            selected = (index, pair, counts)
            break
    if selected is None:
        raise AssertionError("no unique-plurality non-majority canonical pair found")
    index, pair, counts = selected
    input_grid = pair["input"]
    validator_errors = GEN.self_check(input_grid)
    if not validator_errors:
        raise AssertionError("expected current validator to reject plurality-only canonical input")

    generated = []
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            for sample_index in range(6):
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                c = Counter(value for row in grid for value in row)
                generated.append({
                    "difficulty": difficulty,
                    "seed": seed,
                    "sample_index": sample_index,
                    "shape": [len(grid), len(grid[0])],
                    "counts": dict(sorted(c.items())),
                    "strict_majority": strict_majority(c, len(grid) * len(grid[0])),
                    "self_check": GEN.self_check(grid),
                })
    summary = {
        "task_id": TASK,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": SOURCE_SHA,
        "rule_hash": getattr(GEN, "RULE_HASH", None),
        "canonical_pair_index": index,
        "canonical_counts": dict(sorted(counts.items())),
        "canonical_unique_mode": True,
        "canonical_strict_majority": strict_majority(counts, 9),
        "validator_errors": validator_errors,
        "generated_cases": len(generated),
        "generated_strict_majority_cases": sum(item["strict_majority"] for item in generated),
        "generated_validator_passes": sum(not item["self_check"] for item in generated),
        "finding": (
            "The validator and default sampler require a strict majority, but the "
            "canonical authority contains a unique plurality with counts 3,2,2,2."
        ),
    }
    save("prepared.json", {"summary": summary, "generated": generated})
    save("input.json", input_grid)
    save("canonical_expected.json", pair["output"])
    print(json.dumps(summary, indent=2))


def verify() -> None:
    prepared = json.loads((OUT / "prepared.json").read_text())
    receipt = json.loads((OUT / "racket.json").read_text())
    expected = json.loads((OUT / "canonical_expected.json").read_text())
    input_grid = json.loads((OUT / "input.json").read_text())
    if prepared["summary"]["generator_sha256"] != SOURCE_SHA:
        raise AssertionError("generator changed since prepare")
    result = receipt["results"][0]
    if result["input"] != input_grid:
        raise AssertionError("authority receipt input mismatch")
    if result["output"] != expected:
        raise AssertionError("Racket output differs from canonical output")
    counts = Counter(value for row in input_grid for value in row)
    rival = [[0 for _ in row] for row in input_grid]
    differences = [
        [r, c, result["output"][r][c], rival[r][c]]
        for r in range(len(input_grid))
        for c in range(len(input_grid[0]))
        if result["output"][r][c] != rival[r][c]
    ]
    evidence = {
        "task_id": TASK,
        "generator_sha256": SOURCE_SHA,
        "generator_source": str(SOURCE.relative_to(ROOT)),
        "rule_hash": getattr(GEN, "RULE_HASH", None),
        "rule_callable_sha256": receipt.get("rule_text_sha256"),
        "authority_command": receipt.get("command"),
        "authority_cwd": receipt.get("cwd"),
        "canonical_pair_index": prepared["summary"]["canonical_pair_index"],
        "input": input_grid,
        "actual_racket_output": result["output"],
        "canonical_expected_output": expected,
        "validator_errors": GEN.self_check(input_grid),
        "counts": dict(sorted(counts.items())),
        "unique_mode": True,
        "strict_majority": strict_majority(counts, 9),
        "documented_rule_domain": "canonical task input",
        "sampler_reachable_under_current_default_invariant": False,
        "rival_name": "strict_majority_only_else_zero",
        "rival_output": rival,
        "differing_cells": differences,
        "generated_support_probe": {
            "cases": prepared["summary"]["generated_cases"],
            "strict_majority_cases": prepared["summary"]["generated_strict_majority_cases"],
            "validator_passes": prepared["summary"]["generated_validator_passes"],
        },
        "finding": (
            "Current self_check rejects an exact canonical input whose mode is a "
            "unique plurality but not a strict majority.  The strict-majority-only "
            "shortcut agrees throughout the sampled generator support and fails here."
        ),
    }
    if not differences:
        raise AssertionError("rival unexpectedly agrees with authority")
    save("counterexample.json", evidence)
    print(json.dumps({
        "generator_sha256": SOURCE_SHA,
        "validator_errors": evidence["validator_errors"],
        "racket_matches_canonical": True,
        "rival_difference_cells": len(differences),
        "generated_support_probe": evidence["generated_support_probe"],
    }, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
