#!/usr/bin/env python3
"""Source-bound curriculum probe for generator 28aab6c2d6e0.

The battery materializes only a small lesson sample.  This probe checks sliding
three-demo lessons at 100 starts per difficulty band, reports which declared
rivals survive, counts witness coverage, and records input uniqueness and the
exact sampler.  It intentionally uses the generator's pure-Python rule mirror;
Racket parity remains a separate focused test and battery obligation.

Run from any directory:

    python3 repo/generators/28aab6c2d6e0/workspace/semantic_probe.py \
        --out checks/semantic_probe_100.json
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


TASK_ID = "28aab6c2d6e0"
BANDS = ("easy", "medium", "hard")
SEED_BASE = 3_000_000
SEED_BAND_STRIDE = 100_000
LESSON_SAMPLE_STRIDE = 11


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "shared/runtime/puzzle_generators/base.py").is_file():
            return parent
    raise RuntimeError("could not locate repository root")


def _load_generator(repo: Path):
    runtime = repo / "shared/runtime"
    sys.path.insert(0, str(runtime))
    source = repo / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _canonical_pairs(repo: Path) -> list[dict[str, Any]]:
    path = repo / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [pair for split in ("train", "test") for pair in row[split]]
    raise RuntimeError("canonical task row missing")


def run_probe(lessons_per_band: int) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    repo = _repo_root()
    gen, source = _load_generator(repo)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    canonical_pairs = _canonical_pairs(repo)

    canonical_shortcut_fits = {}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        canonical_shortcut_fits[name] = sum(
            rival(pair["input"]) == pair["output"] for pair in canonical_pairs
        )

    per_band = {}
    total_survivors = Counter()
    total_witnesses = Counter()
    for band_index, band in enumerate(BANDS):
        unique_inputs = set()
        dimensions = Counter()
        object_counts = Counter()
        witness_counts = Counter()
        rival_disagreements = Counter()
        survivor_windows = Counter()
        strict_failures = []
        total_examples = 0

        for lesson_index in range(lessons_per_band):
            seed = SEED_BASE + band_index * SEED_BAND_STRIDE + lesson_index
            start = lesson_index * LESSON_SAMPLE_STRIDE
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": gen._canonical_rule(grid)}
                for grid in grids[:-1]
            ]
            query = {"input": grids[-1], "output": gen._canonical_rule(grids[-1])}
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                strict_failures.append(
                    {
                        "lesson_index": lesson_index,
                        "seed": seed,
                        "sample_index": start,
                        "reasons": reasons,
                    }
                )

            for name, rival in gen.LESSON_COMPETITORS.items():
                fits = all(rival(demo["input"]) == demo["output"] for demo in demos)
                if fits:
                    survivor_windows[name] += 1

            for grid in grids:
                total_examples += 1
                unique_inputs.add(_freeze(grid))
                facts = gen.semantic_observables(grid)
                dimensions[f"{facts['grid_h']}x{facts['grid_w']}"] += 1
                object_counts[str(facts["n_objects"])] += 1
                errors = gen.strict_canonical_like(grid)
                if errors:
                    strict_failures.append(
                        {
                            "lesson_index": lesson_index,
                            "seed": seed,
                            "sample_index": start,
                            "errors": errors,
                        }
                    )
                answer = gen._canonical_rule(grid)
                for name, witness in gen.SEMANTIC_WITNESSES.items():
                    if witness(grid):
                        witness_counts[name] += 1
                for name, rival in gen.SEMANTIC_RIVALS.items():
                    if rival(grid) != answer:
                        rival_disagreements[name] += 1

        total_survivors.update(survivor_windows)
        total_witnesses.update(witness_counts)
        per_band[band] = {
            "lessons": lessons_per_band,
            "examples": total_examples,
            "unique_inputs": len(unique_inputs),
            "strict_failures": strict_failures[:10],
            "strict_failure_count": len(strict_failures),
            "surviving_rival_windows": dict(sorted(survivor_windows.items())),
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
            "witness_counts": dict(sorted(witness_counts.items())),
            "dimensions": dict(sorted(dimensions.items())),
            "object_counts": dict(sorted(object_counts.items())),
        }

    return {
        "schema": "28aab6c2d6e0_semantic_probe/1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "examples_needed": gen.EXAMPLES_NEEDED,
        "oracle": "generator._canonical_rule (Racket parity tested separately)",
        "sampler": {
            "bands": list(BANDS),
            "lessons_per_band": lessons_per_band,
            "seed": "3000000 + band_index*100000 + lesson_index",
            "lesson_start_sample_index": "lesson_index * 11",
            "demos": "start..start+2",
            "query": "start+3",
            "difficulty": "band",
        },
        "declared_axis_domains": gen.AXES,
        "canonical_pairs": len(canonical_pairs),
        "canonical_shortcut_fits": canonical_shortcut_fits,
        "per_band": per_band,
        "pooled_surviving_rival_windows": dict(sorted(total_survivors.items())),
        "pooled_witness_counts": dict(sorted(total_witnesses.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run_probe(args.lessons_per_band)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    failed = any(
        row["strict_failure_count"] or row["surviving_rival_windows"]
        for row in result["per_band"].values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
