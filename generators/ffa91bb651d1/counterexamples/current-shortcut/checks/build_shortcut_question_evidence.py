#!/usr/bin/env python3
"""Extract a source-bound generated counterexample from the retained lesson census."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "checks" / "lesson-census.json"
OUT = ROOT / "checks" / "shortcut-question.json"


def digest(obj: object) -> str:
    payload = json.dumps(obj, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def per_color_exact_pair(grid: list[list[int]]) -> list[list[int]]:
    """Fill each color's horizontal span whenever that color occurs twice in a row."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for color in sorted(set(row) - {0}):
            cols = [c for c, value in enumerate(row) if value == color]
            if len(cols) == 2:
                lo, hi = cols
                for c in range(lo, hi + 1):
                    out[r][c] = color
    return out


def main() -> None:
    census = json.loads(CENSUS.read_text())
    chosen = None
    canonical_checks = []
    canonical_path = ROOT / "repo" / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical_task = None
    for line in canonical_path.read_text().splitlines():
        candidate = json.loads(line)
        if candidate.get("task_id") == census["task_id"]:
            canonical_task = candidate
            break
    if canonical_task is None:
        raise SystemExit("canonical task not found")
    for split in ("train", "test"):
        for pair_index, pair in enumerate(canonical_task[split]):
            rival = per_color_exact_pair(pair["input"])
            canonical_checks.append({
                "split": split,
                "pair_index": pair_index,
                "input_sha256": digest(pair["input"]),
                "fits": rival == pair["output"],
            })
    if not all(item["fits"] for item in canonical_checks):
        raise SystemExit("rival does not fit every retained canonical pair")

    for lesson in census["lessons"]:
        pairs = [*lesson["instance"]["train"], *lesson["instance"]["test"]]
        accepted = lesson["instance"]["sampling"]["accepted_pairs"]
        for pair_index, pair in enumerate(pairs):
            rival = per_color_exact_pair(pair["input"])
            if rival != pair["output"]:
                differences = [
                    {"row": r, "col": c, "racket": pair["output"][r][c], "rival": rival[r][c]}
                    for r in range(len(pair["input"]))
                    for c in range(len(pair["input"][r]))
                    if pair["output"][r][c] != rival[r][c]
                ]
                chosen = {
                    "band": lesson["band"],
                    "lesson_index": lesson["index"],
                    "lesson_seed": lesson["seed"],
                    "lesson_sample_index": lesson["sample_index"],
                    "pair_role": "train" if pair_index < len(lesson["instance"]["train"]) else "test",
                    "pair_index": pair_index if pair_index < len(lesson["instance"]["train"]) else pair_index - len(lesson["instance"]["train"]),
                    "generator_sample_index": accepted[pair_index]["sample_index"],
                    "input_sha256": digest(pair["input"]),
                    "input": pair["input"],
                    "racket_output_sha256": digest(pair["output"]),
                    "racket_output": pair["output"],
                    "rival_output_sha256": digest(rival),
                    "rival_output": rival,
                    "differences": differences,
                }
                break
        if chosen:
            break
    if chosen is None:
        raise SystemExit("no generated counterexample found")

    evidence = {
        "schema": "ffa91bb651d1-shortcut-question-v1",
        "task_id": census["task_id"],
        "generator_sha256": census["generator_sha256"],
        "rule_source_sha256": census["rule_source_sha256"],
        "rule_callable_sha256": census["rule_callable_sha256"],
        "declared_rule_hash": census["declared_rule_hash"],
        "source_evidence": "checks/lesson-census.json",
        "source_status": census["status"],
        "rival": {
            "name": "per_color_exact_pair",
            "description": "For each row and each nonzero color independently, fill between that color's two occurrences, even when the row contains another nonzero cell.",
            "canonical_pairs_checked": len(canonical_checks),
            "canonical_fit": canonical_checks,
        },
        "generated_counterexample": chosen,
        "checked_by": "Independent Python rival compared with the source-bound Racket labels retained by lesson-census.",
        "command": [
            "python3", "checks/build_shortcut_question_evidence.py"
        ],
        "cwd": "packet_root",
    }
    OUT.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({
        "status": "PASS",
        "canonical_pairs": len(canonical_checks),
        "counterexample_input_sha256": chosen["input_sha256"],
        "difference_cells": len(chosen["differences"]),
        "output": str(OUT.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
