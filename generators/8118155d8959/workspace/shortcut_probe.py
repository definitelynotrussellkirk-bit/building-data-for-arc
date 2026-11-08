#!/usr/bin/env python3
"""Source-bound shortcut and lesson-window census for task 8118155d8959.

The probe answers three maintenance questions in one reproducible JSON report:

1. Which declared wrong rules fit every canonical input/output pair?
2. How often does the current generated distribution refute each rival?
3. Does every sampled three-demonstration lesson refute every declared rival?

It intentionally uses the checked-in Python mirror for high-volume generated
census work.  For acceptance evidence, feed a saved counterexample input to the
supported ``arcpuzzles apply`` command so the selected Racket authority supplies
the official output.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "8118155d8959"
HERE = Path(__file__).resolve()
REPO = next((p for p in HERE.parents if (p / "shared/runtime").is_dir()), None)
if REPO is None:
    raise RuntimeError("could not locate repository root from shortcut_probe.py")
if str(REPO / "shared/runtime") not in sys.path:
    sys.path.insert(0, str(REPO / "shared/runtime"))

GENERATOR_PATH = REPO / f"generators/{TASK_ID}/generator.py"
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"shortcut_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _normalize_grid(value: Any) -> list[list[int]]:
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return copy.deepcopy(value)


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            raw_test = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [
                {
                    "input": _normalize_grid(pair["input"]),
                    "output": _normalize_grid(pair["output"]),
                }
                for pair in [*row["train"], *raw_test]
            ]
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _source_sha256() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def build_report(*, per_band: int = 100, lesson_starts: int = 100) -> dict[str, Any]:
    if per_band < 1 or lesson_starts < 1:
        raise ValueError("per_band and lesson_starts must both be positive")

    pairs = _canonical_pairs()
    report: dict[str, Any] = {
        "schema": "8118155d8959-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _source_sha256(),
        "rule_hash": gen.RULE_HASH,
        "canonical_pairs": len(pairs),
        "canonical_shortcuts": {},
        "generated_draws_per_band": per_band * 3,
        "generated_draws_total": per_band * 3 * 3,
        "generated_rival_disagreements": {
            name: 0 for name in gen.SEMANTIC_RIVALS
        },
        "first_generated_counterexample": {
            name: None for name in gen.SEMANTIC_RIVALS
        },
        "lesson_windows": {
            "examples_per_lesson": gen.EXAMPLES_NEEDED,
            "starts_per_band": lesson_starts,
            "windows_total": lesson_starts * 3,
            "unrefuted": [],
            "refuted_counts": {name: 0 for name in gen.LESSON_COMPETITORS},
        },
    }

    for name, shortcut in sorted(gen.CANONICAL_SHORTCUTS.items()):
        fits = 0
        errors: list[str] = []
        for index, pair in enumerate(pairs):
            try:
                predicted = shortcut(pair["input"])
            except Exception as exc:  # fail loud in the report
                errors.append(f"pair {index}: {type(exc).__name__}: {exc}")
                continue
            fits += predicted == pair["output"]
        report["canonical_shortcuts"][name] = {
            "pairs": len(pairs),
            "fits": fits,
            "fits_all": fits == len(pairs) and not errors,
            "errors": errors,
        }

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed_index in range(per_band):
            seed = 100_003 * (band_index + 1) + seed_index
            for residue in range(3):
                sample_index = seed_index * 3 + residue
                grid = gen.generate(seed, sample_index, difficulty=band)
                intended = gen.rule_mirror(grid)
                for name, rival in gen.SEMANTIC_RIVALS.items():
                    rival_output = rival(grid)
                    if rival_output == intended:
                        continue
                    report["generated_rival_disagreements"][name] += 1
                    if report["first_generated_counterexample"][name] is None:
                        report["first_generated_counterexample"][name] = {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "schedule_profile": gen.schedule_profile(
                                seed, sample_index, difficulty=band
                            ),
                            "scene_profile": gen.observe_overrides(grid)[
                                "scene_profile"
                            ],
                            "input": grid,
                            "intended_output_python_mirror": intended,
                            "rival_output": rival_output,
                        }

    lesson_stats = report["lesson_windows"]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(lesson_starts):
            seed = 700_001 + band_index * 10_000 + start
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            for name, rival in gen.LESSON_COMPETITORS.items():
                refuted = any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                )
                if refuted:
                    lesson_stats["refuted_counts"][name] += 1
                else:
                    lesson_stats["unrefuted"].append(
                        {
                            "band": band,
                            "seed": seed,
                            "start_sample_index": start,
                            "rival": name,
                        }
                    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(
        per_band=args.per_band,
        lesson_starts=args.lesson_starts,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(text, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
