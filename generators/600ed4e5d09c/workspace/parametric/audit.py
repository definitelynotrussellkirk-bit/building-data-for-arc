"""Bounded protected-Racket rival audit for 600ed4e5d09c."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent


def _load_family():
    path = HERE / "family.py"
    name = "_audit_family_600_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _default_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bridge = RacketBridge()

    def apply(program, grid):
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrap_rule(program)} {literal})")

    return bridge, apply


def run(
    *,
    seeds: list[int],
    demo_counts: list[int],
    queries: int,
    apply_program: Callable[[str, list[list[int]]], list[list[int]]] | None = None,
) -> dict[str, Any]:
    family = _load_family()
    owned = None
    if apply_program is None:
        owned, apply_program = _default_apply()
    rivals = {
        "canonical": (HERE / "canonical.rkt").read_text(),
        "inverse": (HERE / "inverse.rkt").read_text(),
        "skip_transform": (HERE / "skip_transform.rkt").read_text(),
        "shifted_codebook": (HERE / "shifted_codebook.rkt").read_text(),
    }
    jobs = []
    evaluations = 0
    causal_case = None
    try:
        for seed in seeds:
            for demos in demo_counts:
                for setting in family.SETTINGS:
                    episode = family.generate(seed, setting, demos, queries)
                    expected = [pair["output"] for pair in episode["train"]]
                    survivors = []
                    intended = setting["transform_codebook"]
                    for name, source in rivals.items():
                        actual = [apply_program(source, pair["input"]) for pair in episode["train"]]
                        evaluations += len(actual)
                        if actual == expected and name != intended:
                            survivors.append(name)
                    jobs.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "settings": setting,
                            "surviving_rivals": survivors,
                        }
                    )
                    if intended == "inverse" and causal_case is None:
                        pair = episode["test"][0]
                        wrong = apply_program(rivals["skip_transform"], pair["input"])
                        evaluations += 1
                        causal_case = {
                            "settings": setting,
                            "input": pair["input"],
                            "output": pair["output"],
                            "counterfactual_output": wrong,
                            "ablation": "skip_transform_intermediate",
                        }
    finally:
        if owned is not None:
            owned.close()
    passed = (
        all(not job["surviving_rivals"] for job in jobs)
        and causal_case is not None
        and causal_case["output"] != causal_case["counterfactual_output"]
    )
    return {
        "schema": "arcpuzzles-bounded-self-audit-v1",
        "task_id": family.TASK_ID,
        "passed": passed,
        "job_count": len(jobs),
        "racket_evaluations": evaluations,
        "jobs": jobs,
        "causal_case": causal_case,
        "limits": "Finite named-rival audit over supplied seeds/counts; not a uniqueness proof.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 17])
    parser.add_argument("--demo-counts", nargs="+", type=int, default=[2, 3, 6])
    parser.add_argument("--queries", type=int, default=4)
    args = parser.parse_args(argv)
    report = run(seeds=args.seeds, demo_counts=args.demo_counts, queries=args.queries)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "jobs": report["job_count"],
                "racket_evaluations": report["racket_evaluations"],
            }
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
