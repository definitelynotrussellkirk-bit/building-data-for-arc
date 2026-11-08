#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
SOURCE = REPO / "generators" / "66387591ebe6" / "generator.py"
EXPECTED_SOURCE_SHA = "3edd9feed4e95fc26d54952b74fe8fb1dd435849ced16a744833b70fbe9991a7"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_66387591ebe6", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid: list[list[int]]) -> str:
    return sha256_bytes(json.dumps(grid, separators=(",", ":")).encode())


def main() -> None:
    source_sha = sha256_bytes(SOURCE.read_bytes())
    if source_sha != EXPECTED_SOURCE_SHA:
        raise SystemExit(f"source hash mismatch: {source_sha}")
    gen = load_module(SOURCE)

    counts: Counter[str] = Counter()
    rival_matches = 0
    draws = 0
    unique_inputs: set[str] = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(100):
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=band)
                key = gen.observe_overrides(grid)["key"]
                counts[f"{band}:key_{key}"] += 1
                counts[f"key_{key}"] += 1
                draws += 1
                unique_inputs.add(grid_hash(grid))
                if gen.EXTRAPOLATION_RIVALS["keys_2_to_4_only"](grid) == gen.rule_mirror(grid):
                    rival_matches += 1

    witness = gen.generate(
        0,
        0,
        difficulty="medium",
        key=1,
        grid_h=9,
        grid_w=11,
        n_cells=4,
        pivot_region="southeast",
        texture="multicolor",
    )
    errors = gen.self_check(witness, difficulty="medium")
    intended = gen.rule_mirror(witness)
    rival = gen.EXTRAPOLATION_RIVALS["keys_2_to_4_only"](witness)
    observed = gen.observe_overrides(witness)
    (HERE / "input.json").write_text(json.dumps(witness, indent=2) + "\n")
    (HERE / "python_intended.json").write_text(json.dumps(intended, indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps(rival, indent=2) + "\n")
    partial = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": "66387591ebe6",
        "finding_kind": "domain_question",
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "rule_hash": gen.RULE_HASH,
        "ordinary_sampler_probe": {
            "bands": ["easy", "medium", "hard"],
            "seed_range_each_band": [0, 99],
            "sample_indices_each_seed": [0, 1, 2, 3],
            "draws": draws,
            "unique_inputs": len(unique_inputs),
            "key_counts": dict(sorted(counts.items())),
            "key_1_draws": counts.get("key_1", 0),
            "keys_2_to_4_only_rival_matches": rival_matches,
        },
        "counterexample": {
            "seed": 0,
            "sample_index": 0,
            "difficulty": "medium",
            "overrides": {
                "key": 1,
                "grid_h": 9,
                "grid_w": 11,
                "n_cells": 4,
                "pivot_region": "southeast",
                "texture": "multicolor"
            },
            "observed": observed,
            "self_check_errors": errors,
            "input_path": "checks/audit/66387591ebe6/input.json",
            "python_intended_path": "checks/audit/66387591ebe6/python_intended.json",
            "rival_path": "checks/audit/66387591ebe6/rival.json",
            "input_sha256": grid_hash(witness),
            "python_intended_sha256": grid_hash(intended),
            "rival_sha256": grid_hash(rival),
            "intended_differs_from_rival": intended != rival,
            "documented_generated_domain": "lawful exact-override branch; excluded from ordinary production sampler",
        },
        "verdict": "The ordinary sampler never teaches key 1, so a solver that handles only keys 2..4 fits every ordinary draw. The exact key=1 override is a lawful identity witness and refutes it.",
    }
    (HERE / "report.partial.json").write_text(json.dumps(partial, indent=2, sort_keys=True) + "\n")
    if errors or counts.get("key_1", 0) != 0 or rival_matches != draws or intended == rival:
        raise SystemExit(1)
    print(json.dumps({
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "key_counts": {str(k): v for k, v in sorted((int(k.split('_')[1]), v) for k, v in counts.items() if k.startswith('key_'))},
        "rival_matches": rival_matches,
        "witness_valid": not errors,
        "witness_differs": intended != rival,
    }, indent=2))


if __name__ == "__main__":
    main()
