#!/usr/bin/env python3
"""Fast exhaustive probe for this generator's deterministic lesson schedule.

This source-level probe is intentionally cheaper than the Racket-labelled shared
lesson census.  It enumerates cyclic starts, every held-out query position, and
all rivals declared by the generator.  It also proves that every declared
CANONICAL_SHORTCUT fits every public labelled pair.  It is a regression aid, not
a proof against undeclared hypotheses and not a replacement for the shared
production census.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


TASK_ID = "341758fa9de1"
ROOT = find_root(HERE)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SPEC = importlib.util.spec_from_file_location("probe_generator_341758fa9de1", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def intended(grid):
    key = next((value for row in grid for value in row if value != 0), None)
    if key is None:
        return [row[:] for row in grid]
    return [[value if value == key else 0 for value in row] for row in grid]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=12)
    parser.add_argument("--seeds", type=int, nargs="+", default=[12317, 12319, 12323])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.starts < 1 or not args.seeds:
        parser.error("--starts and --seeds must be nonempty")

    source_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    shortcut_failures = []
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            before = deepcopy(pair["input"])
            predicted = rival(pair["input"])
            if predicted != pair["output"]:
                shortcut_failures.append(
                    {
                        "rival": name,
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                    }
                )
            if pair["input"] != before:
                shortcut_failures.append(
                    {
                        "rival": name,
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "error": "mutated input",
                    }
                )

    ambiguities = []
    disagreements = {name: 0 for name in gen.LESSON_COMPETITORS}
    unique_inputs = set()
    windows = 0
    rotations = 0
    for difficulty in ("easy", "medium", "hard"):
        for seed in args.seeds:
            for start in range(args.starts):
                lesson = []
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    grid = gen.generate(seed, start + offset, difficulty=difficulty)
                    label = intended(grid)
                    unique_inputs.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
                    lesson.append({"input": grid, "output": label})
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        if rival(grid) != label:
                            disagreements[name] += 1
                windows += 1
                for query_index, query in enumerate(lesson):
                    demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                    rotations += 1
                    hook_reasons = gen.lesson_identifiable(demos, query)
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
                        changes_query = rival(query["input"]) != query["output"]
                        if fits and changes_query:
                            ambiguities.append(
                                {
                                    "difficulty": difficulty,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "rival": name,
                                    "hook_reasons": hook_reasons,
                                }
                            )
                    if hook_reasons and not any(
                        row["difficulty"] == difficulty
                        and row["seed"] == seed
                        and row["start"] == start
                        and row["query_index"] == query_index
                        for row in ambiguities
                    ):
                        ambiguities.append(
                            {
                                "difficulty": difficulty,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "rival": "hook_only",
                                "hook_reasons": hook_reasons,
                            }
                        )

    never_refuted = sorted(name for name, count in disagreements.items() if count == 0)
    report = {
        "schema": "341758fa9de1-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "difficulties": ["easy", "medium", "hard"],
        "seeds": args.seeds,
        "starts_per_seed_band": args.starts,
        "windows_checked": windows,
        "rotations_checked": rotations,
        "unique_inputs": len(unique_inputs),
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "canonical_shortcuts": sorted(gen.CANONICAL_SHORTCUTS),
        "canonical_shortcut_failures": shortcut_failures,
        "competitor_disagreements": disagreements,
        "competitors_never_refuted": never_refuted,
        "ambiguities": ambiguities,
        "status": (
            "PASS"
            if not shortcut_failures and not never_refuted and not ambiguities
            else "FAIL"
        ),
        "limitations": [
            "Uses an independent Python mirror, not Racket labels.",
            "Tests declared competitors only; undeclared rivals remain unknown.",
            "Finite seeds and starts do not prove universal identifiability.",
        ],
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
