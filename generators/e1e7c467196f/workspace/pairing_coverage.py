#!/usr/bin/env python3
"""Measure source→target rank-pairing coverage for e1e7c467196f.

The ordinary morphology/diversity checks do not distinguish different legend
bijections.  This probe reports the exact permutation signatures generated for
K=2..4 and whether the canonical signatures are represented.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from math import factorial
from pathlib import Path
import sys
from typing import Any

TASK_ID = "e1e7c467196f"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
DEFAULT_GENERATOR = HERE.parent.parent / "generator.py"
DEFAULT_CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
sys.path.insert(0, str(REPO / "shared/runtime"))


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"pairing_probe_{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _signature(grid: list[list[int]]) -> tuple[int, ...]:
    sources = [value for value in grid[0] if value != 0]
    targets = [value for value in grid[1] if value != 0]
    mapping = dict(zip(sources, targets))
    target_rank = {value: index for index, value in enumerate(sorted(targets))}
    return tuple(target_rank[mapping[source]] for source in sorted(sources))


def _canonical_signatures(path: Path) -> dict[str, list[int]]:
    with path.open() as handle:
        record = next(
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == TASK_ID
        )
    pairs = [*record.get("train", []), record["test"]]
    labels = [*(f"train_{index}" for index in range(len(pairs) - 1)), "test"]
    return {
        label: list(_signature(pair["input"]))
        for label, pair in zip(labels, pairs)
    }


def _serialize_counter(counter: Counter[tuple[int, ...]]) -> dict[str, int]:
    return {
        ",".join(map(str, signature)): count
        for signature, count in sorted(counter.items())
    }


def measure(
    generator_path: Path,
    canonical_path: Path,
    *,
    seeds: int,
    sample_indices: int,
) -> dict[str, Any]:
    generator = _load_generator(generator_path)
    canonical = _canonical_signatures(canonical_path)
    bands: dict[str, Any] = {}
    for difficulty in ("easy", "medium", "hard"):
        by_k: dict[int, Counter[tuple[int, ...]]] = {
            2: Counter(),
            3: Counter(),
            4: Counter(),
        }
        for seed in range(seeds):
            for sample_index in range(sample_indices):
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                signature = _signature(grid)
                by_k[len(signature)][signature] += 1

        band: dict[str, Any] = {}
        for k, counter in by_k.items():
            possible = set(itertools.permutations(range(k)))
            observed = set(counter)
            band[str(k)] = {
                "draws": sum(counter.values()),
                "unique_signatures": len(observed),
                "possible_signatures": factorial(k),
                "coverage_fraction": len(observed) / factorial(k),
                "counts": _serialize_counter(counter),
                "missing": [list(item) for item in sorted(possible - observed)],
            }
        canonical_present = {
            label: tuple(signature) in by_k[len(signature)]
            for label, signature in canonical.items()
        }
        band["canonical_present"] = canonical_present
        bands[difficulty] = band

    source = generator_path.read_bytes()
    return {
        "schema": "e1e7c467196f-pairing-coverage/1",
        "task_id": TASK_ID,
        "generator": str(generator_path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "generator_version": getattr(generator, "VERSION", None),
        "seeds": seeds,
        "sample_indices": sample_indices,
        "canonical_signatures": canonical,
        "bands": bands,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--seeds", type=int, default=256)
    parser.add_argument("--sample-indices", type=int, default=12)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = measure(
        args.generator.resolve(),
        args.canonical.resolve(),
        seeds=args.seeds,
        sample_indices=args.sample_indices,
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
