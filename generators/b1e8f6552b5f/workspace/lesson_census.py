#!/usr/bin/env python3
"""Census four-demo lesson identifiability across bands and cyclic starts.

The probe checks both ordinary generation and semantically compatible exact
size overrides.  It uses the generator's declared competitors and witnesses,
so declarations cannot silently drift from the review tool.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GENERATOR_PATH = TASK_DIR / "generator.py"


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR_PATH)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    generator_path = args.generator.resolve()
    gen = _load_generator(generator_path)
    bands = ("easy", "medium", "hard")
    profile_sizes = {
        "aligned_same_pair": (8, 10),
        "canonical_distinct_pair": (10, 11),
        "mixed_triple": (12, 13),
        "distinct_quad": (12, 12),
    }
    modes = ("ordinary", "compatible_dimensions")
    rows: list[dict[str, Any]] = []
    failure_examples: list[dict[str, Any]] = []

    for band in bands:
        for mode in modes:
            rival_fit_counts = {name: 0 for name in gen.LESSON_COMPETITORS}
            witness_lesson_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
            unique_inputs: set[str] = set()
            lessons = 0
            for seed in range(args.seeds):
                for cyclic_start in range(4):
                    demos = []
                    for offset in range(4):
                        sample_index = cyclic_start + offset
                        profile = gen.schedule_profile(seed, sample_index, band)
                        overrides: dict[str, int] = {}
                        if mode == "compatible_dimensions":
                            h, w = profile_sizes[profile]
                            overrides = {"grid_h": h, "grid_w": w}
                        grid = gen.generate(
                            seed,
                            sample_index,
                            difficulty=band,
                            **overrides,
                        )
                        unique_inputs.add(json.dumps(grid, separators=(",", ":")))
                        demos.append({"input": grid, "output": gen._stamp_prediction(grid)})
                    lessons += 1
                    for name, rival in gen.LESSON_COMPETITORS.items():
                        if all(rival(pair["input"]) == pair["output"] for pair in demos):
                            rival_fit_counts[name] += 1
                            if len(failure_examples) < 25:
                                failure_examples.append(
                                    {
                                        "difficulty": band,
                                        "mode": mode,
                                        "seed": seed,
                                        "cyclic_start": cyclic_start,
                                        "rival": name,
                                    }
                                )
                    for name, witness in gen.SEMANTIC_WITNESSES.items():
                        if any(witness(pair["input"]) for pair in demos):
                            witness_lesson_counts[name] += 1
            rows.append(
                {
                    "difficulty": band,
                    "mode": mode,
                    "seed_range": [0, args.seeds - 1],
                    "cyclic_starts": [0, 1, 2, 3],
                    "lessons": lessons,
                    "demo_draws": lessons * 4,
                    "unique_inputs": len(unique_inputs),
                    "rival_fit_counts": rival_fit_counts,
                    "witness_lesson_counts": witness_lesson_counts,
                }
            )

    total_rival_fits = sum(
        sum(row["rival_fit_counts"].values()) for row in rows
    )
    result = {
        "schema": "b1e8f6552b5f-lesson-census-v1",
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "lesson_policy": "four consecutive sample indices; all four cyclic starts",
        "modes": {
            "ordinary": "no exact overrides",
            "compatible_dimensions": profile_sizes,
        },
        "total_lessons": sum(row["lessons"] for row in rows),
        "total_demo_draws": sum(row["demo_draws"] for row in rows),
        "total_rival_fits": total_rival_fits,
        "rows": rows,
        "failure_examples": failure_examples,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if total_rival_fits == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
