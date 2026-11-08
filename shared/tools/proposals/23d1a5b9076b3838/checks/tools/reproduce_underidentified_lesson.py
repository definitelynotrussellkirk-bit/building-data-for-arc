#!/usr/bin/env python3
"""Build a source-bound lesson that passes label/uniqueness checks but is ambiguous.

The three demonstrations place the unique pure block in the top-left, so the
intended rule and the shortcut "always crop the top-left block" agree.  The
query moves the pure block elsewhere, where the shortcut diverges.  This is a
minimal witness for a demonstration-only identifiability gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import find_root, load_selected_generator

TASK_ID = "4d5bb3c0250b"
PROFILE = "canonical_23_5x4"
SCHEMA = "arcpuzzles-underidentified-lesson-reproducer-v1"


def _grid_hash(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _case(generator: Any, attempt: int) -> dict[str, Any]:
    seed = 910_000 + attempt
    sample_index = 70_000 + attempt
    grid = generator.generate(
        seed,
        sample_index,
        difficulty="medium",
        profile=PROFILE,
        target_at_border=True,
        target_cells=4,
        distractor_colors=3,
    )
    answer = generator.rule_mirror(grid)
    rival = generator._crop_top_left_block(grid)
    data = generator._analyze(grid)
    pure = data["pure"][0]
    return {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "overrides": {
            "profile": PROFILE,
            "target_at_border": True,
            "target_cells": 4,
            "distractor_colors": 3,
        },
        "target_block": [pure["ri"], pure["ci"]],
        "input": grid,
        "output": answer,
        "input_sha256": _grid_hash(grid),
        "output_sha256": _grid_hash(answer),
        "rival_output_sha256": _grid_hash(rival),
        "rival_agrees": rival == answer,
    }


def find_underidentified_lesson(generator: Any, max_attempts: int = 512) -> dict[str, Any]:
    """Return 3 shortcut-compatible demos and 1 shortcut-refuting query."""
    demos: list[dict[str, Any]] = []
    query: dict[str, Any] | None = None
    seen: set[str] = set()
    attempts = 0
    for attempt in range(max_attempts):
        attempts = attempt + 1
        case = _case(generator, attempt)
        if case["input_sha256"] in seen:
            continue
        seen.add(case["input_sha256"])
        pair = {"input": case["input"], "output": case["output"]}
        if case["rival_agrees"] and len(demos) < 3:
            demos.append(pair | {"_reproduction": case})
        elif not case["rival_agrees"] and query is None:
            query = pair | {"_reproduction": case}
        if len(demos) == 3 and query is not None:
            break
    if len(demos) != 3 or query is None:
        raise RuntimeError(
            f"bounded search failed after {attempts} attempts: "
            f"demos={len(demos)}, query={query is not None}"
        )

    reasons = generator.lesson_identifiable(
        [{"input": row["input"], "output": row["output"]} for row in demos],
        {"input": query["input"]},
    )
    expected = ["demonstrations remain consistent with shortcut: crop_top_left_block"]
    if reasons != expected:
        raise AssertionError(f"unexpected identifiability verdict: {reasons!r}")
    return {
        "train": demos,
        "test": [query],
        "search_attempts": attempts,
        "legacy_checks": {
            "all_labels_match_rule_mirror": True,
            "all_four_inputs_distinct": len(seen) >= 4,
        },
        "identifiability_gate": {"passed": False, "reasons": reasons},
    }


def _strip_private_grids(lesson: dict[str, Any]) -> dict[str, Any]:
    def summarize(pair: dict[str, Any]) -> dict[str, Any]:
        return dict(pair["_reproduction"])

    return {
        "search_attempts": lesson["search_attempts"],
        "legacy_checks": lesson["legacy_checks"],
        "identifiability_gate": lesson["identifiability_gate"],
        "train": [summarize(pair) for pair in lesson["train"]],
        "test": [summarize(pair) for pair in lesson["test"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-attempts", type=int, default=512)
    args = parser.parse_args()

    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    lesson = find_underidentified_lesson(generator, args.max_attempts)
    report = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "generator_path": source.resolve().relative_to(root.resolve()).as_posix(),
        "generator_sha256": digest,
        "failure_class": (
            "labels and distinct-input checks pass, but all demonstrations remain "
            "consistent with a named shortcut that disagrees on the query"
        ),
        "lesson": _strip_private_grids(lesson),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "generator_sha256": digest,
        "search_attempts": lesson["search_attempts"],
        "demo_count": len(lesson["train"]),
        "query_count": len(lesson["test"]),
        "reasons": lesson["identifiability_gate"]["reasons"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
