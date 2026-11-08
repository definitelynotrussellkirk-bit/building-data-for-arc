#!/usr/bin/env python3
"""Bounded teaching and construction audit for the native 12b9259f7792 family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_nearest_marker_family_audit", HERE / "family.py")
assert SPEC is not None and SPEC.loader is not None
family = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


def _same(a: Any, b: Any) -> bool:
    return a == b


def audit(seed_count: int) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    rival_checks = 0
    pair_count = 0
    causal_checks = 0
    for seed in range(seed_count):
        full = {mode: family.generate(seed, {"mode": mode}, 6, 4) for mode in family.MODES}
        base_inputs = [p["input"] for p in full[family.MODES[0]]["train"] + full[family.MODES[0]]["test"]]
        same_inputs = all(
            base_inputs == [p["input"] for p in full[mode]["train"] + full[mode]["test"]]
            for mode in family.MODES
        )
        unique_inputs = len({json.dumps(g, separators=(",", ":")) for g in base_inputs}) == 10
        stress = full[family.MODES[0]]["test"][3]["input"]
        stress_info = family.analyze(stress)
        stress_ok = (
            len(stress) == 30
            and len(stress[0]) == 30
            and len(stress_info["blobs"]) >= 10
            and sum(blob["area"] for blob in stress_info["blobs"]) >= 50
        )
        causal_grid = full["dominant_assignment"]["test"][0]["input"]
        causal_ok = family.solve(causal_grid, "dominant_assignment") != family.solve_skip_assignment(causal_grid)
        causal_checks += 1
        for demos in (2, 3, 6):
            for mode in family.MODES:
                episode = {
                    "train": full[mode]["train"][:demos],
                    "test": full[mode]["test"],
                }
                pair_count += demos + 4
                survivors = [
                    candidate
                    for candidate in family.MODES
                    if all(_same(family.solve(pair["input"], candidate), pair["output"]) for pair in episode["train"])
                ]
                rival_results = {}
                for name, rival in family.audit_rivals(mode).items():
                    rival_checks += 1
                    try:
                        train_refuted = any(not _same(rival(pair["input"]), pair["output"]) for pair in episode["train"])
                        test_refuted = any(not _same(rival(pair["input"]), pair["output"]) for pair in episode["test"])
                        error = None
                    except Exception as exc:  # An undefined rival is not counted as a successful teaching proof.
                        train_refuted = test_refuted = False
                        error = f"{type(exc).__name__}: {exc}"
                    rival_results[name] = {
                        "train_refuted": train_refuted,
                        "test_refuted": test_refuted,
                        "error": error,
                    }
                ok = (
                    same_inputs
                    and unique_inputs
                    and stress_ok
                    and causal_ok
                    and survivors == [mode]
                    and all(v["train_refuted"] and v["test_refuted"] and v["error"] is None for v in rival_results.values())
                )
                row = {
                    "seed": seed,
                    "demos": demos,
                    "mode": mode,
                    "surviving_modes": survivors,
                    "rivals": rival_results,
                    "same_inputs_across_modes": same_inputs,
                    "unique_inputs": unique_inputs,
                    "stress_ok": stress_ok,
                    "causal_ok": causal_ok,
                    "ok": ok,
                }
                cases.append(row)
                if not ok:
                    failures.append(row)
    return {
        "schema": "12b9259f7792-parametric-bounded-audit-v1",
        "seed_count": seed_count,
        "case_count": len(cases),
        "pair_count": pair_count,
        "rival_check_count": rival_checks,
        "causal_check_count": causal_checks,
        "failure_count": len(failures),
        "failures": failures[:20],
        "cases": cases,
        "scope": "Finite seeds and declared settings/rivals; evidence of bounded identifiability, not a universal proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 256:
        raise SystemExit("--seeds must be 1..256")
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {k: report[k] for k in ("seed_count", "case_count", "pair_count", "rival_check_count", "causal_check_count", "failure_count")}
    print(json.dumps(summary, sort_keys=True))
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
