#!/usr/bin/env python3
"""Bounded protected-Racket self-review for assignment-order variants."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

HERE = Path(__file__).resolve().parent
PROTOTYPE = HERE / "prototype.py"


def load():
    name = "_audit_85e65da9fb15_" + hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
    if spec is None or spec.loader is None:
        raise ImportError(PROTOTYPE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execute(bridge, program, grid):
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise FileExistsError(args.out)
    p = load()
    programs = {mode: p.program_for(mode) for mode in p.MODES}
    rows = []
    evaluations = 0
    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        for seed in (0, 17, 91, 313):
            for mode in p.MODES:
                episode = p.generate_episode(seed, mode, 2, 4)
                report = p.assess_demos(episode["train"], mode)
                survivors = []
                for candidate, program in programs.items():
                    labels = [execute(bridge, program, pair["input"]) for pair in episode["train"]]
                    evaluations += len(labels)
                    if labels == [pair["output"] for pair in episode["train"]]:
                        survivors.append(candidate)
                query_ok = True
                for pair in episode["test"]:
                    label = execute(bridge, programs[mode], pair["input"])
                    evaluations += 1
                    query_ok &= label == pair["output"]
                rows.append({
                    "seed": seed,
                    "settings": {"assignment_order": mode},
                    "setting_survivors": survivors,
                    "shortcut_report": report,
                    "query_labels_match": query_ok,
                    "query_shapes": [[len(x["input"]), len(x["input"][0])] for x in episode["test"]],
                })
        causal_grid = p.select_inputs(97, 2, 4)["train"][0]["input"]
        case = p.causal_case(causal_grid)
        actual = execute(bridge, case["program"], causal_grid)
        counter = execute(bridge, case["counterfactual_program"], causal_grid)
        evaluations += 2
        causal = {
            "ablation": case["ablation"],
            "intermediate_value": case["intermediate_value"],
            "program_matches": actual == case["output"],
            "counterfactual_matches": counter == case["counterfactual_output"],
            "changed_cells": sum(a != b for ar, br in zip(actual, counter) for a, b in zip(ar, br)),
        }
        identity = bridge.runtime_identity
    findings = []
    for row in rows:
        expected = [row["settings"]["assignment_order"]]
        if row["setting_survivors"] != expected:
            findings.append({"kind": "setting_identifiability", "row": row})
        if row["shortcut_report"]["harmful_shortcut_survivors"]:
            findings.append({"kind": "shortcut_survivor", "row": row})
        if not row["query_labels_match"]:
            findings.append({"kind": "query_label", "row": row})
    if not causal["program_matches"] or not causal["counterfactual_matches"] or causal["changed_cells"] == 0:
        findings.append({"kind": "causal", "detail": causal})
    result = {
        "schema": "85e65da9fb15-parametric-self-review-v1",
        "status": "passed" if not findings else "failed",
        "scope": "Four seeds, both settings, minimum two demonstrations, four queries, five declared Python rivals per setting; finite review only.",
        "generator_sha256": p.GENERATOR_SHA256,
        "source_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
        "program_sha256": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in programs.items()},
        "racket": {k: identity[k] for k in ("backend", "protected", "binary_sha256", "prelude_sha256") if k in identity},
        "racket_evaluations": evaluations,
        "rows": rows,
        "causal": causal,
        "findings": findings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "racket_evaluations": evaluations,
                      "cases": len(rows), "changed_cells": causal["changed_cells"]}, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
