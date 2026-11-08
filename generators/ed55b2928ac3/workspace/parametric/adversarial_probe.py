#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import prototype


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for seed in (0, 17, 43):
        for demos in range(2, 7):
            episodes = {mode: prototype.generate_claims(seed, mode, demos=demos, queries=4) for mode in prototype.MODES}
            inputs = {mode: [p["input"] for p in e["train"] + e["test"]] for mode, e in episodes.items()}
            assert inputs["plain"] == inputs["top_edge_to_8"]
            packed = [json.dumps(g, separators=(",", ":")) for g in inputs["plain"]]
            assert len(packed) == len(set(packed))
            assert all(
                prototype.python_mirror(pair["input"], "top_edge_to_8") != prototype.python_wrong_order(pair["input"])
                for pair in episodes["top_edge_to_8"]["train"] + episodes["top_edge_to_8"]["test"]
            )
            stress = inputs["plain"][-1]
            assert (len(stress), len(stress[0])) == (30, 30)
            rows.append({"seed": seed, "demos": demos, "queries": 4, "distinct_inputs": len(packed), "wrong_order_diverged": True})
    value = {
        "schema": "arcpuzzles-parametric-adversarial-self-review-v1",
        "task_id": prototype.TASK_ID,
        "status": "passed",
        "checks": rows,
        "program_sha256": {mode: hashlib.sha256(prototype.program_for(mode).encode()).hexdigest() for mode in prototype.MODES},
        "limits": "Finite Python mirror and sampler checks; protected Racket replay is recorded separately by authoring preflight and witness evidence."
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "passed", "cases": len(rows), "out": str(args.out)}))


if __name__ == "__main__":
    main()
