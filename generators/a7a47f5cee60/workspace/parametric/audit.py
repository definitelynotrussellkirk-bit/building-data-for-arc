#!/usr/bin/env python3
"""Bounded finite teaching audit for the a7a47f5cee60 family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("_a7a47_parametric_audit_family", HERE / "prototype.py")
assert SPEC is not None and SPEC.loader is not None
family = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(family)


def audit(seeds: int) -> dict:
    cases = []
    failures = []
    for seed in range(seeds):
        for demos in (2, 3, 6):
            for role in family.ROLES:
                settings = {family.PARAMETER_NAME: role}
                episode = family.generate(seed, settings, demos, 4)
                cert = family.lesson_certificate(episode["train"], [p["input"] for p in episode["test"]])
                ok = cert["surviving_settings"] == [settings] and cert["surviving_shortcuts"] == []
                row = {
                    "seed": seed,
                    "demos": demos,
                    "settings": settings,
                    "query_shapes": [[len(p["input"]), len(p["input"][0])] for p in episode["test"]],
                    "certificate": cert,
                    "ok": ok,
                }
                cases.append(row)
                if not ok:
                    failures.append(row)
    return {
        "schema": "a7a47f5cee60-parametric-finite-audit-v1",
        "seed_count": seeds,
        "case_count": len(cases),
        "pair_count": sum(row["demos"] + 4 for row in cases),
        "failure_count": len(failures),
        "failures": failures[:20],
        "cases": cases,
        "limits": "Finite declared settings/shortcuts and bounded seeds; not universal identifiability.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 4096:
        raise SystemExit("--seeds must be 1..4096")
    report = audit(args.seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("seed_count", "case_count", "pair_count", "failure_count")}, sort_keys=True))
    return 0 if report["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
