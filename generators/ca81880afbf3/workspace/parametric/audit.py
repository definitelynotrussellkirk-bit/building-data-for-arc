"""Bounded deterministic self-audit for the square-hole relay family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

BASE = Path(__file__).resolve().parent
_name = "_audit_family_ca81880afbf3_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def run_audit(seeds: Iterable[int] = range(16)) -> dict:
    failures: list[dict] = []
    episodes = pair_checks = demo_prefix_checks = query_prefix_checks = 0
    setting_output_changes = shifted_center_changes = large_queries = 0
    seed_values = list(seeds)

    for seed in seed_values:
        family.integer(seed, 0, 2**63 - 1, "seed")
        full_by_mode = {
            mode: family.generate(seed, mode, 6, 4)
            for mode in family.SETTINGS
        }
        default_inputs = [
            pair["input"]
            for pair in full_by_mode[family.DEFAULT]["train"] + full_by_mode[family.DEFAULT]["test"]
        ]
        for mode, full in full_by_mode.items():
            episodes += 1
            inputs = [pair["input"] for pair in full["train"] + full["test"]]
            if inputs != default_inputs:
                failures.append({"seed": seed, "mode": mode, "kind": "setting_dependent_inputs"})

            for count in range(2, 7):
                candidate = family.generate(seed, mode, count, 4)
                expected = full["train"][:count]
                for index, (got, want) in enumerate(zip(candidate["train"], expected)):
                    demo_prefix_checks += 1
                    if got != want:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "demo_prefix",
                            "count": count, "index": index,
                        })

            for count in range(1, 5):
                candidate = family.generate(seed, mode, 6, count)
                expected = full["test"][:count]
                for index, (got, want) in enumerate(zip(candidate["test"], expected)):
                    query_prefix_checks += 1
                    if got != want:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "query_prefix",
                            "count": count, "index": index,
                        })

            for split in ("train", "test"):
                for index, pair in enumerate(full[split]):
                    pair_checks += 1
                    intended = family.solve(pair["input"], mode)
                    if pair["output"] != intended:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "claim_mismatch",
                            "split": split, "index": index,
                        })
                    wrong = family.solve_wrong_shifted_centers(pair["input"])
                    if wrong != intended:
                        shifted_center_changes += 1
                    else:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "shifted_center_ablation_survived",
                            "split": split, "index": index,
                        })
                    other = "bridge_equal_area" if mode == "fill_only" else "fill_only"
                    if family.solve(pair["input"], other) != intended:
                        setting_output_changes += 1
                    else:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "settings_indistinguishable",
                            "split": split, "index": index,
                        })
                    info = family.intermediate(pair["input"])
                    if info["square_components"] < 3 or info["nonsquare_components"] < 1:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "weak_scene",
                            "split": split, "index": index,
                        })
                    if info["relay_pairs"] < 1:
                        failures.append({
                            "seed": seed, "mode": mode, "kind": "missing_relay",
                            "split": split, "index": index,
                        })

            large = full["test"][3]["input"]
            if len(large) == 30 and len(large[0]) == 30:
                large_queries += 1
            else:
                failures.append({"seed": seed, "mode": mode, "kind": "missing_30x30_query"})

    return {
        "schema": "ca81880afbf3-square-hole-relay-audit-v1",
        "passed": not failures,
        "status": "passed" if not failures else "failed",
        "seeds": seed_values,
        "episodes": episodes,
        "pair_checks": pair_checks,
        "demo_prefix_checks": demo_prefix_checks,
        "query_prefix_checks": query_prefix_checks,
        "setting_output_changes": setting_output_changes,
        "shifted_center_changes": shifted_center_changes,
        "large_queries": large_queries,
        "failures": failures,
        "limits": [
            "Finite seed/count audit; no universal identifiability claim.",
            "Protected Racket parity is established separately by authoring preflight.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=16)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not 1 <= args.seeds <= 256:
        parser.error("--seeds must be in 1..256")
    report = run_audit(range(args.seeds))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
