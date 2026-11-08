#!/usr/bin/env python3
"""Source-bound shortcut probe for bf415be1791c.

The probe discovers the generator's declared canonical shortcuts, verifies that
those rules fit every labeled canonical pair, materializes a deterministic
counterexample that refutes each one, and enumerates every query holdout of the
declared finite schedule against every declared lesson competitor. It
deliberately keeps the selected Racket authority separate: run ``arcpuzzles
apply`` on the saved ``input.json`` and compare that receipt with this probe's
Python oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root

TASK_ID = "bf415be1791c"
TASK_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = TASK_DIR / "generator.py"
DEFAULT_OVERRIDES = {
    "grid_h": 10,
    "grid_w": 15,
    "divider_col": 6,
    "n_distractor_cells": 6,
    "n_distractor_colors": 2,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"review_probe_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_record(root: Path) -> dict[str, Any]:
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise RuntimeError(f"canonical record missing for {TASK_ID}")


def _schedule_rotation_probe(gen, schedule_seed: int) -> dict[str, Any]:
    by_rival = {
        name: {"ambiguity_count": 0, "ambiguities": []}
        for name in gen.LESSON_COMPETITORS
    }
    rotation_count = 0
    for difficulty in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                sample_index = start + offset
                grid = gen.generate(
                    schedule_seed,
                    sample_index,
                    difficulty=difficulty,
                )
                pairs.append(
                    {
                        "sample_index": sample_index,
                        "input": grid,
                        "output": gen.rule_mirror(grid),
                        "observed": gen.observe_overrides(grid),
                    }
                )
            for query_index, query in enumerate(pairs):
                rotation_count += 1
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                for name, rival in gen.LESSON_COMPETITORS.items():
                    survives = all(
                        rival(pair["input"]) == pair["output"] for pair in demos
                    )
                    changes_query = rival(query["input"]) != query["output"]
                    if survives and changes_query:
                        item = {
                            "difficulty": difficulty,
                            "start": start,
                            "query_index": query_index,
                            "query_sample_index": query["sample_index"],
                            "query_observed": query["observed"],
                            "demo_sample_indices": [
                                pair["sample_index"] for pair in demos
                            ],
                        }
                        by_rival[name]["ambiguities"].append(item)
                        by_rival[name]["ambiguity_count"] += 1
    return {
        "schedule_seed": schedule_seed,
        "period": gen.LESSON_SCHEDULE_PERIOD,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "bands": ["easy", "medium", "hard"],
        "rotation_count": rotation_count,
        "ambiguity_count": sum(
            item["ambiguity_count"] for item in by_rival.values()
        ),
        "by_rival": by_rival,
    }


def build_record(
    seed: int, sample_index: int, *, schedule_seed: int = 2609
) -> dict[str, Any]:
    root = find_root(__file__)
    gen = _load_generator()
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    record = _canonical_record(root)
    program = record["program_solution"]

    canonical_fit: dict[str, Any] = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        matches = [rival(pair["input"]) == pair["output"] for pair in pairs]
        canonical_fit[name] = {
            "matches": matches,
            "fits_all": all(matches),
            "pair_count": len(matches),
        }

    grid = gen.generate(seed, sample_index, **DEFAULT_OVERRIDES)
    intended = gen.rule_mirror(grid)
    rival_outputs = {
        name: rival(grid) for name, rival in gen.CANONICAL_SHORTCUTS.items()
    }
    disagreements = {
        name: output != intended for name, output in rival_outputs.items()
    }
    if not canonical_fit or not all(item["fits_all"] for item in canonical_fit.values()):
        raise RuntimeError("a declared canonical shortcut failed a canonical pair")
    if not all(disagreements.values()):
        missed = sorted(name for name, differs in disagreements.items() if not differs)
        raise RuntimeError(
            "production sample did not refute canonical shortcut(s): "
            + ", ".join(missed)
        )

    schedule_probe = _schedule_rotation_probe(gen, schedule_seed)
    if schedule_probe["ambiguity_count"]:
        raise RuntimeError(
            "declared schedule leaves query-rotation shortcut ambiguities"
        )

    return {
        "schema": "bf415be1791c-shortcut-probe-v2",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(GENERATOR_PATH),
        "declared_rule_hash": gen.RULE_HASH,
        "rule_source_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": None,
        "overrides": DEFAULT_OVERRIDES,
        "observed": gen.observe_overrides(grid),
        "self_check": gen.self_check(grid),
        "strict_canonical_like": gen.strict_canonical_like(grid),
        "canonical_shortcut_fit": canonical_fit,
        "input": grid,
        "python_intended_output": intended,
        "rival_outputs": rival_outputs,
        "disagrees_with_intended": disagreements,
        "schedule_rotation_probe": schedule_probe,
        "limitations": (
            "This is a finite source-bound check of declared rivals. The Python "
            "intended output is not the selected authority; compare input.json "
            "with a retained arcpuzzles apply receipt."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--input-out", type=Path)
    parser.add_argument("--seed", type=int, default=412)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--schedule-seed", type=int, default=2609)
    args = parser.parse_args()

    record = build_record(
        args.seed,
        args.sample_index,
        schedule_seed=args.schedule_seed,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if args.input_out:
        args.input_out.parent.mkdir(parents=True, exist_ok=True)
        args.input_out.write_text(
            json.dumps(record["input"], indent=2) + "\n", encoding="utf-8"
        )
    print(
        json.dumps(
            {
                "out": str(args.out),
                "input_out": str(args.input_out) if args.input_out else None,
                "generator_sha256": record["generator_sha256"],
                "rule_source_sha256": record["rule_source_sha256"],
                "canonical_shortcut_fit": record["canonical_shortcut_fit"],
                "disagrees_with_intended": record["disagrees_with_intended"],
                "schedule_rotation_probe": {
                    "rotation_count": record["schedule_rotation_probe"][
                        "rotation_count"
                    ],
                    "ambiguity_count": record["schedule_rotation_probe"][
                        "ambiguity_count"
                    ],
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
