#!/usr/bin/env python3
"""Bounded adversarial and protected-Racket audit for the column-order family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "0005ab5b7704"
HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    name = "_audit_0005ab5b7704_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _public_first(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes({"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]})


def static_report(seeds=range(32)) -> dict[str, Any]:
    module = _load()
    findings: list[str] = []
    episodes = 0
    for seed in seeds:
        for demos in (2, 3, 6):
            by_order = {}
            for order in module.ORDERS:
                short = module.generate_episode(seed, order, demos=demos, queries=1)
                full = module.generate_episode(seed, order, demos=demos, queries=4)
                episodes += 1
                if short["train"] != full["train"] or short["test"] != full["test"][:1]:
                    findings.append(f"prefix drift seed={seed} order={order} demos={demos}")
                if _public_first(short) != _public_first(full):
                    findings.append(f"first-turn drift seed={seed} order={order} demos={demos}")
                certificate = module.teaching_check(full, order)
                if certificate["demo_survivors"] or certificate["harmful_survivors"]:
                    findings.append(f"teaching survivor seed={seed} order={order}: {certificate}")
                stress = module.analyze(full["test"][3]["input"])
                if (stress["height"], stress["width"]) != (30, 30) or stress["foreground_cells"] < 350:
                    findings.append(f"weak stress seed={seed} order={order}")
                if stress["density_order"] == stress["selected_columns"]:
                    findings.append(f"collapsed density order seed={seed} order={order}")
                by_order[order] = full
            left_inputs = [p["input"] for p in by_order["left_to_right"]["train"] + by_order["left_to_right"]["test"]]
            density_inputs = [p["input"] for p in by_order["body_density_desc"]["train"] + by_order["body_density_desc"]["test"]]
            if left_inputs != density_inputs:
                findings.append(f"settings changed inputs seed={seed} demos={demos}")
    return {
        "schema": "0005ab5b7704-parametric-bounded-audit-v1",
        "status": "passed" if not findings else "failed",
        "counts": {"episodes": episodes, "seeds": len(tuple(seeds))},
        "findings": findings,
        "limits": "Finite seeds and declared rivals only; not universal uniqueness or measured learning gain.",
    }


def run(out: Path) -> dict[str, Any]:
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    report = static_report()
    if report["status"] != "passed":
        raise AssertionError(report)
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((HERE / "promotion.json").read_text())
    jobs = [
        {"seed": seed, "settings": {"column_order": order}, "demos": demos, "queries": 4}
        for order in _load().ORDERS
        for seed in (0, 17)
        for demos in (2, 6)
    ]
    racket = evaluate_contract(find_root(__file__), TASK_ID, contract, jobs)
    report.update(
        {
            "jobs": jobs,
            "racket": racket["racket"],
            "racket_evaluations": racket["racket_evaluations"],
            "checks": racket["checks"],
        }
    )
    (out / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out.resolve())
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": report["counts"]["episodes"],
                "racket_evaluations": report["racket_evaluations"],
                "report": str(args.out.resolve() / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
