#!/usr/bin/env python3
"""Bounded authoring audit for the 7f666a786bf3 parametric family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("audit_adapter_7f666a786bf3", HERE / "adapter.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ADAPTER)


def audit(seeds: list[int]) -> dict[str, object]:
    jobs = 0
    pairs = 0
    stress = 0
    prefix_checks = 0
    matched_input_checks = 0
    rival_survivors: dict[str, int] = {name: 0 for name in ADAPTER.HYPOTHESES}
    first_query_source_positions: set[int] = set()
    for seed in seeds:
        canonical_bank = ADAPTER.generate(seed, {"finish": "fill_only"}, 6, 4)
        alternate_bank = ADAPTER.generate(seed, {"finish": "highlight_largest_filled"}, 6, 4)
        for left, right in zip(canonical_bank["train"] + canonical_bank["test"], alternate_bank["train"] + alternate_bank["test"]):
            assert left["input"] == right["input"]
            matched_input_checks += 1
        # Compare the first public query to the four unshuffled source profiles.
        raw = [ADAPTER._scene(seed, "query", index) for index in range(4)]
        first = canonical_bank["test"][0]["input"]
        first_query_source_positions.add(next(index for index, value in enumerate(raw) if value == first))
        for demos in (2, 3, 6):
            for finish in ADAPTER.SETTINGS:
                jobs += 1
                episode = ADAPTER.generate(seed, {"finish": finish}, demos, 4)
                pairs += len(episode["train"]) + len(episode["test"])
                cert = ADAPTER.certificate(episode["train"], [pair["input"] for pair in episode["test"]])
                assert cert["survivors"] == [finish]
                for hypothesis in ADAPTER.HYPOTHESES:
                    if hypothesis in cert["survivors"]:
                        rival_survivors[hypothesis] += 1
                assert set(cert["query_disagreements"]) == set(ADAPTER.HYPOTHESES) - {finish}
                stress_pairs = [pair for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30]
                assert len(stress_pairs) == 1
                stress += 1
                small = ADAPTER.generate(seed, {"finish": finish}, 2, 1)
                assert small["train"] == episode["train"][:2]
                assert small["test"] == episode["test"][:1]
                prefix_checks += 2
    assert first_query_source_positions != {0}, "query profile zero is always first"
    return {
        "schema": "arcpuzzles-parametric-authoring-audit-v1",
        "task_id": ADAPTER.TASK_ID,
        "status": "passed",
        "seeds": seeds,
        "settings": list(ADAPTER.SETTINGS),
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "jobs": jobs,
        "pairs": pairs,
        "stress_30x30_jobs": stress,
        "prefix_checks": prefix_checks,
        "matched_input_checks": matched_input_checks,
        "first_query_source_positions": sorted(first_query_source_positions),
        "declared_hypotheses": list(ADAPTER.HYPOTHESES),
        "survivor_counts": rival_survivors,
        "limits": "Finite deterministic seeds and declared rivals only; not universal identifiability or measured learning gain.",
        "training_admitted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="*", default=[0, 17, 97])
    args = parser.parse_args()
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
