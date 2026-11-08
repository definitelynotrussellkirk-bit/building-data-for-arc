"""Bounded protected-Racket self-review for the 96d4a788da47 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _load_family():
    path = Path(__file__).resolve().with_name("family.py")
    name = "_audit_family_96_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _real_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge()
    if bridge.runtime_identity.get("backend") != "racket" or bridge.runtime_identity.get("protected") is not True:
        bridge.close()
        raise ValueError("protected Racket runtime required")
    cache = {}

    def apply(program, grid):
        wrapped = cache.setdefault(program, wrap_rule(program))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped} {literal})")

    return apply, bridge.runtime_identity, bridge


def run(*, seeds=(0, 17), demo_counts=(2, 3), queries=4, apply_program=None):
    family = _load_family()
    bridge = None
    if apply_program is None:
        apply_program, identity, bridge = _real_apply()
    else:
        identity = {"backend": "racket", "protected": True}
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return apply_program(program, grid)

    jobs = []
    try:
        for seed in seeds:
            for demos in demo_counts:
                for setting in family.SETTINGS:
                    episode = family.generate(seed, setting, demos, queries)
                    intended = family.program(setting)
                    for pair in episode["train"] + episode["test"]:
                        if execute(intended, pair["input"]) != pair["output"]:
                            raise ValueError("intended protected-Racket label differs from claim")
                    survivors = []
                    first_disagreements = {}
                    for name, rival in family.rival_programs(setting).items():
                        fits = True
                        for index, pair in enumerate(episode["train"]):
                            if execute(rival, pair["input"]) != pair["output"]:
                                fits = False
                                first_disagreements[name] = index
                                break
                        if fits:
                            survivors.append(name)
                            query_predictions = [execute(rival, pair["input"]) for pair in episode["test"]]
                            if all(pred == pair["output"] for pred, pair in zip(query_predictions, episode["test"])):
                                first_disagreements[name] = None
                    jobs.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": setting,
                        "surviving_rivals": survivors,
                        "first_demo_disagreement": first_disagreements,
                    })

        setting = {"destination_edge": "nearest"}
        episode = family.generate(seeds[0], setting, min(demo_counts), queries)
        pair = episode["test"][0]
        counterfactual = Path(__file__).resolve().with_name("constant_shift_1.rkt").read_text(encoding="utf-8")
        output = execute(family.program(setting), pair["input"])
        counterfactual_output = execute(counterfactual, pair["input"])
        causal = {
            "settings": setting,
            "program": family.program(setting),
            "input": pair["input"],
            "output": output,
            "counterfactual_program": counterfactual,
            "counterfactual_output": counterfactual_output,
            "ablation": "wrong_intermediate",
            "intermediate_value": "per-object signed displacement derived from each bounding-box edge distance",
        }
    finally:
        if bridge is not None:
            bridge.close()

    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": family.TASK_ID,
        "passed": all(not job["surviving_rivals"] for job in jobs)
        and causal["output"] != causal["counterfactual_output"],
        "job_count": len(jobs),
        "jobs": jobs,
        "causal_case": causal,
        "racket": {k: identity[k] for k in identity if k in {"backend", "protected", "schema", "binary_sha256", "prelude_sha256"}},
        "racket_evaluations": evaluations,
        "limits": "Finite named-rival review over requested seeds/counts; not universal uniqueness.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", action="append", type=int, dest="demos")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = run(
        seeds=args.seeds or [0, 17],
        demo_counts=args.demos or [2, 3],
        queries=args.queries,
    )
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "jobs": report["job_count"], "out": str(out)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
