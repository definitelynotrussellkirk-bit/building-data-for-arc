#!/usr/bin/env python3
"""Exhaustively rotate queries across deterministic four-sample lesson windows.

This is a source-bound regression probe for c7c9b61d5a51.  It loads the selected
``generator.py`` directly, iterates the generator's *actual*
``LESSON_COMPETITORS`` declaration, and checks every three-demo subset of each
four-sample window.  The shared lesson census samples the production assembler;
this complementary probe cheaply covers every schedule residue many times.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("lesson_window_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--task", default="c7c9b61d5a51")
    parser.add_argument("--starts-per-band", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    generator_path = repo / "generators" / args.task / "generator.py"
    gen = _load(generator_path)
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    if not competitors:
        raise RuntimeError("generator declares no LESSON_COMPETITORS")

    bands = ("easy", "medium", "hard")
    survivor_counts = {name: 0 for name in competitors}
    teaching_defects = {name: 0 for name in competitors}
    profile_counts: Counter[str] = Counter()
    blocker_pattern_counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    hook_failures = 0
    generation_failures = 0
    examples: list[dict[str, Any]] = []
    rotations = 0
    draws = 0

    for band_index, band in enumerate(bands):
        for start in range(args.starts_per_band):
            # Vary both seed and start while preserving the four consecutive
            # sample indices that define the production curriculum cycle.
            seed = 910_000 + 10_000 * band_index + start
            pairs = []
            try:
                for offset in range(gen.EXAMPLES_NEEDED + 1):
                    sample_index = start + offset
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    truth = gen.rule_mirror(grid)
                    pairs.append({"input": grid, "output": truth})
                    draws += 1
                    unique_inputs.add(_grid_hash(grid))
                    profile_counts[str(gen.schedule_profile(seed, sample_index, band))] += 1
                    observables = gen.semantic_observables(grid)
                    blocker_pattern_counts[str(observables["blocker_pattern"])] += 1
            except Exception as exc:  # retained evidence, never silently skipped
                generation_failures += 1
                if len(examples) < 8:
                    examples.append(
                        {
                            "kind": "generation_failure",
                            "band": band,
                            "seed": seed,
                            "start": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                continue

            for query_index, query in enumerate(pairs):
                rotations += 1
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    hook_failures += 1
                    if len(examples) < 8:
                        examples.append(
                            {
                                "kind": "lesson_hook_failure",
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "query_index": query_index,
                                "reasons": reasons,
                            }
                        )

                for name, competitor in competitors.items():
                    if not all(
                        competitor(demo["input"]) == demo["output"] for demo in demos
                    ):
                        continue
                    survivor_counts[name] += 1
                    rival_query = competitor(query["input"])
                    if rival_query != query["output"]:
                        teaching_defects[name] += 1
                        if len(examples) < 8:
                            examples.append(
                                {
                                    "kind": "surviving_query_disagreement",
                                    "competitor": name,
                                    "band": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_index": query_index,
                                    "demo_inputs": [demo["input"] for demo in demos],
                                    "query_input": query["input"],
                                    "truth": query["output"],
                                    "rival": rival_query,
                                }
                            )

    result = {
        "schema": "c7c9b61d5a51-lesson-window-probe-v1",
        "task_id": args.task,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "assembly": {
            "bands": list(bands),
            "starts_per_band": args.starts_per_band,
            "pairs_per_window": gen.EXAMPLES_NEEDED + 1,
            "query_policy": "hold out each pair once; remaining three are demos",
            "seed_formula": "910000 + 10000*band_index + start",
            "sample_indices": "start..start+3",
        },
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "rotations": rotations,
        "generation_failures": generation_failures,
        "lesson_hook_failures": hook_failures,
        "competitors": sorted(competitors),
        "competitor_demo_survivals": survivor_counts,
        "competitor_query_disagreements": teaching_defects,
        "schedule_profile_counts": dict(sorted(profile_counts.items())),
        "blocker_pattern_counts": dict(sorted(blocker_pattern_counts.items())),
        "examples": examples,
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")

    failed = generation_failures or hook_failures or any(teaching_defects.values())
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
