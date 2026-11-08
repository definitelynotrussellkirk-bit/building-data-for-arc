#!/usr/bin/env python3
"""Reusable bounded audit for the row-fill/bridge family."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def _load():
    path = HERE / "prototype.py"
    spec = importlib.util.spec_from_file_location("_row_parametric_audit_target", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_report(*, seeds=(0, 17, 97), use_racket=True):
    mod = _load()
    errors = []
    requests = 0
    surviving = set()
    input_banks = {}
    for seed in seeds:
        for demos in (2, 6):
            for queries in (1, 4):
                baseline_inputs = None
                for policy in mod.POLICIES:
                    settings = {"row_policy": policy}
                    episode = mod.generate(seed, settings, demos, queries)
                    requests += 1
                    if episode != mod.generate(seed, settings, demos, queries):
                        errors.append(f"nondeterministic request seed={seed} settings={settings}")
                    inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
                    if baseline_inputs is None:
                        baseline_inputs = inputs
                    elif inputs != baseline_inputs:
                        errors.append(f"setting leaked into inputs seed={seed} demos={demos} queries={queries}")
                    check = mod.teaching_check(episode, settings)
                    surviving.update(check["surviving_rivals"])
                    if check["survivors"] != [settings]:
                        errors.append(f"finite setting ambiguity seed={seed} settings={settings}: {check}")
                    prefix = mod.generate(seed, settings, 2, 1)
                    if prefix["train"] != episode["train"][:2] or prefix["test"] != episode["test"][:1]:
                        errors.append(f"count-prefix instability seed={seed} settings={settings}")
                input_banks[(seed, demos, queries)] = baseline_inputs
    if not any(len(g) == 30 and len(g[0]) == 30 for g in input_banks[(seeds[0], 2, 4)]):
        errors.append("four-query bank lacks 30x30 stress")

    racket = None
    evaluations = 0
    counterfactual_cases = []
    if use_racket:
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        with _local_imports(ROOT / "shared/runtime", HERE):
            apply, racket, bridge = _real_evaluator(ROOT / "shared/runtime")
            try:
                counter_program = (HERE / "rightmost-bridge.rkt").read_text().rstrip("\n")
                for seed in seeds:
                    for policy in mod.POLICIES:
                        settings = {"row_policy": policy}
                        episode = mod.generate(seed, settings, 2, 4)
                        program = mod.program(settings)
                        for pair in episode["train"] + episode["test"]:
                            actual = apply(program, pair["input"])
                            evaluations += 1
                            if actual != pair["output"]:
                                errors.append(f"Racket label mismatch seed={seed} settings={settings}")
                        if policy == "bridge_equal":
                            pair = episode["test"][0]
                            wrong = apply(counter_program, pair["input"])
                            evaluations += 1
                            expected_wrong = mod.transform_rightmost_bridge(pair["input"])
                            if wrong != expected_wrong or wrong == pair["output"]:
                                errors.append(f"counterfactual failed seed={seed}")
                            counterfactual_cases.append({
                                "seed": seed,
                                "input_sha256": hashlib.sha256(json.dumps(pair["input"], separators=(",", ":")).encode()).hexdigest(),
                                "output_changed": wrong != pair["output"],
                            })
            finally:
                bridge.close()
    return {
        "schema": "7092d9933e2d-parametric-audit-v1",
        "status": "PASS" if not errors and not surviving else "FAIL",
        "seeds": list(seeds),
        "requests": requests,
        "surviving_rivals": sorted(surviving),
        "racket": racket,
        "racket_evaluations": evaluations,
        "counterfactual_cases": counterfactual_cases,
        "source_sha256": {
            "prototype.py": _sha(HERE / "prototype.py"),
            "canonical.rkt": _sha(HERE / "canonical.rkt"),
            "bridge-equal.rkt": _sha(HERE / "bridge-equal.rkt"),
            "rightmost-bridge.rkt": _sha(HERE / "rightmost-bridge.rkt"),
        },
        "errors": errors,
        "limits": [
            "Finite named-rival and seed audit; it does not prove universal uniqueness.",
            "Protected Racket execution is present only when use_racket is true.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-racket", action="store_true")
    parser.add_argument("--seed", action="append", type=int)
    args = parser.parse_args()
    report = build_report(seeds=tuple(args.seed or (0, 17, 97)), use_racket=not args.no_racket)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: report[k] for k in ("status", "requests", "racket_evaluations", "surviving_rivals", "errors")}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
