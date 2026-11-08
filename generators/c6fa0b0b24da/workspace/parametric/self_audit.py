#!/usr/bin/env python3
"""Reusable bounded audit for the c6fa0b0b24da fill-finish family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "c6fa0b0b24da"
HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "native.py"
    name = "_audit_c6fa0b0b24da_" + hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _public_first(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes({
        "train": episode["train"],
        "test": [{"input": episode["test"][0]["input"]}],
    })


def static_report(seeds=range(32)) -> dict[str, Any]:
    module = _load()
    findings: list[str] = []
    episodes = matched = prefix = teaching = stress = setting_differences = 0
    for seed in seeds:
        for demos in (2, 3, 6):
            by_finish = {}
            for finish in module.FILL_FINISHES:
                short = module.generate_episode(seed, finish, demos=demos, queries=1)
                full = module.generate_episode(seed, finish, demos=demos, queries=4)
                episodes += 1
                if short["train"] != full["train"] or short["test"] != full["test"][:1]:
                    findings.append(f"prefix instability seed={seed} finish={finish} demos={demos}")
                if _public_first(short) != _public_first(full):
                    findings.append(f"first-turn drift seed={seed} finish={finish} demos={demos}")
                prefix += 1
                review = module.teaching_check(full, finish)
                if review["demo_survivors"] or review["harmful_survivors"]:
                    findings.append(f"teaching survivor seed={seed} finish={finish}: {review}")
                teaching += 1
                grid = full["test"][3]["input"]
                output = full["test"][3]["output"]
                foreground = sum(v != 0 for row in output for v in row)
                if (len(grid), len(grid[0])) != (30, 30) or not 600 <= foreground < 900:
                    findings.append(f"weak 30x30 stress seed={seed} finish={finish}")
                stress += 1
                by_finish[finish] = full
            canonical = by_finish["canonical"]
            alternate = by_finish["largest_new_region_to_8"]
            for split in ("train", "test"):
                if [p["input"] for p in canonical[split]] != [p["input"] for p in alternate[split]]:
                    findings.append(f"settings changed inputs seed={seed} demos={demos} split={split}")
                if any(a["output"] == b["output"] for a, b in zip(canonical[split], alternate[split], strict=True)):
                    findings.append(f"settings collapsed seed={seed} demos={demos} split={split}")
                setting_differences += len(canonical[split])
            matched += 1
    return {
        "schema": "c6fa0b0b24da-parametric-bounded-audit-v1",
        "status": "passed" if not findings else "failed",
        "counts": {
            "episodes": episodes,
            "matched_input_comparisons": matched,
            "prefix_and_first_turn_checks": prefix,
            "finite_teaching_reviews": teaching,
            "stress_30x30": stress,
            "setting_output_differences": setting_differences,
        },
        "findings": findings,
        "limits": "Finite declared rivals and seeds only; not universal uniqueness or measured learning gain.",
    }


def run(out: Path) -> dict[str, Any]:
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    module = _load()
    report = static_report()
    if report["status"] != "passed":
        raise AssertionError(report)
    from arcpuzzles.parametric_worker import evaluate_contract
    contract = json.loads((HERE / "promotion.json").read_text(encoding="utf-8"))
    jobs = [
        {"seed": seed, "settings": {"fill_finish": finish}, "demos": demos, "queries": 4}
        for finish in module.FILL_FINISHES
        for seed in (0, 17)
        for demos in (2, 6)
    ]
    racket = evaluate_contract(find_root(__file__), TASK_ID, contract, jobs)
    report.update({
        "jobs": jobs,
        "racket": racket["racket"],
        "racket_evaluations": racket["racket_evaluations"],
        "qualification_like_checks": racket["checks"],
    })
    (out / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out.resolve())
    print(json.dumps({
        "status": report["status"],
        "episodes": report["counts"]["episodes"],
        "racket_evaluations": report["racket_evaluations"],
        "report": str(args.out.resolve() / "report.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
