#!/usr/bin/env python3
"""Bounded protected-Racket self-review for the cap/bridge family."""
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
    name = "_audit_94549757a7f3_" + hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest()
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


def changed_cells(left, right):
    return sum(
        a != b
        for row_a, row_b in zip(left, right, strict=True)
        for a, b in zip(row_a, row_b, strict=True)
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--case-out", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in (args.out, args.case_out):
        if path.exists():
            raise FileExistsError(path)

    p = load()
    programs = {
        "cap_only": p.program({p.PARAMETER: "cap_only"}),
        "cap_then_vertical_bridge": p.program({p.PARAMETER: "cap_then_vertical_bridge"}),
        "skip_cap": (HERE / "skip_cap.rkt").read_text(),
        "horizontal_bridge": (HERE / "horizontal_bridge.rkt").read_text(),
        "first_column_bridge": (HERE / "first_column_bridge.rkt").read_text(),
        "last_column_bridge": (HERE / "last_column_bridge.rkt").read_text(),
        "full_height_bridge": (HERE / "full_height_bridge.rkt").read_text(),
        "green_endpoint_bridge": (HERE / "green_endpoint_bridge.rkt").read_text(),
        "color3_bridge": (HERE / "color3_bridge.rkt").read_text(),
        "cap_all_colors": (HERE / "cap_all_colors.rkt").read_text(),
    }

    rows = []
    evaluations = 0
    identity = {}
    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        for seed in (0, 17, 91, 313):
            for rule in p.RULES:
                episode = p.generate(seed, {p.PARAMETER: rule}, 2, 4)
                expected_demo = [pair["output"] for pair in episode["train"]]
                expected_query = [pair["output"] for pair in episode["test"]]
                survivors = []
                query_equivalent = []
                disagreements = {}
                for name, source in programs.items():
                    demo_labels = [execute(bridge, source, pair["input"])
                                   for pair in episode["train"]]
                    query_labels = [execute(bridge, source, pair["input"])
                                    for pair in episode["test"]]
                    evaluations += len(demo_labels) + len(query_labels)
                    if demo_labels == expected_demo:
                        survivors.append(name)
                    if query_labels == expected_query:
                        query_equivalent.append(name)
                    disagreements[name] = {
                        "demo_changed_cells": [changed_cells(got, want)
                                               for got, want in zip(demo_labels, expected_demo, strict=True)],
                        "query_changed_cells": [changed_cells(got, want)
                                                for got, want in zip(query_labels, expected_query, strict=True)],
                    }
                rows.append({
                    "seed": seed,
                    "settings": {p.PARAMETER: rule},
                    "program_survivors": survivors,
                    "query_equivalent_programs": query_equivalent,
                    "disagreements": disagreements,
                    "query_shapes": [[len(pair["input"]), len(pair["input"][0])]
                                     for pair in episode["test"]],
                })

        causal_grid = p.generate(97, {p.PARAMETER: "cap_then_vertical_bridge"}, 2, 4)["test"][-1]["input"]
        case = p.causal_case(causal_grid)
        actual = execute(bridge, case["program"], causal_grid)
        counter = execute(bridge, case["counterfactual_program"], causal_grid)
        evaluations += 2
        causal = {
            "ablation": case["ablation"],
            "intermediate_value": case["intermediate_value"],
            "program_matches": actual == case["output"],
            "counterfactual_matches": counter == case["counterfactual_output"],
            "changed_cells": changed_cells(actual, counter),
        }
        identity = bridge.runtime_identity

    findings = []
    for row in rows:
        expected = [row["settings"][p.PARAMETER]]
        if row["program_survivors"] != expected:
            findings.append({"kind": "program_identifiability", "row": row})
        if row["settings"][p.PARAMETER] not in row["query_equivalent_programs"]:
            findings.append({"kind": "selected_query_label", "row": row})
    if not causal["program_matches"] or not causal["counterfactual_matches"] or causal["changed_cells"] == 0:
        findings.append({"kind": "causal", "detail": causal})

    result = {
        "schema": "94549757a7f3-parametric-self-review-v1",
        "status": "passed" if not findings else "failed",
        "scope": (
            "Four seeds, both settings, minimum two demonstrations, four queries, "
            "the opposite setting and eight executable semantic shortcut programs; finite review only."
        ),
        "generator_sha256": p.GENERATOR_SHA256,
        "source_sha256": hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest(),
        "program_sha256": {name: hashlib.sha256(source.encode()).hexdigest()
                           for name, source in programs.items()},
        "racket": {key: identity[key] for key in
                   ("backend", "protected", "binary_sha256", "prelude_sha256")
                   if key in identity},
        "racket_evaluations": evaluations,
        "rows": rows,
        "causal": causal,
        "findings": findings,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.case_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.case_out.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "cases": len(rows),
        "programs": len(programs),
        "racket_evaluations": evaluations,
        "changed_cells": causal["changed_cells"],
    }, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
