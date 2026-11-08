#!/usr/bin/env python3
"""Reusable bounded audit for the b39674306606 frequency family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "b39674306606"
HERE = Path(__file__).resolve().parent


def _load():
    path = HERE / "prototype.py"
    name = "_audit_b39674306606_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _inputs(episode: dict[str, Any]) -> list[Any]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def static_report(seeds=(0, 17)) -> dict[str, Any]:
    module = _load()
    findings = []
    episodes = 0
    matched = 0
    stress = 0
    prefix_checks = 0
    reviews = 0
    for seed in seeds:
        by_count = {}
        for demos in (2, 3, 6):
            by_setting = {}
            for target in module.FREQUENCY_TARGETS:
                short = module.generate(seed, {"frequency_target": target}, demos, 1)
                full = module.generate(seed, {"frequency_target": target}, demos, 4)
                if short["train"] != full["train"] or short["test"] != full["test"][:1]:
                    findings.append(f"prefix instability seed={seed} target={target} demos={demos}")
                prefix_checks += 1
                review = module.teaching_check(full, target)
                if review["demo_survivors"] or review["harmful_survivors"]:
                    findings.append(f"teaching survivor seed={seed} target={target}: {review}")
                reviews += 1
                grid = full["test"][3]["input"]
                foreground = sum(cell != 0 for row in grid for cell in row)
                if (len(grid), len(grid[0])) != (30, 30) or foreground < 100:
                    findings.append(f"weak stress seed={seed} target={target}")
                stress += 1
                by_setting[target] = full
                episodes += 1
            if _inputs(by_setting["singleton"]) != _inputs(by_setting["most_frequent"]):
                findings.append(f"settings changed inputs seed={seed} demos={demos}")
            matched += 1
            by_count[demos] = by_setting
    return {
        "schema": "b39674306606-parametric-static-audit-v1",
        "status": "passed" if not findings else "failed",
        "counts": {
            "episodes": episodes,
            "matched_input_comparisons": matched,
            "stress_30x30": stress,
            "prefix_checks": prefix_checks,
            "finite_candidate_reviews": reviews,
        },
        "findings": findings,
        "limits": "Finite declared policies and seeds only; not universal identifiability or measured learning gain.",
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
        {"seed": seed, "settings": {"frequency_target": target}, "demos": demos, "queries": 4}
        for target in module.FREQUENCY_TARGETS for seed in (0, 17) for demos in (2, 6)
    ]
    racket = evaluate_contract(find_root(__file__), TASK_ID, contract, jobs)
    public_dir = out / "public"
    public_dir.mkdir()
    exports = []
    for target in module.FREQUENCY_TARGETS:
        for seed in (0, 17):
            episode = module.generate_episode(seed, frequency_target=target, demos=2, queries=4)
            for index in range(4):
                challenge = module.public_view(episode, index)
                body = public_challenge_bytes(challenge)
                identifier = public_challenge_id(challenge)
                path = public_dir / f"{identifier}.json"
                if path.exists():
                    raise AssertionError("duplicate public payload")
                path.write_bytes(body)
                exports.append({"id": identifier, "path": path.relative_to(out).as_posix(),
                                "seed": seed, "frequency_target": target, "query_index": index})
    report.update({
        "status": "passed",
        "jobs": jobs,
        "racket": racket["racket"],
        "racket_evaluations": racket["racket_evaluations"],
        "qualification_like_checks": racket["checks"],
        "public_exports": exports,
    })
    (out / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = run(args.out.resolve())
    print(json.dumps({"status": report["status"],
                      "racket_evaluations": report["racket_evaluations"],
                      "public_exports": len(report["public_exports"]),
                      "report": str(args.out.resolve() / "report.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
