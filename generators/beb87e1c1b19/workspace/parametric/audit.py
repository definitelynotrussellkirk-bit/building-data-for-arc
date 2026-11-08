"""Bounded deterministic self-audit for the transform-composition family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

BASE = Path(__file__).resolve().parent
_name = "_audit_family_beb87e1c1b19_" + hashlib.sha256(str(BASE).encode()).hexdigest()[:16]
_spec = importlib.util.spec_from_file_location(_name, BASE / "family.py")
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load adjacent family.py")
family = importlib.util.module_from_spec(_spec)
sys.modules[_name] = family
_spec.loader.exec_module(family)


def run_bounded_audit(*, seeds: Iterable[int] = range(16)) -> dict:
    failures: list[dict] = []
    episodes = pair_checks = prefix_checks = query_prefix_checks = 0
    identity_changes = setting_changes = large_queries = 0
    seed_values = list(seeds)
    for seed in seed_values:
        family.integer(seed, 0, 2**63 - 1, "seed")
        full_by_mode = {
            mode: family.generate(seed, mode, 6, 4)
            for mode in family.SETTINGS
        }
        union_episode = full_by_mode["union"]
        xor_episode = full_by_mode["xor"]
        union_inputs = [p["input"] for p in union_episode["train"] + union_episode["test"]]
        xor_inputs = [p["input"] for p in xor_episode["train"] + xor_episode["test"]]
        if union_inputs != xor_inputs:
            failures.append({"seed": seed, "kind": "setting_dependent_inputs"})
        for mode, full in full_by_mode.items():
            episodes += 1
            for count in range(2, 7):
                candidate = family.generate(seed, mode, count, 4)
                expected = full["train"][:count]
                for got, want in zip(candidate["train"], expected):
                    prefix_checks += 1
                    if got != want:
                        failures.append({"seed": seed, "mode": mode, "kind": "demo_prefix", "count": count})
            for count in range(1, 5):
                candidate = family.generate(seed, mode, 6, count)
                expected = full["test"][:count]
                for got, want in zip(candidate["test"], expected):
                    query_prefix_checks += 1
                    if got != want:
                        failures.append({"seed": seed, "mode": mode, "kind": "query_prefix", "count": count})
            for split in ("train", "test"):
                for index, pair in enumerate(full[split]):
                    pair_checks += 1
                    intended = family.solve(pair["input"], mode)
                    if intended != pair["output"]:
                        failures.append({"seed": seed, "mode": mode, "kind": "claim_mismatch", "split": split, "index": index})
                    if family.solve_wrong_identity(pair["input"], mode) != intended:
                        identity_changes += 1
                    else:
                        failures.append({"seed": seed, "mode": mode, "kind": "identity_ablation_survived", "split": split, "index": index})
                    other = "xor" if mode == "union" else "union"
                    if family.solve(pair["input"], other) != intended:
                        setting_changes += 1
                    else:
                        failures.append({"seed": seed, "mode": mode, "kind": "settings_indistinguishable", "split": split, "index": index})
                    info = family.intermediate(pair["input"])
                    if info["transform_matches"] != 1:
                        failures.append({"seed": seed, "mode": mode, "kind": "ambiguous_transform", "split": split, "index": index})
            if len(full["test"][3]["input"]) == 30 and len(full["test"][3]["input"][0]) == 30:
                large_queries += 1
            else:
                failures.append({"seed": seed, "mode": mode, "kind": "missing_30x30_query"})
    return {
        "schema": "beb87e1c1b19-transform-composition-audit-v1",
        "status": "passed" if not failures else "failed",
        "seeds": seed_values,
        "episodes": episodes,
        "pair_checks": pair_checks,
        "prefix_checks": prefix_checks,
        "query_prefix_checks": query_prefix_checks,
        "identity_ablation_changes": identity_changes,
        "setting_output_changes": setting_changes,
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
    report = run_bounded_audit(seeds=range(args.seeds))
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
