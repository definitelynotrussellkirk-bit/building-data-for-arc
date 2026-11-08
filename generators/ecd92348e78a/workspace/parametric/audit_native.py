#!/usr/bin/env python3
"""Bounded deterministic self-audit for the native ecd92348e78a family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _digest(value) -> str:
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()


def audit(seed_count: int) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 64:
        raise ValueError("seed_count must be in 1..64")
    adapter = _load(HERE / "adapter.py", "ecd92348e78a_audit_adapter")
    family = _load(HERE / "native_family.py", "ecd92348e78a_audit_family")
    settings = list(family.SETTINGS)

    episodes = 0
    pairs = 0
    stress_cases = 0
    query_bank_stability_checks = 0
    minimum_teaching_checks = 0
    public_input_hashes = set()
    dimensions = []
    failures = []

    for seed in range(seed_count):
        for selected in settings:
            expected_query_digest = None
            for demos in range(2, 7):
                episodes += 1
                try:
                    episode = adapter.generate(seed, selected, demos=demos, queries=4)
                    pairs += demos + 4
                    query_digest = _digest(episode["test"])
                    if expected_query_digest is None:
                        expected_query_digest = query_digest
                    elif query_digest != expected_query_digest:
                        raise AssertionError("query bank changed with demo count")
                    query_bank_stability_checks += 1

                    inputs = [
                        pair["input"]
                        for split in ("train", "test")
                        for pair in episode[split]
                    ]
                    hashes = [_digest(grid) for grid in inputs]
                    if len(hashes) != len(set(hashes)):
                        raise AssertionError("duplicate input inside episode")
                    public_input_hashes.update(hashes)
                    dimensions.extend((len(grid), len(grid[0])) for grid in inputs)

                    survivors = []
                    for candidate in settings:
                        if all(
                            family.solve_variant(
                                pair["input"],
                                candidate["sort_order"],
                                candidate["bar_alignment"],
                            )
                            == pair["output"]
                            for pair in episode["train"]
                        ):
                            survivors.append(candidate)
                    if survivors != [selected]:
                        raise AssertionError(f"teaching survivors={survivors!r}")
                    if demos == 2:
                        minimum_teaching_checks += 1

                    for split in ("train", "test"):
                        for pair in episode[split]:
                            expected = family.solve_variant(
                                pair["input"],
                                selected["sort_order"],
                                selected["bar_alignment"],
                            )
                            if pair["output"] != expected:
                                raise AssertionError("Python label mismatch")

                    stress = [
                        pair
                        for pair in episode["test"]
                        if len(pair["input"]) == 30 and len(pair["input"][0]) == 30
                    ]
                    if len(stress) != 1:
                        raise AssertionError("expected exactly one 30x30 stress query")
                    if sum(cell != 0 for row in stress[0]["input"] for cell in row) < 250:
                        raise AssertionError("30x30 stress content is too sparse")
                    stress_cases += 1
                except Exception as exc:  # retain every bounded failure in one result
                    failures.append(
                        {
                            "seed": seed,
                            "settings": selected,
                            "demos": demos,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    return {
        "schema": "arcpuzzles-ecd92348e78a-native-self-audit-v1",
        "status": "passed" if not failures else "failed",
        "task_id": "ecd92348e78a",
        "seed_count": seed_count,
        "settings": settings,
        "demo_counts": [2, 3, 4, 5, 6],
        "queries_per_episode": 4,
        "episodes": episodes,
        "labeled_pairs": pairs,
        "minimum_teaching_checks": minimum_teaching_checks,
        "query_bank_stability_checks": query_bank_stability_checks,
        "stress_30x30_cases": stress_cases,
        "unique_input_grids": len(public_input_hashes),
        "input_dimension_min": [min(h for h, _ in dimensions), min(w for _, w in dimensions)],
        "input_dimension_max": [max(h for h, _ in dimensions), max(w for _, w in dimensions)],
        "sequential_dependency": {
            "step_a": "measure bbox row heights and sort (height,color) records",
            "intermediate": "ordered list of (height,color) records",
            "step_b": "render top- or bottom-aligned bars from that ordered list",
            "wrong_intermediate_probe": "opposite sort order changes at least one query for every audited episode",
        },
        "failures": failures,
        "limits": "Finite 0..seed_count-1 audit over declared settings/counts; not universal uniqueness proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-count", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.seed_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "episodes", "labeled_pairs", "stress_30x30_cases", "unique_input_grids")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
