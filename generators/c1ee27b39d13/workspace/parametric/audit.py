#!/usr/bin/env python3
"""Bounded learnability, prefix, and public-projection audit for c1ee27b39d13."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_c1ee_parametric_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def build_report(*, seeds: int = 8) -> dict[str, Any]:
    module = _load()
    modes = list(module.MODES)
    demo_counts = [2, 3, 6]
    episodes = 0
    unique_survivor_checks = 0
    setting_neutral_checks = 0
    prefix_checks = 0
    public_checks = 0
    stress_checks = 0
    input_hashes: set[str] = set()

    for seed in range(seeds):
        for demos in demo_counts:
            generated = {
                mode: module.generate(
                    seed,
                    {"column_order": mode},
                    demos,
                    4,
                )
                for mode in modes
            }
            reference_inputs = _inputs(generated[modes[0]])
            for mode in modes[1:]:
                assert _inputs(generated[mode]) == reference_inputs
            setting_neutral_checks += 1

            short = module.generate(
                seed,
                {"column_order": modes[0]},
                2,
                1,
            )
            assert short["train"] == generated[modes[0]]["train"][:2]
            assert short["test"] == generated[modes[0]]["test"][:1]
            prefix_checks += 1

            for mode, episode in generated.items():
                certificate = module.teaching_certificate(episode)
                assert certificate["survivors"] == [mode]
                unique_survivor_checks += 1
                episodes += 1
                visible = module.public_turn(episode, 0)
                assert set(visible) == {"train", "test"}
                assert len(visible["test"]) == 1
                assert set(visible["test"][0]) == {"input"}
                public_checks += 1
                stress = episode["test"][-1]["input"]
                assert (len(stress), len(stress[0])) == (30, 30)
                assert sum(cell != 0 for row in stress for cell in row) >= 350
                stress_checks += 1
                for grid in reference_inputs:
                    input_hashes.add(
                        hashlib.sha256(
                            json.dumps(grid, separators=(",", ":")).encode("utf-8")
                        ).hexdigest()
                    )

    return {
        "schema": "c1ee27b39d13-parametric-audit-v1",
        "status": "passed",
        "finite_scope": {
            "seeds": seeds,
            "demo_counts": demo_counts,
            "settings": modes,
            "queries_per_episode": 4,
            "declared_hypotheses": list(module.HYPOTHESES),
        },
        "episodes": episodes,
        "setting_neutral_input_checks": setting_neutral_checks,
        "prefix_checks": prefix_checks,
        "unique_survivor_checks": unique_survivor_checks,
        "public_projection_checks": public_checks,
        "query_30x30_checks": stress_checks,
        "distinct_input_sha256": len(input_hashes),
        "limitation": (
            "Finite declared-rival audit; it does not prove uniqueness against "
            "arbitrary programs or all seeds."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 128:
        raise SystemExit("--seeds must be in 1..128")
    report = build_report(seeds=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
