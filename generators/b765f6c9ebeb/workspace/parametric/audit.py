#!/usr/bin/env python3
"""Bounded sampler, teaching, causality, and public-projection audit."""
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
    spec = importlib.util.spec_from_file_location("_b765_parametric_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def build_report(*, seeds: int = 12) -> dict[str, Any]:
    module = _load()
    modes = list(module.MODES)
    demo_counts = [2, 3, 6]
    episodes = 0
    setting_neutral_checks = 0
    prefix_checks = 0
    unique_survivor_checks = 0
    wrong_order_checks = 0
    public_checks = 0
    stress_checks = 0
    input_hashes: set[str] = set()
    rejection_counts = {name: 0 for name in module.HYPOTHESES if name not in modes}

    for seed in range(seeds):
        for demos in demo_counts:
            generated = {
                mode: module.generate(seed, {"finish_rule": mode}, demos, 4)
                for mode in modes
            }
            reference_inputs = _inputs(generated[modes[0]])
            for mode in modes[1:]:
                assert _inputs(generated[mode]) == reference_inputs
            setting_neutral_checks += 1

            short = module.generate(seed, {"finish_rule": modes[0]}, 2, 1)
            assert short["train"] == generated[modes[0]]["train"][:2]
            assert short["test"] == generated[modes[0]]["test"][:1]
            prefix_checks += 1

            for mode, episode in generated.items():
                certificate = module.teaching_certificate(episode)
                assert certificate["survivors"] == [mode]
                for rival in rejection_counts:
                    if rival in certificate["rejected_at_demo"]:
                        rejection_counts[rival] += 1
                unique_survivor_checks += 1
                episodes += 1

                for pair in episode["train"] + episode["test"]:
                    if mode == "erase_then_bridge":
                        assert pair["output"] != module.predict(
                            pair["input"], "bridge_before_erase"
                        )
                        wrong_order_checks += 1
                    input_hashes.add(
                        hashlib.sha256(
                            json.dumps(
                                pair["input"], separators=(",", ":")
                            ).encode("utf-8")
                        ).hexdigest()
                    )

                visible = module.public_turn(episode, 0)
                assert set(visible) == {"train", "test"}
                assert len(visible["test"]) == 1
                assert set(visible["test"][0]) == {"input"}
                public_checks += 1

                stress = episode["test"][-1]["input"]
                assert (len(stress), len(stress[0])) == (30, 30)
                occupied = [
                    (row, col)
                    for row, values in enumerate(stress)
                    for col, value in enumerate(values)
                    if value != 0
                ]
                assert len(occupied) >= 120
                assert min(row for row, _ in occupied) == 0
                assert max(row for row, _ in occupied) == 29
                assert min(col for _, col in occupied) == 0
                assert max(col for _, col in occupied) == 29
                observed = module.observe(stress)
                assert set(observed["bridge_axes"]) == {"row", "column"}
                assert observed["singleton_count"] >= 6
                assert observed["survivor_count"] >= 6
                stress_checks += 1

    expected_per_rival = episodes
    assert all(count == expected_per_rival for count in rejection_counts.values())
    return {
        "schema": "b765f6c9ebeb-parametric-audit-v1",
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
        "wrong_order_pair_checks": wrong_order_checks,
        "public_projection_checks": public_checks,
        "query_30x30_checks": stress_checks,
        "distinct_input_sha256": len(input_hashes),
        "rival_rejections_by_visible_demonstrations": rejection_counts,
        "limitation": (
            "Finite declared-rival audit using the independent Python mirrors. "
            "Focused tests and native qualification separately execute both "
            "selected rules through protected Racket; this is not a proof "
            "against arbitrary programs or all seeds."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=12)
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
