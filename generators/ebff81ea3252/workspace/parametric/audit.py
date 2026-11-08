"""Bounded protected-Racket self-review for the ebff81ea3252 family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def _load_family():
    path = Path(__file__).resolve().with_name("family.py")
    name = "_audit_family_ebff_" + hashlib.sha256(str(path).encode()).hexdigest()
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
    identity = bridge.runtime_identity
    if identity.get("backend") != "racket" or identity.get("protected") is not True:
        bridge.close()
        raise ValueError("protected Racket runtime required")
    cache = {}

    def apply(program, grid):
        wrapped = cache.setdefault(program, wrap_rule(program))
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        return bridge.eval_text(f"({wrapped} {literal})")

    return apply, identity, bridge


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
                        actual = execute(intended, pair["input"])
                        if actual != pair["output"]:
                            raise ValueError("intended protected-Racket label differs from claim")
                    survivors = []
                    disagreements = {}
                    for name, rival in family.rival_programs(setting).items():
                        fits = True
                        for index, pair in enumerate(episode["train"]):
                            prediction = execute(rival, pair["input"])
                            if prediction != pair["output"]:
                                fits = False
                                disagreements[name] = index
                                break
                        if fits:
                            survivors.append(name)
                            query_predictions = [execute(rival, pair["input"]) for pair in episode["test"]]
                            disagreements[name] = next(
                                (i for i, (pred, pair) in enumerate(zip(query_predictions, episode["test"]))
                                 if pred != pair["output"]),
                                None,
                            )
                    jobs.append({
                        "seed": seed,
                        "demos": demos,
                        "settings": setting,
                        "surviving_rivals": survivors,
                        "first_disagreement": disagreements,
                    })

        setting = {"decoy_selection": "nearest"}
        episode = family.generate(seeds[0], setting, min(demo_counts), queries)
        pair = episode["test"][0]
        intended = family.program(setting)
        counterfactual = family._derived_program("nearest", centers_expr="(list (list 0 0))")
        output = execute(intended, pair["input"])
        counterfactual_output = execute(counterfactual, pair["input"])
        causal = {
            "settings": setting,
            "input": pair["input"],
            "output": output,
            "counterfactual_output": counterfactual_output,
            "counterfactual_program": counterfactual,
            "ablation": "wrong_intermediate",
            "intermediate_value": family.analyze(pair["input"])["plus_centers"],
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
        "limits": "Finite named-rival review over two seeds and two demo counts; not universal uniqueness.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="append", type=int, dest="seeds")
    parser.add_argument("--demos", action="append", type=int, dest="demos")
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    report = run(seeds=args.seeds or [0, 17], demo_counts=args.demos or [2, 3], queries=args.queries)
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "jobs": report["job_count"], "racket_evaluations": report["racket_evaluations"], "out": str(out)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
