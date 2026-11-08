#!/usr/bin/env python3
"""Source-bound 100-lesson rival-survival probe for task 892ae3bfe537.

The probe intentionally uses the generator's declared LESSON_COMPETITORS rather
than a copied rival list.  It assembles 100 overlapping, cyclic-start lessons per
band from 102 deterministic generated inputs.  Each lesson has two demos and one
query, matching EXAMPLES_NEEDED=2.  Outputs come from the task's independent
Python bbox-fill oracle; the normal semantic/rule-smoke gates separately bind that
oracle and generator domain to the selected Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK = "892ae3bfe537"
BANDS = ("easy", "medium", "hard")
LESSONS_PER_BAND = 100


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"probe_{TASK}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probe_band(gen: Any, band: str, seed: int) -> dict[str, Any]:
    # 102 samples support 100 consecutive 2-demo + 1-query windows.
    samples = [gen.generate(seed, index, difficulty=band) for index in range(102)]
    outputs = [gen._fill_pairs(grid) for grid in samples]
    unique_inputs = len({freeze(grid) for grid in samples})
    unique_outputs = len({freeze(grid) for grid in outputs})

    rival_disagreements = {name: 0 for name in gen.LESSON_COMPETITORS}
    for grid, expected in zip(samples, outputs):
        for name, rival in gen.LESSON_COMPETITORS.items():
            if rival(grid) != expected:
                rival_disagreements[name] += 1

    survivor_histogram: dict[str, int] = {}
    failed_lessons: list[dict[str, Any]] = []
    for start in range(LESSONS_PER_BAND):
        demos = [
            {"input": samples[start], "output": outputs[start]},
            {"input": samples[start + 1], "output": outputs[start + 1]},
        ]
        query = samples[start + 2]
        errors = gen.lesson_identifiable(demos, query)
        key = "none" if not errors else " | ".join(errors)
        survivor_histogram[key] = survivor_histogram.get(key, 0) + 1
        if errors:
            failed_lessons.append({"start": start, "errors": errors})

    return {
        "band": band,
        "seed": seed,
        "lesson_count": LESSONS_PER_BAND,
        "demo_count_per_lesson": 2,
        "query_count_per_lesson": 1,
        "base_samples": len(samples),
        "windows_overlap": True,
        "unique_inputs": unique_inputs,
        "unique_outputs": unique_outputs,
        "rival_disagreements_over_base_samples": rival_disagreements,
        "survivor_histogram": survivor_histogram,
        "failed_lessons": failed_lessons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    gen = load_generator(generator_path)
    bands = [probe_band(gen, band, seed=7300 + i * 1000) for i, band in enumerate(BANDS)]
    result = {
        "schema": "task-local-lesson-probe-v1",
        "task_id": TASK,
        "generator_sha256": sha256(generator_path),
        "probe_sha256": sha256(Path(__file__)),
        "oracle": "generator._fill_pairs (independent Python bbox-fill oracle)",
        "competitors": sorted(gen.LESSON_COMPETITORS),
        "sampler": {
            "bands": list(BANDS),
            "sample_indices": "0..101 per band",
            "lesson_starts": "0..99 per band",
            "assembly": "two consecutive demos plus the following query",
        },
        "bands": bands,
        "passed": all(not band["failed_lessons"] for band in bands),
        "domain_limit": (
            "This proves declared-rival separation for these deterministic generated "
            "lessons only; it is not a universal induction claim."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "passed": result["passed"],
        "generator_sha256": result["generator_sha256"],
        "bands": [
            {
                "band": b["band"],
                "lessons": b["lesson_count"],
                "unique_inputs": b["unique_inputs"],
                "survivors": len(b["failed_lessons"]),
                "rival_disagreements": b["rival_disagreements_over_base_samples"],
            }
            for b in bands
        ],
    }, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
