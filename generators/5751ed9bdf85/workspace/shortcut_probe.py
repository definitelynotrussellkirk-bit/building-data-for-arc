#!/usr/bin/env python3
"""Source-bound probe for canonical-fitting shortcuts in task 5751ed9bdf85.

This is a reviewer tool, not label authority.  It proves two bounded facts:
(1) the named odd-marker rival agrees with every retained canonical pair, and
(2) the selected generator emits three-marker decoys on which that rival and
    the intended exactly-one-marker rule disagree.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

TASK_ID = "5751ed9bdf85"
DEFAULT_SAMPLES = 100
BANDS = ("easy", "medium", "hard")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _load_generator(path: Path, repo_root: Path):
    runtime = repo_root / "shared" / "runtime"
    import sys

    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _grid_hash(grid: Any) -> str:
    return _sha256_bytes(_stable_json(grid))


def run_probe(generator_path: Path, canonical_path: Path, samples: int) -> dict[str, Any]:
    repo_root = generator_path.resolve().parents[2]
    module = _load_generator(generator_path, repo_root)
    canonical = _canonical_row(canonical_path)
    rival = module.CANONICAL_SHORTCUTS["odd_marker_count"]

    canonical_pairs = list(canonical["train"]) + list(canonical["test"])
    canonical_checks = []
    for index, pair in enumerate(canonical_pairs):
        actual = rival(pair["input"])
        canonical_checks.append(
            {
                "pair_index": index,
                "input_sha256": _grid_hash(pair["input"]),
                "matches_canonical_output": actual == pair["output"],
                "marker_counts": sorted(
                    frame["marker_count"]
                    for frame in module._analyze_scene(pair["input"])["frames"]
                ),
            }
        )

    per_band: dict[str, Any] = {}
    first_witness: dict[str, Any] | None = None
    for band_index, band in enumerate(BANDS):
        unique_inputs: set[str] = set()
        marker_counts: Counter[int] = Counter()
        disagreements = 0
        semantic_witnesses = 0
        for sample_index in range(samples):
            seed = 91_000 + band_index * 1_000 + sample_index
            grid = module.generate(seed, sample_index, difficulty=band)
            unique_inputs.add(_grid_hash(grid))
            observed = module.observe_overrides(grid)
            decoy_count = int(observed["decoy_marker_count"])
            marker_counts[decoy_count] += 1
            expected = module.rule_mirror(grid)
            rival_output = rival(grid)
            disagrees = rival_output != expected
            disagreements += int(disagrees)
            witness = module.SEMANTIC_WITNESSES[
                "three_marker_decoy_refutes_odd_count"
            ](grid)
            semantic_witnesses += int(witness)
            if disagrees and first_witness is None:
                first_witness = {
                    "difficulty": band,
                    "seed": seed,
                    "sample_index": sample_index,
                    "observed_axes": observed,
                    "input": grid,
                    "intended_output": expected,
                    "odd_marker_rival_output": rival_output,
                    "input_sha256": _grid_hash(grid),
                    "intended_output_sha256": _grid_hash(expected),
                    "rival_output_sha256": _grid_hash(rival_output),
                }
        per_band[band] = {
            "samples": samples,
            "unique_inputs": len(unique_inputs),
            "duplicate_inputs": samples - len(unique_inputs),
            "decoy_marker_count_histogram": {
                str(key): marker_counts[key] for key in sorted(marker_counts)
            },
            "odd_rival_disagreements": disagreements,
            "semantic_witnesses": semantic_witnesses,
        }

    failures: list[str] = []
    if not all(item["matches_canonical_output"] for item in canonical_checks):
        failures.append("odd-marker rival did not fit every canonical pair")
    for band, facts in per_band.items():
        if facts["odd_rival_disagreements"] == 0:
            failures.append(f"{band}: generator emitted no odd-rival counterexample")
        if facts["semantic_witnesses"] == 0:
            failures.append(f"{band}: semantic witness never fired")
        if "3" not in facts["decoy_marker_count_histogram"]:
            failures.append(f"{band}: no three-marker decoy was sampled")

    return {
        "schema": "arc-task-shortcut-probe-v1",
        "task_id": TASK_ID,
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256_bytes(generator_path.read_bytes()),
        "generator_version": module.VERSION,
        "rule_hash": module.RULE_HASH,
        "canonical_path": str(canonical_path),
        "canonical_row_sha256": _sha256_bytes(_stable_json(canonical)),
        "rival": "fill every frame whose marker-cell count is odd",
        "intended_rule": "fill only the unique frame containing exactly one marker cell",
        "canonical_checks": canonical_checks,
        "sampler": {
            "samples_per_band": samples,
            "bands": list(BANDS),
            "seed_formula": "91000 + 1000*band_index + sample_index",
            "sample_index_range": [0, samples - 1],
        },
        "per_band": per_band,
        "first_disagreement": first_witness,
        "domain_limits": (
            "The generated census covers the selected generator's three-frame teaching "
            "manifold and the retained canonical pairs. It does not prove identifiability "
            "for arbitrary authority-valid frame arrangements."
        ),
    }


def main() -> int:
    here = Path(__file__).resolve()
    task_root = here.parents[1]
    repo_root = here.parents[3]
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=task_root / "generator.py")
    parser.add_argument(
        "--canonical",
        type=Path,
        default=repo_root / "shared" / "data" / "canonical" / "puzzles.jsonl",
    )
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be positive")

    report = run_probe(args.generator.resolve(), args.canonical.resolve(), args.samples)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "generator_sha256": report["generator_sha256"],
                "canonical_pairs": len(report["canonical_checks"]),
                "per_band": report["per_band"],
                "out": str(args.out) if args.out else None,
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
