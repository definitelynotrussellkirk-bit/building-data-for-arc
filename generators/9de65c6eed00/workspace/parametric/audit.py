"""Reusable bounded teaching, projection, and protected-Racket audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ADAPTER = HERE / "adapter.py"


def _load_adapter():
    name = "_audit_9de65c6eed00_" + hashlib.sha256(str(ADAPTER).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    if spec is None or spec.loader is None:
        raise ImportError(ADAPTER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _real_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("audit requires protected Racket")
    cache: dict[str, str] = {}

    def apply(source: str, grid: list[list[int]]) -> list[list[int]]:
        wrapped = cache.setdefault(source, wrap_rule(source))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped} {literal})")

    keep = {k: identity[k] for k in identity if k in {
        "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
        "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
    }}
    return apply, keep, bridge


def run(*, seed_count: int = 32, apply_program=None) -> dict[str, Any]:
    p = _load_adapter()
    if type(seed_count) is not int or not 1 <= seed_count <= 256:
        raise ValueError("seed_count must be an exact integer in 1..256")

    episode_count = 0
    public_views = 0
    corner_counts = {corner: 0 for corner in p.CORNERS}
    rival_survivors: dict[str, int] = {}
    failures: list[dict[str, Any]] = []
    for seed in range(seed_count):
        setting_dicts = [{"normalization_anchor": value} for value in p.SETTINGS]
        full_by_setting = {
            settings["normalization_anchor"]: p.generate(seed, settings, 6, 4)
            for settings in setting_dicts
        }
        left_inputs = [pair["input"] for pair in full_by_setting["top_left"]["train"] + full_by_setting["top_left"]["test"]]
        right_inputs = [pair["input"] for pair in full_by_setting["relative_corner"]["train"] + full_by_setting["relative_corner"]["test"]]
        if left_inputs != right_inputs:
            failures.append({"seed": seed, "kind": "settings_input_mismatch"})
        for settings in setting_dicts:
            value = settings["normalization_anchor"]
            full = full_by_setting[value]
            for pair in full["train"] + full["test"]:
                corner_counts[p.analyze(pair["input"])["relative_corner"]] += 1
            for demos in range(2, 7):
                for queries in range(1, 5):
                    episode_count += 1
                    episode = p.generate(seed, settings, demos, queries)
                    if episode["train"] != full["train"][:demos] or episode["test"] != full["test"][:queries]:
                        failures.append({"seed": seed, "settings": settings, "demos": demos, "queries": queries, "kind": "prefix_instability"})
                    cert = episode["certificate"]
                    if cert["surviving_settings"] != [settings] or cert["ambiguous_rivals"]:
                        failures.append({"seed": seed, "settings": settings, "demos": demos, "queries": queries, "kind": "teaching", "certificate": cert})
                    for name in cert["surviving_rivals"]:
                        rival_survivors[name] = rival_survivors.get(name, 0) + 1
                    public = p.public_turn(episode, 0)
                    public_views += 1
                    if len(public.get("test", [])) != 1 or "output" in public["test"][0]:
                        failures.append({"seed": seed, "settings": settings, "demos": demos, "queries": queries, "kind": "public_projection"})

    bridge = None
    if apply_program is None:
        apply, identity, bridge = _real_apply()
    else:
        apply = apply_program
        identity = {"backend": "test", "protected": False}
    evaluations = 0
    racket_jobs: list[dict[str, Any]] = []
    causal = None
    try:
        for seed in (0, 17):
            for value in p.SETTINGS:
                settings = {"normalization_anchor": value}
                episode = p.generate(seed, settings, 2, 4)
                source = p.program(settings)
                checked = 0
                for split in ("train", "test"):
                    for pair in episode[split]:
                        actual = apply(source, pair["input"])
                        evaluations += 1
                        checked += 1
                        if actual != pair["output"]:
                            failures.append({"seed": seed, "settings": settings, "split": split, "kind": "racket_claim_mismatch"})
                racket_jobs.append({"seed": seed, "settings": settings, "pairs": checked})
        episode = p.generate(0, {"normalization_anchor": "relative_corner"}, 2, 4)
        pair_index, pair = next((i, pair) for i, pair in enumerate(episode["test"])
                                if p.analyze(pair["input"])["relative_corner"] != "top_left")
        actual_corner = p.analyze(pair["input"])["relative_corner"]
        wrong_corner = "top_left"
        intended_source = p.program({"normalization_anchor": "relative_corner"})
        wrong_source = p.counterfactual_program(wrong_corner)
        intended = apply(intended_source, pair["input"]); evaluations += 1
        wrong = apply(wrong_source, pair["input"]); evaluations += 1
        if intended != pair["output"] or wrong == intended:
            failures.append({"kind": "causal_counterfactual_failed"})
        causal = {
            "settings": {"normalization_anchor": "relative_corner"},
            "program": intended_source,
            "input": pair["input"],
            "output": intended,
            "intermediate_value": actual_corner,
            "counterfactual_program": wrong_source,
            "counterfactual_output": wrong,
            "wrong_intermediate": wrong_corner,
            "ablation": "wrong_intermediate",
            "episode_seed": 0,
            "split": "test",
            "pair_index": pair_index,
        }
    finally:
        if bridge is not None:
            bridge.close()

    return {
        "schema": "arcpuzzles-9de65c6eed00-self-audit-v1",
        "passed": not failures,
        "seed_count": seed_count,
        "episode_count": episode_count,
        "public_views": public_views,
        "corner_counts": corner_counts,
        "rival_survivors": rival_survivors,
        "finite_scope": "all demo counts 2..6 and query counts 1..4 over the requested seed prefix; seven declared corner shortcuts",
        "racket": identity,
        "racket_jobs": racket_jobs,
        "racket_evaluations": evaluations,
        "causal_case": causal,
        "failures": failures,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-count", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise SystemExit(f"refusing existing output: {args.out}")
    report = run(seed_count=args.seed_count)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out), "passed": report["passed"],
        "episodes": report["episode_count"],
        "public_views": report["public_views"],
        "racket_evaluations": report["racket_evaluations"],
    }, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
