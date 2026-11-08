#!/usr/bin/env python3
"""Bounded reusable lesson audit for the profile-source parametric family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype.py"


def _load_prototype():
    body = PROTOTYPE.read_bytes()
    name = "_audit_profile_sources_" + hashlib.sha256(str(PROTOTYPE).encode() + body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(seeds: list[int]) -> dict[str, Any]:
    prototype = _load_prototype()
    rows = []
    failures = []
    for seed in seeds:
        for selected in prototype.ALLOWED_PROFILE_SOURCES:
            for demos in (2, 3, 6):
                episode = prototype.build_claimed_episode(seed, selected, demos, 4)
                result = prototype.audit_episode(episode, selected)
                query_metrics = [prototype.input_metrics(pair["input"]) for pair in episode["test"]]
                row = {
                    "seed": seed,
                    "profile_sources": selected,
                    "demos": demos,
                    "queries": 4,
                    "audit": result,
                    "query_metrics": query_metrics,
                }
                rows.append(row)
                if result["opposite_setting_survives"]:
                    failures.append({**row, "failure": "opposite setting survives demos"})
                if result["query_disagreements"] != 4:
                    failures.append({**row, "failure": "opposite setting agrees on a query"})
                if result["surviving_declared_shortcuts"]:
                    failures.append({**row, "failure": "declared shortcut survives demos"})
                one = prototype.build_claimed_episode(seed, selected, demos, 1)
                if one["train"] != episode["train"] or one["test"] != episode["test"][:1]:
                    failures.append({**row, "failure": "single-query prefix drift"})
    return {
        "schema": "0eb4eaa46003-profile-source-audit-v1",
        "status": "passed" if not failures else "failed",
        "seeds": seeds,
        "episodes": len(rows),
        "declared_shortcuts": list(prototype.DECLARED_SHORTCUTS),
        "rows": rows,
        "failures": failures,
        "limits": "Finite declared settings, seeds and shortcuts only; Racket qualification is separate.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", default="0,1,17,57")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    if not seeds or len(set(seeds)) != len(seeds) or any(seed < 0 for seed in seeds):
        raise ValueError("--seeds needs distinct nonnegative integers")
    report = audit(seeds)
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    else:
        print(payload, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
