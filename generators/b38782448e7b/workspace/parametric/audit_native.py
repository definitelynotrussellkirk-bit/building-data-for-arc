#!/usr/bin/env python3
"""Bounded teaching, causality, sampler and public-projection audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "native.py"
    spec = importlib.util.spec_from_file_location("_b387_native_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def build_report(*, seeds: int = 8) -> dict[str, Any]:
    module = _load()
    demo_counts = [2, 3, 6]
    episodes = setting_checks = prefix_checks = survivor_checks = 0
    public_checks = stress_checks = causal_checks = 0
    input_hashes: set[str] = set()
    rejections = {name: 0 for name in module.HYPOTHESES if name not in module.MODES}

    for seed in range(seeds):
        for demos in demo_counts:
            generated = {
                mode: module.generate(seed, {"finish_rule": mode}, demos, 4)
                for mode in module.MODES
            }
            reference = _inputs(generated[module.MODES[0]])
            assert _inputs(generated[module.MODES[1]]) == reference
            setting_checks += 1
            short = module.generate(seed, {"finish_rule": module.MODES[0]}, 2, 1)
            assert short["train"] == generated[module.MODES[0]]["train"][:2]
            assert short["test"] == generated[module.MODES[0]]["test"][:1]
            prefix_checks += 1

            for mode, episode in generated.items():
                certificate = module.teaching_certificate(episode)
                assert certificate["survivors"] == [mode]
                for rival in rejections:
                    if rival in certificate["rejected_at_demo"]:
                        rejections[rival] += 1
                survivor_checks += 1
                episodes += 1
                for pair in episode["train"] + episode["test"]:
                    input_hashes.add(hashlib.sha256(json.dumps(pair["input"], separators=(",", ":")).encode()).hexdigest())
                    if mode == "toggle_then_relay":
                        assert pair["output"] != module.predict(pair["input"], "relay_raw_source")
                        causal_checks += 1
                visible = module.public_turn(episode, 0)
                assert set(visible) == {"train", "test"}
                assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}
                public_checks += 1
                stress = episode["test"][-1]["input"]
                observed = module.observe(stress)
                assert (len(stress), len(stress[0])) == (30, 30)
                occupied = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value != observed["background"]]
                assert len(occupied) >= 110
                assert {min(r for r, _ in occupied), max(r for r, _ in occupied)} == {0, 29}
                assert {min(c for _, c in occupied), max(c for _, c in occupied)} == {0, 29}
                stress_checks += 1

    assert all(count == episodes for count in rejections.values())
    return {
        "schema": "b38782448e7b-native-parametric-audit-v1",
        "status": "passed",
        "finite_scope": {
            "seeds": seeds,
            "demo_counts": demo_counts,
            "settings": list(module.MODES),
            "queries_per_episode": 4,
            "declared_hypotheses": list(module.HYPOTHESES),
        },
        "episodes": episodes,
        "setting_neutral_input_checks": setting_checks,
        "prefix_checks": prefix_checks,
        "unique_survivor_checks": survivor_checks,
        "wrong_intermediate_pair_checks": causal_checks,
        "public_projection_checks": public_checks,
        "query_30x30_checks": stress_checks,
        "distinct_input_sha256": len(input_hashes),
        "rival_rejections_by_visible_demonstrations": rejections,
        "limitation": "Finite declared-rival Python audit. Focused tests and native qualification separately execute both selected programs through protected Racket; this is not a proof against arbitrary programs or all seeds.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 64:
        raise SystemExit("--seeds must be in 1..64")
    report = build_report(seeds=args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
