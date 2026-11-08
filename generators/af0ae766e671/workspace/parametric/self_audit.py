#!/usr/bin/env python3
"""Protected-Racket self-audit for the af0ae766e671 global-selection family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import normalize_grid

HERE = Path(__file__).resolve().parent
TASK_ID = "af0ae766e671"


def _load():
    path = HERE / "prototype.py"
    name = "_audit_af0a_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _execute(bridge: RacketBridge, source: str, grid: list[list[int]]) -> list[list[int]]:
    return normalize_grid(bridge.eval_text(f"({wrap_rule(source)} {_literal(grid)})"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run() -> tuple[dict[str, Any], dict[str, Any]]:
    module = _load()
    jobs = []
    evaluations = 0
    with RacketBridge() as bridge:
        if bridge.runtime_identity.get("protected") is not True:
            raise RuntimeError("protected Racket required")
        for seed in (0, 17):
            for setting in module.SETTINGS:
                small = module.generate(seed, setting, 2, 1)
                large = module.generate(seed, setting, 6, 4)
                if small["train"] != large["train"][:2] or small["test"] != large["test"][:1]:
                    raise AssertionError("count prefix instability")
                review = module.self_review(large)
                if review["intended_survivors"] != [setting["selection"]] or review["harmful_survivors"]:
                    raise AssertionError((seed, setting, review))
                for split in ("train", "test"):
                    for pair in large[split]:
                        actual = _execute(bridge, module.program(setting), pair["input"])
                        evaluations += 1
                        if actual != pair["output"]:
                            raise AssertionError((seed, setting, split))
                jobs.append({
                    "seed": seed,
                    "settings": setting,
                    "demo_count": 6,
                    "query_count": 4,
                    "episode_sha256": module.episode_digest(large),
                    "self_review": review,
                })
        matched = [module.generate(0, setting, 6, 4) for setting in module.SETTINGS]
        for split in ("train", "test"):
            if [p["input"] for p in matched[0][split]] != [p["input"] for p in matched[1][split]]:
                raise AssertionError("settings do not share inputs")
        stress = matched[0]["test"][3]
        grid = stress["input"]
        if (len(grid), len(grid[0])) != (30, 30):
            raise AssertionError("missing 30x30 stress")
        foreground = sum(v != 0 for row in grid for v in row)
        if foreground < 350:
            raise AssertionError("30x30 stress is not substantive")
        stats = module.occupancy_stats(grid)
        causal = module.causal_case()
        correct = _execute(bridge, module.program(causal["settings"]), causal["input"])
        wrong_source = (HERE / "denser_panel_only.rkt").read_text(encoding="utf-8")
        wrong = _execute(bridge, wrong_source, causal["input"])
        evaluations += 2
        if correct != causal["output"] or wrong != causal["counterfactual_output"] or correct == wrong:
            raise AssertionError("causal witness replay failed")
        audited_case = {
            "settings": causal["settings"],
            "program": module.program(causal["settings"]),
            "input": causal["input"],
            "output": causal["output"],
            "counterfactual_program": wrong_source,
            "intermediate_value": causal["intermediate_value"],
            "ablation": causal["ablation"],
        }
        report = {
            "schema": "af0ae766e671-parametric-self-audit-v1",
            "task_id": TASK_ID,
            "passed": True,
            "settings": list(module.SETTINGS),
            "jobs": jobs,
            "protected_racket_evaluations": evaluations,
            "matched_input_jobs": 2,
            "count_profiles": [[2, 1], [6, 4]],
            "stress": {
                "shape": [30, 30],
                "foreground_cells": foreground,
                "state_counts": stats["state_counts"],
                "upper_count": stats["upper_count"],
                "lower_count": stats["lower_count"],
                "setting_difference_cells": module.diff_cells(
                    matched[0]["test"][3]["output"], matched[1]["test"][3]["output"]
                ),
            },
            "causal_difference_cells": causal["difference_cells"],
            "runtime": bridge.runtime_identity,
            "limitations": [
                "Finite seeds and declared rivals only; not a universal uniqueness proof.",
                "Owner exact-source acceptance and training admission remain separate.",
            ],
        }
        return report, audited_case


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("output directory must be new or empty")
    report, case = run()
    _write(args.out / "self-audit.json", report)
    _write(args.out / "audited-causal-case.json", case)
    print(json.dumps({
        "passed": report["passed"],
        "jobs": len(report["jobs"]),
        "protected_racket_evaluations": report["protected_racket_evaluations"],
        "out": str(args.out),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
